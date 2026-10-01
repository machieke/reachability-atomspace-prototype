from dataclasses import replace
import random
import unittest

from reachability.model import Clause, Status
from reachability.requirements import Requirement, evaluate
from reachability.service import AdmissionService
from tests.lifecycle_support import accept, fact
from tests.oracle import requirement_truth
from tests.support import Driver, lit

A, B, C, D = (lit(n) for n in "ABCD")


class RequirementTests(unittest.TestCase):
    def setUp(self):
        self.service = AdmissionService()
        self.driver = Driver(self.service)
        self.driver.context()

    def test_missing_and_has_no_authorized_partial_witness(self):
        accept(self.driver, A)
        result = self.service.inspect_requirements("ctx", Requirement("AND", children=(fact(A), fact(B))))
        self.assertEqual(result.status, Status.UNKNOWN)
        self.assertEqual(result.witnesses, ())

    def test_or_needs_one_complete_branch(self):
        expression = Requirement("OR", children=(Requirement("AND", children=(fact(A), fact(B))),
                                                  Requirement("AND", children=(fact(C), fact(D)))))
        accept(self.driver, A)
        accept(self.driver, D)
        self.assertEqual(self.service.inspect_requirements("ctx", expression).status, Status.UNKNOWN)
        accept(self.driver, B)
        result = self.service.inspect_requirements("ctx", expression)
        self.assertEqual(result.status, Status.PASS)
        self.assertEqual({w.literal for w in result.witnesses}, {A, B})
        self.assertEqual(result.selected_branches, (((), 0),))
        self.assertEqual({w.path for w in result.witnesses}, {(0, 0), (0, 1)})

    def test_or_can_use_a_valid_branch_despite_another_failed_branch(self):
        accept(self.driver, A.negate())
        accept(self.driver, B)
        result = self.service.inspect_requirements("ctx", Requirement("OR", children=(fact(A), fact(B))))
        self.assertEqual(result.status, Status.PASS)
        self.assertEqual(result.selected_branches, (((), 1),))
        self.assertEqual([w.literal for w in result.witnesses], [B])

    def test_unknown_is_distinct_from_contrary_evidence(self):
        self.assertEqual(self.service.inspect_requirements("ctx", fact(A)).status, Status.UNKNOWN)
        accept(self.driver, A.negate())
        self.assertEqual(self.service.inspect_requirements("ctx", fact(A)).status, Status.FAIL)

    def test_entire_joint_constraint_scope_is_checked(self):
        accept(self.driver, A)
        accept(self.driver, B)
        # Deliberately inconsistent evaluator snapshot: every pair is satisfiable.
        snapshot = replace(self.service.snapshot("ctx"), constraints=(Clause((A.negate(), B.negate())),))
        result = evaluate(Requirement("AND", children=(fact(A), fact(B))), snapshot)
        self.assertEqual(result.status, Status.FAIL)
        self.assertEqual(result.witnesses, ())

    def test_witnesses_cannot_cross_contexts(self):
        self.driver.context("other")
        a = accept(self.driver, A, context="other")
        snapshot = replace(self.service.snapshot("ctx"), usable=(a,))
        self.assertEqual(evaluate(fact(A), snapshot).status, Status.UNKNOWN)

    def test_unsupported_scope_and_limits_fail_closed(self):
        for operator in ("DURING", "K_OF_N", "NOT"):
            self.assertEqual(self.service.inspect_requirements("ctx", Requirement(operator)).status, Status.UNKNOWN)
        expression = fact(A)
        for _ in range(33):
            expression = Requirement("AND", children=(expression,))
        self.assertEqual(self.service.inspect_requirements("ctx", expression).status, Status.UNKNOWN)
        for operator in ("AND", "OR"):
            with self.assertRaises(ValueError):
                Requirement(operator)

    def test_support_fingerprint_changes_with_exact_witness_and_revision(self):
        first = accept(self.driver, A, evidence_id="first")
        before = self.service.inspect_requirements("ctx", fact(A))
        self.service.revoke_evidence("first", idempotency_key=self.driver.key())
        second = accept(self.driver, A, evidence_id="second")
        after = self.service.inspect_requirements("ctx", fact(A))
        self.assertEqual(before.witnesses[0].belief_revision_id, first.belief_revision_id)
        self.assertEqual(after.witnesses[0].belief_revision_id, second.belief_revision_id)
        self.assertNotEqual(before.support_fingerprint, after.support_fingerprint)

    def test_generated_expressions_match_independent_three_valued_oracle(self):
        rng = random.Random(41721)
        literals = dict(enumerate((A, B, C, D)))

        def expression(depth):
            if depth == 0 or rng.random() < 0.4:
                return ("FACT", rng.randrange(4))
            return (rng.choice(("AND", "OR")), *(expression(depth - 1) for _ in range(rng.randint(1, 3))))

        def render(expr):
            return fact(literals[expr[1]]) if expr[0] == "FACT" else Requirement(
                expr[0], children=tuple(render(child) for child in expr[1:]))

        for world in range(12):
            context = f"world-{world}"
            self.driver.context(context)
            values = {variable: rng.choice((True, False, None)) for variable in literals}
            for variable, value in values.items():
                if value is not None:
                    accept(self.driver, literals[variable] if value else literals[variable].negate(), context=context)
            for case in range(20):
                expr = expression(3)
                expected = requirement_truth(expr, values)
                result = self.service.inspect_requirements(context, render(expr))
                with self.subTest(world=world, case=case):
                    self.assertEqual(result.status, {True: Status.PASS, False: Status.FAIL, None: Status.UNKNOWN}[expected])
