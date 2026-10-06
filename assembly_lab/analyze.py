"""Descriptive recorded-sequence analysis; never imported by runtime policy."""
import json
from collections import Counter,defaultdict
from pathlib import Path


def rows_at(path):return [json.loads(t) for t in Path(path).read_text().splitlines()]


def trace_metrics(rows,query_budget):
    total=0;milestones={};tranches=[];counts=Counter();peaks=Counter();known={};binding=None
    for index,row in enumerate(rows):
        d=row['discovery'];base=total;q=0;phase='control';current_job=None;producer_rows={};selected=row['selected'];events=d['events'];t=dict(index=index,binding=row['public_binding'],controls=[],producers=[],attempts=[],preparation=[],bounds=[],selected=selected,result=row.get('result'),after=row['after'],external_loss=row['external_loss'])
        if binding!=row['public_binding']:known={};binding=row['public_binding']
        def landmark(name,event=None):
            if name not in milestones:
                milestones[name]=dict(tranche=index,episode_queries=base+q,
                    episode_elapsed_ns=(row.get('decision_start_episode_ns',0)+event['at_ns'] if event and 'at_ns' in event else None))
        for e in events:
            kind=e['kind']
            if kind=='query_consumed':q+=1;counts['native_queries']+=1;counts[phase+'_queries']+=1
            if kind=='query_start':phase=e['phase']
            if kind=='route' and e['arc']['purpose']=='producer-discovery':
                producer=e['arc']['target'];known.setdefault(producer,base+q);landmark('first_known_producer',e)
                producer_rows.setdefault(producer,dict(producer=producer,known_at_episode_query=known[producer],remaining=query_budget-q,attempted=False))
            if kind=='job_known' and e['job']['kind']=='join':known[e['job']['target']]=e['job']['known_query']
            if kind=='expand':
                current_job=e['job'];phase='join' if current_job['kind']=='join' else 'inspection'
                if current_job['kind']=='join':
                    p=current_job['target'];a=dict(producer=p,start_query=base+q,wait_queries=base+q-known.get(p,base+q),score=e['score'],remaining_queries=query_budget-q,job=e['job'])
                    t['attempts'].append(a);counts['join_attempts']+=1;landmark('first_attempted_join',e)
                    producer_rows.setdefault(p,dict(producer=p,known_at_episode_query=known.get(p),attempted=False))['attempted']=True
            if kind=='join_begin' and t['attempts']:t['attempts'][-1].update(resident=e['resident'],pins=e['pins'],remaining_queries=e['remaining'],phase=e['phase'])
            if kind=='join_end':
                t['attempts'][-1].update(reason=e['reason'],query_cost=e['queries'],tuple_visits=e['tuple_visits'],new_candidates=e['new_candidates']);counts['join_'+e['reason']]+=1
            if kind=='join':
                if t['attempts']:t['attempts'][-1].update(ordered_slots=e['ordered_slots'],alternatives=e['alternatives'],complete_native_join=e['complete'])
                if all(e['alternatives']):landmark('first_complete_tuple',e)
            if kind=='tuple_candidate':landmark('first_complete_tuple',e)
            if kind=='assembly_protected':counts['protected']+=1
            if kind=='assembly_served':counts['served']+=1;counts['served_without_eligible_candidate']+=not e['eligible']
            if kind=='assembly_abandoned':counts['abandoned_stale']+=1
            if kind=='assembly_offers':
                counts['affordability_scans']+=1
                counts['unaffordable_offer_observations']+=sum(not o['affordable'] for o in e['offers'])
                for o in e['offers']:
                    if not o['affordable']:counts['offer_'+o['reason']]+=1
            if kind=='control_end':t['controls'].append(e)
            if kind.startswith('preparation_') or kind=='pin_bundle':t['preparation'].append(e)
            if kind in ('bounded_stop','preparation_blocked'):t['bounds'].append(e);counts['bound_'+e['reason']]+=1
        counts['tranches_without_affordable_slot']+=any(e['kind']=='assembly_offers' and e['offers'] for e in events) and not any(e['kind']=='assembly_offers' and any(o['affordable'] for o in e['offers']) for e in events)
        counts['preparation_blocked']+=sum(e['kind']=='preparation_blocked' for e in events)
        total=base+d['native_queries']
        for p,v in producer_rows.items():
            v['end_wait_queries']=total-known.get(p,total)
            # Actual inspection since first known, until attempt/end; not premise validity.
            attempt=next((a for a in t['attempts'] if a['producer']==p),None)
            v['queries_between_known_and_attempt_or_end']=(attempt['start_query'] if attempt else total)-known.get(p,total)
        t.update(producers=list(producer_rows.values()),native_queries=d['native_queries'],tuple_visits=d['tuple_visits'],pending_joins=[j for j in d['pending_jobs'] if j['kind']=='join'],service=d.get('service'),workspace_costs=d['workspace_costs'],peaks=d['peaks'],reason=d['reason'])
        for metric,value in d['peaks'].items():peaks[metric]=max(peaks[metric],value)
        counts['tuple_visits']+=d['tuple_visits'];counts['evictions']+=d['workspace_costs'].get('evictions',0);counts['rematerializations']+=d['workspace_costs'].get('rematerializations',0)
        if selected:
            actual=row['result'];counts['selected_'+selected['kind']]+=1;counts['result_'+actual['status']]+=1
            if actual['status']=='PASS' and 'commit' in actual:
                counts['certified_numerical_commits']+=1
                if 'first_certified_numerical_commit' not in milestones:milestones['first_certified_numerical_commit']=dict(tranche=index,episode_queries=total,episode_elapsed_ns=row.get('episode_elapsed_ns'))
        tranches.append(t)
    return dict(counts=dict(counts),peaks=dict(peaks),milestones=milestones,tranches=tranches)


