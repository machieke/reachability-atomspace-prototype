"""Deterministic authority races, independent prefixes and reduced defect evidence."""
import ast
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
import unittest
from unittest.mock import patch

from reachability import interleaving_protocol as protocol
from reachability.execution import ExecutionMixin
from reachability.interleaving_session import InterleavingSession
from validation_lab.generate_interleaving_cases import event, scenarios
from validation_lab.interleaving_mutations import mutate
from validation_lab.interleaving_oracle import OracleGap, reference_prefix
from validation_lab.interleaving_schedule import ScheduleError, reserve_pair
from validation_lab.run_deployment import ConformanceMismatch
from validation_lab.run_interleaving import (CORPUS, ROOT, InterleavingPredicate, load_cases, reduce_case, run_case,
                                            semantic_result, validate_case, verify_corpus, verify_report, main)


def read(path):
    return json.loads(path.read_text())


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


class InterleavingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.output = Path(cls.temp.name)
        cls.cases = scenarios()
        cls.results = {c['case_id']: run_case(c, cls.output/c['case_id']) for c in cls.cases}
        cls.reductions = {c['mutant']: reduce_case(c, c['mutant'], cls.output/c['mutant']) for c in cls.cases if c['mutant']}

    def test_every_fixed_and_exhaustively_merged_prefix_matches_and_recovers(self):
        receipt = verify_corpus()
        self.assertEqual(load_cases(), self.cases)
        self.assertEqual(len(self.cases), 22)
        self.assertEqual(sum(r['prefixes'] for r in self.results.values()), receipt['event_prefixes'])
        self.assertEqual(receipt['family_complete_fixtures'], 0)
        for case in self.cases:
            pair = bool(case['schedule']['reserve_pair'])
            self.assertEqual(self.results[case['case_id']]['recovery_checkpoints'], len(case['events'])-pair)

    def test_all_six_two_worker_merges_preserve_each_actors_program_order(self):
        merged = self.cases[-6:]
        self.assertEqual({''.join(e['actor'] for e in c['events']) for c in merged}, {'aabb','abab','abba','baab','baba','bbaa'})
        for case in merged:
            for actor in ('a','b'):
                self.assertEqual([e['kind'] for e in case['events'] if e['actor']==actor], ['certify','reserve'])

    def test_correct_lock_blocks_contender_at_the_actual_check_publication_boundary(self):
        for case in (self.cases[5], self.cases[6]):
            notes = lines(self.output/case['case_id']/'schedule.jsonl')
            self.assertEqual(notes[0]['point'], 'checked')
            self.assertTrue(notes[0]['authority_lock_held'])
            self.assertTrue(notes[1]['blocked_by_first'])
            rows = lines(self.output/case['case_id']/'actual.jsonl')
            pair = case['schedule']['reserve_pair']
            by_id = {r['outcome']['event_id']:r for r in rows}
            self.assertEqual([by_id[e]['outcome']['status'] for e in pair], ['PASS','STALE'])
            self.assertEqual(by_id[pair[-1]]['projection']['used'], 1)

    def test_mutation_changes_atomicity_without_skipping_complete_checks(self):
        result = self.reductions['M10']
        final = self.output/'M10'/'trials'/f"{result['final_trial']:04d}"/'mutant'
        notes = lines(final/'schedule.jsonl')
        self.assertEqual([n['authority_lock_held'] for n in notes if n['point']=='checked'], [False,False])
        actual = lines(final/'actual.jsonl')
        self.assertEqual(actual[-1]['outcome']['status'], 'PASS')
        self.assertEqual(actual[-1]['projection']['used'], 2)
        self.assertEqual(actual[-1]['projection']['intents'], ['a','b'])
        self.assertEqual(result['signature']['expected'], 'STALE')
        self.assertEqual(read(final/'execution.json')['invocations'], 2)

    def test_M08_retains_consistency_fallback_but_wrongly_loses_unrelated_support(self):
        result = self.reductions['M08']
        self.assertEqual(result['signature']['path'], 'projection.usable')
        self.assertEqual(result['signature']['expected'], [2])
        self.assertEqual(result['signature']['actual'], [])
        final = self.output/'M08'/'trials'/f"{result['final_trial']:04d}"
        for stage in ('control','mutant'):
            row = lines(final/stage/'actual.jsonl')[-1]
            self.assertNotIn(1,row['projection']['usable'])
            self.assertEqual(row['projection']['clauses'], [[-1]])
            self.assertEqual(row['outcome']['status'], 'PASS')
        self.assertGreater(read(final/'assessment.json')['invocations'],0)

    def test_reductions_reproduce_pinned_decisions_and_unchanged_schedule_ancestry(self):
        for mutant, result in self.reductions.items():
            expected = read(CORPUS/'mutations'/(mutant+'.json'))
            self.assertEqual(semantic_result(result), expected['result'])
            self.assertTrue(result['one_minimal'])
            self.assertFalse(result['global_minimum'])
            reduced = read(self.output/mutant/'reduced.json')
            self.assertEqual(reduced['schedule'],expected['case']['schedule'])
            self.assertEqual(reduced['split'],'development')
            self.assertEqual(reduced['parent_instance_id'],'interleaving-parent-0')
        self.assertEqual([len(self.reductions[m]['reduced_events']) for m in ('M08','M10')],[1,4])

    def test_fresh_final_witness_and_all_five_single_deletions(self):
        for mutant,result in self.reductions.items():
            case=read(CORPUS/'mutations'/(mutant+'.json'))['case']
            predicate=InterleavingPredicate(case,mutant,self.output/('fresh-'+mutant))
            actual=predicate(result['reduced_events'],0)
            self.assertEqual(actual['kind'],'WITNESS')
            self.assertEqual(actual['signature'],result['signature'])
            for index in range(len(result['reduced_events'])):
                actual=predicate(result['reduced_events'][:index]+result['reduced_events'][index+1:],index+1)
                self.assertEqual(actual['kind'],'NO_WITNESS')
                self.assertTrue(actual['control_passed'])

    def test_rejected_first_worker_can_be_followed_by_a_successful_contender(self):
        # Covers reused OS thread identifiers as well as early missing-reference
        # rejection; the scheduler uses actor-local state, not remembered IDs.
        case=deepcopy(self.cases[5])
        case['events']=[e for e in case['events'] if e['event_id'] not in ('ca','read','end')]
        for index in range(3):
            path=self.output/('early-'+str(index))
            run_case(case,path)
            rows=lines(path/'actual.jsonl')
            self.assertEqual([r['outcome']['status'] for r in rows],['PASS','UNKNOWN','PASS'])
            self.assertEqual(rows[-1]['projection']['intents'],['b'])

    def test_inadequate_capacity_and_prerequisites_never_reach_publication(self):
        for case in self.cases[7:9]:
            rows=lines(self.output/case['case_id']/'actual.jsonl')
            self.assertEqual(rows[-1]['projection']['used'],0)
            self.assertFalse(any(n['point']=='checked' for n in lines(self.output/case['case_id']/'schedule.jsonl')))

    def test_stale_commit_and_reservation_are_rejected_after_policy_insertion(self):
        for index,name in ((0,'commit'),(10,'ra')):
            rows=lines(self.output/self.cases[index]['case_id']/'actual.jsonl')
            self.assertEqual(next(r['outcome']['status'] for r in rows if r['outcome']['event_id']==name),'STALE')

    def test_positive_admission_and_two_unit_control_defeat_blanket_refusal(self):
        admission=lines(self.output/'i12'/'actual.jsonl')[-1]
        resource=lines(self.output/'i10'/'actual.jsonl')[-1]
        self.assertEqual(admission['projection']['usable'],[1,2,3])
        self.assertEqual(resource['projection']['intents'],['a','b'])
        self.assertEqual(resource['projection']['used'],2)

    def test_uncontrolled_thread_stress_also_preserves_last_unit(self):
        for _ in range(6):
            with TemporaryDirectory() as directory, InterleavingSession(self.cases[5]['public'],directory) as session:
                session.apply(event('ca','a','certify'))
                session.apply(event('cb','b','certify'))
                barrier=Barrier(2)
                def reserve(actor):
                    barrier.wait(timeout=5)
                    return session.apply(event('r'+actor,actor,'reserve',permit='c'+actor))['status']
                with ThreadPoolExecutor(max_workers=2) as pool:
                    self.assertCountEqual(pool.map(reserve,('a','b')),['PASS','STALE'])
                self.assertEqual(session.projection()['used'],1)

    def test_deterministic_schedule_replays_identically(self):
        case=self.cases[5]
        original=lines(self.output/case['case_id']/'actual.jsonl')
        for index in range(2):
            path=self.output/('repeat-'+str(index))
            run_case(case,path)
            self.assertEqual(lines(path/'actual.jsonl'),original)
            self.assertEqual(lines(path/'schedule.jsonl'),lines(self.output/case['case_id']/'schedule.jsonl'))

    def test_actual_event_is_retained_when_oracle_fails(self):
        case=self.cases[11]
        def gap(public,prefix):
            if prefix:
                raise OracleGap('injected unsupported prefix')
            return reference_prefix(public,prefix)
        path=self.output/'gap'
        with self.assertRaises(OracleGap):
            run_case(case,path,reference=gap)
        self.assertEqual(len(lines(path/'actual.jsonl')),1)
        self.assertEqual(read(path/'execution.json')['prefixes'],1)

    def test_failing_control_prevents_mutant_replay(self):
        predicate=InterleavingPredicate(self.cases[0],'M08',self.output/'control-error')
        with patch('validation_lab.run_interleaving.run_case',side_effect=ConformanceMismatch('x','projection',1,2)) as replay:
            result=predicate(self.cases[0]['events'],0)
        self.assertEqual(replay.call_count,1)
        self.assertEqual(result['kind'],'CONTROL_MISMATCH')
        self.assertFalse(result['control_passed'])

    def test_budget_exhaustion_keeps_witness_without_minimality_claim(self):
        result=reduce_case(self.cases[5],'M10',self.output/'budget',max_evaluations=1)
        self.assertEqual(result['status'],'BUDGET_EXHAUSTED')
        self.assertEqual(result['evaluations'],1)
        self.assertFalse(result['one_minimal'])
        self.assertEqual(result['signature'],self.reductions['M10']['signature'])

    def test_mutations_restore_original_methods_after_exception(self):
        original=ExecutionMixin.reserve_and_record_intent
        with self.assertRaisesRegex(RuntimeError,'injected'):
            with mutate('M10'):
                self.assertIsNot(ExecutionMixin.reserve_and_record_intent,original)
                raise RuntimeError('injected')
        self.assertIs(ExecutionMixin.reserve_and_record_intent,original)

    def test_no_M08_invocation_when_policy_has_no_new_direct_blocker(self):
        predicate=InterleavingPredicate(self.cases[3],'M08',self.output/'no-blocker-canary')
        result=predicate(self.cases[3]['events'],0)
        self.assertEqual(result['kind'],'NO_WITNESS')
        self.assertEqual(read(self.output/'no-blocker-canary'/'0000'/'mutant'/'execution.json')['invocations'],0)

    def test_cli_report_verifies_and_rejects_missing_evidence_or_coverage(self):
        path=self.output/'cli'
        with patch('sys.argv',['run_interleaving','--output',str(path)]),patch('sys.stdout',new=StringIO()):
            main()
        report=verify_report(path)
        self.assertEqual(len(report['mutations']),2)
        saved=(path/'report.json').read_text()
        report['results'].pop()
        (path/'report.json').write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError,'coverage'):
            verify_report(path)
        (path/'report.json').write_text(saved)
        (path/'i01'/'schedule.jsonl').write_text('tampered\n')
        with self.assertRaisesRegex(ValueError,'sources/files'):
            verify_report(path)

    def test_source_drift_and_unlisted_files_are_rejected(self):
        from validation_lab import run_interleaving as runner
        receipt=verify_corpus()
        fake=deepcopy(receipt)
        fake['source_files']['validation_lab/interleaving_oracle.py']='0'*64
        real_loads=json.loads
        def changed(text):
            value=real_loads(text)
            return fake if isinstance(value,dict) and value.get('schema')=='interleaving-corpus/v1' else value
        with patch.object(runner.json,'loads',side_effect=changed):
            with self.assertRaisesRegex(ValueError,'source/fixture drift'):
                verify_corpus()
        fake=deepcopy(receipt)
        fake['fixture_files']['validation_lab/interleaving_cases/public/extra.json']='0'*64
        with patch.object(runner.json,'loads',side_effect=changed):
            with self.assertRaisesRegex(ValueError,'inventory'):
                verify_corpus()


