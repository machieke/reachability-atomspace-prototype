"""Quiescent wrapper metadata, preserved historical replies and crash boundaries."""
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from reachability.admission_protocol import AdmissionInitial, event as ae
from reachability.admission_trace import AdmissionSession
from reachability.codec import encode
from reachability.deployment_trace import DeploymentSession
from reachability.dispatch_worker_state import read_checkpoint
from reachability.journal import RecoveryError, StoreInUse
from reachability.pln_adapter import PeTTaFormulaRuntime
from reachability.service import AdmissionService
from reachability.simulated_executor import SimulatedExecutor
from reachability.trace_protocol import DeploymentInitial, event as de, canonical, fingerprint
from reachability.trace_worker_state import DurableAdmissionSession, DurableDeploymentSession, SCHEMA
from validation_lab.generate_admission_cases import initial as admission_initial, scenarios as admission_cases
from validation_lab.generate_deployment_cases import scenarios as deployment_cases
from validation_lab.public_worker import PublicWorker, WorkerError, runtime_bundle

PROFILES=(('admission',DurableAdmissionSession,admission_initial()),('deployment',DurableDeploymentSession,DeploymentInitial()))


def public(initial):
    return initial.wire() if hasattr(initial,'wire') else asdict(initial)


def load_state(directory):
    return read_checkpoint(Path(directory)/'worker-checkpoint.json',schema=SCHEMA)


def modify_state(directory,change):
    path=Path(directory)/'worker-checkpoint.json'
    body=load_state(directory)
    change(body)
    body=encode(body)
    path.write_text(canonical(dict(schema=SCHEMA,body=body,digest=fingerprint(body))))


def ready_event(profile):
    return (ae('ctx','context',context_id='c0',assumptions=[],clauses=[]) if profile=='admission'
            else de('tested','fact',name='tested',valid_until=None))


def event(profile,name,kind='restart'):
    return (ae if profile=='admission' else de)(name,kind)


