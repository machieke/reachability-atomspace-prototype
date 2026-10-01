import ast
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from reachability.admission_protocol import AdmissionInitial
from reachability.grounded_planning import GroundedController, Plan, PlanningPublic, RuleCost, SearchBudget, search
from reachability.planning_session import PlanningSession
from reachability.trace_protocol import canonical, fingerprint
from validation_lab.generate_planning_cases import generated_scenarios, scenarios
from validation_lab.planning_oracle import OracleGap, exact_plan, verify_plan
from validation_lab.run_deployment import ConformanceMismatch
from validation_lab.run_planning import PlanningWorld, load_cases, run_case, verify_corpus

ROOT = Path(__file__).resolve().parents[1]


class GroundedPlanningTests(unittest.TestCase):
    def open_case(self, index=0):
        case = scenarios()[index]
        public = PlanningPublic.parse(case['public']['profile'])
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        session = PlanningSession(public, directory.name)
        self.addCleanup(session.close)
        for message in case['public']['events']:
            session.observe(message)
        return public, session

    def test_fixed_whole_plans_and_closed_loop_prefixes_match_independent_references(self):
        verify_corpus()
        results = [run_case(c) for c in load_cases()]
        self.assertEqual(sum(r['compared_prefixes'] for r in results), 77)
        self.assertEqual(sum(r['completed'] for r in results), 11)
        for result in results:
            self.assertEqual(result['compared_prefixes'], result['recovered_prefixes'])

    def test_seeded_graphs_are_reproducible_unfiltered_and_realize_frozen_optima(self):
        cases = generated_scenarios()
        self.assertEqual(cases, generated_scenarios())
        for case in cases:
            with self.subTest(case=case['case_id']):
                result = run_case(case)
                self.assertEqual(result['compared_prefixes'], result['recovered_prefixes'])
                self.assertNotEqual(result['stop_reason'], 'BUDGET_EXHAUSTED')

    def test_shared_subproof_is_charged_once_and_symbolic_references_are_ordered(self):
        public, session = self.open_case(1)
        plan = search(public, session.read())['plan']
        self.assertEqual(plan.work, 3)
        self.assertEqual(plan.steps[1]['premises'], [{'kind': 'step', 'index': 0}])
        self.assertEqual(plan.steps[2]['premises'], [{'kind': 'step', 'index': 0}])
        self.assertEqual(verify_plan(public.wire(), session.read(), plan.wire()), [3, 2, 3])

    def test_whole_alternatives_cannot_mix_one_paths_cost_with_anothers_duration(self):
        results = [run_case(scenarios()[i]) for i in (4, 5, 6, 21)]
        self.assertEqual([r['first_objective'] for r in results], [None, [5, 1, 1], [1, 5, 1], None])
        self.assertEqual(results[1]['records'][0]['plan']['steps'][0]['rule_id'], 'r0')
        self.assertEqual(results[2]['records'][0]['plan']['steps'][0]['rule_id'], 'r1')

    def test_wait_can_end_before_blocker_expiry_when_derivation_itself_takes_time(self):
        result = run_case(scenarios()[8])
        steps = result['records'][0]['plan']['steps']
        self.assertEqual([(s['kind'], s['finishes_at']) for s in steps], [('wait', 1), ('derive', 3)])
        self.assertEqual(result['spent'], 1)
        self.assertEqual(result['final_time'], 3)

    def test_revocation_and_rule_replacement_discard_old_plan_without_charge(self):
        for i in (13, 14):
            result = run_case(scenarios()[i])
            first, second = result['records'][:2]
            self.assertEqual(first['receipt'], dict(status='STALE', work_charged=0, public_events=0))
            self.assertEqual(second['receipt']['status'], 'PASS')
            self.assertNotEqual(first['plan']['snapshot_digest'], second['plan']['snapshot_digest'])
            self.assertEqual(result['spent'], 1)
        self.assertEqual(second['plan']['steps'][0]['rule_revision'], '2')
        self.assertEqual(second['plan']['steps'][0]['premises'], [{'kind': 'belief', 'reference': 'e2'}])

    def test_policy_edit_invalidates_selection_and_replans_unreachable(self):
        result = run_case(scenarios()[15])
        self.assertEqual([r['status'] for r in result['records']], ['SOLVED', 'UNREACHABLE'])
        self.assertEqual(result['spent'], 0)
        self.assertFalse(result['completed'])

    def test_expiry_uses_exact_long_enough_parent_and_preserves_all_public_alternatives(self):
        public, session = self.open_case(18)
        before = session.read()
        self.assertEqual([s['valid_until'] for s in before['supports']], [1, 4])
        plan = search(public, before)['plan']
        self.assertEqual(plan.steps[0]['premises'], [{'kind': 'belief', 'reference': 'e2'}])
        self.assertEqual(session.read(), before)
        result = GroundedController(public).run(session)
        self.assertEqual(result['stop_reason'], 'OBSERVED_GOALS')
        self.assertEqual({s['valid_until'] for s in session.read()['supports']}, {4})

    def test_search_budget_exhaustion_never_executes_partial_plan(self):
        for budget in (SearchBudget(states=0), SearchBudget(transitions=0), SearchBudget(states=1, transitions=100)):
            public, session = self.open_case()
            before = session.read()
            result = GroundedController(public).run(session, search_budget=budget)
            self.assertEqual(result['stop_reason'], 'BUDGET_EXHAUSTED')
            self.assertIsNone(result['records'][0]['plan'])
            self.assertEqual(session.read(), before)
            self.assertLessEqual(result['records'][0]['search_work']['states'], budget.states)
            self.assertLessEqual(result['records'][0]['search_work']['transitions'], budget.transitions)

    def test_reference_exhaustion_never_claims_an_optimum_even_with_incumbent(self):
        public, session = self.open_case(19)
        self.assertEqual(exact_plan(public.wire(), session.read(), state_limit=0)['status'], 'NOT_COMPUTED')
        public, session = self.open_case()
        result = exact_plan(public.wire(), session.read(), transition_limit=0)
        self.assertEqual((result['status'], result['objective']), ('NOT_COMPUTED', None))
        with self.assertRaises(OracleGap):
            exact_plan(public.wire(), session.read(), state_limit=True)

    def test_forged_premises_are_checked_by_actual_authority_and_work_is_charged(self):
        public, session = self.open_case()
        good = search(public, session.read())['plan']
        steps = good.steps
        steps[0]['premises'].reverse()
        receipt = session.execute(replace(good, steps_json=canonical(steps)))
        self.assertEqual(receipt['status'], 'FAIL')
        self.assertEqual(receipt['work_charged'], 1)
        self.assertNotIn(3, {s['literal'] for s in session.read()['supports']})
        self.assertEqual(session.steps, 1)

    def test_stale_digest_and_wrong_rule_revision_cannot_issue_commands(self):
        public, session = self.open_case()
        plan = search(public, session.read())['plan']
        before = session.read()
        altered = plan.steps
        altered[0]['rule_revision'] = 'unregistered'
        for bad in (replace(plan, snapshot_digest='wrong'), replace(plan, steps_json=canonical(altered))):
            self.assertEqual(session.execute(bad)['status'], 'STALE')
            self.assertEqual(session.read(), before)

    def test_cost_time_and_malformed_parent_contracts_fail_before_charge(self):
        public, session = self.open_case()
        plan = search(public, session.read())['plan']
        before = session.read()
        for field, value in [('work', 0), ('work', True), ('finishes_at', 2), ('premises', [{'kind': 'step', 'index': 0}]),
                             ('premises', [{'kind': 'belief', 'reference': []}])]:
            steps = plan.steps
            steps[0][field] = value
            with self.assertRaises(ValueError):
                session.execute(replace(plan, steps_json=canonical(steps)))
            self.assertEqual(session.read(), before)

    def test_full_witness_checker_detects_invalid_later_step_despite_correct_objective(self):
        public, session = self.open_case()
        wire = search(public, session.read())['plan'].wire()
        wire['steps'][1]['premises'][0]['index'] = 7
        with self.assertRaisesRegex(OracleGap, 'absent'):
            verify_plan(public.wire(), session.read(), wire)

    def test_public_port_has_no_future_hooks_and_returns_detached_state(self):
        public, session = self.open_case()
        world = PlanningWorld(session, scenarios()[13]['hooks'])
        port = world.port()
        self.assertFalse(hasattr(port, 'hooks'))
        self.assertFalse(hasattr(port, 'session'))
        read = port.read()
        read['rules'][0]['premises'].clear()
        read['supports'].clear()
        self.assertEqual(session.read(), world.snapshot)
        detached = session.read()
        detached['rules'][0]['premises'].clear()
        self.assertTrue(session.read()['rules'][0]['premises'])

    def test_public_constructor_detaches_nested_admission_inputs(self):
        public, _ = self.open_case()
        atoms = list(public.admission.atoms)
        public = replace(public, admission=AdmissionInitial(atoms, public.admission.rules_json))
        before = public.wire()
        atoms.clear()
        self.assertEqual(public.wire(), before)
        self.assertIs(type(public.admission.atoms), tuple)

    def test_controller_and_session_recovery_between_requests_preserves_event_stream(self):
        case = scenarios()[1]
        expected = run_case(case)
        public, session = self.open_case(1)
        actual = []
        session.emit = lambda message, record: actual.append(message)
        for _ in range(8):
            result = GroundedController(public).run(session, requests=1)
            session.restart()
            if result['stop_reason'] == 'OBSERVED_GOALS':
                break
        self.assertEqual(result['stop_reason'], 'OBSERVED_GOALS')
        self.assertEqual(actual, expected['events'][len(case['public']['events']):])
        self.assertEqual(session.spent, expected['spent'])

    def test_rejecting_all_work_fails_the_positive_control(self):
        class Idle(GroundedController):
            def run(self, port, **kwargs):
                return super().run(port, requests=0, **kwargs)
        with self.assertRaisesRegex(ConformanceMismatch, 'completed'):
            run_case(scenarios()[0], controller_factory=Idle)

    def test_proposals_are_logged_before_reference_rejection(self):
        def reject(*args, **kwargs):
            raise OracleGap('injected reference failure')
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'actual.jsonl'
            with patch('validation_lab.run_planning.exact_plan', reject), self.assertRaises(OracleGap):
                run_case(scenarios()[0], trace_path=path)
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual(rows[-1]['actual']['schema'], 'grounded-controller-step/v1')
            self.assertEqual(rows[-1]['actual']['plan']['work'], 3)

    def test_strict_profile_and_snapshot_protocols_reject_hidden_and_invalid_fields(self):
        public, session = self.open_case()
        for key in ('world', 'future', 'expected'):
            raw = public.wire()
            raw[key] = {}
            with self.assertRaises(ValueError):
                PlanningPublic.parse(raw)
            snapshot = session.read()
            snapshot[key] = {}
            with self.assertRaises(ValueError):
                search(public, snapshot)
        for changes in (dict(work_budget=True), dict(max_steps=9), dict(goals=(0,)), dict(costs=())):
            with self.assertRaises(ValueError):
                replace(public, **changes)
        for changes in (dict(work=0), dict(duration=True), dict(duration=9)):
            with self.assertRaises(ValueError):
                replace(public.costs[0], **changes)
        with self.assertRaises(ValueError):
            SearchBudget(states=-1)
        for mutate in (lambda s: s['supports'].append(dict(s['supports'][0])),
                       lambda s: s['supports'][0].update(valid_until=0),
                       lambda s: s.update(public_digest='other')):
            snapshot = session.read()
            mutate(snapshot)
            with self.assertRaises(ValueError):
                search(public, snapshot)

    def test_oracle_and_runtime_import_boundaries(self):
        for name in ('grounded_planning', 'planning_session'):
            tree = ast.parse((ROOT / f'reachability/{name}.py').read_text())
            modules = [n.module or '' for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
            self.assertFalse(any('validation_lab' in m for m in modules))
        tree = ast.parse((ROOT / 'validation_lab/planning_oracle.py').read_text())
        self.assertEqual({n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}, {'itertools'})
        self.assertFalse(any(isinstance(n, ast.Import) for n in ast.walk(tree)))

    def test_corpus_reproducibility_and_receipt_drift_detection(self):
        self.assertEqual(load_cases(), scenarios())
        receipt = verify_corpus()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for name in (*receipt['fixture_files'], *receipt['source_files'], 'validation_lab/planning_cases/manifest.json'):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, path)
            with patch('validation_lab.run_planning.ROOT', root), patch('validation_lab.run_planning.CORPUS', root / 'validation_lab/planning_cases'):
                verify_corpus()
                source = root / 'reachability/grounded_planning.py'
                source.write_text(source.read_text()+'\n# drift\n')
                with self.assertRaisesRegex(ValueError, 'receipt mismatch'):
                    verify_corpus()
