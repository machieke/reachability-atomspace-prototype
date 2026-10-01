"""The same probability contracts with native PLN inference and native projection."""
from reachability.atomspace_adapter import project_probability
from reachability.pln_adapter import PLNAdapter
from reachability.probability_formula import PinnedFormulaRuntime
from reachability.service import AdmissionService
from tests import test_probability as contract
from tests.test_pln_contracts import snapshot
from unittest import TestCase
import random

from reachability.pln_adapter import TruthValue


class NativeProbabilityContractTests(contract.DurableProbabilityContractTests):
    def setUp(self):
        super().setUp()
        self.driver.adapter = PLNAdapter()

    def tearDown(self):
        expected = {name: project_probability(self.service, name) for name in self.service._contexts}
        self.service.close()
        with AdmissionService(database=self.database) as recovered:
            self.assertEqual({name: project_probability(recovered, name) for name in expected}, expected)


class PinnedFormulaConformanceTests(TestCase):
    def test_native_and_replay_binary64_results_match_exactly(self):
        native, checked = PLNAdapter(), PLNAdapter(PinnedFormulaRuntime())
        rng = random.Random(7612)
        grid = (.125, .25, .375, .5, .625, .75, .875)
        for _ in range(20):
            p, q, r = (rng.choice(grid) for _ in range(3))
            confidences = tuple(rng.random() for _ in range(5))
            rule, data = snapshot((p, q, r, q, r), confidences)
            self.assertEqual(native.apply_rule(rule, data), checked.apply_rule(rule, data))
            pair = tuple(TruthValue(rng.random(), rng.random()) for _ in range(2))
            expected = checked.runtime.evaluate("Truth_Revision", pair)
            actual = native.runtime.evaluate("Truth_Revision", pair)
            self.assertEqual((actual.strength.hex(), actual.confidence.hex()),
                             (expected.strength.hex(), expected.confidence.hex()))
