from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier
import unittest

from reachability.execution_model import ResourceDefinition, ResourceDemand
from reachability.model import Clause, Status
from reachability.requirements import Requirement
from reachability.service import AdmissionDenied, IdempotencyConflict
from tests.execution_support import ExecutionFixture
from tests.lifecycle_support import CREDENTIAL, PRODUCT, TESTED, accept, fact, observe, schema


class ExecutionTests(ExecutionFixture, unittest.TestCase):
    def test_all_claims_and_intent_commit_without_inventing_execution_or_relief(self):
        before = self.service.snapshot("ctx")
        permit = self.permit()
        self.assertEqual(permit.status, Status.PASS)
        intent = self.reserve(permit)
        self.assertEqual(len(intent.reservations), 1)
        reservation = intent.reservations[0]
        self.assertEqual((reservation.owner_id, reservation.attempt_id, reservation.intent_id),
                         ("worker", "attempt", intent.intent_id))
        self.assertEqual(intent.product_id, "artifact-v2")
        self.assertEqual(self.service.inspect_resource("slot").used_now, 1)
        view = self.service.inspect_execution_intent("attempt")
        self.assertEqual((view.state, view.readiness, view.execution_authorized), ("pending", Status.PASS, False))
        self.assertEqual(self.service.snapshot("ctx"), before)
        self.assertEqual(self.service.inspect_operation("attempt").observed_milestones, ())
        self.assertEqual(self.service.inspect_lifecycle("episode").episode.stage, "DRAFT")

    def test_no_selection_no_ready_requirements_and_no_wrong_owner(self):
        self.operation("unselected", select=False)
        self.assertEqual(self.permit("unselected").status, Status.FAIL)
        self.assertEqual(self.permit(owner="other").status, Status.FAIL)
        self.service.revoke_evidence("credential", idempotency_key=self.driver.key())
        permit = self.permit()
        self.assertEqual(permit.status, Status.UNKNOWN)
        with self.assertRaises(AdmissionDenied):
            self.reserve(permit)
        self.assertEqual(self.service.inspect_resource("slot").used_now, 0)

    def test_atomic_failure_leaves_every_resource_unclaimed(self):
        self.service.register_resource(ResourceDefinition("unavailable", 0, "units"), idempotency_key=self.driver.key())
        contract = replace(self.contract, revision="2", demands=(*self.contract.demands,
                           ResourceDemand("unavailable", 1, "units")))
        self.service.register_execution_contract(contract, idempotency_key=self.driver.key())
        permit = self.permit(contract=contract)
        self.assertEqual(permit.status, Status.FAIL)
        before = self.service.resource_snapshot()
        with self.assertRaises(AdmissionDenied):
            self.reserve(permit)
        self.assertEqual(self.service.resource_snapshot(), before)
        self.assertEqual(self.service.inspect_resource("slot").reservations, ())
        with self.assertRaises(KeyError):
            self.service.inspect_execution_intent("attempt")

    def test_competing_workers_can_reserve_only_one_last_unit(self):
        self.operation("other")
        permits = [self.permit(), self.permit("other")]
        self.assertTrue(all(permit.status is Status.PASS for permit in permits))
        barrier = Barrier(2)

        def reserve(index):
            barrier.wait(timeout=5)
            try:
                self.service.reserve_and_record_intent(permits[index], idempotency_key=f"race-{index}")
                return Status.PASS
            except AdmissionDenied as error:
                return error.status

        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(pool.map(reserve, range(2)), (Status.PASS, Status.STALE))
        self.assertEqual(self.service.inspect_resource("slot").used_now, 1)
        self.assertEqual(len(self.service.inspect_resource("slot").reservations), 1)

    def test_resources_are_shared_across_belief_contexts(self):
        self.driver.context("other-context")
        for literal in (TESTED, CREDENTIAL):
            accept(self.driver, literal, context="other-context")
        self.service.open_lifecycle_episode("other-episode", "other-context", "artifact", "1",
                                            idempotency_key=self.driver.key())
        self.operation("other", "other-episode")
        self.reserve()
        self.assertEqual(self.permit("other").status, Status.FAIL)
        self.assertEqual(self.service.inspect_resource("slot").used_now, 1)

    def test_complete_three_way_capacity_conflict(self):
        self.service.register_resource(ResourceDefinition("two", 2, "units"), idempotency_key=self.driver.key())
        contract = replace(self.contract, revision="2", demands=(ResourceDemand("two", 1, "units"),))
        self.service.register_execution_contract(contract, idempotency_key=self.driver.key())
        self.operation("second")
        self.operation("third")
        self.reserve(self.permit(contract=contract))
        self.reserve(self.permit("second", contract=contract))
        self.assertEqual(self.permit("third", contract=contract).status, Status.FAIL)
        self.assertEqual(self.service.inspect_resource("two").used_now, 2)

    def test_duplicate_commands_and_attempts_do_not_duplicate_claims(self):
        permit = self.permit()
        intent = self.reserve(permit, key="reserve")
        self.assertEqual(self.reserve(permit, key="reserve"), intent)
        self.assertEqual(self.reserve(permit), intent)
        self.assertEqual(len(self.service.inspect_resource("slot").reservations), 1)
        changed = self.permit()
        self.assertEqual(changed.status, Status.FAIL)
        with self.assertRaises(IdempotencyConflict):
            self.reserve(changed)
        with self.assertRaises(IdempotencyConflict):
            self.reserve(changed, key="reserve")

    def test_forged_permit_cannot_omit_claims_or_change_owner(self):
        permit = self.permit()
        for forged in (replace(permit, claims=()), replace(permit, owner_id="other"),
                       replace(permit, lease_until=1000), replace(permit, attempt_id="other")):
            with self.assertRaises(AdmissionDenied) as failure:
                self.reserve(forged)
            self.assertEqual(failure.exception.status, Status.FAIL)
        self.assertEqual(self.service.inspect_resource("slot").used_now, 0)

    def test_expected_revisions_are_checked(self):
        for name in ("expected_operation_revision", "expected_knowledge_revision", "expected_resource_revision"):
            with self.subTest(name=name):
                permit = self.permit(**{name: 10000})
                self.assertEqual(permit.status, Status.STALE)
                with self.assertRaises(AdmissionDenied):
                    self.reserve(permit)

    def test_revocation_between_certificate_and_reservation_is_stale(self):
        permit = self.permit()
        self.service.revoke_evidence("credential", idempotency_key=self.driver.key())
        with self.assertRaises(AdmissionDenied) as failure:
            self.reserve(permit)
        self.assertEqual(failure.exception.status, Status.STALE)
        self.assertEqual(self.service.inspect_resource("slot").used_now, 0)

    def test_pending_intent_rechecks_current_requirements_without_rewriting_history(self):
        intent = self.reserve()
        self.service.revoke_evidence("credential", idempotency_key=self.driver.key())
        view = self.service.inspect_execution_intent("attempt")
        self.assertEqual(view.intent, intent)
        self.assertEqual((view.state, view.readiness), ("pending", Status.UNKNOWN))
        self.assertEqual(self.service.inspect_resource("slot").used_now, 1)

    def test_both_time_domains_and_lifecycle_changes_stale_certificates(self):
        permit = self.permit()
        self.service.advance_clock("ctx", 1, idempotency_key=self.driver.key())
        with self.assertRaises(AdmissionDenied):
            self.reserve(permit)
        permit = self.permit()
        self.service.advance_resource_clock(1, idempotency_key=self.driver.key())
        with self.assertRaises(AdmissionDenied):
            self.reserve(permit)
        permit = self.permit()
        self.operation("other")
        with self.assertRaises(AdmissionDenied):
            self.reserve(permit)

    def test_policy_insertion_blocks_prepared_and_new_intents(self):
        permit = self.permit()
        snapshot = self.service.snapshot("ctx")
        self.service.replace_policy("ctx", "blocked", (Clause((CREDENTIAL.negate(),)),),
                                    snapshot.knowledge_revision, idempotency_key=self.driver.key())
        with self.assertRaises(AdmissionDenied):
            self.reserve(permit)
        self.assertNotEqual(self.permit().status, Status.PASS)

    def test_pinned_contract_revision_and_additional_action_gate(self):
        contract = replace(self.contract, revision="2", requirements=fact(PRODUCT))
        self.service.register_execution_contract(contract, idempotency_key=self.driver.key())
        self.assertEqual(self.permit(contract=contract).status, Status.UNKNOWN)
        self.assertEqual(self.permit().status, Status.PASS)
        accept(self.driver, PRODUCT)
        self.assertEqual(self.permit(contract=contract).status, Status.PASS)
        intent = self.reserve(self.permit())
        self.assertEqual(intent.contract_revision, "1")

    def test_contract_and_schema_binding_is_exact(self):
        self.service.register_lifecycle_schema(schema("2"), idempotency_key=self.driver.key())
        contract = replace(self.contract, revision="2", schema_revision="2")
        self.service.register_execution_contract(contract, idempotency_key=self.driver.key())
        self.assertEqual(self.permit(contract=contract).status, Status.FAIL)

    def test_registration_rejects_unsupported_or_rebound_contracts(self):
        for contract in (replace(self.contract, revision="2", requirements=Requirement("TEMPORAL")),
                         replace(self.contract, revision="2", executor_id="untrusted"),
                         replace(self.contract, revision="2", demands=(ResourceDemand("unknown", 1, "units"),)),
                         replace(self.contract, revision="2", demands=(ResourceDemand("slot", 1, "bytes"),))):
            with self.assertRaises(AdmissionDenied):
                self.service.register_execution_contract(contract, idempotency_key=self.driver.key())
        with self.assertRaises(IdempotencyConflict):
            self.service.register_execution_contract(replace(self.contract, lease_duration=100),
                                                       idempotency_key=self.driver.key())
        with self.assertRaises(IdempotencyConflict):
            self.service.register_resource(ResourceDefinition("slot", 2, "slots"), idempotency_key=self.driver.key())
        with self.assertRaises(AdmissionDenied):
            self.service.register_resource(ResourceDefinition("stock", 2, "items", "consumable"),
                                            idempotency_key=self.driver.key())

    def test_lease_boundary_releases_local_capacity_without_reusing_attempt_identity(self):
        intent = self.reserve()
        self.service.advance_resource_clock(9, idempotency_key=self.driver.key())
        self.assertEqual(self.service.inspect_execution_intent("attempt").state, "pending")
        self.service.advance_resource_clock(10, idempotency_key=self.driver.key())
        self.assertEqual(self.service.inspect_resource("slot").used_now, 0)
        self.assertEqual(self.service.inspect_execution_intent("attempt").state, "expired")
        self.assertEqual(self.service.inspect_execution_intent("attempt").intent, intent)
        self.assertEqual(self.permit().status, Status.FAIL)
        self.service.advance_clock("ctx", 10, idempotency_key=self.driver.key())
        self.operation("retry")
        retry = self.reserve(self.permit("retry"))
        self.assertNotEqual(intent.intent_id, retry.intent_id)
        self.assertEqual((retry.created_at, retry.lease_until), (10, 20))
        with self.assertRaises(ValueError):
            self.service.advance_resource_clock(9, idempotency_key=self.driver.key())

    def test_cancellation_requires_owner_and_releases_only_local_claims(self):
        intent = self.reserve()
        with self.assertRaises(AdmissionDenied):
            self.service.cancel_execution_intent("attempt", "other", 0, idempotency_key=self.driver.key())
        with self.assertRaises(AdmissionDenied):
            self.service.cancel_execution_intent("attempt", "worker", 1, idempotency_key=self.driver.key())
        cancelled = self.service.cancel_execution_intent("attempt", "worker", 0, idempotency_key="cancel")
        self.assertEqual(self.service.cancel_execution_intent("attempt", "worker", 0, idempotency_key="cancel"), cancelled)
        self.assertEqual(cancelled.reservations, intent.reservations)
        self.assertEqual(self.service.inspect_execution_intent("attempt").state, "cancelled")
        self.assertEqual(self.service.inspect_resource("slot").used_now, 0)

    def test_observed_attempt_cannot_be_retroactively_given_an_intent(self):
        observe(self.driver, "accepted_by_executor")
        self.assertEqual(self.permit().status, Status.FAIL)

    def test_remote_observation_pins_capacity_even_after_expiry_and_revocation(self):
        self.reserve()
        observation = observe(self.driver, "accepted_by_executor")
        self.service.advance_resource_clock(10, idempotency_key=self.driver.key())
        self.service.advance_clock("ctx", 10, idempotency_key=self.driver.key())
        self.service.revoke_evidence(observation.evidence_id, idempotency_key=self.driver.key())
        self.assertEqual(self.service.inspect_execution_intent("attempt").state, "reconciliation_required")
        resource = self.service.inspect_resource("slot")
        self.assertEqual(resource.reconciliation_attempts, ("attempt",))
        self.assertEqual(len(resource.reservations), 1)
        with self.assertRaises(AdmissionDenied) as failure:
            self.service.cancel_execution_intent("attempt", "worker", 0, idempotency_key=self.driver.key())
        self.assertEqual(failure.exception.status, Status.UNKNOWN)
        self.operation("retry")
        self.assertEqual(self.permit("retry").status, Status.UNKNOWN)

    def test_late_observation_after_local_cancellation_freezes_resource(self):
        self.reserve()
        self.service.cancel_execution_intent("attempt", "worker", 0, idempotency_key=self.driver.key())
        self.operation("other")
        permit = self.permit("other")
        observe(self.driver, "cancellation_observed")
        with self.assertRaises(AdmissionDenied):
            self.reserve(permit)
        self.assertNotEqual(self.permit("other").status, Status.PASS)
        self.assertEqual(self.service.inspect_execution_intent("attempt").intent.state, "cancelled")

    def test_zero_resource_contract_still_requires_current_gates_and_lease(self):
        contract = replace(self.contract, revision="2", demands=())
        self.service.register_execution_contract(contract, idempotency_key=self.driver.key())
        intent = self.reserve(self.permit(contract=contract))
        self.assertEqual(intent.reservations, ())
        self.assertEqual(self.service.inspect_execution_intent("attempt").readiness, Status.PASS)
        self.service.advance_resource_clock(10, idempotency_key=self.driver.key())
        self.assertEqual(self.service.inspect_execution_intent("attempt").readiness, Status.STALE)

    def test_resource_clock_cannot_leave_evidence_fresh_at_an_older_tick(self):
        permit = self.permit()
        self.service.advance_resource_clock(1, idempotency_key=self.driver.key())
        with self.assertRaises(AdmissionDenied):
            self.reserve(permit)
        self.assertEqual(self.permit().status, Status.STALE)
        self.service.advance_clock("ctx", 1, idempotency_key=self.driver.key())
        self.assertEqual(self.permit().status, Status.PASS)
        self.reserve()
        self.service.advance_clock("ctx", 2, idempotency_key=self.driver.key())
        self.assertEqual(self.service.inspect_execution_intent("attempt").readiness, Status.STALE)

    def test_credential_expiry_blocks_the_next_step_while_local_lease_remains_held(self):
        self.service.revoke_evidence("credential", idempotency_key=self.driver.key())
        accept(self.driver, CREDENTIAL, evidence_id="short-credential", valid_until=5)
        intent = self.reserve()
        self.service.advance_resource_clock(5, idempotency_key=self.driver.key())
        self.service.advance_clock("ctx", 5, idempotency_key=self.driver.key())
        view = self.service.inspect_execution_intent("attempt")
        self.assertEqual((view.state, view.readiness), ("pending", Status.UNKNOWN))
        self.assertEqual(view.intent, intent)
        self.assertEqual(self.service.inspect_resource("slot").used_now, 1)
