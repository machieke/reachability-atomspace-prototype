"""Existing sealed replay plus independent physical and admitted-observation checks."""
import json,shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from hashlib import sha256
from experimental_online_pln.agenda import Snapshot,wire
from experimental_multihop.consumer import Consumer
from experimental_work_bridge.capture import detached
from experimental_multihop.project import project
from experimental_obligations.capture import capture,immutable
from experimental_obligations.evaluate import evaluate
from obligations_lab.reference import frozen,qualified
from .reference import graph as graph_check,final as dependency_check
from work_loop_lab.reference import check_step
from work_loop_lab.audit import equal
from reachability.service import AdmissionService
from reachability.simulated_executor import SimulatedExecutor
from reachability.goal_logic import evaluate_durability
from reachability.probability_formula import PinnedFormulaRuntime
from reachability.pln_adapter import TruthValue
from validation_lab.audit_pressure_comparison import artifact_path
from .cases import configuration,manifest,PARENTS,specification,fixture
from .compare import inputs,readable
from world_lab.reference import validate,public_boundary


def audit(directory,allow_dirty=False):
    root=Path(directory)
    def load(n):return json.loads(artifact_path(root,n).read_text())
    seal=load('bundle.json');names={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='bundle.json' and not p.name.endswith(('.lock','-wal','-shm'))}
    equal(names,set(seal['files']),'sealed file inventory')
    for n,h in seal['files'].items():equal(sha256(artifact_path(root,n).read_bytes()).hexdigest(),h,'artifact '+n)
    source=load('sources.json');equal(source['files'],inputs(),'auditor source')
    if not allow_dirty:equal(source['dirty_inputs'],[],'committed measured inputs')
    for n,h in source['files'].items():equal(sha256(artifact_path(root,'source/'+n).read_bytes()).hexdigest(),h,'archived source')
    cfg=load('configuration.json');equal(cfg,configuration(),'preregistered environment');report=load('report.json');equal(report['sources'],source,'report source');equal(report['conformance'],'PASS','cohort conformance')
    equal([(r['mode'],r['parent']) for r in report['results']],[(mode,p) for mode in cfg['modes'] for p in PARENTS],'twelve core executions')
    counts=dict(episodes=0,physical_ticks=0,public_rows=0,selections=0,formula_calls=0,native_formula_calls=0,admitted_goal_predicate_replays=0,physical_samples=0,executor_reconstructions=0,authority_certificates=0)
    for result in report['results']:
        name=result['mode']+'-'+result['parent'];equal(result,load(name+'/result.json'),'result binding');private=load(name+'/private.json');ticks=load(name+'/ticks.json');spec=specification(result['parent']);equal(private['spec'],spec,'private environment declaration')
        validate(spec,cfg,ticks,private,result,core=False);counts['episodes']+=1;counts['physical_ticks']+=len(ticks)
        rows=[json.loads(l) for l in artifact_path(root,name+'/trace.jsonl').read_text().splitlines()];initial=load(name+'/initial.json');initial_public=Snapshot.from_records(initial['public_records']);equal(initial['setup_formula_calls'],0,'no forced setup formula')
        received=load(name+'/received.json');consumer=Consumer();m=manifest(result['parent']);calls=[];attempts=set();snapshots=[];measurement_ids=[]
        for index,row in enumerate(rows):
            equal(row['index'],index,'row sequence');public=Snapshot.from_records(row['public_records']);snapshots.append(public);public_boundary(public,initial_public.contracts)
            equal(wire(public.received),received[:len(public.received)],'only actually received public events')
            equal(public.context.logical_time,row['tick'],'public clock');equal(public.binding,row['public_binding'],'public binding')
            frame=detached(row['frame']);cap=immutable(frame.data()['capture']);ab={k:evaluate(cap,m,k)[0] for k in ('A','B')};view,_=project(frame,m,ab['A'],ab['B']);equal(view.data(),row['view'],'frozen work projection');graph_check(public,m,view.data())
            equal(ab['A'].data()['numerical_status'],frozen(cap.data()),'independent A');equal(ab['B'].data()['numerical_status'],qualified(cap.data(),m)[0],'independent B')
            frontier,selected,choice=consumer.choose(public,view);a=wire(frontier);b=dict(row['frontier']);a.pop('elapsed_ns');b.pop('elapsed_ns');equal(a,b,'whole public frontier')
            a=dict(choice);b=dict(row['choice']);a.pop('selection_elapsed_ns');b.pop('selection_elapsed_ns');equal(a,b,'persistent unchanged consumer state');equal(wire(selected),row['selected'],'unchanged FIFO selection');check_step(row,attempts);counts['public_rows']+=1
            if selected is None:equal(consumer.stop,row['stop'],'consumer stop');continue
            counts['selections']+=1;calls.extend(row['calls']);equal(row['revalidation']['public_binding'],public.binding,'no unrecorded pre-execution event');equal(row['revalidation']['member'],True,'current frontier member')
            if selected.kind=='request':
                offset=row['measurement_offset'];measurement=private['measurements'][offset];measurement_ids.append(offset)
                events=[r for r in row['received'] if r['kind']=='acquisition'];equal(len(events),1,'one actual port result');equal(events[0]['descriptor'],measurement['probe'],'actual requested descriptor');equal(events[0]['response'],measurement['response'],'actual source response')
                equal(measurement['time'],row['tick'],'request sample time');counts['physical_samples']+=measurement['sample'] is not None
            if selected.kind in ('deduction','revision') and row['result']['status']=='PASS':
                by_id={b.belief_revision_id:b for q in public.numerical for b in q.current};equal(row['calls'][0]['inputs'],[wire(by_id[i].proposal.support.truth) for i in selected.premise_ids],'exact ordered formula inputs')
        equal(measurement_ids,list(range(len(private['measurements']))),'no hidden or dropped queries')
        equal(calls,result['runtime_calls'],'only selected runtime calls');equal((consumer.selections,consumer.work,consumer.acquisitions),(result['selections'],result['work'],result['acquisitions']),'no budget reset across ticks')
        for tick in ticks:
            subset=rows[tick['row_start']:tick['row_end']];equal([r['slot'] for r in subset],list(range(len(subset))),'per-tick ordering');equal([r['tick'] for r in subset],[tick['time']]*len(subset),'tick grouping')
            if len(subset)>cfg['max_operations_per_tick']:raise AssertionError('per-tick bound')
            equal(subset[-1]['after'],tick['authority_after'],'actual end-tick authority')
            expected=[]
            for channel,source_id,pre in (('product','executor',['acknowledged']),('health','monitor',['exact_product'])):
                if tick['time'] in cfg['public_opportunities'][channel]:expected.append(dict(probe_id=channel,source=source_id,report_type=channel,target='artifact-v2',preconditions=pre,opportunity=tick['time'],cost=1,availability='unknown'))
            equal(tick['public_event'],dict(time=tick['time'],clock=tick['time'],probes=expected),'public opportunities do not reveal hidden state')
        for call in calls:
            equal(call['status'],'PASS','actual formula');equal(call['commit_status'],'PASS','accepted numerical commit');value=PinnedFormulaRuntime().evaluate(call['formula'],tuple(TruthValue(**t) for t in call['inputs']));equal(wire(value),call['result'],'recorded arithmetic');counts['formula_calls']+=1
            if result['mode']=='native':equal(call['mode'],'native','no substitution');equal(call['formula_agreement'],True,'native agreement');counts['native_formula_calls']+=1
        with TemporaryDirectory() as tmp:
            local=Path(tmp)/'admission.db';remote=Path(tmp)/'executor.db';shutil.copyfile(artifact_path(root,name+'/admission.db'),local);shutil.copyfile(artifact_path(root,name+'/executor.db'),remote)
            with AdmissionService(database=local) as service,SimulatedExecutor(remote) as executor:
                actual,_=capture(service);equal(actual,immutable(rows[-1]['frame']['capture']),'final authority capture');equal(wire(service.inspect_goal('goal')),rows[-1]['view']['observed']['goal'],'actual goal');equal(wire(service.inspect_lifecycle('episode')),rows[-1]['view']['observed']['lifecycle'],'historical lifecycle')
                equal(executor.total_effects,result['effects'],'actual executor effects');counts['executor_reconstructions']+=1
                equal(len(private['state']['accepted']),result['effects'],'one physical link per actual accepted effect')
                if result['effects']:
                    dispatch=service.inspect_dispatch('attempt');request=dispatch.dispatch.request;receipt=executor.query(request)
                    accepted=private['state']['accepted'][0]
                    equal(accepted['request'],wire(request),'exact physical request');equal(accepted['receipt'],wire(receipt),'actual effect independent of ACK');equal(accepted['due'],accepted['accepted_at']+spec['delay'],'scheduled effect time')
                    dispatch_rows=[r for r in rows if r['selected'] and r['selected']['kind']=='dispatch'];equal(accepted['accepted_at'],dispatch_rows[0]['tick'],'actual acceptance time')
                equal(sum(x['new_link'] for x in private['effect_links']),result['effects'],'idempotent physical link')
                for row in rows:
                    if row['selected'] and row['selected']['kind'] in ('adopt','deduction','revision') and row['result']['status']=='PASS':
                        r=row['result'];belief=r['commit']['belief'];equal(wire(service._probability.beliefs[belief['belief_revision_id']]),belief,'actual committed numerical record/roots')
                        for kind in ('pre','post'):equal(wire(service._probability.certificates[r[kind]['certificate_id']]),r[kind],'actual numerical certificate')
                samples=tuple(service._goals.samples.values())
                for public in snapshots:
                    contract=next(c[2] for c in public.contracts if c[:2]==('registered-content/v1','goal_contract'));item=contract.slices[0];recorded=public.goal.projection.slices[0]
                    usable=frozenset(b.belief_revision_id for b in public.context.usable)
                    known=[];sample_time=0
                    for event in public.received:
                        if event.get('outcome',{}).get('status')!='PASS':continue
                        if event['kind']=='tick':sample_time=event['arguments']['time']
                        if event['kind']=='sample':
                            matched=[x for x in samples if x.observed_at==sample_time and x.healthy==event['arguments']['healthy']]
                            equal(len(matched),1,'exact historical admitted sample');known.append(matched[0])
                    cold=evaluate_durability(item.durability,public.goal.episode.monitors[0],tuple(known),usable,public.context.logical_time,recorded.condition.status)
                    equal(cold.label,recorded.label,'frozen goal predicate from actual admitted samples');equal(wire(cold.samples),wire(recorded.samples),'exact observation witnesses');equal(recorded.outstanding_loss,0 if cold.label=='OBSERVED_SUCCESS' else item.loss,'observation-based loss');counts['admitted_goal_predicate_replays']+=1
                for sample in samples:
                    matched=[m for m in private['measurements'] if m['time']==sample.observed_at and m['sample'] and m['sample']['channel']=='health' and m['response']['status']=='PASS'];equal(len(matched),1,'one admitted instantaneous health sample');equal(sample.healthy,matched[0]['sample']['value'],'admitted truthful health polarity')
                certificates={kind:wire(tuple(store[k] for k in sorted(store))) for kind,store in (
                    ('hard',service._certificates),('probability',service._probability.certificates),
                    ('execution',service._execution.permits),('completion',service._completion.permits))}
                equal(certificates,load(name+'/authority-certificates.json'),'all actual persisted certificates')
                counts['authority_certificates']+=sum(map(len,certificates.values()))
        equal(result['dependency_reference'],dependency_check(fixture(result['parent']),initial,rows,result,load(name+'/changes.json')),'independent ancestry, source and invalidation reference')
        equal(result['reconstruction']['authority_equal'],True,'authority reopen');equal(result['reconstruction']['native_calls_before'],result['reconstruction']['native_calls_after'],'no formula on reopen')
        if result['mode']=='native':equal(result['reconstruction']['projection_equal'],True,'native projection boundary')
    equal((root/'COMPARISON.md').read_text(),readable(report),'readable outcomes')
    return dict(status='PASS',revision=source['revision'],development_allow_dirty=allow_dirty,**counts,limitation='Bounded structural/ancestry/fixture witness, physical recurrence and actual admitted-observation replay; not fresh native execution during audit, real-world truth or calibrated safety.')
