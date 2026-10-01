"""Versioned dispatch identities and authoritative executor receipt contracts."""
from dataclasses import asdict, dataclass

from .execution_model import ExecutionIntent
from .model import Check, identity, logical_integer, nonempty
from .requirements import RequirementResult


@dataclass(frozen=True, slots=True)
class ExecutorProfile:
    executor_id: str
    instance_id: str
    supports_idempotency: bool
    supports_query: bool
    supports_release: bool

    def __post_init__(self):
        nonempty(self.executor_id)
        nonempty(self.instance_id)
        if any(type(value) is not bool for value in (
                self.supports_idempotency, self.supports_query, self.supports_release)):
            raise ValueError("executor capabilities must be explicit Booleans")


@dataclass(frozen=True, slots=True)
class DispatchPolicy:
    policy_id: str
    revision: str
    contract_id: str
    contract_revision: str
    executor: ExecutorProfile

    def __post_init__(self):
        for value in (self.policy_id, self.revision, self.contract_id, self.contract_revision):
            nonempty(value)
        if not isinstance(self.executor, ExecutorProfile):
            raise ValueError("a pinned executor profile is required")


@dataclass(frozen=True, slots=True)
class DispatchRequest:
    request_id: str
    intent: ExecutionIntent

    def __post_init__(self):
        nonempty(self.request_id)
        if not isinstance(self.intent, ExecutionIntent):
            raise ValueError("a typed immutable intent is required")

    @property
    def fingerprint(self) -> str:
        return identity("dispatch-request-content/v1", asdict(self))


@dataclass(frozen=True, slots=True)
class ExecutorReceipt:
    executor_id: str
    instance_id: str
    request_id: str
    request_fingerprint: str
    state: str
    sequence: int
    effect_count: int
    fenced: bool = False

    def __post_init__(self):
        for value in (self.executor_id, self.instance_id, self.request_id, self.request_fingerprint):
            nonempty(value)
        logical_integer(self.sequence)
        logical_integer(self.effect_count)
        if self.state not in ("unknown", "absent", "accepted", "released"):
            raise ValueError("unsupported executor receipt state")
        if type(self.fenced) is not bool or self.fenced != (self.state == "released"):
            raise ValueError("release must permanently fence this request against future submission")
        if self.state in ("unknown", "absent") and self.effect_count != 0:
            raise ValueError("an absent or unknown receipt cannot assert effects")
        if self.state == "accepted" and self.effect_count == 0:
            raise ValueError("acceptance must name at least one executor effect")

    @property
    def receipt_id(self) -> str:
        return identity("executor-receipt/v1", asdict(self))


@dataclass(frozen=True, slots=True)
class DispatchAttempt:
    request: DispatchRequest
    policy: DispatchPolicy
    prepared_at: int
    knowledge_revision: int
    policy_revision: str
    lifecycle_revision: int
    resource_revision: int
    prerequisites: RequirementResult
    action_requirements: RequirementResult
    checks: tuple[Check, ...]
    receipts: tuple[ExecutorReceipt, ...] = ()


@dataclass(frozen=True, slots=True)
class DispatchView:
    dispatch: DispatchAttempt
    state: str
    latest_receipt: ExecutorReceipt | None
    resources_released: bool
