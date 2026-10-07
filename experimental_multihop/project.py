"""Bounded template discovery and exact current work; no speculative truth or IDs."""
from dataclasses import dataclass
from itertools import product
import json
from time import perf_counter_ns
from experimental_work_bridge.project import project as one_step,Limits,Incomplete
from experimental_work_bridge.capture import digest
from experimental_online_pln.agenda import wire
from reachability.pln_adapter import DeductionRule
from reachability.trace_protocol import canonical


@dataclass(frozen=True)
class MultiHopView:
    payload_json:str
    def data(self):return json.loads(self.payload_json)


def depths(history):
    """Longest exact committed deduction path, including retired ancestry."""
    out={};active=set()
    def visit(i):
        if i in out:return out[i]
        if i in active or i not in history:raise Incomplete('MISSING_OR_CYCLIC_COMMITTED_ANCESTRY')
        active.add(i);tr=history[i]['transition'];parents=tr['premise_revision_ids']
        value=0 if tr['kind']=='observation' else max((visit(p) for p in parents),default=0)+(tr['kind']=='deduction')
        active.remove(i);out[i]=value;return value
    for i in sorted(history):visit(i)
    return out


def project(frame,manifest,A,B,limits=Limits()):
    started=perf_counter_ns();base,base_costs=one_step(frame,manifest,A,B,limits);v=base.data();f=frame.data();t=perf_counter_ns()
    # Frozen validation/assessment is reused. Only its explicitly deferred deeper
    # route is expanded; malformed, incomplete or exhausted old captures stay closed.
    v.update(schema='bounded-multihop-work/v1',coverage='registered criterion/opposite dependencies through declared depth; not inference closure')
    v['bindings']['review_declaration']=digest(manifest.get('multihop_review'))
    v['templates']=[];v['committed_depths']={};v['traversal_visits']=0
    if not v['complete'] and v['reason']!='UNEXPANDED_DEEPER_ROUTE':
        return MultiHopView(canonical(v)),dict(base=base_costs,total_projection_ns=perf_counter_ns()-started)
    keep={'task','obligation','existing-execution','observed-goal'}
    nodes={n['id']:n for n in v['nodes'] if n['kind'] in keep}
    edges=[e for e in v['edges'] if e['source'] in nodes and e['target'] in nodes]
    v['global_blockers']=[b for b in v['global_blockers'] if b['category'] not in ('NO_REGISTERED_ROUTE','SCOPE_OR_BUDGET_INCOMPLETE')]
    v['complete']=True;v['reason']='COMPLETE';issues=[];templates={};visits=set();tuple_count=0
    def block(reason):
        if reason not in issues:issues.append(reason)
    scope=(f['capture']['authority'],manifest['work_task']['task_episode'],manifest['context'],manifest['product'])
    def node(kind,semantic,**data):
        i=kind+':'+digest((scope,semantic));value=dict(id=i,kind=kind,**data)
        if i not in nodes:
            if len(nodes)>=limits.nodes:raise Incomplete('NODE_BOUND')
            nodes[i]=value
        elif nodes[i]!=value:raise Incomplete('AMBIGUOUS_NODE')
        return i
    def edge(a,b,kind,slot=None):
        e=dict(source=a,target=b,type=kind,slot=slot)
        if e not in edges:
            if len(edges)>=limits.edges:raise Incomplete('EDGE_BOUND')
            edges.append(e)
    try:
        review=manifest['multihop_review'];limit=review['max_depth']
        if review['revision']!='registered-multihop-review/v1' or type(limit) is not int or not 1<=limit<=3 or review['roots']!='criterion-and-opposite' or review['cycles']!='incomplete':raise Incomplete('UNSUPPORTED_REVIEW_DECLARATION')
        d=f['capture'];inv=f['inventory'];history={b['belief_revision_id']:b for q in d['probability_export'][3] for b in q['historical']};current={b['belief_revision_id']:b for q in d['probability_export'][3] for b in q['current']}
        dep=depths(history);v['committed_depths']=dep
        producers=[]
        for rule in inv['rules']:
            r=DeductionRule(**rule['deduction']);producers.append(dict(kind='deduction',identity=[rule['rule_id'],rule['revision']],record=rule,conclusion=wire(r.conclusion),requirements=wire(r.premises),available=True))
        producers.sort(key=canonical);root=next(n['id'] for n in nodes.values() if n['kind']=='task');criterion=manifest['criterion']['conclusion'];opposite=dict(criterion,positive=not criterion['positive'])
        def literal_node(lit):return node('missing-premise',lit,literal=lit,requirement=lit,current_ids=sorted(i for i,b in current.items() if b['proposal']['support']['conclusion']==lit))
        def observation(probe):
            p=dict(kind='observation',identity=[probe['source']],record=probe,conclusion=probe['target'],requirements=[],available=probe['availability']!='unavailable')
            readiness='UNAVAILABLE' if not p['available'] else 'OBSERVATION_AVAILABILITY_UNKNOWN' if probe['availability']=='unknown' else 'OBSERVATION_OPPORTUNITY'
            for pre in probe['preconditions']:
                ok=(f['observed']['dispatch'] is not None and f['observed']['dispatch']['state']=='accepted') if pre=='acknowledged' else 'exact_product_observed' in f['observed']['operation']['current_milestones']
                if not ok:readiness='OBSERVATION_PRECONDITION_UNRESOLVED'
            return node('operation',(p['record'],[]),producer=p,ordered_premises=[],missing_slots=[],materialized_result_ids=[],readiness=readiness,authority=False)
        def template(p):
            nonlocal tuple_count
            ident=canonical(p['record'])
            if ident in templates:return templates[ident]
            key=node('producer-template',p['record'],producer=p,authority=False,executable=False);templates[ident]=key
            application_ids=[]
            alternatives=[sorted(i for i,b in current.items() if b['proposal']['support']['conclusion']==lit) for lit in p['requirements']]
            for premise_tuple in product(*alternatives):
                tuple_count+=1
                if tuple_count>limits.tuples:raise Incomplete('TUPLE_BOUND')
                real_depth=1+max(dep[i] for i in premise_tuple)
                if real_depth>limit:block('COMMITTED_DEPTH_BOUND')
                ids=[]
                for i,b in current.items():
                    tr=b['transition']
                    if tr['kind']=='deduction' and [tr['rule_id'],tr['rule_revision']]==p['identity'] and tr['premise_revision_ids']==list(premise_tuple):ids.append(i)
                op=node('operation',(p['record'],premise_tuple),producer=p,ordered_premises=list(premise_tuple),missing_slots=[],materialized_result_ids=sorted(ids),readiness='RESULT_ALREADY_RECORDED' if ids else 'INPUTS_PRESENT',real_depth=real_depth,authority=False)
                if sum(n['kind']=='operation' for n in nodes.values())>limits.operations:raise Incomplete('OPERATION_BOUND')
                application_ids.append(op);edge(key,op,'EXACT_APPLICATION')
                for slot,i in enumerate(premise_tuple):
                    child=node('premise',i,belief=current[i],state='CURRENT');edge(op,child,'AND_PREREQUISITE',slot)
            nodes[key]['applications']=sorted(application_ids)
            for slot,lit in enumerate(p['requirements']):edge(key,literal_node(lit),'AND_REQUIREMENT',slot)
            return key
        def walk(lit,level,path):
            token=canonical(lit);leaf=literal_node(lit)
            if token in path:block('DEPENDENCY_CYCLE');return leaf
            if (token,level) in visits:return leaf
            visits.add((token,level));v['traversal_visits']+=1
            if len(visits)>limits.comparisons:raise Incomplete('TRAVERSAL_BOUND')
            matching=[p for p in producers if p['conclusion']==lit]
            for model in inv['models']:
                if any(i in history and history[i]['proposal']['support']['conclusion']==lit for i in model['premise_revision_ids']):block('RELEVANT_REVISION_TEMPLATE_UNSUPPORTED')
            if not nodes[leaf]['current_ids']:
                for probe in inv['probes']:
                    if probe['report_type']=='numeric' and probe['target']==lit:edge(leaf,observation(probe),'OR_OBSERVATION_OPPORTUNITY')
            for p in matching:
                if level>limit:
                    cut=node('depth-cutoff',(p['record'],level),producer=p,requested_depth=level);edge(leaf,cut,'OR_UNEXPANDED_PRODUCER');block('DEPENDENCY_DEPTH_BOUND');continue
                key=template(p);edge(leaf,key,'OR_REGISTERED_PRODUCER')
                for required in p['requirements']:walk(required,level+1,path+(token,))
            return leaf
        for lit in (criterion,opposite):edge(root,walk(lit,1,()),'REVIEW_ROOT')
        # A symbolic missing template is retained even when no complete tuple exists.
        v['templates']=sorted(templates.values())
        for o in v['obligations']:
            classes=[c for c in manifest['classes'] if c['id'] in o['classes']]
            routes=[i for i,n in nodes.items() if n['kind']=='producer-template' and n['producer']['conclusion']==criterion and any(c['kind']=='deduction' and c['identity']==n['producer']['identity'] for c in classes)]
            routes += [i for i,n in nodes.items() if n['kind']=='operation' and n['producer']['kind']=='observation' and n['producer']['conclusion']==criterion and any(c['kind']=='observation' and c['identity']==n['producer']['identity'] for c in classes)]
            o['routes']=sorted(routes);nodes[o['id']]['routes']=o['routes']
            for i in routes:edge(o['id'],i,'OR_POSSIBLE_PRODUCER')
        if issues:raise Incomplete(issues[0])
    except (Incomplete,KeyError,TypeError,ValueError,IndexError) as error:
        v['complete']=False;v['reason']=str(error) if isinstance(error,Incomplete) else 'MALFORMED_MULTIHOP_INPUT:'+type(error).__name__
        v['global_blockers'].append(dict(category='SCOPE_OR_BUDGET_INCOMPLETE',detail=v['reason'],all_issues=issues))
    v.update(nodes=sorted(nodes.values(),key=lambda n:n['id']),edges=sorted(edges,key=canonical),partial_nodes_are_diagnostic=not v['complete'],view_identity=digest((frame.identity,manifest,limits.__dict__)),counts=dict(nodes=len(nodes),edges=len(edges),tuple_visits=tuple_count,traversal_visits=v['traversal_visits']))
    payload=canonical(v)
    return MultiHopView(payload),dict(base=base_costs,dependency_discovery_ns=perf_counter_ns()-t,output_bytes=len(payload.encode()),total_projection_ns=perf_counter_ns()-started)
