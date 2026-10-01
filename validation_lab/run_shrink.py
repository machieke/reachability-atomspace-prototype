"""Shrink source-pinned development witnesses and retain every attempted replay."""
import argparse
from copy import deepcopy
import json
from pathlib import Path

from .shrink_replay import ReplayPredicate, digest_file
from .trace_shrink import canonical, digest, shrink

ROOT = Path(__file__).resolve().parents[1]
CORPUS = Path('validation_lab/shrink_cases')
SEEDS = {
    'M05': ('admission', 'admission_cases', 'public/initial.json', 'evaluator/a14.json', None),
    'M06': ('deployment', 'deployment_cases', 'public/initial.json', 'evaluator/d01.json', None),
    'M07': ('deployment', 'b0_cases', 'public/b01.json', 'mutations/M07.json', 'deployment'),
    'M11': ('deployment', 'deployment_cases', 'public/initial.json', 'evaluator/d07.json', None),
}


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def source_seed(mutant, root=ROOT):
    profile, corpus, initial, case, selector = SEEDS[mutant]
    base = Path('validation_lab')/corpus
    initial_path, case_path, receipt = base/initial, base/case, base/'manifest.json'
    public = read(root/initial_path)
    if selector:
        public = public[selector]
    fixture = read(root/case_path)
    return dict(schema='trace-shrink-seed/v1', mutant=mutant, profile=profile, initial=public, case=fixture,
        source=dict(corpus_manifest=str(receipt), corpus_digest=digest_file(root/receipt),
                    initial_path=str(initial_path), initial_selector=selector, case_path=str(case_path),
                    parent_instance_id=fixture['parent_instance_id'], split=fixture['split']))


def source_paths():
    names = ['trace_shrink', 'shrink_replay', 'run_shrink', 'generate_shrink_cases', 'run_deployment',
             'run_admission', 'run_b0', 'b0_environment', 'admission_oracle', 'deployment_oracle', 'mutations']
    return sorted(['adapters.lock.json'] + ['validation_lab/'+name+'.py' for name in names] +
                  [str(p.relative_to(ROOT)) for p in (ROOT/'reachability').glob('*.py')])


def upstream_paths():
    paths = set()
    for _, corpus, initial, case, _ in SEEDS.values():
        paths.update(str(Path('validation_lab')/corpus/p) for p in ('manifest.json', initial, case))
    return sorted(paths)


def verify_corpus(root=ROOT):
    """Verify exact inventory, evaluator/runtime sources and original split ancestry."""
    receipt = read(root/CORPUS/'manifest.json')
    expected = {str(CORPUS/k/(m+'.json')) for k in ('seeds', 'expected') for m in SEEDS}
    actual = {str(p.relative_to(root)) for p in (root/CORPUS).rglob('*') if p.is_file() and p != root/CORPUS/'manifest.json'}
    if (receipt.get('schema') != 'trace-shrink-corpus/v1' or receipt.get('split') != 'development'
            or receipt.get('case_count') != len(SEEDS) or receipt.get('family_complete_fixtures') != 0
            or actual != expected or set(receipt['fixture_files']) != expected
            or set(receipt['source_files']) != set(source_paths()) or set(receipt['upstream_files']) != set(upstream_paths())):
        raise ValueError('shrink corpus inventory or scope differs from receipt')
    for group in ('fixture_files', 'source_files', 'upstream_files'):
        for name, expected_hash in receipt[group].items():
            if digest_file(root/name) != expected_hash:
                raise ValueError('shrink corpus digest mismatch: '+name)
    for mutant in SEEDS:
        seed = read(root/CORPUS/'seeds'/(mutant+'.json'))
        if canonical(seed) != canonical(source_seed(mutant, root)) or seed['source']['split'] != 'development':
            raise ValueError('shrink seed differs from its original source/ancestry')
    return receipt


def semantic_result(result):
    """Deterministic decisions/signatures; raw timing and UUID bytes stay in bundles."""
    value = deepcopy(result)
    value.pop('max_evaluations')  # Unused headroom does not change replay decisions.
    for trial in value['trials']:
        trial['assessment'].pop('artifacts', None)
    return value


