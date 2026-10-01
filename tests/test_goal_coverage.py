import unittest
from dataclasses import replace

from reachability.service import AdmissionDenied
from tests.goal_support import GoalFixture
from tests.lifecycle_support import observe


class CoverageTests(GoalFixture, unittest.TestCase):
    def test_six_covered_units_leave_ten_outstanding_and_four_open(self):
        self.cover()
        projection = self.projection()
        self.assertEqual((projection.outstanding_loss, projection.estimated_committed_coverage, projection.open_loss), (10, 6, 4))
        self.assertTrue(projection.slices[0].observation_required)
        self.assertEqual(self.reconcile().events, ())

    def test_overlapping_promises_use_maximum_and_distinct_slices_add(self):
        self.cover(3)
        self.cover(4)
        self.cover(4)
        self.cover(4, "available")
        self.assertEqual(self.projection().estimated_committed_coverage, 8)
        self.cover(6)
        self.cover(6)
        self.assertEqual(self.projection().estimated_committed_coverage, 10)
        self.assertEqual(self.projection().outstanding_loss, 10)

    def test_coverage_is_capped_by_outstanding_loss_after_partial_relief(self):
        self.cover(6)
        self.cover(4, "available")
        self.product()
        self.sample(0, slice_id="available")
        projection = self.projection()
        self.assertEqual((projection.outstanding_loss, projection.estimated_committed_coverage, projection.open_loss), (6, 6, 0))
        self.assertEqual(self.reconcile().events[0].units, 4)

    def test_coverage_expiry_reopens_work_without_changing_observed_relief(self):
        self.cover(until=2)
        self.reconcile()
        self.tick(2)
        projection = self.projection()
        self.assertEqual((projection.outstanding_loss, projection.estimated_committed_coverage, projection.open_loss), (10, 0, 10))
        self.assertEqual(self.reconcile().events, ())

    def test_local_cancellation_and_revoked_readiness_remove_coverage(self):
        self.cover()
        self.service.revoke_evidence("credential", idempotency_key=self.driver.key())
        self.assertEqual(self.projection().estimated_committed_coverage, 0)
        self.service.cancel_execution_intent("attempt", "worker", 0, idempotency_key=self.driver.key())
        self.assertEqual(self.projection().open_loss, 10)

    def test_failure_removes_coverage_even_if_the_observation_is_later_revoked(self):
        self.cover()
        event = observe(self.driver, "failure_observed")
        self.service.revoke_evidence(event.evidence_id, idempotency_key=self.driver.key())
        self.assertEqual(self.projection().estimated_committed_coverage, 0)

    def test_new_goal_failure_reopens_a_promise_but_a_prior_failure_can_be_repaired(self):
        self.product()
        failed = self.sample(0, healthy=False)
        self.cover()
        self.assertEqual(self.projection().estimated_committed_coverage, 6)
        self.service.record_goal_sample("duplicate-failure", "goal", "healthy", False, failed.belief_revision_id,
                                         idempotency_key=self.driver.key())
        self.assertEqual(self.projection().estimated_committed_coverage, 6)
        self.tick(1)
        self.sample(1, healthy=False)
        self.assertEqual(self.projection().estimated_committed_coverage, 0)

    def test_withdrawal_only_releases_coverage_and_requires_its_owner(self):
        commitment = self.cover()
        with self.assertRaises(AdmissionDenied):
            self.service.withdraw_goal_coverage(commitment.commitment_id, "intruder", idempotency_key=self.driver.key())
        self.service.withdraw_goal_coverage(commitment.commitment_id, "worker", idempotency_key=self.driver.key())
        self.assertEqual(self.projection().estimated_committed_coverage, 0)
        self.assertEqual(self.service.inspect_resource("slot").used_now, 1)

    def test_wrong_owner_units_product_or_expiry_cannot_claim_coverage(self):
        for owner, units, until in (("wrong", 6, 10), ("worker", 7, 10), ("worker", 6, 11), ("worker", 6, 0)):
            with self.assertRaises(AdmissionDenied):
                self.service.claim_goal_coverage(self.driver.key(), "goal", "healthy", "attempt", owner, units, until,
                                                 idempotency_key=self.driver.key())
        with self.assertRaises(ValueError):
            self.cover(units=True)

    def test_censoring_removes_coverage_and_resume_does_not_resurrect_old_promises(self):
        self.cover()
        self.service.censor_goal_monitor("goal", "healthy", "unavailable", idempotency_key=self.driver.key())
        self.assertEqual(self.projection().estimated_committed_coverage, 0)
        self.service.resume_goal_monitor("goal", "healthy", idempotency_key=self.driver.key())
        self.assertEqual(self.projection().estimated_committed_coverage, 0)

    def test_one_operation_can_cover_two_distinct_sources_without_new_resource_claims(self):
        self.service.open_goal_episode("second-goal", "other-obligation", "ctx", "service-goal", "1",
                                       idempotency_key=self.driver.key())
        self.cover()
        self.cover(goal_id="second-goal")
        self.assertEqual(self.projection().estimated_committed_coverage, 6)
        self.assertEqual(self.projection("second-goal").estimated_committed_coverage, 6)
        self.assertEqual(self.service.inspect_resource("slot").used_now, 1)

    def test_coverage_cannot_cross_product_or_context_scope(self):
        other = replace(self.goal_contract, revision="2", slices=(replace(self.goal_contract.slices[0], product_id="other-product"),))
        self.service.register_goal_contract(other, idempotency_key=self.driver.key())
        self.service.open_goal_episode("other-product", "other-source", "ctx", "service-goal", "2",
                                       idempotency_key=self.driver.key())
        with self.assertRaises(AdmissionDenied):
            self.cover(goal_id="other-product")
        self.driver.context("other-context")
        self.service.open_goal_episode("other-context", "service-obligation", "other-context", "service-goal", "1",
                                       idempotency_key=self.driver.key())
        with self.assertRaises(AdmissionDenied):
            self.cover(goal_id="other-context")
