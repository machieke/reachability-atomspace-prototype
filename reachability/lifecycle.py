"""Lifecycle and passive operation ledger sharing the admission transaction boundary.

The mixin uses AdmissionService's lock, snapshots, idempotency and journal. It
does not dispatch actions, allocate resources or declare goal relief.
"""
from dataclasses import dataclass, field, replace

from .errors import AdmissionDenied, IdempotencyConflict
from .lifecycle_model import (
    LifecycleEpisode, LifecycleEvent, LifecyclePermit, LifecycleSchema, LifecycleView,
    OperationEpisode, OperationObservation, OperationView, milestone_literal,
)
from .model import Check, Status, conjunction, identity, logical_integer, nonempty
from .requirements import Requirement, RequirementResult, evaluate


@dataclass
class LifecycleStore:
    schemas: dict[tuple[str, str], LifecycleSchema] = field(default_factory=dict)
    episodes: dict[str, LifecycleEpisode] = field(default_factory=dict)
    permits: dict[str, LifecyclePermit] = field(default_factory=dict)
    attempts: dict[str, OperationEpisode] = field(default_factory=dict)
    operation_bindings: dict[str, tuple[str, str]] = field(default_factory=dict)
    observations: dict[str, OperationObservation] = field(default_factory=dict)
    revisions: dict[str, int] = field(default_factory=dict)


