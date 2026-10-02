"""Separate Goal-native path retaining frozen ranking, ages, budgets and fallback."""
from collections import defaultdict
from time import perf_counter_ns
from math import prod
from experimental_online_pln.agenda import Agenda as FrozenAgenda, Frontier, Limits, enumerate_work, wire
from experimental_goal_pln.relevance import ClosureLimits, closure, extract_task, witness
from .recall import NativeIndex
from .backend import Backend, IncompleteRecall
from dataclasses import replace
from experimental_goal_pln.reference import scan_closure
from .enumeration import enumerate_scoped

ARMS = ('unused-fifo', 'unused-scan', 'Goal-native')


class Agenda(FrozenAgenda):
    def __init__(self, arm="Goal-native", limits=Limits(), closure_limits=ClosureLimits(), backend=None):
        if arm != "Goal-native":
            raise ValueError('unknown experimental arm')
        super().__init__(limits)
        self.arm, self.closure_limits = arm, closure_limits
        self.backend = backend or Backend()
        self.costs, self.diagnostic = defaultdict(int), {}
        self.tuple_visits = 0

    def choose(self, snapshot):
        start = perf_counter_ns()
        self.diagnostic = dict(arm=self.arm, ranking='frozen-fifo/v1' if self.arm == ARMS[0]
                               else 'relevant-first-ready-fifo/v1', fallback=None)
        if self.arm == ARMS[0]:
            frontier, selected = super().choose(snapshot)
            self.costs['full_enumeration_ns'] += frontier.elapsed_ns
            self.tuple_visits += frontier.tuple_visits
            self.costs['selection_inclusive_ns'] += perf_counter_ns()-start
            self.diagnostic.update(scope='full-public-frontier', complete=frontier.complete)
            return frontier, selected
        current_count = sum(len(v.current) for v in snapshot.numerical)
        if (len(snapshot.rules)>self.limits.rules or current_count>self.limits.estimates
            or len(snapshot.models)>16 or len(snapshot.reports)>128 or len(snapshot.probes)>16):
            frontier = enumerate_work(snapshot, self.limits)
            self.stop = frontier.reason
            self.diagnostic.update(scope='full-public-frontier', complete=False, fallback='INPUT_BOUND')
            self.costs['full_enumeration_ns'] += frontier.elapsed_ns
            self.costs['selection_inclusive_ns'] += perf_counter_ns()-start
            return frontier, None
        root_start = perf_counter_ns()
        task = extract_task(snapshot)
        self.costs['roots_ns'] += perf_counter_ns()-root_start
        full = None
        if self.arm == ARMS[1]:
            dependencies = scan_closure(snapshot, task, self.closure_limits)
            full = enumerate_work(snapshot, self.limits)
            self.costs['full_enumeration_ns'] += full.elapsed_ns
            self.tuple_visits += full.tuple_visits
            source = full
        else:
            try:
                index = NativeIndex(snapshot, self.backend)
                self.costs['cold_index_ns'] += index.elapsed_ns
                self.diagnostic['index_entries'] = index.entries
                dependencies = closure(snapshot, task, self.closure_limits, index)
                # Conservative cheap capacity check: when irrelevant work could hit a
                # frozen global bound, use the same full enumerator as B. Never select
                # a candidate that the mandatory full execution check would reject
                # solely because indexed selection hid an exhausted global bound.
                capacity_start = perf_counter_ns()
                upper_tuples = sum(prod(len(index.estimates.get(p, ())) for p in r.deduction.premises)
                                   for r in index.all_rules())
                upper_candidates = upper_tuples+len(snapshot.reports)+len(snapshot.models)+len(snapshot.probes)+4
                risk = (len(snapshot.rules)>self.limits.rules or len(index.by_id)>self.limits.estimates
                        or len(snapshot.models)>16 or len(snapshot.reports)>128 or len(snapshot.probes)>16
                        or upper_tuples>self.limits.tuple_visits or upper_candidates>self.limits.candidates)
                self.costs['capacity_check_ns'] += perf_counter_ns()-capacity_start
                self.diagnostic['capacity_full_scan'] = risk
                if risk:
                    full = enumerate_work(snapshot, self.limits)
                    self.costs['capacity_fallback_enumeration_ns'] += full.elapsed_ns
                    source = full
                else:
                    source = enumerate_scoped(snapshot, dependencies, index, self.limits)
                self.costs['scoped_enumeration_ns'] += source.elapsed_ns
                self.tuple_visits += source.tuple_visits
            except IncompleteRecall as exhausted:
                # Preserve an explicit incomplete descriptor; never promote empty
                # native answers to a complete scoped frontier.
                from experimental_goal_pln.relevance import Closure
                dependencies = Closure(task, (), (), False, 'NATIVE_'+exhausted.result.reason, 0, 0, 0, 0)
                source = Frontier((), False, dependencies.reason, 0, 0)
                self.diagnostic['native_query_exhaustion'] = wire(exhausted.result)
        self.diagnostic['native_view'] = wire(self.backend.receipt)
        self.costs['closure_ns'] += dependencies.elapsed_ns
        classify_start = perf_counter_ns()
        pairs = [(c, witness(c, snapshot, dependencies)) for c in source.candidates] if dependencies.complete else []
        relevant = tuple(c for c, w in pairs if w is not None)
        self.diagnostic.update(task=wire(task), closure=wire(dependencies),
            witnesses=[dict(candidate=c.logical_id, witness=wire(w)) for c,w in pairs if w is not None],
            relevant=wire(relevant), discovery_complete=source.complete and dependencies.complete,
            source_tuple_visits=source.tuple_visits)
        self.costs['classification_ns'] += perf_counter_ns()-classify_start
        rank_start = perf_counter_ns()
        if self.selections >= self.limits.selections:
            self.stop = 'SELECTION_BUDGET'
            self.costs['ranking_ns'] += perf_counter_ns()-rank_start
            self.costs['selection_inclusive_ns'] += perf_counter_ns()-start
            return Frontier(relevant, source.complete and dependencies.complete, 'TASK_SCOPE',
                            source.tuple_visits, perf_counter_ns()-start), None
        for c in relevant:
            self.first_ready.setdefault(c.logical_id, self.round)
        def eligible(c):
            return ((c.logical_id,c.basis) not in self.attempted and self.work+c.cost <= self.limits.work
                    and self.acquisitions+c.acquisition_cost <= self.limits.acquisitions)
        chosen_scope = [c for c in relevant if eligible(c)]
        self.costs['ranking_ns'] += perf_counter_ns()-rank_start
        frontier = Frontier(relevant, source.complete and dependencies.complete, 'TASK_SCOPE',
                            source.tuple_visits, perf_counter_ns()-start)
        if not dependencies.complete or not source.complete or not chosen_scope:
            self.diagnostic['fallback'] = ('INCOMPLETE_CLOSURE:'+dependencies.reason if not dependencies.complete
                else 'INCOMPLETE_DISCOVERY:'+source.reason if not source.complete else 'NO_AFFORDABLE_UNTRIED_RELEVANT_WORK')
            if full is None:
                full = enumerate_work(snapshot, self.limits)
                self.costs['fallback_enumeration_ns'] += full.elapsed_ns
                self.tuple_visits += full.tuple_visits
            frontier = full
            self.diagnostic['scope'] = 'full-public-frontier-fallback'
            if not full.complete:
                self.stop = full.reason
                self.costs['selection_inclusive_ns'] += perf_counter_ns()-start
                return frontier, None
            chosen_scope = [c for c in full.candidates if eligible(c)]
            for c in full.candidates:
                self.first_ready.setdefault(c.logical_id, self.round)
        else:
            self.diagnostic['scope'] = 'declared-task-frontier'
        rank_start = perf_counter_ns()
        self.round += 1
        if not chosen_scope:
            if any((c.logical_id,c.basis) not in self.attempted for c in frontier.candidates):
                self.stop = 'WORK_OR_ACQUISITION_BUDGET'
            else:
                self.stop = 'QUIESCENT_UNRESOLVED' if snapshot.goal.projection.outstanding_loss else 'OBSERVED_GOAL'
            selected = None
        else:
            selected = min(chosen_scope, key=lambda c:(self.first_ready[c.logical_id], c.semantic_tie))
            self.attempted.add((selected.logical_id, selected.basis))
            self.selections += 1
            self.work += selected.cost
            self.acquisitions += selected.acquisition_cost
        self.diagnostic.update(eligible=wire(chosen_scope), complete=frontier.complete,
            ages={c.logical_id:self.first_ready[c.logical_id] for c in chosen_scope})
        self.costs['ranking_ns'] += perf_counter_ns()-rank_start
        self.costs['selection_inclusive_ns'] += perf_counter_ns()-start
        return frontier, selected
