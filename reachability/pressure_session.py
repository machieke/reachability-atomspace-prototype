"""Certified authority adapter for the bounded reasoning comparison.

No inferred result is scripted. Evidence, inference, monitoring and goal
accounting use existing public AdmissionService APIs. This synchronous episode
adapter requires a fresh directory; it provides no new interrupted recovery.
"""
from copy import deepcopy
from itertools import count
import json
from pathlib import Path
from time import perf_counter_ns

from .goal_model import DurabilityContract, GoalContract, GoalSlice, goal_sample_literal
from .model import Clause, Evidence, Literal, Rule, Statement, Status
from .pressure_work import enumerate_work, validate_public
from .requirements import Requirement
from .service import AdmissionDenied, AdmissionService
from .trace_protocol import fingerprint


class Metrics:
    def __init__(self):
        self.values = dict(inference_ns=0, certification_ns=0, persistence_ns=0, authority_other_ns=0,
                           inference_calls=0, certificates=0, journal_commands=0)

    def call(self, category, function, *args, **kwargs):
        start, persisted = perf_counter_ns(), self.values['persistence_ns']
        try:
            return function(*args, **kwargs)
        finally:
            self.values[category] += perf_counter_ns()-start-(self.values['persistence_ns']-persisted)


class ReasoningSession:
    def __init__(self, public, directory):
        self.public = deepcopy(validate_public(public))
        path = Path(directory)/'admission.db'
        if path.exists():
            raise ValueError('comparison requires a fresh authority; interrupted sessions remain blocked')
        self.metrics, self.ids, self.aliases, self.evidence = Metrics(), count(), {}, {}
        self.rules = deepcopy(public['admission']['rules'])
        self.context_id = public['context_id']
        self.service = AdmissionService(tuple(Rule(r['rule_id'], r['revision'], tuple(map(self.literal, r['premises'])),
            self.literal(r['conclusion'])) for r in self.rules), max_variables=20, database=path)
        append = self.service._journal.append
        def measured_append(*args, **kwargs):
            start = perf_counter_ns()
            try:
                result = append(*args, **kwargs)
                self.metrics.values['journal_commands'] += 1
                return result
            finally:
                self.metrics.values['persistence_ns'] += perf_counter_ns()-start
        self.service._journal.append = measured_append
        self.call('open_context', self.context_id, constraints=tuple(Clause(tuple(map(self.literal, c))) for c in public['clauses']))
        for goal in public['goals']:
            contract = GoalContract(goal['goal_id']+'-contract', '1', goal['unit'], (
                GoalSlice('result', goal['loss'], goal['goal_id']+'-result', self.requirement(goal['condition']),
                          DurabilityContract(1, 1, 1000, ('monitor',))),), 'bounded-reasoning-comparison/v1')
            self.call('register_goal_contract', contract)
            self.call('open_goal_episode', goal['goal_id'], goal['source_id'], self.context_id, contract.contract_id, '1')

    def key(self):
        return 'comparison:'+str(next(self.ids))

    def _operation_alias(self):
        # Fixture evidence and generated operations share the public reference
        # namespace. Retain names even after revocation or failed admission.
        while True:
            alias = 'operation-'+str(next(self.ids))
            if alias not in self.aliases and alias not in self.evidence:
                return alias

    def literal(self, value):
        return Literal(Statement('comparison:atom', (self.public['admission']['atoms'][abs(value)-1],)), value > 0)

    def requirement(self, expression):
        if type(expression) is int:
            return Requirement('FACT', self.literal(expression))
        operator, children = next(iter(expression.items()))
        return Requirement(operator, children=tuple(self.requirement(child) for child in children))

    def call(self, name, *args, **kwargs):
        category = 'certification_ns' if name in ('precertify', 'postcertify', 'commit') else 'authority_other_ns'
        result = self.metrics.call(category, getattr(self.service, name), *args, idempotency_key=self.key(), **kwargs)
        self.metrics.values['certificates'] += name in ('precertify', 'postcertify')
        return result

    def admit(self, transition, alias):
        revision = self.service.snapshot(self.context_id).knowledge_revision
        pre = self.call('precertify', transition, revision)
        if pre.status is not Status.PASS:
            raise AdmissionDenied(pre.status, 'comparison pre-certificate refused')
        self.metrics.values['inference_calls'] += 1
        proposal = self.metrics.call('inference_ns', self.service.infer, transition, pre)
        post = self.call('postcertify', proposal, pre)
        result = self.call('commit', proposal, pre, post, revision)
        if result.status is not Status.PASS:
            raise AdmissionDenied(result.status, result.detail)
        self.aliases[alias] = result.belief.belief_revision_id
        return result.belief

    def observe(self, value, name, *, valid_until=None, source='sensor'):
        if name in self.aliases and name not in self.evidence:
            raise ValueError('observation reference is already bound to an inference')
        literal = self.literal(value) if type(value) is int else value
        now = self.service.snapshot(self.context_id).logical_time
        self.call('record_evidence', Evidence(name, self.context_id, literal, source, now, (name,), valid_until))
        self.evidence[name] = valid_until
        return self.admit(self.call('propose_evidence', self.context_id, name), name)

    def read(self):
        state = self.service.snapshot(self.context_id)
        supports = []
        indices = {self.literal(i): i for i in range(1, len(self.public['admission']['atoms'])+1)}
        indices.update({literal.negate(): -i for literal, i in list(indices.items())})
        aliases = {value: key for key, value in reversed(list(self.aliases.items()))}
        for belief in state.usable:
            if belief.conclusion not in indices:
                continue  # Monitoring facts are exposed through the goal ledger.
            expiries = [self.evidence[e] for e in belief.proposal.evidence_ids]
            supports.append(dict(reference=aliases[belief.belief_revision_id], literal=indices[belief.conclusion],
                belief_revision=belief.accepted_at_revision, valid_until=min((e for e in expiries if e is not None), default=None)))
        goals, revisions = [], {}
        for declared in self.public['goals']:
            view = self.service.inspect_goal(declared['goal_id'])
            projection, item = view.projection, view.projection.slices[0]
            goals.append(dict(goal_id=view.episode.goal_id, source_id=view.episode.source_id, slice_id=item.slice_id,
                unit=projection.unit, contract_revision=view.episode.contract_revision, condition=deepcopy(declared['condition']),
                condition_status=item.condition.status.value, outstanding=item.outstanding_loss, coverage=item.estimated_coverage,
                selected_commitment=item.selected_commitment,
                open_loss=item.outstanding_loss-item.estimated_coverage, observation_required=item.observation_required,
                maintenance_required=item.maintenance_required, label=item.label,
                relief_events=[e.event_id for revision in view.history for e in revision.events if e.kind == 'observed_relief'],
                reopened_events=[e.event_id for revision in view.history for e in revision.events if e.kind == 'reopened']))
            revisions[view.episode.goal_id] = dict(goal=projection.goal_revision,
                lifecycle=projection.lifecycle_revision, resources=projection.resource_revision)
        return dict(schema='pressure-work-snapshot/v1', public_digest=fingerprint(self.public), time=state.logical_time,
            revisions=dict(knowledge=state.knowledge_revision, policy=state.policy_revision, goals=revisions,
                           dependencies=fingerprint(self.rules), priorities=fingerprint(self.public['priorities'])),
            supports=sorted(supports, key=lambda s: s['reference']), rules=deepcopy(self.rules), goals=goals,
            clauses=[[indices[literal] for literal in clause.literals] for clause in state.constraints])

    def replace_rule(self, rule):
        from .admission_protocol import rule as validate_rule
        validate_rule(rule, len(self.public['admission']['atoms']))
        previous = next(r for r in self.rules if r['rule_id'] == rule['rule_id'])
        updated = Rule(rule['rule_id'], rule['revision'], tuple(map(self.literal, rule['premises'])), self.literal(rule['conclusion']))
        self.call('replace_rule', updated, previous['revision'])
        self.rules = [deepcopy(rule) if r['rule_id'] == rule['rule_id'] else r for r in self.rules]

    def execute(self, candidate, snapshot_digest, *, response=None):
        before = dict(self.metrics.values)
        status, detail, belief = 'PASS', '', None
        try:
            snapshot = self.read()
            if fingerprint(snapshot) != snapshot_digest:
                raise AdmissionDenied(Status.STALE, 'public snapshot changed before operation')
            if candidate not in enumerate_work(self.public, snapshot).candidates:
                raise AdmissionDenied(Status.FAIL, 'operation not in the shared public frontier')
            args, alias = dict(candidate.arguments), self._operation_alias()
            if candidate.kind == 'derive':
                parents = tuple(self.aliases[name] for name in json.loads(args['premises']))
                transition = self.call('propose_transition', self.context_id, args['rule_id'], parents)
                belief = self.admit(transition, alias)
            elif candidate.kind == 'observe':
                probe = next(p for p in self.public['probes'] if p['probe_id'] == args['probe_id'])
                if response is None:
                    raise AdmissionDenied(Status.UNKNOWN, 'observation returned no evidence')
                if abs(response['literal']) != abs(probe['literal']):
                    raise ValueError('observation does not match requested capability')
                belief = self.observe(response['literal'], alias, valid_until=response['valid_until'])
            elif candidate.kind == 'monitor':
                if type(response) is not bool:
                    raise AdmissionDenied(Status.UNKNOWN, 'no observed outcome sample')
                goal_id = args['goal_id']
                sample = goal_sample_literal(goal_id, 'result', goal_id+'-result', snapshot['time'], response)
                belief = self.observe(sample, alias, source='monitor')
                self.call('record_goal_sample', alias, goal_id, 'result', response, belief.belief_revision_id)
            else:
                raise ValueError('unsupported operation channel')
        except AdmissionDenied as error:
            status, detail = error.status.value, str(error)
        # Goal accounting is an explicit authority operation, never a pressure
        # side effect. It records only relief/reopening already supported now.
        for goal in self.public['goals']:
            view = self.service.inspect_goal(goal['goal_id'])
            if view.reconciliation_needed:
                self.call('reconcile_goal', goal['goal_id'], view.projection.fingerprint)
        delta = {key: value-before[key] for key, value in self.metrics.values.items()}
        return dict(status=status, detail=detail, belief=None if belief is None else belief.belief_revision_id,
                    costs=delta, knowledge_revision=self.service.snapshot(self.context_id).knowledge_revision)

    def tick(self, time):
        self.call('advance_clock', self.context_id, time)
        self.call('advance_resource_clock', time)

    def close(self):
        self.service.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
