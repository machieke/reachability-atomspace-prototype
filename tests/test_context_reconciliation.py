"""Bounded partial-context completion and refusal of ambiguous journal progress."""
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from reachability.admission_protocol import event
from reachability.admission_trace import AdmissionSession
from reachability.codec import encode
from reachability.context_reconciliation import ACTION
from reachability.dispatch_worker_state import atomic_write, read_checkpoint
from reachability.journal import RecoveryError, StoreInUse
from reachability.pln_adapter import PeTTaFormulaRuntime
from reachability.probability_model import ProbabilityPolicy
from reachability.reconciliation_state import ARCHIVE, MARKER
from reachability.service import AdmissionService
from reachability.simulated_executor import SimulatedExecutor
from reachability.trace_protocol import fingerprint
from reachability.trace_worker_state import DurableAdmissionSession, SCHEMA
from reachability.worker_inspection import inspect_worker, capture_names, file_inventory
import reachability.worker_reconciliation as reconciliation
from validation_lab.generate_admission_cases import initial, scenarios
from validation_lab.run_public_workers import REFERENCES


def partial(root, *, prefix=(), pending=None, progress=1, native=False):
    pending = pending or event('new-context', 'context', context_id='c1', assumptions=[1], clauses=[[-1, 2]])
    with DurableAdmissionSession(initial(), root/'state', native=native) as session:
        for command in prefix:
            session.apply(command)
        session.pending = pending
        session._save()
        before = session._metadata()
        session._prefix = pending['event_id']
        args = pending['arguments']
        if progress:
            session.service.open_context(args['context_id'], assumptions=tuple(map(session.literal, args['assumptions'])),
                constraints=session.clauses(args['clauses']), idempotency_key=session.key())
        if progress == 2:
            session.service.configure_probability_policy(args['context_id'], ProbabilityPolicy('p1', ('sensor',)),
                idempotency_key=session.key())
    return pending, before


def inspect(root, name='inspection'):
    report = inspect_worker('admission', root/'state', root/name)
    request = reconciliation.make_request(root/name, 'complete-context', ACTION)
    return report, request


def edit_checkpoint(root, edit):
    path = root/'state'/'worker-checkpoint.json'
    body = read_checkpoint(path, schema=SCHEMA)
    edit(body)
    encoded = encode(body)
    atomic_write(path, dict(schema=SCHEMA, body=encoded, digest=fingerprint(encoded)))


