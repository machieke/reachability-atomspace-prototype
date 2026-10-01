"""Independent exhaustive Boolean oracle using signed integer CNF fixtures.

No imports from the implementation under test; no shared solver, AST or cache.
"""
from itertools import product


def satisfying_assignment(clauses: tuple[tuple[int, ...], ...]) -> dict[int, bool] | None:
    variables = sorted({abs(literal) for clause in clauses for literal in clause})
    if any(variable == 0 for variable in variables):
        raise ValueError("signed oracle variables start at one")
    for values in product((False, True), repeat=len(variables)):
        assignment = dict(zip(variables, values))
        if all(any(assignment[abs(literal)] == (literal > 0) for literal in clause)
               for clause in clauses):
            return assignment
    return None


def requirement_truth(expression, facts):
    """Three-valued reference using plain tuples and Boolean/unknown observations."""
    operator, *children = expression
    if operator == "FACT":
        return facts.get(children[0])
    if operator == "ALWAYS":
        return True
    values = [requirement_truth(child, facts) for child in children]
    if operator == "AND":
        if False in values:
            return False
        return True if all(value is True for value in values) else None
    if operator == "OR":
        if True in values:
            return True
        return False if all(value is False for value in values) else None
    return None
