"""Thin public-API adapter over the existing numerical and deployment ledgers.

Registrations/reports below are receipt indexes, not authority. The service alone
issues permits, determines current estimates and commits. Acquisition is an
injected external port; the agenda receives descriptors and received events only.
"""
from collections import defaultdict
from dataclasses import replace
from itertools import count
from time import perf_counter_ns

from reachability.adapter_runtime import AdapterError
from reachability.atomspace_adapter import RecordProjection
from reachability.deployment_trace import DeploymentSession
from reachability.model import Status
from reachability.pln_adapter import PLNAdapter, PeTTaFormulaRuntime, implication
from reachability.probability_formula import PinnedFormulaRuntime
from reachability.service import AdmissionDenied
from reachability.trace_protocol import DeploymentInitial, event

from .agenda import Limits, Report, Snapshot, digest, enumerate_work, wire


class MeasuredRuntime:
    def __init__(self, native, costs):
        self.native, self.costs, self.calls = native, costs, []
        self.runtime = PeTTaFormulaRuntime() if native else PinnedFormulaRuntime()

    def evaluate(self, formula, truths):
        started = perf_counter_ns()
        record = dict(mode='native' if self.native else 'finite-checker', formula=formula, inputs=wire(truths))
        self.calls.append(record)
        try:
            result = self.runtime.evaluate(formula, truths)
            record['elapsed_ns'] = perf_counter_ns()-started
            record['result'] = wire(result)
            record['status'] = 'PASS'
            if self.native:
                checked_start = perf_counter_ns()
                expected = PinnedFormulaRuntime().evaluate(formula, truths)
                record['formula_agreement'] = result == expected
                record['reference_result'] = wire(expected)
                record['reference_check_ns'] = perf_counter_ns()-checked_start
                self.costs['runtime_reference_check_ns'] += record['reference_check_ns']
            else:
                record['formula_agreement'] = 'finite-runtime-only'
            return result
        except Exception as error:
            record.update(status='ERROR', error=type(error).__name__+': '+str(error))
            raise
        finally:
            record.setdefault('elapsed_ns', perf_counter_ns()-started)
            self.costs['runtime_ns'] += record['elapsed_ns']


