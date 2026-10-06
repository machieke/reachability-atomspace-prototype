"""Six fixed controlled event sequences; projector never sees future events."""
import copy,json
from pathlib import Path
from dataclasses import replace
from experimental_work_bridge.capture import acquire,detached,digest
from experimental_work_bridge.project import project,Limits
from experimental_obligations.capture import immutable,state_digest
from experimental_obligations.evaluate import evaluate
from experimental_online_pln.agenda import Probe,wire
from obligations_lab.cases import setup,report,prepare_inference,infer,goal_outcome
from reachability.probability_model import ProbabilityIndependence,ProbabilityRule
from reachability.pln_adapter import DeductionRule

ROOT=Path(__file__).resolve().parents[1]
PARENTS=('method-gap','optional-weak','copied-source','freshness','objection','registry')
NATIVE=('method-gap','objection')
LAYOUT={
 'method-gap':{x:('primary','shared_method') for x in ('unregistered','registered','produced')},
 'optional-weak':{x:('primary','forecast_all','mandatory_weak') for x in ('before','after')},
 'copied-source':{x:('distinct_source',) for x in ('copied','lawful','withdrawn')},
 'freshness':{x:('distinct_source',) for x in ('initial','revoked','replaced','survivor')},
 'objection':{x:('primary',) for x in ('before','derived','opposite')},
 'registry':{x:('mandatory_weak',) for x in ('initial','registered','partial','complete','revised','unavailable')}}


def manifests():return json.loads((ROOT/'reviews/obligation-work-bridge-v1/task.json').read_text())


def probe(s,source='source-b',available='available',target=None):
    s.publish_probe(Probe('probe-'+source,source,'numeric',target or s.forecast,availability=available))


def model(s,a,b):
    return s.register_model(ProbabilityIndependence('model-ab','ctx',(a.belief_revision_id,b.belief_revision_id),'explicit existing independence declaration for synthetic distinct measurement roots'))


def revision(s):
    result=s.numeric('revision','model-ab',s.models['model-ab'].premise_revision_ids)
    if result['status']!='PASS':raise AssertionError(result)


def assess(frame,m):
    cap=immutable(frame.data()['capture']);out={};costs={}
    for kind in ('A','B'):out[kind],costs[kind]=evaluate(cap,m,kind)
    return out,costs


def observe(s,label,variants):
    before=state_digest(s.service);frame,costs=acquire(s);assert before==state_digest(s.service)
    return dict(label=label,variants=variants,frame=frame,acquisition_costs=costs)


def construct(parent,directory,native=False):
    s=setup(directory,native);rows=[];timeline=[]
    def save(label):rows.append(observe(s,label,LAYOUT[parent][label]))
    try:
        if parent=='method-gap':
            a=report(s,confidence=.2);b=report(s,'b',source='source-b',root='root:b');save('unregistered');model(s,a,b);save('registered');revision(s);save('produced')
        elif parent in ('optional-weak','objection'):
            a=report(s);b=report(s,'b',source='source-b',root='root:b');model(s,a,b);revision(s)
            prepared=prepare_inference(s,parent=='objection');save('before');before=goal_outcome(s);evidence=wire(tuple(s.service._evidence.values()));infer(s,parent=='objection',prepared)
            assert before==goal_outcome(s) and evidence==wire(tuple(s.service._evidence.values()))
            timeline.append(dict(evidence_before=evidence,evidence_after=wire(tuple(s.service._evidence.values())),goal_before=before,goal_after=goal_outcome(s)))
            save('after' if parent=='optional-weak' else 'derived')
            if parent=='objection':report(s,'opposite',.7,.05,'source-b','root:b',s.forecast.negate());save('opposite')
        elif parent=='copied-source':
            report(s);probe(s);report(s,'copy',source='source-b');save('copied');report(s,'lawful',source='source-b',root='root:b');save('lawful');s.emit('revoke',evidence_id='copy');save('withdrawn')
        elif parent=='freshness':
            report(s);report(s,'b',source='source-b',root='root:b');probe(s,'source-a');save('initial');s.emit('revoke',evidence_id='a');save('revoked')
            report(s,'replacement');save('replaced');report(s,'survivor');s.emit('revoke',evidence_id='replacement');save('survivor')
        elif parent=='registry':
            report(s);probe(s);save('initial');rule=ProbabilityRule('r-estimate','1',DeductionRule('tested','weak','healthy'));s.register_rule(rule);save('registered')
            values=(.4,.5,.6,.7,.8)
            for i in (0,1,3,4):report(s,'input-'+str(i),values[i],.05 if i in (1,3,4) else .8,'forecast-model','root:input-'+str(i),rule.deduction.premises[i])
            save('partial');report(s,'input-2',values[2],.8,'forecast-model','root:input-2',rule.deduction.premises[2]);save('complete')
            s.register_rule(replace(rule,revision='2'),expected_revision='1');save('revised');probe(s,available='unavailable');save('unavailable')
        else:raise ValueError(parent)
        reconstruction=s.project_and_reopen() if native else None
        final,_=acquire(s);assert final==rows[-1]['frame']
        return rows,dict(receipts=wire(s.receipts),runtime_calls=wire(s.runtime.calls),costs_ns=dict(s.costs),observed_final=final.data()['observed'],
                         executor_effects=s.executor.total_effects,timeline=timeline,reconstruction=wire(reconstruction),public_probes=wire(tuple(s.probes.values())))
    finally:s.close()


def diagnostics(row):
    for label in ('context','product','time','partial','bound'):
        frame=row['frame'];m=manifests()['mandatory_weak'];limits=Limits()
        if label=='context':m['context']='other-context'
        elif label=='product':m['product']='other-product'
        elif label=='time':m['time_window']=[1,2]
        elif label=='partial':d=frame.data();d['complete']=False;frame=detached(d)
        elif label=='bound':limits=Limits(nodes=0)
        yield dict(label='diagnostic-'+label,variants=('mandatory_weak',),frame=frame,acquisition_costs={},manifest=m,limits=limits,diagnostic=True)
