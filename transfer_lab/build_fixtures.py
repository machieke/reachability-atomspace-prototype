"""Deterministic input construction only. Never imports or runs a controller."""
import copy,json
from fractions import Fraction
from itertools import product
from pathlib import Path
from multihop_lab.cases import fixtures as old_fixtures
from multihop_lab.reference import literal,rule_shape
from world_lab.cases import specification
from reachability.trace_protocol import canonical

ROOT=Path(__file__).resolve().parents[1]
def make(ident,family,triples,question,missing=(),world='observable'):
    rules=[dict(rule_id='r%02d'%i,revision='1',deduction=dict(zip(('p','q','r'),t))) for i,t in enumerate(triples)]
    props=['tested']+sorted({x for t in triples for x in t}-{'tested','healthy'})+['healthy'];rho=Fraction(15,16)
    cells=[]
    for bits in product((0,1),repeat=len(props)):
        mass=Fraction(1,2)
        for x,y in zip(bits,bits[1:]):mass*=Fraction(31,32) if x==y else Fraction(1,32)
        cells.append(dict(bits=list(bits),mass=str(mass)))
    outputs={canonical(rule_shape(r)[0]) for r in rules};requirements={canonical(l):l for r in rules for l in rule_shape(r)[1]};leaves=[l for k,l in sorted(requirements.items()) if k not in outputs]
    sources=[]
    for i,lit in enumerate(leaves):
        args=lit['statement']['arguments'];strength=Fraction(1,2) if len(args)==1 else (1+rho**abs(props.index(args[0])-props.index(args[1])))/2
        miss=tuple(args) in missing;sources.append(dict(id='input-%02d'%i,literal=lit,strength=float(strength),confidence=31/32,source='forecast-model',root='root:input-%02d'%i,delivery='opportunity' if miss else 'initial',probe_id='observe-%02d'%i,response='PASS',availability='unknown',cost=1,joint_scope=True))
    m=copy.deepcopy(old_fixtures()['parents'][0]['manifest']);finals=[r for r in rules if rule_shape(r)[0]==m['criterion']['conclusion']]
    m.update(id=ident,classes=[dict(id=r['rule_id'],kind='deduction',identity=[r['rule_id'],'1'],roots=[]) for r in finals],obligations=[dict(id='required:'+r['rule_id'],mode='all',classes=[r['rule_id']]) for r in finals]);m['work_task'].update(task_id='frozen-transfer',task_episode='transfer-episode',revision=ident+'/v1')
    return dict(id=ident,family=family,question=question,rules=rules,sources=sources,manifest=m,public_changes=[],world=specification(world),joint_witness=dict(propositions=props,cells=cells),reference_claim='Initial in-scope input conditionals share this finite Markov-chain witness; per-invocation certification is local, not a global guarantee for later competing assessments.',task_feasibility='UNKNOWN: finite derivability is not an executable same-information policy witness',limits=copy.deepcopy(old_fixtures()['limits']))
def source(p,*args):return next(x for x in p['sources'] if x['literal']['statement']['arguments']==list(args))
def replacement(p,target,tick,slot,strength=None):
    old=source(p,*target);new=copy.deepcopy(old);new.update(id='replacement:'+old['id'],root='root:replacement:'+old['id'],delivery='event')
    if strength is not None:new.update(strength=strength,joint_scope=False)
    p['public_changes'].append(dict(tick=tick,after_slot=slot,kind='replace',target=old['id'],report=new))
