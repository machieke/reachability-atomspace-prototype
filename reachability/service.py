"""Single-authority admission service with optional checked journal recovery.

All public mutations are serialized and idempotent. The boundary is a trusted
Python process, not a security sandbox against arbitrary in-process code.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from pathlib import Path
from threading import RLock
from typing import Callable, TypeVar
from uuid import uuid4

from .codec import dumps, loads
from .completion import CompletionMixin, CompletionStore
from .dispatch import DispatchMixin, DispatchStore
from .errors import AdmissionDenied, IdempotencyConflict
from .execution import ExecutionMixin, ExecutionStore
from .goals import GoalMixin, GoalStore
from .journal import RecoveryError, SQLiteJournal, digest
from .lifecycle import LifecycleMixin, LifecycleStore
from .logic import LogicResult, check_consistency
from .model import (
    BeliefRevision, BeliefView, Certificate, Check, Clause, CommitResult,
    ContextSnapshot, Evidence, Literal, Proposal, Rule, Status, Transition,
    conjunction, identity, logical_integer, nonempty,
)
from .probability import ProbabilityMixin, ProbabilityStore

T = TypeVar("T")


@dataclass
class _Context:
    context_id: str
    assumptions: tuple[Literal, ...]
    constraints: tuple[Clause, ...]
    policy_revision: str
    revision: int = 0
    beliefs: dict[str, BeliefRevision] = field(default_factory=dict)
    usable: set[str] = field(default_factory=set)
    logical_time: int = 0


class AdmissionService(ProbabilityMixin, CompletionMixin, GoalMixin, DispatchMixin, ExecutionMixin, LifecycleMixin):
    _COMMANDS = (frozenset((
        "open_context", "record_evidence", "revoke_evidence", "propose_evidence",
        "propose_transition", "precertify", "postcertify", "commit", "replace_rule",
        "replace_policy", "advance_clock",
    )) | LifecycleMixin.LIFECYCLE_COMMANDS | ExecutionMixin.EXECUTION_COMMANDS
       | DispatchMixin.DISPATCH_COMMANDS | GoalMixin.GOAL_COMMANDS | CompletionMixin.COMPLETION_COMMANDS
       | ProbabilityMixin.PROBABILITY_COMMANDS)
    _STATE_FIELDS = ("_rules", "_rule_versions", "_policy_versions", "_contexts",
                     "_evidence", "_revoked", "_transitions", "_certificates", "_commands", "_lifecycle", "_execution",
                     "_dispatch", "_goals", "_completion", "_probability")

    def __init__(self, rules: tuple[Rule, ...] | None = None, *,
                 max_variables: int | None = None, database: str | Path | None = None):
        # Validate checker configuration before accepting any state.
        configured_limit = 16 if max_variables is None else max_variables
        configured_rules = () if rules is None else tuple(rules)
        check_consistency((), max_variables=configured_limit)
        if any(not isinstance(rule, Rule) for rule in configured_rules):
            raise ValueError("the rule registry requires typed Rule records")
        if len({rule.rule_id for rule in configured_rules}) != len(configured_rules):
            raise ValueError("rule IDs must be unique in the pinned registry")
        self._lock = RLock()
        self._journal = None
        self._journal_sequence = 0
        self._closed = False
        self._broken = False
        self._replaying = False
        self._authority_id = str(uuid4())
        if database is not None:
            self._journal = SQLiteJournal(database, {
                "implementation": "finite-admission/v2", "authority_id": self._authority_id,
                "rules": configured_rules, "max_variables": configured_limit,
            })
            try:
                initial = self._journal.initial
                if initial["implementation"] != "finite-admission/v2":
                    raise RecoveryError("journal requires a different admission implementation")
                if (rules is not None and configured_rules != initial["rules"]
                        or max_variables is not None and configured_limit != initial["max_variables"]):
                    raise RecoveryError("requested initial configuration differs from the journal")
                configured_rules, configured_limit = initial["rules"], initial["max_variables"]
                check_consistency((), max_variables=configured_limit)
                if (not isinstance(configured_rules, tuple)
                        or any(not isinstance(rule, Rule) for rule in configured_rules)
                        or len({rule.rule_id for rule in configured_rules}) != len(configured_rules)):
                    raise RecoveryError("invalid persisted rule registry")
                nonempty(initial["authority_id"])
                self._authority_id = initial["authority_id"]
            except BaseException:
                self._journal.close()
                raise
        self._max_variables = configured_limit
        self._rules = {rule.rule_id: rule for rule in configured_rules}
        self._rule_versions = {(r.rule_id, r.revision): r for r in configured_rules}
        self._policy_versions: dict[tuple[str, str], tuple[Clause, ...]] = {}
        self._contexts: dict[str, _Context] = {}
        self._evidence: dict[str, Evidence] = {}
        self._revoked: set[str] = set()
        self._transitions: dict[str, Transition] = {}
        self._certificates: dict[str, Certificate] = {}
        self._commands: dict[str, tuple[str, object]] = {}
        self._lifecycle = LifecycleStore()
        self._execution = ExecutionStore()
        self._dispatch = DispatchStore()
        self._goals = GoalStore()
        self._completion = CompletionStore()
        self._probability = ProbabilityStore()
        if self._journal is not None:
            try:
                self._replaying = True
                for entry in self._journal.entries():
                    if entry.command not in self._COMMANDS:
                        raise RecoveryError("unrecognized journal operation")
                    payload = loads(entry.payload)
                    if not isinstance(payload, dict) or "idempotency_key" in payload:
                        raise RecoveryError("invalid journal command arguments")
                    result = getattr(self, entry.command)(**payload, idempotency_key=entry.key)
                    if digest(dumps(result)) != entry.result_digest:
                        raise RecoveryError("replayed operation does not match its recorded result")
                    self._journal_sequence = entry.sequence
            except BaseException as error:
                self.close()
                if isinstance(error, Exception):
                    raise RecoveryError("admission journal recovery failed") from error
                raise
            finally:
                self._replaying = False

    def _ensure_open(self) -> None:
        if self._closed or self._broken:
            raise RecoveryError("service is closed or requires recovery after a storage failure")

    def close(self) -> None:
        with self._lock:
            self._closed = True
            if self._journal is not None:
                self._journal.close()

    def __enter__(self):
        self._ensure_open()
        return self

    def __exit__(self, *_):
        self.close()

    def _mutate(self, command: str, key: str, payload: object, apply: Callable[[], T]) -> T:
        nonempty(key)
        serialized = dumps(payload)
        fingerprint = identity("command/v2", (command, serialized))
        with self._lock:
            self._ensure_open()
            previous = self._commands.get(key)
            if previous is not None:
                if previous[0] != fingerprint:
                    raise IdempotencyConflict("idempotency key reused with different input")
                return previous[1]  # type: ignore[return-value]
            durable = self._journal is not None and not self._replaying
            before = {name: deepcopy(getattr(self, name)) for name in self._STATE_FIELDS} if durable else {}
            try:
                result = apply()
            except BaseException:
                for name, value in before.items():
                    setattr(self, name, value)
                raise
            if durable:
                try:
                    # Readers share the service lock, so no changed state is
                    # published until this atomic durable append succeeds.
                    self._journal_sequence = self._journal.append(
                        command, key, serialized, digest(dumps(result)), self._journal_sequence)
                except BaseException:
                    for name, value in before.items():
                        setattr(self, name, value)
                    # A COMMIT error can have an ambiguous outcome. Reopen and
                    # reconcile the same key rather than serving an old view.
                    self._broken = True
                    raise
            self._commands[key] = (fingerprint, result)
            return result

    def open_context(
        self, context_id: str, *, assumptions: tuple[Literal, ...] = (),
        constraints: tuple[Clause, ...] = (), policy_revision: str = "finite-hard-policy/v1",
        idempotency_key: str,
    ) -> ContextSnapshot:
        nonempty(context_id)
        nonempty(policy_revision)
        assumptions, constraints = tuple(assumptions), tuple(constraints)
        payload = dict(context_id=context_id, assumptions=assumptions,
                       constraints=constraints, policy_revision=policy_revision)

        def apply() -> ContextSnapshot:
            existing = self._contexts.get(context_id)
            if existing is not None:
                if (existing.assumptions, existing.constraints, existing.policy_revision) != (
                    assumptions, constraints, policy_revision
                ):
                    raise ValueError("context identity cannot be redefined")
                return self.snapshot(context_id)
            result = check_consistency(constraints, assumptions, max_variables=self._max_variables)
            if result.status is not Status.PASS:
                raise AdmissionDenied(result.status, result.detail)
            self._contexts[context_id] = _Context(
                context_id, assumptions, constraints, policy_revision
            )
            self._policy_versions[context_id, policy_revision] = constraints
            return self.snapshot(context_id)

        return self._mutate("open_context", idempotency_key, payload, apply)

    def snapshot(self, context_id: str) -> ContextSnapshot:
        with self._lock:
            self._ensure_open()
            context = self._contexts[context_id]
            return ContextSnapshot(
                context_id, context.revision, context.assumptions, context.constraints,
                context.policy_revision,
                tuple(context.beliefs[key] for key in sorted(context.usable)),
                context.logical_time,
            )

    def record_evidence(self, evidence: Evidence, *, idempotency_key: str) -> Evidence:
        def apply() -> Evidence:
            context = self._contexts[evidence.context_id]
            previous = self._evidence.get(evidence.evidence_id)
            if previous is not None:
                if previous != evidence:
                    raise IdempotencyConflict("evidence ID reused with different content")
                return previous
            self._evidence[evidence.evidence_id] = evidence
            context.revision += 1
            return evidence

        return self._mutate("record_evidence", idempotency_key, dict(evidence=evidence), apply)

    def revoke_evidence(self, evidence_id: str, *, idempotency_key: str) -> int:
        def apply() -> int:
            evidence = self._evidence[evidence_id]
            context = self._contexts[evidence.context_id]
            if evidence_id not in self._revoked:
                # A proposal records the complete leaf evidence closure. Remove
                # every dependent revision before publishing the new revision.
                affected = {
                    key for key in context.usable
                    if evidence_id in context.beliefs[key].proposal.evidence_ids
                }
                self._revoked.add(evidence_id)
                context.usable.difference_update(affected)
                context.revision += 1
            return context.revision

        return self._mutate("revoke_evidence", idempotency_key, dict(evidence_id=evidence_id), apply)

    def _invalidate(self, context: _Context, invalid: set[str]) -> None:
        """Remove exact dependent revisions without substituting alternative proofs."""
        while invalid:
            context.usable.difference_update(invalid)
            invalid = {key for key in context.usable
                       if any(p not in context.usable for p in
                              context.beliefs[key].proposal.premise_revision_ids)}

    def replace_rule(self, rule: Rule, expected_revision: str, *, idempotency_key: str) -> Rule:
        """Trusted registry update; all current permits require revalidation."""
        nonempty(expected_revision)

        def apply() -> Rule:
            previous = self._rules[rule.rule_id]
            if previous.revision != expected_revision:
                raise AdmissionDenied(Status.STALE, "rule registry revision changed")
            if previous == rule:
                return previous
            if (rule.rule_id, rule.revision) in self._rule_versions:
                raise ValueError("rule revisions are immutable and cannot be reused")
            self._rule_versions[rule.rule_id, rule.revision] = rule
            self._rules[rule.rule_id] = rule
            for context in self._contexts.values():
                affected = {key for key in context.usable if
                            self._transitions[context.beliefs[key].proposal.transition_id].rule_id
                            == rule.rule_id}
                self._invalidate(context, affected)
                context.revision += 1
            return rule

        return self._mutate("replace_rule", idempotency_key,
                            dict(rule=rule, expected_revision=expected_revision), apply)

    def replace_policy(
        self, context_id: str, policy_revision: str, constraints: tuple[Clause, ...],
        expected_revision: int, *, idempotency_key: str,
    ) -> ContextSnapshot:
        nonempty(policy_revision)
        logical_integer(expected_revision)
        constraints = tuple(constraints)

        def apply() -> ContextSnapshot:
            context = self._contexts[context_id]
            if context.revision != expected_revision:
                raise AdmissionDenied(Status.STALE, "context revision changed")
            if (policy_revision, constraints) == (context.policy_revision, context.constraints):
                return self.snapshot(context_id)
            if (context_id, policy_revision) in self._policy_versions:
                raise ValueError("policy revisions are immutable and cannot be reused")
            base = check_consistency(constraints, context.assumptions,
                                     max_variables=self._max_variables)
            if base.status is not Status.PASS:
                raise AdmissionDenied(base.status, "policy cannot certify the assumption environment")
            invalid = {key for key in context.usable if check_consistency(
                constraints, context.assumptions + (context.beliefs[key].conclusion,),
                max_variables=self._max_variables).status is not Status.PASS}
            context.constraints, context.policy_revision = constraints, policy_revision
            self._policy_versions[context_id, policy_revision] = constraints
            self._invalidate(context, invalid)
            if self._joint(context).status is not Status.PASS:
                # Do not pick one arbitrary world when a new joint constraint
                # conflicts with previously accepted alternatives. Re-admit explicitly.
                context.usable.clear()
            context.revision += 1
            return self.snapshot(context_id)

        return self._mutate("replace_policy", idempotency_key,
                            dict(context_id=context_id, policy_revision=policy_revision,
                                 constraints=constraints, expected_revision=expected_revision), apply)

    def _evidence_status(self, evidence: Evidence, context: _Context) -> Status:
        if evidence.evidence_id in self._revoked:
            return Status.STALE
        if context.logical_time < evidence.observed_at:
            return Status.UNKNOWN
        if evidence.valid_until is not None and context.logical_time >= evidence.valid_until:
            return Status.STALE
        return Status.PASS

    def advance_clock(self, context_id: str, logical_time: int, *,
                      idempotency_key: str) -> ContextSnapshot:
        """Monotone context clock; intervals are [observed_at, valid_until)."""
        logical_integer(logical_time)

        def apply() -> ContextSnapshot:
            context = self._contexts[context_id]
            if logical_time < context.logical_time:
                raise ValueError("logical time cannot move backwards")
            if logical_time != context.logical_time:
                context.logical_time = logical_time
                invalid = {key for key in context.usable if any(
                    self._evidence_status(self._evidence[e], context) is not Status.PASS
                    for e in context.beliefs[key].proposal.evidence_ids)}
                self._invalidate(context, invalid)
                # Coarse clock revisions invalidate pending permits even if no
                # evidence expires, including checks based on temporal absence.
                context.revision += 1
            return self.snapshot(context_id)

        return self._mutate("advance_clock", idempotency_key,
                            dict(context_id=context_id, logical_time=logical_time), apply)

    def propose_evidence(
        self, context_id: str, evidence_id: str, *, idempotency_key: str,
    ) -> Transition:
        """Explicit request to adopt a report under the hard-claim contract."""
        def apply() -> Transition:
            self._contexts[context_id]
            evidence = self._evidence[evidence_id]
            return self._register_transition(
                context_id, evidence.content, None, None, (), evidence_id
            )

        return self._mutate(
            "propose_evidence", idempotency_key, dict(context_id=context_id, evidence_id=evidence_id), apply
        )

    def propose_transition(
        self, context_id: str, rule_id: str, premise_revision_ids: tuple[str, ...], *,
        idempotency_key: str,
    ) -> Transition:
        premises = tuple(premise_revision_ids)
        for premise in premises:
            nonempty(premise)

        def apply() -> Transition:
            self._contexts[context_id]
            rule = self._rules[rule_id]
            return self._register_transition(
                context_id, rule.conclusion, rule.rule_id, rule.revision, premises, None
            )

        return self._mutate(
            "propose_transition", idempotency_key,
            dict(context_id=context_id, rule_id=rule_id, premise_revision_ids=premises), apply
        )

    def _register_transition(
        self, context_id: str, conclusion: Literal, rule_id: str | None,
        rule_revision: str | None, premises: tuple[str, ...], evidence_id: str | None,
    ) -> Transition:
        transition_id = identity("transition/v1", (
            context_id, asdict(conclusion), rule_id, rule_revision, premises, evidence_id
        ))
        transition = Transition(
            transition_id, context_id, conclusion, rule_id, rule_revision, premises, evidence_id
        )
        self._transitions[transition_id] = transition
        return transition

    def _registered(self, transition: Transition) -> _Context:
        if self._transitions.get(transition.transition_id) != transition:
            raise AdmissionDenied(Status.FAIL, "transition was not issued by this service")
        return self._contexts[transition.context_id]

    def _input_checks(self, transition: Transition, context: _Context) -> tuple[Check, ...]:
        if transition.evidence_id is not None:
            evidence = self._evidence[transition.evidence_id]
            return (
                Check("evidence_context", Status.PASS if evidence.context_id == context.context_id
                      else Status.FAIL, "report must belong to the exact context"),
                Check("evidence_current", self._evidence_status(evidence, context),
                      "report must be observed, unrevoked and within its validity interval"),
            )
        rule = self._rule_versions[transition.rule_id, transition.rule_revision]
        checks = [
            Check("rule_revision", Status.PASS if self._rules[rule.rule_id].revision == rule.revision
                  else Status.STALE, "pinned grounded rule revision"),
            Check("complete_premises", Status.PASS if len(transition.premise_revision_ids)
                  == len(rule.premises) else Status.UNKNOWN, "every rule premise is required"),
        ]
        # Find foreign revisions only to diagnose context mixing, never to use them.
        all_beliefs = {key: value for ctx in self._contexts.values()
                      for key, value in ctx.beliefs.items()}
        for index, revision_id in enumerate(transition.premise_revision_ids):
            belief = all_beliefs.get(revision_id)
            if belief is None:
                status, detail = Status.UNKNOWN, "premise revision is unavailable"
            elif belief.context_id != context.context_id:
                status, detail = Status.FAIL, "premise belongs to a different context"
            elif revision_id not in context.usable:
                status, detail = Status.STALE, "premise support has been revoked"
            elif index >= len(rule.premises) or belief.conclusion != rule.premises[index]:
                status, detail = Status.FAIL, "premise does not match its ordered binding"
            else:
                status, detail = Status.PASS, "exact usable premise revision"
            checks.append(Check(f"premise_{index}", status, detail))
        return tuple(checks)

    def _joint(self, context: _Context, additional: tuple[Literal, ...] = ()) -> LogicResult:
        assertions = context.assumptions + tuple(
            context.beliefs[key].conclusion for key in sorted(context.usable)
        ) + additional
        return check_consistency(
            context.constraints, assertions, max_variables=self._max_variables
        )

    def _issue(
        self, stage: str, subject_id: str, context: _Context, transition: Transition,
        checks: tuple[Check, ...], witness=None,
    ) -> Certificate:
        evidence_ids = {transition.evidence_id} if transition.evidence_id else set()
        for premise in transition.premise_revision_ids:
            if premise in context.beliefs:
                evidence_ids.update(context.beliefs[premise].proposal.evidence_ids)
        evidence_binding = tuple(asdict(self._evidence[key]) for key in sorted(evidence_ids))
        expiries = [self._evidence[key].valid_until for key in evidence_ids
                    if self._evidence[key].valid_until is not None]
        certificate = Certificate(
            identity("certificate/v2", (self._authority_id, len(self._certificates))),
            stage, subject_id, context.context_id,
            context.revision, context.policy_revision, transition.rule_revision, checks, witness,
            transition.transition_id, transition.premise_revision_ids,
            identity("lineage/v1", evidence_binding),
            identity("constraints/v1", ([asdict(c) for c in context.constraints],
                                       [asdict(a) for a in context.assumptions])),
            logical_time=context.logical_time, valid_until=min(expiries, default=None),
        )
        self._certificates[certificate.certificate_id] = certificate
        return certificate

    def precertify(
        self, transition: Transition, expected_revision: int, *, idempotency_key: str,
    ) -> Certificate:
        logical_integer(expected_revision)
        def apply() -> Certificate:
            context = self._registered(transition)
            joint = self._joint(context)
            checks = (
                Check("snapshot", Status.PASS if expected_revision == context.revision
                      else Status.STALE, "full context revision comparison"),
                *self._input_checks(transition, context),
                Check("joint_pre_state", joint.status, joint.detail),
            )
            return self._issue("pre", transition.transition_id, context,
                               transition, checks, joint.witness)

        return self._mutate("precertify", idempotency_key,
                            dict(transition=transition, expected_revision=expected_revision), apply)

    def _permit_check(
        self, certificate: Certificate, stage: str, subject_id: str, context: _Context,
    ) -> Check:
        if self._certificates.get(certificate.certificate_id) != certificate:
            return Check(f"{stage}_permit", Status.FAIL, "untrusted or altered certificate")
        if (certificate.stage, certificate.subject_id, certificate.context_id) != (
            stage, subject_id, context.context_id
        ):
            return Check(f"{stage}_permit", Status.FAIL, "certificate subject or stage mismatch")
        if (certificate.knowledge_revision != context.revision
                or certificate.policy_revision != context.policy_revision
                or certificate.logical_time != context.logical_time
                or certificate.valid_until is not None
                and context.logical_time >= certificate.valid_until):
            return Check(f"{stage}_permit", Status.STALE, "certificate dependencies changed")
        return Check(f"{stage}_permit", certificate.status, "verified service-issued contract")

    def _derive(self, transition: Transition, context: _Context) -> Proposal:
        # This function constructs a value only; it cannot commit a belief.
        if transition.evidence_id is not None:
            evidence_ids = (transition.evidence_id,)
        else:
            evidence_ids = tuple(sorted({
                evidence_id for premise_id in transition.premise_revision_ids
                for evidence_id in context.beliefs[premise_id].proposal.evidence_ids
            }))
        roots = tuple(sorted({root for evidence_id in evidence_ids
                              for root in self._evidence[evidence_id].lineage_roots}))
        payload = (transition.transition_id, evidence_ids, roots)
        return Proposal(
            identity("proposal/v1", payload), transition.transition_id, context.context_id,
            transition.conclusion, transition.premise_revision_ids, evidence_ids, roots,
        )

    def infer(self, transition: Transition, pre_certificate: Certificate) -> Proposal:
        with self._lock:
            self._ensure_open()
            context = self._registered(transition)
            check = self._permit_check(pre_certificate, "pre", transition.transition_id, context)
            if check.status is not Status.PASS:
                raise AdmissionDenied(check.status, check.detail)
            return self._derive(transition, context)

    def postcertify(
        self, proposal: Proposal, pre_certificate: Certificate, *, idempotency_key: str,
    ) -> Certificate:
        def apply() -> Certificate:
            transition = self._transitions[proposal.transition_id]
            context = self._registered(transition)
            permit = self._permit_check(pre_certificate, "pre", transition.transition_id, context)
            replay = Status.UNKNOWN
            if permit.status is Status.PASS:
                replay = Status.PASS if self._derive(transition, context) == proposal else Status.FAIL
            joint = self._joint(context, (proposal.conclusion,))
            checks = (permit, Check("formula_and_provenance", replay,
                                    "replay the complete grounded proposal"),
                      Check("joint_post_state", joint.status, joint.detail))
            return self._issue("post", proposal.proposal_id, context,
                               transition, checks, joint.witness)

        return self._mutate("postcertify", idempotency_key,
                            dict(proposal=proposal, pre_certificate=pre_certificate), apply)

    def commit(
        self, proposal: Proposal, pre_certificate: Certificate, post_certificate: Certificate,
        expected_revision: int, *, idempotency_key: str,
    ) -> CommitResult:
        logical_integer(expected_revision)
        def apply() -> CommitResult:
            transition = self._transitions.get(proposal.transition_id)
            if transition is None:
                return CommitResult(Status.FAIL, expected_revision, detail="unknown transition")
            context = self._registered(transition)
            checks = (
                Check("snapshot", Status.PASS if expected_revision == context.revision
                      else Status.STALE, "compare before atomic publication"),
                self._permit_check(pre_certificate, "pre", transition.transition_id, context),
                self._permit_check(post_certificate, "post", proposal.proposal_id, context),
            )
            status = conjunction(checks)
            if status is not Status.PASS:
                return CommitResult(status, context.revision, detail="; ".join(
                    c.detail for c in checks if c.status is not Status.PASS))
            if self._derive(transition, context) != proposal:
                return CommitResult(Status.FAIL, context.revision, detail="proposal was altered")
            for key in sorted(context.usable):
                existing = context.beliefs[key]
                if existing.proposal == proposal:
                    return CommitResult(Status.PASS, context.revision, existing, "idempotent support")
            belief_id = identity("belief/v2", (asdict(proposal), context.revision + 1,
                                                context.policy_revision))
            belief = BeliefRevision(
                belief_id, context.context_id, proposal.conclusion, context.revision + 1,
                proposal, pre_certificate.certificate_id, post_certificate.certificate_id,
            )
            context.beliefs[belief_id] = belief
            context.usable.add(belief_id)
            context.revision += 1
            return CommitResult(Status.PASS, context.revision, belief, "accepted hard claim")

        return self._mutate("commit", idempotency_key, dict(
            proposal=proposal, pre_certificate=pre_certificate, post_certificate=post_certificate,
            expected_revision=expected_revision), apply)

    def export_admission(self, context_id: str) -> tuple:
        """Immutable, revision-consistent diagnostic snapshot for storage adapters.

        Includes historical revisions and freshly checked views. Exporting grants
        no authority to import native Values as accepted beliefs or certificates.
        """
        with self._lock:
            self._ensure_open()
            context = self._contexts[context_id]
            conclusions = sorted({b.conclusion for b in context.beliefs.values()})
            return (self._authority_id, self.snapshot(context_id),
                    tuple(self.query_belief(context_id, c) for c in conclusions))

    def query_belief(self, context_id: str, conclusion: Literal) -> BeliefView:
        with self._lock:
            self._ensure_open()
            context = self._contexts[context_id]
            history = tuple(b for b in context.beliefs.values() if b.conclusion == conclusion)
            current = tuple(b for b in history if b.belief_revision_id in context.usable)
            # Historical permits never authorize a current read. Recheck the
            # complete state under the current revision and current support set.
            joint = self._joint(context)
            checks = (Check("current_joint_state", joint.status, joint.detail),)
            status = joint.status if current else (Status.STALE if history else Status.UNKNOWN)
            return BeliefView(status, context.revision,
                              current if status is Status.PASS else (), history, checks)
