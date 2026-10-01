"""Capture stopped-worker evidence and replay private copies without executor I/O.

Source SQLite files are never opened by SQLite: even a read/recovery connection
can change WAL/SHM files. Existing ownership locks protect capture. Inspection
never clears a pending command or grants permission to resume it.
"""
import argparse
from contextlib import ExitStack
from dataclasses import asdict, fields
import fcntl
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sqlite3
from tempfile import TemporaryDirectory

from .admission_protocol import AdmissionInitial, AdmissionEvent
from .codec import encode
from .dispatch_race_protocol import parse as dispatch_event
from .dispatch_worker_state import SCHEMA as DISPATCH_SCHEMA, journal_tip, read_checkpoint
from .journal import RecoveryError, StoreInUse
from .service import AdmissionService
from .simulated_executor import SimulatedExecutor
from .trace_protocol import DeploymentInitial, DeploymentEvent, canonical
from .trace_worker_state import SCHEMA as TRACE_SCHEMA

SCHEMA = 'worker-inspection/v1'
PROFILES = ('admission', 'deployment', 'dispatch')
DATABASES = dict(authority='admission.db', executor='executor.db')
MAX_CAPTURE = 256 * 1024 * 1024
MAX_FILES = 64


def capture_names(directory):
    names = {'worker.lock', 'worker-checkpoint.json'}
    for name in DATABASES.values():
        names.update(name + suffix for suffix in ('', '.lock', '-wal', '-shm', '-journal'))
    names.update(p.name for p in directory.glob('.checkpoint-*'))
    if len(names) > MAX_FILES:
        raise RecoveryError('inspection file count exceeds its bound')
    return sorted(names)


def file_inventory(directory, names):
    result, total = {}, 0
    for name in names:
        path = directory / name
        if path.is_symlink():
            raise RecoveryError('inspection requires regular evidence files')
        if not path.exists():
            result[name] = None
            continue
        if not path.is_file():
            raise RecoveryError('inspection requires regular evidence files')
        total += path.stat().st_size
        if total > MAX_CAPTURE:
            raise RecoveryError('inspection evidence exceeds its size bound')
        data = path.read_bytes()
        result[name] = dict(size=len(data), sha256=sha256(data).hexdigest())
    return result


def inventory(value):
    """Export keyed registries without losing tuple keys or typed leaf records."""
    if isinstance(value, dict):
        return sorted([dict(key=encode(key), value=encode(item)) for key,item in value.items()], key=canonical)
    if isinstance(value, set):
        return sorted([encode(item) for item in value], key=canonical)
    return encode(value)


def authority_state(service):
    ledgers = {name[1:]: inventory(getattr(service, name)) for name in (
        '_rules', '_rule_versions', '_policy_versions', '_evidence', '_revoked', '_transitions', '_certificates')}
    for name in ('_lifecycle', '_execution', '_dispatch', '_goals', '_completion', '_probability', '_decisions'):
        store = getattr(service, name)
        ledgers[name[1:]] = {field.name: inventory(getattr(store, field.name)) for field in fields(store)}
    ledgers['hard_beliefs'] = {key: inventory(context.beliefs) for key,context in sorted(service._contexts.items())}
    return dict(authority_id=service._authority_id, ledgers=ledgers, views=dict(
        contexts={key: encode(service.snapshot(key)) for key in sorted(service._contexts)},
        lifecycle={key: encode(service.inspect_lifecycle(key)) for key in sorted(service._lifecycle.episodes)},
        operations={key: encode(service.inspect_operation(key)) for key in sorted(service._lifecycle.attempts)},
        intents={key: encode(service.inspect_execution_intent(key)) for key in sorted(service._execution.intents)},
        dispatch={key: encode(service.inspect_dispatch(key)) for key in sorted(service._dispatch.attempts)},
        resources={key: encode(service.inspect_resource(key)) for key in sorted(service._execution.resources)},
        goals={key: encode(service.inspect_goal(key)) for key in sorted(service._goals.goals)}))


