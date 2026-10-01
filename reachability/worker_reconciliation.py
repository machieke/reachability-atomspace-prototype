"""Explicit cancellation of an unstarted local event, bound to captured evidence.

No authority journal command, public event or executor operation is executed.
A prepared marker blocks worker startup until the exact decision is finished.
"""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import argparse
import shutil
from tempfile import TemporaryDirectory, NamedTemporaryFile

from .admission_protocol import AdmissionInitial, ARGUMENTS as ADMISSION_KINDS
from .codec import decode, encode
from .dispatch_worker_state import atomic_write, MAX_CHECKPOINT
from .journal import RecoveryError
from .reconciliation_state import ARCHIVE, MARKER
from .trace_protocol import DeploymentInitial, canonical, fingerprint, identifier, read_json
from .trace_worker_state import DurableAdmissionSession, DurableDeploymentSession
from .worker_inspection import verify_inspection, owned_worker, capture_names, file_inventory, PROFILES

REQUEST_SCHEMA = 'worker-reconciliation-request/v1'
RECORD_SCHEMA = 'worker-reconciliation-prepared/v1'
RESULT_SCHEMA = 'worker-reconciliation-result/v1'
ACTION = 'cancel_unstarted_local'
LOCAL_DEPLOYMENT = frozenset(('fact','forecast','revoke','tick','attempt','reserve','cover','prepare',
    'observation','sample','censor','resume','account','complete','restart'))


def digest_bytes(data):
    return sha256(data).hexdigest()


def parse_request(value):
    fields = {'schema','decision_id','action','profile','inspection_digest','checkpoint_sha256','pending_digest','journals'}
    if type(value) is not dict or set(value) != fields or value['schema'] != REQUEST_SCHEMA:
        raise ValueError('invalid reconciliation request fields/schema')
    identifier(value['decision_id'])
    if value['action'] != ACTION or value['profile'] not in PROFILES:
        raise ValueError('unsupported reconciliation action/profile')
    for name in ('inspection_digest','checkpoint_sha256','pending_digest'):
        if type(value[name]) is not str or len(value[name]) != 64 or any(c not in '0123456789abcdef' for c in value[name]):
            raise ValueError('invalid reconciliation digest')
    expected = {'authority'} if value['profile'] == 'admission' else {'authority','executor'}
    if type(value['journals']) is not dict or set(value['journals']) != expected:
        raise ValueError('invalid reconciliation journal inventory')
    for tip in value['journals'].values():
        if (type(tip) is not dict or set(tip) != {'genesis','sequence','tail'} or type(tip['sequence']) is not int
                or tip['sequence'] < 0 or any(type(tip[k]) is not str or len(tip[k]) != 64
                    or any(c not in '0123456789abcdef' for c in tip[k]) for k in ('genesis','tail'))):
            raise ValueError('invalid reconciliation journal tip')
    if len(canonical(value).encode()) > 65536:
        raise ValueError('reconciliation request exceeds its bound')
    return deepcopy(value)


def make_request(inspection, decision_id):
    report = verify_inspection(Path(inspection))
    if report['pending'] is None or report['checkpoint'] is None or report['errors']:
        raise RecoveryError('a verified pending command is required')
    return parse_request(dict(schema=REQUEST_SCHEMA, decision_id=decision_id, action=ACTION, profile=report['profile'],
        inspection_digest=fingerprint(report), checkpoint_sha256=report['evidence']['worker-checkpoint.json']['sha256'],
        pending_digest=fingerprint(report['pending']), journals={k:v['current'] for k,v in report['journals'].items()}))


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def mkdir_durable(path):
    if not path.exists():
        path.mkdir()
        sync_directory(path.parent)
    if not path.is_dir() or path.is_symlink():
        raise RecoveryError('invalid reconciliation archive directory')


