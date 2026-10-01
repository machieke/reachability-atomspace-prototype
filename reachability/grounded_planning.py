"""Finite B0 proof planning with complete cost/time alternatives and exact gates.

Search is advisory uniform-cost exploration of a frozen public snapshot. It
never admits a belief. Costs are declared proof-work credits, not physical
resource reservations or measured computational work.
"""
from dataclasses import asdict, dataclass
from heapq import heappop, heappush
from itertools import count, product

from .admission_protocol import AdmissionInitial, literal, sequence
from .logic import check_consistency
from .model import Clause, Literal, Statement, Status
from .trace_protocol import canonical, fingerprint, identifier, read_json

PUBLIC_SCHEMA = "grounded-planning-public/v1"
SNAPSHOT_SCHEMA = "grounded-planning-snapshot/v1"
INFINITY = 1001


def bounded(value, maximum, minimum=0):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError("integer outside the finite planning profile")


@dataclass(frozen=True)
class RuleCost:
    rule_id: str
    work: int
    duration: int

    def __post_init__(self):
        identifier(self.rule_id)
        bounded(self.work, 100, 1)
        bounded(self.duration, 8)


@dataclass(frozen=True)
class PlanningPublic:
    admission: AdmissionInitial
    context_id: str
    goals: tuple[int, ...]
    costs: tuple[RuleCost, ...]
    work_budget: int = 100
    deadline: int = 8
    max_steps: int = 6

    def __post_init__(self):
        if type(self.admission) is not AdmissionInitial:
            raise ValueError("typed admission profile required")
        object.__setattr__(self, "admission", AdmissionInitial.parse(self.admission.wire()))
        identifier(self.context_id)
        if type(self.goals) is not tuple or not 1 <= len(self.goals) <= 8 or len(set(self.goals)) != len(self.goals):
            raise ValueError("one to eight distinct goal literals are required")
        for goal in self.goals:
            literal(goal, len(self.admission.atoms))
        if type(self.costs) is not tuple or any(type(c) is not RuleCost for c in self.costs):
            raise ValueError("immutable typed rule costs required")
        rules = self.admission.wire()["rules"]
        if len(self.costs) != len(rules) or {c.rule_id for c in self.costs} != {r["rule_id"] for r in rules}:
            raise ValueError("exactly one cost contract per declared rule")
        bounded(self.work_budget, 1000)
        bounded(self.deadline, 16)
        bounded(self.max_steps, 8)

    def wire(self):
        return dict(schema=PUBLIC_SCHEMA, admission=self.admission.wire(), context_id=self.context_id,
                    goals=list(self.goals), costs=[asdict(c) for c in self.costs], work_budget=self.work_budget,
                    deadline=self.deadline, max_steps=self.max_steps)

    @classmethod
    def parse(cls, value):
        if type(value) is not dict or set(value) != {"schema", "admission", "context_id", "goals", "costs", "work_budget", "deadline", "max_steps"}:
            raise ValueError("invalid public planning fields")
        if value["schema"] != PUBLIC_SCHEMA:
            raise ValueError("unsupported public planning schema")
        sequence(value["goals"], 8)
        sequence(value["costs"], 8)
        costs = []
        for item in value["costs"]:
            if type(item) is not dict or set(item) != {"rule_id", "work", "duration"}:
                raise ValueError("invalid rule cost fields")
            costs.append(RuleCost(**item))
        return cls(AdmissionInitial.parse(value["admission"]), value["context_id"], tuple(value["goals"]), tuple(costs),
                   value["work_budget"], value["deadline"], value["max_steps"])


@dataclass(frozen=True)
class SearchBudget:
    states: int = 10000
    transitions: int = 50000

    def __post_init__(self):
        bounded(self.states, 100000)
        bounded(self.transitions, 500000)


