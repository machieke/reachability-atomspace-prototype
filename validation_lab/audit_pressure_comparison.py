"""Audit a completed bounded B0/B3 comparison without modifying its evidence.

This is a consistency/reproduction check inside the trusted evaluator boundary,
not publisher authentication, an independent inference implementation, or a
reproduction of historical wall-clock measurements.
"""
import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import subprocess
from tempfile import TemporaryDirectory
from time import perf_counter_ns

from reachability.pressure import PressureLimits
from reachability.pressure_controller import ComparisonBudget, rank_b3
from reachability.pressure_session import ReasoningSession
from reachability.pressure_work import b0_ranking, enumerate_work, operation_cost
from reachability.service import AdmissionService
from reachability.trace_protocol import canonical, fingerprint, read_json
from .pressure_episodes import ReasoningWorld, episodes
from .pressure_reference import mutation_witness

ROOT = Path(__file__).resolve().parents[1]
WORK_KEYS = ('actions', 'operation_work', 'observation_work', 'candidate_visits',
             'ranking_states', 'ranking_transitions', 'ranking_joint_checks',
             'pressure_nodes', 'pressure_edges', 'pressure_iterations', 'pressure_edge_visits')
PATHS = {'B0': 'b0-conditional-plan-best-first', 'B3': 'b3-typed-pressure-priority-queue'}


class AuditError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise AuditError(message)


def equal(actual, expected, label):
    require(canonical(actual) == canonical(expected), label + ' differs')


def source_inputs():
    files = [*sorted((ROOT/'reachability').glob('*.py')),
             *[ROOT/'validation_lab'/name for name in ('run_pressure_comparison.py',
                 'pressure_episodes.py', 'pressure_reference.py', 'audit_pressure_comparison.py')],
             *[ROOT/name for name in ('reachability_atomspace_specification.md',
                 'pressure_field_pln_lifecycle_integration.md', 'reachability_validation_design/benchmark_design.md')]]
    return {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest() for path in files}


def artifact_path(directory, name):
    path = directory/name
    require(not Path(name).is_absolute() and '..' not in Path(name).parts,
            'artifact path must stay inside the bundle')
    require(path.resolve().is_relative_to(directory.resolve()) and not path.is_symlink(),
            'artifact must be a local regular file')
    require(path.is_file() and path.stat().st_size <= 64*1024*1024, 'missing or oversized artifact: '+name)
    if path.suffix == '.db':
        wal = Path(str(path)+'-wal')
        require(not wal.exists() or wal.stat().st_size == 0, 'uncheckpointed journal is not a completed artifact: '+name)
    return path


def load(directory, name):
    return read_json(artifact_path(directory, name).read_text(), max_bytes=64*1024*1024)


def run_name(row):
    fields = [row['case_id'], str(row['seed']), row['configuration'], row['variant']]
    require(all(re.fullmatch(r'[A-Za-z0-9-]+', value) for value in fields), 'invalid run name')
    return '-'.join(fields)


def required_artifacts(report):
    names = ['configuration.json', 'report.json', 'ranking-isolation.json', 'comparison.md']
    for row in report['results']:
        names.extend(run_name(row)+'/'+name for name in ('trace.jsonl', 'admission.db'))
    require(len(names) == len(set(names)), 'duplicate run artifacts')
    return sorted(names)


def seal_bundle(directory):
    """Called only after every authority is closed; interrupted bundles fail audit."""
    report = load(directory, 'report.json')
    inventory = {name: sha256(artifact_path(directory, name).read_bytes()).hexdigest()
                 for name in required_artifacts(report)}
    with (directory/'bundle.json').open('x') as stream:
        json.dump(dict(schema='pressure-comparison-bundle/v1', files=inventory), stream, indent=2)
        stream.write('\n')


def semantic_snapshot(snapshot):
    # Fresh authorities issue different belief-derived relief event IDs. Only
    # those opaque identifiers are normalized; event counts, all revisions,
    # supports, conditions, demand and every other public field must reproduce.
    result = deepcopy(snapshot)
    for goal in result['goals']:
        for key in ('relief_events', 'reopened_events'):
            goal[key] = len(goal[key])
    return result


