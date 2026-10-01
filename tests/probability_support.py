"""Public API scenario driver, shared by finite and native contract tests."""
from itertools import count

from reachability.model import Evidence
from reachability.pln_adapter import DeductionRule, PLNAdapter, TruthValue
from reachability.probability_formula import PinnedFormulaRuntime
from reachability.probability_model import ProbabilityPolicy, ProbabilityReport, ProbabilityRule


class ProbabilityDriver:
    def __init__(self, service, adapter=None):
        self.service = service
        self.adapter = adapter if adapter is not None else PLNAdapter(PinnedFormulaRuntime())
        self.keys = count()

    def key(self):
        return f"probability-driver-{next(self.keys)}"

    def context(self, name="world", sources=("sensor",), **kwargs):
        self.service.open_context(name, idempotency_key=self.key())
        self.service.configure_probability_policy(name, ProbabilityPolicy("p1", sources, **kwargs),
                                                  idempotency_key=self.key())

    def report(self, name, literal, truth=TruthValue(.5, .8), context="world", *, source="sensor",
               roots=None, observed_at=0, valid_until=None):
        evidence = Evidence(name, context, literal, source, observed_at, tuple(roots or ("root:"+name,)), valid_until)
        self.service.record_evidence(evidence, idempotency_key=self.key())
        self.service.record_probability_report(ProbabilityReport(name, truth), idempotency_key=self.key())
        return self.service.propose_probability(context, "observation", evidence_id=name, idempotency_key=self.key())

    def prepare(self, transition):
        rev = self.service.snapshot(transition.context_id).knowledge_revision
        pre = self.service.precertify_probability(transition, rev, idempotency_key=self.key())
        proposal = self.service.infer_probability(transition, pre, adapter=self.adapter)
        post = self.service.postcertify_probability(proposal, pre, idempotency_key=self.key())
        return proposal, pre, post, rev

    def finish(self, prepared, key=None):
        return self.service.commit_probability(*prepared, idempotency_key=key or self.key())

    def adopt(self, *args, **kwargs):
        return self.finish(self.prepare(self.report(*args, **kwargs)))

    def deduction(self, strengths=(.4, .5, .6, .7, .8), *, prefix="s", expiry=None):
        rule = ProbabilityRule("deduce", "1", DeductionRule("P", "Q", "R"))
        self.service.configure_probability_rule("world", rule, idempotency_key=self.key())
        beliefs = tuple(self.adopt(prefix+str(i), literal, TruthValue(s, .8), valid_until=expiry).belief
                        for i, (literal, s) in enumerate(zip(rule.deduction.premises, strengths)))
        transition = self.service.propose_probability("world", "deduction", rule_id="deduce",
                                                      premise_revision_ids=tuple(b.belief_revision_id for b in beliefs),
                                                      idempotency_key=self.key())
        return rule, beliefs, transition