@dataclass(frozen=True)
class Plan:
    snapshot_digest: str
    steps_json: str
    work: int
    finishes_at: int

    @property
    def steps(self):
        return read_json(self.steps_json)

    def wire(self):
        return dict(schema="grounded-plan/v1", snapshot_digest=self.snapshot_digest,
                    steps=self.steps, work=self.work, finishes_at=self.finishes_at)


def validate_snapshot(public, snapshot):
    fields = {"schema", "public_digest", "context_id", "knowledge_revision", "policy_revision", "time", "assumptions",
              "clauses", "rules", "supports", "remaining_work", "remaining_steps"}
    if type(snapshot) is not dict or set(snapshot) != fields or snapshot["schema"] != SNAPSHOT_SCHEMA:
        raise ValueError("invalid planning snapshot fields")
    if snapshot["public_digest"] != fingerprint(public.wire()) or snapshot["context_id"] != public.context_id:
        raise ValueError("planning snapshot belongs to another public profile")
    from .admission_protocol import clauses, literals, rule
    identifier(snapshot["policy_revision"])
    bounded(snapshot["knowledge_revision"], 1000000)
    bounded(snapshot["time"], 1000)
    bounded(snapshot["remaining_work"], public.work_budget)
    bounded(snapshot["remaining_steps"], public.max_steps)
    literals(snapshot["assumptions"], len(public.admission.atoms))
    clauses(snapshot["clauses"], len(public.admission.atoms))
    sequence(snapshot["rules"], 8)
    for r in snapshot["rules"]:
        rule(r, len(public.admission.atoms))
    if len(snapshot["rules"]) != len(public.costs) or {r["rule_id"] for r in snapshot["rules"]} != {c.rule_id for c in public.costs}:
        raise ValueError("planning rule registry differs from declared identities")
    sequence(snapshot["supports"], 128)
    names = set()
    for support in snapshot["supports"]:
        if type(support) is not dict or set(support) != {"reference", "literal", "valid_until"}:
            raise ValueError("invalid exact support fields")
        identifier(support["reference"])
        if support["reference"] in names:
            raise ValueError("duplicate exact support reference")
        names.add(support["reference"])
        literal(support["literal"], len(public.admission.atoms))
        if support["valid_until"] is not None:
            bounded(support["valid_until"], 1000)
            if support["valid_until"] <= snapshot["time"]:
                raise ValueError("planning snapshot contains an expired current support")


