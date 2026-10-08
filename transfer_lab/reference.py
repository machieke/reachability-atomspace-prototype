"""Independent finite input/ancestry/outcome checks, never a decision policy."""
from fractions import Fraction
from itertools import permutations,product
from hashlib import sha256
from reachability.trace_protocol import canonical
from experimental_online_pln.agenda import Snapshot,wire
from multihop_lab.reference import rule_shape,ancestry,require,graph
from reachability.probability_formula import PinnedFormulaRuntime,deduction_joint
from reachability.pln_adapter import TruthValue


def topology(f):
    names=sorted({x for r in f['rules'] for x in r['deduction'].values()}-{'tested','healthy'})
    # Isomorphism under internal proposition renaming, preserving endpoints and
    # the three ordered argument positions. These are NOT runtime identities.
    forms=[]
    for perm in permutations(range(len(names))):
        m=dict(zip(names,perm));m.update(tested='T',healthy='H')
        forms.append(canonical(sorted([tuple(str(m[r['deduction'][k]]) for k in ('p','q','r')) for r in f['rules']])))
    return min(forms)


def witness(f):
    w=f['joint_witness'];props=w['propositions'];cells=w['cells'];require(len(cells)==2**len(props),'full joint cell count');require(len({tuple(c['bits']) for c in cells})==len(cells),'unique cells')
    require(all(len(c['bits'])==len(props) and set(c['bits'])<={0,1} and Fraction(c['mass'])>=0 for c in cells),'valid nonnegative joint cells');require(sum(Fraction(c['mass']) for c in cells)==1,'normalized witness')
    def value(lit):
        ids=[props.index(x) for x in lit['statement']['arguments']];n=sum((Fraction(c['mass']) for c in cells if all(c['bits'][i] for i in ids)),Fraction())
        return n if len(ids)==1 else n/sum(Fraction(c['mass']) for c in cells if c['bits'][ids[0]])
    checked=[]
    for x in f['sources']:
        if x['joint_scope']:require(Fraction(x['strength'])==value(x['literal']),'declared input inconsistent with joint');checked.append(x['id'])
    return value,checked


def finite(f):
    """All static exact applications; no controller or preferred action sequence.

    Conditional on all declared primitive reports being received, including
    unavailable/event reports. It is not a same-information feasibility oracle.
    """
    outputs={canonical(rule_shape(r)[0]) for r in f['rules']};require(all(canonical(x['literal']) not in outputs for x in f['sources']),'seeded intermediate/target')
    states={};depth={};order=[];visited=set();checks=[]
    for x in f['sources']:
        states.setdefault(canonical(x['literal']),[]).append((x['id'],TruthValue(x['strength'],x['confidence']),frozenset([x['root']])));depth[x['id']]=0
    for _ in range(4):
        added=False
        for r in f['rules']:
            conclusion,premises=rule_shape(r)
            for items in product(*(states.get(canonical(l),[])[:] for l in premises)):
                key=(r['rule_id'],tuple(i[0] for i in items))
                if key in visited:continue
                visited.add(key);require(len(visited)<=128,'finite reference tuple cap')
                d=1+max(depth[x[0]] for x in items);require(d<=3,'input reasoning depth exceeds fragment')
                truths=tuple(x[1] for x in items);v=PinnedFormulaRuntime().evaluate('Truth_Deduction',truths);joint=deduction_joint(truths,v);require(joint is not None,'local output lacks feasible three-event witness')
                ident='finite:'+sha256(canonical(key).encode()).hexdigest();roots=frozenset().union(*(x[2] for x in items));depth[ident]=d;states.setdefault(canonical(conclusion),[]).append((ident,v,roots));order.append(r['rule_id']);checks.append(dict(rule=r['rule_id'],inputs=wire(truths),output=wire(v),depth=d,roots=sorted(roots),joint_cells=list(map(str,joint))));added=True
        if not added:break
    require(len(depth)<=32,'potential static current estimate cap')
    target=canonical(f['manifest']['criterion']['conclusion']);return dict(applications=checks,max_depth=max(depth.values()),potential_estimates=len(depth),target_estimates=[dict(id=i,truth=wire(v),roots=sorted(roots)) for i,v,roots in states.get(target,[])],feasibility='conditional finite derivability only; source availability, timing, authority and controller work are not proven feasible')


