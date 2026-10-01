from dataclasses import replace
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from reachability.completion import CompletionContract
from reachability.dispatch import Dispatcher
from reachability.dispatch_model import DispatchPolicy
from reachability.model import Status
from reachability.service import AdmissionDenied, AdmissionService
from reachability.simulated_executor import SimulatedExecutor
from tests.goal_support import GoalFixture
from tests.lifecycle_support import CREDENTIAL, TESTED, certify, fact, observe


class CompletionTests(GoalFixture, unittest.TestCase):
    def make_service(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.path = self.directory / "goals.db"
        return AdmissionService(database=self.path)

    def setUp(self):
        super().setUp()
        self.executor = SimulatedExecutor(self.directory / "executor.db")
        self.addCleanup(self.executor.close)
        self.service.register_dispatch_policy(DispatchPolicy("dispatch", "1", "build", "1", self.executor.profile),
                                               idempotency_key=self.driver.key())
        self.completion_contract = CompletionContract("completion", "1", "artifact", "1", "build", "service-goal", "1")
        self.service.register_completion_contract(self.completion_contract, idempotency_key=self.driver.key())

    def dispatch(self):
        return Dispatcher(self.service, self.executor).dispatch("attempt", "dispatch", "1", "worker")

    def certify_completion(self, revision="1"):
        return self.service.certify_goal_completion("completion", revision, "attempt", "goal",
            self.service.inspect_lifecycle("episode").episode.revision, self.service.snapshot("ctx").knowledge_revision,
            idempotency_key=self.driver.key())

    def complete_observations(self):
        self.tick(1)
        self.product()
        observe(self.driver, "completion_observed")
        observe(self.driver, "exact_product_observed")
        for time in (1, 2, 3):
            self.tick(time)
            self.sample(time)
        self.sample(3, slice_id="available")

    def restart(self):
        self.service.close()
        self.service = AdmissionService(database=self.path)
        self.driver.service = self.service

    def test_expired_submission_credential_does_not_block_observed_completion(self):
        self.dispatch()
        self.service.revoke_evidence("credential", idempotency_key=self.driver.key())
        self.complete_observations()
        self.assertEqual(certify(self.driver, attempt="attempt").status, Status.UNKNOWN)
        permit = self.certify_completion()
        self.assertEqual(permit.status, Status.PASS)
        self.assertEqual(permit.prerequisites.logical_time, 0)
        self.assertEqual(permit.outcome.logical_time, 3)
        episode = self.service.advance_goal_completion(permit, 0, idempotency_key="complete")
        self.assertEqual(episode.stage, "BUILT")
        self.assertEqual(self.service.query_belief("ctx", TESTED).status, Status.PASS)
        self.assertEqual(self.service.query_belief("ctx", CREDENTIAL).status, Status.STALE)
        self.restart()
        self.assertEqual(self.service.inspect_lifecycle("episode").episode, episode)
        self.assertEqual(self.service.advance_goal_completion(permit, 0, idempotency_key="complete"), episode)

    def test_ack_and_elapsed_time_cannot_authorize_completion(self):
        self.dispatch()
        self.tick(3)
        self.assertEqual(self.certify_completion().status, Status.UNKNOWN)
        self.assertEqual(self.projection().outstanding_loss, 10)

    def test_preexisting_and_same_tick_samples_do_not_prove_post_submission_outcome(self):
        self.product()
        for time in (0, 1, 2):
            self.tick(time)
            self.sample(time)
        self.sample(2, slice_id="available")
        self.dispatch()
        observe(self.driver, "completion_observed")
        observe(self.driver, "exact_product_observed")
        self.assertEqual(self.projection().outstanding_loss, 0)
        self.assertEqual(self.certify_completion().status, Status.UNKNOWN)

    def test_goal_satisfaction_without_exact_attempt_observations_cannot_advance_lifecycle(self):
        self.dispatch()
        self.product()
        for time in (1, 2, 3):
            self.tick(time)
            self.sample(time)
        self.sample(3, slice_id="available")
        self.assertEqual(self.projection().outstanding_loss, 0)
        self.assertEqual(self.certify_completion().status, Status.UNKNOWN)

    def test_current_completion_requirements_are_separate_from_archived_submission(self):
        self.dispatch()
        self.complete_observations()
        self.service.register_completion_contract(replace(self.completion_contract, revision="2", requirements=fact(CREDENTIAL)),
                                                   idempotency_key=self.driver.key())
        self.service.revoke_evidence("credential", idempotency_key=self.driver.key())
        self.assertEqual(self.certify_completion().status, Status.PASS)
        self.assertEqual(self.certify_completion("2").status, Status.UNKNOWN)

    def test_stale_or_forged_completion_certificate_is_rejected(self):
        self.dispatch()
        self.complete_observations()
        permit = self.certify_completion()
        with self.assertRaises(AdmissionDenied) as failure:
            self.service.advance_goal_completion(replace(permit, goal_id="forged"), 0, idempotency_key=self.driver.key())
        self.assertEqual(failure.exception.status, Status.FAIL)
        self.tick(4)
        with self.assertRaises(AdmissionDenied) as failure:
            self.service.advance_goal_completion(permit, 0, idempotency_key=self.driver.key())
        self.assertEqual(failure.exception.status, Status.STALE)

    def test_failed_completion_commit_recovers_original_stage(self):
        self.dispatch()
        self.complete_observations()
        permit = self.certify_completion()
        with patch.object(self.service._journal, "append", side_effect=OSError("failed write")):
            with self.assertRaises(OSError):
                self.service.advance_goal_completion(permit, 0, idempotency_key="complete")
        self.restart()
        self.assertEqual(self.service.inspect_lifecycle("episode").episode.stage, "DRAFT")
        self.assertEqual(self.service.advance_goal_completion(permit, 0, idempotency_key="complete").stage, "BUILT")

    def test_later_health_failure_reopens_goal_without_erasing_lifecycle_history(self):
        self.dispatch()
        self.complete_observations()
        self.reconcile()
        self.service.advance_goal_completion(self.certify_completion(), 0, idempotency_key=self.driver.key())
        self.tick(4)
        self.sample(4, healthy=False)
        self.assertEqual(self.projection().outstanding_loss, 10)
        self.assertEqual({event.kind for event in self.reconcile().events}, {"reopened"})
        self.assertEqual(self.service.inspect_lifecycle("episode").episode.stage, "BUILT")

    def test_real_process_crash_before_and_after_temporal_completion_commit(self):
        self.dispatch()
        self.complete_observations()
        self.service.close()
        script = '''
import os, sys
from reachability.service import AdmissionService
service = AdmissionService(database=sys.argv[1])
permit = service.certify_goal_completion("completion", "1", "attempt", "goal", 0,
    service.snapshot("ctx").knowledge_revision, idempotency_key="crash-cert")
original = service._journal.append
def crash(*args):
    if sys.argv[2] == "after":
        original(*args)
    os._exit(73)
service._journal.append = crash
service.advance_goal_completion(permit, 0, idempotency_key="crash-complete")
'''
        for side, stage in (("before", "DRAFT"), ("after", "BUILT")):
            with self.subTest(side=side):
                path = self.directory / f"{side}.db"
                shutil.copy2(self.path, path)
                outcome = subprocess.run([sys.executable, "-c", script, str(path), side],
                                         capture_output=True, text=True, timeout=15)
                self.assertEqual(outcome.returncode, 73, outcome.stderr)
                with AdmissionService(database=path) as recovered:
                    self.assertEqual(recovered.inspect_lifecycle("episode").episode.stage, stage)
