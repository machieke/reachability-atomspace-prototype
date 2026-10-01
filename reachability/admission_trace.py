"""One public event at a time over grounded hard and numerical admission APIs."""
import argparse
from itertools import count
from pathlib import Path
import sys
from time import perf_counter_ns

from .admission_protocol import AdmissionEvent, AdmissionInitial, TRACE_SCHEMA
from .codec import encode
from .model import Clause, Evidence, Literal, Rule, Statement, Status
from .pln_adapter import PLNAdapter, PLNRejected, TruthValue
from .probability_formula import PinnedFormulaRuntime
from .probability_model import ProbabilityIndependence, ProbabilityPolicy, ProbabilityReport
from .service import AdmissionDenied, AdmissionService
from .trace_protocol import canonical, fingerprint, read_json


class AdmissionSession:
    def __init__(self, initial, directory, *, native=False):
        self.initial = AdmissionInitial.parse(initial.wire())
        self.path = Path(directory) / "admission.db"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            raise ValueError("start an admission trace in a fresh directory")
        self.adapter = PLNAdapter() if native else PLNAdapter(PinnedFormulaRuntime())
        self.rules = {r["rule_id"]: r for r in self.initial.wire()["rules"]}
        self.service = AdmissionService(tuple(self.rule(r) for r in self.rules.values()),
                                        max_variables=8, database=self.path)
        self.contexts, self.seen = set(), set()
        self.hard, self.numeric = {}, {}
        self.step, self._prefix, self._keys = 0, "initial", count()
        self.certificates = []

    def close(self):
        self.service.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def restart(self):
        # Public stream aliases remain in this driver; authority is reopened from
        # the journal and checked independently at every prefix by the evaluator.
        self.close()
        self.service = AdmissionService(database=self.path)

    def key(self):
        return f"admission-trace:{self._prefix}:{next(self._keys)}"

    def literal(self, value):
        return Literal(Statement("trace:atom", (self.initial.atoms[abs(value)-1],)), value > 0)

    def index(self, value):
        return (self.initial.atoms.index(value.statement.arguments[0])+1) * (1 if value.positive else -1)

    def rule(self, value):
        return Rule(value["rule_id"], value["revision"], tuple(map(self.literal, value["premises"])), self.literal(value["conclusion"]))

    def clauses(self, value):
        return tuple(Clause(tuple(map(self.literal, row))) for row in value)

    def references(self, refs, numeric=False):
        ledger = self.numeric if numeric else self.hard
        return tuple(ledger.get(ref, "missing:" + ref) for ref in refs)

    def _admit(self, event_id, transition, numeric=False):
        s = self.service
        rev = s.snapshot(transition.context_id).knowledge_revision
        suffix = "_probability" if numeric else ""
        pre = getattr(s, "precertify" + suffix)(transition, rev, idempotency_key=self.key())
        self.certificates.append(pre)
        proposal = getattr(s, "infer" + suffix)(transition, pre, **({"adapter": self.adapter} if numeric else {}))
        post = getattr(s, "postcertify" + suffix)(proposal, pre, idempotency_key=self.key())
        self.certificates.append(post)
        result = getattr(s, "commit" + suffix)(proposal, pre, post, rev, idempotency_key=self.key())
        if result.status is not Status.PASS:
            raise AdmissionDenied(result.status, result.detail)
        (self.numeric if numeric else self.hard)[event_id] = result.belief.belief_revision_id

    def _execute(self, e):
        a, s, kind = e.arguments, self.service, e.kind
        ctx = a.get("context_id")
        if kind == "context":
            s.open_context(ctx, assumptions=tuple(map(self.literal, a["assumptions"])), constraints=self.clauses(a["clauses"]),
                           idempotency_key=self.key())
            self.contexts.add(ctx)
            s.configure_probability_policy(ctx, ProbabilityPolicy("p1", ("sensor",)), idempotency_key=self.key())
        elif kind in ("evidence", "estimate"):
            s.record_evidence(Evidence(e.event_id, ctx, self.literal(a["literal"]), "sensor", s.snapshot(ctx).logical_time,
                                      tuple(a["roots"]), a["valid_until"]), idempotency_key=self.key())
            if kind == "estimate":
                s.record_probability_report(ProbabilityReport(e.event_id, TruthValue(a["strength"], a["confidence"])),
                                            idempotency_key=self.key())
                transition = s.propose_probability(ctx, "observation", evidence_id=e.event_id, idempotency_key=self.key())
            else:
                transition = s.propose_evidence(ctx, e.event_id, idempotency_key=self.key())
            self._admit(e.event_id, transition, kind == "estimate")
        elif kind == "adopt":
            self._admit(e.event_id, s.propose_evidence(ctx, a["evidence_id"], idempotency_key=self.key()))
        elif kind == "derive":
            self._admit(e.event_id, s.propose_transition(ctx, a["rule_id"], self.references(a["premises"]), idempotency_key=self.key()))
        elif kind == "rule":
            s.replace_rule(self.rule(a["rule"]), a["expected_revision"], idempotency_key=self.key())
            self.rules[a["rule"]["rule_id"]] = a["rule"]
        elif kind == "policy":
            s.replace_policy(ctx, a["revision"], self.clauses(a["clauses"]), s.snapshot(ctx).knowledge_revision,
                             idempotency_key=self.key())
        elif kind == "tick":
            s.advance_clock(ctx, a["time"], idempotency_key=self.key())
        elif kind == "revoke":
            s.revoke_evidence(a["evidence_id"], idempotency_key=self.key())
        elif kind == "independence":
            s.register_probability_independence(ProbabilityIndependence(a["model_id"], ctx,
                self.references(a["premises"], True), a["justification"]), idempotency_key=self.key())
        elif kind == "revise":
            transition = s.propose_probability(ctx, "revision", premise_revision_ids=self.references(a["premises"], True),
                                               independence_id=a["model_id"], idempotency_key=self.key())
            self._admit(e.event_id, transition, True)
        elif kind == "revoke_model":
            s.revoke_probability_independence(ctx, a["model_id"], idempotency_key=self.key())
        elif kind == "restart":
            self.restart()

    def projection(self):
        names = {}
        for ledger in (self.hard, self.numeric):
            for alias, belief_id in ledger.items():
                names.setdefault(belief_id, alias)
        result = dict(contexts={}, hard={}, numeric={}, aliases={
            kind: {alias: names[key] for alias, key in ledger.items()}
            for kind, ledger in (("hard", self.hard), ("numeric", self.numeric))})
        for ctx in sorted(self.contexts):
            snapshot = self.service.snapshot(ctx)
            data = dict(time=snapshot.logical_time, policy=snapshot.policy_revision,
                        assumptions=list(map(self.index, snapshot.assumptions)),
                        clauses=[list(map(self.index, c.literals)) for c in snapshot.constraints], hard={}, numeric={})
            result["contexts"][ctx] = data
            for number in range(1, len(self.initial.atoms)+1):
                for lit in (number, -number):
                    for kind, query in (("hard", self.service.query_belief), ("numeric", self.service.query_probability)):
                        view = query(ctx, self.literal(lit))
                        data[kind][str(lit)] = view.status.value
                        for belief in view.historical:
                            numeric = kind == "numeric"
                            support = belief.proposal.support if numeric else belief.proposal
                            parents = belief.transition.premise_revision_ids if numeric else support.premise_revision_ids
                            row = dict(context=ctx, literal=lit, current=belief in view.current,
                                       premises=sorted(names[p] for p in parents) if numeric else [names[p] for p in parents],
                                       evidence=list(support.evidence_ids), roots=list(support.lineage_roots))
                            if numeric:
                                row.update(strength=support.truth.strength, confidence=support.truth.confidence)
                            result[kind][names[belief.belief_revision_id]] = row
        return result

    def apply(self, message):
        e = AdmissionEvent.parse(message, len(self.initial.atoms))
        if e.event_id in self.seen or self.step >= 128:
            raise ValueError("duplicate event identity or trace exceeds 128 events")
        if e.kind == "context" and e.arguments["context_id"] not in self.contexts and len(self.contexts) >= 4:
            raise ValueError("trace exceeds four contexts")
        start = perf_counter_ns()
        self.seen.add(e.event_id)
        self.step += 1
        self._prefix, self.certificates = e.event_id, []
        status, detail = "PASS", "completed"
        try:
            self._execute(e)
        except (AdmissionDenied, PLNRejected) as error:
            status, detail = error.status.value, str(error)
        except KeyError:
            status, detail = "FAIL", "unknown public reference"
        # Valid wire messages may request an immutable identity redefinition or a
        # backwards clock. These are rejected commands, not malformed wire data.
        except ValueError as error:
            status, detail = "FAIL", str(error)
        projection = self.projection()
        return dict(schema=TRACE_SCHEMA, step=self.step, event_id=e.event_id, event_digest=fingerprint(e.wire()),
                    initial_digest=fingerprint(self.initial.wire()), outcome=dict(status=status, detail=detail),
                    projection=projection, projection_digest=fingerprint(projection), diagnostics=dict(
                        certificates=encode(tuple(self.certificates)), elapsed_ns=perf_counter_ns()-start,
                        knowledge_revisions={c: self.service.snapshot(c).knowledge_revision for c in sorted(self.contexts)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-dir", required=True, type=Path)
    parser.add_argument("--native", action="store_true", help="evaluate revision using pinned PeTTa/PLN")
    args = parser.parse_args()
    initial = AdmissionInitial.parse(read_json(sys.stdin.readline()))
    with AdmissionSession(initial, args.database_dir, native=args.native) as session:
        print(canonical(dict(schema=TRACE_SCHEMA, step=0, projection=session.projection())), flush=True)
        for line in sys.stdin:
            print(canonical(session.apply(read_json(line))), flush=True)


if __name__ == "__main__":
    main()
