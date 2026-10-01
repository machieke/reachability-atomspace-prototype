from itertools import product
from random import Random
import unittest

from reachability.goal_logic import evaluate_durability
from reachability.goal_model import DurabilityContract, GoalMonitor, GoalSample
from reachability.model import Status
from tests.goal_support import GoalFixture


class DurabilityOracleTests(unittest.TestCase):
    def test_search_limit_is_unknown_even_when_a_later_complete_witness_exists(self):
        contract = DurabilityContract(8, 1, 1, ("monitor",))
        monitor = GoalMonitor("window", "healthy", 0)
        samples = [GoalSample(f"{t}:{root}", "g", "healthy", "window", "p", True, t,
                             f"{t}:{root}", f"{t}:{root}", (str(root),))
                   for t in range(8) for root in range(7)]
        # Every early first choice exhausts seven roots across eight positions.
        # Choosing this last alternative first would leave an explicit full set.
        samples.append(GoalSample("zz", "g", "healthy", "window", "p", True, 0, "zz", "zz", ("extra",)))
        result = evaluate_durability(contract, monitor, tuple(samples),
            frozenset(sample.belief_revision_id for sample in samples), 7, Status.PASS)
        self.assertEqual(result.label, "UNKNOWN")

    def test_witness_alternative_limit_is_unknown_instead_of_truncated_success(self):
        contract = DurabilityContract(3, 1, 1, ("monitor",))
        monitor = GoalMonitor("window", "healthy", 0)
        samples = tuple(GoalSample(str(i), "g", "healthy", "window", "p", True, i % 3,
                                   str(i), str(i), (str(i),)) for i in range(257))
        result = evaluate_durability(contract, monitor, samples, frozenset(str(i) for i in range(257)), 2, Status.PASS)
        self.assertEqual(result.label, "UNKNOWN")

    def test_sampled_windows_match_independent_three_state_timeline_enumeration(self):
        contract = DurabilityContract(3, 1, 1, ("monitor",))
        monitor = GoalMonitor("window", "healthy", 0)
        for world in product((-1, 0, 1), repeat=4):
            samples = tuple(GoalSample(str(t), "g", "healthy", "window", "p", value == 1, t,
                str(t), str(t), (str(t),)) for t, value in enumerate(world) if value)
            for now in range(5):
                history = world[:now + 1]
                if not any(history):
                    expected = "PENDING" if now < 2 else "UNKNOWN"
                elif now >= len(world) or world[now] == 0:
                    expected = "UNKNOWN"
                elif -1 in history[max(0, now - 2):now + 1]:
                    expected = "OBSERVED_FAILURE"
                elif now < 2:
                    expected = "PENDING"
                elif history[now - 2:now + 1] == (1, 1, 1):
                    expected = "OBSERVED_SUCCESS"
                else:
                    expected = "UNKNOWN"
                actual = evaluate_durability(contract, monitor, samples,
                    frozenset(sample.belief_revision_id for sample in samples), now, Status.PASS)
                self.assertEqual(actual.label, expected, (world, now))


class CoverageOracleTests(GoalFixture, unittest.TestCase):
    def test_overlapping_promises_match_union_of_explicit_atomic_obligations(self):
        random = Random(499)
        for _ in range(40):
            atomic_obligations, promises = set(), []
            for _ in range(random.randrange(1, 5)):
                slice_id, size = random.choice((("healthy", 6), ("available", 4)))
                units = random.randrange(1, size + 1)
                promises.append(self.cover(units, slice_id))
                atomic_obligations.update((slice_id, unit) for unit in range(units))
            self.assertEqual(self.projection().estimated_committed_coverage, len(atomic_obligations))
            for promise in promises:
                self.service.withdraw_goal_coverage(promise.commitment_id, "worker", idempotency_key=self.driver.key())
