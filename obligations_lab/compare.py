"""One finite semantic cohort and three native boundary reconstructions."""
import argparse,copy,json,shutil,subprocess
from collections import Counter
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from time import perf_counter_ns
from assembly_lab.compare import inputs as preserved_inputs
from experimental_native_recall.backend import verify_build
from experimental_obligations.capture import immutable
from experimental_obligations.evaluate import Bounds,evaluate
from validation_lab.decision_comparison import write,seal
from .cases import ROOT,PARENTS,construct,manifests
from .historical import historical
from .reference import frozen,qualified

PRESERVED='3d84c6671804e7dacd8aa68c49cadc667fccce16'
NATIVE=('weak-augmented','revision-family','adverse-inference')


def inputs():
    names=set(preserved_inputs())
    for pattern in ('experimental_obligations/*.py','obligations_lab/*.py','tests/test_obligations.py','integration_tests/test_obligations.py'):
        names.update(str(p.relative_to(ROOT)) for p in ROOT.glob(pattern))
    names.update(('SHADOW_OBLIGATIONS.md','reviews/decision-obligations-shadow-v1/PROTOCOL.md','reviews/decision-obligations-shadow-v1/interpretations.json','reviews/decision-obligations-shadow-v1/verify_review.py'))
    return {name:sha256((ROOT/name).read_bytes()).hexdigest() for name in sorted(names)}


def source_binding(allow_dirty=False):
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();files=inputs();dirty=[]
    for name,h in files.items():
        p=subprocess.run(['git','show',revision+':'+name],cwd=ROOT,capture_output=True)
        if p.returncode or sha256(p.stdout).hexdigest()!=h:dirty.append(name)
    if dirty and not allow_dirty:raise ValueError('commit measured inputs first: '+str(dirty))
    return dict(revision=revision,files=files,dirty_inputs=dirty,preserved_publication=PRESERVED,role_mapping_commit='f67a4a0',protocol_commit='ce4ae40')


def configuration():
    return dict(schema='decision-obligations-semantic-cohort/v0',parents=list(PARENTS),native=list(NATIVE),seed=0,
        bounds=asdict(Bounds()),role_manifests=manifests(),policy='detached; no live execution consumption',
        population='11 parent diagnostics, not independent samples; 3 native reconstructions of the same parents',
        costs='one descriptive pass; stage times nested in evaluator total; construction includes existing certification/persistence',
        unmeasured=['isolated native arithmetic','native RSS','isolated SQLite fsync','physical observations','new scheduler or executed counterfactual trajectories'])


def diagnostics(base):
    """Declared, labeled input perturbations; never reinserted into authority."""
    result=[]
    for label,expected in (('context','FAIL'),('time','STALE'),('unsupported','UNKNOWN'),('unclassified','UNKNOWN'),('hard-unknown','UNKNOWN'),('incomplete','UNKNOWN'),('record-bound','UNKNOWN'),('classification-bound','UNKNOWN'),('witness-bound','UNKNOWN')):
        d=base['capture'].data();m=manifests()['alternatives'];bounds=Bounds()
        if label=='context':m['context']='other-context'
        elif label=='time':m['time_window']=[1,2]
        elif label=='unsupported':m['classes'][0]['kind']='unsupported'
        elif label=='unclassified':m['classes'][0]['identity']=['unmapped-source']
        elif label=='hard-unknown':
            for c in d['hard_checks']:
                if c['name']=='owner':c['status']='UNKNOWN'
        elif label=='incomplete':d['complete']=False
        elif label=='record-bound':bounds=Bounds(records=0)
        elif label=='classification-bound':bounds=Bounds(classification=0)
        elif label=='witness-bound':bounds=Bounds(witnesses=0)
        result.append(dict(label=label,capture=immutable(d),costs={},manifests=('alternatives',),override_manifest=m,bounds=bounds,diagnostic=True,expected_B=expected))
    return result


