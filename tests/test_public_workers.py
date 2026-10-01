"""Actual process boundaries, durable observed inboxes and interrupted commands."""
import ast
from dataclasses import asdict
from io import BytesIO, StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from reachability.dispatch_worker_state import DurableDispatchSession, read_checkpoint
from reachability.journal import RecoveryError, StoreInUse
from reachability.service import AdmissionService
from reachability.simulated_executor import SimulatedExecutor
from reachability.stream_worker import read_frame, END
from reachability.trace_protocol import DeploymentInitial, canonical, fingerprint
from validation_lab.dispatch_race_oracle import reference_prefix
from validation_lab.generate_dispatch_race_cases import event, scenarios as dispatch_cases
from validation_lab.generate_public_worker_cases import scenarios
from validation_lab.public_worker import PublicWorker, WorkerError, WorkerTimeout, ROOT, runtime_bundle
from validation_lab.run_public_workers import run_case, verify_corpus, verify_report, load_cases, main


def read(path):
    return json.loads(path.read_text())


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


class PublicWorkerCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root=Path(cls.temp.name)
        cls.bundle=cls.root/'runtime'
        runtime_bundle(cls.bundle)
        cls.cases=scenarios()
        cls.results={c['case_id']:run_case(c,cls.root/c['case_id'],bundle=cls.bundle) for c in cls.cases}

    def test_all_profiles_match_models_and_dispatch_replies_recover_in_new_processes(self):
        receipt=verify_corpus()
        self.assertEqual(load_cases(),self.cases)
        self.assertEqual(receipt['event_prefixes'],186)
        self.assertEqual(receipt['family_complete_fixtures'],0)
        self.assertEqual(sum(r['prefixes'] for r in self.results.values()),186)
        self.assertEqual(sum(r['worker_starts'] for r in self.results.values()),113)
        self.assertEqual(sum(r['recovered_prefixes'] for r in self.results.values()),97)
        self.assertEqual(sum(r['exact_retries'] for r in self.results.values()),97)

    def test_workers_receive_only_initial_state_and_delivered_commands(self):
        for case in self.cases:
            root=self.root/case['case_id']
            rows=lines(root/'exchanges.jsonl')
            for folder in sorted((root/'workers').iterdir()):
                launch=read(folder/'launch.json')
                self.assertNotEqual(launch['pid'],launch['parent_pid'])
                self.assertEqual(launch['environment'],dict(PATH='/bin:/usr/bin',LANG='C.UTF-8',LC_ALL='C.UTF-8'))
                self.assertEqual(launch['argv'][1:3],['-I','-B'])
                self.assertNotIn('validation_lab',' '.join(launch['argv']))
                self.assertEqual(list((folder/'cwd').iterdir()),[])
                sent=lines(folder/'stdin.jsonl')
                self.assertEqual(sent[0],case['public'])
                self.assertEqual(sent[1:],[r['request'] for r in rows if r['worker']==int(folder.name) and r['kind']!='ready'])
                for message in sent:
                    self.assertFalse({'source','events','recovery','schedule','expected','oracle','control'} & set(message))
        self.assertFalse((self.bundle/'validation_lab').exists())
        self.assertEqual({p.name for p in self.bundle.iterdir()},{'reachability','bundle.json'})

    def test_saved_old_receipts_and_fenced_requests_survive_process_recovery(self):
        # w12 is accepted with a lost reply, fenced, then delivered an old ack.
        rows=lines(self.root/'w12'/'exchanges.jsonl')
        ack=next(r['response']['record'] for r in rows if r['kind']=='event' and r['request']['event_id']=='ack')
        self.assertEqual(ack['projection']['attempts']['a']['dispatch']['state'],'released')
        self.assertEqual(ack['executor_effects'],1)
        # w11 releases a queued request before arrival; only the next attempt acts.
        rows=lines(self.root/'w11'/'exchanges.jsonl')
        arrival=next(r['response']['record'] for r in rows if r['kind']=='event' and r['request']['event_id']=='arrive')
        self.assertEqual(arrival['executor_effects'],0)
        self.assertTrue(arrival['projection']['transport']['receipts']['arrive']['fenced'])

    def test_raw_stdout_survives_reference_failure(self):
        def gap(*_):
            raise RuntimeError('injected reference failure')
        path=self.root/'reference-error'
        with self.assertRaisesRegex(RuntimeError,'injected'):
            run_case(self.cases[0],path,bundle=self.bundle,reference=gap)
        self.assertEqual(len(lines(path/'exchanges.jsonl')),2)
        self.assertEqual(len(lines(path/'workers'/'0000'/'stdout.jsonl')),2)
        self.assertEqual(read(path/'execution.json')['prefixes'],1)

    def test_cli_receipts_replay_raw_pipes_and_reject_corruption(self):
        path=self.root/'cli'
        with patch('sys.argv',['run_public_workers','--output',str(path)]),patch('sys.stdout',new=StringIO()):
            main()
        report=verify_report(path)
        self.assertEqual(len(report['results']),16)
        saved=(path/'report.json').read_text()
        report['results'][8]['recovered_prefixes']-=1
        (path/'report.json').write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError,'counts'):
            verify_report(path)
        (path/'report.json').write_text(saved)
        (path/'w09'/'workers'/'0001'/'stdout.jsonl').write_text('changed\n')
        with self.assertRaisesRegex(ValueError,'sources/files'):
            verify_report(path)


