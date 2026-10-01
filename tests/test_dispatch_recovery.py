from pathlib import Path
import json
import shutil
import sqlite3
import subprocess
import sys
import unittest
from unittest.mock import patch

from reachability.dispatch import Dispatcher
from reachability.dispatch_model import DispatchPolicy
from reachability.journal import RecoveryError, SQLiteJournal
from reachability.service import AdmissionService
from reachability.simulated_executor import SimulatedExecutor
from tests.dispatch_support import DispatchFixture


CRASH_SCRIPT = '''
import os, sys
from reachability.dispatch import Dispatcher
from reachability.service import AdmissionService
from reachability.simulated_executor import SimulatedExecutor
service = AdmissionService(database=sys.argv[1])
executor = SimulatedExecutor(sys.argv[2])
phase, side, operation, policy_revision = sys.argv[3:]
journal = executor._journal if phase in ("submit", "release") else service._journal
original = journal.append
def crash(*args):
    if args[0] == phase:
        if side == "after":
            original(*args)
        os._exit(73)
    return original(*args)
journal.append = crash
dispatcher = Dispatcher(service, executor)
if operation == "dispatch":
    dispatcher.dispatch("attempt", "dispatch", policy_revision, "worker")
else:
    dispatcher.release("attempt", "worker")
raise AssertionError("crash boundary was not reached")
'''


