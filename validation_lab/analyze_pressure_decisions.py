"""Trace-derived loss decomposition and same-snapshot ranking diagnostics."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from time import perf_counter_ns

from reachability.pressure import PressureLimits
from reachability.pressure_controller import rank_b3
from reachability.pressure_work import anchor, b0_ranking, enumerate_work, operation_cost
from .audit_pressure_comparison import artifact_path, audit_bundle, equal, load, run_name

FROZEN = '3e8fd7be56362ed21944636bbe505b6a4a7aac6f'


def label(wire):
    args=wire['arguments']
    return wire['kind']+':'+str(args.get('rule_id',args.get('probe_id',args.get('goal_id'))))


def decompose(case, first, second):
    """Exact accounting identity, not a causal attribution to an early choice."""
    weights={g['goal_id']:case['public']['priorities'][g['goal_id']]['weight'] for g in case['public']['goals']}
    ticks=[]; by_goal=dict.fromkeys(weights,0.)
    equal([o['time'] for o in first['outcomes']],[o['time'] for o in second['outcomes']],'paired outcome times')
    for a,b in zip(first['outcomes'][:-1],second['outcomes'][:-1]):
        goals_a={g['goal_id']:g for g in a['goals']}; goals_b={g['goal_id']:g for g in b['goals']}
        delta={key:weights[key]*(goals_b[key]['external_loss']-goals_a[key]['external_loss']) for key in weights}
        for key,value in delta.items(): by_goal[key]+=value
        equal(sum(delta.values()),b['external_weighted_loss']-a['external_weighted_loss'],'per-tick loss decomposition')
        ticks.append(dict(time=a['time'],B0_external=a['external_weighted_loss'],B3_external=b['external_weighted_loss'],
            B0_certified=a['certified_weighted_loss'],B3_certified=b['certified_weighted_loss'],by_goal_delta=delta,
            total_delta=sum(delta.values())))
    total=second['integrated_external_loss']-first['integrated_external_loss']
    equal(sum(by_goal.values()),total,'integrated loss decomposition')
    return dict(B3_minus_B0=total,by_goal=by_goal,ticks=ticks,
        interpretation='Descriptive accounting over full decision sequences; not an intervention or first-divergence causal estimate.')


def decisions(directory, public, result):
    rows=[json.loads(line) for line in artifact_path(directory,'trace.jsonl').read_text().splitlines()]
    output=[]
    for i,row in enumerate(rows):
        if row['stage']!='selection': continue
        frontier=enumerate_work(public,row['snapshot'])
        equal([c.wire() for c in frontier.candidates],row['candidates'],'analysis public frontier')
        candidates=[c for c in frontier.candidates if c.candidate_id in row['ranks']]
        b0,search,complete=b0_ranking(public,row['snapshot'],candidates)
        equal(complete,True,'analysis B0 ranking bound')
        b3,field,_,_=rank_b3(public,row['snapshot'],candidates,PressureLimits(**result['pressure_limits']))
        scores=[]
        for c in candidates:
            scores.append(dict(candidate_id=c.candidate_id,operation=label(c.wire()),cost=operation_cost(public,c),
                recorded_score=-row['ranks'][c.candidate_id][0],recorded_rank=row['ranks'][c.candidate_id],
                same_snapshot_B0_score=-b0[c.candidate_id][0],same_snapshot_B3_score=-b3[c.candidate_id][0],
                same_snapshot_pressure=field['scores'][anchor(c)]['value']))
        output.append(dict(time=row['snapshot']['time'],step=row['step'],selected=label(row['selected']),
            receipt=rows[i+1]['receipt'],scores=scores,snapshot_digest=row['snapshot_digest'],
            support_literals=[s['literal'] for s in row['snapshot']['supports']],goals=row['snapshot']['goals'],
            same_snapshot_choices={name:label(min(candidates,key=lambda c:(rank[c.candidate_id],c.candidate_id)).wire())
                                   for name,rank in (('B0',b0),('B3',b3))},
            analysis_search=search))
    return output


def write_readable(report,path):
    lines=['# Recorded rich-episode decisions', '',f"Frozen source: `{FROZEN}`.", '',
        'Every pair below uses the recorded decisions, observations, stale replies and goal-loss history.',
        'Positive scores are the negated first rank component: higher wins; the full tie-break tuple is retained in JSON.',
        'B0 and B3 scores have different heuristic meanings. Absolute magnitudes across controllers are not calibrated values.',
        'Same-snapshot rescoring in JSON feeds both policies the same affordable candidates; it does not execute a counterfactual policy.',
        'Loss decomposition is an accounting identity across the entire sequence. The first divergence is not assigned the entire difference.', '']
    for pair in report['pairs']:
        lines += [f"## Seed {pair['seed']}, {pair['configuration']}", '',
            f"Integrated B3−B0 loss: {pair['decomposition']['B3_minus_B0']:g}. Per-goal contributions: "
            +', '.join(f'{key} {value:+g}' for key,value in pair['decomposition']['by_goal'].items())+'.', '',
            '| Tick | B0 external / certified | B3 external / certified | B3−B0 external |',
            '| ---: | ---: | ---: | ---: |']
        for tick in pair['decomposition']['ticks']:
            lines.append(f"| {tick['time']} | {tick['B0_external']:g} / {tick['B0_certified']:g} | "
                f"{tick['B3_external']:g} / {tick['B3_certified']:g} | {tick['total_delta']:+g} |")
        for variant in ('B0','B3'):
            lines += ['',f'### {variant} decisions','',
                '| Tick | Selected | Reply | Affordable candidate scores |',
                '| ---: | --- | --- | --- |']
            for row in pair['decisions'][variant]:
                scores='; '.join(f"{s['operation']} {s['recorded_score']:.9g} (cost {s['cost']})" for s in row['scores'])
                lines.append(f"| {row['time']} | {row['selected']} | {row['receipt']['status']} | {scores} |")
            lines += ['',f"Events: `{json.dumps(pair['events'][variant],sort_keys=True)}`.",'']
    lines += ['Authority-certified loss can lag supported external relief until monitoring. Relevant support changes can reopen both.',
        'All costs and final outcomes remain in the comparison bundle. No causal intervention, statistical significance or scaling claim.', '']
    path.write_text('\n'.join(lines))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle',type=Path); parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); start=perf_counter_ns()
    checked=audit_bundle(args.bundle,source_commit=FROZEN)
    original=load(args.bundle,'report.json'); config=load(args.bundle,'configuration.json')
    pairs=[]
    for case in config['episodes']:
        if case['case_id']!='competing-routes': continue
        for budget in config['configurations']:
            runs={r['variant']:r for r in original['results'] if r['case_id']==case['case_id']
                  and r['seed']==case['seed'] and r['configuration']==budget['name']}
            pairs.append(dict(seed=case['seed'],configuration=budget['name'],
                decomposition=decompose(case,runs['B0'],runs['B3']),
                decisions={variant:decisions(args.bundle/run_name(run),case['public'],run) for variant,run in runs.items()},
                events={variant:run['environment_events'] for variant,run in runs.items()}))
    report=dict(schema='pressure-decision-analysis/v1',source_revision=FROZEN,
        analysis_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        analysis_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),input_audit=checked,pairs=pairs,
        elapsed_ns=perf_counter_ns()-start)
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'decisions.json').write_text(json.dumps(report,indent=2)+'\n')
    write_readable(report,args.output/'decisions.md')
    print(json.dumps(dict(status='PASS',pairs=len(pairs),output=str(args.output))),flush=True)


if __name__=='__main__': main()
