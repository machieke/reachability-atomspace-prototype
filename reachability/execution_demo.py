"""Reserve one shared slot, recover the intent, and expire the local lease."""
from itertools import count
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from .execution_model import ExecutionContract, ResourceDefinition, ResourceDemand
from .lifecycle_model import LifecycleEdge, LifecycleSchema, LifecycleState
from .model import Evidence, Literal, Statement
from .requirements import Requirement
from .service import AdmissionDenied, AdmissionService


def run() -> dict[str, object]:
    credential = Literal(Statement("CredentialValid", ("credential-a",)))
    product = Literal(Statement("Available", ("artifact-v2",)))
    fact = lambda value: Requirement("FACT", value)
    schema = LifecycleSchema("artifact", "1", "artifact", "artifact-v2", "DRAFT",
        (LifecycleState("DRAFT"), LifecycleState("BUILT", fact(product))),
        (LifecycleEdge("build", "DRAFT", "BUILT", fact(credential), fact(product), "artifact-v2", ("executor",)),),
        ("BUILT",), "grounded-resource-demo")
    contract = ExecutionContract("build", "1", "artifact", "1", "build", "executor", ("worker",),
                                 (ResourceDemand("slot", 1, "slots"),), 10)
    sequence = count()

    def key():
        return f"execution-demo-{next(sequence)}"

    with TemporaryDirectory() as directory:
        path = Path(directory) / "execution.db"
        with AdmissionService(database=path) as service:
            service.open_context("ctx", idempotency_key=key())
            service.register_lifecycle_schema(schema, idempotency_key=key())
            service.open_lifecycle_episode("episode", "ctx", "artifact", "1", idempotency_key=key())
            service.record_evidence(Evidence("credential", "ctx", credential, "sensor", 0, ("credential",)),
                                      idempotency_key=key())
            transition = service.propose_evidence("ctx", "credential", idempotency_key=key())
            revision = service.snapshot("ctx").knowledge_revision
            pre = service.precertify(transition, revision, idempotency_key=key())
            proposal = service.infer(transition, pre)
            post = service.postcertify(proposal, pre, idempotency_key=key())
            service.commit(proposal, pre, post, revision, idempotency_key=key())
            service.register_resource(ResourceDefinition("slot", 1, "slots"), idempotency_key=key())
            service.register_execution_contract(contract, idempotency_key=key())
            for attempt in ("attempt-a", "attempt-b"):
                service.propose_operation("build-artifact", attempt, "episode", "build", idempotency_key=key())
                service.select_operation(attempt, 0, idempotency_key=key())
            permits = [service.certify_execution(attempt, "build", "1", "worker", 1,
                service.snapshot("ctx").knowledge_revision, service.resource_snapshot().revision,
                idempotency_key=key()) for attempt in ("attempt-a", "attempt-b")]
            intent = service.reserve_and_record_intent(permits[0], idempotency_key="reserve-a")
            try:
                service.reserve_and_record_intent(permits[1], idempotency_key="reserve-b")
            except AdmissionDenied as error:
                competing = error.status.value
        with AdmissionService(database=path) as recovered:
            same_intent = recovered.reserve_and_record_intent(permits[0], idempotency_key="reserve-a") == intent
            held = recovered.inspect_resource("slot").used_now
            recovered.revoke_evidence("credential", idempotency_key=key())
            readiness = recovered.inspect_execution_intent("attempt-a").readiness.value
            recovered.advance_resource_clock(10, idempotency_key=key())
            recovered.advance_clock("ctx", 10, idempotency_key=key())
            return {
                "scope": "local resource reservations and undispatched intents",
                "competing_reservation": competing,
                "same_intent_after_restart": same_intent,
                "held_units_after_restart": held,
                "readiness_after_credential_revocation": readiness,
                "state_at_expiry": recovered.inspect_execution_intent("attempt-a").state,
                "held_units_at_expiry": recovered.inspect_resource("slot").used_now,
                "observed_milestones": list(recovered.inspect_operation("attempt-a").observed_milestones),
            }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
