"""Experimental projection ranking over the unchanged public candidate API."""
from dataclasses import replace
from time import perf_counter_ns

from reachability.pressure import derive
from reachability.pressure_work import anchor, operation_cost
from reachability.trace_protocol import fingerprint
from .projection import ProjectionLimits, project, projected_graph


def rank_projected(public, snapshot, candidates, limits, *, routing_cost=True, queue_cost=True,
                   projection_limits=ProjectionLimits(), metrics=None):
    start = perf_counter_ns()
    projection = project(public, snapshot, limits=projection_limits)
    normalized = perf_counter_ns()
    nodes, edges, sources = projected_graph(public, snapshot, projection)
    if not routing_cost:
        targets = {'rule:'+r['rule_id'] for r in snapshot['rules']} | {'probe:'+p['probe_id'] for p in public['probes']}
        edges = [replace(e, weight=1.) if e.child in targets else e for e in edges]
    constructed = perf_counter_ns()
    field = derive(dict(snapshot=fingerprint(snapshot), revisions=snapshot['revisions'],
        priorities=fingerprint(public['priorities']), projection=projection,
        cost_placement=dict(routing=routing_cost, queue=queue_cost)), nodes, edges, sources, limits=limits)
    solved = perf_counter_ns()
    if metrics is not None:
        metrics['normalization_ns'] += normalized-start
        metrics['graph_ns'] += constructed-normalized
        metrics['normalization_visits'] += projection['work']['visits']
        metrics['projected_occurrences'] += projection['work']['projected']
    ranks = {c.candidate_id: (-field['scores'].get(anchor(c), {}).get('value', 0.) /
        (operation_cost(public, c) if queue_cost else 1), operation_cost(public, c), c.rank) for c in candidates}
    # The frozen controller charges the complete construction phase. The two
    # subcategories are separately reported, never added to that inclusive total.
    return ranks, field, constructed-start, solved-constructed
