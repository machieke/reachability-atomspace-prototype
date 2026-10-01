"""Atomic local leases and intents shared with the durable dispatch boundary.

One authority clock orders shared resource leases across all belief contexts.
Action gates require the context evidence clock to match that clock exactly.
"""
from dataclasses import dataclass, field, replace

from .errors import AdmissionDenied, IdempotencyConflict
from .execution_model import (
    ExecutionContract, ExecutionIntent, ExecutionIntentView, ExecutionPermit,
    Reservation, ResourceClaim, ResourceDefinition, ResourceSnapshot, ResourceView,
)
from .model import Check, Status, conjunction, identity, logical_integer, nonempty
from .requirements import validate_requirement
from .resources import check_capacity


@dataclass
class ExecutionStore:
    resources: dict[str, ResourceDefinition] = field(default_factory=dict)
    contracts: dict[tuple[str, str], ExecutionContract] = field(default_factory=dict)
    permits: dict[str, ExecutionPermit] = field(default_factory=dict)
    intents: dict[str, ExecutionIntent] = field(default_factory=dict)  # keyed by attempt
    revision: int = 0
    logical_time: int = 0


class ExecutionMixin:
    EXECUTION_COMMANDS = frozenset((
        "register_resource", "register_execution_contract", "advance_resource_clock",
        "certify_execution", "reserve_and_record_intent", "cancel_execution_intent",
    ))

    def register_resource(self, resource: ResourceDefinition, *, idempotency_key: str) -> ResourceDefinition:
        if not isinstance(resource, ResourceDefinition):
            raise ValueError("a typed resource definition is required")
        if resource.mode != "renewable":
            raise AdmissionDenied(Status.UNKNOWN, "only renewable capacity is supported")

        def apply():
            previous = self._execution.resources.get(resource.resource_id)
            if previous is not None:
                if previous != resource:
                    raise IdempotencyConflict("resource definitions are immutable")
                return previous
            self._execution.resources[resource.resource_id] = resource
            self._execution.revision += 1
            return resource

        return self._mutate("register_resource", idempotency_key, dict(resource=resource), apply)

    def register_execution_contract(self, contract: ExecutionContract, *,
                                    idempotency_key: str) -> ExecutionContract:
        """Trusted promotion; callers cannot omit claims when reserving an intent."""
        if not isinstance(contract, ExecutionContract):
            raise ValueError("a typed execution contract is required")
        if validate_requirement(contract.requirements) is not Status.PASS:
            raise AdmissionDenied(Status.UNKNOWN, "unsupported execution requirements")

        def apply():
            schema = self._lifecycle.schemas[contract.schema_id, contract.schema_revision]
            edge = next((edge for edge in schema.edges if edge.edge_id == contract.edge_id), None)
            if edge is None or contract.executor_id not in edge.observation_sources:
                raise AdmissionDenied(Status.FAIL, "executor must match the pinned edge observation contract")
            for demand in contract.demands:
                resource = self._execution.resources.get(demand.resource_id)
                if resource is None:
                    raise AdmissionDenied(Status.UNKNOWN, "resource is not registered")
                if demand.unit != resource.unit:
                    raise AdmissionDenied(Status.FAIL, "resource unit mismatch")
            key = contract.contract_id, contract.revision
            previous = self._execution.contracts.get(key)
            if previous is not None and previous != contract:
                raise IdempotencyConflict("execution contract revisions are immutable")
            if previous is None:
                self._execution.contracts[key] = contract
                self._execution.revision += 1
            return contract

        return self._mutate("register_execution_contract", idempotency_key, dict(contract=contract), apply)

    def advance_resource_clock(self, logical_time: int, *, idempotency_key: str) -> int:
        logical_integer(logical_time)

        def apply():
            if logical_time < self._execution.logical_time:
                raise ValueError("resource clock cannot move backwards")
            if logical_time != self._execution.logical_time:
                self._execution.logical_time = logical_time
                self._execution.revision += 1
            return self._execution.revision

        return self._mutate("advance_resource_clock", idempotency_key, dict(logical_time=logical_time), apply)

    def _execution_observed(self, attempt_id: str) -> None:
        # Called inside the observation's existing journal transaction. Even a
        # subsequently revoked observation leaves remote occupancy unresolved.
        if attempt_id in self._execution.intents:
            self._execution.revision += 1

    def resource_snapshot(self) -> ResourceSnapshot:
        with self._lock:
            self._ensure_open()
            return ResourceSnapshot(self._execution.revision, self._execution.logical_time,
                tuple(self._execution.resources[key] for key in sorted(self._execution.resources)))

    def _intent_state(self, intent: ExecutionIntent) -> str:
        dispatched = self._dispatch_resource_state(intent.attempt_id)
        if dispatched is not None:
            return dispatched
        if self._lifecycle.attempts[intent.attempt_id].observations:
            return "reconciliation_required"
        if intent.state == "cancelled":
            return "cancelled"
        if self._execution.logical_time >= intent.lease_until:
            return "expired"
        return "pending"

    def inspect_resource(self, resource_id: str) -> ResourceView:
        with self._lock:
            self._ensure_open()
            resource = self._execution.resources[resource_id]
            reservations = []
            uncertain = set()
            for intent in self._execution.intents.values():
                state = self._intent_state(intent)
                for reservation in intent.reservations:
                    if reservation.claim.resource_id != resource_id:
                        continue
                    if state == "reconciliation_required":
                        uncertain.add(intent.attempt_id)
                    if state in ("pending", "reconciliation_required"):
                        reservations.append(reservation)
            reservations.sort(key=lambda item: item.reservation_id)
            now = self._execution.logical_time
            used = sum(item.claim.quantity for item in reservations
                       if item.claim.starts_at <= now < item.claim.ends_at)
            return ResourceView(resource, tuple(reservations), used, tuple(sorted(uncertain)),
                                self._execution.revision, now)

    def _resource_checks(self, claims: tuple[ResourceClaim, ...], *, exclude_attempt: str | None = None,
                         ignore_own_uncertainty: bool = False):
        checks = []
        for claim in claims:
            view = self.inspect_resource(claim.resource_id)
            uncertain = tuple(attempt for attempt in view.reconciliation_attempts
                              if not ignore_own_uncertainty or attempt != exclude_attempt)
            if uncertain:
                checks.append(Check("remote_occupancy", Status.UNKNOWN,
                                    f"{claim.resource_id} requires executor reconciliation"))
            others = tuple(reservation.claim for reservation in view.reservations
                           if reservation.attempt_id != exclude_attempt)
            checks.append(check_capacity(view.resource, (*others, claim)))
        return tuple(checks)

    def _execution_checks(self, attempt_id: str, contract: ExecutionContract, owner_id: str):
        operation = self._lifecycle.attempts[attempt_id]
        view = self.inspect_operation(attempt_id)
        action = self._evaluate_requirement(operation.context_id, contract.requirements)
        checks = (
            Check("clock_alignment", Status.PASS if self._contexts[operation.context_id].logical_time
                  == self._execution.logical_time else Status.STALE,
                  "evidence and resource clocks must describe the same logical tick"),
            Check("contract_binding", Status.PASS if (operation.schema_id, operation.schema_revision,
                  operation.edge_id) == (contract.schema_id, contract.schema_revision, contract.edge_id)
                  else Status.FAIL, "exact schema revision and edge"),
            Check("owner", Status.PASS if owner_id in contract.owners else Status.FAIL, "declared lease owner"),
            Check("selected", Status.PASS if operation.selected else Status.FAIL, "selected next operation"),
            Check("operation_readiness", view.readiness, "complete current lifecycle prerequisites"),
            Check("action_requirements", action.status, "separate execution contract requirements"),
            Check("undispatched_attempt", Status.PASS if not operation.observations else Status.FAIL,
                  "an observed attempt requires reconciliation, not a new intent"),
        )
        return checks, view.requirements, action

    def certify_execution(self, attempt_id: str, contract_id: str, contract_revision: str,
                          owner_id: str, expected_operation_revision: int,
                          expected_knowledge_revision: int, expected_resource_revision: int, *,
                          idempotency_key: str) -> ExecutionPermit:
        for revision in (expected_operation_revision, expected_knowledge_revision, expected_resource_revision):
            logical_integer(revision)
        nonempty(owner_id)

        def apply():
            operation = self._lifecycle.attempts[attempt_id]
            episode = self._lifecycle.episodes[operation.episode_id]
            context = self._contexts[operation.context_id]
            contract = self._execution.contracts[contract_id, contract_revision]
            checks, prerequisites, action = self._execution_checks(attempt_id, contract, owner_id)
            now = self._execution.logical_time
            until = now + contract.lease_duration
            claims = tuple(ResourceClaim(d.resource_id, d.quantity, d.unit, now, until) for d in contract.demands)
            checks = (
                Check("operation_revision", Status.PASS if expected_operation_revision == operation.revision
                      else Status.STALE, "exact operation revision"),
                Check("knowledge_revision", Status.PASS if expected_knowledge_revision == context.revision
                      else Status.STALE, "exact knowledge snapshot"),
                Check("resource_revision", Status.PASS if expected_resource_revision == self._execution.revision
                      else Status.STALE, "single shared resource authority"),
                Check("attempt_identity", Status.PASS if attempt_id not in self._execution.intents else Status.FAIL,
                      "one immutable intent identity per attempt"),
                *checks, *self._resource_checks(claims),
            )
            permit = ExecutionPermit(
                identity("execution-certificate/v1", (self._authority_id, len(self._execution.permits))),
                attempt_id, operation.context_id, owner_id, contract_id, contract_revision,
                context.revision, context.policy_revision, context.logical_time,
                self._lifecycle_revision(operation.context_id), operation.revision, episode.revision,
                self._execution.revision, now, until, claims, prerequisites, action, checks,
            )
            self._execution.permits[permit.certificate_id] = permit
            return permit

        return self._mutate("certify_execution", idempotency_key, dict(
            attempt_id=attempt_id, contract_id=contract_id, contract_revision=contract_revision,
            owner_id=owner_id, expected_operation_revision=expected_operation_revision,
            expected_knowledge_revision=expected_knowledge_revision,
            expected_resource_revision=expected_resource_revision), apply)

    def reserve_and_record_intent(self, permit: ExecutionPermit, *, idempotency_key: str) -> ExecutionIntent:
        if not isinstance(permit, ExecutionPermit):
            raise ValueError("a typed execution certificate is required")

        def apply():
            if self._execution.permits.get(permit.certificate_id) != permit:
                raise AdmissionDenied(Status.FAIL, "untrusted or altered execution certificate")
            previous = self._execution.intents.get(permit.attempt_id)
            if previous is not None:
                if previous.certificate_id != permit.certificate_id:
                    raise IdempotencyConflict("attempt already has an execution intent")
                return previous  # Historical result; inspect for current status.
            operation = self._lifecycle.attempts[permit.attempt_id]
            episode = self._lifecycle.episodes[operation.episode_id]
            context = self._contexts[operation.context_id]
            if (permit.knowledge_revision != context.revision or permit.policy_revision != context.policy_revision
                    or permit.logical_time != context.logical_time or permit.operation_revision != operation.revision
                    or permit.episode_revision != episode.revision
                    or permit.lifecycle_revision != self._lifecycle_revision(operation.context_id)
                    or permit.resource_revision != self._execution.revision
                    or permit.resource_time != self._execution.logical_time):
                raise AdmissionDenied(Status.STALE, "execution certificate dependencies changed")
            if permit.status is not Status.PASS:
                raise AdmissionDenied(permit.status, "execution contract did not pass")
            contract = self._execution.contracts[permit.contract_id, permit.contract_revision]
            checks, prerequisites, action = self._execution_checks(permit.attempt_id, contract, permit.owner_id)
            checks += self._resource_checks(permit.claims)
            if conjunction(checks) is not Status.PASS or (prerequisites, action) != (
                    permit.prerequisites, permit.action_requirements):
                raise AdmissionDenied(Status.STALE, "execution contract replay changed")
            intent_id = identity("execution-intent/v1", (self._authority_id, permit.attempt_id))
            reservations = tuple(Reservation(identity("reservation/v1", (intent_id, claim.resource_id)),
                intent_id, permit.attempt_id, permit.owner_id, claim) for claim in permit.claims)
            intent = ExecutionIntent(intent_id, permit.attempt_id, operation.context_id, permit.owner_id,
                contract.executor_id, operation.product_id, contract.contract_id, contract.revision,
                permit.certificate_id, permit.resource_time, permit.lease_until, reservations)
            # All checks precede the only mutation; volatile mode is atomic too.
            self._execution.intents[permit.attempt_id] = intent
            self._execution.revision += 1
            return intent

        return self._mutate("reserve_and_record_intent", idempotency_key, dict(permit=permit), apply)

    def inspect_execution_intent(self, attempt_id: str) -> ExecutionIntentView:
        with self._lock:
            self._ensure_open()
            intent = self._execution.intents[attempt_id]
            contract = self._execution.contracts[intent.contract_id, intent.contract_revision]
            state = self._intent_state(intent)
            checks, _, _ = self._execution_checks(attempt_id, contract, intent.owner_id)
            checks = (Check("lease", Status.PASS if state == "pending" else Status.STALE,
                            f"local intent is {state}"), *checks,
                      *self._resource_checks(tuple(r.claim for r in intent.reservations), exclude_attempt=attempt_id))
            return ExecutionIntentView(intent, state, conjunction(checks), checks,
                                       self._execution.revision, self._execution.logical_time)

    def cancel_execution_intent(self, attempt_id: str, owner_id: str, expected_revision: int, *,
                                idempotency_key: str) -> ExecutionIntent:
        logical_integer(expected_revision)

        def apply():
            intent = self._execution.intents[attempt_id]
            if intent.owner_id != owner_id:
                raise AdmissionDenied(Status.FAIL, "only the recorded owner can cancel the local lease")
            if expected_revision != intent.revision:
                raise AdmissionDenied(Status.STALE, "intent revision changed")
            if attempt_id in self._dispatch.attempts:
                raise AdmissionDenied(Status.UNKNOWN, "submitted attempts require executor release/reconciliation")
            if self._intent_state(intent) == "reconciliation_required":
                raise AdmissionDenied(Status.UNKNOWN, "remote occupancy requires explicit reconciliation")
            if intent.state == "cancelled":
                return intent
            updated = replace(intent, state="cancelled", revision=intent.revision + 1,
                              closed_at=self._execution.logical_time)
            self._execution.intents[attempt_id] = updated
            self._execution.revision += 1
            return updated

        return self._mutate("cancel_execution_intent", idempotency_key, dict(
            attempt_id=attempt_id, owner_id=owner_id, expected_revision=expected_revision), apply)
