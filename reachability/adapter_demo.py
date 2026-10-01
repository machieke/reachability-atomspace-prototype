"""A real PLN proposal and AtomSpace Atoms/Values readback, with no belief commit."""
import json

from .atomspace_adapter import RecordProjection
from .pln_adapter import (DeductionRule, PLNAdapter, ProbabilisticSupport,
                          ProbabilitySnapshot, TruthValue)


def run():
    adapter = PLNAdapter()
    rule = DeductionRule("P", "Q", "R")
    values = ((.4, .9), (.5, .9), (.6, .9), (.7, .8), (.8, .7))
    supports = tuple(ProbabilisticSupport(f"premise-{i}", "demo-world", literal,
                                         TruthValue(*value), (f"evidence-{i}",), (f"origin-{i}",))
                     for i, (literal, value) in enumerate(zip(rule.premises, values)))
    snapshot = ProbabilitySnapshot("demo-world", 0, supports)
    proposal = adapter.apply_rule(rule, snapshot)
    projection = RecordProjection()
    atom = projection.add_probability(proposal)
    graph = projection.batch.run()
    tv = proposal.support.truth
    return {"scope": "real runtimes; proposed probabilistic support only",
            "formula_id": proposal.formula_id,
            "strength": tv.strength, "confidence": tv.confidence,
            "lineage_roots": proposal.support.lineage_roots,
            "native_atom_count": graph.size,
            "native_proposal_atom": graph.aliases[atom],
            "native_readback_verified": True,
            "accepted_beliefs_created": 0}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
