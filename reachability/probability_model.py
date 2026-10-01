"""Versioned records for certified probabilistic estimates, separate from hard claims."""
from dataclasses import dataclass

from .model import Check, Literal, Status, conjunction, nonempty
from .pln_adapter import DeductionRule, FORMULA_PREFIX, PLNProposal, TRUTH_MODEL, TruthValue

PROBABILITY_SCHEMA = "probability-ledger/v1"
PROBABILITY_CHECKER = "pln-binary64-joint3/v1"
PROBABILITY_INTERPRETATION = "scoped-estimate-alternatives/v1"


@dataclass(frozen=True, slots=True)
class ProbabilityPolicy:
    revision: str
    allowed_sources: tuple[str, ...]
    truth_model: str = TRUTH_MODEL
    interpretation: str = PROBABILITY_INTERPRETATION
    checker_revision: str = PROBABILITY_CHECKER
    formula_revision: str = FORMULA_PREFIX
    max_beliefs: int = 256

    def __post_init__(self):
        nonempty(self.revision)
        if not isinstance(self.allowed_sources, tuple) or not self.allowed_sources:
            raise ValueError("declare the trusted probability report sources")
        for source in self.allowed_sources:
            nonempty(source)
        object.__setattr__(self, "allowed_sources", tuple(sorted(set(self.allowed_sources))))
        if (self.truth_model, self.interpretation, self.checker_revision, self.formula_revision) != (
                TRUTH_MODEL, PROBABILITY_INTERPRETATION, PROBABILITY_CHECKER, FORMULA_PREFIX):
            raise ValueError("unsupported probability contract")
        if type(self.max_beliefs) is not int or not 1 <= self.max_beliefs <= 512:
            raise ValueError("probability history limit must be in [1,512]")


@dataclass(frozen=True, slots=True)
class ProbabilityReport:
    evidence_id: str
    truth: TruthValue

    def __post_init__(self):
        nonempty(self.evidence_id)
        if type(self.truth) is not TruthValue:
            raise ValueError("report requires the declared finite empirical truth model")


@dataclass(frozen=True, slots=True)
class ProbabilityRule:
    rule_id: str
    revision: str
    deduction: DeductionRule

    def __post_init__(self):
        nonempty(self.rule_id)
        nonempty(self.revision)
        if type(self.deduction) is not DeductionRule:
            raise ValueError("only the grounded deduction schema is supported")


@dataclass(frozen=True, slots=True)
class ProbabilityIndependence:
    model_id: str
    context_id: str
    premise_revision_ids: tuple[str, str]
    justification: str

    def __post_init__(self):
        for value in (self.model_id, self.context_id, self.justification):
            nonempty(value)
        if (not isinstance(self.premise_revision_ids, tuple) or len(self.premise_revision_ids) != 2
                or len(set(self.premise_revision_ids)) != 2):
            raise ValueError("independence must bind two distinct exact belief revisions")
        for value in self.premise_revision_ids:
            nonempty(value)
        object.__setattr__(self, "premise_revision_ids", tuple(sorted(self.premise_revision_ids)))


@dataclass(frozen=True, slots=True)
class ProbabilityTransition:
    transition_id: str
    context_id: str
    kind: str
    evidence_id: str | None
    rule_id: str | None
    rule_revision: str | None
    premise_revision_ids: tuple[str, ...]
    independence_id: str | None


@dataclass(frozen=True, slots=True)
class ProbabilityCertificate:
    certificate_id: str
    stage: str
    transition_id: str
    context_id: str
    knowledge_revision: int
    hard_policy_revision: str
    probability_policy_revision: str | None
    logical_time: int
    snapshot_digest: str
    proposal_digest: str | None
    pre_certificate_id: str | None
    checks: tuple[Check, ...]
    joint_witness: tuple[str, ...] | None = None
    checker_revision: str = PROBABILITY_CHECKER
    schema: str = "probability-certificate/v1"

    @property
    def status(self):
        return conjunction(self.checks)


@dataclass(frozen=True, slots=True)
class ProbabilityBeliefRevision:
    belief_revision_id: str
    context_id: str
    accepted_at_revision: int
    transition: ProbabilityTransition
    proposal: PLNProposal
    pre_certificate_id: str
    post_certificate_id: str
    hard_policy_revision: str
    probability_policy_revision: str
    interpretation: str = PROBABILITY_INTERPRETATION


@dataclass(frozen=True, slots=True)
class ProbabilityCommitResult:
    status: Status
    knowledge_revision: int
    belief: ProbabilityBeliefRevision | None = None
    detail: str = ""


@dataclass(frozen=True, slots=True)
class ProbabilityView:
    context_id: str
    conclusion: Literal
    checked_at_revision: int
    status: Status
    current: tuple[ProbabilityBeliefRevision, ...]
    historical: tuple[ProbabilityBeliefRevision, ...]
    checks: tuple[Check, ...]
