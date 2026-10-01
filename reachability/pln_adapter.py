"""Pure grounded proposals from pinned trueagi-io/PLN formulas on PeTTa.

This is a separate finite-empirical truth model. It never converts uncertain
support to a hard claim, commits beliefs, or treats disjoint IDs as independence.
"""
from dataclasses import asdict, dataclass
from fractions import Fraction
import math
from pathlib import Path
import re
import tempfile

from .adapter_runtime import AdapterError, ROOT, checked_run, lockfile, verify_source
from .model import Literal, Statement, Status, identity, logical_integer, nonempty

TRUTH_MODEL = "trueagi-pln-stv-finite-k1/v1"
FORMULA_PREFIX = "trueagi-pln/4405956947c4b53c7ff01bd565aa3b114bc970a1/"


@dataclass(frozen=True)
class TruthValue:
    strength: float
    confidence: float
    truth_model: str = TRUTH_MODEL

    def __post_init__(self):
        for value in (self.strength, self.confidence):
            if type(value) not in (float, int) or not math.isfinite(value):
                raise ValueError("truth components must be finite numbers")
        if not 0 <= self.strength <= 1 or not 0 <= self.confidence < 1:
            raise ValueError("finite empirical truth requires s in [0,1], c in [0,1)")
        if self.truth_model != TRUTH_MODEL:
            raise ValueError("unsupported truth model")
        object.__setattr__(self, "strength", float(self.strength))
        object.__setattr__(self, "confidence", float(self.confidence))

    def metta(self) -> str:
        # Only validated numbers enter executable syntax; labels never do.
        return f"(stv {self.strength!r} {self.confidence!r})"


@dataclass(frozen=True)
class ProbabilisticSupport:
    support_id: str
    context_id: str
    conclusion: Literal
    truth: TruthValue
    evidence_ids: tuple[str, ...]
    lineage_roots: tuple[str, ...]
    ancestors: tuple[Literal, ...] = ()

    def __post_init__(self):
        nonempty(self.support_id)
        nonempty(self.context_id)
        if not isinstance(self.conclusion, Literal) or not isinstance(self.truth, TruthValue):
            raise ValueError("support requires a literal and explicit truth model")
        for field in ("evidence_ids", "lineage_roots"):
            items = getattr(self, field)
            if not isinstance(items, tuple) or not items:
                raise ValueError("finite support requires evidence and source lineage")
            for item in items:
                nonempty(item)
            object.__setattr__(self, field, tuple(sorted(set(items))))
        if not isinstance(self.ancestors, tuple) or any(not isinstance(x, Literal) for x in self.ancestors):
            raise ValueError("ancestors must be grounded literals")
        object.__setattr__(self, "ancestors", tuple(sorted(set(self.ancestors))))


def proposition(entity: str) -> Literal:
    return Literal(Statement("pln:proposition", (entity,)))


def implication(source: str, target: str) -> Literal:
    return Literal(Statement("pln:implication", (source, target)))


@dataclass(frozen=True)
class DeductionRule:
    p: str
    q: str
    r: str

    def __post_init__(self):
        for value in (self.p, self.q, self.r):
            nonempty(value)
        if len({self.p, self.q, self.r}) != 3:
            raise ValueError("this deduction fragment requires three distinct propositions")

    @property
    def premises(self) -> tuple[Literal, ...]:
        return (proposition(self.p), proposition(self.q), proposition(self.r),
                implication(self.p, self.q), implication(self.q, self.r))

    @property
    def conclusion(self) -> Literal:
        return implication(self.p, self.r)


@dataclass(frozen=True)
class ProbabilitySnapshot:
    context_id: str
    knowledge_revision: int
    supports: tuple[ProbabilisticSupport, ...]

    def __post_init__(self):
        nonempty(self.context_id)
        logical_integer(self.knowledge_revision)
        if not isinstance(self.supports, tuple) or any(not isinstance(x, ProbabilisticSupport) for x in self.supports):
            raise ValueError("snapshot supports must be immutable")
        ids = {}
        for support in self.supports:
            if support.context_id != self.context_id:
                raise ValueError("support context mismatch")
            if support.support_id in ids and ids[support.support_id] != support:
                raise ValueError("support identity reused with different content")
            ids[support.support_id] = support


@dataclass(frozen=True)
class Preconditions:
    status: Status
    detail: str


@dataclass(frozen=True)
class PLNProposal:
    proposal_id: str
    context_id: str
    knowledge_revision: int
    support: ProbabilisticSupport
    formula_id: str
    assumptions: tuple[str, ...]
    premise_ids: tuple[str, ...]


