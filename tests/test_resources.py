from dataclasses import replace
from itertools import combinations
from random import Random
import unittest

from reachability.execution_model import ExecutionContract, ResourceClaim, ResourceDefinition, ResourceDemand
from reachability.model import Status
from reachability.resources import check_capacity


class CapacityTests(unittest.TestCase):
    def test_joint_portfolio_rejects_conflict_even_when_every_pair_fits(self):
        resource = ResourceDefinition("slot", 2, "slots")
        claims = tuple(ResourceClaim("slot", 1, "slots", 0, 10) for _ in range(3))
        for pair in combinations(claims, 2):
            self.assertEqual(check_capacity(resource, pair).status, Status.PASS)
        self.assertEqual(check_capacity(resource, claims).status, Status.FAIL)

    def test_adjacent_intervals_release_at_the_exact_boundary(self):
        resource = ResourceDefinition("slot", 1, "slots")
        self.assertEqual(check_capacity(resource, (ResourceClaim("slot", 1, "slots", 0, 5),
                         ResourceClaim("slot", 1, "slots", 5, 10))).status, Status.PASS)
        self.assertEqual(check_capacity(resource, (ResourceClaim("slot", 1, "slots", 0, 6),
                         ResourceClaim("slot", 1, "slots", 5, 10))).status, Status.FAIL)

    def test_capacity_matches_independent_discrete_time_enumeration(self):
        random = Random(3186)
        for _ in range(500):
            capacity = random.randrange(5)
            raw = [(random.randrange(1, 4), random.randrange(8), random.randrange(1, 5))
                   for _ in range(random.randrange(8))]
            # Independent oracle: sum occupancy at every integer time, without
            # runtime records or the implementation's boundary sweep.
            expected = all(sum(q for q, start, duration in raw if start <= t < start + duration) <= capacity
                           for t in range(13))
            claims = tuple(ResourceClaim("slot", q, "slots", start, start + duration) for q, start, duration in raw)
            result = check_capacity(ResourceDefinition("slot", capacity, "slots"), claims)
            self.assertEqual(result.status, Status.PASS if expected else Status.FAIL, raw)

    def test_units_identity_and_modes_fail_closed(self):
        resource = ResourceDefinition("slot", 2, "slots")
        claim = ResourceClaim("slot", 1, "slots", 0, 10)
        for bad in (replace(claim, unit="bytes"), replace(claim, resource_id="other")):
            self.assertEqual(check_capacity(resource, (bad,)).status, Status.FAIL)
        self.assertEqual(check_capacity(replace(resource, mode="consumable"), (claim,)).status, Status.UNKNOWN)

    def test_exact_quantities_and_nonempty_intervals(self):
        for quantity in (True, False, -1, 0, 1.5, "1"):
            with self.subTest(quantity=quantity), self.assertRaises(ValueError):
                ResourceDemand("slot", quantity, "slots")
        for capacity in (True, -1, 0.5):
            with self.assertRaises(ValueError):
                ResourceDefinition("slot", capacity, "slots")
        for start, end in ((0, 0), (2, 1), (False, 1), (0, 1.0)):
            with self.assertRaises(ValueError):
                ResourceClaim("slot", 1, "slots", start, end)

    def test_duplicate_resource_demands_are_not_silently_deduplicated(self):
        demand = ResourceDemand("slot", 1, "slots")
        with self.assertRaises(ValueError):
            ExecutionContract("c", "1", "s", "1", "edge", "executor", ("worker",), (demand, demand), 10)
