import ast
from copy import deepcopy
from dataclasses import asdict, replace
import json
from pathlib import Path
import select
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from reachability.deployment_trace import DeploymentSession
from reachability.trace_protocol import DeploymentInitial, DeploymentEvent, canonical, event, fingerprint, read_json
from validation_lab.deployment_oracle import OracleGap, reference_prefix
from validation_lab.generate_deployment_cases import generated_scenarios, scenarios
from validation_lab.mutations import mutate
from validation_lab.run_deployment import ConformanceMismatch, load_cases, mutation_witness, run_case, verify_corpus

ROOT = Path(__file__).resolve().parents[1]


class DeploymentTraceTests(unittest.TestCase):
    def test_all_fixed_cases_match_every_cold_and_recovered_prefix(self):
        initial, cases = load_cases()
        manifest = verify_corpus()
        prefixes = 0
        for case in cases:
            with self.subTest(case=case["case_id"]):
                records = run_case(initial, case)
                prefixes += len(records)
                for record, message in zip(records, case["events"]):
                    self.assertEqual(record["event_digest"], fingerprint(message))
                    self.assertEqual(record["schema"], "deployment-trace/v1")
                    self.assertGreaterEqual(record["diagnostics"]["elapsed_ns"], 0)
        self.assertEqual(prefixes, manifest["event_prefixes"])
        self.assertEqual(prefixes, 137)

    def test_seeded_stateful_cases_have_no_filtered_outcomes(self):
        cases = generated_scenarios()
        self.assertEqual(cases, generated_scenarios())
        self.assertEqual(len(cases), 12)
        for case in cases:
            with self.subTest(case=case["case_id"]):
                run_case(DeploymentInitial(), case)

    def test_M06_acknowledgement_is_not_observed_durable_success(self):
        initial, cases = load_cases()
        case = next(c for c in cases if c["case_id"] == "d01")
        run_case(initial, case, restart_every_prefix=False)
        result = mutation_witness(initial, case, "M06")
        self.assertTrue(result["detected"])
        self.assertEqual(result["first_divergent_prefix"], 7)
        self.assertEqual(result["path"], "projection.goal.label")
        self.assertGreater(result["invocations"], 0)

    def test_M11_censored_observation_is_not_observed_failure(self):
        initial, cases = load_cases()
        case = next(c for c in cases if c["case_id"] == "d07")
        run_case(initial, case, restart_every_prefix=False)
        result = mutation_witness(initial, case, "M11")
        self.assertTrue(result["detected"])
        self.assertEqual(result["first_divergent_prefix"], 3)
        self.assertEqual((result["expected"], result["actual"]), ("CENSORED", "OBSERVED_FAILURE"))

    def test_logger_preserves_mutant_output_before_any_oracle_comparison(self):
        initial, cases = load_cases()
        with TemporaryDirectory() as directory:
            path = Path(directory) / "actual.jsonl"
            with mutate("M06"), self.assertRaises(ConformanceMismatch):
                run_case(initial, cases[0], restart_every_prefix=False, trace_path=path)
            records = [json.loads(line) for line in path.read_text().splitlines()]
        self.assertEqual(len(records), 7)
        self.assertEqual(records[-1]["projection"]["goal"]["outstanding"], 0)
        self.assertEqual(records[-1]["projection"]["goal"]["label"], "OBSERVED_SUCCESS")
        self.assertEqual(records[-1]["projection_digest"], fingerprint(records[-1]["projection"]))

    def test_renamed_inputs_preserve_semantics_and_ancestry(self):
        initial, cases = load_cases()
        original = cases[0]
        changed = deepcopy(original)
        mapping = {"p0": "object-42", "c0": "context-42", "g0": "goal-42", "a0": "attempt-42"}
        mapping.update({e["event_id"]: "r-"+e["event_id"] for e in original["events"]})
        def renamed(value, names):
            if isinstance(value, dict):
                return {names.get(k, k): renamed(v, names) for k, v in value.items()}
            if isinstance(value, list):
                return [renamed(v, names) for v in value]
            return names.get(value, value) if isinstance(value, str) else value
        changed["events"] = renamed(changed["events"], mapping)
        changed["checkpoints"] = []
        public = replace(initial, context_id=mapping["c0"], product_id=mapping["p0"], goal_id=mapping["g0"])
        before = run_case(initial, original, restart_every_prefix=False)
        after = run_case(public, changed, restart_every_prefix=False)
        self.assertEqual(changed["parent_instance_id"], original["parent_instance_id"])
        self.assertEqual([r["projection"] for r in before],
                         renamed([r["projection"] for r in after], {v: k for k, v in mapping.items()}))

    def test_independent_initial_observations_commute_without_changing_later_results(self):
        initial, cases = load_cases()
        original = cases[2]
        changed = deepcopy(original)
        changed["events"][:3] = reversed(changed["events"][:3])
        changed["checkpoints"] = []
        before = run_case(initial, original, restart_every_prefix=False)
        after = run_case(initial, changed, restart_every_prefix=False)
        self.assertEqual([r["projection"] for r in before[2:]], [r["projection"] for r in after[2:]])

    def test_rejected_composite_event_preserves_its_earlier_admitted_evidence(self):
        messages = [event("e0", "observation", attempt_id="absent", milestone="exact_product_observed", product_id="p0"),
                    event("e1", "fact", name="product", valid_until=None), event("e2", "sample", healthy=True),
                    event("e3", "sample", healthy=False), event("e4", "revoke", evidence_id="e2"),
                    event("e5", "sample", healthy=False)]
        records = run_case(DeploymentInitial(), dict(events=messages))
        self.assertEqual(records[0]["outcome"]["status"], "FAIL")
        self.assertIn("e0", records[0]["projection"]["hard"])
        self.assertEqual(records[3]["outcome"]["status"], "FAIL")
        self.assertNotIn("e3", records[3]["projection"]["hard"])
        self.assertEqual(records[-1]["projection"]["goal"]["label"], "OBSERVED_FAILURE")

    def test_release_fences_a_prepared_request_that_never_reached_the_executor(self):
        messages = scenarios()[0]["events"][:5]
        messages += [event("m0", "prepare", attempt_id="a0"), event("m1", "release", attempt_id="a0"),
                     event("m2", "dispatch", attempt_id="a0", fault="none")]
        records = run_case(DeploymentInitial(), dict(events=messages))
        self.assertEqual(records[-1]["instrumentation"]["executor_effects"], 0)
        self.assertEqual(records[-1]["projection"]["attempts"]["a0"]["dispatch"]["state"], "released")

    def test_declared_capacity_and_lease_boundary_are_not_hardcoded_to_one_slot(self):
        messages = scenarios()[2]["events"][:5]
        messages += [event("m0", "attempt", attempt_id="a1"), event("m1", "reserve", attempt_id="a1"),
                     event("m2", "attempt", attempt_id="a2"), event("m3", "reserve", attempt_id="a2"),
                     event("m4", "tick", time=3), event("m5", "reserve", attempt_id="a2")]
        records = run_case(DeploymentInitial(capacity=2, lease_duration=3), dict(events=messages))
        self.assertEqual(records[6]["projection"]["resource"]["used"], 2)
        self.assertEqual(records[8]["outcome"]["status"], "FAIL")
        self.assertEqual(records[-1]["outcome"]["status"], "PASS")
        self.assertEqual(records[-1]["projection"]["resource"]["used"], 1)

    def test_corpus_is_reproducible_development_data_with_no_family_complete_claim(self):
        _, cases = load_cases()
        self.assertEqual(cases, scenarios())
        self.assertEqual({c["split"] for c in cases}, {"development"})
        self.assertEqual({c["parent_instance_id"] for c in cases}, {"deployment-parent-0"})
        for case in cases:
            self.assertTrue(all(1 <= check["step"] <= len(case["events"]) for check in case["checkpoints"]))
        self.assertEqual(verify_corpus()["family_complete_fixtures"], 0)

    def test_unlisted_fixture_or_modified_oracle_cannot_escape_corpus_verification(self):
        receipt = verify_corpus()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in (*receipt["fixture_files"], *receipt["source_files"], "validation_lab/deployment_cases/manifest.json"):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            corpus = root / "validation_lab" / "deployment_cases"
            with patch("validation_lab.run_deployment.ROOT", root), patch("validation_lab.run_deployment.CORPUS", corpus):
                verify_corpus()
                extra = corpus / "evaluator" / "unlisted.json"
                extra.write_text('{}')
                with self.assertRaisesRegex(ValueError, "unlisted"):
                    verify_corpus()
                extra.unlink()
                oracle = root / "validation_lab" / "deployment_oracle.py"
                oracle.write_text(oracle.read_text() + '\n# drift\n')
                with self.assertRaisesRegex(ValueError, "receipt mismatch"):
                    verify_corpus()

    def test_oracle_has_no_runtime_or_driver_imports(self):
        tree = ast.parse((ROOT / "validation_lab" / "deployment_oracle.py").read_text())
        modules = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                modules.append(node.module)
        self.assertEqual(set(modules), {"copy", "json"})

    def test_reference_scope_gaps_are_errors_not_epistemic_unknown(self):
        with self.assertRaises(OracleGap):
            reference_prefix(asdict(DeploymentInitial()), [dict(schema="future", event_id="e0")])
        bad = dict(schema="deployment-event/v1", event_id="e0", kind="unsupported", arguments={})
        with self.assertRaises(OracleGap):
            reference_prefix(asdict(DeploymentInitial()), [bad])

    def test_worker_accepts_only_the_current_public_message(self):
        initial = DeploymentInitial()
        messages = scenarios()[0]["events"][:5]
        with TemporaryDirectory() as directory:
            process = subprocess.Popen([sys.executable, "-m", "reachability.deployment_trace", "--database-dir", directory],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            try:
                def exchange(message):
                    process.stdin.write(canonical(message) + "\n")
                    process.stdin.flush()
                    self.assertTrue(select.select([process.stdout], [], [], 15)[0], "runtime response timed out")
                    return json.loads(process.stdout.readline())
                first = exchange(asdict(initial))
                self.assertEqual(first["initial"], reference_prefix(asdict(initial), ())["projection"])
                for index, message in enumerate(messages):
                    actual = exchange(message)
                    expected = reference_prefix(asdict(initial), messages[:index+1])
                    self.assertEqual(actual["projection"], expected["projection"])
                    self.assertNotIn("checkpoints", actual)
                    self.assertNotIn("controls", actual)
                process.stdin.close()
                self.assertEqual(process.wait(timeout=15), 0, process.stderr.read())
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=5)
                for stream in (process.stdin, process.stdout, process.stderr):
                    stream.close()


