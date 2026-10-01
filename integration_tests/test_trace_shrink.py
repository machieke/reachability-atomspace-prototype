"""Reduced shared-lineage witness against actual pinned native PLN inference."""
from tempfile import TemporaryDirectory
import unittest

from validation_lab.run_shrink import CORPUS, ROOT, read, source_seed, verify_corpus
from validation_lab.shrink_replay import ReplayPredicate


class NativeTraceShrinkTests(unittest.TestCase):
    def test_reduced_M05_control_mutant_and_deletions_with_native_inference(self):
        verify_corpus()
        seed = source_seed('M05')
        expected = read(ROOT/CORPUS/'expected'/'M05.json')
        reduced = expected['reduced_events']
        with TemporaryDirectory() as directory:
            predicate = ReplayPredicate('admission', seed['initial'], seed['case'], 'M05', directory, native=True)
            actual = predicate(reduced, 0)
            self.assertEqual(actual['kind'], 'WITNESS')
            self.assertEqual(actual['signature'], expected['signature'])
            self.assertTrue(actual['control_passed'])
            self.assertGreater(actual['invocations'], 0)
            for index in range(len(reduced)):
                actual = predicate(reduced[:index]+reduced[index+1:], index+1)
                self.assertEqual(actual['kind'], 'NO_WITNESS')
