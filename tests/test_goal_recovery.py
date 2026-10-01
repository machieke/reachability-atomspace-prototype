from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from reachability.goal_model import DurabilityResult
from reachability.journal import RecoveryError
from reachability.model import Check, Status
from reachability.service import AdmissionService
from tests.goal_support import GoalFixture


class GoalRecoveryTests(GoalFixture, unittest.TestCase):
    def make_service(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.path = self.directory / "goals.db"
        return AdmissionService(database=self.path)

    def restart(self):
        self.service.close()
        self.service = AdmissionService(database=self.path)
        self.driver.service = self.service

    def test_event_prefixes_recover_pending_success_failure_and_censoring(self):
        self.product()
        for time in (0, 1, 2):
            self.tick(time)
            self.sample(time)
            self.reconcile()
            before = self.service.inspect_goal("goal")
            self.restart()
            self.assertEqual(self.service.inspect_goal("goal"), before)
        self.tick(3)
        self.sample(3, healthy=False)
        self.assertEqual(self.reconcile().events[0].kind, "reopened")
        self.service.censor_goal_monitor("goal", "healthy", "telemetry ended", idempotency_key=self.driver.key())
        self.reconcile()
        before = self.service.inspect_goal("goal")
        self.restart()
        self.assertEqual(self.service.inspect_goal("goal"), before)
        self.assertEqual(before.projection.slices[0].label, "CENSORED")

    def test_failed_relief_append_cannot_publish_history_and_recovery_rechecks_evidence(self):
        self.product()
        self.sample(0, slice_id="available")
        fingerprint = self.projection().fingerprint
        with patch.object(self.service._journal, "append", side_effect=OSError("failed write")):
            with self.assertRaises(OSError):
                self.service.reconcile_goal("goal", fingerprint, idempotency_key="account")
        with self.assertRaises(RecoveryError):
            self.service.inspect_goal("goal")
        self.restart()
        view = self.service.inspect_goal("goal")
        self.assertEqual(view.history, ())
        self.assertEqual(view.projection.outstanding_loss, 6)
        self.assertTrue(view.reconciliation_needed)
        self.assertEqual(self.reconcile().events[0].units, 4)

    def test_lost_accounting_reply_does_not_duplicate_relief(self):
        self.product()
        self.sample(0, slice_id="available")
        fingerprint = self.projection().fingerprint
        original = self.service._journal.append

        def lose_reply(*args):
            original(*args)
            raise OSError("reply lost")

        with patch.object(self.service._journal, "append", lose_reply), self.assertRaises(OSError):
            self.service.reconcile_goal("goal", fingerprint, idempotency_key="account")
        self.restart()
        record = self.service.reconcile_goal("goal", fingerprint, idempotency_key="account")
        self.assertEqual(record.events[0].units, 4)
        self.assertEqual(len(self.service.inspect_goal("goal").history), 1)

    def test_failed_coverage_commit_leaves_no_prediction_and_keeps_resource_ownership(self):
        with patch.object(self.service._journal, "append", side_effect=OSError("failed write")):
            with self.assertRaises(OSError):
                self.cover()
        self.restart()
        self.assertEqual(self.projection().estimated_committed_coverage, 0)
        self.assertEqual(self.service.inspect_resource("slot").used_now, 1)

    def test_saved_success_from_a_broken_monitor_is_not_trusted_on_recovery(self):
        forged = DurabilityResult("OBSERVED_SUCCESS", (), (Check("broken_monitor", Status.PASS, "injected mutant"),))
        with patch("reachability.goals.evaluate_durability", return_value=forged):
            self.assertEqual(self.reconcile().projection.outstanding_loss, 0)
        self.service.close()
        with self.assertRaises(RecoveryError):
            AdmissionService(database=self.path)

    def test_real_process_crash_before_and_after_relief_history_commit(self):
        self.product()
        self.sample(0, slice_id="available")
        self.service.close()
        script = '''
import os, sys
from reachability.service import AdmissionService
service = AdmissionService(database=sys.argv[1])
fingerprint = service.inspect_goal("goal").projection.fingerprint
original = service._journal.append
def crash(*args):
    if sys.argv[2] == "after":
        original(*args)
    os._exit(73)
service._journal.append = crash
service.reconcile_goal("goal", fingerprint, idempotency_key="crash-account")
'''
        for side in ("before", "after"):
            with self.subTest(side=side):
                path = self.directory / f"{side}.db"
                shutil.copy2(self.path, path)
                outcome = subprocess.run([sys.executable, "-c", script, str(path), side],
                                         capture_output=True, text=True, timeout=15)
                self.assertEqual(outcome.returncode, 73, outcome.stderr)
                with AdmissionService(database=path) as recovered:
                    view = recovered.inspect_goal("goal")
                    self.assertEqual(view.projection.outstanding_loss, 6)
                    self.assertEqual(len(view.history), int(side == "after"))
                    record = recovered.reconcile_goal("goal", view.projection.fingerprint, idempotency_key="crash-account")
                    self.assertEqual(record.events[0].units, 4)
                    self.assertEqual(len(recovered.inspect_goal("goal").history), 1)
