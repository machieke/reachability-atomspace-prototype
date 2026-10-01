"""Reproduce the bounded B0/B3 development comparison and its M09 witness."""
import argparse
from collections import Counter
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import platform
import subprocess
from time import perf_counter_ns, process_time_ns

from reachability.pressure import PressureLimits
from reachability.pressure_controller import ComparisonBudget, ComparisonController, rank_b3
from reachability.pressure_session import ReasoningSession
from reachability.pressure_work import b0_ranking, enumerate_work
from reachability.trace_protocol import canonical, fingerprint
from .pressure_episodes import ReasoningWorld, episodes
from .pressure_reference import mutation_witness

ROOT = Path(__file__).resolve().parents[1]


def configurations():
    # Frozen before comparative results: equal operation/observation work and
    # equal wall caps within each pair. No training or controller-specific tuning.
    return [dict(name='work-8', mode='matched-operation-work', budget=asdict(ComparisonBudget(actions=8, operation_work=16))),
            dict(name='work-16', mode='matched-operation-work', budget=asdict(ComparisonBudget())),
            dict(name='time-100ms', mode='matched-wall-cap', budget=asdict(ComparisonBudget(actions=16, operation_work=128, observation_work=64, wall_ns=100_000_000))),
            dict(name='time-500ms', mode='matched-wall-cap', budget=asdict(ComparisonBudget(actions=16, operation_work=128, observation_work=64, wall_ns=500_000_000)))]


def run_one(case, variant, config, output, *, limits=PressureLimits()):
    output.mkdir(parents=True)
    start, cpu_start = perf_counter_ns(), process_time_ns()
    stream = (output/'trace.jsonl').open('w')
    def emit(row):
        stream.write(canonical(row)+'\n'); stream.flush()
    try:
        with ReasoningSession(case['public'], output) as session:
            world = ReasoningWorld(session, case)
            initial = session.read()
            initial_candidates = [c.wire() for c in enumerate_work(case['public'], initial).candidates]
            world.sample_outcomes()
            setup_costs = dict(session.metrics.values)
            setup_ns = perf_counter_ns()-start
            result = ComparisonController(case['public'], variant, limits=limits).run(world.port(),
                ComparisonBudget(**config['budget']), emit=emit)
            stop_snapshot = session.read()
            metrics = {key: value-setup_costs[key] for key, value in session.metrics.values.items()}
            evaluation_start, before_evaluation = perf_counter_ns(), dict(session.metrics.values)
            # Every pair uses the same sixteen-tick outcome horizon. After its
            # budget stops, the controller gets no free work or observations.
            world.idle_until(16)
            final = world.sample_outcomes()
            snapshot = session.read()
            evaluation_ns = perf_counter_ns()-evaluation_start
            evaluation_costs = {key: value-before_evaluation[key] for key, value in session.metrics.values.items()}
            # All authoritative commands, exact certificates and support IDs are
            # retained in admission.db, independently replayable by the service.
            journal_tip = session.service._journal_sequence
        states = world.outcomes[:-1]
        integrated = sum(row['external_weighted_loss'] for row in states)
        failures = Counter(r['receipt']['status'] for r in result['records'] if r['receipt']['status'] != 'PASS')
        timing = dict(result['costs'], **{k: v for k, v in metrics.items() if k.endswith('_ns')})
        # Execution includes authority categories; it must not be added to them.
        measured_exclusive = sum(timing[k] for k in ('snapshot_ns', 'candidate_discovery_ns', 'ranking_ns',
            'pressure_construction_ns', 'pressure_iteration_ns', 'inference_ns', 'certification_ns',
            'persistence_ns', 'authority_other_ns'))
        timing['other_controller_ns'] = max(0, result['total_elapsed_ns']-measured_exclusive)
        return dict(case_id=case['case_id'], seed=case['seed'], variant=variant, configuration=config['name'],
            status='PASS', stop_reason=result['stop_reason'], budget=config['budget'], pressure_limits=asdict(limits),
            initial_snapshot=initial, initial_candidates=initial_candidates,
            selected=[dict(kind=r['selected']['kind'], arguments=r['selected']['arguments'], status=r['receipt']['status']) for r in result['records']],
            ranking_paths=sorted({r['ranking_path'] for r in result['records']}),
            outcomes=world.outcomes, final=final, integrated_external_loss=integrated,
            environment_events=world.events, failures=dict(failures), final_snapshot=snapshot,
            controller_stop_snapshot=stop_snapshot, evaluation_horizon=16,
            evaluation_elapsed_ns=evaluation_ns, evaluation_costs=evaluation_costs,
            work=dict(result['work'], **{k: v for k, v in metrics.items() if not k.endswith('_ns')}),
            costs_ns=timing, setup_costs=setup_costs, setup_elapsed_ns=setup_ns,
            controller_elapsed_ns=result['total_elapsed_ns'], wall_overrun_ns=result['wall_overrun_ns'],
            total_elapsed_ns=perf_counter_ns()-start, process_cpu_ns=process_time_ns()-cpu_start,
            pressure_converged=(all(r['pressure']['converged'] for r in result['records'] if r['pressure'])
                               and (result['last_pressure'] is None or result['last_pressure']['converged'])),
            pressure_exhausted=[e for r in result['records'] if r['pressure'] for e in r['pressure']['exhausted']],
            last_pressure=result['last_pressure'],
            journal_commands_total=journal_tip,
            unmeasured_costs=['peak memory', 'GPU (unused)', 'OS scheduling attribution',
                'individual SQLite bytes/fsync latency (append+commit time measured)',
                'setup category split before journal timing hook', 'real external sensor latency (simulated)'])
    finally:
        stream.close()


