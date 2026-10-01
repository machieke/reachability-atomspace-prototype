"""Exercise a grounded lifecycle and passive operation observations with recovery."""
from itertools import count
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from .lifecycle_model import LifecycleEdge, LifecycleSchema, LifecycleState, milestone_literal
from .model import Evidence, Literal, Statement
from .requirements import Requirement
from .service import AdmissionDenied, AdmissionService


def run() -> dict[str, object]:
    tested = Literal(Statement("Tested", ("artifact-v2",)))
    credential = Literal(Statement("CredentialValid", ("credential-a",)))
    product = Literal(Statement("Available", ("artifact-v2",)))
    fact = lambda value: Requirement("FACT", value)
    requirements = Requirement("AND", children=(fact(tested), fact(credential)))
    schema = LifecycleSchema("artifact", "1", "artifact", "artifact-v2", "DRAFT",
        (LifecycleState("DRAFT"), LifecycleState("BUILT", fact(product))),
        (LifecycleEdge("build", "DRAFT", "BUILT", requirements, fact(product), "artifact-v2", ("executor",)),),
        ("BUILT",), "grounded-demo-schema")
    sequence = count()

    def key():
        return f"lifecycle-demo-{next(sequence)}"

    def accept(service, evidence_id, literal, source="sensor"):
        service.record_evidence(Evidence(evidence_id, "ctx", literal, source, 0, (evidence_id,)), idempotency_key=key())
        transition = service.propose_evidence("ctx", evidence_id, idempotency_key=key())
        revision = service.snapshot("ctx").knowledge_revision
        pre = service.precertify(transition, revision, idempotency_key=key())
        proposal = service.infer(transition, pre)
        post = service.postcertify(proposal, pre, idempotency_key=key())
        return service.commit(proposal, pre, post, revision, idempotency_key=key()).belief

    def observe(service, milestone, product_id="artifact-v2"):
        belief = accept(service, key(), milestone_literal("attempt", product_id, milestone), "executor")
        return service.record_operation_observation(key(), "attempt", milestone, belief.belief_revision_id,
                                                     idempotency_key=key())

    with TemporaryDirectory() as directory:
        path = Path(directory) / "lifecycle.db"
        with AdmissionService(database=path) as service:
            service.open_context("ctx", idempotency_key=key())
            service.register_lifecycle_schema(schema, idempotency_key=key())
            service.open_lifecycle_episode("episode", "ctx", "artifact", "1", idempotency_key=key())
            service.propose_operation("build-artifact", "attempt", "episode", "build", idempotency_key=key())
            service.select_operation("attempt", 0, idempotency_key=key())
            accept(service, "test", tested)
            accept(service, "credential", credential)
            observe(service, "accepted_by_executor")
            ack_status = service.inspect_operation("attempt").outcome_status.value
            try:
                observe(service, "completion_observed", "artifact-v1")
            except AdmissionDenied as error:
                wrong_product = error.status.value
            accept(service, "product", product)
            observe(service, "completion_observed")
            observe(service, "exact_product_observed")
            permit = service.certify_lifecycle_transition("episode", "build", 0,
                service.snapshot("ctx").knowledge_revision, attempt_id="attempt", idempotency_key=key())
            service.advance_lifecycle(permit, 0, idempotency_key=key())
        with AdmissionService(database=path) as recovered:
            stage = recovered.inspect_lifecycle("episode").episode.stage
            recovered.revoke_evidence("credential", idempotency_key=key())
            after_credential = recovered.inspect_lifecycle("episode").validity.value
            recovered.revoke_evidence("product", idempotency_key=key())
            current = recovered.inspect_lifecycle("episode")
            return {
                "scope": "passive operation observations; no external execution or goal relief",
                "ack_outcome": ack_status,
                "wrong_product": wrong_product,
                "stage_after_restart": stage,
                "artifact_validity_after_credential_revocation": after_credential,
                "stage_after_product_revocation": current.episode.stage,
                "validity_after_product_revocation": current.validity.value,
                "historical_transitions": len(current.episode.events),
            }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
