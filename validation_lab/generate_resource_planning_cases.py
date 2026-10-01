"""Development serial execution portfolios and evaluator-only outcome scripts."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from random import Random

from reachability.resource_planning import ResourcePublic
from reachability.resource_planning_session import event

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT/'validation_lab'/'resource_planning_cases'


def profile(modes=None, *, jobs=('a',), capacity=1, deadline=6, budget=20):
    modes = modes or [('a', 2, 2, [('cpu', 1)]), ('a', 4, 1, [('gpu', 1)])]
    return ResourcePublic.parse(dict(schema='resource-planning-public/v1', jobs=list(jobs),
        resources=[dict(resource_id=r, capacity=capacity, unit='slots') for r in ('cpu', 'gpu')],
        modes=[dict(mode_id=f'm{i}', revision='1', job_id=j, cost=c, duration=d,
                    demands=[dict(resource_id=r, quantity=q, unit='slots') for r, q in demands]) for i, (j, c, d, demands) in enumerate(modes)],
        deadline=deadline, work_budget=budget))


def ready(job='a', until=None):
    return event('ready-'+job, 'ready', job_id=job, valid_until=until)


def lease(name='x', resource='cpu', quantity=1, duration=3, remote=False):
    return event('lease-'+name, 'lease', hold_id=name, resource_id=resource, quantity=quantity, duration=duration, remote=remote)


def make_case(name, p, *, events=None, hooks=(), responses=None, faults=(), completed=True, objective=None, stop='OBSERVED_GOALS', visit_limit=50000):
    return dict(schema='resource-planning-case/v1', case_id=name, parent_instance_id='resource-planning-parent-0', split='development',
        public=dict(profile=p.wire(), events=[ready(j) for j in p.wire()['jobs']] if events is None else events),
        controls=[], hooks=deepcopy(list(hooks)), responses=responses or {}, faults=list(faults), visit_limit=visit_limit,
        expected=dict(completed=completed, objective=objective, stop_reason=stop))


def scenarios():
    cases=[]
    def case(p, control, **args):
        c=make_case(f'r{len(cases)+1:02}', p, **args)
        c['controls']=control
        cases.append(c)
    case(profile(), ['F03:cheap-complete-alternative'], objective=[2,2])
    case(profile(deadline=1), ['F03:fast-resource-alternative'], objective=[4,1])
    case(profile(deadline=1,budget=2), ['F03:incompatible-cost-time-pieces'], completed=False, stop='NO_CERTIFIABLE_PLAN')
    case(profile(), ['F03:half-open-lease-boundary'], events=[ready(),lease()], objective=[2,5])
    case(profile(capacity=2), ['F03:aggregate-capacity'], events=[ready(),lease()], objective=[2,2])
    case(profile([('a',1,2,[('cpu',1),('gpu',1)]),('a',3,1,[('gpu',1)])],deadline=2),
         ['F03:whole-multiple-resource-packet'], events=[ready(),lease(duration=3)], objective=[3,1])
    case(profile(), ['F08:occupancy-after-selection'], objective=[2,2], hooks=[dict(kind='reserve',occurrence=1,events=[lease()])])
    case(profile(), ['F08:revocation-before-dispatch'], completed=False, objective=[2,2], stop='PREREQUISITE_UNAVAILABLE',
         hooks=[dict(kind='dispatch',occurrence=1,events=[event('revoke','revoke',evidence_id='ready-a')])])
    case(profile(), ['F10:lost-acknowledgement'], objective=[2,2], faults=['lost_reply'])
    case(profile(), ['F10:failed-first-submit'], objective=[2,2], faults=['before_effect'])
    case(profile(), ['F10:wrong-product-then-correct'], objective=[2,2], responses={'m0':dict(wrong_until=3)})
    case(profile(deadline=2), ['F12:missing-completion'], completed=False, objective=[2,2], stop='DEADLINE', responses={'m0':None})
    case(profile([('a',1,1,[('cpu',1)])]), ['F14:uncertain-occupancy-after-lease-expiry'],
         events=[ready(),lease(duration=1,remote=True),event('later','tick',time=2)], completed=False, stop='NO_CERTIFIABLE_PLAN')
    portfolio=[('a',1,2,[('cpu',1)]),('a',3,1,[('gpu',1)]),('b',1,2,[('cpu',1)]),('b',3,1,[('gpu',1)])]
    case(profile(portfolio,jobs=('a','b'),deadline=3,budget=4), ['F03:whole-serial-portfolio'], objective=[4,3])
    case(profile(portfolio,jobs=('a','b'),deadline=3,budget=3), ['F03:combined-portfolio-cost'], completed=False, stop='NO_CERTIFIABLE_PLAN')
    case(profile(), ['F14:exclusive-prerequisite-expiry'], events=[ready(until=2)], objective=[4,1])
    case(profile(), ['F13:search-budget'], completed=False, stop='BUDGET_EXHAUSTED', visit_limit=0)
    case(profile(), ['F01:missing-ready-evidence'], events=[], completed=False, stop='NO_CERTIFIABLE_PLAN')
    case(profile(capacity=2), ['F08:remote-occupancy-before-dispatch'], completed=False, objective=[2,2], stop='REJECTED',
         hooks=[dict(kind='dispatch',occurrence=1,events=[lease(remote=True)])])
    case(profile(portfolio,jobs=('a','b'),deadline=4,budget=2), ['F12:delayed-outcome-invalidates-remaining-plan'],
         completed=False,objective=[2,4],stop='NO_CERTIFIABLE_PLAN',responses={'m0':dict(delay=1)})
    return cases


def generated_scenarios(seed=5107, count=8):
    rng, cases = Random(seed), []
    for i in range(count):
        p=profile([('a',rng.randrange(1,5),rng.randrange(1,4),[('cpu',1)]),('a',rng.randrange(1,5),rng.randrange(1,4),[('gpu',1)])],
                  deadline=rng.randrange(2,7),budget=rng.randrange(1,7),capacity=rng.randrange(1,3))
        c=make_case(f'generated-{seed}-{i}',p,events=[ready(),lease(duration=rng.randrange(1,5))])
        c['expected']=None
        cases.append(c)
    return cases


def write():
    cases=scenarios()
    files={CORPUS/'public'/(c['case_id']+'.json'):c['public'] for c in cases}
    files.update({CORPUS/'evaluator'/(c['case_id']+'.json'):{k:v for k,v in c.items() if k!='public'} for c in cases})
    for path,value in files.items():
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(value,indent=2)+'\n')
    sources=['validation_lab/'+name+'.py' for name in ('generate_resource_planning_cases','run_resource_planning','resource_planning_oracle','run_deployment')]
    sources += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'reachability').glob('*.py'))]
    receipt=dict(schema='resource-planning-corpus/v1',split='development',parent_instance_id='resource-planning-parent-0',case_count=len(cases),
        fixture_files={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in sorted(files)},
        source_files={p:sha256((ROOT/p).read_bytes()).hexdigest() for p in sources}, family_complete_fixtures=0,
        scope='serial renewable execution portfolios; conditional duration forecasts; no concurrent, consumable or optimal closed-loop claim')
    (CORPUS/'manifest.json').write_text(json.dumps(receipt,indent=2)+'\n')


if __name__=='__main__':
    write()
