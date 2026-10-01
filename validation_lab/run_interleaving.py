"""Finite two-worker schedules, cold controls, mutation reduction and receipts."""
import argparse
from contextlib import nullcontext
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from reachability import interleaving_protocol as protocol
from reachability.interleaving_session import InterleavingSession
from reachability.trace_protocol import canonical, fingerprint
from .interleaving_oracle import OracleGap, reference_prefix
from .interleaving_schedule import reserve_pair
from .interleaving_mutations import mutate
from .run_deployment import ConformanceMismatch, compare
from .shrink_replay import digest_file
from .trace_shrink import shrink
from .run_shrink import semantic_result

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT/'validation_lab'/'interleaving_cases'


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def validate_case(case):
    protocol.initial(case['public'])
    if type(case['events']) is not list or len(case['events']) > 64:
        raise ValueError('at most 64 events required')
    for e in case['events']:
        protocol.event(e)
    ids = [e['event_id'] for e in case['events']]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate event identity')
    race = case['schedule']
    if type(race) is not dict or set(race) != {'schema', 'reserve_pair'} or race['schema'] != 'interleaving-schedule/v1':
        raise ValueError('unsupported evaluator schedule')
    pair = race['reserve_pair']
    if type(pair) is not list or len(pair) not in (0, 2) or any(type(x) is not str or not x for x in pair) or len(set(pair)) != len(pair):
        raise ValueError('zero or two distinct race event IDs required')
    # A deletion can remove either endpoint; the remaining command is then serial.
    if pair and all(x in ids for x in pair):
        first, second = (case['events'][ids.index(x)] for x in pair)
        if (ids.index(pair[1]) != ids.index(pair[0])+1 or first['kind'] != second['kind'] or
                first['kind'] != 'reserve' or first['actor'] == second['actor']):
            raise ValueError('race endpoints must be adjacent reservations by distinct workers')
        if any(e['kind'] == 'reserve' for e in case['events'][:ids.index(pair[0])]):
            raise ValueError('paired reservation checkpoints require fresh attempts; retries must be serial')


def run_case(case, output, *, mutant=None, reference=reference_prefix, session_factory=InterleavingSession):
    validate_case(case)
    output = Path(output)
    output.mkdir(parents=True)
    write(output/'case.json', case)
    count, recoveries, calls = 0, 0, 0
    with (output/'actual.jsonl').open('w') as log, (output/'schedule.jsonl').open('w') as schedules:
        def note(value):
            schedules.write(canonical(value)+'\n')
            schedules.flush()
        with TemporaryDirectory() as directory, session_factory(case['public'], directory) as session:
            prefix = []
            def emit(event, outcome):
                nonlocal count
                row = session.record(outcome)
                log.write(canonical(row)+'\n')
                log.flush()
                count += 1
                prefix.append(event)
                expected = reference(case['public'], prefix)
                compare(expected['status'], outcome['status'], event['event_id'], 'outcome.status')
                compare(expected['projection'], row['projection'], event['event_id'])
            def recover():
                nonlocal recoveries
                session.restart()
                compare(reference(case['public'], prefix)['projection'], session.projection(), prefix[-1]['event_id'], 'recovered_projection')
                recoveries += 1
            compare(reference(case['public'], [])['projection'], session.projection(), 'initial')
            pair, events, i = case['schedule']['reserve_pair'], case['events'], 0
            scope = mutate(mutant) if mutant else nullcontext(dict(calls=0))
            try:
                with scope as canary:
                    try:
                        while i < len(events):
                            if pair and i+1 < len(events) and [events[i]['event_id'], events[i+1]['event_id']] == pair:
                                reserve_pair(session, events[i], events[i+1], emit, note)
                                i += 2
                            else:
                                emit(events[i], session.apply(events[i]))
                                i += 1
                            # Threads are quiescent here. An in-flight transaction
                            # is never replaced by a replaying service instance.
                            if not mutant:
                                recover()
                    finally:
                        calls = canary['calls']
            finally:
                write(output/'execution.json', dict(prefixes=count, recovery_checkpoints=recoveries, invocations=calls))
    return dict(prefixes=count, recovery_checkpoints=recoveries, invocations=calls)


