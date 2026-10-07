"""Existing executor evidence link and passive current-time observation port."""
from time import perf_counter_ns
from experimental_online_pln.agenda import Probe,wire
from reachability.model import Evidence
from reachability.probability_model import ProbabilityReport
from reachability.pln_adapter import TruthValue


class Port:
    def __init__(self,session,world,numeric_responses,opportunities):
        self.session=session;self.world=world;self.numeric_responses=numeric_responses;self.opportunities=opportunities
        self.measurements=[];self.links=[];self.public_events=[];self.costs=dict(measurement_ns=0,effect_link_ns=0,publication_ns=0)
    def sync_effect(self):
        t=perf_counter_ns()
        try:
            try:dispatch=self.session.service.inspect_dispatch('attempt')
            except KeyError:return
            request=dispatch.dispatch.request
            # Evaluator-side actual executor query, never sent to the consumer's inbox.
            receipt=self.session.executor.query(request)
            added=self.world.accept(request,receipt)
            self.links.append(dict(time=self.world.time,request=wire(request),actual_executor_receipt=wire(receipt),local_dispatch_state=dispatch.state,new_link=added))
        finally:self.costs['effect_link_ns']+=perf_counter_ns()-t
    def publish(self,tick):
        t=perf_counter_ns();s=self.session
        if tick:s.emit('tick',time=tick)
        s.emit('account')
        probes=[]
        if tick in self.opportunities['product']:
            probes.append(Probe('product','executor','product','artifact-v2',('acknowledged',),opportunity=tick))
        if tick in self.opportunities['health']:
            probes.append(Probe('health','monitor','health','artifact-v2',('exact_product',),opportunity=tick))
        for p in probes:s.publish_probe(p)
        self.public_events.append(dict(time=tick,clock=tick,probes=wire(probes)))
        self.costs['publication_ns']+=perf_counter_ns()-t
    def acquire(self,probe):
        start=perf_counter_ns();before=self.world.state();sample=None
        try:
            s=self.session;now=s.service.snapshot('ctx').logical_time
            if now!=self.world.time:raise ValueError('sample time must equal public and physical clock')
            if probe.report_type=='numeric':
                name,literal,value,confidence,root=self.numeric_responses[probe.probe_id]
                response=dict(status='PASS',numeric=(Evidence(name,'ctx',literal,probe.source,now,(root,)),ProbabilityReport(name,TruthValue(value,confidence))))
            else:
                sample=self.world.measure(probe.report_type)
                if sample['status']!='PASS':response=dict(status='UNKNOWN',detail='observation channel unavailable')
                elif probe.report_type=='product':
                    actual=sample['value']
                    if actual is None:response=dict(status='UNKNOWN',detail='no installed artifact observed')
                    elif actual!=probe.target:
                        response=dict(status='PASS',events=(('observation',dict(attempt_id='attempt',product_id=actual,milestone='exact_product_observed')),))
                    else:
                        response=dict(status='PASS',events=(('fact',dict(name='product',valid_until=None)),('observation',dict(attempt_id='attempt',product_id=actual,milestone='completion_observed')),('observation',dict(attempt_id='attempt',product_id=actual,milestone='exact_product_observed'))))
                elif self.world.installed!=probe.target:response=dict(status='UNKNOWN',detail='measurement target is not installed')
                else:response=dict(status='PASS',events=(('sample',dict(healthy=sample['value'])),))
            self.measurements.append(dict(time=now,probe=wire(probe),sample=sample,response=wire(response),physical_before=before,physical_after=self.world.state()))
            if before!=self.world.state():raise AssertionError('passive port mutated physical state')
            return response
        finally:self.costs['measurement_ns']+=perf_counter_ns()-start
