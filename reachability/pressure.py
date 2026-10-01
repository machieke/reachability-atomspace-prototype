"""Bounded advisory pressure: p = d + gamma R p, never an authority API.

Inputs are detached, revision-bound public views. Sources are canonical goal
slices, not graph paths. Channel changes are explicit typed dependency edges.
Only infer/observe are implemented; there is no activation or transport state.
"""
from dataclasses import asdict, dataclass
from math import fsum, isfinite, nextafter

from .trace_protocol import fingerprint

CHANNELS = ('infer', 'observe')
DEPENDENCIES = ('epistemic', 'lifecycle', 'teleological', 'observation')
ROUTING_VERSION = 'binary64-substochastic/v2'


def finite(value, maximum=1e9):
    if type(value) not in (int, float) or not isfinite(value) or not 0 <= value <= maximum:
        raise ValueError('bounded nonnegative finite number required')
    return float(value)


@dataclass(frozen=True)
class PressureLimits:
    nodes: int = 128
    edges: int = 256
    sources: int = 8
    iterations: int = 128
    gamma: float = .85
    tolerance: float = 1e-8

    def __post_init__(self):
        for value, cap in ((self.nodes, 256), (self.edges, 1024), (self.sources, 32), (self.iterations, 4096)):
            if type(value) is not int or not 1 <= value <= cap:
                raise ValueError('pressure limit outside supported capacity')
        if not 0 < finite(self.gamma, 1) < 1 or not 0 < finite(self.tolerance, 1):
            raise ValueError('invalid contraction or tolerance')


@dataclass(frozen=True)
class Node:
    identity: str
    operator: str
    channel: str
    satisfied: bool = False
    blocked: str | None = None

    def __post_init__(self):
        if not self.identity or self.operator not in ('LEAF', 'AND', 'OR') or self.channel not in CHANNELS:
            raise ValueError('unsupported pressure node/operator/channel')
        if type(self.satisfied) is not bool:
            raise ValueError('satisfaction is an authoritative Boolean projection')


@dataclass(frozen=True)
class Edge:
    parent: str
    child: str
    kind: str
    weight: float = 1.

    def __post_init__(self):
        if self.kind not in DEPENDENCIES or finite(self.weight, 1e6) <= 0:
            raise ValueError('unsupported dependency or nonpositive exploration weight')


@dataclass(frozen=True)
class Source:
    context_id: str
    source_id: str
    slice_id: str
    goal_id: str
    unit: str
    policy_unit: str
    policy_revision: str
    root: str
    monitor: str
    outstanding: float
    coverage: float
    weight: float = 1.
    urgency: float = 1.
    commitment: float = 1.
    relief_events: tuple[str, ...] = ()

    def __post_init__(self):
        if not all((self.context_id, self.source_id, self.slice_id, self.goal_id, self.unit, self.policy_revision)):
            raise ValueError('source and policy identities are required')
        if self.policy_unit != 'priority/'+self.unit:
            raise ValueError('explicit conversion from each goal unit to priority is required')
        for value in (self.outstanding, self.coverage, self.weight, self.urgency, self.commitment):
            finite(value, 1e6)
        if self.coverage > self.outstanding or self.urgency > 10 or self.commitment > 10:
            raise ValueError('coverage or policy factor exceeds its bound')

    @property
    def identity(self):
        # Contract/knowledge revisions describe a new view of this obligation,
        # never a new source merely because its support or graph changed.
        return fingerprint((self.context_id, self.source_id, self.slice_id))

    @property
    def factor(self):
        return self.weight*self.urgency*self.commitment

    @property
    def open_demand(self):
        return self.factor*(self.outstanding-self.coverage)


def unique(items, key):
    result = {}
    for item in items:
        name = key(item)
        if name in result and result[name] != item:
            raise ValueError('conflicting duplicate pressure identity')
        result[name] = item
    return [result[name] for name in sorted(result)]


