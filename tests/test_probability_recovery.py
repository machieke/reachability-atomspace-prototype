from dataclasses import replace
import json
import math
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from reachability.codec import dumps, loads
from reachability.journal import RecoveryError
from reachability.model import Status
from reachability.pln_adapter import TruthValue, implication, proposition
from reachability.probability_formula import PinnedFormulaRuntime
from reachability.service import AdmissionService
from tests.probability_support import ProbabilityDriver


class ProbabilityRecoveryTests(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "probability.sqlite"
        self.service = AdmissionService(database=self.path)
        self.addCleanup(lambda: self.service.close())
        self.driver = ProbabilityDriver(self.service)
        self.driver.context()

    def restart(self):
        self.service.close()
        self.service = AdmissionService(database=self.path)
        self.driver.service = self.service

    def test_pending_certificates_and_commits_survive_restart_without_native_io(self):
        _, _, transition = self.driver.deduction()
        prepared = self.driver.prepare(transition)
        with patch("reachability.pln_adapter.PeTTaFormulaRuntime.evaluate", side_effect=AssertionError("replayed external I/O")):
            self.restart()
            result = self.driver.finish(prepared, "commit-once")
            expected = self.service.export_probability("world")
            self.restart()
            self.assertEqual(self.service.export_probability("world"), expected)
            self.assertEqual(self.driver.finish(prepared, "commit-once"), result)
        self.assertEqual(self.service.query_belief("world", implication("P", "R")).status, Status.UNKNOWN)

    def test_failed_commit_append_rolls_back_all_numeric_state(self):
        transition = self.driver.report("e", proposition("P"))
        prepared = self.driver.prepare(transition)
        before = self.service.export_probability("world")
        with patch.object(self.service._journal, "append", side_effect=OSError("failed append")):
            with self.assertRaises(OSError):
                self.driver.finish(prepared, "retry")
        self.assertEqual(self.service._probability.beliefs, {})
        with self.assertRaises(RecoveryError):
            self.service.export_probability("world")
        self.restart()
        self.assertEqual(self.service.export_probability("world"), before)
        self.assertEqual(self.driver.finish(prepared, "retry").status, Status.PASS)

    def test_ambiguous_commit_returns_original_response_on_retry(self):
        transition = self.driver.report("e", proposition("P"))
        prepared = self.driver.prepare(transition)
        append = self.service._journal.append
        def committed_then_failed(*args):
            append(*args)
            raise OSError("lost commit reply")
        with patch.object(self.service._journal, "append", committed_then_failed), self.assertRaises(OSError):
            self.driver.finish(prepared, "retry")
        self.restart()
        before = self.service.snapshot("world").knowledge_revision
        result = self.driver.finish(prepared, "retry")
        self.assertEqual(result.status, Status.PASS)
        self.assertEqual(result.knowledge_revision, before)
        self.assertEqual(len(self.service.query_probability("world", proposition("P")).current), 1)

    def test_partial_certificate_write_rolls_back(self):
        transition = self.driver.report("e", proposition("P"))
        original = self.service._issue_probability
        def interrupted(*args, **kwargs):
            original(*args, **kwargs)
            raise RuntimeError("after certificate allocation")
        with patch.object(self.service, "_issue_probability", interrupted), self.assertRaises(RuntimeError):
            self.service.precertify_probability(transition, self.service.snapshot("world").knowledge_revision,
                                                idempotency_key="pre")
        self.assertEqual(self.service._probability.certificates, {})
        self.restart()
        self.assertEqual(self.driver.finish(self.driver.prepare(transition)).status, Status.PASS)

    def test_stored_success_from_broken_formula_checker_is_rejected(self):
        _, _, transition = self.driver.deduction()
        with patch.object(PinnedFormulaRuntime, "evaluate", return_value=TruthValue(.99, .99)):
            result = self.driver.finish(self.driver.prepare(transition))
            self.assertEqual(result.status, Status.PASS)
        self.service.close()
        with self.assertRaises(RecoveryError):
            AdmissionService(database=self.path)

    def test_payload_tampering_is_rejected(self):
        transition = self.driver.report("e", proposition("P"))
        self.driver.finish(self.driver.prepare(transition))
        self.service.close()
        with sqlite3.connect(self.path) as connection:
            connection.execute("UPDATE events SET payload='{}' WHERE command='commit_probability'")
        with self.assertRaises(RecoveryError):
            AdmissionService(database=self.path)

    def test_process_crashes_on_both_sides_of_numeric_commit(self):
        transition = self.driver.report("e", proposition("P"))
        prepared = self.driver.prepare(transition)
        request = Path(self.directory.name) / "request.json"
        request.write_text(dumps(prepared))
        self.service.close()
        script = '''
import os, sys
from pathlib import Path
from reachability.codec import loads
from reachability.service import AdmissionService
s=AdmissionService(database=sys.argv[1])
original=s._journal.append
def crash(*args):
    if sys.argv[3] == "after": original(*args)
    os._exit(74)
s._journal.append=crash
s.commit_probability(*loads(Path(sys.argv[2]).read_text()),idempotency_key="crash-commit")
'''
        for mode, expected in (("before", 0), ("after", 1)):
            with self.subTest(mode=mode):
                result = subprocess.run([sys.executable, "-c", script, str(self.path), str(request), mode],
                                        capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 74, result.stderr)
                self.restart()
                self.assertEqual(len(self.service.query_probability("world", proposition("P")).current), expected)
                self.service.close()
        self.restart()
        self.assertEqual(self.driver.finish(prepared, "crash-commit").status, Status.PASS)


class Binary64CodecTests(TestCase):
    def test_finite_numbers_roundtrip_bit_exactly(self):
        for value in (0.0, -0.0, .1, .9999999999999999, math.nextafter(0, 1), sys.float_info.max):
            with self.subTest(value=value):
                self.assertEqual(loads(dumps(value)).hex(), value.hex())
                self.assertIn("$float64", dumps(value))
        truth = TruthValue(.4, .8)
        self.assertEqual(loads(dumps(truth)), truth)

    def test_nonfinite_untyped_or_noncanonical_numbers_are_rejected(self):
        for data in ('0.5', 'NaN', '{"$float64":"nan"}', '{"$float64":"inf"}',
                     '{"$float64":"0.5"}', '{"$float64":0.5}', '{"$float64":"0x1p+0"}',
                     '{"$float64":"0x1p+99999"}'):
            with self.subTest(data=data), self.assertRaises(ValueError):
                loads(data)
        for value in (float("nan"), float("inf"), -float("inf")):
            with self.assertRaises(ValueError):
                dumps(value)
