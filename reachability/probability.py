"""Issued probability permits and a separate, replay-checked estimate ledger.

Accepted numerical estimates are alternatives, never Boolean assertions. All
mutations use the existing authority's lock/journal. Only infer_probability may
call a native runtime, outside the lock and outside replayable mutations.
"""
from dataclasses import asdict, dataclass, field

from .errors import AdmissionDenied, IdempotencyConflict
from .model import Check, Literal, Status, conjunction, identity, logical_integer, nonempty
from .pln_adapter import (IndependenceDeclaration, PLNAdapter, PLNProposal, PLNRejected,
                          ProbabilisticSupport, ProbabilitySnapshot)
from .probability_formula import PinnedFormulaRuntime, deduction_joint
from .probability_model import (ProbabilityBeliefRevision, ProbabilityCertificate,
                                ProbabilityCommitResult, ProbabilityIndependence,
                                ProbabilityPolicy, ProbabilityReport, ProbabilityRule,
                                ProbabilityTransition, ProbabilityView)


@dataclass
class ProbabilityStore:
    policies: dict[str, ProbabilityPolicy] = field(default_factory=dict)
    policy_versions: dict[tuple[str, str], ProbabilityPolicy] = field(default_factory=dict)
    reports: dict[str, ProbabilityReport] = field(default_factory=dict)
    rules: dict[tuple[str, str], ProbabilityRule] = field(default_factory=dict)
    rule_versions: dict[tuple[str, str, str], ProbabilityRule] = field(default_factory=dict)
    independence: dict[tuple[str, str], ProbabilityIndependence] = field(default_factory=dict)
    revoked_models: set[tuple[str, str]] = field(default_factory=set)
    transitions: dict[str, ProbabilityTransition] = field(default_factory=dict)
    certificates: dict[str, ProbabilityCertificate] = field(default_factory=dict)
    beliefs: dict[str, ProbabilityBeliefRevision] = field(default_factory=dict)


def fingerprint(value) -> str:
    return identity("probability-binding/v1", asdict(value))


