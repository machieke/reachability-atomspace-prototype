"""Source-bound raw/normalized projection comparison; frozen benchmark untouched."""
import argparse
from collections import Counter, defaultdict
from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path
import platform
import subprocess
from tempfile import TemporaryDirectory
from time import perf_counter_ns

from experimental_pressure.ranking import rank_projected
from reachability import pressure_controller as controller
from reachability.trace_protocol import canonical, fingerprint
from . import audit_pressure_comparison as audit
from .pressure_cost_ablation import FROZEN, POLICIES as COSTS, rank_cost, sources as frozen_sources
from .pressure_episodes import episodes
from .projection_cases import diagnostic_cases
from .run_pressure_comparison import configurations, run_one

POLICIES = list(COSTS)+['B3-normalized-'+suffix for suffix in ('both','route','queue','neither')]
TOOL_FILES = ['experimental_pressure/__init__.py', 'experimental_pressure/projection.py',
    'experimental_pressure/ranking.py', 'validation_lab/pressure_cost_ablation.py',
    'validation_lab/projection_cases.py', 'validation_lab/projection_comparison.py',
    'tests/test_pressure_projection.py', 'tests/test_projection_comparison.py',
    'reviews/pressure-projection-v1/PROTOCOL.md', 'pyproject.toml']


@contextmanager
def ranking_policy(policy):
    if policy not in POLICIES: raise ValueError('unsupported projection policy')
    previous = controller.rank_b3, audit.rank_b3
    metrics = dict(ranking_calls=0, normalization_ns=0, graph_ns=0,
                   normalization_visits=0, projected_occurrences=0)
    evaluations = []
    def rank(*args):
        metrics['ranking_calls'] += 1
        before = dict(metrics)
        if policy.startswith('B3-normalized-'):
            routing, queue = COSTS[policy.replace('normalized', 'cost')]
            result = rank_projected(*args, routing_cost=routing, queue_cost=queue, metrics=metrics)
        else:
            result = rank_cost(*args, policy)
            metrics['graph_ns'] += result[2]
        evaluations.append(dict(epoch=result[1]['epoch'],
            normalization_ns=metrics['normalization_ns']-before['normalization_ns'],
            graph_ns=metrics['graph_ns']-before['graph_ns'], iteration_ns=result[3],
            normalization_visits=metrics['normalization_visits']-before['normalization_visits'],
            projected_occurrences=metrics['projected_occurrences']-before['projected_occurrences']))
        return result
    try:
        if policy != 'B0': controller.rank_b3 = audit.rank_b3 = rank
        yield dict(metrics=metrics, evaluations=evaluations)
    finally:
        controller.rank_b3, audit.rank_b3 = previous


def experiment():
    return dict(schema='representation-projection/v1', frozen_revision=FROZEN,
        policies=POLICIES, seeds=[7,18], training_runs=0,
        frozen_cases=[case for seed in (7,18) for case in episodes(seed)],
        frozen_configurations=configurations(), diagnostic_cases=diagnostic_cases(),
        diagnostic_configurations=[configurations()[0]],
        duration_model='unchanged: one request advances one tick, cost separately charges operation work',
        pressure_gamma=.85, numerical_floor=1e-12,
        interpretation='Experimental Boolean syntax invariance only; no policy promotion or general superiority claim.')


def matrix(config):
    for group in ('frozen', 'diagnostic'):
        for case in config[group+'_cases']:
            for budget in config[group+'_configurations']: yield group, case, budget


def sources():
    base = frozen_sources()
    return dict(frozen_revision=FROZEN, frozen_files=base['frozen_files'],
        tool_revision=base['tool_revision'],
        tool_files={name:sha256((audit.ROOT/name).read_bytes()).hexdigest() for name in TOOL_FILES})


