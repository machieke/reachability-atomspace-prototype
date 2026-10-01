from dataclasses import replace
import unittest
from unittest.mock import patch

from reachability.journal import RecoveryError, StoreInUse
from reachability.service import IdempotencyConflict
from reachability.simulated_executor import NonIdempotentSimulatedExecutor, SimulatedExecutor
from tests.dispatch_support import DispatchFixture


class SimulatedExecutorTests(DispatchFixture, unittest.TestCase):
    def test_idempotency_and_release_tombstone_survive_executor_restart(self):
        request = self.prepare().request
        accepted = self.executor.submit(request)
        self.assertEqual(self.executor.submit(request), accepted)
        released = self.executor.release(request)
        self.restart()
        self.assertEqual(self.executor.submit(request), released)
        self.assertEqual(self.executor.release(request), released)
        self.assertEqual(self.executor.total_effects, 1)

    def test_non_idempotent_class_exposes_duplicate_effects_and_unknown_queries(self):
        request = self.prepare().request
        with NonIdempotentSimulatedExecutor(self.directory / "non-idempotent.db") as executor:
            self.assertEqual(executor.submit(request).effect_count, 1)
            self.assertEqual(executor.submit(request).effect_count, 2)
            self.assertEqual(executor.query(request).state, "unknown")
            with self.assertRaises(ValueError):
                executor.release(request)
        with NonIdempotentSimulatedExecutor(self.directory / "non-idempotent.db") as executor:
            self.assertEqual(executor.total_effects, 2)

    def test_request_identity_cannot_be_rebound_to_another_product_or_owner(self):
        request = self.prepare().request
        self.executor.submit(request)
        for changed in (replace(request.intent, product_id="other-product"),
                        replace(request.intent, owner_id="other-owner")):
            for method in (self.executor.submit, self.executor.query, self.executor.release):
                with self.assertRaises(IdempotencyConflict):
                    method(replace(request, intent=changed))

    def test_fence_before_any_submission_prevents_late_effects(self):
        request = self.prepare().request
        released = self.executor.release(request)
        self.assertEqual(released.effect_count, 0)
        self.restart()
        self.assertEqual(self.executor.submit(request), released)
        self.assertEqual(self.executor.total_effects, 0)

    def test_profile_and_single_authority_are_persistent(self):
        profile = self.executor.profile
        with self.assertRaises(StoreInUse):
            SimulatedExecutor(self.executor_path)
        self.executor.close()
        with self.assertRaises(RecoveryError):
            SimulatedExecutor(self.executor_path, supports_idempotency=False)
        self.executor = SimulatedExecutor(self.executor_path)
        self.assertEqual(self.executor.profile, profile)

    def test_ambiguous_executor_storage_failure_requires_reopening_and_query(self):
        request = self.prepare().request
        original = self.executor._journal.append

        def lose_reply(*args):
            original(*args)
            raise OSError("executor commit reply lost")

        with patch.object(self.executor._journal, "append", lose_reply), self.assertRaises(OSError):
            self.executor.submit(request)
        with self.assertRaises(RecoveryError):
            self.executor.query(request)
        self.restart()
        self.assertEqual(self.executor.query(request).effect_count, 1)
        self.assertEqual(self.dispatch().state, "accepted")
        self.assertEqual(self.executor.total_effects, 1)
