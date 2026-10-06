"""Independent expected reasons and structural conformance; no projector import."""
from hashlib import sha256
import json
from itertools import product


def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)

def check(condition,why):
    if not condition:raise AssertionError(why)


def validate(frame,manifest,A,B,view):
    f=frame.data();d=f['capture'];a=A.data();b=B.data();v=view.data()
    check(v['A']==a and v['B']==b,'frozen assessments unchanged');check(v['observed']==f['observed'],'actual observed state preserved')
    if not v['complete']:
        check(any(r['category']=='SCOPE_OR_BUDGET_INCOMPLETE' for r in v['global_blockers']),'explicit incomplete boundary');return
    check(v['bindings']['capture_identity']==f['capture_identity'],'complete capture binding');check(v['bindings']['inventory_digest']==f['inventory_digest'],'inventory binding')
    nodes={n['id']:n for n in v['nodes']};check(len(nodes)==len(v['nodes']),'unique semantic nodes')
    edges=v['edges'];check(len({canonical(e) for e in edges})==len(edges),'unique typed edges')
    check(all(e['source'] in nodes and e['target'] in nodes for e in edges),'no dangling dependency')
    current={x['belief_revision_id']:x for query in d['probability_export'][3] for x in query['current']}
    by_id={r['id']:r for r in b['records']};actual={o['obligation_id']:o for o in v['obligations']};check(set(actual)=={g['id'] for g in manifest['obligations']},'declared obligations only')
    for g in b['obligations']:
        o=actual[g['id']];check(o['status']==g['status'] and o['witnesses']==sorted(g['witnesses']),'all frozen witnesses/status')
        check(o['current_applicable']==sorted(g['inspected']) and o['stale_records']==sorted(g['retired']),'all applicable current/stale records')
        expected=[i for i in g['inspected'] if not by_id[i]['adequate']];check(o['insufficient_records']==sorted(expected),'insufficient records kept')
        reasons=[] if g['status']=='PASS' else ['INADEQUATE_SUPPORT' if g['inspected'] else 'STALE_SUPPORT' if g['retired'] else 'MISSING_ASSESSMENT']
        check(o['reasons'][:len(reasons)]==reasons and (g['status']!='PASS' or not o['reasons']),'semantic missing-work reason')
        task=manifest['work_task'];semantic=[task['task_episode'],task['revision'],manifest['context'],manifest['product'],manifest['criterion']['criterion_id'],g['id']]
        expected_id='obligation:'+sha256(canonical(semantic).encode()).hexdigest();check(o['id']==expected_id,'independent obligation identity')
        links=[e['target'] for e in edges if e['source']==o['id'] and e['type']=='OR_POSSIBLE_PRODUCER'];check(sorted(links)==o['routes'],'OR producer routes')
        for target in links:check(nodes[target]['producer']['conclusion']==manifest['criterion']['conclusion'],'no opposite support shortcut')
    objections={r['id'] for r in b['records'] if r['current'] and (r['orientation']=='opposite' or r['disposition']=='strength_objection')}
    check({x['record']['id'] for x in v['global_blockers'] if x['category']=='OBJECTION_REQUIRES_REVIEW'}==objections,'complete objections')
    unclassified={r['id'] for r in b['records'] if r['current'] and not r['eligible_classes']}
    check({x['record']['id'] for x in v['global_blockers'] if x['category']=='APPLICABILITY_REQUIRES_REVIEW' and 'record' in x}==unclassified,'complete applicability problems')
    check(any(x['category']=='LIVE_POLICY_BLOCK' for x in v['global_blockers'])==(a['numerical_status']!='PASS'),'live block never erased')
    for n in nodes.values():
        if n['kind']!='operation':continue
        p=n['producer'];requirements=p['requirements'];dependencies=sorted((e for e in edges if e['source']==n['id'] and e['type']=='AND_PREREQUISITE'),key=lambda e:e['slot'])
        check([e['slot'] for e in dependencies]==list(range(len(requirements))),'complete AND slots')
        check(len(n['ordered_premises'])==len(requirements),'ordered exact premise tuple')
        if p['kind']=='deduction':
            rule=p['record']['deduction'];names=[rule['p'],rule['q'],rule['r']]
            literals=[{'positive':True,'statement':{'predicate':'pln:proposition','arguments':[name]}} for name in names]
            literals += [{'positive':True,'statement':{'predicate':'pln:implication','arguments':[names[i],names[i+1]]}} for i in (0,1)]
            check(requirements==literals,'independent deduction premise requirements')
        for j,edge in enumerate(dependencies):
            child=nodes[edge['target']];ref=n['ordered_premises'][j]
            if ref in current:
                check(child['kind']=='premise' and child['belief']==current[ref],'exact current premise')
                if p['kind']=='deduction':check(current[ref]['proposal']['support']['conclusion']==requirements[j],'coherent literal slot')
            else:check(child['kind']=='missing-premise','missing AND prerequisite visible')
        if n['materialized_result_ids']:check(n['readiness']=='RESULT_ALREADY_RECORDED' and not n['reexecution_as_repair'],'no repeat-as-adequacy strategy')
    # Derive every eligible rule tuple independently from the full ledger, no numeric evaluation.
    forecast=manifest['criterion']['conclusion'];opposite=json.loads(canonical(forecast));opposite['positive']=not opposite['positive']
    for r in f['inventory']['rules']:
        q=r['deduction'];out={'positive':True,'statement':{'predicate':'pln:implication','arguments':[q['p'],q['r']]}}
        if out not in (forecast,opposite):continue
        lits=[{'positive':True,'statement':{'predicate':'pln:proposition','arguments':[q[k]]}} for k in ('p','q','r')]+[{'positive':True,'statement':{'predicate':'pln:implication','arguments':[q[x],q[y]]}} for x,y in (('p','q'),('q','r'))]
        choices=[sorted(i for i,x in current.items() if x['proposal']['support']['conclusion']==lit) or [None] for lit in lits]
        expected={tuple(t) for t in product(*choices)}
        observed={tuple(n['ordered_premises']) for n in nodes.values() if n['kind']=='operation' and n['producer']['kind']=='deduction' and n['producer']['record']==r}
        check(observed==expected,'all coherent alternative bundles')


