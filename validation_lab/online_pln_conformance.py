"""Source-bound finite/native online numerical lifecycle conformance command."""
import argparse
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import traceback
from tempfile import TemporaryDirectory
from time import perf_counter_ns

from experimental_online_pln.agenda import Agenda, Limits, Snapshot, digest, wire
from experimental_online_pln.session import Session
from reachability.adapter_runtime import verify_native_build
from reachability.trace_protocol import canonical
from reachability.service import AdmissionService
from validation_lab.audit_pressure_comparison import artifact_path, source_inputs
from validation_lab.decision_comparison import seal, write
from validation_lab.online_pln_cases import ROOT, World, check_case, fixtures


def summary(session):
    view = session.read()
    forecast = session.service.query_probability('ctx', session.forecast)
    return dict(stage=view.lifecycle.episode.stage, outstanding=view.goal.projection.outstanding_loss,
        coverage=view.goal.projection.estimated_committed_coverage, open_work=view.goal.projection.open_loss,
        goal_label=view.goal.projection.slices[0].label,
        relief_kinds=[e.kind for h in view.goal.history for e in h.events],
        decision=view.decision.status.value, decision_basis=view.decision.basis_id,
        hard_forecast=session.service.query_belief('ctx', session.forecast).status.value,
        product_observed='exact_product_observed' in view.operation.current_milestones,
        dispatch=view.dispatch.state if view.dispatch else None,
        effects=session.executor.total_effects, forecast=[wire(b.proposal.support.truth) for b in forecast.current],
        forecast_ids=[b.belief_revision_id for b in forecast.current],
        retired_forecast_ids=[b.belief_revision_id for b in forecast.historical if b not in forecast.current])


def run_case(fixture, directory, *, native=False, limits=Limits()):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    world, agenda = World(fixture), Agenda(limits)
    start = perf_counter_ns()
    rows, last_attempt = [], {}
    result = dict(case_id=fixture['id'], mode='native' if native else 'finite-checker')
    with Session(directory, native=native, limits=limits, acquire=world.acquire) as session:
        try:
            setup_start = perf_counter_ns()
            world.setup(session)
            session.costs['setup_ns'] += perf_counter_ns()-setup_start
            write(directory/'initial.json', wire(dict(snapshot=session.read(), receipts=session.receipts)))
            with (directory/'trace.jsonl').open('x') as trace:
                while True:
                    view = session.read()
                    frontier, selected = agenda.choose(view)
                    session.costs['enumeration_ns'] += frontier.elapsed_ns
                    row = dict(step=agenda.selections, public=wire(view), public_records=view.records(), public_binding=view.binding,
                               frontier=wire(frontier), selected=wire(selected))
                    if selected is None:
                        row.update(stop=agenda.stop, after=summary(session), external_loss=world.external_loss)
                    else:
                        calls, receipts = len(session.runtime.calls), len(session.receipts)
                        attempt_start = perf_counter_ns()
                        actual = session.execute(selected)
                        row['selected_elapsed_ns'] = perf_counter_ns()-attempt_start
                        previous = last_attempt.get((selected.kind, selected.target))
                        row['retry_of_failed_operation'] = previous is not None and previous != 'PASS'
                        if row['retry_of_failed_operation']:
                            session.costs['retry_attempt_inclusive_ns'] += row['selected_elapsed_ns']
                        last_attempt[selected.kind, selected.target] = actual['status']
                        row['result'] = wire(actual)
                        row['before_external_event'] = summary(session)
                        world.after(selected, actual)
                        row.update(after=summary(session), external_loss=world.external_loss,
                                   calls=wire(session.runtime.calls[calls:]), receipts=wire(session.receipts[receipts:]))
                    rows.append(row)
                    trace.write(canonical(row)+'\n')
                    trace.flush()  # retain actual failures before checking expectations
                    if selected is None:
                        break
            result.update(summary(session), external_loss=world.external_loss, stop=agenda.stop,
                          selections=agenda.selections, work=agenda.work, acquisitions=agenda.acquisitions)
            result['reconstruction'] = session.project_and_reopen()
            check_case(fixture, rows, result)
            result['conformance'] = 'PASS'
        except Exception as error:
            result.update(conformance='FAIL', error=type(error).__name__+': '+str(error), traceback=traceback.format_exc())
        finally:
            result.update(costs_ns=dict(session.costs), runtime_calls=wire(session.runtime.calls),
                          seams=wire(world.seams), elapsed_ns=perf_counter_ns()-start)
            write(directory/'receipts.json', wire(session.receipts))
            write(directory/'result.json', result)
    result['elapsed_ns'] = perf_counter_ns()-start
    write(directory/'result.json', result)
    return result


