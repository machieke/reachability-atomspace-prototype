import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from reachability.journal import RecoveryError, SQLiteJournal
from reachability.model import Status
from reachability.service import AdmissionService
from tests.lifecycle_support import CREDENTIAL, PRODUCT, TESTED, accept, certify, observe, schema
from tests.support import Driver, lit


class LifecycleRecoveryTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "lifecycle.db"
        self.service = AdmissionService(database=self.path)
        self.addCleanup(lambda: self.service.close())
        self.driver = Driver(self.service)
        self.driver.context()
        self.service.register_lifecycle_schema(schema(), idempotency_key=self.driver.key())
        self.service.open_lifecycle_episode("episode", "ctx", "artifact", "1", idempotency_key=self.driver.key())
        for literal in (TESTED, CREDENTIAL, PRODUCT):
            accept(self.driver, literal)

    def restart(self):
        self.service.close()
        self.service = AdmissionService(database=self.path)
        self.driver.service = self.service

    def test_operation_prefixes_recover_without_inventing_missing_milestones(self):
        self.service.propose_operation("build", "attempt", "episode", "build", idempotency_key=self.driver.key())
        expected = set()
        for milestone in ("completion_observed", "accepted_by_executor", "exact_product_observed"):
            observe(self.driver, milestone)
            expected.add(milestone)
            before = self.service.inspect_operation("attempt")
            self.restart()
            after = self.service.inspect_operation("attempt")
            self.assertEqual(after, before)
            self.assertEqual(set(after.current_milestones), expected)
            self.assertEqual(after.outcome_status, Status.PASS if "exact_product_observed" in expected else Status.UNKNOWN)
            self.assertFalse(after.execution_authorized)

    def test_pending_transition_permit_survives_recovery_with_exact_binding(self):
        permit = certify(self.driver)
        self.restart()
        result = self.service.advance_lifecycle(permit, 0, idempotency_key="advance")
        self.restart()
        self.assertEqual(self.service.inspect_lifecycle("episode").episode, result)
        self.assertEqual(self.service.advance_lifecycle(permit, 0, idempotency_key="advance"), result)

    def test_failed_transition_append_rolls_back_lifecycle_and_requires_recovery(self):
        permit = certify(self.driver)
        with patch.object(self.service._journal, "append", side_effect=OSError("injected failure")):
            with self.assertRaises(OSError):
                self.service.advance_lifecycle(permit, 0, idempotency_key="advance")
        with self.assertRaises(RecoveryError):
            self.service.inspect_lifecycle("episode")
        self.restart()
        self.assertEqual(self.service.inspect_lifecycle("episode").episode.stage, "DRAFT")
        result = self.service.advance_lifecycle(permit, 0, idempotency_key="advance")
        self.assertEqual(result.stage, "BUILT")
        self.assertEqual(len(result.events), 1)

    def test_lost_callback_commit_response_is_reconciled_without_duplicate_history(self):
        self.service.propose_operation("build", "attempt", "episode", "build", idempotency_key=self.driver.key())
        observation = observe(self.driver, "accepted_by_executor")
        # A different observed milestone is accepted before inserting its ledger event.
        from reachability.lifecycle_model import milestone_literal
        support = accept(self.driver, milestone_literal("attempt", "artifact-v2", "completion_observed"), source="executor")
        original = self.service._journal.append

        def fail_after_commit(*args):
            original(*args)
            raise OSError("lost reply")

        with patch.object(self.service._journal, "append", fail_after_commit), self.assertRaises(OSError):
            self.service.record_operation_observation("completion", "attempt", "completion_observed",
                support.belief_revision_id, idempotency_key="completion")
        self.restart()
        result = self.service.record_operation_observation("completion", "attempt", "completion_observed",
            support.belief_revision_id, idempotency_key="completion")
        observations = self.service.inspect_operation("attempt").operation.observations
        self.assertEqual(observations, (observation, result))
        self.assertEqual(self.service.inspect_operation("attempt").outcome_status, Status.UNKNOWN)

    def test_real_process_crash_on_each_side_of_lifecycle_commit(self):
        self.service.close()
        script = '''
import os, sys
from reachability.service import AdmissionService
service = AdmissionService(database=sys.argv[1])
permit = service.certify_lifecycle_transition("episode", "build", 0,
    service.snapshot("ctx").knowledge_revision, idempotency_key="crash-cert")
original = service._journal.append
def crash(*args):
    if sys.argv[2] == "after":
        original(*args)
    os._exit(73)
service._journal.append = crash
service.advance_lifecycle(permit, 0, idempotency_key="crash-advance")
'''
        for mode, stage in (("before", "DRAFT"), ("after", "BUILT")):
            with self.subTest(mode=mode):
                outcome = subprocess.run([sys.executable, "-c", script, str(self.path), mode],
                                         capture_output=True, text=True, timeout=15)
                self.assertEqual(outcome.returncode, 73, outcome.stderr)
                self.restart()
                view = self.service.inspect_lifecycle("episode")
                self.assertEqual(view.episode.stage, stage)
                self.assertEqual(len(view.episode.events), int(stage == "BUILT"))
                self.service.close()

    def test_journal_produced_by_committed_v2_implementation_still_recovers(self):
        fixture = json.loads((Path(__file__).parent / "fixtures/admission_v2_journal.json").read_text())
        self.assertEqual(fixture["producer_commit"], "3e2516ea2205a90aa6d414588b810dde7324e65c")
        path = self.path.with_name("legacy.db")
        journal = SQLiteJournal(path, {})
        journal.close()
        with sqlite3.connect(path) as connection:
            connection.execute("UPDATE metadata SET value=? WHERE id=1", (fixture["metadata"],))
            connection.executemany("INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?)", fixture["events"])
        with AdmissionService(database=path) as legacy:
            view = legacy.query_belief("legacy", lit("A"))
            self.assertEqual(view.status, Status.STALE)
            self.assertEqual(len(view.historical), 1)
            self.assertEqual(legacy.snapshot("legacy").logical_time, 5)
            legacy.register_lifecycle_schema(schema(), idempotency_key="new-schema")
            episode = legacy.open_lifecycle_episode("new-episode", "legacy", "artifact", "1",
                                                     idempotency_key="new-episode")
        with AdmissionService(database=path) as extended:
            self.assertEqual(extended.inspect_lifecycle("new-episode").episode, episode)
