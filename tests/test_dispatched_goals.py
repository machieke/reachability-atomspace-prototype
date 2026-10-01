import unittest
from unittest.mock import patch

from reachability.goal_model import DurabilityContract, GoalContract, GoalSlice
from tests.dispatch_support import DispatchFixture
from tests.lifecycle_support import PRODUCT, fact, observe


class DispatchedCoverageTests(DispatchFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        contract = GoalContract("goal-contract", "1", "units", (
            GoalSlice("healthy", 10, "artifact-v2", fact(PRODUCT), DurabilityContract(3, 1, 1, ("monitor",))),), "test")
        self.service.register_goal_contract(contract, idempotency_key=self.driver.key())
        self.service.open_goal_episode("goal", "source", "ctx", "goal-contract", "1", idempotency_key=self.driver.key())
        self.service.claim_goal_coverage("promise", "goal", "healthy", "attempt", "worker", 6, 10,
                                          idempotency_key=self.driver.key())

    def coverage(self):
        return self.service.inspect_goal("goal").projection.estimated_committed_coverage

    def test_ack_preserves_only_coverage_and_credential_expiry_does_not_undo_submission(self):
        self.dispatch()
        self.assertEqual(self.coverage(), 6)
        self.service.revoke_evidence("credential", idempotency_key=self.driver.key())
        self.assertEqual(self.coverage(), 6)
        projection = self.service.inspect_goal("goal").projection
        self.assertEqual((projection.outstanding_loss, projection.open_loss), (10, 4))
        self.assertEqual(self.service.reconcile_goal("goal", projection.fingerprint,
                                                     idempotency_key=self.driver.key()).events, ())

    def test_uncertain_submission_removes_estimated_coverage_but_keeps_resource_hold(self):
        with patch.object(self.executor, "submit", side_effect=TimeoutError("unknown remote outcome")):
            self.dispatch()
        self.assertEqual(self.coverage(), 0)
        self.assertEqual(self.service.inspect_resource("slot").reconciliation_attempts, ("attempt",))
        self.dispatch()
        self.assertEqual(self.coverage(), 6)

    def test_release_failure_and_expiry_reopen_loss_without_proving_goal_success(self):
        self.dispatch()
        self.dispatcher.release("attempt", "worker")
        self.assertEqual(self.coverage(), 0)
        self.assertEqual(self.service.inspect_goal("goal").projection.outstanding_loss, 10)

    def test_dispatched_lease_expiry_loses_coverage_even_while_resources_remain_held(self):
        self.dispatch()
        self.service.advance_clock("ctx", 10, idempotency_key=self.driver.key())
        self.service.advance_resource_clock(10, idempotency_key=self.driver.key())
        self.assertEqual(self.coverage(), 0)
        self.assertEqual(self.service.inspect_resource("slot").reconciliation_attempts, ("attempt",))

    def test_observed_cancellation_removes_coverage_even_with_an_accepted_receipt(self):
        self.dispatch()
        observe(self.driver, "cancellation_observed")
        self.assertEqual(self.coverage(), 0)
