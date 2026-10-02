"""Bounded, scoped Boolean syntax projection. No authority or evaluator handles.

This is deliberately not a logical-equivalence canonicalizer. A FACT denotes a
proposition, never an evidence identity, operation, resource quantity or clock.
Only idempotent requirements in the same explicit scope can be deduplicated.
"""
from copy import deepcopy
from dataclasses import asdict, dataclass

from reachability.pressure import Node, Edge, Source
from reachability.pressure_work import build_graph, current, holds
from reachability.trace_protocol import canonical, fingerprint

VERSION = 'scoped-boolean-projection/v1'


@dataclass(frozen=True)
class ProjectionLimits:
    visits: int = 512
    depth: int = 8
    children: int = 512
    projected: int = 512
    goals: int = 4

    def __post_init__(self):
        for name, cap in (('visits', 4096), ('depth', 32), ('children', 4096),
                          ('projected', 4096), ('goals', 4)):
            value = getattr(self, name)
            if type(value) is not int or not 0 <= value <= cap:
                raise ValueError('projection limit outside supported capacity: '+name)


@dataclass(frozen=True)
class Scope:
    context: str
    goal: str
    source: str
    slice: str
    temporal: str
    semantics: str = 'idempotent-propositional-boolean/v1'

    def __post_init__(self):
        if any(type(v) is not str or not v for v in asdict(self).values()):
            raise ValueError('complete explicit requirement scope required')
        if self.semantics != 'idempotent-propositional-boolean/v1':
            raise ValueError('unsupported requirement multiplicity or semantics')


class ProjectionBlocked(ValueError):
    """Fail closed: no partial normalized graph/ranks, with original accounts."""
    def __init__(self, reason, work=None, accounts=()):
        super().__init__(reason)
        self.reason, self.work, self.accounts = reason, dict(work or {}), deepcopy(list(accounts))


def node_id(tree, scope):
    return ('fact:'+str(tree) if type(tree) is int else
            'projected-requirement:'+fingerprint((VERSION, asdict(scope), tree)))


def normalize(condition, scope, revisions, *, limits=ProjectionLimits(), work=None):
    """Return normal form plus every original occurrence's projection mapping.

    Flattened-away subexpressions map to the containing projected operator with
    relation 'flattened_into', not a claim that those conditions are equivalent.
    Removed unary and duplicate occurrences retain exact original paths/digests.
    Revision dependencies are conservative: all relevant public revision tokens.
    """
    if not isinstance(scope, Scope):
        raise ValueError('typed explicit scope required')
    work = {} if work is None else work
    work.setdefault('visits', 0); work.setdefault('projected', 0)
    work.setdefault('max_depth', 0)
    originals = []
    def visit(value, path):
        work['visits'] += 1
        work['max_depth'] = max(work['max_depth'], len(path))
        if work['visits'] > limits.visits:
            raise ProjectionBlocked('projection_visits', work)
        if len(path) > limits.depth:
            raise ProjectionBlocked('projection_depth', work)
        if type(value) is int and value != 0 and -8 <= value <= 8:
            normalized = value
        elif (type(value) is dict and len(value) == 1 and next(iter(value)) in ('AND', 'OR')
              and type(next(iter(value.values()))) is list and next(iter(value.values()))):
            operator, children = next(iter(value.items()))
            if len(children) > limits.children:
                raise ProjectionBlocked('projection_children', work)
            flattened = []
            for index, child in enumerate(children):
                projected = visit(child, path+(index,))
                if type(projected) is dict and operator in projected:
                    flattened.extend(projected[operator])
                else:
                    flattened.append(projected)
            unique = {canonical(child): child for child in flattened}
            children = [unique[key] for key in sorted(unique)]
            normalized = children[0] if len(children) == 1 else {operator: children}
        else:
            raise ProjectionBlocked('unsupported_requirement', work)
        originals.append((path, value, normalized))
        return normalized
    tree = visit(condition, ())
    surviving = {}
    pending = [tree]
    while pending:
        value = pending.pop()
        work['projected'] += 1
        if work['projected'] > limits.projected:
            raise ProjectionBlocked('projection_output', work)
        surviving[canonical(value)] = node_id(value, scope)
        if type(value) is dict:
            pending.extend(next(iter(value.values())))
    by_path = {path: normalized for path, _, normalized in originals}
    mapping = []
    for path, original, normalized in sorted(originals):
        target, ancestor = canonical(normalized), path
        while target not in surviving:
            ancestor = ancestor[:-1]
            target = canonical(by_path[ancestor])
        mapping.append(dict(path=list(path), original=deepcopy(original),
            original_digest=fingerprint(original), node=surviving[target],
            relation='equivalent' if ancestor == path else 'flattened_into',
            containing_path=list(ancestor)))
    return dict(schema=VERSION, scope=asdict(scope), revisions=deepcopy(revisions),
        condition=tree, mapping=mapping, limits=asdict(limits))


