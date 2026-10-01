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