def inputs():
    names = set(source_inputs())
    for pattern in ('experimental_online_pln/*.py', 'experimental_pressure/*.py',
                    'validation_lab/*.py', 'tests/test_online_pln*.py', 'integration_tests/test_online_pln*.py'):
        names.update(str(p.relative_to(ROOT)) for p in ROOT.glob(pattern))
    names.update(('adapters.lock.json', 'native/atomspace_batch.cc', 'PROBABILITY.md', 'ADAPTERS.md',
                  'DECISIONS.md', 'pyproject.toml', 'scripts/build_adapters.py',
                  'reviews/online-pln-lifecycle-v1/PROTOCOL.md', 'reviews/online-pln-lifecycle-v1/fixtures.json'))
    return {name: sha256((ROOT/name).read_bytes()).hexdigest() for name in sorted(names)}


def source_binding(allow_dirty=False):
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    files = inputs()
    mismatches = []
    for name, checksum in files.items():
        original = subprocess.run(['git', 'show', revision+':'+name], cwd=ROOT, capture_output=True)
        if original.returncode or sha256(original.stdout).hexdigest() != checksum:
            mismatches.append(name)
    if mismatches and not allow_dirty:
        raise ValueError('commit measured inputs before publication: '+str(mismatches))
    return dict(revision=revision, files=files, dirty_inputs=mismatches,
                baseline_publication='4fffa740003a121eb4fd7809c143bbdaa22419fa')


def readable(report):
    lines = ['# Online numerical PLN/lifecycle conformance', '',
             'Measured source: `'+report['sources']['revision']+'`. Seed 0. FIFO agenda; no pressure.', '',
             '| Case | Mode | Check | Stage | Goal loss | Effects | Selected | Runtime calls |',
             '|---|---|---|---|---:|---:|---:|---:|']
    for r in report['results']:
        lines.append('| '+' | '.join(str(r.get(k, 'unavailable')) for k in
            ('case_id', 'mode', 'conformance', 'stage', 'outstanding', 'effects', 'selections'))+
            ' | '+str(len(r['runtime_calls']))+' |')
    lines += ['', 'These are twelve paired engineering fixtures, not independent performance samples.',
        'Blocked cases are conformance successes only when the declared rejection and open need are observed.',
        'A supported numeric forecast, current decision, ACK, exact product and durable goal completion are separate.',
        'The low-confidence revision parents remain current and block the all-current decision.',
        'Support/dispatch races are labelled seam events, not autonomous event predictions.', '',
        'Runtime call timings include dependency verification and subprocess startup. precheck, postcheck and',
        'numeric_commit include existing deterministic checks and their journal persistence. inference_inclusive',
        'contains runtime_ns; acquisition_inclusive contains report ingestion and product/health monitoring;',
        'failed_attempt_inclusive overlaps execution_total. Do not sum inclusive categories.',
        'Total elapsed includes setup, observation events, reads, enumeration, traces, projection and reopening.',
        'Unmeasured separately: SQL/fsync, OS scheduling, memory/RSS, native compute versus startup,',
        'physical sensing/network latency (local simulator), trace serialization and retry-only CPU.',
        'All selected failures and retries still consume declared budgets and appear in traces.', '',
        'AtomSpace is a disposable native projection. Finite mode does not claim native verification.',
        'Interrupted coordinator continuation is unsupported; the existing journals remain authoritative.',
        'No policy tuning, transport, general stochastic planning or recovery expansion was performed.']
    return '\n'.join(lines)+'\n'


def run(output, *, modes=('finite', 'native'), allow_dirty=False):
    output = Path(output)
    if output.exists():
        raise ValueError('use a fresh output directory')
    sources = source_binding(allow_dirty)
    output.mkdir(parents=True)
    config = dict(schema='online-pln-run/v1', modes=list(modes), seed=0, agenda='fifo-first-ready-semantic/v1',
                  limits=asdict(Limits()), fixtures=fixtures())
    write(output/'configuration.json', config)
    write(output/'sources.json', sources)
    for name in sources['files']:
        target = output/'source'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/name, target)
    if 'native' in modes:
        try:
            verify_native_build(ROOT/'artifacts')
        except Exception as error:
            write(output/'blocked.json', dict(status='BLOCKED', requirement='pinned native build',
                  error=type(error).__name__+': '+str(error), fallback=False))
            raise
        shutil.copyfile(ROOT/'artifacts/adapter-build.json', output/'adapter-build.json')
        shutil.copyfile(ROOT/'adapters.lock.json', output/'adapters.lock.json')
    start, results = perf_counter_ns(), []
    for mode in modes:
        for fixture in fixtures():
            result = run_case(fixture, output/(mode+'-'+fixture['id']), native=mode == 'native')
            results.append(result)
            print(f'{mode} {fixture["id"]}: {result["conformance"]} {result.get("error", "")}', flush=True)
    report = dict(schema='online-pln-conformance/v1', sources=sources, configuration_digest=digest(config),
                  results=results, elapsed_ns=perf_counter_ns()-start,
                  conformance='PASS' if all(r['conformance'] == 'PASS' for r in results) else 'FAIL')
    write(output/'report.json', report)
    (output/'conformance.md').write_text(readable(report))
    seal(output)  # existing manifest/checksum utility; no new publication framework
    return report


