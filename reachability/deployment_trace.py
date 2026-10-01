"""Public, one-event-at-a-time conformance adapter. No evaluator imports."""
import argparse
from dataclasses import asdict
from itertools import count
from pathlib import Path
import sys
from time import perf_counter_ns

from .codec import encode
from .completion import CompletionContract
from .decision_model import DecisionContract, DecisionCriterion
from .dispatch import Dispatcher
from .dispatch_model import DispatchPolicy
from .execution_model import ExecutionContract, ResourceDefinition, ResourceDemand
from .goal_model import DurabilityContract, GoalContract, GoalSlice, goal_sample_literal
from .lifecycle_model import LifecycleEdge, LifecycleSchema, LifecycleState, milestone_literal
from .model import Evidence, Literal, Statement, Status
from .pln_adapter import TruthValue
from .probability_model import ProbabilityPolicy, ProbabilityReport
from .requirements import Requirement
from .service import AdmissionDenied, AdmissionService
from .simulated_executor import SimulatedExecutor
from .trace_protocol import (DeploymentEvent, DeploymentInitial, TRACE_SCHEMA, canonical, fingerprint, read_json)


class _FaultTransport:
    """One scheduled transport fault; the decision service sees normal receipt semantics."""
    def __init__(self, executor, fault):
        self.executor, self.fault = executor, fault
        self.profile = executor.profile

    def submit(self, request):
        if self.fault == "before_effect":
            raise OSError("scheduled pre-effect transport failure")
        receipt = self.executor.submit(request)
        if self.fault == "lost_reply":
            raise OSError("scheduled lost acknowledgement")
        return receipt

    def query(self, request):
        return self.executor.query(request)

    def release(self, request):
        return self.executor.release(request)


