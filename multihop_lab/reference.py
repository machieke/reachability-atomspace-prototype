"""Independent finite structural enumeration, fixture witness and ancestry checks."""
from itertools import product
from fractions import Fraction
from experimental_online_pln.agenda import wire
from reachability.trace_protocol import canonical


def require(ok,why):
    if not ok:raise AssertionError(why)


def literal(predicate,*args):return dict(positive=True,statement=dict(predicate=predicate,arguments=list(args)))
def rule_shape(rule):
    r=rule['deduction'];a,b,c=(r[k] for k in ('p','q','r'))
    return literal('pln:implication',a,c),[literal('pln:proposition',x) for x in (a,b,c)]+[literal('pln:implication',a,b),literal('pln:implication',b,c)]


def ancestry(history):
    # Iterative topological labeling; no production recursion or traversal import.
    result={};paths={};remaining=dict(history)
    while remaining:
        progress=False
        for i,b in list(remaining.items()):
            tr=b['transition'];parents=tr['premise_revision_ids']
            if tr['kind']=='observation':result[i]=0;paths[i]=[]
            elif all(p in result for p in parents):
                longest=max((paths[p] for p in parents),key=len,default=[])
                paths[i]=longest+([i] if tr['kind']=='deduction' else []);result[i]=len(paths[i])
            else:continue
            del remaining[i];progress=True
        require(progress,'missing or cyclic actual ancestry')
    return result,paths


def structure(snapshot,manifest):
    criterion=manifest['criterion']['conclusion'];opposite=dict(criterion,positive=not criterion['positive']);limit=manifest['multihop_review']['max_depth']
    registry=wire(snapshot.rules);queue=[(criterion,1,()),(opposite,1,())];templates={};literals={};issues=set();steps=0
    while queue:
        lit,depth,path=queue.pop(0);key=canonical(lit);literals[key]=lit;steps+=1
        require(steps<=2048,'reference traversal bound')
        if key in path:issues.add('DEPENDENCY_CYCLE');continue
        for rule in registry:
            conclusion,requirements=rule_shape(rule)
            if conclusion!=lit:continue
            if depth>limit:issues.add('DEPENDENCY_DEPTH_BOUND');continue
            templates[(rule['rule_id'],rule['revision'])]=(rule,requirements)
            queue.extend((p,depth+1,path+(key,)) for p in requirements)
    current={b.belief_revision_id:wire(b) for q in snapshot.numerical for b in q.current};history={b.belief_revision_id:wire(b) for q in snapshot.numerical for b in q.historical};dep,paths=ancestry(history)
    applications={}
    for key,(rule,requirements) in templates.items():
        choices=[[i for i,b in current.items() if b['proposal']['support']['conclusion']==lit] for lit in requirements]
        for ids in product(*choices):
            depth=1+max(dep[i] for i in ids)
            if depth>limit:issues.add('COMMITTED_DEPTH_BOUND')
            actual=sorted(i for i,b in current.items() if b['transition']['kind']=='deduction' and (b['transition']['rule_id'],b['transition']['rule_revision'])==key and b['transition']['premise_revision_ids']==list(ids))
            applications[(*key,ids)]=(depth,actual)
    return templates,literals,applications,issues,dep


def graph(snapshot,manifest,view):
    templates,literals,applications,issues,dep=structure(snapshot,manifest);nodes={n['id']:n for n in view['nodes']};edges=view['edges']
    if issues:require(not view['complete'],'partial depth/cycle review marked complete');return
    require(view['complete'],'supported structural graph incomplete: '+view['reason'])
    require(view['committed_depths']==dep,'actual ancestry depth differs')
    actual={tuple(n['producer']['identity']):n for n in nodes.values() if n['kind']=='producer-template'}
    require(set(actual)==set(templates),'omitted or invented relevant producer template')
    for key,(rule,requirements) in templates.items():
        n=actual[key];require(n['executable'] is False and n['producer']['record']==rule,'template is not a candidate')
        slots=sorted((e for e in edges if e['source']==n['id'] and e['type']=='AND_REQUIREMENT'),key=lambda e:e['slot'])
        require([e['slot'] for e in slots]==list(range(5)) and [nodes[e['target']]['literal'] for e in slots]==requirements,'complete ordered symbolic AND')
    refs={canonical(n['literal']):n for n in nodes.values() if n['kind']=='missing-premise'}
    require(set(refs)==set(literals),'missing dependency literal')
    for key,lit in literals.items():
        n=refs[key];expected={actual[k]['id'] for k,(rule,req) in templates.items() if rule_shape(rule)[0]==lit}
        actual_edges={e['target'] for e in edges if e['source']==n['id'] and e['type']=='OR_REGISTERED_PRODUCER'}
        require(actual_edges==expected,'complete producer OR alternatives')
    actual_apps={}
    for n in nodes.values():
        if n['kind']!='operation' or n['producer']['kind']!='deduction':continue
        key=(*n['producer']['identity'],tuple(n['ordered_premises']));actual_apps[key]=(n['real_depth'],n['materialized_result_ids'])
        require(len(n['ordered_premises'])==5 and None not in n['ordered_premises'],'phantom or partial executable tuple')
        inputs=sorted((e for e in edges if e['source']==n['id'] and e['type']=='AND_PREREQUISITE'),key=lambda e:e['slot'])
        require([e['slot'] for e in inputs]==list(range(5)),'missing concrete AND')
        require([nodes[e['target']]['belief']['belief_revision_id'] for e in inputs]==n['ordered_premises'],'wrong concrete premise order')
    require(actual_apps==applications,'exact current application bindings')


