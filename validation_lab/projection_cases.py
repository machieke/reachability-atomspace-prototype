"""Declared syntax transformations and separate projection diagnostics."""
from copy import deepcopy
from itertools import product
import random

from reachability.pressure_work import check_condition
from .pressure_cost_ablation import diagnostic_cases as old_diagnostics
from .pressure_episodes import goal, profile, rule

BASES = {'and': {'AND': [2, 3, 4]}, 'or': {'OR': [2, 3, 4]},
         'and-or': {'AND': [2, {'OR': [3, 4]}]},
         'or-and': {'OR': [2, {'AND': [3, 4]}]}}


def transformed(condition, seed):
    """Only declared transformations; fixed seeds are not fitted to outcomes."""
    rng = random.Random(seed)
    def visit(value):
        if type(value) is int:
            tree = value
        else:
            op, children = next(iter(value.items()))
            children = [visit(child) for child in children]
            rng.shuffle(children)
            children.append(deepcopy(rng.choice(children)))
            if len(children) > 2:
                children = [{op: children[:2]}, *children[2:]]
            tree = {op: children}
        # Alternating operators defeat a special case that just strips ANDs.
        return {rng.choice(('AND', 'OR')): [tree]}
    result = visit(deepcopy(condition))
    check_condition(result, 5)
    return result


def truth_set(condition, atoms):
    """Independent exhaustive set algebra, not runtime holds/normalization."""
    universe = set(product((False, True), repeat=atoms))
    def interpret(tree):
        if type(tree) is int:
            return {world for world in universe if world[abs(tree)-1] == (tree > 0)}
        op, children = next(iter(tree.items()))
        values = [interpret(child) for child in children]
        return set.intersection(*values) if op == 'AND' else set.union(*values)
    return interpret(condition)


def mixed_case(family, seed=None):
    base = BASES[family]
    condition = deepcopy(base) if seed is None else transformed(base, seed)
    public = profile(['seed', 'a', 'b', 'c', 'low'],
        [rule('make-'+str(i), [1], i) for i in range(2, 6)],
        [goal('high', condition, 3), goal('low', 5)], [],
        {'make-'+str(i): 1 for i in range(2, 6)}, {'high': 1., 'low': 1.})
    return dict(case_id='mixed-'+family+('-base' if seed is None else '-'+str(seed)),
        version='projection-diagnostic/v1', seed=7, public=public,
        diagnostic=dict(family='mixed-transform', equivalence_group='mixed-'+family, transform_seed=seed),
        world=dict(initial=[dict(literal=1, name='initial-seed')], probes={},
                   revoke_at=None, revoke_evidence=None, truth=[1, 2, 3, 4, 5]),
        description='Scoped Boolean syntax changes only; four identical certified operations.')


def diagnostic_cases():
    cases = deepcopy(old_diagnostics())
    for case in cases:
        if case['diagnostic']['family'] == 'equivalent-condition-depth':
            case['diagnostic']['equivalence_group'] = 'wrapper-cost-'+str(case['diagnostic']['cost'])
    base = next(c for c in cases if c['case_id'] == 'depth-0-cost-1')
    for op, depths in (('AND', (1, 3, 5, 7)), ('OR', range(1, 9))):
        for depth in depths:
            case = deepcopy(base)
            condition = 2
            for _ in range(depth): condition = {op: [condition]}
            case['public']['goals'][0]['condition'] = condition
            case['case_id'] = f'wrapper-{op.lower()}-{depth}'
            case['diagnostic'].update(depth=depth, operator=op)
            cases.append(case)
    cases += [mixed_case(family, seed) for family in BASES for seed in (None, 11, 29, 47)]
    # Real epistemic depth is not a transparent Boolean wrapper. All operations
    # remain certified and consume one unit; this family is not equivalence data.
    for depth in (1, 2, 3):
        high = depth+1; low = depth+2
        rules = [rule('step-'+str(i), [i], i+1) for i in range(1, depth+1)]
        rules.append(rule('low', [1], low))
        public = profile(['seed']+['step-'+str(i) for i in range(depth)]+['low'], rules,
            [goal('high', high, 3), goal('low', low)], [],
            {r['rule_id']: 1 for r in rules}, {'high': 1., 'low': 1.})
        cases.append(dict(case_id=f'real-work-{depth}', version='projection-diagnostic/v1', seed=7,
            public=public, diagnostic=dict(family='real-operation-depth', operations=depth),
            world=dict(initial=[dict(literal=1, name='initial-seed')], probes={},
                revoke_at=None, revoke_evidence=None, truth=list(range(1, low+1))),
            description='Negative control: real proof operations and budget charges cannot be flattened.'))
    return cases
