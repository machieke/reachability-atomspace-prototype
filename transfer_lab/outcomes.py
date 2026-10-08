"""Descriptive outcome extraction; never supplied to the consumer."""
import json
from pathlib import Path
from collections import Counter
from .cases import fixture

def describe(path,result):
    path=Path(path);rows=[json.loads(s) for s in (path/'trace.jsonl').read_text().splitlines()];ticks=json.loads((path/'ticks.json').read_text());changes=json.loads((path/'changes.json').read_text());f=fixture(result['parent'])
    if not rows:return dict(construction_or_runtime_failure=result.get('error'),task_success=False,reference_feasibility='UNKNOWN')
    last=rows[-1];v=last['view'];stops=sorted({r['stop'] for r in rows if r.get('stop')});conditions=[]
    if result.get('metrics',{}).get('first_observed_completion') is not None:conditions.append('completed-historically')
    if result.get('metrics',{}).get('final_observed_loss',10)>0:conditions.append('recognized-loss-remains')
    if not all(r['view']['complete'] and r['frontier']['complete'] for r in rows):conditions.append('incomplete-or-unsupported-scope')
    if any('EXHAUSTED' in s or 'BOUND' in s for s in stops):conditions.append('exhausted-budget')
    if any('OPPORTUNITY' in s or 'OUTCOME' in s for s in stops):conditions.append('waiting-or-observation-unavailable')
    if any('NO_KNOWN' in s for s in stops):conditions.append('no-registered-supported-route')
    if v.get('A',{}).get('numerical_status')!='PASS':conditions.append('live-policy-not-passing')
    if last.get('choice',{}).get('review_complete') is False:conditions.append('required-review-unresolved')
    if any(b['category'] in ('OBJECTION_REQUIRES_REVIEW','APPLICABILITY_REQUIRES_REVIEW') for b in v.get('global_blockers',[])):conditions.append('objection-or-applicability-unresolved')
    for name in ('B','A'):
        if v.get(name,{}).get('unresolved_obligations'):conditions.append(name+'-mandatory-obligations-unresolved')
    selections=[dict(index=r['index'],tick=r['tick'],slot=r['slot'],kind=r['selected']['kind'],target=r['selected']['target'],premise_ids=r['selected']['premise_ids'],status=r['result']['status'],budget=r['choice']['budget'],A=r['view'].get('A',{}).get('numerical_status'),B=r['view'].get('B',{}).get('numerical_status'),loss_after=r['after']['outstanding']) for r in rows if r['selected']]
    selected_keys=[(r['selected']['logical_id'],r['selected']['basis']) for r in rows if r['selected']]
    repeated=len(selected_keys)-len(set(selected_keys));logical_retries=len(selected_keys)-len({k[0] for k in selected_keys})
    actual_observations=[dict(tick=r['tick'],descriptor=e['descriptor'],response=e['response']) for r in rows for e in r.get('received',[]) if e['kind']=='acquisition']
    requests=[r for r in selections if r['kind']=='request'];calls=result.get('runtime_calls',[])
    return dict(family=f['family'],question=f['question'],capture_complete=all(r['frame']['complete'] for r in rows),review_complete_at_end=last['choice'].get('review_complete'),queries_complete=all(r['costs'].get('native_retrieval',{}).get('complete',True) for r in rows),work_complete=all(r['view']['complete'] for r in rows),conditions=sorted(set(conditions)),raw_stop_reasons=stops,final_stop=result.get('stop'),task_success=result.get('metrics',{}).get('final_observed_loss')==0,physical_completion=result.get('metrics',{}).get('first_physical_goal'),recognized_completion=result.get('metrics',{}).get('first_observed_completion'),final_A=v.get('A',{}).get('numerical_status'),final_B=v.get('B',{}).get('numerical_status'),unresolved_obligations=v.get('B',{}).get('unresolved_obligations',[]),global_blockers=v.get('global_blockers',[]),unresolved_producers=[r['producer']['identity'] for r in last['choice'].get('review',[]) if r['status']!='MATERIALIZED_CURRENT'],accepted_depth=result.get('longest_dependency_path'),formula_calls=len(calls),rejected_or_stale_operations=[r for r in selections if r['status']!='PASS'],operation_counts=dict(Counter(r['kind'] for r in selections)),requests=requests,public_changes=[c['declaration'] for c in changes],selections=selections,budget=dict(selections=result.get('selections'),work=result.get('work'),acquisitions=result.get('acquisitions')),effects=result.get('effects'),trajectory=[dict(tick=t['time'],world_loss=t['physical_sample']['goal_deficit'],recognized_loss=t['authority_after']['outstanding'],goal_label=t['authority_after']['goal_label'],stage=t['authority_after']['stage'],stop=t['consumer_stop'],mismatch_reasons=t['mismatch_reasons']) for t in ticks],monitoring_gaps=[dict(tick=t['time'],reasons=t['mismatch_reasons']) for t in ticks if t['mismatch_reasons']],reference_feasibility=result.get('dependency_reference',{}).get('task_feasibility','UNKNOWN'),missed_opportunity='NOT_ESTABLISHED: no counterfactual same-information policy witness',attempted_work_suppression=dict(repeated_same_basis_selections=repeated,same_logical_work_new_basis_retries=logical_retries,scope='Full relevant-basis identity checked independently for every selected operation'),actual_observation_responses=actual_observations)

def render(report):
    lines=['# Frozen transfer evaluation','',f"Measured source: `{report['sources']['revision']}`. Twelve declared parent structures, two retrieval arms, native PLN in both. Conformance is separate from effectiveness.",'','| Parent | Arm | Conformance | Depth / calls | Physical / recognized first completion | J physical / recognized | Final stop | Seconds |','|---|---|---|---|---|---|---|---:|']
    for r in report['results']:
        m=r.get('metrics',{});lines.append('| '+' | '.join(map(str,(r['parent'],r['arm'],r['conformance'],str(r.get('longest_dependency_path'))+' / '+str(len(r.get('runtime_calls',[]))),str(m.get('first_physical_goal'))+' / '+str(m.get('first_observed_completion')),str(m.get('J_world'))+' / '+str(m.get('J_certified')),r.get('stop',r.get('error')),f"{r['elapsed_ns']/1e9:.6f}")))+' |')
    lines+=['','Every result retains simultaneous conditions, exact sequences, live/mandatory status, observations, replacements, monitoring gaps and both loss trajectories in result.json/report.json. Scan shares the same cognitive policy; parity is not superiority. A completed history can coexist with current reopened loss. Unresolved does not mean correct abstention; counterfactual task feasibility remains explicitly limited.']
    return '\n'.join(lines)+'\n'
