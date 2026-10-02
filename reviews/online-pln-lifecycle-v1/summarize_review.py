"""Offline publication analysis; no controller inputs or native invocations."""
from collections import Counter
import json
from pathlib import Path
import sys

from reachability.pln_adapter import TruthValue
from reachability.probability_formula import PinnedFormulaRuntime


def summarize(root):
    root = Path(root)
    report = json.loads((root/'report.json').read_text())
    runs, commits, calls = [], 0, 0
    for result in report['results']:
        mode = 'finite' if result['mode'] == 'finite-checker' else 'native'
        folder = root/(mode+'-'+result['case_id'])
        rows = [json.loads(line) for line in (folder/'trace.jsonl').read_text().splitlines()]
        selected = [r for r in rows if r.get('selected')]
        history = {b['belief_revision_id']: b for v in result['reconstruction']['authority'][0][3]
                   for b in v['historical']}
        selected_calls = [c for r in selected for c in r['calls']]
        if selected_calls != result['runtime_calls']:
            raise ValueError('off-books or omitted runtime call')
        for row in selected:
            actual = row['result']
            numerical = row['selected']['kind'] in ('deduction', 'revision')
            if len(row['calls']) != int(numerical and 'proposal' in actual):
                raise ValueError('selected operation/formula call count differs')
            if 'commit' in actual and actual['status'] == 'PASS':
                belief = actual['commit']['belief']
                if (history.get(belief['belief_revision_id']) != belief
                        or actual['proposal'] != belief['proposal']
                        or actual['pre']['certificate_id'] != belief['pre_certificate_id']
                        or actual['post']['certificate_id'] != belief['post_certificate_id']):
                    raise ValueError('trace commit is not the persisted certified belief')
                commits += 1
        for call in selected_calls:
            truths = tuple(TruthValue(**v) for v in call['inputs'])
            expected = PinnedFormulaRuntime().evaluate(call['formula'], truths)
            actual = TruthValue(**call['result'])
            if actual != expected:
                raise ValueError('recorded runtime/formula mismatch')
            calls += 1
        runs.append(dict(case_id=result['case_id'], mode=mode, operations=[dict(step=r['step'],
            kind=r['selected']['kind'], target=r['selected']['target'], status=r['result']['status'],
            current_candidates=len(r['frontier']['candidates']), tuple_visits=r['frontier']['tuple_visits'],
            outstanding=r['after']['outstanding'], external_loss=r['external_loss'],
            coverage=r['after']['coverage'], open_work=r['after']['open_work'], decision=r['after']['decision'],
            product_observed=r['after']['product_observed']) for r in selected],
            result={k:result[k] for k in ('stage','outstanding','external_loss','effects','stop','selections',
                'work','acquisitions','forecast','relief_kinds','costs_ns','elapsed_ns')},
            runtime_calls=[{k:c[k] for k in ('mode','formula','status','postcheck_status','commit_status',
                                           'formula_agreement','elapsed_ns')} for c in selected_calls]))
    parity = all(next(s for s in runs if s['case_id'] == f['case_id'] and s['mode'] == 'native')['operations']
                 == f['operations'] for f in runs if f['mode'] == 'finite')
    if not parity:
        raise ValueError('finite/native semantic sequences differ')
    return dict(schema='online-pln-publication-summary/v1', measured_revision=report['sources']['revision'],
        runs=runs, status_counts=dict(Counter(op['status'] for r in runs for op in r['operations'])),
        finite_native_operation_parity=parity,
        offline_checks=dict(selected_persisted_commits=commits, formula_calls_recomputed=calls,
                            omitted_or_unselected_runtime_calls=0, status='PASS'))


if __name__ == '__main__':
    print(json.dumps(summarize(sys.argv[1]), indent=2))