@dataclass(frozen=True)
class IndependenceDeclaration:
    """An explicit caller-supplied model assumption bound to exact supports.

    This assertion is recorded, not empirically established by this adapter.
    """
    model_id: str
    supports: tuple[ProbabilisticSupport, ProbabilisticSupport]

    def __post_init__(self):
        nonempty(self.model_id)
        if (not isinstance(self.supports, tuple) or len(self.supports) != 2 or
                any(not isinstance(s, ProbabilisticSupport) for s in self.supports)):
            raise ValueError("independence must bind exactly two supports")


@dataclass(frozen=True)
class RevisionResult:
    status: Status
    alternatives: tuple[ProbabilisticSupport, ...]
    proposal: PLNProposal | None
    detail: str


class PLNRejected(AdapterError):
    def __init__(self, status: Status, message: str):
        super().__init__(message)
        self.status = status


def conditional_consistent(a: float, b: float, conditional: float) -> bool:
    # Exact binary rational boundary check, with no permissive epsilon.
    a, b, conditional = map(Fraction, (a, b, conditional))
    return a > 0 and max(Fraction(0), a + b - 1) <= a * conditional <= min(a, b)


class PeTTaFormulaRuntime:
    def __init__(self, root: Path = ROOT / "artifacts", *, swipl: str = "swipl", timeout: float = 10):
        self.root, self.swipl, self.timeout = Path(root).resolve(), swipl, timeout

    def evaluate(self, formula: str, truths: tuple[TruthValue, ...]) -> TruthValue:
        arities = {"Truth_Deduction": 5, "Truth_Revision": 2}
        if (formula not in arities or not isinstance(truths, tuple) or
                len(truths) != arities[formula] or any(type(tv) is not TruthValue for tv in truths)):
            raise ValueError("unsupported formula or arity")
        pln = verify_source("pln", self.root)
        petta = verify_source("petta", self.root)
        version = checked_run([self.swipl, "--version"])
        expected = lockfile()["toolchain"]["swipl"]
        if not version.startswith(f"SWI-Prolog version {expected} "):
            raise AdapterError("SWI-Prolog version differs from the runtime pin")
        library = str(pln / "lib_pln.metta")
        # A quoted import path is the only nonnumeric substitution into MeTTa.
        if any(c in library for c in ('"', '\\', '\n', '\r')):
            raise AdapterError("unsupported import path")
        expression = f"({formula} {' '.join(tv.metta() for tv in truths)})"
        if formula == "Truth_Deduction":
            p, q, r, pq, qr = (repr(tv.strength) for tv in truths)
            expression = (f"(if (and (conditional-probability-consistency {p} {q} {pq}) "
                          f"(conditional-probability-consistency {q} {r} {qr})) "
                          f"{expression} ReachabilityRejected)")
        program = f'!(import! &self "{library}")\n!{expression}\n'
        with tempfile.TemporaryDirectory(prefix="reachability-pln-") as directory:
            path = Path(directory) / "request.metta"
            path.write_text(program)
            output = checked_run([self.swipl, "-q", "-s", str(petta / "src/main.pl"),
                                  "--", str(path), "--silent"], timeout=self.timeout)
        lines = output.strip().splitlines()
        if lines == ["true", "ReachabilityRejected"]:
            raise PLNRejected(Status.UNKNOWN, "runtime probability check disagrees with exact precheck")
        if len(lines) != 2 or lines[0] != "true":
            raise AdapterError("unexpected MeTTa result shape")
        match = re.fullmatch(r"\(stv ([^\s()]+) ([^\s()]+)\)", lines[1])
        if not match:
            raise AdapterError("formula did not return exactly one truth pair")
        try:
            return TruthValue(float(match[1]), float(match[2]))
        except ValueError as exc:
            raise AdapterError("invalid or rounded-to-certainty formula output") from exc


