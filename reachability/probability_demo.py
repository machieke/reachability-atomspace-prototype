"""Native PLN inference, certified numeric commit, AtomSpace projection and recovery."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from .atomspace_adapter import project_probability
from .model import Evidence
from .pln_adapter import DeductionRule, implication, TruthValue
from .probability_model import ProbabilityPolicy, ProbabilityReport, ProbabilityRule
from .service import AdmissionService


def run():
    with TemporaryDirectory(prefix="reachability-probability-demo-") as directory:
        database = Path(directory) / "authority.sqlite"
        with AdmissionService(database=database) as service:
            service.open_context("world", idempotency_key="open")
            service.configure_probability_policy("world", ProbabilityPolicy("p1", ("sensor",)), idempotency_key="policy")
            rule = ProbabilityRule("chain", "1", DeductionRule("P", "Q", "R"))
            service.configure_probability_rule("world", rule, idempotency_key="rule")

            def accept(transition, key):
                revision = service.snapshot("world").knowledge_revision
                pre = service.precertify_probability(transition, revision, idempotency_key=key+":pre")
                proposal = service.infer_probability(transition, pre)
                post = service.postcertify_probability(proposal, pre, idempotency_key=key+":post")
                return service.commit_probability(proposal, pre, post, revision, idempotency_key=key+":commit"), post

            beliefs = []
            for i, (literal, strength) in enumerate(zip(rule.deduction.premises, (.4, .5, .6, .7, .8))):
                key = f"sample-{i}"
                service.record_evidence(Evidence(key, "world", literal, "sensor", 0, ("origin-"+str(i),)), idempotency_key=key)
                service.record_probability_report(ProbabilityReport(key, TruthValue(strength, .8)), idempotency_key=key+":tv")
                transition = service.propose_probability("world", "observation", evidence_id=key, idempotency_key=key+":transition")
                result, _ = accept(transition, key)
                beliefs.append(result.belief)
            transition = service.propose_probability("world", "deduction", rule_id="chain",
                premise_revision_ids=tuple(b.belief_revision_id for b in beliefs), idempotency_key="deduction")
            result, certificate = accept(transition, "derived")
            literal = implication("P", "R")
            before = service.query_probability("world", literal)
            graph = project_probability(service, "world")
            report = {"commit": result.status.value,
                      "strength": result.belief.proposal.support.truth.strength,
                      "confidence": result.belief.proposal.support.truth.confidence,
                      "joint_witness_worlds": len(certificate.joint_witness),
                      "hard_query": service.query_belief("world", literal).status.value,
                      "native_atom_count": graph.size}
        with AdmissionService(database=database) as service:
            report["recovered_same_view"] = before == service.query_probability("world", literal)
            report["recovered_same_projection"] = graph == project_probability(service, "world")
            service.revoke_evidence("sample-0", idempotency_key="revoke")
            view = service.query_probability("world", literal)
            report["after_revocation"] = view.status.value
            report["historical_estimates"] = len(view.historical)
        return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