class DeploymentSession:
    """Fixed public slice, durable service/executor, strict observed-event stream.

    Events may compose several journal commands; rejected later commands retain
    earlier observations. Records expose those actual effects without correction.
    """
    def __init__(self, initial: DeploymentInitial, directory):
        self.initial = DeploymentInitial.parse(asdict(initial))
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.local, self.remote = self.directory / "admission.db", self.directory / "executor.db"
        if self.local.exists() or self.remote.exists():
            raise ValueError("start a new trace in an empty database directory")
        self.service = AdmissionService(database=self.local, max_variables=20)
        try:
            self.executor = SimulatedExecutor(self.remote)
            self.attempts, self.seen = set(), set()
            self.step = 0
            self.certificates = []
            self._keys = count()
            self._prefix = "initial"
            self._initialize()
        except BaseException:
            self.close()
            raise

    def close(self):
        self.service.close()
        if hasattr(self, "executor"):
            self.executor.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def key(self):
        return f"trace:{self._prefix}:{next(self._keys)}"

    def fact(self, name):
        predicate = dict(tested="Tested", credential="CredentialValid", product="Available")[name]
        return Literal(Statement(predicate, (self.initial.product_id,)))

    @property
    def forecast(self):
        return Literal(Statement("DeploymentHealthyForecast", (self.initial.product_id,)))

    def _initialize(self):
        s, c = self.service, self.initial
        req = lambda name: Requirement("FACT", self.fact(name))
        schema = LifecycleSchema("artifact", "1", "artifact", c.product_id, "DRAFT",
            (LifecycleState("DRAFT"), LifecycleState("BUILT", req("product"))),
            (LifecycleEdge("deploy", "DRAFT", "BUILT", Requirement("AND", children=(req("tested"), req("credential"))),
                           req("product"), c.product_id, ("executor",)),), ("BUILT",), "deployment-trace/v1")
        s.open_context(c.context_id, idempotency_key=self.key())
        s.register_lifecycle_schema(schema, idempotency_key=self.key())
        s.open_lifecycle_episode("episode", c.context_id, "artifact", "1", idempotency_key=self.key())
        s.register_resource(ResourceDefinition("slot", c.capacity, "slots"), idempotency_key=self.key())
        s.register_execution_contract(ExecutionContract("deploy", "1", "artifact", "1", "deploy", "executor", ("worker",),
            (ResourceDemand("slot", 1, "slots"),), c.lease_duration), idempotency_key=self.key())
        s.configure_probability_policy(c.context_id, ProbabilityPolicy("1", ("forecast-model",)), idempotency_key=self.key())
        s.register_decision_contract(DecisionContract("acceptance", "1", "deploy", "1", c.product_id, (
            DecisionCriterion("forecast", self.forecast, c.min_strength, 1, c.min_confidence),)), idempotency_key=self.key())
        s.register_dispatch_policy(DispatchPolicy("dispatch", "1", "deploy", "1", self.executor.profile), idempotency_key=self.key())
        s.register_goal_contract(GoalContract("health", "1", "obligation-units", (
            GoalSlice("healthy", c.loss, c.product_id, req("product"), DurabilityContract(3, 1, 1, ("monitor",))),),
            "deployment-trace/v1"), idempotency_key=self.key())
        s.open_goal_episode(c.goal_id, "source", c.context_id, "health", "1", idempotency_key=self.key())
        s.register_completion_contract(CompletionContract("completion", "1", "artifact", "1", "deploy", "health", "1"),
                                       idempotency_key=self.key())

    def _adopt(self, evidence_id, literal, source, valid_until=None, truth=None):
        s, ctx = self.service, self.initial.context_id
        now = s.snapshot(ctx).logical_time
        s.record_evidence(Evidence(evidence_id, ctx, literal, source, now, (evidence_id,), valid_until), idempotency_key=self.key())
        if truth is not None:
            s.record_probability_report(ProbabilityReport(evidence_id, truth), idempotency_key=self.key())
            transition = s.propose_probability(ctx, "observation", evidence_id=evidence_id, idempotency_key=self.key())
            rev = s.snapshot(ctx).knowledge_revision
            pre = s.precertify_probability(transition, rev, idempotency_key=self.key())
            self.certificates.append(pre)
            proposal = s.infer_probability(transition, pre)
            post = s.postcertify_probability(proposal, pre, idempotency_key=self.key())
            self.certificates.append(post)
            result = s.commit_probability(proposal, pre, post, rev, idempotency_key=self.key())
        else:
            transition = s.propose_evidence(ctx, evidence_id, idempotency_key=self.key())
            rev = s.snapshot(ctx).knowledge_revision
            pre = s.precertify(transition, rev, idempotency_key=self.key())
            self.certificates.append(pre)
            proposal = s.infer(transition, pre)
            post = s.postcertify(proposal, pre, idempotency_key=self.key())
            self.certificates.append(post)
            result = s.commit(proposal, pre, post, rev, idempotency_key=self.key())
        if result.status is not Status.PASS:
            raise AdmissionDenied(result.status, result.detail)
        return result.belief

    def restart(self):
        self.close()
        self.service = AdmissionService(database=self.local)
        try:
            self.executor = SimulatedExecutor(self.remote)
        except BaseException:
            self.service.close()
            raise

    def _execute(self, event):
        s, c, a, kind = self.service, self.initial, dict(event.arguments), event.kind
        attempt = a.get("attempt_id")
        if kind == "fact":
            self._adopt(event.event_id, self.fact(a["name"]), "sensor", a["valid_until"])
        elif kind == "forecast":
            self._adopt(event.event_id, self.forecast, "forecast-model", a["valid_until"],
                        TruthValue(a["strength"], a["confidence"]))
        elif kind == "revoke":
            s.revoke_evidence(a["evidence_id"], idempotency_key=self.key())
        elif kind == "tick":
            s.advance_clock(c.context_id, a["time"], idempotency_key=self.key())
            s.advance_resource_clock(a["time"], idempotency_key=self.key())
        elif kind == "attempt":
            operation = s.propose_operation("deploy", attempt, "episode", "deploy", idempotency_key=self.key())
            s.select_operation(attempt, operation.revision, idempotency_key=self.key())
            self.attempts.add(attempt)
        elif kind == "reserve":
            permit = s.certify_execution(attempt, "deploy", "1", "worker", s.inspect_operation(attempt).operation.revision,
                s.snapshot(c.context_id).knowledge_revision, s.resource_snapshot().revision, idempotency_key=self.key())
            self.certificates.append(permit)
            s.reserve_and_record_intent(permit, idempotency_key=self.key())
        elif kind == "cover":
            s.claim_goal_coverage(event.event_id, c.goal_id, "healthy", attempt, "worker", a["units"], a["valid_until"],
                                  idempotency_key=self.key())
        elif kind == "prepare":
            s.prepare_dispatch(attempt, "dispatch", "1", "worker", idempotency_key=self.key())
        elif kind in ("dispatch", "reconcile", "release"):
            dispatcher = Dispatcher(s, _FaultTransport(self.executor, a.get("fault", "none")))
            if kind == "dispatch":
                dispatcher.dispatch(attempt, "dispatch", "1", "worker")
            else:
                getattr(dispatcher, kind)(attempt, "worker")
        elif kind == "observation":
            belief = self._adopt(event.event_id, milestone_literal(attempt, a["product_id"], a["milestone"]), "executor")
            s.record_operation_observation(event.event_id, attempt, a["milestone"], belief.belief_revision_id,
                                           idempotency_key=self.key())
        elif kind == "sample":
            literal = goal_sample_literal(c.goal_id, "healthy", c.product_id, s.snapshot(c.context_id).logical_time, a["healthy"])
            belief = self._adopt(event.event_id, literal, "monitor")
            s.record_goal_sample(event.event_id, c.goal_id, "healthy", a["healthy"], belief.belief_revision_id,
                                 idempotency_key=self.key())
        elif kind == "censor":
            s.censor_goal_monitor(c.goal_id, "healthy", "trace-censor", idempotency_key=self.key())
        elif kind == "resume":
            s.resume_goal_monitor(c.goal_id, "healthy", idempotency_key=self.key())
        elif kind == "account":
            s.reconcile_goal(c.goal_id, s.inspect_goal(c.goal_id).projection.fingerprint, idempotency_key=self.key())
        elif kind == "complete":
            permit = s.certify_goal_completion("completion", "1", attempt, c.goal_id,
                s.inspect_lifecycle("episode").episode.revision, s.snapshot(c.context_id).knowledge_revision, idempotency_key=self.key())
            self.certificates.append(permit)
            s.advance_goal_completion(permit, permit.episode_revision, idempotency_key=self.key())
        elif kind == "restart":
            self.restart()
        else:
            raise ValueError("unsupported event")

    def projection(self):
        s, c = self.service, self.initial
        _, snapshot, views = s.export_admission(c.context_id)
        hard = {}
        for view in views:
            for belief in view.historical:
                for evidence_id in belief.proposal.evidence_ids:
                    hard[evidence_id] = dict(literal=dict(statement=dict(predicate=belief.conclusion.statement.predicate,
                        arguments=list(belief.conclusion.statement.arguments)), positive=belief.conclusion.positive),
                        current=belief in view.current)
        numeric = s.query_probability(c.context_id, self.forecast)
        forecasts = {b.proposal.support.evidence_ids[0]: dict(strength=b.proposal.support.truth.strength,
            confidence=b.proposal.support.truth.confidence, current=b in numeric.current) for b in numeric.historical}
        attempts = {}
        for attempt in sorted(self.attempts):
            op = s.inspect_operation(attempt)
            data = dict(observed=list(op.observed_milestones), current=list(op.current_milestones),
                        readiness=op.readiness.value, intent=None, dispatch=None, decision=None)
            try:
                view = s.inspect_execution_intent(attempt)
            except KeyError:
                pass
            else:
                bound = s.execution_decision(view.intent.certificate_id)
                numerical_ids = {b.belief_revision_id: b.proposal.support.evidence_ids[0] for b in numeric.historical}
                data["intent"] = dict(state=view.state, readiness=view.readiness.value, starts_at=view.intent.created_at,
                    ends_at=view.intent.lease_until, basis=sorted(numerical_ids[item.belief_revision_id]
                        for item in bound.criteria[0].current))
            data["decision"] = s.inspect_probability_decision(attempt, "deploy", "1").status.value
            try:
                dispatch = s.inspect_dispatch(attempt)
            except KeyError:
                pass
            else:
                data["dispatch"] = dict(state=dispatch.state, prepared_at=dispatch.dispatch.prepared_at,
                    effect_count=dispatch.latest_receipt.effect_count if dispatch.latest_receipt else None)
            attempts[attempt] = data
        goal = s.inspect_goal(c.goal_id)
        resource = s.inspect_resource("slot")
        return dict(logical_time=snapshot.logical_time, hard=hard, forecasts=forecasts, attempts=attempts,
            stage=s.inspect_lifecycle("episode").episode.stage,
            goal=dict(label=goal.projection.slices[0].label, outstanding=goal.projection.outstanding_loss,
                covered=goal.projection.estimated_committed_coverage, open=goal.projection.open_loss,
                selected_commitment=goal.projection.slices[0].selected_commitment,
                accounted_loss=goal.history[-1].projection.outstanding_loss if goal.history else c.loss,
                relief=[dict(kind=event.kind, units=event.units, time=event.logical_time, causal_attempt_id=event.causal_attempt_id)
                        for revision in goal.history for event in revision.events]),
            resource=dict(used=resource.used_now, uncertain=list(resource.reconciliation_attempts)))

    def apply(self, message):
        event = DeploymentEvent.parse(message)
        if event.event_id in self.seen or self.step >= 128:
            raise ValueError("a trace requires unique event IDs and at most 128 events")
        args = dict(event.arguments)
        now = self.service.snapshot(self.initial.context_id).logical_time
        if (event.kind == "tick" and args["time"] < now
                or event.kind in ("fact", "forecast") and args["valid_until"] is not None and args["valid_until"] <= now):
            raise ValueError("invalid event time or evidence validity interval")
        self.seen.add(event.event_id)
        self.step += 1
        self._prefix, self._keys, self.certificates = "event:" + event.event_id, count(), []
        start, journal_before = perf_counter_ns(), self.service._journal_sequence
        status, detail = "PASS", "command applied"
        try:
            self._execute(event)
        except AdmissionDenied as error:
            status, detail = error.status.value, str(error)
        except KeyError as error:
            status, detail = "FAIL", "missing referenced record: " + str(error)
        projection = self.projection()
        return dict(schema=TRACE_SCHEMA, step=self.step, event_id=event.event_id,
            event_digest=fingerprint(message), initial_digest=fingerprint(asdict(self.initial)),
            outcome=dict(status=status, detail=detail), projection=projection,
            projection_digest=fingerprint(projection), diagnostics=dict(
                knowledge_revision=self.service.snapshot(self.initial.context_id).knowledge_revision,
                resource_revision=self.service.resource_snapshot().revision,
                journal_commands=self.service._journal_sequence - journal_before,
                elapsed_ns=perf_counter_ns() - start, certificates=encode(tuple(self.certificates))),
            instrumentation=dict(executor_effects=self.executor.total_effects))


def main():
    parser = argparse.ArgumentParser(description="Read public initial JSON, then one event per line; emit actual trace records.")
    parser.add_argument("--database-dir", type=Path, required=True)
    args = parser.parse_args()
    initial = DeploymentInitial.parse(read_json(sys.stdin.readline()))
    with DeploymentSession(initial, args.database_dir) as session:
        print(canonical(dict(schema=TRACE_SCHEMA, initial=session.projection())), flush=True)
        for line in sys.stdin:
            print(canonical(session.apply(read_json(line))), flush=True)


if __name__ == "__main__":
    main()