class CheckpointTests(unittest.TestCase):
    def test_resume_and_exact_retry_do_no_executor_io(self):
        case=dispatch_cases()[11]
        with TemporaryDirectory() as d:
            with DurableDispatchSession(DeploymentInitial(),d) as session:
                for e in case['events']:
                    row=session.apply(e)
                before=session.projection()
            with patch.object(SimulatedExecutor,'submit',side_effect=AssertionError('submit on recovery')),\
                 patch.object(SimulatedExecutor,'query',side_effect=AssertionError('query on recovery')),\
                 patch.object(SimulatedExecutor,'release',side_effect=AssertionError('release on recovery')):
                with DurableDispatchSession(DeploymentInitial(),d,resume=True) as session:
                    self.assertEqual(session.apply(e),row)
                    self.assertTrue(session.replayed)
            with DurableDispatchSession(DeploymentInitial(),d,resume=True) as session:
                self.assertEqual(session.projection(),before)

    def test_rebinding_completed_identity_rejected_and_returned_replies_detached(self):
        with TemporaryDirectory() as d,DurableDispatchSession(DeploymentInitial(),d) as session:
            e=event('missing','arrive',request_event='x')
            row=session.apply(e)
            row['outcome']['status']='PASS'
            self.assertEqual(session.apply(e)['outcome']['status'],'FAIL')
            checkpoint=session.checkpoint_path.read_bytes()
            with self.assertRaisesRegex(ValueError,'rebound'):
                session.apply(event('missing','arrive',request_event='different'))
            self.assertEqual(session.checkpoint_path.read_bytes(),checkpoint)
            historical=session.apply(e)
            session.apply(event('new','fact',name='tested',valid_until=None))
            self.assertEqual(session.apply(e),historical)
            self.assertNotEqual(session.projection(),historical['projection'])
            self.assertEqual(len(session.completed),2)

    def test_wrapper_lock_survives_in_session_journal_restart(self):
        with TemporaryDirectory() as d,DurableDispatchSession(DeploymentInitial(),d) as session:
            session.apply(event('restart','restart'))
            with self.assertRaises(StoreInUse):
                DurableDispatchSession(DeploymentInitial(),d,resume=True)
            self.assertEqual(session.apply(event('missing','deliver',receipt_event='none'))['outcome']['status'],'FAIL')

    def test_wrong_initial_missing_journal_and_corrupt_checkpoint_fail_closed(self):
        with TemporaryDirectory() as d:
            with DurableDispatchSession(DeploymentInitial(),d):
                pass
            with self.assertRaisesRegex(RecoveryError,'initial'):
                DurableDispatchSession(DeploymentInitial(capacity=2),d,resume=True)
            path=Path(d)/'worker-checkpoint.json'
            original=path.read_bytes()
            envelope=read(path)
            envelope['digest']='0'*64
            path.write_text(json.dumps(envelope))
            with self.assertRaisesRegex(RecoveryError,'integrity'):
                DurableDispatchSession(DeploymentInitial(),d,resume=True)
            path.write_bytes(original)
            (Path(d)/'executor.db').unlink()
            with self.assertRaisesRegex(RecoveryError,'both existing'):
                DurableDispatchSession(DeploymentInitial(),d,resume=True)
            self.assertFalse((Path(d)/'executor.db').exists())

    def test_older_checkpoint_cannot_hide_journal_changes(self):
        with TemporaryDirectory() as d:
            with DurableDispatchSession(DeploymentInitial(),d) as session:
                saved=session.checkpoint_path.read_bytes()
                session.apply(event('t','fact',name='tested',valid_until=None))
            (Path(d)/'worker-checkpoint.json').write_bytes(saved)
            with self.assertRaisesRegex(RecoveryError,'journals differ'):
                DurableDispatchSession(DeploymentInitial(),d,resume=True)

    def test_external_journal_mutation_is_not_absorbed_by_resume(self):
        for target in ('authority','executor'):
            with self.subTest(target=target),TemporaryDirectory() as d:
                with DurableDispatchSession(DeploymentInitial(),d) as session:
                    for e in dispatch_cases()[11]['events'][:6]:
                        session.apply(e)
                    request=session.requests['s']
                if target=='authority':
                    with AdmissionService(database=Path(d)/'admission.db') as service:
                        service.advance_clock('c0',1,idempotency_key='external-clock')
                else:
                    with SimulatedExecutor(Path(d)/'executor.db') as executor:
                        executor.release(request)
                with self.assertRaisesRegex(RecoveryError,'journals differ'):
                    DurableDispatchSession(DeploymentInitial(),d,resume=True)

    def test_storage_failure_poisons_live_wrapper_and_pending_resume_is_refused(self):
        with TemporaryDirectory() as d:
            session=DurableDispatchSession(DeploymentInitial(),d)
            original=session._save
            count=0
            def fail_second():
                nonlocal count
                count+=1
                if count==2:
                    raise OSError('checkpoint disk failure')
                original()
            with patch.object(session,'_save',fail_second):
                with self.assertRaisesRegex(OSError,'disk failure'):
                    session.apply(event('t','fact',name='tested',valid_until=None))
            with self.assertRaises(RecoveryError):
                session.apply(event('other','restart'))
            session.close()
            with self.assertRaisesRegex(RecoveryError,'interrupted'):
                DurableDispatchSession(DeploymentInitial(),d,resume=True)

    def test_invalid_public_fields_do_not_start_a_pending_command(self):
        with TemporaryDirectory() as d,DurableDispatchSession(DeploymentInitial(),d) as session:
            before=session.checkpoint_path.read_bytes()
            with self.assertRaises(ValueError):
                session.apply(dict(event('x','restart'),schedule={'future':True}))
            self.assertEqual(session.checkpoint_path.read_bytes(),before)

    def test_64_event_limit_survives_resume_and_does_not_count_retries(self):
        with TemporaryDirectory() as d:
            with DurableDispatchSession(DeploymentInitial(),d) as session:
                for index in range(64):
                    message=event(str(index),'arrive',request_event='missing')
                    session.apply(message)
            with DurableDispatchSession(DeploymentInitial(),d,resume=True) as session:
                self.assertEqual(session.apply(message)['outcome']['status'],'FAIL')
                with self.assertRaisesRegex(ValueError,'bound'):
                    session.apply(event('overflow','restart'))
                self.assertIsNone(read_checkpoint(session.checkpoint_path)['pending'])