class TraceMetadataTests(unittest.TestCase):
    def test_nonlexical_hard_alias_order_survives_restore_and_future_derivation(self):
        initial=admission_initial()
        with TemporaryDirectory() as d:
            with DurableAdmissionSession(initial,d) as s:
                s.apply(ready_event('admission'))
                s.apply(ae('z-original','evidence',context_id='c0',literal=1,roots=['source'],valid_until=None))
                last=s.apply(ae('a-duplicate','adopt',context_id='c0',evidence_id='z-original'))
            with DurableAdmissionSession(initial,d,resume=True) as s:
                self.assertEqual(list(s.hard),['z-original','a-duplicate'])
                self.assertEqual(s.projection(),last['projection'])
                self.assertEqual(s.projection()['aliases']['hard']['a-duplicate'],'z-original')
                derived=s.apply(ae('derive','derive',context_id='c0',rule_id='r2',premises=['a-duplicate']))
                self.assertEqual(derived['projection']['hard']['derive']['premises'],['z-original'])

    def test_nonlexical_numeric_alias_order_and_independence_survive_restore(self):
        events=deepcopy(admission_cases()[12]['events'])
        # Both revision orders produce the same belief; the first alias must win
        # even if checkpoint object-key sorting would put the second one first.
        events[5]['event_id'],events[6]['event_id']='z-first-revision','a-second-revision'
        with TemporaryDirectory() as d:
            with DurableAdmissionSession(admission_initial(),d) as s:
                for message in events:
                    row=s.apply(message)
            with DurableAdmissionSession(admission_initial(),d,resume=True) as s:
                self.assertEqual(s.projection(),row['projection'])
                self.assertEqual(s.projection()['aliases']['numeric']['a-second-revision'],'z-first-revision')
                self.assertEqual(s.apply(events[-1]),row)

    def test_rule_replacement_failed_retry_contexts_and_key_counter_are_preserved(self):
        messages=admission_cases()[3]['events']
        with TemporaryDirectory() as d:
            with DurableAdmissionSession(admission_initial(),d) as s:
                for message in messages:
                    row=s.apply(message)
                before=s._metadata()
            with DurableAdmissionSession(admission_initial(),d,resume=True) as s:
                self.assertEqual(s._metadata(),before)
                self.assertEqual(s.rules['r0']['revision'],'2')
                self.assertEqual(s.apply(messages[-1]),row)
                self.assertEqual(row['outcome']['status'],'STALE')
                self.assertEqual(s._metadata(),before)
                s.apply(ae('new-evidence','evidence',context_id='c0',literal=4,roots=['fresh'],valid_until=None))
                keys=[e.key for e in s.service._journal.entries() if e.key.startswith('admission-trace:new-evidence:')]
                self.assertEqual(int(keys[0].rsplit(':',1)[1]),before['next_key'])

    def test_restore_and_exact_retry_use_neither_event_execution_nor_numeric_executor_io(self):
        for profile,cls,initial in PROFILES:
            with self.subTest(profile=profile),TemporaryDirectory() as d:
                messages=admission_cases()[12]['events'] if profile=='admission' else deployment_cases()[2]['events']
                with cls(initial,d) as s:
                    for message in messages:
                        row=s.apply(message)
                    tips=s._tips()
                base=AdmissionSession if profile=='admission' else DeploymentSession
                with patch.object(base,'_execute',side_effect=AssertionError('event replay')),\
                     patch.object(PeTTaFormulaRuntime,'evaluate',side_effect=AssertionError('native inference I/O')),\
                     patch.object(SimulatedExecutor,'submit',side_effect=AssertionError('submission')),\
                     patch.object(SimulatedExecutor,'query',side_effect=AssertionError('query')),\
                     patch.object(SimulatedExecutor,'release',side_effect=AssertionError('release')):
                    with cls(initial,d,resume=True) as s:
                        self.assertEqual(s.apply(message),row)
                        self.assertTrue(s.replayed)
                        self.assertEqual(s._tips(),tips)

    def test_128_event_budget_and_failed_replies_survive_restarts(self):
        for profile,cls,initial in PROFILES:
            with self.subTest(profile=profile),TemporaryDirectory() as d:
                with cls(initial,d) as s:
                    for index in range(128):
                        message=event(profile,str(index))
                        row=s.apply(message)
                with cls(initial,d,resume=True) as s:
                    self.assertEqual(s.step,128)
                    self.assertEqual(s.apply(message),row)
                    with self.assertRaisesRegex(ValueError,'bound'):
                        s.apply(event(profile,'overflow'))
                    self.assertIsNone(load_state(d)['pending'])

    def test_context_limit_is_retained_and_rejection_does_not_mark_pending(self):
        with TemporaryDirectory() as d:
            with DurableAdmissionSession(admission_initial(),d) as s:
                for index in range(4):
                    s.apply(ae('c'+str(index),'context',context_id='c'+str(index),assumptions=[],clauses=[]))
            with DurableAdmissionSession(admission_initial(),d,resume=True) as s:
                before=s.checkpoint_path.read_bytes()
                with self.assertRaisesRegex(ValueError,'four contexts'):
                    s.apply(ae('fifth','context',context_id='c4',assumptions=[],clauses=[]))
                self.assertEqual(s.checkpoint_path.read_bytes(),before)

    def test_deployment_monitor_goal_and_completion_history_survive_restore(self):
        for index in (0,6,7):
            with self.subTest(case=index),TemporaryDirectory() as d:
                with DurableDeploymentSession(DeploymentInitial(),d) as s:
                    for message in deployment_cases()[index]['events']:
                        row=s.apply(message)
                    before=s._metadata()
                with DurableDeploymentSession(DeploymentInitial(),d,resume=True) as s:
                    self.assertEqual(s._metadata(),before)
                    self.assertEqual(s.projection(),row['projection'])
                    self.assertEqual(s.apply(message),row)

    def test_completed_reply_is_historical_detached_and_preserves_exact_diagnostics(self):
        for profile,cls,initial in PROFILES:
            with self.subTest(profile=profile),TemporaryDirectory() as d:
                first=ready_event(profile)
                with cls(initial,d) as s:
                    original=s.apply(first)
                    saved=deepcopy(original)
                    original['diagnostics']['elapsed_ns']=-1
                    s.apply(event(profile,'later'))
                with cls(initial,d,resume=True) as s:
                    self.assertEqual(s.apply(first),saved)
                    self.assertEqual(s.step,2)
                    changed=deepcopy(first)
                    changed['arguments']['context_id' if profile=='admission' else 'name']='c1' if profile=='admission' else 'credential'
                    before=s.checkpoint_path.read_bytes()
                    with self.assertRaisesRegex(ValueError,'rebound'):
                        s.apply(changed)
                    self.assertEqual(s.checkpoint_path.read_bytes(),before)

    def test_internal_restart_preserves_wrapper_ownership(self):
        for profile,cls,initial in PROFILES:
            with self.subTest(profile=profile),TemporaryDirectory() as d,cls(initial,d) as s:
                s.apply(event(profile,'reopen'))
                with self.assertRaises(StoreInUse):
                    cls(initial,d,resume=True)
                self.assertEqual(s.apply(ready_event(profile))['outcome']['status'],'PASS')


