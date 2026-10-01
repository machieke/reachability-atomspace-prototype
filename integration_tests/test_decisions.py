"""Run identical decision contracts with real PLN and AtomSpace projections."""
import math
import unittest

from reachability.atomspace_adapter import RecordProjection, project_execution_decision, project_probability
from reachability.pln_adapter import PLNAdapter
from tests import test_decisions as contracts
from tests import test_decision_demo as deployment


class NativeDecisionContractTests(contracts.DurableDecisionContractTests):
    def setUp(self):
        super().setUp()
        self.numeric.adapter = PLNAdapter()

    def tearDown(self):
        before = project_probability(self.service, "ctx")
        intents = {attempt: project_execution_decision(self.service, attempt)
                   for attempt in self.service._execution.intents}
        super().tearDown()
        self.assertEqual(project_probability(self.service, "ctx"), before)
        self.assertEqual({attempt: project_execution_decision(self.service, attempt) for attempt in intents}, intents)


class NativeDeploymentDecisionTests(deployment.DeploymentDecisionTests):
    native = True


class NativeDecisionProjectionTests(unittest.TestCase):
    def test_ordered_numeric_tuples_preserve_type_exact_integers_and_signed_zero(self):
        projection = RecordProjection()
        values = (0, 1, 2**100, -1, 0.0, -0.0, True, "1")
        atoms = tuple(projection.add(value) for value in values)
        container = projection.batch.link(atoms)
        graph = projection.batch.run()
        refs = tuple(graph.aliases[atom] for atom in atoms)
        self.assertEqual(len(set(refs)), len(values))
        self.assertEqual(graph.atoms[graph.aliases[container]], ("L", refs))
        def stored(ref):
            return next(v for (atom, _), v in graph.values.items() if atom == ref)
        self.assertEqual(stored(refs[2]), str(2**100))
        self.assertEqual(math.copysign(1, stored(refs[4])[0]), 1)
        self.assertEqual(math.copysign(1, stored(refs[5])[0]), -1)
