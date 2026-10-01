"""Independent tiny occupancy enumeration and cold serial-execution model.

Only standard-library imports. No runtime, capacity sweep, fixtures or search
results are available to the reference algorithms.
"""
from copy import deepcopy
from itertools import permutations, product


class OracleGap(ValueError):
    pass


def feasible(public, snapshot, steps):
    modes = {m['mode_id']: m for m in public['modes']}
    jobs = {j for j in public['jobs'] if not snapshot['jobs'][j]['completed']}
    now, cost, claims = snapshot['time'], 0, list(snapshot['holds'])
    seen = set()
    for s in steps:
        m = modes[s['mode_id']]
        if s != dict(job_id=m['job_id'], mode_id=m['mode_id'], revision=m['revision'], start=s['start'],
                     end=s['start']+m['duration'], cost=m['cost'], demands=m['demands']):
            return None
        info = snapshot['jobs'][m['job_id']]
        if m['job_id'] in seen or m['job_id'] not in jobs or s['start'] < now or s['end'] > public['deadline'] or not info['ready']:
            return None
        if info['ready_until'] is not None and s['end'] >= info['ready_until']:
            return None
        if any(h['uncertain'] and h['resource_id'] == d['resource_id'] for h in snapshot['holds'] for d in m['demands']):
            return None
        seen.add(m['job_id'])
        cost += m['cost']
        now = s['end']
        claims += [dict(**d, start=s['start'], end=s['end']) for d in m['demands']]
    if seen != jobs or cost > snapshot['remaining_work'] or now > public['deadline']:
        return None
    # Discrete unit-time occupancy, independent of the runtime interval sweep.
    for tick in range(max([public['deadline']]+[c['end'] for c in claims])):
        for r in public['resources']:
            used = sum(c['quantity'] for c in claims if c['resource_id'] == r['resource_id'] and c['start'] <= tick < c['end'])
            if used > r['capacity']:
                return None
    return [cost, now]


def exact_plan(public, snapshot, *, candidate_limit=200000):
    if public.get('schema') != 'resource-planning-public/v1' or snapshot.get('schema') != 'resource-planning-snapshot/v1':
        raise OracleGap('unsupported reference schema')
    if len(public['jobs']) > 3 or len(public['modes']) > 6 or public['deadline'] > 8 or snapshot['active'] is not None:
        raise OracleGap('outside tiny idle serial profile')
    if type(candidate_limit) is not int or candidate_limit < 0:
        raise OracleGap('invalid reference budget')
    jobs = [j for j in public['jobs'] if not snapshot['jobs'][j]['completed']]
    choices = {j: [m for m in public['modes'] if m['job_id'] == j] for j in jobs}
    best, visits = None, 0
    for order in permutations(jobs):
        for modes in product(*(choices[j] for j in order)):
            for starts in product(range(snapshot['time'], public['deadline']+1), repeat=len(order)):
                if visits >= candidate_limit:
                    return dict(status='NOT_COMPUTED', objective=None, candidates=visits)
                visits += 1
                steps = [dict(job_id=m['job_id'], mode_id=m['mode_id'], revision=m['revision'], start=t,
                    end=t+m['duration'], cost=m['cost'], demands=m['demands']) for m, t in zip(modes, starts)]
                objective = feasible(public, snapshot, steps)
                if objective is not None and (best is None or objective < best):
                    best = objective
    return dict(status='SOLVED' if best is not None else 'NO_CERTIFIABLE_PLAN', objective=best, candidates=visits)


