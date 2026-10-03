"""Eight fixed engineering parents. No fixture or future event reaches discovery."""
from dataclasses import replace
from goal_pln_lab.cases import World as GoalWorld,configuration
from experimental_online_pln.agenda import Probe,wire
from reachability.pln_adapter import DeductionRule,TruthValue
from reachability.probability_model import ProbabilityRule

PARENTS=(
 dict(id='control',base='route-control',theme='simple positive control'),
 dict(id='distractors',base='route-distractors',theme='distractors and shared inputs'),
 dict(id='alternatives',base='path-alternatives',theme='AND premises and OR producers'),
 dict(id='shared-intermediate',base='path-two',theme='shared useful intermediate'),
 dict(id='closed-sinks',base='route-control',theme='intentionally adverse closed-use observation sinks'),
 dict(id='eviction-chain',base='path-three',theme='eviction and repeated exact premise inspection'),
 dict(id='changed-support',base='change-replacement',theme='equal-valued replacement and new producer'),
 dict(id='monitor-reopen',base='supported-reopen',theme='wrong product and later monitoring failure'),
)


class World(GoalWorld):
    def __init__(self,parent):
        self.parent=parent
        super().__init__(next(dict(f) for f in configuration()['fixtures'] if f['id']==parent['base']))
    def setup(self,session,*,rename=False,reverse=False):
        super().setup(session,rename=rename,reverse=reverse)
        if self.parent['id']=='shared-intermediate':
            # Reuse the first real deduction as a shared premise of two routes.
            rule=ProbabilityRule('e-alternative','1',DeductionRule('tested','v','healthy'))
            session.register_rule(rule)
        if self.parent['id']=='closed-sinks':
            for index in range(4):
                session.publish_probe(Probe('closed-'+str(index),'forecast-model','numeric',session.forecast,
                    ('exact_product',) if index%2 else (),availability='unknown' if index%2 else 'unavailable'))
    def change(self,session,transition,proposal):
        old_trigger=self.triggered
        super().change(session,transition,proposal)
        if not old_trigger and self.triggered:
            old=session.rules[transition.rule_id]
            session.register_rule(ProbabilityRule('outside-new-producer','1',old.deduction))
            self.seams.append(dict(kind='new-producer-after-equal-replacement',rule='outside-new-producer'))
    def acquire(self,probe):
        if self.parent['id']=='closed-sinks' and probe.probe_id.startswith('closed-'):
            # A precondition may become satisfied later. Inspection still cannot
            # fabricate a numerical report from this deliberately unhelpful source.
            return dict(status='UNKNOWN',detail='inspection source has no numerical report')
        if self.parent['id']=='monitor-reopen' and probe.report_type=='product' and self.product_requests==0:
            self.product_requests+=1
            return dict(status='PASS',events=(('observation',dict(attempt_id='attempt',product_id='artifact-v1',milestone='exact_product_observed')),))
        return super().acquire(probe)
