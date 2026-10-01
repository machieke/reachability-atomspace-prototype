"""Independent numerical, source-accounting and unchanged authority checks."""
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
import math
import random
import unittest
from unittest.mock import patch

from reachability.pressure import Edge, Node, PressureLimits, Source, derive
from reachability.model import Status
from reachability.pln_adapter import TruthValue, proposition
from reachability.service import AdmissionService
from tests.goal_support import GoalFixture
from tests.probability_support import ProbabilityDriver
from validation_lab.pressure_reference import linear_reference, mutation_witness


def source(**kwargs):
    defaults = dict(context_id='ctx', source_id='obligation', slice_id='slice', goal_id='g', unit='results',
        policy_unit='priority/results', policy_revision='1', root='root', monitor='monitor', outstanding=10, coverage=0)
    defaults.update(kwargs)
    return Source(**defaults)


def graph():
    return ([Node('root', 'AND', 'infer'), Node('a', 'LEAF', 'infer'), Node('b', 'LEAF', 'observe'),
             Node('monitor', 'LEAF', 'observe')], [Edge('root', 'a', 'epistemic'), Edge('root', 'b', 'observation')])


class PressureTests(unittest.TestCase):
    def test_fixed_point_matches_independent_exact_linear_solver(self):
        rng = random.Random(841)
        for n in range(2, 7):
            for trial in range(4):
                nodes = [Node(str(i), 'AND', 'infer' if i % 2 else 'observe') for i in range(n)]
                edges = [Edge(str(j), str(i), 'epistemic', rng.randint(1, 5)) for j in range(n) for i in range(n) if rng.random() < .5]
                src = source(root='0', monitor='0')
                result = derive({'revision': trial}, nodes, edges, [src], limits=PressureLimits(iterations=512, tolerance=1e-11))
                routing = [[0.]*n for _ in range(n)]
                for parent, child, weight in result['routing']:
                    routing[int(child)][int(parent)] += weight
                self.assertTrue(all(sum(Fraction(routing[i][j]) for i in range(n)) <= 1 for j in range(n)))
                expected = linear_reference([10]+[0]*(n-1), routing, .85)
                field = result['fields'][src.identity]
                error = math.fsum(abs(field['values'][str(i)]-expected[i]) for i in range(n))
                self.assertTrue(field['converged'])
                self.assertLessEqual(error, field['error_bound_l1']+1e-12)
                self.assertLessEqual(field['pressure_norm'], field['norm_bound']+1e-10)

    def test_stored_column_bound_detects_excess_hidden_by_rounded_sum(self):
        # Independent rational witness: the previous fsum guard accepted this.
        self.assertEqual(math.fsum([.2]*5), 1.)
        self.assertEqual(sum(Fraction(.2) for _ in range(5))-1, Fraction(1, 2**54))
        nodes = [Node('root', 'AND', 'infer'), Node('monitor', 'LEAF', 'observe')]
        nodes += [Node(str(i), 'LEAF', 'infer') for i in range(5)]
        edges = [Edge('root', str(i), 'epistemic') for i in range(5)]
        field = derive({}, nodes, edges, [source()])
        shares = [weight for _, _, weight in field['routing']]
        self.assertTrue(all(weight > 0 for weight in shares))
        self.assertLessEqual(sum(map(Fraction, shares)), 1)
        self.assertEqual(sum(a != .2 for a in shares), 1)
        self.assertTrue(all(field['scores'][str(i)]['value'] > 0 for i in range(5)))
        self.assertEqual(field, derive({}, nodes[::-1], edges[::-1]*2, [source()]*2))

    def test_column_bound_covers_wide_weight_ranges_and_subnormals(self):
        rng = random.Random(9017)
        weight_sets = [[1.]*n for n in range(1, 65)]
        weight_sets += [[math.ulp(0.)]*5, [1e-300, 1e-200, 1e-100, 1, 1e6]]
        weight_sets += [[10.**rng.uniform(-300, 6) for _ in range(rng.randint(2, 64))] for _ in range(24)]
        for weights in weight_sets:
            with self.subTest(weights=weights):
                nodes = [Node('root', 'AND', 'infer'), Node('monitor', 'LEAF', 'observe')]
                nodes += [Node(str(i), 'LEAF', 'infer') for i in range(len(weights))]
                edges = [Edge('root', str(i), 'epistemic', w) for i, w in enumerate(weights)]
                field = derive({}, nodes, edges, [source()])
                shares = [Fraction(w) for _, _, w in field['routing']]
                self.assertEqual(len(shares), len(weights))
                self.assertTrue(all(w > 0 for w in shares))
                self.assertLessEqual(sum(shares), 1)

    def test_unrepresentable_positive_share_is_rejected_without_mutating_inputs(self):
        nodes, _ = graph()
        edges = [Edge('root', 'a', 'epistemic', math.ulp(0.)), Edge('root', 'b', 'observation', 1e6)]
        binding = {'revision': 1}; src = source(); before = deepcopy((binding, nodes, edges, src))
        exact_share = Fraction(math.ulp(0.))/(Fraction(math.ulp(0.))+1_000_000)
        self.assertGreater(exact_share, 0); self.assertEqual(float(exact_share), 0.)
        with self.assertRaisesRegex(ValueError, 'normalized positive share underflows'):
            derive(binding, nodes, edges, [src])
        self.assertEqual((binding, nodes, edges, src), before)

    def test_routing_version_binds_epoch_and_cyclic_field_matches_reference(self):
        names = ['root', 'a', 'b', 'c', 'd']
        nodes = [Node(name, 'AND', 'infer') for name in names]+[Node('monitor', 'LEAF', 'observe')]
        edges = [Edge(parent, child, 'epistemic') for parent in names for child in names]
        src = source(); field = derive({}, nodes, edges, [src], limits=PressureLimits(iterations=1024, tolerance=1e-11))
        routing = [[0.]*5 for _ in names]
        for parent, child, weight in field['routing']:
            routing[names.index(child)][names.index(parent)] = weight
        self.assertTrue(all(sum(Fraction(routing[i][j]) for i in range(5)) <= 1 for j in range(5)))
        expected = linear_reference([10, 0, 0, 0, 0], routing, .85)
        self.assertTrue(field['converged'])
        for name, value in zip(names, expected):
            self.assertAlmostEqual(field['scores'][name]['value'], value, delta=field['error_bound_l1']+1e-12)
        with patch('reachability.pressure.ROUTING_VERSION', 'different-routing-revision'):
            changed = derive({}, nodes, edges, [src], limits=PressureLimits(iterations=1024, tolerance=1e-11))
        self.assertNotEqual(field['epoch'], changed['epoch'])
        self.assertEqual(field['scores'], changed['scores'])
        self.assertEqual(field['routing_version'], 'binary64-substochastic/v2')

    def test_unchanged_recomputation_and_duplicate_paths_do_not_inject_sources(self):
        nodes, edges = graph(); src = source()
        first = derive({'revision': 1}, nodes, edges, [src])
        for _ in range(8):
            self.assertEqual(derive({'revision': 1}, nodes*2, edges*3, [src]*5), first)
        alternative = derive({'revision': 1}, nodes+[Node('bridge', 'AND', 'infer')],
            edges+[Edge('root', 'bridge', 'epistemic'), Edge('bridge', 'a', 'epistemic')], [src])
        self.assertEqual(alternative['sources'], first['sources'])
        self.assertEqual(len(first['sources']), 1)
        with self.assertRaisesRegex(ValueError, 'conflicting duplicate'):
            derive({}, nodes, edges, [src, replace(src, outstanding=20)])

    def test_cycle_is_bounded_and_cannot_satisfy_or_create_an_obligation(self):
        nodes = [Node('root', 'AND', 'infer'), Node('a', 'AND', 'infer', blocked='UNMET_REQUIREMENTS'),
                 Node('b', 'AND', 'infer', blocked='UNMET_REQUIREMENTS'), Node('monitor', 'LEAF', 'observe')]
        edges = [Edge('root', 'a', 'teleological'), Edge('a', 'b', 'epistemic'), Edge('b', 'a', 'epistemic')]
        src = source()
        result = derive({}, nodes, edges, [src], limits=PressureLimits(gamma=.8, iterations=256))
        self.assertEqual(result['cycles'], [['a', 'b']])
        self.assertAlmostEqual(result['scores']['a']['value'], 80/3.6, places=6)
        self.assertTrue(result['stranded'][0]['fully_stranded'])
        self.assertEqual(result['sources'][src.identity]['outstanding_loss'], 10)
        empty = derive({}, nodes, edges, [replace(src, outstanding=0)])
        self.assertTrue(all(row['value'] == 0 for row in empty['scores'].values()))

    def test_and_sends_positive_pressure_to_each_missing_conjunct(self):
        nodes, edges = graph(); src = source()
        result = derive({}, nodes, edges, [src])
        self.assertAlmostEqual(result['scores']['a']['value'], 4.25)
        self.assertAlmostEqual(result['scores']['b']['value'], 4.25)
        satisfied = [replace(n, satisfied=True) if n.identity == 'a' else n for n in nodes]
        after = derive({}, satisfied, edges, [src])
        self.assertEqual(after['scores']['a']['value'], 0.)
        self.assertAlmostEqual(after['scores']['b']['value'], 8.5)
        self.assertEqual(after['conversions'][0]['after'], 'observe')

    def test_or_normalizes_whole_branches_and_does_not_duplicate_source_value(self):
        nodes, _ = graph(); nodes[0] = replace(nodes[0], operator='OR')
        result = derive({}, nodes, [Edge('root', 'a', 'epistemic', 3), Edge('root', 'b', 'observation', 1)], [source()])
        self.assertAlmostEqual(result['scores']['a']['value'], 6.375)
        self.assertAlmostEqual(result['scores']['b']['value'], 2.125)
        self.assertEqual(sum(s['outstanding_demand'] for s in result['sources'].values()), 10)

    def test_stranded_demand_remains_when_capability_is_absent(self):
        nodes = [Node('root', 'LEAF', 'infer', blocked='MISSING_CAPABILITY'), Node('monitor', 'LEAF', 'observe')]
        result = derive({}, nodes, [], [source(weight=8)])
        self.assertEqual(result['stranded'], [dict(source_id=source().identity, demand=80,
            reasons=['MISSING_CAPABILITY'], fully_stranded=True)])

    def test_graph_iteration_and_source_bounds_are_reported(self):
        nodes, edges = graph()
        for limits, expected in ((PressureLimits(nodes=1), 'nodes'), (PressureLimits(edges=1), 'edges'),
                                 (PressureLimits(sources=1), 'sources')):
            sources = [source(), source(source_id='other')]
            result = derive({}, nodes, edges, sources, limits=limits)
            self.assertIn(expected, result['exhausted'])
            self.assertEqual(result['scores'], {})
            self.assertEqual(result['stranded'][0]['reasons'], ['SEARCH_BUDGET_EXHAUSTED'])
        result = derive({}, nodes, edges, [source()], limits=PressureLimits(iterations=1))
        self.assertFalse(result['converged'])
        self.assertGreater(result['residual_l1'], 0)
        self.assertTrue(result['exhausted'][0].startswith('iterations:'))
        self.assertEqual(result['stranded'], [])  # A numerical cap is not impossibility.
        zero_priority = derive({}, nodes, edges, [source(weight=0)])
        self.assertEqual(zero_priority['stranded'], [])

    def test_units_channels_and_parameters_are_explicit(self):
        with self.assertRaisesRegex(ValueError, 'conversion'):
            source(unit='seconds')
        with self.assertRaises(ValueError): Node('act', 'LEAF', 'act')
        with self.assertRaises(ValueError): Edge('a', 'b', 'causal')
        for value in (float('nan'), float('inf'), -1, True):
            with self.assertRaises(ValueError): source(weight=value)
        for gamma in (0, 1, float('nan')):
            with self.assertRaises(ValueError): PressureLimits(gamma=gamma)
        nodes, edges = graph()
        converted = source(source_id='latency', unit='seconds', policy_unit='priority/seconds', weight=.1)
        result = derive({}, nodes, edges, [source(), converted])
        self.assertEqual(sum(s['outstanding_demand'] for s in result['sources'].values()), 11)
        self.assertEqual(result['unsupported_channels'], ['act', 'expand', 'retain'])

    def test_m09_actual_source_injection_mutation_is_detected(self):
        witness = mutation_witness()
        self.assertTrue(witness['detected'])
        self.assertEqual(witness['mutant_repeated_pressures'], [10., 20.])

    def test_priority_and_pressure_do_not_change_numerical_truth_or_authority(self):
        with AdmissionService() as service:
            driver = ProbabilityDriver(service); driver.context()
            driver.adopt('report', proposition('P'), TruthValue(.3, .7))
            before = deepcopy({name: getattr(service, name) for name in service._STATE_FIELDS})
            nodes, edges = graph()
            low = derive({'knowledge': 1}, nodes, edges, [source(weight=1)])
            high = derive({'knowledge': 1}, nodes, edges, [source(weight=1000)])
            self.assertGreater(high['scores']['a']['value'], low['scores']['a']['value'])
            self.assertEqual(before, {name: getattr(service, name) for name in service._STATE_FIELDS})
            self.assertEqual(service.query_probability('world', proposition('P')).current[0].proposal.support.truth, TruthValue(.3, .7))
            self.assertIs(service.query_belief('world', proposition('P')).status, Status.UNKNOWN)


