"""Actual public authority calls with actor-local certificates and no scheduler."""
from pathlib import Path
from threading import Lock

from . import interleaving_protocol as protocol
from .errors import AdmissionDenied, IdempotencyConflict
from .execution_model import ExecutionContract, ResourceDefinition, ResourceDemand
from .lifecycle_model import LifecycleEdge, LifecycleSchema, LifecycleState
from .model import Clause, Evidence, Literal, Statement, Status
from .requirements import Requirement
from .service import AdmissionService
from .trace_protocol import fingerprint


def lit(number):
    return Literal(Statement('interleave:atom', (str(abs(number)),)), number > 0)


def cnf(items):
    return tuple(Clause(tuple(lit(n) for n in clause)) for clause in items)


class InterleavingSession:
    def __init__(self, public, directory):
        self.public = protocol.initial(public)
        self.database = Path(directory)/'authority.sqlite'
        self.service = AdmissionService(database=self.database)
        self.prepared, self.permits, self.seen = {}, {}, set()
        self._metadata = Lock()
        s = self.service
        s.open_context('ctx', idempotency_key='setup:context')
        for number in (1, 2, 3):
            s.record_evidence(Evidence(str(number), 'ctx', lit(number), 'sensor', 0, ('source:'+str(number),)),
                              idempotency_key='setup:report:'+str(number))
        for number in self.public['facts']:
            proposal, pre, post, revision = self._prepare(number, 'setup:fact:'+str(number))
            result = s.commit(proposal, pre, post, revision, idempotency_key='setup:commit:'+str(number))
            if result.status is not Status.PASS:
                raise ValueError('invalid initial fact')
        ready, product = Requirement('FACT', lit(1)), Requirement('FACT', lit(3))
        schema = LifecycleSchema('work', '1', 'artifact', 'product', 'DRAFT',
            (LifecycleState('DRAFT'), LifecycleState('BUILT', product)),
            (LifecycleEdge('build', 'DRAFT', 'BUILT', ready, product, 'product', ('executor',)),), ('BUILT',), 'public-interleaving-profile')
        s.register_lifecycle_schema(schema, idempotency_key='setup:schema')
        s.register_resource(ResourceDefinition('slot', self.public['capacity'], 'units'), idempotency_key='setup:resource')
        s.register_execution_contract(ExecutionContract('build', '1', 'work', '1', 'build', 'executor', ('a', 'b'),
            (ResourceDemand('slot', 1, 'units'),), 4), idempotency_key='setup:contract')
        for actor in ('a', 'b'):
            s.open_lifecycle_episode(actor, 'ctx', 'work', '1', idempotency_key='setup:episode:'+actor)
            operation = s.propose_operation('build:'+actor, actor, actor, 'build', idempotency_key='setup:operation:'+actor)
            s.select_operation(actor, operation.revision, idempotency_key='setup:select:'+actor)
        self.knowledge_base = s.snapshot('ctx').knowledge_revision
        self.resource_base = s.resource_snapshot().revision

    def _prepare(self, number, key):
        s = self.service
        transition = s.propose_evidence('ctx', str(number), idempotency_key=key+':transition')
        revision = s.snapshot('ctx').knowledge_revision
        pre = s.precertify(transition, revision, idempotency_key=key+':pre')
        proposal = s.infer(transition, pre)
        post = s.postcertify(proposal, pre, idempotency_key=key+':post')
        return proposal, pre, post, revision

    def apply(self, message):
        e = protocol.event(message)
        with self._metadata:
            if len(self.seen) >= 64 or e['event_id'] in self.seen:
                raise ValueError('at most 64 unique events required')
            self.seen.add(e['event_id'])
        key, actor, kind, args = 'event:'+e['event_id'], e['actor'], e['kind'], e['arguments']
        s, status = self.service, Status.PASS
        try:
            if kind == 'read':
                s.snapshot('ctx')
            elif kind == 'prepare':
                packet = self._prepare(args['literal'], key)
                status = packet[2].status
                self.prepared[e['event_id']] = (actor, args['literal'], packet)
            elif kind == 'commit':
                owner, _, packet = self.prepared[args['prepared']]
                status = Status.FAIL if owner != actor else s.commit(*packet, idempotency_key=key).status
            elif kind == 'policy':
                s.replace_policy('ctx', e['event_id'], cnf(args['clauses']), s.snapshot('ctx').knowledge_revision, idempotency_key=key)
            elif kind == 'certify':
                op = s.inspect_operation(actor).operation
                permit = s.certify_execution(actor, 'build', '1', actor, op.revision, s.snapshot('ctx').knowledge_revision,
                                             s.resource_snapshot().revision, idempotency_key=key)
                self.permits[e['event_id']] = permit
                status = permit.status
            elif kind == 'reserve':
                permit = self.permits[args['permit']]
                if permit.owner_id != actor:
                    status = Status.FAIL
                else:
                    s.reserve_and_record_intent(permit, idempotency_key=key)
        except AdmissionDenied as error:
            status = error.status
        except KeyError:
            status = Status.UNKNOWN
        except IdempotencyConflict:
            status = Status.FAIL
        # Projection is captured by the evaluator only at a quiescent boundary.
        return dict(schema='interleaving-outcome/v1', event_id=e['event_id'], status=status.value)

    def projection(self):
        s, snap = self.service, self.service.snapshot('ctx')
        resource = s.inspect_resource('slot')
        usable = sorted({int(b.conclusion.statement.arguments[0])*(1 if b.conclusion.positive else -1) for b in snap.usable})
        return dict(usable=usable, clauses=[[int(x.statement.arguments[0])*(1 if x.positive else -1) for x in c.literals] for c in snap.constraints],
            policy=snap.policy_revision, knowledge_epoch=snap.knowledge_revision-self.knowledge_base,
            resource_epoch=resource.resource_revision-self.resource_base,
            prepared={key: dict(actor=a, literal=n, status=p[2].status.value) for key, (a, n, p) in sorted(self.prepared.items())},
            permits={key: dict(actor=p.owner_id, status=p.status.value) for key, p in sorted(self.permits.items())},
            intents=sorted({r.attempt_id for r in resource.reservations}), used=resource.used_now,
            readiness={a: s.inspect_operation(a).readiness.value for a in ('a', 'b')})

    def record(self, outcome):
        projection = self.projection()
        return dict(schema='interleaving-trace/v1', outcome=outcome, projection=projection, projection_digest=fingerprint(projection))

    def restart(self):
        self.service.close()
        self.service = AdmissionService(database=self.database)

    def close(self):
        self.service.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
