from dataclasses import replace
import unittest

from reachability.model import Clause, Evidence, Rule, Status
from reachability.service import AdmissionDenied, AdmissionService
from tests.support import Driver, lit

A, B, C, D = (lit(n) for n in "ABCD")


class RevisionTests(unittest.TestCase):
    def setUp(self):
        self.service = AdmissionService((Rule("ab", "1", (A,), B),
                                         Rule("bc", "1", (B,), C)))
        self.driver = Driver(self.service)
        self.driver.context()

    def derive(self, rule, premise):
        transition = self.driver.transition(rule, (premise.belief_revision_id,))
        return self.driver.finish(self.driver.prepare(transition)).belief

    def policy(self, revision, clauses):
        return self.service.replace_policy(
            "ctx", revision, clauses, self.service.snapshot("ctx").knowledge_revision,
            idempotency_key=self.driver.key())

    def test_rule_replacement_invalidates_descendants_and_keeps_alternate_proof(self):
        a = self.driver.adopt("a", A).belief
        b = self.derive("ab", a)
        c = self.derive("bc", b)
        independent = self.driver.adopt("c-direct", C).belief
        transition = self.driver.transition("ab", (a.belief_revision_id,))
        prepared = self.driver.prepare(transition)
        self.service.replace_rule(Rule("ab", "2", (A,), D), "1", idempotency_key="rule")
        self.assertEqual(self.driver.finish(prepared).status, Status.STALE)
        self.assertEqual(self.service.query_belief("ctx", A).current, (a,))
        self.assertEqual(self.service.query_belief("ctx", B).status, Status.STALE)
        self.assertEqual(self.service.query_belief("ctx", C).current, (independent,))
        self.assertIn(c, self.service.query_belief("ctx", C).historical)
        old = self.service.precertify(transition, self.service.snapshot("ctx").knowledge_revision,
                                      idempotency_key="old-rule")
        self.assertEqual(old.status, Status.STALE)
        self.assertEqual(self.derive("ab", a).conclusion, D)

    def test_rule_revisions_are_immutable_and_updates_compare_revision(self):
        before = self.service.snapshot("ctx")
        with self.assertRaises(ValueError):
            self.service.replace_rule(Rule("ab", "1", (A,), C), "1", idempotency_key="bad")
        with self.assertRaises(AdmissionDenied):
            self.service.replace_rule(Rule("ab", "2", (A,), C), "missing", idempotency_key="old")
        self.assertEqual(before, self.service.snapshot("ctx"))
        self.service.replace_rule(Rule("ab", "2", (A,), C), "1", idempotency_key="good")
        with self.assertRaises(ValueError):
            self.service.replace_rule(Rule("ab", "1", (A,), B), "2", idempotency_key="reuse")

    def test_inserted_blocker_invalidates_support_and_pending_certificate(self):
        a = self.driver.adopt("a", A).belief
        b = self.derive("ab", a)
        independent = self.driver.adopt("d", D).belief
        transition = self.driver.transition("bc", (b.belief_revision_id,))
        prepared = self.driver.prepare(transition)
        self.policy("p2", (Clause((A.negate(),)),))
        self.assertEqual(self.driver.finish(prepared).status, Status.STALE)
        self.assertEqual(self.service.query_belief("ctx", A).status, Status.STALE)
        self.assertEqual(self.service.query_belief("ctx", B).status, Status.STALE)
        self.assertEqual(self.service.query_belief("ctx", D).current, (independent,))
        self.assertEqual(len(self.service.query_belief("ctx", A).historical), 1)

    def test_joint_conflict_does_not_choose_an_arbitrary_survivor(self):
        self.driver.adopt("a", A)
        self.driver.adopt("b", B)
        self.policy("p2", (Clause((A.negate(), B.negate())),))
        self.assertEqual(self.service.snapshot("ctx").usable, ())
        # Re-admission under the new policy requires fresh certificates and an
        # immutable new result revision, even though the report is unchanged.
        transition = self.service.propose_evidence("ctx", "a", idempotency_key="again")
        result = self.driver.finish(self.driver.prepare(transition))
        self.assertEqual(result.status, Status.PASS)
        view = self.service.query_belief("ctx", A)
        self.assertEqual(len(view.historical), 2)
        self.assertEqual(view.current, (result.belief,))
        self.assertNotEqual(view.historical[0].belief_revision_id, result.belief.belief_revision_id)
        rejected = self.service.propose_evidence("ctx", "b", idempotency_key="b-again")
        self.assertEqual(self.driver.finish(self.driver.prepare(rejected)).status, Status.FAIL)

    def test_relaxed_policy_does_not_automatically_restore_old_beliefs(self):
        self.driver.adopt("a", A)
        self.policy("p2", (Clause((A.negate(),)),))
        self.policy("p3", ())
        self.assertEqual(self.service.query_belief("ctx", A).status, Status.STALE)
        transition = self.service.propose_evidence("ctx", "a", idempotency_key="again")
        self.assertEqual(self.driver.finish(self.driver.prepare(transition)).status, Status.PASS)

    def test_invalid_policy_update_leaves_context_unchanged(self):
        self.driver.adopt("a", A)
        before = self.service.snapshot("ctx")
        with self.assertRaises(AdmissionDenied):
            self.policy("p2", (Clause(()),))
        with self.assertRaises(ValueError):
            self.policy("finite-hard-policy/v1", (Clause((B,)),))
        with self.assertRaises(AdmissionDenied):
            self.service.replace_policy("ctx", "p2", (), 0, idempotency_key="old")
        self.assertEqual(self.service.snapshot("ctx"), before)

    def test_compatible_policy_revalidates_without_creating_new_support(self):
        a = self.driver.adopt("a", A).belief
        self.policy("p2", (Clause((A, B)),))
        self.assertEqual(self.service.query_belief("ctx", A).current, (a,))
        self.assertEqual(len(self.service.query_belief("ctx", A).historical), 1)

    def test_expiry_is_exclusive_and_propagates_through_rules(self):
        evidence = Evidence("expires", "ctx", A, "sensor", 0, ("origin",), valid_until=5)
        self.service.record_evidence(evidence, idempotency_key="record")
        transition = self.service.propose_evidence("ctx", "expires", idempotency_key="adopt")
        a = self.driver.finish(self.driver.prepare(transition)).belief
        b = self.derive("ab", a)
        independent = self.driver.adopt("b-direct", B).belief
        self.service.advance_clock("ctx", 4, idempotency_key="t4")
        ready = self.driver.transition("bc", (b.belief_revision_id,))
        prepared = self.driver.prepare(ready)
        self.assertEqual(prepared[1].logical_time, 4)
        self.assertEqual(prepared[1].valid_until, 5)
        self.assertEqual(self.service.query_belief("ctx", A).status, Status.PASS)
        self.service.advance_clock("ctx", 5, idempotency_key="t5")
        self.assertEqual(self.driver.finish(prepared).status, Status.STALE)
        self.assertEqual(self.service.query_belief("ctx", A).status, Status.STALE)
        self.assertEqual(self.service.query_belief("ctx", B).current, (independent,))
        self.assertEqual(len(self.service.query_belief("ctx", B).historical), 2)
        pre = self.service.precertify(transition, self.service.snapshot("ctx").knowledge_revision,
                                     idempotency_key="expired")
        self.assertEqual(pre.status, Status.STALE)

    def test_future_observation_is_stored_but_not_usable(self):
        self.service.record_evidence(Evidence("future", "ctx", A, "sensor", 10, ("root",)),
                                     idempotency_key="record")
        transition = self.service.propose_evidence("ctx", "future", idempotency_key="adopt")
        pre = self.service.precertify(transition, self.service.snapshot("ctx").knowledge_revision,
                                     idempotency_key="early")
        self.assertEqual(pre.status, Status.UNKNOWN)
        self.service.advance_clock("ctx", 10, idempotency_key="arrived")
        self.assertEqual(self.driver.finish(self.driver.prepare(transition)).status, Status.PASS)

    def test_clock_is_scoped_monotone_and_idempotent(self):
        self.driver.context("other")
        other = self.service.snapshot("other")
        snapshot = self.service.advance_clock("ctx", 4, idempotency_key="advance")
        self.assertEqual(snapshot, self.service.advance_clock("ctx", 4, idempotency_key="again"))
        self.assertEqual(other, self.service.snapshot("other"))
        for time in (3, -1, True, 4.0):
            with self.subTest(time=time), self.assertRaises(ValueError):
                self.service.advance_clock("ctx", time, idempotency_key=self.driver.key())

    def test_validity_and_revision_fields_reject_inexact_numbers(self):
        for expiry in (0, -1, True, 1.0):
            with self.subTest(expiry=expiry), self.assertRaises(ValueError):
                Evidence("a", "ctx", A, "sensor", 0, ("root",), valid_until=expiry)
        transition = self.driver.transition("ab", ("unavailable",))
        for revision in (True, 0.0, -1):
            with self.subTest(revision=revision), self.assertRaises(ValueError):
                self.service.precertify(transition, revision, idempotency_key=self.driver.key())
