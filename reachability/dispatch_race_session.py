"""Actual authority/executor calls with explicit queued requests and receipt delivery.

The in-memory transport inbox survives same-wrapper journal reopenings only.
No scheduler, oracle or future event script is available to this adapter.
"""
from dataclasses import asdict
from itertools import count
from threading import Lock, local

from .deployment_trace import DeploymentSession
from .dispatch import Dispatcher
from .dispatch_race_protocol import parse
from .service import AdmissionDenied
from .trace_protocol import DeploymentEvent, fingerprint


class _Transport:
    def __init__(self, session, event):
        self.session, self.event = session, event
        self.profile = session.executor.profile

    def submit(self, request):
        session, event = self.session, self.event
        session.requests[event['event_id']] = request
        fault = event['arguments']['fault']
        if fault in ('queued', 'before_effect'):
            if fault == 'before_effect':
                del session.requests[event['event_id']]
            raise OSError('transport has not returned a submission receipt')
        receipt = session.executor.submit(request)
        session.receipts[event['event_id']] = (request.intent.attempt_id, receipt)
        if fault == 'lost_reply':
            raise OSError('acknowledgement retained by transport')
        return receipt

    def query(self, request):
        return self.session.executor.query(request)

    def release(self, request):
        return self.session.executor.release(request)


def receipt_wire(receipt):
    return dict(state=receipt.state, sequence=receipt.sequence, effects=receipt.effect_count, fenced=receipt.fenced)


class DispatchRaceSession(DeploymentSession):
    def __init__(self, initial, directory):
        self._event_local, self._metadata = local(), Lock()
        self.requests, self.receipts = {}, {}
        super().__init__(initial, directory)

    def key(self):
        if hasattr(self._event_local, 'name'):
            return 'race:'+self._event_local.name+':'+str(next(self._event_local.keys))
        return super().key()

    def apply(self, message):
        """Serial public entry point; the evaluator controls paired execution."""
        return self.record(self.execute(message))

    def execute(self, message):
        event = parse(message)
        with self._metadata:
            if event['event_id'] in self.seen or len(self.seen) >= 64:
                raise ValueError('up to 64 uniquely identified events required')
            self.seen.add(event['event_id'])
        self._event_local.name, self._event_local.keys = event['event_id'], count()
        kind, args = event['kind'], event['arguments']
        status = 'PASS'
        try:
            now = self.service.snapshot(self.initial.context_id).logical_time
            if (kind == 'tick' and args['time'] < now or kind in ('fact', 'forecast') and
                    args['valid_until'] is not None and args['valid_until'] <= now):
                raise ValueError('invalid event time')
            if kind == 'dispatch':
                Dispatcher(self.service, _Transport(self,event)).dispatch(args['attempt_id'],'dispatch','1','worker')
            elif kind == 'arrive':
                request = self.requests[args['request_event']]
                receipt = self.executor.submit(request)
                self.receipts[event['event_id']] = (request.intent.attempt_id,receipt)
            elif kind == 'deliver':
                attempt, receipt = self.receipts[args['receipt_event']]
                self.service.record_dispatch_receipt(attempt,'submission',receipt,idempotency_key=self.key())
            else:
                base = dict(event,schema='deployment-event/v1')
                super()._execute(DeploymentEvent.parse(base))
        except AdmissionDenied as error:
            status = error.status.value
        except KeyError:
            status = 'FAIL'
        finally:
            del self._event_local.name
        return dict(event_id=event['event_id'],status=status)

    def projection(self):
        projection = super().projection()
        remote = {}
        for attempt in sorted(self.attempts):
            try:
                request = self.service.inspect_dispatch(attempt).dispatch.request
            except KeyError:
                continue
            remote[attempt] = receipt_wire(self.executor.query(request))
        projection['transport'] = dict(requests={key:r.intent.attempt_id for key,r in sorted(self.requests.items())},
            receipts={key:dict(attempt=a,**receipt_wire(r)) for key,(a,r) in sorted(self.receipts.items())})
        projection['executor'] = remote
        return projection

    def record(self, outcome):
        projection = self.projection()
        return dict(schema='dispatch-race-trace/v1',outcome=outcome,initial_digest=fingerprint(asdict(self.initial)),
                    projection=projection,projection_digest=fingerprint(projection),executor_effects=self.executor.total_effects)
