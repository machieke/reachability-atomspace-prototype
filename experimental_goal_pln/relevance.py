"""Typed contract roots and bounded directed dependencies. Pure public data only."""
from collections import defaultdict, deque
from dataclasses import dataclass
from time import perf_counter_ns
from experimental_online_pln.agenda import digest, wire
from reachability.trace_protocol import canonical


@dataclass(frozen=True)
class ClosureLimits:
    nodes: int = 128
    edges: int = 256
    depth: int = 16

    def __post_init__(self):
        if any(type(v) is not int or not 0 <= v <= cap for v, cap in
               zip((self.nodes, self.edges, self.depth), (128, 256, 16))):
            raise ValueError('closure bounds exceed declared finite scope')


@dataclass(frozen=True)
class Root:
    root_id: str
    kind: str
    context_id: str
    target: object
    version: tuple
    model_scope: str


@dataclass(frozen=True)
class Task:
    binding: str
    roots: tuple
    requirements: tuple
    contract_versions: tuple
    revisions: tuple
    schema: str = 'goal-pln-task/v1'


@dataclass(frozen=True)
class Path:
    root: Root
    steps: tuple = ()


@dataclass(frozen=True)
class Closure:
    task: Task
    paths: tuple  # (literal, canonical root/path)
    producers: tuple  # every producer and all five ordered requirements
    complete: bool
    reason: str
    nodes: int
    edges: int
    max_depth: int
    elapsed_ns: int

    @property
    def by_literal(self):
        return dict(self.paths)


def key(value):
    return canonical(wire(value))


def extract_task(snapshot):
    records = {c[1]: c[2] for c in snapshot.contracts if c[0] == 'registered-content/v1'}
    schema, execution, goal, completion = (records[n] for n in
        ('lifecycle_schema', 'execution_contract', 'goal_contract', 'completion_contract'))
    op, decision = snapshot.operation.operation, snapshot.decision.contract
    if ((schema.schema_id, schema.revision) != (op.schema_id, op.schema_revision)
        or (execution.schema_id, execution.schema_revision, execution.edge_id) !=
           (schema.schema_id, schema.revision, op.edge_id)
        or (goal.contract_id, goal.revision) !=
           (snapshot.goal.episode.contract_id, snapshot.goal.episode.contract_revision)
        or (decision.execution_contract_id, decision.execution_contract_revision) !=
           (execution.contract_id, execution.revision)):
        raise ValueError('task registration binding mismatch')
    if (snapshot.context.context_id != op.context_id or snapshot.decision.context_id != op.context_id
        or snapshot.goal.episode.context_id != op.context_id or snapshot.lifecycle.episode.context_id != op.context_id
        or (completion.schema_id, completion.schema_revision, completion.edge_id) !=
           (schema.schema_id, schema.revision, op.edge_id)
        or (completion.goal_contract_id, completion.goal_contract_revision) != (goal.contract_id, goal.revision)):
        raise ValueError('task scope mismatch')
    edge = next(e for e in schema.edges if e.edge_id == op.edge_id)
    state = next(s for s in schema.states if s.name == edge.target)
    ctx = snapshot.context.context_id
    roots, requirements = [], []
    versions = ((decision.contract_id, decision.revision), (execution.contract_id, execution.revision),
                (schema.schema_id, schema.revision), (goal.contract_id, goal.revision),
                (completion.contract_id, completion.revision),
                (records['dispatch_policy'].policy_id, records['dispatch_policy'].revision))
    def add(kind, target, version, label, model='hard/observation'):
        roots.append(Root(label, kind, ctx, target, version, model))
    for criterion in decision.criteria:
        for polarity, literal in (('criterion', criterion.conclusion), ('opposite', criterion.conclusion.negate())):
            add('numeric', literal, versions[0], polarity+':'+criterion.criterion_id, decision.truth_model)
    def requirement(label, expression, version):
        requirements.append((label, expression, version))
        queue = [(expression, ())]
        while queue:
            node, path = queue.pop(0)
            if node.literal is not None:
                add('hard', node.literal, version, label+':'+str(path))
            queue.extend((child, path+(i,)) for i, child in enumerate(node.children))
    for label, expression, version in (
        ('edge-prerequisites', edge.requirements, versions[2]),
        ('edge-outcome', edge.outcome, versions[2]), ('target-state', state.validity, versions[2]),
        ('execution', execution.requirements, versions[1]), ('completion', completion.requirements, versions[4])):
        requirement(label, expression, version)
    add('product', (edge.product_id, edge.observation_sources), versions[2], 'operation-product')
    for item in goal.slices:
        requirement('goal:'+item.slice_id, item.condition, versions[3])
        add('health', (item.product_id, item.durability.sources), versions[3], 'monitor:'+item.slice_id)
    add('operation', op.attempt_id, versions[1], 'operation:'+op.operation_id)
    revisions = (snapshot.context.knowledge_revision, snapshot.context.policy_revision,
                 snapshot.policy.revision, snapshot.lifecycle.lifecycle_revision,
                 snapshot.goal.projection.goal_revision, snapshot.resource.revision,
                 snapshot.context.logical_time, digest((snapshot.rules, snapshot.models, snapshot.revoked_models)))
    return Task(snapshot.binding, tuple(roots), tuple(requirements), versions, revisions)