def inventory(directory):
    return {str(p.relative_to(directory)): digest_file(p) for p in sorted(directory.rglob('*'))
            if p.is_file() and p != directory/'report.json'}


def run_seed(seed, output, *, max_evaluations=256, native=False, corpus=None):
    sources = {p: digest_file(ROOT/p) for p in source_paths()}
    output = Path(output)
    output.mkdir(parents=True)  # Never overwrite a previous run, even if incomplete.
    write(output/'seed.json', seed)
    write(output/'original.json', seed['case']['events'])
    predicate = ReplayPredicate(seed['profile'], seed['initial'], seed['case'], seed['mutant'], output/'trials', native=native)
    with (output/'attempts.jsonl').open('w') as log:
        def emit(row):
            log.write(canonical(row)+'\n')
            log.flush()
        result = shrink(seed['case']['events'], predicate, max_evaluations=max_evaluations, emit=emit)
    write(output/'reduced.json', result['reduced_events'])
    report = dict(schema='trace-shrink-bundle/v1', native_inference=native, source=seed['source'], source_files=sources, corpus=corpus,
                  result=result, files=inventory(output))
    write(output/'report.json', report)
    return report


def verify_bundle(directory):
    """Check recorded evidence integrity; this is not a fresh execution or signature."""
    directory = Path(directory)
    report = read(directory/'report.json')
    def require(condition, message):
        if not condition:
            raise ValueError('invalid shrink bundle: '+message)
    require(report['schema'] == 'trace-shrink-bundle/v1' and report['files'] == inventory(directory), 'file inventory/digests')
    require(set(report['source_files']) == set(source_paths()), 'source inventory')
    seed, result = read(directory/'seed.json'), report['result']
    original, reduced = read(directory/'original.json'), read(directory/'reduced.json')
    require(seed['source'] == report['source'], 'source ancestry')
    require(original == seed['case']['events'] == result['original_events'] and reduced == result['reduced_events'], 'event streams')
    require(digest(original) == result['original_digest'] and digest(reduced) == result['reduced_digest'], 'event digests')
    originals = {e['event_id']: e for e in original}
    require(len(originals) == len(original), 'unique identities')
    def subsequence(candidate, parent):
        ids = {e['event_id'] for e in candidate}
        return canonical([e for e in parent if e['event_id'] in ids]) == canonical(candidate)
    require(subsequence(reduced, original), 'order/arguments changed')
    require(result['removed_event_ids'] == [e['event_id'] for e in original if e not in reduced], 'removed identities')
    rows, log = result['trials'], [json.loads(line) for line in (directory/'attempts.jsonl').read_text().splitlines()]
    require(len(rows) == result['evaluations'] <= result['max_evaluations'] and len(log) == 2*len(rows), 'trial budget/log')
    candidates = []
    for index, row in enumerate(rows):
        path = directory/'trials'/f'{index:04d}'
        candidate, assessment = read(path/'events.json'), read(path/'assessment.json')
        require(row['trial'] == index and row['assessment'] == assessment, 'trial assessment')
        require(subsequence(candidate, original) and digest(candidate) == row['candidate_digest'], 'trial candidate')
        require(row['event_ids'] == [e['event_id'] for e in candidate], 'trial identities')
        request = {k: v for k, v in row.items() if k not in ('assessment', 'preserves_signature')}
        request['schema'] = 'trace-shrink-trial-request/v1'
        require(log[2*index] == request and log[2*index+1] == row, 'attempt log')
        artifacts = {p.name: dict(sha256=digest_file(p), bytes=p.stat().st_size) for p in path.iterdir() if p.name != 'assessment.json'}
        require(assessment['artifacts'] == artifacts, 'raw replay artifacts')
        preserved = assessment['kind'] == 'WITNESS' and canonical(assessment['signature']) == canonical(result['signature'])
        require(row['preserves_signature'] == preserved, 'failure signature')
        if assessment['kind'] == 'WITNESS':
            require(assessment['control_passed'] and assessment['invocations'] > 0, 'witness control/canary')
            require(assessment['control_recovered_prefixes'] == len(candidate), 'recovery control')
        candidates.append(candidate)
    if rows:
        require(candidates[0] == original and rows[0]['phase'] == 'original', 'original replay')
    current = original
    for accepted in result['accepted']:
        trial = rows[accepted['trial']]
        candidate = candidates[accepted['trial']]
        require(trial['preserves_signature'] and subsequence(candidate, current) and len(candidate) < len(current), 'accepted reduction')
        require(accepted['from_digest'] == trial['parent_digest'] == digest(current)
                and accepted['to_digest'] == digest(candidate), 'reduction chain')
        require(accepted['removed'] == trial['deleted_event_ids'] == [e['event_id'] for e in current if e not in candidate], 'deletion chain')
        current = candidate
    require(current == reduced, 'final reduction chain')
    if result['signature'] is not None:
        selected = result['selected_trial']
        require(rows[selected]['preserves_signature'] and candidates[selected] == reduced, 'selected witness')
    require(result['one_minimal'] == (result['status'] == 'ONE_MINIMAL') and result['global_minimum'] is False, 'minimality scope')
    if result['one_minimal']:
        final = result['final_trial']
        require(final == len(rows)-1 and rows[final]['phase'] == 'final-replay' and rows[final]['preserves_signature']
                and candidates[final] == reduced, 'fresh final replay')
        require(len(result['deletion_checks']) == len(reduced), 'deletion audit count')
        for index, check in enumerate(result['deletion_checks']):
            trial = rows[check['trial']]
            require(result['selected_trial'] < check['trial'] < final and trial['phase'] == 'single-deletion' and trial['parent_digest'] == digest(reduced)
                    and candidates[check['trial']] == reduced[:index]+reduced[index+1:], 'deletion audit candidate')
            require(check['removed_event_id'] == reduced[index]['event_id'] and check['kind'] == trial['assessment']['kind']
                    and check['preserves_signature'] is False and trial['preserves_signature'] is False
                    and check['kind'] in {'NO_WITNESS', 'INVALID', 'CONTROL_MISMATCH', 'WITNESS'}, 'decided deletion audit')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'artifacts'/'trace-shrinking')
    parser.add_argument('--max-evaluations', type=int, help='default: saved budget for replay, otherwise 256')
    parser.add_argument('--native', action='store_true', help='use native PLN inference for admission replays')
    parser.add_argument('--replay-bundle', type=Path, help='verify and rerun a saved bundle; require identical semantic decisions')
    args = parser.parse_args()
    receipt = verify_corpus()
    replay = verify_bundle(args.replay_bundle) if args.replay_bundle else None
    seeds = [read(args.replay_bundle/'seed.json')] if replay else [read(ROOT/CORPUS/'seeds'/(m+'.json')) for m in SEEDS]
    if replay and canonical(seeds[0]) != canonical(source_seed(seeds[0]['mutant'])):
        raise ValueError('saved bundle seed differs from pinned source')
    if replay and replay['source_files'] != receipt['source_files']:
        raise ValueError('saved bundle implementation sources differ from current receipt')
    args.output.mkdir(parents=True)
    results = []
    for seed in seeds:
        mutant = seed['mutant']
        output = args.output/mutant
        try:
            budget = args.max_evaluations if args.max_evaluations is not None else replay['result']['max_evaluations'] if replay else 256
            native = args.native or bool(replay and replay['native_inference'])
            report = run_seed(seed, output, max_evaluations=budget, native=native, corpus=receipt)
            verify_bundle(output)
            result = report['result']
            expected = semantic_result(replay['result']) if replay else read(ROOT/CORPUS/'expected'/(mutant+'.json'))
            matched = canonical(semantic_result(result)) == canonical(expected)
            results.append(dict(mutant=mutant, status=result['status'], original_events=len(result['original_events']),
                                reduced_events=len(result['reduced_events']), evaluations=result['evaluations'],
                                expected_match=matched, passed=result['one_minimal'] and matched))
        except Exception as error:
            entry = dict(mutant=mutant, passed=False, error_type=type(error).__name__, error=str(error))
            write(args.output/(mutant+'-error.json'), entry)
            results.append(entry)
    write(args.output/'report.json', dict(schema='trace-shrink-run/v1', corpus=receipt, results=results))
    print(json.dumps(results, indent=2))
    if not all(r['passed'] for r in results):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