def components(names, routing):
    """Bounded Tarjan SCC diagnostics; cycles never establish satisfaction."""
    adjacency = {name: [] for name in names}
    for parent, child, _ in routing:
        adjacency[parent].append(child)
    index, low, stack, active, found = {}, {}, [], set(), []
    def visit(name):
        index[name] = low[name] = len(index)
        stack.append(name); active.add(name)
        for child in adjacency[name]:
            if child not in index:
                visit(child); low[name] = min(low[name], low[child])
            elif child in active:
                low[name] = min(low[name], index[child])
        if low[name] == index[name]:
            group = []
            while True:
                child = stack.pop(); active.remove(child); group.append(child)
                if child == name:
                    break
            if len(group) > 1 or name in adjacency[name]:
                found.append(sorted(group))
    for name in names:
        if name not in index:
            visit(name)
    return sorted(found)


def normalized_shares(children):
    """Positive binary64 shares whose *exact stored* sum is at most one.

    Rounded summation cannot prove the bound (five stored 0.2 values exceed
    one). Float denominators are powers of two, so integer ratios let us check
    and correct that excess exactly, independently of the iteration arithmetic.
    """
    total = fsum(edge.weight for edge in children)
    shares = [edge.weight/total for edge in children]
    if any(share <= 0 for share in shares):
        raise ValueError('unsupported dependency weight range: normalized positive share underflows')
    ratios = [share.as_integer_ratio() for share in shares]
    denominator = max((d for _, d in ratios), default=1)
    numerator = sum(n*(denominator//d) for n, d in ratios)
    if numerator > denominator:
        largest = max(range(len(shares)), key=shares.__getitem__)
        n, d = ratios[largest]
        capacity = n*(denominator//d)-(numerator-denominator)
        corrected = capacity/denominator
        n, d = corrected.as_integer_ratio()
        if n*denominator > capacity*d:
            corrected = nextafter(corrected, 0.)
        if corrected <= 0:
            raise ValueError('unsupported dependency weight range: column correction loses a positive share')
        shares[largest] = corrected
    return shares


def derive(binding, nodes, edges, sources, *, limits=PressureLimits()):
    """Return a new immutable-in-spirit JSON view; no service or state handle.

    AND routes to every missing child with a positive share. OR shares planning
    pressure across whole alternative branch nodes. Satisfaction is supplied by
    the authority and never inferred from numerical circulation. The sum across
    graph depth is diagnostic only; source demand stays in a separate ledger.
    """
    nodes = unique(nodes, lambda n: n.identity)
    edges = unique(edges, lambda e: (e.parent, e.child, e.kind))
    sources = unique(sources, lambda s: s.identity)
    by_name = {n.identity: n for n in nodes}
    ledger = {s.identity: dict(goal_id=s.goal_id, context_id=s.context_id, source_id=s.source_id,
        slice_id=s.slice_id, unit=s.unit, policy_revision=s.policy_revision, conversion=s.policy_unit,
        outstanding_loss=s.outstanding, predicted_coverage=s.coverage,
        open_loss=s.outstanding-s.coverage, outstanding_demand=s.factor*s.outstanding,
        open_demand=s.open_demand, monitoring_demand=s.factor*s.coverage,
        observed_relief_events=list(s.relief_events)) for s in sources}
    exhausted = [name for name, size, bound in (('nodes', len(nodes), limits.nodes),
        ('edges', len(edges), limits.edges), ('sources', len(sources), limits.sources)) if size > bound]
    result = dict(schema='typed-pressure/v1', routing_version=ROUTING_VERSION,
        epoch=fingerprint((ROUTING_VERSION, binding, list(map(asdict, nodes)),
        list(map(asdict, edges)), list(map(asdict, sources)), asdict(limits))), binding=binding,
        supported_channels=list(CHANNELS), unsupported_channels=['act', 'expand', 'retain'],
        sources=ledger, fields={}, scores={}, routing=[], cycles=[], conversions=[],
        work=dict(nodes=len(nodes), edges=len(edges), sources=len(sources), iterations=0, edge_visits=0),
        converged=False, residual_l1=0., error_bound_l1=0., exhausted=exhausted, stranded=[])
    if exhausted:
        result['stranded'] = [dict(source_id=s.identity, demand=s.factor*s.outstanding,
            reasons=['SEARCH_BUDGET_EXHAUSTED']) for s in sources if s.outstanding]
        return result
    outgoing = {n.identity: [] for n in nodes}
    for edge in edges:
        if edge.parent not in by_name or edge.child not in by_name:
            raise ValueError('dependency endpoint missing')
        if by_name[edge.parent].operator == 'LEAF':
            raise ValueError('leaf cannot have dependencies')
        if not by_name[edge.parent].satisfied and not by_name[edge.child].satisfied:
            outgoing[edge.parent].append(edge)
    routing = []
    for parent, children in outgoing.items():
        shares = normalized_shares(children)
        for edge, share in zip(children, shares):
            routing.append((parent, edge.child, share))
            if by_name[parent].channel != by_name[edge.child].channel:
                result['conversions'].append(dict(parent=parent, child=edge.child, kind=edge.kind,
                    before=by_name[parent].channel, after=by_name[edge.child].channel))
    result['routing'] = routing
    result['cycles'] = components(by_name, routing)
    scores = {name: 0. for name in by_name}
    for source in sources:
        if source.root not in by_name or source.monitor not in by_name:
            raise ValueError('source root/monitor is absent')
        d = dict.fromkeys(by_name, 0.)
        d[source.root] = source.open_demand
        d[source.monitor] += source.factor*source.coverage
        p = dict.fromkeys(by_name, 0.)
        def apply(values):
            incoming = {name: [d[name]] for name in by_name}
            for parent, child, weight in routing:
                incoming[child].append(limits.gamma*weight*values[parent])
            return {name: fsum(terms) for name, terms in incoming.items()}
        converged = False
        for iteration in range(1, limits.iterations+1):
            p = apply(p)
            following = apply(p)
            residual = fsum(abs(following[name]-p[name]) for name in by_name)
            error = residual/(1-limits.gamma)
            if error <= limits.tolerance*(1+fsum(d.values())):
                converged = True
                break
        if not converged:
            result['exhausted'].append('iterations:'+source.identity)
        result['fields'][source.identity] = dict(values=p, iterations=iteration,
            residual_l1=residual, error_bound_l1=error, converged=converged,
            source_norm=fsum(d.values()), pressure_norm=fsum(p.values()),
            norm_bound=fsum(d.values())/(1-limits.gamma))
        result['work']['iterations'] += iteration
        result['work']['edge_visits'] += 2*iteration*len(routing)
        result['residual_l1'] += residual
        result['error_bound_l1'] += error
        for name, value in p.items():
            scores[name] += value
        # Diagnose the bounded graph, not a not-yet-converged numerical wave.
        # Neither an iteration cap nor zero policy weight proves no route exists.
        pending = ([source.root] if source.outstanding > source.coverage else [])
        if source.coverage:
            pending.append(source.monitor)
        reachable = set()
        while pending:
            name = pending.pop()
            if name in reachable:
                continue
            reachable.add(name)
            pending.extend(edge.child for edge in outgoing[name])
        reasons = sorted({by_name[name].blocked for name in reachable if by_name[name].blocked})
        useful = any(by_name[name].operator == 'LEAF' and not by_name[name].blocked
                     and not by_name[name].satisfied for name in reachable)
        if source.outstanding and (reasons or not useful):
            result['stranded'].append(dict(source_id=source.identity, demand=source.factor*source.outstanding,
                reasons=reasons or ['NO_CAUSAL_ROUTE'], fully_stranded=not useful))
    result['scores'] = {name: dict(channel=by_name[name].channel, value=value) for name, value in scores.items()}
    result['converged'] = all(field['converged'] for field in result['fields'].values())
    return result
