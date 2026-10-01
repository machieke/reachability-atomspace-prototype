"""Real dispatch locking, immutable receipt ordering and independent cold evidence."""
import ast
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from reachability.dispatch import DispatchMixin, Dispatcher
from reachability.dispatch_race_protocol import parse
from reachability.dispatch_race_session import DispatchRaceSession
from reachability.simulated_executor import SimulatedExecutor
from reachability.trace_protocol import DeploymentInitial
from validation_lab.dispatch_race_mutations import mutate
from validation_lab.dispatch_race_oracle import OracleGap, reference_prefix
from validation_lab.dispatch_race_schedule import dispatch_pair, ScheduleError
from validation_lab.generate_dispatch_race_cases import event, scenarios
from validation_lab.run_deployment import ConformanceMismatch
from validation_lab.run_dispatch_races import (CORPUS, ROOT, DispatchRacePredicate, load_cases, main, reduce_case,
    run_case, semantic_result, validate_case, verify_corpus, verify_report)


def read(path):
    return json.loads(path.read_text())


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


class DispatchRaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.output=Path(cls.temp.name)
        cls.cases=scenarios()
        cls.results={c['case_id']:run_case(c,cls.output/c['case_id']) for c in cls.cases}
        cls.reductions={c['mutant']:reduce_case(c,c['mutant'],cls.output/c['mutant']) for c in cls.cases if c['mutant']}

    def rows(self,case):
        return {r['outcome']['event_id']:r for r in lines(self.output/case/'actual.jsonl')}

    def test_all_prefixes_match_cold_model_and_both_journals_recover(self):
        receipt=verify_corpus()
        self.assertEqual(load_cases(),self.cases)
        self.assertEqual(len(self.cases),24)
        self.assertEqual(sum(r['prefixes'] for r in self.results.values()),receipt['event_prefixes'])
        self.assertEqual(receipt['family_complete_fixtures'],0)
        for case in self.cases:
            self.assertEqual(self.results[case['case_id']]['recovery_checkpoints'],len(case['events'])-bool(case['schedule']['pair']))

    def test_actual_lock_blocks_revocation_and_expiry_on_both_sides_of_effect(self):
        for index in range(4,8):
            case=self.cases[index]
            notes=lines(self.output/case['case_id']/'schedule.jsonl')
            self.assertTrue(notes[0]['authority_lock_held'])
            self.assertTrue(notes[1]['blocked_by_first'])
            self.assertEqual(notes[0]['executor_effects'],int(case['schedule']['checkpoint']=='before_ack'))
            self.assertEqual(self.rows(case['case_id'])['s']['projection']['attempts']['a']['dispatch']['state'],'accepted')

    def test_revoked_or_expired_current_gates_never_send(self):
        for case,status in (('dr01','UNKNOWN'),('dr03','STALE'),('dr04','STALE')):
            row=self.rows(case)['s']
            self.assertEqual(row['outcome']['status'],status)
            self.assertEqual(row['executor_effects'],0)
            self.assertEqual(row['projection']['transport']['requests'],{})
        self.assertEqual(self.rows('dr02')['retry']['executor_effects'],1)
        self.assertEqual(self.rows('dr23')['s']['executor_effects'],1)

    def test_expiry_and_delayed_ack_keep_occupancy_without_completion_or_relief(self):
        for case in ('dr09','dr10'):
            rows=self.rows(case)
            self.assertEqual(rows['x']['projection']['resource'],dict(used=0,uncertain=['a']))
            self.assertEqual(rows['rb']['outcome']['status'],'UNKNOWN')
            p=rows['ack']['projection']
            self.assertEqual(p['attempts']['a']['dispatch']['state'],'accepted')
            self.assertEqual(p['attempts']['a']['intent']['state'],'reconciliation_required')
            self.assertEqual(p['stage'],'DRAFT')
            self.assertEqual(p['goal']['outstanding'],10)
            self.assertEqual(p['attempts']['a']['observed'],[])
            self.assertEqual(rows['again']['outcome']['status'],'PASS')

    def test_delayed_request_can_effect_after_expiry_until_fenced(self):
        rows=self.rows('dr10')
        self.assertEqual(rows['x']['executor_effects'],0)
        self.assertEqual(rows['arrive']['executor_effects'],1)
        self.assertEqual(rows['arrive']['projection']['attempts']['a']['dispatch']['state'],'uncertain')
        rows=self.rows('dr11')
        self.assertEqual(rows['arrive']['executor_effects'],0)
        self.assertTrue(rows['arrive']['projection']['transport']['receipts']['arrive']['fenced'])
        self.assertEqual(rows['sb']['executor_effects'],1)

    def test_old_ack_cannot_undo_release_or_lower_historical_effects(self):
        for case in ('dr12','dr22'):
            row=self.rows(case)['ack']
            self.assertEqual(row['projection']['attempts']['a']['dispatch']['state'],'released')
            self.assertEqual(row['projection']['attempts']['a']['dispatch']['effect_count'],1)
        self.assertEqual(self.rows('dr22')['old-ack']['executor_effects'],2)

    def test_duplicate_arrivals_receipts_retries_and_queries_have_one_effect(self):
        for case in ('dr13','dr21'):
            row=list(self.rows(case).values())[-1]
            self.assertEqual(row['executor_effects'],1)
            self.assertEqual(row['projection']['executor']['a']['effects'],1)
        rows=self.rows('dr14')
        self.assertEqual(rows['query']['projection']['attempts']['a']['dispatch']['state'],'uncertain')
        self.assertEqual(rows['rb']['outcome']['status'],'UNKNOWN')

    def test_transport_missing_references_and_unsent_fault_have_no_effect(self):
        for case in ('dr16','dr17'):
            rows=self.rows(case)
            self.assertEqual(rows['arrive']['outcome']['status'],'FAIL')
            self.assertEqual(rows['ack']['outcome']['status'],'FAIL')
            self.assertEqual(list(rows.values())[-1]['executor_effects'],0)

    def test_completed_and_rejected_dispatches_need_no_submission_checkpoint(self):
        for case in ('dr18','dr19','dr24'):
            notes=lines(self.output/case/'schedule.jsonl')
            self.assertEqual([n['point'] for n in notes],['done'])

    def test_pinned_diagnostic_reductions_keep_same_signature_and_schedule(self):
        for name,result in self.reductions.items():
            expected=read(CORPUS/'mutations'/(name+'.json'))
            self.assertEqual(semantic_result(result),expected['result'])
            self.assertTrue(result['one_minimal'])
            self.assertFalse(result['global_minimum'])
            self.assertEqual(read(self.output/name/'reduced.json')['schedule'],expected['case']['schedule'])
            final=self.output/name/'trials'/f"{result['final_trial']:04d}"
            self.assertGreater(read(final/'assessment.json')['invocations'],0)
        cached=self.reductions['cached-send-gate']['signature']
        self.assertEqual((cached['expected'],cached['actual']),('UNKNOWN','PASS'))

    def test_fresh_witness_and_every_remaining_single_deletion(self):
        for name,result in self.reductions.items():
            case=read(CORPUS/'mutations'/(name+'.json'))['case']
            predicate=DispatchRacePredicate(case,name,self.output/('fresh-'+name))
            actual=predicate(result['reduced_events'],0)
            self.assertEqual(actual['kind'],'WITNESS')
            self.assertEqual(actual['signature'],result['signature'])
            for index in range(len(result['reduced_events'])):
                actual=predicate(result['reduced_events'][:index]+result['reduced_events'][index+1:],index+1)
                self.assertEqual(actual['kind'],'NO_WITNESS')
                self.assertTrue(actual['control_passed'])

    def test_repeat_schedule_is_deterministic(self):
        for case in self.cases[4:8]:
            path=self.output/('repeat-'+case['case_id'])
            run_case(case,path)
            for name in ('actual.jsonl','schedule.jsonl'):
                self.assertEqual((path/name).read_text(),(self.output/case['case_id']/name).read_text())

    def test_raw_event_retained_before_oracle_gap(self):
        def gap(public,prefix):
            if prefix:
                raise OracleGap('injected')
            return reference_prefix(public,prefix)
        path=self.output/'gap'
        with self.assertRaises(OracleGap):
            run_case(self.cases[0],path,reference=gap)
        self.assertEqual(len(lines(path/'actual.jsonl')),1)

    def test_failed_control_prevents_mutant_and_budget_does_not_prove_minimality(self):
        p=DispatchRacePredicate(self.cases[0],'cached-send-gate',self.output/'failed-control')
        with patch('validation_lab.run_dispatch_races.run_case',side_effect=ConformanceMismatch('x','projection',1,2)) as replay:
            result=p(self.cases[0]['events'],0)
        self.assertEqual(replay.call_count,1)
        self.assertEqual(result['kind'],'CONTROL_MISMATCH')
        result=reduce_case(self.cases[0],'cached-send-gate',self.output/'budget',max_evaluations=1)
        self.assertEqual(result['status'],'BUDGET_EXHAUSTED')
        self.assertFalse(result['one_minimal'])

    def test_cli_report_receipts_reject_corrupted_raw_evidence(self):
        path=self.output/'cli'
        with patch('sys.argv',['run_dispatch_races','--output',str(path)]),patch('sys.stdout',new=StringIO()):
            main()
        self.assertEqual(len(verify_report(path)['results']),24)
        (path/'dr01'/'actual.jsonl').write_text('tampered\n')
        with self.assertRaisesRegex(ValueError,'sources/files'):
            verify_report(path)