class TraceCheckpointBoundaries(unittest.TestCase):
    def test_missing_checkpoint_never_recreates_an_existing_stream(self):
        for profile,cls,initial in PROFILES:
            with self.subTest(profile=profile),TemporaryDirectory() as d:
                with cls(initial,d): pass
                (Path(d)/'worker-checkpoint.json').unlink()
                with self.assertRaises(RecoveryError):
                    cls(initial,d,resume=True)
                with self.assertRaises(ValueError):
                    cls(initial,d)

    def test_corrupt_checkpoint_wrong_initial_backend_and_profile_are_refused(self):
        with TemporaryDirectory() as d:
            with DurableAdmissionSession(admission_initial(),d): pass
            with self.assertRaisesRegex(RecoveryError,'backend'):
                DurableAdmissionSession(admission_initial(),d,resume=True,native=True)
            with self.assertRaisesRegex(RecoveryError,'initial'):
                DurableAdmissionSession(AdmissionInitial(),d,resume=True)
            with self.assertRaisesRegex(RecoveryError,'profile'):
                DurableDeploymentSession(DeploymentInitial(),d,resume=True)
            path=Path(d)/'worker-checkpoint.json'
            envelope=json.loads(path.read_text())
            envelope['digest']='0'*64
            path.write_text(json.dumps(envelope))
            with self.assertRaisesRegex(RecoveryError,'integrity'):
                DurableAdmissionSession(admission_initial(),d,resume=True)

    def test_missing_or_changed_journal_refuses_resume_without_creating_store(self):
        for profile,cls,initial in PROFILES:
            with self.subTest(profile=profile),TemporaryDirectory() as d:
                with cls(initial,d) as s:
                    s.apply(ready_event(profile))
                with AdmissionService(database=Path(d)/'admission.db') as service:
                    service.advance_clock('c0',1,idempotency_key='external')
                with self.assertRaisesRegex(RecoveryError,'journals differ'):
                    cls(initial,d,resume=True)
                target=Path(d)/('executor.db' if profile=='deployment' else 'admission.db')
                target.unlink()
                with self.assertRaisesRegex(RecoveryError,'existing journals'):
                    cls(initial,d,resume=True)
                self.assertFalse(target.exists())

    def test_resigned_malformed_metadata_and_reordered_aliases_fail_validation(self):
        mutations=[lambda b:b['metadata'].update(step=True),lambda b:b['metadata'].update(next_key=-1),
                   lambda b:b['metadata']['seen'].append('ghost'),lambda b:b['metadata']['hard'].reverse(),
                   lambda b:b['metadata']['rules'][0].update(revision='different'),
                   lambda b:b['completed']['a-duplicate']['record'].update(step=1)]
        for change in mutations:
            with self.subTest(change=change),TemporaryDirectory() as d:
                with DurableAdmissionSession(admission_initial(),d) as s:
                    s.apply(ready_event('admission'))
                    s.apply(ae('z-first','evidence',context_id='c0',literal=1,roots=['root'],valid_until=None))
                    s.apply(ae('a-duplicate','adopt',context_id='c0',evidence_id='z-first'))
                modify_state(d,change)
                with self.assertRaises(RecoveryError):
                    DurableAdmissionSession(admission_initial(),d,resume=True)

    def test_checkpoint_failure_poisoning_and_pending_marker_survive_process_reopen(self):
        for profile,cls,initial in PROFILES:
            with self.subTest(profile=profile),TemporaryDirectory() as d:
                s=cls(initial,d)
                original=s._save
                count=0
                def save():
                    nonlocal count
                    count+=1
                    if count==2:
                        raise OSError('injected disk failure')
                    original()
                with patch.object(s,'_save',save):
                    with self.assertRaises(OSError):
                        s.apply(ready_event(profile))
                with self.assertRaises(RecoveryError):
                    s.apply(event(profile,'more'))
                s.close()
                with self.assertRaisesRegex(RecoveryError,'interrupted'):
                    cls(initial,d,resume=True)

    def test_invalid_fields_are_rejected_before_checkpoint_publication(self):
        for profile,cls,initial in PROFILES:
            with self.subTest(profile=profile),TemporaryDirectory() as d,cls(initial,d) as s:
                before=s.checkpoint_path.read_bytes()
                with self.assertRaises(ValueError):
                    s.apply(dict(ready_event(profile),future=[]))
                self.assertEqual(s.checkpoint_path.read_bytes(),before)


