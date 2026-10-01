from dataclasses import replace
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from reachability.codec import dumps, loads
from reachability.journal import JournalEntry, RecoveryError, StoreInUse
from reachability.logic import check_consistency
from reachability.model import Clause, Evidence, Rule, Status
from reachability.service import AdmissionDenied, AdmissionService, IdempotencyConflict
from tests.support import Driver, lit

A, B, C = (lit(name) for name in "ABC")


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "admission.db"
        self.service = AdmissionService((Rule("ab", "1", (A,), B),), database=self.path)
        self.addCleanup(lambda: self.service.close())
        self.driver = Driver(self.service)
        self.driver.context()

    def restart(self):
        self.service.close()
        self.service = AdmissionService(database=self.path)
        self.driver.service = self.service

    def test_accepted_history_and_command_idempotency_survive_restart(self):
        self.driver.record("a", A)
        transition = self.service.propose_evidence("ctx", "a", idempotency_key="transition")
        prepared = self.driver.prepare(transition)
        result = self.driver.finish(prepared, "accept")
        before = self.service.snapshot("ctx")
        count = len(self.service._journal.entries())
        self.restart()
        self.assertEqual(self.service.snapshot("ctx"), before)
        self.assertEqual(self.driver.finish(prepared, "accept"), result)
        self.assertEqual(len(self.service._journal.entries()), count)
        self.assertEqual(self.service.query_belief("ctx", A).current, (result.belief,))
        with self.assertRaises(IdempotencyConflict):
            self.service.advance_clock("ctx", 1, idempotency_key="accept")

    def test_pending_certificates_are_reconstructed_and_can_be_used_if_current(self):
        self.driver.record("a", A)
        transition = self.service.propose_evidence("ctx", "a", idempotency_key="transition")
        prepared = self.driver.prepare(transition)
        self.restart()
        self.assertEqual(self.driver.finish(prepared).status, Status.PASS)

    def test_rule_policy_and_clock_changes_survive_each_event_prefix(self):
        self.service.record_evidence(Evidence("a", "ctx", A, "sensor", 0, ("root",), 5),
                                     idempotency_key="a")
        transition = self.service.propose_evidence("ctx", "a", idempotency_key="transition")
        a = self.driver.finish(self.driver.prepare(transition)).belief
        derived = self.driver.transition("ab", (a.belief_revision_id,))
        b = self.driver.finish(self.driver.prepare(derived)).belief
        old_prepared = self.driver.prepare(derived)

        def check_prefix(expected):
            before = self.service.snapshot("ctx")
            self.restart()
            self.assertEqual(before, self.service.snapshot("ctx"))
            # Hand-specified semantic expectations are independent of replay.
            self.assertEqual({x.conclusion for x in before.usable}, expected)

        check_prefix({A, B})
        self.service.replace_rule(Rule("ab", "2", (A,), C), "1", idempotency_key="rule")
        check_prefix({A})
        self.assertEqual(self.driver.finish(old_prepared).status, Status.STALE)
        current = self.driver.transition("ab", (a.belief_revision_id,))
        c = self.driver.finish(self.driver.prepare(current)).belief
        check_prefix({A, C})
        self.service.replace_policy("ctx", "p2", (Clause((B.negate(),)),),
                                    self.service.snapshot("ctx").knowledge_revision,
                                    idempotency_key="policy")
        check_prefix({A, C})
        self.service.advance_clock("ctx", 5, idempotency_key="expiry")
        check_prefix(set())
        self.assertEqual(self.service.query_belief("ctx", B).historical, (b,))
        self.assertEqual(self.service.query_belief("ctx", C).historical, (c,))
        self.assertEqual(self.service.snapshot("ctx").logical_time, 5)
        self.assertEqual(self.service.snapshot("ctx").policy_revision, "p2")

    def test_revocation_and_independent_proof_survive_restart(self):
        self.driver.adopt("a1", A)
        independent = self.driver.adopt("a2", A).belief
        self.service.revoke_evidence("a1", idempotency_key="revoke")
        self.restart()
        self.assertEqual(self.service.query_belief("ctx", A).current, (independent,))
        self.assertEqual(len(self.service.query_belief("ctx", A).historical), 2)
        transition = self.service.propose_evidence("ctx", "a1", idempotency_key="old")
        with self.assertRaises(AdmissionDenied):
            self.driver.prepare(transition)

    def test_second_authority_is_rejected_and_close_releases_ownership(self):
        with self.assertRaises(StoreInUse):
            AdmissionService(database=self.path)
        closed = self.service
        self.restart()
        with self.assertRaises(RecoveryError):
            closed.snapshot("ctx")
        self.assertEqual(self.service.snapshot("ctx").knowledge_revision, 0)

    def test_incompatible_initial_configuration_is_rejected_without_leaking_lock(self):
        self.service.close()
        with self.assertRaises(RecoveryError):
            AdmissionService(database=self.path, max_variables=2)
        with self.assertRaises(RecoveryError):
            AdmissionService((), database=self.path)
        self.service = AdmissionService(database=self.path)
        self.assertEqual(self.service.snapshot("ctx").usable, ())

    def test_validation_error_does_not_append_a_command(self):
        before = self.service.snapshot("ctx")
        count = len(self.service._journal.entries())
        with self.assertRaises(AdmissionDenied):
            self.service.open_context("bad", assumptions=(A, A.negate()), idempotency_key="bad")
        self.assertEqual(self.service.snapshot("ctx"), before)
        self.assertEqual(len(self.service._journal.entries()), count)
        self.restart()
        with self.assertRaises(KeyError):
            self.service.snapshot("bad")

    def test_partial_in_memory_mutation_is_rolled_back_on_exception(self):
        self.driver.record("a", A)
        transition = self.service.propose_evidence("ctx", "a", idempotency_key="transition")
        original = self.service._issue
        count = len(self.service._journal.entries())

        def fail(*args, **kwargs):
            original(*args, **kwargs)
            raise RuntimeError("checker interrupted after allocating a record")

        with patch.object(self.service, "_issue", fail), self.assertRaises(RuntimeError):
            self.service.precertify(transition, 1, idempotency_key="pre")
        self.assertEqual(self.service._certificates, {})
        self.assertEqual(len(self.service._journal.entries()), count)
        certificate = self.service.precertify(transition, 1, idempotency_key="pre")
        self.restart()
        self.assertEqual(certificate, self.service.precertify(transition, 1, idempotency_key="pre"))

    def test_sql_failure_publishes_nothing_and_requires_recovery(self):
        with sqlite3.connect(self.path) as connection:
            connection.execute("CREATE TRIGGER fail_append BEFORE INSERT ON events "
                               "BEGIN SELECT RAISE(ABORT, 'injected storage failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.driver.record("a", A)
        with self.assertRaises(RecoveryError):
            self.service.snapshot("ctx")
        self.service.close()
        with sqlite3.connect(self.path) as connection:
            connection.execute("DROP TRIGGER fail_append")
        self.restart()
        self.assertEqual(self.service.snapshot("ctx").knowledge_revision, 0)
        self.assertEqual(len(self.service._journal.entries()), 1)

    def test_ambiguous_commit_reconciles_original_key_after_restart(self):
        original = self.service._journal.append
        evidence = Evidence("a", "ctx", A, "sensor", 0, ("root",))

        def committed_then_failed(*args):
            original(*args)
            raise OSError("lost completion after durable commit")

        with patch.object(self.service._journal, "append", committed_then_failed):
            with self.assertRaises(OSError):
                self.service.record_evidence(evidence, idempotency_key="ambiguous")
        with self.assertRaises(RecoveryError):
            self.service.query_belief("ctx", A)
        self.restart()
        self.assertEqual(self.service.snapshot("ctx").knowledge_revision, 1)
        self.assertEqual(self.service.record_evidence(evidence, idempotency_key="ambiguous"), evidence)
        self.assertEqual(len(self.service._journal.entries()), 2)

    def test_corrupt_payload_is_detected(self):
        self.driver.record("a", A)
        self.service.close()
        with sqlite3.connect(self.path) as connection:
            connection.execute("UPDATE events SET payload='{}' WHERE sequence=2")
        with self.assertRaises(RecoveryError):
            AdmissionService(database=self.path)

    def test_missing_middle_event_is_detected(self):
        self.driver.record("a", A)
        self.driver.record("b", B)
        self.service.close()
        with sqlite3.connect(self.path) as connection:
            connection.execute("DELETE FROM events WHERE sequence=2")
        with self.assertRaises(RecoveryError):
            AdmissionService(database=self.path)

    def test_valid_hash_chain_does_not_override_failed_semantic_replay(self):
        self.driver.record("a", A)
        self.service.close()
        with sqlite3.connect(self.path) as connection:
            row = connection.execute("SELECT * FROM events WHERE sequence=2").fetchone()
            changed = replace(JournalEntry(*row), result_digest="0" * 64)
            connection.execute("UPDATE events SET result_digest=?, entry_digest=? WHERE sequence=2",
                               (changed.result_digest, changed.computed_digest()))
        with self.assertRaises(RecoveryError):
            AdmissionService(database=self.path)

    def test_saved_acceptance_from_a_broken_checker_is_not_trusted_on_restart(self):
        self.driver.adopt("a", A)

        def broken(*args, **kwargs):
            result = check_consistency(*args, **kwargs)
            return replace(result, status=Status.PASS, witness=()) if result.status is Status.FAIL else result

        with patch("reachability.service.check_consistency", broken):
            self.assertEqual(self.driver.adopt("opposite", A.negate()).status, Status.PASS)
        self.service.close()
        with self.assertRaises(RecoveryError):
            AdmissionService(database=self.path)

    def test_process_crash_before_and_after_transaction_commit(self):
        self.service.close()
        script = '''
import os, sys
from reachability.model import Evidence, Literal, Statement
from reachability.service import AdmissionService
service = AdmissionService(database=sys.argv[1])
original = service._journal.append
def crash(*args):
    if sys.argv[2] == "after":
        original(*args)
    os._exit(73)
service._journal.append = crash
service.record_evidence(Evidence("crash", "ctx", Literal(Statement("A")), "sensor", 0, ("root",)),
                        idempotency_key="crash-command")
'''
        for mode, expected_revision in (("before", 0), ("after", 1)):
            with self.subTest(mode=mode):
                result = subprocess.run([sys.executable, "-c", script, str(self.path), mode],
                                        capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 73, result.stderr)
                self.restart()
                self.assertEqual(self.service.snapshot("ctx").knowledge_revision, expected_revision)
                self.service.close()


class CodecTests(unittest.TestCase):
    def test_explicit_records_round_trip_without_executing_input(self):
        evidence = Evidence("a", "ctx", A, "sensor", 0, ("root",), 5)
        self.assertEqual(loads(dumps({"evidence": evidence, "status": Status.STALE})),
                         {"evidence": evidence, "status": Status.STALE})
        for data in ('{"$record":"subprocess.run","fields":{}}',
                     '{"$record":"Evidence","fields":{}}', '{"$status":"APPROVED"}'):
            with self.subTest(data=data), self.assertRaises(ValueError):
                loads(data)