class LifecycleMixin:
    LIFECYCLE_COMMANDS = frozenset((
        "register_lifecycle_schema", "open_lifecycle_episode", "certify_lifecycle_transition",
        "advance_lifecycle", "propose_operation", "select_operation", "record_operation_observation",
    ))

    def _lifecycle_revision(self, context_id: str) -> int:
        return self._lifecycle.revisions.get(context_id, 0)

    def _lifecycle_changed(self, context_id: str) -> None:
        self._lifecycle.revisions[context_id] = self._lifecycle_revision(context_id) + 1

    def _schema(self, episode: LifecycleEpisode) -> LifecycleSchema:
        return self._lifecycle.schemas[episode.schema_id, episode.schema_revision]

    def _edge(self, episode: LifecycleEpisode, edge_id: str):
        for edge in self._schema(episode).edges:
            if edge.edge_id == edge_id:
                return edge
        raise KeyError(f"unknown lifecycle edge: {edge_id}")

    def _state_requirement(self, episode: LifecycleEpisode, state: str) -> Requirement:
        return next(s.validity for s in self._schema(episode).states if s.name == state)

    def _evaluate_requirement(self, context_id: str, requirement: Requirement) -> RequirementResult:
        return evaluate(requirement, self.snapshot(context_id), max_variables=self._max_variables)

    def inspect_requirements(self, context_id: str, requirement: Requirement) -> RequirementResult:
        with self._lock:
            self._ensure_open()
            return self._evaluate_requirement(context_id, requirement)

    def register_lifecycle_schema(self, schema: LifecycleSchema, *, idempotency_key: str) -> LifecycleSchema:
        """Trusted promotion of a fully checked grounded schema revision."""
        if not isinstance(schema, LifecycleSchema):
            raise ValueError("a typed lifecycle schema is required")
        if not schema.supported():
            raise AdmissionDenied(Status.UNKNOWN, "schema exceeds supported requirements or lacks outcome evidence")

        def apply():
            key = schema.schema_id, schema.revision
            previous = self._lifecycle.schemas.get(key)
            if previous is not None and previous != schema:
                raise IdempotencyConflict("lifecycle schema revisions are immutable")
            self._lifecycle.schemas[key] = schema
            return schema

        return self._mutate("register_lifecycle_schema", idempotency_key, dict(schema=schema), apply)

    def open_lifecycle_episode(self, episode_id: str, context_id: str, schema_id: str,
                               schema_revision: str, *, idempotency_key: str) -> LifecycleEpisode:
        for value in (episode_id, context_id, schema_id, schema_revision):
            nonempty(value)

        def apply():
            context = self._contexts[context_id]
            schema = self._lifecycle.schemas[schema_id, schema_revision]
            previous = self._lifecycle.episodes.get(episode_id)
            if previous is not None:
                if (previous.context_id, previous.schema_id, previous.schema_revision) != (
                    context_id, schema_id, schema_revision
                ):
                    raise IdempotencyConflict("episode identity cannot be rebound")
                return previous
            validity = next(state.validity for state in schema.states if state.name == schema.initial_state)
            result = self._evaluate_requirement(context_id, validity)
            if result.status is not Status.PASS:
                raise AdmissionDenied(result.status, "initial state has no current validity witness")
            episode = LifecycleEpisode(episode_id, context_id, schema_id, schema_revision,
                                       schema.entity_id, schema.initial_state, 0,
                                       context.logical_time, result)
            self._lifecycle.episodes[episode_id] = episode
            self._lifecycle_changed(context_id)
            return episode

        return self._mutate("open_lifecycle_episode", idempotency_key, dict(
            episode_id=episode_id, context_id=context_id, schema_id=schema_id,
            schema_revision=schema_revision), apply)

    def inspect_lifecycle(self, episode_id: str) -> LifecycleView:
        with self._lock:
            self._ensure_open()
            episode = self._lifecycle.episodes[episode_id]
            result = self._evaluate_requirement(episode.context_id,
                                                self._state_requirement(episode, episode.stage))
            # History was supported when recorded. Lack of present support makes
            # that judgment stale without rewriting the stage or old events.
            validity = Status.STALE if result.status is Status.UNKNOWN else result.status
            return LifecycleView(episode, validity, result, self._lifecycle_revision(episode.context_id))

    def _transition_contract(self, episode: LifecycleEpisode, edge_id: str, attempt_id: str | None):
        edge = self._edge(episode, edge_id)
        source = self.inspect_lifecycle(episode.episode_id)
        prerequisites = self._evaluate_requirement(episode.context_id, edge.requirements)
        outcome = self._evaluate_requirement(episode.context_id, edge.outcome)
        target = self._evaluate_requirement(episode.context_id, self._state_requirement(episode, edge.target))
        checks = [
            Check("source_stage", Status.PASS if episode.stage == edge.source else Status.FAIL,
                  "edge must leave the current historical stage"),
            Check("source_validity", Status.PASS if edge.kind in ("recovery", "regression")
                  else source.validity, "recovery edges may explicitly leave an invalid state"),
            Check("requirements", prerequisites.status, "complete grounded requirement expression"),
            Check("observed_outcome", outcome.status, "outcome evidence is separate from readiness"),
            Check("target_validity", target.status, "current target-state support"),
        ]
        if attempt_id is not None:
            operation = self._lifecycle.attempts.get(attempt_id)
            if operation is None:
                status = Status.UNKNOWN
            elif (operation.episode_id, operation.edge_id) != (episode.episode_id, edge_id):
                status = Status.FAIL
            else:
                status = self.inspect_operation(attempt_id).outcome_status
            checks.append(Check("operation_outcome", status, "exact attempt, product and observed completion"))
        return tuple(checks), prerequisites, outcome, target

    def certify_lifecycle_transition(
        self, episode_id: str, edge_id: str, expected_episode_revision: int,
        expected_knowledge_revision: int, *, attempt_id: str | None = None, idempotency_key: str,
    ) -> LifecyclePermit:
        logical_integer(expected_episode_revision)
        logical_integer(expected_knowledge_revision)

        def apply():
            episode = self._lifecycle.episodes[episode_id]
            context = self._contexts[episode.context_id]
            checks, prerequisites, outcome, target = self._transition_contract(episode, edge_id, attempt_id)
            checks = (
                Check("episode_revision", Status.PASS if expected_episode_revision == episode.revision
                      else Status.STALE, "exact lifecycle episode revision"),
                Check("knowledge_revision", Status.PASS if expected_knowledge_revision == context.revision
                      else Status.STALE, "exact belief and policy snapshot"), *checks,
            )
            permit = LifecyclePermit(
                identity("lifecycle-certificate/v1", (self._authority_id, len(self._lifecycle.permits))),
                identity("lifecycle-transition/v1", (episode_id, episode.revision, edge_id, attempt_id)),
                episode_id, edge_id, attempt_id, episode.context_id, context.revision,
                self._lifecycle_revision(episode.context_id), episode.revision, episode.schema_revision,
                context.policy_revision, context.logical_time, checks, prerequisites, outcome, target,
            )
            self._lifecycle.permits[permit.certificate_id] = permit
            return permit

        return self._mutate("certify_lifecycle_transition", idempotency_key, dict(
            episode_id=episode_id, edge_id=edge_id, expected_episode_revision=expected_episode_revision,
            expected_knowledge_revision=expected_knowledge_revision, attempt_id=attempt_id), apply)

    def advance_lifecycle(self, permit: LifecyclePermit, expected_revision: int, *,
                          idempotency_key: str) -> LifecycleEpisode:
        logical_integer(expected_revision)

        def apply():
            if self._lifecycle.permits.get(permit.certificate_id) != permit:
                raise AdmissionDenied(Status.FAIL, "untrusted or altered lifecycle certificate")
            episode = self._lifecycle.episodes[permit.episode_id]
            context = self._contexts[episode.context_id]
            if (expected_revision != episode.revision or permit.episode_revision != episode.revision
                    or permit.knowledge_revision != context.revision
                    or permit.lifecycle_revision != self._lifecycle_revision(episode.context_id)
                    or permit.policy_revision != context.policy_revision
                    or permit.logical_time != context.logical_time):
                raise AdmissionDenied(Status.STALE, "lifecycle certificate dependencies changed")
            if permit.status is not Status.PASS:
                raise AdmissionDenied(permit.status, "lifecycle contract did not pass")
            checks, prerequisites, outcome, target = self._transition_contract(
                episode, permit.edge_id, permit.attempt_id)
            if conjunction(checks) is not Status.PASS or (prerequisites, outcome, target) != (
                permit.prerequisites, permit.outcome, permit.target_validity
            ):
                raise AdmissionDenied(Status.STALE, "lifecycle contract replay changed")
            edge = self._edge(episode, permit.edge_id)
            event = LifecycleEvent(identity("lifecycle-event/v1", permit.certificate_id), edge.edge_id,
                                   episode.stage, edge.target, context.logical_time, permit.certificate_id,
                                   permit.attempt_id, prerequisites, outcome, target)
            updated = replace(episode, stage=edge.target, revision=episode.revision + 1,
                              events=episode.events + (event,))
            self._lifecycle.episodes[episode.episode_id] = updated
            self._lifecycle_changed(episode.context_id)
            return updated

        return self._mutate("advance_lifecycle", idempotency_key,
                            dict(permit=permit, expected_revision=expected_revision), apply)

    def propose_operation(self, operation_id: str, attempt_id: str, episode_id: str,
                           edge_id: str, *, idempotency_key: str) -> OperationEpisode:
        for value in (operation_id, attempt_id, episode_id, edge_id):
            nonempty(value)

        def apply():
            episode = self._lifecycle.episodes[episode_id]
            edge = self._edge(episode, edge_id)
            binding = (episode_id, edge_id)
            prior_binding = self._lifecycle.operation_bindings.get(operation_id)
            if prior_binding is not None and prior_binding != binding:
                raise IdempotencyConflict("operation identity cannot change its target")
            previous = self._lifecycle.attempts.get(attempt_id)
            if previous is not None:
                if (previous.operation_id, previous.episode_id, previous.edge_id) != (operation_id, *binding):
                    raise IdempotencyConflict("attempt identity cannot be rebound")
                return previous
            operation = OperationEpisode(operation_id, attempt_id, episode_id, edge_id, episode.context_id,
                                         episode.schema_id, episode.schema_revision, edge.product_id,
                                         self._contexts[episode.context_id].logical_time)
            self._lifecycle.operation_bindings[operation_id] = binding
            self._lifecycle.attempts[attempt_id] = operation
            self._lifecycle_changed(episode.context_id)
            return operation

        return self._mutate("propose_operation", idempotency_key, dict(
            operation_id=operation_id, attempt_id=attempt_id, episode_id=episode_id, edge_id=edge_id), apply)

    def select_operation(self, attempt_id: str, expected_revision: int, *,
                         idempotency_key: str) -> OperationEpisode:
        """Planning selection only; it is not external execution authorization."""
        logical_integer(expected_revision)

        def apply():
            operation = self._lifecycle.attempts[attempt_id]
            if operation.revision != expected_revision:
                raise AdmissionDenied(Status.STALE, "operation revision changed")
            if operation.selected:
                return operation
            updated = replace(operation, selected=True, selected_at=self._contexts[operation.context_id].logical_time,
                              revision=operation.revision + 1)
            self._lifecycle.attempts[attempt_id] = updated
            self._lifecycle_changed(operation.context_id)
            return updated

        return self._mutate("select_operation", idempotency_key,
                            dict(attempt_id=attempt_id, expected_revision=expected_revision), apply)

    def record_operation_observation(self, observation_id: str, attempt_id: str,
                                      milestone: str, belief_revision_id: str, *,
                                      idempotency_key: str) -> OperationObservation:
        nonempty(observation_id)

        def apply():
            operation = self._lifecycle.attempts[attempt_id]
            expected = milestone_literal(attempt_id, operation.product_id, milestone)
            context = self._contexts[operation.context_id]
            previous = self._lifecycle.observations.get(observation_id)
            if previous is not None:
                if (previous.attempt_id, previous.milestone, previous.belief_revision_id) != (
                    attempt_id, milestone, belief_revision_id
                ):
                    raise IdempotencyConflict("observation ID reused with different content")
                return previous
            belief = context.beliefs.get(belief_revision_id)
            if belief is None:
                raise AdmissionDenied(Status.UNKNOWN, "no scoped observation support")
            if belief_revision_id not in context.usable:
                raise AdmissionDenied(Status.STALE, "observation support is not current")
            if belief.conclusion != expected:
                raise AdmissionDenied(Status.FAIL, "observation does not match exact attempt, product and milestone")
            transition = self._transitions[belief.proposal.transition_id]
            if transition.evidence_id is None:
                raise AdmissionDenied(Status.FAIL, "executor milestones require direct observation evidence")
            evidence = self._evidence[transition.evidence_id]
            episode = self._lifecycle.episodes[operation.episode_id]
            edge = self._edge(episode, operation.edge_id)
            if evidence.source not in edge.observation_sources or evidence.observed_at < operation.created_at:
                raise AdmissionDenied(Status.FAIL, "observation source or event time violates the operation contract")
            observation = OperationObservation(observation_id, attempt_id, operation.product_id, milestone,
                                               belief_revision_id, evidence.evidence_id,
                                               evidence.source, evidence.observed_at)
            updated = replace(operation, revision=operation.revision + 1,
                              observations=operation.observations + (observation,))
            self._lifecycle.observations[observation_id] = observation
            self._lifecycle.attempts[attempt_id] = updated
            self._lifecycle_changed(operation.context_id)
            return observation

        return self._mutate("record_operation_observation", idempotency_key, dict(
            observation_id=observation_id, attempt_id=attempt_id, milestone=milestone,
            belief_revision_id=belief_revision_id), apply)

    def inspect_operation(self, attempt_id: str) -> OperationView:
        with self._lock:
            self._ensure_open()
            operation = self._lifecycle.attempts[attempt_id]
            episode = self._lifecycle.episodes[operation.episode_id]
            edge = self._edge(episode, operation.edge_id)
            context = self._contexts[episode.context_id]
            requirements = self._evaluate_requirement(episode.context_id, edge.requirements)
            outcome = self._evaluate_requirement(episode.context_id, edge.outcome)
            source = self.inspect_lifecycle(episode.episode_id)
            readiness = conjunction((Check("stage", Status.PASS if episode.stage == edge.source else Status.FAIL, ""),
                                     Check("source", Status.PASS if edge.kind in ("regression", "recovery")
                                           else source.validity, ""), Check("requirements", requirements.status, "")))
            observed = tuple(sorted({event.milestone for event in operation.observations}))
            current = tuple(sorted({event.milestone for event in operation.observations
                                    if event.belief_revision_id in context.usable}))
            complete = {"completion_observed", "exact_product_observed"} <= set(current)
            outcome_status = outcome.status if complete else Status.UNKNOWN
            return OperationView(operation, observed, current, readiness, outcome_status,
                                 requirements, outcome, self._lifecycle_revision(operation.context_id))