def nonnegative_counts(values, label):
    require(all(type(v) is int and v >= 0 for v in values.values()), label+' requires nonnegative integer counts')


def belief_history(authority, context_id):
    beliefs = authority._contexts[context_id].beliefs
    return {b.accepted_at_revision: dict(context=b.context_id, conclusion=asdict(b.conclusion),
        premises=[beliefs[p].accepted_at_revision for p in b.proposal.premise_revision_ids],
        evidence=b.proposal.evidence_ids, lineage=b.proposal.lineage_roots,
        formula=b.proposal.formula_id, interpretation=b.interpretation) for b in beliefs.values()}


def audit_run(directory, case, config, result):
    """Verify decisions, then reproduce their effects without running a controller."""
    public, variant = case['public'], result['variant']
    require(result['status'] == 'PASS' and variant in PATHS, 'incomplete or unsupported run')
    equal(result['budget'], config['budget'], 'declared budget')
    budget = ComparisonBudget(**result['budget'])
    limits = PressureLimits(**result['pressure_limits'])
    equal(asdict(limits), asdict(PressureLimits()), 'frozen pressure limits')
    lines = artifact_path(directory, 'trace.jsonl').read_text().splitlines()
    require(len(lines) <= 2*budget.actions+1 and len(lines) % 2 == 1, 'trace selection/receipt framing')
    rows = [read_json(line, max_bytes=8*1024*1024) for line in lines]
    require(rows[-1]['stage'] == 'stop', 'trace must end with exactly one stop')
    work = dict.fromkeys(WORK_KEYS, 0)
    selected, statuses, fields, rank_paths, receipts, receipt_revisions = [], Counter(), [], set(), [], []
    with TemporaryDirectory(prefix='pressure-audit-') as temporary:
        with ReasoningSession(public, Path(temporary)/'reproduction') as session:
            world = ReasoningWorld(session, case)
            initial = session.read()
            equal(semantic_snapshot(result['initial_snapshot']), semantic_snapshot(initial), 'initial snapshot')
            equal(result['initial_candidates'], [c.wire() for c in enumerate_work(public, initial).candidates], 'initial candidates')
            world.sample_outcomes()
            for step in range(1, (len(rows)-1)//2+1):
                row, reply = rows[2*step-2:2*step]
                require(row['stage'] == 'selection' and reply['stage'] == 'receipt'
                        and row['step'] == reply['step'] == step, 'trace selection/receipt order')
                equal(row['schema'], 'pressure-comparison-step/v1', 'trace schema')
                equal(row['variant'], variant, 'trace controller')
                equal(row['ranking_path'], PATHS[variant], 'ranking code path')
                equal(row['budget'], result['budget'], 'trace budget')
                snapshot = row['snapshot']
                equal(row['snapshot_digest'], fingerprint(snapshot), 'snapshot binding')
                equal(semantic_snapshot(snapshot), semantic_snapshot(session.read()), 'replayed public snapshot')
                frontier = enumerate_work(public, snapshot, visit_limit=budget.candidate_visits-work['candidate_visits'])
                require(frontier.complete and not frontier.terminal, 'selection after exhausted or terminal frontier')
                equal(row['candidates'], [c.wire() for c in frontier.candidates], 'shared candidate frontier')
                work['candidate_visits'] += frontier.visits
                candidates = [c for c in frontier.candidates if
                    operation_cost(public, c)+work['operation_work'] <= budget.operation_work
                    and c.observation_cost+work['observation_work'] <= budget.observation_work]
                require(candidates, 'selection has no affordable candidate')
                if variant == 'B0':
                    ranks, search, complete = b0_ranking(public, snapshot, candidates,
                        state_limit=budget.ranking_states-work['ranking_states'])
                    require(complete, 'selection after B0 ranking exhaustion')
                    for key in ('states', 'transitions', 'joint_checks'):
                        work['ranking_'+key] += search[key]
                    equal(row['pressure'], None, 'B0 pressure')
                else:
                    require(work['pressure_iterations']+len(snapshot['goals'])*limits.iterations <= budget.pressure_iterations,
                            'selection after pressure session exhaustion')
                    ranks, field, _, _ = rank_b3(public, snapshot, candidates, limits)
                    equal(row['pressure'], field, 'recomputed pressure')
                    require(not any(k in field['exhausted'] for k in ('nodes', 'edges', 'sources')), 'pressure graph exhausted')
                    for key in ('nodes', 'edges', 'iterations', 'edge_visits'):
                        work['pressure_'+key] += field['work'][key]
                    fields.append(field)
                equal(row['ranks'], ranks, 'recomputed ranks')
                candidate = min(candidates, key=lambda c: (ranks[c.candidate_id], c.candidate_id))
                equal(row['selected'], candidate.wire(), 'ranked selection')
                work['actions'] += 1
                work['operation_work'] += operation_cost(public, candidate)
                work['observation_work'] += candidate.observation_cost
                equal(row['work'], work, 'selection work accounting')
                receipt = world.execute(candidate, fingerprint(session.read()))
                recorded = reply['receipt']
                for key in ('status', 'detail', 'knowledge_revision'):
                    equal(recorded[key], receipt[key], 'replayed receipt '+key)
                equal(recorded['belief'] is None, receipt['belief'] is None, 'receipt belief presence')
                nonnegative_counts(recorded['costs'], 'receipt costs')
                for key in ('inference_calls', 'certificates', 'journal_commands'):
                    equal(recorded['costs'][key], receipt['costs'][key], 'receipt '+key)
                receipts.append(recorded)
                receipt_revisions.append(None if receipt['belief'] is None else
                    session.service._contexts[public['context_id']].beliefs[receipt['belief']].accepted_at_revision)
                if recorded['status'] != 'PASS':
                    statuses[recorded['status']] += 1
                selected.append(dict(kind=candidate.kind, arguments=dict(candidate.arguments), status=receipt['status']))
                rank_paths.add(row['ranking_path'])
            equal(semantic_snapshot(result['controller_stop_snapshot']), semantic_snapshot(session.read()), 'controller stop snapshot')
            require(result['evaluation_horizon'] == 16, 'evaluation horizon differs')
            world.idle_until(16)
            final = world.sample_outcomes()
            equal(result['outcomes'], world.outcomes, 'replayed external outcome history')
            equal(result['final'], final, 'final outcomes')
            equal(result['environment_events'], world.events, 'environment events')
            equal(semantic_snapshot(result['final_snapshot']), semantic_snapshot(session.read()), 'final snapshot')
            equal(result['journal_commands_total'], session.service._journal_sequence, 'reproduced journal command count')
            expected_history = belief_history(session.service, public['context_id'])
            expected_current = sorted(b.accepted_at_revision for b in session.service.snapshot(public['context_id']).usable)
            expected_commands = [(e.command, e.key) for e in session.service._journal.entries()]
        # Copy rather than open the supplied database through a writable service.
        # No original journal, sidecar, trace or report is changed by this audit.
        copied = Path(temporary)/'saved.db'
        shutil.copyfile(artifact_path(directory, 'admission.db'), copied)
        with AdmissionService(database=copied) as authority:
            equal(authority._journal_sequence, result['journal_commands_total'], 'saved journal command count')
            state = authority.snapshot(public['context_id'])
            equal(state.knowledge_revision, result['final_snapshot']['revisions']['knowledge'], 'saved journal revision')
            equal(state.logical_time, 16, 'saved journal time')
            equal(belief_history(authority, public['context_id']), expected_history, 'saved journal belief history')
            equal(sorted(b.accepted_at_revision for b in state.usable), expected_current, 'saved journal current support')
            equal([(e.command, e.key) for e in authority._journal.entries()], expected_commands, 'saved journal command order')
            for goal in result['final_snapshot']['goals']:
                view = authority.inspect_goal(goal['goal_id'])
                item = view.projection.slices[0]
                equal(goal['outstanding'], item.outstanding_loss, 'saved journal outstanding loss')
                equal(goal['coverage'], item.estimated_coverage, 'saved journal coverage')
                for key, kind in (('relief_events', 'observed_relief'), ('reopened_events', 'reopened')):
                    events = [e.event_id for revision in view.history for e in revision.events if e.kind == kind]
                    equal(goal[key], events, 'saved journal '+key)
                    snapshots = [result['initial_snapshot'], result['controller_stop_snapshot'],
                                 *[r['snapshot'] for r in rows if r['stage'] == 'selection']]
                    for snapshot in snapshots:
                        observed = next(g for g in snapshot['goals'] if g['goal_id'] == goal['goal_id'])[key]
                        equal(observed, events[:len(observed)], 'saved journal historical '+key)
            beliefs = authority._contexts[public['context_id']].beliefs
            require(all(r['belief'] is None or r['belief'] in beliefs for r in receipts), 'receipt belief missing from saved journal')
            equal([None if r['belief'] is None else beliefs[r['belief']].accepted_at_revision for r in receipts],
                  receipt_revisions, 'receipt belief revision')
    stop = rows[-1]
    audit_stop(public, variant, result, stop, work, fields[-1] if fields else None)
    equal(stop['reason'], result['stop_reason'], 'stop reason')
    equal(stop['last_pressure'], result['last_pressure'], 'last pressure')
    equal(stop['work'], {key: result['work'][key] for key in WORK_KEYS}, 'stop work accounting')
    nonnegative_counts(result['work'], 'run work')
    for key in ('actions', 'operation_work', 'observation_work'):
        equal(stop['work'][key], work[key], 'stop '+key)
    for key in WORK_KEYS:
        require(stop['work'][key] >= work[key], 'stop work regresses')
    for key in ('actions', 'operation_work', 'observation_work', 'candidate_visits', 'ranking_states', 'pressure_iterations'):
        require(stop['work'][key] <= getattr(budget, key), 'session budget exceeded: '+key)
    equal(result['selected'], selected, 'selected operation summary')
    equal(result['failures'], dict(statuses), 'operation failure counts')
    equal(result['ranking_paths'], sorted(rank_paths), 'ranking path summary')
    equal(result['integrated_external_loss'], sum(o['external_weighted_loss'] for o in result['outcomes'][:-1]), 'integrated loss')
    evaluated_fields = fields+([stop['last_pressure']] if stop['last_pressure'] is not None else [])
    equal(result['pressure_converged'], all(f['converged'] for f in evaluated_fields), 'convergence summary')
    equal(result['pressure_exhausted'], sorted({e for f in evaluated_fields for e in f['exhausted']}),
          'pressure exhaustion summary')
    audit_costs(result, receipts)
    return len(selected)


def audit_stop(public, variant, result, stop, previous, last_pressure):
    """Account for a final discovery/ranking pass that issued no operation."""
    budget = ComparisonBudget(**result['budget'])
    work = dict(previous)
    reason = stop['reason']
    if reason == 'WALL_BUDGET':
        require(result['controller_elapsed_ns'] >= budget.wall_ns, 'wall stop before declared cap')
    if work['actions'] == budget.actions:
        expected = 'ACTION_BUDGET'
    elif reason == 'WALL_BUDGET' and stop['work'] == work:
        expected = 'WALL_BUDGET'  # cap checked before snapshot/discovery
    else:
        snapshot = result['controller_stop_snapshot']
        frontier = enumerate_work(public, snapshot, visit_limit=budget.candidate_visits-work['candidate_visits'])
        work['candidate_visits'] += frontier.visits
        if not frontier.complete:
            expected = 'CANDIDATE_BUDGET'
        elif frontier.terminal:
            expected = 'OBSERVED_GOALS'
        else:
            candidates = [c for c in frontier.candidates if
                operation_cost(public, c)+work['operation_work'] <= budget.operation_work
                and c.observation_cost+work['observation_work'] <= budget.observation_work]
            empty = 'WORK_BUDGET' if frontier.candidates else 'BLOCKED'
            if not candidates and variant == 'B0':
                expected = empty
            elif variant == 'B0':
                _, search, complete = b0_ranking(public, snapshot, candidates,
                    state_limit=budget.ranking_states-work['ranking_states'])
                for key in ('states', 'transitions', 'joint_checks'):
                    work['ranking_'+key] += search[key]
                expected = 'WALL_BUDGET' if complete else 'RANKING_BUDGET'
            else:
                limits = PressureLimits(**result['pressure_limits'])
                if work['pressure_iterations']+len(snapshot['goals'])*limits.iterations > budget.pressure_iterations:
                    expected = 'PRESSURE_SESSION_BUDGET'
                else:
                    _, last_pressure, _, _ = rank_b3(public, snapshot, candidates, limits)
                    for key in ('nodes', 'edges', 'iterations', 'edge_visits'):
                        work['pressure_'+key] += last_pressure['work'][key]
                    expected = ('PRESSURE_GRAPH_BUDGET' if any(k in last_pressure['exhausted'] for k in ('nodes', 'edges', 'sources'))
                                else empty if not candidates else 'WALL_BUDGET')
    equal(reason, expected, 'derived stop reason')
    equal(stop['work'], work, 'derived stop work')
    equal(stop['last_pressure'], last_pressure, 'derived last pressure')


def audit_costs(result, receipts):
    for key in ('costs_ns', 'setup_costs', 'evaluation_costs'):
        nonnegative_counts(result[key], key)
    for key in ('setup_elapsed_ns', 'controller_elapsed_ns', 'evaluation_elapsed_ns',
                'total_elapsed_ns', 'process_cpu_ns', 'wall_overrun_ns'):
        nonnegative_counts({key: result[key]}, 'elapsed time')
    require(result['total_elapsed_ns'] >= sum(result[k] for k in
            ('setup_elapsed_ns', 'controller_elapsed_ns', 'evaluation_elapsed_ns')), 'total elapsed accounting')
    equal(result['wall_overrun_ns'], max(0, result['controller_elapsed_ns']-result['budget']['wall_ns']), 'wall overrun')
    costs = result['costs_ns']
    exclusive = sum(costs[k] for k in ('snapshot_ns', 'candidate_discovery_ns', 'ranking_ns',
        'pressure_construction_ns', 'pressure_iteration_ns', 'inference_ns', 'certification_ns',
        'persistence_ns', 'authority_other_ns'))
    require(exclusive <= result['controller_elapsed_ns'], 'exclusive measured time exceeds controller elapsed')
    equal(costs['other_controller_ns'], result['controller_elapsed_ns']-exclusive, 'residual controller time')
    for key in ('inference_calls', 'certificates'):
        equal(result['work'][key], sum(r['costs'][key] for r in receipts), 'authority '+key)
    for key in ('inference_ns', 'certification_ns', 'persistence_ns', 'authority_other_ns'):
        require(costs[key] >= sum(r['costs'][key] for r in receipts), 'receipt time exceeds run category')
    equal(result['journal_commands_total'], result['setup_costs']['journal_commands']
          +result['work']['journal_commands']+result['evaluation_costs']['journal_commands'], 'journal category accounting')
    require(bool(result['unmeasured_costs']), 'unmeasured costs must remain explicit')


def audit_bundle(directory, *, source_commit=None):
    from .run_pressure_comparison import configurations, isolate_ranking, write_comparison
    start = perf_counter_ns()
    directory = Path(directory)
    report, config, bundle = (load(directory, name) for name in ('report.json', 'configuration.json', 'bundle.json'))
    equal(report['schema'], 'b0-b3-comparison/v1', 'report schema')
    equal(bundle['schema'], 'pressure-comparison-bundle/v1', 'bundle schema')
    equal(sorted(bundle['files']), required_artifacts(report), 'complete artifact inventory')
    for name, digest in bundle['files'].items():
        equal(sha256(artifact_path(directory, name).read_bytes()).hexdigest(), digest, 'artifact digest: '+name)
    equal(report['source_files'], source_inputs(), 'current source bindings')
    verified_commit = None
    if source_commit is not None:
        verified_commit = subprocess.check_output(['git', 'rev-parse', '--verify', '--end-of-options',
            source_commit+'^{commit}'], cwd=ROOT, text=True).strip()
        for name, digest in report['source_files'].items():
            content = subprocess.check_output(['git', 'show', verified_commit+':'+name], cwd=ROOT)
            equal(sha256(content).hexdigest(), digest, 'committed source binding: '+name)
    seeds = report['seeds']
    require(1 <= len(seeds) <= 8 and len(seeds) == len(set(seeds))
            and all(type(s) is int and 0 <= s < 2**32 for s in seeds), 'invalid seeds')
    cases, configs = [case for seed in seeds for case in episodes(seed)], configurations()
    equal(config, dict(configurations=configs, episodes=cases), 'frozen comparison configuration')
    equal(report['configuration_digest'], fingerprint(config), 'configuration binding')
    expected = {(c['case_id'], c['seed'], b['name'], v) for c in cases for b in configs for v in PATHS}
    indexed = {(r['case_id'], r['seed'], r['configuration'], r['variant']): r for r in report['results']}
    require(set(indexed) == expected and len(indexed) == len(report['results']), 'incomplete or duplicate comparison matrix')
    require(all(r['status'] == 'PASS' for r in report['results']), 'comparison contains a failed run')
    audited, pairs, isolation = 0, [], []
    for case in cases:
        for configuration in configs:
            pair = {v: indexed[case['case_id'], case['seed'], configuration['name'], v] for v in PATHS}
            for result in pair.values():
                audited += audit_run(directory/run_name(result), case, configuration, result)
            b0, b3 = pair['B0'], pair['B3']
            equal(b0['initial_snapshot'], b3['initial_snapshot'], 'paired initial snapshot')
            equal(b0['initial_candidates'], b3['initial_candidates'], 'paired initial candidates')
            pairs.append(dict(case_id=case['case_id'], seed=case['seed'], configuration=configuration['name'],
                B3_minus_B0_integrated_external_loss=b3['integrated_external_loss']-b0['integrated_external_loss'],
                B3_minus_B0_final_external_loss=b3['final']['external_weighted_loss']-b0['final']['external_weighted_loss'],
                B3_minus_B0_controller_elapsed_ns=b3['controller_elapsed_ns']-b0['controller_elapsed_ns'],
                initial_candidates_identical=True))
            if configuration['name'] == 'work-16':
                isolation.append(dict(case_id=case['case_id'], seed=case['seed'],
                                      **isolate_ranking(case['public'], b0['initial_snapshot'])))
    equal(report['pairs'], pairs, 'paired differences')
    equal(report['candidate_frontiers_audited'], audited, 'audited frontier count')
    recorded_isolation = load(directory, 'ranking-isolation.json')
    equal(len(recorded_isolation), report['ranking_isolation_cases'], 'isolation count')
    for item in recorded_isolation+isolation:
        for variant in PATHS:
            for key in list(item[variant]):
                if key.endswith('_ns'):
                    nonnegative_counts({key: item[variant][key]}, 'ranking isolation times')
                    del item[variant][key]
    equal(recorded_isolation, isolation, 'same-snapshot rankings')
    equal(report['m09'], mutation_witness(), 'M09 witness')
    require(report['m09']['detected'], 'M09 was not detected')
    for key, value in dict(evaluator_process_isolation=False, family_complete_fixtures=0, transport=False, training_runs=0).items():
        equal(report[key], value, 'bounded scope '+key)
    with TemporaryDirectory(prefix='pressure-audit-readable-') as temporary:
        readable = Path(temporary)/'comparison.md'
        write_comparison(report, readable)
        equal(artifact_path(directory, 'comparison.md').read_text(), readable.read_text(), 'readable comparison')
    return dict(schema='pressure-comparison-audit/v1', status='PASS', runs=len(indexed),
        selections_reproduced=audited, source_files_verified=len(report['source_files']),
        source_revision=report['source_revision'], verified_source_commit=verified_commit,
        bundle_sha256=sha256((directory/'bundle.json').read_bytes()).hexdigest(),
        auditor_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        elapsed_ns=perf_counter_ns()-start, charged_to_controllers=False,
        limitations=['hash inventory is not publisher authentication',
            'replay uses the existing authority and ranking implementations',
            'fresh replay normalizes only opaque goal-event IDs; saved journals preserve and verify them',
            'timing consistency checked; historical elapsed times and wall-stop decisions cannot be remeasured'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--source-commit', help='also require every source input to match this Git commit')
    parser.add_argument('--output', type=Path, help='write audit JSON to a new file (input artifacts remain read-only)')
    args = parser.parse_args()
    try:
        result = audit_bundle(args.directory, source_commit=args.source_commit)
    except Exception as error:
        result = dict(schema='pressure-comparison-audit/v1', status='FAIL', error_type=type(error).__name__, error=str(error))
    if args.output:
        with args.output.open('x') as stream:
            stream.write(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))
    if result['status'] != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
