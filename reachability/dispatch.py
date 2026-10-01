"""Durable submission boundary; journal replay never invokes an executor."""
from dataclasses import dataclass, field, replace
from typing import Protocol

from .dispatch_model import (
    DispatchAttempt, DispatchPolicy, DispatchRequest, DispatchView, ExecutorProfile, ExecutorReceipt,
)
from .errors import AdmissionDenied, IdempotencyConflict
from .model import Check, Status, conjunction, identity


@dataclass
class DispatchStore:
    policies: dict[tuple[str, str], DispatchPolicy] = field(default_factory=dict)
    attempts: dict[str, DispatchAttempt] = field(default_factory=dict)


class DispatchMixin:
    DISPATCH_COMMANDS = frozenset(("register_dispatch_policy", "prepare_dispatch", "record_dispatch_receipt"))

    def register_dispatch_policy(self, policy: DispatchPolicy, *, idempotency_key: str) -> DispatchPolicy:
        if not isinstance(policy, DispatchPolicy):
            raise ValueError("a typed dispatch policy is required")

        def apply():
            contract = self._execution.contracts[policy.contract_id, policy.contract_revision]
            if contract.executor_id != policy.executor.executor_id:
                raise AdmissionDenied(Status.FAIL, "executor identity differs from the execution contract")
            key = policy.policy_id, policy.revision
            previous = self._dispatch.policies.get(key)
            if previous is not None and previous != policy:
                raise IdempotencyConflict("dispatch policy revisions are immutable")
            self._dispatch.policies[key] = policy
            return policy

        return self._mutate("register_dispatch_policy", idempotency_key, dict(policy=policy), apply)

    def _dispatch_submission_checks(self, attempt_id: str):
        intent = self._execution.intents[attempt_id]
        contract = self._execution.contracts[intent.contract_id, intent.contract_revision]
        checks, prerequisites, action = self._execution_checks(attempt_id, contract, intent.owner_id)
        checks = (Check("local_lease", Status.PASS if intent.state == "pending"
                        and self._execution.logical_time < intent.lease_until else Status.STALE,
                        "submission requires a live local lease"), *checks,
                  *self._resource_checks(tuple(r.claim for r in intent.reservations),
                                         exclude_attempt=attempt_id, ignore_own_uncertainty=True))
        return checks, prerequisites, action

    def prepare_dispatch(self, attempt_id: str, policy_id: str, policy_revision: str,
                         owner_id: str, *, idempotency_key: str) -> DispatchAttempt:
        """Persist uncertainty before I/O. Returning this record never sends a request."""
        if self._journal is None:
            raise AdmissionDenied(Status.FAIL, "dispatch requires durable intent storage")

        def apply():
            intent = self._execution.intents[attempt_id]
            policy = self._dispatch.policies[policy_id, policy_revision]
            if intent.owner_id != owner_id or (intent.contract_id, intent.contract_revision) != (
                    policy.contract_id, policy.contract_revision):
                raise AdmissionDenied(Status.FAIL, "dispatch owner or pinned contract mismatch")
            previous = self._dispatch.attempts.get(attempt_id)
            if previous is not None:
                if previous.policy != policy:
                    raise IdempotencyConflict("a dispatched attempt cannot change executor policy")
                return previous
            checks, prerequisites, action = self._dispatch_submission_checks(attempt_id)
            if conjunction(checks) is not Status.PASS:
                raise AdmissionDenied(conjunction(checks), "current submission gates did not pass")
            context = self._contexts[intent.context_id]
            request = DispatchRequest(identity("dispatch-request/v1", intent.intent_id), intent)
            record = DispatchAttempt(request, policy, self._execution.logical_time, context.revision,
                context.policy_revision, self._lifecycle_revision(intent.context_id), self._execution.revision,
                prerequisites, action, checks)
            self._dispatch.attempts[attempt_id] = record
            self._execution.revision += 1
            return record

        return self._mutate("prepare_dispatch", idempotency_key, dict(attempt_id=attempt_id,
            policy_id=policy_id, policy_revision=policy_revision, owner_id=owner_id), apply)

    def inspect_dispatch(self, attempt_id: str) -> DispatchView:
        with self._lock:
            self._ensure_open()
            record = self._dispatch.attempts[attempt_id]
            known = tuple(receipt for receipt in record.receipts if receipt.state != "unknown")
            latest = max(known, key=lambda receipt: receipt.sequence) if known else None
            state = latest.state if latest is not None and latest.state in ("accepted", "released") else "uncertain"
            return DispatchView(record, state, latest, state == "released")

    def _dispatch_resource_state(self, attempt_id: str) -> str | None:
        if attempt_id not in self._dispatch.attempts:
            return None
        return "released" if self.inspect_dispatch(attempt_id).resources_released else "reconciliation_required"

    def record_dispatch_receipt(self, attempt_id: str, source: str, receipt: ExecutorReceipt, *,
                                idempotency_key: str) -> DispatchAttempt:
        if not isinstance(receipt, ExecutorReceipt) or source not in ("submission", "query", "release"):
            raise ValueError("a typed executor receipt and supported source are required")

        def apply():
            record = self._dispatch.attempts[attempt_id]
            request, profile = record.request, record.policy.executor
            if (receipt.executor_id, receipt.instance_id, receipt.request_id, receipt.request_fingerprint) != (
                    profile.executor_id, profile.instance_id, request.request_id, request.fingerprint):
                raise AdmissionDenied(Status.FAIL, "receipt does not match the pinned executor and exact request")
            if (source == "query" and not profile.supports_query and receipt.state != "unknown"
                    or source == "release" and receipt.state != "released"
                    or receipt.state == "released" and not profile.supports_release
                    or receipt.state == "absent" and source != "query"
                    or profile.supports_idempotency and receipt.effect_count > 1):
                raise AdmissionDenied(Status.FAIL, "receipt exceeds the executor capability contract")
            if receipt in record.receipts:
                return record
            known = self.inspect_dispatch(attempt_id).latest_receipt
            if receipt.state != "unknown" and known is not None:
                if any(old.state != "unknown" and old.sequence == receipt.sequence and old != receipt
                       for old in record.receipts):
                    raise AdmissionDenied(Status.FAIL, "conflicting executor receipts at one revision")
                if receipt.sequence > known.sequence and (
                        known.fenced and not receipt.fenced or receipt.effect_count < known.effect_count):
                    raise AdmissionDenied(Status.FAIL, "executor receipt violates monotone effects or permanent release")
            updated = replace(record, receipts=(*record.receipts, receipt))
            self._dispatch.attempts[attempt_id] = updated
            self._execution.revision += 1
            return updated

        return self._mutate("record_dispatch_receipt", idempotency_key,
                            dict(attempt_id=attempt_id, source=source, receipt=receipt), apply)


