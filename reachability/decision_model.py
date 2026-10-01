"""Explicit acceptance policies for estimates; these records assert no hard facts."""
from dataclasses import asdict, dataclass
import math

from .model import Check, Literal, conjunction, identity, nonempty
from .pln_adapter import TRUTH_MODEL, TruthValue

DECISION_SCHEMA = "probability-decision/v1"


@dataclass(frozen=True, slots=True)
class DecisionCriterion:
    criterion_id: str
    conclusion: Literal
    min_strength: float
    max_strength: float
    min_confidence: float
    unit: str = "dimensionless-probability"
    confidence_semantics: str = "pln-evidence-adequacy-floor/v1"

    def __post_init__(self):
        nonempty(self.criterion_id)
        if type(self.conclusion) is not Literal:
            raise ValueError("a criterion requires an exact grounded estimate")
        for name in ("min_strength", "max_strength", "min_confidence"):
            value = getattr(self, name)
            if type(value) not in (float, int) or not math.isfinite(value):
                raise ValueError("decision thresholds must be finite numbers")
            object.__setattr__(self, name, float(value))
        if not 0 <= self.min_strength <= self.max_strength <= 1 or not 0 <= self.min_confidence < 1:
            raise ValueError("invalid strength interval or confidence floor")
        if (self.unit, self.confidence_semantics) != (
                "dimensionless-probability", "pln-evidence-adequacy-floor/v1"):
            raise ValueError("unsupported decision units or uncertainty semantics")


@dataclass(frozen=True, slots=True)
class DecisionContract:
    contract_id: str
    revision: str
    execution_contract_id: str
    execution_contract_revision: str
    product_id: str
    criteria: tuple[DecisionCriterion, ...]
    alternative_policy: str = "all-current-exact-literal/v1"
    truth_model: str = TRUTH_MODEL
    schema: str = DECISION_SCHEMA

    def __post_init__(self):
        for value in (self.contract_id, self.revision, self.execution_contract_id,
                      self.execution_contract_revision, self.product_id):
            nonempty(value)
        if (not isinstance(self.criteria, tuple) or not 1 <= len(self.criteria) <= 16
                or any(type(item) is not DecisionCriterion for item in self.criteria)):
            raise ValueError("declare between one and sixteen decision criteria")
        if (len({item.criterion_id for item in self.criteria}) != len(self.criteria)
                or len({item.conclusion for item in self.criteria}) != len(self.criteria)):
            raise ValueError("criterion IDs and exact conclusions must be unique")
        if (self.alternative_policy, self.truth_model, self.schema) != (
                "all-current-exact-literal/v1", TRUTH_MODEL, DECISION_SCHEMA):
            raise ValueError("unsupported decision contract")

    @property
    def fingerprint(self):
        return identity(DECISION_SCHEMA, asdict(self))


@dataclass(frozen=True, slots=True)
class DecisionSupport:
    belief_revision_id: str
    truth: TruthValue


@dataclass(frozen=True, slots=True)
class CriterionDecision:
    criterion: DecisionCriterion
    current: tuple[DecisionSupport, ...]
    opposite: tuple[DecisionSupport, ...]
    checks: tuple[Check, ...]

    @property
    def status(self):
        return conjunction(self.checks)


@dataclass(frozen=True, slots=True)
class DecisionEvaluation:
    contract: DecisionContract
    context_id: str
    product_id: str
    knowledge_revision: int
    logical_time: int
    criteria: tuple[CriterionDecision, ...]
    checks: tuple[Check, ...]

    @property
    def status(self):
        return conjunction(self.checks)

    @property
    def evaluation_id(self):
        return identity("decision-evaluation/v1", asdict(self))

    @property
    def basis_id(self):
        # Unrelated context changes and clock ticks do not replace an estimate.
        # Freshness is checked separately on every use of this exact basis.
        return identity("decision-basis/v1", (self.contract.fingerprint, self.context_id,
            self.product_id, tuple((item.criterion.criterion_id,
                tuple(asdict(s) for s in item.current), tuple(asdict(s) for s in item.opposite))
                for item in self.criteria)))