class PressureCoverageTests(GoalFixture, unittest.TestCase):
    def pressure(self):
        view = self.service.inspect_goal('goal')
        nodes, edges = graph()
        sources = [source(context_id=view.episode.context_id, source_id=view.episode.source_id,
            slice_id=s.slice_id, unit=view.projection.unit, policy_unit='priority/'+view.projection.unit,
            outstanding=s.outstanding_loss, coverage=s.estimated_coverage,
            relief_events=tuple(e.event_id for r in view.history for e in r.events if e.kind == 'observed_relief')) for s in view.projection.slices]
        return derive(dict(knowledge=view.projection.knowledge_revision, goal=view.projection.goal_revision,
            lifecycle=view.projection.lifecycle_revision, resource=view.projection.resource_revision,
            time=view.projection.logical_time), nodes, edges, sources)

    def test_live_overlap_coverage_monitoring_expiry_and_relief_stay_distinct(self):
        initial = self.pressure()
        self.cover(6, commitment_id='one', until=2)
        self.cover(6, commitment_id='duplicate-promise', until=2)
        before = deepcopy({name: getattr(self.service, name) for name in self.service._STATE_FIELDS})
        covered = self.pressure()
        self.assertEqual(before, {name: getattr(self.service, name) for name in self.service._STATE_FIELDS})
        self.assertEqual(sum(s['outstanding_loss'] for s in covered['sources'].values()), 10)
        self.assertEqual(sum(s['predicted_coverage'] for s in covered['sources'].values()), 6)
        self.assertEqual(sum(s['open_loss'] for s in covered['sources'].values()), 4)
        self.assertEqual(covered['scores']['monitor']['value'], 6)
        self.assertTrue(all(not s['observed_relief_events'] for s in covered['sources'].values()))
        self.tick(2)
        expired = self.pressure()
        self.assertEqual(sum(s['open_loss'] for s in expired['sources'].values()), 10)
        self.assertNotEqual(initial['epoch'], expired['epoch'])
        self.assertEqual(set(initial['sources']), set(expired['sources']))
        self.product()
        self.sample(2, slice_id='available'); self.reconcile()
        observed = self.pressure()
        self.assertEqual(sum(s['outstanding_loss'] for s in observed['sources'].values()), 6)
        self.assertTrue(any(s['observed_relief_events'] for s in observed['sources'].values()))
