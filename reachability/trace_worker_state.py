"""Completed admission/deployment stream recovery without replaying public events.

Only the actual authority journals replay. Wrapper aliases keep their insertion
order; saved replies, including diagnostics, are historical and immutable.
Interrupted composite commands require explicit reconciliation, not blind retry.
"""
from dataclasses import asdict
import fcntl
from itertools import count
import json
from pathlib import Path

from .admission_protocol import AdmissionInitial, AdmissionEvent, rule
from .admission_trace import AdmissionSession
from .codec import encode
from .deployment_trace import DeploymentSession
from .dispatch_worker_state import atomic_write, journal_tip, read_checkpoint
from .journal import RecoveryError, StoreInUse
from .pln_adapter import PLNAdapter
from .probability_formula import PinnedFormulaRuntime
from .service import AdmissionService
from .simulated_executor import SimulatedExecutor
from .trace_protocol import DeploymentInitial, DeploymentEvent, canonical, fingerprint, identifier

SCHEMA = 'trace-worker-checkpoint/v1'


def ordered_map(value):
    if type(value) is not list or len(value)>128:
        raise RecoveryError('invalid ordered alias inventory')
    result={}
    for pair in value:
        if type(pair) is not list or len(pair)!=2:
            raise RecoveryError('invalid ordered alias entry')
        key,target=pair
        identifier(key)
        identifier(target)
        if key in result:
            raise RecoveryError('duplicate ordered alias')
        result[key]=target
    return result


