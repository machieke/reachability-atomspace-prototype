"""Post-measurement descriptive report; never imported by the experiment."""
from collections import Counter, defaultdict
import json
from pathlib import Path
import statistics
import sys


def load(path):return json.loads(Path(path).read_text())
def mean(xs):return sum(xs)/len(xs) if xs else None

def signs(xs):return dict(favorable=sum(x<0 for x in xs),neutral=sum(x==0 for x in xs),unfavorable=sum(x>0 for x in xs))


def summarize(bundle):
    bundle=Path(bundle);s=load(bundle/'summary.json');parents=[r for r in s['closed'] if not r['sibling']]
    paired={(r['task_id'],r['budget'],r['policy']):r for r in s['closed']}
    groups=defaultdict(list);qgroups=defaultdict(list);rootgroups=defaultdict(list)
    for r in parents:groups[(r['cohort'],r['policy'])].append(r)
    for r in s['common']:
        if not r['sibling']:qgroups[(r['cohort'],r['policy'])].append(r)
    for r in s['roots']:
        if not r['sibling']:rootgroups[(r['cohort'],r['policy'])].append(r)
    aggregates=[]
    for key,rs in sorted(groups.items()):
        qs=qgroups[key];roots=rootgroups[key];success=[r['first_optimal_witness'] for r in roots if r['first_optimal_witness']]
        cost_keys=set().union(*(r['costs_ns'] for r in rs))
        aggregates.append(dict(cohort=key[0],policy=key[1],parent_budget_cells=len(rs),parents=len({r['parent_id'] for r in rs}),
            mean_episode_gap=mean([r['gap'] for r in rs]),worst_episode_gap=max(r['gap'] for r in rs),
            mean_external_loss=mean([r['external'] for r in rs]),mean_certified_loss=mean([r['certified'] for r in rs]),
            mean_actions=mean([r['actions'] for r in rs]),mean_operation_work=mean([r['operation_work'] for r in rs]),
            mean_observation_work=mean([r['observation_work'] for r in rs]),
            query_count=len(qs),optimal_decisions=sum(r['agreement'] for r in qs),mean_decision_regret=mean([r['regret'] for r in qs]),
            worst_decision_regret=max(r['regret'] for r in qs),mean_query_ms=mean([r['elapsed_ns']/1e6 for r in qs]),
            mean_shared_discovery_ms=mean([r['charged_discovery_ns']/1e6 for r in qs]),
            mean_controller_ms=mean([r['controller_elapsed_ns']/1e6 for r in rs]),mean_total_ms=mean([r['total_elapsed_ns']/1e6 for r in rs]),
            mean_costs_ms={k:mean([r['costs_ns'].get(k,0)/1e6 for r in rs]) for k in sorted(cost_keys)},
            mean_model_validation_ms=mean([r['model_validation_ns']/1e6 for r in rs]),
            mean_retention_validation_ms=mean([r['retention_validation_ns']/1e6 for r in rs]),
            vs_direct_B0=signs([r['loss']-paired[(r['task_id'],r['budget'],'B0')]['loss'] for r in rs]),
            vs_direct_both=signs([r['loss']-paired[(r['task_id'],r['budget'],'B3-normalized-both')]['loss'] for r in rs]),
            roots=len(roots),roots_with_primary_optimal_witness=len(success),
            mean_root_plan_gap=mean([r['incumbent_value']-r['reference_value'] for r in roots]),
            median_first_optimal_attempts_among_successes=statistics.median(r['attempts'] for r in success) if success else None,
            median_first_optimal_ms_among_successes=statistics.median(r['elapsed_ns']/1e6 for r in success) if success else None))
    guidance=[]
    for key,rs in sorted(groups.items()):
        if not key[1].startswith('PLAN-pressure-order-'):continue
        suffix=key[1][len('PLAN-pressure-order'):]
        for other in ('PLAN-neutral','PLAN-B0-order'):
            delta=[r['loss']-paired[(r['task_id'],r['budget'],other+suffix)]['loss'] for r in rs]
            guidance.append(dict(cohort=key[0],configuration=suffix,comparison=other,**signs(delta),
                mean_loss_delta=mean(delta),best_delta=min(delta),worst_delta=max(delta)))
    cases={};gate_counts=Counter();query_status=Counter();suffix_status=Counter();bounds=Counter();wall=[];memory=[]
    chosen={'depth-2','shared-0','depth-0','depth-3','budget-2','budget-7','and-6','budget-0','budget-0-dominated',
            'completion-0','new-depth-0','new-completion-0','shared-6','shared-6-permuted'}
    for r in s['closed']:
        entry=load(bundle/r['path']/'result.json');result=entry['result']
        gate_counts.update(x['status'] for x in result['selected'])
        for q in entry['searches']:
            query_status[q['status']]+=1;suffix_status[q['suffix_status']]+=1;bounds.update(q['bounds'])
            memory.append(q['work']['memory_accounting_bytes'])
            if r['mode']=='wall': wall.append(dict(policy=r['policy'],elapsed_ns=q['elapsed_ns'],limit=r['limits']['wall_ns'],
                overrun_ns=max(0,q['elapsed_ns']-r['limits']['wall_ns']),attempts=q['work']['attempts']))
        if r['task_id'] not in chosen:continue
        key=r['task_id']+'/'+r['budget'];cases.setdefault(key,[])
        actions=[]
        for d in entry['labels']['decisions']:
            actions.append(dict(action=d['selected'],reference_value=d['value'],q_selected=d['q'][d['selected']]['value'],
                regret=d['regret'],status=d['receipt']['status'],before=d['outcome_before'],after=d['outcome_after']))
        cases[key].append(dict(policy=r['policy'],loss=r['loss'],gap=r['gap'],external=r['external'],certified=r['certified'],
            actions=actions,work={k:r[k] for k in ('actions','operation_work','observation_work')},path=r['path']))
    siblings=[]
    for r in s['closed']:
        if not r['sibling']:continue
        parent=paired[(r['parent_id'],r['budget'],r['policy'])]
        siblings.append(dict(task=r['task_id'],budget=r['budget'],policy=r['policy'],
            loss_delta=r['loss']-parent['loss'],reference_optimum_delta=(r['loss']-r['gap'])-(parent['loss']-parent['gap'])))
    family=defaultdict(list)
    for r in parents:family[(r['cohort'],r['family'],r['policy'])].append(r)
    family_rows=[dict(cohort=k[0],family=k[1],policy=k[2],parent_budget_cells=len(rs),mean_gap=mean([r['gap'] for r in rs]),
        worst_gap=max(r['gap'] for r in rs)) for k,rs in sorted(family.items())]
    branch=[]
    for cap in (1,4,16,64):
        for other in ('PLAN-neutral','PLAN-B0-order'):
            rs=[r for r in s['branch_comparisons'] if r['cap']==cap and r['comparison']==other]
            branch.append(dict(cap=cap,comparison=other,queries=len(rs),different_expanded_sets=sum(not r['same_set'] for r in rs),
                different_expanded_order=sum(not r['same_order'] for r in rs)))
    rootlookup={(r['task_id'],r['budget'],r['policy']):r for r in s['roots'] if r['mode']=='attempts'}
    worsened=[]
    for r in rootlookup.values():
        n=r['limits']['attempts']
        if n==1:continue
        smaller={4:1,16:4,64:16}[n];p=r['policy'].rsplit('-n',1)[0]+'-n'+str(smaller)
        prior=rootlookup[(r['task_id'],r['budget'],p)]
        if r['incumbent_value']>prior['incumbent_value']:worsened.append((r['task_id'],r['budget'],r['policy']))
    return dict(schema='planning-publication-summary/v1',source=load(bundle/'source.json'),execution=load(bundle/'execution.json'),
        closed_runs=len(s['closed']),common_states=444,common_queries=len(s['common']),aggregates=aggregates,guidance=guidance,
        families=family_rows,diagnostics=cases,siblings=siblings,branch_expansion_comparisons=branch,
        root_primary_worsenings=worsened,closed_escalation=s['search_escalation'],
        actual_gate_results=dict(gate_counts),closed_search_statuses=dict(query_status),closed_suffix_statuses=dict(suffix_status),
        closed_search_bounds=dict(bounds),maximum_query_memory_accounting_bytes=max(memory),
        wall_query_count=len(wall),maximum_wall_query_overrun_ns=max(r['overrun_ns'] for r in wall),
        mean_wall_query_overrun_ns=mean([r['overrun_ns'] for r in wall]),
        limitations=['Timing is a single engineering run, with boundary-checked atomic overruns; no significance claim.',
            'First optimum means primary external-loss optimum. Conditional medians exclude censored roots; success counts must accompany them.',
            'Cohort aggregates pool two semantic budgets equally per parent; decision averages count sampled states, not independent parents.',
            'Pressure guidance conclusions apply only to the frozen normalized both orderer.'])


if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('usage: summarize_review.py BUNDLE OUTPUT_JSON')
    Path(sys.argv[2]).write_text(json.dumps(summarize(sys.argv[1]),indent=2,sort_keys=True)+'\n')
