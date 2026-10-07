"""Actual native formula and authority projection remain distinct from world truth."""
import unittest,json
from pathlib import Path
from tempfile import TemporaryDirectory
from world_lab.run import episode


class NativeIndependentWorldTests(unittest.TestCase):
    def check_case(self,parent):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)/'run';result=episode(parent,root,native=True)
            self.assertEqual(result['conformance'],'PASS',result.get('traceback'));self.assertEqual(len(result['runtime_calls']),2)
            self.assertTrue(result['reconstruction']['authority_equal']);self.assertTrue(result['reconstruction']['projection_equal'])
            self.assertEqual(result['reconstruction']['native_calls_before'],result['reconstruction']['native_calls_after'])
            for call in result['runtime_calls']:self.assertEqual(call['mode'],'native');self.assertTrue(call['formula_agreement']);self.assertEqual(call['commit_status'],'PASS')
            return result
    def test_native_observable_physical_and_observed_completion(self):self.assertEqual(self.check_case('observable')['metrics']['first_observed_completion'],3)
    def test_native_unobservable_success_does_not_create_certified_relief(self):
        m=self.check_case('unobservable')['metrics'];self.assertEqual((m['final_physical_deficit'],m['final_observed_loss']),(0,10))
    def test_native_regression_retains_history_and_recognizes_later_failure(self):
        m=self.check_case('regression')['metrics'];self.assertTrue(m['historical_completion']);self.assertEqual(m['recognition'][0]['lag'],1)
