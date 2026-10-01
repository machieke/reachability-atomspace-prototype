"""Exact goal slices, monitoring contracts and immutable accounting records."""
from dataclasses import dataclass

from .execution_model import positive_integer
from .model import Check, Literal, Statement, logical_integer, nonempty
from .requirements import Requirement, RequirementResult


def goal_sample_literal(goal_id: str, slice_id: str, product_id: str, observed_at: int,
                        healthy: bool = True) -> Literal:
    for value in (goal_id, slice_id, product_id):
        nonempty(value)
    logical_integer(observed_at)
    if type(healthy) is not bool:
        raise ValueError("sample polarity must be Boolean")
    return Literal(Statement("rd:goal/sample", (goal_id, slice_id, product_id, str(observed_at))), healthy)


@dataclass(frozen=True, slots=True)
class DurabilityContract:
    samples: int
    interval: int
    fresh_for: int
    sources: tuple[str, ...]

    def __post_init__(self):
        for value in (self.samples, self.interval, self.fresh_for):
            positive_integer(value)
        if isinstance(self.sources, str):
            raise ValueError("monitor sources must be a sequence")
        object.__setattr__(self, "sources", tuple(self.sources))
        if not self.sources or len(set(self.sources)) != len(self.sources):
            raise ValueError("distinct monitoring sources are required")
        for source in self.sources:
            nonempty(source)


@dataclass(frozen=True, slots=True)
class GoalSlice:
    slice_id: str
    loss: int
    product_id: str
    condition: Requirement
    durability: DurabilityContract

    def __post_init__(self):
        nonempty(self.slice_id)
        nonempty(self.product_id)
        positive_integer(self.loss)
        if not isinstance(self.condition, Requirement) or not isinstance(self.durability, DurabilityContract):
            raise ValueError("typed condition and durability contracts are required")


@dataclass(frozen=True, slots=True)
class GoalContract:
    contract_id: str
    revision: str
    unit: str
    slices: tuple[GoalSlice, ...]
    provenance: str

    def __post_init__(self):
        for value in (self.contract_id, self.revision, self.unit, self.provenance):
            nonempty(value)
        object.__setattr__(self, "slices", tuple(self.slices))
        if not self.slices or any(not isinstance(item, GoalSlice) for item in self.slices):
            raise ValueError("a nonempty set of typed disjoint goal slices is required")
        if len({item.slice_id for item in self.slices}) != len(self.slices):
            raise ValueError("goal slice identities must be distinct")


@dataclass(frozen=True, slots=True)
class GoalMonitor:
    monitor_id: str
    slice_id: str
    opened_at: int
    censored_at: int | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class GoalEpisode:
    goal_id: str
    source_id: str
    context_id: str
    contract_id: str
    contract_revision: str
    opened_at: int
    monitors: tuple[GoalMonitor, ...]


@dataclass(frozen=True, slots=True)
class GoalSample:
    sample_id: str
    goal_id: str
    slice_id: str
    monitor_id: str
    product_id: str
    healthy: bool
    observed_at: int
    belief_revision_id: str
    evidence_id: str
    lineage_roots: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CoverageCommitment:
    commitment_id: str
    goal_id: str
    slice_id: str
    monitor_id: str
    attempt_id: str
    owner_id: str
    units: int
    created_at: int
    valid_until: int
    baseline_measurements: tuple[str, ...] = ()
    withdrawn_at: int | None = None


@dataclass(frozen=True, slots=True)
class DurabilityResult:
    label: str
    samples: tuple[GoalSample, ...]
    checks: tuple[Check, ...]


@dataclass(frozen=True, slots=True)
class GoalSliceView:
    slice_id: str
    label: str
    condition: RequirementResult
    samples: tuple[GoalSample, ...]
    checks: tuple[Check, ...]
    outstanding_loss: int
    estimated_coverage: int
    selected_commitment: str | None
    observation_required: bool
    maintenance_required: bool = True


@dataclass(frozen=True, slots=True)
class GoalProjection:
    goal_id: str
    unit: str
    slices: tuple[GoalSliceView, ...]
    outstanding_loss: int
    estimated_committed_coverage: int
    open_loss: int
    knowledge_revision: int
    goal_revision: int
    lifecycle_revision: int
    resource_revision: int
    logical_time: int
    fingerprint: str


@dataclass(frozen=True, slots=True)
class GoalReliefEvent:
    event_id: str
    slice_id: str
    kind: str
    units: int
    unit: str
    logical_time: int
    sample_ids: tuple[str, ...]
    causal_attempt_id: str | None = None


@dataclass(frozen=True, slots=True)
class GoalAccountingRevision:
    revision_id: str
    number: int
    projection: GoalProjection
    events: tuple[GoalReliefEvent, ...]


@dataclass(frozen=True, slots=True)
class GoalView:
    episode: GoalEpisode
    projection: GoalProjection
    history: tuple[GoalAccountingRevision, ...]
    reconciliation_needed: bool
