"""Explicit lifecycle completion contract using historical submission witnesses.

This finite policy separates submission requirements from current completion
requirements. It does not implement general temporal logic or causal credit.
"""
from dataclasses import dataclass, field, replace

from .errors import AdmissionDenied, IdempotencyConflict
from .lifecycle_model import LifecycleEvent
from .model import Check, Status, conjunction, identity, logical_integer, nonempty
from .requirements import Requirement, RequirementResult, validate_requirement


@dataclass(frozen=True, slots=True)
class CompletionContract:
    contract_id: str
    revision: str
    schema_id: str
    schema_revision: str
    edge_id: str
    goal_contract_id: str
    goal_contract_revision: str
    requirements: Requirement = Requirement("ALWAYS")

    def __post_init__(self):
        for value in (self.contract_id, self.revision, self.schema_id, self.schema_revision,
                      self.edge_id, self.goal_contract_id, self.goal_contract_revision):
            nonempty(value)
        if not isinstance(self.requirements, Requirement):
            raise ValueError("completion requirements must be typed")


@dataclass(frozen=True, slots=True)
class CompletionPermit:
    certificate_id: str
    contract_id: str
    contract_revision: str
    attempt_id: str
    goal_id: str
    episode_id: str
    edge_id: str
    episode_revision: int
    knowledge_revision: int
    lifecycle_revision: int
    resource_revision: int
    logical_time: int
    goal_fingerprint: str
    checks: tuple[Check, ...]
    prerequisites: RequirementResult
    outcome: RequirementResult
    target_validity: RequirementResult
    completion_requirements: RequirementResult

    @property
    def status(self):
        return conjunction(self.checks)


@dataclass
class CompletionStore:
    contracts: dict[tuple[str, str], CompletionContract] = field(default_factory=dict)
    permits: dict[str, CompletionPermit] = field(default_factory=dict)


