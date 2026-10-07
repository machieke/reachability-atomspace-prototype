"""Fresh pinned-native selected work and exact AtomSpace/journal reconstruction."""
import unittest,json
from pathlib import Path
from tempfile import TemporaryDirectory
from work_loop_lab.run import episode


class NativeWorkLoopTests(unittest.TestCase):
    def check(self,parent):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)/'run';r=episode(parent,root,native=True)
            self.assertEqual(r['conformance'],'PASS',r.get('traceback'));self.assertTrue(r['runtime_calls'])
            self.assertTrue(r['reconstruction']['authority_equal']);self.assertTrue(r['reconstruction']['projection_equal'])
            self.assertEqual(r['reconstruction']['native_calls_before'],r['reconstruction']['native_calls_after'])
            self.assertEqual(r['setup_formula_calls'],0)
            for call in r['runtime_calls']:self.assertEqual(call['mode'],'native');self.assertTrue(call['formula_agreement']);self.assertEqual(call['commit_status'],'PASS')
            return r
    def test_positive_native_information_to_observed_completion(self):self.assertEqual(self.check('positive')['outstanding'],0)
    def test_shared_native_revision_selected_once(self):self.assertEqual(len(self.check('shared')['runtime_calls']),1)
    def test_fresh_registry_native_result_does_not_satisfy_old_role(self):self.assertEqual(self.check('freshness')['effects'],0)
    def test_native_adverse_investigation_blocks_external_action(self):self.assertEqual(self.check('adverse')['effects'],0)
