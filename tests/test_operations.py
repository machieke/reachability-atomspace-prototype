from dataclasses import replace
import unittest

from reachability.lifecycle_model import milestone_literal
from reachability.model import Rule, Status
from reachability.service import AdmissionDenied, AdmissionService, IdempotencyConflict
from tests.lifecycle_support import CREDENTIAL, PRODUCT, TESTED, accept, certify, observe, schema
from tests.support import Driver


class OperationTests(unittest.TestCase):
    def make_service(self):
        return AdmissionService()

    def setUp(self):
        self.service = self.make_service()
        self.driver = Driver(self.service)
        self.driver.context()
        self.definition = schema()
        self.service.register_lifecycle_schema(self.definition, idempotency_key=self.driver.key())
        self.service.open_lifecycle_episode("episode", "ctx", "artifact", "1", idempotency_key=self.driver.key())
        self.operation = self.service.propose_operation("build-artifact", "attempt", "episode", "build",
                                                        idempotency_key=self.driver.key())

    def ready(self):
        accept(self.driver, TESTED)
        accept(self.driver, CREDENTIAL)

    def finish_observations(self):
        accept(self.driver, PRODUCT)
        observe(self.driver, "completion_observed")
        observe(self.driver, "exact_product_observed")

    def test_selection_and_ack_do_not_create_success_or_execution_authority(self):
        self.ready()
        self.service.advance_clock("ctx", 1, idempotency_key=self.driver.key())
        selected = self.service.select_operation("attempt", 0, idempotency_key=self.driver.key())
        self.assertTrue(selected.selected)
        self.assertEqual(selected.selected_at, 1)
        observe(self.driver, "accepted_by_executor")
        view = self.service.inspect_operation("attempt")
        self.assertEqual(view.current_milestones, ("accepted_by_executor",))
        self.assertEqual(view.readiness, Status.PASS)
        self.assertEqual(view.outcome_status, Status.UNKNOWN)
        self.assertFalse(view.execution_authorized)
        self.assertEqual(certify(self.driver, attempt="attempt").status, Status.UNKNOWN)
        self.assertEqual(self.service.inspect_lifecycle("episode").episode.stage, "DRAFT")

    def test_exact_product_and_completion_are_separate_observations(self):
        self.ready()
        accept(self.driver, PRODUCT)
        observe(self.driver, "completion_observed")
        self.assertEqual(self.service.inspect_operation("attempt").outcome_status, Status.UNKNOWN)
        observe(self.driver, "exact_product_observed")
        view = self.service.inspect_operation("attempt")
        self.assertEqual(view.outcome_status, Status.PASS)
        self.assertNotIn("accepted_by_executor", view.observed_milestones)
        permit = certify(self.driver, attempt="attempt")
        self.assertEqual(permit.status, Status.PASS)
        episode = self.service.advance_lifecycle(permit, 0, idempotency_key=self.driver.key())
        self.assertEqual(episode.events[0].attempt_id, "attempt")

    def test_milestones_without_the_declared_outcome_cannot_complete(self):
        self.ready()
        observe(self.driver, "completion_observed")
        observe(self.driver, "exact_product_observed")
        self.assertEqual(self.service.inspect_operation("attempt").outcome_status, Status.UNKNOWN)

    def test_wrong_product_or_attempt_callback_is_rejected(self):
        for attempt, product in (("old-attempt", "artifact-v2"), ("attempt", "artifact-v1")):
            support = accept(self.driver, milestone_literal(attempt, product, "completion_observed"), source="executor")
            with self.subTest(attempt=attempt, product=product), self.assertRaises(AdmissionDenied) as caught:
                self.service.record_operation_observation(self.driver.key(), "attempt", "completion_observed",
                                                          support.belief_revision_id, idempotency_key=self.driver.key())
            self.assertEqual(caught.exception.status, Status.FAIL)
        self.assertEqual(self.service.inspect_operation("attempt").observed_milestones, ())

    def test_unregistered_source_is_rejected(self):
        support = accept(self.driver, milestone_literal("attempt", "artifact-v2", "completion_observed"),
                         source="other-source")
        with self.assertRaises(AdmissionDenied) as caught:
            self.service.record_operation_observation("obs", "attempt", "completion_observed",
                                                      support.belief_revision_id, idempotency_key=self.driver.key())
        self.assertEqual(caught.exception.status, Status.FAIL)

    def test_unaccepted_and_foreign_reports_cannot_be_milestone_witnesses(self):
        self.driver.context("other")
        support = accept(self.driver, milestone_literal("attempt", "artifact-v2", "completion_observed"),
                         source="executor", context="other")
        for revision in ("nonexistent-belief", support.belief_revision_id):
            with self.subTest(revision=revision), self.assertRaises(AdmissionDenied):
                self.service.record_operation_observation(self.driver.key(), "attempt", "completion_observed",
                                                          revision, idempotency_key=self.driver.key())

    def test_inferred_executor_event_is_not_a_direct_observation(self):
        literal = milestone_literal("attempt", "artifact-v2", "completion_observed")
        with AdmissionService((Rule("invent-event", "1", (TESTED,), literal),)) as service:
            driver = Driver(service)
            driver.context()
            service.register_lifecycle_schema(schema(), idempotency_key=driver.key())
            service.open_lifecycle_episode("episode", "ctx", "artifact", "1", idempotency_key=driver.key())
            service.propose_operation("operation", "attempt", "episode", "build", idempotency_key=driver.key())
            tested = accept(driver, TESTED)
            transition = driver.transition("invent-event", (tested.belief_revision_id,))
            derived = driver.finish(driver.prepare(transition)).belief
            with self.assertRaises(AdmissionDenied):
                service.record_operation_observation("obs", "attempt", "completion_observed",
                                                     derived.belief_revision_id, idempotency_key=driver.key())

    def test_observation_predating_attempt_cannot_be_reused(self):
        self.service.advance_clock("ctx", 5, idempotency_key=self.driver.key())
        self.service.propose_operation("build-artifact", "later", "episode", "build", idempotency_key=self.driver.key())
        support = accept(self.driver, milestone_literal("later", "artifact-v2", "completion_observed"),
                         observed_at=4, source="executor")
        with self.assertRaises(AdmissionDenied):
            self.service.record_operation_observation("obs", "later", "completion_observed",
                                                      support.belief_revision_id, idempotency_key=self.driver.key())

    def test_observation_id_is_idempotent_and_cannot_be_rebound(self):
        observation = observe(self.driver, "completion_observed", observation_id="obs")
        before = self.service.inspect_operation("attempt")
        again = self.service.record_operation_observation("obs", "attempt", "completion_observed",
            observation.belief_revision_id, idempotency_key=self.driver.key())
        self.assertEqual(again, observation)
        self.assertEqual(self.service.inspect_operation("attempt"), before)
        with self.assertRaises(IdempotencyConflict):
            self.service.record_operation_observation("obs", "attempt", "exact_product_observed",
                observation.belief_revision_id, idempotency_key=self.driver.key())

    def test_late_completion_after_cancellation_is_still_recorded(self):
        observe(self.driver, "cancellation_observed")
        self.finish_observations()
        view = self.service.inspect_operation("attempt")
        self.assertIn("cancellation_observed", view.observed_milestones)
        self.assertEqual(view.outcome_status, Status.PASS)

    def test_revoked_observation_preserves_history_but_closes_outcome(self):
        self.finish_observations()
        view = self.service.inspect_operation("attempt")
        evidence_id = view.operation.observations[-1].evidence_id
        self.service.revoke_evidence(evidence_id, idempotency_key=self.driver.key())
        current = self.service.inspect_operation("attempt")
        self.assertEqual(current.operation, view.operation)
        self.assertIn("exact_product_observed", current.observed_milestones)
        self.assertNotIn("exact_product_observed", current.current_milestones)
        self.assertEqual(current.outcome_status, Status.UNKNOWN)

    def test_attempts_do_not_share_outcomes_or_allow_identity_rebinding(self):
        self.service.propose_operation("build-artifact", "retry", "episode", "build", idempotency_key=self.driver.key())
        self.finish_observations()
        self.assertEqual(self.service.inspect_operation("attempt").outcome_status, Status.PASS)
        self.assertEqual(self.service.inspect_operation("retry").outcome_status, Status.UNKNOWN)
        with self.assertRaises(IdempotencyConflict):
            self.service.propose_operation("different", "attempt", "episode", "build", idempotency_key=self.driver.key())
        with self.assertRaises(IdempotencyConflict):
            self.service.propose_operation("build-artifact", "new", "episode", "retire", idempotency_key=self.driver.key())

    def test_schema_updates_do_not_change_attempt_product_identity(self):
        changed = replace(self.definition, revision="2", edges=(replace(self.definition.edges[0], product_id="artifact-v3"),))
        self.service.register_lifecycle_schema(changed, idempotency_key=self.driver.key())
        self.assertEqual(self.service.inspect_operation("attempt").operation.product_id, "artifact-v2")
        self.assertEqual(self.service.inspect_operation("attempt").operation.schema_revision, "1")

    def test_selection_revision_and_lifecycle_permit_epoch_are_checked(self):
        self.ready()
        self.finish_observations()
        permit = certify(self.driver, attempt="attempt")
        revision = self.service.inspect_operation("attempt").operation.revision
        self.service.select_operation("attempt", revision, idempotency_key=self.driver.key())
        with self.assertRaises(AdmissionDenied):
            self.service.select_operation("attempt", revision, idempotency_key=self.driver.key())
        with self.assertRaises(AdmissionDenied) as caught:
            self.service.advance_lifecycle(permit, 0, idempotency_key=self.driver.key())
        self.assertEqual(caught.exception.status, Status.STALE)

    def test_other_edge_attempt_cannot_authorize_lifecycle_transition(self):
        self.ready()
        self.finish_observations()
        self.service.propose_operation("retire", "wrong-edge", "episode", "retire", idempotency_key=self.driver.key())
        self.assertEqual(certify(self.driver, attempt="wrong-edge").status, Status.FAIL)