def run(output,allow_dirty=False):
    output=Path(output)
    if output.exists():raise ValueError('fresh output directory required')
    sources=source_binding(allow_dirty);config=configuration();output.mkdir(parents=True)
    write(output/'sources.json',sources);write(output/'configuration.json',config)
    for name in sources['files']:
        p=output/'source'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p)
    verify_build(ROOT/'artifacts')
    for name in ('adapter-build.json','recall-build.json'):shutil.copyfile(ROOT/'artifacts'/name,output/name)
    shutil.copyfile(ROOT/'adapters.lock.json',output/'adapters.lock.json')
    started=perf_counter_ns();index=[];sessions=[]
    for mode,parents in (('finite',PARENTS),('native',NATIVE)):
        for parent in parents:
            name=mode+'-'+parent;directory=output/name;t=perf_counter_ns()
            rows,receipts=historical(directory) if parent=='historical-anchor' else construct(parent,directory,native=mode=='native')
            costs=dict(construction_elapsed_ns=perf_counter_ns()-t,snapshot_acquisition_ns=sum(r['costs'].get('snapshot_acquisition_ns',0) for r in rows))
            if parent=='scope-bounds':rows+=diagnostics(rows[0])
            write(directory/'receipts.json',receipts)
            for row in rows:
                cap=row['capture'];write(directory/(row['label']+'.capture.json'),cap.data())
                for variant in row['manifests']:
                    m=row.get('override_manifest',config['role_manifests'][variant]);bounds=row.get('bounds',Bounds());assessments={};timing={}
                    for kind in ('A','B'):
                        value,elapsed=evaluate(cap,m,kind,bounds);assessments[kind]=value.data();timing[kind]=elapsed
                    if row.get('diagnostic'):
                        if assessments['B']['status']!=row['expected_B']:raise AssertionError((name,row['label'],assessments['B']))
                    else:
                        data=cap.data();reference=qualified(data,m)
                        if assessments['A']['numerical_status']!=frozen(data) or frozen(data)!=data['live_criterion_statuses'][0]:raise AssertionError('frozen A mismatch')
                        if assessments['B']['numerical_status']!=reference[0] or {o['id']:(o['status'],o['witnesses']) for o in assessments['B']['obligations']}!=reference[1]:raise AssertionError('independent B mismatch')
                    entry=dict(session=name,parent=parent,mode=mode,label=row['label'],variant=variant,capture_file=name+'/'+row['label']+'.capture.json',snapshot_identity=cap.identity,
                        manifest=m,bounds=asdict(bounds),capture_nonmutation=row.get('nonmutation'),diagnostic=row.get('diagnostic',False),expected_B=row.get('expected_B'),assessments=assessments,costs=timing)
                    path=name+'/'+row['label']+'.'+variant+'.json';write(output/path,entry);index.append(path)
            sessions.append(dict(name=name,parent=parent,mode=mode,costs=costs,rows=len(rows),last_authoritative_capture=next(r for r in reversed(rows) if not r.get('diagnostic'))['label']+'.capture.json'))
            print(name,len(rows),'PASS',flush=True)
    report=dict(schema='decision-obligations-comparison/v0',conformance='PASS',sources=sources,sessions=sessions,index=index,elapsed_ns=perf_counter_ns()-started,
        snapshot_count=sum(s['rows'] for s in sessions),assessment_pairs=len(index),interpretation='policy disagreements, not empirical safety/error rates')
    write(output/'report.json',report);(output/'comparison.md').write_text(readable(output,report));seal(output);return report


def readable(directory,report):
    lines=['# Detached decision-obligation comparison','', 'A is the unchanged all-current interpretation. B is an experimental declared obligation interpretation. No shadow result authorizes actions.','',
           '| Session / snapshot | Role manifest | A numerical / scoped | B numerical / scoped | B blocking checks |','|---|---|---|---|---|']
    for name in report['index']:
        e=json.loads((Path(directory)/name).read_text());a,b=(e['assessments'][k] for k in ('A','B'))
        blocking=', '.join(c['name']+':'+c['status'] for c in b['checks'] if c['status']!='PASS') or b.get('reason','')
        lines.append(f"| {e['session']} / {e['label']} | {e['variant']} | {a['numerical_status']} / {a['status']} | {b['numerical_status']} / {b['status']} | {blocking} |")
    lines+=['','Every pair JSON contains the exact manifest, full supporting/opposing records, retired records, applicability explanations, all witness IDs and basis hashes. Capture JSON also includes the full unfiltered context ledger, registries and hard checks. Diagnostic input perturbations are explicitly labeled. Historical role assignments are counterfactual.','']
    return '\n'.join(lines)


def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    r=sub.add_parser('run');r.add_argument('--output',required=True);r.add_argument('--allow-dirty',action='store_true')
    a=sub.add_parser('audit');a.add_argument('directory')
    args=p.parse_args()
    if args.command=='run':result=run(args.output,args.allow_dirty)
    else:
        from .audit import audit
        result=audit(args.directory)
    print(json.dumps({k:v for k,v in result.items() if k not in ('sources','sessions','index')},indent=2))

if __name__=='__main__':main()
