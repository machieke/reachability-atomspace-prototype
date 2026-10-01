"""Bounded complete CNF checking by unit propagation and deterministic branching.

The independent evaluator uses truth-table enumeration, never this module.
"""
from __future__ import annotations

from dataclasses import dataclass

from .model import Clause, Literal, Statement, Status


@dataclass(frozen=True, slots=True)
class LogicResult:
    status: Status
    witness: tuple[tuple[Statement, bool], ...] | None
    detail: str


def check_consistency(
    clauses: tuple[Clause, ...],
    assertions: tuple[Literal, ...] = (),
    *,
    max_variables: int = 16,
) -> LogicResult:
    if type(max_variables) is not int or not 0 <= max_variables <= 20:
        raise ValueError("finite checker capacity must be an integer between 0 and 20")
    if any(not isinstance(c, Clause) for c in clauses):
        return LogicResult(Status.UNKNOWN, None, "unsupported constraint schema")
    if any(not isinstance(a, Literal) for a in assertions):
        return LogicResult(Status.UNKNOWN, None, "unsupported assertion schema")
    cnf = tuple(frozenset(c.literals) for c in clauses) + tuple(
        frozenset((a,)) for a in assertions
    )
    variables = sorted({literal.statement for clause in cnf for literal in clause})
    if len(variables) > max_variables:
        return LogicResult(Status.UNKNOWN, None, "complete scope exceeds variable capacity")

    def search(
        pending: tuple[frozenset[Literal], ...], assignment: dict[Statement, bool]
    ) -> dict[Statement, bool] | None:
        while pending:
            if any(not clause for clause in pending):
                return None
            unit = next((next(iter(c)) for c in pending if len(c) == 1), None)
            if unit is None:
                chosen = min(min(c) for c in pending)
                for value in (chosen, chosen.negate()):
                    result = search(pending + (frozenset((value,)),), dict(assignment))
                    if result is not None:
                        return result
                return None
            assignment[unit.statement] = unit.positive
            pending = tuple(c - {unit.negate()} for c in pending if unit not in c)
        return assignment

    solution = search(cnf, {})
    if solution is None:
        return LogicResult(Status.FAIL, None, "joint hard-claim set is unsatisfiable")
    witness = tuple((variable, solution.get(variable, False)) for variable in variables)
    return LogicResult(Status.PASS, witness, "complete finite CNF model found")
