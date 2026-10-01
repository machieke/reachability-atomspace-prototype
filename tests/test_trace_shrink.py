"""Failure identity, bounded deletion, actual replay and retained evidence contracts."""
from contextlib import contextmanager
from copy import deepcopy
import json
from io import StringIO
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from validation_lab import admission_oracle
from validation_lab.run_deployment import ConformanceMismatch
from validation_lab.run_shrink import (CORPUS, ROOT, SEEDS, inventory, read, run_seed, semantic_result,
                                      source_seed, verify_bundle, verify_corpus, write, main)
from validation_lab.shrink_replay import ReplayPredicate, digest_file
from validation_lab.trace_shrink import canonical, shrink


def events(*names):
    return [dict(event_id=n, arguments=dict(reference='unchanged-'+n)) for n in names]


SIGNATURE = dict(event_id='b', path='outcome.status', expected='FAIL', actual='PASS')


def witness(value=SIGNATURE):
    return dict(kind='WITNESS', signature=deepcopy(value))


class DeletionEngineTests(unittest.TestCase):
    def test_retains_identity_order_arguments_and_detaches_callback_inputs(self):
        original = events('a', 'b', 'c', 'd')
        saved, seen, emitted = deepcopy(original), [], []
        def assess(candidate, trial):
            self.assertEqual(emitted[-1]['schema'], 'trace-shrink-trial-request/v1')
            self.assertEqual(emitted[-1]['trial'], trial)
            seen.append(deepcopy(candidate))
            answer = witness() if any(e['event_id'] == 'b' for e in candidate) else dict(kind='NO_WITNESS')
            candidate.clear()
            return answer
        result = shrink(original, assess, emit=emitted.append)
        self.assertEqual(original, saved)
        self.assertEqual(result['reduced_events'], [original[1]])
        self.assertTrue(result['one_minimal'])
        self.assertEqual(len(emitted), 2*len(seen))
        self.assertEqual([r['trial'] for r in emitted[::2]], list(range(len(seen))))
        self.assertEqual(result['trials'][-1]['phase'], 'final-replay')
        self.assertEqual(seen[-2:], [[], [original[1]]])

    def test_exact_failure_fields_and_json_types_cannot_drift(self):
        for field, value in (('event_id', 'other'), ('path', 'projection'), ('expected', 'UNKNOWN'), ('actual', 'OTHER')):
            changed = dict(SIGNATURE, **{field: value})
            result = shrink(events('b'), lambda e, _: witness() if e else witness(changed))
            self.assertEqual(len(result['reduced_events']), 1)
            self.assertTrue(result['one_minimal'])
        result = shrink(events('b'), lambda e, _: witness(dict(actual=1 if e else True)))
        self.assertEqual(len(result['reduced_events']), 1)

    def test_oracle_gaps_and_errors_cannot_prove_deletion_minimality(self):
        for kind in ('ORACLE_GAP', 'ERROR'):
            result = shrink(events('b'), lambda e, _: witness() if e else dict(kind=kind))
            self.assertEqual(result['status'], 'MINIMALITY_UNPROVEN')
            self.assertFalse(result['one_minimal'])
            self.assertTrue(result['trials'][-1]['preserves_signature'])

    def test_invalid_protocol_or_failing_control_is_outside_the_witness_domain(self):
        for kind in ('INVALID', 'CONTROL_MISMATCH'):
            result = shrink(events('b'), lambda e, _: witness() if e else dict(kind=kind))
            self.assertTrue(result['one_minimal'])

    def test_callback_exceptions_are_retained_and_never_treated_as_negatives(self):
        def assess(e, _):
            if e:
                return witness()
            raise RuntimeError('injected evaluator failure')
        result = shrink(events('b'), assess)
        self.assertEqual(result['status'], 'MINIMALITY_UNPROVEN')
        self.assertEqual(result['trials'][1]['assessment']['error_type'], 'RuntimeError')

    def test_budget_zero_does_not_call_predicate_or_claim_a_witness(self):
        result = shrink(events('b'), lambda *_: self.fail('budget exceeded'), max_evaluations=0)
        self.assertEqual(result['status'], 'BUDGET_EXHAUSTED')
        self.assertIsNone(result['signature'])
        self.assertEqual(result['evaluations'], 0)

    def test_budget_exhaustion_keeps_last_verified_reduction_without_minimality(self):
        calls = []
        def assess(e, trial):
            calls.append(trial)
            return witness()
        result = shrink(events('a', 'b', 'c'), assess, max_evaluations=2)
        self.assertEqual(calls, [0, 1])
        self.assertEqual(result['reduced_events'], events('c'))
        self.assertEqual(result['selected_trial'], 1)
        self.assertEqual(result['status'], 'BUDGET_EXHAUSTED')
        self.assertFalse(result['one_minimal'])
        self.assertIsNone(result['final_trial'])

    def test_final_replay_failure_revokes_minimality(self):
        result = shrink(events('b'), lambda e, trial: witness() if trial == 0 else dict(kind='NO_WITNESS'))
        self.assertEqual(result['status'], 'FINAL_REPLAY_FAILED')
        self.assertFalse(result['one_minimal'])
        self.assertEqual(result['selected_trial'], 0)

    def test_unwitnessed_seed_stops_without_search(self):
        result = shrink(events('b'), lambda *_: dict(kind='NO_WITNESS'))
        self.assertEqual(result['status'], 'SEED_NOT_WITNESSED')
        self.assertEqual(result['evaluations'], 1)
        self.assertIsNone(result['signature'])

    def test_single_deletion_minimality_is_not_a_global_minimum(self):
        def assess(e, _):
            ids = {x['event_id'] for x in e}
            return witness() if {'a', 'b'} <= ids or not ids else dict(kind='NO_WITNESS')
        result = shrink(events('a', 'b', 'c'), assess)
        self.assertEqual(result['reduced_events'], events('a', 'b'))
        self.assertTrue(result['one_minimal'])
        self.assertFalse(result['global_minimum'])
        self.assertEqual(assess([], 0)['kind'], 'WITNESS')

    def test_empty_seed_and_empty_reduction_are_audited(self):
        for original in ([], events('b')):
            result = shrink(original, lambda *_: witness())
            self.assertEqual(result['reduced_events'], [])
            self.assertTrue(result['one_minimal'])
            self.assertEqual(result['deletion_checks'], [])
            self.assertEqual(result['final_trial'], result['evaluations']-1)

    def test_every_accepted_single_deletion_restarts_its_audit(self):
        # A one-event input goes straight to the final deletion pass; the empty
        # witness must be replayed again, rather than inheriting the old audit.
        result = shrink(events('b'), lambda *_: witness())
        self.assertEqual([r['phase'] for r in result['trials']], ['original', 'single-deletion', 'final-replay'])
        self.assertEqual(result['accepted'][0]['trial'], 1)
        self.assertEqual(result['deletion_checks'], [])

    def test_strict_bounds_duplicate_ids_and_invalid_predicate_responses(self):
        for budget in (-1, 4097, True, 2.0):
            with self.assertRaises(ValueError):
                shrink([], lambda *_: witness(), max_evaluations=budget)
        for stream in (events('a', 'a'), events(*map(str, range(129))), [dict(event_id='')], ()):
            with self.assertRaises(ValueError):
                shrink(stream, lambda *_: witness())
        for value in (True, dict(kind='UNKNOWN_KIND'), dict(kind='WITNESS'), dict(kind='WITNESS', signature={}),
                      dict(kind='NO_WITNESS', value=float('nan'))):
            result = shrink(events('b'), lambda *_: value)
            self.assertEqual(result['trials'][0]['assessment']['kind'], 'ERROR')
            self.assertEqual(result['status'], 'SEED_NOT_WITNESSED')


class ReplayPredicateTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.seed = source_seed('M05')
        self.predicate = ReplayPredicate('admission', self.seed['initial'], self.seed['case'], 'M05', self.temp.name)

    def test_strict_protocol_rejection_precedes_control_or_mutation(self):
        invalid = deepcopy(self.seed['case']['events'][:1])
        invalid[0]['kind'] = 'future-kind'
        with patch('validation_lab.shrink_replay.run_case', side_effect=AssertionError('must not replay')):
            result = self.predicate(invalid, 0)
        self.assertEqual(result['kind'], 'INVALID')
        self.assertEqual(set(result['artifacts']), {'events.json'})
        self.assertFalse(result['control_passed'])

    def test_failing_unmodified_control_prevents_mutation(self):
        original_reference = self.predicate.reference
        def wrong(initial, prefix):
            result = original_reference(initial, prefix)
            result['projection']['extra'] = True
            return result
        self.predicate.reference = wrong
        with patch('validation_lab.shrink_replay.mutate', side_effect=AssertionError('must not mutate')):
            result = self.predicate(self.seed['case']['events'], 0)
        self.assertEqual(result['kind'], 'CONTROL_MISMATCH')
        self.assertFalse(result['control_passed'])
        self.assertNotIn('mutant.jsonl', result['artifacts'])

    def test_oracle_gap_after_an_event_retains_actual_prefix(self):
        reference = self.predicate.reference
        def gap(initial, prefix):
            if prefix:
                raise admission_oracle.OracleGap('unsupported injected prefix')
            return reference(initial, prefix)
        self.predicate.reference = gap
        result = self.predicate(self.seed['case']['events'], 0)
        self.assertEqual(result['kind'], 'ORACLE_GAP')
        records = (Path(self.temp.name)/'0000'/'control.jsonl').read_text().splitlines()
        self.assertEqual(len(records), 1)
        self.assertEqual(json.loads(records[0])['event_id'], 'e000')

    def test_unexpected_replay_errors_are_not_protocol_rejections(self):
        with patch('validation_lab.shrink_replay.run_case', side_effect=ValueError('injected runtime failure')):
            result = self.predicate(self.seed['case']['events'], 0)
        self.assertEqual(result['kind'], 'ERROR')
        self.assertEqual(result['stage'], 'control')

    def test_a_mutant_divergence_without_canary_is_not_a_witness(self):
        @contextmanager
        def unused(_):
            yield dict(calls=0)
        with patch('validation_lab.shrink_replay.mutate', unused), patch('validation_lab.shrink_replay.run_case',
                side_effect=[[], ConformanceMismatch('e004', 'outcome.status', 'UNKNOWN', 'PASS')]):
            result = self.predicate(self.seed['case']['events'], 0)
        self.assertEqual(result['kind'], 'ERROR')
        self.assertEqual(result['invocations'], 0)

    def test_trial_files_cannot_be_overwritten(self):
        self.predicate([], 1)
        with self.assertRaises(FileExistsError):
            self.predicate([], 1)

    def test_original_checkpoints_are_checked_but_not_reused_at_reduced_positions(self):
        case = deepcopy(self.seed['case'])
        case['checkpoints'] = [dict(step=1, path='outcome.status', expected='wrong')]
        self.predicate.case = case
        first = self.predicate(case['events'], 0)
        self.assertEqual(first['kind'], 'CONTROL_MISMATCH')
        second = self.predicate(case['events'][:5], 1)
        self.assertEqual(second['kind'], 'WITNESS')


class ShrinkCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.output = Path(cls.temp.name)
        cls.receipt = verify_corpus()
        cls.reports = {m: run_seed(read(ROOT/CORPUS/'seeds'/(m+'.json')), cls.output/m, corpus=cls.receipt) for m in SEEDS}

    def test_all_four_reductions_reproduce_source_pinned_semantic_decisions(self):
        for mutant, report in self.reports.items():
            with self.subTest(mutant=mutant):
                self.assertEqual(canonical(semantic_result(report['result'])), canonical(read(ROOT/CORPUS/'expected'/(mutant+'.json'))))
                self.assertEqual(verify_bundle(self.output/mutant), report)
                self.assertTrue(report['result']['one_minimal'])
        self.assertEqual([len(self.reports[m]['result']['reduced_events']) for m in SEEDS], [5, 6, 2, 1])
        self.assertEqual([self.reports[m]['result']['evaluations'] for m in SEEDS], [25, 47, 6, 10])

    def test_final_witnesses_and_each_single_deletion_replay_independently(self):
        for mutant, report in self.reports.items():
            result = report['result']
            seed = source_seed(mutant)
            predicate = ReplayPredicate(seed['profile'], seed['initial'], seed['case'], mutant, self.output/('audit-'+mutant))
            actual = predicate(result['reduced_events'], 0)
            self.assertEqual(actual['kind'], 'WITNESS')
            self.assertEqual(actual['signature'], result['signature'])
            for index in range(len(result['reduced_events'])):
                reduced = result['reduced_events'][:index]+result['reduced_events'][index+1:]
                actual = predicate(reduced, index+1)
                self.assertEqual(actual['kind'], 'NO_WITNESS')

    def test_offending_raw_output_is_saved_before_comparison(self):
        for mutant, report in self.reports.items():
            result = report['result']
            row = result['trials'][result['final_trial']]
            directory = self.output/mutant/'trials'/f"{row['trial']:04d}"
            actual = [json.loads(line) for line in (directory/'mutant.jsonl').read_text().splitlines()]
            control = [json.loads(line) for line in (directory/'control.jsonl').read_text().splitlines()]
            self.assertEqual(len(actual), row['assessment']['first_divergent_prefix'])
            self.assertEqual(len(control), len(result['reduced_events']))
            value = actual[-1]
            for key in result['signature']['path'].split('.'):
                value = value[key]
            self.assertEqual(value, result['signature']['actual'])
            self.assertEqual(actual[-1]['event_id'], result['signature']['event_id'])
            if mutant == 'M05':
                self.assertEqual(actual[-1]['projection']['numeric']['e004']['confidence'], 2/3)

    def test_bundle_rejects_extra_or_changed_files_and_false_minimality_evidence(self):
        source = self.output/'M07'
        for kind in ('raw', 'extra', 'audit', 'signature', 'arguments'):
            directory = self.output/('tampered-'+kind)
            shutil.copytree(source, directory)
            report = read(directory/'report.json')
            if kind == 'raw':
                (directory/'trials'/'0000'/'mutant.jsonl').write_text('changed\n')
            elif kind == 'extra':
                (directory/'unlisted.json').write_text('{}\n')
            elif kind == 'audit':
                report['result']['deletion_checks'].pop()
            elif kind == 'signature':
                report['result']['signature']['actual'] = 'UNKNOWN'
            else:
                changed = read(directory/'reduced.json')
                changed[0]['arguments']['attempt_id'] = 'changed'
                write(directory/'reduced.json', changed)
                report['files'] = inventory(directory)
            write(directory/'report.json', report)
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                verify_bundle(directory)

    def test_source_inventory_and_split_ancestry_are_verified(self):
        receipt = self.receipt
        root = self.output/'checkout'
        for name in (*receipt['fixture_files'], *receipt['source_files'], *receipt['upstream_files'], str(CORPUS/'manifest.json')):
            path = root/name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/name, path)
        verify_corpus(root)
        path = root/'validation_lab'/'trace_shrink.py'
        path.write_text(path.read_text()+'\n# drift\n')
        with self.assertRaisesRegex(ValueError, 'digest mismatch'):
            verify_corpus(root)
        shutil.copyfile(ROOT/'validation_lab'/'trace_shrink.py', path)
        extra = root/CORPUS/'seeds'/'extra.json'
        extra.write_text('{}\n')
        with self.assertRaisesRegex(ValueError, 'inventory'):
            verify_corpus(root)
        extra.unlink()
        seed_path = root/CORPUS/'seeds'/'M05.json'
        seed = read(seed_path)
        seed['source']['split'] = 'held-out'
        write(seed_path, seed)
        changed = deepcopy(receipt)
        changed['fixture_files'][str(seed_path.relative_to(root))] = digest_file(seed_path)
        write(root/CORPUS/'manifest.json', changed)
        with self.assertRaisesRegex(ValueError, 'ancestry'):
            verify_corpus(root)

    def test_budget_limited_bundle_retains_original_witness_and_all_attempts(self):
        directory = self.output/'budget'
        report = run_seed(source_seed('M07'), directory, max_evaluations=1)
        self.assertEqual(report['result']['status'], 'BUDGET_EXHAUSTED')
        self.assertEqual(report['result']['selected_trial'], 0)
        self.assertFalse(report['result']['one_minimal'])
        self.assertEqual(verify_bundle(directory), report)
        with self.assertRaises(FileExistsError):
            run_seed(source_seed('M07'), directory)

    def test_every_reduced_trace_remains_in_its_development_parent(self):
        for mutant in SEEDS:
            seed = read(ROOT/CORPUS/'seeds'/(mutant+'.json'))
            self.assertEqual(seed, source_seed(mutant))
            self.assertEqual(seed['source']['split'], 'development')
            self.assertEqual(seed['source']['parent_instance_id'], seed['case']['parent_instance_id'])
        self.assertEqual(self.receipt['family_complete_fixtures'], 0)

    def test_cli_budget_exhaustion_exits_nonzero_and_retains_all_reports(self):
        directory = self.output/'cli-budget'
        with patch('sys.argv', ['run_shrink', '--output', str(directory), '--max-evaluations', '0']), patch('sys.stdout', new=StringIO()):
            with self.assertRaises(SystemExit) as stopped:
                main()
        self.assertEqual(stopped.exception.code, 1)
        for mutant in SEEDS:
            report = verify_bundle(directory/mutant)
            self.assertEqual(report['result']['status'], 'BUDGET_EXHAUSTED')
            self.assertEqual(report['result']['evaluations'], 0)
        self.assertFalse(any(r['passed'] for r in read(directory/'report.json')['results']))

    def test_cli_replays_saved_evidence_and_allows_unused_budget_headroom(self):
        directory = self.output/'cli-replay'
        with patch('sys.argv', ['run_shrink', '--output', str(directory), '--replay-bundle', str(self.output/'M07'),
                                '--max-evaluations', '512']), patch('sys.stdout', new=StringIO()):
            main()
        self.assertTrue(read(directory/'report.json')['results'][0]['passed'])
        self.assertEqual(verify_bundle(directory/'M07')['result']['max_evaluations'], 512)

    def test_cli_refuses_replay_when_saved_implementation_receipt_differs(self):
        directory = self.output/'stale-source'
        shutil.copytree(self.output/'M07', directory)
        report = read(directory/'report.json')
        report['source_files']['validation_lab/trace_shrink.py'] = '0'*64
        write(directory/'report.json', report)
        with patch('sys.argv', ['run_shrink', '--output', str(self.output/'stale-replay'), '--replay-bundle', str(directory)]):
            with self.assertRaisesRegex(ValueError, 'implementation sources'):
                main()
