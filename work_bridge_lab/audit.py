"""Sealed replay, independent graph checks and reconstruction of existing authority."""
import json,shutil
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from reachability.service import AdmissionService
from reachability.probability_formula import PinnedFormulaRuntime
from reachability.pln_adapter import TruthValue
from experimental_online_pln.agenda import wire
from experimental_obligations.capture import capture,immutable,state_digest
from experimental_work_bridge.capture import detached
from experimental_work_bridge.project import project,Limits
from obligations_lab.reference import frozen,qualified
from validation_lab.audit_pressure_comparison import artifact_path
from .cases import assess,diagnostics,LAYOUT
from .compare import inputs,configuration,readable
from .reference import validate,expected_prefix


def equal(a,b,why):
    if a!=b:raise ValueError('audit differs: '+why)


def audit(directory,allow_dirty=False):
    directory=Path(directory)
    def load(n):return json.loads(artifact_path(directory,n).read_text())
    bundle=load('bundle.json');files={str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file() and p.name!='bundle.json' and not p.name.endswith(('.lock','-wal','-shm'))}
    equal(set(bundle['files']),files,'sealed inventory')
    for n,h in bundle['files'].items():equal(sha256(artifact_path(directory,n).read_bytes()).hexdigest(),h,'artifact '+n)
    source=load('sources.json');equal(source['files'],inputs(),'auditor source files')
    if not allow_dirty:equal(source['dirty_inputs'],[],'committed measured inputs')
    for n,h in source['files'].items():equal(sha256(artifact_path(directory,'source/'+n).read_bytes()).hexdigest(),h,'archived source '+n)
    cfg=load('configuration.json');equal(cfg,configuration(),'fixed task/cohort');report=load('report.json');equal(report['sources'],source,'source metadata')
    sessions=[('finite',p) for p in cfg['parents']]+[('native',p) for p in cfg['native']]
    equal([s['name'] for s in report['sessions']],[mode+'-'+p for mode,p in sessions],'bounded session inventory');expected=[]
    for mode,parent in sessions:
        rows=dict(LAYOUT[parent])
        if parent=='registry':rows.update({'diagnostic-'+x:('mandatory_weak',) for x in cfg['diagnostics']})
        expected += [mode+'-'+parent+'/'+label+'.'+variant+'.json' for label,variants in rows.items() for variant in variants]
    equal(report['index'],expected,'all declared event-prefix variants')
    view_count=nodes=edges=formulas=native_formulas=0
    for file in report['index']:
        e=load(file);equal(file,e['session']+'/'+e['label']+'.'+e['variant']+'.json','entry identity');equal(e['input_file'],e['session']+'/'+e['label']+'.input.json','prefix binding')
        frame=detached(load(e['input_file']));equal(frame.identity,e['input_identity'],'full input digest');m=e['manifest']
        if e['diagnostic']:
            base=dict(frame=detached(load('finite-registry/complete.input.json')))
            expected=next(r for r in diagnostics(base) if r['label']==e['label']);equal(frame,expected['frame'],'diagnostic input');equal(m,expected['manifest'],'diagnostic task');equal(e['limits'],expected['limits'].__dict__,'diagnostic bounds')
        else:equal(m,cfg['manifests'][e['variant']],'frozen task declaration');equal(e['limits'],cfg['limits'],'fixed graph bounds')
        ab,_=assess(frame,m);equal(e['assessments'],{k:v.data() for k,v in ab.items()},'frozen numerical assessments')
        replayed,_=project(frame,m,ab['A'],ab['B'],Limits(**e['limits']));equal(replayed.data(),e['view'],'exact work graph replay');validate(frame,m,ab['A'],ab['B'],replayed);expected_prefix(e['parent'],e['label'],e['variant'],replayed.data())
        if not e['diagnostic']:
            d=frame.data()['capture'];equal(ab['A'].data()['numerical_status'],frozen(d),'independent A');equal(frozen(d),d['live_criterion_statuses'][0],'live inspector');equal(ab['B'].data()['numerical_status'],qualified(d,m)[0],'independent B')
        view_count+=1;nodes+=len(e['view']['nodes']);edges+=len(e['view']['edges'])
    for s in report['sessions']:
        name=s['name'];receipt=load(name+'/receipts.json');last=load(name+'/'+s['last_authoritative_prefix']+'.input.json')
        equal(receipt['executor_effects'],0,'no effects from shadow');equal(last['observed'],receipt['observed_final'],'recorded goal/lifecycle')
        equal(last['inventory']['probes'],sorted(receipt['public_probes'],key=lambda p:p['probe_id']),'public probe receipt')
        for prefix in s['prefixes']:
            if not prefix['diagnostic']:
                proof=prefix['acquisition_costs']['nonmutation'];equal(proof['before'],proof['after'],'acquisition nonmutation')
        with TemporaryDirectory() as tmp:
            db=Path(tmp)/'admission.db';shutil.copyfile(artifact_path(directory,name+'/admission.db'),db)
            with AdmissionService(database=db) as service:
                before=state_digest(service);cap,_=capture(service);equal(cap,immutable(last['capture']),'final authoritative capture');equal(state_digest(service),before,'read-only SQLite replay')
                equal(wire(service.inspect_goal('goal')),last['observed']['goal'],'actual goal projection');equal(wire(service.inspect_lifecycle('episode')),last['observed']['lifecycle'],'actual lifecycle')
        for t in receipt['timeline']:equal(t['evidence_before'],t['evidence_after'],'inference adds no observations');equal(t['goal_before'],t['goal_after'],'inference adds no observed relief')
        if s['mode']=='native':
            r=receipt['reconstruction'];equal(r['authority_equal'],True,'native authority parity');equal(r['projection_equal'],True,'native AtomSpace parity');equal(r['native_calls_before'],r['native_calls_after'],'no new formula at reconstruction')
        for call in receipt['runtime_calls']:
            equal(call['status'],'PASS','supported actual formula');expected=PinnedFormulaRuntime().evaluate(call['formula'],tuple(TruthValue(**x) for x in call['inputs']));equal(call['result'],wire(expected),'pinned arithmetic');formulas+=1
            equal(call['postcheck_status'],'PASS','certified formula');equal(call['commit_status'],'PASS','committed formula')
            if s['mode']=='native':equal(call['mode'],'native','no substitution');equal(call['formula_agreement'],True,'native agreement');native_formulas+=1
    equal(report['views'],view_count,'view count');equal((directory/'event-prefixes.md').read_text(),readable(directory,report),'event table')
    return dict(status='PASS',revision=source['revision'],development_allow_dirty=allow_dirty,views=view_count,prefixes=report['prefixes'],node_occurrences=nodes,edge_occurrences=edges,
                authority_reconstructions=len(sessions),formula_calls=formulas,new_native_cohort_formula_calls=native_formulas,limitation='source/graph conformance; no authentication, calibrated safety or autonomous outcome claim')
