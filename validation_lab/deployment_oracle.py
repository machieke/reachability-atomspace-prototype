"""Cold public-prefix model, using only Python's standard library.

This bounded model has direct evidence, one product/goal, three independent sample
ticks, renewable integer slots, and an idempotent queryable/fenced executor. It
neither imports nor calls the service, its checkers, accounting or projection code.
"""
from copy import deepcopy
import json


class OracleGap(ValueError):
    """Unsupported or malformed reference scope, never an epistemic UNKNOWN."""


def status(*values):
    return min(values, key={"FAIL": 0, "STALE": 1, "UNKNOWN": 2, "PASS": 3}.__getitem__)


def literal(predicate, arguments, positive=True):
    return dict(statement=dict(predicate=predicate, arguments=list(arguments)), positive=positive)


class _World:
    def __init__(self, initial):
        if initial.get("schema") != "deployment-initial/v1":
            raise OracleGap("unknown initial schema")
        self.c = deepcopy(initial)
        self.now, self.stage = 0, "DRAFT"
        self.evidence, self.hard, self.forecasts, self.attempts, self.promises = {}, {}, {}, {}, {}
        self.revoked = set()
        self.samples, self.relief = [], []
        self.monitor, self.opened, self.censored = 0, 0, False
        self.accounted = self.c["loss"]

    def live(self, evidence_id):
        expiry = self.evidence[evidence_id]
        return evidence_id not in self.revoked and (expiry is None or self.now < expiry)

    def fact(self, name):
        return literal({"tested": "Tested", "credential": "CredentialValid", "product": "Available"}[name],
                       (self.c["product_id"],))

    def holds(self, name):
        return any(value == self.fact(name) and self.live(key) for key, value in self.hard.items())

    def admit(self, key, value, expiry=None):
        self.evidence[key] = expiry
        active = [v for k, v in self.hard.items() if self.live(k)]
        atoms = {json.dumps(v["statement"], sort_keys=True) for v in [*active, value]}
        if len(atoms) > 20:
            raise OracleGap("reference trace exceeds the declared twenty-statement fragment")
        if any(v["statement"] == value["statement"] and v["positive"] != value["positive"] for v in active):
            return "FAIL"
        self.hard[key] = value
        return "PASS"

    def basis(self):
        return sorted(key for key in self.forecasts if self.live(key))

    def decision(self):
        values = [self.forecasts[key] for key in self.basis()]
        if not values:
            return "STALE" if self.forecasts else "UNKNOWN"
        if any(v["strength"] < self.c["min_strength"] for v in values):
            return "FAIL"
        return "UNKNOWN" if any(v["confidence"] < self.c["min_confidence"] for v in values) else "PASS"

    def readiness(self):
        return "FAIL" if self.stage != "DRAFT" else "PASS" if self.holds("tested") and self.holds("credential") else "UNKNOWN"

    def intent_state(self, attempt):
        a = self.attempts[attempt]
        if a["dispatch"] is not None:
            return "released" if a["dispatch"]["state"] == "released" else "reconciliation_required"
        if a["observations"]:
            return "reconciliation_required"
        return "expired" if self.now >= a["intent"]["ends_at"] else "pending"

    def resources(self, start, end, exclude=None, ignore_own_uncertainty=False):
        occupied, uncertain = [], []
        for name, a in self.attempts.items():
            if a["intent"] is None:
                continue
            state = self.intent_state(name)
            if state == "reconciliation_required" and (name != exclude or not ignore_own_uncertainty):
                uncertain.append(name)
            if name != exclude and state in ("pending", "reconciliation_required"):
                occupied.append(range(a["intent"]["starts_at"], a["intent"]["ends_at"]))
        # Independent finite occupancy enumeration, not the runtime interval sweep.
        portfolio = [*occupied, range(start, end)]
        times = set().union(*(set(interval) for interval in portfolio))
        capacity = all(sum(t in interval for interval in portfolio) <= self.c["capacity"] for t in times)
        return status("PASS" if capacity else "FAIL", "UNKNOWN" if uncertain else "PASS")

    def action(self, name, intent=False, submission=False):
        a = self.attempts[name]
        checks = [self.readiness(), self.decision(), "FAIL" if a["observations"] else "PASS"]
        if intent or submission:
            saved = a["intent"]
            lease = self.now < saved["ends_at"] if submission else self.intent_state(name) == "pending"
            checks += ["PASS" if lease else "STALE", "PASS" if saved["basis"] == self.basis() else "STALE",
                       self.resources(saved["starts_at"], saved["ends_at"], name, submission)]
        else:
            checks += ["FAIL" if a["intent"] is not None else "PASS",
                       self.resources(self.now, self.now + self.c["lease_duration"])]
        return status(*checks)

    def window(self):
        if self.censored:
            return "CENSORED"
        rows = [r for r in self.samples if r["monitor"] == self.monitor]
        if not rows:
            return "PENDING" if self.now < self.opened + 2 else "UNKNOWN"
        latest = max(r["time"] for r in rows)
        if latest != self.now:
            return "UNKNOWN"
        window = {latest - 2, latest - 1, latest}
        active = [r for r in rows if r["time"] in window and self.live(r["id"])]
        if any(not r["healthy"] for r in active):
            return "OBSERVED_FAILURE"
        if not self.holds("product"):
            return "UNKNOWN"
        if latest - 2 < self.opened:
            return "PENDING"
        observed = {r["time"] for r in active if r["healthy"]}
        return "OBSERVED_SUCCESS" if observed == window else "UNKNOWN"

    def coverage_live(self, promise):
        a = self.attempts[promise["attempt_id"]]
        if (self.censored or promise["monitor"] != self.monitor
                or self.now >= min(promise["valid_until"], a["intent"]["ends_at"])):
            return False
        if any(row["milestone"] in ("failure_observed", "cancellation_observed") for row in a["observations"]):
            return False
        if any(not r["healthy"] and r["monitor"] == self.monitor and r["id"] not in promise["baseline"] for r in self.samples):
            return False
        return a["dispatch"]["state"] == "accepted" if a["dispatch"] else self.action(promise["attempt_id"], intent=True) == "PASS"

    def goal(self):
        label = self.window()
        loss = 0 if label == "OBSERVED_SUCCESS" else self.c["loss"]
        eligible = [(key, p) for key, p in self.promises.items() if self.coverage_live(p)] if loss else []
        chosen = sorted(eligible, key=lambda row: (-row[1]["units"], row[0]))[:1]
        covered = min(loss, chosen[0][1]["units"]) if chosen else 0
        return dict(label=label, outstanding=loss, covered=covered, open=loss-covered,
                    selected_commitment=chosen[0][0] if chosen else None,
                    accounted_loss=self.accounted, relief=deepcopy(self.relief))

    def query_remote(self, a):
        remote = a["remote"]
        a["dispatch"].update(state=("released" if remote["fenced"] else "accepted") if remote else "uncertain",
                             effect_count=remote["effects"] if remote else 0)

    def execute(self, event):
        if event.get("schema") != "deployment-event/v1":
            raise OracleGap("unknown event schema")
        kind, key, args = event["kind"], event["event_id"], event["arguments"]
        name = args.get("attempt_id")
        if kind == "fact":
            return self.admit(key, self.fact(args["name"]), args["valid_until"])
        if kind == "forecast":
            self.evidence[key] = args["valid_until"]
            self.forecasts[key] = dict(strength=args["strength"], confidence=args["confidence"])
        elif kind == "revoke":
            if args["evidence_id"] not in self.evidence:
                return "FAIL"
            self.revoked.add(args["evidence_id"])
        elif kind == "tick":
            if args["time"] < self.now:
                raise OracleGap("time moved backwards")
            self.now = args["time"]
        elif kind == "attempt":
            self.attempts.setdefault(name, dict(intent=None, dispatch=None, observations=[], remote=None))
        elif kind == "reserve":
            if name not in self.attempts:
                return "FAIL"
            result = self.action(name)
            if result == "PASS":
                self.attempts[name]["intent"] = dict(starts_at=self.now, ends_at=self.now+self.c["lease_duration"], basis=self.basis())
            return result
        elif kind == "cover":
            if name not in self.attempts or self.attempts[name]["intent"] is None:
                return "FAIL"
            if not 0 < args["units"] <= self.c["loss"] or not self.now < args["valid_until"] <= self.attempts[name]["intent"]["ends_at"]:
                return "FAIL"
            promise = dict(args, monitor=self.monitor, baseline=[r["id"] for r in self.samples])
            if not self.coverage_live(promise):
                return "UNKNOWN"
            self.promises[key] = promise
        elif kind in ("prepare", "dispatch", "reconcile", "release"):
            if name not in self.attempts or self.attempts[name]["intent"] is None:
                return "FAIL"
            a = self.attempts[name]
            fresh = a["dispatch"] is None
            if fresh:
                if kind in ("reconcile", "release"):
                    return "FAIL"
                result = self.action(name, submission=True)
                if result != "PASS":
                    return result
                a["dispatch"] = dict(state="uncertain", prepared_at=self.now, effect_count=None)
            if kind in ("dispatch", "reconcile") and not fresh:
                self.query_remote(a)
            if kind == "release":
                a["remote"] = dict(fenced=True, effects=a["remote"]["effects"] if a["remote"] else 0)
                self.query_remote(a)
            if kind == "dispatch" and a["dispatch"]["state"] not in ("accepted", "released"):
                result = self.action(name, submission=True)
                if result != "PASS":
                    return result
                if args["fault"] != "before_effect":
                    a["remote"] = a["remote"] or dict(fenced=False, effects=1)
                    if args["fault"] != "lost_reply":
                        self.query_remote(a)
        elif kind == "observation":
            value = literal("rd:operation/"+args["milestone"], (name, args["product_id"]))
            result = self.admit(key, value)
            if result != "PASS":
                return result
            if name not in self.attempts or args["product_id"] != self.c["product_id"]:
                return "FAIL"
            self.attempts[name]["observations"].append(dict(id=key, time=self.now, milestone=args["milestone"]))
        elif kind == "sample":
            value = literal("rd:goal/sample", (self.c["goal_id"], "healthy", self.c["product_id"], str(self.now)), args["healthy"])
            result = self.admit(key, value)
            if result != "PASS":
                return result
            if self.censored:
                return "STALE"
            self.samples.append(dict(id=key, time=self.now, healthy=args["healthy"], monitor=self.monitor))
        elif kind == "censor":
            self.censored = True
        elif kind == "resume":
            if self.censored:
                self.monitor, self.opened, self.censored = self.monitor+1, self.now, False
        elif kind == "account":
            loss = self.goal()["outstanding"]
            if loss != self.accounted:
                self.relief.append(dict(kind="observed_relief" if loss < self.accounted else "reopened",
                    units=abs(loss-self.accounted), time=self.now, causal_attempt_id=None))
            self.accounted = loss
        elif kind == "complete":
            if name not in self.attempts or self.attempts[name]["dispatch"] is None:
                return "FAIL"
            a = self.attempts[name]
            if self.stage != "DRAFT":
                return "FAIL"
            after = a["dispatch"]["prepared_at"]
            observed = {r["milestone"] for r in a["observations"] if self.live(r["id"]) and r["time"] > after}
            if (a["dispatch"]["state"] not in ("accepted", "released") or not a["dispatch"]["effect_count"]
                    or not {"completion_observed", "exact_product_observed"} <= observed or not self.holds("product")
                    or self.window() != "OBSERVED_SUCCESS" or self.now-2 <= after):
                return "UNKNOWN"
            self.stage = "BUILT"
        elif kind != "restart":
            raise OracleGap("unsupported reference event: " + kind)
        return "PASS"

    def projection(self):
        attempts, used, uncertain = {}, 0, []
        for name, a in sorted(self.attempts.items()):
            intent = None
            if a["intent"] is not None:
                state = self.intent_state(name)
                intent = dict(a["intent"], state=state, readiness=self.action(name, intent=True))
                if state in ("pending", "reconciliation_required") and intent["starts_at"] <= self.now < intent["ends_at"]:
                    used += 1
                if state == "reconciliation_required":
                    uncertain.append(name)
            attempts[name] = dict(observed=sorted({r["milestone"] for r in a["observations"]}),
                current=sorted({r["milestone"] for r in a["observations"] if self.live(r["id"])}),
                readiness=self.readiness(), intent=intent, dispatch=deepcopy(a["dispatch"]), decision=self.decision())
        return dict(logical_time=self.now, hard={k: dict(literal=v, current=self.live(k)) for k, v in self.hard.items()},
            forecasts={k: dict(v, current=self.live(k)) for k, v in self.forecasts.items()}, attempts=attempts,
            stage=self.stage, goal=self.goal(), resource=dict(used=used, uncertain=uncertain))


def reference_prefix(initial, events):
    """Reconstruct from scratch; accepts no actual service outputs or saved oracle state."""
    world, seen, outcome = _World(initial), set(), "PASS"
    for event in events:
        if event["event_id"] in seen or len(seen) >= 128:
            raise OracleGap("duplicate event identity or trace scope exceeded")
        seen.add(event["event_id"])
        outcome = world.execute(event)
    effects = sum(a["remote"]["effects"] for a in world.attempts.values() if a["remote"])
    return dict(status=outcome, projection=world.projection(), executor_effects=effects)
