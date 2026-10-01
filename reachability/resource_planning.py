"""Bounded serial execution portfolios over immutable renewable contracts.

Durations predict observation time, never authorize resource release. Scheduling
is advisory; the execution service still certifies reservations and dispatch.
"""
from dataclasses import dataclass

from .execution_model import ResourceClaim, ResourceDefinition
from .grounded_planning import bounded
from .model import Status
from .resources import check_capacity
from .trace_protocol import canonical, fingerprint, identifier, read_json

PUBLIC_SCHEMA = 'resource-planning-public/v1'
SNAPSHOT_SCHEMA = 'resource-planning-snapshot/v1'


def fields(value, names):
    if type(value) is not dict or set(value) != set(names.split()):
        raise ValueError('invalid resource planning fields')


def array(value, limit, minimum=0):
    if type(value) is not list or not minimum <= len(value) <= limit:
        raise ValueError('invalid bounded planning array')


@dataclass(frozen=True)
class ResourcePublic:
    description_json: str

    def __post_init__(self):
        v = read_json(self.description_json)
        fields(v, 'schema jobs resources modes deadline work_budget')
        if v['schema'] != PUBLIC_SCHEMA:
            raise ValueError('unsupported resource planning schema')
        array(v['jobs'], 3, 1)
        array(v['resources'], 3, 1)
        array(v['modes'], 6, 1)
        for job in v['jobs']:
            identifier(job)
        if len(set(v['jobs'])) != len(v['jobs']):
            raise ValueError('duplicate job')
        resources = {}
        for r in v['resources']:
            fields(r, 'resource_id capacity unit')
            identifier(r['resource_id'])
            identifier(r['unit'])
            bounded(r['capacity'], 4)
            if r['resource_id'] in resources:
                raise ValueError('duplicate resource')
            resources[r['resource_id']] = r
        seen, jobs = set(), set()
        for m in v['modes']:
            fields(m, 'mode_id revision job_id cost duration demands')
            for key in ('mode_id', 'revision', 'job_id'):
                identifier(m[key])
            if m['mode_id'] in seen or m['job_id'] not in v['jobs']:
                raise ValueError('duplicate mode or undeclared job')
            seen.add(m['mode_id'])
            jobs.add(m['job_id'])
            bounded(m['cost'], 20, 1)
            bounded(m['duration'], 4, 1)
            array(m['demands'], 3, 1)
            used = set()
            for d in m['demands']:
                fields(d, 'resource_id quantity unit')
                identifier(d['resource_id'])
                identifier(d['unit'])
                if d['resource_id'] not in resources or d['resource_id'] in used or d['unit'] != resources[d['resource_id']]['unit']:
                    raise ValueError('invalid exact resource demand')
                bounded(d['quantity'], 4, 1)
                used.add(d['resource_id'])
        if jobs != set(v['jobs']):
            raise ValueError('every job requires a declared alternative')
        bounded(v['deadline'], 8)
        bounded(v['work_budget'], 100)
        object.__setattr__(self, 'description_json', canonical(v))

    def wire(self):
        return read_json(self.description_json)

    @classmethod
    def parse(cls, value):
        return cls(canonical(value))


def validate_snapshot(public, s):
    p = public.wire()
    fields(s, 'schema public_digest time knowledge_revision resource_revision jobs holds active remaining_work')
    if s['schema'] != SNAPSHOT_SCHEMA or s['public_digest'] != fingerprint(p):
        raise ValueError('snapshot/profile mismatch')
    for key in ('time', 'knowledge_revision', 'resource_revision'):
        bounded(s[key], 1000000)
    bounded(s['remaining_work'], p['work_budget'])
    if type(s['jobs']) is not dict or set(s['jobs']) != set(p['jobs']):
        raise ValueError('snapshot jobs mismatch')
    for j in s['jobs'].values():
        fields(j, 'completed ready ready_until')
        if type(j['completed']) is not bool or type(j['ready']) is not bool:
            raise ValueError('typed readiness required')
        if j['ready_until'] is not None:
            bounded(j['ready_until'], 1000)
            if not j['ready'] or j['ready_until'] <= s['time']:
                raise ValueError('invalid current prerequisite lifetime')
    array(s['holds'], 24)
    resources = {r['resource_id']: r for r in p['resources']}
    for h in s['holds']:
        fields(h, 'attempt resource_id quantity unit start end uncertain')
        identifier(h['attempt'])
        identifier(h['resource_id'])
        identifier(h['unit'])
        if h['resource_id'] not in resources or h['unit'] != resources[h['resource_id']]['unit'] or type(h['uncertain']) is not bool:
            raise ValueError('invalid held resource')
        bounded(h['quantity'], 4, 1)
        bounded(h['start'], 1000)
        bounded(h['end'], 1000, h['start']+1)
    if s['active'] is not None:
        fields(s['active'], 'attempt job_id mode_id dispatch completed')
        identifier(s['active']['attempt'])
        modes = {m['mode_id']: m for m in p['modes']}
        a = s['active']
        identifier(a['mode_id'])
        identifier(a['job_id'])
        if a['mode_id'] not in modes or modes[a['mode_id']]['job_id'] != a['job_id'] or a['dispatch'] not in (None, 'accepted', 'uncertain', 'released') or type(a['completed']) is not bool:
            raise ValueError('invalid active execution')


def step(mode, start):
    return dict(job_id=mode['job_id'], mode_id=mode['mode_id'], revision=mode['revision'],
                start=start, end=start+mode['duration'], cost=mode['cost'], demands=mode['demands'])


