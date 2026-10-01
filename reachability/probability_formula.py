"""Deterministic commit/replay checker for the selected PLN binary64 expressions.

Grouping follows lib_pln.metta at FORMULA_PREFIX's revision, including its
rounded preconditions and near-one branch. Native runtime conformance is tested
separately; journal replay never starts an external process. No tolerance admits
a changed value. The exact probability-domain guard is additional to upstream's
floating guard, not a claim of exact arithmetic for the heuristic truth formula.
"""
import math
from fractions import Fraction

from .model import Status
from .pln_adapter import PLNRejected, TruthValue, conditional_consistent


def three_event_joint(marginals, intersections):
    """Exact feasibility witness for all three marginals and all three pairs.

    Pair order: PQ, QR, PR. World order: 111,110,101,011,100,010,001,000.
    All eight nonnegative cells are affine in the one free triple intersection.
    This is complete for this declared fragment, not for arbitrary joint models.
    """
    p, q, r = map(Fraction, marginals)
    pq, qr, pr = map(Fraction, intersections)
    lower = max(Fraction(0), pq + pr - p, pq + qr - q, pr + qr - r)
    upper = min(pq, qr, pr, 1 - p - q - r + pq + qr + pr)
    if lower > upper:
        return None
    t = lower
    cells = (t, pq-t, pr-t, qr-t, p-pq-pr+t, q-pq-qr+t, r-pr-qr+t,
             1-p-q-r+pq+pr+qr-t)
    if any(cell < 0 for cell in cells) or sum(cells) != 1:
        return None
    return cells


def deduction_joint(truths, conclusion):
    p, q, r, pq, qr = (Fraction(tv.strength) for tv in truths)
    return three_event_joint((p, q, r), (p*pq, q*qr, p*Fraction(conclusion.strength)))


class PinnedFormulaRuntime:
    def evaluate(self, formula: str, truths: tuple[TruthValue, ...]) -> TruthValue:
        expected = {"Truth_Deduction": 5, "Truth_Revision": 2}
        if (formula not in expected or len(truths) != expected[formula]
                or any(type(tv) is not TruthValue for tv in truths)):
            raise ValueError("unsupported checked formula input")
        try:
            if formula == "Truth_Deduction":
                p, q, r, pq, qr = (tv.strength for tv in truths)
                if p == 0 or q == 0:
                    raise PLNRejected(Status.UNKNOWN, "undefined conditional antecedent")
                if not (conditional_consistent(p, q, pq) and conditional_consistent(q, r, qr)):
                    raise PLNRejected(Status.FAIL, "infeasible conditional probability model")
                def rounded_consistent(a, b, ab):
                    raw_lower, raw_upper = ((a + b) - 1.0) / a, b / a
                    if not math.isfinite(raw_lower) or not math.isfinite(raw_upper):
                        raise ArithmeticError("nonfinite probability intermediate")
                    lower = min(1.0, max(0.0, raw_lower))
                    upper = min(1.0, max(0.0, raw_upper))
                    return lower <= ab <= upper
                if not (rounded_consistent(p, q, pq) and rounded_consistent(q, r, qr)):
                    raise PLNRejected(Status.UNKNOWN, "runtime probability check disagrees with exact precheck")
                strength = r if q > .9999 else (pq * qr) + (((1.0 - pq) * (r - (q * qr))) / (1.0 - q))
                confidence = (pq * qr) * (truths[3].confidence * truths[4].confidence)
            else:
                a, b = truths
                w1 = a.confidence / (1.0 - a.confidence)
                w2 = b.confidence / (1.0 - b.confidence)
                weight = w1 + w2
                if weight == 0:
                    raise PLNRejected(Status.UNKNOWN, "zero evidence weight")
                strength = min(1.0, ((w1 * a.strength) + (w2 * b.strength)) / weight)
                confidence = min(1.0, max(max(weight / (weight + 1.0), a.confidence), b.confidence))
            return TruthValue(strength, confidence)
        except (ValueError, ArithmeticError) as error:
            raise PLNRejected(Status.FAIL, "invalid finite empirical formula result") from error
