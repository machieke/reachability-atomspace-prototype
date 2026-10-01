"""Immutable records for the initial grounded, propositional hard-claim fragment."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from hashlib import sha256
import json


def identity(kind: str, value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return f"{kind}:{sha256(payload.encode()).hexdigest()}"


def nonempty(value: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError("identifiers must be nonempty strings")


def logical_integer(value: int) -> None:
    if type(value) is not int or value < 0:
        raise ValueError("revisions and logical times must be nonnegative integers")


class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    STALE = "STALE"


@dataclass(frozen=True, slots=True, order=True)
class Statement:
    """Grounded predicate application; argument order is semantically significant."""

    predicate: str
    arguments: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        nonempty(self.predicate)
        if isinstance(self.arguments, str):
            raise ValueError("arguments must be a sequence of entity IDs, not a string")
        object.__setattr__(self, "arguments", tuple(self.arguments))
        for argument in self.arguments:
            nonempty(argument)

    @property
    def statement_id(self) -> str:
        return identity("statement/v1", asdict(self))


@dataclass(frozen=True, slots=True, order=True)
class Literal:
    statement: Statement
    positive: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.statement, Statement) or type(self.positive) is not bool:
            raise ValueError("a literal requires a Statement and a Boolean polarity")

    def negate(self) -> Literal:
        return Literal(self.statement, not self.positive)


@dataclass(frozen=True, slots=True)
class Clause:
    """Disjunction. An empty clause is false; a tuple of clauses is a conjunction."""

    literals: tuple[Literal, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "literals", tuple(self.literals))
        if any(not isinstance(item, Literal) for item in self.literals):
            raise ValueError("CNF clauses contain only grounded literals")


@dataclass(frozen=True, slots=True)
class Evidence:
    evidence_id: str
    context_id: str
    content: Literal
    source: str
    observed_at: int
    lineage_roots: tuple[str, ...]
    valid_until: int | None = None

    def __post_init__(self) -> None:
        for value in (self.evidence_id, self.context_id, self.source):
            nonempty(value)
        if not isinstance(self.content, Literal):
            raise ValueError("evidence content must be a literal")
        logical_integer(self.observed_at)
        if self.valid_until is not None:
            logical_integer(self.valid_until)
            if self.valid_until <= self.observed_at:
                raise ValueError("evidence validity must end after its observation time")
        if isinstance(self.lineage_roots, str):
            raise ValueError("lineage roots must be a sequence of IDs, not a string")
        object.__setattr__(self, "lineage_roots", tuple(sorted(set(self.lineage_roots))))
        if not self.lineage_roots:
            raise ValueError("evidence must declare at least one lineage root")
        for root in self.lineage_roots:
            nonempty(root)


@dataclass(frozen=True, slots=True)
class Rule:
    """Trusted, explicitly registered grounded implication; not a PLN formula."""

    rule_id: str
    revision: str
    premises: tuple[Literal, ...]
    conclusion: Literal

    def __post_init__(self) -> None:
        nonempty(self.rule_id)
        nonempty(self.revision)
        object.__setattr__(self, "premises", tuple(self.premises))
        if not self.premises or any(not isinstance(p, Literal) for p in self.premises):
            raise ValueError("grounded rules require at least one typed premise")
        if not isinstance(self.conclusion, Literal):
            raise ValueError("rule conclusion must be a literal")


@dataclass(frozen=True, slots=True)
class Check:
    name: str
    status: Status
    detail: str


def conjunction(checks: tuple[Check, ...]) -> Status:
    # Empty or malformed contracts never authorize work.
    if not checks or any(not isinstance(check.status, Status) for check in checks):
        return Status.UNKNOWN
    for status in (Status.FAIL, Status.STALE, Status.UNKNOWN):
        if any(check.status is status for check in checks):
            return status
    return Status.PASS


@dataclass(frozen=True, slots=True)
class Transition:
    transition_id: str
    context_id: str
    conclusion: Literal
    rule_id: str | None
    rule_revision: str | None
    premise_revision_ids: tuple[str, ...]
    evidence_id: str | None


@dataclass(frozen=True, slots=True)
class Proposal:
    proposal_id: str
    transition_id: str
    context_id: str
    conclusion: Literal
    premise_revision_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    lineage_roots: tuple[str, ...]
    formula_id: str = "grounded-hard-implication/v1"


@dataclass(frozen=True, slots=True)
class Certificate:
    certificate_id: str
    stage: str
    subject_id: str
    context_id: str
    knowledge_revision: int
    policy_revision: str
    rule_revision: str | None
    checks: tuple[Check, ...]
    witness: tuple[tuple[Statement, bool], ...] | None
    transition_id: str
    premise_revision_ids: tuple[str, ...]
    evidence_lineage_digest: str
    constraint_digest: str
    schema_version: str = "finite-certificate/v2"
    checker_version: str = "bounded-cnf-dpll/v1"
    formula_id: str = "grounded-hard-implication/v1"
    logical_time: int = 0
    valid_until: int | None = None
    # Certificate lookup plus exact record equality is the integrity binding in
    # this trusted, single-process prototype. It is not remote attestation.

    @property
    def status(self) -> Status:
        return conjunction(self.checks)


@dataclass(frozen=True, slots=True)
class BeliefRevision:
    belief_revision_id: str
    context_id: str
    conclusion: Literal
    accepted_at_revision: int
    proposal: Proposal
    pre_certificate_id: str
    post_certificate_id: str
    interpretation: str = "explicit-hard-claim"


@dataclass(frozen=True, slots=True)
class CommitResult:
    status: Status
    knowledge_revision: int
    belief: BeliefRevision | None = None
    detail: str = ""


@dataclass(frozen=True, slots=True)
class BeliefView:
    status: Status
    checked_at_revision: int
    current: tuple[BeliefRevision, ...]
    historical: tuple[BeliefRevision, ...]
    checks: tuple[Check, ...]


@dataclass(frozen=True, slots=True)
class ContextSnapshot:
    context_id: str
    knowledge_revision: int
    assumptions: tuple[Literal, ...]
    constraints: tuple[Clause, ...]
    policy_revision: str
    usable: tuple[BeliefRevision, ...]
    logical_time: int = 0