class Index:
    """Cold maps built from a complete snapshot. Counts are entries, not RSS."""
    def __init__(self, snapshot):
        started = perf_counter_ns()
        self.rules, self.estimates, self.reports, self.probes = (defaultdict(list) for _ in range(4))
        self.by_id = {}
        for rule in snapshot.rules:
            self.rules[rule.deduction.conclusion].append(rule)
        for view in snapshot.numerical:
            for belief in view.current:
                self.estimates[belief.proposal.support.conclusion].append(belief)
                self.by_id[belief.belief_revision_id] = belief
        for report in snapshot.reports:
            self.reports[report.evidence.content].append(report)
        for probe in snapshot.probes:
            self.probes[(probe.report_type, probe.target)].append(probe)
        self.entries = sum(sum(map(len, m.values())) for m in
                           (self.rules, self.estimates, self.reports, self.probes)) + len(self.by_id)
        self.elapsed_ns = perf_counter_ns()-started


def closure(snapshot, task, limits=ClosureLimits(), index=None):
    started = perf_counter_ns()
    if task.binding != snapshot.binding:
        raise ValueError('stale task descriptor')
    index = index if index is not None else Index(snapshot)
    paths, producers, queue = {}, {}, deque()
    edges = max_depth = 0
    complete, reason = True, 'COMPLETE_TASK_DEPENDENCIES'
    def retain(literal, path, depth):
        nonlocal complete, reason, max_depth
        if literal in paths:
            return
        if depth > limits.depth or len(paths) >= limits.nodes:
            complete, reason = False, 'DEPTH_BOUND' if depth > limits.depth else 'NODE_BOUND'
            return
        paths[literal] = path
        queue.append((literal, path, depth))
        max_depth = max(max_depth, depth)
    for root in sorted((r for r in task.roots if r.kind == 'numeric'), key=key):
        retain(root.target, Path(root), 0)
    while queue and complete:
        literal, path, depth = queue.popleft()
        for rule in sorted(index.rules.get(literal, ()), key=lambda r: r.rule_id):
            if edges+len(rule.deduction.premises) > limits.edges:
                complete, reason = False, 'EDGE_BOUND'
                break
            producers[rule.rule_id] = (rule, path, rule.deduction.premises)
            for position, premise in enumerate(rule.deduction.premises):
                edges += 1
                retain(premise, Path(path.root, path.steps+((rule.rule_id, rule.revision, position, literal, premise),)), depth+1)
    return Closure(task, tuple(sorted(paths.items(), key=lambda p:key(p[0]))),
        tuple(producers[k] for k in sorted(producers)), complete, reason, len(paths), edges,
        max_depth, perf_counter_ns()-started)


def probe_path(probe, task, paths):
    if probe.report_type == 'numeric':
        return paths.get(probe.target)
    for root in task.roots:
        if root.kind == probe.report_type and probe.target == root.target[0] and probe.source in root.target[1]:
            return Path(root)
    return None


def witness(candidate, snapshot, dependencies):
    """No truth/strength/queue-age test occurs in this classifier."""
    paths = dependencies.by_literal
    path, version = None, ()
    if candidate.kind == 'deduction':
        rule = next(r for r in snapshot.rules if r.rule_id == candidate.target)
        path, version = paths.get(rule.deduction.conclusion), (rule.rule_id, rule.revision)
    elif candidate.kind == 'adopt':
        report = next(r for r in snapshot.reports if r.evidence.evidence_id == candidate.target)
        path, version = paths.get(report.evidence.content), (report.evidence.evidence_id,)
    elif candidate.kind == 'revision':
        model = next(m for m in snapshot.models if m.model_id == candidate.target)
        beliefs = {b.belief_revision_id:b for v in snapshot.numerical for b in v.current}
        matching = [paths[beliefs[p].proposal.support.conclusion] for p in model.premise_revision_ids
                    if p in beliefs and beliefs[p].proposal.support.conclusion in paths]
        path = min(matching, key=key) if matching else None
        version = (model.model_id, model.premise_revision_ids, digest(model))
    elif candidate.kind == 'request':
        probe = next(p for p in snapshot.probes if p.probe_id == candidate.target)
        path, version = probe_path(probe, dependencies.task, paths), (probe.probe_id, probe.opportunity, digest(probe))
    else:
        path = next((Path(r) for r in dependencies.task.roots
                     if r.kind == 'operation' and r.target == candidate.target), None)
        version = dependencies.task.contract_versions
    if path is None:
        return None
    return dict(schema='goal-pln-relevance-witness/v1', task_binding=dependencies.task.binding,
                path=path, operation_version=version, context_id=candidate.context_id,
                exact_premises=candidate.premise_ids, candidate_basis=candidate.basis)