def analyze(output,report):
    from .compare import folder
    output=Path(output);entries=[];by={}
    for r in report['results']:
        m=trace_metrics(rows_at(output/folder(r)/'trace.jsonl'),r['queries'])
        item=dict(run=folder(r),case_id=r['case_id'],formula_mode=r['formula_mode'],queries=r['queries'],contract=r['contract'],mode=r['mode'],conformance=r['conformance'],outstanding=r.get('outstanding'),external_loss=r.get('external_loss'),elapsed_ns=r['elapsed_ns'],costs_ns=r['costs_ns'],discovery_costs_ns=r['discovery_costs_ns'],recall_costs=r['recall_costs'],**m)
        entries.append(item);by[r['case_id'],r['formula_mode'],r['queries'],r['contract'],r['mode']]=item
    pairs=[]
    comparisons=(('shared_queue','assembly','WS-queue','frozen','WS-queue'),('shared_flow','assembly','WS-flow','frozen','WS-flow'),('incremental_flow_vs_queue','assembly','WS-flow','assembly','WS-queue'),('incremental_flow_vs_local','assembly','WS-flow','assembly','WS-local'))
    for case,formula,q,contract,mode in by:
        if (contract,mode)!=('frozen','WS-queue'):continue
        for name,ac,am,bc,bm in comparisons:
            if (case,formula,q,ac,am) not in by or (case,formula,q,bc,bm) not in by:continue
            a,b=by[case,formula,q,ac,am],by[case,formula,q,bc,bm]
            valid=a['conformance']==b['conformance']=='PASS'
            delta=a['outstanding']-b['outstanding'] if valid else None
            ext=a['external_loss']-b['external_loss'] if valid else None
            pairs.append(dict(comparison=name,case_id=case,formula_mode=formula,queries=q,loss_delta=delta,external_delta=ext,
                result='unavailable' if delta is None else 'favorable' if delta<0 else 'unfavorable' if delta>0 else 'neutral',
                query_delta=a['counts']['native_queries']-b['counts']['native_queries'],elapsed_delta_ns=a['elapsed_ns']-b['elapsed_ns']))
    summary={name:dict(Counter(p['result'] for p in pairs if p['comparison']==name)) for name,*_ in comparisons}
    return dict(schema='completion-aware-recorded-analysis/v1',summary=summary,pairs=pairs,runs=entries,
                limitations=['descriptive timings; single balanced pass with concurrent validation','queries between known producer and attempt are not proof of complete premises','first divergence is not assigned causal credit for all later outcomes','offers are repeated observations, not unique obligations','active workspace is not total memory'])
