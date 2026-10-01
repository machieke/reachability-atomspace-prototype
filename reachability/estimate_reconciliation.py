"""Adopt one fully persisted, successful numerical observation admission event.

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
from .pln_adapter import TruthValue
from .probability_model import ProbabilityReport
from .reconciliation_state import MARKER
from .trace_protocol import fingerprint
from .trace_worker_state import DurableAdmissionSession

ACTION = 'adopt_persisted_estimate'
COMMANDS = ('record_evidence', 'record_probability_report', 'propose_probability',
    'precertify_probability', 'postcertify_probability', 'commit_probability')


def candidate(report, inspection, request):
    body, event = decode(report['checkpoint']), report['pending']
    boundary = report['journals'].get('authority', {})
    if (request['profile'] != 'admission' or event['kind'] != 'estimate' or report['errors']
            or report['status'] != 'pending_journal_progress' or boundary.get('relation') != 'advanced'
            or len(boundary.get('appended', [])) != len(COMMANDS)):
        raise RecoveryError('estimate adoption requires exactly six persisted numerical-estimate commands')
    if len(body['completed']) >= 128:
        raise RecoveryError('reconciliation would exceed the stream event bound')
    with TemporaryDirectory(prefix='estimate-reconciliation-') as temporary:
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
                raise RecoveryError('invalid pending estimate identity')
            args, service, event_id = event['arguments'], session.service, event['event_id']
            ctx = args['context_id']
            if ctx not in session.contexts or event_id in service._evidence or event_id in service._probability.reports:
                raise RecoveryError('estimate adoption requires a new report in a saved context')
            session.step += 1
            session.seen.add(event_id)
            session._prefix, session.certificates = event_id, []
            entries = []
            def check_entry():
                entry = asdict(service._journal.entries()[-1])
                index = len(entries)
                if entry['command'] != COMMANDS[index] or entry != boundary['appended'][index]:
                    raise RecoveryError('persisted estimate command differs: '+COMMANDS[index])
                entries.append(entry)
            service.record_evidence(Evidence(event_id, ctx, session.literal(args['literal']), 'sensor',
                service.snapshot(ctx).logical_time, tuple(args['roots']), args['valid_until']), idempotency_key=session.key())
            check_entry()
            service.record_probability_report(ProbabilityReport(event_id, TruthValue(args['strength'], args['confidence'])),
                idempotency_key=session.key())
            check_entry()
            transition = service.propose_probability(ctx, 'observation', evidence_id=event_id, idempotency_key=session.key())
            check_entry()
            revision = service.snapshot(ctx).knowledge_revision
            pre = service.precertify_probability(transition, revision, idempotency_key=session.key())
            check_entry()
            if pre.status is not Status.PASS:
                raise RecoveryError('estimate adoption requires a successful pre-certificate')
            # Only the observation transition is constructed above. Its proposal
            # preserves the recorded truth values and uses no inference adapter;
            # numerical revision/deduction events require separate decisions.
            proposal = service.infer_probability(transition, pre)
            post = service.postcertify_probability(proposal, pre, idempotency_key=session.key())
            check_entry()
            if post.status is not Status.PASS:
                raise RecoveryError('estimate adoption requires a successful post-certificate')
            result = service.commit_probability(proposal, pre, post, revision, idempotency_key=session.key())
            check_entry()
            if result.status is not Status.PASS or result.belief is None or session._tips() != request['journals']:
                raise RecoveryError('estimate adoption requires the exact successful commit boundary')
            session.certificates = [pre, post]
            session.numeric[event_id] = result.belief.belief_revision_id
            projection = session.projection()
            row = dict(schema='admission-trace/v1', step=session.step, event_id=event_id,
                event_digest=fingerprint(event), initial_digest=fingerprint(body['initial']),
                outcome=dict(status='PASS', detail='adopted by explicit persisted-estimate reconciliation'),
                projection=projection, projection_digest=fingerprint(projection),
                diagnostics=dict(certificates=encode(tuple(session.certificates)), elapsed_ns=0,
                    knowledge_revisions={c:service.snapshot(c).knowledge_revision for c in sorted(session.contexts)},
                    reconciliation=dict(decision_id=request['decision_id'], request_digest=fingerprint(request), action=ACTION)))
            session.completed[event_id] = dict(command=event, record=row)
            session._save()
        with DurableAdmissionSession(initial, private, resume=True, native=body['native']) as session:
            if session.apply(event) != row or not session.replayed:
                raise RecoveryError('candidate estimate reply failed exact recovery')
        return path.read_bytes(), row, entries


def validate_adoption(record, before):
    validate_chain(record, before, kind='estimate', commands=COMMANDS)
