"""Bounded, unranked work explanation. No authority, runtime or execution access."""
from dataclasses import dataclass
from itertools import product
import json
from time import perf_counter_ns
from experimental_obligations.capture import immutable
from experimental_obligations.evaluate import evaluate,ShadowAssessment,Bounds as AssessmentBounds
from experimental_online_pln.agenda import wire
from reachability.pln_adapter import DeductionRule
from reachability.trace_protocol import canonical
from .capture import WorkInput,digest


@dataclass(frozen=True)
class Limits:
    bytes: int=4194304
    inventory: int=64
    estimates: int=128
    tuples: int=128
    operations: int=64
    nodes: int=256
    edges: int=512
    comparisons: int=2048
    def __post_init__(self):
        caps=(4194304,64,128,128,64,256,512,2048)
        if any(type(v) is not int or not 0<=v<=c for v,c in zip(self.__dict__.values(),caps)):raise ValueError('unsupported bridge limits')


@dataclass(frozen=True)
class ObligationWorkView:
    payload_json: str
    def data(self):return json.loads(self.payload_json)


class Incomplete(Exception):pass


def object_data(payload):
    value=json.loads(payload);canonical(value)
    if not isinstance(value,dict):raise Incomplete('MALFORMED_ASSESSMENT')
    return value


