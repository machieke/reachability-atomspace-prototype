from dataclasses import replace
from fractions import Fraction
from itertools import product
import math
from unittest import TestCase

from reachability.model import Literal, Statement, Status
from reachability.pln_adapter import (
    DeductionRule, IndependenceDeclaration, PLNAdapter, PLNRejected,
    ProbabilisticSupport, ProbabilitySnapshot, TruthValue, conditional_consistent,
)


def snapshot(strengths=(.4, .5, .6, .7, .8), confidences=(.9, .9, .9, .8, .7)):
    rule = DeductionRule("P", "Q", "R")
    supports = tuple(ProbabilisticSupport(f"s{i}", "world", literal, TruthValue(s, c),
                                        (f"e{i}",), (f"origin{i}",))
                     for i, (literal, s, c) in enumerate(zip(rule.premises, strengths, confidences)))
    return rule, ProbabilitySnapshot("world", 7, supports)


class RecordingRuntime:
    """A call recorder for guard tests, not an inference oracle or native substitute."""
    def __init__(self):
        self.calls = []

    def evaluate(self, formula, truths):
        self.calls.append((formula, truths))
        return TruthValue(.5, .5)


class PLNContractTests(TestCase):
    def setUp(self):
        self.runtime = RecordingRuntime()
        self.adapter = PLNAdapter(self.runtime)
        self.rule, self.snapshot = snapshot()

    def test_nonfinite_out_of_range_and_wrong_interpretation_rejected(self):
        for s, c in ((float("nan"), .5), (.5, float("inf")), (-.1, .5),
                     (1.1, .5), (.5, -.1), (.5, 1), (.5, True), ("0.5", .5)):
            with self.subTest(s=s, c=c), self.assertRaises(ValueError):
                TruthValue(s, c)
        with self.assertRaises(ValueError):
            TruthValue(.5, .5, "logical-certainty")

    def test_exact_boundaries_against_four_cell_joint_distribution(self):
        grid = [Fraction(i, 4) for i in range(5)]
        for a, b, conditional in product(grid, repeat=3):
            intersection = a * conditional
            cells = (intersection, a - intersection, b - intersection,
                     1 - a - b + intersection)
            expected = a > 0 and all(cell >= 0 for cell in cells)
            self.assertEqual(conditional_consistent(float(a), float(b), float(conditional)), expected)

    def test_just_outside_boundary_never_accepted_by_epsilon(self):
        self.assertTrue(conditional_consistent(.5, .25, .5))
        self.assertFalse(conditional_consistent(.5, .25, math.nextafter(.5, 1)))

    def test_invalid_probabilities_never_reach_runtime(self):
        rule, data = snapshot((.9, .1, .5, .9, .5))
        with self.assertRaises(PLNRejected) as error:
            self.adapter.apply_rule(rule, data)
        self.assertEqual(error.exception.status, Status.FAIL)
        self.assertEqual(self.runtime.calls, [])

    def test_zero_antecedent_is_unknown(self):
        rule, data = snapshot((0, .5, .5, .5, .5))
        self.assertEqual(self.adapter.check_rule_preconditions(rule, data).status, Status.UNKNOWN)

    def test_premise_roles_are_ordered(self):
        data = replace(self.snapshot, supports=tuple(reversed(self.snapshot.supports)))
        self.assertEqual(self.adapter.check_rule_preconditions(self.rule, data).status, Status.FAIL)
        with self.assertRaises(PLNRejected):
            self.adapter.apply_rule(self.rule, data)
        self.assertEqual(self.runtime.calls, [])

    def test_scope_identity_and_immutability(self):
        first = self.snapshot.supports[0]
        with self.assertRaises(ValueError):
            replace(self.snapshot, context_id="elsewhere")
        with self.assertRaises(ValueError):
            replace(self.snapshot, supports=(first, replace(first, truth=TruthValue(.1, .1))))
        with self.assertRaises(ValueError):
            replace(self.snapshot, supports=list(self.snapshot.supports))
        with self.assertRaises(ValueError):
            replace(first, lineage_roots=())

    def test_pure_deterministic_proposal_keeps_lineage(self):
        original = self.snapshot
        a = self.adapter.apply_rule(self.rule, original)
        b = self.adapter.apply_rule(self.rule, original)
        self.assertEqual(a, b)
        self.assertEqual(self.snapshot, original)
        self.assertEqual(a.support.evidence_ids, tuple(f"e{i}" for i in range(5)))
        self.assertEqual(a.support.lineage_roots, tuple(f"origin{i}" for i in range(5)))
        self.assertEqual(a.knowledge_revision, 7)
        self.assertEqual(self.adapter.explain(a)["premises"], tuple(f"s{i}" for i in range(5)))
        self.assertIn("Truth_Deduction", a.formula_id)
        other = replace(original, context_id="other", supports=tuple(
            replace(s, context_id="other") for s in original.supports))
        self.assertNotEqual(a.support.support_id, self.adapter.apply_rule(self.rule, other).support.support_id)

    def test_cycle_is_not_new_support(self):
        supports = self.snapshot.supports
        changed = replace(supports[0], ancestors=(self.rule.conclusion,))
        data = replace(self.snapshot, supports=(changed, *supports[1:]))
        with self.assertRaises(PLNRejected) as error:
            self.adapter.apply_rule(self.rule, data)
        self.assertEqual(error.exception.status, Status.UNKNOWN)
        self.assertEqual(self.runtime.calls, [])

    def pair(self):
        a = self.snapshot.supports[0]
        b = replace(a, support_id="independent", evidence_ids=("other",), lineage_roots=("other-origin",))
        return a, b

    def test_duplicate_revision_never_calls_formula(self):
        a, _ = self.pair()
        result = self.adapter.revise(a, a, 7)
        self.assertEqual(result.alternatives, (a,))
        self.assertIsNone(result.proposal)
        self.assertEqual(self.runtime.calls, [])

    def test_disjoint_ids_alone_do_not_justify_revision(self):
        a, b = self.pair()
        result = self.adapter.revise(a, b, 7)
        self.assertEqual(result.status, Status.UNKNOWN)
        self.assertEqual(len(result.alternatives), 2)
        self.assertEqual(self.runtime.calls, [])

    def test_common_origin_overrides_independence_assertion(self):
        a, b = self.pair()
        for b in (replace(b, lineage_roots=a.lineage_roots), replace(b, evidence_ids=a.evidence_ids)):
            result = self.adapter.revise(a, b, 7, IndependenceDeclaration("claimed", (a, b)))
            self.assertEqual(result.status, Status.UNKNOWN)
        self.assertEqual(self.runtime.calls, [])

    def test_declaration_must_bind_exact_support(self):
        a, b = self.pair()
        wrong = replace(b, truth=TruthValue(.1, .2))
        result = self.adapter.revise(a, b, 7, IndependenceDeclaration("wrong", (a, wrong)))
        self.assertEqual(result.status, Status.FAIL)
        self.assertEqual(self.runtime.calls, [])

    def test_revision_commutes_and_duplicate_roots_do_not_accumulate(self):
        a, b = self.pair()
        declaration = IndependenceDeclaration("two-independent-samples", (a, b))
        forward = self.adapter.revise(a, b, 7, declaration)
        backward = self.adapter.revise(b, a, 7, declaration)
        self.assertEqual(forward, backward)
        combined = forward.proposal.support
        again = self.adapter.revise(combined, a, 7, IndependenceDeclaration("bad", (combined, a)))
        self.assertEqual(again.status, Status.UNKNOWN)
        self.assertEqual(len(self.runtime.calls), 2)

    def test_zero_weight_is_unknown_and_wrong_claim_fails(self):
        a, b = self.pair()
        a, b = replace(a, truth=TruthValue(.5, 0)), replace(b, truth=TruthValue(.5, 0))
        result = self.adapter.revise(a, b, 7, IndependenceDeclaration("zero", (a, b)))
        self.assertEqual(result.status, Status.UNKNOWN)
        self.assertEqual(self.adapter.revise(a, replace(b, conclusion=b.conclusion.negate()), 7).status, Status.FAIL)
        self.assertEqual(self.runtime.calls, [])
