"""Explicit optional suite: missing dependencies are errors, never silent skips."""
from dataclasses import replace
from fractions import Fraction
import math
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from reachability.adapter_runtime import AdapterError, ROOT, verify_source
from reachability.atomspace_adapter import AtomSpaceBatch, RecordProjection, project_admission
from reachability.model import Evidence, Literal, Statement, Status
from reachability.pln_adapter import (
    IndependenceDeclaration, PLNAdapter, PLNRejected, PeTTaFormulaRuntime, TruthValue,
)
from reachability.service import AdmissionService
from tests.test_pln_contracts import snapshot


class NativeAtomSpaceTests(TestCase):
    def test_native_identity_order_unicode_and_values(self):
        batch = AtomSpaceBatch()
        a = batch.node('quotes " \\ newline\nλ')
        duplicate = batch.node('quotes " \\ newline\nλ')
        b = batch.node("B")
        ab = batch.link((a, b))
        ba = batch.link((b, a))
        truth = batch.node("pln:strength-confidence", predicate=True)
        exact = batch.node("knowledge-revision", predicate=True)
        batch.set_value(ab, truth, (.6, .7))
        batch.set_value(ba, exact, str(2**80))
        # Writes through aliases must preserve actual temporal overwrite order.
        batch.set_value(a, exact, "first")
        batch.set_value(duplicate, exact, "second")
        batch.set_value(a, exact, "final")
        graph = batch.run()
        self.assertEqual(graph.aliases[a], graph.aliases[duplicate])
        self.assertNotEqual(graph.aliases[ab], graph.aliases[ba])
        self.assertEqual(graph.values[graph.aliases[a], graph.aliases[exact]], "final")
        self.assertEqual(graph.values[graph.aliases[ab], graph.aliases[truth]], (.6, .7))
        self.assertEqual(graph.values[graph.aliases[ba], graph.aliases[exact]], str(2**80))
        self.assertEqual(graph.size, 7)  # Six structural atoms plus native key marker.

    def test_empty_values_and_empty_batch(self):
        self.assertEqual(AtomSpaceBatch().run().size, 0)
        batch = AtomSpaceBatch()
        node, key = batch.node(""), batch.node("key", predicate=True)
        batch.set_value(node, key, ())
        self.assertEqual(batch.run().values[(node, key)], ())
        batch.set_value(node, key, "")
        self.assertEqual(batch.run().values[(node, key)], "")

    def test_native_rejects_malformed_commands(self):
        for command in ("N zz\n", "L 1 0\n", "N 61 extra\n", "eval arbitrary\n", "L 5000\n"):
            with self.subTest(command=command):
                result = subprocess.run([str(ROOT / "artifacts/bin/atomspace_batch")], input=command,
                                        capture_output=True, text=True, timeout=10)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")

    def test_typed_records_keep_polarity_scope_and_exact_integers(self):
        projection = RecordProjection()
        evidence = Evidence("sample", "a", Literal(Statement("rel", ("x", "y"))), "sensor", 2**80, ("origin",))
        a = projection.add(evidence)
        duplicate = projection.add(evidence)
        b = projection.add(replace(evidence, context_id="b"))
        neg = projection.add(replace(evidence, content=evidence.content.negate()))
        later = projection.add(replace(evidence, observed_at=2**80+1))
        graph = projection.batch.run()
        self.assertEqual(a, duplicate)
        self.assertEqual(len({graph.aliases[x] for x in (a, b, neg, later)}), 4)
        self.assertIn(str(2**80), graph.values.values())
        self.assertIn(str(2**80+1), graph.values.values())

    def test_checked_journal_rebuild_and_revocation(self):
        with TemporaryDirectory() as directory:
            database = Path(directory) / "authority.sqlite"
            with AdmissionService(database=database) as service:
                service.open_context("c", idempotency_key="open")
                literal = Literal(Statement("Ready", ("machine",)))
                evidence = Evidence("e", "c", literal, "sensor", 0, ("origin",))
                service.record_evidence(evidence, idempotency_key="e")
                transition = service.propose_evidence("c", "e", idempotency_key="t")
                revision = service.snapshot("c").knowledge_revision
                pre = service.precertify(transition, revision, idempotency_key="pre")
                proposal = service.infer(transition, pre)
                post = service.postcertify(proposal, pre, idempotency_key="post")
                service.commit(proposal, pre, post, revision, idempotency_key="commit")
                accepted = project_admission(service, "c")
                self.assertIn(("N", "enum:Status:PASS"), accepted.atoms.values())
                before = service.export_admission("c")
                with self.assertRaises(AdapterError):
                    project_admission(service, "c", root=Path(directory) / "missing")
                self.assertEqual(service.export_admission("c"), before)
            with AdmissionService(database=database) as service:
                self.assertEqual(project_admission(service, "c"), accepted)
                service.revoke_evidence("e", idempotency_key="revoke")
                stale = project_admission(service, "c")
                self.assertIn(("N", "enum:Status:STALE"), stale.atoms.values())
                self.assertEqual(service.query_belief("c", literal).current, ())
                self.assertNotEqual(stale, accepted)