class _DurableTrace:
    """Shared serial checkpoint transaction for the two original trace adapters."""
    def __init__(self, initial, directory, *, resume=False, native=False):
        if type(native) is not bool:
            raise ValueError('native inference mode must be Boolean')
        if native and self.profile!='admission':
            raise ValueError('native inference mode applies only to admission')
        self.native=native
        self.directory=Path(directory)
        self.directory.mkdir(parents=True,exist_ok=True)
        self.checkpoint_path=self.directory/'worker-checkpoint.json'
        self._worker_lock=(self.directory/'worker.lock').open('a+b')
        try:
            fcntl.flock(self._worker_lock.fileno(),fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            self._worker_lock.close()
            raise StoreInUse('another process owns this worker directory') from error
        self.completed,self.pending,self.replayed,self._broken={},None,False,False
        try:
            if resume:
                self._restore(initial)
            else:
                if self.checkpoint_path.exists():
                    raise ValueError('worker checkpoint exists; use explicit resume')
                if self.profile=='admission':
                    super().__init__(initial,directory,native=native)
                else:
                    super().__init__(initial,directory)
                self._save()
        except BaseException:
            self.close()
            raise

    def _public(self):
        return self.initial.wire() if self.profile=='admission' else asdict(self.initial)

    def _parse(self,message):
        if self.profile=='admission':
            return AdmissionEvent.parse(message,len(self.initial.atoms)).wire()
        return DeploymentEvent.parse(message).wire()

    def _tips(self):
        tips=dict(authority=journal_tip(self.service._journal))
        if self.profile=='deployment':
            tips['executor']=journal_tip(self.executor._journal)
        return tips

    def _metadata(self):
        common=dict(step=self.step,seen=sorted(self.seen),prefix=self._prefix,
            next_key=self._keys.__reduce__()[1][0],certificates=tuple(self.certificates))
        if self.profile=='admission':
            common.update(contexts=sorted(self.contexts),rules=list(self.rules.values()),
                hard=[list(pair) for pair in self.hard.items()],numeric=[list(pair) for pair in self.numeric.items()])
        else:
            common['attempts']=sorted(self.attempts)
        return common

    def _save(self):
        body=encode(dict(profile=self.profile,initial=self._public(),native=self.native,journals=self._tips(),
            pending=self.pending,metadata=self._metadata(),completed=self.completed))
        atomic_write(self.checkpoint_path,dict(schema=SCHEMA,body=body,digest=fingerprint(body)))

    def _restore(self,initial):
        body=read_checkpoint(self.checkpoint_path,schema=SCHEMA)
        public=initial.wire() if self.profile=='admission' else asdict(initial)
        if (type(body) is not dict or set(body)!={'profile','initial','native','journals','pending','metadata','completed'}
                or body['profile']!=self.profile or canonical(body['initial'])!=canonical(public)
                or body['native'] is not self.native):
            raise RecoveryError('worker checkpoint profile/initial/backend mismatch')
        if body['pending'] is not None:
            raise RecoveryError('interrupted worker command requires explicit reconciliation; automatic resume refused')
        self.initial=AdmissionInitial.parse(public) if self.profile=='admission' else DeploymentInitial.parse(public)
        self.path=self.local=self.directory/'admission.db'
        self.remote=self.directory/'executor.db'
        if not self.local.is_file() or self.profile=='deployment' and not self.remote.is_file():
            raise RecoveryError('worker requires all existing journals')
        self.service=AdmissionService(database=self.local)
        if self.profile=='deployment':
            self.executor=SimulatedExecutor(self.remote)
        if body['journals']!=self._tips():
            raise RecoveryError('worker checkpoint and journals differ; automatic resume refused')
        metadata=body['metadata']
        fields={'step','seen','prefix','next_key','certificates'} | (
            {'contexts','rules','hard','numeric'} if self.profile=='admission' else {'attempts'})
        if (type(metadata) is not dict or set(metadata)!=fields or type(metadata['step']) is not int
                or not 0<=metadata['step']<=128 or type(metadata['next_key']) is not int or metadata['next_key']<0
                or type(metadata['seen']) is not list or len(set(metadata['seen']))!=len(metadata['seen'])
                or type(body['completed']) is not dict):
            raise RecoveryError('worker stream metadata is invalid')
        self.step,self.seen=metadata['step'],set(metadata['seen'])
        self._prefix,self._keys=metadata['prefix'],count(metadata['next_key'])
        self.certificates,self.completed=list(metadata['certificates']),body['completed']
        if len(self.seen)!=self.step or set(self.completed)!=self.seen:
            raise RecoveryError('worker completed-event inventory differs')
        steps=[]
        for key,saved in self.completed.items():
            message=self._parse(saved['command'])
            row=saved['record']
            if (message['event_id']!=key or row['event_id']!=key or row['event_digest']!=fingerprint(message)
                    or row['initial_digest']!=fingerprint(public) or row['projection_digest']!=fingerprint(row['projection'])
                    or type(row['step']) is not int):
                raise RecoveryError('worker completed reply identity/digest differs')
            steps.append(row['step'])
        if sorted(steps)!=list(range(1,self.step+1)):
            raise RecoveryError('worker completed reply steps differ')
        if self.profile=='admission':
            contexts=metadata['contexts']
            if type(contexts) is not list or len(contexts)>4 or len(set(contexts))!=len(contexts):
                raise RecoveryError('worker context inventory is invalid')
            self.contexts=set(contexts)
            if self.contexts!=set(self.service._contexts):
                raise RecoveryError('worker contexts differ from authority')
            rules=metadata['rules']
            if type(rules) is not list or len(rules)>8:
                raise RecoveryError('worker rule inventory is invalid')
            for item in rules:
                rule(item,len(self.initial.atoms))
            self.rules={r['rule_id']:r for r in rules}
            if len(self.rules)!=len(rules) or {key:self.rule(r) for key,r in self.rules.items()}!=self.service._rules:
                raise RecoveryError('worker rules differ from authority')
            self.hard,self.numeric=ordered_map(metadata['hard']),ordered_map(metadata['numeric'])
            self.adapter=PLNAdapter() if self.native else PLNAdapter(PinnedFormulaRuntime())
        else:
            attempts=metadata['attempts']
            if type(attempts) is not list or len(set(attempts))!=len(attempts):
                raise RecoveryError('worker attempt inventory is invalid')
            self.attempts=set(attempts)
            for attempt in self.attempts:
                self.service.inspect_operation(attempt)
        if self.completed:
            last=max(self.completed.values(),key=lambda item:item['record']['step'])
            expected_prefix=last['command']['event_id']
            if self.profile=='deployment':
                expected_prefix='event:'+expected_prefix
            try:
                matches=fingerprint(self.projection())==last['record']['projection_digest']
            except (KeyError,ValueError) as error:
                raise RecoveryError('worker aliases cannot project recovered authority') from error
            if self._prefix!=expected_prefix or not matches:
                raise RecoveryError('worker metadata differs from last completed state')

    def apply(self,message):
        if self._broken:
            raise RecoveryError('worker requires reopening after storage or command failure')
        message=self._parse(message)
        key=message['event_id']
        old=self.completed.get(key)
        if old is not None:
            if canonical(old['command'])!=canonical(message):
                raise ValueError('completed event identity cannot be rebound')
            self.replayed=True
            return json.loads(canonical(old['record']))
        if self.pending is not None:
            raise RecoveryError('worker has an unresolved command')
        if len(self.completed)>=128:
            raise ValueError('worker event bound exceeded')
        # Check the adapter's non-mutating stream limits before marking pending.
        if self.profile=='admission':
            args=message['arguments']
            if message['kind']=='context' and args['context_id'] not in self.contexts and len(self.contexts)>=4:
                raise ValueError('trace exceeds four contexts')
        try:
            self.pending,self.replayed=message,False
            self._save()
            row=super().apply(message)
            self.completed[key]=dict(command=message,record=row)
            self.pending=None
            self._save()  # Completed checkpoint must precede stdout.
            return json.loads(canonical(row))
        except BaseException:
            self._broken=True
            raise

    def restart(self):
        # Base adapters call self.close(); avoid releasing wrapper ownership.
        self.service.close()
        if self.profile=='deployment':
            self.executor.close()
        self.service=AdmissionService(database=self.local if self.profile=='deployment' else self.path)
        if self.profile=='deployment':
            try:
                self.executor=SimulatedExecutor(self.remote)
            except BaseException:
                self.service.close()
                raise

    def close(self):
        if hasattr(self,'service'):
            super().close()
        if hasattr(self,'_worker_lock') and not self._worker_lock.closed:
            fcntl.flock(self._worker_lock.fileno(),fcntl.LOCK_UN)
            self._worker_lock.close()


class DurableAdmissionSession(_DurableTrace,AdmissionSession):
    profile='admission'


class DurableDeploymentSession(_DurableTrace,DeploymentSession):
    profile='deployment'
