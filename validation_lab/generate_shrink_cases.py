"""Explicitly regenerate shrink witnesses from verified upstream development cases."""
import argparse
from pathlib import Path

from . import run_admission, run_b0, run_deployment
from .run_shrink import (CORPUS, ROOT, SEEDS, run_seed, semantic_result, source_paths,
                         source_seed, upstream_paths, verify_bundle, write)
from .shrink_replay import digest_file


def generate(output):
    for module in (run_admission, run_deployment, run_b0):
        module.verify_corpus()
    output = Path(output)
    output.mkdir(parents=True)
    for kind in ('seeds', 'expected'):
        (ROOT/CORPUS/kind).mkdir(parents=True, exist_ok=True)
    for mutant in SEEDS:
        seed = source_seed(mutant)
        report = run_seed(seed, output/mutant)
        verify_bundle(output/mutant)
        if not report['result']['one_minimal']:
            raise ValueError('unproven deletion minimality: '+mutant)
        write(ROOT/CORPUS/'seeds'/(mutant+'.json'), seed)
        write(ROOT/CORPUS/'expected'/(mutant+'.json'), semantic_result(report['result']))
        print(mutant, len(seed['case']['events']), '->', len(report['result']['reduced_events']), flush=True)
    fixtures = sorted(str(CORPUS/k/(m+'.json')) for k in ('seeds', 'expected') for m in SEEDS)
    receipt = dict(schema='trace-shrink-corpus/v1', split='development', case_count=len(SEEDS), family_complete_fixtures=0,
        fixture_files={p: digest_file(ROOT/p) for p in fixtures}, source_files={p: digest_file(ROOT/p) for p in source_paths()},
        upstream_files={p: digest_file(ROOT/p) for p in upstream_paths()},
        scope='bounded order-preserving whole-event deletion; identical first divergence with a passing independent control; no global minimum claim')
    write(ROOT/CORPUS/'manifest.json', receipt)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'artifacts'/'trace-shrinking-generation')
    generate(parser.parse_args().output)