class ProcessCrashTests(unittest.TestCase):
    def prepare(self,root):
        runtime_bundle(root/'runtime')
        case=dispatch_cases()[8]
        with DurableDispatchSession(DeploymentInitial(),root/'state') as session:
            for e in case['events'][:5]:
                session.apply(e)
        return case

    def test_crashes_before_command_after_effect_and_before_checkpoint_refuse_resume(self):
        for stage in ('before-command','after-effect','before-completed-checkpoint'):
            with self.subTest(stage=stage),TemporaryDirectory() as d:
                root=Path(d); case=self.prepare(root)
                if stage=='after-effect':
                    path=root/'runtime'/'reachability'/'simulated_executor.py'
                    source=path.read_text().replace('return self._write("submit", request)',
                        'receipt = self._write("submit", request)\n        __import__("os")._exit(72)\n        return receipt')
                else:
                    path=root/'runtime'/'reachability'/'dispatch_worker_state.py'
                    source=path.read_text()
                    needle=('row = super().apply(message)' if stage=='before-command' else
                            'self._save()  # Must precede a successful response on stdout.')
                    source=source.replace(needle,'os._exit(71)\n            '+needle)
                path.write_text(source)
                worker=PublicWorker(root/'runtime','dispatch',root/'state',root/'crash',resume=True)
                try:
                    worker.request(case['public'])
                    with self.assertRaises(WorkerError):
                        worker.request(case['events'][5])
                finally:
                    worker.stop(kill=True)
                self.assertEqual(len(lines(root/'crash'/'stdout.jsonl')),1)
                with self.assertRaisesRegex(RecoveryError,'interrupted'):
                    DurableDispatchSession(DeploymentInitial(),root/'state',resume=True)
                with SimulatedExecutor(root/'state'/'executor.db') as executor:
                    self.assertEqual(executor.total_effects,int(stage!='before-command'))

    def test_lost_stdout_after_completed_checkpoint_returns_saved_reply_without_resend(self):
        with TemporaryDirectory() as d:
            root=Path(d); case=self.prepare(root)
            path=root/'runtime'/'reachability'/'stream_worker.py'
            original=path.read_text()
            path.write_text(original.replace('def emit(value):',
                'def emit(value):\n    if value.get("kind") == "event":\n        __import__("os")._exit(74)'))
            worker=PublicWorker(root/'runtime','dispatch',root/'state',root/'lost-output',resume=True)
            try:
                worker.request(case['public'])
                with self.assertRaises(WorkerError):
                    worker.request(case['events'][5])
            finally:
                worker.stop(kill=True)
            path.write_text(original)
            worker=PublicWorker(root/'runtime','dispatch',root/'state',root/'resumed',resume=True)
            try:
                ready=worker.request(case['public'])
                self.assertEqual(ready['completed'],6)
                self.assertEqual(ready['executor_effects'],1)
                reply=worker.request(case['events'][5])
                self.assertTrue(reply['replayed'])
                self.assertEqual(reply['record']['projection'],reference_prefix(case['public'],case['events'][:6])['projection'])
                self.assertEqual(reply['record']['projection']['attempts']['a']['dispatch']['state'],'uncertain')
            finally:
                worker.stop()


