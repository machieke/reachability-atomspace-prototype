import unittest

from reachability.demo import run
from reachability.recovery_demo import run as recover


class DemoTests(unittest.TestCase):
    def test_public_workflow(self):
        result = run()
        self.assertEqual(result["missing_premise"], "UNKNOWN")
        self.assertEqual(result["complete_inference"], "PASS")
        self.assertEqual(result["contradictory_result"], "FAIL")
        self.assertEqual(result["commit_after_revocation"], "STALE")
        self.assertEqual(result["current_conclusion_after_revocation"], "STALE")
        self.assertEqual(result["historical_conclusions_retained"], 1)
        self.assertEqual(result["lineage_roots"], ["sensor-origin"])

    def test_recovered_workflow_and_scoped_expiry(self):
        result = recover()
        self.assertEqual(result["after_restart"], "PASS")
        self.assertTrue(result["same_accepted_revision"])
        self.assertEqual(result["at_credential_expiry"], "STALE")
        self.assertEqual(result["artifact_test_after_expiry"], "PASS")
        self.assertEqual(result["historical_ready_records"], 1)
