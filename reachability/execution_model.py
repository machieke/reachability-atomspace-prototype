"""Grounded local resource contracts and undispatched execution intent records."""
from dataclasses import dataclass

from .model import Check, Status, conjunction, logical_integer, nonempty
from .requirements import Requirement, RequirementResult


def positive_integer(value: int) -> None:
    logical_integer(value)
    if value == 0:
        raise ValueError("quantities and lease durations must be positive integers")


@dataclass(frozen=True, slots=True)
class ResourceDefinition:
    resource_id: str
    capacity: int
    unit: str
    mode: str = "renewable"

    def __post_init__(self):
        for value in (self.resource_id, self.unit, self.mode):
            nonempty(value)
        logical_integer(self.capacity)


@dataclass(frozen=True, slots=True)
class ResourceDemand:
    resource_id: str
    quantity: int
    unit: str

    def __post_init__(self):
        nonempty(self.resource_id)
        nonempty(self.unit)
        positive_integer(self.quantity)


@dataclass(frozen=True, slots=True)
class ResourceClaim:
    resource_id: str
    quantity: int
    unit: str
    starts_at: int
    ends_at: int

    def __post_init__(self):
        ResourceDemand(self.resource_id, self.quantity, self.unit)
        logical_integer(self.starts_at)
        logical_integer(self.ends_at)
        if self.ends_at <= self.starts_at:
            raise ValueError("resource intervals must be nonempty and half-open")


@dataclass(frozen=True, slots=True)
class ExecutionContract:
    contract_id: str
    revision: str
    schema_id: str
    schema_revision: str
    edge_id: str
    executor_id: str
    owners: tuple[str, ...]
    demands: tuple[ResourceDemand, ...]
    lease_duration: int
    requirements: Requirement = Requirement("ALWAYS")

    def __post_init__(self):
        for value in (self.contract_id, self.revision, self.schema_id, self.schema_revision,
                      self.edge_id, self.executor_id):
            nonempty(value)
        positive_integer(self.lease_duration)
        if isinstance(self.owners, str):
            raise ValueError("owners must be a sequence of identities")
        object.__setattr__(self, "owners", tuple(self.owners))
        object.__setattr__(self, "demands", tuple(self.demands))
        if not self.owners or len(set(self.owners)) != len(self.owners):
            raise ValueError("a contract requires distinct allowed owners")
        for owner in self.owners:
            nonempty(owner)
        if any(not isinstance(demand, ResourceDemand) for demand in self.demands):
            raise ValueError("resource demands must be typed")
        if len({d.resource_id for d in self.demands}) != len(self.demands):
            raise ValueError("declare each resource's total demand once")
        if not isinstance(self.requirements, Requirement):
            raise ValueError("execution requirements must be typed")


@dataclass(frozen=True, slots=True)
class ExecutionPermit:
    certificate_id: str
    attempt_id: str
    context_id: str
    owner_id: str
    contract_id: str
    contract_revision: str
    knowledge_revision: int
    policy_revision: str
    logical_time: int
    lifecycle_revision: int
    operation_revision: int
    episode_revision: int
    resource_revision: int
    resource_time: int
    lease_until: int
    claims: tuple[ResourceClaim, ...]
    prerequisites: RequirementResult
    action_requirements: RequirementResult
    checks: tuple[Check, ...]

    @property
    def status(self) -> Status:
        return conjunction(self.checks)


@dataclass(frozen=True, slots=True)
class Reservation:
    reservation_id: str
    intent_id: str
    attempt_id: str
    owner_id: str
    claim: ResourceClaim


@dataclass(frozen=True, slots=True)
class ExecutionIntent:
    intent_id: str
    attempt_id: str
    context_id: str
    owner_id: str
    executor_id: str
    product_id: str
    contract_id: str
    contract_revision: str
    certificate_id: str
    created_at: int
    lease_until: int
    reservations: tuple[Reservation, ...]
    state: str = "pending"
    revision: int = 0
    closed_at: int | None = None


@dataclass(frozen=True, slots=True)
class ExecutionIntentView:
    intent: ExecutionIntent
    state: str
    readiness: Status
    checks: tuple[Check, ...]
    resource_revision: int
    resource_time: int
    execution_authorized: bool = False


@dataclass(frozen=True, slots=True)
class ResourceView:
    resource: ResourceDefinition
    reservations: tuple[Reservation, ...]
    used_now: int
    reconciliation_attempts: tuple[str, ...]
    resource_revision: int
    logical_time: int


@dataclass(frozen=True, slots=True)
class ResourceSnapshot:
    revision: int
    logical_time: int
    resources: tuple[ResourceDefinition, ...]
