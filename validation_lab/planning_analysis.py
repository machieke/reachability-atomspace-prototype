"""Offline labels and comparisons. Never imported by production planners."""
from collections import Counter, defaultdict
from pathlib import Path

from .planning_comparison import load, ARMS


def mean(values): return sum(values)/len(values) if values else None

def signs(values):
    return dict(favorable=sum(x<0 for x in values),neutral=sum(x==0 for x in values),unfavorable=sum(x>0 for x in values))


def summarize(directory,index):
    directory=Path(directory);closed=[];common=[];roots=[];pairs={};bounds=Counter();counter=Counter();costs=Counter()
    for cell in index:
        task=cell['task'];cohort='new' if task['partition']=='new-confirmation' else 'old-inspected';b=cell['configuration']['name']
        metadata=dict(task_id=task['task_id'],parent_id=task['parent_id'],family=task['family'],cohort=cohort,sibling=task['sibling'],budget=b)
        for path in cell['closed']:
            entry=load(directory/path/'result.json');r=entry['result'];config=entry['policy'];searches=entry['searches']
            work=Counter();times=Counter()
            for s in searches:
                bounds.update(s['bounds'])
                work.update({k:v for k,v in s['work'].items() if not k.endswith('_ns')})
                times.update({k:v for k,v in s['work'].items() if k.endswith('_ns')})
            row=dict(**metadata,policy=config['name'],arm=config['arm'],mode=config['mode'],limits=config['limits'],
                loss=r['integrated_external_loss'],gap=entry['labels']['episode_gap'],
                external=r['final']['external_weighted_loss'],certified=r['final']['certified_weighted_loss'],
                monitored_goals=sum(g['outstanding']==0 for g in r['final_snapshot']['goals']),
                actions=r['work']['actions'],operation_work=r['work']['operation_work'],observation_work=r['work']['observation_work'],
                total_elapsed_ns=r['total_elapsed_ns'],controller_elapsed_ns=r['controller_elapsed_ns'],costs_ns=r['costs_ns'],
                search_work=dict(work),search_costs_inclusive_ns=dict(times),search_elapsed_ns=sum(s['elapsed_ns'] for s in searches),
                model_validation_ns=sum(s['model_validation_ns'] for s in searches),retention_validation_ns=r.get('planner_retention_ns',0),
                bounds=[x for s in searches for x in s['bounds']],stop=r['stop_reason'],failures=r['failures'],
                decision_regrets=[d['regret'] for d in entry['labels']['decisions']],path=path)
            closed.append(row);pairs[(task['task_id'],b,config['name'])]=row
            counter.update(work);costs.update(times)
        for path in cell['common']:
            sample=load(directory/path/'result.json')
            for q in sample['rankings']:
                config=q['configuration'];search=q['search']
                row=dict(**metadata,policy=config['name'],arm=config['arm'],mode=config['mode'],limits=config['limits'],
                    tick=sample['state']['tick'],selected=q['selected'],regret=q['label']['regret'],agreement=q['label']['agreement'],
                    elapsed_ns=q['elapsed_ns'],charged_discovery_ns=q['discovery_ns'],path=path+'/'+q['path'],
                    search_value=None if search is None else search['value'],
                    expanded_states=[] if search is None else search['expanded_states'],
                    work={} if search is None else search['work'])
                common.append(row)
                if not sample['prefix'] and search is not None:
                    roots.append(dict(**metadata,policy=config['name'],mode=config['mode'],limits=config['limits'],
                        reference_value=q['label']['value'],incumbent_value=search['value'],first_optimal_witness=search['first_optimal_witness'],
                        improvements=search['improvements'],attempts=search['work']['attempts'],elapsed_ns=search['elapsed_ns'],path=row['path']))
    groups=defaultdict(list);qgroups=defaultdict(list)
    for row in closed:
        if not row['sibling']:groups[(row['cohort'],row['budget'],row['policy'])].append(row)
    for row in common:
        if not row['sibling']:qgroups[(row['cohort'],row['budget'],row['policy'])].append(row)
    aggregates=[]
    for key,rows in sorted(groups.items()):
        cohort,b,policy=key;queries=qgroups[key]
        aggregates.append(dict(cohort=cohort,budget=b,policy=policy,parents=len(rows),mean_loss=mean([r['loss'] for r in rows]),
            mean_gap=mean([r['gap'] for r in rows]),max_gap=max(r['gap'] for r in rows),worst=[r['task_id'] for r in rows if r['gap']==max(x['gap'] for x in rows)],
            mean_external=mean([r['external'] for r in rows]),mean_certified=mean([r['certified'] for r in rows]),
            common_states=len(queries),agreement=sum(q['agreement'] for q in queries),mean_regret=mean([q['regret'] for q in queries]),
            max_regret=max(q['regret'] for q in queries),mean_query_ms=mean([q['elapsed_ns']/1e6 for q in queries]),
            mean_controller_ms=mean([r['controller_elapsed_ns']/1e6 for r in rows]),mean_total_ms=mean([r['total_elapsed_ns']/1e6 for r in rows]),
            mean_attempts=mean([r['search_work'].get('attempts',0) for r in rows]),
            vs_direct_B0=signs([r['loss']-pairs[(r['task_id'],b,'B0')]['loss'] for r in rows]),
            vs_direct_both=signs([r['loss']-pairs[(r['task_id'],b,'B3-normalized-both')]['loss'] for r in rows])))
    comparisons=[]
    for cohort in ('old-inspected','new'):
        for b in sorted({r['budget'] for r in closed}):
            for cap in (1,4,16,64):
                pressure=[r for r in closed if r['cohort']==cohort and r['budget']==b and not r['sibling'] and r['policy']==ARMS[2]+'-n'+str(cap)]
                for other in ARMS[:2]:
                    deltas=[r['loss']-pairs[(r['task_id'],b,other+'-n'+str(cap))]['loss'] for r in pressure]
                    comparisons.append(dict(cohort=cohort,budget=b,attempt_cap=cap,comparison='pressure versus '+other,
                        **signs(deltas),mean_loss_delta=mean(deltas),worst_loss_delta=max(deltas),best_loss_delta=min(deltas)))
    escalation=[]
    for cohort in ('old-inspected','new'):
        for arm in ARMS:
            for small,large in ((1,4),(4,16),(16,64)):
                selected=[r for r in closed if r['cohort']==cohort and not r['sibling'] and r['policy']==arm+'-n'+str(large)]
                delta=[r['loss']-pairs[(r['task_id'],r['budget'],arm+'-n'+str(small))]['loss'] for r in selected]
                escalation.append(dict(cohort=cohort,arm=arm,small=small,large=large,**signs(delta),mean_loss_delta=mean(delta)))
    state_groups=defaultdict(dict)
    for row in common:
        if row['mode']=='attempts': state_groups[(row['task_id'],row['budget'],row['tick'],row['limits']['attempts'])][row['arm']]=row
    branch=[]
    for key,arms in state_groups.items():
        if len(arms)!=3:continue
        p=arms[ARMS[2]]
        for other in ARMS[:2]:
            q=arms[other];a=set(p['expanded_states']);b=set(q['expanded_states'])
            branch.append(dict(task_id=key[0],budget=key[1],tick=key[2],cap=key[3],comparison=other,
                same_set=a==b,same_order=p['expanded_states']==q['expanded_states'],pressure_only=len(a-b),other_only=len(b-a),shared=len(a&b)))
    return dict(schema='planning-analysis/v1',closed=closed,common=common,roots=roots,aggregates=aggregates,
        pressure_comparisons=comparisons,search_escalation=escalation,branch_comparisons=branch,
        closed_bounds=dict(bounds),closed_search_counters=dict(counter),closed_search_costs_inclusive_ns=dict(costs),
        notes=['Decision regret and episode gap are separate; overlapping regrets are never summed for causal attribution.',
               'Model/ranking/pressure/suffix subcategory times overlap inclusive search elapsed; do not sum them with controller totals.',
               'Old cohort is inspected; new cohort has twelve preregistered parents. Siblings excluded from headline aggregates.',
               'No statistical, transport, native PLN, recovery, duration or scaling claim.'])


