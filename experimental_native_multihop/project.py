"""Frozen graph semantics with actual native membership, no scan fallback.

The one-step graph is fully charged validation-only work. Its operations, routes
and producer annotations are discarded and reconstructed from native responses.
The original policy and full-frontier revalidation are outside this module.
"""
from itertools import product
import json
from time import perf_counter_ns
from experimental_work_bridge.project import project as one_step,Limits,Incomplete
from experimental_work_bridge.capture import digest
from experimental_online_pln.agenda import wire
from reachability.pln_adapter import DeductionRule
from reachability.trace_protocol import canonical


from experimental_multihop.project import MultiHopView
from .access import Access,DiscoveryFailure


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


def project(frame,manifest,A,B,access,limits=Limits()):
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
    v['global_blockers']=[b for b in v['global_blockers'] if b['category'] not in ('NO_REGISTERED_ROUTE','SCOPE_OR_BUDGET_INCOMPLETE') and 'producer' not in b]
    for o in v['obligations']:
        o['routes']=[];o['reasons']=[r for r in o['reasons'] if r!='NO_REGISTERED_ROUTE']
        nodes[o['id']]['routes']=[];nodes[o['id']]['reasons']=list(o['reasons'])
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
        access.validate(frame);access.open()
        history=access.history();current={}
        dep=depths(history);v['committed_depths']=dep
        models=access.records('models')
        for model in models:
            parents=[history.get(i) for i in model['premise_revision_ids']]
            literals=[p['proposal']['support']['conclusion'] for p in parents if p]
            if len(literals)!=2 or literals[0]!=literals[1]:
                v['global_blockers'].append(dict(category='APPLICABILITY_REQUIRES_REVIEW',detail='model conclusion unavailable or mixed; no inferred result',producer=model))
        def supports(lit):
            records=access.records('current',literal=lit)
            current.update((b['belief_revision_id'],b) for b in records)
            return sorted(b['belief_revision_id'] for b in records)
        def producers(lit):
            result=[]
            for rule in access.records('producers',literal=lit):
                r=DeductionRule(**rule['deduction']);result.append(dict(kind='deduction',identity=[rule['rule_id'],rule['revision']],record=rule,conclusion=wire(r.conclusion),requirements=wire(r.premises),available=True))
            return sorted(result,key=canonical)
        root=next(n['id'] for n in nodes.values() if n['kind']=='task');criterion=manifest['criterion']['conclusion'];opposite=dict(criterion,positive=not criterion['positive'])
        def literal_node(lit):return node('missing-premise',lit,literal=lit,requirement=lit,current_ids=supports(lit))
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
            alternatives=[supports(lit) for lit in p['requirements']]
            materialized=supports(p['conclusion'])
            for premise_tuple in product(*alternatives):
                tuple_count+=1
                if tuple_count>limits.tuples:raise Incomplete('TUPLE_BOUND')
                real_depth=1+max(dep[i] for i in premise_tuple)
                if real_depth>limit:block('COMMITTED_DEPTH_BOUND')
                ids=[]
                for i in materialized:
                    b=current[i];tr=b['transition']
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
            matching=producers(lit)
            # Report membership is queried even with current support: pending adverse
            # observations cannot be hidden by an existing favorable result.
            access.records('reports',literal=lit)
            if level==1:
                for p in matching:
                    if not any(c['kind']==p['kind'] and c['identity']==p['identity'] for c in manifest['classes']):
                        v['global_blockers'].append(dict(category='APPLICABILITY_REQUIRES_REVIEW',detail='registered relevant producer has no declared role; retained for investigation',producer=p))
            if level==1:
                for model in models:
                    parents=[history.get(i) for i in model['premise_revision_ids']]
                    literals=[p['proposal']['support']['conclusion'] for p in parents if p]
                    if len(literals)==2 and literals[0]==literals[1]==lit:
                        p=dict(kind='revision',identity=[model['model_id']],record=model,conclusion=lit,requirements=model['premise_revision_ids'],available=model['model_id'] not in access.snapshot.revoked_models)
                        if not any(c['kind']==p['kind'] and c['identity']==p['identity'] for c in manifest['classes']):
                            v['global_blockers'].append(dict(category='APPLICABILITY_REQUIRES_REVIEW',detail='registered relevant producer has no declared role; retained for investigation',producer=p))
                for probe in access.records('probes',report_type='numeric',target=lit):
                    checks=[]
                    for name in probe['preconditions']:
                        satisfied=(f['observed']['dispatch'] is not None and f['observed']['dispatch']['state']=='accepted') if name=='acknowledged' else 'exact_product_observed' in f['observed']['operation']['current_milestones']
                        checks.append(dict(name=name,status='PASS' if satisfied else 'UNKNOWN'))
                    p=dict(kind='observation',identity=[probe['source']],record=probe,conclusion=lit,requirements=[],available=probe['availability']!='unavailable',checks=checks)
                    if not any(c['kind']==p['kind'] and c['identity']==p['identity'] for c in manifest['classes']):
                        v['global_blockers'].append(dict(category='APPLICABILITY_REQUIRES_REVIEW',detail='registered relevant producer has no declared role; retained for investigation',producer=p))
            for model in models:
                if any(i in history and history[i]['proposal']['support']['conclusion']==lit for i in model['premise_revision_ids']):block('RELEVANT_REVISION_TEMPLATE_UNSUPPORTED')
            if not nodes[leaf]['current_ids']:
                for probe in access.records('probes',report_type='numeric',target=lit):
                    edge(leaf,observation(probe),'OR_OBSERVATION_OPPORTUNITY')
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
            # Recompute the legacy unresolved annotation from native-discovered
            # routes, never from the discarded one-step operation IDs.
            repair=False
            for i in routes:
                n=nodes[i]
                if n['kind']=='producer-template':
                    apps=n.get('applications',[])
                    repair |= not apps or any(not nodes[a]['materialized_result_ids'] for a in apps)
                else:repair |= n['producer']['available'] and not n['materialized_result_ids']
            if o['status']!='PASS' and not repair:o['reasons'].append('NO_REGISTERED_ROUTE')
            nodes[o['id']]['reasons']=list(o['reasons'])
            for i in routes:edge(o['id'],i,'OR_POSSIBLE_PRODUCER')
        if issues:raise Incomplete(issues[0])
    except (Incomplete,DiscoveryFailure,KeyError,TypeError,ValueError,IndexError) as error:
        v['complete']=False;v['reason']=str(error) if isinstance(error,(Incomplete,DiscoveryFailure)) else 'MALFORMED_MULTIHOP_INPUT:'+type(error).__name__
        v['global_blockers'].append(dict(category='SCOPE_OR_BUDGET_INCOMPLETE',detail=v['reason'],all_issues=issues))
    v['global_blockers']=sorted((b for b in v['global_blockers'] if b['category']!='SCOPE_OR_BUDGET_INCOMPLETE'),key=canonical)+[b for b in v['global_blockers'] if b['category']=='SCOPE_OR_BUDGET_INCOMPLETE']
    v.update(nodes=sorted(nodes.values(),key=lambda n:n['id']),edges=sorted(edges,key=canonical),partial_nodes_are_diagnostic=not v['complete'],view_identity=digest((frame.identity,manifest,limits.__dict__)),counts=dict(nodes=len(nodes),edges=len(edges),tuple_visits=tuple_count,traversal_visits=v['traversal_visits']))
    payload=canonical(v)
    return MultiHopView(payload),dict(base=base_costs,dependency_discovery_ns=perf_counter_ns()-t,output_bytes=len(payload.encode()),total_projection_ns=perf_counter_ns()-started)