class CompletionMixin:
    COMPLETION_COMMANDS = frozenset(("register_completion_contract", "certify_goal_completion", "advance_goal_completion"))

    def register_completion_contract(self, contract: CompletionContract, *, idempotency_key: str) -> CompletionContract:
        if not isinstance(contract, CompletionContract):
            raise ValueError("a typed completion contract is required")
        if validate_requirement(contract.requirements) is not Status.PASS:
            raise AdmissionDenied(Status.UNKNOWN, "unsupported completion requirements")

        def apply():
            schema = self._lifecycle.schemas[contract.schema_id, contract.schema_revision]
            edge = next(edge for edge in schema.edges if edge.edge_id == contract.edge_id)
            goal = self._goals.contracts[contract.goal_contract_id, contract.goal_contract_revision]
            if any(item.product_id != edge.product_id for item in goal.slices):
                raise AdmissionDenied(Status.FAIL, "all completion slices must concern the edge's exact product")
            key = contract.contract_id, contract.revision
            previous = self._completion.contracts.get(key)
            if previous is not None and previous != contract:
                raise IdempotencyConflict("completion contract revisions are immutable")
            self._completion.contracts[key] = contract
            return contract

        return self._mutate("register_completion_contract", idempotency_key, dict(contract=contract), apply)

    def _completion_checks(self, contract, attempt_id, goal_id):
        operation = self._lifecycle.attempts[attempt_id]
        episode = self._lifecycle.episodes[operation.episode_id]
        edge = self._edge(episode, operation.edge_id)
        goal = self._goals.goals[goal_id]
        projection = self._project_goal(goal_id)
        dispatch = self.inspect_dispatch(attempt_id)
        context = self._contexts[operation.context_id]
        current = self.inspect_operation(attempt_id)
        outcome = current.outcome
        target = self._evaluate_requirement(operation.context_id, self._state_requirement(episode, edge.target))
        extra = self._evaluate_requirement(operation.context_id, contract.requirements)
        milestones = {observation.milestone for observation in operation.observations
                      if observation.belief_revision_id in context.usable
                      and observation.observed_at > dispatch.dispatch.prepared_at}
        checks = (
            Check("binding", Status.PASS if (
                operation.schema_id, operation.schema_revision, operation.edge_id,
                goal.contract_id, goal.contract_revision, goal.context_id) == (
                contract.schema_id, contract.schema_revision, contract.edge_id,
                contract.goal_contract_id, contract.goal_contract_revision, operation.context_id) else Status.FAIL,
                "exact lifecycle, product goal and context binding"),
            Check("stage", Status.PASS if episode.stage == edge.source else Status.FAIL, "historical source stage"),
            Check("clock_alignment", Status.PASS if context.logical_time == self._execution.logical_time else Status.STALE,
                  "completion evidence and resource time describe one logical tick"),
            Check("submission", conjunction(dispatch.dispatch.checks), "registered historical submission checks"),
            Check("executor_effect", Status.PASS if dispatch.state in ("accepted", "released")
                  and dispatch.latest_receipt.effect_count > 0 else Status.UNKNOWN, "authoritative attempt acceptance"),
            Check("completion_observations", Status.PASS if {"completion_observed", "exact_product_observed"}
                  <= milestones else Status.UNKNOWN, "exact current attempt/product observations strictly after submission"),
            Check("operation_outcome", current.outcome_status, "current declared operation outcome"),
            Check("goal_durability", Status.PASS if projection.outstanding_loss == 0 else Status.UNKNOWN,
                  "all declared goal slices have supported observed success"),
            Check("sample_timing", Status.PASS if all(view.samples and all(sample.observed_at
                  > dispatch.dispatch.prepared_at for sample in view.samples) for view in projection.slices)
                  else Status.UNKNOWN, "preexisting or same-tick samples cannot complete a submitted action"),
            Check("completion_requirements", extra.status, "current completion-specific policy requirements"),
            Check("target_validity", target.status, "current target-state validity"),
        )
        return checks, dispatch.dispatch.prerequisites, outcome, target, extra, projection

    def certify_goal_completion(self, contract_id: str, contract_revision: str, attempt_id: str,
                                goal_id: str, expected_episode_revision: int, expected_knowledge_revision: int, *,
                                idempotency_key: str) -> CompletionPermit:
        logical_integer(expected_episode_revision)
        logical_integer(expected_knowledge_revision)

        def apply():
            contract = self._completion.contracts[contract_id, contract_revision]
            operation = self._lifecycle.attempts[attempt_id]
            episode = self._lifecycle.episodes[operation.episode_id]
            context = self._contexts[operation.context_id]
            checks, prerequisites, outcome, target, extra, projection = self._completion_checks(contract, attempt_id, goal_id)
            checks = (Check("episode_revision", Status.PASS if expected_episode_revision == episode.revision else Status.STALE, ""),
                      Check("knowledge_revision", Status.PASS if expected_knowledge_revision == context.revision else Status.STALE, ""), *checks)
            permit = CompletionPermit(identity("goal-completion-certificate/v1", (self._authority_id, len(self._completion.permits))),
                contract_id, contract_revision, attempt_id, goal_id, episode.episode_id, operation.edge_id, episode.revision,
                context.revision, self._lifecycle_revision(operation.context_id), self._execution.revision, context.logical_time,
                projection.fingerprint, checks, prerequisites, outcome, target, extra)
            self._completion.permits[permit.certificate_id] = permit
            return permit

        return self._mutate("certify_goal_completion", idempotency_key, dict(contract_id=contract_id,
            contract_revision=contract_revision, attempt_id=attempt_id, goal_id=goal_id,
            expected_episode_revision=expected_episode_revision, expected_knowledge_revision=expected_knowledge_revision), apply)

    def advance_goal_completion(self, permit: CompletionPermit, expected_episode_revision: int, *, idempotency_key: str):
        logical_integer(expected_episode_revision)
        if not isinstance(permit, CompletionPermit):
            raise ValueError("a typed completion permit is required")

        def apply():
            if self._completion.permits.get(permit.certificate_id) != permit:
                raise AdmissionDenied(Status.FAIL, "untrusted or altered completion certificate")
            episode = self._lifecycle.episodes[permit.episode_id]
            context = self._contexts[episode.context_id]
            if (episode.revision != expected_episode_revision or episode.revision != permit.episode_revision
                    or context.revision != permit.knowledge_revision or context.logical_time != permit.logical_time
                    or self._execution.revision != permit.resource_revision
                    or self._lifecycle_revision(episode.context_id) != permit.lifecycle_revision
                    or self._project_goal(permit.goal_id).fingerprint != permit.goal_fingerprint):
                raise AdmissionDenied(Status.STALE, "completion dependencies changed")
            if permit.status is not Status.PASS:
                raise AdmissionDenied(permit.status, "completion contract did not pass")
            contract = self._completion.contracts[permit.contract_id, permit.contract_revision]
            checks, prerequisites, outcome, target, extra, _ = self._completion_checks(contract, permit.attempt_id, permit.goal_id)
            if conjunction(checks) is not Status.PASS or (prerequisites, outcome, target, extra) != (
                    permit.prerequisites, permit.outcome, permit.target_validity, permit.completion_requirements):
                raise AdmissionDenied(Status.STALE, "completion contract replay changed")
            edge = self._edge(episode, permit.edge_id)
            event = LifecycleEvent(identity("goal-completion-event/v1", permit.certificate_id), edge.edge_id,
                episode.stage, edge.target, context.logical_time, permit.certificate_id, permit.attempt_id,
                prerequisites, outcome, target)
            updated = replace(episode, stage=edge.target, revision=episode.revision + 1, events=(*episode.events, event))
            self._lifecycle.episodes[episode.episode_id] = updated
            self._lifecycle_changed(episode.context_id)
            return updated

        return self._mutate("advance_goal_completion", idempotency_key,
                            dict(permit=permit, expected_episode_revision=expected_episode_revision), apply)
