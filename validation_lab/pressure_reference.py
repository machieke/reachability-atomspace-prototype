"""Evaluator-only small-instance checks: direct elimination, not iteration."""
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import sys
from types import ModuleType


def linear_reference(source, routing, gamma):
    """Exact rational Gaussian elimination for supplied decimal coefficients."""
    n = len(source)
    f = lambda value: Fraction(str(value))
    matrix = [[Fraction(int(i == j))-f(gamma)*f(routing[i][j]) for j in range(n)]+[f(source[i])] for i in range(n)]
    for column in range(n):
        pivot = next(i for i in range(column, n) if matrix[i][column])
        matrix[column], matrix[pivot] = matrix[pivot], matrix[column]
        divisor = matrix[column][column]
        matrix[column] = [x/divisor for x in matrix[column]]
        for row in range(n):
            if row != column:
                coefficient = matrix[row][column]
                matrix[row] = [a-coefficient*b for a, b in zip(matrix[row], matrix[column])]
    return [float(row[-1]) for row in matrix]


def condition_holds(expression, facts):
    if isinstance(expression, int):
        return expression in facts
    if 'AND' in expression:
        return not any(not condition_holds(c, facts) for c in expression['AND'])
    return any(condition_holds(c, facts) for c in expression['OR'])


def external_outcomes(case, snapshot):
    facts = {s['literal'] for s in snapshot['supports']}
    truth = set(case['world']['truth'])
    loss, observed, goals = 0., 0., []
    for contract in case['public']['goals']:
        supported = condition_holds(contract['condition'], facts)
        correct = condition_holds(contract['condition'], truth)
        weight = case['public']['priorities'][contract['goal_id']]['weight']
        remaining = 0 if supported and correct else contract['loss']
        authority = next(g for g in snapshot['goals'] if g['goal_id'] == contract['goal_id'])
        loss += weight*remaining
        observed += weight*authority['outstanding']
        if authority['outstanding'] == 0 and (not supported or not correct):
            raise AssertionError('goal relief lacks a valid externally checked result')
        goals.append(dict(goal_id=contract['goal_id'], correct_supported_result=supported and correct,
                          external_loss=remaining, certified_outstanding=authority['outstanding']))
    return dict(external_weighted_loss=loss, certified_weighted_loss=observed, goals=goals)


def mutation_witness():
    """M09 changes the actual pressure source injection, not a fake result row."""
    from reachability.pressure import Node, Edge, Source, derive
    source_path = Path(__file__).resolve().parents[1]/'reachability/pressure.py'
    source = source_path.read_text()
    needle = 'd[source.root] = source.open_demand'
    assert source.count(needle) == 1
    replacement = "d[source.root] = _M09_STOCK.get(source.identity, 0.) + source.open_demand\n        _M09_STOCK[source.identity] = d[source.root]"
    changed = source.replace(needle, replacement)
    module = ModuleType('reachability._pressure_m09')
    module.__package__ = 'reachability'
    module.__dict__['_M09_STOCK'] = {}
    sys.modules[module.__name__] = module
    nodes = [Node('goal', 'AND', 'infer'), Node('work', 'LEAF', 'infer'), Node('monitor', 'LEAF', 'observe')]
    edges = [Edge('goal', 'work', 'teleological')]
    sources = [Source('ctx', 'canonical-obligation', 'slice', 'goal', 'results', 'priority/results', 'v1', 'goal', 'monitor', 10, 0)]
    try:
        exec(compile(changed, str(source_path)+'#M09', 'exec'), module.__dict__)
        correct = [derive({'revision': 1}, nodes, edges, sources) for _ in range(2)]
        mutant = [module.derive({'revision': 1}, nodes, edges, sources) for _ in range(2)]
        expected = linear_reference([10, 0], [[0, 0], [1, 0]], .85)[0]
        actual = [row['scores']['goal']['value'] for row in mutant]
        detected = correct[0] == correct[1] and actual[0] == expected and actual[1] != expected
        return dict(mutant='M09', detected=detected, expected_source_pressure=expected,
                    mutant_repeated_pressures=actual, unchanged_snapshot=True,
                    original_sha256=sha256(source.encode()).hexdigest(), mutant_sha256=sha256(changed.encode()).hexdigest(),
                    mechanism='repeated source injection accumulates prior demand in the actual solver')
    finally:
        sys.modules.pop(module.__name__, None)
