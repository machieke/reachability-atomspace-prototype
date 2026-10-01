from fractions import Fraction
from itertools import combinations_with_replacement, product
from unittest import TestCase

from reachability.probability_formula import three_event_joint


class ProbabilityJointOracleTests(TestCase):
    def test_exact_joint_feasibility_against_enumerated_four_observation_worlds(self):
        # Independent oracle: enumerate every multiset of four Boolean worlds.
        # Integer-quarter marginals and pairs admit a quarter-grid witness iff
        # any real witness exists for this three-variable fragment.
        worlds = tuple(product((0, 1), repeat=3))
        possible = set()
        for sample in combinations_with_replacement(worlds, 4):
            totals = tuple(sum(world[i] for world in sample) for i in range(3))
            pairs = tuple(sum(world[a]*world[b] for world in sample) for a, b in ((0, 1), (1, 2), (0, 2)))
            possible.add(totals + pairs)
        for values in product(range(5), repeat=6):
            exact = tuple(Fraction(x, 4) for x in values)
            witness = three_event_joint(exact[:3], exact[3:])
            self.assertEqual(witness is not None, values in possible, values)
            if witness is not None:
                self.assertTrue(all(x >= 0 for x in witness))
                self.assertEqual(sum(witness), 1)
                # Reconstruct the supplied constraints from the actual witness.
                order = ((1,1,1), (1,1,0), (1,0,1), (0,1,1), (1,0,0), (0,1,0), (0,0,1), (0,0,0))
                totals = tuple(sum(w[i]*mass for w, mass in zip(order, witness)) for i in range(3))
                pairs = tuple(sum(w[a]*w[b]*mass for w, mass in zip(order, witness)) for a,b in ((0,1),(1,2),(0,2)))
                self.assertEqual(totals + pairs, exact)

    def test_pairwise_consistency_does_not_imply_joint_consistency(self):
        # Three pairwise disjoint half-probability events cannot fit in one world.
        self.assertIsNone(three_event_joint((.5, .5, .5), (0, 0, 0)))