def search(public, snapshot, budget=SearchBudget()):
    """Find minimum (declared work, finish time, steps) within the frozen profile.

    State equality uses all current literal/lifetime alternatives: shorter-lived
    parents can produce conclusions that expire before a later conflicting goal.
    Exact chosen parent references remain in the plan. Assumptions constrain worlds but are
    never materialized as premises. Budget exhaustion is not unreachability.
    """
    validate_snapshot(public, snapshot)
    if type(budget) is not SearchBudget:
        raise ValueError("typed search budget required")
    work = dict(states=0, transitions=0, joint_checks=0, duplicate_states=0, loaded_supports=len(snapshot["supports"]))
    def result(status, plan=None):
        return dict(schema="grounded-search-result/v1", status=status, plan=plan, work=dict(work))
    def typed(lit):
        return Literal(Statement("planning:atom", (str(abs(lit)),)), lit > 0)
    constraints = tuple(Clause(tuple(map(typed, c))) for c in snapshot["clauses"])
    assumptions = tuple(map(typed, snapshot["assumptions"]))
    def consistent(facts):
        work["joint_checks"] += 1
        return check_consistency(constraints, assumptions+tuple(typed(x) for x in facts), max_variables=8).status is Status.PASS
    now = snapshot["time"]
    if now > public.deadline:
        return result("UNREACHABLE")
    # Facts map (literal, exclusive expiry) -> exact/symbolic reference.
    facts = {}
    for s in sorted(snapshot["supports"], key=lambda x: x["reference"]):
        expiry = INFINITY if s["valid_until"] is None else s["valid_until"]
        facts.setdefault((s["literal"], expiry), dict(kind="belief", reference=s["reference"]))
    if not consistent({lit for lit, _ in facts}):
        raise ValueError("current planning environment is inconsistent")
    costs = {c.rule_id: c for c in public.costs}
    serial = count()
    queue = [(0, now, 0, next(serial), facts, [])]
    best = {}
    while queue:
        if work["states"] >= budget.states:
            return result("BUDGET_EXHAUSTED")
        spent, time, depth, _, facts, path = heappop(queue)
        work["states"] += 1
        signature = time, depth, tuple(sorted(facts))
        if best.get(signature, spent+1) <= spent:
            work["duplicate_states"] += 1
            continue
        best[signature] = spent
        if set(public.goals) <= {lit for lit, _ in facts}:
            return result("SOLVED", Plan(fingerprint(snapshot), canonical(path), spent, time))
        if depth == snapshot["remaining_steps"]:
            continue
        options = [("derive", r) for r in sorted(snapshot["rules"], key=lambda r: r["rule_id"])]
        options += [("wait", target) for target in range(time+1, public.deadline+1)]
        for kind, action in options:
            if work["transitions"] >= budget.transitions:
                return result("BUDGET_EXHAUSTED")
            work["transitions"] += 1
            if kind == "wait":
                end, charge = action, 0
            else:
                cost = costs[action["rule_id"]]
                end, charge = time+cost.duration, cost.work
            if end > public.deadline or spent+charge > snapshot["remaining_work"]:
                continue
            after = {key: ref for key, ref in facts.items() if key[1] > end}
            if kind == "derive":
                choices = [sorted(key for key in after if key[0] == p) for p in action["premises"]]
                for inputs in product(*choices):
                    if work["transitions"] >= budget.transitions:
                        return result("BUDGET_EXHAUSTED")
                    work["transitions"] += 1
                    key = action["conclusion"], min(p[1] for p in inputs)
                    if key in after:
                        continue  # Identical lifetime adds no frozen-state capability.
                    updated = dict(after)
                    updated[key] = dict(kind="step", index=depth)
                    if not consistent({lit for lit, _ in updated}):
                        continue
                    step = dict(kind=kind, rule_id=action["rule_id"], rule_revision=action["revision"],
                                premises=[after[p] for p in inputs], finishes_at=end, work=charge)
                    heappush(queue, (spent+charge, end, depth+1, next(serial), updated, path+[step]))
            else:
                step = dict(kind=kind, rule_id=None, rule_revision=None, premises=[], finishes_at=end, work=0)
                heappush(queue, (spent+charge, end, depth+1, next(serial), after, path+[step]))
    return result("UNREACHABLE")


class GroundedController:
    """Recompute complete plans, execute only the first step through the port."""
    def __init__(self, public):
        self.public = PlanningPublic.parse(public.wire())

    def run(self, port, *, requests=16, search_budget=SearchBudget(), emit=None):
        bounded(requests, 32)
        records = []
        for index in range(requests):
            snapshot = port.read()
            found = search(self.public, snapshot, search_budget)
            record = dict(schema="grounded-controller-step/v1", step=index, snapshot_digest=fingerprint(snapshot),
                          status=found["status"], search_work=found["work"], plan=None if found["plan"] is None else found["plan"].wire())
            if emit is not None:
                emit(record)  # Log the proposed complete plan before execution.
            records.append(record)
            if found["status"] != "SOLVED":
                return dict(stop_reason=found["status"], records=records)
            if not found["plan"].steps:
                return dict(stop_reason="OBSERVED_GOALS", records=records)
            receipt = port.execute(found["plan"])
            record["receipt"] = receipt
            if emit is not None:
                emit(dict(schema="grounded-controller-receipt/v1", step=index, receipt=receipt))
            if receipt["status"] not in ("PASS", "STALE"):
                return dict(stop_reason="REJECTED", records=records)
        return dict(stop_reason="REQUEST_BUDGET", records=records)
