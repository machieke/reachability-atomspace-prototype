"""Preregistered engineering cases; never imported by the coordinator."""
from attention_lab.cases import World as PreviousWorld
from reachability.pln_adapter import DeductionRule,TruthValue
from reachability.probability_model import ProbabilityRule

PARENTS=(
 dict(id='alternatives',base='path-alternatives',cohort='diagnostic'),
 dict(id='shared-intermediate',base='path-two',cohort='diagnostic'),
 dict(id='ready-broad',base='route-control',cohort='constructed'),
 dict(id='missing-upstream',base='path-two',cohort='constructed'),
 dict(id='unproductive-early',base='route-control',cohort='constructed'),
 dict(id='evicted-alternatives',base='path-alternatives',cohort='constructed'),
 dict(id='refreshed-competing',base='change-replacement',cohort='constructed'),
 dict(id='monitor-competition',base='supported-reopen',cohort='constructed'),
)


class World(PreviousWorld):
    def setup(self,session,**kwargs):
        super().setup(session,**kwargs);name=self.parent['id']
        if name in ('ready-broad','monitor-competition'):
            for i in range(3):session.register_rule(ProbabilityRule('zz-branch-'+str(i),'1',DeductionRule('tested','fan'+str(i),'healthy')))
        if name=='missing-upstream':
            session.register_rule(ProbabilityRule('a-input-alternative','1',DeductionRule('tested','bridge','v')))
        if name=='unproductive-early':
            rule=ProbabilityRule('a-low-yield','1',DeductionRule('tested','weak','healthy'));session.register_rule(rule)
            for slot,strength in ((1,.5),(3,.7),(4,.8)):
                self.report('weak-input-'+str(slot),rule.deduction.premises[slot],TruthValue(strength,.05))
            self.report('direct-received',session.forecast,TruthValue(.7,.8),adopt=False)
        if name=='evicted-alternatives':
            literal=session.rules['b-step1'].deduction.premises[0]
            for i in range(5):self.report('additional-shared-'+str(i),literal,TruthValue(.5,.95))
        if name=='refreshed-competing':
            session.register_rule(ProbabilityRule('zz-start','1',session.rules['z-route'].deduction))
    def acquire(self,probe):
        if self.parent['id']=='monitor-competition' and probe.report_type=='product' and self.product_requests==0:
            self.product_requests+=1
            return dict(status='PASS',events=(('observation',dict(attempt_id='attempt',product_id='artifact-v1',milestone='exact_product_observed')),))
        return super().acquire(probe)
