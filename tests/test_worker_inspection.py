"""Evidence preservation, offline replay and actual interrupted-process probes."""
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from reachability.admission_trace import AdmissionSession
from reachability.codec import encode, decode
from reachability.dispatch_worker_state import DurableDispatchSession, read_checkpoint
from reachability.journal import RecoveryError, SQLiteJournal, StoreInUse
from reachability.pln_adapter import PeTTaFormulaRuntime
from reachability.service import AdmissionService
from reachability.simulated_executor import SimulatedExecutor
from reachability.trace_protocol import DeploymentInitial, canonical, fingerprint
from reachability.trace_worker_state import DurableAdmissionSession, DurableDeploymentSession, SCHEMA as TRACE_SCHEMA
from reachability.worker_inspection import inspect_worker, verify_inspection, capture_names, file_inventory
from validation_lab.generate_admission_cases import initial, scenarios as admission_cases
from validation_lab.generate_deployment_cases import scenarios as deployment_cases
from validation_lab.generate_dispatch_race_cases import scenarios as dispatch_cases
from validation_lab.run_worker_inspection import main as run_probes, verify_report

PROFILES=(('admission',DurableAdmissionSession,initial()),('deployment',DurableDeploymentSession,DeploymentInitial()),
          ('dispatch',DurableDispatchSession,DeploymentInitial()))


def source_files(directory):
    return {p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in directory.iterdir() if p.is_file()}


def change_checkpoint(directory, change, schema=TRACE_SCHEMA):
    path=directory/'worker-checkpoint.json'
    body=read_checkpoint(path,schema=schema)
    change(body)
    body=encode(body)
    path.write_text(canonical(dict(schema=schema,body=body,digest=fingerprint(body))))


def messages(profile):
    return (admission_cases()[12] if profile=='admission' else deployment_cases()[2]
            if profile=='deployment' else dispatch_cases()[11])['events']


