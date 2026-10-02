"""Independent metamorphic semantics, advisory boundaries and negative controls."""
import ast
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from experimental_pressure.projection import (Scope, ProjectionLimits, ProjectionBlocked,
    normalize, project, projected_graph, node_id)
from experimental_pressure.ranking import rank_projected
from reachability import pressure_controller as controller
from reachability.model import Clause, Status
from reachability.pressure import PressureLimits
from reachability.pressure_session import ReasoningSession
from reachability.pressure_work import anchor, build_graph, enumerate_work
from reachability.service import AdmissionDenied
from reachability.trace_protocol import fingerprint
from validation_lab.pressure_cost_ablation import POLICIES, rank_cost
from validation_lab.pressure_episodes import episodes
from validation_lab.projection_cases import BASES, diagnostic_cases, mixed_case, transformed, truth_set

SCOPE = Scope('context', 'goal', 'source', 'slice', 'window-1')


class ProjectionTests(unittest.TestCase):
    def test_generated_equivalence_idempotence_and_determinism(self):
        for base in list(BASES.values())+[{'AND': [-2, {'OR': [3, -4]}]}]:
            expected = normalize(base, SCOPE, {})['condition']
            for seed in range(32):
                condition = transformed(base, seed)
                with self.subTest(base=base, seed=seed):
                    projected = normalize(condition, SCOPE, {'knowledge': 3})
                    self.assertEqual(truth_set(condition, 5), truth_set(base, 5))
                    self.assertEqual(truth_set(projected['condition'], 5), truth_set(base, 5))
                    self.assertEqual(projected['condition'], expected)
                    self.assertEqual(projected, normalize(condition, SCOPE, {'knowledge': 3}))
                    self.assertEqual(normalize(projected['condition'], SCOPE, {})['condition'], expected)

    def test_mappings_preserve_all_original_occurrences_and_dependencies(self):
        original = {'AND': [2, {'AND': [3, 4]}, {'OR': [2]}]}
        result = normalize(original, SCOPE, {'knowledge': 7, 'resources': 4})
        self.assertEqual(result['condition'], {'AND': [2, 3, 4]})
        self.assertEqual(len(result['mapping']), 7)
        self.assertEqual(result['revisions'], {'knowledge': 7, 'resources': 4})
        for row in result['mapping']:
            value = original
            for index in row['path']: value = next(iter(value.values()))[index]
            self.assertEqual(row['original'], value)
            self.assertEqual(row['original_digest'], fingerprint(value))
        flattened = next(row for row in result['mapping'] if row['path'] == [1])
        self.assertEqual(flattened['relation'], 'flattened_into')
        self.assertEqual(flattened['containing_path'], [])
        self.assertEqual(flattened['node'], node_id(result['condition'], SCOPE))

    def test_no_distribution_absorption_or_cross_scope_equivalence(self):
        base = {'AND': [2, {'OR': [3, 4]}]}
        distributed = {'OR': [{'AND': [2, 3]}, {'AND': [2, 4]}]}
        self.assertEqual(truth_set(base, 4), truth_set(distributed, 4))
        self.assertNotEqual(normalize(base, SCOPE, {})['condition'], normalize(distributed, SCOPE, {})['condition'])
        for field in ('context', 'goal', 'source', 'slice', 'temporal'):
            self.assertNotEqual(node_id(base, SCOPE), node_id(base, replace(SCOPE, **{field: 'different'})))
        with self.assertRaisesRegex(ValueError, 'multiplicity'):
            replace(SCOPE, semantics='quantity-addition')

    def test_resource_quantities_temporal_predicates_and_evidence_are_unsupported_not_collapsed(self):
        for operator, values in (('RESOURCE', (1, 2)), ('AT', (10, 20)), ('EVIDENCE', ('a', 'b'))):
            for value in values:
                with self.subTest(operator=operator, value=value), self.assertRaises(ProjectionBlocked) as caught:
                    normalize({'AND': [{operator: value}, {operator: value}]}, SCOPE, {})
                self.assertEqual(caught.exception.reason, 'unsupported_requirement')

    def test_metamorphic_candidates_fields_rankings_at_four_support_states_all_placements(self):
        for family in BASES:
            case = mixed_case(family)
            with TemporaryDirectory() as directory, ReasoningSession(case['public'], directory) as session:
                session.observe(1, 'seed')
                for next_fact in (None, 2, 3, 4):
                    if next_fact: session.observe(next_fact, 'fact-'+str(next_fact))
                    snapshot = session.read()
                    candidates = enumerate_work(session.public, snapshot).candidates
                    for policy, flags in POLICIES.items():
                        if flags is None: continue
                        kwargs = dict(routing_cost=flags[0], queue_cost=flags[1])
                        ranks, field, _, _ = rank_projected(session.public, snapshot, candidates, PressureLimits(), **kwargs)
                        for seed in range(8):
                            public, changed = deepcopy(session.public), deepcopy(snapshot)
                            condition = transformed(BASES[family], seed)
                            public['goals'][0]['condition'] = changed['goals'][0]['condition'] = condition
                            changed['public_digest'] = fingerprint(public)
                            actual_candidates = enumerate_work(public, changed).candidates
                            actual_ranks, actual, _, _ = rank_projected(public, changed, actual_candidates, PressureLimits(), **kwargs)
                            self.assertEqual(actual_candidates, candidates)
                            self.assertEqual(actual['sources'], field['sources'])
                            self.assertEqual(actual_ranks, ranks)
                            self.assertEqual(actual['fields'], field['fields'])
                            self.assertNotEqual(actual['epoch'], field['epoch'])

    def test_every_unary_depth_reproduces_frozen_failure_and_normalized_counterpart(self):
        values = {}
        for case in diagnostic_cases():
            info = case['diagnostic']
            if info.get('equivalence_group') != 'wrapper-cost-1': continue
            with TemporaryDirectory() as directory, ReasoningSession(case['public'], directory) as session:
                session.observe(1, 'seed'); snapshot = session.read()
                candidates = enumerate_work(session.public, snapshot).candidates
                _, raw, _, _ = rank_cost(session.public, snapshot, candidates, PressureLimits(), 'B3-cost-both')
                ranks, normalized, _, _ = rank_projected(session.public, snapshot, candidates, PressureLimits())
                self.assertAlmostEqual(raw['scores']['rule:high']['value'], 3*.85**(info['depth']+2), places=12)
                self.assertAlmostEqual(normalized['scores']['rule:high']['value'], 3*.85**2, places=12)
                self.assertEqual(min(candidates, key=lambda c:ranks[c.candidate_id]).arguments,
                                 next(c for c in candidates if anchor(c)=='rule:high').arguments)
                values[info['depth']] = raw['scores']['rule:high']['value']
        self.assertEqual(set(values), set(range(9)))
        self.assertLess(values[8], .85**2)

    def test_real_operation_depth_remains_in_graph(self):
        values = []
        for case in diagnostic_cases():
            if case['diagnostic']['family'] != 'real-operation-depth': continue
            with TemporaryDirectory() as directory, ReasoningSession(case['public'], directory) as session:
                session.observe(1, 'seed'); snapshot = session.read()
                candidates = enumerate_work(session.public, snapshot).candidates
                _, field, _, _ = rank_projected(session.public, snapshot, candidates, PressureLimits())
                nodes, edges, _ = projected_graph(session.public, snapshot, project(session.public, snapshot))
                self.assertEqual(sum(n.identity.startswith('rule:step-') for n in nodes), case['diagnostic']['operations'])
                self.assertEqual(edges, build_graph(session.public, snapshot)[1])
                values.append(field['scores']['rule:step-1']['value'])
        self.assertGreater(values[0], values[1]); self.assertGreater(values[1], values[2])

    def test_evidence_identity_expiry_support_and_resource_revisions_remain_bound(self):
        with TemporaryDirectory() as directory, ReasoningSession(episodes()[0]['public'], directory) as session:
            session.observe(1, 'first', valid_until=3); original = session.read()
            projection = project(session.public, original)
            session.observe(1, 'second', valid_until=8); changed = session.read()
            self.assertNotEqual(enumerate_work(session.public, original), enumerate_work(session.public, changed))
            for snapshot in (changed, dict(changed, time=9), dict(changed, revisions=dict(changed['revisions'], resources=2))):
                self.assertNotEqual(projection['binding'], project(session.public, snapshot)['binding'])
                with self.assertRaisesRegex(ProjectionBlocked, 'stale_projection'):
                    projected_graph(session.public, snapshot, projection)
            session.tick(8)
            self.assertFalse(any(c.kind=='derive' for c in enumerate_work(session.public, session.read()).candidates))
            after = project(session.public, session.read())
            self.assertNotEqual(after['goals']['answer']['revisions'], projection['goals']['answer']['revisions'])

    def test_all_bounds_block_before_ranking_and_keep_original_source_accounts(self):
        case = mixed_case('and-or', 11)
        with TemporaryDirectory() as directory, ReasoningSession(case['public'], directory) as session:
            session.observe(1, 'seed'); snapshot = session.read()
            accounts = project(session.public, snapshot)['sources']
            for limit, value in (('visits', 1), ('depth', 0), ('children', 1), ('projected', 1), ('goals', 1)):
                calls = []
                class Port:
                    def read(self): return session.read()
                    def execute(self, *args): calls.append(args); raise AssertionError('partial operation')
                previous = controller.rank_b3
                try:
                    controller.rank_b3 = lambda *args: rank_projected(*args,
                        projection_limits=replace(ProjectionLimits(), **{limit:value}))
                    with self.assertRaises(ProjectionBlocked) as caught:
                        controller.ComparisonController(session.public, 'B3').run(Port())
                    self.assertEqual(caught.exception.accounts, accounts)
                    self.assertEqual(calls, [])
                    self.assertEqual(session.read(), snapshot)
                finally: controller.rank_b3 = previous

    def test_normalization_and_priority_cannot_change_authority_or_defeat_gates(self):
        for flags in ((True,True), (True,False), (False,True), (False,False)):
            with TemporaryDirectory() as directory, ReasoningSession(episodes()[0]['public'], directory) as session:
                session.observe(1, 'seed'); snapshot = session.read()
                candidates = enumerate_work(session.public, snapshot).candidates
                state = deepcopy({k:getattr(session.service,k) for k in session.service._STATE_FIELDS})
                journal = session.service._journal.entries()
                public = deepcopy(session.public); public['priorities']['answer']['weight'] = 1000.
                rank_projected(public, snapshot, candidates, PressureLimits(), routing_cost=flags[0], queue_cost=flags[1])
                self.assertEqual(state, {k:getattr(session.service,k) for k in session.service._STATE_FIELDS})
                self.assertEqual(journal, session.service._journal.entries())
                candidate = next(c for c in candidates if anchor(c)=='rule:shared')
                transition = session.call('propose_transition', session.context_id, 'shared', (session.aliases['seed'],))
                pre = session.call('precertify', transition, session.service.snapshot(session.context_id).knowledge_revision)
                session.call('revoke_evidence', 'seed')
                self.assertEqual(session.execute(candidate, fingerprint(snapshot))['status'], 'STALE')
                with self.assertRaises(AdmissionDenied) as caught: session.service.infer(transition, pre)
                self.assertIs(caught.exception.status, Status.STALE)
                session.observe(1, 'replacement')
                current = session.service.snapshot(session.context_id)
                session.call('replace_policy', session.context_id, 'forbid', (Clause((session.literal(-2),)),), current.knowledge_revision)
                self.assertEqual(session.execute(candidate, fingerprint(session.read()))['status'], 'FAIL')

    def test_source_duplication_is_idempotent_and_goals_stay_distinct(self):
        case = mixed_case('and', 11)
        with TemporaryDirectory() as directory, ReasoningSession(case['public'], directory) as session:
            snapshot = session.read(); first = project(session.public, snapshot)
            changed = deepcopy(snapshot)
            changed['goals'][0]['condition'] = {'AND':[changed['goals'][0]['condition']]*2}
            second = project(session.public, changed)
            self.assertEqual(first['sources'], second['sources'])
            self.assertEqual(len({s['identity'] for s in second['sources']}), 2)
            from reachability.pressure import derive
            nodes, edges, sources = projected_graph(session.public, changed, second)
            one = derive({}, nodes, edges, sources)
            many = derive({}, nodes, edges, sources*3)
            self.assertEqual(one, many)

    def test_runtime_extension_has_no_evaluator_import(self):
        for path in Path('experimental_pressure').glob('*.py'):
            for node in ast.walk(ast.parse(path.read_text())):
                modules = ([node.module or ''] if isinstance(node, ast.ImportFrom) else
                    [a.name for a in node.names] if isinstance(node, ast.Import) else [])
                self.assertFalse(any(m.startswith(('validation_lab', 'tests')) for m in modules))


if __name__ == '__main__': unittest.main()