def source_records(public, snapshot):
    result = []
    for goal in snapshot['goals']:
        policy = public['priorities'][goal['goal_id']]
        result.append(Source(public['context_id'], goal['source_id'], goal['slice_id'], goal['goal_id'],
            goal['unit'], policy['unit'], policy['revision'], 'goal:'+goal['goal_id'], 'monitor:'+goal['goal_id'],
            goal['outstanding'], goal['coverage'], policy['weight'], policy['urgency'], policy['commitment'],
            tuple(goal['relief_events'])))
    return result


def project(public, snapshot, *, limits=ProjectionLimits()):
    """Normalize detached requirements only; bind all revision/support inputs.

    Accounts are built before traversal. Any bound or unsupported expression
    blocks the entire projection, even if earlier goals could be normalized.
    """
    sources = source_records(public, snapshot)
    accounts = [dict(identity=s.identity, **asdict(s)) for s in sources]
    work = dict(visits=0, projected=0, max_depth=0, goals=len(snapshot['goals']))
    try:
        if len(snapshot['goals']) > limits.goals:
            raise ProjectionBlocked('projection_goals', work)
        records = {}
        for goal in snapshot['goals']:
            scope = Scope(public['context_id'], goal['goal_id'], goal['source_id'], goal['slice_id'],
                canonical(dict(contract_revision=goal['contract_revision'], episode=goal['goal_id'], slice=goal['slice_id'])))
            dependencies = dict(snapshot_revisions=snapshot['revisions'], time=snapshot['time'],
                supports=snapshot['supports'], contract_revision=goal['contract_revision'],
                public_digest=snapshot['public_digest'])
            records[goal['goal_id']] = normalize(goal['condition'], scope, dependencies, limits=limits, work=work)
    except ProjectionBlocked as error:
        raise ProjectionBlocked(error.reason, work, accounts) from error
    return dict(schema=VERSION, goals=records, sources=accounts, work=work, limits=asdict(limits),
                binding=fingerprint((VERSION, snapshot, public['priorities'], asdict(limits))))


def projected_graph(public, snapshot, projection):
    """Reuse frozen operation graph; add scoped normalized requirement nodes.

    Real rule/premise edges, probes, source ledgers and monitoring are unchanged.
    Only the Boolean representation between a goal and its facts is projected.
    """
    if projection['binding'] != fingerprint((VERSION, snapshot, public['priorities'], projection['limits'])):
        raise ProjectionBlocked('stale_projection', accounts=projection['sources'])
    nodes, edges, _ = build_graph(public, dict(snapshot, goals=[]))
    nodes = {n.identity: n for n in nodes}
    facts = current(snapshot)
    def requirement(condition, scope):
        name = node_id(condition, scope)
        if type(condition) is not int and name not in nodes:
            operator, children = next(iter(condition.items()))
            nodes[name] = Node(name, operator, 'infer', holds(condition, facts))
            for child in children:
                edges.append(Edge(name, requirement(child, scope), 'lifecycle'))
        return name
    for goal in snapshot['goals']:
        root, monitor = 'goal:'+goal['goal_id'], 'monitor:'+goal['goal_id']
        nodes[root], nodes[monitor] = Node(root, 'AND', 'infer'), Node(monitor, 'LEAF', 'observe')
        if goal['condition_status'] == 'PASS':
            edges.append(Edge(root, monitor, 'observation'))
        else:
            record = projection['goals'][goal['goal_id']]
            edges.append(Edge(root, requirement(record['condition'], Scope(**record['scope'])), 'teleological'))
    return list(nodes.values()), edges, source_records(public, snapshot)
