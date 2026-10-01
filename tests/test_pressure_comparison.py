"""Same-information scheduling, certified execution, reproducibility and costs."""
import ast
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
from random import Random
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from reachability.model import Clause, Status
from reachability.pressure import PressureLimits, derive
from reachability.pressure_controller import ComparisonBudget, ComparisonController, rank_b3
from reachability.pressure_session import ReasoningSession
from reachability.pressure_work import b0_ranking, build_graph, enumerate_work, validate_public
from reachability.service import AdmissionDenied, AdmissionService
from reachability.trace_protocol import fingerprint
from validation_lab.pressure_episodes import ReasoningWorld, episodes, goal
from validation_lab.run_pressure_comparison import configurations, fairness_audit, run_one, write_comparison


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory(); self.addCleanup(self.directory.cleanup)
        self.case = episodes()[0]
        self.session = ReasoningSession(self.case['public'], self.directory.name)
        self.addCleanup(self.session.close)
        self.world = ReasoningWorld(self.session, self.case)

    def field(self):
        snapshot = self.session.read()
        return derive(snapshot['revisions'], *build_graph(self.session.public, snapshot))

    def test_identical_snapshot_frontier_and_switch_select_different_ranking_paths(self):
        public, snapshot = self.case['public'], self.session.read()
        candidates = enumerate_work(public, snapshot).candidates
        original = deepcopy(snapshot)
        b0, _, complete = b0_ranking(public, snapshot, candidates)
        b3, pressure, _, _ = rank_b3(public, snapshot, candidates, PressureLimits())
        self.assertTrue(complete); self.assertTrue(pressure['converged'])
        selected0 = min(candidates, key=lambda c: b0[c.candidate_id])
        selected3 = min(candidates, key=lambda c: b3[c.candidate_id])
        self.assertEqual(dict(selected0.arguments)['rule_id'], 'detour')
        self.assertEqual(dict(selected3.arguments)['rule_id'], 'shared')
        self.assertEqual(snapshot, original)
        self.assertEqual(candidates, enumerate_work(public, snapshot).candidates)
        for variant, expected in (('B0', 'b0-conditional-plan-best-first'), ('B3', 'b3-typed-pressure-priority-queue')):
            class Port:
                def read(self): return deepcopy(snapshot)
                def execute(self, candidate, binding): return {'status': 'PASS'}
            result = ComparisonController(public, variant).run(Port(), ComparisonBudget(actions=1))
            self.assertEqual(result['records'][0]['ranking_path'], expected)
            self.assertEqual(result['records'][0]['candidates'], [c.wire() for c in candidates])

    def test_b0_whole_branch_plans_need_all_and_premises_and_use_lower_cost_route(self):
        public, snapshot = self.case['public'], self.session.read()
        candidates = enumerate_work(public, snapshot).candidates
        self.assertNotIn('direct-answer', [dict(c.arguments).get('rule_id') for c in candidates])
        self.assertNotIn('alternate-answer', [dict(c.arguments).get('rule_id') for c in candidates])
        ranks, work, complete = b0_ranking(public, snapshot, candidates)
        self.assertTrue(complete)
        self.assertGreater(work['joint_checks'], 0)
        self.assertEqual(dict(min(candidates, key=lambda c:ranks[c.candidate_id]).arguments)['rule_id'], 'detour')
        cheaper = deepcopy(public); cheaper['costs']['direct-answer'] = 1
        cheap_snapshot = deepcopy(snapshot); cheap_snapshot['public_digest'] = fingerprint(cheaper)
        cheap_ranks, _, complete = b0_ranking(cheaper, cheap_snapshot, candidates)
        self.assertTrue(complete)
        self.assertEqual(dict(min(candidates, key=lambda c:cheap_ranks[c.candidate_id]).arguments)['rule_id'], 'shared')
        without_measurement = deepcopy(public); without_measurement['probes'] = without_measurement['probes'][:1]
        reduced = deepcopy(snapshot); reduced['public_digest'] = fingerprint(without_measurement)
        reduced['goals'] = reduced['goals'][:1]
        ranks, _, _ = b0_ranking(without_measurement, reduced, enumerate_work(without_measurement, reduced).candidates)
        self.assertTrue(all(rank[0] == 0 for rank in ranks.values()))

    def test_pressure_priority_cannot_authorize_missing_or_stale_premises(self):
        s = self.session; service = s.service
        s.public['priorities']['answer']['weight'] = 1e6
        pressure = self.field()
        self.assertTrue(pressure['sources'])
        transition = s.call('propose_transition', s.context_id, 'direct-answer', (s.aliases['initial-seed'],))
        pre = s.call('precertify', transition, service.snapshot(s.context_id).knowledge_revision)
        self.assertIsNot(pre.status, Status.PASS)
        with self.assertRaises(AdmissionDenied): service.infer(transition, pre)
        good = s.call('propose_transition', s.context_id, 'shared', (s.aliases['initial-seed'],))
        pre = s.call('precertify', good, service.snapshot(s.context_id).knowledge_revision)
        self.assertIs(pre.status, Status.PASS)
        s.call('revoke_evidence', 'initial-seed')
        self.field()
        with self.assertRaises(AdmissionDenied) as caught: service.infer(good, pre)
        self.assertIs(caught.exception.status, Status.STALE)
        self.assertIsNot(service.query_belief(s.context_id, s.literal(6)).status, Status.PASS)

    def test_unchanged_view_has_no_authority_writes_and_relevant_revisions_change_epoch(self):
        s = self.session
        before = deepcopy({name: getattr(s.service, name) for name in s.service._STATE_FIELDS})
        journal = s.service._journal.entries()
        first = self.field()
        self.assertEqual(self.field(), first)
        self.assertEqual(s.service._journal.entries(), journal)
        self.assertEqual(before, {name: getattr(s.service, name) for name in s.service._STATE_FIELDS})
        s.public['priorities']['answer'].update(revision='priority-v2', weight=3.)
        priority = self.field()
        self.assertNotEqual(priority, first)
        self.assertEqual(s.service._journal.entries(), journal)
        s.tick(1); clock = self.field()
        self.assertNotEqual(clock['epoch'], priority['epoch'])
        s.replace_rule(dict(rule_id='shared', revision='2', premises=[1], conclusion=2))
        rule = self.field(); self.assertNotEqual(rule['epoch'], clock['epoch'])
        state = s.service.snapshot(s.context_id)
        s.call('replace_policy', s.context_id, 'policy-v2', (), state.knowledge_revision)
        policy = self.field(); self.assertNotEqual(policy['epoch'], rule['epoch'])
        s.call('revoke_evidence', 'initial-seed')
        revoked = self.field(); self.assertNotEqual(revoked['epoch'], policy['epoch'])
        self.assertEqual(set(first['sources']), set(revoked['sources']))

    def test_joint_constraints_are_kept_outside_pressure_authority(self):
        s = self.session
        state = s.service.snapshot(s.context_id)
        s.call('replace_policy', s.context_id, 'deny-shared', (Clause((s.literal(-2),)),), state.knowledge_revision)
        snapshot = s.read()
        candidates = enumerate_work(s.public, snapshot).candidates
        self.assertNotIn('shared', [dict(c.arguments).get('rule_id') for c in candidates])
        field = self.field()
        self.assertGreater(field['scores']['rule:shared']['value'], 0)
        self.assertTrue(any('FORBIDDEN_ACTION' in row['reasons'] for row in field['stranded']))
        transition = s.call('propose_transition', s.context_id, 'shared', (s.aliases['initial-seed'],))
        revision = s.service.snapshot(s.context_id).knowledge_revision
        pre = s.call('precertify', transition, revision)
        proposal = s.service.infer(transition, pre)
        post = s.call('postcertify', proposal, pre)
        self.assertEqual(post.status, Status.FAIL)
        self.assertEqual(s.call('commit', proposal, pre, post, revision).status, Status.FAIL)
        self.assertNotIn(2, {x['literal'] for x in s.read()['supports']})

    def test_session_bounds_fail_explicitly_without_hidden_work(self):
        for variant in ('B0', 'B3'):
            for budget, reason in ((ComparisonBudget(wall_ns=0), 'WALL_BUDGET'),
                (ComparisonBudget(candidate_visits=0), 'CANDIDATE_BUDGET'),
                (ComparisonBudget(operation_work=0), 'WORK_BUDGET')):
                with self.subTest(variant=variant, reason=reason):
                    before = self.session.service._journal_sequence
                    result = ComparisonController(self.case['public'], variant).run(self.world.port(), budget)
                    self.assertEqual(result['stop_reason'], reason)
                    self.assertEqual(self.session.service._journal_sequence, before)
            if variant == 'B0':
                budget, reason = ComparisonBudget(ranking_states=0), 'RANKING_BUDGET'
            else:
                budget, reason = ComparisonBudget(pressure_iterations=0), 'PRESSURE_SESSION_BUDGET'
            result = ComparisonController(self.case['public'], variant).run(self.world.port(), budget)
            self.assertEqual(result['stop_reason'], reason)
        result = ComparisonController(self.case['public'], 'B3', limits=PressureLimits(nodes=1)).run(self.world.port())
        self.assertEqual(result['stop_reason'], 'PRESSURE_GRAPH_BUDGET')

    def test_profile_validation_rejects_unsupported_units_or_requirements(self):
        for condition in ({'K_OF_N': [1, 2]}, {'AND': []}, {'OR': [100]}):
            public = deepcopy(self.case['public']); public['goals'][0]['condition'] = condition
            with self.assertRaises(ValueError): validate_public(public)
        public = deepcopy(self.case['public']); public['goals'][0]['unit'] = 'seconds'
        with self.assertRaisesRegex(ValueError, 'conversion'): validate_public(public)

    def test_no_ready_candidate_keeps_stranded_demand_and_its_reason(self):
        self.session.call('revoke_evidence', 'initial-seed')
        self.session.public['probes'] = []
        result = ComparisonController(self.session.public, 'B3').run(self.world.port())
        self.assertEqual(result['stop_reason'], 'BLOCKED')
        self.assertEqual(result['work']['actions'], 0)
        field = result['last_pressure']
        self.assertEqual(sum(s['outstanding_loss'] for s in field['sources'].values()), 4)
        self.assertTrue(all(s['fully_stranded'] for s in field['stranded']))
        self.assertTrue(any('MISSING_CAPABILITY' in s['reasons'] for s in field['stranded']))

    def test_iteration_exhaustion_stays_visible_when_used_as_advisory_rank(self):
        result = ComparisonController(self.case['public'], 'B3', limits=PressureLimits(iterations=1)).run(
            self.world.port(), ComparisonBudget(actions=1))
        self.assertFalse(result['last_pressure']['converged'])
        self.assertTrue(result['last_pressure']['exhausted'])

    def test_runtime_has_no_evaluator_or_hidden_world_imports(self):
        root = Path(__file__).resolve().parents[1]/'reachability'
        for name in ('pressure.py', 'pressure_work.py', 'pressure_controller.py', 'pressure_session.py'):
            tree = ast.parse((root/name).read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    self.assertFalse((node.module or '').startswith(('validation_lab', 'tests')))
        self.assertEqual(set(vars(self.world.port())), set())
        self.assertNotIn('world', self.session.read())


class CandidateSupportTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory(); self.addCleanup(self.directory.cleanup)
        self.session = ReasoningSession(episodes()[1]['public'], self.directory.name)
        self.addCleanup(self.session.close)

    def candidate(self, snapshot=None):
        s = self.session
        return next(c for c in enumerate_work(s.public, snapshot or s.read()).candidates if c.kind == 'derive')

    def parents(self, snapshot=None):
        return json.loads(dict(self.candidate(snapshot).arguments)['premises'])

    def test_no_expiry_precedes_large_finite_expiry_for_both_controllers(self):
        s = self.session
        for i, expiry in enumerate((1000000, 2000000, 10**100)):
            s.observe(1, 'a-finite-'+str(i), valid_until=expiry)
        s.observe(1, 'z-no-expiry')
        snapshot = s.read()
        self.assertEqual(self.parents(snapshot), ['z-no-expiry'])
        candidates = enumerate_work(s.public, snapshot).candidates
        before = s.service._journal.entries()
        for variant in ('B0', 'B3'):
            class Port:
                def read(self): return deepcopy(snapshot)
                def execute(self, candidate, binding): return {'status': 'PASS'}
            result = ComparisonController(s.public, variant).run(Port(), ComparisonBudget(actions=1))
            self.assertEqual(result['records'][0]['candidates'], [c.wire() for c in candidates])
            self.assertEqual(result['records'][0]['selected'], self.candidate(snapshot).wire())
        self.assertEqual(s.service._journal.entries(), before)

    def test_finite_expiry_ordering_preserves_exact_large_integer_times(self):
        s = self.session
        for i, expiry in enumerate((2**53, 10**100)):
            with self.subTest(expiry=expiry):
                s.observe(1, 'a-earlier-'+str(i), valid_until=expiry)
                s.observe(1, 'z-later-'+str(i), valid_until=expiry+1)
                self.assertEqual(self.parents(), ['z-later-'+str(i)])

    def test_equal_expiries_use_alias_order_independent_of_support_order(self):
        s = self.session
        for expiry, suffix in ((2000000, 'finite'), (None, 'open')):
            with self.subTest(expiry=expiry):
                for prefix in ('z-', 'a-'):
                    s.observe(1, prefix+suffix, valid_until=expiry)
                snapshot = s.read()
                reversed_snapshot = deepcopy(snapshot)
                reversed_snapshot['supports'].reverse()
                self.assertEqual(self.parents(snapshot), ['a-'+suffix])
                self.assertEqual(self.candidate(snapshot), self.candidate(reversed_snapshot))

    def test_certified_result_survives_expiry_of_competing_finite_support(self):
        s = self.session
        s.observe(1, 'z-no-expiry')
        s.observe(1, 'a-finite', valid_until=2000000)
        receipt = s.execute(self.candidate(), fingerprint(s.read()))
        self.assertEqual(receipt['status'], 'PASS')
        belief = next(b for b in s.service.snapshot(s.context_id).usable
                      if b.belief_revision_id == receipt['belief'])
        self.assertEqual(belief.proposal.evidence_ids, ('z-no-expiry',))
        s.tick(2000000)
        self.assertIs(s.service.query_belief(s.context_id, s.literal(2)).status, Status.PASS)
        self.assertNotIn('a-finite', [p['reference'] for p in s.read()['supports']])
        self.assertEqual(s.read()['goals'][0]['outstanding'], 1)

    def test_revocation_stales_bound_request_and_certificate_before_finite_fallback(self):
        s = self.session
        s.public['priorities']['answer']['weight'] = 1e6
        s.observe(1, 'z-no-expiry')
        s.observe(1, 'a-finite', valid_until=2000000)
        snapshot, candidate = s.read(), self.candidate()
        self.assertEqual(self.parents(snapshot), ['z-no-expiry'])
        transition = s.call('propose_transition', s.context_id, 'answer',
                            tuple(s.aliases[p] for p in self.parents(snapshot)))
        pre = s.call('precertify', transition, s.service.snapshot(s.context_id).knowledge_revision)
        self.assertIs(pre.status, Status.PASS)
        s.call('revoke_evidence', 'z-no-expiry')
        rank_b3(s.public, s.read(), enumerate_work(s.public, s.read()).candidates, PressureLimits())
        self.assertEqual(s.execute(candidate, fingerprint(snapshot))['status'], 'STALE')
        with self.assertRaises(AdmissionDenied) as caught:
            s.service.infer(transition, pre)
        self.assertIs(caught.exception.status, Status.STALE)
        self.assertIsNot(s.service.query_belief(s.context_id, s.literal(2)).status, Status.PASS)
        self.assertEqual(self.parents(), ['a-finite'])
        self.assertNotEqual(candidate, self.candidate())
        self.assertEqual(s.execute(self.candidate(), fingerprint(s.read()))['status'], 'PASS')
        s.tick(2000000)
        self.assertIsNot(s.service.query_belief(s.context_id, s.literal(2)).status, Status.PASS)

    def test_and_bundle_selects_current_support_for_every_prerequisite(self):
        with TemporaryDirectory() as directory, ReasoningSession(episodes()[0]['public'], directory) as s:
            s.observe(1, 'seed')
            def frontier():
                return {dict(c.arguments)['rule_id']: c for c in enumerate_work(s.public, s.read()).candidates
                        if c.kind == 'derive'}
            self.assertNotIn('direct-answer', frontier())
            self.assertEqual(s.execute(frontier()['shared'], fingerprint(s.read()))['status'], 'PASS')
            self.assertNotIn('direct-answer', frontier())
            s.observe(3, 'a-finite-measurement', valid_until=2000000)
            s.observe(3, 'z-open-measurement')
            candidate = frontier()['direct-answer']
            parents = json.loads(dict(candidate.arguments)['premises'])
            supports = {p['reference']: p['literal'] for p in s.read()['supports']}
            self.assertEqual([supports[p] for p in parents], [2, 3])
            self.assertEqual(parents[1], 'z-open-measurement')
            receipt = s.execute(candidate, fingerprint(s.read()))
            self.assertEqual(receipt['status'], 'PASS')
            belief = next(b for b in s.service.snapshot(s.context_id).usable
                          if b.belief_revision_id == receipt['belief'])
            self.assertEqual(set(belief.proposal.evidence_ids), {'seed', 'z-open-measurement'})


class ComparisonCostTests(unittest.TestCase):
    def set_cost(self, public, kind, cost):
        if kind == 'derive':
            public['costs']['answer'] = cost
        else:
            public['probes'][0]['cost'] = cost

    def case(self, rule_cost, probe_cost):
        case = deepcopy(episodes()[1])
        case['world']['initial'] = []
        self.set_cost(case['public'], 'derive', rule_cost)
        self.set_cost(case['public'], 'observe', probe_cost)
        return case

    def test_costs_require_exact_bounded_integers_for_rules_and_probes(self):
        for kind in ('derive', 'observe'):
            for cost in (-1, 0, 101, 10**400, True, False, 1.0, 1.5, 100.0,
                         float('nan'), float('inf'), None, '1'):
                with self.subTest(kind=kind, cost=cost):
                    public = deepcopy(episodes()[1]['public'])
                    self.set_cost(public, kind, cost)
                    with self.assertRaisesRegex(ValueError, 'integer.*1.*100'):
                        validate_public(public)

    def test_unsupported_costs_are_rejected_before_authority_creation(self):
        for kind in ('derive', 'observe'):
            for cost in (1.5, 1.0, 10**400):
                with self.subTest(kind=kind, cost=cost), TemporaryDirectory() as directory:
                    public = deepcopy(episodes()[1]['public'])
                    self.set_cost(public, kind, cost)
                    before = deepcopy(public)
                    for variant in ('B0', 'B3'):
                        with self.assertRaises(ValueError): ComparisonController(public, variant)
                    with patch('reachability.pressure_session.AdmissionService',
                               side_effect=AssertionError('invalid cost opened authority')) as authority:
                        with self.assertRaises(ValueError): ReasoningSession(public, directory)
                        authority.assert_not_called()
                    self.assertEqual(list(Path(directory).iterdir()), [])
                    self.assertEqual(public, before)

    def test_boundary_costs_produce_auditable_certified_work_for_both_controllers(self):
        from validation_lab.audit_pressure_comparison import audit_run
        for rule_cost, probe_cost in ((1, 1), (1, 100), (100, 1), (100, 100)):
            case = self.case(rule_cost, probe_cost)
            config = deepcopy(configurations()[1])
            config['budget'].update(operation_work=rule_cost+probe_cost+1, observation_work=probe_cost+1)
            for variant in ('B0', 'B3'):
                with self.subTest(rule=rule_cost, probe=probe_cost, variant=variant), TemporaryDirectory() as d:
                    path = Path(d)/'run'
                    result = run_one(case, variant, config, path)
                    self.assertEqual([row['kind'] for row in result['selected']], ['observe', 'derive', 'monitor'])
                    self.assertEqual(result['work']['operation_work'], rule_cost+probe_cost+1)
                    self.assertEqual(result['work']['observation_work'], probe_cost+1)
                    self.assertTrue(all(type(value) is int for value in result['work'].values()))
                    self.assertEqual(result['stop_reason'], 'OBSERVED_GOALS')
                    self.assertEqual(result['final']['certified_weighted_loss'], 0)
                    self.assertEqual(result['failures'], {})
                    audit_run(path, case, config, result)

    def test_work_limits_stop_before_unaffordable_probe_inference_or_monitor(self):
        case = self.case(100, 100)
        for operation_work, observation_work, selected, spent, observed in (
            (99, 101, 0, 0, 0), (201, 99, 0, 0, 0),
            (199, 101, 1, 100, 100), (200, 101, 2, 200, 100), (201, 100, 2, 200, 100)):
            for variant in ('B0', 'B3'):
                with self.subTest(work=operation_work, observations=observation_work, variant=variant), TemporaryDirectory() as d:
                    with ReasoningSession(case['public'], d) as session:
                        world = ReasoningWorld(session, case)
                        result = ComparisonController(case['public'], variant).run(world.port(),
                            ComparisonBudget(operation_work=operation_work, observation_work=observation_work))
                        self.assertEqual(result['stop_reason'], 'WORK_BUDGET')
                        self.assertEqual(result['work']['actions'], selected)
                        self.assertEqual(result['work']['operation_work'], spent)
                        self.assertEqual(result['work']['observation_work'], observed)
                        self.assertEqual(session.read()['goals'][0]['outstanding'], 1)


class PressureSummaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = TemporaryDirectory(); cls.addClassCleanup(cls.directory.cleanup)
        cls.path = Path(cls.directory.name)/'graph-bound'
        cls.case = deepcopy(episodes()[1]); cls.case['case_id'] = 'graph-bound-control'
        rng = Random(19)
        def condition(depth):
            return (rng.randrange(1, 9) if not depth else
                    {rng.choice(('AND', 'OR')): [condition(depth-1), condition(depth-1)]})
        public = cls.case['public']
        public['admission'].update(atoms=[str(i) for i in range(8)], rules=[])
        public['costs'] = {}; public['probes'] = []
        policy = deepcopy(public['priorities']['answer'])
        public['goals'] = [goal('g'+str(i), condition(6)) for i in range(4)]
        public['priorities'] = {g['goal_id']: deepcopy(policy) for g in public['goals']}
        cls.case['world'].update(initial=[], truth=list(range(1, 9)))
        cls.config = configurations()[1]
        cls.result = run_one(cls.case, 'B3', cls.config, cls.path)

    def test_final_unselected_graph_exhaustion_is_reported_with_unresolved_demand(self):
        result = self.result
        self.assertEqual(result['stop_reason'], 'PRESSURE_GRAPH_BUDGET')
        self.assertEqual(result['work']['actions'], 0)
        self.assertEqual(result['work']['inference_calls'], 0)
        self.assertEqual(set(result['last_pressure']['exhausted']), {'nodes', 'edges'})
        self.assertEqual(result['pressure_exhausted'], ['edges', 'nodes'])
        self.assertFalse(result['pressure_converged'])
        self.assertEqual(result['final']['certified_weighted_loss'], 4)
        self.assertEqual(sum(s['outstanding_loss'] for s in result['last_pressure']['sources'].values()), 4)

    def test_audit_requires_final_bounds_and_rejects_erased_or_invented_summary(self):
        from validation_lab.audit_pressure_comparison import audit_run, AuditError
        result = deepcopy(self.result); result['pressure_exhausted'] = ['edges', 'nodes']
        self.assertEqual(audit_run(self.path, self.case, self.config, result), 0)
        for bounds in ([], ['nodes'], ['edges', 'nodes', 'sources'], ['edges', 'nodes', 'nodes']):
            with self.subTest(bounds=bounds):
                result['pressure_exhausted'] = bounds
                with self.assertRaisesRegex(AuditError, 'pressure exhaustion summary'):
                    audit_run(self.path, self.case, self.config, result)

    def test_iteration_exhaustion_without_selection_is_in_summary(self):
        config = deepcopy(configurations()[1]); config['budget']['operation_work'] = 0
        with TemporaryDirectory() as d:
            result = run_one(episodes()[0], 'B3', config, Path(d)/'run', limits=PressureLimits(iterations=1))
            self.assertEqual(result['stop_reason'], 'WORK_BUDGET')
            self.assertEqual(result['work']['actions'], 0)
            expected = sorted('iterations:'+s for s in result['last_pressure']['sources'])
            self.assertEqual(result['pressure_exhausted'], expected)
            self.assertFalse(result['pressure_converged'])

    def test_repeated_iteration_bounds_are_unique_without_rewriting_field_history(self):
        config = deepcopy(configurations()[1]); config['budget']['actions'] = 3
        with TemporaryDirectory() as d:
            path = Path(d)/'run'
            result = run_one(episodes()[0], 'B3', config, path, limits=PressureLimits(iterations=1))
            rows = [json.loads(line) for line in (path/'trace.jsonl').read_text().splitlines()]
            fields = [row['pressure'] for row in rows if row['stage'] == 'selection']
            bounds = [bound for field in fields for bound in field['exhausted']]
            self.assertGreater(len(bounds), len(set(bounds)))
            self.assertEqual(result['pressure_exhausted'], sorted(set(bounds)))
            self.assertEqual(fingerprint(fields[-1]), fingerprint(result['last_pressure']))
            self.assertFalse(result['pressure_converged'])

    def test_later_convergence_does_not_erase_prior_iteration_exhaustion(self):
        case = deepcopy(episodes()[1]); public = case['public']
        public['admission'].update(atoms=['seed', 'middle', 'answer'], rules=[
            dict(rule_id='middle', revision='1', premises=[1], conclusion=2),
            dict(rule_id='answer', revision='1', premises=[2], conclusion=3)])
        public['costs'] = {'middle': 1, 'answer': 1}
        public['goals'][0]['condition'] = 3
        case['world']['truth'] = [1, 2, 3]
        with TemporaryDirectory() as d:
            path = Path(d)/'run'
            result = run_one(case, 'B3', configurations()[1], path, limits=PressureLimits(iterations=2))
            rows = [json.loads(line) for line in (path/'trace.jsonl').read_text().splitlines()]
            first = next(row['pressure'] for row in rows if row['stage'] == 'selection')
            self.assertFalse(first['converged'])
            self.assertTrue(result['last_pressure']['converged'])
            self.assertEqual(result['last_pressure']['exhausted'], [])
            self.assertEqual(result['pressure_exhausted'], sorted(first['exhausted']))
            self.assertFalse(result['pressure_converged'])
            self.assertEqual(result['final']['certified_weighted_loss'], 0)
            self.assertEqual(result['work']['actions'], 3)

    def test_no_evaluation_reports_no_exhaustion_for_either_controller(self):
        config = deepcopy(configurations()[1]); config['budget']['actions'] = 0
        for variant in ('B0', 'B3'):
            with self.subTest(variant=variant), TemporaryDirectory() as d:
                result = run_one(episodes()[1], variant, config, Path(d)/'run')
                self.assertEqual(result['pressure_exhausted'], [])
                self.assertIsNone(result['last_pressure'])
                self.assertEqual(result['work']['pressure_nodes'], 0)

    def test_readable_report_includes_bounds_from_unselected_evaluation(self):
        report = dict(source_revision='test-revision', seeds=[7], results=[self.result], m09={'detected': True})
        with TemporaryDirectory() as d:
            path = Path(d)/'comparison.md'; write_comparison(report, path)
            self.assertIn('graph-bound-control/7/work-16/B3: edges, nodes', path.read_text())


class ComparisonEpisodeTests(unittest.TestCase):
    def test_closed_loop_real_inference_relevant_change_and_simple_control(self):
        summaries = {}
        for case in episodes():
            for variant in ('B0', 'B3'):
                with self.subTest(case=case['case_id'], variant=variant), TemporaryDirectory() as d:
                    output = Path(d)/'run'
                    result = run_one(case, variant, configurations()[1], output)
                    self.assertEqual(result['status'], 'PASS')
                    self.assertEqual(result['final']['external_weighted_loss'], 0)
                    self.assertEqual(result['final']['certified_weighted_loss'], 0)
                    self.assertEqual(fairness_audit(output, case['public']), result['work']['actions'])
                    self.assertGreater(result['work']['inference_calls'], 0)
                    self.assertGreater(result['work']['certificates'], 0)
                    for category in ('candidate_discovery_ns', 'inference_ns', 'certification_ns', 'persistence_ns'):
                        self.assertGreater(result['costs_ns'][category], 0)
                    if variant == 'B3':
                        self.assertGreater(result['costs_ns']['pressure_iteration_ns'], 0)
                    if case['case_id'] == 'competing-routes':
                        self.assertEqual(result['environment_events'][0]['time'], 4)
                        self.assertIn('STALE', result['failures'])
                    with AdmissionService(database=output/'admission.db') as authority:
                        self.assertEqual(authority._journal_sequence, result['journal_commands_total'])
                        commands = [entry.command for entry in authority._journal.entries()]
                        self.assertIn('propose_transition', commands)
                        self.assertIn('precertify', commands); self.assertIn('postcertify', commands); self.assertIn('commit', commands)
                        self.assertEqual(authority.inspect_goal('answer').projection.outstanding_loss, 0)
                    summaries[case['case_id'], variant] = result
        self.assertEqual(summaries['simple-control', 'B0']['selected'], summaries['simple-control', 'B3']['selected'])
        self.assertNotEqual(summaries['competing-routes', 'B0']['selected'][0], summaries['competing-routes', 'B3']['selected'][0])

    def test_work_limited_semantics_reproduce_and_interrupted_directory_cannot_resume(self):
        case = episodes()[0]; results = []
        for _ in range(2):
            with TemporaryDirectory() as d:
                output = Path(d)/'run'
                result = run_one(case, 'B3', configurations()[0], output)
                results.append((result['selected'], result['final'], result['work'], result['stop_reason']))
                with self.assertRaisesRegex(ValueError, 'fresh authority'):
                    ReasoningSession(case['public'], output)
        self.assertEqual(results[0], results[1])

    def test_trace_audit_rejects_changed_candidate_frontier(self):
        with TemporaryDirectory() as d:
            case = episodes()[1]; output = Path(d)/'run'
            run_one(case, 'B0', configurations()[0], output)
            path = output/'trace.jsonl'; lines = path.read_text().splitlines()
            row = json.loads(lines[0]); row['candidates'] = []; lines[0] = json.dumps(row)
            path.write_text('\n'.join(lines)+'\n')
            with self.assertRaisesRegex(AssertionError, 'frontier'): fairness_audit(output, case['public'])

    def test_equal_horizon_does_not_give_stopped_controller_free_operations(self):
        case = episodes()[0]
        config = dict(name='zero-requests', budget=vars(ComparisonBudget(actions=0)))
        with TemporaryDirectory() as d:
            output = Path(d)/'run'
            result = run_one(case, 'B3', config, output)
            self.assertEqual(result['work']['actions'], 0)
            self.assertEqual(result['selected'], [])
            self.assertEqual(result['evaluation_horizon'], 16)
            self.assertEqual([row['time'] for row in result['outcomes']], list(range(17)))
            self.assertEqual(result['environment_events'][0]['time'], 4)
            self.assertEqual(result['final']['external_weighted_loss'], 7)
            self.assertEqual(result['integrated_external_loss'], 112)