def verify_sources(binding):
    current = sources()
    for key in ('frozen_revision','frozen_files','tool_files'):
        audit.equal(binding[key], current[key], 'projection source '+key)
    revision = subprocess.check_output(['git','rev-parse','--verify','--end-of-options',
        binding['tool_revision']+'^{commit}'],cwd=audit.ROOT,text=True).strip()
    audit.equal(revision, binding['tool_revision'], 'complete committed source revision')
    for name,digest in binding['tool_files'].items():
        blob = subprocess.check_output(['git','show',revision+':'+name],cwd=audit.ROOT)
        audit.equal(sha256(blob).hexdigest(), digest, 'committed projection file '+name)


def name(case, budget, policy):
    return f"{case['case_id']}-{case['seed']}-{budget['name']}-{policy}"


def trace(directory, entry):
    return [json.loads(line) for line in audit.artifact_path(directory,entry['name']+'/trace.jsonl').read_text().splitlines()]


def evaluated_fields(rows):
    fields = [row['pressure'] for row in rows if row['stage']=='selection' and row['pressure'] is not None]
    final = rows[-1]['last_pressure']
    if final is not None and (not fields or final != fields[-1]): fields.append(final)
    return fields


def source_semantics(field):
    accounts = json.loads(canonical(field['sources']))
    for source in accounts.values():
        source['observed_relief_events'] = len(source['observed_relief_events'])
    return accounts


def primary_ties(row):
    if row['pressure'] is None: return []
    allowance = 2*row['pressure']['error_bound_l1']+1e-12
    values = sorted((value[0], key) for key,value in row['ranks'].items())
    return [dict(candidates=[left[1],right[1]], gap=abs(left[0]-right[0]), allowance=allowance)
        for i,left in enumerate(values) for right in values[i+1:] if abs(left[0]-right[0]) <= allowance]


def compare_fields(left, right, *, all_nodes):
    same_sources = source_semantics(left)==source_semantics(right)
    delta, allowed, count = 0., left['error_bound_l1']+right['error_bound_l1']+1e-12, 0
    valid = set(left['fields']) == set(right['fields'])
    for source in set(left['fields']) & set(right['fields']):
        a, b = left['fields'][source]['values'], right['fields'][source]['values']
        if not all_nodes:
            a = {k:v for k,v in a.items() if not k.startswith('requirement:')}
            b = {k:v for k,v in b.items() if not k.startswith('requirement:')}
        valid &= set(a)==set(b)
        for key in set(a) & set(b):
            delta = max(delta, abs(a[key]-b[key])); count += 1
    return dict(source_accounting_equal=same_sources, nodes_equal=bool(valid), compared_values=count,
        max_absolute_difference=delta, allowance=allowed,
        pressure_equal=bool(valid and delta<=allowed))


def semantic_checks(directory, results, config):
    cases = {c['case_id']:c for c in config['diagnostic_cases']}
    groups = defaultdict(list)
    for entry in results:
        if entry['group'] != 'diagnostic' or entry['policy']=='B0': continue
        group = cases[entry['result']['case_id']]['diagnostic'].get('equivalence_group')
        if group: groups[group,entry['policy']].append(entry)
    checks = []
    for (group,policy), entries in sorted(groups.items()):
        base = next(e for e in entries if e['result']['case_id'].endswith('-base') or
                    e['result']['case_id'].startswith('depth-0-'))
        first = [r for r in trace(directory,base) if r['stage']=='selection']
        for entry in entries:
            if entry is base: continue
            rows = [r for r in trace(directory,entry) if r['stage']=='selection']
            normalized = policy.startswith('B3-normalized-')
            # Raw trajectories can diverge: only initial public state is matched.
            pairs = list(zip(first,rows)) if normalized else list(zip(first[:1],rows[:1]))
            comparisons = [compare_fields(a['pressure'],b['pressure'],all_nodes=normalized) for a,b in pairs]
            candidate_match = all(a['candidates']==b['candidates'] for a,b in pairs)
            rank_match = all(set(a['ranks'])==set(b['ranks']) and all(
                abs(a['ranks'][key][0]-b['ranks'][key][0]) <= comparison['allowance'] and
                a['ranks'][key][1:]==b['ranks'][key][1:] for key in a['ranks'])
                for (a,b),comparison in zip(pairs,comparisons))
            checks.append(dict(group=group,policy=policy,base=base['name'],transformed=entry['name'],
                snapshots_compared=len(pairs), complete_trajectory=normalized and len(first)==len(rows),
                candidates_equal=candidate_match, rankings_equal=rank_match,
                source_accounting_equal=all(c['source_accounting_equal'] for c in comparisons),
                pressure_equal=all(c['pressure_equal'] for c in comparisons),
                max_absolute_difference=max((c['max_absolute_difference'] for c in comparisons),default=0.),
                choices_equal=base['result']['selected']==entry['result']['selected'],
                outcomes_equal=base['result']['outcomes']==entry['result']['outcomes'],
                comparisons=comparisons,
                unresolved_primary_ties=[dict(step=row['step'],pairs=primary_ties(row)) for row in rows if primary_ties(row)]))
    return checks


