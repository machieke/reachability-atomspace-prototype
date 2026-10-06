"""Detached, lock-coherent export adapter; never certifies, registers or executes.

Private frozen read-only seams are used to include registry/certificate contents
and known execution checks absent from the public numerical export. No callback
or service reference survives in the immutable capture.
"""
from dataclasses import dataclass
from hashlib import sha256
import json,pickle
from time import perf_counter_ns
from experimental_online_pln.agenda import wire
from reachability.execution_model import ResourceClaim
from reachability.model import Check,Status
from reachability.trace_protocol import canonical


@dataclass(frozen=True)
class Captured:
    payload_json: str
    @property
    def identity(self):return sha256(self.payload_json.encode()).hexdigest()
    def data(self):return json.loads(self.payload_json)


def immutable(value):return Captured(canonical(value))


def state_digest(service):
    names=('_contexts','_evidence','_revoked','_certificates','_commands','_lifecycle','_execution','_dispatch','_goals','_completion','_probability','_decisions','_journal_sequence')
    return sha256(pickle.dumps(tuple(getattr(service,n) for n in names),protocol=5)).hexdigest()


def capture(service,attempt='attempt',execution=('deploy','1'),owner='worker'):
    started=perf_counter_ns()
    with service._lock:
        service._ensure_open();operation=service.inspect_operation(attempt)
        context=operation.operation.context_id
        p=service._probability
        counts=(sum(b.context_id==context for b in p.beliefs.values()),sum(e.context_id==context for e in service._evidence.values()),sum(ctx==context for ctx,_,_ in p.rule_versions),sum(ctx==context for ctx,_ in p.independence))
        if any(n>cap for n,cap in zip(counts,(512,512,32,16))):
            return immutable(dict(schema='complete-decision-shadow-capture/v0',complete=False,reason='SOURCE_BOUND',counts=counts)),dict(snapshot_acquisition_ns=perf_counter_ns()-started)
        exported=service.export_probability(context);registry=service._probability
        decision=service.inspect_probability_decision(attempt,*execution)
        contract=service._execution.contracts[execution]
        hard,prerequisites,action=service._execution_checks(attempt,contract,owner)
        now=service.resource_snapshot().logical_time
        claims=tuple(ResourceClaim(d.resource_id,d.quantity,d.unit,now,now+contract.lease_duration) for d in contract.demands)
        hard=tuple(c for c in hard if c.name!='probability_decision')+(Check('attempt_identity',Status.FAIL if attempt in service._execution.intents else Status.PASS,'existing intent is never replaced'),)+service._resource_checks(claims)
        views=tuple((service.query_probability(context,c.conclusion),service.query_probability(context,c.conclusion.negate())) for c in decision.contract.criteria)
        beliefs=tuple(b for v in exported[3] for b in v.historical)
        certids={i for b in beliefs for i in (b.pre_certificate_id,b.post_certificate_id)}
        certs=[registry.certificates[i] for i in sorted(certids)]
        data=dict(schema='complete-decision-shadow-capture/v0',complete=True,authority=exported[0],context=wire(exported[1]),policy=wire(exported[2]),
            probability_export=wire(exported),admission_export=wire(service.export_admission(context)),operation=wire(operation),execution_contract=wire(contract),resource=wire(service.resource_snapshot()),
            contract=wire(decision.contract),decision=wire(decision),live_status=decision.status.value,live_criterion_statuses=[c.status.value for c in decision.criteria],
            pairs=wire(views),hard_checks=wire(hard),hard_checks_complete=True,prerequisites=wire(prerequisites),action_requirements=wire(action),
            registry=dict(rules=wire(tuple(r for (ctx,_),r in sorted(registry.rules.items()) if ctx==context)),rule_versions=wire(tuple(r for (ctx,_,_),r in sorted(registry.rule_versions.items()) if ctx==context)),
                models=wire(tuple(m for (ctx,_),m in sorted(registry.independence.items()) if ctx==context)),revoked_models=wire(tuple(sorted(m for ctx,m in registry.revoked_models if ctx==context))),
                evidence=wire(tuple(e for _,e in sorted(service._evidence.items()) if e.context_id==context)),revoked=sorted(service._revoked),
                certificates=wire(certs),certificate_statuses={c.certificate_id:c.status.value for c in certs}),
            coverage='Complete existing authority context export and required registered checks; no claim about undiscovered facts outside this authority.')
        result=immutable(data)
    return result,dict(snapshot_acquisition_ns=perf_counter_ns()-started)
