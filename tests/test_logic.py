from itertools import combinations
import random
import unittest

from reachability.logic import check_consistency
from reachability.model import Clause, Literal, Statement, Status
from tests.oracle import satisfying_assignment


def render(clauses):
    return tuple(Clause(tuple(Literal(Statement(f"v{abs(n)}"), n > 0) for n in clause))
                 for clause in clauses)


class LogicTests(unittest.TestCase):
    def test_joint_contradiction_has_satisfiable_pairs(self):
        raw = ((1,), (2,), (-1, -2))
        self.assertIsNone(satisfying_assignment(raw))
        self.assertEqual(check_consistency(render(raw)).status, Status.FAIL)
        for pair in combinations(raw, 2):
            self.assertIsNotNone(satisfying_assignment(pair))

    def test_empty_and_tautological_formulas(self):
        for raw, expected in (((), Status.PASS), (((),), Status.FAIL),
                              (((1, -1),), Status.PASS)):
            with self.subTest(raw=raw):
                self.assertEqual(check_consistency(render(raw)).status, expected)

    def test_capacity_is_unknown_without_truncation(self):
        result = check_consistency(render(((1, 2, 3),)), max_variables=2)
        self.assertEqual(result.status, Status.UNKNOWN)
        self.assertIsNone(result.witness)

    def test_unsupported_constraint_is_unknown(self):
        self.assertEqual(check_consistency(("unsupported",)).status, Status.UNKNOWN)

    def test_independent_oracle_and_witnesses_on_generated_formulas(self):
        rng = random.Random(20261001)
        for case in range(400):
            raw = tuple(tuple(rng.choice((-1, 1)) * rng.randint(1, 6)
                              for _ in range(rng.randint(0, 4)))
                        for _ in range(rng.randint(0, 14)))
            with self.subTest(case=case, formula=raw):
                expected = satisfying_assignment(raw)
                result = check_consistency(render(raw))
                self.assertEqual(result.status is Status.PASS, expected is not None)
                if result.status is Status.PASS:
                    witness = {int(s.predicate[1:]): value for s, value in result.witness}
                    self.assertTrue(all(any(witness[abs(n)] == (n > 0) for n in clause)
                                        for clause in raw))

    def test_renaming_and_order_preserve_admission(self):
        raw = ((1, 2), (-1, 3), (-2, 3), (-3,))
        renamed = tuple(tuple((1 if n > 0 else -1) * (10 + abs(n))
                              for n in reversed(c)) for c in reversed(raw))
        self.assertEqual(check_consistency(render(raw)).status,
                         check_consistency(render(renamed)).status)