class InterleavingBoundaryTests(unittest.TestCase):
    def test_wire_rejects_hidden_labels_schedule_fields_booleans_and_unknown_commands(self):
        public=scenarios()[0]['public']
        for bad in (dict(public,schedule={}),dict(public,capacity=True),dict(public,facts=[True]),dict(public,facts=[1,1])):
            with self.assertRaises(ValueError):
                protocol.initial(bad)
        sample=event('e','a','read')
        for bad in (dict(sample,expected='PASS'),dict(sample,schedule={}),dict(sample,kind='future'),dict(sample,actor='c')):
            with self.assertRaises(ValueError):
                protocol.event(bad)
        with self.assertRaises(ValueError):
            protocol.event(event('p','a','policy',clauses=[[True]]))

    def test_invalid_schedule_is_rejected_but_deleted_endpoints_are_defined(self):
        original=scenarios()[5]
        for pair in (['ra'],['ra','ra'],['ca','cb'],['rb','ra']):
            case=deepcopy(original)
            case['schedule']['reserve_pair']=pair
            with self.assertRaises(ValueError):
                validate_case(case)
        original['events']=[e for e in original['events'] if e['event_id']!='ra']
        validate_case(original)

    def test_historical_intent_retry_is_rejected_before_scheduling_threads(self):
        case=scenarios()[5]
        case['public']['capacity']=2
        case['events']=[event('cb','b','certify'),event('old','b','reserve',permit='cb'),event('ca','a','certify'),
                        event('ra','a','reserve',permit='ca'),event('rb','b','reserve',permit='cb')]
        with self.assertRaisesRegex(ValueError,'fresh attempts'):
            validate_case(case)
        with TemporaryDirectory() as directory,InterleavingSession(case['public'],directory) as session:
            for e in case['events'][:3]:
                session.apply(e)
            with self.assertRaisesRegex(ScheduleError,'fresh attempts'):
                reserve_pair(session,case['events'][3],case['events'][4],lambda *_:None,lambda *_:None,timeout=.1)
            self.assertEqual(session.projection()['intents'],['b'])

    def test_input_bounds_duplicate_events_and_reused_output_fail_closed(self):
        case=scenarios()[0]
        case['events']*=2
        with self.assertRaises(ValueError):
            validate_case(case)
        with TemporaryDirectory() as directory:
            with self.assertRaises(FileExistsError):
                run_case(scenarios()[0],directory)
            with InterleavingSession(scenarios()[0]['public'],directory) as session:
                for index in range(64):
                    session.apply(event(str(index),'a','read'))
                with self.assertRaises(ValueError):
                    session.apply(event('overflow','a','read'))

    def test_oracle_has_only_standard_library_imports_and_is_cold(self):
        tree=ast.parse((ROOT/'validation_lab'/'interleaving_oracle.py').read_text())
        self.assertEqual([n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)],['itertools'])
        self.assertFalse(any(isinstance(n,ast.Import) for n in ast.walk(tree)))
        case=scenarios()[0]
        saved=deepcopy(case)
        result=reference_prefix(case['public'],case['events'])
        result['projection']['usable'].clear()
        self.assertEqual(reference_prefix(case['public'],case['events'])['projection']['usable'],[2])
        self.assertEqual(case,saved)
        with self.assertRaises(OracleGap):
            reference_prefix(case['public'],[event('future','a','future')])

    def test_scheduler_cleans_up_on_failed_check_without_waiting_for_a_fake_block(self):
        case=scenarios()[5]
        with TemporaryDirectory() as directory, InterleavingSession(case['public'],directory) as session:
            for e in case['events'][1:3]:
                session.apply(e)
            original=session.service._lock
            with patch.object(session.service,'_prepare_execution_intent',side_effect=RuntimeError('injected')):
                with self.assertRaisesRegex(RuntimeError,'injected'):
                    reserve_pair(session,case['events'][3],case['events'][4],lambda *_:None,lambda *_:None,timeout=.5)
            self.assertIs(session.service._lock,original)
            self.assertEqual(session.projection()['used'],0)
