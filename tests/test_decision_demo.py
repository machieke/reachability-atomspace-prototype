import unittest

from reachability.decision_demo import run


class DeploymentDecisionTests(unittest.TestCase):
    native = False

    def test_forecast_expiry_does_not_rewrite_submission_or_observed_completion(self):
        result = run(native=self.native)
        self.assertEqual(result["missing_forecast"], "UNKNOWN")
        self.assertEqual(result["submission_decision"], "PASS")
        self.assertAlmostEqual(result["forecast_strength"], .68)
        self.assertAlmostEqual(result["forecast_confidence"], .3584)
        self.assertEqual(result["forecast_as_hard_fact"], "UNKNOWN")
        self.assertEqual(result["current_decision_after_expiry"], "STALE")
        self.assertEqual(result["completion_certificate"], "PASS")
        self.assertEqual(result["before_dispatch"], dict(outstanding=10, covered=6, open=4))
        self.assertEqual(result["outstanding_after_ack"], 10)
        self.assertEqual(result["loss_after_health_samples"], [10, 10, 0])
        self.assertEqual(result["wrong_product"], "FAIL")
        self.assertEqual(result["stage_after_later_failure_and_restart"], "BUILT")
        self.assertEqual(result["outstanding_after_later_failure"], 10)
        self.assertFalse(result["causal_credit_assigned"])
        self.assertTrue(result["recovered_identical_deployment_snapshot"])
        if self.native:
            self.assertTrue(result["native_projection_identical_after_restart"])
