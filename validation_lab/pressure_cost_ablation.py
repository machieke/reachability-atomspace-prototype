"""Evaluator-only cost-placement ablation; the frozen B0/B3 runtime is unchanged."""
import argparse
from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from time import perf_counter_ns

from reachability import pressure_controller as controller
from reachability.pressure import derive
from reachability.pressure_work import anchor, build_graph, enumerate_work, operation_cost
from reachability.trace_protocol import fingerprint
from . import audit_pressure_comparison as audit
from .pressure_episodes import episodes, goal, profile, rule
from .run_pressure_comparison import configurations, run_one

FROZEN = '3e8fd7be56362ed21944636bbe505b6a4a7aac6f'
POLICIES = {'B0': None, 'B3-cost-both': (True, True),
            'B3-cost-route': (True, False), 'B3-cost-queue': (False, True),
            'B3-cost-neither': (False, False)}
ORIGINAL_RANK = controller.rank_b3
TOOL = 'validation_lab/pressure_cost_ablation.py'


def rank_cost(public, snapshot, candidates, limits, policy):
    routing, queue = POLICIES[policy]
    if routing and queue:
        return ORIGINAL_RANK(public, snapshot, candidates, limits)
    start = perf_counter_ns()
    nodes, edges, sources = build_graph(public, snapshot)
    if not routing:
        # Only these two edge classes encode operation costs in the frozen
        # builder. Prerequisite semantics, graph depth and normalization stay.
        targets = {'rule:'+r['rule_id'] for r in snapshot['rules']}
        targets |= {'probe:'+p['probe_id'] for p in public['probes']}
        edges = [replace(e, weight=1.) if e.child in targets else e for e in edges]
    construction = perf_counter_ns()-start
    start = perf_counter_ns()
    field = derive(dict(snapshot=fingerprint(snapshot), revisions=snapshot['revisions'],
        priorities=fingerprint(public['priorities']), cost_placement=policy), nodes, edges, sources, limits=limits)
    iteration = perf_counter_ns()-start
    ranks = {c.candidate_id: (-field['scores'].get(anchor(c), {}).get('value', 0.) /
             (operation_cost(public, c) if queue else 1), operation_cost(public, c), c.rank) for c in candidates}
    return ranks, field, construction, iteration


@contextmanager
def ranking_policy(policy):
    """Single-process evaluator binding, restored even after failed execution.

    Both live selection and offline audit use the named ranking. Candidate
    discovery, budget charging, public execution and all hard gates are untouched.
    No controller receives the evaluator case, outcomes or future events.
    """
    if policy not in POLICIES:
        raise ValueError('unknown cost-placement policy')
    previous = controller.rank_b3, audit.rank_b3
    calls = {'ranking_calls': 0}
    def rank(*args):
        calls['ranking_calls'] += 1
        return rank_cost(*args, policy)
    try:
        if policy != 'B0':
            controller.rank_b3 = audit.rank_b3 = rank
        yield calls
    finally:
        controller.rank_b3, audit.rank_b3 = previous


