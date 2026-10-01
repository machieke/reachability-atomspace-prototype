"""Bounded B0 controller for the public deployment dependency graph.

Full recomputation, best-first ready work, existing operation/admission authority.
The port supplies only observable state and executes actions through normal gates.
No hidden world, future schedule, executor instrumentation or evaluator is read.
"""
from dataclasses import asdict, dataclass, field
from time import perf_counter_ns

from .trace_protocol import DeploymentInitial, fingerprint, identifier

PUBLIC_SCHEMA = "deployment-b0-public/v1"
TRACE_SCHEMA = "deployment-b0-step/v1"
TARGETS = ("tested", "credential", "forecast", "outcome", "monitor")


def bounded(value, maximum, minimum=0):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError("integer outside the declared B0 bound")


@dataclass(frozen=True)
class Probe:
    probe_id: str
    target: str
    cost: int = 1

    def __post_init__(self):
        identifier(self.probe_id)
        if self.target not in TARGETS:
            raise ValueError("unsupported observation capability")
        bounded(self.cost, 1000, 1)


@dataclass(frozen=True)
class B0Public:
    deployment: DeploymentInitial = field(default_factory=DeploymentInitial)
    probes: tuple[Probe, ...] = tuple(Probe("q"+str(i), target) for i, target in enumerate(TARGETS))
    max_attempts: int = 4

    def __post_init__(self):
        DeploymentInitial.parse(asdict(self.deployment))
        if type(self.probes) is not tuple or len(self.probes) > 16 or any(type(p) is not Probe for p in self.probes):
            raise ValueError("at most sixteen immutable observation capabilities")
        if len({p.probe_id for p in self.probes}) != len(self.probes):
            raise ValueError("duplicate observation capability")
        bounded(self.max_attempts, 4, 1)

    def wire(self):
        return dict(schema=PUBLIC_SCHEMA, deployment=asdict(self.deployment), probes=[asdict(p) for p in self.probes],
                    max_attempts=self.max_attempts)

    @classmethod
    def parse(cls, value):
        if type(value) is not dict or set(value) != {"schema", "deployment", "probes", "max_attempts"} or value["schema"] != PUBLIC_SCHEMA:
            raise ValueError("invalid B0 public profile")
        if type(value["probes"]) is not list:
            raise ValueError("observation capabilities require a JSON array")
        probes = []
        for p in value["probes"]:
            if type(p) is not dict or set(p) != {"probe_id", "target", "cost"}:
                raise ValueError("invalid capability fields")
            probes.append(Probe(**p))
        return cls(DeploymentInitial.parse(value["deployment"]), tuple(probes), value["max_attempts"])


@dataclass(frozen=True)
class Budget:
    actions: int = 32
    enumerations: int = 40
    candidate_visits: int = 2048
    observation_cost: int = 1000

    def __post_init__(self):
        for value, limit in ((self.actions, 64), (self.enumerations, 128), (self.candidate_visits, 4096),
                             (self.observation_cost, 64000)):
            bounded(value, limit)


@dataclass(frozen=True)
class Candidate:
    kind: str
    arguments: tuple[tuple[str, str], ...] = ()
    distance: int = 0
    observation_cost: int = 0

    @property
    def candidate_id(self):
        return fingerprint(dict(kind=self.kind, arguments=dict(self.arguments)))

    @property
    def rank(self):
        # Neutral public identity is the final deterministic tie-breaker.
        return self.distance, self.observation_cost, self.kind, self.arguments

    def wire(self):
        return dict(schema="deployment-candidate/v1", candidate_id=self.candidate_id, kind=self.kind,
                    arguments=dict(self.arguments), distance=self.distance, observation_cost=self.observation_cost)


@dataclass(frozen=True)
class Frontier:
    candidates: tuple[Candidate, ...]
    visits: int
    complete: bool
    terminal: bool