class ProbabilityMixin:
    PROBABILITY_COMMANDS = frozenset(("configure_probability_policy", "record_probability_report",
        "configure_probability_rule", "register_probability_independence", "revoke_probability_independence",
        "propose_probability", "precertify_probability", "postcertify_probability", "commit_probability"))

    def configure_probability_policy(self, context_id: str, policy: ProbabilityPolicy,
                                     expected_revision: str | None = None, *, idempotency_key: str):
        if type(policy) is not ProbabilityPolicy:
            raise ValueError("a typed probability policy is required")
        def apply():
            context = self._contexts[context_id]
            previous = self._probability.policies.get(context_id)
            if (previous.revision if previous else None) != expected_revision:
                raise AdmissionDenied(Status.STALE, "probability policy changed")
            if previous == policy:
                return previous
            key = context_id, policy.revision
            if key in self._probability.policy_versions:
                raise ValueError("probability policy revisions cannot be reused")
            self._probability.policy_versions[key] = policy
            self._probability.policies[context_id] = policy
            context.revision += 1
            return policy
        return self._mutate("configure_probability_policy", idempotency_key,
                            dict(context_id=context_id, policy=policy, expected_revision=expected_revision), apply)

    def record_probability_report(self, report: ProbabilityReport, *, idempotency_key: str):
        if type(report) is not ProbabilityReport:
            raise ValueError("a typed probability report is required")
        def apply():
            evidence = self._evidence[report.evidence_id]
            previous = self._probability.reports.get(report.evidence_id)
            if previous is not None:
                if fingerprint(previous) != fingerprint(report):
                    raise IdempotencyConflict("an evidence identity cannot change its truth interpretation")
                return previous
            self._probability.reports[report.evidence_id] = report
            self._contexts[evidence.context_id].revision += 1
            return report
        return self._mutate("record_probability_report", idempotency_key, dict(report=report), apply)

    def configure_probability_rule(self, context_id: str, rule: ProbabilityRule,
                                   expected_revision: str | None = None, *, idempotency_key: str):
        if type(rule) is not ProbabilityRule:
            raise ValueError("a typed probability rule is required")
        def apply():
            context = self._contexts[context_id]
            key = context_id, rule.rule_id
            previous = self._probability.rules.get(key)
            if (previous.revision if previous else None) != expected_revision:
                raise AdmissionDenied(Status.STALE, "probability rule changed")
            if previous == rule:
                return previous
            version = (*key, rule.revision)
            if version in self._probability.rule_versions:
                raise ValueError("probability rule revisions cannot be reused")
            self._probability.rule_versions[version] = rule
            self._probability.rules[key] = rule
            context.revision += 1
            return rule
        return self._mutate("configure_probability_rule", idempotency_key,
                            dict(context_id=context_id, rule=rule, expected_revision=expected_revision), apply)

    def register_probability_independence(self, declaration: ProbabilityIndependence, *, idempotency_key: str):
        if type(declaration) is not ProbabilityIndependence:
            raise ValueError("a typed independence declaration is required")
        def apply():
            context = self._contexts[declaration.context_id]
            key = context.context_id, declaration.model_id
            previous = self._probability.independence.get(key)
            if previous is not None:
                if previous != declaration:
                    raise IdempotencyConflict("independence identity cannot be redefined")
                return previous
            supports = [self._probability.beliefs[p] for p in declaration.premise_revision_ids]
            if any(s.context_id != context.context_id for s in supports):
                raise AdmissionDenied(Status.FAIL, "independence declaration crosses contexts")
            self._probability.independence[key] = declaration
            context.revision += 1
            return declaration
        return self._mutate("register_probability_independence", idempotency_key, dict(declaration=declaration), apply)

    def revoke_probability_independence(self, context_id: str, model_id: str, *, idempotency_key: str):
        def apply():
            context = self._contexts[context_id]
            key = context_id, model_id
            self._probability.independence[key]
            if key not in self._probability.revoked_models:
                self._probability.revoked_models.add(key)
                context.revision += 1
            return context.revision
        return self._mutate("revoke_probability_independence", idempotency_key,
                            dict(context_id=context_id, model_id=model_id), apply)

    def propose_probability(self, context_id: str, kind: str, *, evidence_id: str | None = None,
                            rule_id: str | None = None, premise_revision_ids: tuple[str, ...] = (),
                            independence_id: str | None = None, idempotency_key: str):
        if kind not in ("observation", "deduction", "revision"):
            raise AdmissionDenied(Status.UNKNOWN, "unsupported probability operation")
        premises = tuple(premise_revision_ids)
        if len(premises) > 5:
            raise ValueError("probability transition arity exceeds supported scope")
        for premise in premises:
            nonempty(premise)
        if kind == "observation":
            nonempty(evidence_id)
            if rule_id is not None or premises or independence_id is not None:
                raise ValueError("an observation binds only an evidence report")
        elif kind == "deduction":
            nonempty(rule_id)
            if evidence_id is not None or independence_id is not None:
                raise ValueError("deduction binds a grounded rule and ordered premises")
        elif evidence_id is not None or rule_id is not None:
            raise ValueError("revision binds only two estimates and an independence model")
        if kind == "revision":
            premises = tuple(sorted(premises))
        payload = dict(context_id=context_id, kind=kind, evidence_id=evidence_id, rule_id=rule_id,
                       premise_revision_ids=premises, independence_id=independence_id)
        def apply():
            self._contexts[context_id]
            revision = self._probability.rules[context_id, rule_id].revision if rule_id else None
            if evidence_id:
                self._probability.reports[evidence_id]
            transition = ProbabilityTransition(identity("probability-transition/v1", (payload, revision)),
                                               context_id, kind, evidence_id, rule_id, revision,
                                               premises, independence_id)
            self._probability.transitions.setdefault(transition.transition_id, transition)
            return transition
        return self._mutate("propose_probability", idempotency_key, payload, apply)

    def _probability_registered(self, transition):
        if (type(transition) is not ProbabilityTransition or
                self._probability.transitions.get(transition.transition_id) != transition):
            raise AdmissionDenied(Status.FAIL, "unregistered or altered probability transition")
        return self._contexts[transition.context_id]

    def _probability_live(self, context):
        """Topological pass over immutable commits; descendants bind exact parents."""
        policy = self._probability.policies.get(context.context_id)
        live = {}
        for key, belief in self._probability.beliefs.items():
            if belief.context_id != context.context_id:
                continue
            status = Status.PASS
            if (policy is None or belief.probability_policy_revision != policy.revision or
                    belief.hard_policy_revision != context.policy_revision):
                status = Status.STALE
            transition = belief.transition
            if transition.rule_id:
                rule = self._probability.rules.get((context.context_id, transition.rule_id))
                if rule is None or rule.revision != transition.rule_revision:
                    status = Status.STALE
            if transition.independence_id and (context.context_id, transition.independence_id) in self._probability.revoked_models:
                status = Status.STALE
            if any(live.get(p) is not Status.PASS for p in transition.premise_revision_ids):
                status = Status.STALE
            for evidence_id in belief.proposal.support.evidence_ids:
                evidence = self._evidence[evidence_id]
                if (self._evidence_status(evidence, context) is not Status.PASS or
                        policy is None or evidence.source not in policy.allowed_sources):
                    status = Status.STALE
            live[key] = status
        return live

    def _probability_inputs(self, transition, context):
        policy = self._probability.policies.get(context.context_id)
        joint = self._joint(context)
        checks = [Check("probability_policy", Status.PASS if policy else Status.UNKNOWN, "declared scoped estimate policy"),
                  Check("hard_environment", joint.status, "the enclosing hard environment must remain valid")]
        if transition.kind == "observation":
            evidence = self._evidence[transition.evidence_id]
            checks.extend((Check("report_context", Status.PASS if evidence.context_id == context.context_id else Status.FAIL,
                                 "evidence belongs to the exact context"),
                           Check("report_current", self._evidence_status(evidence, context), "current unrevoked source evidence"),
                           Check("report_source", Status.PASS if policy and evidence.source in policy.allowed_sources else Status.UNKNOWN,
                                 "report source is authorized by the probability policy")))
        else:
            live = self._probability_live(context)
            expected = 5 if transition.kind == "deduction" else 2
            checks.append(Check("premise_arity", Status.PASS if len(transition.premise_revision_ids) == expected else Status.UNKNOWN,
                                "complete ordered numeric premises required"))
            for i, premise in enumerate(transition.premise_revision_ids):
                belief = self._probability.beliefs.get(premise)
                status = (Status.UNKNOWN if belief is None else Status.FAIL if belief.context_id != context.context_id
                          else live[premise])
                checks.append(Check(f"numeric_premise_{i}", status, "exact current numerical revision; no substitution"))
            if transition.kind == "deduction":
                rule = self._probability.rules[context.context_id, transition.rule_id]
                checks.append(Check("probability_rule", Status.PASS if rule.revision == transition.rule_revision else Status.STALE,
                                    "grounded probability rule revision"))
            else:
                declaration = self._probability.independence.get((context.context_id, transition.independence_id))
                status = (Status.UNKNOWN if declaration is None else
                          Status.STALE if (context.context_id, transition.independence_id) in self._probability.revoked_models else
                          Status.PASS if declaration.premise_revision_ids == transition.premise_revision_ids else Status.FAIL)
                checks.append(Check("independence_model", status, "registered assumption bound to exact revisions"))
        if conjunction(checks) is Status.PASS:
            try:
                # Pure formula replay also checks domains, cycles and dependence.
                self._derive_probability(transition, context, PLNAdapter(PinnedFormulaRuntime()))
                checks.append(Check("probability_formula", Status.PASS, "pinned finite formula and provenance checks"))
            except PLNRejected as error:
                checks.append(Check("probability_formula", error.status, str(error)))
        return tuple(checks)

    def _derive_probability(self, transition, context, adapter):
        if transition.kind == "observation":
            evidence = self._evidence[transition.evidence_id]
            report = self._probability.reports[transition.evidence_id]
            support = ProbabilisticSupport(identity("probability-observation/v1", (asdict(evidence), asdict(report))),
                                           context.context_id, evidence.content, report.truth,
                                           (evidence.evidence_id,), evidence.lineage_roots)
            formula = "probability-observation/v1"
            proposal_id = identity("probability-proposal/v1", (context.revision, asdict(support), formula))
            return PLNProposal(proposal_id, context.context_id, context.revision, support, formula,
                               ("trusted-source-finite-estimate",), ())
        supports = tuple(self._probability.beliefs[p].proposal.support for p in transition.premise_revision_ids)
        if transition.kind == "deduction":
            rule = self._probability.rule_versions[context.context_id, transition.rule_id, transition.rule_revision]
            proposal = adapter.apply_rule(rule.deduction, ProbabilitySnapshot(context.context_id, context.revision, supports))
            if deduction_joint(tuple(s.truth for s in supports), proposal.support.truth) is None:
                raise PLNRejected(Status.FAIL, "proposed estimate has no complete three-proposition joint model")
            return proposal
        result = adapter.revise(*supports, context.revision,
                                IndependenceDeclaration(transition.independence_id, supports))
        if result.status is not Status.PASS or result.proposal is None:
            raise PLNRejected(Status.UNKNOWN if result.status is Status.PASS else result.status, result.detail)
        return result.proposal

    def _probability_binding(self, transition, context):
        # Include actual immutable records, not just IDs or cached PASS flags.
        policy = self._probability.policies.get(context.context_id)
        premises = tuple(self._probability.beliefs.get(p) for p in transition.premise_revision_ids)
        evidence_ids = {transition.evidence_id} if transition.evidence_id else set()
        for premise in premises:
            if premise:
                evidence_ids.update(premise.proposal.support.evidence_ids)
        model = self._probability.independence.get((context.context_id, transition.independence_id))
        rule = self._probability.rule_versions.get((context.context_id, transition.rule_id, transition.rule_revision))
        return identity("probability-snapshot/v1", (
            self._authority_id, context.context_id, context.revision, context.logical_time, context.policy_revision,
            asdict(transition), asdict(policy) if policy else None, asdict(rule) if rule else None,
            asdict(model) if model else None, tuple(asdict(p) if p else None for p in premises),
            tuple((asdict(self._evidence[e]), asdict(self._probability.reports[e]), e in self._revoked)
                  for e in sorted(evidence_ids))))

    def _issue_probability(self, stage, transition, context, checks, proposal=None, pre=None):
        policy = self._probability.policies.get(context.context_id)
        witness = None
        if transition.kind == "deduction" and conjunction(checks) is Status.PASS:
            expected = self._derive_probability(transition, context, PLNAdapter(PinnedFormulaRuntime()))
            truths = tuple(self._probability.beliefs[p].proposal.support.truth for p in transition.premise_revision_ids)
            witness = tuple(str(cell) for cell in deduction_joint(truths, expected.support.truth))
        permit = ProbabilityCertificate(
            identity("probability-certificate/v1", (self._authority_id, len(self._probability.certificates))),
            stage, transition.transition_id, context.context_id, context.revision, context.policy_revision,
            policy.revision if policy else None, context.logical_time, self._probability_binding(transition, context),
            fingerprint(proposal) if proposal else None, pre.certificate_id if pre else None, checks, witness)
        self._probability.certificates[permit.certificate_id] = permit
        return permit

    def _probability_permit(self, permit, stage, transition, context, proposal=None, pre=None):
        if (type(permit) is not ProbabilityCertificate or
                self._probability.certificates.get(permit.certificate_id) != permit):
            return Check(stage + "_permit", Status.FAIL, "untrusted or altered numerical certificate")
        if (permit.stage, permit.transition_id, permit.context_id) != (stage, transition.transition_id, context.context_id):
            return Check(stage + "_permit", Status.FAIL, "certificate stage/transition/context mismatch")
        if proposal is not None and (permit.proposal_digest != fingerprint(proposal) or
                                     pre is None or permit.pre_certificate_id != pre.certificate_id):
            return Check(stage + "_permit", Status.FAIL, "post certificate binds a different proposal or pre certificate")
        if permit.snapshot_digest != self._probability_binding(transition, context):
            return Check(stage + "_permit", Status.STALE, "numerical snapshot changed")
        return Check(stage + "_permit", permit.status, "issued numerical permit must pass")

    def precertify_probability(self, transition: ProbabilityTransition, expected_revision: int, *, idempotency_key: str):
        logical_integer(expected_revision)
        def apply():
            context = self._probability_registered(transition)
            checks = (Check("snapshot", Status.PASS if context.revision == expected_revision else Status.STALE,
                            "full authority knowledge revision"), *self._probability_inputs(transition, context))
            return self._issue_probability("pre", transition, context, checks)
        return self._mutate("precertify_probability", idempotency_key,
                            dict(transition=transition, expected_revision=expected_revision), apply)

    def infer_probability(self, transition: ProbabilityTransition, pre_certificate: ProbabilityCertificate,
                          *, adapter: PLNAdapter | None = None) -> PLNProposal:
        with self._lock:
            self._ensure_open()
            context = self._probability_registered(transition)
            checks = (self._probability_permit(pre_certificate, "pre", transition, context),
                      *self._probability_inputs(transition, context))
            if conjunction(checks) is not Status.PASS:
                raise AdmissionDenied(conjunction(checks), "numerical inference requires a fresh issued pre certificate")
            # Capture immutable inputs for computation outside the authority lock.
            # No native call is part of a replayable mutation.
            if transition.kind == "observation":
                return self._derive_probability(transition, context, None)
            supports = tuple(self._probability.beliefs[p].proposal.support for p in transition.premise_revision_ids)
            snapshot = ProbabilitySnapshot(context.context_id, context.revision, supports)
            rule = (self._probability.rule_versions[context.context_id, transition.rule_id, transition.rule_revision]
                    if transition.kind == "deduction" else None)
        adapter = adapter if adapter is not None else PLNAdapter()
        if rule:
            return adapter.apply_rule(rule.deduction, snapshot)
        result = adapter.revise(*supports, snapshot.knowledge_revision,
                                IndependenceDeclaration(transition.independence_id, supports))
        if result.status is not Status.PASS or result.proposal is None:
            raise PLNRejected(Status.UNKNOWN if result.status is Status.PASS else result.status, result.detail)
        return result.proposal

    def postcertify_probability(self, proposal: PLNProposal, pre_certificate: ProbabilityCertificate, *, idempotency_key: str):
        if type(proposal) is not PLNProposal or type(pre_certificate) is not ProbabilityCertificate:
            raise ValueError("typed numerical proposal and pre certificate required")
        def apply():
            transition = self._probability.transitions[pre_certificate.transition_id]
            context = self._probability_registered(transition)
            checks = (self._probability_permit(pre_certificate, "pre", transition, context),
                      *self._probability_inputs(transition, context))
            if conjunction(checks) is Status.PASS:
                expected = self._derive_probability(transition, context, PLNAdapter(PinnedFormulaRuntime()))
                checks += (Check("proposal_replay", Status.PASS if fingerprint(proposal) == fingerprint(expected) else Status.FAIL,
                                 "exact formula result, interpretation, bindings and source lineage"),)
            return self._issue_probability("post", transition, context, checks, proposal, pre_certificate)
        return self._mutate("postcertify_probability", idempotency_key,
                            dict(proposal=proposal, pre_certificate=pre_certificate), apply)

    def commit_probability(self, proposal: PLNProposal, pre_certificate: ProbabilityCertificate,
                           post_certificate: ProbabilityCertificate, expected_revision: int, *, idempotency_key: str):
        if (type(proposal) is not PLNProposal or type(pre_certificate) is not ProbabilityCertificate
                or type(post_certificate) is not ProbabilityCertificate):
            raise ValueError("typed numerical proposal and certificates required")
        logical_integer(expected_revision)
        def apply():
            transition = self._probability.transitions[pre_certificate.transition_id]
            context = self._probability_registered(transition)
            checks = (Check("snapshot", Status.PASS if context.revision == expected_revision else Status.STALE,
                            "serialized numerical commit revision"),
                      self._probability_permit(pre_certificate, "pre", transition, context),
                      self._probability_permit(post_certificate, "post", transition, context, proposal, pre_certificate),
                      *self._probability_inputs(transition, context))
            status = conjunction(checks)
            if status is not Status.PASS:
                return ProbabilityCommitResult(status, context.revision, detail="; ".join(c.detail for c in checks if c.status is not Status.PASS))
            expected = self._derive_probability(transition, context, PLNAdapter(PinnedFormulaRuntime()))
            if fingerprint(proposal) != fingerprint(expected):
                return ProbabilityCommitResult(Status.FAIL, context.revision, detail="numerical proposal was altered")
            live = self._probability_live(context)
            for key, belief in self._probability.beliefs.items():
                if live.get(key) is Status.PASS and belief.transition == transition and belief.proposal.support == proposal.support:
                    return ProbabilityCommitResult(Status.PASS, context.revision, belief, "idempotent numerical support")
            policy = self._probability.policies[context.context_id]
            if sum(b.context_id == context.context_id for b in self._probability.beliefs.values()) >= policy.max_beliefs:
                return ProbabilityCommitResult(Status.UNKNOWN, context.revision, detail="numerical history limit exceeded")
            belief_id = identity("probability-belief/v1", (fingerprint(proposal), transition.transition_id,
                                                        context.revision + 1, policy.revision))
            belief = ProbabilityBeliefRevision(belief_id, context.context_id, context.revision + 1, transition, proposal,
                                              pre_certificate.certificate_id, post_certificate.certificate_id,
                                              context.policy_revision, policy.revision)
            self._probability.beliefs[belief_id] = belief
            context.revision += 1
            return ProbabilityCommitResult(Status.PASS, context.revision, belief, "accepted scoped estimate; no hard assertion")
        return self._mutate("commit_probability", idempotency_key, dict(proposal=proposal, pre_certificate=pre_certificate,
                            post_certificate=post_certificate, expected_revision=expected_revision), apply)

    def query_probability(self, context_id: str, conclusion: Literal) -> ProbabilityView:
        if type(conclusion) is not Literal:
            raise ValueError("a grounded literal is required")
        with self._lock:
            self._ensure_open()
            context = self._contexts[context_id]
            history = tuple(b for b in self._probability.beliefs.values() if b.context_id == context_id and
                            b.proposal.support.conclusion == conclusion)
            live = self._probability_live(context)
            current = tuple(b for b in history if live[b.belief_revision_id] is Status.PASS)
            joint = self._joint(context)
            status = joint.status if current else (Status.STALE if history else Status.UNKNOWN)
            return ProbabilityView(context_id, conclusion, context.revision, status,
                                   current if status is Status.PASS else (), history,
                                   (Check("hard_environment", joint.status, "current enclosing hard environment"),))

    def export_probability(self, context_id: str) -> tuple:
        with self._lock:
            self._ensure_open()
            context = self._contexts[context_id]
            literals = sorted({b.proposal.support.conclusion for b in self._probability.beliefs.values()
                               if b.context_id == context_id})
            return (self._authority_id, self.snapshot(context_id), self._probability.policies.get(context_id),
                    tuple(self.query_probability(context_id, literal) for literal in literals))