def fairness_audit(directory, public):
    """Recompute every recorded frontier with shared code, independent of rank."""
    checked = 0
    for line in (directory/'trace.jsonl').read_text().splitlines():
        row = json.loads(line)
        if row['stage'] != 'selection':
            continue
        actual = [c.wire() for c in enumerate_work(public, row['snapshot']).candidates]
        if actual != row['candidates'] or row['snapshot_digest'] != fingerprint(row['snapshot']):
            raise AssertionError('candidate frontier is not the common public snapshot frontier')
        if row['selected'] not in actual:
            raise AssertionError('selected operation is not a public candidate')
        checked += 1
    return checked


def isolate_ranking(public, snapshot):
    """Same frozen input and candidates; diagnostics never feed a controller."""
    candidates = enumerate_work(public, snapshot).candidates
    start = perf_counter_ns()
    b0, work, complete = b0_ranking(public, snapshot, candidates)
    b0_ns = perf_counter_ns()-start
    start = perf_counter_ns()
    b3, field, construction, iteration = rank_b3(public, snapshot, candidates, PressureLimits())
    b3_ns = perf_counter_ns()-start
    if not complete:
        raise AssertionError('initial ranking isolation exhausted B0 budget')
    return dict(snapshot=snapshot, snapshot_digest=fingerprint(snapshot), candidates=[c.wire() for c in candidates],
        B0=dict(selected=min(candidates, key=lambda c:b0[c.candidate_id]).wire(), ranks=b0,
                path='b0-conditional-plan-best-first', work=work, elapsed_ns=b0_ns),
        B3=dict(selected=min(candidates, key=lambda c:b3[c.candidate_id]).wire(), ranks=b3,
                path='b3-typed-pressure-priority-queue', pressure=field, construction_ns=construction,
                iteration_ns=iteration, elapsed_ns=b3_ns),
        charged_to_episode=False, scope='separate identical-snapshot diagnostic, no execution')


