"""Full deployment slice with declared numerical gates and optional real adapters."""
import json

from .decision_model import DecisionContract, DecisionCriterion
from .model import Evidence, Status
from .pln_adapter import DeductionRule, PLNAdapter, TruthValue
from .probability_formula import PinnedFormulaRuntime
from .probability_model import ProbabilityPolicy, ProbabilityReport, ProbabilityRule

RULE = ProbabilityRule("deployment-forecast", "1", DeductionRule(
    "tested:artifact-v2", "staged:artifact-v2", "healthy:artifact-v2"))


def register_contract(service, key):
    service.configure_probability_policy("ctx", ProbabilityPolicy("1", ("forecast-model",)), idempotency_key=key())
    service.configure_probability_rule("ctx", RULE, idempotency_key=key())
    service.register_decision_contract(DecisionContract("deployment-acceptance", "1", "deploy", "1", "artifact-v2", (
        DecisionCriterion("healthy-given-tested", RULE.deduction.conclusion, .65, 1, .35),)), idempotency_key=key())


def admit_forecast(service, key, adapter):
    def commit(transition):
        revision = service.snapshot("ctx").knowledge_revision
        pre = service.precertify_probability(transition, revision, idempotency_key=key())
        proposal = service.infer_probability(transition, pre, adapter=adapter)
        post = service.postcertify_probability(proposal, pre, idempotency_key=key())
        result = service.commit_probability(proposal, pre, post, revision, idempotency_key=key())
        if result.status is not Status.PASS:
            raise AssertionError(result)
        return result.belief

    premises = []
    for literal, strength in zip(RULE.deduction.premises, (.4, .5, .6, .7, .8)):
        evidence_id = key()
        service.record_evidence(Evidence(evidence_id, "ctx", literal, "forecast-model", 0,
                                         (evidence_id,), valid_until=1), idempotency_key=key())
        service.record_probability_report(ProbabilityReport(evidence_id, TruthValue(strength, .8)), idempotency_key=key())
        transition = service.propose_probability("ctx", "observation", evidence_id=evidence_id, idempotency_key=key())
        premises.append(commit(transition).belief_revision_id)
    return commit(service.propose_probability("ctx", "deduction", rule_id=RULE.rule_id,
                  premise_revision_ids=tuple(premises), idempotency_key=key()))


def deployment_snapshot(service, completion_permit):
    with service._lock:
        return (service.export_execution_decision("attempt"), service.inspect_goal("goal"),
                service.inspect_lifecycle("episode"), completion_permit)


def project_snapshot(snapshot):
    from .atomspace_adapter import RecordProjection
    projection = RecordProjection()
    projection.add(snapshot)
    return projection.batch.run()


def run(*, native=True):
    from .goal_demo import run as deployment
    adapter = PLNAdapter() if native else PLNAdapter(PinnedFormulaRuntime())
    return deployment(probability_adapter=adapter, project_native=native)


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
