from dataclasses import replace
import unittest

from reachability.goal_model import DurabilityContract, goal_sample_literal
from reachability.model import Rule, Status
from reachability.requirements import Requirement
from reachability.service import AdmissionDenied, AdmissionService, IdempotencyConflict
from tests.goal_support import GoalFixture
from tests.lifecycle_support import PRODUCT, accept
from tests.support import Driver


class GoalTests(GoalFixture, unittest.TestCase):
    def test_unknown_world_retains_loss_without_manufacturing_observed_relief(self):
        projection = self.projection()
        self.assertEqual((projection.outstanding_loss, projection.estimated_committed_coverage, projection.open_loss), (10, 0, 10))
        self.assertEqual([s.label for s in projection.slices], ["PENDING", "UNKNOWN"])
        self.assertTrue(all(s.observation_required and s.maintenance_required for s in projection.slices))
        self.assertEqual(self.reconcile().events, ())

    def test_scoped_source_identity_prevents_aliases_from_duplicating_loss(self):
        with self.assertRaises(IdempotencyConflict):
            self.service.open_goal_episode("alias", "service-obligation", "ctx", "service-goal", "1",
                                           idempotency_key=self.driver.key())
        same = self.service.open_goal_episode("goal", "service-obligation", "ctx", "service-goal", "1",
                                              idempotency_key=self.driver.key())
        self.assertEqual(same, self.goal)
        with self.assertRaises(IdempotencyConflict):
            self.service.open_goal_episode("goal", "other-source", "ctx", "service-goal", "1",
                                           idempotency_key=self.driver.key())

    def test_supported_contracts_are_pinned_and_revisions_are_immutable(self):
        changed = replace(self.goal_contract, revision="2", slices=(replace(self.goal_contract.slices[0], loss=99),))
        self.service.register_goal_contract(changed, idempotency_key=self.driver.key())
        self.assertEqual(self.projection().outstanding_loss, 10)
        with self.assertRaises(IdempotencyConflict):
            self.service.register_goal_contract(replace(changed, revision="1"), idempotency_key=self.driver.key())
        for item in (replace(self.goal_contract.slices[0], condition=Requirement("TEMPORAL")),
                     replace(self.goal_contract.slices[0], durability=DurabilityContract(17, 1, 1, ("monitor",)))):
            with self.assertRaises(AdmissionDenied):
                self.service.register_goal_contract(replace(changed, slices=(item,)), idempotency_key=self.driver.key())
        with self.assertRaises(ValueError):
            replace(self.goal_contract, slices=(self.goal_contract.slices[0],) * 2)
        for bad in (True, -1, 0, 0.5):
            with self.assertRaises(ValueError):
                replace(self.goal_contract.slices[0], loss=bad)

    def test_three_consecutive_observations_and_exact_product_condition_are_required(self):
        self.product()
        self.reconcile()
        for time in range(3):
            self.tick(time)
            self.sample(time)
            view = self.projection().slices[0]
            self.assertEqual(view.label, "OBSERVED_SUCCESS" if time == 2 else "PENDING")
        projection = self.projection()
        self.assertEqual((projection.outstanding_loss, projection.open_loss), (4, 4))
        events = self.reconcile().events
        self.assertEqual([(e.slice_id, e.kind, e.units) for e in events], [("healthy", "observed_relief", 6)])
        self.assertIsNone(events[0].causal_attempt_id)

    def test_time_alone_cannot_complete_a_durability_window(self):
        self.product()
        self.sample(0)
        self.tick(3)
        self.assertEqual(self.projection().slices[0].label, "UNKNOWN")
        self.assertEqual(self.reconcile().events, ())
        self.assertEqual(self.projection().outstanding_loss, 10)

    def test_missing_middle_sample_is_unknown_even_with_enough_total_samples(self):
        self.product()
        for time in (0, 2, 3):
            self.tick(time)
            self.sample(time)
        self.assertEqual(self.projection().slices[0].label, "UNKNOWN")

    def test_duplicate_samples_cannot_replace_distinct_measurements(self):
        self.product()
        first = self.sample(0)
        for _ in range(4):
            self.service.record_goal_sample(self.driver.key(), "goal", "healthy", True, first.belief_revision_id,
                                             idempotency_key=self.driver.key())
        self.assertEqual(self.projection().slices[0].label, "PENDING")
        self.tick(2)
        self.assertEqual(self.projection().slices[0].label, "UNKNOWN")

    def test_shared_lineage_does_not_count_as_three_distinct_observations(self):
        self.product()
        for time in range(3):
            self.tick(time)
            self.sample(time, roots=("copied-measurement",))
        self.assertEqual(self.projection().slices[0].label, "UNKNOWN")
        # An independent alternative at each time supports a whole valid window.
        for time in (0, 1):
            self.sample(time)
        self.assertEqual(self.projection().slices[0].label, "OBSERVED_SUCCESS")

    def test_partial_relief_is_scoped_to_the_observed_slice(self):
        self.product()
        self.sample(0, slice_id="available")
        view = self.projection()
        self.assertEqual([s.outstanding_loss for s in view.slices], [6, 0])
        event = self.reconcile().events[0]
        self.assertEqual((event.slice_id, event.units), ("available", 4))

    def test_sample_revocation_reopens_loss_and_retains_relief_history(self):
        self.product()
        samples = []
        for time in range(3):
            self.tick(time)
            samples.append(self.sample(time))
        success = self.reconcile()
        self.service.revoke_evidence(samples[1].evidence_id, idempotency_key=self.driver.key())
        self.assertEqual(self.projection().slices[0].label, "UNKNOWN")
        reopened = self.reconcile()
        self.assertEqual((reopened.events[0].kind, reopened.events[0].units), ("reopened", 6))
        self.assertEqual(self.service.inspect_goal("goal").history[0], success)
        self.sample(1)
        self.assertEqual(self.reconcile().events[0].kind, "observed_relief")

    def test_freshness_expiry_reopens_success_without_counting_time_as_failure(self):
        self.product()
        for time in range(3):
            self.tick(time)
            self.sample(time)
        self.reconcile()
        self.tick(3)
        self.assertEqual(self.projection().slices[0].label, "UNKNOWN")
        self.assertEqual(self.reconcile().events[0].kind, "reopened")

    def test_observed_failure_requires_a_new_healthy_streak(self):
        self.product()
        self.sample(0, healthy=False)
        self.assertEqual(self.projection().slices[0].label, "OBSERVED_FAILURE")
        for time in (1, 2, 3):
            self.tick(time)
            self.sample(time)
            expected = "OBSERVED_SUCCESS" if time == 3 else "OBSERVED_FAILURE"
            self.assertEqual(self.projection().slices[0].label, expected)

    def test_censoring_is_neither_success_nor_failure_and_resume_starts_a_new_window(self):
        self.product()
        self.sample(0)
        self.service.censor_goal_monitor("goal", "healthy", "telemetry disconnected", idempotency_key=self.driver.key())
        self.assertEqual(self.projection().slices[0].label, "CENSORED")
        with self.assertRaises(AdmissionDenied):
            self.sample(0)
        self.tick(2)
        self.service.resume_goal_monitor("goal", "healthy", idempotency_key=self.driver.key())
        for time in (2, 3, 4):
            self.tick(time)
            self.sample(time)
        result = self.projection().slices[0]
        self.assertEqual(result.label, "OBSERVED_SUCCESS")
        self.assertEqual([s.observed_at for s in result.samples], [2, 3, 4])

    def test_wrong_product_source_goal_or_context_is_not_goal_evidence(self):
        self.product()
        for kwargs in ({"product": "artifact-v1"}, {"source": "intruder"}):
            with self.assertRaises(AdmissionDenied):
                self.sample(0, **kwargs)
        self.driver.context("other")
        belief = accept(self.driver, goal_sample_literal("goal", "healthy", "artifact-v2", 0), context="other")
        with self.assertRaises(AdmissionDenied):
            self.service.record_goal_sample("foreign", "goal", "healthy", True, belief.belief_revision_id,
                                             idempotency_key=self.driver.key())
        wrong = accept(self.driver, goal_sample_literal("other-goal", "healthy", "artifact-v2", 0), source="monitor")
        with self.assertRaises(AdmissionDenied):
            self.service.record_goal_sample("wrong-goal", "goal", "healthy", True, wrong.belief_revision_id,
                                             idempotency_key=self.driver.key())

    def test_stale_projection_and_forged_fingerprint_cannot_append_accounting(self):
        projection = self.projection()
        self.product()
        for fingerprint in (projection.fingerprint, "forged"):
            with self.assertRaises(AdmissionDenied) as failure:
                self.service.reconcile_goal("goal", fingerprint, idempotency_key=self.driver.key())
            self.assertEqual(failure.exception.status, Status.STALE)
        self.assertEqual(self.service.inspect_goal("goal").history, ())

    def test_reconciliation_is_idempotent_and_does_not_write_beliefs_or_resources(self):
        self.product()
        self.sample(0, slice_id="available")
        snapshot, resource = self.service.snapshot("ctx"), self.service.resource_snapshot()
        first = self.reconcile(key="account")
        self.assertEqual(self.reconcile(key="account"), first)
        self.assertEqual(self.reconcile(), first)
        self.assertEqual(self.service.snapshot("ctx"), snapshot)
        self.assertEqual(self.service.resource_snapshot(), resource)
        self.assertFalse(self.service.inspect_goal("goal").reconciliation_needed)

    def test_repeated_measurement_reports_do_not_mint_additional_relief_events(self):
        self.product()
        sample = self.sample(0, slice_id="available")
        first = self.reconcile()
        self.service.record_goal_sample("duplicate", "goal", "available", True, sample.belief_revision_id,
                                         idempotency_key=self.driver.key())
        self.assertEqual(self.reconcile().events, ())
        self.assertEqual(sum(e.units for r in self.service.inspect_goal("goal").history for e in r.events), 4)
        with self.assertRaises(IdempotencyConflict):
            self.service.record_goal_sample("duplicate", "goal", "available", False, sample.belief_revision_id,
                                             idempotency_key=self.driver.key())

    def test_inference_cannot_manufacture_a_monitor_observation(self):
        literal = goal_sample_literal("goal", "healthy", "artifact-v2", 0)
        with AdmissionService(rules=(Rule("fake-sample", "1", (PRODUCT,), literal),)) as service:
            driver = Driver(service)
            driver.context()
            service.register_goal_contract(self.goal_contract, idempotency_key=driver.key())
            service.open_goal_episode("goal", "source", "ctx", "service-goal", "1", idempotency_key=driver.key())
            product = accept(driver, PRODUCT)
            transition = driver.transition("fake-sample", (product.belief_revision_id,))
            belief = driver.finish(driver.prepare(transition)).belief
            with self.assertRaises(AdmissionDenied) as failure:
                service.record_goal_sample("fake", "goal", "healthy", True, belief.belief_revision_id,
                                             idempotency_key=driver.key())
            self.assertEqual(failure.exception.status, Status.FAIL)

    def test_observations_must_follow_monitor_start_and_its_declared_grid(self):
        slow = replace(self.goal_contract.slices[0], durability=DurabilityContract(3, 2, 2, ("monitor",)))
        contract = replace(self.goal_contract, revision="2", slices=(slow,))
        self.service.register_goal_contract(contract, idempotency_key=self.driver.key())
        self.service.open_goal_episode("slow", "slow-source", "ctx", "service-goal", "2", idempotency_key=self.driver.key())
        self.tick(1)
        with self.assertRaises(AdmissionDenied):
            self.sample(1, goal_id="slow")
        self.tick(2)
        self.service.open_goal_episode("later", "later-source", "ctx", "service-goal", "1", idempotency_key=self.driver.key())
        with self.assertRaises(AdmissionDenied):
            self.sample(0, goal_id="later")
