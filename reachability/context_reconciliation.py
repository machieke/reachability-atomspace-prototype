"""Recover the two specified journal boundaries of a new context event.

Candidate construction uses disposable journals. Partial completion appends the
validated policy entry; adoption of both persisted entries preserves source bytes.
"""
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import sqlite3
from tempfile import TemporaryDirectory

from .admission_protocol import AdmissionInitial
from .codec import decode, encode, dumps
from .dispatch_worker_state import atomic_write
from .journal import JournalEntry, RecoveryError, digest
from .probability_model import ProbabilityPolicy
from .reconciliation_state import MARKER
from .trace_protocol import fingerprint
from .trace_worker_state import DurableAdmissionSession

ACTION = 'complete_partial_context'
ADOPT_ACTION = 'adopt_persisted_context'
ACTIONS = (ACTION, ADOPT_ACTION)


def candidate(report, inspection, request):
    body = decode(report['checkpoint'])
    event = report['pending']
    boundary = report['journals'].get('authority', {})
    adopting = request['action'] == ADOPT_ACTION
    persisted = 2 if adopting else 1
    if (request['profile'] != 'admission' or event['kind'] != 'context'
            or report['status'] != 'pending_journal_progress' or report['errors']
            or boundary.get('relation') != 'advanced' or len(boundary.get('appended', [])) != persisted):
        raise RecoveryError('context adoption requires exactly two persisted context commands' if adopting else
            'context completion requires exactly one persisted open_context command')
    if len(body['completed']) >= 128:
        raise RecoveryError('reconciliation would exceed the stream event bound')
    with TemporaryDirectory(prefix='context-reconciliation-') as temporary:
        private = Path(temporary)
        for source in (Path(inspection)/'snapshot').iterdir():
            if source.name != MARKER:
                shutil.copyfile(source, private/source.name)
        # Rewind only the disposable copy to the saved wrapper boundary. Ordinary
        # resume then validates aliases, rules, historical replies and projection.
        with sqlite3.connect(private/'admission.db') as connection:
            connection.execute('DELETE FROM events WHERE sequence > ?', (body['journals']['authority']['sequence'],))
        connection.close()
        clean = deepcopy(body)
        clean['pending'] = None
        path = private/'worker-checkpoint.json'
        envelope = json.loads(path.read_text())
        envelope.update(body=encode(clean), digest=fingerprint(encode(clean)))
        atomic_write(path, envelope)
        initial = AdmissionInitial.parse(body['initial'])
        with DurableAdmissionSession(initial, private, resume=True, native=body['native']) as session:
            if session._parse(event) != event or event['event_id'] in session.seen:
                raise RecoveryError('invalid pending context identity')
            args = event['arguments']
            ctx = args['context_id']
            if ctx in session.contexts or len(session.contexts) >= 4:
                raise RecoveryError('context completion requires a new context within the stream bound')
            session.step += 1
            session.seen.add(event['event_id'])
            session._prefix, session.certificates = event['event_id'], []
            session.service.open_context(ctx, assumptions=tuple(map(session.literal, args['assumptions'])),
                constraints=session.clauses(args['clauses']), idempotency_key=session.key())
            opened = asdict(session.service._journal.entries()[-1])
            if opened != boundary['appended'][0] or not adopting and session._tips() != request['journals']:
                raise RecoveryError('persisted open_context differs from the saved command/counter')
            session.contexts.add(ctx)
            session.service.configure_probability_policy(ctx, ProbabilityPolicy('p1', ('sensor',)),
                idempotency_key=session.key())
            appended = asdict(session.service._journal.entries()[-1])
            if adopting and (appended != boundary['appended'][1] or session._tips() != request['journals']):
                raise RecoveryError('persisted context policy differs from the saved command/counter')
            projection = session.projection()
            row = dict(schema='admission-trace/v1', step=session.step, event_id=event['event_id'],
                event_digest=fingerprint(event), initial_digest=fingerprint(body['initial']),
                outcome=dict(status='PASS', detail='adopted by explicit persisted-context reconciliation' if adopting else
                    'completed by explicit partial-context reconciliation'),
                projection=projection, projection_digest=fingerprint(projection),
                diagnostics=dict(certificates=encode(()), elapsed_ns=0,
                    knowledge_revisions={c:session.service.snapshot(c).knowledge_revision for c in sorted(session.contexts)},
                    reconciliation=dict(decision_id=request['decision_id'], request_digest=fingerprint(request), action=request['action'])))
            session.completed[event['event_id']] = dict(command=event, record=row)
            session._save()
        with DurableAdmissionSession(initial, private, resume=True, native=body['native']) as session:
            if session.apply(event) != row or not session.replayed:
                raise RecoveryError('candidate context reply failed exact recovery')
        return path.read_bytes(), row, [opened, appended] if adopting else appended