def enumerate_candidates(public, projection, *, visit_limit=4096):
    """Enumerate the finite dependency frontier without executing a command.

    Distance is remaining protocol stages, not optimal cost or predicted relief.
    A truncated enumeration is never used for selection. Each probe and attempt,
    and the common dependency expansion, consumes one visit, even if blocked.
    """
    bounded(visit_limit, 4096)
    visits, candidates = 0, []
    def visit():
        nonlocal visits
        if visits == visit_limit:
            return False
        visits += 1
        return True
    def add(kind, distance=0, cost=0, **args):
        candidates.append(Candidate(kind, tuple(sorted(args.items())), distance, cost))
    if not visit():
        return Frontier((), visits, False, False)
    c, p = public.deployment, projection
    current = [r["literal"] for r in p["hard"].values() if r["current"]]
    def holds(predicate, arguments):
        return any(r["positive"] and r["statement"] == dict(predicate=predicate, arguments=list(arguments)) for r in current)
    tested, credential, product = (holds(name, (c.product_id,)) for name in ("Tested", "CredentialValid", "Available"))
    forecasts = [f for f in p["forecasts"].values() if f["current"]]
    forecast = bool(forecasts) and all(c.min_strength <= f["strength"] <= 1 and f["confidence"] >= c.min_confidence for f in forecasts)
    basis = sorted(k for k, f in p["forecasts"].items() if f["current"])
    sampled = any(r["statement"] == dict(predicate="rd:goal/sample", arguments=[c.goal_id, "healthy", c.product_id, str(p["logical_time"])])
                  for r in current)
    satisfied = p["goal"]["outstanding"] == 0
    if p["goal"]["accounted_loss"] != p["goal"]["outstanding"]:
        add("account")
    active, outcome_attempts, needs_complete = False, [], False
    for name, a in sorted(p["attempts"].items()):
        if not visit():
            return Frontier((), visits, False, False)
        intent, dispatch = a["intent"], a["dispatch"]
        observed = {"completion_observed", "exact_product_observed"} <= set(a["current"])
        if satisfied and observed and p["stage"] == "DRAFT" and dispatch and dispatch["state"] == "accepted":
            add("complete", attempt_id=name)
            needs_complete = True
        if dispatch and dispatch["state"] != "released":
            active = True
            if satisfied:
                if not (observed and p["stage"] == "DRAFT"):
                    add("release", attempt_id=name)
            elif dispatch["state"] == "uncertain":
                if dispatch["effect_count"] is None:
                    add("reconcile", attempt_id=name)
                elif (dispatch["effect_count"] == 0 and tested and credential and forecast
                      and intent["ends_at"] > p["logical_time"] and intent["basis"] == basis):
                    add("dispatch", 3, attempt_id=name)
                else:
                    add("release", attempt_id=name)
            elif dispatch["state"] == "accepted" and not observed:
                outcome_attempts.append(name)
        elif not satisfied and intent is None and not a["observed"] and a["readiness"] == a["decision"] == "PASS":
            active = True
            if p["resource"]["used"] < c.capacity and not p["resource"]["uncertain"]:
                add("reserve", 4, attempt_id=name)
        elif not satisfied and intent and intent["state"] == "pending":
            active = True
            if intent["readiness"] == "PASS":
                add("dispatch", 3, attempt_id=name)
    needs = []
    if not satisfied:
        if outcome_attempts:
            needs.append(("outcome", 2))
        if product and not sampled and p["goal"]["label"] != "CENSORED":
            needs.append(("monitor", 1))
        if not active and not product and p["stage"] == "DRAFT":
            needs.extend((target, 6) for target, ready in (("tested", tested), ("credential", credential), ("forecast", forecast)) if not ready)
            if tested and credential and forecast and len(p["attempts"]) < public.max_attempts:
                # Existing attempts with no intent can become ready after new evidence.
                available = [a for a in p["attempts"].values() if a["intent"] is None and not a["observed"]]
                if not available:
                    index = next(i for i in range(public.max_attempts+1) if "b0-a"+str(i) not in p["attempts"])
                    add("attempt", 5, attempt_id="b0-a"+str(index))
        # A stale unsubmitted lease is allowed to expire; this profile never
        # invents cancellation or a remote release receipt.
        if p["logical_time"] < 1000:
            add("wait", 99)
    for probe in sorted(public.probes, key=lambda q: q.probe_id):
        if not visit():
            return Frontier((), visits, False, False)
        for target, distance in needs:
            if probe.target == target:
                args = dict(probe_id=probe.probe_id)
                if target == "outcome":
                    args["attempt_id"] = min(outcome_attempts)
                add("observe", distance, probe.cost, **args)
    terminal = satisfied and not active and not needs_complete and p["goal"]["accounted_loss"] == 0
    return Frontier(tuple(sorted(candidates, key=lambda q: q.rank)), visits, True, terminal)


