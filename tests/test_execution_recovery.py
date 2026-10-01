from dataclasses import replace
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from reachability.execution_model import ResourceDefinition, ResourceDemand
from reachability.journal import RecoveryError
from reachability.model import Status
from reachability.service import AdmissionService
from tests.execution_support import ExecutionFixture
from tests.lifecycle_support import observe


class ExecutionRecoveryTests(ExecutionFixture, unittest.TestCase):
    def make_service(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "execution.db"
        return AdmissionService(database=self.path)

    def setUp(self):
        super().setUp()
        self.service.register_resource(ResourceDefinition("memory", 4, "pages"), idempotency_key=self.driver.key())
        self.contract = replace(self.contract, revision="2", demands=(*self.contract.demands,
                                ResourceDemand("memory", 2, "pages")))
        self.service.register_execution_contract(self.contract, idempotency_key=self.driver.key())

    def restart(self):
        self.service.close()
        self.service = AdmissionService(database=self.path)
        self.driver.service = self.service

    def assert_occupancy(self, slot, memory):
        self.assertEqual(self.service.inspect_resource("slot").used_now, slot)
        self.assertEqual(self.service.inspect_resource("memory").used_now, memory)

    def test_pending_certificate_recovers_and_reserves_exact_claims(self):
        permit = self.permit()
        self.restart()
        intent = self.reserve(permit, key="reserve")
        self.assert_occupancy(1, 2)
        self.restart()
        self.assertEqual(self.service.inspect_execution_intent("attempt").intent, intent)
        self.assertEqual(self.reserve(permit, key="reserve"), intent)
        self.assert_occupancy(1, 2)

    def test_failed_atomic_append_rolls_back_all_claims_and_intent(self):
        permit = self.permit()
        with patch.object(self.service._journal, "append", side_effect=OSError("failed write")):
            with self.assertRaises(OSError):
                self.reserve(permit, key="reserve")
        with self.assertRaises(RecoveryError):
            self.service.inspect_resource("slot")
        self.restart()
        self.assert_occupancy(0, 0)
        with self.assertRaises(KeyError):
            self.service.inspect_execution_intent("attempt")
        self.reserve(permit, key="reserve")
        self.assert_occupancy(1, 2)

    def test_lost_commit_reply_recovers_same_attempt_and_reservation_ids(self):
        permit = self.permit()
        original = self.service._journal.append

        def lost_reply(*args):
            original(*args)
            raise OSError("reply lost after COMMIT")

        with patch.object(self.service._journal, "append", lost_reply), self.assertRaises(OSError):
            self.reserve(permit, key="reserve")
        self.restart()
        intent = self.service.inspect_execution_intent("attempt").intent
        self.assertEqual(self.reserve(permit, key="reserve"), intent)
        self.assertEqual(len(intent.reservations), 2)
        self.assert_occupancy(1, 2)

    def test_failed_local_cancellation_cannot_publish_released_capacity(self):
        self.reserve()
        with patch.object(self.service._journal, "append", side_effect=OSError("failed write")):
            with self.assertRaises(OSError):
                self.service.cancel_execution_intent("attempt", "worker", 0, idempotency_key="cancel")
        self.restart()
        self.assert_occupancy(1, 2)
        self.assertEqual(self.service.inspect_execution_intent("attempt").state, "pending")

    def test_event_prefixes_recover_ownership_expiry_and_remote_uncertainty(self):
        self.reserve()
        self.restart()
        self.assert_occupancy(1, 2)
        self.service.advance_resource_clock(10, idempotency_key=self.driver.key())
        self.service.advance_clock("ctx", 10, idempotency_key=self.driver.key())
        self.restart()
        self.assert_occupancy(0, 0)
        self.assertEqual(self.service.inspect_execution_intent("attempt").state, "expired")
        self.operation("retry")
        self.reserve(self.permit("retry"))
        self.restart()
        self.assert_occupancy(1, 2)
        observe(self.driver, "accepted_by_executor", attempt="attempt")
        self.restart()
        self.assertEqual(self.service.inspect_resource("slot").reconciliation_attempts, ("attempt",))
        self.assertEqual(self.service.inspect_execution_intent("retry").readiness, Status.UNKNOWN)
        self.assertFalse(self.service.inspect_execution_intent("retry").execution_authorized)

    def test_observation_and_resource_freeze_share_one_durable_transaction(self):
        self.reserve()
        from reachability.lifecycle_model import milestone_literal
        from tests.lifecycle_support import accept
        belief = accept(self.driver, milestone_literal("attempt", "artifact-v2", "submitted"), source="executor")
        revision = self.service.resource_snapshot().revision
        with patch.object(self.service._journal, "append", side_effect=OSError("failed write")):
            with self.assertRaises(OSError):
                self.service.record_operation_observation("submitted", "attempt", "submitted",
                    belief.belief_revision_id, idempotency_key="submitted")
        self.restart()
        self.assertEqual(self.service.resource_snapshot().revision, revision)
        self.assertEqual(self.service.inspect_execution_intent("attempt").state, "pending")
        self.service.record_operation_observation("submitted", "attempt", "submitted", belief.belief_revision_id,
                                                  idempotency_key="submitted")
        self.restart()
        self.assertEqual(self.service.resource_snapshot().revision, revision + 1)
        self.assertEqual(self.service.inspect_execution_intent("attempt").state, "reconciliation_required")

    def test_real_process_crash_before_and_after_atomic_intent_commit(self):
        self.service.close()
        script = '''
import os, sys
from reachability.service import AdmissionService
service = AdmissionService(database=sys.argv[1])
permit = service.certify_execution("attempt", "build", "2", "worker",
    service.inspect_operation("attempt").operation.revision,
    service.snapshot("ctx").knowledge_revision, service.resource_snapshot().revision,
    idempotency_key="crash-cert")
original = service._journal.append
def crash(*args):
    if sys.argv[2] == "after":
        original(*args)
    os._exit(73)
service._journal.append = crash
service.reserve_and_record_intent(permit, idempotency_key="crash-intent")
'''
        for mode, expected in (("before", (0, 0)), ("after", (1, 2))):
            with self.subTest(mode=mode):
                outcome = subprocess.run([sys.executable, "-c", script, str(self.path), mode],
                                         capture_output=True, text=True, timeout=15)
                self.assertEqual(outcome.returncode, 73, outcome.stderr)
                self.restart()
                self.assert_occupancy(*expected)
                if mode == "before":
                    with self.assertRaises(KeyError):
                        self.service.inspect_execution_intent("attempt")
                else:
                    self.assertEqual(len(self.service.inspect_execution_intent("attempt").intent.reservations), 2)
                self.service.close()
