"""Thin input/event adapter; physical world and all runtime APIs are frozen."""
import copy,json
from pathlib import Path
from time import perf_counter_ns
from experimental_online_pln.agenda import Probe,wire
from reachability.model import Literal,Statement
from reachability.probability_model import ProbabilityRule
from reachability.pln_adapter import DeductionRule
from obligations_lab.cases import setup
from work_loop_lab.cases import admit
from world_lab.adapter import Port as OriginalPort
from multihop_lab.cases import configuration as old_configuration
ROOT=Path(__file__).resolve().parents[1]
def fixtures():return json.loads((ROOT/'reviews/frozen-transfer-v1/fixtures.json').read_text())
PARENTS=tuple(p['id'] for p in fixtures()['parents'])
def fixture(parent):return copy.deepcopy(next(p for p in fixtures()['parents'] if p['id']==parent))
def manifest(parent):return fixture(parent)['manifest']
def specification(parent):return fixture(parent)['world']
def configuration():
    cfg=old_configuration();return {k:cfg[k] for k in ('horizon_inclusive','tick_duration','max_operations_per_tick','public_opportunities','physical_goal','order','limits','seed')}
def literal(d):return Literal(Statement(d['statement']['predicate'],tuple(d['statement']['arguments'])),d['positive'])
def initialize(s,parent):
    f=fixture(parent);responses={}
    for r in f['rules']:s.register_rule(ProbabilityRule(r['rule_id'],r['revision'],DeductionRule(**r['deduction'])))
    for x in f['sources']:
        if x['delivery']=='initial':admit(s,x['id'],literal(x['literal']),x['strength'],x['confidence'],x['source'],x['root'])
        elif x['delivery']=='opportunity':
            responses[x['probe_id']]=(x['id'],literal(x['literal']),x['strength'],x['confidence'],x['root'])
            s.publish_probe(Probe(x['probe_id'],x['source'],'numeric',literal(x['literal']),cost=x['cost'],availability=x['availability']))
    return responses
class Port(OriginalPort):
    def __init__(self,*args,declaration,**kwargs):super().__init__(*args,**kwargs);self.unavailable={s['probe_id'] for s in declaration['sources'] if s['response']=='UNKNOWN'}
    def acquire(self,probe):
        if probe.report_type!='numeric' or probe.probe_id not in self.unavailable:return super().acquire(probe)
        t=perf_counter_ns();before=self.world.state();now=self.session.service.snapshot('ctx').logical_time
        if now!=self.world.time:raise ValueError('sample clock mismatch')
        response=dict(status='UNKNOWN',detail='declared source unavailable')
        self.measurements.append(dict(time=now,probe=wire(probe),sample=None,response=response,physical_before=before,physical_after=self.world.state()));self.costs['measurement_ns']+=perf_counter_ns()-t;return response

def apply_events(s,parent,tick,slot,changes):
    for e in fixture(parent)['public_changes']:
        if (e['tick'],e['after_slot'])!=(tick,slot):continue
        before=wire(s.read());ri=len(s.received)
        if e['kind']=='replace':s.emit('revoke',evidence_id=e['target'])
        x=e['report'];admit(s,x['id'],literal(x['literal']),x['strength'],x['confidence'],x['source'],x['root'],adopt=False)
        changes.append(dict(declaration=e,before=before,received=wire(s.received[ri:]),after=wire(s.read())))