def boundary(saved, journal):
    entries = journal.entries()
    current = journal_tip(journal)
    if saved is None:
        return dict(saved=None, current=current, relation='unbound', appended=None)
    if (type(saved) is not dict or set(saved) != {'genesis','sequence','tail'}
            or type(saved['sequence']) is not int or saved['sequence'] < 0):
        return dict(saved=saved, current=current, relation='diverged', appended=None)
    n = saved['sequence']
    prefix = (saved['genesis'] == current['genesis'] and n <= len(entries)
              and saved['tail'] == (entries[n-1].entry_digest if n else current['genesis']))
    return dict(saved=saved, current=current, relation=('equal' if n == len(entries) else 'advanced') if prefix else 'diverged',
                appended=[asdict(entry) for entry in entries[n:]] if prefix else None)


def checkpoint(path, profile):
    schema = DISPATCH_SCHEMA if profile == 'dispatch' else TRACE_SCHEMA
    body = read_checkpoint(path, schema=schema)
    expected = ({'initial','journals','pending','attempts','seen','requests','receipts','certificates','completed'}
                if profile == 'dispatch' else {'profile','initial','native','journals','pending','metadata','completed'})
    if type(body) is not dict or set(body) != expected:
        raise RecoveryError('checkpoint fields differ')
    if profile != 'dispatch' and (body['profile'] != profile or type(body['native']) is not bool
                                 or profile == 'deployment' and body['native']):
        raise RecoveryError('checkpoint profile/backend differs')
    initial = (AdmissionInitial if profile == 'admission' else DeploymentInitial).parse(body['initial'])
    required = {'authority'} if profile == 'admission' else {'authority','executor'}
    if type(body['journals']) is not dict or set(body['journals']) != required or type(body['completed']) is not dict:
        raise RecoveryError('checkpoint journal/completed inventory differs')
    pending = body['pending']
    if pending is not None:
        if profile == 'admission':
            AdmissionEvent.parse(pending, len(initial.atoms))
        elif profile == 'deployment':
            DeploymentEvent.parse(pending)
        else:
            dispatch_event(pending)
        if pending['event_id'] in body['completed']:
            raise RecoveryError('pending command is already completed')
    return body


def analyze_snapshot(profile, snapshot, evidence):
    """Recompute an inspection solely from captured bytes, on disposable copies."""
    if profile not in PROFILES:
        raise ValueError('unsupported inspection profile')
    report = dict(schema=SCHEMA, profile=profile, evidence=evidence, checkpoint=None,
                  pending=None, journals={}, authority=None, executor=None, errors=[],
                  continuation_authorized=False)
    body = None
    try:
        body = checkpoint(snapshot/'worker-checkpoint.json', profile)
        report['checkpoint'] = encode(body)
        report['pending'] = body['pending']
    except (RecoveryError, ValueError, TypeError, KeyError) as error:
        report['errors'].append(dict(component='checkpoint', detail=str(error)))
    required = ['authority'] if profile == 'admission' else ['authority','executor']
    with TemporaryDirectory(prefix='worker-inspection-') as temporary:
        private = Path(temporary)
        for component in required:
            name = DATABASES[component]
            saved = body['journals'].get(component) if body is not None else None
            report['journals'][component] = dict(saved=saved, current=None, relation='unavailable', appended=None)
            try:
                if not (snapshot/name).is_file():
                    raise RecoveryError('required journal is missing')
                # SHM is a mutable WAL index, rebuilt only in this private copy.
                for suffix in ('', '-wal', '-journal'):
                    source = snapshot/(name+suffix)
                    if source.is_file():
                        shutil.copyfile(source, private/source.name)
                # Existing empty/partial databases must not be initialized by the
                # normal journal constructor and then reported as recovered state.
                connection = sqlite3.connect((private/name).as_uri()+'?mode=ro', uri=True)
                try:
                    if connection.execute('PRAGMA quick_check').fetchall() != [('ok',)]:
                        raise RecoveryError('SQLite integrity check failed')
                    if connection.execute('SELECT id FROM metadata').fetchall() != [(1,)]:
                        raise RecoveryError('journal metadata is missing or duplicated')
                    connection.execute('SELECT sequence FROM events LIMIT 1').fetchall()
                finally:
                    connection.close()
                cls = AdmissionService if component == 'authority' else SimulatedExecutor
                with cls(database=private/name) as recovered:
                    report['journals'][component] = boundary(saved, recovered._journal)
                    if component == 'authority':
                        report['authority'] = authority_state(recovered)
                    else:
                        report['executor'] = dict(profile=encode(recovered.profile), total_effects=recovered.total_effects,
                            requests=inventory(recovered._requests), receipts=inventory(recovered._receipts))
            except (RecoveryError, ValueError, TypeError, KeyError, OSError, sqlite3.Error) as error:
                report['errors'].append(dict(component=component, detail=str(error)))
    relations = {row['relation'] for row in report['journals'].values()}
    if report['errors'] or relations & {'diverged','unavailable','unbound'}:
        report['status'] = 'unverified'
    elif report['pending'] is not None:
        report['status'] = 'pending_journal_progress' if 'advanced' in relations else 'pending_no_journal_change'
    else:
        report['status'] = 'checkpoint_journal_mismatch' if 'advanced' in relations else 'no_pending_marker'
    return report