class InterleavingPredicate:
    def __init__(self, case, mutant, output):
        self.case, self.mutant, self.output = deepcopy(case), mutant, Path(output)
        self.output.mkdir(parents=True)

    def __call__(self, events, trial):
        directory = self.output/f'{trial:04d}'
        directory.mkdir()
        case = deepcopy(self.case)
        case['events'] = events
        write(directory/'candidate.json', case)
        stage = 'protocol'
        try:
            validate_case(case)
            stage = 'control'
            run_case(case, directory/'control')
            stage = 'mutant'
            run_case(case, directory/'mutant', mutant=self.mutant)
        except OracleGap as error:
            result = dict(kind='ORACLE_GAP', stage=stage, error=str(error))
        except ConformanceMismatch as error:
            calls = json.loads((directory/'mutant'/'execution.json').read_text())['invocations'] if stage == 'mutant' else 0
            signature = dict(schema='trace-failure-signature/v1', profile='interleaving', initial_digest=fingerprint(case['public']),
                schedule_digest=fingerprint(case['schedule']), mutant=self.mutant, event_id=error.event_id, path=error.path,
                expected=error.expected, actual=error.actual)
            result = dict(kind='CONTROL_MISMATCH' if stage == 'control' else 'WITNESS' if calls else 'ERROR',
                          stage=stage, signature=signature, invocations=calls)
        except Exception as error:
            result = dict(kind='INVALID' if stage == 'protocol' and isinstance(error, ValueError) else 'ERROR',
                          stage=stage, error_type=type(error).__name__, error=str(error))
        else:
            result = dict(kind='NO_WITNESS')
        result['control_passed'] = stage == 'mutant'
        result['artifacts'] = {str(p.relative_to(directory)): digest_file(p) for p in sorted(directory.rglob('*')) if p.is_file()}
        write(directory/'assessment.json', result)
        return result


def reduce_case(case, mutant, output, *, max_evaluations=128):
    output = Path(output)
    output.mkdir(parents=True)
    write(output/'original.json', case)
    predicate = InterleavingPredicate(case, mutant, output/'trials')
    with (output/'attempts.jsonl').open('w') as log:
        def emit(row):
            log.write(canonical(row)+'\n')
            log.flush()
        result = shrink(case['events'], predicate, max_evaluations=max_evaluations, emit=emit)
    write(output/'reduced.json', dict(case, events=result['reduced_events']))
    write(output/'result.json', result)
    return result


def source_paths():
    names = ['interleaving_oracle', 'interleaving_schedule', 'interleaving_mutations', 'run_interleaving', 'generate_interleaving_cases',
             'run_deployment', 'run_shrink', 'trace_shrink', 'shrink_replay', 'admission_oracle', 'deployment_oracle', 'mutations']
    return sorted(['adapters.lock.json']+['validation_lab/'+n+'.py' for n in names]+[str(p.relative_to(ROOT)) for p in (ROOT/'reachability').glob('*.py')])


def verify_corpus():
    receipt = json.loads((CORPUS/'manifest.json').read_text())
    files = {str(p.relative_to(ROOT)) for p in CORPUS.rglob('*') if p.is_file() and p != CORPUS/'manifest.json'}
    if receipt['schema'] != 'interleaving-corpus/v1' or set(receipt['fixture_files']) != files or set(receipt['source_files']) != set(source_paths()):
        raise ValueError('interleaving corpus inventory mismatch')
    for group in ('fixture_files', 'source_files'):
        for path, expected in receipt[group].items():
            if digest_file(ROOT/path) != expected:
                raise ValueError('interleaving corpus source/fixture drift: '+path)
    cases = load_cases()
    if (len(cases) != receipt['case_count'] or receipt['family_complete_fixtures'] != 0
            or sum(len(c['events']) for c in cases) != receipt['event_prefixes']
            or any(c['split'] != 'development' or c['parent_instance_id'] != 'interleaving-parent-0' for c in cases)):
        raise ValueError('interleaving split/count mismatch')
    for case in cases:
        validate_case(case)
        if case['mutant']:
            expected = json.loads((CORPUS/'mutations'/(case['mutant']+'.json')).read_text())
            if expected['case'] != case or expected['result']['original_events'] != case['events']:
                raise ValueError('interleaving mutation ancestry mismatch')
    return receipt


