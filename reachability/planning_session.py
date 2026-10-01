"""Public planning port over the existing certified admission trace adapter."""
from copy import deepcopy
from itertools import count

from .admission_protocol import AdmissionEvent, event
from .admission_trace import AdmissionSession
from .grounded_planning import Plan, PlanningPublic, SNAPSHOT_SCHEMA
from .trace_protocol import fingerprint, identifier


class PlanningSession:
    def __init__(self, public, directory, *, emit=None, native=False):
        self.public = PlanningPublic.parse(public.wire())
        self.admission = AdmissionSession(public.admission, directory, native=native)
        self.emit = emit
        self.evidence = {}
        self.spent, self.steps = 0, 0
        self._ids = count()

    def close(self):
        self.admission.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def restart(self):
        # Like the trace adapters, this retains the observed stream metadata.
        # Work charges are a synchronous session ledger, not a crash transaction.
        self.admission.restart()

    def observe(self, message):
        parsed = AdmissionEvent.parse(message, len(self.public.admission.atoms))
        args = parsed.arguments
        report_recorded = False
        if parsed.kind in ("evidence", "estimate") and args["context_id"] in self.admission.contexts:
            now = self.admission.service.snapshot(args["context_id"]).logical_time
            report_recorded = args["valid_until"] is None or args["valid_until"] > now
        record = self.admission.apply(message)
        if report_recorded:
            # Reports are immutable and recorded before admission, including a
            # report whose subsequent hard assertion fails joint certification.
            self.evidence[parsed.event_id] = args["valid_until"]
        if self.emit is not None:
            self.emit(message, record)
        return record

    def _event(self, kind, **args):
        while True:
            name = "plan-event-"+str(next(self._ids))
            if name not in self.admission.seen:
                return self.observe(event(name, kind, **args))

    def read(self):
        projection = self.admission.projection()
        ctx = projection["contexts"][self.public.context_id]
        supports = []
        for alias, belief in sorted(projection["hard"].items()):
            if belief["context"] != self.public.context_id or not belief["current"]:
                continue
            expiries = [self.evidence[e] for e in belief["evidence"]]
            supports.append(dict(reference=alias, literal=belief["literal"],
                                 valid_until=min((end for end in expiries if end is not None), default=None)))
        return dict(schema=SNAPSHOT_SCHEMA, public_digest=fingerprint(self.public.wire()), context_id=self.public.context_id,
                    knowledge_revision=self.admission.service.snapshot(self.public.context_id).knowledge_revision,
                    policy_revision=ctx["policy"], time=ctx["time"], assumptions=ctx["assumptions"], clauses=ctx["clauses"],
                    rules=[deepcopy(self.admission.rules[k]) for k in sorted(self.admission.rules)], supports=supports,
                    remaining_work=self.public.work_budget-self.spent, remaining_steps=self.public.max_steps-self.steps)

    def execute(self, plan):
        if type(plan) is not Plan:
            raise ValueError("a typed frozen plan is required")
        snapshot = self.read()
        if plan.snapshot_digest != fingerprint(snapshot):
            return dict(status="STALE", work_charged=0, public_events=0)
        steps = plan.steps
        if type(steps) is not list or not steps:
            raise ValueError("cannot execute an empty plan")
        first = steps[0]
        fields = {"kind", "rule_id", "rule_revision", "premises", "finishes_at", "work"}
        if type(first) is not dict or set(first) != fields or type(first["finishes_at"]) is not int:
            raise ValueError("malformed first plan step")
        ctx, end, kind = self.public.context_id, first["finishes_at"], first["kind"]
        if self.steps >= self.public.max_steps or end > self.public.deadline or end < snapshot["time"]:
            return dict(status="FAIL", work_charged=0, public_events=0)
        if kind == "wait":
            if end == snapshot["time"] or first["premises"] != [] or first["rule_id"] is not None or first["rule_revision"] is not None or type(first["work"]) is not int or first["work"] != 0:
                raise ValueError("invalid wait step")
            charge = 0
        elif kind == "derive":
            identifier(first["rule_id"])
            identifier(first["rule_revision"])
            costs = {c.rule_id: c for c in self.public.costs}
            if first["rule_id"] not in costs:
                raise ValueError("unknown cost contract")
            cost = costs[first["rule_id"]]
            if first["rule_revision"] != self.admission.rules[first["rule_id"]]["revision"]:
                return dict(status="STALE", work_charged=0, public_events=0)
            charge = cost.work
            if type(first["work"]) is not int or first["work"] != charge or end != snapshot["time"]+cost.duration:
                raise ValueError("plan step does not match its declared cost/time contract")
            if type(first["premises"]) is not list or any(type(p) is not dict or set(p) != {"kind", "reference"} or p["kind"] != "belief" for p in first["premises"]):
                raise ValueError("the executed first step must bind exact current belief aliases")
            if len(first["premises"]) > 8:
                raise ValueError("too many grounded premises")
            for parent in first["premises"]:
                identifier(parent["reference"])
        else:
            raise ValueError("unsupported planning operation")
        if self.spent+charge > self.public.work_budget:
            return dict(status="FAIL", work_charged=0, public_events=0)
        self.spent += charge
        self.steps += 1
        records = []
        if end != snapshot["time"]:
            records.append(self._event("tick", context_id=ctx, time=end))
        if kind == "derive":
            records.append(self._event("derive", context_id=ctx, rule_id=first["rule_id"],
                                       premises=[p["reference"] for p in first["premises"]]))
        status = next((s for s in ("FAIL", "STALE", "UNKNOWN") if any(r["outcome"]["status"] == s for r in records)), "PASS")
        return dict(status=status, work_charged=charge, public_events=len(records))