def verify(output):
    output = Path(output)
    manifest = json.loads((output/'bundle.json').read_text())
    for name, checksum in manifest['files'].items():
        if sha256(artifact_path(output, name).read_bytes()).hexdigest() != checksum:
            raise ValueError('bundle artifact changed: '+name)
    report = json.loads((output/'report.json').read_text())
    for name, checksum in report['sources']['files'].items():
        if sha256(artifact_path(output, 'source/'+name).read_bytes()).hexdigest() != checksum:
            raise ValueError('source changed: '+name)
    config = json.loads((output/'configuration.json').read_text())
    if digest(config) != report['configuration_digest']:
        raise ValueError('configuration changed')
    expected_runs = {(mode, f['id']) for mode in config['modes'] for f in config['fixtures']}
    actual_runs = {('finite' if r['mode'] == 'finite-checker' else 'native', r['case_id']) for r in report['results']}
    if expected_runs != actual_runs or len(actual_runs) != len(report['results']):
        raise ValueError('missing or duplicate fixture/mode')
    if report['sources']['dirty_inputs']:
        raise ValueError('development run is not a source-bound publication')
    selections = 0
    for result in report['results']:
        mode = 'finite' if result['mode'] == 'finite-checker' else 'native'
        folder = output/(mode+'-'+result['case_id'])
        fixture = next(f for f in config['fixtures'] if f['id'] == result['case_id'])
        rows = [json.loads(line) for line in (folder/'trace.jsonl').read_text().splitlines()]
        check_case(fixture, rows, result)
        agenda = Agenda(Limits(**config['limits']))
        for row in rows:
            snapshot = Snapshot.from_records(row['public_records'])
            if wire(snapshot) != row['public'] or snapshot.binding != row['public_binding']:
                raise ValueError('public record binding differs')
            frontier, selected = agenda.choose(snapshot)
            actual = wire(frontier)
            actual['elapsed_ns'] = row['frontier']['elapsed_ns']
            if actual != row['frontier'] or wire(selected) != row['selected']:
                raise ValueError('candidate enumeration or FIFO selection differs')
            selections += selected is not None
        if (agenda.selections, agenda.work, agenda.acquisitions, agenda.stop) != (
                result['selections'], result['work'], result['acquisitions'], result['stop']):
            raise ValueError('budget/stop accounting differs')
        if mode == 'native' and any(c['status'] != 'PASS' or c['formula_agreement'] is not True
                                   for c in result['runtime_calls']):
            raise ValueError('native formula conformance did not pass')
        # Reopen a copy, never modify the published authority. Existing checked
        # journal replay independently validates its persisted successful commands.
        with TemporaryDirectory() as tmp:
            local = Path(tmp)/'authority.db'
            shutil.copyfile(folder/'admission.db', local)
            with AdmissionService(database=local) as service:
                try:
                    execution = service.export_execution_decision('attempt')
                except KeyError:
                    execution = None
                recovered = (service.export_probability('ctx'), service.export_admission('ctx'), execution,
                             service.inspect_lifecycle('episode'), service.inspect_goal('goal'), service.inspect_resource('slot'))
                if wire(recovered) != result['reconstruction']['authority']:
                    raise ValueError('saved authority reconstruction differs')
    return dict(status='PASS', files=len(manifest['files']), cases=len(report['results']), selections=selections,
                checks='sealed files, source/config, public frontiers/FIFO, prefix expectations, checked SQLite replay')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path)
    p.add_argument('--verify', type=Path)
    p.add_argument('--modes', nargs='+', choices=('finite', 'native'), default=['finite', 'native'])
    p.add_argument('--allow-dirty', action='store_true', help='development runs only; explicitly recorded')
    args = p.parse_args()
    if args.verify:
        print(json.dumps(verify(args.verify), indent=2))
    elif args.output:
        result = run(args.output, modes=tuple(args.modes), allow_dirty=args.allow_dirty)
        if result['conformance'] != 'PASS':
            raise SystemExit(1)
    else:
        p.error('--output or --verify is required')


if __name__ == '__main__':
    main()