def diagnostic_cases():
    """Predeclared sensitivity cases, never added to pressure_episodes.py."""
    cases = []
    for depth in (0, 2, 4, 6, 8):
        for cost in (1, 2, 4, 8):
            condition = 2
            for _ in range(depth):
                condition = {'AND': [condition]}
            public = profile(['seed', 'high', 'low'],
                [rule('high', [1], 2), rule('low', [1], 3)],
                [goal('high', condition, 3), goal('low', 3)], [],
                {'high': cost, 'low': 1}, {'high': 1., 'low': 1.})
            cases.append(dict(case_id=f'depth-{depth}-cost-{cost}', version='diagnostic-v1', seed=7,
                public=public, diagnostic=dict(family='equivalent-condition-depth', depth=depth, cost=cost),
                world=dict(initial=[dict(literal=1, name='initial-seed')], probes={},
                           revoke_at=None, revoke_evidence=None, truth=[1, 2, 3]),
                description='Equivalent unary AND wrappers; unchanged ready operations, truth and loss.'))
    for cost in (1, 2, 4, 8):
        public = profile(['seed', 'answer'], [rule('cheap', [1], 2), rule('costly', [1], 2)],
            [goal('answer', 2)], [], {'cheap': 1, 'costly': cost}, {'answer': 1.})
        cases.append(dict(case_id=f'parallel-cost-{cost}', version='diagnostic-v1', seed=7,
            public=public, diagnostic=dict(family='parallel-route-cost', cost=cost),
            world=dict(initial=[dict(literal=1, name='initial-seed')], probes={},
                       revoke_at=None, revoke_evidence=None, truth=[1, 2]),
            description='Two ready proofs of the same result; only declared operation cost differs.'))
    return cases


def experiment():
    return dict(schema='pressure-cost-placement/v1', frozen_revision=FROZEN,
        policies=POLICIES, seeds=[7, 18], training_runs=0,
        frozen_cases=[case for seed in (7, 18) for case in episodes(seed)],
        frozen_configurations=configurations(), diagnostic_cases=diagnostic_cases(),
        diagnostic_configurations=[configurations()[0]],
        fixed=['candidate generation', 'cost tie-break', 'operation/observation charges',
               'budgets and pressure limits', 'certified authority', 'world events', 'outcome horizon'],
        interpretation='Exploratory factorial score ablation; no winner selection or benchmark replacement.')


def matrix(config):
    for group in ('frozen', 'diagnostic'):
        for case in config[group+'_cases']:
            for budget in config[group+'_configurations']:
                yield group, case, budget


def sources():
    files = audit.source_inputs()
    for name, digest in files.items():
        blob = subprocess.check_output(['git', 'show', FROZEN+':'+name], cwd=audit.ROOT)
        audit.equal(sha256(blob).hexdigest(), digest, 'frozen implementation '+name)
    return dict(frozen_revision=FROZEN, frozen_files=files,
                tool_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=audit.ROOT, text=True).strip(),
                tool_files={TOOL: sha256((audit.ROOT/TOOL).read_bytes()).hexdigest()})


def name(case, budget, policy):
    return f"{case['case_id']}-{case['seed']}-{budget['name']}-{policy}"


def comparison_rows(results):
    indexed = {(r['group'], r['result']['case_id'], r['result']['seed'], r['result']['configuration'], r['policy']): r for r in results}
    rows = []
    for entry in results:
        run = entry['result']; key = (entry['group'], run['case_id'], run['seed'], run['configuration'])
        for reference in ('B0', 'B3-cost-both'):
            if entry['policy'] == reference: continue
            base = indexed[key+(reference,)]['result']
            delta = run['integrated_external_loss']-base['integrated_external_loss']
            rows.append(dict(group=entry['group'], case_id=run['case_id'], seed=run['seed'],
                configuration=run['configuration'], policy=entry['policy'], reference=reference,
                integrated_loss_delta=delta,
                final_loss_delta=run['final']['external_weighted_loss']-base['final']['external_weighted_loss'],
                classification='favorable' if delta < 0 else 'unfavorable' if delta > 0 else 'neutral',
                controller_elapsed_ns_delta=run['controller_elapsed_ns']-base['controller_elapsed_ns'],
                pressure_ns=sum(run['costs_ns'][k] for k in ('pressure_construction_ns','pressure_iteration_ns'))))
    return rows