class PipeBoundaryTests(unittest.TestCase):
    def test_frame_size_utf8_and_eof_are_distinct_from_json_null(self):
        self.assertIs(read_frame(BytesIO()),END)
        self.assertIsNone(read_frame(BytesIO(b'null\n')))
        self.assertEqual(read_frame(BytesIO(b'"'+b'x'*65533+b'"\n')),'x'*65533)
        for data in (b'"'+b'x'*65534+b'"\n',b'{}',b'\xff\n'):
            with self.assertRaises(ValueError):
                read_frame(BytesIO(data))

    def test_bad_initial_fields_and_resume_for_unsupported_profile_fail_without_ack(self):
        for profile,public,resume in (('dispatch',dict(asdict(DeploymentInitial()),future=[]),False),
                                      ('deployment',asdict(DeploymentInitial()),True)):
            with TemporaryDirectory() as d:
                root=Path(d); runtime_bundle(root/'runtime')
                worker=PublicWorker(root/'runtime',profile,root/'state',root/'evidence',resume=resume)
                try:
                    with self.assertRaises(WorkerError):
                        worker.request(public)
                finally:
                    worker.stop(kill=True)
                self.assertEqual((root/'evidence'/'stdout.jsonl').read_bytes(),b'')
                self.assertEqual(read(root/'evidence'/'exit.json')['returncode'],2)
                self.assertFalse((root/'state'/'admission.db').exists())

    def test_malformed_duplicate_fields_and_unknown_command_are_raw_worker_errors(self):
        for message in (b'{"schema":"x","schema":"y"}\n',b'{not json}\n',b'null\n',
                        (canonical(dict(event('bad','restart'),expected='PASS'))+'\n').encode()):
            with TemporaryDirectory() as d:
                root=Path(d); runtime_bundle(root/'runtime')
                worker=PublicWorker(root/'runtime','dispatch',root/'state',root/'evidence')
                try:
                    worker.request(asdict(DeploymentInitial()))
                    with self.assertRaises(WorkerError):
                        worker.exchange_bytes(message)
                finally:
                    worker.stop(kill=True)
                self.assertTrue((root/'evidence'/'stdin.jsonl').read_bytes().endswith(message))
                self.assertEqual(len(lines(root/'evidence'/'stdout.jsonl')),1)
                self.assertIsNone(read_checkpoint(root/'state'/'worker-checkpoint.json')['pending'])

    def fake_worker(self,root,body,**options):
        runtime_bundle(root/'runtime')
        (root/'runtime'/'reachability'/'stream_worker.py').write_text('def main():\n'+body+'\n')
        return PublicWorker(root/'runtime','dispatch',root/'state',root/'evidence',**options)

    def test_partial_stdout_timeout_is_bounded_and_raw_bytes_are_retained(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            worker=self.fake_worker(root,'    import sys,time\n    sys.stdout.write("partial")\n    sys.stdout.flush()\n    time.sleep(5)',timeout=.2)
            try:
                with self.assertRaises(WorkerTimeout):
                    worker.request(asdict(DeploymentInitial()))
            finally:
                worker.stop(kill=True)
            self.assertEqual((root/'evidence'/'stdout.jsonl').read_bytes(),b'partial')

    def test_child_environment_and_import_path_exclude_parent_evaluator_state(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            body=('    import os,json,importlib.util\n'
                  '    print(json.dumps(dict(secret=os.getenv("EVALUATOR_SECRET"),'
                  'evaluator=importlib.util.find_spec("validation_lab") is not None)))')
            with patch.dict('os.environ',{'EVALUATOR_SECRET':'must-stay-in-parent','PYTHONPATH':str(ROOT)}):
                worker=self.fake_worker(root,body)
            try:
                self.assertEqual(worker.request({}),dict(secret=None,evaluator=False))
            finally:
                worker.stop()

    def test_oversized_duplicate_and_unsolicited_stdout_fail_closed(self):
        for body,options in (('    print("x"*128)',dict(max_response=64)),
            ('    print(\'{"x":1,"x":2}\')',{}),('    print("{}\\n{}")',{})):
            with TemporaryDirectory() as d:
                root=Path(d); worker=self.fake_worker(root,body,**options)
                try:
                    with self.assertRaises(WorkerError):
                        worker.request(asdict(DeploymentInitial()))
                finally:
                    worker.stop(kill=True)
                self.assertTrue((root/'evidence'/'stdout.jsonl').read_bytes())

    def test_runtime_imports_neither_evaluator_nor_process_control(self):
        for name in ('stream_worker','dispatch_worker_state'):
            tree=ast.parse((ROOT/'reachability'/(name+'.py')).read_text())
            for node in ast.walk(tree):
                modules=([node.module or ''] if isinstance(node,ast.ImportFrom) else
                         [alias.name for alias in node.names] if isinstance(node,ast.Import) else [])
                self.assertFalse(any(m.startswith(('validation_lab','tests','subprocess')) for m in modules))
