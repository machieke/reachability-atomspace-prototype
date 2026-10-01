"""Small non-actuating mutation witnesses, not performance baselines.

Each test first proves the valid service blocks the violation, then deliberately
breaks one contract and proves the same public scenario exposes that violation.
This initial set covers M01–M04. M05 lives in test_admission_traces.py;
M06/M11 live in test_deployment_traces.py. The bounded B0 suite adds the
deletion-minimal M07 product-binding witness. M08–M10 and M12 stay open.
"""
from dataclasses import replace
from itertools import combinations
import unittest
from unittest.mock import patch

from reachability import model
from reachability.logic import LogicResult, check_consistency
from reachability.model import Check, Clause, Rule, Status
from reachability.service import AdmissionDenied, AdmissionService
from tests.support import Driver, lit

A, B, C = lit("A"), lit("B"), lit("C")


def missing_premise_is_accepted():
    service = AdmissionService((Rule("join", "1", (A, B), C),))
    driver = Driver(service)
    driver.context()
    a = driver.adopt("a", A).belief
    transition = driver.transition("join", (a.belief_revision_id,))
    try:
        return driver.finish(driver.prepare(transition)).status is Status.PASS
    except AdmissionDenied:
        return False


def stale_permit_is_accepted():
    service = AdmissionService()
    driver = Driver(service)
    driver.context()
    driver.record("a", A)
    transition = service.propose_evidence("ctx", "a", idempotency_key="t")
    proposal, pre, post, _ = driver.prepare(transition)
    driver.record("b", B)
    # Supplying the latest expected revision is allowed; the old permits still
    # need to be rejected independently at the actual commit boundary.
    current = service.snapshot("ctx").knowledge_revision
    return driver.finish((proposal, pre, post, current)).status is Status.PASS


def inconsistent_bundle_is_accepted():
    service = AdmissionService()
    driver = Driver(service)
    driver.context(constraints=(Clause((A.negate(), B.negate())),))
    driver.adopt("a", A)
    return driver.adopt("b", B).status is Status.PASS


class MutationTests(unittest.TestCase):
    def test_M01_unknown_as_pass_is_detected(self):
        self.assertFalse(missing_premise_is_accepted())
        original = model.conjunction

        def mutant(checks):
            return original(tuple(replace(c, status=Status.PASS)
                                  if c.status is Status.UNKNOWN else c for c in checks))

        with patch("reachability.model.conjunction", mutant):
            self.assertTrue(missing_premise_is_accepted())

    def test_M02_stale_certificate_is_detected(self):
        self.assertFalse(stale_permit_is_accepted())
        original = AdmissionService._permit_check

        def mutant(service, *args):
            check = original(service, *args)
            return replace(check, status=Status.PASS) if check.status is Status.STALE else check

        with patch.object(AdmissionService, "_permit_check", mutant):
            self.assertTrue(stale_permit_is_accepted())

    def test_M03_skipped_and_premise_is_detected(self):
        self.assertFalse(missing_premise_is_accepted())
        original = AdmissionService._input_checks

        def mutant(service, *args):
            return tuple(replace(c, status=Status.PASS) if c.name == "complete_premises"
                         else c for c in original(service, *args))

        with patch.object(AdmissionService, "_input_checks", mutant):
            self.assertTrue(missing_premise_is_accepted())

    def test_M04_pairwise_consistency_is_detected(self):
        self.assertFalse(inconsistent_bundle_is_accepted())

        def mutant(clauses, assertions=(), *, max_variables=16):
            formulas = tuple(clauses) + tuple(Clause((a,)) for a in assertions)
            subsets = list(combinations(formulas, 2)) or [formulas]
            for subset in subsets:
                result = check_consistency(subset, max_variables=max_variables)
                if result.status is not Status.PASS:
                    return result
            return LogicResult(Status.PASS, (), "mutant only checked pairs")

        with patch("reachability.service.check_consistency", mutant):
            self.assertTrue(inconsistent_bundle_is_accepted())
