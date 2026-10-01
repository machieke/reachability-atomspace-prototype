"""Adopt one fully persisted, successful hard-evidence admission event.

Only disposable journals execute the specified primitive commands. The source
authority, its native backend and any executor remain untouched during adoption.
"""
from contextlib import closing
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import sqlite3
from tempfile import TemporaryDirectory

from .admission_protocol import AdmissionInitial
from .codec import decode, encode
from .context_reconciliation import validate_adoption as validate_chain
from .dispatch_worker_state import atomic_write
from .journal import RecoveryError
from .model import Evidence, Status
from .reconciliation_state import MARKER
from .trace_protocol import fingerprint
from .trace_worker_state import DurableAdmissionSession

ACTION = 'adopt_persisted_evidence'
COMMANDS = ('record_evidence', 'propose_evidence', 'precertify', 'postcertify', 'commit')


def candidate(report, inspection, request):
    body, event = decode(report['checkpoint']), report['pending']
    boundary = report['journals'].get('authority', {})
    if (request['profile'] != 'admission' or event['kind'] != 'evidence' or report['errors']
            or report['status'] != 'pending_journal_progress' or boundary.get('relation') != 'advanced'
            or len(boundary.get('appended', [])) != len(COMMANDS)):
        raise RecoveryError('evidence adoption requires exactly five persisted hard-evidence commands')
    if len(body['completed']) >= 128:
        raise RecoveryError('reconciliation would exceed the stream event bound')
    with TemporaryDirectory(prefix='evidence-reconciliation-') as temporary:
        private = Path(temporary)
        for source in (Path(inspection)/'snapshot').iterdir():
            if source.name != MARKER:
                shutil.copyfile(source, private/source.name)
        # Rewind only this disposable copy. Ordinary resume checks the complete
        # previous wrapper, including alias order and its last saved projection.
        with closing(sqlite3.connect(private/'admission.db')) as connection, connection:
            connection.execute('DELETE FROM events WHERE sequence > ?', (body['journals']['authority']['sequence'],))
        path = private/'worker-checkpoint.json'
        clean = deepcopy(body); clean['pending'] = None
        envelope = json.loads(path.read_text())
        envelope.update(body=encode(clean), digest=fingerprint(encode(clean)))
        atomic_write(path, envelope)
        initial = AdmissionInitial.parse(body['initial'])
        with DurableAdmissionSession(initial, private, resume=True, native=body['native']) as session:
            if session._parse(event) != event or event['event_id'] in session.seen:
                raise RecoveryError('invalid pending evidence identity')
            args, service, event_id = event['arguments'], session.service, event['event_id']
            ctx = args['context_id']
            if ctx not in session.contexts or event_id in service._evidence:
                raise RecoveryError('evidence adoption requires a new report in a saved context')
            session.step += 1
            session.seen.add(event_id)
            session._prefix, session.certificates = event_id, []
            entries = []
            def check_entry():
                entry = asdict(service._journal.entries()[-1])
                index = len(entries)
                if entry['command'] != COMMANDS[index] or entry != boundary['appended'][index]:
                    raise RecoveryError('persisted evidence command differs: '+COMMANDS[index])
                entries.append(entry)
            service.record_evidence(Evidence(event_id, ctx, session.literal(args['literal']), 'sensor',
                service.snapshot(ctx).logical_time, tuple(args['roots']), args['valid_until']), idempotency_key=session.key())
            check_entry()
            transition = service.propose_evidence(ctx, event_id, idempotency_key=session.key())
            check_entry()
            revision = service.snapshot(ctx).knowledge_revision
            pre = service.precertify(transition, revision, idempotency_key=session.key())
            check_entry()
            if pre.status is not Status.PASS:
                raise RecoveryError('evidence adoption requires a successful pre-certificate')
            # Grounded hard inference constructs a deterministic value only; it
            # invokes no native inference engine and cannot publish a belief.
            proposal = service.infer(transition, pre)
            post = service.postcertify(proposal, pre, idempotency_key=session.key())
            check_entry()
            if post.status is not Status.PASS:
                raise RecoveryError('evidence adoption requires a successful post-certificate')
            result = service.commit(proposal, pre, post, revision, idempotency_key=session.key())
            check_entry()
            if result.status is not Status.PASS or result.belief is None or session._tips() != request['journals']:
                raise RecoveryError('evidence adoption requires the exact successful commit boundary')
            session.certificates = [pre, post]
            session.hard[event_id] = result.belief.belief_revision_id
            projection = session.projection()
            row = dict(schema='admission-trace/v1', step=session.step, event_id=event_id,
                event_digest=fingerprint(event), initial_digest=fingerprint(body['initial']),
                outcome=dict(status='PASS', detail='adopted by explicit persisted-evidence reconciliation'),
                projection=projection, projection_digest=fingerprint(projection),
                diagnostics=dict(certificates=encode(tuple(session.certificates)), elapsed_ns=0,
                    knowledge_revisions={c:service.snapshot(c).knowledge_revision for c in sorted(session.contexts)},
                    reconciliation=dict(decision_id=request['decision_id'], request_digest=fingerprint(request), action=ACTION)))
            session.completed[event_id] = dict(command=event, record=row)
            session._save()
        with DurableAdmissionSession(initial, private, resume=True, native=body['native']) as session:
            if session.apply(event) != row or not session.replayed:
                raise RecoveryError('candidate evidence reply failed exact recovery')
        return path.read_bytes(), row, entries


def validate_adoption(record, before):
    validate_chain(record, before, kind='evidence', commands=COMMANDS)
