"""Finite deployment slice: coverage, exact outcomes, sampled durability and reopening."""
from itertools import count
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from .completion import CompletionContract
from .dispatch import Dispatcher
from .dispatch_model import DispatchPolicy
from .execution_model import ExecutionContract, ResourceDefinition, ResourceDemand
from .goal_model import DurabilityContract, GoalContract, GoalSlice, goal_sample_literal
from .lifecycle_model import LifecycleEdge, LifecycleSchema, LifecycleState, milestone_literal
from .model import Evidence, Literal, Statement
from .requirements import Requirement
from .service import AdmissionDenied, AdmissionService
from .simulated_executor import SimulatedExecutor


def run() -> dict[str, object]:
    tested = Literal(Statement("Tested", ("artifact-v2",)))
    credential = Literal(Statement("CredentialValid", ("credential",)))
    product = Literal(Statement("Available", ("artifact-v2",)))
    fact = lambda literal: Requirement("FACT", literal)
    schema = LifecycleSchema("artifact", "1", "artifact", "artifact-v2", "DRAFT",
        (LifecycleState("DRAFT"), LifecycleState("BUILT", fact(product))),
        (LifecycleEdge("deploy", "DRAFT", "BUILT", Requirement("AND", children=(fact(tested), fact(credential))),
                       fact(product), "artifact-v2", ("executor",)),), ("BUILT",), "goal-demo")
    execution = ExecutionContract("deploy", "1", "artifact", "1", "deploy", "executor", ("worker",),
                                   (ResourceDemand("slot", 1, "slots"),), 10)
    goal_contract = GoalContract("healthy-service", "1", "obligation-units", (
        GoalSlice("healthy", 10, "artifact-v2", fact(product), DurabilityContract(3, 1, 1, ("monitor",))),), "goal-demo")
    sequence = count()

    def key():
        return f"goal-demo:{next(sequence)}"

    def accept(service, literal, source="sensor", valid_until=None):
        evidence_id = key()
        service.record_evidence(Evidence(evidence_id, "ctx", literal, source,
            service.snapshot("ctx").logical_time, (evidence_id,), valid_until), idempotency_key=key())
        transition = service.propose_evidence("ctx", evidence_id, idempotency_key=key())
        revision = service.snapshot("ctx").knowledge_revision
        pre = service.precertify(transition, revision, idempotency_key=key())
        proposal = service.infer(transition, pre)
        post = service.postcertify(proposal, pre, idempotency_key=key())
        return service.commit(proposal, pre, post, revision, idempotency_key=key()).belief

    def observe(service, milestone, product_id="artifact-v2"):
        belief = accept(service, milestone_literal("attempt", product_id, milestone), "executor")
        service.record_operation_observation(key(), "attempt", milestone, belief.belief_revision_id, idempotency_key=key())

    def certify(service):
        return service.certify_execution("attempt", "deploy", "1", "worker",
            service.inspect_operation("attempt").operation.revision, service.snapshot("ctx").knowledge_revision,
            service.resource_snapshot().revision, idempotency_key=key())

    def tick(service, time):
        service.advance_clock("ctx", time, idempotency_key=key())
        service.advance_resource_clock(time, idempotency_key=key())

    def sample(service, time, healthy=True):
        belief = accept(service, goal_sample_literal("goal", "healthy", "artifact-v2", time, healthy), "monitor")
        service.record_goal_sample(key(), "goal", "healthy", healthy, belief.belief_revision_id, idempotency_key=key())
        view = service.inspect_goal("goal")
        return service.reconcile_goal("goal", view.projection.fingerprint, idempotency_key=key())

    with TemporaryDirectory() as directory:
        local, remote = Path(directory) / "admission.db", Path(directory) / "executor.db"
        with AdmissionService(database=local) as service, SimulatedExecutor(remote) as executor:
            service.open_context("ctx", idempotency_key=key())
            service.register_lifecycle_schema(schema, idempotency_key=key())
            service.open_lifecycle_episode("episode", "ctx", "artifact", "1", idempotency_key=key())
            service.propose_operation("deploy", "attempt", "episode", "deploy", idempotency_key=key())
            service.select_operation("attempt", 0, idempotency_key=key())
            service.register_resource(ResourceDefinition("slot", 1, "slots"), idempotency_key=key())
            service.register_execution_contract(execution, idempotency_key=key())
            service.register_dispatch_policy(DispatchPolicy("dispatch", "1", "deploy", "1", executor.profile), idempotency_key=key())
            service.register_goal_contract(goal_contract, idempotency_key=key())
            service.open_goal_episode("goal", "run-healthy-artifact-v2", "ctx", "healthy-service", "1", idempotency_key=key())
            service.register_completion_contract(CompletionContract("completion", "1", "artifact", "1", "deploy",
                                                                    "healthy-service", "1"), idempotency_key=key())
            accept(service, tested)
            missing = certify(service).status.value
            accept(service, credential, valid_until=1)
            service.reserve_and_record_intent(certify(service), idempotency_key=key())
            service.claim_goal_coverage("promise", "goal", "healthy", "attempt", "worker", 6, 10, idempotency_key=key())
            before = service.inspect_goal("goal").projection
            dispatcher = Dispatcher(service, executor)
            dispatcher.dispatch("attempt", "dispatch", "1", "worker")
            after_ack = service.inspect_goal("goal").projection.outstanding_loss
            tick(service, 1)
            try:
                observe(service, "exact_product_observed", "artifact-v1")
            except AdmissionDenied as error:
                wrong_product = error.status.value
            accept(service, product)
            observe(service, "completion_observed")
            observe(service, "exact_product_observed")
            losses = []
            for time in (1, 2, 3):
                tick(service, time)
                losses.append(sample(service, time).projection.outstanding_loss)
            permit = service.certify_goal_completion("completion", "1", "attempt", "goal", 0,
                service.snapshot("ctx").knowledge_revision, idempotency_key=key())
            service.advance_goal_completion(permit, 0, idempotency_key=key())
            dispatcher.release("attempt", "worker")
            credential_status = service.query_belief("ctx", credential).status.value
            tick(service, 4)
            sample(service, 4, False)
        with AdmissionService(database=local) as recovered:
            view = recovered.inspect_goal("goal")
            return {
                "scope": "finite deployment conformance with a local executor simulator",
                "missing_submission_credential": missing,
                "before_dispatch": {"outstanding": before.outstanding_loss,
                    "covered": before.estimated_committed_coverage, "open": before.open_loss},
                "outstanding_after_ack": after_ack,
                "wrong_product": wrong_product,
                "loss_after_health_samples": losses,
                "credential_at_completion": credential_status,
                "completion_certificate": permit.status.value,
                "stage_after_later_failure_and_restart": recovered.inspect_lifecycle("episode").episode.stage,
                "outstanding_after_later_failure": view.projection.outstanding_loss,
                "relief_history": [event.kind for revision in view.history for event in revision.events],
                "causal_credit_assigned": any(event.causal_attempt_id for revision in view.history for event in revision.events),
            }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
