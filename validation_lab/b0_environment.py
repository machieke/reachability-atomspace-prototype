"""Evaluator-owned deployment world; only selected probes reveal observations.

The controller receives a narrow read/execute port, never this object's world,
future hooks, physical-effect instrumentation, or reference projections.
"""
from copy import deepcopy
from dataclasses import asdict

from reachability.trace_protocol import event, fingerprint
from .deployment_oracle import reference_prefix
from .run_deployment import compare


class DeploymentWorld:
    def __init__(self, session, public, world, *, emit=None, restart_every_prefix=True):
        self.session, self.public, self.world = session, public, deepcopy(world)
        self.emit, self.restart_every_prefix = emit, restart_every_prefix
        self.events, self.records = [], []
        self.probe_counts, self.action_counts, self.evidence = {}, {}, {}
        self.effect_at = {}
        self.requests = []
        self.recovered_prefixes = 0

    def send(self, kind, **arguments):
        message = event(f"w{len(self.events):03}", kind, **arguments)
        record = self.session.apply(message)
        self.events.append(message)
        self.records.append(record)
        if self.emit is not None:
            self.emit(dict(record_type="runtime", event=message, actual=record))
        expected = reference_prefix(asdict(self.public.deployment), self.events)
        compare(expected["status"], record["outcome"]["status"], message["event_id"], "outcome.status")
        compare(expected["projection"], record["projection"], message["event_id"])
        compare(expected["executor_effects"], record["instrumentation"]["executor_effects"], message["event_id"], "executor_effects")
        if fingerprint(record["projection"]) != record["projection_digest"]:
            raise ValueError("runtime projection digest mismatch")
        if self.restart_every_prefix:
            self.session.restart()
            compare(expected["projection"], self.session.projection(), message["event_id"], "recovered_projection")
            compare(expected["executor_effects"], self.session.executor.total_effects, message["event_id"], "recovered_effects")
            self.recovered_prefixes += 1
        if kind == "fact":
            self.evidence[arguments["name"]] = message["event_id"]
        elif kind == "forecast":
            self.evidence["forecast"] = message["event_id"]
        return record

    def initialize(self):
        for entry in self.world.get("initial_events", []):
            self.send(entry["kind"], **entry["arguments"])

    def _hooks(self, candidate):
        occurrence = self.action_counts[candidate.kind]
        for hook in self.world.get("hooks", []):
            if (hook["kind"], hook["occurrence"]) != (candidate.kind, occurrence):
                continue
            for item in hook["events"]:
                args = deepcopy(item["arguments"])
                if item["kind"] == "revoke" and args["evidence_id"].startswith("latest:"):
                    args["evidence_id"] = self.evidence[args["evidence_id"].split(":", 1)[1]]
                self.send(item["kind"], **args)

    def _observe(self, candidate):
        args = dict(candidate.arguments)
        probe = next(p for p in self.public.probes if p.probe_id == args["probe_id"])
        self.probe_counts[probe.probe_id] = self.probe_counts.get(probe.probe_id, 0)+1
        response = self.world["probes"].get(probe.probe_id)
        now = self.session.projection()["logical_time"]
        if response is None or now < response.get("available_at", 0):
            return
        until = None if response.get("valid_for") is None else now+response["valid_for"]
        if probe.target in ("tested", "credential"):
            self.send("fact", name=probe.target, valid_until=until)
        elif probe.target == "forecast":
            self.send("forecast", strength=response["strength"], confidence=response["confidence"], valid_until=until)
        elif probe.target == "outcome":
            attempt = args["attempt_id"]
            if attempt not in self.effect_at or now < self.effect_at[attempt]+response.get("delay", 0):
                return
            product = self.public.deployment.product_id
            if now < response.get("wrong_until", 0):
                product += "0"
            else:
                self.send("fact", name="product", valid_until=None)
            for milestone in ("completion_observed", "exact_product_observed"):
                self.send("observation", attempt_id=attempt, milestone=milestone, product_id=product)
        elif probe.target == "monitor":
            if now in response.get("missing_at", []):
                return
            self.send("sample", healthy=now >= response.get("healthy_after", 0))

    def execute(self, candidate):
        before = len(self.records)
        if self.emit is not None:
            self.emit(dict(record_type="request", candidate=candidate.wire()))
        self.action_counts[candidate.kind] = self.action_counts.get(candidate.kind, 0)+1
        self._hooks(candidate)
        args = dict(candidate.arguments)
        if candidate.kind == "observe":
            self._observe(candidate)
        elif candidate.kind == "wait":
            self.send("tick", time=self.session.projection()["logical_time"]+1)
        else:
            if candidate.kind == "dispatch":
                faults = self.world.get("dispatch_faults", [])
                index = self.action_counts["dispatch"]-1
                args["fault"] = faults[index] if index < len(faults) else "none"
            self.send(candidate.kind, **args)
            # This physical instrumentation remains environment-owned. It can
            # cause later outcomes but is never included in the controller port.
            if candidate.kind in ("dispatch", "reconcile"):
                attempt = args["attempt_id"]
                if self.session.executor.total_effects > len(self.effect_at):
                    self.effect_at.setdefault(attempt, self.session.projection()["logical_time"])
        new = self.records[before:]
        statuses = [r["outcome"]["status"] for r in new]
        status = next((s for s in ("FAIL", "STALE", "UNKNOWN") if s in statuses), "PASS" if new else "UNKNOWN")
        receipt = dict(status=status, public_events=len(new), admission_journal_commands=sum(r["diagnostics"]["journal_commands"] for r in new),
                       certificates=sum(len(r["diagnostics"]["certificates"]["$tuple"]) for r in new))
        self.requests.append(dict(candidate=candidate.wire(), receipt=receipt))
        return receipt

    def port(self):
        world = self
        class PublicPort:
            def read(self):
                return world.session.projection()

            def execute(self, candidate):
                return world.execute(candidate)
        return PublicPort()
