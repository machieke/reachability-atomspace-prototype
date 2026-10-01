from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Event
import unittest
from unittest.mock import patch

from reachability.decision_model import DecisionContract, DecisionCriterion
from reachability.codec import dumps
from reachability.dispatch import Dispatcher
from reachability.dispatch_model import DispatchPolicy
from reachability.journal import RecoveryError
from reachability.model import Check, Status
from reachability.pln_adapter import TruthValue, implication
from reachability.probability_model import ProbabilityPolicy
from reachability.service import AdmissionDenied, AdmissionService
from reachability.simulated_executor import SimulatedExecutor
from tests.execution_support import ExecutionFixture
from tests.probability_support import ProbabilityDriver

FORECAST = implication("tested:artifact-v2", "healthy:artifact-v2")


class DecisionDispatchTests(ExecutionFixture, unittest.TestCase):
    def make_service(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "admission.db"
        return AdmissionService(database=self.path)

    def setUp(self):
        super().setUp()
        self.numeric = ProbabilityDriver(self.service)
        self.service.configure_probability_policy("ctx", ProbabilityPolicy("1", ("sensor",)),
                                                  idempotency_key=self.driver.key())
        self.decision = DecisionContract("risk", "1", "build", "1", "artifact-v2", (
            DecisionCriterion("forecast", FORECAST, .6, 1, .3),))
        self.service.register_decision_contract(self.decision, idempotency_key=self.driver.key())
        self.numeric.adopt("forecast", FORECAST, TruthValue(.75, .8), context="ctx")
        self.executor = SimulatedExecutor(self.path.with_name("executor.db"))
        self.addCleanup(self.executor.close)
        self.service.register_dispatch_policy(DispatchPolicy("dispatch", "1", "build", "1", self.executor.profile),
                                              idempotency_key=self.driver.key())

    @property
    def dispatcher(self):
        return Dispatcher(self.service, self.executor)

    def dispatch(self):
        return self.dispatcher.dispatch("attempt", "dispatch", "1", "worker")

    def prepare(self):
        return self.service.prepare_dispatch("attempt", "dispatch", "1", "worker", idempotency_key=self.driver.key())

    def restart(self):
        self.service.close()
        self.service = AdmissionService(database=self.path)
        self.driver.service = self.numeric.service = self.service

    def revoke(self):
        self.service.revoke_evidence("forecast", idempotency_key=self.driver.key())

    def test_current_decision_and_exact_support_survive_restart_and_dispatch(self):
        intent = self.reserve()
        before = self.service.execution_decision(intent.certificate_id)
        self.restart()
        self.assertEqual(self.service.execution_decision(intent.certificate_id), before)
        self.assertEqual(self.dispatch().state, "accepted")
        self.assertEqual(self.executor.total_effects, 1)

    def test_revocation_blocks_first_dispatch_without_remote_effect(self):
        self.reserve()
        self.revoke()
        self.restart()
        with self.assertRaises(AdmissionDenied):
            self.dispatch()
        self.assertEqual(self.executor.total_effects, 0)
        with self.assertRaises(KeyError):
            self.service.inspect_dispatch("attempt")

    def test_pending_marker_cannot_authorize_withdrawn_estimates(self):
        self.reserve()
        self.prepare()
        self.revoke()
        self.restart()
        with self.assertRaises(AdmissionDenied):
            self.dispatch()
        self.assertEqual(self.executor.total_effects, 0)
        self.assertEqual(self.service.inspect_resource("slot").reconciliation_attempts, ("attempt",))

    def test_final_send_rechecks_after_a_prepared_marker(self):
        self.reserve()
        original = self.service.prepare_dispatch
        def prepare_and_revoke(*args, **kwargs):
            result = original(*args, **kwargs)
            self.revoke()
            return result
        with patch.object(self.service, "prepare_dispatch", prepare_and_revoke), self.assertRaises(AdmissionDenied):
            self.dispatch()
        self.assertEqual(self.executor.total_effects, 0)

    def test_equal_valued_replacement_cannot_silently_rebind_an_intent(self):
        self.reserve()
        self.revoke()
        self.numeric.adopt("replacement", FORECAST, TruthValue(.75, .8), context="ctx")
        self.assertEqual(self.service.inspect_probability_decision("attempt", "build", "1").status, Status.PASS)
        with self.assertRaises(AdmissionDenied) as error:
            self.dispatch()
        self.assertEqual(error.exception.status, Status.STALE)
        self.assertEqual(self.executor.total_effects, 0)

    def test_query_and_release_remain_available_after_support_revocation(self):
        intent = self.reserve()
        self.dispatch()
        self.revoke()
        self.restart()
        self.assertEqual(self.dispatch().state, "accepted")
        self.assertEqual(self.service.execution_decision(intent.certificate_id).status, Status.PASS)
        self.assertEqual(self.service.inspect_probability_decision("attempt", "build", "1").status, Status.STALE)
        self.assertTrue(self.dispatcher.release("attempt", "worker").resources_released)
        self.assertEqual(self.executor.total_effects, 1)

    def test_lost_reply_can_be_reconciled_after_prediction_retirement(self):
        self.reserve()
        original = self.executor.submit
        def lost_reply(request):
            original(request)
            raise OSError("reply lost")
        with patch.object(self.executor, "submit", lost_reply):
            self.assertEqual(self.dispatch().state, "uncertain")
        self.revoke()
        self.restart()
        self.assertEqual(self.dispatch().state, "accepted")
        self.assertEqual(self.executor.total_effects, 1)

    def test_revocation_cannot_interleave_between_final_gate_and_executor_call(self):
        self.reserve()
        entered, revoking = Event(), Event()
        original = self.executor.submit
        def submit(request):
            entered.set()
            self.assertTrue(revoking.wait(timeout=5))
            self.assertEqual(self.service.inspect_probability_decision("attempt", "build", "1").status, Status.PASS)
            return original(request)
        def revoke():
            self.assertTrue(entered.wait(timeout=5))
            revoking.set()
            self.revoke()
        with patch.object(self.executor, "submit", submit), ThreadPoolExecutor(max_workers=2) as pool:
            sent = pool.submit(self.dispatch)
            withdrawn = pool.submit(revoke)
            self.assertEqual(sent.result(timeout=10).state, "accepted")
            withdrawn.result(timeout=10)
        self.assertEqual(self.executor.total_effects, 1)

    def test_certificate_append_failure_rolls_back_the_numerical_witness_too(self):
        with patch.object(self.service._journal, "append", side_effect=OSError("failed append")):
            with self.assertRaises(OSError):
                self.permit()
        self.assertEqual(self.service._execution.permits, {})
        self.assertEqual(self.service._decisions.certificates, {})
        self.restart()
        self.assertEqual(self.permit().status, Status.PASS)

    def test_ambiguous_reservation_recovers_one_intent_with_the_exact_decision(self):
        permit = self.permit()
        original = self.service._journal.append
        def committed_then_failed(*args):
            original(*args)
            raise OSError("lost reply")
        with patch.object(self.service._journal, "append", committed_then_failed), self.assertRaises(OSError):
            self.reserve(permit, "reserve-once")
        with patch("reachability.pln_adapter.PeTTaFormulaRuntime.evaluate", side_effect=AssertionError("native replay")):
            self.restart()
            intent = self.reserve(permit, "reserve-once")
        self.assertEqual(intent.certificate_id, permit.certificate_id)
        self.assertEqual(len(self.service.inspect_resource("slot").reservations), 1)
        self.assertEqual(self.service.execution_decision(permit.certificate_id).status, Status.PASS)

    def test_recovery_rejects_success_from_a_broken_decision_checker(self):
        self.numeric.adopt("bad", FORECAST, TruthValue(.1, .8), context="ctx")
        original = self.service._evaluate_decision
        def broken(*args):
            return replace(original(*args), checks=(Check("broken", Status.PASS, "wrong acceptance"),))
        with patch.object(self.service, "_evaluate_decision", broken):
            self.assertEqual(self.permit().status, Status.PASS)
        self.service.close()
        with self.assertRaises(RecoveryError):
            AdmissionService(database=self.path)

    def test_registration_failure_rolls_back_binding_and_resource_epoch(self):
        execution = replace(self.contract, revision="2")
        self.service.register_execution_contract(execution, idempotency_key=self.driver.key())
        decision = replace(self.decision, revision="2", execution_contract_revision="2")
        before = self.service.resource_snapshot()
        with patch.object(self.service._journal, "append", side_effect=OSError("failed append")), self.assertRaises(OSError):
            self.service.register_decision_contract(decision, idempotency_key="register-once")
        self.assertNotIn(("build", "2"), self.service._decisions.bindings)
        self.restart()
        self.assertEqual(self.service.resource_snapshot(), before)
        self.assertEqual(self.service.register_decision_contract(decision, idempotency_key="register-once"), decision)

    def test_process_crashes_preserve_decision_and_atomic_reservation(self):
        permit = self.permit()
        witness = self.service.execution_decision(permit.certificate_id)
        request = self.path.with_suffix(".json")
        request.write_text(dumps(permit))
        self.service.close()
        script = '''
import os, sys
from pathlib import Path
from reachability.codec import loads
from reachability.service import AdmissionService
s = AdmissionService(database=sys.argv[1])
append = s._journal.append
def crash(*args):
    if sys.argv[3] == "after": append(*args)
    os._exit(74)
s._journal.append = crash
s.reserve_and_record_intent(loads(Path(sys.argv[2]).read_text()), idempotency_key="crash-intent")
'''
        for mode, expected in (("before", 0), ("after", 1)):
            with self.subTest(mode=mode):
                result = subprocess.run([sys.executable, "-c", script, str(self.path), str(request), mode],
                                        capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 74, result.stderr)
                self.restart()
                self.assertEqual(self.service.execution_decision(permit.certificate_id), witness)
                self.assertEqual(len(self.service.inspect_resource("slot").reservations), expected)
                self.assertEqual(self.executor.total_effects, 0)
                self.service.close()
        self.restart()
        intent = self.reserve(permit, "crash-intent")
        self.assertEqual(intent.certificate_id, permit.certificate_id)