class DeploymentProtocolTests(unittest.TestCase):
    def test_hidden_schedules_and_expected_outputs_cannot_be_public_arguments(self):
        message = event("e0", "tick", time=1)
        for name in ("expected", "events", "checkpoints", "oracle", "future_observations"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                DeploymentEvent.parse(dict(message, **{name: "leak"}))
            changed = deepcopy(message)
            changed["arguments"][name] = "leak"
            with self.assertRaises(ValueError):
                DeploymentEvent.parse(changed)
            with self.assertRaises(ValueError):
                DeploymentInitial.parse(dict(asdict(DeploymentInitial()), **{name: "leak"}))

    def test_nonfinite_boolean_numeric_and_malformed_messages_are_rejected(self):
        for value in (True, float("nan"), float("inf"), -1, 1.1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                event("e0", "forecast", strength=value, confidence=.8, valid_until=None)
        for value in (True, -1, 1001, .5):
            with self.assertRaises(ValueError):
                event("e0", "tick", time=value)
        for text in ('{"x":1,"x":2}', '{"x": NaN}', '[' * 2, '"' + 'a'*65537 + '"'):
            with self.assertRaises(ValueError):
                read_json(text)
        with self.assertRaises(ValueError):
            event("e0", "sample", healthy=1)

    def test_duplicate_event_identity_and_invalid_time_leave_runtime_unchanged(self):
        with TemporaryDirectory() as directory, DeploymentSession(DeploymentInitial(), directory) as session:
            message = event("e0", "tick", time=2)
            session.apply(message)
            before = session.projection()
            for message in (message, event("e1", "tick", time=1),
                            event("e2", "forecast", strength=.8, confidence=.8, valid_until=2)):
                with self.assertRaises(ValueError):
                    session.apply(message)
                self.assertEqual(session.projection(), before)

    def test_invalid_new_run_cannot_reuse_an_existing_authority_directory(self):
        with TemporaryDirectory() as directory:
            with DeploymentSession(DeploymentInitial(), directory):
                pass
            with self.assertRaises(ValueError):
                DeploymentSession(DeploymentInitial(), directory)