class TraceProcessCrashTests(unittest.TestCase):
    def test_pending_before_execution_and_after_composite_execution_refuse_resume(self):
        for profile,cls,initial in PROFILES:
            for stage in ('before','after'):
                with self.subTest(profile=profile,stage=stage),TemporaryDirectory() as d:
                    root=Path(d); runtime_bundle(root/'runtime')
                    with cls(initial,root/'state'): pass
                    path=root/'runtime'/'reachability'/'trace_worker_state.py'
                    source=path.read_text()
                    needle='row=super().apply(message)' if stage=='before' else 'self._save()  # Completed checkpoint must precede stdout.'
                    self.assertIn(needle,source)
                    path.write_text(source.replace(needle,'__import__("os")._exit(71)\n            '+needle))
                    w=PublicWorker(root/'runtime',profile,root/'state',root/'crash',resume=True)
                    try:
                        w.request(public(initial))
                        with self.assertRaises(WorkerError):
                            w.request(ready_event(profile))
                    finally:
                        w.stop(kill=True)
                    self.assertEqual(json.loads((root/'crash'/'exit.json').read_text())['returncode'],71)
                    with self.assertRaisesRegex(RecoveryError,'interrupted'):
                        cls(initial,root/'state',resume=True)
                    with AdmissionService(database=root/'state'/'admission.db') as service:
                        if profile=='admission':
                            self.assertEqual('c0' in service._contexts,stage=='after')
                        else:
                            self.assertEqual(len(service._evidence),int(stage=='after'))

    def test_lost_stdout_returns_exact_completed_reply_in_fresh_process(self):
        for profile,cls,initial in PROFILES:
            with self.subTest(profile=profile),TemporaryDirectory() as d:
                root=Path(d); runtime_bundle(root/'runtime')
                with cls(initial,root/'state'): pass
                path=root/'runtime'/'reachability'/'stream_worker.py'
                source=path.read_text()
                path.write_text(source.replace('def emit(value):',
                    'def emit(value):\n    if value.get("kind")=="event":\n        __import__("os")._exit(74)'))
                w=PublicWorker(root/'runtime',profile,root/'state',root/'lost',resume=True)
                try:
                    w.request(public(initial))
                    with self.assertRaises(WorkerError):
                        w.request(ready_event(profile))
                finally:
                    w.stop(kill=True)
                saved=load_state(root/'state')['completed'][ready_event(profile)['event_id']]['record']
                path.write_text(source)
                w=PublicWorker(root/'runtime',profile,root/'state',root/'resumed',resume=True)
                try:
                    self.assertEqual(w.request(public(initial))['completed'],1)
                    retry=w.request(ready_event(profile))
                    self.assertTrue(retry['replayed'])
                    self.assertEqual(retry['record'],saved)
                finally:
                    w.stop()

    def test_deployment_crash_after_remote_effect_preserves_uncertainty_and_refuses_resume(self):
        with TemporaryDirectory() as d:
            root=Path(d); runtime_bundle(root/'runtime')
            messages=deployment_cases()[2]['events']
            with DurableDeploymentSession(DeploymentInitial(),root/'state') as s:
                for message in messages[:6]:
                    s.apply(message)
            path=root/'runtime'/'reachability'/'simulated_executor.py'
            source=path.read_text().replace('return self._write("submit", request)',
                'receipt=self._write("submit",request)\n        __import__("os")._exit(72)\n        return receipt')
            path.write_text(source)
            w=PublicWorker(root/'runtime','deployment',root/'state',root/'crash',resume=True)
            try:
                w.request(asdict(DeploymentInitial()))
                with self.assertRaises(WorkerError):
                    w.request(messages[6])
            finally:
                w.stop(kill=True)
            with self.assertRaisesRegex(RecoveryError,'interrupted'):
                DurableDeploymentSession(DeploymentInitial(),root/'state',resume=True)
            with SimulatedExecutor(root/'state'/'executor.db') as executor:
                self.assertEqual(executor.total_effects,1)
            with AdmissionService(database=root/'state'/'admission.db') as service:
                self.assertEqual(service.inspect_dispatch('a0').state,'uncertain')
