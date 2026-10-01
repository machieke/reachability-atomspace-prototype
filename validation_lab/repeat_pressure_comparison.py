"""Run the frozen B0/B3 comparison twice and check audited semantic repeatability."""
import argparse
from contextlib import closing
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from time import perf_counter_ns

from reachability.codec import loads
from reachability.trace_protocol import canonical, fingerprint, read_json
from .audit_pressure_comparison import (
    ROOT, artifact_path, audit_bundle, equal, load, require, run_name, semantic_snapshot)

SCHEMA = 'pressure-comparison-repeatability/v1'
SELF = Path(__file__).resolve()
RESULT_TIMES = ('costs_ns', 'setup_elapsed_ns', 'evaluation_elapsed_ns',
                'controller_elapsed_ns', 'wall_overrun_ns', 'total_elapsed_ns', 'process_cpu_ns')


def counts(values):
    return {key: value for key, value in values.items() if not key.endswith('_ns')}


def semantic_pressure(field):
    if field is None:
        return None
    result = deepcopy(field)
    # Each bundle audit checks these bindings exactly. Across fresh authorities
    # they include opaque event IDs; retain every numerical/structural field.
    del result['epoch']
    del result['binding']['snapshot']
    for source in result['sources'].values():
        source['observed_relief_events'] = len(source['observed_relief_events'])
    return result


def semantic_result(result):
    value = deepcopy(result)
    for key in RESULT_TIMES:
        del value[key]
    for key in ('setup_costs', 'evaluation_costs'):
        value[key] = counts(value[key])
    for key in ('initial_snapshot', 'controller_stop_snapshot', 'final_snapshot'):
        value[key] = semantic_snapshot(value[key])
    value['last_pressure'] = semantic_pressure(value['last_pressure'])
    return value


def semantic_trace(directory):
    rows = []
    for line in artifact_path(directory, 'trace.jsonl').read_text().splitlines():
        row = read_json(line, max_bytes=8*1024*1024)
        if row['stage'] == 'selection':
            del row['snapshot_digest']
            row['snapshot'] = semantic_snapshot(row['snapshot'])
            row['pressure'] = semantic_pressure(row['pressure'])
        elif row['stage'] == 'receipt':
            row['receipt']['belief'] = row['receipt']['belief'] is not None
            row['receipt']['costs'] = counts(row['receipt']['costs'])
        else:
            row['last_pressure'] = semantic_pressure(row['last_pressure'])
        rows.append(row)
    return rows


def differences(first, second, path='$', *, limit=32):
    """Bounded diagnostic paths; full semantic hashes still bind all differences."""
    if canonical(first) == canonical(second):
        return []
    found = []
    if isinstance(first, dict) and isinstance(second, dict) and first.keys() == second.keys():
        for key in sorted(first):
            found.extend(differences(first[key], second[key], path+'.'+key, limit=limit-len(found)))
            if len(found) >= limit:
                break
    elif isinstance(first, list) and isinstance(second, list) and len(first) == len(second):
        for index, (a, b) in enumerate(zip(first, second)):
            found.extend(differences(a, b, f'{path}[{index}]', limit=limit-len(found)))
            if len(found) >= limit:
                break
    else:
        found.append(path)
    return found


def compare_run(first, second, first_trace, second_trace, mode):
    require(mode in ('matched-operation-work', 'matched-wall-cap'), 'unsupported comparison mode')
    a = dict(result=semantic_result(first), trace=first_trace)
    b = dict(result=semantic_result(second), trace=second_trace)
    changed = differences(a, b)
    limited = any(r['stop_reason'] == 'WALL_BUDGET' or r['wall_overrun_ns'] > 0 for r in (first, second))
    if mode == 'matched-wall-cap':
        status = 'OBSERVED_VARIATION' if changed else 'MATCH'
    elif limited:
        status = 'INCONCLUSIVE'
    else:
        status = 'FAIL' if changed else 'PASS'
    return dict(case_id=first['case_id'], seed=first['seed'], configuration=first['configuration'],
        variant=first['variant'], mode=mode, status=status, semantics_identical=not changed,
        first_semantic_sha256=fingerprint(a), second_semantic_sha256=fingerprint(b),
        difference_paths=changed, difference_path_limit=32,
        reason=('work-limited run reached its wall safety cap' if status == 'INCONCLUSIVE' else None),
        controller_elapsed_ns=[r['controller_elapsed_ns'] for r in (first, second)],
        total_elapsed_ns=[r['total_elapsed_ns'] for r in (first, second)],
        pressure_elapsed_ns=[r['costs_ns']['pressure_construction_ns']+r['costs_ns']['pressure_iteration_ns']
                             for r in (first, second)],
        all_costs_ns=[r['costs_ns'] for r in (first, second)],
        work=[r['work'] for r in (first, second)],
        final_external_loss=[r['final']['external_weighted_loss'] for r in (first, second)],
        integrated_external_loss=[r['integrated_external_loss'] for r in (first, second)],
        second_minus_first_controller_elapsed_ns=second['controller_elapsed_ns']-first['controller_elapsed_ns'])


