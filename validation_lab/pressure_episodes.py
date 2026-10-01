"""Frozen development episodes. Only `public` crosses the controller boundary."""
from copy import deepcopy


def rule(name, premises, conclusion):
    return dict(rule_id=name, revision='1', premises=premises, conclusion=conclusion)


def goal(name, condition, loss=1):
    return dict(goal_id=name, source_id='obligation:'+name, unit='verified-result', loss=loss, condition=condition)


def profile(atoms, rules, goals, probes, costs, priorities):
    return dict(schema='pressure-work-public/v1', admission=dict(schema='admission-initial/v1', atoms=atoms, rules=rules),
        context_id='reasoning', clauses=[], costs=costs, probes=probes, goals=goals,
        priorities={g['goal_id']: dict(unit='priority/'+g['unit'], revision='priority-v1',
            weight=priorities[g['goal_id']], urgency=1., commitment=1.) for g in goals})


def episodes(seed=7):
    # Seed changes a declared evaluator observation delay, never a controller
    # tie-breaker or its public capabilities. No tuning or held-out claim.
    delay = 2+seed % 2
    rich = profile(['seed', 'shared', 'measurement', 'detour', 'alternate', 'answer', 'side-result'],
        [rule('shared', [1], 2), rule('detour', [1], 4), rule('alternate', [4, 3], 5),
         rule('direct-answer', [2, 3], 6), rule('alternate-answer', [2, 5], 6), rule('side', [2], 7)],
        [goal('answer', {'AND': [2, 6]}, 3), goal('side', 7)],
        [dict(probe_id='seed', literal=1, cost=1), dict(probe_id='measurement', literal=3, cost=2)],
        {'shared': 1, 'detour': 1, 'alternate': 1, 'direct-answer': 3, 'alternate-answer': 1, 'side': 1},
        {'answer': 2., 'side': 1.})
    control = profile(['seed', 'answer'], [rule('answer', [1], 2)], [goal('answer', 2)],
        [dict(probe_id='seed', literal=1, cost=1)], {'answer': 1}, {'answer': 1.})
    return [dict(case_id='competing-routes', version='1', seed=seed, public=rich,
        world=dict(initial=[dict(literal=1, name='initial-seed')], probes={'seed': 0, 'measurement': delay},
                   revoke_at=4, revoke_evidence='initial-seed', truth=[1, 2, 3, 4, 5, 6, 7]),
        description='Two coherent inference routes, missing measurement, shared prerequisite, seed support revoked at tick 4.'),
        dict(case_id='simple-control', version='1', seed=seed, public=control,
        world=dict(initial=[dict(literal=1, name='initial-seed')], probes={'seed': 0},
                   revoke_at=None, revoke_evidence=None, truth=[1, 2]),
        description='One available inference then one outcome observation; pressure is not expected to help.')]


class ReasoningWorld:
    """Evaluator owns future events and physical truth; port exposes two methods."""
    def __init__(self, session, case):
        self.session, self.case = session, deepcopy(case)
        self.step, self.changed, self.events, self.outcomes = 0, False, [], []
        for item in case['world']['initial']:
            session.observe(item['literal'], item['name'])

    def sample_outcomes(self):
        # Independent finite interpretation of a supported proof. Ground truth
        # verifies the exact inferred result; an uncomputed proof is unresolved.
        from .pressure_reference import external_outcomes
        result = external_outcomes(self.case, self.session.read())
        row = dict(time=self.step, **result)
        if self.outcomes and self.outcomes[-1]['time'] == self.step:
            self.outcomes[-1] = row
        else:
            self.outcomes.append(row)
        return result

    def apply_changes(self):
        world = self.case['world']
        if not self.changed and world['revoke_at'] is not None and self.step >= world['revoke_at']:
            self.session.call('revoke_evidence', world['revoke_evidence'])
            self.changed = True
            self.events.append(dict(time=self.step, kind='revoke_evidence', evidence_id=world['revoke_evidence']))
            self.sample_outcomes()

    def idle_until(self, horizon):
        while self.step < horizon:
            self.apply_changes()
            self.step += 1
            self.session.tick(self.step)
            self.sample_outcomes()

    def execute(self, candidate, binding):
        world = self.case['world']
        self.apply_changes()
        args = dict(candidate.arguments)
        response = None
        if candidate.kind == 'observe':
            probe = next(p for p in self.case['public']['probes'] if p['probe_id'] == args['probe_id'])
            if self.step >= world['probes'].get(probe['probe_id'], 1000000):
                value = probe['literal'] if probe['literal'] in world['truth'] else -probe['literal']
                response = dict(literal=value, valid_until=None)
        elif candidate.kind == 'monitor':
            from .pressure_reference import condition_holds
            declared = next(g for g in self.case['public']['goals'] if g['goal_id'] == args['goal_id'])
            response = condition_holds(declared['condition'], set(world['truth']))
        receipt = self.session.execute(candidate, binding, response=response)
        self.step += 1
        self.session.tick(self.step)
        self.sample_outcomes()
        return receipt

    def port(self):
        world = self
        class PublicPort:
            def read(self):
                return world.session.read()

            def execute(self, candidate, snapshot_digest):
                return world.execute(candidate, snapshot_digest)
        return PublicPort()