def archive_bytes(path, data):
    if path.exists():
        if path.read_bytes() != data:
            raise RecoveryError('prepared checkpoint archive differs')
        return
    temporary = None
    try:
        with NamedTemporaryFile(dir=path.parent, prefix='.reconcile-stage-', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        sync_directory(path.parent)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def read_control(path):
    try:
        value = read_json(path.read_text())
        if (type(value) is not dict or set(value) != {'body','digest'}
                or fingerprint(value['body']) != value['digest']):
            raise ValueError('integrity mismatch')
        return value['body']
    except (ValueError, KeyError, TypeError, OSError) as error:
        raise RecoveryError('reconciliation control record cannot be read') from error


def control(value):
    return dict(body=value, digest=fingerprint(value))


def journal_evidence(evidence):
    # Checkpoint publication and its leftover temporary files are controlled by
    # this decision. Database bytes and sidecars must remain exactly unchanged.
    return {k:v for k,v in evidence.items() if k == 'worker.lock' or k.startswith(('admission.db','executor.db'))}


def candidate_checkpoint(report, inspection, request):
    body = decode(report['checkpoint'])
    profile, event = request['profile'], report['pending']
    kinds = ADMISSION_KINDS if profile == 'admission' else LOCAL_DEPLOYMENT
    if profile == 'dispatch' or event['kind'] not in kinds:
        raise RecoveryError('cancellation supports only admission and local deployment events')
    if (report['status'] != 'pending_no_journal_change' or report['errors']
            or any(v['relation'] != 'equal' for v in report['journals'].values())):
        raise RecoveryError('cancellation requires no journal progress')
    if len(body['completed']) >= 128:
        raise RecoveryError('reconciliation would exceed the stream event bound')
    with TemporaryDirectory(prefix='reconciliation-check-') as temporary:
        private = Path(temporary)
        # Copy only checkpoint and journal evidence. Never copy a reconciliation
        # control marker into the disposable wrapper-validation session.
        for source in (Path(inspection)/'snapshot').iterdir():
            if source.name != MARKER:
                shutil.copyfile(source, private/source.name)
        path = private/'worker-checkpoint.json'
        envelope = json.loads(path.read_text())
        clean = deepcopy(body); clean['pending'] = None
        envelope['body'] = encode(clean); envelope['digest'] = fingerprint(envelope['body'])
        atomic_write(path, envelope)
        cls = DurableAdmissionSession if profile == 'admission' else DurableDeploymentSession
        initial = (AdmissionInitial if profile == 'admission' else DeploymentInitial).parse(body['initial'])
        kwargs = dict(native=body['native']) if profile == 'admission' else {}
        # Existing restore validates full inventories, aliases/rules, counters,
        # reply identities/digests and the last projection, without event replay.
        with cls(initial, private, resume=True, **kwargs) as session:
            projection = session.projection()
            session.step += 1
            session.seen.add(event['event_id'])
            session._prefix = event['event_id'] if profile == 'admission' else 'event:'+event['event_id']
            session.certificates = []
            diagnostics = dict(certificates=encode(()), elapsed_ns=0, reconciliation=dict(
                decision_id=request['decision_id'], request_digest=fingerprint(request), action=ACTION))
            if profile == 'admission':
                diagnostics['knowledge_revisions'] = {c:session.service.snapshot(c).knowledge_revision for c in sorted(session.contexts)}
            else:
                diagnostics.update(knowledge_revision=session.service.snapshot(initial.context_id).knowledge_revision,
                    resource_revision=session.service.resource_snapshot().revision, journal_commands=0)
            row = dict(schema=profile+'-trace/v1', step=session.step, event_id=event['event_id'],
                event_digest=fingerprint(event), initial_digest=fingerprint(body['initial']),
                outcome=dict(status='UNKNOWN', detail='cancelled by explicit reconciliation without journal progress'),
                projection=projection, projection_digest=fingerprint(projection), diagnostics=diagnostics)
            if profile == 'deployment':
                row['instrumentation'] = dict(executor_effects=session.executor.total_effects)
            session.completed[event['event_id']] = dict(command=event, record=row)
            session._save()
        # The proposed checkpoint must itself satisfy the ordinary resume path.
        with cls(initial, private, resume=True, **kwargs) as session:
            if session.apply(event) != row or not session.replayed:
                raise RecoveryError('candidate cancellation reply failed exact recovery')
        return path.read_bytes(), row


def archive_path(directory, request):
    # Public identities need not be safe path components.
    return directory/ARCHIVE/fingerprint(request['decision_id'])


def expected_result(record):
    return dict(schema=RESULT_SCHEMA, decision_id=record['request']['decision_id'],
        request_digest=fingerprint(record['request']), action=ACTION, profile=record['request']['profile'],
        event_id=record['event_id'], status='APPLIED', outcome='cancelled',
        before_checkpoint_sha256=record['before_sha256'], after_checkpoint_sha256=record['after_sha256'],
        journals=record['request']['journals'], reply_digest=record['reply_digest'])


def validate_archive(archive, request):
    record = read_control(archive/'prepared.json')
    if (type(record) is not dict or set(record) != {'schema','request','event_id','before_sha256','after_sha256','journal_files','reply_digest'}
            or record['schema'] != RECORD_SCHEMA or record['request'] != request
            or record['before_sha256'] != request['checkpoint_sha256']):
        raise RecoveryError('decision identity or prepared record differs')
    expected_files={'worker.lock'} | {base+suffix for base in ('admission.db','executor.db')
        for suffix in ('','.lock','-wal','-shm','-journal')}
    if type(record['journal_files']) is not dict or set(record['journal_files']) != expected_files:
        raise RecoveryError('prepared journal file inventory differs')
    for name, digest in (('before.json',record['before_sha256']),('after.json',record['after_sha256'])):
        path=archive/name
        if not path.is_file() or path.stat().st_size > MAX_CHECKPOINT or digest_bytes(path.read_bytes()) != digest:
            raise RecoveryError('reconciliation checkpoint archive differs')
    after = json.loads((archive/'after.json').read_text())
    if fingerprint(after['body']) != after['digest']:
        raise RecoveryError('candidate checkpoint integrity differs')
    body=decode(after['body'])
    saved=body['completed'][record['event_id']]
    if (body['pending'] is not None or fingerprint(saved['command']) != request['pending_digest']
            or fingerprint(saved['record']) != record['reply_digest'] or body['journals'] != request['journals']):
        raise RecoveryError('candidate reply/boundary differs')
    return record


def finish(directory, archive, record):
    marker=directory/MARKER
    if read_control(marker) != record:
        raise RecoveryError('another or corrupted reconciliation is pending')
    actual=file_inventory(directory, sorted(record['journal_files']))
    if actual != record['journal_files']:
        raise RecoveryError('journal evidence changed during reconciliation')
    path=directory/'worker-checkpoint.json'
    current=digest_bytes(path.read_bytes())
    if current not in (record['before_sha256'],record['after_sha256']):
        raise RecoveryError('checkpoint changed during reconciliation')
    if current == record['before_sha256']:
        atomic_write(path, json.loads((archive/'after.json').read_text()))  # Publish cancellation.
    if digest_bytes(path.read_bytes()) != record['after_sha256']:
        raise RecoveryError('published checkpoint differs from prepared decision')
    result=expected_result(record)
    if (archive/'result.json').exists():
        if read_control(archive/'result.json') != result:
            raise RecoveryError('durable reconciliation result differs')
    else:
        atomic_write(archive/'result.json', control(result))  # Durable result precedes marker removal.
    marker.unlink()
    sync_directory(directory)
    return result


def reconcile(request, directory, inspection):
    request=parse_request(request)
    directory=Path(directory).resolve(strict=True)
    inspection=Path(inspection).resolve()
    if not directory.is_dir():
        raise ValueError('existing worker directory required')
    archive=archive_path(directory,request)
    if (directory/ARCHIVE).is_symlink() or archive.is_symlink():
        raise RecoveryError('invalid reconciliation archive directory')
    with owned_worker(directory):
        if (archive/'result.json').exists():
            record=validate_archive(archive,request)
            result=read_control(archive/'result.json')
            if result != expected_result(record):
                raise RecoveryError('durable reconciliation result differs')
            if (directory/MARKER).exists() and read_control(directory/MARKER) == record:
                finish(directory,archive,record)
            return dict(result=result, replayed=True)
        if (directory/MARKER).exists():
            record=validate_archive(archive,request)
            if read_control(directory/MARKER) != record:
                raise RecoveryError('another or corrupted reconciliation is pending')
            # The prepared record already binds the retained evidence and target;
            # it can finish after a crash without an external inspection path.
            result=finish(directory,archive,record)
            return dict(result=result, replayed=True)
        report=verify_inspection(inspection)
        if (report['profile'] != request['profile'] or fingerprint(report) != request['inspection_digest']
                or fingerprint(report['pending']) != request['pending_digest']
                or report['evidence']['worker-checkpoint.json']['sha256'] != request['checkpoint_sha256']
                or {k:v['current'] for k,v in report['journals'].items()} != request['journals']):
            raise RecoveryError('request differs from inspected pending command/boundaries')
        if file_inventory(directory,capture_names(directory)) != report['evidence']:
            raise RecoveryError('inspection is stale; worker evidence changed')
        after, row=candidate_checkpoint(report,inspection,request)
        before=(directory/'worker-checkpoint.json').read_bytes()
        record=dict(schema=RECORD_SCHEMA, request=request, event_id=report['pending']['event_id'],
            before_sha256=digest_bytes(before), after_sha256=digest_bytes(after),
            journal_files=journal_evidence(report['evidence']), reply_digest=fingerprint(row))
        mkdir_durable(directory/ARCHIVE)
        mkdir_durable(archive)
        # Preparation is repeatable after a crash before marker publication. Never
        # overwrite a different decision, including an incomplete earlier one.
        prepared=archive/'prepared.json'
        prepared_before=prepared.exists()
        if prepared_before and read_control(prepared) != record:
            raise RecoveryError('decision identity cannot be rebound')
        atomic_write(prepared,control(record))
        for name,data in (('before.json',before),('after.json',after)):
            # Before bytes can have a noncanonical layout; preserve them exactly.
            archive_bytes(archive/name,data)
        validate_archive(archive,request)
        atomic_write(directory/MARKER,control(record))  # Worker gate precedes checkpoint publication.
        return dict(result=finish(directory,archive,record), replayed=prepared_before)


def verify_reconciliation(archive, inspection):
    """Reproduce an archived decision from its retained original inspection."""
    archive, inspection=Path(archive),Path(inspection)
    prepared=read_control(archive/'prepared.json')
    request=parse_request(prepared['request'])
    record=validate_archive(archive,request)
    report=verify_inspection(inspection)
    if make_request(inspection,request['decision_id']) != request:
        raise RecoveryError('decision differs from original inspection')
    after,row=candidate_checkpoint(report,inspection,request)
    if (after != (archive/'after.json').read_bytes()
            or (inspection/'snapshot'/'worker-checkpoint.json').read_bytes() != (archive/'before.json').read_bytes()
            or journal_evidence(report['evidence']) != record['journal_files']
            or fingerprint(row) != record['reply_digest']):
        raise RecoveryError('decision cannot be reproduced from original evidence')
    if (archive/'result.json').exists():
        result=read_control(archive/'result.json')
        if result != expected_result(record):
            raise RecoveryError('durable reconciliation result differs')
        return result
    return dict(schema=RECORD_SCHEMA,status='PREPARED',request_digest=fingerprint(request))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    prepare=sub.add_parser('request',help='print a request bound to an inspection; no worker mutation')
    prepare.add_argument('--inspection',required=True,type=Path)
    prepare.add_argument('--decision-id',required=True)
    apply=sub.add_parser('apply',help='apply or exactly retry an explicit reconciliation request')
    apply.add_argument('--request',required=True,type=Path)
    apply.add_argument('--inspection',required=True,type=Path)
    apply.add_argument('--database-dir',required=True,type=Path)
    args=parser.parse_args()
    result=(make_request(args.inspection,args.decision_id) if args.command=='request' else
            reconcile(read_json(args.request.read_text()),args.database_dir,args.inspection))
    print(canonical(result),flush=True)


if __name__=='__main__':
    main()