class Executor(Protocol):
    @property
    def profile(self) -> ExecutorProfile: ...
    def submit(self, request: DispatchRequest) -> ExecutorReceipt: ...
    def query(self, request: DispatchRequest) -> ExecutorReceipt: ...
    def release(self, request: DispatchRequest) -> ExecutorReceipt: ...


class Dispatcher:
    """Synchronous trusted adapter boundary, serialized with admission changes.

    Calls are deliberately outside replayable mutations. The reference service
    lock spans gate checking and simulator I/O; a real transport needs its own
    authenticated, bounded-time protocol before replacing this local adapter.
    """

    def __init__(self, service, executor: Executor):
        self.service = service
        self.executor = executor

    def _bound(self, record: DispatchAttempt, owner_id: str) -> None:
        if record.request.intent.owner_id != owner_id or record.policy.executor != self.executor.profile:
            raise AdmissionDenied(Status.FAIL, "owner or executor instance/capabilities do not match")

    def _observe(self, attempt_id: str, source: str, receipt: ExecutorReceipt) -> DispatchView:
        self.service.record_dispatch_receipt(attempt_id, source, receipt,
            idempotency_key=identity("dispatch-observation/v1", (attempt_id, source, receipt.receipt_id)))
        return self.service.inspect_dispatch(attempt_id)

    def dispatch(self, attempt_id: str, policy_id: str, policy_revision: str, owner_id: str) -> DispatchView:
        service = self.service
        with service._lock:
            service._ensure_open()
            policy = service._dispatch.policies[policy_id, policy_revision]
            if policy.executor != self.executor.profile:
                raise AdmissionDenied(Status.FAIL, "executor instance/capabilities do not match policy")
            fresh = attempt_id not in service._dispatch.attempts
            record = service.prepare_dispatch(attempt_id, policy_id, policy_revision, owner_id,
                idempotency_key=identity("dispatch-prepare/v1", (attempt_id, policy_id, policy_revision, owner_id)))
            self._bound(record, owner_id)
            if not fresh:
                view = self.reconcile(attempt_id, owner_id)
                if view.state in ("accepted", "released") or not record.policy.executor.supports_idempotency:
                    return view
            checks, _, _ = service._dispatch_submission_checks(attempt_id)
            if conjunction(checks) is not Status.PASS:
                raise AdmissionDenied(conjunction(checks), "current submission gates did not pass")
            try:
                receipt = self.executor.submit(record.request)
            except OSError:
                # The durable marker already records uncertainty. Never assume
                # a transport exception means no effect took place.
                return service.inspect_dispatch(attempt_id)
            return self._observe(attempt_id, "submission", receipt)

    def reconcile(self, attempt_id: str, owner_id: str) -> DispatchView:
        service = self.service
        with service._lock:
            service._ensure_open()
            view = service.inspect_dispatch(attempt_id)
            self._bound(view.dispatch, owner_id)
            if view.resources_released or not view.dispatch.policy.executor.supports_query:
                return view
            try:
                receipt = self.executor.query(view.dispatch.request)
            except OSError:
                return view
            return self._observe(attempt_id, "query", receipt)

    def release(self, attempt_id: str, owner_id: str) -> DispatchView:
        service = self.service
        with service._lock:
            service._ensure_open()
            view = service.inspect_dispatch(attempt_id)
            self._bound(view.dispatch, owner_id)
            if view.resources_released:
                return view
            if not view.dispatch.policy.executor.supports_release:
                raise AdmissionDenied(Status.UNKNOWN, "executor has no authoritative release and fencing contract")
            try:
                receipt = self.executor.release(view.dispatch.request)
            except OSError:
                return view
            return self._observe(attempt_id, "release", receipt)
