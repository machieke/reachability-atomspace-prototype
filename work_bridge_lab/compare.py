"""Fixed controlled replay and event-prefix publication; no controller choices."""
import argparse,json,shutil,subprocess
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from time import perf_counter_ns
from obligations_lab.compare import inputs as previous_inputs
from experimental_native_recall.backend import verify_build
from experimental_work_bridge.project import project,Limits
from experimental_work_bridge.capture import digest
from validation_lab.decision_comparison import write,seal
from .cases import ROOT,PARENTS,NATIVE,LAYOUT,construct,manifests,assess,diagnostics
from .reference import validate,expected_prefix

PRESERVED='259bc0fc4dc88eeb6d085b47d3a17b86cf8208fe'


def inputs():
    names=set(previous_inputs())
    for pattern in ('experimental_work_bridge/*.py','work_bridge_lab/*.py','tests/test_work_bridge.py','integration_tests/test_work_bridge.py'):
        names.update(str(p.relative_to(ROOT)) for p in ROOT.glob(pattern))
    names.update(('OBLIGATION_WORK_BRIDGE.md','reviews/obligation-work-bridge-v1/PROTOCOL.md','reviews/obligation-work-bridge-v1/task.json','reviews/obligation-work-bridge-v1/verify_review.py'))
    return {n:sha256((ROOT/n).read_bytes()).hexdigest() for n in sorted(names)}


def source_binding(allow_dirty=False):
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();files=inputs();dirty=[]
    for n,h in files.items():
        p=subprocess.run(['git','show',revision+':'+n],cwd=ROOT,capture_output=True)
        if p.returncode or sha256(p.stdout).hexdigest()!=h:dirty.append(n)
    if dirty and not allow_dirty:raise ValueError('commit measured inputs first: '+str(dirty))
    return dict(revision=revision,files=files,dirty_inputs=dirty,preserved_publication=PRESERVED,protocol_commit='45fb871',frozen_evaluator_revision='5161e19b73f89676edf0b9f772200c12eee02ef1')


def configuration():
    return json.loads(json.dumps(dict(schema='obligation-work-bridge-cohort/v0',seed=0,parents=PARENTS,native=NATIVE,layout=LAYOUT,manifests=manifests(),limits=asdict(Limits()),
        diagnostics=['context','product','time','partial','bound'],policy='controlled replay; unranked read-only projector; live all-current unchanged',
        cost_policy='one serial descriptive pass, acquisition once per prefix, frozen evaluation and revalidation explicitly charged; nested costs',
        unmeasured=['isolated native arithmetic','isolated fsync','RSS','physical observation latency','source-copy/build-verification preflight','autonomous repair/outcomes'])))


def run(output,allow_dirty=False):
    output=Path(output)
    if output.exists():raise ValueError('fresh output directory required')
    sources=source_binding(allow_dirty);cfg=configuration();output.mkdir(parents=True)
    write(output/'sources.json',sources);write(output/'configuration.json',cfg)
    for n in sources['files']:
        p=output/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,p)
    verify_build(ROOT/'artifacts')
    for n in ('adapter-build.json','recall-build.json'):shutil.copyfile(ROOT/'artifacts'/n,output/n)
    shutil.copyfile(ROOT/'adapters.lock.json',output/'adapters.lock.json')
    start=perf_counter_ns();sessions=[];index=[]
    for mode,parents in (('finite',PARENTS),('native',NATIVE)):
        for parent in parents:
            name=mode+'-'+parent;t=perf_counter_ns();rows,receipt=construct(parent,output/name,native=mode=='native');construction=perf_counter_ns()-t
            if parent=='registry':rows.extend(diagnostics(next(r for r in rows if r['label']=='complete')))
            write(output/name/'receipts.json',receipt);prefixes=[]
            for row in rows:
                frame=row['frame'];write(output/name/(row['label']+'.input.json'),frame.data());prefixes.append(dict(label=row['label'],acquisition_costs=row['acquisition_costs'],diagnostic=row.get('diagnostic',False)))
                for variant in row['variants']:
                    m=row.get('manifest',cfg['manifests'][variant]);ab,assessment_costs=assess(frame,m);limits=row.get('limits',Limits());v,costs=project(frame,m,ab['A'],ab['B'],limits)
                    validate(frame,m,ab['A'],ab['B'],v);expected_prefix(parent,row['label'],variant,v.data())
                    entry=dict(session=name,parent=parent,mode=mode,label=row['label'],variant=variant,input_file=name+'/'+row['label']+'.input.json',input_identity=frame.identity,
                        manifest=m,limits=asdict(limits),diagnostic=row.get('diagnostic',False),assessments={k:a.data() for k,a in ab.items()},view=v.data(),costs=dict(frozen_evaluation=assessment_costs,projection=costs))
                    file=name+'/'+row['label']+'.'+variant+'.json';write(output/file,entry);index.append(file)
            sessions.append(dict(name=name,parent=parent,mode=mode,prefixes=prefixes,construction_elapsed_ns=construction,last_authoritative_prefix=next(r for r in reversed(rows) if not r.get('diagnostic'))['label']))
            print(name,len(rows),'PASS',flush=True)
    report=dict(schema='obligation-work-bridge-comparison/v0',conformance='PASS',sources=sources,index=index,sessions=sessions,elapsed_ns=perf_counter_ns()-start,
                views=len(index),prefixes=sum(len(s['prefixes']) for s in sessions),interpretation='conformance of work explanation only; no policy preference or autonomous trajectory')
    write(output/'report.json',report);(output/'event-prefixes.md').write_text(readable(output,report));seal(output);return report


def readable(directory,report):
    lines=['# Controlled obligation-work event prefixes','', 'A/B are frozen numerical judgments; complete means the explanation covers its declared finite fragment. Execution and observed outcomes remain separate authority state. Each JSON contains exact records, producer identities, coherent AND/OR graph, all blockers and input bindings.','',
     '| Session / prefix / role | A / B | Complete | Unresolved obligations | Global reasons | Operations (by readiness) | Observed loss |','|---|---|---|---|---|---|---:|']
    from collections import Counter
    for file in report['index']:
        e=json.loads((Path(directory)/file).read_text());v=e['view'];gaps='; '.join(o['obligation_id']+': '+','.join(o['reasons']) for o in v['obligations'] if o['status']!='PASS') or 'none in numerical obligations'
        reasons=','.join(sorted({b['category'] for b in v['global_blockers']}));ops=dict(Counter(n['readiness'] for n in v['nodes'] if n['kind']=='operation'))
        loss=v['observed']['goal']['projection']['outstanding_loss'] if v['observed'] else 'unavailable'
        lines.append(f"| {e['session']} / {e['label']} / {e['variant']} | {v['A'].get('numerical_status','unavailable')} / {v['B'].get('numerical_status','unavailable')} | {v['complete']} | {gaps} | {reasons} | {ops} | {loss} |")
    return '\n'.join(lines)+'\n'


def main():
    p=argparse.ArgumentParser();subs=p.add_subparsers(dest='command',required=True);r=subs.add_parser('run');r.add_argument('--output',required=True);r.add_argument('--allow-dirty',action='store_true');a=subs.add_parser('audit');a.add_argument('directory');args=p.parse_args()
    if args.command=='run':result=run(args.output,args.allow_dirty)
    else:
        from .audit import audit
        result=audit(args.directory)
    print(json.dumps({k:v for k,v in result.items() if k not in ('sources','index','sessions')},indent=2))

if __name__=='__main__':main()