def readable(summary,revision):
    lines=['# Bounded planning comparison','',f'Experimental source: `{revision}`.',
        '', 'The shared DFS evaluates complete feasible STOP continuations. Pressure changes child order only. '
        'Old tasks are inspected diagnostics; twelve new parents are preregistered confirmation cases. '
        'The table excludes identifier and dominated-route siblings. No policy is promoted.', '',
        '| Cohort | Budget | Policy | Mean episode gap | Worst gap | Mean decision regret | Query ms | Controller ms |',
        '| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for r in summary['aggregates']:
        lines.append(f"| {r['cohort']} | {r['budget']} | {r['policy']} | {r['mean_gap']:.3f} | {r['max_gap']:g} | "
            f"{r['mean_regret']:.3f} | {r['mean_query_ms']:.3f} | {r['mean_controller_ms']:.3f} |")
    lines += ['', 'Pressure ordering versus the same planner with neutral or B0 ordering. '
        'Favorable/neutral/unfavorable counts compare complete episode loss; lower is better.', '',
        '| Cohort | Budget | Attempts | Comparator | Favorable | Neutral | Unfavorable | Mean loss delta | Worst delta |',
        '| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |']
    for r in summary['pressure_comparisons']:
        lines.append(f"| {r['cohort']} | {r['budget']} | {r['attempt_cap']} | {r['comparison']} | {r['favorable']} | "
            f"{r['neutral']} | {r['unfavorable']} | {r['mean_loss_delta']:.3f} | {r['worst_loss_delta']:g} |")
    lines += ['', 'Detailed parent/family results, comparisons against both direct controls, terminal external and certified loss, '
        'requests/work, failures, bound hits, fixed-root improvement curves and first reference-optimal witnesses are in `summary.json`. '
        'Every search prefix, ordering score and actual certified request is retained in the per-run traces. '
        'References label recorded decisions offline and never stop the runtime search.', '',
        'Candidate discovery includes real and speculative enumeration. Pressure construction and iteration, actual inference, '
        'certification and persistence have separate controller categories. Model validation, B0 search, sorting, suffix validation '
        'and other search costs remain in the detailed records. Search subcategories overlap inclusive query/controller durations; '
        'do not add them twice. Actual peak RSS, OS scheduling attribution, individual fsync/byte attribution and real sensor latency '
        'are unmeasured. Timings are single-run engineering measurements, with rotated arm order and no significance claim.', '',
        'Decision regret and episode gap are distinct; overlapping decision regrets are not summed as causal explanations. '
        'Larger search caps guarantee no worse incumbent within an identical deterministic query prefix, but not monotone '
        'closed-loop episode loss. No adaptive transport, learned conductance, normalization expansion, numerical PLN scheduling, '
        'generalized recovery, new objective, duration model or scaling claim.', '']
    return '\n'.join(lines)
