"""Sealed exact replay, independent route checks, final journal and recorded arithmetic."""
import json,shutil
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from experimental_online_pln.agenda import Snapshot,wire
from experimental_work_loop.consumer import Consumer
from experimental_work_bridge.capture import detached
from experimental_work_bridge.project import project
from experimental_obligations.capture import capture,immutable
from experimental_obligations.evaluate import evaluate
from work_bridge_lab.reference import validate
from obligations_lab.reference import frozen,qualified
from reachability.service import AdmissionService
from reachability.probability_formula import PinnedFormulaRuntime
from reachability.pln_adapter import TruthValue
from validation_lab.audit_pressure_comparison import artifact_path
from .cases import manifest,configuration,PARENTS
from .compare import inputs,readable
from .reference import check_episode,require


def equal(a,b,reason):
    if a!=b:raise ValueError('audit differs: '+reason)


def audit(directory,allow_dirty=False):
    root=Path(directory)
    def load(n):return json.loads(artifact_path(root,n).read_text())
    seal=load('bundle.json');files={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='bundle.json' and not p.name.endswith(('.lock','-wal','-shm'))}
    equal(files,set(seal['files']),'file inventory')
    for n,h in seal['files'].items():equal(sha256(artifact_path(root,n).read_bytes()).hexdigest(),h,'artifact '+n)
    source=load('sources.json');equal(source['files'],inputs(),'auditor source')
    if not allow_dirty:equal(source['dirty_inputs'],[],'committed source')
    for n,h in source['files'].items():equal(sha256(artifact_path(root,'source/'+n).read_bytes()).hexdigest(),h,'archived source')
    cfg=load('configuration.json');equal(cfg,configuration(),'preregistered configuration');report=load('report.json');equal(report['sources'],source,'report source');equal(report['conformance'],'PASS','final cohort conformance')
    expected=[(mode,parent) for mode in cfg['modes'] for parent in PARENTS];equal([(r['mode'],r['parent']) for r in report['results']],expected,'twelve episodes')
    total_rows=selections=formulas=native_calls=stale=0
    for result in report['results']:
        name=result['mode']+'-'+result['parent'];equal(load(name+'/result.json'),result,'episode result')
        rows=[json.loads(line) for line in artifact_path(root,name+'/trace.jsonl').read_text().splitlines()];check_episode(result['parent'],rows,result)
        consumer=Consumer();m=manifest(result['parent']);flattened=[]
        for i,row in enumerate(rows):
            equal(row['index'],i,'row order');snapshot=Snapshot.from_records(row['public_records']);frame=detached(row['frame']);cap=immutable(frame.data()['capture'])
            ab={k:evaluate(cap,m,k)[0] for k in ('A','B')};view,_=project(frame,m,ab['A'],ab['B']);equal(view.data(),row['view'],'exact frozen work view');validate(frame,m,ab['A'],ab['B'],view)
            equal(ab['A'].data()['numerical_status'],frozen(cap.data()),'independent numerical A')
            equal(ab['B'].data()['numerical_status'],qualified(cap.data(),m)[0],'independent numerical B')
            frontier,selected,choice=consumer.choose(snapshot,view)
            f=wire(frontier);recorded=dict(row['frontier']);f.pop('elapsed_ns');recorded.pop('elapsed_ns');equal(f,recorded,'complete public frontier')
            c=dict(choice);recorded=dict(row['choice']);c.pop('selection_elapsed_ns');recorded.pop('selection_elapsed_ns');equal(c,recorded,'work selection and finite review')
            equal(wire(selected),row['selected'],'FIFO choice');total_rows+=1
            if selected is None:equal(consumer.stop,row['stop'],'explained stop');continue
            selections+=1;flattened.extend(row['calls']);stale+=row['result']['status']=='STALE'
            equal(row['before_environment'],rows[i+1]['before'] if not row['environment_events'] else row['before_environment'],'no unrecorded between-step changes')
            equal(row['after'],rows[i+1]['before'],'next public outcome')
            if selected.kind in ('deduction','revision') and row['result']['status']=='PASS':
                equal(row['result']['commit']['belief']['proposal'],row['result']['proposal'],'committed certified proposal')
                equal(len(row['calls']),1,'one runtime evaluation per selected formula')
                equal(row['calls'][0]['result'],row['result']['proposal']['support']['truth'],'actual formula conclusion')
        equal(flattened,result['runtime_calls'],'only selected calls; no setup formulas');equal(result['setup_formula_calls'],0,'no forced setup inference')
        equal((consumer.selections,consumer.work,consumer.acquisitions),(result['selections'],result['work'],result['acquisitions']),'charged budgets')
        equal(result['reconstruction']['native_calls_before'],result['reconstruction']['native_calls_after'],'no inference at reconstruction')
        for call in flattened:
            equal(call['status'],'PASS','actual formula execution');expected_value=PinnedFormulaRuntime().evaluate(call['formula'],tuple(TruthValue(**v) for v in call['inputs']));equal(wire(expected_value),call['result'],'independent recorded arithmetic');formulas+=1
            if result['mode']=='native':equal(call['mode'],'native','no finite substitution');equal(call['formula_agreement'],True,'native arithmetic');native_calls+=1
        with TemporaryDirectory() as tmp:
            db=Path(tmp)/'admission.db';shutil.copyfile(artifact_path(root,name+'/admission.db'),db)
            with AdmissionService(database=db) as service:
                actual,_=capture(service);equal(actual,immutable(rows[-1]['frame']['capture']),'final authoritative capture')
                equal(wire(service.inspect_goal('goal')),rows[-1]['view']['observed']['goal'],'observed goal')
                equal(wire(service.inspect_lifecycle('episode')),rows[-1]['view']['observed']['lifecycle'],'observed lifecycle')
                for row in rows:
                    if row.get('result',{}).get('commit',{}).get('status')=='PASS':
                        belief=row['result']['commit']['belief'];found=[wire(b) for q in service.export_probability('ctx')[3] for b in q.historical if b.belief_revision_id==belief['belief_revision_id']]
                        equal(found,[belief],'selected commit exists in authoritative journal')
    equal((root/'COMPARISON.md').read_text(),readable(report),'readable comparison')
    return dict(status='PASS',revision=source['revision'],development_allow_dirty=allow_dirty,episodes=12,rows=total_rows,selections=selections,authority_reconstructions=12,
        formula_calls=formulas,new_native_formula_calls=native_calls,stale_requests=stale,limitation='Source/selection/receipt conformance and recorded arithmetic replay; not fresh native execution, independent environment truth, authentication or empirical safety.')
