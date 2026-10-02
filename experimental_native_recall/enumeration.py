"""Native-recalled records feed the frozen tuple/candidate semantics.

All producer/support/report/probe/model membership comes from native queries.
Full-state bindings and public service execution are unchanged.
"""
from itertools import product
from time import perf_counter_ns
from reachability.model import Status
from reachability.trace_protocol import canonical
from experimental_online_pln.agenda import Candidate, Frontier, Limits, digest, wire
from experimental_goal_pln.relevance import probe_path


def enumerate_scoped(snapshot, dependencies, index, limits=Limits()):
    """Exact ordered tuples only; admission (including numeric domains) stays public API work."""
    start = perf_counter_ns()
    if dependencies.task.binding != snapshot.binding:
        raise ValueError('stale dependency scope')
    current = index.current()
    if snapshot.schema != 'online-pln-public/v1':
        raise ValueError('unsupported snapshot schema')
    if (len(snapshot.rules) > limits.rules or len(current) > limits.estimates
            or len(snapshot.models) > 16 or len(snapshot.reports) > 128 or len(snapshot.probes) > 16):
        return Frontier((), False, 'INPUT_BOUND', 0, perf_counter_ns()-start)
    items, visits, complete, reason = [], 0, dependencies.complete, dependencies.reason
    if not complete:
        return Frontier((), False, reason, 0, perf_counter_ns()-start)
    paths = dependencies.by_literal
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
    for received in sorted((r for literal in paths for r in index.reports.get(literal, ())), key=lambda r: r.evidence.evidence_id):
        evidence = received.evidence
        if (evidence.evidence_id not in adopted and not received.revoked
                and evidence.observed_at <= now
                and (evidence.valid_until is None or now < evidence.valid_until)):
            if not add('adopt', evidence.evidence_id, inputs=(received, numeric_policy)):
                break

    for rule in sorted((r for literal in paths for r in index.rules.get(literal, ())), key=lambda r: r.rule_id):
        if not complete:
            break
        alternatives = [sorted(index.estimates.get(literal, ()),
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
    for model in sorted(index.models(), key=lambda m: m.model_id):
        if not any(p in index.by_id and index.by_id[p].proposal.support.conclusion in paths
                   for p in model.premise_revision_ids):
            continue
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

    for probe in sorted((p for p in index.probes_for_scope(dependencies) if probe_path(p, dependencies.task, paths)), key=lambda p: (p.probe_id, p.opportunity)):
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