def expected_prefix(parent,label,variant,v):
    """Hand-declared event-prefix expectations; never input to the projector."""
    if label.startswith('diagnostic-'):
        check(not v['complete'],'closed input diagnostic');return
    g={o['obligation_id']:o for o in v['obligations']}
    expected={}
    if parent=='method-gap':
        expected={'forecast':'PASS','method-assessment':'PASS' if label=='produced' else 'UNKNOWN'}
        if variant=='shared_method':expected['method-review']=expected['method-assessment']
        check(v['A']['numerical_status']=='UNKNOWN','weak parent still blocks A')
    elif parent=='optional-weak':
        expected={'forecast':'UNKNOWN' if label=='after' and variant=='forecast_all' else 'PASS','method-assessment':'PASS'}
        if variant=='mandatory_weak':expected['weak-method']='UNKNOWN';check(g['weak-method']['reasons'][0]==('MISSING_ASSESSMENT' if label=='before' else 'INADEQUATE_SUPPORT'),'presence versus adequacy')
        check(v['A']['numerical_status']==('PASS' if label=='before' else 'UNKNOWN'),'new materialized weak assessment')
    elif parent=='copied-source':expected={'forecast':'PASS','source-b':'UNKNOWN' if label=='copied' else 'PASS'}
    elif parent=='freshness':expected={'forecast':'STALE' if label=='revoked' else 'PASS','source-b':'PASS'}
    elif parent=='objection':
        expected={'forecast':'PASS','method-assessment':'PASS'}
        check(sum(x['category']=='OBJECTION_REQUIRES_REVIEW' for x in v['global_blockers'])=={'before':0,'derived':1,'opposite':2}[label],'concurrent global objections')
        check(v['A']['numerical_status']==v['B']['numerical_status']==('PASS' if label=='before' else 'FAIL'),'adverse computation frozen result')
    elif parent=='registry':
        expected={'forecast':'PASS','method-assessment':'UNKNOWN','weak-method':'UNKNOWN'}
        if label in ('registered','partial','complete'):
            ops=[n for n in v['nodes'] if n['kind']=='operation' and n['producer']['kind']=='deduction'];check(len(ops)==1,'single declared rule bundle')
            check(len(ops[0]['missing_slots'])=={'registered':5,'partial':1,'complete':0}[label],'exact missing AND slots')
        if label in ('revised','unavailable'):check(not g['weak-method']['routes'],'new rule revision cannot satisfy old role')
    else:raise AssertionError('unknown parent')
    check({k:x['status'] for k,x in g.items()}==expected,'predeclared prefix obligation table')
    check(v['observed']['goal']['projection']['outstanding_loss']==10,'no manufactured relief')
