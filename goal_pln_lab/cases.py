"""Preregistered evaluator-only worlds. No task roots or correct-action lists."""
import json
from pathlib import Path
from experimental_online_pln.agenda import Probe, wire
from reachability.model import Evidence
from reachability.pln_adapter import DeductionRule, TruthValue, implication
from reachability.probability_model import ProbabilityReport, ProbabilityRule
from validation_lab.online_pln_cases import World as FrozenWorld

ROOT = Path(__file__).resolve().parents[1]


def configuration():
    return json.loads((ROOT/'reviews/goal-directed-online-pln-v1/fixtures.json').read_text())


class World(FrozenWorld):
    def setup(self, session, *, rename=False, reverse=False):
        self.session = session
        self.pending = {}
        self.rename, self.reverse = rename, reverse
        s, family, variant = session, self.fixture['family'], self.fixture['variant']
        s.emit('fact', name='tested', valid_until=None)
        s.emit('fact', name='credential', valid_until=None)
        def report(name, literal, truth, roots=None, adopt=True):
            evidence = Evidence(name, s.initial.context_id, literal, 'forecast-model',
                s.service.snapshot(s.initial.context_id).logical_time, tuple(roots or ('root:'+name,)))
            numeric = ProbabilityReport(name, truth)
            s.receive_report(evidence, numeric)
            if adopt:
                result = s.numeric('adopt', name, label='initial-report-adoption')
                if result['status'] != 'PASS':
                    raise AssertionError(result)
                return result['commit'].belief
            return evidence, numeric
        self.report = report
        if family == 'lifecycle':
            report('forecast-received', s.forecast, TruthValue(.7,.8))
            if variant == 'monitor':
                # Initial accepted operation and exact observed product, via the same
                # public gates. This is initial state, not a selected-work shortcut.
                assert s.reserve()['status'] == 'PASS'
                assert s.emit('dispatch', attempt_id='attempt', fault='none')['outcome']['status'] == 'PASS'
                s.emit('tick', time=1)
                s.publish_probe(Probe('product', 'executor', 'product', s.initial.product_id, ('acknowledged',)))
                assert s.request(s.probes['product'])['status'] == 'PASS'
                s.emit('account')
                s.publish_probe(Probe('health','monitor','health',s.initial.product_id,('exact_product',),opportunity=1))
            return
        def rule(name, p,q,r):
            # Reverse lexical identities in diagnostics; no desired-outcome priority.
            name = ''.join(chr(219-ord(c)) if 'a'<=c<='z' else c for c in name) if rename else name
            return ProbabilityRule(name,'1',DeductionRule(p,q,r))
        if family == 'composition':
            if variant == 'three':
                rules = [rule('b-step1','tested','u','v'), rule('c-step2','tested','v','w'),
                         rule('d-target','tested','w','healthy')]
            else:
                rules = [rule('b-step1','tested','u','v'), rule('d-target','tested','v','healthy')]
                if variant == 'alternatives':
                    rules.append(rule('c-other','tested','w','healthy'))
            strengths, confidence = (.5,.5,.5,.8,.8), .95
        else:
            rules = [rule('z-route','tested','staged','healthy')]
            strengths, confidence = (.4,.5,.6,.7,.8), .8
            if family == 'selection' and variant in ('distractors','shared'):
                rules.append(rule('a-shared','tested','staged','unused'))
                if variant == 'distractors':
                    rules.append(rule('a-separate','i','j','k'))
        values = {}
        conclusions = {r.deduction.conclusion for r in rules}
        for r in rules:
            s.register_rule(r)
            for literal, strength in zip(r.deduction.premises, strengths):
                if literal in conclusions:
                    continue  # intermediate numerical result must actually be inferred
                if literal in values and values[literal] != strength:
                    raise AssertionError('incompatible shared premise definition')
                values[literal] = strength
        missing = None
        if (family == 'selection' and variant != 'control') or family == 'composition' or variant == 'blocked':
            missing = rules[0].deduction.premises[-1]
        ordered = list(values.items())
        if reverse:
            ordered.reverse()
        # IDs based on semantic literal, stable across receipt order.
        for literal, strength in ordered:
            from experimental_online_pln.agenda import digest
            name = 'report-'+digest(literal)[:12]
            truth = TruthValue(strength, confidence)
            if literal == missing:
                probe = Probe('source-report','forecast-model','numeric',literal)
                self.pending[probe.probe_id] = (name,literal,truth)
                s.publish_probe(probe)
            else:
                report(name,literal,truth)
        if variant == 'alternatives':
            report('alternative-support', rules[0].deduction.premises[0],TruthValue(.5,.95))
        if variant == 'blocked':
            report('current-opposite', s.forecast.negate(), TruthValue(.7,.8))
            report('received-unfavorable', s.forecast, TruthValue(.2,.2), adopt=False)
        if family == 'changes' and variant in ('replacement','producer'):
            s.after_proposal = self.change

    def change(self, session, transition, proposal):
        if self.triggered or transition.kind != 'deduction':
            return
        self.triggered = True
        if self.fixture['variant'] == 'replacement':
            selected = next(b for v in session.read().numerical for b in v.current
                            if b.belief_revision_id == transition.premise_revision_ids[0])
            session.emit('revoke', evidence_id=selected.proposal.support.evidence_ids[0])
            self.report('replacement',selected.proposal.support.conclusion,selected.proposal.support.truth,adopt=False)
        else:
            old = session.rules[transition.rule_id]
            session.register_rule(ProbabilityRule(old.rule_id,'2',DeductionRule('tested','staged','other-output')),'1')
            session.register_rule(ProbabilityRule('new-producer','1',old.deduction))
        self.seams.append(dict(kind='after-proposal-before-postcheck',variant=self.fixture['variant'],
                               transition=wire(transition),proposal=wire(proposal)))

    def acquire(self, probe):
        if probe.report_type == 'numeric':
            if self.fixture['variant'] == 'blocked':
                return dict(status='UNKNOWN',detail='source responded unavailable')
            name,literal,truth = self.pending[probe.probe_id]
            return dict(status='PASS',numeric=(Evidence(name,self.session.initial.context_id,literal,probe.source,
                self.session.service.snapshot(self.session.initial.context_id).logical_time,('root:'+name,)),
                ProbabilityReport(name,truth)))
        return super().acquire(probe)

    def after(self, candidate, result):
        super().after(candidate, result)
        if candidate.kind == 'complete' and result['status'] == 'PASS' and self.fixture['variant'] == 'reopen':
            self.later_failure = True
            self.session.emit('tick',time=4)
            self.session.publish_probe(Probe('health','monitor','health',self.session.initial.product_id,
                                            ('exact_product',),opportunity=4))
            self.seams.append(dict(kind='continuing-monitor-after-completion',logical_tick=4))
