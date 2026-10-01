import ast
from copy import deepcopy
import json
import math
from pathlib import Path
import select
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from reachability.admission_protocol import AdmissionEvent, AdmissionInitial, event
from reachability.admission_trace import AdmissionSession
from reachability.trace_protocol import canonical, fingerprint
from validation_lab.admission_oracle import OracleGap, reference_prefix
from validation_lab.generate_admission_cases import (adopt, context, derive, evidence, generated_scenarios, independence,
    initial, make_case, op, policy, revise, scenarios, tick)
from validation_lab.run_admission import load_cases, mutation_witness, run_case, verify_corpus

ROOT = Path(__file__).resolve().parents[1]


class AdmissionTraceTests(unittest.TestCase):
    def test_fixed_controls_match_every_cold_and_recovered_prefix(self):
        config, cases = load_cases()
        receipt = verify_corpus()
        prefixes = 0
        for case in cases:
            with self.subTest(case=case["case_id"]):
                records = run_case(config, case)
                prefixes += len(records)
                for record, message in zip(records, case["events"]):
                    self.assertEqual(record["schema"], "admission-trace/v1")
                    self.assertEqual(record["event_digest"], fingerprint(message))
                    self.assertEqual(record["initial_digest"], fingerprint(config.wire()))
        self.assertEqual(prefixes, receipt["event_prefixes"])
        self.assertEqual(prefixes, 127)

    def test_seeded_cases_keep_all_outcomes_and_recover_every_prefix(self):
        cases = generated_scenarios()
        self.assertEqual(cases, generated_scenarios())
        self.assertEqual(sum(len(c["events"]) for c in cases), 168)
        for case in cases:
            with self.subTest(case=case["case_id"]):
                run_case(initial(), case)

    def test_M05_has_a_passing_control_and_preserves_the_actual_faulty_output(self):
        case = scenarios()[13]
        run_case(initial(), case, restart_every_prefix=False)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "actual.jsonl"
            witness = mutation_witness(initial(), case, trace_path=path)
            records = [json.loads(line) for line in path.read_text().splitlines()]
        self.assertTrue(witness["detected"])
        self.assertEqual(witness["first_divergent_prefix"], 5)
        self.assertEqual((witness["expected"], witness["actual"]), ("UNKNOWN", "PASS"))
        self.assertGreater(witness["invocations"], 0)
        self.assertEqual(len(records), 5)
        self.assertEqual(records[-1]["projection"]["numeric"]["e004"]["confidence"], 2/3)
        self.assertEqual(records[-1]["projection_digest"], fingerprint(records[-1]["projection"]))
        # Mutation scope has ended: another unmodified run must block again.
        self.assertEqual(run_case(initial(), case, restart_every_prefix=False)[4]["outcome"]["status"], "UNKNOWN")

    def test_identity_renaming_preserves_semantics_and_development_ancestry(self):
        case = scenarios()[15]
        names = {x: "renamed-"+x for x in ("c0", "m0", "m1", "s0", "s1", "a0", "a1", "a2", "a3")}
        names.update({e["event_id"]: "renamed-"+e["event_id"] for e in case["events"]})
        def rename(value, mapping):
            if isinstance(value, dict):
                return {mapping.get(k, k): rename(v, mapping) for k, v in value.items()}
            if isinstance(value, list):
                return [rename(v, mapping) for v in value]
            return mapping.get(value, value) if isinstance(value, str) else value
        changed = rename(case, names)
        changed["checkpoints"] = []  # Dot paths are evaluator data, not public IDs.
        config = AdmissionInitial.parse(rename(initial().wire(), names))
        original_records = run_case(initial(), case)
        changed_records = run_case(config, changed)
        inverse = {v: k for k, v in names.items()}
        for old, new in zip(original_records, changed_records):
            self.assertEqual(old["projection"], rename(new["projection"], inverse))
            self.assertEqual(old["outcome"]["status"], new["outcome"]["status"])
        self.assertEqual(changed["parent_instance_id"], case["parent_instance_id"])
        self.assertEqual(changed["split"], "development")

    def test_independent_context_events_commute(self):
        case = scenarios()[8]
        changed = deepcopy(case)
        changed["events"][2:4] = reversed(changed["events"][2:4])
        changed["checkpoints"] = []
        self.assertEqual(run_case(initial(), case)[-1]["projection"], run_case(initial(), changed)[-1]["projection"])

    def test_eighth_atom_and_negative_ordered_premises_are_in_scope(self):
        config = AdmissionInitial.parse(dict(schema="admission-initial/v1", atoms=["v"+str(i) for i in range(8)],
            rules=[dict(rule_id="r0", revision="1", premises=[8, -7], conclusion=6)]))
        case = make_case("eight", "F01", "boundary", [context(clauses=[[-8, -7]]), evidence(8), evidence(-7),
                         derive("r0", 1, 2), derive("r0", 2, 1)])
        records = run_case(config, case)
        self.assertEqual(records[-2]["projection"]["contexts"]["c0"]["hard"]["6"], "PASS")
        self.assertEqual(records[-1]["outcome"]["status"], "FAIL")

    def test_unsatisfiable_base_and_rejected_policy_preserve_accepted_state(self):
        case = make_case("reject", "F02", "blocked", [context(clauses=[[]]), context(assumptions=[1]), evidence(2),
                         policy([[-1]]), adopt(2), tick(1), tick(0), evidence(4, until=1)])
        records = run_case(initial(), case)
        self.assertEqual([r["outcome"]["status"] for r in records], ["FAIL", "PASS", "PASS", "FAIL", "PASS", "PASS", "FAIL", "FAIL"])
        self.assertEqual(records[2]["projection"], records[3]["projection"])

    def test_nested_revision_and_exact_model_retirement(self):
        case = make_case("nested", "F05", "revision_change", [context(), evidence(1, truth=(.2, .4)),
            evidence(1, root="s1", truth=(.7, .8)), independence(1, 2), revise(1, 2),
            evidence(1, root="s2", truth=(.3, .6)), independence(4, 5, model="m1"), revise(4, 5, model="m1"),
            independence(4, 1, model="m2"), revise(4, 1, model="m2"),
            op("revoke_model", context_id="c0", model_id="m0")])
        records = run_case(initial(), case)
        self.assertEqual(records[7]["outcome"]["status"], "PASS")
        self.assertEqual(records[9]["outcome"]["status"], "UNKNOWN")
        self.assertFalse(records[-1]["projection"]["numeric"]["e007"]["current"])
        self.assertTrue(records[-1]["projection"]["numeric"]["e005"]["current"])

    def test_rational_oracle_matches_binary64_revision_boundaries(self):
        for truths in (((.1, math.nextafter(1., 0.)), (.9, math.nextafter(1., 0.))),
                       ((.25, 5e-324), (.75, 5e-324)), ((.1, .7), (.9, .3))):
            with self.subTest(truths=truths):
                case = make_case("numeric", "F05", "boundary", [context(), evidence(1, truth=truths[0]),
                    evidence(1, root="s1", truth=truths[1]), independence(1, 2), revise(1, 2)])
                run_case(initial(), case)

    def test_duplicate_proof_aliases_cannot_forge_an_independence_pair(self):
        case = make_case("alias", "F05", "blocked", [context(), evidence(1, truth=(.25, .5)),
            evidence(1, root="s1", truth=(.75, .5)), independence(1, 2), revise(1, 2), revise(2, 1), independence(4, 5, model="m1")])
        self.assertEqual(run_case(initial(), case)[-1]["outcome"]["status"], "FAIL")

    def test_oracle_is_cold_does_not_mutate_inputs_and_has_no_runtime_imports(self):
        tree = ast.parse((ROOT / "validation_lab" / "admission_oracle.py").read_text())
        imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        self.assertEqual(set(imports), {"copy", "fractions"})
        self.assertFalse(any(isinstance(n, ast.Import) for n in ast.walk(tree)))
        config, events = initial().wire(), scenarios()[13]["events"]
        saved = deepcopy((config, events))
        first = reference_prefix(config, events)
        first["projection"].clear()
        self.assertTrue(reference_prefix(config, events)["projection"])
        self.assertEqual((config, events), saved)
        with self.assertRaises(OracleGap):
            reference_prefix(config, [dict(schema="admission-event/v1", event_id="x", kind="future", arguments={})])

    def test_corpus_is_reproducible_with_four_explicit_controls_per_scoped_family(self):
        config, cases = load_cases()
        self.assertEqual(config, initial())
        self.assertEqual(cases, scenarios())
        receipt = verify_corpus()
        self.assertEqual(set(receipt["control_coverage"]), {"F01", "F02", "F04", "F05"})
        for controls in receipt["control_coverage"].values():
            self.assertEqual(set(controls), {"positive", "blocked", "boundary", "revision_change"})
        self.assertEqual(receipt["family_complete_fixtures"], 0)

    def test_receipts_reject_unlisted_cases_and_source_drift(self):
        receipt = verify_corpus()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in (*receipt["fixture_files"], *receipt["source_files"], "validation_lab/admission_cases/manifest.json"):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            with patch("validation_lab.run_deployment.ROOT", root), patch("validation_lab.run_admission.CORPUS", root / "validation_lab/admission_cases"):
                verify_corpus()
                extra = root / "validation_lab/admission_cases/evaluator/unlisted.json"
                extra.write_text("{}")
                with self.assertRaisesRegex(ValueError, "unlisted"):
                    verify_corpus()
                extra.unlink()
                oracle = root / "validation_lab/admission_oracle.py"
                oracle.write_text(oracle.read_text()+"\n# drift\n")
                with self.assertRaisesRegex(ValueError, "receipt mismatch"):
                    verify_corpus()

    def test_stream_worker_exchanges_one_current_event_at_a_time(self):
        config, messages = initial(), scenarios()[13]["events"][:5]
        with TemporaryDirectory() as directory:
            process = subprocess.Popen([sys.executable, "-m", "reachability.admission_trace", "--database-dir", directory],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            try:
                def exchange(message):
                    process.stdin.write(canonical(message)+"\n")
                    process.stdin.flush()
                    self.assertTrue(select.select([process.stdout], [], [], 15)[0], "runtime response timed out")
                    return json.loads(process.stdout.readline())
                self.assertEqual(exchange(config.wire())["projection"], reference_prefix(config.wire(), ())["projection"])
                for index, message in enumerate(messages):
                    self.assertEqual(exchange(message)["projection"], reference_prefix(config.wire(), messages[:index+1])["projection"])
                process.stdin.close()
                self.assertEqual(process.wait(timeout=15), 0, process.stderr.read())
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=5)
                for stream in (process.stdin, process.stdout, process.stderr):
                    stream.close()


