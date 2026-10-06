"""Coherent detached acquisition; public probe model plus frozen registry seams."""
from dataclasses import dataclass
from hashlib import sha256
import json
from time import perf_counter_ns
from experimental_obligations.capture import capture,state_digest
from experimental_online_pln.agenda import wire
from reachability.trace_protocol import canonical


def digest(value):return sha256(canonical(value).encode()).hexdigest()


@dataclass(frozen=True)
class WorkInput:
    payload_json: str
    def data(self):
        value=json.loads(self.payload_json);canonical(value)
        return value
    @property
    def identity(self):return sha256(self.payload_json.encode()).hexdigest()


def detached(value):return WorkInput(canonical(value))


def acquire(session):
    start=perf_counter_ns();s=session.service
    with s._lock:
        before=state_digest(s);cap,cap_costs=capture(s);d=cap.data();t=perf_counter_ns()
        if not d.get('complete') or len(session.probes)>16:
            return detached(dict(schema='obligation-work-input/v0',complete=False,reason='ACQUISITION_BOUND',capture=d)),dict(total_acquisition_ns=perf_counter_ns()-start,**cap_costs)
        public=session.read();registry=d['registry']
        inventory=dict(context_id=d['context']['context_id'],rules=registry['rules'],models=registry['models'],revoked_models=registry['revoked_models'],
                       probes=sorted(wire(public.probes),key=lambda p:p['probe_id']))
        observed=dict(goal=wire(public.goal),lifecycle=wire(public.lifecycle),operation=wire(public.operation),resource=wire(public.resource),intent=wire(public.intent),dispatch=wire(public.dispatch))
        assert wire(public.context)==d['context'] and wire(public.operation)==d['operation']
        assert state_digest(s)==before
        costs=dict(**cap_costs,inventory_and_state_acquisition_ns=perf_counter_ns()-t,
                   acquisition_counts=dict(beliefs=sum(len(v['historical']) for v in d['probability_export'][3]),evidence=len(registry['evidence']),registry_items=len(registry['rules'])+len(registry['models'])+len(inventory['probes'])),
                   nonmutation=dict(before=before,after=state_digest(s)))
        frame=dict(schema='obligation-work-input/v0',complete=True,capture=d,capture_identity=cap.identity,inventory=inventory,inventory_digest=digest(inventory),
                   observed=observed,observed_binding=digest((cap.identity,observed)))
        value=detached(frame)
    costs['total_acquisition_ns']=perf_counter_ns()-start
    return value,costs
