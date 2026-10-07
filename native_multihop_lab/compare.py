"""One source-bound twelve-episode conformance cohort, no scheduler contest."""
import argparse,json,subprocess,shutil
from hashlib import sha256
from pathlib import Path
from time import perf_counter_ns
from multihop_lab.compare import inputs as previous_inputs
from experimental_native_recall.backend import verify_build
from validation_lab.decision_comparison import write,seal
from multihop_lab.cases import ROOT,PARENTS
from .config import configuration,ARMS
from .run import episode as native_episode
from multihop_lab.run import episode as scan_episode

PRESERVED='c4686bc6fb100c324874f12f2f98d66aa2f0e9d7'


def inputs():
    names=set(previous_inputs())
    for pattern in ('experimental_native_multihop/*.py','native_multihop_lab/*.py','tests/test_native_multihop.py','integration_tests/test_native_multihop.py'):
        names.update(str(p.relative_to(ROOT)) for p in ROOT.glob(pattern))
    names.update(('NATIVE_MULTIHOP_RECALL.md','reviews/native-multihop-v1/PROTOCOL.md','reviews/native-multihop-v1/HANDOFF.md','reviews/native-multihop-v1/verify_review.py'))
    return {n:sha256((ROOT/n).read_bytes()).hexdigest() for n in sorted(names)}


def source_binding(allow_dirty=False):
    rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();files=inputs();dirty=[]
    for n,h in files.items():
        p=subprocess.run(['git','show',rev+':'+n],cwd=ROOT,capture_output=True)
        if p.returncode or sha256(p.stdout).hexdigest()!=h:dirty.append(n)
    if dirty and not allow_dirty:raise ValueError('commit measured inputs first: '+str(dirty))
    return dict(revision=rev,files=files,dirty_inputs=dirty,preserved_publication=PRESERVED,protocol_commit='55ec450',frozen_consumer_revision='d2a6b6605eaefc32f0c56e2a7c0d5e9bf11cffb8')


def readable(report):
    lines=['# Native multi-hop retrieval comparison','',
      'Measured source: `'+report['sources']['revision']+'`. Six parents, two retrieval arms and two formula modes. Timing is descriptive.','',
      '| Structure | Retrieval | Formula | Depth | Calls | Completion | J world / certified | Wall seconds |',
      '|---|---|---|---:|---:|---|---|---:|']
    for r in report['results']:
        m=r.get('metrics',{});values=[r['parent'],r['arm'],r['mode'],r.get('longest_dependency_path'),len(r['runtime_calls']),m.get('first_observed_completion'),str(m.get('J_world'))+' / '+str(m.get('J_certified')),round(r['elapsed_ns']/1e9,3)]
        lines.append('| '+' | '.join(str(x) for x in values)+' |')
    return '\n'.join(lines)+'\n'


def run(output,allow_dirty=False):
    output=Path(output)
    if output.exists():raise ValueError('fresh output directory required')
    source=source_binding(allow_dirty);cfg=configuration();output.mkdir(parents=True)
    write(output/'sources.json',source);write(output/'configuration.json',cfg)
    for n in source['files']:
        dest=output/'source'/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,dest)
    # Fail visibly if the pinned native dependencies are absent. Never substitute.
    verify_build(ROOT/'artifacts')
    for n in ('adapter-build.json','recall-build.json'):shutil.copyfile(ROOT/'artifacts'/n,output/n)
    shutil.copyfile(ROOT/'adapters.lock.json',output/'adapters.lock.json')
    start=perf_counter_ns();results=[]
    for arm in ARMS:
        for mode in cfg['modes']:
            for parent in PARENTS:
                path=output/(arm+'-'+mode+'-'+parent)
                result=(scan_episode if arm=='MH-scan' else native_episode)(parent,path,native=mode=='native')
                result['arm']=arm;write(path/'result.json',result);results.append(result)
                print(arm,mode,parent,result['conformance'],result.get('error',result.get('stop')),flush=True)
    report=dict(schema='native-multihop-cohort-result/v1',sources=source,results=results,elapsed_ns=perf_counter_ns()-start,
                conformance='PASS' if all(r['conformance']=='PASS' for r in results) else 'FAIL',
                cost_scope='Serial descriptive pass; full nested acquisition/evaluation/frontier/selection/admission/execution/monitoring timings and counters in raw traces. Preflight source copy/build verification excluded.',
                unmeasured=['isolated fsync','isolated native arithmetic within subprocess runtime','RSS','peak memory','native process memory','serialization copies','physical sensor latency','production decision quality','physical real-world latency or calibrated probability'])
    write(output/'report.json',report);(output/'COMPARISON.md').write_text(readable(report))
    from .costs import collect,render
    costs=collect(output,report);write(output/'costs.json',costs);(output/'COSTS.md').write_text(render(costs));seal(output);return report


def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True);r=sub.add_parser('run');r.add_argument('--output',required=True);r.add_argument('--allow-dirty',action='store_true');a=sub.add_parser('audit');a.add_argument('directory');a.add_argument('--allow-dirty',action='store_true');a.add_argument('--output',required=True);args=p.parse_args()
    if args.command=='run':out=run(args.output,args.allow_dirty)
    else:
        from .audit import audit
        target=Path(args.output)
        if target.exists():raise ValueError('fresh audit output required')
        target.mkdir(parents=True);out=audit(args.directory,args.allow_dirty);write(target/'audit.json',out)
    print(json.dumps({k:v for k,v in out.items() if k not in ('sources','results')},indent=2))
    if out.get('conformance')=='FAIL':raise SystemExit(1)

if __name__=='__main__':main()