def load_cases():
    return [dict(json.loads(p.read_text()), public=json.loads((CORPUS/'public'/p.name).read_text())) for p in sorted((CORPUS/'evaluator').glob('*.json'))]


def verify_report(output):
    """Check receipt/file integrity and compare all saved reduction decisions.

    Fresh execution still requires rerunning the CLI into a new directory.
    File hashes are integrity receipts, not authenticated execution certificates.
    """
    output = Path(output)
    report = json.loads((output/'report.json').read_text())
    files = {str(p.relative_to(output)): digest_file(p) for p in sorted(output.rglob('*')) if p.is_file() and p != output/'report.json'}
    if report['schema'] != 'interleaving-validation/v1' or report['corpus'] != verify_corpus() or report['files'] != files:
        raise ValueError('interleaving report sources/files differ from receipt')
    cases = {c['case_id']: c for c in load_cases()}
    if (len(report['results']) != len(cases) or {r['case_id'] for r in report['results']} != set(cases)
            or not all(r['passed'] for r in report['results'])
            or len(report['mutations']) != 2 or {r['mutant'] for r in report['mutations']} != {'M08','M10'}):
        raise ValueError('interleaving report coverage mismatch')
    for record in report['results']:
        case = cases[record['case_id']]
        rows = [json.loads(line) for line in (output/case['case_id']/'actual.jsonl').read_text().splitlines()]
        if len(rows) != record['prefixes'] or len(rows) != len(case['events']):
            raise ValueError('interleaving prefix count mismatch')
        for index, row in enumerate(rows):
            name = case['events'][index]['event_id']
            expected = reference_prefix(case['public'],case['events'][:index+1])
            if row['outcome']['event_id'] != name or fingerprint(row['projection']) != row['projection_digest']:
                raise ValueError('interleaving recorded event/digest mismatch')
            compare(expected['status'],row['outcome']['status'],name,'outcome.status')
            compare(expected['projection'],row['projection'],name)
    for record in report['mutations']:
        result = json.loads((output/(record['case_id']+'-reduced')/'result.json').read_text())
        expected = json.loads((CORPUS/'mutations'/(record['mutant']+'.json')).read_text())
        if (expected['case'] != cases[record['case_id']] or canonical(semantic_result(result)) != canonical(expected['result'])
                or record['signature'] != result['signature'] or record['status'] != result['status']
                or not record['expected_match'] or not result['one_minimal']):
            raise ValueError('interleaving reduction differs from pinned replay decisions')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'artifacts'/'interleaving-validation')
    args = parser.parse_args()
    receipt = verify_corpus()
    args.output.mkdir(parents=True)
    results, mutations = [], []
    for case in load_cases():
        try:
            result = run_case(case, args.output/case['case_id'])
            results.append(dict(case_id=case['case_id'], passed=True, **result))
            if case.get('mutant'):
                reduced = reduce_case(case, case['mutant'], args.output/(case['case_id']+'-reduced'))
                expected = json.loads((CORPUS/'mutations'/(case['mutant']+'.json')).read_text())['result']
                mutations.append(dict(case_id=case['case_id'], mutant=case['mutant'], status=reduced['status'],
                    original=len(case['events']), reduced=len(reduced['reduced_events']), evaluations=reduced['evaluations'], signature=reduced['signature'],
                    expected_match=canonical(semantic_result(reduced)) == canonical(expected)))
        except Exception as error:
            results.append(dict(case_id=case['case_id'], passed=False, error_type=type(error).__name__, error=str(error)))
    report = dict(schema='interleaving-validation/v1', corpus=receipt, results=results, mutations=mutations,
                  files={str(p.relative_to(args.output)): digest_file(p) for p in sorted(args.output.rglob('*')) if p.is_file()})
    write(args.output/'report.json', report)
    print(json.dumps(dict(results=results, mutations=mutations), indent=2))
    if not all(r['passed'] for r in results) or len(mutations) != 2 or any(m['status'] != 'ONE_MINIMAL' or not m['expected_match'] for m in mutations):
        raise SystemExit(1)
    verify_report(args.output)


if __name__ == '__main__':
    main()