def authority_ids(directory, report):
    ids = []
    for row in report['results']:
        path = artifact_path(directory/run_name(row), 'admission.db')
        # Completed journals were already audited, including the absence of a
        # pending WAL. Immutable read-only SQLite creates no source sidecars.
        with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro&immutable=1', uri=True)) as database:
            initial = loads(database.execute('SELECT value FROM metadata WHERE id=1').fetchone()[0])['initial']
            ids.append(initial['authority_id'])
    require(len(set(ids)) == len(ids), 'comparison bundle reuses an authority')
    return set(ids)


def compare_bundles(first, second, *, source_commit=None):
    start, own_hash = perf_counter_ns(), sha256(SELF.read_bytes()).hexdigest()
    first, second = Path(first).resolve(), Path(second).resolve()
    require(first != second, 'two distinct comparison bundles required')
    reports = [load(directory, 'report.json') for directory in (first, second)]
    configurations = [load(directory, 'configuration.json') for directory in (first, second)]
    equal(reports[0]['source_files'], reports[1]['source_files'], 'repeat source inputs')
    equal(configurations[0], configurations[1], 'repeat configurations and seeds')
    audits = [audit_bundle(directory, source_commit=source_commit) for directory in (first, second)]
    identities = [authority_ids(directory, report) for directory, report in zip((first, second), reports)]
    require(not identities[0] & identities[1], 'repeat bundles reuse authorities; copied evidence is not a fresh run')
    verified = audits[0]['verified_source_commit']
    if verified:
        committed = subprocess.check_output(['git', 'show', verified+':'+str(SELF.relative_to(ROOT))], cwd=ROOT)
        equal(sha256(committed).hexdigest(), own_hash, 'committed repeatability checker')
    modes = {c['name']: c['mode'] for c in configurations[0]['configurations']}
    indexed = [{run_name(row): row for row in report['results']} for report in reports]
    equal(sorted(indexed[0]), sorted(indexed[1]), 'repeat run matrix')
    comparisons = []
    for name in sorted(indexed[0]):
        a, b = indexed[0][name], indexed[1][name]
        comparisons.append(compare_run(a, b, semantic_trace(first/name), semantic_trace(second/name), modes[a['configuration']]))
    work = [row for row in comparisons if row['mode'] == 'matched-operation-work']
    status = ('FAIL' if any(r['status'] == 'FAIL' for r in work) else
              'INCONCLUSIVE' if any(r['status'] == 'INCONCLUSIVE' for r in work) else 'PASS')
    require(work, 'repeatability needs work-limited runs')
    equal(sha256(SELF.read_bytes()).hexdigest(), own_hash, 'repeatability checker changed during verification')
    return dict(schema=SCHEMA, status=status, bundles=[str(first), str(second)], audits=audits,
        checker_sha256=own_hash, checker_source_revision=subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), verified_source_commit=verified,
        source_files=reports[0]['source_files'], configuration_digest=reports[0]['configuration_digest'],
        seeds=reports[0]['seeds'], distinct_authorities=sum(map(len, identities)), comparisons=comparisons,
        work_limited_matches=sum(r['status'] == 'PASS' for r in work),
        work_limited_failures=sum(r['status'] == 'FAIL' for r in work),
        work_limited_inconclusive=sum(r['status'] == 'INCONCLUSIVE' for r in work),
        wall_limited_variations=sum(r['status'] == 'OBSERVED_VARIATION' for r in comparisons),
        verification_elapsed_ns=perf_counter_ns()-start, charged_to_controllers=False,
        limitations=['two repeats of frozen development episodes; no statistical performance claim',
            'same runtime, audit and evaluator implementations; no independent inference claim',
            'timing and wall-limited differences are reported, not required to match',
            'separate authority IDs reject reused evidence, not provide execution attestation',
            'transport/M12, generalized recovery and broader benchmark scope remain deferred'])


