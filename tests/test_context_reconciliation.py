"""Bounded partial-context completion and refusal of ambiguous journal progress."""
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from reachability.admission_protocol import AdmissionInitial, event
from reachability.admission_trace import AdmissionSession
from reachability.codec import encode
from reachability.context_reconciliation import ACTION, ADOPT_ACTION
from reachability.dispatch_worker_state import atomic_write, read_checkpoint
from reachability.journal import JournalEntry, RecoveryError, SQLiteJournal, StoreInUse
from reachability.pln_adapter import PeTTaFormulaRuntime
from reachability.probability_model import ProbabilityPolicy
from reachability.reconciliation_state import ARCHIVE, MARKER
from reachability.service import AdmissionService
from reachability.simulated_executor import SimulatedExecutor
from reachability.trace_protocol import fingerprint, read_json
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


def inspect(root, name='inspection', action=ACTION):
    report = inspect_worker('admission', root/'state', root/name)
    request = reconciliation.make_request(root/name, 'complete-context', action)
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


class PersistedContextAdoptionTests(unittest.TestCase):
    def test_large_typed_entries_fit_bounded_archives_without_widening_public_messages(self):
        public = initial().wire()
        public.update(atoms=[str(i)+'a'*255 for i in range(8)], rules=[])
        configuration = AdmissionInitial.parse(public)
        pending = event('large', 'context', context_id='large', assumptions=[1], clauses=[list(range(1,9)) for _ in range(32)])
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with DurableAdmissionSession(configuration, root/'state') as session:
                session.pending=pending;session._save();session._prefix=pending['event_id']
                session.service.open_context('large', assumptions=(session.literal(1),),
                    constraints=session.clauses(pending['arguments']['clauses']), idempotency_key=session.key())
                session.service.configure_probability_policy('large', ProbabilityPolicy('p1', ('sensor',)), idempotency_key=session.key())
            _, request = inspect(root, action=ADOPT_ACTION)
            with patch.object(reconciliation, 'finish', side_effect=OSError('interrupted')), self.assertRaises(OSError):
                reconciliation.reconcile(request, root/'state', root/'inspection')
            archive = reconciliation.archive_path(root/'state', request)
            self.assertGreater((archive/'prepared.json').stat().st_size, 65536)
            with self.assertRaisesRegex(ValueError, '64 KiB'):
                read_json((archive/'prepared.json').read_text())
            result = reconciliation.reconcile(request, root/'state', root/'missing')
            self.assertEqual(reconciliation.verify_reconciliation(archive, root/'inspection'), result['result'])
            with DurableAdmissionSession(configuration, root/'state', resume=True) as session:
                self.assertEqual(session.apply(pending)['outcome']['status'], 'PASS')
            oversized = root/'oversized.json'
            with oversized.open('wb') as stream:
                stream.truncate(reconciliation.MAX_CHECKPOINT+1)
            with self.assertRaisesRegex(RecoveryError, 'control record'):
                reconciliation.read_control(oversized)

    def test_adoption_preserves_journals_historical_replies_and_restores_counters(self):
        prefix = scenarios()[12]['events'][:-1]
        with TemporaryDirectory() as directory:
            root = Path(directory); pending, metadata = partial(root, prefix=prefix, progress=2)
            report, request = inspect(root, action=ADOPT_ACTION)
            original = read_checkpoint(root/'state'/'worker-checkpoint.json', schema=SCHEMA)
            evidence = reconciliation.journal_evidence(report['evidence'])
            raw = {str(p.relative_to(root/'inspection')):p.read_bytes() for p in (root/'inspection').rglob('*') if p.is_file()}
            result = reconciliation.reconcile(request, root/'state', root/'inspection')
            self.assertFalse(result['replayed'])
            self.assertEqual(result['result']['outcome'], 'adopted')
            self.assertEqual(result['result']['journals'], request['journals'])
            self.assertEqual(reconciliation.journal_evidence(file_inventory(root/'state', capture_names(root/'state'))), evidence)
            archive = reconciliation.archive_path(root/'state', request)
            prepared = reconciliation.read_control(archive/'prepared.json')
            self.assertEqual(prepared['schema'], reconciliation.ADOPTION_RECORD_SCHEMA)
            self.assertEqual(prepared['authority_entries'], report['journals']['authority']['appended'])
            self.assertEqual(reconciliation.verify_reconciliation(archive, root/'inspection'), result['result'])
            self.assertEqual(raw, {str(p.relative_to(root/'inspection')):p.read_bytes() for p in (root/'inspection').rglob('*') if p.is_file()})
            with DurableAdmissionSession(initial(), root/'state', resume=True) as session:
                for key, saved in original['completed'].items():
                    self.assertEqual(session.completed[key], saved)
                for key in ('hard', 'numeric', 'rules'):
                    self.assertEqual(session._metadata()[key], metadata[key])
                self.assertEqual(session._metadata()['next_key'], metadata['next_key']+2)
                row = session.apply(pending)
                self.assertTrue(session.replayed)
                self.assertEqual(row['outcome']['status'], 'PASS')
                self.assertEqual(row['step'], len(prefix)+1)
                self.assertEqual(row['diagnostics']['elapsed_ns'], 0)
                self.assertEqual(row['diagnostics']['reconciliation']['action'], ADOPT_ACTION)
                self.assertEqual(row['projection'], REFERENCES['admission'](initial().wire(), [*prefix, pending])['projection'])
                self.assertEqual(session.apply(pending), row)
                altered = deepcopy(pending); altered['arguments']['clauses'] = []
                with self.assertRaisesRegex(ValueError, 'identity'):
                    session.apply(altered)
                session.apply(scenarios()[12]['events'][-1])
            self.assertEqual(reconciliation.reconcile(request, root/'state', root/'missing'), dict(result=result['result'], replayed=True))

    def test_adoption_never_opens_source_sqlite_or_appends_to_source(self):
        from reachability import context_reconciliation
        with TemporaryDirectory() as directory:
            root = Path(directory); partial(root, progress=2); _, request = inspect(root, action=ADOPT_ACTION)
            connect, append = sqlite3.connect, SQLiteJournal.append
            def private_connect(path, *args, **kwargs):
                self.assertNotIn(str(root/'state'), str(path))
                return connect(path, *args, **kwargs)
            def private_append(journal, *args, **kwargs):
                self.assertNotEqual(journal.path.parent, root/'state')
                return append(journal, *args, **kwargs)
            with patch('sqlite3.connect', private_connect), patch.object(SQLiteJournal, 'append', private_append), \
                 patch.object(context_reconciliation, 'append_under_ownership', side_effect=AssertionError('source append')), \
                 patch.object(AdmissionSession, '_execute', side_effect=AssertionError('public event')), \
                 patch.object(PeTTaFormulaRuntime, 'evaluate', side_effect=AssertionError('native inference')), \
                 patch.object(SimulatedExecutor, 'submit', side_effect=AssertionError('submit')), \
                 patch.object(SimulatedExecutor, 'query', side_effect=AssertionError('query')), \
                 patch.object(SimulatedExecutor, 'release', side_effect=AssertionError('release')):
                result = reconciliation.reconcile(request, root/'state', root/'inspection')
                self.assertEqual(reconciliation.verify_reconciliation(reconciliation.archive_path(root/'state', request), root/'inspection'), result['result'])

    def test_adoption_refuses_no_partial_or_extra_progress(self):
        for progress in (0, 1, 3):
            with self.subTest(progress=progress), TemporaryDirectory() as directory:
                root = Path(directory); partial(root, progress=min(progress, 2))
                if progress == 3:
                    with AdmissionService(database=root/'state'/'admission.db') as service:
                        service.advance_clock('c1', 1, idempotency_key='extra')
                _, request = inspect(root, action=ADOPT_ACTION)
                before = file_inventory(root/'state', capture_names(root/'state'))
                with self.assertRaisesRegex(RecoveryError, 'exactly two persisted'):
                    reconciliation.reconcile(request, root/'state', root/'inspection')
                self.assertEqual(before, file_inventory(root/'state', capture_names(root/'state')))
                self.assertFalse((root/'state'/ARCHIVE).exists())

    def test_second_command_key_policy_and_operation_are_bound_exactly(self):
        for change in ('key', 'policy', 'operation'):
            with self.subTest(change=change), TemporaryDirectory() as directory:
                root = Path(directory); pending, metadata = partial(root)
                key = f"admission-trace:{pending['event_id']}:{metadata['next_key']+1}"
                with AdmissionService(database=root/'state'/'admission.db') as service:
                    if change == 'operation':
                        service.advance_clock('c1', 1, idempotency_key=key)
                    else:
                        service.configure_probability_policy('c1', ProbabilityPolicy('wrong' if change=='policy' else 'p1', ('sensor',)),
                            idempotency_key='wrong' if change=='key' else key)
                _, request = inspect(root, action=ADOPT_ACTION)
                with self.assertRaisesRegex(RecoveryError, 'persisted context policy differs'):
                    reconciliation.reconcile(request, root/'state', root/'inspection')
                self.assertFalse((root/'state'/ARCHIVE).exists())

    def test_first_command_arguments_identity_and_counter_remain_bound(self):
        edits = [lambda b:b['metadata'].update(next_key=9), lambda b:b['pending'].update(event_id='wrong'),
            lambda b:b['pending']['arguments'].update(assumptions=[]), lambda b:b['pending']['arguments'].update(clauses=[])]
        for edit in edits:
            with self.subTest(edit=edit), TemporaryDirectory() as directory:
                root = Path(directory); partial(root, progress=2); edit_checkpoint(root, edit)
                _, request = inspect(root, action=ADOPT_ACTION)
                with self.assertRaisesRegex(RecoveryError, 'persisted open_context differs'):
                    reconciliation.reconcile(request, root/'state', root/'inspection')
                self.assertFalse((root/'state'/ARCHIVE).exists())

    def test_event_budget_final_slot_and_exact_retry(self):
        for count in (127, 128):
            with self.subTest(count=count), TemporaryDirectory() as directory:
                root = Path(directory); pending, _ = partial(root, prefix=[event(str(i), 'restart') for i in range(count)], progress=2)
                _, request = inspect(root, action=ADOPT_ACTION)
                if count == 128:
                    with self.assertRaisesRegex(RecoveryError, 'stream event bound'):
                        reconciliation.reconcile(request, root/'state', root/'inspection')
                else:
                    reconciliation.reconcile(request, root/'state', root/'inspection')
                    with DurableAdmissionSession(initial(), root/'state', resume=True) as session:
                        self.assertEqual(session.apply(pending)['step'], 128)
                        self.assertEqual(session.apply(pending)['step'], 128)
                        with self.assertRaisesRegex(ValueError, 'bound'):
                            session.apply(event('overflow', 'restart'))

    def test_existing_context_and_context_capacity_are_not_adopted(self):
        for existing in (False, True):
            with self.subTest(existing=existing), TemporaryDirectory() as directory:
                root = Path(directory)
                # An existing hard-only context can have both commands persisted
                # under a later event ID; this is still outside new-context adoption.
                if existing:
                    with DurableAdmissionSession(initial(), root/'state') as session:
                        session.service.open_context('c0', idempotency_key='initial-context')
                        session.contexts.add('c0'); session._save()
                        pending = event('again', 'context', context_id='c0', assumptions=[], clauses=[])
                        session.pending=pending; session._save(); session._prefix=pending['event_id']
                        session.service.open_context('c0', idempotency_key=session.key())
                        session.service.configure_probability_policy('c0', ProbabilityPolicy('p1', ('sensor',)), idempotency_key=session.key())
                else:
                    prefix = [event(str(i), 'context', context_id='c'+str(i), assumptions=[], clauses=[]) for i in range(4)]
                    partial(root, prefix=prefix, pending=event('fifth','context',context_id='c4',assumptions=[],clauses=[]), progress=2)
                _, request = inspect(root, action=ADOPT_ACTION)
                with self.assertRaisesRegex(RecoveryError, 'new context within'):
                    reconciliation.reconcile(request, root/'state', root/'inspection')

    def test_publication_failure_retries_without_inspection_and_preserves_gate(self):
        for name in ('worker-checkpoint.json', 'result.json'):
            with self.subTest(name=name), TemporaryDirectory() as directory:
                root = Path(directory); pending, _ = partial(root, progress=2)
                report, request = inspect(root, action=ADOPT_ACTION)
                original = reconciliation.atomic_write
                def fail(path, value):
                    if path.name == name and (name != 'worker-checkpoint.json' or path.parent == root/'state'):
                        raise OSError('publication failure')
                    return original(path, value)
                with patch.object(reconciliation, 'atomic_write', fail), self.assertRaises(OSError):
                    reconciliation.reconcile(request, root/'state', root/'inspection')
                self.assertTrue((root/'state'/MARKER).exists())
                with self.assertRaisesRegex(RecoveryError, 'unfinished reconciliation'):
                    DurableAdmissionSession(initial(), root/'state', resume=True)
                archive = reconciliation.archive_path(root/'state', request)
                self.assertEqual(reconciliation.verify_reconciliation(archive, root/'inspection')['schema'], reconciliation.ADOPTION_RECORD_SCHEMA)
                result = reconciliation.reconcile(request, root/'state', root/'missing')
                self.assertTrue(result['replayed'])
                self.assertEqual(reconciliation.journal_evidence(report['evidence']),
                    reconciliation.journal_evidence(file_inventory(root/'state', capture_names(root/'state'))))
                with DurableAdmissionSession(initial(), root/'state', resume=True) as session:
                    self.assertEqual(session.apply(pending)['outcome']['status'], 'PASS')

    def test_stale_evidence_before_or_after_preparation_is_refused(self):
        for prepared in (False, True):
            with self.subTest(prepared=prepared), TemporaryDirectory() as directory:
                root = Path(directory); partial(root, progress=2); _, request = inspect(root, action=ADOPT_ACTION)
                if prepared:
                    with patch.object(reconciliation, 'finish', side_effect=OSError('interrupt')), self.assertRaises(OSError):
                        reconciliation.reconcile(request, root/'state', root/'inspection')
                with AdmissionService(database=root/'state'/'admission.db') as service:
                    service.advance_clock('c1', 1, idempotency_key='external')
                before = file_inventory(root/'state', capture_names(root/'state'))
                with self.assertRaisesRegex(RecoveryError, 'journal evidence changed' if prepared else 'stale'):
                    reconciliation.reconcile(request, root/'state', root/'inspection')
                self.assertEqual(before, file_inventory(root/'state', capture_names(root/'state')))
                self.assertEqual((root/'state'/MARKER).exists(), prepared)

    def test_archive_entry_order_and_rehashed_payloads_cannot_change_bound_chain(self):
        for change in ('order', 'payload'):
            with self.subTest(change=change), TemporaryDirectory() as directory:
                root = Path(directory); partial(root, progress=2); _, request = inspect(root, action=ADOPT_ACTION)
                reconciliation.reconcile(request, root/'state', root/'inspection')
                path = reconciliation.archive_path(root/'state', request)/'prepared.json'
                record = reconciliation.read_control(path)
                entries = record['authority_entries']
                if change == 'order':
                    entries.reverse()
                else:
                    entries[0]['payload'] += ' '
                    entries[0]['entry_digest'] = JournalEntry(**entries[0]).computed_digest()
                    entries[1]['previous_digest'] = entries[0]['entry_digest']
                    entries[1]['entry_digest'] = JournalEntry(**entries[1]).computed_digest()
                atomic_write(path, reconciliation.control(record))
                with self.assertRaisesRegex(RecoveryError, 'prepared context adoption'):
                    reconciliation.reconcile(request, root/'state', root/'inspection')

    def test_non_admission_profiles_and_already_completed_workers_are_refused(self):
        with TemporaryDirectory() as directory:
            root = Path(directory); pending, _ = partial(root, progress=2); _, request = inspect(root, action=ADOPT_ACTION)
            for profile in ('deployment', 'dispatch'):
                altered=deepcopy(request);altered['profile']=profile
                with self.assertRaisesRegex(ValueError, 'only admission'):
                    reconciliation.parse_request(altered)
            reconciliation.reconcile(request, root/'state', root/'inspection')
            inspect_worker('admission', root/'state', root/'completed-inspection')
            with self.assertRaisesRegex(RecoveryError, 'verified pending'):
                reconciliation.make_request(root/'completed-inspection', 'another', ADOPT_ACTION)
            for action in (reconciliation.ACTION, ACTION):
                altered=deepcopy(request);altered['action']=action
                with self.assertRaisesRegex(RecoveryError, 'identity'):
                    reconciliation.reconcile(altered, root/'state', root/'inspection')
