"""Actual durable admission/reservation/dispatch port for serial portfolios."""
from itertools import count
from pathlib import Path

from .codec import encode
from .deployment_trace import _FaultTransport
from .dispatch import Dispatcher
from .dispatch_model import DispatchPolicy
from .execution_model import ExecutionContract, ResourceDefinition, ResourceDemand
from .lifecycle_model import LifecycleEdge, LifecycleSchema, LifecycleState, milestone_literal
from .model import Evidence, Literal, Statement, Status
from .requirements import Requirement
from .resource_planning import ResourcePublic, SNAPSHOT_SCHEMA, bounded, fields, step
from .service import AdmissionDenied, AdmissionService
from .simulated_executor import SimulatedExecutor
from .trace_protocol import canonical, fingerprint, identifier

EVENT_FIELDS = dict(ready='job_id valid_until', revoke='evidence_id', tick='time',
    lease='hold_id resource_id quantity duration remote', reserve='mode_id revision attempt_id',
    dispatch='fault', reconcile='', release='', outcome='product_id', restart='')


def event(event_id, kind, **arguments):
    identifier(event_id)
    if kind not in EVENT_FIELDS:
        raise ValueError('unsupported resource event')
    fields(arguments, EVENT_FIELDS[kind])
    for name, value in arguments.items():
        if name in ('time', 'quantity', 'duration'):
            bounded(value, 1000, 1 if name in ('quantity', 'duration') else 0)
        elif name == 'valid_until':
            if value is not None:
                bounded(value, 1000)
        elif name == 'remote':
            if type(value) is not bool:
                raise ValueError('typed remote flag required')
        else:
            identifier(value)
    if kind == 'dispatch' and arguments['fault'] not in ('none', 'lost_reply', 'before_effect'):
        raise ValueError('unsupported transport fault')
    return dict(schema='resource-planning-event/v1', event_id=event_id, kind=kind, arguments=arguments)


