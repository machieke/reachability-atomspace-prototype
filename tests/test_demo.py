import unittest

from reachability.demo import run
from reachability.recovery_demo import run as recover
from reachability.lifecycle_demo import run as lifecycle
from reachability.execution_demo import run as execution
from reachability.dispatch_demo import run as dispatch
from reachability.goal_demo import run as goal


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

    def test_lifecycle_history_and_current_validity_are_separate(self):
        result = lifecycle()
        self.assertEqual(result["ack_outcome"], "UNKNOWN")
        self.assertEqual(result["wrong_product"], "FAIL")
        self.assertEqual(result["stage_after_restart"], "BUILT")
        self.assertEqual(result["artifact_validity_after_credential_revocation"], "PASS")
        self.assertEqual(result["stage_after_product_revocation"], "BUILT")
        self.assertEqual(result["validity_after_product_revocation"], "STALE")
        self.assertEqual(result["historical_transitions"], 1)

    def test_atomic_resource_intent_and_recovery(self):
        result = execution()
        self.assertEqual(result["competing_reservation"], "STALE")
        self.assertTrue(result["same_intent_after_restart"])
        self.assertEqual(result["held_units_after_restart"], 1)
        self.assertEqual(result["readiness_after_credential_revocation"], "UNKNOWN")
        self.assertEqual(result["state_at_expiry"], "expired")
        self.assertEqual(result["held_units_at_expiry"], 0)
        self.assertEqual(result["observed_milestones"], [])

    def test_dispatch_reconciles_same_attempt_and_fences_remote_release(self):
        result = dispatch()
        self.assertEqual(result["after_lost_reply"], "uncertain")
        self.assertEqual(result["after_restart_reconciliation"], "accepted")
        self.assertTrue(result["same_request"])
        self.assertTrue(result["capacity_held_after_lease_expiry"])
        self.assertTrue(result["resources_released"])
        self.assertEqual(result["late_submission"], "released")
        self.assertEqual(result["historical_effects"], 1)
        self.assertEqual(result["lifecycle_stage"], "READY")
        self.assertEqual(result["operation_outcome"], "UNKNOWN")

    def test_deployment_goal_requires_three_samples_and_reopens_after_failure(self):
        result = goal()
        self.assertEqual(result["missing_submission_credential"], "UNKNOWN")
        self.assertEqual(result["before_dispatch"], {"outstanding": 10, "covered": 6, "open": 4})
        self.assertEqual(result["outstanding_after_ack"], 10)
        self.assertEqual(result["wrong_product"], "FAIL")
        self.assertEqual(result["loss_after_health_samples"], [10, 10, 0])
        self.assertEqual(result["credential_at_completion"], "STALE")
        self.assertEqual(result["completion_certificate"], "PASS")
        self.assertEqual(result["stage_after_later_failure_and_restart"], "BUILT")
        self.assertEqual(result["outstanding_after_later_failure"], 10)
        self.assertEqual(result["relief_history"], ["observed_relief", "reopened"])
        self.assertFalse(result["causal_credit_assigned"])