def reference_prefix(public, events):
    """Reconstruct the declared event profile from scratch at each boundary."""
    now, spent, active, effects = 0, 0, None, 0
    facts, attempts, contracts, revoked, observations = {}, {}, {}, set(), {}
    built = set()
    modes = {m['mode_id']: m for m in public['modes']}
    resources = {r['resource_id']: r for r in public['resources']}
    def current(eid):
        f = facts[eid]
        return eid not in revoked and (f['valid_until'] is None or now < f['valid_until'])
    def ready(job):
        candidates = [eid for eid, f in facts.items() if f['predicate'] == 'PortfolioReady' and f['arguments'] == [job]]
        return 'PASS' if any(current(e) for e in candidates) else 'STALE' if candidates else 'UNKNOWN'
    def completed(job):
        return job in built and any(current(eid) for eid, f in facts.items()
                                   if f['predicate'] == 'Available' and f['arguments'] == ['product:'+job])
    def add(eid, predicate, args, until=None):
        facts[eid] = dict(predicate=predicate, arguments=args, valid_until=until)
    def holds():
        out = []
        for attempt, a in attempts.items():
            if a['intent'] is None or a['dispatch'] == 'released':
                continue
            uncertain = a['dispatch'] is not None
            if now >= a['intent']['end'] and not uncertain:
                continue
            for d in contracts[attempt]:
                out.append(dict(attempt=attempt, **d, start=a['intent']['start'], end=a['intent']['end'], uncertain=uncertain))
        return sorted(out, key=lambda h: (h['attempt'], h['resource_id']))
    def capacity(demands, end, exclude=None):
        occupied = [h for h in holds() if h['attempt'] != exclude]
        uncertain = any(h['uncertain'] and h['resource_id'] == d['resource_id'] for h in occupied for d in demands)
        for d in demands:
            r = resources[d['resource_id']]
            for t in range(now, end):
                if d['quantity']+sum(h['quantity'] for h in occupied if h['resource_id'] == r['resource_id'] and h['start'] <= t < h['end']) > r['capacity']:
                    return 'FAIL'
        return 'UNKNOWN' if uncertain else 'PASS'
    def reserve(attempt, demands, duration, prerequisite):
        attempts[attempt] = dict(intent=None, dispatch=None, milestones=[])
        contracts[attempt] = demands
        statuses = [capacity(demands, now+duration), prerequisite]
        status = next((s for s in ('FAIL', 'STALE', 'UNKNOWN') if s in statuses), 'PASS')
        if status == 'PASS':
            attempts[attempt]['intent'] = dict(state='pending', start=now, end=now+duration)
        return status
    status = 'PASS'
    for event in events:
        kind, a, eid = event['kind'], event['arguments'], event['event_id']
        status = 'PASS'
        if kind == 'ready':
            if a['valid_until'] is not None and a['valid_until'] <= now:
                raise OracleGap('invalid observation time in reference profile')
            add(eid, 'PortfolioReady', [a['job_id']], a['valid_until'])
        elif kind == 'revoke':
            revoked.add(a['evidence_id'])
        elif kind == 'tick':
            if a['time'] < now:
                raise OracleGap('backwards time')
            now = a['time']
        elif kind == 'lease':
            r = resources[a['resource_id']]
            attempt = 'hold:'+a['hold_id']
            demands = [dict(resource_id=r['resource_id'], quantity=a['quantity'], unit=r['unit'])]
            status = reserve(attempt, demands, a['duration'], 'PASS')
            if status == 'PASS' and a['remote']:
                attempts[attempt]['dispatch'] = 'accepted'
                effects += 1
        elif kind == 'reserve':
            m = modes[a['mode_id']]
            if a['revision'] != m['revision']:
                status = 'STALE'
            elif active is not None or spent+m['cost'] > public['work_budget']:
                status = 'FAIL'
            else:
                spent += m['cost']
                prerequisite = 'FAIL' if m['job_id'] in built else ready(m['job_id'])
                status = reserve(a['attempt_id'], m['demands'], m['duration'], prerequisite)
                if status == 'PASS':
                    active = dict(attempt=a['attempt_id'], job_id=m['job_id'], mode_id=m['mode_id'])
        elif kind == 'dispatch':
            x = attempts[active['attempt']]
            checks = [ready(active['job_id']), capacity(contracts[active['attempt']], x['intent']['end'], active['attempt'])]
            if now >= x['intent']['end']:
                checks.append('STALE')
            status = next((s for s in ('FAIL', 'STALE', 'UNKNOWN') if s in checks), 'PASS')
            if status == 'PASS':
                x['dispatch'] = 'accepted' if a['fault'] == 'none' else 'uncertain'
                x['effect'] = a['fault'] != 'before_effect'
                effects += int(x['effect'])
        elif kind == 'reconcile':
            x = attempts[active['attempt']]
            if x['dispatch'] == 'uncertain' and x.get('effect'):
                x['dispatch'] = 'accepted'
        elif kind == 'release':
            attempts[active['attempt']]['dispatch'] = 'released'
            active = None
        elif kind == 'outcome':
            attempt, job = active['attempt'], active['job_id']
            add(eid+':product', 'Available', [a['product_id']])
            for milestone in ('completion_observed', 'exact_product_observed'):
                add(eid+':'+milestone, 'rd:operation/'+milestone, [attempt, a['product_id']])
                if a['product_id'] != 'product:'+job:
                    status = 'FAIL'
                    break
                attempts[attempt]['milestones'] = sorted(set(attempts[attempt]['milestones']) | {milestone})
                observations.setdefault(attempt, {}).setdefault(milestone, []).append(eid+':'+milestone)
            if status == 'PASS':
                status = 'FAIL' if job in built else ready(job)
                if status == 'PASS':
                    built.add(job)
        elif kind != 'restart':
            raise OracleGap('unknown reference event')
    projected = {}
    for name, a in attempts.items():
        intent = deepcopy(a['intent'])
        if intent is not None:
            intent['state'] = 'released' if a['dispatch'] == 'released' else 'reconciliation_required' if a['dispatch'] is not None else 'expired' if now >= intent['end'] else 'pending'
        milestones = sorted(m for m, ids in observations.get(name, {}).items() if any(current(eid) for eid in ids))
        projected[name] = dict(intent=intent, dispatch=a['dispatch'], milestones=milestones)
    jobs = {}
    for job in public['jobs']:
        lives = [f['valid_until'] for eid, f in facts.items() if f['predicate'] == 'PortfolioReady' and f['arguments'] == [job] and current(eid)]
        available = bool(lives) and job not in built
        jobs[job] = dict(completed=completed(job), ready=available, ready_until=None if not available or None in lives else max(lives))
    return dict(status=status, executor_effects=effects, projection=dict(time=now, jobs=jobs, holds=holds(), spent=spent,
        active=None if active is None else dict(**active, dispatch=attempts[active['attempt']]['dispatch'], completed=completed(active['job_id'])),
        facts={eid: dict(**f, current=current(eid)) for eid, f in sorted(facts.items())}, attempts=projected))
