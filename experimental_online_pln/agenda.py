"""Read-only public frontier and pressure-free FIFO. No service or evaluator access."""
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from itertools import product
from time import perf_counter_ns

from reachability.model import Status
from reachability.codec import decode, encode
from reachability.trace_protocol import canonical, fingerprint


def wire(value):
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {f.name: wire(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, (tuple, list)):
        return [wire(v) for v in value]
    if isinstance(value, dict):
        return {k: wire(v) for k, v in value.items()}
    return value


def digest(value):
    return fingerprint(wire(value))


@dataclass(frozen=True)
class Limits:
    rules: int = 16
    estimates: int = 32
    candidates: int = 64
    tuple_visits: int = 128
    selections: int = 32
    work: int = 64
    acquisitions: int = 16

    def __post_init__(self):
        caps = (16, 32, 64, 128, 32, 64, 16)
        if any(type(v) is not int or not 0 <= v <= cap
               for v, cap in zip(wire(self).values(), caps)):
            raise ValueError('coordinator bounds must be integers within the registered caps')


@dataclass(frozen=True)
class Probe:
    probe_id: str
    source: str
    report_type: str
    target: object
    preconditions: tuple[str, ...] = ()
    opportunity: int = 0
    cost: int = 1
    availability: str = 'unknown'

    def __post_init__(self):
        if (self.report_type not in ('numeric', 'product', 'health')
                or self.availability not in ('unknown', 'available', 'unavailable')
                or type(self.cost) is not int or not 1 <= self.cost <= 16
                or type(self.opportunity) is not int or not 0 <= self.opportunity <= 32
                or not self.probe_id or not self.source
                or any(p not in ('acknowledged', 'exact_product') for p in self.preconditions)):
            raise ValueError('unsupported public acquisition descriptor')


@dataclass(frozen=True)
class Report:
    evidence: object
    report: object
    revoked: bool = False


@dataclass(frozen=True)
class Snapshot:
    context: object
    policy: object
    rules: tuple
    models: tuple
    revoked_models: tuple
    reports: tuple[Report, ...]
    numerical: tuple
    hard: tuple
    operation: object
    intent: object
    dispatch: object
    decision: object
    lifecycle: object
    goal: object
    resource: object
    probes: tuple[Probe, ...]
    contracts: tuple
    received: tuple
    schema: str = 'online-pln-public/v1'

    @property
    def binding(self):
        return digest(self)

    def records(self):
        """Use the existing allowlisted record codec for independent replay of public inputs."""
        data = {f.name: getattr(self, f.name) for f in fields(self)}
        data['reports'] = tuple((r.evidence, r.report, r.revoked) for r in self.reports)
        data['probes'] = tuple(tuple(getattr(p, f.name) for f in fields(p)) for p in self.probes)
        # Already received diagnostic events have custom receipt-index wrappers.
        # They are inert JSON, not authority records used by candidate generation.
        data['received'] = wire(self.received)
        return encode(data)

    @classmethod
    def from_records(cls, value):
        data = decode(value)
        data['reports'] = tuple(Report(*r) for r in data['reports'])
        data['probes'] = tuple(Probe(*p) for p in data['probes'])
        data['received'] = tuple(data['received'])
        return cls(**data)


@dataclass(frozen=True)
class Candidate:
    kind: str
    target: str
    context_id: str
    premise_ids: tuple
    basis: str
    logical_id: str
    semantic_tie: str
    expected_binding: str
    cost: int = 1
    acquisition_cost: int = 0


@dataclass(frozen=True)
class Frontier:
    candidates: tuple[Candidate, ...]
    complete: bool
    reason: str
    tuple_visits: int
    elapsed_ns: int


def enumerate_work(snapshot, limits=Limits()):
    """Exact ordered tuples only; admission (including numeric domains) stays public API work."""
    start = perf_counter_ns()
    current = tuple(b for v in snapshot.numerical for b in v.current)
    if snapshot.schema != 'online-pln-public/v1':
        raise ValueError('unsupported snapshot schema')
    if (len(snapshot.rules) > limits.rules or len(current) > limits.estimates
            or len(snapshot.models) > 16 or len(snapshot.reports) > 128 or len(snapshot.probes) > 16):
        return Frontier((), False, 'INPUT_BOUND', 0, perf_counter_ns()-start)
    items, visits, complete, reason = [], 0, True, 'COMPLETE'
    expected = snapshot.binding
    # Permit freshness includes the whole snapshot; retry eligibility includes
    # actual relevant input records, not queue age or arbitrary tick increments.
    numeric_policy = (snapshot.policy, snapshot.context.policy_revision,
                      snapshot.context.assumptions, snapshot.context.constraints,
                      snapshot.context.usable)

    def add(kind, target, premises=(), inputs=(), tie=(), cost=1, acquisition=0):
        nonlocal complete, reason
        if len(items) == limits.candidates:
            complete, reason = False, 'CANDIDATE_BOUND'
            return False
        logical = digest((kind, target, premises))
        items.append(Candidate(kind, target, snapshot.context.context_id, premises,
            digest(inputs), logical, canonical(wire((kind, target, tie))), expected, cost, acquisition))
        return True

    adopted = {b.transition.evidence_id for b in current if b.transition.kind == 'observation'}
    now = snapshot.context.logical_time
    for received in sorted(snapshot.reports, key=lambda r: r.evidence.evidence_id):
        evidence = received.evidence
        if (evidence.evidence_id not in adopted and not received.revoked
                and evidence.observed_at <= now
                and (evidence.valid_until is None or now < evidence.valid_until)):
            if not add('adopt', evidence.evidence_id, inputs=(received, numeric_policy)):
                break

    for rule in sorted(snapshot.rules, key=lambda r: r.rule_id):
        if not complete:
            break
        alternatives = [sorted((b for b in current if b.proposal.support.conclusion == literal),
            key=lambda b: (b.proposal.support.evidence_ids, b.belief_revision_id))
            for literal in rule.deduction.premises]
        for supports in product(*alternatives):
            if visits == limits.tuple_visits:
                complete, reason = False, 'TUPLE_BOUND'
                break
            visits += 1
            premises = tuple(b.belief_revision_id for b in supports)
            if any(b.transition.kind == 'deduction' and b.transition.rule_id == rule.rule_id
                   and b.transition.rule_revision == rule.revision
                   and b.transition.premise_revision_ids == premises for b in current):
                continue
            if not add('deduction', rule.rule_id, premises, (rule, supports, numeric_policy),
                       tuple(b.proposal.support.evidence_ids for b in supports)):
                break

    by_id = {b.belief_revision_id: b for b in current}
    for model in sorted(snapshot.models, key=lambda m: m.model_id):
        if not complete:
            break
        if model.model_id in snapshot.revoked_models or not set(model.premise_revision_ids) <= by_id.keys():
            continue
        if any(b.transition.kind == 'revision' and b.transition.independence_id == model.model_id
               and b.transition.premise_revision_ids == model.premise_revision_ids for b in current):
            continue
        add('revision', model.model_id, model.premise_revision_ids,
            (model, tuple(by_id[p] for p in model.premise_revision_ids), numeric_policy),
            tuple(by_id[p].proposal.support.evidence_ids for p in model.premise_revision_ids))

    for probe in sorted(snapshot.probes, key=lambda p: (p.probe_id, p.opportunity)):
        if not complete:
            break
        if probe.availability == 'unavailable':
            continue
        if ('acknowledged' in probe.preconditions and
                (snapshot.dispatch is None or snapshot.dispatch.state != 'accepted')):
            continue
        if 'exact_product' in probe.preconditions and 'exact_product_observed' not in snapshot.operation.current_milestones:
            continue
        add('request', probe.probe_id, (probe.opportunity,), probe, (probe.opportunity,),
            probe.cost, probe.cost)

    if complete and snapshot.intent is None and snapshot.decision.status is Status.PASS:
        # A PASS numerical gate is merely a useful readiness observation.
        # certify_execution still enforces every hard/resource/owner requirement.
        add('reserve', snapshot.operation.operation.attempt_id,
            inputs=(snapshot.decision.basis_id, snapshot.operation, snapshot.resource, snapshot.hard,
                    snapshot.contracts))
    if complete and snapshot.intent is not None and snapshot.dispatch is None:
        add('dispatch', snapshot.operation.operation.attempt_id,
            inputs=(snapshot.intent, snapshot.decision.basis_id, snapshot.operation, snapshot.contracts))
    if complete and snapshot.dispatch is not None and snapshot.dispatch.state == 'uncertain':
        add('query', snapshot.operation.operation.attempt_id, inputs=(snapshot.dispatch, snapshot.intent))
    if (complete and snapshot.goal.projection.outstanding_loss == 0
            and snapshot.lifecycle.episode.stage != 'BUILT'):
        add('complete', snapshot.operation.operation.attempt_id,
            inputs=(snapshot.goal, snapshot.operation, snapshot.lifecycle, snapshot.dispatch, snapshot.contracts))
    return Frontier(tuple(items), complete, reason, visits, perf_counter_ns()-start)


class Agenda:
    """One attempt per relevant basis/opportunity; FIFO age persists across refreshes."""
    def __init__(self, limits=Limits()):
        self.limits = limits
        self.round = self.selections = self.work = self.acquisitions = 0
        self.first_ready, self.attempted = {}, set()
        self.stop = None

    def choose(self, snapshot):
        frontier = enumerate_work(snapshot, self.limits)
        if not frontier.complete:
            self.stop = frontier.reason
            return frontier, None
        if self.selections >= self.limits.selections:
            self.stop = 'SELECTION_BUDGET'
            return frontier, None
        eligible = []
        for c in frontier.candidates:
            self.first_ready.setdefault(c.logical_id, self.round)
            if (c.logical_id, c.basis) not in self.attempted:
                eligible.append(c)
        self.round += 1
        if not eligible:
            self.stop = 'QUIESCENT_UNRESOLVED' if snapshot.goal.projection.outstanding_loss else 'OBSERVED_GOAL'
            return frontier, None
        affordable = [c for c in eligible if self.work+c.cost <= self.limits.work
                      and self.acquisitions+c.acquisition_cost <= self.limits.acquisitions]
        if not affordable:
            self.stop = 'WORK_OR_ACQUISITION_BUDGET'
            return frontier, None
        selected = min(affordable, key=lambda c: (self.first_ready[c.logical_id], c.semantic_tie))
        self.attempted.add((selected.logical_id, selected.basis))
        self.selections += 1
        self.work += selected.cost
        self.acquisitions += selected.acquisition_cost
        return frontier, selected