class AdmissionProtocolTests(unittest.TestCase):
    def test_nested_public_arguments_and_initial_rules_are_immutable(self):
        raw = initial().wire()
        config = AdmissionInitial.parse(raw)
        raw["rules"][0]["premises"].clear()
        self.assertEqual(config.wire()["rules"][0]["premises"], [1, 2])
        raw = event("x", "derive", context_id="c0", rule_id="r0", premises=["a", "b"])
        parsed = AdmissionEvent.parse(raw)
        raw["arguments"]["premises"].clear()
        parsed.arguments["premises"].clear()
        self.assertEqual(parsed.arguments["premises"], ["a", "b"])

    def test_hidden_fields_and_invalid_literals_numbers_are_rejected(self):
        base = event("x", "estimate", context_id="c0", literal=1, roots=["s"], valid_until=None, strength=.5, confidence=.5)
        for field, value in (("expected", "PASS"), ("literal", 0), ("literal", True), ("literal", 9),
                             ("confidence", 1.), ("strength", float("nan")), ("strength", True), ("roots", []),
                             ("valid_until", -1), ("roots", "source")):
            raw = deepcopy(base)
            raw["arguments"][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                AdmissionEvent.parse(raw)
        raw = initial().wire()
        raw["expected"] = "PASS"
        with self.assertRaises(ValueError):
            AdmissionInitial.parse(raw)

    def test_duplicate_events_trace_limits_and_declared_atom_scope(self):
        with TemporaryDirectory() as directory, AdmissionSession(initial(), directory) as session:
            session.apply(event("open", "context", context_id="c0", assumptions=[], clauses=[]))
            with self.assertRaises(ValueError):
                session.apply(event("open", "restart"))
            with self.assertRaises(ValueError):
                session.apply(event("outside", "evidence", context_id="c0", literal=5, roots=["s"], valid_until=None))
            for index in range(1, 4):
                session.apply(event(str(index), "context", context_id="c"+str(index), assumptions=[], clauses=[]))
            with self.assertRaises(ValueError):
                session.apply(event("fifth", "context", context_id="c4", assumptions=[], clauses=[]))
            for index in range(4, 128):
                session.apply(event(str(index), "tick", context_id="c0", time=0))
            with self.assertRaises(ValueError):
                session.apply(event("last", "restart"))
