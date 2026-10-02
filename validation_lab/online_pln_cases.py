"""Evaluator-private counterfactual setup and actual observation source.

No fixture, future response or seam callback is passed to Agenda. Initial reports
are adopted via the public ledger; every deduction/revision is selected online.
"""
import json
from pathlib import Path

from experimental_online_pln.agenda import Probe, wire
from reachability.model import Evidence
from reachability.pln_adapter import DeductionRule, TruthValue
from reachability.probability_model import ProbabilityIndependence, ProbabilityReport, ProbabilityRule

ROOT = Path(__file__).resolve().parents[1]
MAIN = ProbabilityRule('deployment', '1', DeductionRule('tested', 'staged', 'healthy'))
VALID = (.4, .5, .6, .7, .8)
JOINT_FAILURE = (.99995, .99995, .499975, 1, .5)


def fixtures():
    return json.loads((ROOT/'reviews/online-pln-lifecycle-v1/fixtures.json').read_text())['fixtures']


class World:
    def __init__(self, fixture):
        self.fixture = fixture
        self.product = False
        self.healthy = None
        self.samples = self.product_requests = 0
        self.seams = []
        self.triggered = self.later_failure = False
        self.missing = None

    @property
    def external_loss(self):
        return 0 if self.product and self.healthy is True else 10

    def setup(self, session, *, rule_prefix='', reverse_reports=False):
        self.session = session
        s, family, variant = session, self.fixture['family'], self.fixture['variant']
        s.emit('fact', name='tested', valid_until=None)
        s.emit('fact', name='credential', valid_until=None)

        def report(name, literal, truth, roots=None, adopt=True):
            evidence = Evidence(name, 'ctx', literal, 'forecast-model',
                s.service.snapshot('ctx').logical_time, tuple(roots or ('root:'+name,)))
            numeric = ProbabilityReport(name, truth)
            s.receive_report(evidence, numeric)
            if adopt:
                result = s.numeric('adopt', name, label='initial-report-adoption')
                if result['status'] != 'PASS':
                    raise AssertionError(result)
                return result['commit'].belief
            return evidence, numeric
        self.report = report

        if family == 'lineage':
            left = report('report-a', s.forecast, TruthValue(.7, .25), ('root-a',))
            right = report('report-b', s.forecast, TruthValue(.7, .25),
                           ('root-a' if variant == 'copied' else 'root-b',))
            s.register_model(ProbabilityIndependence('declared-independence', 'ctx',
                (left.belief_revision_id, right.belief_revision_id),
                'trusted source declaration of independent report-generating processes'))
        else:
            rules = [MAIN]
            if family == 'choice':
                rules += [ProbabilityRule('canary', '1', DeductionRule('tested', 'staged', 'canary')),
                          ProbabilityRule('audit', '1', DeductionRule('tested', 'cached', 'audit'))]
            values = {}
            for rule in rules:
                s.register_rule(ProbabilityRule(rule_prefix+rule.rule_id, rule.revision, rule.deduction))
                strengths = JOINT_FAILURE if family == 'boundary' and variant == 'joint' else VALID
                for literal, strength in zip(rule.deduction.premises, strengths):
                    if literal in values and values[literal] != strength:
                        raise AssertionError('fixture has incompatible shared premise definitions')
                    values[literal] = strength
            reports = list(enumerate(values.items()))
            if reverse_reports:
                reports.reverse()
            for index, (literal, strength) in reports:
                name = 'report-'+str(index)
                if family == 'choice' and literal == MAIN.deduction.premises[-1]:
                    self.missing = (name, literal, TruthValue(strength, .8))
                    continue
                report(name, literal, TruthValue(strength, .8))
            if family == 'support' and variant == 'alternative':
                report('independent-p', MAIN.deduction.premises[0], TruthValue(.4, .8))
            if family == 'choice':
                s.publish_probe(Probe('source-report', 'forecast-model', 'numeric', self.missing[1]))
        if family == 'support':
            s.after_proposal = self.support_change
        if family == 'race':
            # Reuse the exact deterministic prepare/final-send seam of the
            # existing decision-dispatch regression. This is not agenda input.
            original = s.service.prepare_dispatch
            def prepare(*args, **kwargs):
                result = original(*args, **kwargs)
                if not self.triggered:
                    self.triggered = True
                    before = s.read().decision
                    if variant == 'revoked':
                        evidence = next(v.current[0].proposal.support.evidence_ids[0]
                            for v in s.read().numerical if v.conclusion == s.forecast)
                        s.emit('revoke', evidence_id=evidence)
                    self.seams.append(dict(kind='after-prepare-before-send', variant=variant,
                                           before=wire(before), after=wire(s.read().decision)))
                return result
            s.service.prepare_dispatch = prepare

    def support_change(self, session, transition, proposal):
        if self.triggered or transition.kind != 'deduction':
            return
        self.triggered = True
        selected = next(b for v in session.read().numerical for b in v.current
                        if b.belief_revision_id == transition.premise_revision_ids[0])
        evidence_id = selected.proposal.support.evidence_ids[0]
        session.emit('revoke', evidence_id=evidence_id)
        if self.fixture['variant'] == 'replacement':
            self.report('equal-replacement', selected.proposal.support.conclusion,
                        selected.proposal.support.truth, adopt=False)
        self.seams.append(dict(kind='after-proposal-before-postcheck', transition=wire(transition),
                               proposal=wire(proposal), revoked=evidence_id,
                               replacement=self.fixture['variant'] == 'replacement'))

    def acquire(self, probe):
        if probe.report_type == 'numeric':
            if self.fixture['variant'] == 'unavailable':
                return dict(status='UNKNOWN', detail='source responded unavailable')
            name, literal, truth = self.missing
            evidence = Evidence(name, 'ctx', literal, probe.source,
                self.session.service.snapshot('ctx').logical_time, ('root:'+name,))
            return dict(status='PASS', numeric=(evidence, ProbabilityReport(name, truth)))
        if probe.report_type == 'product':
            self.product_requests += 1
            if self.fixture['variant'] == 'reopened' and self.product_requests == 1:
                return dict(status='PASS', events=(('observation', dict(attempt_id='attempt',
                    product_id='artifact-v1', milestone='exact_product_observed')),))
            self.product = True
            return dict(status='PASS', events=(('fact', dict(name='product', valid_until=None)),
                ('observation', dict(attempt_id='attempt', product_id='artifact-v2', milestone='completion_observed')),
                ('observation', dict(attempt_id='attempt', product_id='artifact-v2', milestone='exact_product_observed'))))
        self.samples += 1
        self.healthy = not self.later_failure
        return dict(status='PASS', events=(('sample', dict(healthy=self.healthy)),))

    def after(self, candidate, result):
        s = self.session
        if candidate.kind == 'dispatch' and result['status'] == 'PASS':
            # These are received clock/capability events, never future answers.
            if self.fixture['family'] == 'product':
                evidence = next(v.current[0].proposal.support.evidence_ids[0]
                    for v in s.read().numerical if v.conclusion == s.forecast)
                s.emit('revoke', evidence_id=evidence)
                self.seams.append(dict(kind='forecast-retirement-after-ack', evidence_id=evidence))
            s.emit('tick', time=1)
            s.publish_probe(Probe('product', 'executor', 'product', 'artifact-v2', ('acknowledged',)))
        elif candidate.kind == 'request' and candidate.target == 'product':
            if result['status'] != 'PASS':
                s.publish_probe(Probe('product', 'executor', 'product', 'artifact-v2', ('acknowledged',),
                                      opportunity=self.product_requests))
            else:
                s.publish_probe(Probe('health', 'monitor', 'health', 'artifact-v2', ('exact_product',), opportunity=1))
        elif candidate.kind == 'request' and candidate.target == 'health' and self.samples < 3:
            s.emit('tick', time=self.samples+1)
            s.publish_probe(Probe('health', 'monitor', 'health', 'artifact-v2', ('exact_product',),
                                  opportunity=self.samples+1))
        elif candidate.kind == 'complete' and result['status'] == 'PASS' and self.fixture['variant'] == 'reopened':
            self.later_failure = True
            s.emit('tick', time=4)
            s.publish_probe(Probe('health', 'monitor', 'health', 'artifact-v2', ('exact_product',), opportunity=4))


