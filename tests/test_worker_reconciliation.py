"""Explicit cancellation, evidence binding and durable publication boundaries."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import unittest

from reachability.admission_protocol import event as ae
from reachability.admission_trace import AdmissionSession
from reachability.deployment_trace import DeploymentSession
from reachability.dispatch_worker_state import DurableDispatchSession, atomic_write, read_checkpoint
from reachability.journal import RecoveryError, SQLiteJournal, StoreInUse
from reachability.pln_adapter import PeTTaFormulaRuntime
from reachability.reconciliation_state import MARKER, ARCHIVE
from reachability.service import AdmissionService
from reachability.simulated_executor import SimulatedExecutor
from reachability.trace_protocol import DeploymentInitial, event as de, canonical
from reachability.trace_worker_state import DurableAdmissionSession,DurableDeploymentSession
from reachability.worker_inspection import inspect_worker,capture_names,file_inventory
from reachability.worker_reconciliation import (reconcile,make_request,parse_request,archive_path,
    verify_reconciliation,journal_evidence,control,read_control)
from validation_lab.generate_admission_cases import initial,scenarios as admission_cases
from validation_lab.generate_deployment_cases import scenarios as deployment_cases
from validation_lab.generate_dispatch_race_cases import scenarios as dispatch_cases

PROFILES=(('admission',DurableAdmissionSession,initial()),('deployment',DurableDeploymentSession,DeploymentInitial()))


def pending_state(root,profile,cls,ini,*,prefix=(),event=None,native=False):
    event=event or (admission_cases()[0]['events'][0] if profile=='admission' else deployment_cases()[0]['events'][0])
    kwargs=dict(native=True) if native else {}
    with cls(ini,root/'state',**kwargs) as session:
        for item in prefix:
            session.apply(item)
        session.pending=event;session._save()
    report=inspect_worker(profile,root/'state',root/'inspection')
    request=make_request(root/'inspection','operator/decision .. 1')
    return event,report,request


class WorkerReconciliationTests(unittest.TestCase):
    def test_cancel_consumes_identity_preserves_state_and_allows_new_event(self):
        for profile,cls,ini in PROFILES:
            with self.subTest(profile=profile),TemporaryDirectory() as d:
                root=Path(d);event,report,request=pending_state(root,profile,cls,ini)
                before=journal_evidence(report['evidence'])
                result=reconcile(request,root/'state',root/'inspection')
                self.assertEqual(result['result']['outcome'],'cancelled')
                self.assertFalse(result['replayed'])
                self.assertEqual(journal_evidence(file_inventory(root/'state',capture_names(root/'state'))),before)
                self.assertEqual(verify_reconciliation(archive_path(root/'state',request),root/'inspection'),result['result'])
                self.assertFalse((root/'state'/MARKER).exists())
                with cls(ini,root/'state',resume=True) as session:
                    row=session.apply(event)
                    self.assertTrue(session.replayed)
                    self.assertEqual(row['outcome']['status'],'UNKNOWN')
                    self.assertEqual(row['diagnostics']['reconciliation']['decision_id'],request['decision_id'])
                    self.assertEqual(session.step,1)
                    altered=deepcopy(event);altered['event_id']='after-cancellation'
                    self.assertEqual(session.apply(altered)['outcome']['status'],'PASS')
                    self.assertEqual(session.step,2)
                self.assertEqual(reconcile(request,root/'state',root/'missing-inspection'),dict(result=result['result'],replayed=True))

    def test_original_checkpoint_and_inspection_are_preserved_exactly(self):
        with TemporaryDirectory() as d:
            root=Path(d);event,report,request=pending_state(root,*PROFILES[0])
            path=root/'inspection'
            original={str(p.relative_to(path)):p.read_bytes() for p in path.rglob('*') if p.is_file()}
            before=(root/'state'/'worker-checkpoint.json').read_bytes()
            reconcile(request,root/'state',path)
            self.assertEqual((archive_path(root/'state',request)/'before.json').read_bytes(),before)
            self.assertEqual({str(p.relative_to(path)):p.read_bytes() for p in path.rglob('*') if p.is_file()},original)

    def test_reconciliation_executes_no_public_event_journal_command_or_executor_io(self):
        for profile,cls,ini in PROFILES:
            with self.subTest(profile=profile),TemporaryDirectory() as d:
                root=Path(d)
                prefix=admission_cases()[12]['events'] if profile=='admission' else deployment_cases()[2]['events']
                event=(ae if profile=='admission' else de)('cancel-restart','restart')
                _,_,request=pending_state(root,profile,cls,ini,prefix=prefix,event=event)
                with patch.object(AdmissionSession,'_execute',side_effect=AssertionError('event')),\
                     patch.object(DeploymentSession,'_execute',side_effect=AssertionError('event')),\
                     patch.object(SQLiteJournal,'append',side_effect=AssertionError('append')),\
                     patch.object(PeTTaFormulaRuntime,'evaluate',side_effect=AssertionError('native inference')),\
                     patch.object(SimulatedExecutor,'submit',side_effect=AssertionError('submit')),\
                     patch.object(SimulatedExecutor,'query',side_effect=AssertionError('query')),\
                     patch.object(SimulatedExecutor,'release',side_effect=AssertionError('release')):
                    result=reconcile(request,root/'state',root/'inspection')
                    self.assertEqual(verify_reconciliation(archive_path(root/'state',request),root/'inspection'),result['result'])

    def test_stale_checkpoint_or_journals_refuse_without_creating_decision(self):
        for kind in ('checkpoint','journal'):
            with self.subTest(kind=kind),TemporaryDirectory() as d:
                root=Path(d);_,_,request=pending_state(root,*PROFILES[0])
                if kind=='checkpoint':
                    path=root/'state'/'worker-checkpoint.json';path.write_bytes(path.read_bytes()+b' ')
                else:
                    with AdmissionService(database=root/'state'/'admission.db') as s:
                        s.open_context('external',idempotency_key='external')
                before=file_inventory(root/'state',capture_names(root/'state'))
                with self.assertRaisesRegex(RecoveryError,'stale'):
                    reconcile(request,root/'state',root/'inspection')
                self.assertEqual(file_inventory(root/'state',capture_names(root/'state')),before)
                self.assertFalse((root/'state'/ARCHIVE).exists())

    def test_altered_request_bindings_and_decision_identity_are_rejected(self):
        with TemporaryDirectory() as d:
            root=Path(d);_,_,request=pending_state(root,*PROFILES[0])
            changes=[lambda r:r.update(inspection_digest='0'*64),lambda r:r.update(pending_digest='0'*64),
                     lambda r:r.update(checkpoint_sha256='0'*64),lambda r:r['journals']['authority'].update(sequence=999)]
            for change in changes:
                altered=deepcopy(request);change(altered)
                with self.assertRaisesRegex(RecoveryError,'differs'):
                    reconcile(altered,root/'state',root/'inspection')
            reconcile(request,root/'state',root/'inspection')
            altered=deepcopy(request);altered['pending_digest']='0'*64
            with self.assertRaisesRegex(RecoveryError,'identity'):
                reconcile(altered,root/'state',root/'inspection')

    def test_malformed_or_unknown_request_fields_are_rejected(self):
        with TemporaryDirectory() as d:
            root=Path(d);_,_,request=pending_state(root,*PROFILES[0])
            for change in (lambda r:r.update(future=True),lambda r:r.update(action='release'),
                lambda r:r.update(profile='unknown'),lambda r:r.update(decision_id=''),
                lambda r:r.update(pending_digest='z'*64),lambda r:r['journals']['authority'].update(sequence=True)):
                altered=deepcopy(request);change(altered)
                with self.assertRaises(ValueError):
                    parse_request(altered)

    def test_partial_context_numerical_lifecycle_and_remote_progress_are_refused(self):
        # Real process cases supply checked actual partial journals, not fabricated tips.
        from validation_lab.run_worker_inspection import cases,run_case
        selected={'admission-partial-context','admission-partial-estimate','deployment-partial-attempt',
                  'deployment-partial-sample','deployment-remote-effect'}
        with TemporaryDirectory() as d:
            for case in cases():
                if case['case_id'] not in selected: continue
                with self.subTest(case=case['case_id']):
                    root=Path(d)/case['case_id'];run_case(case,root)
                    request=make_request(root/'inspection','refused')
                    before=file_inventory(root/'state',capture_names(root/'state'))
                    with self.assertRaises(RecoveryError):
                        reconcile(request,root/'state',root/'inspection')
                    self.assertEqual(file_inventory(root/'state',capture_names(root/'state')),before)
                    self.assertFalse((root/'state'/ARCHIVE).exists())

    def test_executor_commands_and_dispatch_profile_refuse_even_with_equal_tips(self):
        with TemporaryDirectory() as d:
            for kind in ('dispatch','reconcile','release'):
                root=Path(d)/kind;event=de('pending',kind,attempt_id='a0',**({'fault':'none'} if kind=='dispatch' else {}))
                _,_,request=pending_state(root,*PROFILES[1],event=event)
                with self.assertRaisesRegex(RecoveryError,'local deployment'):
                    reconcile(request,root/'state',root/'inspection')
            root=Path(d)/'dispatch-profile'
            _,_,request=pending_state(root,'dispatch',DurableDispatchSession,DeploymentInitial(),event=dispatch_cases()[0]['events'][0])
            with self.assertRaisesRegex(RecoveryError,'local deployment'):
                reconcile(request,root/'state',root/'inspection')

    def test_prior_remote_uncertainty_survives_cancel_and_continuation(self):
        with TemporaryDirectory() as d:
            root=Path(d);source=deployment_cases()[2]['events']
            event=de('cancel-tick','tick',time=1)
            _,_,request=pending_state(root,*PROFILES[1],prefix=source[:7],event=event)
            reconcile(request,root/'state',root/'inspection')
            with DurableDeploymentSession(DeploymentInitial(),root/'state',resume=True) as s:
                self.assertEqual(s.service.inspect_dispatch('a0').state,'uncertain')
                self.assertEqual(s.executor.total_effects,1)
                self.assertEqual(s.service.inspect_resource('slot').reconciliation_attempts,('a0',))
                self.assertEqual(s.apply(event)['outcome']['status'],'UNKNOWN')
                s.apply(de('expire','tick',time=10))
                s.apply(de('other','attempt',attempt_id='a1'))
                self.assertEqual(s.apply(de('reserve-other','reserve',attempt_id='a1'))['outcome']['status'],'UNKNOWN')

    def test_cancellation_respects_event_budget_and_exact_retry_does_not_consume_it(self):
        with TemporaryDirectory() as d:
            root=Path(d);event=ae('last','restart')
            _,_,request=pending_state(root,*PROFILES[0],prefix=[ae(str(i),'restart') for i in range(127)],event=event)
            reconcile(request,root/'state',root/'inspection')
            with DurableAdmissionSession(initial(),root/'state',resume=True) as s:
                self.assertEqual(s.apply(event)['step'],128)
                self.assertEqual(s.apply(event)['step'],128)
                with self.assertRaisesRegex(ValueError,'bound'):
                    s.apply(ae('overflow','restart'))

    def test_unfinished_reconciliation_blocks_every_worker_profile(self):
        profiles=(*PROFILES,('dispatch',DurableDispatchSession,DeploymentInitial()))
        for profile,cls,ini in profiles:
            with self.subTest(profile=profile),TemporaryDirectory() as d:
                root=Path(d)
                with cls(ini,root/'state'): pass
                (root/'state'/MARKER).write_text('{}')
                with self.assertRaisesRegex(RecoveryError,'unfinished reconciliation'):
                    cls(ini,root/'state',resume=True)

    def test_live_worker_or_journal_owner_blocks_reconciliation(self):
        with TemporaryDirectory() as d:
            root=Path(d);_,_,request=pending_state(root,*PROFILES[0])
            with AdmissionService(database=root/'state'/'admission.db'):
                with self.assertRaises(StoreInUse):
                    reconcile(request,root/'state',root/'inspection')
            self.assertFalse((root/'state'/ARCHIVE).exists())

    def test_corrupted_candidate_or_result_archive_refuses_exact_retry(self):
        for name in ('after.json','result.json'):
            with self.subTest(name=name),TemporaryDirectory() as d:
                root=Path(d);_,_,request=pending_state(root,*PROFILES[0])
                reconcile(request,root/'state',root/'inspection')
                (archive_path(root/'state',request)/name).write_text('{}')
                with self.assertRaises(RecoveryError):
                    reconcile(request,root/'state',root/'inspection')

    def test_prepared_storage_failure_blocks_worker_until_exact_retry(self):
        import reachability.worker_reconciliation as module
        with TemporaryDirectory() as d:
            root=Path(d);event,_,request=pending_state(root,*PROFILES[0])
            original=module.atomic_write
            def fail(path,value):
                if path==root/'state'/'worker-checkpoint.json':
                    raise OSError('injected publication failure')
                return original(path,value)
            with patch.object(module,'atomic_write',fail):
                with self.assertRaises(OSError):
                    reconcile(request,root/'state',root/'inspection')
            self.assertTrue((root/'state'/MARKER).exists())
            inspection=inspect_worker('admission',root/'state',root/'interrupted')
            self.assertEqual(inspection['status'],'reconciliation_in_progress')
            with self.assertRaisesRegex(RecoveryError,'unfinished reconciliation'):
                DurableAdmissionSession(initial(),root/'state',resume=True)
            result=reconcile(request,root/'state',root/'removed-inspection')
            self.assertTrue(result['replayed'])
            with DurableAdmissionSession(initial(),root/'state',resume=True) as s:
                self.assertEqual(s.apply(event)['outcome']['status'],'UNKNOWN')

    def test_changed_journal_after_preparation_keeps_gate_and_refuses_finish(self):
        import reachability.worker_reconciliation as module
        with TemporaryDirectory() as d:
            root=Path(d);_,_,request=pending_state(root,*PROFILES[0])
            with patch.object(module,'finish',side_effect=OSError('interrupted')):
                with self.assertRaises(OSError):
                    reconcile(request,root/'state',root/'inspection')
            with AdmissionService(database=root/'state'/'admission.db') as s:
                s.open_context('external',idempotency_key='external')
            with self.assertRaisesRegex(RecoveryError,'journal evidence changed'):
                reconcile(request,root/'state',root/'inspection')
            self.assertTrue((root/'state'/MARKER).exists())
            with self.assertRaisesRegex(RecoveryError,'unfinished reconciliation'):
                DurableAdmissionSession(initial(),root/'state',resume=True)

    def test_invalid_wrapper_metadata_is_refused_before_any_decision(self):
        from reachability.codec import encode
        from reachability.trace_protocol import fingerprint
        from reachability.trace_worker_state import SCHEMA
        with TemporaryDirectory() as d:
            root=Path(d);_,_,_=pending_state(root,*PROFILES[0])
            path=root/'state'/'worker-checkpoint.json'
            body=read_checkpoint(path,schema=SCHEMA);body['metadata']['next_key']=-1
            body=encode(body);atomic_write(path,dict(schema=SCHEMA,body=body,digest=fingerprint(body)))
            inspect_worker('admission',root/'state',root/'invalid-inspection')
            request=make_request(root/'invalid-inspection','invalid')
            with self.assertRaisesRegex(RecoveryError,'metadata'):
                reconcile(request,root/'state',root/'invalid-inspection')
            self.assertFalse((root/'state'/ARCHIVE).exists())

    def test_prepared_assets_can_be_retried_before_marker_publication(self):
        import reachability.worker_reconciliation as module
        with TemporaryDirectory() as d:
            root=Path(d);_,_,request=pending_state(root,*PROFILES[0])
            original=module.atomic_write
            def fail(path,value):
                if path.name==MARKER: raise OSError('marker storage failure')
                return original(path,value)
            with patch.object(module,'atomic_write',fail):
                with self.assertRaises(OSError):
                    reconcile(request,root/'state',root/'inspection')
            self.assertFalse((root/'state'/MARKER).exists())
            with self.assertRaisesRegex(RecoveryError,'interrupted worker command'):
                DurableAdmissionSession(initial(),root/'state',resume=True)
            self.assertTrue(reconcile(request,root/'state',root/'inspection')['replayed'])


class ReconciliationProcessTests(unittest.TestCase):
    def test_real_publication_crashes_exact_decision_retries_and_fresh_worker_continuation(self):
        from validation_lab.run_worker_reconciliation import main,verify_report
        with TemporaryDirectory() as d:
            output=Path(d)/'probes'
            with patch('sys.argv',['run_worker_reconciliation','--output',str(output)]):
                main()
            report=verify_report(output)
            self.assertEqual(len(report['results']),50)
            report['results'][0]['resolved_status']='PASS'
            (output/'report.json').write_text(canonical(report))
            with self.assertRaisesRegex(ValueError,'results differ'):
                verify_report(output)