class DispatchRecoveryTests(DispatchFixture, unittest.TestCase):
    def crash_copy(self, name, phase, side, operation="dispatch"):
        directory = self.directory / name
        directory.mkdir()
        local, remote = directory / "admission.db", directory / "executor.db"
        shutil.copy2(self.path, local)
        shutil.copy2(self.executor_path, remote)
        outcome = subprocess.run([sys.executable, "-c", CRASH_SCRIPT, str(local), str(remote),
            phase, side, operation, self.policy.revision], capture_output=True, text=True, timeout=20)
        self.assertEqual(outcome.returncode, 73, outcome.stderr)
        return local, remote

    def test_real_process_crashes_at_all_three_submission_boundaries(self):
        self.service.close()
        self.executor.close()
        for phase in ("prepare_dispatch", "submit", "record_dispatch_receipt"):
            for side in ("before", "after"):
                with self.subTest(phase=phase, side=side):
                    local, remote = self.crash_copy(f"{phase}-{side}", phase, side)
                    with AdmissionService(database=local) as service, SimulatedExecutor(remote) as executor:
                        expected_effects = int(phase == "record_dispatch_receipt" or phase == "submit" and side == "after")
                        self.assertEqual(executor.total_effects, expected_effects)
                        if phase == "prepare_dispatch" and side == "before":
                            with self.assertRaises(KeyError):
                                service.inspect_dispatch("attempt")
                            self.assertEqual(service.inspect_resource("slot").reconciliation_attempts, ())
                        else:
                            expected_state = "accepted" if phase == "record_dispatch_receipt" and side == "after" else "uncertain"
                            self.assertEqual(service.inspect_dispatch("attempt").state, expected_state)
                            self.assertEqual(service.inspect_resource("slot").reconciliation_attempts, ("attempt",))
                        recovered = Dispatcher(service, executor).dispatch("attempt", "dispatch", "1", "worker")
                        self.assertEqual(recovered.state, "accepted")
                        self.assertEqual(executor.total_effects, 1)

    def test_real_non_idempotent_crashes_never_trigger_a_blind_retry(self):
        self.configure_executor(supports_idempotency=False, supports_query=False, supports_release=False)
        self.service.close()
        self.executor.close()
        for side, effects in (("before", 0), ("after", 1)):
            with self.subTest(side=side):
                local, remote = self.crash_copy(side, "submit", side)
                with AdmissionService(database=local) as service, SimulatedExecutor(remote) as executor:
                    view = Dispatcher(service, executor).dispatch("attempt", "dispatch", self.policy.revision, "worker")
                    self.assertEqual(view.state, "uncertain")
                    self.assertEqual(executor.total_effects, effects)
                    self.assertEqual(service.inspect_resource("slot").reconciliation_attempts, ("attempt",))

    def test_real_process_crashes_at_executor_release_and_local_receipt_boundaries(self):
        request = self.dispatch().dispatch.request
        self.service.close()
        self.executor.close()
        for phase in ("release", "record_dispatch_receipt"):
            for side in ("before", "after"):
                with self.subTest(phase=phase, side=side):
                    local, remote = self.crash_copy(f"{phase}-{side}", phase, side, "release")
                    with AdmissionService(database=local) as service, SimulatedExecutor(remote) as executor:
                        remote_released = phase == "record_dispatch_receipt" or side == "after"
                        local_released = phase == "record_dispatch_receipt" and side == "after"
                        self.assertEqual(executor.query(request).fenced, remote_released)
                        self.assertEqual(service.inspect_dispatch("attempt").resources_released, local_released)
                        self.assertEqual(bool(service.inspect_resource("slot").reservations), not local_released)
                        view = Dispatcher(service, executor).release("attempt", "worker")
                        self.assertTrue(view.resources_released)
                        self.assertEqual(service.inspect_resource("slot").reservations, ())
                        self.assertEqual(executor.submit(request).state, "released")
                        self.assertEqual(executor.total_effects, 1)

    def test_failed_submission_marker_prevents_any_executor_call(self):
        with patch.object(self.service._journal, "append", side_effect=OSError("failed local commit")):
            with self.assertRaises(OSError):
                self.dispatch()
        self.assertEqual(self.executor.total_effects, 0)
        with self.assertRaises(RecoveryError):
            self.service.resource_snapshot()
        self.restart()
        with self.assertRaises(KeyError):
            self.service.inspect_dispatch("attempt")
        self.assertEqual(self.dispatch().state, "accepted")

    def test_lost_marker_commit_reply_keeps_the_original_attempt(self):
        original = self.service._journal.append

        def lose_reply(*args):
            original(*args)
            raise OSError("lost local commit reply")

        with patch.object(self.service._journal, "append", lose_reply), self.assertRaises(OSError):
            self.dispatch()
        self.assertEqual(self.executor.total_effects, 0)
        self.restart()
        request = self.service.inspect_dispatch("attempt").dispatch.request
        self.assertEqual(self.dispatch().dispatch.request, request)
        self.assertEqual(self.executor.total_effects, 1)

    def test_failed_receipt_commit_reconciles_the_already_created_effect(self):
        original = self.service._journal.append

        def fail_receipt(*args):
            if args[0] == "record_dispatch_receipt":
                raise OSError("receipt write failed")
            return original(*args)

        with patch.object(self.service._journal, "append", fail_receipt), self.assertRaises(OSError):
            self.dispatch()
        self.assertEqual(self.executor.total_effects, 1)
        self.restart()
        self.assertEqual(self.service.inspect_dispatch("attempt").state, "uncertain")
        self.assertEqual(self.dispatch().state, "accepted")
        self.assertEqual(self.executor.total_effects, 1)

    def test_failed_release_receipt_cannot_publish_available_capacity(self):
        self.dispatch()
        with patch.object(self.service._journal, "append", side_effect=OSError("receipt write failed")):
            with self.assertRaises(OSError):
                self.dispatcher.release("attempt", "worker")
        self.restart()
        self.assertFalse(self.service.inspect_dispatch("attempt").resources_released)
        self.assertEqual(self.service.inspect_resource("slot").reconciliation_attempts, ("attempt",))
        self.assertTrue(self.dispatcher.reconcile("attempt", "worker").resources_released)
        self.assertEqual(self.service.inspect_resource("slot").reservations, ())

    def test_lost_release_reply_does_not_erase_effect_or_release_local_claims_early(self):
        self.dispatch()
        original = self.executor.release

        def lose_reply(request):
            original(request)
            raise TimeoutError("release reply lost")

        with patch.object(self.executor, "release", lose_reply):
            self.assertFalse(self.dispatcher.release("attempt", "worker").resources_released)
        self.restart()
        self.assertTrue(self.dispatcher.reconcile("attempt", "worker").resources_released)
        self.assertEqual(self.executor.total_effects, 1)

    def test_cold_replay_never_invokes_submission_or_release(self):
        accepted = self.dispatch()
        self.service.close()
        self.executor.close()
        with patch.object(SimulatedExecutor, "submit", side_effect=AssertionError("replayed I/O")), \
             patch.object(SimulatedExecutor, "release", side_effect=AssertionError("replayed I/O")):
            self.restart()
        self.assertEqual(self.service.inspect_dispatch("attempt"), accepted)
        self.assertEqual(self.executor.total_effects, 1)

    def test_committed_resource_intent_journal_recovers_and_accepts_dispatch_commands(self):
        fixture = json.loads((Path(__file__).parent / "fixtures/execution_v1_journal.json").read_text())
        self.assertEqual(fixture["producer_commit"], "9da7639c86d5f679584ec911b3e1dc9760b82f54")
        path = self.directory / "legacy.db"
        journal = SQLiteJournal(path, {})
        journal.close()
        with sqlite3.connect(path) as connection:
            connection.execute("UPDATE metadata SET value=? WHERE id=1", (fixture["metadata"],))
            connection.executemany("INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?)", fixture["events"])
        with AdmissionService(database=path) as legacy:
            intent = legacy.inspect_execution_intent("attempt").intent
            self.assertEqual(legacy.inspect_resource("slot").used_now, 1)
            legacy.register_dispatch_policy(DispatchPolicy("dispatch", "1", "build", "1", self.executor.profile),
                                             idempotency_key="dispatch-policy")
            view = Dispatcher(legacy, self.executor).dispatch("attempt", "dispatch", "1", "worker")
            self.assertEqual(view.dispatch.request.intent, intent)
        with AdmissionService(database=path) as recovered:
            self.assertEqual(recovered.inspect_dispatch("attempt"), view)
            self.assertEqual(self.executor.total_effects, 1)