class WorkerInspectionTests(unittest.TestCase):
    def test_completed_all_profiles_reproduce_without_changing_source_bytes_names_or_mtimes(self):
        for profile,cls,ini in PROFILES:
            with self.subTest(profile=profile),TemporaryDirectory() as d:
                root=Path(d); state=root/'state'
                with cls(ini,state) as session:
                    for event in messages(profile):
                        last=session.apply(event)
                (state/'.checkpoint-abandoned').write_bytes(b'incomplete replacement')
                before=source_files(state)
                report=inspect_worker(profile,state,root/'inspection')
                self.assertEqual(report['status'],'no_pending_marker')
                self.assertEqual(report['errors'],[])
                self.assertFalse(report['continuation_authorized'])
                self.assertEqual({r['relation'] for r in report['journals'].values()},{'equal'})
                self.assertEqual(verify_inspection(root/'inspection'),report)
                self.assertEqual(source_files(state),before)
                self.assertEqual(inspect_worker(profile,state,root/'again'),report)
                with cls(ini,state,resume=True) as session:
                    self.assertEqual(session.apply(event),last)

    def test_pending_without_journal_change_never_authorizes_replay(self):
        for profile,cls,ini in PROFILES:
            with self.subTest(profile=profile),TemporaryDirectory() as d:
                root=Path(d); state=root/'state'
                with cls(ini,state) as session:
                    session.pending=messages(profile)[0]
                    session._save()
                before=source_files(state)
                report=inspect_worker(profile,state,root/'inspection')
                self.assertEqual(report['status'],'pending_no_journal_change')
                self.assertEqual(report['pending'],messages(profile)[0])
                self.assertFalse(report['continuation_authorized'])
                self.assertEqual(source_files(state),before)
                with self.assertRaisesRegex(RecoveryError,'interrupted'):
                    cls(ini,state,resume=True)

    def test_active_worker_and_direct_journal_ownership_refuse_capture(self):
        with TemporaryDirectory() as d:
            root=Path(d); state=root/'state'
            with DurableDeploymentSession(DeploymentInitial(),state):
                with self.assertRaises(StoreInUse):
                    inspect_worker('deployment',state,root/'worker-busy')
            with AdmissionService(database=state/'admission.db'):
                with self.assertRaises(StoreInUse):
                    inspect_worker('deployment',state,root/'authority-busy')
            with SimulatedExecutor(state/'executor.db'):
                with self.assertRaises(StoreInUse):
                    inspect_worker('admission',state,root/'executor-busy')
            self.assertEqual(sorted(p.name for p in root.iterdir()),['state'])

    def test_missing_ownership_locks_are_never_created(self):
        for name in ('worker.lock','admission.db.lock','executor.db.lock'):
            with self.subTest(name=name),TemporaryDirectory() as d:
                root=Path(d); state=root/'state'
                with DurableDeploymentSession(DeploymentInitial(),state): pass
                (state/name).unlink()
                before=source_files(state)
                with self.assertRaisesRegex(RecoveryError,'ownership lock'):
                    inspect_worker('deployment',state,root/'inspection')
                self.assertEqual(source_files(state),before)
                self.assertFalse((root/'inspection').exists())

    def test_missing_journal_and_checkpoint_still_preserve_available_evidence(self):
        for name in ('admission.db','executor.db','worker-checkpoint.json'):
            with self.subTest(name=name),TemporaryDirectory() as d:
                root=Path(d); state=root/'state'
                with DurableDeploymentSession(DeploymentInitial(),state): pass
                (state/name).unlink()
                before=source_files(state)
                report=inspect_worker('deployment',state,root/'inspection')
                self.assertEqual(report['status'],'unverified')
                self.assertTrue(report['errors'])
                self.assertEqual(verify_inspection(root/'inspection'),report)
                self.assertEqual(source_files(state),before)
                self.assertIsNone(report['evidence'][name])

    def test_corruption_never_initializes_or_repairs_an_original_journal(self):
        for data in (b'',b'not a SQLite database'):
            with self.subTest(data=data),TemporaryDirectory() as d:
                root=Path(d); state=root/'state'
                with DurableAdmissionSession(initial(),state): pass
                (state/'admission.db').write_bytes(data)
                before=source_files(state)
                report=inspect_worker('admission',state,root/'inspection')
                self.assertEqual(report['status'],'unverified')
                self.assertIsNone(report['authority'])
                self.assertEqual(report['journals']['authority']['relation'],'unavailable')
                self.assertEqual(verify_inspection(root/'inspection'),report)
                self.assertEqual(source_files(state),before)

    def test_corrupt_checkpoint_and_wrong_profile_are_explicitly_unverified(self):
        with TemporaryDirectory() as d:
            root=Path(d); state=root/'state'
            with DurableAdmissionSession(initial(),state): pass
            report=inspect_worker('deployment',state,root/'wrong')
            self.assertEqual(report['status'],'unverified')
            path=state/'worker-checkpoint.json'
            envelope=json.loads(path.read_text()); envelope['digest']='0'*64
            path.write_text(canonical(envelope))
            before=source_files(state)
            report=inspect_worker('admission',state,root/'corrupt')
            self.assertIsNone(report['checkpoint'])
            self.assertIsNotNone(report['authority'])
            self.assertEqual(report['journals']['authority']['relation'],'unbound')
            self.assertEqual(source_files(state),before)

    def test_advanced_journal_is_reported_without_absorbing_progress_into_checkpoint(self):
        with TemporaryDirectory() as d:
            root=Path(d); state=root/'state'
            with DurableAdmissionSession(initial(),state) as session:
                old=session.checkpoint_path.read_bytes()
                session.apply(messages('admission')[0])
            (state/'worker-checkpoint.json').write_bytes(old)
            report=inspect_worker('admission',state,root/'inspection')
            self.assertEqual(report['status'],'checkpoint_journal_mismatch')
            boundary=report['journals']['authority']
            self.assertEqual(boundary['relation'],'advanced')
            self.assertEqual([e['command'] for e in boundary['appended']],['open_context','configure_probability_policy'])
            self.assertEqual((state/'worker-checkpoint.json').read_bytes(),old)

    def test_same_sequence_wrong_tail_and_replaced_journal_are_diverged(self):
        with TemporaryDirectory() as d:
            root=Path(d); state=root/'state'
            with DurableAdmissionSession(initial(),state): pass
            original=(state/'worker-checkpoint.json').read_bytes()
            change_checkpoint(state,lambda b:b['journals']['authority'].update(tail='0'*64))
            report=inspect_worker('admission',state,root/'tail')
            self.assertEqual(report['journals']['authority']['relation'],'diverged')
            (state/'worker-checkpoint.json').write_bytes(original)
            with DurableAdmissionSession(initial(),root/'replacement'): pass
            shutil.copyfile(root/'replacement'/'admission.db',state/'admission.db')
            report=inspect_worker('admission',state,root/'genesis')
            self.assertEqual(report['journals']['authority']['relation'],'diverged')
            self.assertEqual(report['status'],'unverified')

    def test_inspection_and_offline_verification_have_no_executor_or_native_inference_io(self):
        with TemporaryDirectory() as d:
            root=Path(d); state=root/'state'
            with DurableDispatchSession(DeploymentInitial(),state) as session:
                for event in messages('dispatch'):
                    session.apply(event)
            before=source_files(state)
            with patch.object(SimulatedExecutor,'submit',side_effect=AssertionError('submit')),\
                 patch.object(SimulatedExecutor,'query',side_effect=AssertionError('query')),\
                 patch.object(SimulatedExecutor,'release',side_effect=AssertionError('release')),\
                 patch.object(PeTTaFormulaRuntime,'evaluate',side_effect=AssertionError('native inference')),\
                 patch.object(AdmissionSession,'apply',side_effect=AssertionError('public event replay')),\
                 patch.object(SQLiteJournal,'append',side_effect=AssertionError('journal append')):
                report=inspect_worker('dispatch',state,root/'inspection')
                self.assertEqual(verify_inspection(root/'inspection'),report)
            self.assertEqual(source_files(state),before)

    def test_historical_observed_ack_is_separate_from_current_executor_fence(self):
        with TemporaryDirectory() as d:
            root=Path(d); state=root/'state'
            with DurableDispatchSession(DeploymentInitial(),state) as session:
                for event in dispatch_cases()[11]['events']:
                    session.apply(event)
            report=inspect_worker('dispatch',state,root/'inspection')
            body=decode(report['checkpoint'])
            self.assertEqual(body['receipts']['s'][1].state,'accepted')
            self.assertEqual(decode(report['executor']['receipts'][0]['value']).state,'released')
            local=decode(report['authority']['views']['dispatch']['a'])
            self.assertTrue(local.resources_released)
            self.assertEqual(local.state,'released')
            self.assertEqual(report['executor']['total_effects'],1)

    def test_receipt_rejects_changed_raw_files_added_files_and_resigned_false_report(self):
        with TemporaryDirectory() as d:
            root=Path(d); state=root/'state'; output=root/'inspection'
            with DurableAdmissionSession(initial(),state): pass
            inspect_worker('admission',state,output)
            checkpoint=output/'snapshot'/'worker-checkpoint.json'
            original=checkpoint.read_bytes(); checkpoint.write_bytes(b'changed')
            with self.assertRaisesRegex(RecoveryError,'files differ'):
                verify_inspection(output)
            checkpoint.write_bytes(original)
            extra=output/'snapshot'/'extra'; extra.write_text('extra')
            with self.assertRaisesRegex(RecoveryError,'files differ'):
                verify_inspection(output)
            extra.unlink()
            report=json.loads((output/'report.json').read_text()); report['continuation_authorized']=True
            (output/'report.json').write_text(canonical(report))
            receipt=json.loads((output/'receipt.json').read_text())
            receipt['report_sha256']=sha256((output/'report.json').read_bytes()).hexdigest()
            (output/'receipt.json').write_text(canonical(receipt))
            with self.assertRaisesRegex(RecoveryError,'captured evidence'):
                verify_inspection(output)

    def test_output_reuse_nested_output_missing_directory_and_symlinks_are_refused(self):
        with TemporaryDirectory() as d:
            root=Path(d); state=root/'state'
            with DurableAdmissionSession(initial(),state): pass
            before=source_files(state)
            for output in (state,state/'nested'):
                with self.assertRaises(ValueError):
                    inspect_worker('admission',state,output)
            with self.assertRaises(FileNotFoundError):
                inspect_worker('admission',root/'missing',root/'unused')
            inspect_worker('admission',state,root/'inspection')
            with self.assertRaises(FileExistsError):
                inspect_worker('admission',state,root/'inspection')
            self.assertEqual(source_files(state),before)
            (state/'executor.db-wal').symlink_to(state/'admission.db')
            with self.assertRaisesRegex(RecoveryError,'regular evidence'):
                inspect_worker('admission',state,root/'symlink')

    def test_capture_bounds_leave_original_files_unchanged(self):
        with TemporaryDirectory() as d:
            root=Path(d); state=root/'state'
            with DurableAdmissionSession(initial(),state): pass
            before=source_files(state)
            for name in ('MAX_CAPTURE','MAX_FILES'):
                with self.subTest(bound=name),patch('reachability.worker_inspection.'+name,1):
                    with self.assertRaisesRegex(RecoveryError,'bound'):
                        inspect_worker('admission',state,root/name)
            self.assertEqual(source_files(state),before)

    def test_command_line_inspection_publishes_reviewable_bundle(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            with DurableAdmissionSession(initial(),root/'state'): pass
            result=subprocess.run([sys.executable,'-m','reachability.worker_inspection','--profile','admission',
                '--database-dir',str(root/'state'),'--output',str(root/'inspection')],capture_output=True,text=True,check=True)
            self.assertEqual(json.loads(result.stdout)['status'],'no_pending_marker')
            self.assertEqual(result.stderr,'')
            self.assertEqual(verify_inspection(root/'inspection')['status'],'no_pending_marker')


class WorkerInspectionProcessTests(unittest.TestCase):
    def test_real_crashes_partial_commands_wal_capture_and_independent_raw_report(self):
        with TemporaryDirectory() as d:
            output=Path(d)/'probes'
            with patch('sys.argv',['run_worker_inspection','--output',str(output)]):
                run_probes()
            report=verify_report(output)
            self.assertEqual(len(report['results']),18)
            remote=output/'dispatch-remote-effect'/'inspection'
            inspection=verify_inspection(remote)
            self.assertGreater(inspection['evidence']['executor.db-wal']['size'],0)
            body=decode(inspection['checkpoint'])
            self.assertEqual(body['requests'],{})
            self.assertEqual(body['receipts'],{})
            self.assertEqual(decode(inspection['authority']['views']['dispatch']['a']).state,'uncertain')
            self.assertEqual(inspection['executor']['total_effects'],1)
            original_report=(output/'report.json').read_bytes()
            report['results']['dispatch-remote-effect']['effects']=0
            (output/'report.json').write_text(canonical(report))
            with self.assertRaisesRegex(ValueError,'results differ'):
                verify_report(output)
            (output/'report.json').write_bytes(original_report)
            fault_path=output/'dispatch-remote-effect'/'fault.json'
            fault=json.loads(fault_path.read_text()); fault['before']='0'*64
            fault_path.write_text(canonical(fault))
            receipt=json.loads(original_report)
            receipt['files'][str(fault_path.relative_to(output))]=sha256(fault_path.read_bytes()).hexdigest()
            (output/'report.json').write_text(canonical(receipt))
            with self.assertRaisesRegex(ValueError,'fault receipt'):
                verify_report(output)