def comparisons(results):
    index = {(e['group'],e['result']['case_id'],e['result']['seed'],e['result']['configuration'],e['policy']):e for e in results}
    rows = []
    for entry in results:
        r = entry['result']; prefix = (entry['group'],r['case_id'],r['seed'],r['configuration'])
        refs = ['B0','B3-cost-both']
        if entry['policy'].startswith('B3-normalized-'): refs.append(entry['policy'].replace('normalized','cost'))
        for reference in sorted(set(refs)-{entry['policy']}):
            base = index[prefix+(reference,)]['result']
            delta = r['integrated_external_loss']-base['integrated_external_loss']
            rows.append(dict(group=entry['group'],case_id=r['case_id'],seed=r['seed'],configuration=r['configuration'],
                policy=entry['policy'],reference=reference,integrated_loss_delta=delta,
                final_loss_delta=r['final']['external_weighted_loss']-base['final']['external_weighted_loss'],
                operation_work_delta=r['work']['operation_work']-base['work']['operation_work'],
                classification='favorable' if delta<0 else 'unfavorable' if delta>0 else 'neutral'))
    return rows


def write_readable(report, path):
    lines = ['# Experimental requirement projection', '',
        f"Frozen runtime: `{FROZEN}`. Experimental source: `{report['sources']['tool_revision']}`.", '',
        'Original benchmark unchanged. Nine policies share candidate discovery, budgets and certified execution.',
        'No ablation is promoted. Wall caps and measured runtime vary with host load; one run per cell.', '',
        '| Group | Case | Seed | Budget | Policy | Integrated loss | Final loss | Requests | Op work | Normalize ms | Graph ms | Solve ms | Controller ms | Total ms |',
        '| --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for e in report['results']:
        r,m = e['result'],e['metrics']
        lines.append(f"| {e['group']} | {r['case_id']} | {r['seed']} | {r['configuration']} | {e['policy']} | "
            f"{r['integrated_external_loss']:g} | {r['final']['external_weighted_loss']:g} | {r['work']['actions']} | "
            f"{r['work']['operation_work']} | {m['normalization_ns']/1e6:.3f} | {m['graph_ns']/1e6:.3f} | "
            f"{r['costs_ns']['pressure_iteration_ns']/1e6:.3f} | {r['controller_elapsed_ns']/1e6:.3f} | {r['total_elapsed_ns']/1e6:.3f} |")
    lines += ['', '## Semantic checks', '',
        '| Family | Policy | Pairs | Pressure invariant | Full choices invariant | External outcomes invariant |',
        '| --- | --- | ---: | ---: | ---: | ---: |']
    grouped = defaultdict(list)
    for c in report['semantic_checks']: grouped[c['group'],c['policy']].append(c)
    for (family,policy),checks in sorted(grouped.items()):
        lines.append(f"| {family} | {policy} | {len(checks)} | {sum(c['pressure_equal'] for c in checks)} | "
            f"{sum(c['choices_equal'] for c in checks)} | {sum(c['outcomes_equal'] for c in checks)} |")
    lines += ['', 'Unresolved primary-score ties and numerical allowances are explicit in report.json. Common cost/identity tie-breaks remain active.',
        'Normalized pairs compare every selected snapshot; raw pairs compare pressure only at the common initial state and retain actual closed-loop divergence.',
        'Source accounting ignores only opaque relief-event identifiers when comparing different authorities; each run retains and audits its exact provenance.',
        'Normalization plus graph time equals inclusive pressure construction; do not add these twice. Discovery, inference, certification, persistence and unmeasured costs are retained per run.',
        'All favorable, neutral and unfavorable loss comparisons remain in report.json. No general performance superiority is claimed.', '']
    path.write_text('\n'.join(lines))


def audit_experiment(directory):
    directory = Path(directory); start = perf_counter_ns()
    report,config = audit.load(directory,'report.json'),audit.load(directory,'configuration.json')
    audit.equal(config,experiment(),'projection experiment')
    audit.equal(report['schema'],'representation-projection-results/v1','projection results schema')
    verify_sources(report['sources'])
    audit.equal(report['configuration_digest'],fingerprint(config),'projection configuration binding')
    bundle = audit.load(directory,'bundle.json')
    audit.equal(bundle['schema'],'representation-projection-bundle/v1','projection bundle schema')
    expected = ['configuration.json','report.json','comparison.md']
    index = {e['name']:e for e in report['results']}
    checked = ranking_calls = 0
    for group,case,budget in matrix(config):
        initial = None
        for policy in POLICIES:
            key = name(case,budget,policy); entry = index[key]; result = entry['result']
            audit.equal((entry['group'],entry['policy']),(group,policy),'projection cell identity')
            audit.equal((result['case_id'],result['seed'],result['configuration'],result['variant']),
                (case['case_id'],case['seed'],budget['name'],'B0' if policy=='B0' else 'B3'),'projection run identity')
            with ranking_policy(policy): checked += audit.audit_run(directory/key,case,budget,result)
            if initial is None: initial = (result['initial_snapshot'],result['initial_candidates'])
            audit.equal((result['initial_snapshot'],result['initial_candidates']),initial,'common initial information')
            fields = evaluated_fields(trace(directory,entry)); metrics = entry['metrics']; evaluations = entry['evaluations']
            audit.equal(metrics['ranking_calls'],len(fields),'live ranking invocation count')
            audit.equal([e['epoch'] for e in evaluations],[f['epoch'] for f in fields],'evaluated projection epochs')
            ranking_calls += len(fields)
            for key_metric in ('normalization_ns','graph_ns','normalization_visits','projected_occurrences'):
                audit.equal(metrics[key_metric],sum(e[key_metric] for e in evaluations),'ranking cost '+key_metric)
            for e in evaluations:
                audit.nonnegative_counts({k:v for k,v in e.items() if k!='epoch'}, 'projection measured costs')
            audit.equal(metrics['normalization_ns']+metrics['graph_ns'],result['costs_ns']['pressure_construction_ns'],
                        'charged projection construction')
            audit.equal(sum(e['iteration_ns'] for e in evaluations),result['costs_ns']['pressure_iteration_ns'],'charged solve')
            normalized = policy.startswith('B3-normalized-')
            for field,e in zip(fields,evaluations):
                audit.equal('projection' in field['binding'],normalized,'executed projection variant')
                work = field['binding']['projection']['work'] if normalized else dict(visits=0,projected=0)
                audit.equal((e['normalization_visits'],e['projected_occurrences']),(work['visits'],work['projected']),
                            'normalization work accounting')
                if not normalized: audit.equal(e['normalization_ns'],0,'raw normalization cost')
            expected.extend(entry['name']+'/'+file for file in ('trace.jsonl','admission.db'))
    audit.equal(len(index),len(report['results']),'unique projection run identities')
    audit.equal(len(index),len(list(matrix(config)))*len(POLICIES),'complete projection matrix')
    audit.equal(sorted(bundle['files']),sorted(expected),'complete projection inventory')
    for filename,digest in bundle['files'].items():
        audit.equal(sha256(audit.artifact_path(directory,filename).read_bytes()).hexdigest(),digest,'projection artifact '+filename)
    audit.equal(report['comparisons'],comparisons(report['results']),'projection outcome comparisons')
    checks = semantic_checks(directory,report['results'],config)
    audit.equal(report['semantic_checks'],checks,'projection semantic comparisons')
    for check in checks:
        if check['policy'].startswith('B3-normalized-'):
            for key in ('complete_trajectory','candidates_equal','rankings_equal','source_accounting_equal',
                        'pressure_equal','choices_equal','outcomes_equal'):
                audit.require(check[key],'failed normalized invariance: '+key+' '+check['transformed'])
    with TemporaryDirectory() as temporary:
        path = Path(temporary)/'comparison.md'; write_readable(report,path)
        audit.equal(audit.artifact_path(directory,'comparison.md').read_text(),path.read_text(),'readable projection report')
    return dict(status='PASS',runs=len(index),selections_reproduced=checked,ranking_calls=ranking_calls,
        normalized_equivalence_pairs=sum(c['policy'].startswith('B3-normalized-') for c in checks),
        frozen_revision=FROZEN,tool_revision=report['sources']['tool_revision'],elapsed_ns=perf_counter_ns()-start,
        limitation='Trusted evaluator replay, not publisher authentication or historical timing reproduction.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path); parser.add_argument('--audit',type=Path)
    args = parser.parse_args()
    if bool(args.output)==bool(args.audit): parser.error('choose --output or --audit')
    if args.audit: print(json.dumps(audit_experiment(args.audit))); return
    start = perf_counter_ns(); binding = sources(); verify_sources(binding); config = experiment()
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'configuration.json').write_text(json.dumps(config,indent=2)+'\n')
    results = []
    for cell,(group,case,budget) in enumerate(matrix(config)):
        offset = cell%len(POLICIES); order = POLICIES[offset:]+POLICIES[:offset]
        for policy in order:
            key = name(case,budget,policy)
            with ranking_policy(policy) as measured:
                result = run_one(case,'B0' if policy=='B0' else 'B3',budget,args.output/key)
            results.append(dict(name=key,group=group,policy=policy,result=result,**measured))
        print(json.dumps(dict(cell=cell+1,case=case['case_id'],budget=budget['name'],runs=len(results))),flush=True)
    report = dict(schema='representation-projection-results/v1',sources=binding,
        configuration_digest=fingerprint(config),python=platform.python_version(),platform=platform.platform(),
        results=results,comparisons=comparisons(results),semantic_checks=semantic_checks(args.output,results,config),
        experiment_elapsed_ns=perf_counter_ns()-start)
    audit.equal(sources(),binding,'projection sources changed during run')
    (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    write_readable(report,args.output/'comparison.md')
    paths = ['configuration.json','report.json','comparison.md']
    paths += [e['name']+'/'+file for e in results for file in ('trace.jsonl','admission.db')]
    inventory = {name:sha256(audit.artifact_path(args.output,name).read_bytes()).hexdigest() for name in sorted(paths)}
    (args.output/'bundle.json').write_text(json.dumps(dict(schema='representation-projection-bundle/v1',files=inventory),indent=2)+'\n')
    checked = audit_experiment(args.output)
    (args.output/'audit.json').write_text(json.dumps(checked,indent=2)+'\n')
    print(json.dumps(checked),flush=True)


if __name__=='__main__': main()
