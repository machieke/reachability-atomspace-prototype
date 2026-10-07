"""Private deterministic environment. Only public descriptors/received events escape."""
import json
from pathlib import Path
from dataclasses import replace
from experimental_online_pln.agenda import Probe, Limits, wire
from obligations_lab.cases import setup
from reachability.model import Evidence
from reachability.pln_adapter import DeductionRule, TruthValue
from reachability.probability_model import ProbabilityRule,ProbabilityIndependence,ProbabilityReport

ROOT=Path(__file__).resolve().parents[1]
PARENTS=('positive','shared','blocked','unavailable','freshness','adverse')


def configuration():return json.loads((ROOT/'reviews/closed-loop-obligations-v1/task.json').read_text())


def manifest(parent):
    cfg=configuration();kind=next(p['task'] for p in cfg['parents'] if p['id']==parent)
    return cfg['tasks'][kind]


def admit(s,name,literal,strength=.7,confidence=.8,source='forecast-model',root=None,adopt=True):
    evidence=Evidence(name,'ctx',literal,source,s.service.snapshot('ctx').logical_time,(root or 'root:'+name,))
    report=ProbabilityReport(name,TruthValue(strength,confidence));s.receive_report(evidence,report)
    if adopt:
        result=s.numeric('adopt',name,label='setup-adoption')
        if result['status']!='PASS':raise AssertionError(result)
        return result['commit'].belief
    return evidence,report


class World:
    def __init__(self,parent,continuation=None):
        self.parent,self.continuation=parent,continuation
        self.events=[];self.samples=0;self.product=False;self.healthy=None;self.changed=False;self.later=False
        self.responses={};self.product_requests=0
    @property
    def external_loss(self):return 0 if self.product and self.healthy is True else 10
    def record(self,kind,**fields):self.events.append(dict(kind=kind,**wire(fields)))
    def initialize(self,s):
        self.s=s;cfg=configuration();v=cfg['values']
        if self.parent in ('positive','freshness'):
            rules=[ProbabilityRule('r-estimate','1',DeductionRule('tested','staged','healthy')),
                   ProbabilityRule('r-competing','1',DeductionRule('tested','cached','healthy'))]
            values={}
            for r in rules:
                s.register_rule(r)
                for lit,value in zip(r.deduction.premises,v['deduction_strengths']):
                    if lit in values:assert values[lit]==value
                    values[lit]=value
            for i,(lit,value) in enumerate(values.items()):
                name='premise-'+str(i)
                if lit==rules[0].deduction.premises[-1]:
                    self.responses['missing-premise']=(name,lit,value,.8,'root:'+name)
                    s.publish_probe(Probe('missing-premise','forecast-model','numeric',lit))
                else:admit(s,name,lit,value,.8)
        else:
            a=admit(s,'a',s.forecast,.7,.2 if self.parent=='blocked' else .8,'source-a','root:a')
            if self.parent in ('shared','blocked','adverse'):
                b=admit(s,'b',s.forecast,.7,.8,'source-b','root:b')
            if self.parent in ('shared','blocked'):
                s.register_model(ProbabilityIndependence('model-ab','ctx',(a.belief_revision_id,b.belief_revision_id),'explicit synthetic independent measurement processes'))
            elif self.parent=='unavailable':
                s.publish_probe(Probe('source-b','source-b','numeric',s.forecast))
                self.responses['source-b']=('b',s.forecast,.7,.8,'root:b')
            elif self.parent=='adverse':
                r=ProbabilityRule('r-objection','1',DeductionRule('tested','weak','healthy'));s.register_rule(r)
                for i,(lit,value) in enumerate(zip(r.deduction.premises,v['adverse_strengths'])):admit(s,'objection-'+str(i),lit,value,v['adverse_confidence'])
        self.record('setup',public=wire(s.read()),receipts=wire(s.receipts))
    def acquire(self,probe):
        s=self.s
        if probe.report_type=='numeric':
            if self.parent=='unavailable' and self.continuation not in ('copied','unknown-source'):
                response=dict(status='UNKNOWN',detail='declared source unavailable')
            else:
                name,lit,value,confidence,root=self.responses[probe.probe_id]
                if self.continuation=='copied':root='root:a'
                response=dict(status='PASS',numeric=(Evidence(name,'ctx',lit,probe.source,s.service.snapshot('ctx').logical_time,(root,)),ProbabilityReport(name,TruthValue(value,confidence))))
        elif probe.report_type=='product':
            self.product_requests+=1
            if self.continuation=='wrong-product':
                response=dict(status='PASS',events=(('observation',dict(attempt_id='attempt',product_id='artifact-v1',milestone='exact_product_observed')),))
            else:
                self.product=True
                response=dict(status='PASS',events=(('fact',dict(name='product',valid_until=None)),('observation',dict(attempt_id='attempt',product_id='artifact-v2',milestone='completion_observed')),('observation',dict(attempt_id='attempt',product_id='artifact-v2',milestone='exact_product_observed'))))
        else:
            self.samples+=1;self.healthy=not self.later
            response=dict(status='PASS',events=(('sample',dict(healthy=self.healthy)),))
        self.record('actual-response',probe=probe,response=response)
        return response
    def before(self,candidate):
        if self.parent=='freshness' and not self.changed and candidate.kind=='deduction' and candidate.target=='r-estimate':
            self.changed=True;old=self.s.rules[candidate.target]
            self.s.register_rule(replace(old,revision='2'),expected_revision='1')
            self.record('exogenous-rule-change-before-execute',old=old,new=self.s.rules[candidate.target])
    def after(self,candidate,result):
        s=self.s
        if candidate.kind=='dispatch' and result['status']=='PASS':
            s.emit('tick',time=1);s.publish_probe(Probe('product','executor','product','artifact-v2',('acknowledged',)))
            self.record('received-clock-and-opportunity',time=1,probe=s.probes['product'])
            if self.continuation=='inflight-block':
                admit(s,'late-opposite',s.forecast.negate(),.7,.8,'source-b','root:b',adopt=False)
                self.record('exogenous-adverse-report',report=s.reports['late-opposite'])
        elif candidate.kind=='request' and candidate.target=='product' and result['status']=='PASS' and self.continuation!='missing-health':
            s.publish_probe(Probe('health','monitor','health','artifact-v2',('exact_product',),opportunity=1))
            self.record('received-opportunity',probe=s.probes['health'])
        elif candidate.kind=='request' and candidate.target=='health' and self.samples<3:
            s.emit('tick',time=self.samples+1);s.publish_probe(Probe('health','monitor','health','artifact-v2',('exact_product',),opportunity=self.samples+1))
            self.record('received-clock-and-opportunity',time=self.samples+1,probe=s.probes['health'])
        elif candidate.kind=='complete' and result['status']=='PASS' and self.continuation=='later-unhealthy':
            self.later=True;s.emit('tick',time=4);s.publish_probe(Probe('health','monitor','health','artifact-v2',('exact_product',),opportunity=4))
            self.record('exogenous-later-health-opportunity',time=4,probe=s.probes['health'])
