#!/usr/bin/env python3
"""Selected reference checks for the Pressure-Field PLN lifecycle proposal.

Python 3.10+; standard library only.
Run: python pressure_field_lifecycle_reference_checks.py

These are numerical/accounting models, NOT an AtomSpace/PLN implementation,
external executor, complete certifier, or proof of end-to-end correctness.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Iterable, Sequence
import unittest


def nonnegative_finite(value: float, label: str) -> float:
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{label} must be finite and nonnegative")
    return value


@dataclass(frozen=True)
class PressureResult:
    values: tuple[float, ...]
    iterations: int
    residual_l1: float
    error_bound_l1: float
    converged: bool


def solve_pressure(
    source: Sequence[float],
    routing: Sequence[Sequence[float]],
    attenuation: float = 0.85,
    tolerance: float = 1e-10,
    max_iterations: int = 5000,
) -> PressureResult:
    """Solve p = d + attenuation * R @ p for a fixed substochastic R.

    R[i][j] routes the share at parent j to dependency i. Columns sum to
    at most one. The returned error bound uses the actual fixed-point
    residual, even when the iteration cap is reached.
    """
    if not math.isfinite(attenuation) or not 0 < attenuation < 1:
        raise ValueError("attenuation must be finite and strictly between 0 and 1")
    if not math.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("tolerance must be finite and positive")
    if not isinstance(max_iterations, int) or max_iterations < 1:
        raise ValueError("max_iterations must be a positive integer")
    d = tuple(nonnegative_finite(v, "source") for v in source)
    n = len(d)
    if not n or len(routing) != n or any(len(row) != n for row in routing):
        raise ValueError("routing must be square and match a nonempty source")
    r = tuple(tuple(nonnegative_finite(v, "routing coefficient") for v in row)
              for row in routing)
    if any(math.fsum(r[i][j] for i in range(n)) > 1.0 for j in range(n)):
        raise ValueError("each routing column must sum to at most one")

    def apply(p: Sequence[float]) -> tuple[float, ...]:
        result = tuple(d[i] + attenuation * math.fsum(
            r[i][j] * p[j] for j in range(n)) for i in range(n))
        if not all(math.isfinite(v) for v in result):
            raise ArithmeticError("pressure arithmetic overflow")
        return result

    p: tuple[float, ...] = (0.0,) * n
    target = tolerance * (1.0 + math.fsum(d))
    for iteration in range(1, max_iterations + 1):
        p = apply(p)
        residual = math.fsum(abs(x - y) for x, y in zip(apply(p), p))
        bound = residual / (1.0 - attenuation)
        if bound <= target:
            return PressureResult(p, iteration, residual, bound, True)
    return PressureResult(p, max_iterations, residual, bound, False)


def permitted_rate(gate_pass: bool, proposed_rate: float) -> float:
    """Illustrate gate-first evaluation: closed routes return zero."""
    if not gate_pass:
        return 0.0
    return nonnegative_finite(proposed_rate, "rate")


def transport_step(
    activation: Sequence[float], rates: Sequence[Sequence[float]]
) -> tuple[float, ...]:
    """One conservative step, rates[i][j] = nonnegative rate i -> j."""
    a = tuple(nonnegative_finite(v, "activation") for v in activation)
    n = len(a)
    if not n or len(rates) != n or any(len(row) != n for row in rates):
        raise ValueError("rates must be square and match nonempty activation")
    q = tuple(tuple(nonnegative_finite(v, "rate") for v in row) for row in rates)
    if any(q[i][i] != 0 for i in range(n)):
        raise ValueError("self rates must be zero; self allocation is derived")
    exits = tuple(math.fsum(row) for row in q)
    maximum_exit = max(exits)
    if maximum_exit == 0:
        return a
    dt = 0.9 / maximum_exit
    return tuple(a[i] * (1 - dt * exits[i]) + dt * math.fsum(
        a[j] * q[j][i] for j in range(n) if j != i) for i in range(n))


@dataclass(frozen=True)
class Coverage:
    slice_id: str
    loss_units: float
    expires_at: int


def open_loss(loss: float, commitments: Iterable[Coverage], now: int) -> float:
    """Conservative slice example, with explicit assumptions.

    Different slice IDs MUST already have been certified as disjoint.
    Claims within one slice overlap fully; use their maximum, not their sum.
    This is not a general probabilistic portfolio-coverage estimator.
    """
    outstanding = nonnegative_finite(loss, "loss")
    per_slice: dict[str, float] = {}
    for item in commitments:
        value = nonnegative_finite(item.loss_units, "coverage")
        if not item.slice_id:
            raise ValueError("slice identity is required")
        if item.expires_at <= now:
            continue
        per_slice[item.slice_id] = max(value, per_slice.get(item.slice_id, 0.0))
    covered = min(outstanding, math.fsum(per_slice.values()))
    return max(0.0, outstanding - covered)


def requirement_gate(statuses: Sequence[str], joint_check: str) -> bool:
    """Individual PASS statuses are insufficient without a joint PASS."""
    valid = {"PASS", "FAIL", "UNKNOWN", "STALE"}
    if joint_check not in valid or any(s not in valid for s in statuses):
        raise ValueError("unknown gate status")
    return joint_check == "PASS" and all(s == "PASS" for s in statuses)


def portfolio_fits(capacity: float, claims: Iterable[float]) -> bool:
    cap = nonnegative_finite(capacity, "capacity")
    return math.fsum(nonnegative_finite(c, "claim") for c in claims) <= cap


class ReferenceChecks(unittest.TestCase):
    def test_cycle_example_and_source_distinction(self) -> None:
        # source -> A -> B -> A. All columns sum to one.
        r = [[0.0, 0.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0]]
        result = solve_pressure([10.0, 0.0, 0.0], r, 0.8)
        expected = [10.0, 80.0 / 3.6, 64.0 / 3.6]
        self.assertTrue(result.converged)
        for actual, target in zip(result.values, expected):
            self.assertAlmostEqual(actual, target, places=8)
        self.assertAlmostEqual(math.fsum(result.values), 50.0, places=8)
        self.assertNotAlmostEqual(math.fsum(result.values), 10.0)

    def test_ungrounded_cycle_has_zero_pressure(self) -> None:
        result = solve_pressure([0.0, 0.0], [[0.0, 1.0], [1.0, 0.0]])
        self.assertEqual(result.values, (0.0, 0.0))

    def test_random_fixed_operator_bound(self) -> None:
        rng = random.Random(20260930)
        for _ in range(120):
            n = rng.randint(2, 8)
            r = [[rng.random() for _ in range(n)] for _ in range(n)]
            for j in range(n):
                total = math.fsum(r[i][j] for i in range(n))
                scale = rng.uniform(0.0, 0.98) / total
                for i in range(n):
                    r[i][j] *= scale
            d = [rng.uniform(0.0, 10.0) for _ in range(n)]
            gamma = rng.uniform(0.1, 0.95)
            result = solve_pressure(d, r, gamma)
            self.assertTrue(result.converged)
            self.assertTrue(all(v >= 0 for v in result.values))
            self.assertLessEqual(math.fsum(result.values),
                                 math.fsum(d) / (1.0 - gamma) + 1e-9)

    def test_iteration_cap_reported(self) -> None:
        result = solve_pressure([1.0], [[1.0]], 0.99, max_iterations=1)
        self.assertFalse(result.converged)
        self.assertGreater(result.error_bound_l1, 1.0)

    def test_invalid_pressure_operator_rejected(self) -> None:
        with self.assertRaises(ValueError):
            solve_pressure([1.0], [[1.01]])
        with self.assertRaises(ValueError):
            solve_pressure([1.0], [[-0.1]])
        with self.assertRaises(ValueError):
            solve_pressure([1.0], [[1.0]], attenuation=1.0)

    def test_gate_first_even_for_nonfinite_rates(self) -> None:
        for rate in [0.0, 1e200, math.inf, math.nan]:
            self.assertEqual(permitted_rate(False, rate), 0.0)
        with self.assertRaises(ValueError):
            permitted_rate(True, math.nan)

    def test_random_transport_conservation(self) -> None:
        rng = random.Random(9917)
        for _ in range(500):
            n = rng.randint(2, 10)
            a = [rng.random() for _ in range(n)]
            q = [[0.0 if i == j else permitted_rate(
                rng.random() > 0.35, rng.random() * 20.0)
                for j in range(n)] for i in range(n)]
            after = transport_step(a, q)
            self.assertTrue(all(v >= -1e-14 for v in after))
            self.assertAlmostEqual(math.fsum(a), math.fsum(after), places=12)

    def test_zero_rate_transport_preserves_allocation(self) -> None:
        self.assertEqual(transport_step([0.1, 0.9], [[0, 0], [0, 0]]),
                         (0.1, 0.9))

    def test_coverage_is_not_observed_relief(self) -> None:
        loss = 10.0
        self.assertEqual(open_loss(loss, [Coverage("slice-A", 6, 100)], now=1), 4)
        self.assertEqual(loss, 10.0)

    def test_duplicate_slice_not_double_covered(self) -> None:
        commitments = [Coverage("slice-A", 6, 100), Coverage("slice-A", 6, 100)]
        self.assertEqual(open_loss(10, commitments, now=1), 4)

    def test_expiry_reopens_demand(self) -> None:
        commitments = [Coverage("slice-A", 6, 100)]
        self.assertEqual(open_loss(10, commitments, now=100), 10)

    def test_disjoint_coverage_capped(self) -> None:
        commitments = [Coverage("slice-A", 6, 100), Coverage("slice-B", 5, 100)]
        self.assertEqual(open_loss(10, commitments, now=1), 0)

    def test_all_individual_and_joint_requirements(self) -> None:
        self.assertTrue(requirement_gate(["PASS", "PASS"], "PASS"))
        self.assertFalse(requirement_gate(["PASS", "PASS"], "FAIL"))
        for missing in ["FAIL", "UNKNOWN", "STALE"]:
            self.assertFalse(requirement_gate(["PASS", missing], "PASS"))

    def test_resource_portfolio_not_individual_feasibility(self) -> None:
        self.assertTrue(portfolio_fits(1, [1]))
        self.assertFalse(portfolio_fits(1, [1, 1]))

    def test_complementary_plan_value(self) -> None:
        def relief(completed: set[str]) -> float:
            return 4.0 if {"A", "B"} <= completed else 0.0
        self.assertEqual(relief({"A"}), 0.0)
        self.assertEqual(relief({"B"}), 0.0)
        self.assertEqual(relief({"A", "B"}) - 2.0, 2.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