def project(frame,manifest,A,B,limits=Limits()):
    if type(frame) is not WorkInput or type(A) is not ShadowAssessment or type(B) is not ShadowAssessment:raise ValueError('detached inputs and frozen assessment objects required')
    start=perf_counter_ns();costs={};nodes={};edges={};blockers=[];obligations=[];counts=dict(inventory_items=0,premise_records=0,tuple_visits=0,operations=0,role_comparisons=0,history_scan_visits=0)
    f={};m={};a={};b={};task={};bindings={};complete=True;reason='COMPLETE';discovery_start=None
    def key(kind,value):return kind+':'+digest(value)
    def node(kind,semantic,**fields):
        i=key(kind,semantic)
        if i not in nodes:
            if len(nodes)>=limits.nodes:raise Incomplete('NODE_BOUND')
            nodes[i]=dict(id=i,kind=kind,**fields)
        elif nodes[i]!=dict(id=i,kind=kind,**fields):raise Incomplete('AMBIGUOUS_NODE')
        return i
    def edge(src,dst,kind,slot=None):
        value=dict(source=src,target=dst,type=kind,slot=slot);i=digest(value)
        if i not in edges:
            if len(edges)>=limits.edges:raise Incomplete('EDGE_BOUND')
            edges[i]=value
    def block(category,detail,**fields):
        value=dict(category=category,detail=detail,**fields)
        if value not in blockers:blockers.append(value)
    try:
        if len(frame.payload_json.encode())+len(A.payload_json.encode())+len(B.payload_json.encode())+len(canonical(manifest).encode())>limits.bytes:raise Incomplete('INPUT_BYTE_BOUND')
        f=frame.data();m=json.loads(canonical(manifest));a=object_data(A.payload_json);b=object_data(B.payload_json)
        if not isinstance(f,dict):f={};raise Incomplete('MALFORMED_INPUT_ENVELOPE')
        if f.get('schema')!='obligation-work-input/v0' or not f.get('complete'):raise Incomplete(f.get('reason','INCOMPLETE_INPUT'))
        d=f['capture'];cap=immutable(d);inv=f['inventory'];observed=f['observed'];task=m['work_task']
        if cap.identity!=f['capture_identity'] or digest(inv)!=f['inventory_digest'] or digest((cap.identity,observed))!=f['observed_binding']:raise Incomplete('INPUT_BINDING_MISMATCH')
        for name in ('rules','models','revoked_models'):
            if inv[name]!=d['registry'][name]:raise Incomplete('REGISTRY_CAPTURE_MISMATCH')
        if inv['context_id']!=d['context']['context_id'] or observed['operation']!=d['operation'] or observed['resource']!=d['resource']:raise Incomplete('STATE_BINDING_MISMATCH')
        ctx=d['context'];op=d['operation']['operation'];goal=observed['goal'];life=observed['lifecycle']
        exact=(ctx['context_id']==m['context'] and op['product_id']==m['product'] and op['attempt_id']==task['attempt_id'] and op['operation_id']==task['operation_id']
               and op['episode_id']==task['lifecycle_episode'] and goal['episode']['goal_id']==task['goal_id'] and goal['episode']['context_id']==m['context']
               and goal['projection']['knowledge_revision']==ctx['knowledge_revision'] and goal['projection']['logical_time']==ctx['logical_time']
               and [d['execution_contract']['contract_id'],d['execution_contract']['revision']]==task['execution_contract']
               and d['contract']['criteria']==[m['criterion']] and [d['contract']['contract_id'],d['contract']['revision']]==m['contract']
               and m['time_window'][0]<=ctx['logical_time']<m['time_window'][1] and bool(task['task_episode']) and bool(task['revision']))
        if not exact:raise Incomplete('TASK_SCOPE_MISMATCH')
        t=perf_counter_ns()
        for kind,provided in (('A',a),('B',b)):
            recomputed,cost=evaluate(cap,m,kind,AssessmentBounds(**provided['bounds']))
            if recomputed.data()!=provided:raise Incomplete('ASSESSMENT_BINDING_MISMATCH:'+kind)
            if provided['reason']!='COMPLETE':raise Incomplete('ASSESSMENT_INCOMPLETE:'+provided['reason'])
        costs['frozen_assessment_revalidation_ns']=perf_counter_ns()-t
        if a['numerical_status']!=d['live_criterion_statuses'][0]:raise Incomplete('FROZEN_LIVE_PARITY_MISMATCH')
        bindings=dict(input_identity=frame.identity,capture_identity=cap.identity,inventory_digest=f['inventory_digest'],observed_binding=f['observed_binding'],manifest_hash=digest(m),
                      assessment_A=digest(a),assessment_B=digest(b))
        scope=(task['task_episode'],task['revision'],m['context'],m['product'],m['criterion']['criterion_id'])
        work_scope=(d['authority'],task['task_episode'],m['context'],m['product'])
        root=node('task',scope,task=task,context=m['context'],product=m['product'],criterion=m['criterion'])
        lifecycle=node('existing-execution',scope,authority='existing-public-APIs-only',observed=observed['operation'])
        outcome=node('observed-goal',scope,observed=goal)
        edge(root,lifecycle,'EXISTING_AUTHORITY_REQUIREMENT');edge(root,outcome,'OBSERVED_OUTCOME_REQUIREMENT')
        records=b['records'];by_record={r['id']:r for r in records};group_nodes={}
        for group in sorted(b['obligations'],key=lambda g:g['id']):
            current=group['inspected'];insufficient=[i for i in current if not by_record[i]['adequate']]
            item=dict(obligation_id=group['id'],mode=group['mode'],classes=sorted(group['classes']),status=group['status'],witnesses=sorted(group['witnesses']),
                      current_applicable=sorted(current),insufficient_records=sorted(insufficient),stale_records=sorted(group['retired']),reasons=[])
            if group['status']!='PASS':item['reasons'].append('INADEQUATE_SUPPORT' if current else 'STALE_SUPPORT' if group['retired'] else 'MISSING_ASSESSMENT')
            i=node('obligation',(*scope,group['id']),**item);item=dict(id=i,**item);obligations.append(item);group_nodes[group['id']]=i;edge(root,i,'AND_OBLIGATION')
        for r in records:
            if not r['current']:continue
            if r['orientation']=='opposite' or r['disposition']=='strength_objection':block('OBJECTION_REQUIRES_REVIEW',r['disposition'],record=r)
            if not r['eligible_classes']:block('APPLICABILITY_REQUIRES_REVIEW','current unclassified record remains visible',record=r)
        for kind,assessment in (('A',a),('B',b)):
            for check in assessment['checks']:
                if check['status']!='PASS' and not check['name'].startswith(('obligation:','unclassified:','same_literal_ledger','opposite_literal','strength_objections','universal_confidence_floor')):
                    block('HARD_OR_SCOPE_CHECK','frozen required check',interpretation=kind,check=check)
        if a['numerical_status']!='PASS':block('LIVE_POLICY_BLOCK','shadow interpretation cannot repair or replace live all-current policy',status=a['numerical_status'])
        if a['numerical_status']!=b['numerical_status']:block('POLICY_DISAGREEMENT','both frozen judgments retained; no automatic policy choice',A=a['numerical_status'],B=b['numerical_status'])
        # Full current ledger for premises; never restrict to positive witness lists.
        history={v['belief_revision_id']:v for view in d['probability_export'][3] for v in view['historical']}
        current={v['belief_revision_id']:v for view in d['probability_export'][3] for v in view['current']}
        counts['premise_records']=len(current);counts['inventory_items']=sum(len(inv[k]) for k in ('rules','models','probes'))
        if counts['premise_records']>limits.estimates:raise Incomplete('ESTIMATE_BOUND')
        if counts['inventory_items']>limits.inventory or len(inv['probes'])>16:raise Incomplete('INVENTORY_BOUND')
        discovery_start=perf_counter_ns();conclusion=m['criterion']['conclusion'];opposite=json.loads(canonical(conclusion));opposite['positive']=not opposite['positive']
        producers=[]
        for rule in inv['rules']:
            deduction=DeductionRule(**rule['deduction'])
            producers.append(dict(kind='deduction',identity=[rule['rule_id'],rule['revision']],record=rule,conclusion=wire(deduction.conclusion),requirements=wire(deduction.premises),available=True))
        for model in inv['models']:
            parents=[history.get(i) for i in model['premise_revision_ids']]
            literals=[p['proposal']['support']['conclusion'] for p in parents if p]
            if len(literals)!=2 or literals[0]!=literals[1]:
                block('APPLICABILITY_REQUIRES_REVIEW','model conclusion unavailable or mixed; no inferred result',producer=model);continue
            producers.append(dict(kind='revision',identity=[model['model_id']],record=model,conclusion=literals[0],requirements=model['premise_revision_ids'],available=model['model_id'] not in inv['revoked_models']))
        probes=[]
        for probe in inv['probes']:
            if probe['availability'] not in ('available','unavailable','unknown') or probe['report_type'] not in ('numeric','product','health') or not set(probe['preconditions'])<={'acknowledged','exact_product'}:raise Incomplete('UNSUPPORTED_PROBE')
            if probe['report_type']=='numeric':
                checks=[]
                for name in probe['preconditions']:
                    satisfied=(observed['dispatch'] is not None and observed['dispatch']['state']=='accepted') if name=='acknowledged' else 'exact_product_observed' in observed['operation']['current_milestones']
                    checks.append(dict(name=name,status='PASS' if satisfied else 'UNKNOWN'))
                probes.append(dict(kind='observation',identity=[probe['source']],record=probe,conclusion=probe['target'],requirements=[],available=probe['availability']!='unavailable',checks=checks))
        if len({p['probe_id'] for p in inv['probes']})!=len(inv['probes']):raise Incomplete('AMBIGUOUS_PROBE_IDENTITY')
        producers=sorted(producers+probes,key=canonical);route_links={g['id']:[] for g in b['obligations']}
        def operation(p,premises,missing):
            ids=[]
            if p['kind']!='observation':
                for belief in history.values():
                    counts['history_scan_visits']+=1
                    tr=belief['transition'];match=(tr['kind']==p['kind'] and tr['premise_revision_ids']==premises)
                    match=match and ((tr['rule_id']==p['identity'][0] and tr['rule_revision']==p['identity'][1]) if p['kind']=='deduction' else tr['independence_id']==p['identity'][0])
                    if match:ids.append(belief['belief_revision_id'])
            readiness='RESULT_ALREADY_RECORDED' if ids else 'UNAVAILABLE' if not p['available'] else 'MISSING_PREMISES' if missing else 'INPUTS_PRESENT' if p['kind']!='observation' else 'OBSERVATION_OPPORTUNITY'
            if p['kind']=='observation' and p['available']:
                if any(c['status']!='PASS' for c in p['checks']):readiness='OBSERVATION_PRECONDITION_UNRESOLVED'
                elif p['record']['availability']=='unknown':readiness='OBSERVATION_AVAILABILITY_UNKNOWN'
            semantic=(*work_scope,p['kind'],p['record'],premises)
            identifier=key('operation',semantic)
            if identifier in nodes:return identifier
            if counts['operations']>=limits.operations:raise Incomplete('OPERATION_BOUND')
            counts['operations']+=1
            i=node('operation',semantic,producer=p,ordered_premises=premises,missing_slots=missing,materialized_result_ids=sorted(ids),readiness=readiness,
                   authority=False,adequacy='UNKNOWN_UNTIL_NEW_CERTIFIED_RESULT',reexecution_as_repair=False,eligibility='actual source/lineage and admission must be checked')
            for check in p.get('checks',[]):
                child=node('observation-precondition',(*work_scope,check['name']),check=check)
                edge(i,child,'AND_OBSERVATION_PRECONDITION')
            for slot,requirement in enumerate(p['requirements']):
                ref=premises[slot]
                if ref is not None and ref in current:
                    child=node('premise',(*work_scope,ref),belief=current[ref],state='CURRENT')
                else:
                    literal=history[requirement]['proposal']['support']['conclusion'] if p['kind']=='revision' and requirement in history else requirement if p['kind']=='deduction' else None
                    child=node('missing-premise',(*work_scope,p['kind'],requirement),requirement=requirement,literal=literal,state='STALE' if p['kind']=='revision' and requirement in history else 'MISSING')
                    # Direct observation is an opportunity, not permission to replace an exact model parent ID.
                    routes=[q for q in probes if q['conclusion']==literal] if p['kind']=='deduction' else []
                    for q in routes:edge(child,operation(q,[],[]),'OR_OBSERVATION_OPPORTUNITY')
                    if not routes:block('NO_REGISTERED_ROUTE','no direct observation route for this exact premise in the supported fragment',node=child)
                    if any(q['kind']!='observation' and q['conclusion']==literal for q in producers):
                        block('SCOPE_OR_BUDGET_INCOMPLETE','deeper inference not expanded by this one-step bridge',node=child)
                        nonlocal_incomplete.append('UNEXPANDED_DEEPER_ROUTE')
                edge(i,child,'AND_PREREQUISITE',slot)
            return i
        nonlocal_incomplete=[]
        for p in producers:
            if p['conclusion'] not in (conclusion,opposite):continue
            eligible=[]
            for c in sorted(m['classes'],key=lambda c:c['id']):
                if counts['role_comparisons']>=limits.comparisons:raise Incomplete('COMPARISON_BOUND')
                counts['role_comparisons']+=1
                if c['kind']==p['kind'] and c['identity']==p['identity']:eligible.append(c['id'])
            if not eligible:block('APPLICABILITY_REQUIRES_REVIEW','registered relevant producer has no declared role; retained for investigation',producer=p)
            if p['kind']=='deduction':
                alternatives=[sorted(i for i,x in current.items() if x['proposal']['support']['conclusion']==lit) or [None] for lit in p['requirements']]
                tuples=product(*alternatives)
            elif p['kind']=='revision':tuples=[tuple(p['requirements'])]
            else:tuples=[()]
            for candidate in tuples:
                if counts['tuple_visits']>=limits.tuples:raise Incomplete('TUPLE_BOUND')
                counts['tuple_visits']+=1;premises=list(candidate);missing=[j for j,i in enumerate(premises) if i is None or i not in current]
                i=operation(p,premises,missing);edge(root,i,'INVESTIGATE_REGISTERED_PRODUCER')
                if p['conclusion']==conclusion:
                    for group in b['obligations']:
                        if set(eligible)&set(group['classes']):edge(group_nodes[group['id']],i,'OR_POSSIBLE_PRODUCER');route_links[group['id']].append(i)
        for item in obligations:
            routes=sorted(set(route_links[item['obligation_id']]));item['routes']=routes
            if item['status']!='PASS' and not any(nodes[i]['producer']['available'] and not nodes[i]['materialized_result_ids'] for i in routes):
                item['reasons'].append('NO_REGISTERED_ROUTE');block('NO_REGISTERED_ROUTE','no available unmaterialized declared route; repetition of existing evidence is not a repair',obligation=item['id'])
            nodes[item['id']].update(routes=routes,reasons=item['reasons'])
        if nonlocal_incomplete:raise Incomplete('UNEXPANDED_DEEPER_ROUTE')
    except (Incomplete,KeyError,IndexError,TypeError,ValueError) as error:
        complete=False;reason=str(error) if isinstance(error,Incomplete) else 'MALFORMED_OR_UNSUPPORTED_INPUT:'+type(error).__name__
        block('SCOPE_OR_BUDGET_INCOMPLETE',reason)
    if discovery_start is not None:costs['discovery_and_graph_ns']=perf_counter_ns()-discovery_start
    t=perf_counter_ns()
    probe_records=f.get('inventory',{}).get('probes',[]) if isinstance(f.get('inventory',{}),dict) else []
    probe_records=probe_records if isinstance(probe_records,list) else []
    result=dict(schema='obligation-work-view/v0',authority=False,complete=complete,reason=reason,partial_nodes_are_diagnostic=not complete,
        task=task,bindings=bindings,view_identity=digest((frame.identity,m,a,b,limits.__dict__)),
        A=a,B=b,observed=f.get('observed'),obligations=sorted(obligations,key=lambda o:o['id']),
        global_blockers=sorted(blockers,key=canonical),nodes=sorted(nodes.values(),key=lambda n:n['id']),edges=sorted(edges.values(),key=canonical),
        counts=dict(**counts,nodes=len(nodes),edges=len(edges)),limits=limits.__dict__,
        unsupported_observation_channels=[p for p in probe_records if isinstance(p,dict) and p.get('report_type')!='numeric'],
        coverage='one-step registered producer explanation plus full frozen assessment; not inference closure, scheduling or an execution permission')
    view=ObligationWorkView(canonical(result));costs['serialization_ns']=perf_counter_ns()-t;costs['output_bytes']=len(view.payload_json.encode());costs['total_projection_ns']=perf_counter_ns()-start
    return view,costs