class ContextReconciliationTests(unittest.TestCase):
    def test_one_append_preserves_prefix_aliases_counters_and_original_evidence(self):
        prefix = scenarios()[12]['events'][:-1]
        with TemporaryDirectory() as directory:
            root = Path(directory)
            pending, before = partial(root, prefix=prefix)
            report, request = inspect(root)
            original = {str(p.relative_to(root/'inspection')):p.read_bytes() for p in (root/'inspection').rglob('*') if p.is_file()}
            result = reconciliation.reconcile(request, root/'state', root/'inspection')
            self.assertEqual(result['result']['outcome'], 'completed')
            self.assertFalse(result['replayed'])
            self.assertEqual(result['result']['journals']['authority']['sequence'], request['journals']['authority']['sequence']+1)
            self.assertEqual(reconciliation.verify_reconciliation(reconciliation.archive_path(root/'state', request), root/'inspection'), result['result'])
            self.assertEqual(original, {str(p.relative_to(root/'inspection')):p.read_bytes() for p in (root/'inspection').rglob('*') if p.is_file()})
            with DurableAdmissionSession(initial(), root/'state', resume=True) as session:
                entries = session.service._journal.entries()
                self.assertEqual(asdict(entries[-2]), report['journals']['authority']['appended'][0])
                self.assertEqual(entries[-1].command, 'configure_probability_policy')
                after = session._metadata()
                for key in ('hard', 'numeric', 'rules'):
                    self.assertEqual(after[key], before[key])
                self.assertEqual(after['next_key'], before['next_key']+2)
                row = session.apply(pending)
                self.assertTrue(session.replayed)
                self.assertEqual(row['outcome']['status'], 'PASS')
                self.assertEqual(row['step'], len(prefix)+1)
                self.assertEqual(row['projection'], REFERENCES['admission'](initial().wire(), [*prefix, pending])['projection'])
                session.apply(scenarios()[12]['events'][-1])
                altered = deepcopy(pending); altered['arguments']['assumptions'] = []
                with self.assertRaises(ValueError):
                    session.apply(altered)
            self.assertEqual(reconciliation.reconcile(request, root/'state', root/'missing'), dict(result=result['result'], replayed=True))

    def test_saved_counter_arguments_and_event_identity_must_match_persisted_open(self):
        edits = [lambda b:b['metadata'].update(next_key=99),
            lambda b:b['pending']['arguments'].update(assumptions=[]),
            lambda b:b['pending']['arguments'].update(clauses=[]),
            lambda b:b['pending'].update(event_id='different')]
        for edit in edits:
            with self.subTest(edit=edit), TemporaryDirectory() as directory:
                root = Path(directory); partial(root); edit_checkpoint(root, edit)
                _, request = inspect(root)
                before = file_inventory(root/'state', capture_names(root/'state'))
                with self.assertRaisesRegex(RecoveryError, 'persisted open_context differs'):
                    reconciliation.reconcile(request, root/'state', root/'inspection')
                self.assertEqual(file_inventory(root/'state', capture_names(root/'state')), before)
                self.assertFalse((root/'state'/ARCHIVE).exists())

    def test_no_progress_or_fully_persisted_composite_is_not_partial_context(self):
        for progress in (0, 2):
            with self.subTest(progress=progress), TemporaryDirectory() as directory:
                root = Path(directory); partial(root, progress=progress); _, request = inspect(root)
                with self.assertRaisesRegex(RecoveryError, 'exactly one persisted'):
                    reconciliation.reconcile(request, root/'state', root/'inspection')
                self.assertFalse((root/'state'/ARCHIVE).exists())

    def test_existing_context_and_context_capacity_are_refused(self):
        for existing in (True, False):
            with self.subTest(existing=existing), TemporaryDirectory() as directory:
                root = Path(directory)
                prefix = [event('c'+str(i), 'context', context_id='c'+str(i), assumptions=[], clauses=[])
                    for i in range(1 if existing else 4)]
                pending = event('pending', 'context', context_id='c0' if existing else 'overflow', assumptions=[], clauses=[])
                partial(root, prefix=prefix, pending=pending); _, request = inspect(root)
                with self.assertRaisesRegex(RecoveryError, 'new context within'):
                    reconciliation.reconcile(request, root/'state', root/'inspection')

    def test_event_budget_refuses_before_preparation(self):
        with TemporaryDirectory() as directory:
            root = Path(directory); partial(root, prefix=[event(str(i), 'restart') for i in range(128)])
            _, request = inspect(root)
            with self.assertRaisesRegex(RecoveryError, 'stream event bound'):
                reconciliation.reconcile(request, root/'state', root/'inspection')
            self.assertFalse((root/'state'/ARCHIVE).exists())

    def test_unrelated_single_append_is_not_context_progress(self):
        with TemporaryDirectory() as directory:
            root = Path(directory); partial(root, progress=0)
            with AdmissionService(database=root/'state'/'admission.db') as service:
                service.open_context('unrelated', idempotency_key='external')
            _, request = inspect(root)
            with self.assertRaisesRegex(RecoveryError, 'persisted open_context differs'):
                reconciliation.reconcile(request, root/'state', root/'inspection')

    def test_checkpoint_failure_retries_committed_suffix_without_inspection(self):
        with TemporaryDirectory() as directory:
            root = Path(directory); pending, _ = partial(root); _, request = inspect(root)
            original = reconciliation.atomic_write
            def fail(path, value):
                if path == root/'state'/'worker-checkpoint.json':
                    raise OSError('checkpoint failure')
                return original(path, value)
            with patch.object(reconciliation, 'atomic_write', fail), self.assertRaises(OSError):
                reconciliation.reconcile(request, root/'state', root/'inspection')
            self.assertTrue((root/'state'/MARKER).exists())
            with self.assertRaisesRegex(RecoveryError, 'unfinished reconciliation'):
                DurableAdmissionSession(initial(), root/'state', resume=True)
            result = reconciliation.reconcile(request, root/'state', root/'missing')
            self.assertTrue(result['replayed'])
            with DurableAdmissionSession(initial(), root/'state', resume=True) as session:
                self.assertEqual(len(session.service._journal.entries()), 2)
                self.assertEqual(session.apply(pending)['outcome']['status'], 'PASS')

    def test_extra_authority_progress_keeps_gate_before_and_after_suffix(self):
        for committed in (False, True):
            with self.subTest(committed=committed), TemporaryDirectory() as directory:
                root = Path(directory); partial(root); _, request = inspect(root)
                original = reconciliation.atomic_write
                def fail(path, value):
                    if path == root/'state'/'worker-checkpoint.json': raise OSError('checkpoint')
                    return original(path, value)
                with patch.object(reconciliation, 'atomic_write', fail) if committed else patch.object(reconciliation, 'finish', side_effect=OSError('before append')):
                    with self.assertRaises(OSError): reconciliation.reconcile(request, root/'state', root/'inspection')
                with AdmissionService(database=root/'state'/'admission.db') as service:
                    service.advance_clock('c1', 1, idempotency_key='external')
                with self.assertRaisesRegex(RecoveryError, 'authority boundary differs'):
                    reconciliation.reconcile(request, root/'state', root/'inspection')
                self.assertTrue((root/'state'/MARKER).exists())

    def test_published_checkpoint_requires_suffix_to_remain_durable(self):
        with TemporaryDirectory() as directory:
            root = Path(directory); partial(root); _, request = inspect(root)
            original = reconciliation.atomic_write
            def fail(path, value):
                if path.name == 'result.json': raise OSError('result failure')
                return original(path, value)
            with patch.object(reconciliation, 'atomic_write', fail), self.assertRaises(OSError):
                reconciliation.reconcile(request, root/'state', root/'inspection')
            with sqlite3.connect(root/'state'/'admission.db') as connection:
                connection.execute('DELETE FROM events WHERE sequence=2')
            connection.close()
            with self.assertRaisesRegex(RecoveryError, 'authority boundary differs'):
                reconciliation.reconcile(request, root/'state', root/'missing')
            self.assertTrue((root/'state'/MARKER).exists())

    def test_public_event_native_inference_and_executor_operations_are_never_replayed(self):
        with TemporaryDirectory() as directory:
            root = Path(directory); partial(root); _, request = inspect(root)
            with patch.object(AdmissionSession, '_execute', side_effect=AssertionError('public event')), \
                 patch.object(PeTTaFormulaRuntime, 'evaluate', side_effect=AssertionError('native inference')), \
                 patch.object(SimulatedExecutor, 'submit', side_effect=AssertionError('executor submit')), \
                 patch.object(SimulatedExecutor, 'query', side_effect=AssertionError('executor query')), \
                 patch.object(SimulatedExecutor, 'release', side_effect=AssertionError('executor release')):
                result = reconciliation.reconcile(request, root/'state', root/'inspection')
                self.assertEqual(reconciliation.verify_reconciliation(reconciliation.archive_path(root/'state', request), root/'inspection'), result['result'])

    def test_worker_and_journal_ownership_are_retained_through_append(self):
        from reachability import context_reconciliation
        with TemporaryDirectory() as directory:
            root = Path(directory); partial(root); _, request = inspect(root)
            original = context_reconciliation.append_under_ownership
            def check(directory, record, **kwargs):
                with self.assertRaises(StoreInUse):
                    AdmissionService(database=directory/'admission.db')
                with self.assertRaises(StoreInUse):
                    DurableAdmissionSession(initial(), directory, resume=True)
                return original(directory, record, **kwargs)
            with patch.object(context_reconciliation, 'append_under_ownership', check):
                reconciliation.reconcile(request, root/'state', root/'inspection')

    def test_archive_suffix_and_action_cannot_be_rebound(self):
        with TemporaryDirectory() as directory:
            root = Path(directory); partial(root); _, request = inspect(root)
            reconciliation.reconcile(request, root/'state', root/'inspection')
            altered = deepcopy(request); altered['action'] = reconciliation.ACTION
            with self.assertRaisesRegex(RecoveryError, 'identity'):
                reconciliation.reconcile(altered, root/'state', root/'inspection')
            path = reconciliation.archive_path(root/'state', request)/'prepared.json'
            record = reconciliation.read_control(path)
            record['authority_append']['key'] = 'different'
            atomic_write(path, reconciliation.control(record))
            with self.assertRaisesRegex(RecoveryError, 'prepared context suffix differs'):
                reconciliation.reconcile(request, root/'state', root/'inspection')

    def test_stale_inspection_refuses_before_source_sqlite_is_opened(self):
        with TemporaryDirectory() as directory:
            root = Path(directory); partial(root); _, request = inspect(root)
            path = root/'state'/'worker-checkpoint.json'
            path.write_bytes(path.read_bytes()+b' ')
            with self.assertRaisesRegex(RecoveryError, 'stale'):
                reconciliation.reconcile(request, root/'state', root/'inspection')
            self.assertFalse((root/'state'/ARCHIVE).exists())
