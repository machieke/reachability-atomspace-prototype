"""Demonstrate durable admission and exact expiry without external actions."""
from itertools import count
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from .model import Evidence, Literal, Rule, Statement
from .service import AdmissionService


def run() -> dict[str, object]:
    tested = Literal(Statement("Tested", ("artifact-v2",)))
    credential = Literal(Statement("CredentialValid", ("credential-1",)))
    ready = Literal(Statement("ReadyToDeploy", ("artifact-v2",)))
    keys = count()

    def key():
        return f"recovery-demo-{next(keys)}"

    def accept(service, transition):
        revision = service.snapshot("production").knowledge_revision
        pre = service.precertify(transition, revision, idempotency_key=key())
        proposal = service.infer(transition, pre)
        post = service.postcertify(proposal, pre, idempotency_key=key())
        return service.commit(proposal, pre, post, revision, idempotency_key=key()).belief

    with TemporaryDirectory() as directory:
        path = Path(directory) / "admission.db"
        with AdmissionService((Rule("ready", "1", (tested, credential), ready),), database=path) as service:
            service.open_context("production", idempotency_key=key())
            premises = []
            for evidence_id, content, expiry in (("test", tested, None), ("credential", credential, 3)):
                service.record_evidence(Evidence(evidence_id, "production", content, "observer", 0,
                                                 (f"root:{evidence_id}",), expiry), idempotency_key=key())
                transition = service.propose_evidence("production", evidence_id, idempotency_key=key())
                premises.append(accept(service, transition).belief_revision_id)
            transition = service.propose_transition("production", "ready", tuple(premises),
                                                    idempotency_key=key())
            accepted = accept(service, transition)
        with AdmissionService(database=path) as recovered:
            before = recovered.query_belief("production", ready)
            recovered.advance_clock("production", 3, idempotency_key=key())
            after = recovered.query_belief("production", ready)
            return {
                "scope": "durable admission and expiry; no external deployment",
                "after_restart": before.status.value,
                "same_accepted_revision": before.current[0].belief_revision_id == accepted.belief_revision_id,
                "at_credential_expiry": after.status.value,
                "artifact_test_after_expiry": recovered.query_belief("production", tested).status.value,
                "historical_ready_records": len(after.historical),
            }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