class PLNAdapter:
    def __init__(self, runtime: PeTTaFormulaRuntime | None = None):
        self.runtime = runtime if runtime is not None else PeTTaFormulaRuntime()

    def check_rule_preconditions(self, rule: DeductionRule, snapshot: ProbabilitySnapshot) -> Preconditions:
        if not isinstance(rule, DeductionRule) or not isinstance(snapshot, ProbabilitySnapshot):
            return Preconditions(Status.UNKNOWN, "unsupported grounded probability contract")
        if tuple(s.conclusion for s in snapshot.supports) != rule.premises:
            return Preconditions(Status.FAIL, "wrong ordered premise bindings")
        if any(rule.conclusion in (s.conclusion, *s.ancestors) for s in snapshot.supports):
            return Preconditions(Status.UNKNOWN, "cyclic derivation cannot mint new support")
        p, q, r, pq, qr = (s.truth.strength for s in snapshot.supports)
        if p == 0 or q == 0:
            return Preconditions(Status.UNKNOWN, "conditional on a zero-probability antecedent")
        if not (conditional_consistent(p, q, pq) and conditional_consistent(q, r, qr)):
            return Preconditions(Status.FAIL, "infeasible marginal/conditional probabilities")
        return Preconditions(Status.PASS, "exact conditional probability bounds satisfied")

    def _proposal(self, snapshot, conclusion, truth, formula, assumptions) -> PLNProposal:
        evidence = tuple(sorted({x for s in snapshot.supports for x in s.evidence_ids}))
        roots = tuple(sorted({x for s in snapshot.supports for x in s.lineage_roots}))
        ancestors = tuple(sorted({x for s in snapshot.supports for x in (*s.ancestors, s.conclusion)}))
        formula_id = FORMULA_PREFIX + formula
        support_id = identity("pln-support/v1", (snapshot.context_id, asdict(conclusion), asdict(truth), evidence,
                                                roots, formula_id, assumptions, ancestors_as_dict(ancestors)))
        support = ProbabilisticSupport(support_id, snapshot.context_id, conclusion, truth, evidence, roots, ancestors)
        premises = tuple(s.support_id for s in snapshot.supports)
        proposal_id = identity("pln-proposal/v1", (asdict(snapshot), asdict(support), formula_id, assumptions))
        return PLNProposal(proposal_id, snapshot.context_id, snapshot.knowledge_revision,
                           support, formula_id, assumptions, premises)

    def apply_rule(self, rule: DeductionRule, snapshot: ProbabilitySnapshot) -> PLNProposal:
        check = self.check_rule_preconditions(rule, snapshot)
        if check.status is not Status.PASS:
            raise PLNRejected(check.status, check.detail)
        truth = self.runtime.evaluate("Truth_Deduction", tuple(s.truth for s in snapshot.supports))
        # No statistical independence is inferred from the roots of these premises.
        # Upstream's heuristic deduction and near-one branch are named assumptions.
        return self._proposal(snapshot, rule.conclusion, truth, "Truth_Deduction",
                              ("upstream-heuristic-deduction", "upstream-q>0.9999-uses-r"))

    def revise(self, existing: ProbabilisticSupport, new_support: ProbabilisticSupport,
               knowledge_revision: int, dependency_model: IndependenceDeclaration | None = None) -> RevisionResult:
        snapshot = ProbabilitySnapshot(existing.context_id, knowledge_revision, (existing, new_support))
        if existing.conclusion != new_support.conclusion:
            return RevisionResult(Status.FAIL, (), None, "different conclusions")
        alternatives = tuple(sorted(set(snapshot.supports), key=lambda s: s.support_id))
        if len(alternatives) == 1:
            return RevisionResult(Status.PASS, alternatives, None, "identical support; no new weight")
        overlap = (set(existing.evidence_ids) & set(new_support.evidence_ids) or
                   set(existing.lineage_roots) & set(new_support.lineage_roots))
        if overlap or dependency_model is None:
            return RevisionResult(Status.UNKNOWN, alternatives, None, "retain alternatives; independence not justified")
        if set(dependency_model.supports) != set(snapshot.supports):
            return RevisionResult(Status.FAIL, alternatives, None, "independence declaration binds other support")
        if existing.truth.confidence == new_support.truth.confidence == 0:
            return RevisionResult(Status.UNKNOWN, alternatives, None, "zero evidence weight")
        # Canonical order makes revision commutative down to floating evaluation order.
        snapshot = ProbabilitySnapshot(existing.context_id, knowledge_revision, alternatives)
        truth = self.runtime.evaluate("Truth_Revision", tuple(s.truth for s in alternatives))
        proposal = self._proposal(snapshot, existing.conclusion, truth, "Truth_Revision",
                                  ("finite-evidence-weight-k=1", "independence:" + dependency_model.model_id))
        return RevisionResult(Status.PASS, alternatives, proposal, "revision under explicit independence assumption")

    def explain(self, result: PLNProposal) -> dict:
        return {"formula_id": result.formula_id, "truth_model": result.support.truth.truth_model,
                "assumptions": result.assumptions, "premises": result.premise_ids,
                "evidence_ids": result.support.evidence_ids, "lineage_roots": result.support.lineage_roots,
                "context_id": result.context_id, "knowledge_revision": result.knowledge_revision}


def ancestors_as_dict(ancestors):
    return tuple(asdict(x) for x in ancestors)
