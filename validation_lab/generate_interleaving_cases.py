"""Explicit development controls plus every merge of two certify/reserve chains."""
import argparse
from itertools import combinations
from pathlib import Path

from .run_interleaving import ROOT, CORPUS, reduce_case, semantic_result, source_paths, write
from .shrink_replay import digest_file


def event(name, actor, kind, **arguments):
    return dict(schema='interleaving-event/v1', event_id=name, actor=actor, kind=kind, arguments=arguments)


def scenarios():
    cases = []
    def add(control, events, *, facts=(1,2), capacity=1, pair=(), mutant=None):
        cases.append(dict(schema='interleaving-case/v1', case_id=f'i{len(cases)+1:02}', parent_instance_id='interleaving-parent-0',
            split='development', control=control, public=dict(schema='interleaving-initial/v1', facts=list(facts), capacity=capacity),
            events=events, schedule=dict(schema='interleaving-schedule/v1', reserve_pair=list(pair)), mutant=mutant))
    prepare = event('prepare', 'a', 'prepare', literal=3)
    commit = event('commit', 'a', 'commit', prepared='prepare')
    policy = event('policy', 'b', 'policy', clauses=[[-1]])
    add('new-blocker-invalidation-and-stale-commit', [prepare, event('read','b','read'), policy, commit, event('end','a','read')], mutant='M08')
    add('blocker-after-commit', [prepare, commit, policy])
    add('blocked-new-conclusion', [event('policy','b','policy',clauses=[[-3]]), prepare, commit])
    add('joint-blocker-clears-conflicting-alternatives', [event('policy','b','policy',clauses=[[-1,-2]])])
    add('inconsistent-policy-rejected', [prepare, event('policy','b','policy',clauses=[[]]), commit])
    ca, cb = event('ca','a','certify'), event('cb','b','certify')
    ra, rb = event('ra','a','reserve',permit='ca'), event('rb','b','reserve',permit='cb')
    add('last-unit-a-first', [event('read','a','read'),ca,cb,ra,rb,event('end','b','read')], pair=('ra','rb'), mutant='M10')
    add('last-unit-b-first', [ca,cb,rb,ra], pair=('rb','ra'))
    add('missing-prerequisite', [ca,cb,ra,rb], facts=(), pair=('ra','rb'))
    add('zero-capacity', [ca,cb,ra,rb], capacity=0, pair=('ra','rb'))
    add('two-units-fresh-certificates', [ca,ra,cb,rb], capacity=2)
    add('blocker-before-reservation', [ca,policy,ra])
    add('positive-admission', [prepare,commit])
    add('competing-belief-publications', [prepare,event('other','b','prepare',literal=3),commit,event('second','b','commit',prepared='other')])
    add('wrong-owner-certificate', [ca,event('rb','b','reserve',permit='ca')])
    add('capacity-remains-but-old-certificate-is-stale', [ca,cb,ra,rb], capacity=2, pair=('ra','rb'))
    add('same-intent-retry-is-historical', [ca,ra,event('again','a','reserve',permit='ca')])
    # All six topological merges; choose which two slots belong to worker a.
    for slots in combinations(range(4),2):
        streams, order = {'a':iter((ca,ra)), 'b':iter((cb,rb))}, []
        for index in range(4):
            order.append(next(streams['a' if index in slots else 'b']))
        pair = tuple(e['event_id'] for e in order[-2:]) if all(e['kind']=='reserve' for e in order[-2:]) else ()
        add('exhaustive-two-worker-merge:'+''.join(e['actor'] for e in order), order, pair=pair)
    return cases


def generate(output):
    cases = scenarios()
    for case in cases:
        for folder, value in (('public',case['public']), ('evaluator',{k:v for k,v in case.items() if k!='public'})):
            (CORPUS/folder).mkdir(parents=True,exist_ok=True)
            write(CORPUS/folder/(case['case_id']+'.json'),value)
    (CORPUS/'mutations').mkdir(parents=True,exist_ok=True)
    output.mkdir(parents=True)
    for case in cases:
        if case['mutant']:
            result = reduce_case(case, case['mutant'], output/case['mutant'])
            if not result['one_minimal']:
                raise ValueError('unproven minimality: '+case['mutant'])
            write(CORPUS/'mutations'/(case['mutant']+'.json'), dict(case=case, result=semantic_result(result)))
            print(case['mutant'], len(case['events']), '->', len(result['reduced_events']), flush=True)
    fixtures = sorted(str(p.relative_to(ROOT)) for folder in ('public','evaluator','mutations') for p in (CORPUS/folder).glob('*.json'))
    receipt = dict(schema='interleaving-corpus/v1', split='development', parent_instance_id='interleaving-parent-0', case_count=len(cases),
        event_prefixes=sum(len(c['events']) for c in cases), family_complete_fixtures=0,
        fixture_files={p:digest_file(ROOT/p) for p in fixtures}, source_files={p:digest_file(ROOT/p) for p in source_paths()},
        scope='two actors; policy/commit command boundaries and one concurrent check/publication reservation pair; no dispatch race coverage')
    write(CORPUS/'manifest.json',receipt)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'artifacts'/'interleaving-generation')
    generate(parser.parse_args().output)
