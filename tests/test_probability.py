from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from reachability.errors import AdmissionDenied, IdempotencyConflict
from reachability.model import Clause, Literal, Statement, Status
from reachability.pln_adapter import DeductionRule, PLNAdapter, TruthValue, implication, proposition
from reachability.probability_model import ProbabilityIndependence, ProbabilityPolicy, ProbabilityReport, ProbabilityRule
from reachability.service import AdmissionService
from tests.probability_support import ProbabilityDriver

P = proposition("P")


class ProbabilityContractTests(TestCase):
    database = None

    def setUp(self):
        self.service = AdmissionService(database=self.database)
        self.addCleanup(self.service.close)
        self.driver = ProbabilityDriver(self.service)
        self.driver.context()

    def pre(self, transition):
        return self.service.precertify_probability(transition, self.service.snapshot(transition.context_id).knowledge_revision,
                                                   idempotency_key=self.driver.key())

    def test_report_does_not_accept_any_belief(self):
        self.driver.report("e", P)
        self.assertEqual(self.service.query_probability("world", P).status, Status.UNKNOWN)
        self.assertEqual(self.service.query_belief("world", P).status, Status.UNKNOWN)

    def test_numeric_admission_preserves_uncertainty_and_hard_query_is_unknown(self):
        belief = self.driver.adopt("e", P, TruthValue(.4, .8)).belief
        view = self.service.query_probability("world", P)
        self.assertEqual(view.status, Status.PASS)
        self.assertEqual(view.current, (belief,))
        self.assertEqual(view.current[0].proposal.support.truth, TruthValue(.4, .8))
        self.assertEqual(self.service.query_belief("world", P).status, Status.UNKNOWN)
        self.assertEqual(self.service.snapshot("world").usable, ())

    def test_source_policy_future_and_expired_reports(self):
        denied = self.driver.report("unauthorized", P, source="untrusted")
        self.assertEqual(self.pre(denied).status, Status.UNKNOWN)
        future = self.driver.report("future", P, observed_at=2, valid_until=4)
        self.assertEqual(self.pre(future).status, Status.UNKNOWN)
        self.service.advance_clock("world", 2, idempotency_key=self.driver.key())
        self.assertEqual(self.driver.finish(self.driver.prepare(future)).status, Status.PASS)
        self.service.advance_clock("world", 4, idempotency_key=self.driver.key())
        self.assertEqual(self.service.query_probability("world", P).status, Status.STALE)
        self.assertEqual(self.pre(future).status, Status.STALE)

    def test_report_cannot_be_reinterpreted_under_same_evidence_id(self):
        self.driver.report("e", P)
        with self.assertRaises(IdempotencyConflict):
            self.service.record_probability_report(ProbabilityReport("e", TruthValue(.9, .9)), idempotency_key=self.driver.key())

    def test_foreign_report_and_premise_cannot_cross_contexts(self):
        foreign = self.driver.adopt("e", P).belief
        self.driver.context("other")
        t = self.service.propose_probability("other", "observation", evidence_id="e", idempotency_key=self.driver.key())
        self.assertEqual(self.pre(t).status, Status.FAIL)
        self.service.configure_probability_rule("other", ProbabilityRule("r", "1", DeductionRule("P", "Q", "R")),
                                               idempotency_key=self.driver.key())
        t = self.service.propose_probability("other", "deduction", rule_id="r", premise_revision_ids=(foreign.belief_revision_id,),
                                            idempotency_key=self.driver.key())
        self.assertEqual(self.pre(t).status, Status.FAIL)

    def test_deduction_requires_complete_ordered_current_numeric_premises(self):
        _, beliefs, transition = self.driver.deduction()
        prepared = self.driver.prepare(transition)
        self.assertIsNotNone(prepared[2].joint_witness)
        result = self.driver.finish(prepared)
        self.assertEqual(result.status, Status.PASS)
        self.assertAlmostEqual(result.belief.proposal.support.truth.strength, .68)
        self.assertEqual(result.belief.proposal.support.lineage_roots, tuple("root:s"+str(i) for i in range(5)))
        reversed_t = self.service.propose_probability("world", "deduction", rule_id="deduce",
            premise_revision_ids=tuple(b.belief_revision_id for b in reversed(beliefs)), idempotency_key=self.driver.key())
        self.assertEqual(self.pre(reversed_t).status, Status.FAIL)
        missing = self.service.propose_probability("world", "deduction", rule_id="deduce",
            premise_revision_ids=(beliefs[0].belief_revision_id,), idempotency_key=self.driver.key())
        self.assertEqual(self.pre(missing).status, Status.UNKNOWN)

    def test_infeasible_conditional_and_float_disagreement_fail_closed(self):
        _, _, transition = self.driver.deduction((.9, .1, .5, .9, .5))
        self.assertEqual(self.pre(transition).status, Status.FAIL)
        with self.assertRaises(AdmissionDenied):
            self.service.infer_probability(transition, self.pre(transition), adapter=self.driver.adapter)

    def test_runtime_boundary_disagreement_does_not_issue_pass(self):
        _, _, transition = self.driver.deduction((.5, .6, .6, .2, .5))
        self.assertEqual(self.pre(transition).status, Status.UNKNOWN)

    def test_altered_numeric_result_lineage_formula_and_revision_are_rejected(self):
        transition = self.driver.report("e", P, TruthValue(0, .8))
        proposal, pre, post, rev = self.driver.prepare(transition)
        altered = (replace(proposal, formula_id="unregistered"), replace(proposal, knowledge_revision=rev+1),
                   replace(proposal, context_id="elsewhere"),
                   replace(proposal, support=replace(proposal.support, truth=TruthValue(.9, .9))),
                   replace(proposal, support=replace(proposal.support, lineage_roots=("forged",))),
                   replace(proposal, support=replace(proposal.support, truth=TruthValue(-0.0, .8))))
        for changed in altered:
            with self.subTest(proposal=changed):
                failed = self.service.postcertify_probability(changed, pre, idempotency_key=self.driver.key())
                self.assertEqual(failed.status, Status.FAIL)
                self.assertEqual(self.service.commit_probability(changed, pre, failed, rev,
                                                                 idempotency_key=self.driver.key()).status, Status.FAIL)
        self.assertEqual(self.driver.finish((proposal, pre, post, rev)).status, Status.PASS)

    def test_forged_or_swapped_certificates_cannot_commit(self):
        transition = self.driver.report("e", P)
        proposal, pre, post, rev = self.driver.prepare(transition)
        for altered in (replace(post, certificate_id="fabricated"), replace(post, snapshot_digest="forged"), pre):
            with self.subTest(cert=altered):
                result = self.service.commit_probability(proposal, pre, altered, rev, idempotency_key=self.driver.key())
                self.assertEqual(result.status, Status.FAIL)
        other_pre = self.pre(transition)
        result = self.service.commit_probability(proposal, other_pre, post, rev, idempotency_key=self.driver.key())
        self.assertEqual(result.status, Status.FAIL)

    def test_wrong_authority_certificate_is_untrusted(self):
        transition = self.driver.report("e", P)
        prepared = self.driver.prepare(transition)
        with AdmissionService() as other:
            d = ProbabilityDriver(other); d.context()
            same_transition = d.report("e", P)
            foreign = d.prepare(same_transition)
            self.assertEqual(transition, same_transition)
            result = self.service.commit_probability(prepared[0], foreign[1], foreign[2], prepared[3],
                                                     idempotency_key=self.driver.key())
            self.assertEqual(result.status, Status.FAIL)

    def test_intervening_evidence_clock_and_policy_stale_pending_permits(self):
        transition = self.driver.report("e", P)
        prepared = self.driver.prepare(transition)
        self.driver.report("other", proposition("Q"))
        self.assertEqual(self.driver.finish(prepared).status, Status.STALE)
        prepared = self.driver.prepare(transition)
        self.service.advance_clock("world", 1, idempotency_key=self.driver.key())
        self.assertEqual(self.driver.finish(prepared).status, Status.STALE)
        prepared = self.driver.prepare(transition)
        self.service.configure_probability_policy("world", ProbabilityPolicy("p2", ("sensor",)), "p1",
                                                  idempotency_key=self.driver.key())
        self.assertEqual(self.driver.finish(prepared).status, Status.STALE)

    def test_revocation_invalidates_derived_closure_and_retains_history(self):
        _, beliefs, transition = self.driver.deduction()
        derived = self.driver.finish(self.driver.prepare(transition)).belief
        alternative = self.driver.adopt("alternative", proposition("P"), TruthValue(.4, .8)).belief
        self.service.revoke_evidence("s0", idempotency_key=self.driver.key())
        self.assertEqual(self.service.query_probability("world", proposition("P")).current, (alternative,))
        view = self.service.query_probability("world", implication("P", "R"))
        self.assertEqual(view.status, Status.STALE)
        self.assertEqual(view.historical, (derived,))
        self.assertEqual(self.pre(transition).status, Status.STALE)

    def test_rule_replacement_retires_only_dependent_numeric_estimates(self):
        _, beliefs, transition = self.driver.deduction()
        self.driver.finish(self.driver.prepare(transition))
        self.service.configure_probability_rule("world", ProbabilityRule("deduce", "2", DeductionRule("P", "Q", "S")),
                                                "1", idempotency_key=self.driver.key())
        self.assertEqual(self.service.query_probability("world", implication("P", "R")).status, Status.STALE)
        self.assertEqual(self.service.query_probability("world", proposition("P")).current, (beliefs[0],))
        self.assertEqual(self.pre(transition).status, Status.STALE)
        with self.assertRaises(ValueError):
            self.service.configure_probability_rule("world", ProbabilityRule("deduce", "1", DeductionRule("P", "Q", "R")),
                                                    "2", idempotency_key=self.driver.key())

    def test_policy_replacement_retires_estimates_without_reusing_old_revision(self):
        self.driver.adopt("e", P)
        self.service.configure_probability_policy("world", ProbabilityPolicy("p2", ("sensor",)), "p1",
                                                  idempotency_key=self.driver.key())
        self.assertEqual(self.service.query_probability("world", P).status, Status.STALE)
        with self.assertRaises(ValueError):
            self.service.configure_probability_policy("world", ProbabilityPolicy("p1", ("sensor",)), "p2",
                                                      idempotency_key=self.driver.key())

    def test_hard_policy_change_requires_numeric_readmission(self):
        self.driver.adopt("e", P)
        rev = self.service.snapshot("world").knowledge_revision
        self.service.replace_policy("world", "hard-p2", (), rev, idempotency_key=self.driver.key())
        self.assertEqual(self.service.query_probability("world", P).status, Status.STALE)

    def pair(self, roots=None, confidences=(.5, .5)):
        a = self.driver.adopt("a", P, TruthValue(.25, confidences[0])).belief
        b = self.driver.adopt("b", P, TruthValue(.75, confidences[1]), roots=roots).belief
        return a, b

    def revise(self, a, b, declare=True):
        ids = (a.belief_revision_id, b.belief_revision_id)
        if declare:
            self.service.register_probability_independence(ProbabilityIndependence("independent", "world", ids,
                                                         "separately sampled observations under declared model"),
                                                          idempotency_key=self.driver.key())
        return self.service.propose_probability("world", "revision", premise_revision_ids=ids,
                                                independence_id="independent" if declare else None,
                                                idempotency_key=self.driver.key())

    def test_revision_requires_registered_model_and_preserves_alternatives(self):
        a, b = self.pair()
        transition = self.revise(a, b, declare=False)
        self.assertEqual(self.pre(transition).status, Status.UNKNOWN)
        self.assertEqual(self.service.query_probability("world", P).current, (a, b))
        transition = self.revise(a, b)
        result = self.driver.finish(self.driver.prepare(transition))
        self.assertEqual(result.status, Status.PASS)
        self.assertAlmostEqual(result.belief.proposal.support.truth.strength, .5)
        self.assertAlmostEqual(result.belief.proposal.support.truth.confidence, 2/3)
        self.assertEqual(len(self.service.query_probability("world", P).current), 3)

    def test_overlap_and_zero_weight_cannot_become_revision(self):
        a, b = self.pair(roots=("root:a",))
        transition = self.revise(a, b)
        self.assertEqual(self.pre(transition).status, Status.UNKNOWN)

    def test_zero_weight_revision_unknown(self):
        a, b = self.pair(confidences=(0, 0))
        self.assertEqual(self.pre(self.revise(a, b)).status, Status.UNKNOWN)

    def test_wrong_independence_binding_and_revocation(self):
        a, b = self.pair()
        transition = self.revise(a, b)
        merged = self.driver.finish(self.driver.prepare(transition)).belief
        wrong = self.service.propose_probability("world", "revision",
            premise_revision_ids=(a.belief_revision_id, merged.belief_revision_id), independence_id="independent",
            idempotency_key=self.driver.key())
        self.assertEqual(self.pre(wrong).status, Status.FAIL)
        self.service.revoke_probability_independence("world", "independent", idempotency_key=self.driver.key())
        self.assertEqual(self.service.query_probability("world", P).current, (a, b))
        self.assertEqual(self.pre(transition).status, Status.STALE)
        declaration = self.service._probability.independence["world", "independent"]
        self.service.register_probability_independence(declaration, idempotency_key=self.driver.key())
        self.assertEqual(self.pre(transition).status, Status.STALE)

    def test_repeated_derivation_and_command_retry_create_no_new_support(self):
        _, _, transition = self.driver.deduction()
        prepared = self.driver.prepare(transition)
        first = self.driver.finish(prepared, "once")
        revision = self.service.snapshot("world").knowledge_revision
        self.assertEqual(self.driver.finish(prepared, "once"), first)
        repeated = self.driver.finish(self.driver.prepare(transition))
        self.assertEqual(repeated.belief, first.belief)
        self.assertEqual(repeated.knowledge_revision, revision)
        with self.assertRaises(IdempotencyConflict):
            self.service.advance_clock("world", 9, idempotency_key="once")

    def test_one_of_two_concurrent_commits_wins(self):
        a = self.driver.report("a", P)
        b = self.driver.report("b", proposition("Q"))
        prepared = (self.driver.prepare(a), self.driver.prepare(b))
        with ThreadPoolExecutor(2) as workers:
            futures = [workers.submit(self.driver.finish, p, f"race-{i}") for i, p in enumerate(prepared)]
            statuses = [f.result().status for f in futures]
        self.assertEqual(set(statuses), {Status.PASS, Status.STALE})

    def test_native_inference_can_race_revocation_but_cannot_commit(self):
        _, _, transition = self.driver.deduction()
        rev = self.service.snapshot("world").knowledge_revision
        pre = self.pre(transition)
        real = self.driver.adapter
        service = self.service
        class RevokingAdapter:
            def apply_rule(self, rule, snapshot):
                # Another worker can acquire the service lock during external I/O.
                with ThreadPoolExecutor(1) as workers:
                    workers.submit(service.revoke_evidence, "s0", idempotency_key="inflight-revoke").result(timeout=5)
                return real.apply_rule(rule, snapshot)
        proposal = self.service.infer_probability(transition, pre, adapter=RevokingAdapter())
        post = self.service.postcertify_probability(proposal, pre, idempotency_key=self.driver.key())
        self.assertEqual(post.status, Status.STALE)
        self.assertEqual(self.service.commit_probability(proposal, pre, post, rev, idempotency_key=self.driver.key()).status, Status.STALE)

    def test_history_budget_does_not_partially_publish(self):
        self.driver.context("small", max_beliefs=1)
        first = self.driver.adopt("first", P, context="small").belief
        second = self.driver.report("second", P, context="small")
        prepared = self.driver.prepare(second)
        result = self.driver.finish(prepared)
        self.assertEqual(result.status, Status.UNKNOWN)
        self.assertEqual(self.service.query_probability("small", P).historical, (first,))
        self.assertEqual(result.knowledge_revision, prepared[3])

    def test_numeric_estimates_never_satisfy_boolean_requirements(self):
        from reachability.requirements import Requirement, evaluate
        self.driver.adopt("e", P, TruthValue(1, .999))
        result = evaluate(Requirement("FACT", literal=P), self.service.snapshot("world"))
        self.assertEqual(result.status, Status.UNKNOWN)

    def test_cyclic_deduction_cannot_mint_new_weight(self):
        _, beliefs, first = self.driver.deduction((.5, .5, .5, .5, .5))
        derived = self.driver.finish(self.driver.prepare(first)).belief
        rq = self.driver.adopt("rq", implication("R", "Q")).belief
        self.service.configure_probability_rule("world", ProbabilityRule("back", "1", DeductionRule("P", "R", "Q")),
                                               idempotency_key=self.driver.key())
        premises = (beliefs[0], beliefs[2], beliefs[1], derived, rq)
        back = self.service.propose_probability("world", "deduction", rule_id="back",
            premise_revision_ids=tuple(b.belief_revision_id for b in premises), idempotency_key=self.driver.key())
        self.assertEqual(self.pre(back).status, Status.UNKNOWN)
        self.assertEqual(self.service.query_probability("world", implication("P", "Q")).current, (beliefs[3],))

    def test_revoked_independence_invalidates_descendant_deduction(self):
        _, beliefs, transition = self.driver.deduction((.5, .5, .5, .5, .5))
        alternative = self.driver.adopt("alt-pq", implication("P", "Q")).belief
        revision = self.revise(beliefs[3], alternative)
        merged = self.driver.finish(self.driver.prepare(revision)).belief
        ids = tuple(b.belief_revision_id for b in (*beliefs[:3], merged, beliefs[4]))
        transition = self.service.propose_probability("world", "deduction", rule_id="deduce",
                                                      premise_revision_ids=ids, idempotency_key=self.driver.key())
        self.assertEqual(self.driver.finish(self.driver.prepare(transition)).status, Status.PASS)
        self.service.revoke_probability_independence("world", "independent", idempotency_key=self.driver.key())
        self.assertEqual(self.service.query_probability("world", implication("P", "R")).status, Status.STALE)

    def test_nonfinite_intermediate_cannot_pass_clamping(self):
        _, _, transition = self.driver.deduction((5e-324, .5, .5, .5, .5))
        self.assertEqual(self.pre(transition).status, Status.FAIL)

    def test_near_one_approximation_cannot_bypass_whole_joint_check(self):
        # P and Q denote the same event in this model: P=Q and P(Q|P)=1.
        # Hence P(R|P) must equal P(R|Q)=.5. The upstream approximation
        # returns P(R)=.499975 instead; every pair is feasible but the triad is not.
        _, _, transition = self.driver.deduction((.99995, .99995, .499975, 1, .5))
        certificate = self.pre(transition)
        self.assertEqual(certificate.status, Status.FAIL)
        self.assertIsNone(certificate.joint_witness)

    def test_retry_after_revocation_returns_history_without_current_authority(self):
        transition = self.driver.report("e", P)
        prepared = self.driver.prepare(transition)
        accepted = self.driver.finish(prepared, "accept-once")
        self.service.revoke_evidence("e", idempotency_key=self.driver.key())
        self.assertEqual(self.driver.finish(prepared, "accept-once"), accepted)
        self.assertEqual(self.service.query_probability("world", P).status, Status.STALE)

    def test_old_certificates_cannot_authorize_replacement_transition(self):
        _, _, transition = self.driver.deduction()
        prepared = self.driver.prepare(transition)
        changed = replace(transition, transition_id="invented")
        with self.assertRaises(AdmissionDenied):
            self.service.precertify_probability(changed, prepared[3], idempotency_key=self.driver.key())
        forged = replace(prepared[1], knowledge_revision=prepared[3]+1)
        self.assertEqual(self.service.commit_probability(prepared[0], forged, prepared[2], prepared[3],
                                                         idempotency_key=self.driver.key()).status, Status.FAIL)


class DurableProbabilityContractTests(ProbabilityContractTests):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.database = Path(self.directory.name) / "probability.sqlite"
        super().setUp()

    def tearDown(self):
        expected = {name: self.service.export_probability(name) for name in self.service._contexts}
        self.service.close()
        with AdmissionService(database=self.database) as recovered:
            self.assertEqual({name: recovered.export_probability(name) for name in expected}, expected)