def fixture_witness(f):
    w=f['joint_witness'];props=w['propositions'];cells=w['cells'];require(len(cells)==2**len(props) and len({tuple(c['bits']) for c in cells})==len(cells),'full finite joint inventory')
    require(all(len(c['bits'])==len(props) and set(c['bits'])<={0,1} and Fraction(c['mass'])>=0 for c in cells),'nonnegative joint cells')
    require(sum(Fraction(c['mass']) for c in cells)==1,'joint normalized')
    def value(lit):
        args=lit['statement']['arguments'];indices=[props.index(x) for x in args];numerator=sum((Fraction(c['mass']) for c in cells if all(c['bits'][i] for i in indices)),Fraction())
        if len(indices)==1:return numerator
        denominator=sum((Fraction(c['mass']) for c in cells if c['bits'][indices[0]]),Fraction());return numerator/denominator
    checked=[]
    for source in f['sources']:
        lit=source['literal']
        if all(x in props for x in lit['statement']['arguments']):require(Fraction(source['strength'])==value(lit),'source inconsistent with declared fixture joint');checked.append(source['id'])
    return value,checked


def final(f,initial,rows,result,changes):
    from experimental_online_pln.agenda import Snapshot
    first=Snapshot.from_records(initial['public_records']);last=Snapshot.from_records(rows[-1]['public_records'])
    initial_history={b.belief_revision_id:wire(b) for q in first.numerical for b in q.historical};initial_depths,_=ancestry(initial_history)
    require(not any(initial_depths.values()),'intermediate/final was seeded')
    history={b.belief_revision_id:wire(b) for q in last.numerical for b in q.historical};dep,paths=ancestry(history)
    require(dep==result['committed_depths'] and max(dep.values(),default=0)==result['longest_dependency_path'],'longest actual chain, not call count')
    allowed={x['id']:x for x in f['sources']}
    for event in f['public_changes']:
        source=dict(allowed[event['target']],id=event['replacement_id'],root=event['replacement_root']);allowed[source['id']]=source
    expected_reports=set(allowed)-({x['id'] for x in f['sources'] if x['missing']} if f['numeric_channel']=='UNKNOWN' else set())
    require({r.evidence.evidence_id for r in last.reports}==expected_reports,'undeclared or hidden source report')
    for r in last.reports:
        e=r.evidence;source=allowed[e.evidence_id]
        require(wire(e.content)==source['literal'] and e.source==source['source'] and e.lineage_roots==(source['root'],),'exact declared source/lineage')
        require((r.report.truth.strength,r.report.truth.confidence)==(source['strength'],source['confidence']),'actual source estimate changed')
    joint,checked=fixture_witness(f)
    for b in history.values():
        tr=b['transition']
        if tr['kind']=='deduction' and tr['rule_id']!='r-adverse':require(Fraction(b['proposal']['support']['truth']['strength'])==joint(b['proposal']['support']['conclusion']),'derived conditional disagrees with declared fixture witness')
    emitted={x['result']['commit']['belief']['belief_revision_id'] for x in rows if x['selected'] and x['selected']['kind'] in ('adopt','deduction','revision') and x['result']['status']=='PASS'}
    require(set(history)==set(initial_history)|emitted,'phantom intermediate or hidden adoption')
    expected={'two-hop':(2,2,True),'three-hop':(3,3,True),'shared':(3,4,True),'unavailable':(0,0,False),'replacement':(2,3,True),'adverse':(2,3,False)}[f['id']]
    require((max(dep.values()),len(result['runtime_calls']),result['stage']=='BUILT')==expected,'declared depth/call/completion boundary')
    require(all(d<=3 for d in dep.values()),'unsupported actual depth')
    if f['id']=='shared':
        mids=[i for i,b in history.items() if b['transition']['rule_id']=='r-mid'];require(len(mids)==1,'shared intermediate duplicated')
        uses=[i for i,b in history.items() if mids[0] in b['transition']['premise_revision_ids']];require(len(uses)==2,'shared intermediate not actually reused')
    if f['id']=='replacement':
        require(len(changes)==1,'missing exact support event');event=changes[0];old={b['belief_revision_id'] for q in event['before']['numerical'] for b in q['current'] if b['transition']['rule_id']=='r-mid'};new={b['belief_revision_id'] for q in event['after']['numerical'] for b in q['current']};require(old and not old&new,'stale descendant stayed current')
        finals=[b for b in history.values() if b['transition']['rule_id']=='r-final'];require(not old&set(finals[0]['transition']['premise_revision_ids']),'old intermediate substituted into new chain')
    if f['id']=='adverse':require(result['effects']==0 and rows[-1]['view']['A']['numerical_status']==rows[-1]['view']['B']['numerical_status']=='FAIL','adverse estimate hidden')
    return dict(initial_derived_records=sum(d>0 for d in initial_depths.values()),depths=dep,longest_path=max(paths.values(),key=len,default=[]),joint_source_checks=checked)