class B0Controller:
    """Port interface: read() -> projection; execute(candidate) -> public receipt.

    Receipts contain status, public_events, admission_journal_commands and certificates.
    The controller has no executor or environment handle. Its checkpoint is only
    scheduling history; all authority remains in the existing service ledgers.
    """
    def __init__(self, public):
        self.public = B0Public.parse(public.wire())
        self.seen, self.steps = set(), 0

    def checkpoint(self):
        return dict(schema="deployment-b0-checkpoint/v1", public_digest=fingerprint(self.public.wire()), steps=self.steps,
                    seen=[list(item) for item in sorted(self.seen)])

    @classmethod
    def restore(cls, public, value):
        if (type(value) is not dict or set(value) != {"schema", "public_digest", "steps", "seen"}
                or value["schema"] != "deployment-b0-checkpoint/v1" or value["public_digest"] != fingerprint(public.wire())):
            raise ValueError("checkpoint profile mismatch")
        bounded(value["steps"], 128)
        if type(value["seen"]) is not list or len(value["seen"]) > 128:
            raise ValueError("invalid scheduling history")
        for item in value["seen"]:
            if type(item) is not list or len(item) != 2 or any(type(s) is not str or len(s) != 64 or
                    any(ch not in "0123456789abcdef" for ch in s) for s in item):
                raise ValueError("invalid scheduling fingerprint")
        if len(set(map(tuple, value["seen"]))) != len(value["seen"]) or len(value["seen"]) != value["steps"]:
            raise ValueError("scheduling history count differs from step count")
        result = cls(public)
        result.steps, result.seen = value["steps"], set(map(tuple, value["seen"]))
        return result

    def run_budget(self, port, budget, *, emit=None):
        if type(budget) is not Budget:
            raise ValueError("a typed work budget is required")
        work = dict(state_reads=0, loaded_hard=0, loaded_forecasts=0, loaded_attempts=0, candidate_visits=0,
                    candidates_returned=0, actions=0, observation_requests=0, observation_cost=0,
                    public_events=0, admission_journal_commands=0, certificates=0)
        records, reason, start = [], "action_budget", perf_counter_ns()
        while work["actions"] < budget.actions:
            if self.steps >= 128:
                reason = "controller_limit"
                break
            if work["state_reads"] >= budget.enumerations:
                reason = "enumeration_budget"
                break
            # Snapshot work is separately reported; candidate visits do not hide
            # the cost of reading/scanning the full bounded public projection.
            projection = port.read()
            if type(projection) is not dict or set(projection) != {
                    "logical_time", "hard", "forecasts", "attempts", "stage", "goal", "resource"}:
                raise ValueError("port must expose only the declared deployment projection")
            for key in ("hard", "forecasts", "attempts"):
                if type(projection[key]) is not dict or len(projection[key]) > 128:
                    raise ValueError("public projection exceeds the bounded trace profile")
            work["state_reads"] += 1
            for key in ("hard", "forecasts", "attempts"):
                work["loaded_"+key] += len(projection[key])
            view = fingerprint(projection)
            frontier = enumerate_candidates(self.public, projection, visit_limit=budget.candidate_visits-work["candidate_visits"])
            work["candidate_visits"] += frontier.visits
            work["candidates_returned"] += len(frontier.candidates)
            if not frontier.complete:
                reason = "candidate_budget"
                break
            if frontier.terminal:
                reason = "observed_success"
                break
            def request_key(candidate):
                # Repeated empty/wrong observations cannot create an endless
                # same-tick polling loop by adding fresh historical report IDs.
                epoch = fingerprint(dict(logical_time=projection["logical_time"])) if candidate.kind == "observe" else view
                return candidate.candidate_id, epoch
            available = [c for c in frontier.candidates if request_key(c) not in self.seen]
            remaining = budget.observation_cost-work["observation_cost"]
            affordable = [c for c in available if c.observation_cost <= remaining]
            if any(c.kind != "wait" for c in available) and not any(c.kind != "wait" for c in affordable):
                reason = "observation_budget"
                break
            if not affordable:
                reason = "blocked"
                break
            selected = min(affordable, key=lambda c: c.rank)
            # Charge an issued request even if the command fails or its probe
            # returns no observation. Never rerank using hidden outcomes.
            work["actions"] += 1
            self.steps += 1
            work["observation_cost"] += selected.observation_cost
            work["observation_requests"] += selected.kind == "observe"
            self.seen.add(request_key(selected))
            receipt = port.execute(selected)
            for key in ("public_events", "admission_journal_commands", "certificates"):
                work[key] += receipt[key]
            record = dict(schema=TRACE_SCHEMA, step=self.steps, view_digest=view,
                          candidates=[c.wire() for c in frontier.candidates], selected=selected.wire(),
                          receipt=receipt, work=dict(work))
            records.append(record)
            if emit is not None:
                emit(record)
        return dict(schema="deployment-b0-budget-result/v1", stop_reason=reason, records=records, work=work,
                    elapsed_ns=perf_counter_ns()-start, checkpoint=self.checkpoint())