def build():
    ps=[]
    def add(*a,**kw):p=make(*a,**kw);ps.append(p);return p
    add('A1-right-composition','A',[('b','c','healthy'),('tested','b','healthy')],'Acquire a missing suffix input, then consume its inferred right-hand conditional.',missing=[('c','healthy')])
    add('A2-two-sided','A',[('tested','a','b'),('b','c','healthy'),('tested','b','healthy')],'Combine two genuinely inferred AND branches; neither final conditional is an input.',missing=[('a','b'),('b','c')])
    add('A3-shared-suffix-review','A',[('b','c','healthy'),('a','b','healthy'),('tested','a','healthy'),('tested','b','healthy')],'Reuse a suffix intermediate across a short final route and a longer required route.',missing=[('c','healthy')])
    add('A4-intermediate-alternatives','A',[('tested','a','c'),('tested','b','c'),('tested','c','healthy')],'Review both producers of an intermediate and every exact final application.',missing=[('a','c')])
    p=add('B1-mixed-opportunities','B',[('a','b','healthy'),('tested','a','healthy'),('c','d','healthy'),('tested','c','healthy')],'One branch can be acquired; another registered source returns UNKNOWN. A good route does not finish complete review.',missing=[('b','healthy'),('d','healthy')]);source(p,'d','healthy')['response']='UNKNOWN'
    p=add('B2-source-role-copies','B',[('a','b','healthy'),('tested','a','healthy'),('tested','c','healthy')],'Eligible independent provenance and a copied source coexist as separate current estimates. The copied route cannot acquire the missing declared role.')
    a=source(p,'tested','a');a.update(source='source-a',root='root:channel-a');b=source(p,'tested','c');b.update(source='source-b',root='root:channel-b')
    copied=copy.deepcopy(b);copied.update(id='copied-channel-b',root='root:channel-a');p['sources'].append(copied)
    for c in p['manifest']['classes']:c['roots']=['root:channel-a' if c['id']=='r01' else 'root:channel-b']
    p['source_role_note']='Distinct/copy lineage is an explicit applicability requirement; no empirical or statistical independence is inferred from IDs.'
    p=add('B3-low-confidence-branch','B',[('tested','a','b'),('b','c','d'),('b','d','healthy'),('tested','b','healthy')],'A fully available three-hop path has an inadequately confident primitive input; keep all-current policy A.',missing=[('c','d')]);source(p,'c','d')['confidence']=.125
    p=add('B4-acquisition-headroom','B',[('tested','a','b'),('tested','b','c'),('c','d','healthy'),('tested','c','healthy')],'Four required primitive requests each cost four; investigate work/headroom exhaustion without enlarging the original caps.',missing=[('tested','a'),('a','b'),('b','c'),('d','healthy')])
    for x in p['sources']:
        if x['delivery']=='opportunity':x['cost']=4
    p['reference_budget_note']='All four missing conditionals are necessary, with total acquisition cost 16; the frozen pre-dispatch acquisition headroom leaves 12. This is a policy-budget limitation, not proof no other same-information policy exists.'
    p=add('C1-shared-replacement','C',[('b','c','healthy'),('b','d','healthy'),('a','b','healthy'),('tested','a','healthy'),('tested','b','healthy')],'Replace an exact source on one of two shared suffix producers at a fixed public boundary; retain unrelated ancestry.');replacement(p,('b','c'),0,2)
    p=add('C2-late-adverse-route','C',[('tested','a','b'),('b','c','healthy'),('tested','b','healthy'),('tested','d','healthy')],'Deliver an adverse primitive conditional through the public report path; require real inference and complete contrary assessment.')
    adverse=source(p,'d','healthy');adverse.update(delivery='event',strength=.0625,joint_scope=False)
    p['public_changes'].append(dict(tick=2,after_slot=0,kind='report',report=copy.deepcopy(adverse)))
    p=add('C3-replacement-unobservable','C',[('b','c','d'),('tested','b','d'),('tested','d','healthy')],'Change a relevant exact premise while product sensing is unavailable; distinguish physical completion from recognition.',world='unobservable');replacement(p,('c','d'),1,0)
    p=add('C4-regression-reassessment','C',[('tested','a','b'),('b','c','d'),('d','e','healthy'),('b','d','healthy'),('tested','b','healthy')],'Combine supported three-hop work with the existing physical regression/outage and a public changed estimate; preserve historical completion.',world='regression');replacement(p,('d','e'),6,0,.125)
    return dict(schema='frozen-transfer-cohort/v1',seed=0,baseline='d50baa1e9604c9e3df1ea4ead3e18a92fe24b7ec',construction='Deterministic declarations; no controller executions used for task selection.',parents=ps)
if __name__=='__main__':
    path=ROOT/'reviews/frozen-transfer-v1/fixtures.json'
    if path.exists():raise ValueError('fixture manifest already exists; retain cohort history')
    path.write_text(json.dumps(build(),indent=2)+'\n')