def validate_cohort(cohort,old):
    from collections import Counter
    require(len(cohort['parents'])==12 and Counter(p['family'] for p in cohort['parents'])==dict(A=4,B=4,C=4),'twelve parents / three families')
    seen={};old_shapes={topology(f) for f in old['parents']};out=[]
    for f in cohort['parents']:
        shape=topology(f);require(shape not in old_shapes,'old inspected dependency structure reused');require(shape not in seen,'renamed dependency sibling counted as parent');seen[shape]=f['id']
        require(len(f['rules'])<=16 and len(f['sources'])<=32,'rule/input caps');require(len({r['rule_id'] for r in f['rules']})==len(f['rules']),'unique rules');require(all(len(set(r['deduction'].values()))==3 for r in f['rules']),'deduction domain')
        require(len({x['id'] for x in f['sources']})==len(f['sources']),'unique primitive reports')
        require(sum(x['delivery']=='opportunity' for x in f['sources'])+2<=16,'probe cap')
        value,checked=witness(f);numerical=finite(f)
        for e in f['public_changes']:
            require(0<=e['tick']<=8 and 0<=e['after_slot']<8,'event horizon/slot bound')
            if e['kind']=='replace':require(e['target'] in {x['id'] for x in f['sources'] if x['delivery']=='initial'},'replacement targets actual initial evidence')
        out.append(dict(parent=f['id'],family=f['family'],status='PASS',ordered_topology_sha256=sha256(shape.encode()).hexdigest(),joint_source_checks=checked,numerical=numerical,task_feasibility=f['task_feasibility']))
    return dict(status='PASS',parents=out,no_controller_execution=True,old_shapes=len(old_shapes),limitations='Twelve constructed input structures, not twelve independent population samples; numerical evidence is conditional and local. No optimal or same-information task-feasibility policy is supplied.')


def final(f,initial,rows,result,changes):
    first=Snapshot.from_records(initial['public_records']);last=Snapshot.from_records(rows[-1]['public_records']);ih={b.belief_revision_id:wire(b) for q in first.numerical for b in q.historical};history={b.belief_revision_id:wire(b) for q in last.numerical for b in q.historical};dep,paths=ancestry(history)
    require(not any(ancestry(ih)[0].values()),'no seeded inference');require(dep==result['committed_depths'],'actual dependency depths');require(all(d<=3 for d in dep.values()),'actual depth cap')
    allowed={x['id']:x for x in f['sources']};allowed.update({e['report']['id']:e['report'] for e in f['public_changes']})
    expected={x['id'] for x in f['sources'] if x['delivery']=='initial'}
    for row in rows:
        for e in row.get('received',[]):
            if e['kind']=='numeric_report':expected.add(e['report']['evidence']['evidence_id'])
    expected.update(e['declaration']['report']['id'] for e in changes)
    require({r.evidence.evidence_id for r in last.reports}==expected,'only initially admitted or actually delivered reports')
    for r in last.reports:
        x=allowed[r.evidence.evidence_id];require(wire(r.evidence.content)==x['literal'] and r.evidence.source==x['source'] and r.evidence.lineage_roots==(x['root'],),'exact source identity/lineage');require((r.report.truth.strength,r.report.truth.confidence)==(x['strength'],x['confidence']),'source values altered')
    emitted={r['result']['commit']['belief']['belief_revision_id'] for r in rows if r['selected'] and r['selected']['kind'] in ('adopt','deduction','revision') and r['result']['status']=='PASS'};require(set(history)==set(ih)|emitted,'phantom derived or adopted record')
    require([c['declaration'] for c in changes]==f['public_changes'],'declared public changes delivered once')
    retired=[]
    for c in changes:
        if c['declaration']['kind']!='replace':continue
        target=c['declaration']['target'];before=[b for q in c['before']['numerical'] for b in q['current'] if target in b['proposal']['support']['evidence_ids']];after={b['belief_revision_id'] for q in c['after']['numerical'] for b in q['current']}
        require(not ({b['belief_revision_id'] for b in before}&after),'dependent current support survived revocation');retired.append(dict(target=target,retired=[b['belief_revision_id'] for b in before]))
    return dict(initial_derived_records=0,depths=dep,longest_path=max(paths.values(),key=len,default=[]),declared_source_reports=sorted(expected),retired=retired,task_feasibility='actual completion establishes this trajectory only' if result['stage']=='BUILT' else 'UNKNOWN; no same-information counterfactual controller supplied')