def check_case(fixture, rows, result):
    """Prefix conformance expectations, independent of agenda implementation."""
    expected = fixture['expected']
    for name in ('stage', 'outstanding', 'effects', 'decision'):
        if name in expected and result[name] != expected[name]:
            raise AssertionError(f'{fixture["id"]}: {name} expected {expected[name]}, got {result[name]}')
    selected = [r for r in rows if r.get('selected')]
    for row in selected:
        after = row['after']
        if not after['product_observed']:
            if after['outstanding'] != 10 or row['external_loss'] != 10:
                raise AssertionError('forecast/ACK became observed relief')
        if after['hard_forecast'] != 'UNKNOWN':
            raise AssertionError('numeric forecast became a hard fact')
        numeric = row['result']
        if row['selected']['kind'] == 'deduction' and numeric['status'] == 'PASS':
            if len(numeric['post']['joint_witness']) != 8 or numeric['post_status'] != 'PASS':
                raise AssertionError('deduction lacks complete joint certificate')
    for key, kind in (('revision', 'revision'), ('old_commit', 'deduction'),
                      ('deduction', 'deduction'), ('dispatch', 'dispatch')):
        if key in expected and not any(r['selected']['kind'] == kind and r['result']['status'] == expected[key] for r in selected):
            raise AssertionError(f'missing expected {key} {expected[key]}')
    if 'wrong_product' in expected and not any(r['selected']['target'] == 'product'
            and r['result']['status'] == 'FAIL' for r in selected):
        raise AssertionError('wrong product was not rejected')
    if fixture['family'] == 'choice':
        initial = rows[0]['frontier']['candidates']
        if sum(c['kind'] == 'deduction' for c in initial) != 2 or not any(c['kind'] == 'request' for c in initial):
            raise AssertionError('positive selection lacks live competing work')
    if fixture['family'] == 'lineage':
        forecast = result['forecast']
        if len(forecast) != (3 if fixture['variant'] == 'independent' else 2):
            raise AssertionError('lineage/revision alternatives were lost or inflated')
        if sum(x['confidence'] == .25 for x in forecast) != 2:
            raise AssertionError('low-confidence parents were hidden')
    if result['stage'] == 'BUILT':
        samples = [r['after']['outstanding'] for r in selected
                   if r['selected']['kind'] == 'request' and r['selected']['target'] == 'health']
        if samples[:3] != [10, 10, 0]:
            raise AssertionError('durability prefix differs: '+str(samples))
    if fixture['variant'] == 'reopened' and not {'observed_relief', 'reopened'} <= set(result['relief_kinds']):
        # Actual event kind spellings are fixed by the existing goal API.
        raise AssertionError('reopening failed to retain relief history: '+str(result['relief_kinds']))