def write_comparison(report, path):
    lines = ['# Bounded B0 versus B3 comparison', '',
        'Development episodes only; no transport, learning, full benchmark or scaling claim.', '',
        f"Source revision: `{report['source_revision']}`. Seeds: {report['seeds']}. No tuning runs.", '',
        'Both controllers use the same public candidates, operation capabilities and certified authority. '
        'B0 performs best-first conditional planning; B3 uses typed pressure and a direct priority queue.', '',
        '| Episode | Seed | Budget | Controller | External loss | Certified loss | Integrated loss | Requests | Total ms | Pressure ms | Stop |',
        '| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |']
    for row in report['results']:
        if row['status'] != 'PASS':
            lines.append(f"| {row['case_id']} | {row['seed']} | {row['configuration']} | {row['variant']} | FAIL | | | | | | {row['error']} |")
            continue
        cost = row['costs_ns']
        lines.append(f"| {row['case_id']} | {row['seed']} | {row['configuration']} | {row['variant']} | "
            f"{row['final']['external_weighted_loss']:g} | {row['final']['certified_weighted_loss']:g} | "
            f"{row['integrated_external_loss']:g} | {row['work']['actions']} | {row['total_elapsed_ns']/1e6:.2f} | "
            f"{(cost['pressure_construction_ns']+cost['pressure_iteration_ns'])/1e6:.2f} | {row['stop_reason']} |")
    lines += ['', 'Integrated loss uses fixed evaluation weights over the same sixteen logical ticks. After '
        'a controller stops, exogenous support changes still happen, but it receives no free work '
        'or observations. This is a bounded development comparison, not optimal regret or statistical generalization.', '',
        'The separate ranking-isolation.json artifact feeds both rankings the identical snapshot '
        'and candidate list. Its diagnostic cost is recorded separately and cannot affect episode selection.', '',
        'Timing includes candidate discovery, pressure construction/iteration, ranking, actual inference, '
        'certification/commit checks, SQLite append/commit persistence and total elapsed time. Detailed '
        'counts and category times are in report.json. Execution is an inclusive diagnostic and must not '
        'be summed with its authority components. Setup, evaluation-tail cost, CPU time and atomic-operation wall overruns '
        'are reported separately. Wall-limited results vary with machine load; semantic work-limited '
        'runs are deterministic apart from authority IDs and timing.', '',
        'Unmeasured: peak memory, individual fsync/byte attribution, OS scheduling attribution and '
        'real sensor latency. No GPU is used. Environment outcomes and trace-writing overhead are '
        'included in elapsed time but not separately profiled.', '',
        f"M09 detected: **{report['m09']['detected']}**. M12 remains deferred with transport.", '',
        'Neutral or worse B3 outcomes are retained. The simple control should have identical operations '
        'and relief; pressure overhead can make it slower. No result here establishes an empirical '
        'advantage, calibrated success probability, or family-complete validation.', '']
    path.write_text('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'artifacts/pressure-comparison')
    parser.add_argument('--seeds', nargs='+', type=int, default=[7, 18])
    args = parser.parse_args()
    if not 1 <= len(args.seeds) <= 8 or len(set(args.seeds)) != len(args.seeds) or any(not 0 <= s < 2**32 for s in args.seeds):
        parser.error('one to eight distinct uint32 seeds required')
    args.output.mkdir(parents=True, exist_ok=False)
    files = [*sorted((ROOT/'reachability').glob('*.py')),
        *[ROOT/'validation_lab'/name for name in ('run_pressure_comparison.py', 'pressure_episodes.py', 'pressure_reference.py')],
        *[ROOT/name for name in ('reachability_atomspace_specification.md', 'pressure_field_pln_lifecycle_integration.md',
                                'reachability_validation_design/benchmark_design.md')]]
    source_revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    cases = [case for seed in args.seeds for case in episodes(seed)]
    configs = configurations()
    (args.output/'configuration.json').write_text(json.dumps(dict(configurations=configs, episodes=cases), indent=2)+'\n')
    results, audits = [], 0
    for index, case in enumerate(cases):
        for config in configs:
            # Alternate pair order; no implicit warm-cache advantage for B0.
            for variant in (('B0', 'B3') if index % 2 == 0 else ('B3', 'B0')):
                directory = args.output/f"{case['case_id']}-{case['seed']}-{config['name']}-{variant}"
                try:
                    result = run_one(case, variant, config, directory)
                    audits += fairness_audit(directory, case['public'])
                except Exception as error:
                    result = dict(case_id=case['case_id'], seed=case['seed'], configuration=config['name'], variant=variant,
                                  status='FAIL', error_type=type(error).__name__, error=str(error))
                results.append(result)
    report = dict(schema='b0-b3-comparison/v1', source_revision=source_revision,
        source_files={str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest() for path in files},
        working_tree=subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).splitlines(),
        python=platform.python_version(), platform=platform.platform(), seeds=args.seeds,
        configuration_digest=fingerprint(dict(configurations=configs, episodes=cases)),
        results=results, candidate_frontiers_audited=audits, m09=mutation_witness(),
        evaluator_process_isolation=False, family_complete_fixtures=0, transport=False, training_runs=0,
        unimplemented=['adaptive activation transport', 'learned conductance', 'act/expand/retain channels',
                       'generalized recovery', 'numerical PLN scheduling', 'full benchmark', 'M12'])
    isolation = []
    for case in cases:
        pair = [r for r in results if r['case_id'] == case['case_id'] and r['seed'] == case['seed']
                and r['configuration'] == 'work-16' and r['status'] == 'PASS']
        if len(pair) == 2:
            if pair[0]['initial_snapshot'] != pair[1]['initial_snapshot'] or pair[0]['initial_candidates'] != pair[1]['initial_candidates']:
                raise AssertionError('paired initial public information differs')
            isolation.append(dict(case_id=case['case_id'], seed=case['seed'], **isolate_ranking(case['public'], pair[0]['initial_snapshot'])))
    report['ranking_isolation_cases'] = len(isolation)
    report['pairs'] = []
    for case in cases:
        for config in configs:
            pair = {r['variant']: r for r in results if r['case_id'] == case['case_id'] and r['seed'] == case['seed']
                    and r['configuration'] == config['name'] and r['status'] == 'PASS'}
            if set(pair) == {'B0', 'B3'}:
                b0, b3 = pair['B0'], pair['B3']
                report['pairs'].append(dict(case_id=case['case_id'], seed=case['seed'], configuration=config['name'],
                    B3_minus_B0_integrated_external_loss=b3['integrated_external_loss']-b0['integrated_external_loss'],
                    B3_minus_B0_final_external_loss=b3['final']['external_weighted_loss']-b0['final']['external_weighted_loss'],
                    B3_minus_B0_controller_elapsed_ns=b3['controller_elapsed_ns']-b0['controller_elapsed_ns'],
                    initial_candidates_identical=b0['initial_candidates'] == b3['initial_candidates']))
    (args.output/'ranking-isolation.json').write_text(json.dumps(isolation, indent=2)+'\n')
    (args.output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    write_comparison(report, args.output/'comparison.md')
    print(json.dumps(dict(runs=len(results), passed=sum(r['status'] == 'PASS' for r in results),
        candidate_frontiers_audited=audits, m09=report['m09']['detected'], output=str(args.output))))
    if any(r['status'] != 'PASS' for r in results) or not report['m09']['detected']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
