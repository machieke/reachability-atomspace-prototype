"""Submission-only probabilistic gates, bound to immutable execution versions."""
from dataclasses import dataclass, field

from .decision_model import (CriterionDecision, DecisionContract, DecisionEvaluation, DecisionSupport)
from .errors import AdmissionDenied, IdempotencyConflict
from .model import Check, Status


@dataclass
class DecisionStore:
    contracts: dict[tuple[str, str], DecisionContract] = field(default_factory=dict)
    bindings: dict[tuple[str, str], DecisionContract] = field(default_factory=dict)
    certificates: dict[str, DecisionEvaluation] = field(default_factory=dict)


class DecisionMixin:
    DECISION_COMMANDS = frozenset(("register_decision_contract",))

    def register_decision_contract(self, contract: DecisionContract, *, idempotency_key: str) -> DecisionContract:
        """Trusted policy registration, before issuing any certificate for this execution version."""
        if type(contract) is not DecisionContract:
            raise ValueError("a typed decision contract is required")

        def apply():
            key = contract.contract_id, contract.revision
            previous = self._decisions.contracts.get(key)
            if previous is not None:
                if previous.fingerprint != contract.fingerprint:
                    raise IdempotencyConflict("decision contract revisions are immutable")
                return previous
            binding = contract.execution_contract_id, contract.execution_contract_revision
            execution = self._execution.contracts[binding]
            schema = self._lifecycle.schemas[execution.schema_id, execution.schema_revision]
            edge = next(edge for edge in schema.edges if edge.edge_id == execution.edge_id)
            if edge.product_id != contract.product_id:
                raise AdmissionDenied(Status.FAIL, "decision requires the exact execution product")
            if binding in self._decisions.bindings:
                raise IdempotencyConflict("an execution version has one immutable decision contract")
            if any((permit.contract_id, permit.contract_revision) == binding
                   for permit in self._execution.permits.values()):
                raise AdmissionDenied(Status.FAIL, "register decisions before certification; use a new execution version")
            self._decisions.contracts[key] = contract
            self._decisions.bindings[binding] = contract
            self._execution.revision += 1
            return contract

        return self._mutate("register_decision_contract", idempotency_key, dict(contract=contract), apply)

    def _evaluate_decision(self, attempt_id, contract):
        operation = self._lifecycle.attempts[attempt_id]
        context = self._contexts[operation.context_id]
        execution = self._execution.contracts[contract.execution_contract_id, contract.execution_contract_revision]
        criteria = []
        for criterion in contract.criteria:
            view = self.query_probability(operation.context_id, criterion.conclusion)
            opposite = self.query_probability(operation.context_id, criterion.conclusion.negate())

            def support(view):
                return tuple(DecisionSupport(b.belief_revision_id, b.proposal.support.truth)
                             for b in sorted(view.current, key=lambda b: b.belief_revision_id))

            current, contrary = support(view), support(opposite)
            checks = (
                *view.checks,
                Check("current_estimates", view.status, "at least one current certified exact-literal estimate"),
                Check("orientation", Status.UNKNOWN if contrary else Status.PASS,
                      "mixed literal orientations require a separate explicit model"),
                Check("strength_interval", Status.UNKNOWN if not current else Status.PASS if all(
                    criterion.min_strength <= item.truth.strength <= criterion.max_strength
                    for item in current) else Status.FAIL, "every current strength lies in the inclusive declared interval"),
                Check("confidence_floor", Status.UNKNOWN if not current or any(
                    item.truth.confidence < criterion.min_confidence for item in current) else Status.PASS,
                    "evidence adequacy only; confidence is not an event probability or calibrated bound"),
            )
            criteria.append(CriterionDecision(criterion, current, contrary, checks))
        checks = (Check("decision_execution", Status.PASS if (operation.schema_id, operation.schema_revision,
                        operation.edge_id) == (execution.schema_id, execution.schema_revision, execution.edge_id)
                        else Status.FAIL, "exact operation schema revision and edge"),
                  Check("decision_product", Status.PASS if operation.product_id == contract.product_id else Status.FAIL,
                        "exact product scoped by the execution contract"),
                  *(Check(item.criterion.criterion_id, item.status, "all declared criteria must pass") for item in criteria))
        return DecisionEvaluation(contract, operation.context_id, operation.product_id,
                                  context.revision, context.logical_time, tuple(criteria), checks)

    def inspect_probability_decision(self, attempt_id: str, contract_id: str, contract_revision: str) -> DecisionEvaluation:
        with self._lock:
            self._ensure_open()
            return self._evaluate_decision(attempt_id, self._decisions.bindings[contract_id, contract_revision])

    def execution_decision(self, certificate_id: str) -> DecisionEvaluation | None:
        """Historical numerical witness; inspect the intent for present authorization."""
        with self._lock:
            self._ensure_open()
            self._execution.permits[certificate_id]
            return self._decisions.certificates.get(certificate_id)

    def _execution_decision_checks(self, attempt_id, execution):
        contract = self._decisions.bindings.get((execution.contract_id, execution.revision))
        if contract is None:
            return ()  # Preserve all existing command results and journal encodings.
        evaluation = self._evaluate_decision(attempt_id, contract)
        checks = (Check("probability_decision", evaluation.status, evaluation.evaluation_id),)
        intent = self._execution.intents.get(attempt_id)
        if intent is not None:
            bound = self._decisions.certificates.get(intent.certificate_id)
            checks += (Check("decision_support_binding", Status.PASS if bound is not None
                and bound.basis_id == evaluation.basis_id else Status.STALE,
                "submission must retain the exact certified set of numerical alternatives"),)
        return checks

    def _capture_execution_decision(self, permit):
        contract = self._decisions.bindings.get((permit.contract_id, permit.contract_revision))
        if contract is not None:
            self._decisions.certificates[permit.certificate_id] = self._evaluate_decision(permit.attempt_id, contract)

    def export_execution_decision(self, attempt_id: str) -> tuple:
        """One immutable diagnostic snapshot, including the exact historical numerical witness."""
        with self._lock:
            self._ensure_open()
            intent = self._execution.intents[attempt_id]
            return (self.export_admission(intent.context_id), self.export_probability(intent.context_id),
                    self.inspect_execution_intent(attempt_id), self._execution.permits[intent.certificate_id],
                    self.execution_decision(intent.certificate_id), self._dispatch.attempts.get(attempt_id))
