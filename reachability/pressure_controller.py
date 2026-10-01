"""Two ranking policies over one public read/execute port; no evaluator imports."""
from dataclasses import asdict, dataclass
from heapq import heapify, heappop
from time import perf_counter_ns

from .pressure import PressureLimits, derive
from .pressure_work import anchor, b0_ranking, build_graph, enumerate_work, operation_cost, validate_public
from .trace_protocol import fingerprint


@dataclass(frozen=True)
class ComparisonBudget:
    actions: int = 16
    operation_work: int = 32
    observation_work: int = 16
    candidate_visits: int = 4096
    ranking_states: int = 65536
    pressure_iterations: int = 8192
    wall_ns: int = 30_000_000_000

    def __post_init__(self):
        for name, bound in (('actions', 64), ('operation_work', 1000), ('observation_work', 1000),
                            ('candidate_visits', 16384), ('ranking_states', 1000000),
                            ('pressure_iterations', 65536), ('wall_ns', 120_000_000_000)):
            value = getattr(self, name)
            if type(value) is not int or not 0 <= value <= bound:
                raise ValueError('comparison session budget outside supported bound')


def rank_b3(public, snapshot, candidates, limits):
    start = perf_counter_ns()
    nodes, edges, sources = build_graph(public, snapshot)
    construction_ns = perf_counter_ns()-start
    start = perf_counter_ns()
    field = derive(dict(snapshot=fingerprint(snapshot), revisions=snapshot['revisions'],
        priorities=fingerprint(public['priorities'])), nodes, edges, sources, limits=limits)
    solve_ns = perf_counter_ns()-start
    ranks = {c.candidate_id: (-field['scores'].get(anchor(c), {}).get('value', 0.)/operation_cost(public, c),
                            operation_cost(public, c), c.rank) for c in candidates}
    return ranks, field, construction_ns, solve_ns


class ComparisonController:
    def __init__(self, public, variant, *, limits=PressureLimits()):
        self.public = validate_public(public)
        if variant not in ('B0', 'B3'):
            raise ValueError('supported variants are B0 and B3')
        self.variant, self.limits = variant, limits

    def run(self, port, budget=ComparisonBudget(), *, emit=None):
        start = perf_counter_ns()
        work = dict(actions=0, operation_work=0, observation_work=0, candidate_visits=0,
                    ranking_states=0, ranking_transitions=0, ranking_joint_checks=0,
                    pressure_nodes=0, pressure_edges=0, pressure_iterations=0, pressure_edge_visits=0)
        costs = dict(snapshot_ns=0, candidate_discovery_ns=0, ranking_ns=0,
                     pressure_construction_ns=0, pressure_iteration_ns=0, execution_ns=0)
        records, reason, last_pressure = [], 'ACTION_BUDGET', None
        while work['actions'] < budget.actions:
            if perf_counter_ns()-start >= budget.wall_ns:
                reason = 'WALL_BUDGET'; break
            clock = perf_counter_ns(); snapshot = port.read(); costs['snapshot_ns'] += perf_counter_ns()-clock
            clock = perf_counter_ns()
            frontier = enumerate_work(self.public, snapshot, visit_limit=budget.candidate_visits-work['candidate_visits'])
            costs['candidate_discovery_ns'] += perf_counter_ns()-clock
            work['candidate_visits'] += frontier.visits
            if not frontier.complete:
                reason = 'CANDIDATE_BUDGET'; break
            if frontier.terminal:
                reason = 'OBSERVED_GOALS'; break
            candidates = [c for c in frontier.candidates if
                operation_cost(self.public, c)+work['operation_work'] <= budget.operation_work
                and c.observation_cost+work['observation_work'] <= budget.observation_work]
            empty_reason = 'WORK_BUDGET' if frontier.candidates else 'BLOCKED'
            if not candidates and self.variant == 'B0':
                reason = empty_reason; break
            clock = perf_counter_ns()
            field = None
            if self.variant == 'B0':
                ranks, search, complete = b0_ranking(self.public, snapshot, candidates,
                    state_limit=budget.ranking_states-work['ranking_states'])
                work['ranking_states'] += search['states']; work['ranking_transitions'] += search['transitions']
                work['ranking_joint_checks'] += search['joint_checks']
                if not complete:
                    costs['ranking_ns'] += perf_counter_ns()-clock
                    reason = 'RANKING_BUDGET'; break
            else:
                # Reserve a conservative complete solve allowance before work;
                # no session may exceed its declared numerical iteration limit.
                if work['pressure_iterations']+len(snapshot['goals'])*self.limits.iterations > budget.pressure_iterations:
                    reason = 'PRESSURE_SESSION_BUDGET'; break
                ranks, field, construction, iteration = rank_b3(self.public, snapshot, candidates, self.limits)
                costs['pressure_construction_ns'] += construction
                costs['pressure_iteration_ns'] += iteration
                work['pressure_iterations'] += field['work']['iterations']
                work['pressure_edge_visits'] += field['work']['edge_visits']
                work['pressure_nodes'] += field['work']['nodes']; work['pressure_edges'] += field['work']['edges']
                last_pressure = field
                if any(name in field['exhausted'] for name in ('nodes', 'edges', 'sources')):
                    costs['ranking_ns'] += perf_counter_ns()-clock-construction-iteration
                    reason = 'PRESSURE_GRAPH_BUDGET'; break
                if not candidates:
                    costs['ranking_ns'] += perf_counter_ns()-clock-construction-iteration
                    reason = empty_reason; break
            queue = [(ranks[c.candidate_id], c.candidate_id, c) for c in candidates]
            heapify(queue)
            selected = heappop(queue)[2]
            elapsed = perf_counter_ns()-clock
            costs['ranking_ns'] += elapsed-(construction+iteration if self.variant == 'B3' else 0)
            # A wall limit is checked again before issuing an operation. In-flight
            # certified operations are atomic and never interrupted to meet time.
            if perf_counter_ns()-start >= budget.wall_ns:
                reason = 'WALL_BUDGET'; break
            work['actions'] += 1
            work['operation_work'] += operation_cost(self.public, selected)
            work['observation_work'] += selected.observation_cost
            row = dict(schema='pressure-comparison-step/v1', variant=self.variant, step=work['actions'],
                ranking_path='b0-conditional-plan-best-first' if self.variant == 'B0' else 'b3-typed-pressure-priority-queue',
                snapshot=snapshot, snapshot_digest=fingerprint(snapshot),
                candidates=[c.wire() for c in frontier.candidates],
                ranks={key: list(value) for key, value in ranks.items()}, pressure=field,
                selected=selected.wire(), budget=asdict(budget), work=dict(work))
            if emit:
                emit(dict(stage='selection', **row))
            clock = perf_counter_ns()
            row['receipt'] = port.execute(selected, fingerprint(snapshot))
            costs['execution_ns'] += perf_counter_ns()-clock
            records.append(row)
            if emit:
                emit(dict(stage='receipt', step=work['actions'], receipt=row['receipt']))
        total = perf_counter_ns()-start
        if emit:
            emit(dict(stage='stop', reason=reason, work=work, last_pressure=last_pressure))
        return dict(variant=self.variant, stop_reason=reason, work=work, costs=costs,
                    total_elapsed_ns=total, wall_overrun_ns=max(0, total-budget.wall_ns), records=records,
                    last_pressure=last_pressure)
