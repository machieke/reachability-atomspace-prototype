"""Sealed input replay plus independent finite predicates and frozen authority replay."""
import json,shutil
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from reachability.service import AdmissionService
from reachability.pln_adapter import TruthValue
from reachability.probability_formula import PinnedFormulaRuntime
from experimental_online_pln.agenda import wire
from experimental_obligations.capture import immutable,capture,state_digest
from experimental_obligations.evaluate import evaluate,Bounds
from validation_lab.audit_pressure_comparison import artifact_path
from .compare import configuration,inputs,diagnostics,readable
from .reference import frozen,qualified


def equal(a,b,reason):
    if a!=b:raise ValueError('audit differs: '+reason)


def audit(directory,allow_dirty=False):
    directory=Path(directory)
    def load(name):return json.loads(artifact_path(directory,name).read_text())
    seal=load('bundle.json');files={str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file() and p.name!='bundle.json' and not p.name.endswith(('.lock','-wal','-shm'))}
    equal(set(seal['files']),files,'sealed inventory')
    for name,h in seal['files'].items():equal(sha256(artifact_path(directory,name).read_bytes()).hexdigest(),h,'artifact '+name)
    sources=load('sources.json');equal(inputs(),sources['files'],'auditor source inventory');
    if not allow_dirty:equal(sources['dirty_inputs'],[],'committed source only')
    for name,h in sources['files'].items():equal(sha256(artifact_path(directory,'source/'+name).read_bytes()).hexdigest(),h,'archived source '+name)
    config=load('configuration.json');equal(config,configuration(),'preregistered configuration');report=load('report.json');equal(report['sources'],sources,'report source')
    expected_sessions=['finite-'+p for p in config['parents']]+['native-'+p for p in config['native']]
    equal([s['name'] for s in report['sessions']],expected_sessions,'small cohort inventory')
    equal(len(set(report['index'])),len(report['index']),'no duplicated pair counts')
    # Independently enumerated preregistered row/role inventory, not report-derived.
    layout={
        'adequate-direct':{'base':('alternatives',)},
        'weak-augmented':{'before':('alternatives',),'after':('alternatives','mandatory_method','all_assessments')},
        'only-weak':{'weak':('alternatives','mandatory_method')},
        'missing-mandatory':{'missing':('alternatives','two_sources','required_model')},
        'objections':{'outside':('alternatives',),'opposite':('alternatives',)},
        'lineage-copies':{x:('alternatives','two_sources') for x in ('one','copies','distinct-root')},
        'revision-family':{x:('alternatives','all_assessments','required_model') for x in ('parents','parents-and-child')},
        'freshness':{x:('alternatives',) for x in ('before','sole-revoked','replacement','surviving-alternative')},
        'scope-bounds':{x:('alternatives',) for x in ('base','context','time','unsupported','unclassified','hard-unknown','incomplete','record-bound','classification-bound','witness-bound')},
        'adverse-inference':{x:('alternatives',) for x in ('before','after')},
        'historical-anchor':{'published-final':('historical-alternatives','historical-mandatory')}}
    expected_index=[]
    for session in report['sessions']:
        for label,variants in layout[session['parent']].items():
            expected_index += [session['name']+'/'+label+'.'+v+'.json' for v in variants]
        equal(session['rows'],len(layout[session['parent']]),'snapshot inventory')
    equal(report['index'],expected_index,'complete preregistered pairs')
    comparisons=records=witnesses=reference_checks=formulas=native_formulas=0
    for name in report['index']:
        entry=load(name);equal(name,entry['session']+'/'+entry['label']+'.'+entry['variant']+'.json','pair identity');equal(entry['capture_file'],entry['session']+'/'+entry['label']+'.capture.json','capture path');cap=immutable(load(entry['capture_file']));equal(cap.identity,entry['snapshot_identity'],'snapshot identity');data=cap.data()
        if entry['diagnostic']:
            base=immutable(load('finite-scope-bounds/base.capture.json'));variants=diagnostics(dict(capture=base))
            expected=next(v for v in variants if v['label']==entry['label'])
            equal(cap,expected['capture'],'diagnostic input');equal(entry['manifest'],expected['override_manifest'],'diagnostic manifest');equal(entry['bounds'],expected['bounds'].__dict__,'diagnostic bounds');equal(entry['expected_B'],expected['expected_B'],'diagnostic expected answer')
        else:
            equal(entry['capture_nonmutation']['before'],entry['capture_nonmutation']['after'],'capture nonmutation');equal(entry['manifest'],config['role_manifests'][entry['variant']],'frozen role assignment');equal(entry['bounds'],config['bounds'],'fixed finite bounds')
            equal(frozen(data),data['live_criterion_statuses'][0],'independent frozen A');reference_checks+=1
        for kind in ('A','B'):
            actual=entry['assessments'][kind];replayed=evaluate(cap,entry['manifest'],kind,Bounds(**entry['bounds']))[0].data();equal(actual,replayed,'detached replay '+name+' '+kind)
            equal(actual['authority'],False,'no authority');equal(actual['not_a_permission'],True,'not a permission')
        a,b=(entry['assessments'][k] for k in ('A','B'))
        if entry['diagnostic']:equal(b['status'],entry['expected_B'],'closed diagnostic')
        else:
            equal(a['numerical_status'],frozen(data),'actual frozen numerical boundary')
            status,groups=qualified(data,entry['manifest']);equal(b['numerical_status'],status,'independent B status')
            equal({o['id']:(o['status'],o['witnesses']) for o in b['obligations']},groups,'independent full witness set');reference_checks+=1
            equal(sorted(r['id'] for r in b['records']),sorted(v['belief_revision_id'] for view in data['pairs'][0] for v in view['historical']),'complete relevant scan')
        comparisons+=1;records+=len(b['records']);witnesses+=sum(len(o['witnesses']) for o in b['obligations'])
    for s in report['sessions']:
        name=s['name'];receipts=load(name+'/receipts.json');db=artifact_path(directory,name+('/historical.db' if s['parent']=='historical-anchor' else '/admission.db'))
        with TemporaryDirectory() as tmp:
            copy=Path(tmp)/'admission.db';shutil.copyfile(db,copy)
            with AdmissionService(database=copy) as service:
                before=state_digest(service);live,_=capture(service);equal(before,state_digest(service),'read-only frozen reconstruction')
                equal(live,immutable(load(name+'/'+s['last_authoritative_capture'])),'final authoritative SQLite reconstruction')
        for temporal in receipts.get('temporal',[]):
            equal(temporal['evidence_before'],temporal['evidence_after'],'no new observations around adverse inference');equal(temporal['goal_before'],temporal['goal_after'],'no changed observed goal relief');equal(temporal['executor_effects'],0,'no external action')
        if s['mode']=='native':
            equal(receipts['reconstruction']['authority_equal'],True,'native authority parity');equal(receipts['reconstruction']['projection_equal'],True,'native AtomSpace parity')
            equal(receipts['reconstruction']['native_calls_before'],receipts['reconstruction']['native_calls_after'],'no rerun at reconstruction')
        for call in receipts['runtime_calls']:
            equal(call['status'],'PASS','actual inference');expected=PinnedFormulaRuntime().evaluate(call['formula'],tuple(TruthValue(**t) for t in call['inputs']))
            equal(wire(expected),call['result'],'independent pinned arithmetic');formulas+=1
            if s['mode']=='native':equal(call['mode'],'native','no finite substitution');equal(call['formula_agreement'],True,'native/finite boundary');native_formulas+=1
    equal(report['assessment_pairs'],comparisons,'pair count');equal((directory/'comparison.md').read_text(),readable(directory,report),'readable table')
    return dict(status='PASS',development_allow_dirty=allow_dirty,revision=sources['revision'],pairs=comparisons,independent_reference_checks=reference_checks,records=records,witnesses=witnesses,sqlite_reconstructions=len(report['sessions']),formula_calls=formulas,new_native_formula_calls=native_formulas,
        limitation='Semantic replay and checked authority journals, not an external safety or data-truth oracle; timing values are descriptive measurements.')
