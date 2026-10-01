from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier, Event
import unittest
from unittest.mock import patch

from reachability.dispatch import Dispatcher
from reachability.model import Status
from reachability.service import AdmissionDenied, AdmissionService, IdempotencyConflict
from reachability.simulated_executor import SimulatedExecutor
from tests.dispatch_support import DispatchFixture
from tests.lifecycle_support import CREDENTIAL, observe


class DispatchTests(DispatchFixture, unittest.TestCase):
    def test_prepare_persists_uncertainty_without_calling_executor(self):
        marker = self.prepare()
        self.assertEqual(marker.request.intent, self.intent)
        self.assertEqual(self.executor.total_effects, 0)
        self.assertEqual(self.service.inspect_dispatch("attempt").state, "uncertain")
        self.assertEqual(self.service.inspect_resource("slot").reconciliation_attempts, ("attempt",))
        self.restart()
        self.assertEqual(self.service.inspect_dispatch("attempt").dispatch, marker)
        self.assertEqual(self.executor.total_effects, 0)

    def test_submission_ack_is_not_completion_product_or_goal_relief(self):
        snapshot = self.service.snapshot("ctx")
        view = self.dispatch()
        self.assertEqual(view.state, "accepted")
        self.assertEqual(view.latest_receipt.effect_count, 1)
        self.assertEqual(self.executor.total_effects, 1)
        self.assertEqual(self.service.snapshot("ctx"), snapshot)
        self.assertEqual(self.service.inspect_lifecycle("episode").episode.stage, "DRAFT")
        self.assertEqual(self.service.inspect_operation("attempt").outcome_status, Status.UNKNOWN)
        self.assertFalse(view.resources_released)

    def test_repeated_dispatch_and_restart_keep_one_request_and_effect(self):
        first = self.dispatch()
        for _ in range(2):
            self.restart()
            self.assertEqual(self.dispatch().dispatch.request, first.dispatch.request)
            self.assertEqual(self.executor.total_effects, 1)
        self.assertEqual(len(self.service.inspect_dispatch("attempt").dispatch.receipts), 1)

    def test_two_dispatchers_cannot_send_a_non_idempotent_attempt_twice(self):
        self.configure_executor(supports_idempotency=False, supports_query=False)
        barrier = Barrier(2)

        def send(_):
            barrier.wait(timeout=5)
            return self.dispatch().state

        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(list(pool.map(send, range(2))), ["accepted", "accepted"])
        self.assertEqual(self.executor.total_effects, 1)

    def test_revoked_credentials_block_initial_submission(self):
        self.service.revoke_evidence("credential", idempotency_key=self.driver.key())
        with self.assertRaises(AdmissionDenied):
            self.dispatch()
        self.assertEqual(self.executor.total_effects, 0)
        with self.assertRaises(KeyError):
            self.service.inspect_dispatch("attempt")

    def test_recovered_marker_cannot_authorize_submission_under_revoked_support(self):
        self.prepare()
        self.service.revoke_evidence("credential", idempotency_key=self.driver.key())
        self.restart()
        with self.assertRaises(AdmissionDenied):
            self.dispatch()
        self.assertEqual(self.executor.total_effects, 0)
        self.assertEqual(self.service.inspect_dispatch("attempt").state, "uncertain")

    def test_expired_lease_blocks_resubmission_but_holds_uncertain_capacity(self):
        self.prepare()
        self.service.advance_resource_clock(10, idempotency_key=self.driver.key())
        self.service.advance_clock("ctx", 10, idempotency_key=self.driver.key())
        with self.assertRaises(AdmissionDenied):
            self.dispatch()
        self.assertEqual(self.service.inspect_resource("slot").reconciliation_attempts, ("attempt",))
        self.operation("other")
        self.assertEqual(self.permit("other").status, Status.UNKNOWN)
        self.assertEqual(self.executor.total_effects, 0)

    def test_storage_is_required_for_the_submission_boundary(self):
        with AdmissionService() as volatile, self.assertRaises(AdmissionDenied) as failure:
            volatile.prepare_dispatch("attempt", "policy", "1", "owner", idempotency_key="prepare")
        self.assertEqual(failure.exception.status, Status.FAIL)

    def test_wrong_owner_or_executor_instance_cannot_send_or_release(self):
        with self.assertRaises(AdmissionDenied):
            self.dispatcher.dispatch("attempt", "dispatch", "1", "intruder")
        with SimulatedExecutor(self.directory / "wrong.db") as wrong:
            with self.assertRaises(AdmissionDenied):
                Dispatcher(self.service, wrong).dispatch("attempt", "dispatch", "1", "worker")
            self.assertEqual(wrong.total_effects, 0)
        self.dispatch()
        with self.assertRaises(AdmissionDenied):
            self.dispatcher.release("attempt", "intruder")

    def test_policy_revision_cannot_rebind_an_already_prepared_attempt(self):
        self.prepare()
        changed = replace(self.policy, revision="2")
        self.service.register_dispatch_policy(changed, idempotency_key=self.driver.key())
        with self.assertRaises(IdempotencyConflict):
            self.dispatcher.dispatch("attempt", "dispatch", "2", "worker")
        with self.assertRaises(IdempotencyConflict):
            self.service.register_dispatch_policy(replace(self.policy, executor=replace(
                self.policy.executor, supports_query=False)), idempotency_key=self.driver.key())
        with self.assertRaises(AdmissionDenied):
            self.service.register_dispatch_policy(replace(changed, executor=replace(
                changed.executor, executor_id="wrong")), idempotency_key=self.driver.key())

    def test_lost_submission_reply_is_reconciled_without_another_effect(self):
        original = self.executor.submit

        def lose_reply(request):
            original(request)
            raise TimeoutError("reply lost")

        with patch.object(self.executor, "submit", lose_reply):
            self.assertEqual(self.dispatch().state, "uncertain")
        self.restart()
        self.assertEqual(self.dispatch().state, "accepted")
        self.assertEqual(self.executor.total_effects, 1)

    def test_idempotent_retry_without_query_uses_same_envelope(self):
        self.configure_executor(supports_query=False)
        original = self.executor.submit

        def lose_reply(request):
            original(request)
            raise TimeoutError("reply lost")

        with patch.object(self.executor, "submit", lose_reply):
            first = self.dispatch()
        self.restart()
        second = self.dispatch()
        self.assertEqual(second.state, "accepted")
        self.assertEqual(first.dispatch.request, second.dispatch.request)
        self.assertEqual(self.executor.total_effects, 1)

    def test_non_idempotent_lost_reply_remains_uncertain_without_blind_retry(self):
        self.configure_executor(supports_idempotency=False, supports_query=False, supports_release=False)
        original = self.executor.submit

        def lose_reply(request):
            original(request)
            raise TimeoutError("reply lost")

        with patch.object(self.executor, "submit", lose_reply):
            self.assertEqual(self.dispatch().state, "uncertain")
        self.restart()
        self.assertEqual(self.dispatch().state, "uncertain")
        self.assertEqual(self.executor.total_effects, 1)
        with self.assertRaises(AdmissionDenied) as failure:
            self.dispatcher.release("attempt", "worker")
        self.assertEqual(failure.exception.status, Status.UNKNOWN)

    def test_authoritative_absence_is_insufficient_to_retry_non_idempotent_submission(self):
        self.configure_executor(supports_idempotency=False)
        self.prepare()  # Models a crash after marking submission but before sending.
        view = self.dispatch()
        self.assertEqual((view.state, view.latest_receipt.state), ("uncertain", "absent"))
        self.assertEqual(self.executor.total_effects, 0)
        self.assertEqual(self.service.inspect_resource("slot").reconciliation_attempts, ("attempt",))

    def test_non_idempotent_executor_can_reconcile_an_existing_effect(self):
        self.configure_executor(supports_idempotency=False)
        marker = self.prepare()
        self.executor.submit(marker.request)
        self.assertEqual(self.dispatch().state, "accepted")
        self.assertEqual(self.executor.total_effects, 1)

    def test_release_fences_delayed_submission_and_frees_capacity(self):
        marker = self.prepare()
        released = self.dispatcher.release("attempt", "worker")
        self.assertTrue(released.resources_released)
        self.assertEqual(released.latest_receipt.effect_count, 0)
        self.assertEqual(self.service.inspect_resource("slot").reservations, ())
        # A request still in flight cannot recreate occupancy after release.
        self.assertEqual(self.executor.submit(marker.request).state, "released")
        self.assertEqual(self.executor.total_effects, 0)
        self.assertEqual(self.dispatch().state, "released")
        self.operation("retry")
        self.assertEqual(self.permit("retry").status, Status.PASS)

    def test_release_and_reconciliation_do_not_need_expired_action_credentials(self):
        self.dispatch()
        self.service.revoke_evidence("credential", idempotency_key=self.driver.key())
        self.service.advance_resource_clock(20, idempotency_key=self.driver.key())
        self.service.advance_clock("ctx", 20, idempotency_key=self.driver.key())
        self.assertEqual(self.dispatcher.reconcile("attempt", "worker").state, "accepted")
        self.assertTrue(self.dispatcher.release("attempt", "worker").resources_released)
        self.assertEqual(self.executor.total_effects, 1)  # Release does not erase history.
        self.assertEqual(self.service.inspect_resource("slot").reconciliation_attempts, ())

    def test_local_cancel_and_passive_milestones_cannot_release_dispatched_capacity(self):
        self.dispatch()
        for milestone in ("completion_observed", "exact_product_observed", "cancellation_observed"):
            observe(self.driver, milestone)
        with self.assertRaises(AdmissionDenied):
            self.service.cancel_execution_intent("attempt", "worker", 0, idempotency_key=self.driver.key())
        self.assertEqual(self.service.inspect_resource("slot").reconciliation_attempts, ("attempt",))
        self.assertTrue(self.dispatcher.release("attempt", "worker").resources_released)
        observe(self.driver, "failure_observed")  # Historical callbacks remain recordable after fencing.
        self.assertEqual(self.service.inspect_resource("slot").reservations, ())

    def test_receipts_bind_executor_instance_request_payload_and_capabilities(self):
        marker = self.prepare()
        receipt = self.executor.submit(marker.request)
        bad_receipts = (replace(receipt, instance_id="wrong"), replace(receipt, executor_id="wrong"),
                        replace(receipt, request_id="wrong"), replace(receipt, request_fingerprint="wrong"),
                        replace(receipt, effect_count=2))
        for bad in bad_receipts:
            with self.subTest(bad=bad), self.assertRaises(AdmissionDenied):
                self.service.record_dispatch_receipt("attempt", "submission", bad, idempotency_key=self.driver.key())
        self.assertEqual(self.service.inspect_dispatch("attempt").state, "uncertain")

    def test_late_receipt_cannot_undo_terminal_release(self):
        accepted = self.dispatch().latest_receipt
        released = self.dispatcher.release("attempt", "worker")
        self.service.record_dispatch_receipt("attempt", "submission", accepted, idempotency_key=self.driver.key())
        self.assertEqual(self.service.inspect_dispatch("attempt").state, "released")
        with self.assertRaises(AdmissionDenied):
            self.service.record_dispatch_receipt("attempt", "submission",
                replace(accepted, sequence=released.latest_receipt.sequence + 1), idempotency_key=self.driver.key())

    def test_receipt_conflicts_and_unsupported_query_authority_are_rejected(self):
        marker = self.prepare()
        accepted = self.executor.submit(marker.request)
        self.service.record_dispatch_receipt("attempt", "submission", accepted, idempotency_key=self.driver.key())
        absent = replace(accepted, state="absent", effect_count=0)
        with self.assertRaises(AdmissionDenied):
            self.service.record_dispatch_receipt("attempt", "query", absent, idempotency_key=self.driver.key())
        with self.assertRaises(ValueError):
            replace(accepted, state="released", fenced=False)

    def test_service_revisions_cannot_interleave_with_gate_check_and_submit(self):
        entered, revoking = Event(), Event()
        original = self.executor.submit

        def submit(request):
            entered.set()
            self.assertTrue(revoking.wait(timeout=5))
            self.assertEqual(self.service.query_belief("ctx", CREDENTIAL).status, Status.PASS)
            return original(request)

        def revoke():
            self.assertTrue(entered.wait(timeout=5))
            revoking.set()
            self.service.revoke_evidence("credential", idempotency_key="concurrent-revoke")

        with patch.object(self.executor, "submit", submit), ThreadPoolExecutor(max_workers=2) as pool:
            sent = pool.submit(self.dispatch)
            revoked = pool.submit(revoke)
            self.assertEqual(sent.result(timeout=10).state, "accepted")
            revoked.result(timeout=10)
        self.assertEqual(self.executor.total_effects, 1)
        self.assertEqual(self.service.inspect_operation("attempt").readiness, Status.UNKNOWN)

    def test_receipts_cannot_claim_query_or_release_capabilities_not_in_policy(self):
        self.configure_executor(supports_query=False, supports_release=False)
        marker = self.prepare()
        receipt = self.executor.submit(marker.request)
        with self.assertRaises(AdmissionDenied):
            self.service.record_dispatch_receipt("attempt", "query", receipt, idempotency_key=self.driver.key())
        with self.assertRaises(AdmissionDenied):
            self.service.record_dispatch_receipt("attempt", "release",
                replace(receipt, state="released", fenced=True), idempotency_key=self.driver.key())