class ResourceSession:
    def __init__(self, public, directory, *, emit=None):
        self.public = ResourcePublic.parse(public.wire())
        self.p = self.public.wire()
        self.modes = {m['mode_id']: m for m in self.p['modes']}
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        self.local, self.remote = directory/'admission.db', directory/'executor.db'
        if self.local.exists() or self.remote.exists():
            raise ValueError('new portfolio sessions require an empty directory')
        self.service = AdmissionService(database=self.local, max_variables=20)
        self.executor = SimulatedExecutor(self.remote)
        self.emit, self.spent, self.active = emit, 0, None
        self.facts, self.attempts, self.seen = {}, {}, set()
        self._keys, self._ids = count(), count()
        self.certificates = []
        self.service.open_context('portfolio', idempotency_key=self.key())
        for r in self.p['resources']:
            self.service.register_resource(ResourceDefinition(**r), idempotency_key=self.key())
        for job in self.p['jobs']:
            self._schema('job:'+job, 'product:'+job, Requirement('FACT', self.credential(job)))
        for mode in self.p['modes']:
            self._contract('mode:'+mode['mode_id'], mode['revision'], 'job:'+mode['job_id'], mode['demands'], mode['duration'])

    def key(self):
        return 'portfolio-command-'+str(next(self._keys))

    def close(self):
        self.service.close()
        self.executor.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def restart(self):
        self.close()
        self.service = AdmissionService(database=self.local)
        self.executor = SimulatedExecutor(self.remote)

    @staticmethod
    def credential(job):
        return Literal(Statement('PortfolioReady', (job,)))

    @staticmethod
    def product(name):
        return Literal(Statement('Available', (name,)))

    def _schema(self, name, product, requirement):
        outcome = Requirement('FACT', self.product(product))
        schema = LifecycleSchema(name, '1', 'portfolio-product', product, 'DRAFT',
            (LifecycleState('DRAFT'), LifecycleState('BUILT', outcome)),
            (LifecycleEdge('execute', 'DRAFT', 'BUILT', requirement, outcome, product, ('executor',)),), ('BUILT',), 'serial-resource-profile/v1')
        self.service.register_lifecycle_schema(schema, idempotency_key=self.key())
        self.service.open_lifecycle_episode(name, 'portfolio', name, '1', idempotency_key=self.key())

    def _contract(self, name, revision, schema, demands, duration):
        self.service.register_execution_contract(ExecutionContract(name, revision, schema, '1', 'execute', 'executor', ('worker',),
            tuple(ResourceDemand(**d) for d in demands), duration), idempotency_key=self.key())
        self.service.register_dispatch_policy(DispatchPolicy(name, revision, name, revision, self.executor.profile), idempotency_key=self.key())

    def _adopt(self, eid, literal, source, until=None):
        s = self.service
        now = s.snapshot('portfolio').logical_time
        s.record_evidence(Evidence(eid, 'portfolio', literal, source, now, (eid,), until), idempotency_key=self.key())
        transition = s.propose_evidence('portfolio', eid, idempotency_key=self.key())
        rev = s.snapshot('portfolio').knowledge_revision
        pre = s.precertify(transition, rev, idempotency_key=self.key())
        self.certificates.append(pre)
        proposal = s.infer(transition, pre)
        post = s.postcertify(proposal, pre, idempotency_key=self.key())
        self.certificates.append(post)
        result = s.commit(proposal, pre, post, rev, idempotency_key=self.key())
        if result.status is not Status.PASS:
            raise AdmissionDenied(result.status, result.detail)
        self.facts[eid] = literal, until, result.belief.belief_revision_id
        return result.belief

    def _reserve(self, attempt, schema, contract, revision):
        s = self.service
        op = s.propose_operation(schema, attempt, schema, 'execute', idempotency_key=self.key())
        s.select_operation(attempt, op.revision, idempotency_key=self.key())
        self.attempts[attempt] = dict(schema=schema, contract=contract, revision=revision)
        permit = s.certify_execution(attempt, contract, revision, 'worker', s.inspect_operation(attempt).operation.revision,
            s.snapshot('portfolio').knowledge_revision, s.resource_snapshot().revision, idempotency_key=self.key())
        self.certificates.append(permit)
        s.reserve_and_record_intent(permit, idempotency_key=self.key())

    def _execute(self, message):
        s, kind, a, eid = self.service, message['kind'], message['arguments'], message['event_id']
        if kind == 'ready':
            if a['job_id'] not in self.p['jobs']:
                raise ValueError('unknown job')
            self._adopt(eid, self.credential(a['job_id']), 'sensor', a['valid_until'])
        elif kind == 'revoke':
            s.revoke_evidence(a['evidence_id'], idempotency_key=self.key())
        elif kind == 'tick':
            s.advance_clock('portfolio', a['time'], idempotency_key=self.key())
            s.advance_resource_clock(a['time'], idempotency_key=self.key())
        elif kind == 'lease':
            bounded(a['quantity'], 4, 1)
            bounded(a['duration'], 1000-s.resource_snapshot().logical_time, 1)
            name = 'hold:'+a['hold_id']
            if name in self.attempts or len([x for x in self.attempts if x.startswith('hold:')]) >= 8:
                raise ValueError('duplicate or excessive background lease')
            r = next(r for r in self.p['resources'] if r['resource_id'] == a['resource_id'])
            self._schema(name, 'hold-product:'+a['hold_id'], Requirement('ALWAYS'))
            self._contract(name, '1', name, [dict(resource_id=r['resource_id'], quantity=a['quantity'], unit=r['unit'])], a['duration'])
            self._reserve(name, name, name, '1')
            if a['remote']:
                Dispatcher(s, self.executor).dispatch(name, name, '1', 'worker')
        elif kind == 'reserve':
            mode = self.modes[a['mode_id']]
            if a['revision'] != mode['revision']:
                raise AdmissionDenied(Status.STALE, 'exact immutable contract revision required')
            if self.active is not None or self.spent+mode['cost'] > self.p['work_budget']:
                raise AdmissionDenied(Status.FAIL, 'serial episode or declared cost limit')
            if not a['attempt_id'].startswith('run:') or a['attempt_id'] in self.attempts:
                raise ValueError('fresh namespaced attempt required')
            self.spent += mode['cost']
            self._reserve(a['attempt_id'], 'job:'+mode['job_id'], 'mode:'+mode['mode_id'], mode['revision'])
            self.active = dict(attempt=a['attempt_id'], job_id=mode['job_id'], mode_id=mode['mode_id'])
        elif kind in ('dispatch', 'reconcile', 'release'):
            active = self.active
            mode = self.modes[active['mode_id']]
            dispatcher = Dispatcher(s, _FaultTransport(self.executor, a.get('fault', 'none')))
            if kind == 'dispatch':
                dispatcher.dispatch(active['attempt'], 'mode:'+mode['mode_id'], mode['revision'], 'worker')
            else:
                view = getattr(dispatcher, kind)(active['attempt'], 'worker')
                if kind == 'release' and view.resources_released:
                    self.active = None
        elif kind == 'outcome':
            attempt, job = self.active['attempt'], self.active['job_id']
            self._adopt(eid+':product', self.product(a['product_id']), 'executor')
            for milestone in ('completion_observed', 'exact_product_observed'):
                belief = self._adopt(eid+':'+milestone, milestone_literal(attempt, a['product_id'], milestone), 'executor')
                s.record_operation_observation(eid+':'+milestone, attempt, milestone, belief.belief_revision_id, idempotency_key=self.key())
            episode = s.inspect_lifecycle('job:'+job).episode
            permit = s.certify_lifecycle_transition(episode.episode_id, 'execute', episode.revision,
                s.snapshot('portfolio').knowledge_revision, attempt_id=attempt, idempotency_key=self.key())
            self.certificates.append(permit)
            s.advance_lifecycle(permit, episode.revision, idempotency_key=self.key())
        elif kind == 'restart':
            self.restart()

    def projection(self):
        s = self.service
        usable = {b.belief_revision_id for view in s.export_admission('portfolio')[2] for b in view.current}
        facts = {eid: dict(predicate=lit.statement.predicate, arguments=list(lit.statement.arguments),
                           valid_until=until, current=bid in usable) for eid, (lit, until, bid) in sorted(self.facts.items())}
        jobs = {}
        for job in self.p['jobs']:
            proofs = [f for f in facts.values() if f['predicate'] == 'PortfolioReady' and f['arguments'] == [job] and f['current']]
            lifetimes = [f['valid_until'] for f in proofs]
            view = s.inspect_lifecycle('job:'+job)
            ready = bool(proofs) and view.episode.stage == 'DRAFT'
            jobs[job] = dict(completed=view.episode.stage == 'BUILT' and view.validity is Status.PASS,
                ready=ready, ready_until=None if not ready or None in lifetimes else max(lifetimes))
        holds = []
        for r in self.p['resources']:
            view = s.inspect_resource(r['resource_id'])
            for reservation in view.reservations:
                c = reservation.claim
                holds.append(dict(attempt=reservation.attempt_id, resource_id=c.resource_id, quantity=c.quantity, unit=c.unit,
                    start=c.starts_at, end=c.ends_at, uncertain=reservation.attempt_id in view.reconciliation_attempts))
        attempts = {}
        for attempt in sorted(self.attempts):
            op = s.inspect_operation(attempt)
            intent, dispatch = None, None
            try:
                v = s.inspect_execution_intent(attempt)
                intent = dict(state=v.state, start=v.intent.created_at, end=v.intent.lease_until)
            except KeyError:
                pass
            try:
                dispatch = s.inspect_dispatch(attempt).state
            except KeyError:
                pass
            attempts[attempt] = dict(intent=intent, dispatch=dispatch, milestones=list(op.current_milestones))
        active = None if self.active is None else dict(**self.active, dispatch=attempts[self.active['attempt']]['dispatch'],
                                                        completed=jobs[self.active['job_id']]['completed'])
        return dict(time=s.snapshot('portfolio').logical_time, jobs=jobs, holds=sorted(holds, key=lambda h: (h['attempt'], h['resource_id'])),
                    active=active, spent=self.spent, facts=facts, attempts=attempts)

    def read(self):
        p = self.projection()
        return dict(schema=SNAPSHOT_SCHEMA, public_digest=fingerprint(self.public.wire()), time=p['time'], jobs=p['jobs'], holds=p['holds'],
                    active=p['active'], remaining_work=self.p['work_budget']-self.spent,
                    knowledge_revision=self.service.snapshot('portfolio').knowledge_revision, resource_revision=self.service.resource_snapshot().revision)

    def observe(self, message):
        fields(message, 'schema event_id kind arguments')
        if message['schema'] != 'resource-planning-event/v1' or message != event(message['event_id'], message['kind'], **message['arguments']):
            raise ValueError('invalid resource event')
        if message['event_id'] in self.seen or len(self.seen) >= 128:
            raise ValueError('unique event ids and at most 128 events required')
        self.seen.add(message['event_id'])
        self.certificates = []
        before = self.service._journal_sequence
        status = 'PASS'
        try:
            self._execute(message)
        except AdmissionDenied as error:
            status = error.status.value
        except (KeyError, ValueError, TypeError, StopIteration):
            status = 'FAIL'
        projection = self.projection()
        record = dict(schema='resource-planning-trace/v1', event_id=message['event_id'], event_digest=fingerprint(message), status=status,
            projection=projection, projection_digest=fingerprint(projection), executor_effects=self.executor.total_effects,
            diagnostics=dict(journal_commands=self.service._journal_sequence-before, certificates=encode(tuple(self.certificates))))
        if self.emit:
            self.emit(message, record)
        return record

    def send(self, kind, **args):
        while True:
            eid = 'resource-event-'+str(next(self._ids))
            if eid not in self.seen:
                return self.observe(event(eid, kind, **args))

    def execute(self, action):
        fields(action, 'schema kind snapshot_digest plan until')
        if action['schema'] != 'resource-action/v1':
            raise ValueError('unsupported resource action')
        snapshot = self.read()
        if action['snapshot_digest'] != fingerprint(snapshot):
            return dict(status='STALE', public_events=0, charged=0)
        kind, before = action['kind'], self.spent
        if kind != 'reserve' and action['plan'] is not None or kind != 'wait' and action['until'] is not None:
            raise ValueError('unbound extra action fields')
        if kind == 'wait':
            bounded(action['until'], self.p['deadline'], snapshot['time']+1)
            record = self.send('tick', time=action['until'])
        elif kind == 'reserve':
            plan = action['plan']
            fields(plan, 'schema snapshot_digest steps cost finishes_at')
            if plan['schema'] != 'resource-plan/v1' or plan['snapshot_digest'] != action['snapshot_digest'] or type(plan['steps']) is not list or not plan['steps']:
                raise ValueError('a complete snapshot-bound resource plan is required')
            first = plan['steps'][0]
            mode = self.modes[first['mode_id']]
            if canonical(first) != canonical(step(mode, snapshot['time'])):
                raise ValueError('first step must match the whole immutable contract and current time')
            if first['end'] > self.p['deadline']:
                return dict(status='FAIL', public_events=0, charged=0)
            record = self.send('reserve', mode_id=mode['mode_id'], revision=mode['revision'], attempt_id='run:'+str(len(self.attempts)))
        elif kind in ('dispatch', 'reconcile', 'release'):
            record = self.send(kind, **({'fault': 'none'} if kind == 'dispatch' else {}))
        else:
            raise ValueError('observation requests must be answered by the environment')
        return dict(status=record['status'], public_events=1, charged=self.spent-before)
