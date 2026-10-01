"""Quiescent dispatch-worker checkpoints, bound to both real journals.

A durable pending marker makes interrupted composite commands fail closed.
Completed reply retries do not execute the command or send to the executor.
This is trusted local storage, not an authenticated external transport.
"""
from dataclasses import asdict
import fcntl
from itertools import count
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Lock, local

from .codec import encode, decode
from .dispatch_race_protocol import parse
from .dispatch_race_session import DispatchRaceSession
from .journal import RecoveryError, StoreInUse
from .service import AdmissionService
from .simulated_executor import SimulatedExecutor
from .trace_protocol import DeploymentInitial, canonical, fingerprint

SCHEMA = 'dispatch-worker-checkpoint/v1'
MAX_CHECKPOINT = 32 * 1024 * 1024


def journal_tip(journal):
    entries = journal.entries()
    return dict(genesis=journal._genesis, sequence=len(entries), tail=entries[-1].entry_digest if entries else journal._genesis)


def atomic_write(path, value):
    wire = (canonical(value)+'\n').encode()
    if len(wire) > MAX_CHECKPOINT:
        raise ValueError('worker checkpoint exceeds its size bound')
    temporary = None
    try:
        with NamedTemporaryFile(dir=path.parent, prefix='.checkpoint-', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(wire)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def read_checkpoint(path, *, schema=SCHEMA):
    def unique(pairs):
        result = {}
        for key,value in pairs:
            if key in result:
                raise RecoveryError('duplicate checkpoint field')
            result[key] = value
        return result
    try:
        with path.open('rb') as stream:
            data = stream.read(MAX_CHECKPOINT+1)
        if len(data) > MAX_CHECKPOINT:
            raise RecoveryError('worker checkpoint exceeds its size bound')
        value = json.loads(data,object_pairs_hook=unique)
        if (type(value) is not dict or set(value) != {'schema','body','digest'} or value['schema'] != schema
                or fingerprint(value['body']) != value['digest']):
            raise RecoveryError('worker checkpoint schema/integrity mismatch')
        return decode(value['body'])
    except (ValueError, TypeError, KeyError, OSError) as error:
        raise RecoveryError('worker checkpoint cannot be read') from error


class DurableDispatchSession(DispatchRaceSession):
    def __init__(self, initial, directory, *, resume=False):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True,exist_ok=True)
        self.checkpoint_path = self.directory/'worker-checkpoint.json'
        self._worker_lock = (self.directory/'worker.lock').open('a+b')
        try:
            fcntl.flock(self._worker_lock.fileno(),fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            self._worker_lock.close()
            raise StoreInUse('another process owns this worker directory') from error
        self.completed, self.pending, self.replayed, self._broken = {}, None, False, False
        try:
            if resume:
                self._restore(initial)
            else:
                if self.checkpoint_path.exists():
                    raise ValueError('worker directory already contains a checkpoint; use explicit resume')
                super().__init__(initial,directory)
                self._save()
        except BaseException:
            self.close()
            raise

    def _body(self):
        return dict(initial=asdict(self.initial), journals=self._tips(), pending=self.pending,
            attempts=sorted(self.attempts), seen=sorted(self.seen), requests=self.requests, receipts=self.receipts,
            certificates=tuple(self.certificates), completed=self.completed)

    def _tips(self):
        return dict(authority=journal_tip(self.service._journal),executor=journal_tip(self.executor._journal))

    def _save(self):
        body = encode(self._body())
        atomic_write(self.checkpoint_path,dict(schema=SCHEMA,body=body,digest=fingerprint(body)))

    def _restore(self, initial):
        body = read_checkpoint(self.checkpoint_path)
        if (type(body) is not dict or set(body) != {'initial','journals','pending','attempts','seen','requests','receipts','certificates','completed'}
                or body['initial'] != asdict(initial)):
            raise RecoveryError('worker checkpoint initial state/fields mismatch')
        if body['pending'] is not None:
            raise RecoveryError('interrupted worker command requires explicit reconciliation; automatic resume refused')
        self.initial = DeploymentInitial.parse(body['initial'])
        self.local,self.remote = self.directory/'admission.db',self.directory/'executor.db'
        if not self.local.is_file() or not self.remote.is_file():
            raise RecoveryError('worker requires both existing journals')
        self.service = AdmissionService(database=self.local)
        self.executor = SimulatedExecutor(self.remote)
        if body['journals'] != self._tips():
            raise RecoveryError('worker checkpoint and journals differ; automatic resume refused')
        self._event_local,self._metadata = local(),Lock()
        self._keys,self._prefix,self.step = count(),'restored',0
        self.attempts,self.seen = set(body['attempts']),set(body['seen'])
        self.requests,self.receipts = body['requests'],body['receipts']
        self.certificates,self.completed = list(body['certificates']),body['completed']
        if len(self.seen) > 64 or set(self.completed) != self.seen:
            raise RecoveryError('worker completed-event inventory differs')
        # Receipts may be older than the executor's current state. Bind each
        # stored packet to the exact prepared request without replacing it by a
        # fresh query (which would erase delayed acknowledgement semantics).
        for request in self.requests.values():
            if request != self.service.inspect_dispatch(request.intent.attempt_id).dispatch.request:
                raise RecoveryError('queued request differs from durable dispatch intent')
        for attempt,receipt in self.receipts.values():
            record = self.service.inspect_dispatch(attempt).dispatch
            if (receipt.request_id,receipt.request_fingerprint,receipt.instance_id) != (
                    record.request.request_id,record.request.fingerprint,self.executor.profile.instance_id):
                raise RecoveryError('queued receipt differs from durable executor binding')
        for key,record in self.completed.items():
            command = parse(record['command'])
            if command['event_id'] != key or record['record']['outcome']['event_id'] != key:
                raise RecoveryError('worker completed reply identity differs')

    def apply(self, message):
        if self._broken:
            raise RecoveryError('worker requires reopening after storage or command failure')
        message = parse(message)
        key = message['event_id']
        old = self.completed.get(key)
        if old is not None:
            if canonical(old['command']) != canonical(message):
                raise ValueError('completed event identity cannot be rebound')
            self.replayed = True
            # Return a detached historical reply, not a current-state assertion.
            return json.loads(canonical(old['record']))
        if self.pending is not None:
            raise RecoveryError('worker has an unresolved command')
        if len(self.completed) >= 64:
            raise ValueError('worker event bound exceeded')
        try:
            self.replayed,self.pending = False,message
            self._save()  # Must precede any authority mutation, inbox change or send.
            row = super().apply(message)
            self.completed[key] = dict(command=message,record=row)
            self.pending = None
            self._save()  # Must precede a successful response on stdout.
            return json.loads(canonical(row))
        except BaseException:
            self._broken = True
            raise

    def restart(self):
        # Preserve wrapper ownership while reopening the two authority stores.
        self.service.close()
        self.executor.close()
        self.service = AdmissionService(database=self.local)
        try:
            self.executor = SimulatedExecutor(self.remote)
        except BaseException:
            self.service.close()
            raise

    def close(self):
        if hasattr(self,'service'):
            super().close()
        if hasattr(self,'_worker_lock') and not self._worker_lock.closed:
            fcntl.flock(self._worker_lock.fileno(),fcntl.LOCK_UN)
            self._worker_lock.close()