def target_tip(before, entry):
    return dict(genesis=before['genesis'], sequence=entry['sequence'], tail=entry['entry_digest'])


def validate_append(record, before):
    """Bind the prepared suffix to the original pending command and counter."""
    entry = JournalEntry(**record['authority_append'])
    request = record['request']
    event = before['pending']
    tip = request['journals']['authority']
    if (request['profile'] != 'admission' or event['kind'] != 'context'
            or fingerprint(event) != request['pending_digest']
            or entry.command != 'configure_probability_policy'
            or entry.key != f"admission-trace:{event['event_id']}:{before['metadata']['next_key']+1}"
            or entry.payload != dumps(dict(context_id=event['arguments']['context_id'],
                policy=ProbabilityPolicy('p1', ('sensor',)), expected_revision=None))
            or entry.sequence != tip['sequence']+1 or entry.previous_digest != tip['tail']
            or entry.computed_digest() != entry.entry_digest):
        raise RecoveryError('prepared context suffix differs from original command/boundary')


def validate_adoption(record, before):
    """Retained entries must bridge the saved checkpoint and inspected tip exactly."""
    request, entries = record['request'], record['authority_entries']
    event, tip = before['pending'], before['journals']['authority']
    if (request['profile'] != 'admission' or event['kind'] != 'context'
            or fingerprint(event) != request['pending_digest'] or type(entries) is not list or len(entries) != 2):
        raise RecoveryError('prepared context adoption inventory differs')
    for offset, command in enumerate(('open_context', 'configure_probability_policy')):
        try:
            entry = JournalEntry(**entries[offset])
        except TypeError as error:
            raise RecoveryError('prepared context adoption entry differs') from error
        if (entry.command != command or entry.sequence != tip['sequence']+1
                or entry.key != f"admission-trace:{event['event_id']}:{before['metadata']['next_key']+offset}"
                or entry.previous_digest != tip['tail'] or entry.computed_digest() != entry.entry_digest):
            raise RecoveryError('prepared context adoption chain differs')
        tip = target_tip(tip, entries[offset])
    if dict(authority=tip) != request['journals']:
        raise RecoveryError('prepared context adoption boundary differs')


def append_under_ownership(directory, record, *, allow_append):
    """Caller must retain owned_worker throughout this transaction and publication.

    No lock handoff, public composite replay or replacement database is involved.
    A retry accepts only the complete original chain or that chain plus this row.
    """
    before = record['request']['journals']['authority']
    entry = JournalEntry(**record['authority_append'])
    after = target_tip(before, record['authority_append'])
    connection = None
    try:
        connection = sqlite3.connect((directory/'admission.db').as_uri()+'?mode=rw', uri=True, isolation_level=None)
        if connection.execute('PRAGMA journal_mode').fetchone()[0] != 'wal':
            raise RecoveryError('context reconciliation requires the existing WAL journal')
        connection.execute('PRAGMA synchronous=FULL')
        connection.execute('BEGIN IMMEDIATE')
        metadata = connection.execute('SELECT value FROM metadata WHERE id=1').fetchone()
        if metadata is None or digest(metadata[0]) != before['genesis']:
            raise RecoveryError('authority genesis differs during context reconciliation')
        rows = connection.execute('SELECT sequence,command,key,payload,result_digest,previous_digest,entry_digest FROM events ORDER BY sequence').fetchall()
        previous = before['genesis']
        for sequence, raw in enumerate(rows, 1):
            actual = JournalEntry(*raw)
            if actual.sequence != sequence or actual.previous_digest != previous or actual.entry_digest != actual.computed_digest():
                raise RecoveryError('authority chain differs during context reconciliation')
            previous = actual.entry_digest
        tip = dict(genesis=before['genesis'], sequence=len(rows), tail=previous)
        if tip == after:
            if JournalEntry(*rows[-1]) != entry:
                raise RecoveryError('persisted context suffix differs')
        elif tip == before and allow_append:
            connection.execute('INSERT INTO events VALUES (?,?,?,?,?,?,?)', tuple(asdict(entry).values()))
        else:
            raise RecoveryError('authority boundary differs during context reconciliation')
        connection.execute('COMMIT')  # Only the validated missing policy entry can be appended.
    except sqlite3.Error as error:
        raise RecoveryError('context reconciliation journal transaction failed') from error
    finally:
        if connection is not None:
            connection.close()