class Session(DeploymentSession):
    """Fresh coordinator only. Reopen checks authority; it does not resume this agenda."""
    def __init__(self, directory, *, native=False, limits=Limits(), acquire=None):
        self.ids = count()
        self.costs = defaultdict(int)
        self.receipts, self.received = [], []
        self.rules, self.models, self.reports, self.probes = {}, {}, {}, {}
        self.revoked_models = set()
        self.limits, self.acquire = limits, acquire
        self.after_proposal = None  # evaluator seam, never a controller input
        self.runtime = MeasuredRuntime(native, self.costs)
        self.adapter = PLNAdapter(self.runtime)
        started = perf_counter_ns()
        super().__init__(DeploymentInitial(context_id='ctx', product_id='artifact-v2', goal_id='goal',
                                           lease_duration=100), directory)
        self.emit('attempt', attempt_id='attempt')
        self.costs['setup_ns'] += perf_counter_ns()-started

    def key(self):
        return 'online:'+str(next(self.ids))

    @property
    def forecast(self):
        return implication('tested', 'healthy')

    def measured(self, category, function, *args, **kwargs):
        started = perf_counter_ns()
        try:
            return function(*args, **kwargs)
        finally:
            self.costs[category] += perf_counter_ns()-started

    def emit(self, kind, **arguments):
        record = self.apply(event(self.key(), kind, **arguments))
        if kind == 'revoke' and arguments['evidence_id'] in self.reports:
            old = self.reports[arguments['evidence_id']]
            self.reports[arguments['evidence_id']] = replace(old, revoked=True)
        self.received.append(dict(kind=kind, arguments=arguments, outcome=record['outcome']))
        self.receipts.append(record)
        return record

    def receive_report(self, evidence, report):
        if evidence.context_id != self.initial.context_id or evidence.evidence_id != report.evidence_id:
            raise ValueError('received report context/identity mismatch')
        self.service.record_evidence(evidence, idempotency_key=self.key())
        self.service.record_probability_report(report, idempotency_key=self.key())
        old = self.reports.get(evidence.evidence_id)
        item = Report(evidence, report, old.revoked if old else False)
        self.reports[evidence.evidence_id] = item
        self.received.append(dict(kind='numeric_report', report=item))

    def register_rule(self, rule, expected_revision=None):
        result = self.service.configure_probability_rule(self.initial.context_id, rule, expected_revision,
                                                          idempotency_key=self.key())
        self.rules[rule.rule_id] = result
        return result

    def register_model(self, model):
        result = self.service.register_probability_independence(model, idempotency_key=self.key())
        self.models[model.model_id] = result
        return result

    def revoke_model(self, model_id):
        result = self.service.revoke_probability_independence(self.initial.context_id, model_id,
                                                              idempotency_key=self.key())
        self.revoked_models.add(model_id)
        return result

    def publish_probe(self, descriptor):
        self.probes[descriptor.probe_id] = descriptor

    def read(self):
        started = perf_counter_ns()
        s = self.service
        # One coherent capture, using public service query/export methods.
        with s._lock:
            _, context, policy, numerical = s.export_probability(self.initial.context_id)
            def optional(method):
                try:
                    return method('attempt')
                except KeyError:
                    return None
            result = Snapshot(context, policy, tuple(self.rules.values()), tuple(self.models.values()),
                tuple(sorted(self.revoked_models)), tuple(self.reports.values()), numerical,
                s.export_admission(self.initial.context_id)[2], s.inspect_operation('attempt'),
                optional(s.inspect_execution_intent), optional(s.inspect_dispatch),
                s.inspect_probability_decision('attempt', 'deploy', '1'), s.inspect_lifecycle('episode'),
                s.inspect_goal('goal'), s.resource_snapshot(), tuple(self.probes.values()),
                (('execution', 'deploy', '1'), ('lifecycle', 'artifact', '1'),
                 ('completion', 'completion', '1'), ('dispatch', 'dispatch', '1'),
                 ('goal', 'health', '1'), ('public-initial', wire(self.initial))), tuple(self.received))
        self.costs['public_read_ns'] += perf_counter_ns()-started
        return result

    def numeric(self, kind, target, premises=(), *, label='selected'):
        s, ctx = self.service, self.initial.context_id
        record = dict(kind=kind, target=target, premises=premises, origin=label)
        self.receipts.append(record)
        arguments = (dict(evidence_id=target) if kind == 'adopt' else
                     dict(rule_id=target, premise_revision_ids=premises) if kind == 'deduction' else
                     dict(independence_id=target, premise_revision_ids=premises))
        call_start = len(self.runtime.calls)
        try:
            transition = s.propose_probability(ctx, 'observation' if kind == 'adopt' else kind,
                                               **arguments, idempotency_key=self.key())
            record['transition'] = transition
            rev = s.snapshot(ctx).knowledge_revision
            pre = self.measured('precheck_ns', s.precertify_probability, transition, rev, idempotency_key=self.key())
            record.update(pre=pre, pre_status=pre.status.value)
            if pre.status is not Status.PASS:
                record.update(status=pre.status.value, detail='numeric precertificate rejected')
                return record
            proposal = self.measured('inference_inclusive_ns', s.infer_probability, transition, pre, adapter=self.adapter)
            record['proposal'] = proposal
            if self.after_proposal is not None:
                self.after_proposal(self, transition, proposal)
            post = self.measured('postcheck_ns', s.postcertify_probability, proposal, pre, idempotency_key=self.key())
            record.update(post=post, post_status=post.status.value)
            result = self.measured('numeric_commit_ns', s.commit_probability, proposal, pre, post, rev,
                                   idempotency_key=self.key())
            record.update(commit=result, status=result.status.value, detail=result.detail)
        except (AdmissionDenied, AdapterError) as error:
            record.update(status=getattr(error, 'status', Status.UNKNOWN).value,
                          detail=type(error).__name__+': '+str(error))
        finally:
            for call in self.runtime.calls[call_start:]:
                call['postcheck_status'] = record.get('post_status', 'NOT_REACHED')
                call['commit_status'] = record.get('status', 'ERROR')
        return record

    def execute(self, candidate):
        started = perf_counter_ns()
        result = dict(status='STALE', detail='public snapshot changed')
        try:
            snapshot = self.read()
            if snapshot.binding != candidate.expected_binding:
                return result
            frontier = enumerate_work(snapshot, self.limits)
            self.costs['execution_enumeration_ns'] += frontier.elapsed_ns
            if not frontier.complete or candidate not in frontier.candidates:
                return dict(status='FAIL', detail='candidate not in current complete public frontier')
            if candidate.kind in ('adopt', 'deduction', 'revision'):
                result = self.numeric(candidate.kind, candidate.target, candidate.premise_ids)
            elif candidate.kind == 'request':
                result = self.measured('acquisition_inclusive_ns', self.request, self.probes[candidate.target])
            elif candidate.kind == 'reserve':
                result = self.measured('execution_gate_reservation_ns', self.reserve)
            elif candidate.kind in ('dispatch', 'query', 'complete'):
                category = 'dispatch_ns' if candidate.kind == 'dispatch' else 'monitor_ns' if candidate.kind == 'query' else 'completion_ns'
                kind = 'reconcile' if candidate.kind == 'query' else candidate.kind
                arguments = dict(attempt_id='attempt')
                if kind == 'dispatch':
                    arguments['fault'] = 'none'
                record = self.measured(category, self.emit, kind, **arguments)
                result = record['outcome']
            else:
                result = dict(status='UNKNOWN', detail='unsupported operation channel')
            self.measured('goal_accounting_ns', self.emit, 'account')
            return result
        finally:
            elapsed = perf_counter_ns()-started
            self.costs['execution_total_ns'] += elapsed
            if result.get('status') != 'PASS':
                self.costs['failed_attempt_inclusive_ns'] += elapsed

    def reserve(self):
        record = self.emit('reserve', attempt_id='attempt')
        if record['outcome']['status'] == 'PASS':
            # Coverage is a declared promise, never observed relief.
            self.emit('cover', attempt_id='attempt', units=6,
                      valid_until=self.service.snapshot(self.initial.context_id).logical_time+100)
        return record['outcome']

    def request(self, probe):
        started = perf_counter_ns()
        try:
            if self.acquire is None:
                return dict(status='UNKNOWN', detail='no acquisition port')
            response = self.acquire(probe)
            self.received.append(dict(kind='acquisition', descriptor=probe, response=response))
            if response['status'] != 'PASS':
                self.probes[probe.probe_id] = replace(probe, availability='unavailable')
                return dict(status=response['status'], detail=response.get('detail', 'unavailable observation'))
            if probe.report_type == 'numeric':
                evidence, report = response['numeric']
                if evidence.source != probe.source or evidence.content != probe.target:
                    return dict(status='FAIL', detail='source/report does not match requested descriptor')
                self.measured('report_ingestion_ns', self.receive_report, evidence, report)
            else:
                allowed = {'fact', 'observation'} if probe.report_type == 'product' else {'sample'}
                for kind, arguments in response['events']:
                    if kind not in allowed or (kind == 'fact' and arguments['name'] != 'product'):
                        raise ValueError('acquisition response exceeds declared observation channel')
                    record = self.emit(kind, **arguments)
                    if record['outcome']['status'] != 'PASS':
                        return record['outcome']
            self.probes.pop(probe.probe_id, None)
            return dict(status='PASS', detail='received actual source response')
        finally:
            if probe.report_type in ('product', 'health'):
                self.costs['monitor_ns'] += perf_counter_ns()-started

    def authority_records(self):
        s, ctx = self.service, self.initial.context_id
        try:
            execution = s.export_execution_decision('attempt')
        except KeyError:
            execution = None
        return (s.export_probability(ctx), s.export_admission(ctx), execution,
                s.inspect_lifecycle('episode'), s.inspect_goal('goal'), s.inspect_resource('slot'))

    def project_and_reopen(self):
        before = self.authority_records()
        count_before = len(self.runtime.calls)
        def project(records):
            p = RecordProjection()
            p.add(records)
            return p.batch.run()
        graph = self.measured('projection_ns', project, before) if self.runtime.native else None
        self.measured('authority_reopen_ns', self.restart)
        after = self.authority_records()
        again = self.measured('projection_ns', project, after) if self.runtime.native else None
        result = dict(authority_equal=before == after, native_calls_before=count_before,
                      native_calls_after=len(self.runtime.calls), projection_equal=graph == again if graph else None,
                      native_atom_count=graph.size if graph else None, authority=wire(after))
        if before != after or graph != again or count_before != len(self.runtime.calls):
            raise AssertionError('quiescent reconstruction changed authority/projection or reran inference')
        return result
