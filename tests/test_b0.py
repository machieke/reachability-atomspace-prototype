import ast
from copy import deepcopy
from dataclasses import asdict, replace
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from reachability.b0 import B0Controller, B0Public, Budget, Probe, enumerate_candidates
from reachability.deployment_trace import DeploymentSession
from validation_lab.b0_environment import DeploymentWorld
from validation_lab.generate_b0_cases import generated_scenarios, minimal_product_case, scenarios, world
from validation_lab.run_b0 import load_cases, mutation_witness, run_case, verify_corpus
from validation_lab import run_deployment

ROOT = Path(__file__).resolve().parents[1]


class B0Tests(unittest.TestCase):
    def test_fixed_closed_loop_episodes_match_every_cold_and_recovered_prefix(self):
        verify_corpus()
        results = []
        for case in load_cases():
            with self.subTest(case=case["case_id"]):
                result = run_case(case)
                results.append(result)
                self.assertEqual(result["compared_prefixes"], result["recovered_prefixes"])
                self.assertLessEqual(result["work"]["actions"], case["budget"]["actions"])
        self.assertEqual(sum(r["compared_prefixes"] for r in results), 197)
        self.assertEqual(sum(r["completed"] for r in results), 9)
        self.assertEqual(results[9]["stop_reason"], "observation_budget")
        self.assertEqual(results[10]["stop_reason"], "candidate_budget")

    def test_seeded_worlds_are_not_filtered_by_outcome(self):
        cases = generated_scenarios()
        self.assertEqual(cases, generated_scenarios())
        for case in cases:
            with self.subTest(case=case["case_id"]):
                result = run_case(case)
                self.assertTrue(result["completed"])
                self.assertEqual(result["compared_prefixes"], result["recovered_prefixes"])

    def test_frontier_is_read_only_dependency_aware_and_cost_ordered(self):
        public = replace(B0Public(), probes=(Probe("z", "tested", 1), Probe("a", "credential", 4), Probe("b", "forecast", 2)))
        with TemporaryDirectory() as directory, DeploymentSession(public.deployment, directory) as session:
            before = session.service.snapshot("c0")
            projection = session.projection()
            frontier = enumerate_candidates(public, projection)
            self.assertEqual(frontier.visits, 4)
            self.assertEqual([dict(c.arguments).get("probe_id") for c in frontier.candidates], ["z", "b", "a", None])
            self.assertNotIn("dispatch", [c.kind for c in frontier.candidates])
            self.assertEqual(session.service.snapshot("c0"), before)
            self.assertEqual(enumerate_candidates(replace(public, probes=tuple(reversed(public.probes))), projection), frontier)

    def test_incomplete_candidate_enumeration_never_selects_its_partial_frontier(self):
        case = scenarios()[10]
        result = run_case(case)
        self.assertEqual(result["events"], [])
        self.assertEqual(result["work"]["candidate_visits"], 2)
        self.assertEqual(result["work"]["candidates_returned"], 0)

    def test_zero_action_or_enumeration_budget_has_no_issued_commands(self):
        for budget in (Budget(actions=0), Budget(enumerations=0), Budget(candidate_visits=0)):
            public = B0Public()
            with TemporaryDirectory() as directory, DeploymentSession(public.deployment, directory) as session:
                env = DeploymentWorld(session, public, world())
                result = B0Controller(public).run_budget(env.port(), budget)
                self.assertEqual(env.records, [])
                self.assertEqual(result["work"]["actions"], 0)

    def test_unavailable_cheap_probe_does_not_starve_a_costlier_alternative(self):
        result = run_case(scenarios()[1])
        probes = [r["selected"]["arguments"]["probe_id"] for r in result["records"] if r["selected"]["kind"] == "observe"]
        self.assertEqual(probes[:4], ["q0", "q1", "q2", "q5"])
        first = result["records"][0]
        self.assertEqual(first["receipt"]["status"], "UNKNOWN")
        self.assertEqual(first["receipt"]["public_events"], 0)
        self.assertEqual(first["work"]["observation_cost"], 1)
        self.assertTrue(result["completed"])

    def test_lost_reply_reconciles_before_any_new_submission(self):
        result = run_case(scenarios()[3])
        selected = result["selected"]
        self.assertEqual(selected.count("dispatch"), 1)
        self.assertEqual(selected[selected.index("dispatch")+1], "reconcile")
        self.assertEqual(result["effects"], 1)

    def test_failed_delivery_retries_the_same_attempt_after_reconciliation(self):
        result = run_case(scenarios()[4])
        sends = [r["selected"] for r in result["records"] if r["selected"]["kind"] == "dispatch"]
        self.assertEqual(len(sends), 2)
        self.assertEqual(sends[0]["arguments"], sends[1]["arguments"])
        self.assertEqual(result["effects"], 1)

    def test_revocation_between_selection_and_execution_still_blocks_dispatch(self):
        result = run_case(scenarios()[5])
        sends = [r for r in result["records"] if r["selected"]["kind"] == "dispatch"]
        self.assertEqual(sends[0]["receipt"]["status"], "UNKNOWN")
        self.assertEqual(sends[0]["receipt"]["public_events"], 2)  # Revocation and rejected dispatch.
        self.assertEqual(sends[1]["receipt"]["status"], "PASS")
        self.assertNotEqual(sends[0]["selected"]["arguments"], sends[1]["selected"]["arguments"])
        self.assertEqual(result["effects"], 1)

    def test_work_counts_include_empty_rejected_and_composite_requests(self):
        case = scenarios()[6]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "actual.jsonl"
            result = run_case(case, trace_path=path)
            rows = [json.loads(line) for line in path.read_text().splitlines()]
        actual = [r["actual"] for r in rows if r["record_type"] == "runtime"]
        requests = [r["candidate"] for r in rows if r["record_type"] == "request"]
        work = result["work"]
        self.assertEqual(work["actions"], len(requests))
        self.assertEqual(work["public_events"], len(actual))
        self.assertEqual(work["admission_journal_commands"], sum(r["diagnostics"]["journal_commands"] for r in actual))
        self.assertEqual(work["certificates"], sum(len(r["diagnostics"]["certificates"]["$tuple"]) for r in actual))
        costs = {p["probe_id"]: p["cost"] for p in case["public"]["probes"]}
        self.assertEqual(work["observation_cost"], sum(costs[r["arguments"]["probe_id"]] for r in requests if r["kind"] == "observe"))
        self.assertTrue(any(r["outcome"]["status"] == "FAIL" for r in actual))
        self.assertGreater(work["loaded_hard"], 0)

    def test_hidden_observations_are_not_delivered_without_a_selected_probe(self):
        public = B0Public()
        with TemporaryDirectory() as directory, DeploymentSession(public.deployment, directory) as session:
            env = DeploymentWorld(session, public, world())
            self.assertEqual(env.port().read()["hard"], {})
            self.assertEqual(env.port().read()["forecasts"], {})
            self.assertFalse(hasattr(env.port(), "world"))
            controller = B0Controller(public)
            controller.run_budget(env.port(), Budget(actions=1))
            self.assertEqual(len(env.events), 1)
            self.assertEqual(env.events[0]["arguments"]["name"], "tested")
            self.assertEqual(env.port().read()["forecasts"], {})

    def test_rejecting_all_work_cannot_count_as_completion(self):
        class Idle(B0Controller):
            def run_budget(self, port, budget, **kwargs):
                return super().run_budget(port, replace(budget, actions=0), **kwargs)
        with self.assertRaisesRegex(run_deployment.ConformanceMismatch, "completed"):
            run_case(scenarios()[0], controller_factory=Idle)

    def test_checkpoint_and_authority_recovery_preserve_the_selected_action_stream(self):
        case, public = scenarios()[3], B0Public()
        expected = run_case(case)
        with TemporaryDirectory() as directory, DeploymentSession(public.deployment, directory) as session:
            env = DeploymentWorld(session, public, case["world"])
            controller, records = B0Controller(public), []
            for _ in range(32):
                result = controller.run_budget(env.port(), Budget(actions=1))
                records.extend(result["records"])
                controller = B0Controller.restore(public, controller.checkpoint())
                session.restart()
                if result["stop_reason"] == "observed_success":
                    break
            else:
                self.fail("recovered controller did not complete")
            self.assertEqual([r["selected"] for r in records], [r["selected"] for r in expected["records"]])
            self.assertEqual(env.events, expected["events"])

    def test_runtime_has_no_evaluator_import_or_hidden_environment_access(self):
        tree = ast.parse((ROOT / "reachability/b0.py").read_text())
        imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        self.assertEqual(set(imports), {"dataclasses", "time", "trace_protocol"})
        attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "port"}
        self.assertEqual(attrs, {"read", "execute"})

    def test_M07_has_a_passing_control_and_a_deletion_minimal_witness(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "mutant.jsonl"
            witness = mutation_witness(trace_path=path)
            records = [json.loads(line) for line in path.read_text().splitlines()]
        self.assertTrue(witness["detected"])
        self.assertEqual(witness["first_divergent_prefix"], 2)
        self.assertEqual((witness["expected"], witness["actual"]), ("FAIL", "PASS"))
        self.assertGreater(witness["invocations"], 0)
        self.assertEqual(records[-1]["projection"]["attempts"]["a0"]["current"], ["exact_product_observed"])
        case = minimal_product_case()
        for index in range(2):
            shortened = deepcopy(case)
            shortened["events"].pop(index)
            shortened["checkpoints"] = []
            run_deployment.run_case(B0Public().deployment, shortened)
            self.assertFalse(run_deployment.mutation_witness(B0Public().deployment, shortened, "M07")["detected"])

    def test_public_protocol_budgets_and_checkpoints_reject_hidden_or_malformed_fields(self):
        raw = B0Public().wire()
        for field in ("world", "expected", "future"):
            invalid = deepcopy(raw)
            invalid[field] = {}
            with self.assertRaises(ValueError):
                B0Public.parse(invalid)
        for budget in (dict(actions=True), dict(candidate_visits=-1), dict(actions=65), dict(observation_cost=float("inf"))):
            with self.assertRaises(ValueError):
                Budget(**budget)
        invalid = B0Controller(B0Public()).checkpoint()
        invalid["steps"] = 1
        with self.assertRaises(ValueError):
            B0Controller.restore(B0Public(), invalid)
        invalid = B0Controller(B0Public()).checkpoint()
        with self.assertRaises(ValueError):
            B0Controller.restore(replace(B0Public(), max_attempts=1), invalid)

    def test_port_rejects_privileged_instrumentation(self):
        public = B0Public()
        with TemporaryDirectory() as directory, DeploymentSession(public.deployment, directory) as session:
            env = DeploymentWorld(session, public, world())
            port = env.port()
            value = port.read()
            value["executor_effects"] = 1
            with patch.object(port, "read", return_value=value), self.assertRaises(ValueError):
                B0Controller(public).run_budget(port, Budget())
            self.assertEqual(env.events, [])

    def test_corpus_is_reproducible_and_receipts_reject_source_drift(self):
        self.assertEqual(load_cases(), scenarios())
        receipt = verify_corpus()
        self.assertEqual(receipt["family_complete_fixtures"], 0)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in (*receipt["fixture_files"], *receipt["source_files"], "validation_lab/b0_cases/manifest.json"):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            with patch("validation_lab.run_b0.ROOT", root), patch("validation_lab.run_b0.CORPUS", root / "validation_lab/b0_cases"):
                verify_corpus()
                extra = root / "validation_lab/b0_cases/mutations/extra.json"
                extra.write_text("{}")
                with self.assertRaisesRegex(ValueError, "unlisted"):
                    verify_corpus()
                extra.unlink()
                source = root / "reachability/b0.py"
                source.write_text(source.read_text()+"\n# drift\n")
                with self.assertRaisesRegex(ValueError, "receipt mismatch"):
                    verify_corpus()
