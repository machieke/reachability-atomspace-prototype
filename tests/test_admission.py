from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, replace
from threading import Barrier
import unittest

from reachability.model import Check, Clause, Rule, Statement, Status, conjunction
from reachability.service import AdmissionDenied, AdmissionService, IdempotencyConflict
from tests.support import Driver, lit

A, B, C = lit("A"), lit("B"), lit("C")


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.service = AdmissionService((Rule("join", "1", (A, B), C),
                                         Rule("next", "1", (A,), B),
                                         Rule("back", "1", (B,), A)))
        self.driver = Driver(self.service)
        self.driver.context()

    def test_structural_identity_and_argument_order(self):
        a = Statement("relation", ("x", "y"))
        self.assertEqual(a.statement_id, Statement("relation", ("x", "y")).statement_id)
        self.assertNotEqual(a.statement_id, Statement("relation", ("y", "x")).statement_id)
        self.assertNotEqual(a.statement_id, Statement("different", ("x", "y")).statement_id)
        with self.assertRaises(FrozenInstanceError):
            a.predicate = "changed"

    def test_reports_are_not_automatically_accepted(self):
        self.driver.record("e1", A)
        self.driver.record("e2", A.negate())
        self.assertEqual(self.service.query_belief("ctx", A).status, Status.UNKNOWN)
        self.assertEqual(self.service.snapshot("ctx").usable, ())

    def test_complete_pipeline_has_no_early_acceptance(self):
        self.driver.record("e1", A)
        t = self.service.propose_evidence("ctx", "e1", idempotency_key="propose")
        prepared = self.driver.prepare(t)
        self.assertEqual(prepared[1].status, Status.PASS)
        self.assertEqual(prepared[2].status, Status.PASS)
        self.assertEqual(self.service.query_belief("ctx", A).status, Status.UNKNOWN)
        result = self.driver.finish(prepared)
        self.assertEqual(result.status, Status.PASS)
        view = self.service.query_belief("ctx", A)
        self.assertEqual(view.status, Status.PASS)
        self.assertEqual(view.checked_at_revision, result.knowledge_revision)
        self.assertEqual(view.current[0].interpretation, "explicit-hard-claim")

    def test_registered_rule_preserves_all_evidence_and_lineage(self):
        a = self.driver.adopt("a", A, roots=("common-origin",)).belief
        b = self.driver.adopt("b", B, roots=("common-origin",)).belief
        t = self.driver.transition("join", (a.belief_revision_id, b.belief_revision_id))
        result = self.driver.finish(self.driver.prepare(t))
        self.assertEqual(result.status, Status.PASS)
        self.assertEqual(result.belief.proposal.evidence_ids, ("a", "b"))
        self.assertEqual(result.belief.proposal.lineage_roots, ("common-origin",))

    def test_missing_and_premise_is_unknown_and_cannot_infer(self):
        a = self.driver.adopt("a", A).belief
        t = self.driver.transition("join", (a.belief_revision_id,))
        pre = self.service.precertify(t, self.service.snapshot("ctx").knowledge_revision,
                                     idempotency_key="pre")
        self.assertEqual(pre.status, Status.UNKNOWN)
        with self.assertRaises(AdmissionDenied):
            self.service.infer(t, pre)

    def test_unknown_premise_revision_cannot_infer(self):
        t = self.driver.transition("next", ("absent-revision",))
        pre = self.service.precertify(t, 0, idempotency_key="pre")
        self.assertEqual(pre.status, Status.UNKNOWN)
        with self.assertRaises(AdmissionDenied):
            self.service.infer(t, pre)

    def test_ordered_premise_binding_is_checked(self):
        a = self.driver.adopt("a", A).belief
        b = self.driver.adopt("b", B).belief
        t = self.driver.transition("join", (b.belief_revision_id, a.belief_revision_id))
        pre = self.service.precertify(t, self.service.snapshot("ctx").knowledge_revision,
                                     idempotency_key="pre")
        self.assertEqual(pre.status, Status.FAIL)

    def test_joint_constraint_blocks_post_state(self):
        self.driver.context("limited", constraints=(Clause((A.negate(), B.negate())),))
        self.assertEqual(self.driver.adopt("a", A, "limited").status, Status.PASS)
        result = self.driver.adopt("b", B, "limited")
        self.assertEqual(result.status, Status.FAIL)
        self.assertEqual(self.service.query_belief("limited", B).status, Status.UNKNOWN)

    def test_direct_contradiction_blocks_commit(self):
        self.driver.adopt("a", A)
        self.assertEqual(self.driver.adopt("opposite", A.negate()).status, Status.FAIL)

    def test_context_mixing_rejected_even_with_shared_statement(self):
        self.driver.context("other")
        a = self.driver.adopt("a", A, "other").belief
        t = self.driver.transition("next", (a.belief_revision_id,))
        pre = self.service.precertify(t, 0, idempotency_key="pre")
        self.assertEqual(pre.status, Status.FAIL)
        with self.assertRaises(AdmissionDenied):
            self.service.infer(t, pre)

    def test_report_cannot_be_adopted_into_another_context(self):
        self.driver.context("other")
        self.driver.record("a", A, "other")
        t = self.service.propose_evidence("ctx", "a", idempotency_key="t")
        pre = self.service.precertify(t, 0, idempotency_key="pre")
        self.assertEqual(pre.status, Status.FAIL)

    def test_changed_revision_blocks_inference_and_commit(self):
        self.driver.record("a", A)
        t = self.service.propose_evidence("ctx", "a", idempotency_key="t")
        prepared = self.driver.prepare(t)
        self.driver.record("b", B)
        with self.assertRaises(AdmissionDenied) as caught:
            self.service.infer(t, prepared[1])
        self.assertEqual(caught.exception.status, Status.STALE)
        self.assertEqual(self.driver.finish(prepared).status, Status.STALE)
        # Supplying today's revision cannot refresh yesterday's certificate.
        prepared = (*prepared[:3], self.service.snapshot("ctx").knowledge_revision)
        self.assertEqual(self.driver.finish(prepared).status, Status.STALE)

    def test_forged_certificate_and_altered_checks_rejected(self):
        self.driver.record("a", A)
        t = self.service.propose_evidence("ctx", "a", idempotency_key="t")
        proposal, pre, post, revision = self.driver.prepare(t)
        for forged in (replace(pre, certificate_id="certificate:forged"),
                       replace(pre, checks=(Check("fake", Status.PASS, "looks valid"),))):
            with self.subTest(forged=forged.certificate_id):
                with self.assertRaises(AdmissionDenied):
                    self.service.infer(t, forged)
                outcome = self.driver.finish((proposal, forged, post, revision))
                self.assertEqual(outcome.status, Status.FAIL)

    def test_certificate_from_another_service_is_not_authority(self):
        other = AdmissionService()
        driver = Driver(other)
        driver.context()
        driver.record("a", A)
        foreign = other.propose_evidence("ctx", "a", idempotency_key="t")
        foreign_pre = driver.prepare(foreign)[1]
        self.driver.record("a", A)
        local = self.service.propose_evidence("ctx", "a", idempotency_key="t")
        with self.assertRaises(AdmissionDenied):
            self.service.infer(local, foreign_pre)

    def test_wrong_subject_or_stage_certificate_is_rejected(self):
        self.driver.record("a", A)
        self.driver.record("b", B)
        ta = self.service.propose_evidence("ctx", "a", idempotency_key="ta")
        tb = self.service.propose_evidence("ctx", "b", idempotency_key="tb")
        pa, prea, posta, revision = self.driver.prepare(ta)
        _, preb, _, _ = self.driver.prepare(tb)
        self.assertEqual(self.driver.finish((pa, preb, posta, revision)).status, Status.FAIL)
        self.assertEqual(self.driver.finish((pa, posta, prea, revision)).status, Status.FAIL)

    def test_altered_proposal_cannot_reuse_a_valid_post_certificate(self):
        self.driver.record("a", A)
        t = self.service.propose_evidence("ctx", "a", idempotency_key="t")
        proposal, pre, post, revision = self.driver.prepare(t)
        for forged in (replace(proposal, conclusion=B), replace(proposal, lineage_roots=("fake",)),
                       replace(proposal, context_id="other")):
            cert = self.service.postcertify(forged, pre, idempotency_key=self.driver.key())
            self.assertEqual(cert.status, Status.FAIL)
            self.assertEqual(self.driver.finish((forged, pre, post, revision)).status, Status.FAIL)

    def test_idempotency_replays_original_result_without_changing_state(self):
        evidence = self.driver.record("a", A)
        before = self.service.snapshot("ctx")
        self.service.record_evidence(evidence, idempotency_key="replay")
        self.assertEqual(self.service.snapshot("ctx"), before)
        with self.assertRaises(IdempotencyConflict):
            self.service.record_evidence(replace(evidence, source="changed"),
                                         idempotency_key="replay")
        with self.assertRaises(IdempotencyConflict):
            self.service.record_evidence(replace(evidence, source="changed"),
                                         idempotency_key="new-key")
        self.assertEqual(self.service.snapshot("ctx"), before)
        t = self.service.propose_evidence("ctx", "a", idempotency_key="t")
        prepared = self.driver.prepare(t)
        result = self.driver.finish(prepared, "commit")
        self.assertEqual(self.driver.finish(prepared, "commit"), result)
        self.assertEqual(len(self.service.query_belief("ctx", A).current), 1)
        # A fresh certificate and a new request key still do not add support.
        again = self.driver.finish(self.driver.prepare(t))
        self.assertEqual(again.knowledge_revision, result.knowledge_revision)
        self.assertEqual(again.belief, result.belief)

    def test_revocation_invalidates_descendants_but_preserves_history(self):
        a = self.driver.adopt("a", A).belief
        t = self.driver.transition("next", (a.belief_revision_id,))
        b = self.driver.finish(self.driver.prepare(t)).belief
        self.service.revoke_evidence("a", idempotency_key="revoke")
        view = self.service.query_belief("ctx", B)
        self.assertEqual(view.status, Status.STALE)
        self.assertEqual(view.current, ())
        self.assertEqual(view.historical, (b,))
        self.assertEqual(self.service.snapshot("ctx").usable, ())

    def test_alternative_proof_survives_revocation(self):
        self.driver.adopt("a1", A)
        second = self.driver.adopt("a2", A).belief
        self.service.revoke_evidence("a1", idempotency_key="revoke")
        view = self.service.query_belief("ctx", A)
        self.assertEqual(view.status, Status.PASS)
        self.assertEqual(view.current, (second,))
        self.assertEqual(len(view.historical), 2)

    def test_replaying_revoked_report_does_not_restore_support(self):
        self.driver.adopt("a", A)
        self.service.revoke_evidence("a", idempotency_key="revoke")
        self.driver.record("a", A)
        t = self.service.propose_evidence("ctx", "a", idempotency_key="t")
        pre = self.service.precertify(t, self.service.snapshot("ctx").knowledge_revision,
                                     idempotency_key="pre")
        self.assertEqual(pre.status, Status.STALE)

    def test_cycle_preserves_root_and_cannot_outlive_it(self):
        a = self.driver.adopt("a", A).belief
        b = self.driver.finish(self.driver.prepare(
            self.driver.transition("next", (a.belief_revision_id,)))).belief
        derived_a = self.driver.finish(self.driver.prepare(
            self.driver.transition("back", (b.belief_revision_id,)))).belief
        self.assertEqual(derived_a.proposal.evidence_ids, ("a",))
        self.assertEqual(derived_a.proposal.lineage_roots, ("origin:a",))
        self.service.revoke_evidence("a", idempotency_key="revoke")
        self.assertEqual(self.service.snapshot("ctx").usable, ())

    def test_same_snapshot_concurrent_conflicts_commit_at_most_once(self):
        self.driver.record("a", A)
        self.driver.record("not-a", A.negate())
        ta = self.service.propose_evidence("ctx", "a", idempotency_key="ta")
        tn = self.service.propose_evidence("ctx", "not-a", idempotency_key="tn")
        prepared = (self.driver.prepare(ta), self.driver.prepare(tn))
        barrier = Barrier(2)

        def worker(index):
            barrier.wait(timeout=5)
            return self.service.commit(*prepared[index], idempotency_key=f"worker-{index}")

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(worker, range(2)))
        self.assertCountEqual([r.status for r in outcomes], [Status.PASS, Status.STALE])
        self.assertEqual(len(self.service.snapshot("ctx").usable), 1)
        loser = ta if outcomes[0].status is Status.STALE else tn
        self.assertEqual(self.driver.finish(self.driver.prepare(loser)).status, Status.FAIL)

    def test_capacity_exhaustion_cannot_certify_truncated_scope(self):
        service = AdmissionService(max_variables=1)
        driver = Driver(service)
        driver.context()
        driver.adopt("a", A)
        self.assertEqual(driver.adopt("b", B).status, Status.UNKNOWN)
        self.assertEqual(len(service.snapshot("ctx").usable), 1)

    def test_invalid_context_is_not_created(self):
        with self.assertRaises(AdmissionDenied):
            self.driver.context("bad", assumptions=(A, A.negate()))
        with self.assertRaises(KeyError):
            self.service.snapshot("bad")

    def test_mutable_constructor_inputs_are_copied(self):
        arguments = ["x"]
        statement = Statement("P", arguments)
        arguments.append("y")
        self.assertEqual(statement.arguments, ("x",))
        assumptions = [A]
        self.driver.context("immutable", assumptions=assumptions)
        assumptions.append(A.negate())
        self.assertEqual(self.service.snapshot("immutable").assumptions, (A,))

    def test_empty_or_malformed_gate_contract_is_not_pass(self):
        self.assertEqual(conjunction(()), Status.UNKNOWN)
        self.assertEqual(conjunction((Check("x", "PASS", "untyped"),)), Status.UNKNOWN)
        for status in (Status.FAIL, Status.UNKNOWN, Status.STALE):
            self.assertEqual(conjunction((Check("a", Status.PASS, ""),
                                          Check("b", status, ""))), status)
