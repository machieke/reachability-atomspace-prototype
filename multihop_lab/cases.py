"""Declared evaluator fixtures; only actual reports cross the public boundary."""
import json,copy
from pathlib import Path
from time import perf_counter_ns
from experimental_online_pln.agenda import Probe,wire
from reachability.model import Literal,Statement
from reachability.pln_adapter import DeductionRule
from reachability.probability_model import ProbabilityRule
from work_loop_lab.cases import admit
from obligations_lab.cases import setup
from world_lab.cases import configuration as world_configuration,specification as world_specification
from world_lab.adapter import Port as WorldPort

ROOT=Path(__file__).resolve().parents[1]
PARENTS=('two-hop','three-hop','shared','unavailable','replacement','adverse')
def fixtures():return json.loads((ROOT/'reviews/bounded-multihop-v1/fixtures.json').read_text())
def fixture(parent):return copy.deepcopy(next(p for p in fixtures()['parents'] if p['id']==parent))
def manifest(parent):return fixture(parent)['manifest']
def configuration():
    world=world_configuration();cfg={k:world[k] for k in ('horizon_inclusive','tick_duration','max_operations_per_tick','public_opportunities','physical_goal','order')}
    cfg.update(schema='bounded-multihop-world-run/v1',limits=fixtures()['limits'],modes=fixtures()['modes'],seed=fixtures()['seed'],fixture_protocol=fixtures(),environment=world_specification('observable'));return cfg

def specification(parent):return world_specification('observable')
def literal(data):return Literal(Statement(data['statement']['predicate'],tuple(data['statement']['arguments'])),data['positive'])

def initialize(session,parent):
    f=fixture(parent);responses={}
    for r in f['rules']:session.register_rule(ProbabilityRule(r['rule_id'],r['revision'],DeductionRule(**r['deduction'])))
    for source in f['sources']:
        lit=literal(source['literal'])
        if source['missing']:
            responses['upstream-leaf']=(source['id'],lit,source['strength'],source['confidence'],source['root'])
            session.publish_probe(Probe('upstream-leaf',source['source'],'numeric',lit))
        else:admit(session,source['id'],lit,source['strength'],source['confidence'],source['source'],source['root'])
    return responses


class Port(WorldPort):
    def __init__(self,*args,numeric_channel,**kwargs):super().__init__(*args,**kwargs);self.numeric_channel=numeric_channel
    def acquire(self,probe):
        if probe.report_type!='numeric' or self.numeric_channel!='UNKNOWN':return super().acquire(probe)
        start=perf_counter_ns();before=self.world.state();now=self.session.read().context.logical_time
        if now!=self.world.time:raise ValueError('sample time mismatch')
        response=dict(status='UNKNOWN',detail='declared upstream source unavailable')
        self.measurements.append(dict(time=now,probe=wire(probe),sample=None,response=response,physical_before=before,physical_after=self.world.state()))
        self.costs['measurement_ns']+=perf_counter_ns()-start;return response


def apply_events(s,parent,tick,slot,changes):
    for e in fixture(parent)['public_changes']:
        if e['tick']!=tick or e['after_slot']!=slot:continue
        before=wire(s.read());ri=len(s.received);source=next(x for x in fixture(parent)['sources'] if x['id']==e['target'])
        s.emit('revoke',evidence_id=e['target']);admit(s,e['replacement_id'],literal(source['literal']),source['strength'],source['confidence'],source['source'],e['replacement_root'],adopt=False)
        changes.append(dict(declaration=e,before=before,received=wire(s.received[ri:]),after=wire(s.read())))
