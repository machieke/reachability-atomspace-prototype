import ast
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from experimental_online_pln.agenda import Agenda, Limits, Probe, Snapshot, digest, enumerate_work
from experimental_online_pln.session import Session
from reachability.adapter_runtime import AdapterError
from reachability.model import Evidence, Status
from reachability.pln_adapter import DeductionRule, TruthValue
from reachability.probability_model import ProbabilityPolicy, ProbabilityReport, ProbabilityRule
from validation_lab.online_pln_cases import World, fixtures
from validation_lab.online_pln_conformance import run_case, summary


class OnlinePLNTests(unittest.TestCase):
    def setup_case(self, name='boundary-valid', *, native=False, **setup):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        world = World(next(f for f in fixtures() if f['id'] == name))
        session = Session(temporary.name, native=native, acquire=world.acquire)
        self.addCleanup(session.close)
        world.setup(session, **setup)
        return session, world

    def test_twelve_finite_cases_match_declared_prefixes(self):
        with TemporaryDirectory() as directory:
            for fixture in fixtures():
                with self.subTest(case=fixture['id']):
                    result = run_case(fixture, Path(directory)/fixture['id'])
                    self.assertEqual(result['conformance'], 'PASS', result.get('traceback'))
                    self.assertEqual(result['reconstruction']['native_calls_before'],
                                     result['reconstruction']['native_calls_after'])

    def test_frontier_is_read_only_complete_and_has_real_choice(self):
        s, _ = self.setup_case('choice-available')
        before, commands, calls = s.read(), s.service._journal_sequence, len(s.runtime.calls)
        a, b = enumerate_work(before), enumerate_work(s.read())
        self.assertTrue(a.complete)
        self.assertEqual(a.candidates, b.candidates)
        self.assertEqual([c.kind for c in a.candidates].count('deduction'), 2)
        self.assertIn('request', [c.kind for c in a.candidates])
        self.assertEqual(before, s.read())
        self.assertEqual((commands, calls), (s.service._journal_sequence, len(s.runtime.calls)))
        restored = Snapshot.from_records(before.records())
        self.assertEqual(restored.binding, before.binding)
        self.assertEqual(enumerate_work(restored).candidates, a.candidates)

    def test_rediscovery_and_duplicate_report_do_not_create_more_work_or_weight(self):
        s, _ = self.setup_case('lineage-independent')
        before = s.service.export_probability('ctx')
        report = next(iter(s.reports.values()))
        s.receive_report(report.evidence, report.report)
        self.assertEqual(before, s.service.export_probability('ctx'))
        agenda = Agenda()
        _, candidate = agenda.choose(s.read())
        self.assertEqual(s.execute(candidate)['status'], 'PASS')
        self.assertIsNone(agenda.choose(s.read())[1])
        self.assertIsNone(agenda.choose(s.read())[1])
        self.assertEqual(len(s.runtime.calls), 1)
        self.assertEqual(len(s.service.query_probability('ctx', s.forecast).current), 3)
        self.assertEqual(summary(s)['outstanding'], 10)

    def test_exact_retry_calls_are_charged_but_do_not_inflate_beliefs(self):
        s, _ = self.setup_case()
        candidate = enumerate_work(s.read()).candidates[0]
        first = s.numeric(candidate.kind, candidate.target, candidate.premise_ids)
        second = s.numeric(candidate.kind, candidate.target, candidate.premise_ids, label='exact-retry-test')
        self.assertEqual(first['commit'].belief, second['commit'].belief)
        self.assertEqual(len(s.runtime.calls), 2)
        self.assertGreater(s.costs['runtime_ns'], 0)
        self.assertEqual(summary(s)['outstanding'], 10)
        self.assertEqual(len(s.service.query_probability('ctx', s.forecast).current), 1)

    def test_failed_basis_not_retried_on_unrelated_clock_change(self):
        s, _ = self.setup_case('boundary-joint')
        agenda = Agenda()
        _, candidate = agenda.choose(s.read())
        self.assertEqual(s.execute(candidate)['status'], 'FAIL')
        s.emit('tick', time=1)
        self.assertIsNone(agenda.choose(s.read())[1])
        self.assertEqual(agenda.selections, 1)
        self.assertFalse(s.runtime.calls)

    def test_candidate_and_pending_numeric_commit_stale_after_equal_replacement(self):
        s, _ = self.setup_case('support-replacement')
        candidate = enumerate_work(s.read()).candidates[0]
        result = s.execute(candidate)
        self.assertEqual(result['status'], 'STALE')
        self.assertEqual(result['post_status'], 'STALE')
        self.assertEqual(s.execute(candidate)['status'], 'STALE')
        self.assertIsNone(result['commit'].belief)
        old = candidate.premise_ids[0]
        adopt = next(c for c in enumerate_work(s.read()).candidates if c.kind == 'adopt')
        self.assertEqual(s.execute(adopt)['status'], 'PASS')
        fresh = next(c for c in enumerate_work(s.read()).candidates if c.kind == 'deduction')
        self.assertNotEqual(fresh.premise_ids[0], old)
        self.assertEqual(s.execute(fresh)['status'], 'PASS')

    def test_bound_stops_retain_obligations_and_do_not_claim_impossibility(self):
        s, _ = self.setup_case()
        for limits, expected in [(Limits(selections=0), 'SELECTION_BUDGET'),
                                 (Limits(work=0), 'WORK_OR_ACQUISITION_BUDGET'),
                                 (Limits(tuple_visits=0), 'TUPLE_BOUND'),
                                 (Limits(candidates=0), 'CANDIDATE_BOUND'),
                                 (Limits(estimates=0), 'INPUT_BOUND'),
                                 (Limits(rules=0), 'INPUT_BOUND')]:
            with self.subTest(bound=expected):
                agenda = Agenda(limits)
                _, selected = agenda.choose(s.read())
                self.assertIsNone(selected)
                self.assertEqual(agenda.stop, expected)
                self.assertEqual(summary(s)['outstanding'], 10)

    def test_formula_failure_mismatch_and_missing_runtime_never_commit(self):
        # Real adapter failure classes, driven through the new selected-work seam.
        # Actual timeout/parser/source-drift behavior is covered by existing native suites.
        for response in (AdapterError('missing dependency'), AdapterError('timeout'),
                         AdapterError('malformed output'), TruthValue(.99, .8)):
            with self.subTest(response=response):
                s, _ = self.setup_case(native=True)
                agenda = Agenda()
                _, c = agenda.choose(s.read())
                kwargs = {'side_effect': response} if isinstance(response, Exception) else {'return_value': response}
                with patch.object(s.runtime.runtime, 'evaluate', **kwargs):
                    result = s.execute(c)
                self.assertNotEqual(result['status'], 'PASS')
                self.assertEqual(len(s.runtime.calls), 1)
                self.assertFalse(s.service.query_probability('ctx', s.forecast).current)
                self.assertEqual(agenda.selections, 1)
                self.assertIsNone(agenda.choose(s.read())[1])

    def test_numerical_acceptance_does_not_bypass_hard_credential_or_product(self):
        s, _ = self.setup_case()
        credential = s.service.query_belief('ctx', s.fact('credential')).current[0].proposal.evidence_ids[0]
        candidate = enumerate_work(s.read()).candidates[0]
        self.assertEqual(s.execute(candidate)['status'], 'PASS')
        s.emit('revoke', evidence_id=credential)
        reserve = next(c for c in enumerate_work(s.read()).candidates if c.kind == 'reserve')
        # An absent current positive hard witness is UNKNOWN in this contract.
        self.assertEqual(s.execute(reserve)['status'], 'UNKNOWN')
        self.assertEqual(summary(s)['effects'], 0)
        self.assertEqual(summary(s)['hard_forecast'], 'UNKNOWN')
        self.assertEqual(summary(s)['outstanding'], 10)

    def test_all_current_policy_retains_low_confidence_parents(self):
        s, _ = self.setup_case('lineage-independent')
        c = enumerate_work(s.read()).candidates[0]
        self.assertEqual(s.execute(c)['status'], 'PASS')
        decision = s.read().decision
        self.assertEqual(decision.status, Status.UNKNOWN)
        self.assertEqual(len(decision.criteria[0].current), 3)
        self.assertTrue(any(x.truth.confidence >= .35 for x in decision.criteria[0].current))
        self.assertEqual(sum(x.truth.confidence == .25 for x in decision.criteria[0].current), 2)
        self.assertNotIn('reserve', [c.kind for c in enumerate_work(s.read()).candidates])

    def test_equivalent_operations_keep_numeric_validity_under_reorder_and_rename(self):
        outputs = []
        for rename, reverse in [(False, False), (True, True)]:
            s, _ = self.setup_case('choice-available', rule_prefix='renamed-' if rename else '',
                                   reverse_reports=reverse)
            names = sorted((c.target for c in enumerate_work(s.read()).candidates if c.kind == 'deduction'), reverse=reverse)
            values = []
            for name in names:
                c = next(c for c in enumerate_work(s.read()).candidates if c.target == name)
                result = s.execute(c)
                self.assertEqual(result['status'], 'PASS')
                support = result['commit'].belief.proposal.support
                values.append((support.conclusion, support.truth, support.evidence_ids, support.lineage_roots))
            outputs.append(sorted(values))
            self.assertEqual(s.read().decision.status, Status.UNKNOWN)
            self.assertEqual(summary(s)['effects'], 0)
        self.assertEqual(*outputs)

    def test_registry_revisions_invalidate_candidates_and_exact_support(self):
        s, _ = self.setup_case()
        old = enumerate_work(s.read()).candidates[0]
        self.assertEqual(s.execute(old)['status'], 'PASS')
        rule = s.rules[old.target]
        s.register_rule(replace(rule, revision='2'), expected_revision='1')
        self.assertEqual(s.service.query_probability('ctx', s.forecast).status, Status.STALE)
        self.assertEqual(s.execute(old)['status'], 'STALE')
        fresh = next(c for c in enumerate_work(s.read()).candidates if c.kind == 'deduction')
        self.assertEqual(fresh.logical_id, old.logical_id)
        self.assertNotEqual(fresh.basis, old.basis)
        self.assertEqual(s.execute(fresh)['status'], 'PASS')

    def test_policy_and_model_retirement_reach_current_frontier_and_gates(self):
        s, _ = self.setup_case('lineage-independent')
        old = enumerate_work(s.read()).candidates[0]
        self.assertEqual(s.execute(old)['status'], 'PASS')
        s.revoke_model(old.target)
        current = s.service.query_probability('ctx', s.forecast)
        self.assertEqual(len(current.current), 2)
        self.assertEqual(len(current.historical), 3)
        self.assertFalse(any(c.kind == 'revision' for c in enumerate_work(s.read()).candidates))
        s.service.configure_probability_policy('ctx', ProbabilityPolicy('2', ('forecast-model',)), '1',
                                               idempotency_key=s.key())
        self.assertEqual(s.service.query_probability('ctx', s.forecast).status, Status.STALE)
        self.assertEqual(s.execute(old)['status'], 'STALE')
        self.assertEqual(sum(c.kind == 'adopt' for c in enumerate_work(s.read()).candidates), 2)

    def test_alternative_support_tuple_enumeration_reports_exhaustion(self):
        s, _ = self.setup_case('support-alternative')
        frontier = enumerate_work(s.read())
        self.assertEqual(frontier.tuple_visits, 2)
        self.assertEqual(len(frontier.candidates), 2)
        truncated = enumerate_work(s.read(), Limits(tuple_visits=1))
        self.assertFalse(truncated.complete)
        self.assertEqual(truncated.reason, 'TUPLE_BOUND')
        agenda = Agenda(Limits(tuple_visits=1))
        self.assertIsNone(agenda.choose(s.read())[1])
        self.assertFalse(s.runtime.calls)

    def test_mutant_unchecked_cached_candidate_binding_is_detected(self):
        s, _ = self.setup_case()
        stale = enumerate_work(s.read()).candidates[0]
        s.emit('tick', time=1)
        self.assertEqual(s.execute(stale)['status'], 'STALE')
        # Mutant silently refreshes a stale request instead of rejecting it.
        def mutant(candidate):
            return s.execute(replace(candidate, expected_binding=s.read().binding))
        with self.assertRaises(AssertionError):
            self.assertEqual(mutant(stale)['status'], 'STALE')

    def test_mutant_retry_suppression_removed_is_detected(self):
        s, _ = self.setup_case('lineage-copied')
        agenda = Agenda()
        _, c = agenda.choose(s.read())
        self.assertEqual(s.execute(c)['status'], 'UNKNOWN')
        self.assertIsNone(agenda.choose(s.read())[1])
        agenda.attempted.clear()  # mutant forgets fixed-basis attempt history
        with self.assertRaises(AssertionError):
            self.assertIsNone(agenda.choose(s.read())[1])

    def test_mutant_forecast_counted_as_world_relief_is_detected(self):
        from validation_lab import online_pln_conformance as harness
        original = harness.summary
        def mutant(session):
            result = original(session)
            if result['forecast']:
                result['outstanding'] = 0
            return result
        with TemporaryDirectory() as directory, patch.object(harness, 'summary', mutant):
            result = run_case(next(f for f in fixtures() if f['id'] == 'boundary-valid'), Path(directory)/'mutant')
        self.assertEqual(result['conformance'], 'FAIL')
        self.assertIn('forecast/ACK became observed relief', result['error'])

    def test_public_contract_cannot_carry_answers_or_fixture_labels(self):
        for field in ('future', 'answer', 'expected', 'fixture', 'best_candidate'):
            with self.assertRaises(TypeError):
                Probe('sensor', 'source', 'numeric', 'target', **{field:'leak'})
        package = Path(__file__).resolve().parents[1]/'experimental_online_pln'
        for path in package.glob('*.py'):
            for node in ast.walk(ast.parse(path.read_text())):
                modules = ([node.module or ''] if isinstance(node, ast.ImportFrom) else
                           [a.name for a in node.names] if isinstance(node, ast.Import) else [])
                self.assertFalse(any(m.startswith(('validation_lab', 'tests', 'experimental_planning',
                                                  'experimental_pressure')) for m in modules), path)


if __name__ == '__main__':
    unittest.main()
