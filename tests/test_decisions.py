from dataclasses import replace
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from reachability.codec import dumps, loads
from reachability.decision_model import DecisionContract, DecisionCriterion
from reachability.model import Status
from reachability.pln_adapter import DeductionRule, TruthValue, implication, proposition
from reachability.probability_model import ProbabilityPolicy, ProbabilityRule
from reachability.service import AdmissionDenied, AdmissionService, IdempotencyConflict
from tests.execution_support import ExecutionFixture
from tests.probability_support import ProbabilityDriver

FORECAST = implication("tested:artifact-v2", "healthy:artifact-v2")


class DecisionContractTests(ExecutionFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.numeric = ProbabilityDriver(self.service)
        self.service.configure_probability_policy("ctx", ProbabilityPolicy("1", ("sensor",)),
                                                  idempotency_key=self.driver.key())
        self.criterion = DecisionCriterion("healthy-forecast", FORECAST, .6, .9, .3)
        self.decision = DecisionContract("deploy-risk", "1", "build", "1", "artifact-v2", (self.criterion,))
        self.service.register_decision_contract(self.decision, idempotency_key=self.driver.key())

    def adopt(self, name="forecast", truth=TruthValue(.75, .8), literal=FORECAST, **kwargs):
        return self.numeric.adopt(name, literal, truth, context="ctx", **kwargs).belief

    def decision_view(self):
        return self.service.inspect_probability_decision("attempt", "build", "1")

    def derived(self, expiry=None):
        rule = ProbabilityRule("deployment", "1", DeductionRule(
            "tested:artifact-v2", "staged:artifact-v2", "healthy:artifact-v2"))
        self.service.configure_probability_rule("ctx", rule, idempotency_key=self.driver.key())
        inputs = tuple(self.adopt(f"input-{i}", TruthValue(value, .8), literal, valid_until=expiry)
                       for i, (value, literal) in enumerate(zip((.4, .5, .6, .7, .8), rule.deduction.premises)))
        transition = self.service.propose_probability("ctx", "deduction", rule_id=rule.rule_id,
            premise_revision_ids=tuple(b.belief_revision_id for b in inputs), idempotency_key=self.driver.key())
        result = self.numeric.finish(self.numeric.prepare(transition))
        self.assertEqual(result.status, Status.PASS)
        return result.belief

    def test_missing_estimates_do_not_authorize_resource_reservation(self):
        permit = self.permit()
        self.assertEqual(permit.status, Status.UNKNOWN)
        with self.assertRaises(AdmissionDenied):
            self.reserve(permit)
        self.assertEqual(self.service.inspect_resource("slot").reservations, ())

    def test_estimates_authorize_only_the_declared_contract_not_a_hard_fact(self):
        belief = self.adopt()
        permit = self.permit()
        decision = self.service.execution_decision(permit.certificate_id)
        self.assertEqual(permit.status, Status.PASS)
        self.assertEqual(decision.criteria[0].current[0].belief_revision_id, belief.belief_revision_id)
        self.assertEqual(loads(dumps(decision)), decision)
        self.assertEqual(self.service.query_belief("ctx", FORECAST).status, Status.UNKNOWN)
        self.reserve(permit)
        self.assertEqual(self.service.inspect_execution_intent("attempt").readiness, Status.PASS)
        self.assertEqual(self.service.inspect_lifecycle("episode").episode.stage, "DRAFT")

    def test_all_current_alternatives_must_pass_without_cherry_picking(self):
        self.adopt("good")
        self.adopt("bad", TruthValue(.59, .8))
        view = self.decision_view()
        self.assertEqual(len(view.criteria[0].current), 2)
        self.assertEqual(view.status, Status.FAIL)
        self.assertEqual(self.permit().status, Status.FAIL)
        self.service.revoke_evidence("bad", idempotency_key=self.driver.key())
        self.assertEqual(self.permit().status, Status.PASS)

    def test_inadequate_confidence_is_unknown_and_is_not_multiplied_into_strength(self):
        self.adopt("weak", TruthValue(.75, math.nextafter(.3, 0)))
        self.assertEqual(self.permit().status, Status.UNKNOWN)
        self.service.revoke_evidence("weak", idempotency_key=self.driver.key())
        self.adopt("adequate", TruthValue(.75, .3))
        self.assertEqual(self.permit().status, Status.PASS)  # .75 * .3 < .6, intentionally irrelevant.

    def test_strength_boundaries_are_inclusive_binary64_without_tolerance(self):
        for index, (strength, expected) in enumerate(((.6, Status.PASS), (.9, Status.PASS),
                (math.nextafter(.6, 0), Status.FAIL), (math.nextafter(.9, 1), Status.FAIL))):
            name = f"boundary-{index}"
            self.adopt(name, TruthValue(strength, .3))
            self.assertEqual(self.permit().status, expected)
            self.service.revoke_evidence(name, idempotency_key=self.driver.key())

    def test_opposite_polarity_is_not_silently_dropped_or_converted(self):
        self.adopt()
        opposite = self.adopt("opposite", TruthValue(.25, .8), FORECAST.negate())
        view = self.decision_view()
        self.assertEqual(view.status, Status.UNKNOWN)
        self.assertEqual(view.criteria[0].opposite[0].belief_revision_id, opposite.belief_revision_id)
        self.assertEqual(self.permit().status, Status.UNKNOWN)

    def test_context_and_exact_product_are_not_interchangeable(self):
        self.numeric.context("other")
        self.numeric.adopt("elsewhere", FORECAST, TruthValue(.75, .8), context="other")
        self.adopt("other-product", TruthValue(.75, .8), implication("tested:artifact-v1", "healthy:artifact-v1"))
        self.assertEqual(self.permit().status, Status.UNKNOWN)
        with self.assertRaises(AdmissionDenied):
            self.service.register_decision_contract(replace(self.decision, contract_id="wrong", product_id="artifact-v1"),
                                                    idempotency_key=self.driver.key())

    def test_uncommitted_reports_cannot_supply_a_decision(self):
        self.numeric.report("report-only", FORECAST, TruthValue(.75, .8), context="ctx")
        self.assertEqual(self.permit().status, Status.UNKNOWN)

    def test_numeric_pass_cannot_replace_hard_submission_requirements(self):
        self.adopt()
        self.service.revoke_evidence("credential", idempotency_key=self.driver.key())
        self.assertEqual(self.decision_view().status, Status.PASS)
        self.assertEqual(self.permit().status, Status.UNKNOWN)

    def test_rule_retirement_invalidates_a_derived_decision(self):
        belief = self.derived()
        permit = self.permit()
        self.assertEqual(permit.status, Status.PASS)
        self.assertEqual(belief.proposal.support.conclusion, FORECAST)
        self.service.configure_probability_rule("ctx", ProbabilityRule("deployment", "2", DeductionRule(
            "tested:artifact-v2", "staged:artifact-v2", "healthy:artifact-v2")),
            expected_revision="1", idempotency_key=self.driver.key())
        self.assertEqual(self.decision_view().status, Status.STALE)
        with self.assertRaises(AdmissionDenied):
            self.reserve(permit)

    def test_derived_source_expiry_is_exclusive_and_invalidates_pending_intent(self):
        self.derived(expiry=2)
        self.reserve()
        for time, expected in ((1, Status.PASS), (2, Status.STALE)):
            self.service.advance_clock("ctx", time, idempotency_key=self.driver.key())
            self.service.advance_resource_clock(time, idempotency_key=self.driver.key())
            self.assertEqual(self.service.inspect_execution_intent("attempt").readiness, expected)

    def test_revocation_after_certification_cannot_reserve(self):
        self.adopt()
        permit = self.permit()
        self.service.revoke_evidence("forecast", idempotency_key=self.driver.key())
        with self.assertRaises(AdmissionDenied) as error:
            self.reserve(permit)
        self.assertEqual(error.exception.status, Status.STALE)
        self.assertEqual(self.service.inspect_resource("slot").reservations, ())

    def test_new_good_alternative_requires_a_new_intent_basis(self):
        self.adopt()
        self.reserve()
        self.adopt("another")
        self.assertEqual(self.decision_view().status, Status.PASS)
        self.assertEqual(self.service.inspect_execution_intent("attempt").readiness, Status.STALE)

    def test_unrelated_updates_do_not_replace_exact_numerical_support(self):
        self.adopt()
        self.reserve()
        self.adopt("unrelated", literal=proposition("unrelated"))
        self.assertEqual(self.service.inspect_execution_intent("attempt").readiness, Status.PASS)

    def test_policy_replacement_retires_all_old_decision_support(self):
        self.adopt()
        self.reserve()
        self.service.configure_probability_policy("ctx", ProbabilityPolicy("2", ("sensor",)),
            expected_revision="1", idempotency_key=self.driver.key())
        self.assertEqual(self.service.inspect_execution_intent("attempt").readiness, Status.STALE)

    def test_contract_versions_and_binding_cannot_be_changed_or_removed(self):
        self.assertEqual(self.service.register_decision_contract(self.decision, idempotency_key=self.driver.key()), self.decision)
        for contract in (replace(self.decision, criteria=(replace(self.criterion, min_strength=.5),)),
                         replace(self.decision, revision="2"), replace(self.decision, contract_id="replacement")):
            with self.assertRaises(IdempotencyConflict):
                self.service.register_decision_contract(contract, idempotency_key=self.driver.key())

    def test_decisions_cannot_be_added_after_certification_even_if_no_intent_exists(self):
        execution = replace(self.contract, revision="2")
        self.service.register_execution_contract(execution, idempotency_key=self.driver.key())
        self.permit(contract=execution)
        with self.assertRaises(AdmissionDenied):
            self.service.register_decision_contract(replace(self.decision, revision="2", execution_contract_revision="2"),
                                                    idempotency_key=self.driver.key())

    def test_multiple_criteria_cannot_ignore_a_missing_or_failed_risk_estimate(self):
        execution = replace(self.contract, revision="2")
        self.service.register_execution_contract(execution, idempotency_key=self.driver.key())
        risk = proposition("deployment-outage-risk")
        contract = replace(self.decision, revision="2", execution_contract_revision="2", criteria=(
            self.criterion, DecisionCriterion("outage", risk, 0, .1, .5)))
        self.service.register_decision_contract(contract, idempotency_key=self.driver.key())
        self.adopt()
        self.assertEqual(self.permit(contract=execution).status, Status.UNKNOWN)
        self.adopt("outage", TruthValue(.11, .9), risk)
        self.assertEqual(self.permit(contract=execution).status, Status.FAIL)

    def test_altered_or_forged_permit_cannot_omit_the_decision_gate(self):
        permit = self.permit()
        forged = replace(permit, checks=tuple(c for c in permit.checks if c.name != "probability_decision"))
        with self.assertRaises(AdmissionDenied):
            self.reserve(forged)


class DurableDecisionContractTests(DecisionContractTests):
    def make_service(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "decisions.sqlite"
        return AdmissionService(database=self.path)

    def restart(self):
        self.service.close()
        self.service = AdmissionService(database=self.path)
        self.driver.service = self.numeric.service = self.service

    def tearDown(self):
        before = tuple(self.service._decisions.certificates.items())
        self.restart()
        self.assertEqual(tuple(self.service._decisions.certificates.items()), before)


class DecisionModelTests(unittest.TestCase):
    def test_invalid_thresholds_units_and_uncertainty_semantics_are_rejected(self):
        criterion = DecisionCriterion("criterion", FORECAST, .6, .9, .3)
        for kwargs in (dict(min_strength=True), dict(min_strength=float("nan")), dict(max_strength=float("inf")),
                       dict(min_confidence=1), dict(min_confidence=-.1), dict(min_strength=.95),
                       dict(max_strength=1.1), dict(unit="percent"), dict(confidence_semantics="success-probability")):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                replace(criterion, **kwargs)
        contract = DecisionContract("d", "1", "e", "1", "product", (criterion,))
        for kwargs in (dict(criteria=()), dict(criteria=(criterion, criterion)), dict(criteria=(criterion,) * 17),
                       dict(alternative_policy="pick-highest"), dict(truth_model="calibrated-95%-bound")):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                replace(contract, **kwargs)
