"""Immutable grounded lifecycle schemas, episodes and operation observations."""
from __future__ import annotations

from dataclasses import dataclass

from .model import Check, Literal, Statement, Status, conjunction, nonempty
from .requirements import Requirement, RequirementResult, requires_evidence, validate_requirement

MILESTONES = frozenset(("submitted", "accepted_by_executor", "completion_observed",
                        "exact_product_observed", "failure_observed", "cancellation_observed"))


def milestone_literal(attempt_id: str, product_id: str, milestone: str) -> Literal:
    nonempty(attempt_id)
    nonempty(product_id)
    if milestone not in MILESTONES:
        raise ValueError("unsupported observed operation milestone")
    return Literal(Statement(f"rd:operation/{milestone}", (attempt_id, product_id)))


@dataclass(frozen=True, slots=True)
class LifecycleState:
    name: str
    validity: Requirement = Requirement("ALWAYS")

    def __post_init__(self):
        nonempty(self.name)
        if not isinstance(self.validity, Requirement):
            raise ValueError("state validity must be a typed requirement")


@dataclass(frozen=True, slots=True)
class LifecycleEdge:
    edge_id: str
    source: str
    target: str
    requirements: Requirement
    outcome: Requirement
    product_id: str
    observation_sources: tuple[str, ...]
    kind: str = "advance"

    def __post_init__(self):
        for value in (self.edge_id, self.source, self.target, self.product_id):
            nonempty(value)
        if not isinstance(self.requirements, Requirement) or not isinstance(self.outcome, Requirement):
            raise ValueError("edge requires typed preconditions and outcome contracts")
        if self.kind not in ("advance", "recovery", "regression"):
            raise ValueError("unsupported lifecycle edge kind")
        if isinstance(self.observation_sources, str):
            raise ValueError("observation sources must be a sequence of IDs")
        object.__setattr__(self, "observation_sources", tuple(self.observation_sources))
        if not self.observation_sources:
            raise ValueError("an operation requires a declared observation authority")
        for source in self.observation_sources:
            nonempty(source)


@dataclass(frozen=True, slots=True)
class LifecycleSchema:
    schema_id: str
    revision: str
    entity_type: str
    entity_id: str
    initial_state: str
    states: tuple[LifecycleState, ...]
    edges: tuple[LifecycleEdge, ...]
    terminal_states: tuple[str, ...]
    provenance: str

    def __post_init__(self):
        for value in (self.schema_id, self.revision, self.entity_type, self.entity_id,
                      self.initial_state, self.provenance):
            nonempty(value)
        for name in ("states", "edges", "terminal_states"):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        if any(not isinstance(state, LifecycleState) for state in self.states):
            raise ValueError("schema states must be typed")
        if any(not isinstance(edge, LifecycleEdge) for edge in self.edges):
            raise ValueError("schema edges must be typed")
        names = {state.name for state in self.states}
        if not names or len(names) != len(self.states) or self.initial_state not in names:
            raise ValueError("schema needs unique states and a declared initial state")
        if not set(self.terminal_states) <= names:
            raise ValueError("unknown terminal state")
        if len({edge.edge_id for edge in self.edges}) != len(self.edges):
            raise ValueError("edge IDs must be unique in a schema revision")
        for edge in self.edges:
            if edge.source not in names or edge.target not in names:
                raise ValueError("lifecycle edge references an unknown state")
            if edge.source in self.terminal_states and edge.kind == "advance":
                raise ValueError("leaving a terminal state needs an explicit recovery/regression edge")

    def supported(self) -> bool:
        expressions = [state.validity for state in self.states]
        expressions += [r for edge in self.edges for r in (edge.requirements, edge.outcome)]
        return (all(validate_requirement(r) is Status.PASS for r in expressions)
                and all(requires_evidence(edge.outcome) for edge in self.edges))


@dataclass(frozen=True, slots=True)
class LifecycleEvent:
    event_id: str
    edge_id: str
    source: str
    target: str
    logical_time: int
    certificate_id: str
    attempt_id: str | None
    prerequisites: RequirementResult
    outcome: RequirementResult
    target_validity: RequirementResult


@dataclass(frozen=True, slots=True)
class LifecycleEpisode:
    episode_id: str
    context_id: str
    schema_id: str
    schema_revision: str
    entity_id: str
    stage: str
    revision: int
    opened_at: int
    initial_validity: RequirementResult
    events: tuple[LifecycleEvent, ...] = ()


@dataclass(frozen=True, slots=True)
class LifecycleView:
    episode: LifecycleEpisode
    validity: Status
    current_support: RequirementResult
    lifecycle_revision: int


@dataclass(frozen=True, slots=True)
class LifecyclePermit:
    certificate_id: str
    subject_id: str
    episode_id: str
    edge_id: str
    attempt_id: str | None
    context_id: str
    knowledge_revision: int
    lifecycle_revision: int
    episode_revision: int
    schema_revision: str
    policy_revision: str
    logical_time: int
    checks: tuple[Check, ...]
    prerequisites: RequirementResult
    outcome: RequirementResult
    target_validity: RequirementResult

    @property
    def status(self) -> Status:
        return conjunction(self.checks)


@dataclass(frozen=True, slots=True)
class OperationObservation:
    observation_id: str
    attempt_id: str
    product_id: str
    milestone: str
    belief_revision_id: str
    evidence_id: str
    source: str
    observed_at: int


@dataclass(frozen=True, slots=True)
class OperationEpisode:
    operation_id: str
    attempt_id: str
    episode_id: str
    edge_id: str
    context_id: str
    schema_id: str
    schema_revision: str
    product_id: str
    created_at: int
    revision: int = 0
    selected: bool = False
    selected_at: int | None = None
    observations: tuple[OperationObservation, ...] = ()


@dataclass(frozen=True, slots=True)
class OperationView:
    operation: OperationEpisode
    observed_milestones: tuple[str, ...]
    current_milestones: tuple[str, ...]
    readiness: Status
    outcome_status: Status
    requirements: RequirementResult
    outcome: RequirementResult
    lifecycle_revision: int
    execution_authorized: bool = False
