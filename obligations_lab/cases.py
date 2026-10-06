"""Declared semantic diagnostics created solely through existing public authority."""
from pathlib import Path
import json
from experimental_native_recall.session import Session
from experimental_online_pln.agenda import wire
from reachability.model import Evidence
from reachability.pln_adapter import DeductionRule,TruthValue
from reachability.probability_model import ProbabilityPolicy,ProbabilityReport,ProbabilityRule,ProbabilityIndependence
from experimental_obligations.capture import capture,state_digest

ROOT=Path(__file__).resolve().parents[1]
PARENTS=('adequate-direct','weak-augmented','only-weak','missing-mandatory','objections','lineage-copies','revision-family','freshness','scope-bounds','adverse-inference','historical-anchor')


def manifests():return json.loads((ROOT/'reviews/decision-obligations-shadow-v1/interpretations.json').read_text())


def setup(directory,native=False):
    s=Session(directory,native=native);s.emit('fact',name='tested',valid_until=None);s.emit('fact',name='credential',valid_until=None)
    s.service.configure_probability_policy('ctx',ProbabilityPolicy('semantic-input/v1',('forecast-model','source-a','source-b','unclassified-source')),expected_revision='1',idempotency_key=s.key())
    return s


def report(s,name='a',strength=.7,confidence=.8,source='source-a',root='root:a',literal=None):
    e=Evidence(name,'ctx',literal or s.forecast,source,s.service.snapshot('ctx').logical_time,(root,));s.receive_report(e,ProbabilityReport(name,TruthValue(strength,confidence)))
    result=s.numeric('adopt',name)
    if result['status']!='PASS':raise AssertionError(result)
    return result['commit'].belief


def prepare_inference(s,objection=False):
    name='r-objection' if objection else 'r-estimate';rule=ProbabilityRule(name,'1',DeductionRule('tested','weak','healthy'));s.register_rule(rule)
    strengths=(.5,.5,.1,.8,.1) if objection else (.4,.5,.6,.7,.8)
    bs=[report(s,'input-'+str(i),strength,.05 if i in (1,3,4) or objection else .8,'forecast-model','root:input-'+str(i),lit) for i,(lit,strength) in enumerate(zip(rule.deduction.premises,strengths))]
    return name,tuple(b.belief_revision_id for b in bs)


def infer(s,objection=False,prepared=None):
    name,premises=prepared or prepare_inference(s,objection)
    result=s.numeric('deduction',name,premises)
    if result['status']!='PASS':raise AssertionError(result)
    return result


def snapshot(s,label,variant_names=('alternatives',)):
    before=state_digest(s.service);value,costs=capture(s.service);assert state_digest(s.service)==before
    return dict(label=label,capture=value,costs=costs,manifests=variant_names,nonmutation=dict(before=before,after=state_digest(s.service)))


def goal_outcome(s):
    # Observe outcomes separately from knowledge-sensitive diagnostic fingerprints.
    view=s.service.inspect_goal('goal');projection=view.projection
    return dict(episode=wire(view.episode),history=wire(view.history),
                samples=wire(tuple(s.service._goals.samples.values())),
                outstanding_loss=projection.outstanding_loss,
                estimated_coverage=projection.estimated_committed_coverage,
                open_loss=projection.open_loss,
                slices=[dict(id=v.slice_id,loss=v.outstanding_loss,samples=wire(v.samples)) for v in projection.slices])


def construct(parent,directory,native=False):
    s=setup(directory,native);rows=[];temporal=[]
    try:
        if parent not in ('only-weak','revision-family'):report(s)
        if parent in ('adequate-direct','scope-bounds'):rows.append(snapshot(s,'base'))
        elif parent=='weak-augmented':
            prepared=prepare_inference(s);rows.append(snapshot(s,'before'));infer(s,prepared=prepared);rows.append(snapshot(s,'after',('alternatives','mandatory_method','all_assessments')))
        elif parent=='only-weak':infer(s);rows.append(snapshot(s,'weak',('alternatives','mandatory_method')))
        elif parent=='missing-mandatory':rows.append(snapshot(s,'missing',('alternatives','two_sources','required_model')))
        elif parent=='objections':
            report(s,'outside',.2,.05,'source-b','root:b');rows.append(snapshot(s,'outside'))
            s.emit('revoke',evidence_id='outside');report(s,'opposite',.7,.05,'source-b','root:b',s.forecast.negate());rows.append(snapshot(s,'opposite'))
        elif parent=='lineage-copies':
            rows.append(snapshot(s,'one',('alternatives','two_sources')))
            report(s,'renamed-a');report(s,'copied-b',source='source-b');rows.append(snapshot(s,'copies',('alternatives','two_sources')))
            s.emit('revoke',evidence_id='copied-b');report(s,'lawful-b',source='source-b',root='root:b');rows.append(snapshot(s,'distinct-root',('alternatives','two_sources')))
        elif parent=='revision-family':
            a=report(s,confidence=.2);b=report(s,'b',source='source-b',root='root:b');rows.append(snapshot(s,'parents',('alternatives','all_assessments','required_model')))
            s.register_model(ProbabilityIndependence('model-ab','ctx',(a.belief_revision_id,b.belief_revision_id),'declared independent measurement channels for this constructed fixture'))
            result=s.numeric('revision','model-ab',tuple(sorted((a.belief_revision_id,b.belief_revision_id))))
            if result['status']!='PASS':raise AssertionError(result)
            rows.append(snapshot(s,'parents-and-child',('alternatives','all_assessments','required_model')))
        elif parent=='freshness':
            rows.append(snapshot(s,'before'))
            s.emit('revoke',evidence_id='a');rows.append(snapshot(s,'sole-revoked'));report(s,'equal-replacement');rows.append(snapshot(s,'replacement'))
            report(s,'survivor',source='source-b',root='root:b');s.emit('revoke',evidence_id='equal-replacement');rows.append(snapshot(s,'surviving-alternative'))
        elif parent=='adverse-inference':
            prepared=prepare_inference(s,True);rows.append(snapshot(s,'before'));before=goal_outcome(s);evidence=wire(tuple(s.service._evidence.values()));infer(s,True,prepared);after=goal_outcome(s);assert before==after;assert evidence==wire(tuple(s.service._evidence.values()))
            rows.append(snapshot(s,'after'));temporal.append(dict(external_observations_unchanged=True,evidence_before=evidence,evidence_after=wire(tuple(s.service._evidence.values())),goal_before=before,goal_after=after,executor_effects=s.executor.total_effects,goal_outstanding=after['outstanding_loss']))
        else:raise ValueError(parent)
        reconstruction=s.project_and_reopen() if native else None
        return rows,dict(reconstruction=wire(reconstruction),runtime_calls=wire(s.runtime.calls),costs_ns=dict(s.costs),receipts=wire(s.receipts),temporal=temporal,executor_effects=s.executor.total_effects,goal=wire(s.service.inspect_goal('goal')))
    finally:s.close()
