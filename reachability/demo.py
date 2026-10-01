"""Run a finite admission demonstration without a backend or external executor."""
from itertools import count
import json

from .model import Evidence, Literal, Rule, Statement
from .service import AdmissionService


def run() -> dict[str, object]:
    powered = Literal(Statement("Powered", ("machine-M",)))
    sound = Literal(Statement("NotFaulty", ("machine-M",)))
    operable = Literal(Statement("Operable", ("machine-M",)))
    service = AdmissionService((Rule("operable", "1", (powered, sound), operable),))
    ids = count()

    def key():
        return f"demo-{next(ids)}"

    service.open_context("plant-A", idempotency_key=key())

    def prepare(transition):
        revision = service.snapshot("plant-A").knowledge_revision
        pre = service.precertify(transition, revision, idempotency_key=key())
        proposal = service.infer(transition, pre)
        post = service.postcertify(proposal, pre, idempotency_key=key())
        return proposal, pre, post, revision

    def adopt(evidence_id, statement):
        service.record_evidence(Evidence(evidence_id, "plant-A", statement, "sensor", 0,
                                         ("sensor-origin",)), idempotency_key=key())
        transition = service.propose_evidence("plant-A", evidence_id, idempotency_key=key())
        return service.commit(*prepare(transition), idempotency_key=key())

    a = adopt("power-reading", powered).belief
    missing = service.propose_transition("plant-A", "operable", (a.belief_revision_id,),
                                         idempotency_key=key())
    blocked = service.precertify(missing, service.snapshot("plant-A").knowledge_revision,
                                 idempotency_key=key())
    b = adopt("diagnostic-reading", sound).belief
    ready = service.propose_transition("plant-A", "operable",
                                       (a.belief_revision_id, b.belief_revision_id),
                                       idempotency_key=key())
    accepted = service.commit(*prepare(ready), idempotency_key=key())
    contradiction = adopt("opposing-reading", operable.negate())
    stale_inputs = prepare(ready)
    service.revoke_evidence("power-reading", idempotency_key=key())
    stale = service.commit(*stale_inputs, idempotency_key=key())
    view = service.query_belief("plant-A", operable)
    return {
        "scope": "volatile finite admission demo; no AtomSpace/PLN integration",
        "missing_premise": blocked.status.value,
        "complete_inference": accepted.status.value,
        "lineage_roots": list(accepted.belief.proposal.lineage_roots),
        "contradictory_result": contradiction.status.value,
        "commit_after_revocation": stale.status.value,
        "current_conclusion_after_revocation": view.status.value,
        "historical_conclusions_retained": len(view.historical),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