def search(public, snapshot, *, visit_limit=50000):
    """Exhaust bounded serial schedules; compare whole interval portfolios."""
    validate_snapshot(public, snapshot)
    bounded(visit_limit, 500000)
    p, s = public.wire(), snapshot
    if s['active'] is not None:
        raise ValueError('resolve and release the active operation before replanning')
    work = dict(candidates=0, capacity_checks=0, complete_plans=0)
    best, exhausted = None, False
    resources = {r['resource_id']: ResourceDefinition(**r) for r in p['resources']}
    blocked = {h['resource_id'] for h in s['holds'] if h['uncertain']}
    initial = [ResourceClaim(h['resource_id'], h['quantity'], h['unit'], h['start'], h['end']) for h in s['holds']]
    remaining = {j for j in p['jobs'] if not s['jobs'][j]['completed']}
    def visit(todo, now, cost, path, claims):
        nonlocal best, exhausted
        if exhausted:
            return
        if not todo:
            if now <= p['deadline']:
                work['complete_plans'] += 1
                rank = cost, now, canonical(path)
                if best is None or rank < best[0]:
                    best = rank, path
            return
        for job in sorted(todo):
            info = s['jobs'][job]
            for mode in sorted((m for m in p['modes'] if m['job_id'] == job), key=lambda m: m['mode_id']):
                for start in range(now, p['deadline']-mode['duration']+1):
                    if work['candidates'] >= visit_limit:
                        exhausted = True
                        return
                    work['candidates'] += 1
                    end, total = start+mode['duration'], cost+mode['cost']
                    if not info['ready'] or info['ready_until'] is not None and end >= info['ready_until']:
                        continue
                    if total > s['remaining_work'] or best is not None and total > best[0][0]:
                        continue
                    if any(d['resource_id'] in blocked for d in mode['demands']):
                        continue
                    added = [ResourceClaim(d['resource_id'], d['quantity'], d['unit'], start, end) for d in mode['demands']]
                    portfolio = claims+added
                    valid = True
                    for r in resources.values():
                        work['capacity_checks'] += 1
                        if check_capacity(r, tuple(c for c in portfolio if c.resource_id == r.resource_id)).status is not Status.PASS:
                            valid = False
                            break
                    if valid:
                        visit(todo-{job}, end, total, path+[step(mode, start)], portfolio)
    visit(remaining, s['time'], 0, [], initial)
    status = 'BUDGET_EXHAUSTED' if exhausted else 'SOLVED' if best else 'NO_CERTIFIABLE_PLAN'
    plan = None if status != 'SOLVED' else dict(schema='resource-plan/v1', snapshot_digest=fingerprint(s),
        steps=best[1], cost=best[0][0], finishes_at=best[0][1])
    return dict(status=status, plan=plan, work=work)


class ResourceController:
    """Complete serial portfolios; only delivered observations establish outcomes."""
    def __init__(self, public):
        self.public = ResourcePublic.parse(public.wire())
        self.observed = set()
        self.reconciled = set()

    def run(self, port, *, requests=64, visit_limit=50000, emit=None):
        bounded(requests, 128)
        records = []
        for index in range(requests):
            s = port.read()
            validate_snapshot(self.public, s)
            plan, work = None, None
            active, now = s['active'], s['time']
            if active is None:
                found = search(self.public, s, visit_limit=visit_limit)
                plan, work = found['plan'], found['work']
                stop = found['status'] if plan is None else 'OBSERVED_GOALS' if not plan['steps'] else None
                kind = None if stop else 'wait' if plan['steps'][0]['start'] > now else 'reserve'
                until = plan['steps'][0]['start'] if kind == 'wait' else None
            else:
                stop, until = None, None
                if active['completed']:
                    kind = 'release'
                elif not s['jobs'][active['job_id']]['ready']:
                    kind, stop = None, 'PREREQUISITE_UNAVAILABLE'
                elif now > self.public.wire()['deadline']:
                    kind, stop = None, 'DEADLINE'
                elif active['dispatch'] is None:
                    kind = 'dispatch'
                elif active['dispatch'] == 'uncertain':
                    kind = 'dispatch' if active['attempt'] in self.reconciled else 'reconcile'
                elif (active['attempt'], now) not in self.observed:
                    kind = 'observe'
                elif now == self.public.wire()['deadline']:
                    kind, stop = None, 'DEADLINE'
                else:
                    kind, until = 'wait', now+1
            action = None if stop else dict(schema='resource-action/v1', kind=kind, snapshot_digest=fingerprint(s),
                                           plan=plan if kind == 'reserve' else None, until=until)
            row = dict(schema='resource-controller-step/v1', index=index, snapshot_digest=fingerprint(s),
                       plan=plan, search_work=work, action=action, stop_reason=stop)
            if emit:
                emit(row)
            records.append(row)
            if stop:
                return dict(stop_reason=stop, records=records)
            receipt = port.execute(action)
            if active is not None and receipt['status'] != 'STALE':
                if kind == 'observe':
                    self.observed.add((active['attempt'], now))
                elif kind == 'reconcile':
                    self.reconciled.add(active['attempt'])
            row['receipt'] = receipt
            if emit:
                emit(dict(schema='resource-controller-receipt/v1', index=index, receipt=receipt))
            if receipt['status'] not in ('PASS', 'STALE') and kind != 'observe':
                return dict(stop_reason='REJECTED', records=records)
        return dict(stop_reason='REQUEST_BUDGET', records=records)
