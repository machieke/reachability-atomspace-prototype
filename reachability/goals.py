"""Persistent goal obligations, conservative coverage and observed relief history."""
from dataclasses import asdict, dataclass, field, replace

from .errors import AdmissionDenied, IdempotencyConflict
from .execution_model import positive_integer
from .goal_logic import evaluate_durability
from .goal_model import (
    CoverageCommitment, GoalAccountingRevision, GoalContract, GoalEpisode, GoalMonitor,
    GoalProjection, GoalReliefEvent, GoalSample, GoalSliceView, GoalView, goal_sample_literal,
)
from .model import Status, identity, logical_integer, nonempty
from .requirements import validate_requirement


@dataclass
class GoalStore:
    contracts: dict[tuple[str, str], GoalContract] = field(default_factory=dict)
    goals: dict[str, GoalEpisode] = field(default_factory=dict)
    sources: dict[tuple[str, str], str] = field(default_factory=dict)
    samples: dict[str, GoalSample] = field(default_factory=dict)
    coverage: dict[str, CoverageCommitment] = field(default_factory=dict)
    revisions: dict[str, int] = field(default_factory=dict)
    history: dict[str, tuple[GoalAccountingRevision, ...]] = field(default_factory=dict)


class GoalMixin:
    GOAL_COMMANDS = frozenset(("register_goal_contract", "open_goal_episode", "record_goal_sample",
        "censor_goal_monitor", "resume_goal_monitor", "claim_goal_coverage", "withdraw_goal_coverage", "reconcile_goal"))

    def _goal_changed(self, goal_id):
        self._goals.revisions[goal_id] = self._goals.revisions.get(goal_id, 0) + 1

    def _goal_contract(self, goal):
        return self._goals.contracts[goal.contract_id, goal.contract_revision]

    def _goal_slice(self, goal, slice_id):
        return next(item for item in self._goal_contract(goal).slices if item.slice_id == slice_id)

    def _goal_monitor(self, goal, slice_id):
        return next(monitor for monitor in reversed(goal.monitors) if monitor.slice_id == slice_id)

    @staticmethod
    def _measurement_identity(sample):
        return identity("goal-measurement/v1", (sample.goal_id, sample.slice_id, sample.product_id,
                        sample.observed_at, sample.healthy, tuple(sorted(sample.lineage_roots))))

    def register_goal_contract(self, contract: GoalContract, *, idempotency_key: str) -> GoalContract:
        if not isinstance(contract, GoalContract):
            raise ValueError("a typed goal contract is required")
        if len(contract.slices) > 32 or any(item.durability.samples > 16
                or validate_requirement(item.condition) is not Status.PASS for item in contract.slices):
            raise AdmissionDenied(Status.UNKNOWN, "goal contract exceeds the supported finite fragment")

        def apply():
            key = contract.contract_id, contract.revision
            previous = self._goals.contracts.get(key)
            if previous is not None and previous != contract:
                raise IdempotencyConflict("goal contract revisions are immutable")
            self._goals.contracts[key] = contract
            return contract

        return self._mutate("register_goal_contract", idempotency_key, dict(contract=contract), apply)

    def open_goal_episode(self, goal_id: str, source_id: str, context_id: str, contract_id: str,
                          contract_revision: str, *, idempotency_key: str) -> GoalEpisode:
        for value in (goal_id, source_id, context_id, contract_id, contract_revision):
            nonempty(value)

        def apply():
            context = self._contexts[context_id]
            contract = self._goals.contracts[contract_id, contract_revision]
            previous = self._goals.goals.get(goal_id)
            if previous is not None:
                if (previous.source_id, previous.context_id, previous.contract_id, previous.contract_revision) != (
                        source_id, context_id, contract_id, contract_revision):
                    raise IdempotencyConflict("goal identity cannot change its obligation")
                return previous
            if (context_id, source_id) in self._goals.sources:
                raise IdempotencyConflict("this scoped source already has a goal; aliases cannot duplicate loss")
            monitors = tuple(GoalMonitor(identity("goal-monitor/v1", (self._authority_id, goal_id, item.slice_id, 0)),
                                        item.slice_id, context.logical_time) for item in contract.slices)
            goal = GoalEpisode(goal_id, source_id, context_id, contract_id, contract_revision, context.logical_time, monitors)
            self._goals.goals[goal_id] = goal
            self._goals.sources[context_id, source_id] = goal_id
            self._goal_changed(goal_id)
            return goal

        return self._mutate("open_goal_episode", idempotency_key, dict(goal_id=goal_id, source_id=source_id,
            context_id=context_id, contract_id=contract_id, contract_revision=contract_revision), apply)

    def record_goal_sample(self, sample_id: str, goal_id: str, slice_id: str, healthy: bool,
                           belief_revision_id: str, *, idempotency_key: str) -> GoalSample:
        nonempty(sample_id)
        if type(healthy) is not bool:
            raise ValueError("sample polarity must be Boolean")

        def apply():
            previous = self._goals.samples.get(sample_id)
            if previous is not None:
                if (previous.goal_id, previous.slice_id, previous.healthy, previous.belief_revision_id) != (
                        goal_id, slice_id, healthy, belief_revision_id):
                    raise IdempotencyConflict("sample identity cannot be rebound")
                return previous
            goal = self._goals.goals[goal_id]
            item, monitor = self._goal_slice(goal, slice_id), self._goal_monitor(goal, slice_id)
            context = self._contexts[goal.context_id]
            if monitor.censored_at is not None:
                raise AdmissionDenied(Status.STALE, "monitoring is censored; explicitly resume a new window")
            belief = context.beliefs.get(belief_revision_id)
            if belief is None or belief_revision_id not in context.usable:
                raise AdmissionDenied(Status.UNKNOWN if belief is None else Status.STALE, "sample support is not current")
            transition = self._transitions[belief.proposal.transition_id]
            if transition.evidence_id is None:
                raise AdmissionDenied(Status.FAIL, "monitor samples require direct observation evidence")
            evidence = self._evidence[transition.evidence_id]
            if belief.conclusion != goal_sample_literal(goal_id, slice_id, item.product_id, evidence.observed_at, healthy):
                raise AdmissionDenied(Status.FAIL, "sample does not match exact goal, slice, product, time and polarity")
            if (evidence.source not in item.durability.sources or evidence.observed_at < monitor.opened_at
                    or (evidence.observed_at - monitor.opened_at) % item.durability.interval):
                raise AdmissionDenied(Status.FAIL, "sample violates source, monitoring window or sampling grid")
            sample = GoalSample(sample_id, goal_id, slice_id, monitor.monitor_id, item.product_id, healthy,
                evidence.observed_at, belief_revision_id, evidence.evidence_id, evidence.lineage_roots)
            self._goals.samples[sample_id] = sample
            self._goal_changed(goal_id)
            return sample

        return self._mutate("record_goal_sample", idempotency_key, dict(sample_id=sample_id, goal_id=goal_id,
            slice_id=slice_id, healthy=healthy, belief_revision_id=belief_revision_id), apply)

    def censor_goal_monitor(self, goal_id: str, slice_id: str, reason: str, *, idempotency_key: str) -> GoalMonitor:
        nonempty(reason)

        def apply():
            goal = self._goals.goals[goal_id]
            monitor = self._goal_monitor(goal, slice_id)
            if monitor.censored_at is not None:
                if monitor.reason != reason:
                    raise IdempotencyConflict("the censoring record is immutable")
                return monitor
            updated = replace(monitor, censored_at=self._contexts[goal.context_id].logical_time, reason=reason)
            self._goals.goals[goal_id] = replace(goal, monitors=tuple(updated if m == monitor else m for m in goal.monitors))
            self._goal_changed(goal_id)
            return updated

        return self._mutate("censor_goal_monitor", idempotency_key,
                            dict(goal_id=goal_id, slice_id=slice_id, reason=reason), apply)

    def resume_goal_monitor(self, goal_id: str, slice_id: str, *, idempotency_key: str) -> GoalMonitor:
        def apply():
            goal = self._goals.goals[goal_id]
            previous = self._goal_monitor(goal, slice_id)
            if previous.censored_at is None:
                return previous
            monitor = GoalMonitor(identity("goal-monitor/v1", (self._authority_id, goal_id, slice_id, len(goal.monitors))),
                                  slice_id, self._contexts[goal.context_id].logical_time)
            self._goals.goals[goal_id] = replace(goal, monitors=(*goal.monitors, monitor))
            self._goal_changed(goal_id)
            return monitor

        return self._mutate("resume_goal_monitor", idempotency_key, dict(goal_id=goal_id, slice_id=slice_id), apply)

    def _coverage_live(self, commitment: CoverageCommitment) -> bool:
        goal = self._goals.goals[commitment.goal_id]
        monitor = self._goal_monitor(goal, commitment.slice_id)
        now = self._contexts[goal.context_id].logical_time
        intent = self._execution.intents[commitment.attempt_id]
        if (commitment.withdrawn_at is not None or monitor.censored_at is not None
                or commitment.monitor_id != monitor.monitor_id or now != self._execution.logical_time
                or now >= min(commitment.valid_until, intent.lease_until)):
            return False
        operation = self.inspect_operation(commitment.attempt_id)
        if {"failure_observed", "cancellation_observed"}.intersection(operation.observed_milestones):
            return False
        if any(sample.goal_id == goal.goal_id and sample.slice_id == commitment.slice_id
               and sample.monitor_id == monitor.monitor_id and not sample.healthy
               and self._measurement_identity(sample) not in commitment.baseline_measurements
               for sample in self._goals.samples.values()):
            return False
        if commitment.attempt_id in self._dispatch.attempts:
            return self.inspect_dispatch(commitment.attempt_id).state == "accepted"
        return self.inspect_execution_intent(commitment.attempt_id).readiness is Status.PASS

    def claim_goal_coverage(self, commitment_id: str, goal_id: str, slice_id: str, attempt_id: str,
                            owner_id: str, units: int, valid_until: int, *, idempotency_key: str) -> CoverageCommitment:
        nonempty(commitment_id)
        positive_integer(units)
        logical_integer(valid_until)

        def apply():
            previous = self._goals.coverage.get(commitment_id)
            if previous is not None:
                if (previous.goal_id, previous.slice_id, previous.attempt_id, previous.owner_id,
                        previous.units, previous.valid_until) != (goal_id, slice_id, attempt_id, owner_id, units, valid_until):
                    raise IdempotencyConflict("coverage commitment identity is immutable")
                return previous
            goal = self._goals.goals[goal_id]
            item, monitor = self._goal_slice(goal, slice_id), self._goal_monitor(goal, slice_id)
            intent = self._execution.intents[attempt_id]
            now = self._contexts[goal.context_id].logical_time
            if ((intent.context_id, intent.product_id, intent.owner_id) != (goal.context_id, item.product_id, owner_id)
                    or units > item.loss or not now < valid_until <= intent.lease_until):
                raise AdmissionDenied(Status.FAIL, "coverage must bind the exact intent, product, owner, units and live lease")
            commitment = CoverageCommitment(commitment_id, goal_id, slice_id, monitor.monitor_id,
                attempt_id, owner_id, units, now, valid_until,
                tuple(sorted({self._measurement_identity(sample) for sample in self._goals.samples.values()
                              if sample.goal_id == goal_id and sample.slice_id == slice_id})))
            if not self._coverage_live(commitment):
                raise AdmissionDenied(Status.UNKNOWN, "there is no supported live commitment for coverage")
            self._goals.coverage[commitment_id] = commitment
            self._goal_changed(goal_id)
            return commitment

        return self._mutate("claim_goal_coverage", idempotency_key, dict(commitment_id=commitment_id, goal_id=goal_id,
            slice_id=slice_id, attempt_id=attempt_id, owner_id=owner_id, units=units, valid_until=valid_until), apply)

    def withdraw_goal_coverage(self, commitment_id: str, owner_id: str, *, idempotency_key: str) -> CoverageCommitment:
        def apply():
            commitment = self._goals.coverage[commitment_id]
            if commitment.owner_id != owner_id:
                raise AdmissionDenied(Status.FAIL, "only the recorded owner can withdraw this promise")
            if commitment.withdrawn_at is not None:
                return commitment
            goal = self._goals.goals[commitment.goal_id]
            updated = replace(commitment, withdrawn_at=self._contexts[goal.context_id].logical_time)
            self._goals.coverage[commitment_id] = updated
            self._goal_changed(goal.goal_id)
            return updated

        return self._mutate("withdraw_goal_coverage", idempotency_key,
                            dict(commitment_id=commitment_id, owner_id=owner_id), apply)

    def _project_goal(self, goal_id: str) -> GoalProjection:
        goal = self._goals.goals[goal_id]
        contract = self._goal_contract(goal)
        context = self._contexts[goal.context_id]
        views = []
        for item in contract.slices:
            condition = self._evaluate_requirement(goal.context_id, item.condition)
            monitor = self._goal_monitor(goal, item.slice_id)
            samples = tuple(sample for sample in self._goals.samples.values() if sample.goal_id == goal_id
                            and sample.slice_id == item.slice_id)
            durability = evaluate_durability(item.durability, monitor, samples, frozenset(context.usable),
                                             context.logical_time, condition.status)
            loss = 0 if durability.label == "OBSERVED_SUCCESS" else item.loss
            promises = [promise for promise in self._goals.coverage.values() if promise.goal_id == goal_id
                        and promise.slice_id == item.slice_id and self._coverage_live(promise)]
            # Same-slice promises overlap completely absent a stronger model.
            chosen = min(promises, key=lambda promise: (-promise.units, promise.commitment_id)) if promises and loss else None
            covered = min(loss, chosen.units) if chosen is not None else 0
            views.append(GoalSliceView(item.slice_id, durability.label, condition, durability.samples,
                durability.checks, loss, covered, chosen.commitment_id if chosen else None,
                durability.label != "OBSERVED_SUCCESS"))
        views = tuple(views)
        loss, coverage = sum(view.outstanding_loss for view in views), sum(view.estimated_coverage for view in views)
        epochs = (context.revision, self._goals.revisions[goal_id], self._lifecycle_revision(goal.context_id),
                  self._execution.revision, context.logical_time)
        fingerprint = identity("goal-projection/v1", (asdict(goal), asdict(contract), epochs, tuple(map(asdict, views))))
        return GoalProjection(goal_id, contract.unit, views, loss, coverage, loss - coverage, *epochs, fingerprint)

    def inspect_goal(self, goal_id: str) -> GoalView:
        with self._lock:
            self._ensure_open()
            projection = self._project_goal(goal_id)
            history = self._goals.history.get(goal_id, ())
            return GoalView(self._goals.goals[goal_id], projection, history,
                            not history or history[-1].projection.fingerprint != projection.fingerprint)

    def reconcile_goal(self, goal_id: str, expected_fingerprint: str, *, idempotency_key: str) -> GoalAccountingRevision:
        nonempty(expected_fingerprint)

        def apply():
            projection = self._project_goal(goal_id)
            if projection.fingerprint != expected_fingerprint:
                raise AdmissionDenied(Status.STALE, "goal monitor dependencies changed")
            history = self._goals.history.get(goal_id, ())
            if history and history[-1].projection.fingerprint == projection.fingerprint:
                return history[-1]
            number = len(history) + 1
            revision_id = identity("goal-accounting/v1", (self._authority_id, goal_id, number, projection.fingerprint))
            previous = ({view.slice_id: view.outstanding_loss for view in history[-1].projection.slices}
                        if history else {item.slice_id: item.loss for item in self._goal_contract(self._goals.goals[goal_id]).slices})
            events = []
            for view in projection.slices:
                delta = previous[view.slice_id] - view.outstanding_loss
                if delta:
                    events.append(GoalReliefEvent(identity("goal-relief/v1", (revision_id, view.slice_id)), view.slice_id,
                        "observed_relief" if delta > 0 else "reopened", abs(delta), projection.unit,
                        projection.logical_time, tuple(sample.sample_id for sample in view.samples)))
            revision = GoalAccountingRevision(revision_id, number, projection, tuple(events))
            self._goals.history[goal_id] = (*history, revision)
            return revision

        return self._mutate("reconcile_goal", idempotency_key,
                            dict(goal_id=goal_id, expected_fingerprint=expected_fingerprint), apply)