def inspect_worker(profile, directory, output):
    """Create a new evidence bundle; never create files in the worker directory."""
    if profile not in PROFILES:
        raise ValueError('unsupported inspection profile')
    directory, output = Path(directory).resolve(strict=True), Path(output).resolve()
    if not directory.is_dir() or output == directory or directory in output.parents:
        raise ValueError('inspection output must be outside the worker directory')
    if output.exists():
        raise FileExistsError('inspection output must be a new directory')
    with ExitStack() as stack:
        # Lock both databases even for an incorrectly selected profile. This
        # avoids a mixed snapshot if a caller mistakes a deployment for admission.
        locks = ['worker.lock'] + [name+'.lock' for name in DATABASES.values() if (directory/name).exists() or (directory/(name+'.lock')).exists()]
        for name in locks:
            path = directory/name
            if not path.is_file() or path.is_symlink():
                raise RecoveryError('existing ownership lock required: '+name)
            lock = stack.enter_context(path.open('rb'))
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise StoreInUse('stop the worker and journal owners before inspection') from error
        names = capture_names(directory)
        before = file_inventory(directory, names)
        snapshot = output/'snapshot'
        snapshot.mkdir(parents=True)
        for name, value in before.items():
            if value is not None:
                shutil.copyfile(directory/name, snapshot/name)
        if (capture_names(directory) != names or file_inventory(directory, names) != before
                or file_inventory(snapshot, names) != before):
            raise RecoveryError('worker evidence changed during capture')
    report = analyze_snapshot(profile, snapshot, before)
    (output/'report.json').write_text(canonical(report)+'\n')
    (output/'receipt.json').write_text(canonical(dict(schema=SCHEMA, profile=profile,
        report_sha256=sha256((output/'report.json').read_bytes()).hexdigest(), files=before))+'\n')
    return report


def verify_inspection(output):
    """Check exact evidence inventory and reproduce the report without source I/O."""
    output = Path(output)
    receipt = json.loads((output/'receipt.json').read_text())
    snapshot = output/'snapshot'
    if (set(receipt) != {'schema','profile','report_sha256','files'} or receipt['schema'] != SCHEMA
            or set(receipt['files']) != set(capture_names(snapshot))
            or {p.name for p in snapshot.iterdir()} != {n for n,v in receipt['files'].items() if v is not None}
            or file_inventory(snapshot, sorted(receipt['files'])) != receipt['files']
            or sha256((output/'report.json').read_bytes()).hexdigest() != receipt['report_sha256']):
        raise RecoveryError('inspection receipt/files differ')
    expected = analyze_snapshot(receipt['profile'], snapshot, receipt['files'])
    if json.loads((output/'report.json').read_text()) != expected:
        raise RecoveryError('inspection report differs from captured evidence')
    return expected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', required=True, choices=PROFILES)
    parser.add_argument('--database-dir', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    report = inspect_worker(args.profile, args.database_dir, args.output)
    print(canonical(dict(schema=SCHEMA, status=report['status'], output=str(args.output),
                         continuation_authorized=False)), flush=True)


if __name__ == '__main__':
    main()
