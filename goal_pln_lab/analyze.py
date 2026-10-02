"""Offline decision/cost analysis; no evaluator answer is exposed to controllers."""
from collections import Counter, defaultdict
import json
from pathlib import Path
from experimental_online_pln.agenda import Snapshot
from experimental_goal_pln.reference import scan_closure
from experimental_goal_pln.relevance import extract_task, witness
from experimental_online_pln.agenda import Candidate


def analyze(root):
    root=Path(root);report=json.loads((root/'report.json').read_text())
    runs=[];commits=0;totals=defaultdict(lambda:defaultdict(int))
    for result in report['results']:
        folder=root/f"{result['mode']}-{result['case_id']}-w{result['budget']}-{result['arm']}"
        rows=[json.loads(line) for line in (folder/'trace.jsonl').read_text().splitlines()]
        history={b['belief_revision_id']:b for v in result['reconstruction']['authority'][0][3] for b in v['historical']}
        operations=[];unrelated=0
        for row in rows:
            if not row['selected']:continue
            snapshot=Snapshot.from_records(row['public_records']);raw=dict(row['selected']);raw['premise_ids']=tuple(raw['premise_ids'])
            c=Candidate(**raw);dep=scan_closure(snapshot,extract_task(snapshot));relevant=witness(c,snapshot,dep) is not None
            unrelated+=len(row['calls']) if not relevant else 0
            actual=row['result'];numerical=c.kind in ('deduction','revision')
            if len(row['calls'])!=int(numerical and 'proposal' in actual):
                raise ValueError('selected formula call count differs')
            if 'commit' in actual and actual['status']=='PASS':
                belief=actual['commit']['belief']
                if (history.get(belief['belief_revision_id'])!=belief or actual['proposal']!=belief['proposal']
                    or actual['pre']['certificate_id']!=belief['pre_certificate_id']
                    or actual['post']['certificate_id']!=belief['post_certificate_id']):
                    raise ValueError('selected commit differs from persisted certified belief')
                commits+=1
            operations.append(dict(step=row['step'],kind=c.kind,target=c.target,status=actual['status'],
                relevant=relevant,work=row['work'],acquisitions=row['acquisitions'],tick=row['logical_tick'],
                goal_loss=row['after']['outstanding'],external_loss=row['external_loss'],decision=row['after']['decision'],
                product=row['after']['product_observed'],dispatch=row['after']['dispatch'],
                calls=len(row['calls']),post_status=actual.get('post_status'),
                frontier_scope=row['discovery'].get('scope'),fallback=row['discovery'].get('fallback')))
        r={k:result[k] for k in ('case_id','mode','budget','arm','conformance','outstanding','external_loss','work',
            'acquisitions','stop','landmarks','costs_ns','discovery_costs_ns','elapsed_ns','tuple_visits')}
        r.update(operations=operations,unrelated_formula_calls=unrelated,formula_calls=len(result['runtime_calls']))
        runs.append(r)
        group=totals[result['mode']+':'+result['arm']]
        for k in ('elapsed_ns','work','acquisitions','tuple_visits'):group[k]+=result[k]
        group['formula_calls']+=len(result['runtime_calls']);group['unrelated_formula_calls']+=unrelated
        for costs in ('costs_ns','discovery_costs_ns'):
            for k,v in result[costs].items():group[k]+=v
    return dict(schema='goal-pln-analysis/v1',revision=report['sources']['revision'],parents=12,executions=len(runs),
        runs=runs,totals=dict(totals),selected_persisted_commits_checked=commits,
        operation_statuses=dict(Counter(o['status'] for r in runs for o in r['operations'])),
        limitations=['Nested inclusive timings are not additive.','One ordered pass, no timing uncertainty estimate.',
                    'Logical event clock is not elapsed world time.','Index entries measured; memory/RSS unmeasured.',
                    'Local formula joint checks do not establish a global overlapping joint model.'])


if __name__=='__main__':
    import sys
    print(json.dumps(analyze(sys.argv[1]),indent=2))