def write_readable(report, path):
    lines = ['# B0/B3 fresh-run repeatability', '', f"Status: **{report['status']}**.", '']
    if 'error' in report:
        lines += [report['error'], '']
    else:
        lines += [f"Work-limited matches: {report['work_limited_matches']}; failures: {report['work_limited_failures']}; "
                  f"inconclusive: {report['work_limited_inconclusive']}. Wall-limited variations: {report['wall_limited_variations']}.", '',
            '| Episode | Seed | Budget | Controller | Result | Integrated loss 1 / 2 | Controller ms 1 / 2 |',
            '| --- | ---: | --- | --- | --- | --- | --- |']
        for row in report['comparisons']:
            loss = ' / '.join(f'{v:g}' for v in row['integrated_external_loss'])
            elapsed = ' / '.join(f'{v/1e6:.2f}' for v in row['controller_elapsed_ns'])
            lines.append(f"| {row['case_id']} | {row['seed']} | {row['configuration']} | {row['variant']} | {row['status']} | {loss} | {elapsed} |")
        lines += ['', 'Work-limited equality covers selections, ranks, pressure diagnostics, snapshots, work counters, '
            'rejections, outcome histories and stopping behavior after audited identifier/timing normalization. '
            'A reached wall safety cap makes a work-limited comparison inconclusive. Wall-limited variation '
            'does not establish a defect or a controller advantage.', '',
            'Both input bundles are audited before comparison. Verification cost is separate from controller '
            'cost; complete times, deltas, semantic hashes and bounded difference paths are in repeatability.json. '
            'Two repeats provide development repeatability evidence, not statistical significance or scaling evidence.', '']
    path.write_text('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='new output directory')
    parser.add_argument('--bundles', type=Path, nargs=2, help='audit and compare two existing bundles instead of generating them')
    parser.add_argument('--seeds', type=int, nargs='+', help='fresh-run seeds (default: 7 18); cannot be combined with --bundles')
    parser.add_argument('--source-commit', help='also bind comparison and checker sources to this commit')
    args = parser.parse_args()
    if args.bundles and args.seeds is not None:
        parser.error('--seeds applies only to fresh runs')
    seeds = args.seeds if args.seeds is not None else [7, 18]
    if not 1 <= len(seeds) <= 8 or len(set(seeds)) != len(seeds) or any(not 0 <= s < 2**32 for s in seeds):
        parser.error('one to eight distinct uint32 seeds required')
    if args.bundles and any(args.output.resolve().is_relative_to(p.resolve()) for p in args.bundles):
        parser.error('output must be outside the input bundles')
    args.output.mkdir(parents=True, exist_ok=False)
    start, attempts = perf_counter_ns(), []
    own_hash = sha256(SELF.read_bytes()).hexdigest()
    try:
        directories = args.bundles or [args.output/f'repeat-{i}' for i in (1, 2)]
        if not args.bundles:
            for index, directory in enumerate(directories, 1):
                command = [sys.executable, '-m', 'validation_lab.run_pressure_comparison', '--output', str(directory.resolve()),
                           '--seeds', *map(str, seeds)]
                clock = perf_counter_ns()
                with (args.output/f'repeat-{index}.log').open('x') as log:
                    process = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
                attempts.append(dict(repeat=index, command=command, returncode=process.returncode,
                                     elapsed_ns=perf_counter_ns()-clock))
                require(process.returncode == 0, f'comparison repeat {index} failed; see repeat-{index}.log')
                print(json.dumps(dict(stage='comparison-complete', repeat=index)), flush=True)
        report = compare_bundles(*directories, source_commit=args.source_commit)
        equal(sha256(SELF.read_bytes()).hexdigest(), own_hash, 'repeatability checker changed during experiment')
    except Exception as error:
        report = dict(schema=SCHEMA, status='FAIL', error_type=type(error).__name__, error=str(error))
    report.update(attempts=attempts, total_experiment_elapsed_ns=perf_counter_ns()-start)
    (args.output/'repeatability.json').write_text(json.dumps(report, indent=2)+'\n')
    write_readable(report, args.output/'repeatability.md')
    print(json.dumps(dict(status=report['status'], output=str(args.output))), flush=True)
    raise SystemExit({'PASS': 0, 'FAIL': 1, 'INCONCLUSIVE': 2}[report['status']])


if __name__ == '__main__':
    main()