def write_readable(report, path):
    lines = ['# Operation-cost placement ablation', '',
        f"Frozen implementation: `{FROZEN}`. Diagnostic source: `{report['sources']['tool_revision']}`.", '',
        'The original benchmark and runtime are unchanged. These are exploratory results from one run per cell.',
        'Operation costs always charge the original budgets and remain the secondary tie-break. Only score placement varies.',
        'Wall caps vary with host load; raw elapsed costs do not establish a performance advantage.', '',
        '| Group | Case | Seed | Budget | Policy | Integrated loss | Final loss | Requests | Pressure ms | Controller ms |',
        '| --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for entry in report['results']:
        r = entry['result']; costs = r['costs_ns']
        lines.append(f"| {entry['group']} | {r['case_id']} | {r['seed']} | {r['configuration']} | {entry['policy']} | "
            f"{r['integrated_external_loss']:g} | {r['final']['external_weighted_loss']:g} | {r['work']['actions']} | "
            f"{(costs['pressure_construction_ns']+costs['pressure_iteration_ns'])/1e6:.3f} | {r['controller_elapsed_ns']/1e6:.3f} |")
    lines += ['', 'All candidate ranks, source-bound fields, observations, certified receipts, journals, work counts and cost categories are retained.',
        'Favorable/neutral/unfavorable classifications use integrated external loss only; final loss and measured overhead remain separate.',
        'Unary AND depth changes representation while preserving the condition, operations and physical truth. It does not add required work.',
        'Parallel-route cases isolate the score ratio for two ready proofs with different costs. Neither family is part of the frozen benchmark.',
        'No statistical significance, transport, learned conductance or generalized recovery claim.', '']
    path.write_text('\n'.join(lines))


def audit_experiment(directory):
    directory = Path(directory); start = perf_counter_ns()
    report = audit.load(directory, 'report.json'); config = audit.load(directory, 'configuration.json')
    audit.equal(report['schema'], 'pressure-cost-placement-results/v1', 'ablation schema')
    audit.equal(config, experiment(), 'ablation configuration')
    current = sources()
    audit.equal(report['sources']['frozen_revision'], FROZEN, 'frozen revision')
    audit.equal(report['sources']['frozen_files'], current['frozen_files'], 'frozen source inputs')
    audit.equal(report['sources']['tool_files'], current['tool_files'], 'ablation tool inputs')
    revision = subprocess.check_output(['git','rev-parse','--verify','--end-of-options',
        report['sources']['tool_revision']+'^{commit}'],cwd=audit.ROOT,text=True).strip()
    audit.equal(revision,report['sources']['tool_revision'],'full ablation source revision')
    for filename, digest in report['sources']['tool_files'].items():
        blob = subprocess.check_output(['git', 'show', revision+':'+filename], cwd=audit.ROOT)
        audit.equal(sha256(blob).hexdigest(), digest, 'committed ablation tool')
    audit.equal(report['configuration_digest'], fingerprint(config), 'ablation configuration binding')
    bundle = audit.load(directory, 'bundle.json')
    audit.equal(bundle['schema'],'pressure-cost-placement-bundle/v1','ablation bundle schema')
    inventory = bundle['files']
    expected = ['configuration.json', 'report.json', 'comparison.md']
    index = {r['name']: r for r in report['results']}
    checked = calls = 0
    for group, case, budget in matrix(config):
        initial = None
        for policy in POLICIES:
            key = name(case, budget, policy); entry = index[key]; result = entry['result']
            audit.equal((entry['group'],entry['policy']), (group,policy), 'ablation cell identity')
            audit.equal((result['case_id'],result['seed'],result['configuration']),
                        (case['case_id'],case['seed'],budget['name']),'ablation result identity')
            audit.equal(result['variant'], 'B0' if policy == 'B0' else 'B3', 'ablation controller')
            expected.extend(key+'/'+file for file in ('trace.jsonl','admission.db'))
            with ranking_policy(policy):
                checked += audit.audit_run(directory/key, case, budget, result)
            if initial is None: initial = (result['initial_snapshot'], result['initial_candidates'])
            audit.equal((result['initial_snapshot'],result['initial_candidates']), initial, 'matched initial public information')
            rows = [json.loads(line) for line in audit.artifact_path(directory/key, 'trace.jsonl').read_text().splitlines()]
            fields = [r['pressure'] for r in rows if r['stage']=='selection' and r['pressure'] is not None]
            stop = rows[-1]['last_pressure']
            if stop is not None and (not fields or stop != fields[-1]): fields.append(stop)
            # Each evaluated field is rebuilt once; cached stop fields are not an extra call.
            audit.equal(entry['ranking_calls'], len(fields), 'executed ablation ranking path')
            calls += entry['ranking_calls']
    audit.equal(len(index), len(report['results']), 'unique ablation runs')
    audit.equal(len(index), len(list(matrix(config)))*len(POLICIES), 'complete ablation matrix')
    audit.equal(sorted(inventory), sorted(expected), 'ablation artifact inventory')
    for filename,digest in inventory.items():
        audit.equal(sha256(audit.artifact_path(directory, filename).read_bytes()).hexdigest(), digest, 'ablation artifact '+filename)
    audit.equal(report['comparisons'], comparison_rows(report['results']), 'ablation comparisons')
    with TemporaryDirectory() as temporary:
        readable=Path(temporary)/'comparison.md'; write_readable(report,readable)
        audit.equal(audit.artifact_path(directory,'comparison.md').read_text(),readable.read_text(),'ablation readable report')
    return dict(status='PASS', runs=len(index), selections_reproduced=checked, ranking_calls=calls,
        frozen_revision=FROZEN, tool_revision=report['sources']['tool_revision'], elapsed_ns=perf_counter_ns()-start,
        limitation='Trusted evaluator replay, not publisher authentication or historical timing reproduction.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--audit', type=Path)
    args = parser.parse_args()
    if bool(args.output) == bool(args.audit): parser.error('choose --output or --audit')
    if args.audit:
        print(json.dumps(audit_experiment(args.audit))); return
    start = perf_counter_ns(); binding = sources(); config = experiment()
    # Freeze the evaluator extension too: do not publish runs of uncommitted tools.
    blob = subprocess.check_output(['git','show',binding['tool_revision']+':'+TOOL],cwd=audit.ROOT)
    audit.equal(sha256(blob).hexdigest(), binding['tool_files'][TOOL], 'committed ablation tool')
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'configuration.json').write_text(json.dumps(config,indent=2)+'\n')
    results = []
    for cell,(group,case,budget) in enumerate(matrix(config)):
        order = list(POLICIES); offset = cell % len(order); order = order[offset:]+order[:offset]
        for policy in order:
            key = name(case,budget,policy)
            with ranking_policy(policy) as calls:
                result = run_one(case,'B0' if policy=='B0' else 'B3',budget,args.output/key)
            results.append(dict(name=key,group=group,policy=policy,result=result,**calls))
        print(json.dumps(dict(cell=cell+1,case=case['case_id'],budget=budget['name'],runs=len(results))),flush=True)
    report = dict(schema='pressure-cost-placement-results/v1',sources=binding,
        configuration_digest=fingerprint(config),results=results,comparisons=comparison_rows(results),
        experiment_elapsed_ns=perf_counter_ns()-start)
    audit.equal(sources(),binding,'sources changed during ablation')
    (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    write_readable(report,args.output/'comparison.md')
    paths = ['configuration.json','report.json','comparison.md']
    paths += [r['name']+'/'+file for r in results for file in ('trace.jsonl','admission.db')]
    inventory = {name:sha256(audit.artifact_path(args.output,name).read_bytes()).hexdigest() for name in sorted(paths)}
    (args.output/'bundle.json').write_text(json.dumps(dict(schema='pressure-cost-placement-bundle/v1',files=inventory),indent=2)+'\n')
    checked = audit_experiment(args.output)
    (args.output/'audit.json').write_text(json.dumps(checked,indent=2)+'\n')
    print(json.dumps(checked),flush=True)


if __name__ == '__main__':
    main()