class DispatchRaceBoundaries(unittest.TestCase):
    def test_public_protocol_excludes_future_schedule_labels_and_invalid_references(self):
        sample=event('s','dispatch',attempt_id='a',fault='queued')
        self.assertEqual(parse(sample),sample)
        for bad in (dict(sample,schedule={}),dict(sample,expected='PASS'),dict(sample,kind='future'),
                    event('a','arrive',request_event=True),event('a','deliver',receipt_event='s',future=True)):
            with self.assertRaises(ValueError):
                parse(bad)
        for pair in (['s'],['s','s'],['r','s'],['x','s']):
            case=scenarios()[5]
            case['schedule']['pair']=pair
            with self.assertRaises(ValueError):
                validate_case(case)
        case=scenarios()[5]
        case['events']=[e for e in case['events'] if e['event_id']!='s']
        validate_case(case)

    def test_event_budget_duplicate_identity_and_output_reuse_rejected(self):
        with TemporaryDirectory() as directory:
            with self.assertRaises(FileExistsError):
                run_case(scenarios()[0],directory)
            with DispatchRaceSession(DeploymentInitial(),directory) as session:
                for index in range(64):
                    session.execute(event(str(index),'arrive',request_event='missing'))
                with self.assertRaises(ValueError):
                    session.execute(event('overflow','restart'))
                with self.assertRaises(ValueError):
                    session.execute(event('0','restart'))

    def test_recovery_does_not_call_executor_io_and_retains_observed_inbox(self):
        case=scenarios()[14]
        with TemporaryDirectory() as directory,DispatchRaceSession(DeploymentInitial(),directory) as session:
            for e in case['events']:
                session.execute(e)
            before=session.projection()
            with patch.object(SimulatedExecutor,'submit',side_effect=AssertionError('replay submit')),\
                 patch.object(SimulatedExecutor,'query',side_effect=AssertionError('replay query')),\
                 patch.object(SimulatedExecutor,'release',side_effect=AssertionError('replay release')):
                session.restart()
            self.assertEqual(session.projection(),before)

    def test_scheduler_restores_lock_and_workers_after_submit_error(self):
        case=scenarios()[4]
        with TemporaryDirectory() as directory,DispatchRaceSession(DeploymentInitial(),directory) as session:
            for e in case['events'][:5]:
                session.execute(e)
            original=session.service._lock
            with patch.object(session.executor,'submit',side_effect=RuntimeError('injected')):
                with self.assertRaisesRegex(RuntimeError,'injected'):
                    dispatch_pair(session,*case['events'][5:7],'before_send',lambda *_:None,lambda *_:None,timeout=.5)
            self.assertIs(session.service._lock,original)
            self.assertEqual(session.executor.total_effects,0)

    def test_scheduler_detects_actual_send_without_the_authority_lock(self):
        def unlocked(dispatcher, attempt, policy, revision, owner):
            record=dispatcher.service.prepare_dispatch(attempt,policy,revision,owner,idempotency_key='unsafe-test')
            return dispatcher.executor.submit(record.request)
        case=scenarios()[4]
        with TemporaryDirectory() as directory,DispatchRaceSession(DeploymentInitial(),directory) as session:
            for e in case['events'][:5]:
                session.execute(e)
            original=session.service._lock
            notes=[]
            with patch.object(Dispatcher,'dispatch',unlocked):
                with self.assertRaisesRegex(ScheduleError,'lock absent'):
                    dispatch_pair(session,*case['events'][5:7],'before_send',lambda *_:None,notes.append,timeout=.5)
            self.assertFalse(notes[0]['authority_lock_held'])
            self.assertIs(session.service._lock,original)
            self.assertEqual(session.executor.total_effects,0)

    def test_diagnostic_mutations_restore_methods_and_do_not_invent_designated_ids(self):
        original=DispatchMixin._dispatch_submission_checks
        with self.assertRaisesRegex(RuntimeError,'injected'):
            with mutate('cached-send-gate'):
                self.assertIsNot(DispatchMixin._dispatch_submission_checks,original)
                raise RuntimeError('injected')
        self.assertIs(DispatchMixin._dispatch_submission_checks,original)
        for name in ('M09','M12'):
            with self.assertRaises(ValueError):
                with mutate(name):
                    pass

    def test_model_is_independent_cold_and_does_not_mutate_inputs(self):
        tree=ast.parse((ROOT/'validation_lab'/'dispatch_race_oracle.py').read_text())
        self.assertEqual([n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)],['copy','deployment_oracle'])
        self.assertFalse(any(isinstance(n,ast.Import) for n in ast.walk(tree)))
        case=scenarios()[11]
        saved=deepcopy(case)
        result=reference_prefix(case['public'],case['events'])
        result['projection']['transport']['receipts'].clear()
        self.assertTrue(reference_prefix(case['public'],case['events'])['projection']['transport']['receipts'])
        self.assertEqual(case,saved)