class NativePLNTests(TestCase):
    def setUp(self):
        self.adapter = PLNAdapter()
        self.rule, self.data = snapshot()

    def test_deduction_matches_independent_rational_fixtures(self):
        fixtures = [(.4, .5, .6, .7, .8), (.5, .5, .5, .5, .5),
                    (.5, .25, .5, .5, 1), (.5, 1, .75, 1, .75),
                    (.5, .99995, .75, .99995, .75), (.5, .5, .5, 0, 0)]
        for strengths in fixtures:
            with self.subTest(strengths=strengths):
                rule, data = snapshot(strengths)
                result = self.adapter.apply_rule(rule, data)
                p, q, r, pq, qr = map(Fraction, strengths)
                expected_s = r if q > Fraction.from_float(.9999) else pq*qr + (1-pq)*(r-q*qr)/(1-q)
                expected_c = pq*qr*Fraction(.8)*Fraction(.7)
                self.assertAlmostEqual(result.support.truth.strength, float(expected_s), places=14)
                self.assertAlmostEqual(result.support.truth.confidence, float(expected_c), places=14)

    def test_invalid_domain_cannot_accept_upstream_fallback(self):
        rule, data = snapshot((.9, .1, .5, .9, .5))
        with self.assertRaises(PLNRejected) as error:
            self.adapter.apply_rule(rule, data)
        self.assertEqual(error.exception.status, Status.FAIL)
        with self.assertRaises(PLNRejected):
            self.adapter.runtime.evaluate("Truth_Deduction", tuple(s.truth for s in data.supports))

    def test_runtime_boundary_disagreement_remains_unknown(self):
        # (.5 + .6 - 1) / .5 rounds above .2 in the upstream lower-bound check.
        # The exact joint cell constraints are feasible; disagreement still cannot
        # be treated as an accepted upstream fallback truth value.
        rule, data = snapshot((.5, .6, .6, .2, .5))
        self.assertEqual(self.adapter.check_rule_preconditions(rule, data).status, Status.PASS)
        with self.assertRaises(PLNRejected) as error:
            self.adapter.apply_rule(rule, data)
        self.assertEqual(error.exception.status, Status.UNKNOWN)

    def test_actual_modified_formula_checkout_is_rejected(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "upstream/pln"
            target.parent.mkdir()
            subprocess.run(["git", "clone", "--quiet", "--shared",
                            str(ROOT / "artifacts/upstream/pln"), str(target)], check=True)
            verify_source("pln", root)
            library = target / "lib_pln.metta"
            library.write_text(library.read_text() + "\n; changed formula source\n")
            with self.assertRaises(AdapterError):
                verify_source("pln", root)

    def test_revision_matches_exact_weight_arithmetic(self):
        for c1, c2 in ((.5, .5), (.25, .75), (0, .75)):
            a = replace(self.data.supports[0], truth=TruthValue(.25, c1))
            b = replace(a, support_id="b", truth=TruthValue(.75, c2), evidence_ids=("eb",), lineage_roots=("rb",))
            result = self.adapter.revise(a, b, 7, IndependenceDeclaration("independent-trials", (a, b)))
            w1, w2 = (Fraction(c)/(1-Fraction(c)) for c in (c1, c2))
            self.assertAlmostEqual(result.proposal.support.truth.strength, float((w1/4+w2*3/4)/(w1+w2)))
            self.assertAlmostEqual(result.proposal.support.truth.confidence, float((w1+w2)/(w1+w2+1)))

    def test_near_certain_finite_revision_stays_below_one(self):
        near_one = math.nextafter(1, 0)
        result = self.adapter.runtime.evaluate("Truth_Revision", (TruthValue(.5, near_one), TruthValue(.5, near_one)))
        self.assertLess(result.confidence, 1)
        self.assertGreaterEqual(result.confidence, near_one)

    def test_proposal_roundtrip_to_named_native_float_value(self):
        result = self.adapter.apply_rule(self.rule, self.data)
        projection = RecordProjection()
        atom = projection.add_probability(result)
        tv = result.support.truth
        graph = projection.batch.run()
        key = next(k for k, v in graph.atoms.items() if v == ("P", "pln:strength-confidence"))
        self.assertEqual(graph.values[graph.aliases[atom], key], (tv.strength, tv.confidence))
        self.assertIn(("N", "text:proposed-probabilistic-support/v1"), graph.atoms.values())
        self.assertNotIn(("N", "record:BeliefRevision"), graph.atoms.values())

    def test_unexpected_runtime_output_fails_closed(self):
        # Verify pins normally; substitute only the final process response.
        from reachability import pln_adapter
        real_run = pln_adapter.checked_run
        for output in ("true\n(stv nan 0.5)\n", "true\n(stv 0.5 1.0)\n", "true\n(stv 0.5 0.5)\n(stv 0.6 0.6)\n", "false\n"):
            def run(args, **kwargs):
                return output if "--silent" in args else real_run(args, **kwargs)
            with self.subTest(output=output), patch.object(pln_adapter, "checked_run", run), self.assertRaises(AdapterError):
                self.adapter.apply_rule(self.rule, self.data)

    def test_runtime_timeout_is_not_a_truth_value(self):
        runtime = PeTTaFormulaRuntime(timeout=.00001)
        with self.assertRaises(AdapterError):
            runtime.evaluate("Truth_Deduction", tuple(s.truth for s in self.data.supports))
