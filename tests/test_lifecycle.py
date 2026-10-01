from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier
import unittest

from reachability.lifecycle_model import LifecycleState
from reachability.model import Status
from reachability.requirements import Requirement
from reachability.service import AdmissionDenied, AdmissionService, IdempotencyConflict
from tests.lifecycle_support import ALTERNATIVE, CREDENTIAL, PRODUCT, RETIRED, TESTED, accept, certify, fact, schema
from tests.support import Driver


class LifecycleTests(unittest.TestCase):
    def make_service(self):
        return AdmissionService()

    def setUp(self):
        self.service = self.make_service()
        self.driver = Driver(self.service)
        self.driver.context()
        self.definition = schema()
        self.service.register_lifecycle_schema(self.definition, idempotency_key=self.driver.key())
        self.episode = self.service.open_lifecycle_episode("episode", "ctx", "artifact", "1",
                                                          idempotency_key=self.driver.key())

    def complete_inputs(self):
        accept(self.driver, TESTED)
        accept(self.driver, CREDENTIAL, evidence_id="credential")
        accept(self.driver, PRODUCT, evidence_id="product")

    def advance(self, permit):
        return self.service.advance_lifecycle(permit, permit.episode_revision, idempotency_key=self.driver.key())

    def test_readiness_cannot_substitute_for_observed_outcome(self):
        accept(self.driver, TESTED)
        accept(self.driver, CREDENTIAL)
        permit = certify(self.driver)
        self.assertEqual(permit.prerequisites.status, Status.PASS)
        self.assertEqual(permit.outcome.status, Status.UNKNOWN)
        self.assertEqual(permit.status, Status.UNKNOWN)
        with self.assertRaises(AdmissionDenied):
            self.advance(permit)
        self.assertEqual(self.service.inspect_lifecycle("episode").episode.stage, "DRAFT")

    def test_observed_product_cannot_compensate_for_missing_requirement(self):
        accept(self.driver, PRODUCT)
        self.assertEqual(certify(self.driver).status, Status.UNKNOWN)

    def test_certified_transition_retains_exact_history_and_does_not_change_beliefs(self):
        self.complete_inputs()
        snapshot = self.service.snapshot("ctx")
        permit = certify(self.driver)
        self.assertEqual(permit.status, Status.PASS)
        updated = self.advance(permit)
        self.assertEqual(updated.stage, "BUILT")
        self.assertEqual(updated.revision, 1)
        self.assertEqual(updated.events[0].certificate_id, permit.certificate_id)
        self.assertEqual(updated.events[0].prerequisites, permit.prerequisites)
        self.assertEqual(self.service.snapshot("ctx"), snapshot)

    def test_schema_revision_is_pinned_and_cannot_be_redefined(self):
        modified_edge = replace(self.definition.edges[0], requirements=fact(RETIRED))
        with self.assertRaises(IdempotencyConflict):
            self.service.register_lifecycle_schema(replace(self.definition, edges=(modified_edge,)),
                                                   idempotency_key=self.driver.key())
        newer = replace(self.definition, revision="2", edges=(modified_edge,))
        self.service.register_lifecycle_schema(newer, idempotency_key=self.driver.key())
        self.service.open_lifecycle_episode("new", "ctx", "artifact", "2", idempotency_key=self.driver.key())
        self.complete_inputs()
        self.assertEqual(certify(self.driver).status, Status.PASS)
        self.assertEqual(certify(self.driver, "new").status, Status.UNKNOWN)
        self.assertEqual(self.service.inspect_lifecycle("episode").episode.schema_revision, "1")

    def test_schema_rejects_unknown_contract_or_outcome_without_evidence(self):
        for outcome in (Requirement("DURING"), Requirement("ALWAYS"),
                        Requirement("OR", children=(Requirement("ALWAYS"), fact(PRODUCT)))):
            edge = replace(self.definition.edges[0], outcome=outcome)
            with self.subTest(outcome=outcome.operator), self.assertRaises(AdmissionDenied):
                self.service.register_lifecycle_schema(replace(self.definition, revision=self.driver.key(), edges=(edge,)),
                                                       idempotency_key=self.driver.key())

    def test_schema_rejects_invalid_edges_and_terminal_advances(self):
        with self.assertRaises(ValueError):
            replace(self.definition, edges=(replace(self.definition.edges[0], source="missing"),))
        with self.assertRaises(ValueError):
            replace(self.definition, edges=(replace(self.definition.edges[1], kind="advance"),))

    def test_initial_state_requires_current_support(self):
        changed = replace(self.definition, revision="2", states=(LifecycleState("DRAFT", fact(TESTED)),
                                                                *self.definition.states[1:]))
        self.service.register_lifecycle_schema(changed, idempotency_key=self.driver.key())
        with self.assertRaises(AdmissionDenied):
            self.service.open_lifecycle_episode("new", "ctx", "artifact", "2", idempotency_key=self.driver.key())
        with self.assertRaises(KeyError):
            self.service.inspect_lifecycle("new")

    def test_revoked_prerequisite_does_not_erase_completed_artifact(self):
        self.complete_inputs()
        completed = self.advance(certify(self.driver))
        self.service.revoke_evidence("credential", idempotency_key=self.driver.key())
        view = self.service.inspect_lifecycle("episode")
        self.assertEqual(view.episode, completed)
        self.assertEqual(view.validity, Status.PASS)
        self.assertEqual({w.literal for w in view.current_support.witnesses}, {PRODUCT})

    def test_lost_current_validity_preserves_history_and_can_use_new_support(self):
        self.complete_inputs()
        completed = self.advance(certify(self.driver))
        self.service.revoke_evidence("product", idempotency_key=self.driver.key())
        view = self.service.inspect_lifecycle("episode")
        self.assertEqual(view.episode, completed)
        self.assertEqual(view.validity, Status.STALE)
        alternative = accept(self.driver, PRODUCT)
        view = self.service.inspect_lifecycle("episode")
        self.assertEqual(view.episode, completed)
        self.assertEqual(view.validity, Status.PASS)
        self.assertEqual(view.current_support.witnesses[0].belief_revision_id, alternative.belief_revision_id)

    def test_regression_can_leave_stale_state_with_its_own_complete_contract(self):
        self.complete_inputs()
        self.advance(certify(self.driver))
        self.service.revoke_evidence("product", idempotency_key=self.driver.key())
        self.assertEqual(certify(self.driver, edge="retire").status, Status.UNKNOWN)
        accept(self.driver, RETIRED)
        permit = certify(self.driver, edge="retire")
        self.assertEqual(permit.status, Status.PASS)
        retired = self.advance(permit)
        self.assertEqual(retired.stage, "RETIRED")
        self.assertEqual(len(retired.events), 2)

    def test_target_validity_is_checked_separately(self):
        changed = replace(self.definition, revision="2", states=(self.definition.states[0],
            LifecycleState("BUILT", fact(ALTERNATIVE)), self.definition.states[2]))
        self.service.register_lifecycle_schema(changed, idempotency_key=self.driver.key())
        self.service.open_lifecycle_episode("new", "ctx", "artifact", "2", idempotency_key=self.driver.key())
        self.complete_inputs()
        permit = certify(self.driver, "new")
        self.assertEqual(permit.outcome.status, Status.PASS)
        self.assertEqual(permit.target_validity.status, Status.UNKNOWN)
        self.assertEqual(permit.status, Status.UNKNOWN)

    def test_changed_dependencies_and_forged_permits_cannot_advance(self):
        self.complete_inputs()
        permit = certify(self.driver)
        for forged in (replace(permit, certificate_id="forged"), replace(permit, edge_id="retire"),
                       replace(permit, schema_revision="fake")):
            with self.subTest(forged=forged), self.assertRaises(AdmissionDenied) as caught:
                self.advance(forged)
            self.assertEqual(caught.exception.status, Status.FAIL)
        self.service.advance_clock("ctx", 1, idempotency_key=self.driver.key())
        with self.assertRaises(AdmissionDenied) as caught:
            self.advance(permit)
        self.assertEqual(caught.exception.status, Status.STALE)

    def test_wrong_revision_is_stale_and_unrelated_context_does_not_invalidate(self):
        self.complete_inputs()
        permit = self.service.certify_lifecycle_transition("episode", "build", 0, 0,
                                                          idempotency_key=self.driver.key())
        self.assertEqual(permit.status, Status.STALE)
        permit = certify(self.driver)
        self.driver.context("other")
        accept(self.driver, PRODUCT, context="other")
        self.assertEqual(self.advance(permit).stage, "BUILT")

    def test_advance_is_idempotent_but_old_permit_is_not_new_authority(self):
        self.complete_inputs()
        permit = certify(self.driver)
        first = self.service.advance_lifecycle(permit, 0, idempotency_key="advance")
        self.assertEqual(first, self.service.advance_lifecycle(permit, 0, idempotency_key="advance"))
        with self.assertRaises(AdmissionDenied):
            self.advance(permit)
        self.assertEqual(len(self.service.inspect_lifecycle("episode").episode.events), 1)

    def test_concurrent_transitions_can_advance_an_episode_only_once(self):
        self.complete_inputs()
        permits = (certify(self.driver), certify(self.driver))
        barrier = Barrier(2)

        def worker(index):
            barrier.wait(timeout=5)
            try:
                self.service.advance_lifecycle(permits[index], 0, idempotency_key=f"advance-{index}")
                return Status.PASS
            except AdmissionDenied as error:
                return error.status

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(worker, range(2)))
        self.assertCountEqual(results, [Status.PASS, Status.STALE])
        self.assertEqual(len(self.service.inspect_lifecycle("episode").episode.events), 1)
