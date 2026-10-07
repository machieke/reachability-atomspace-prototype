"""One source-bound twelve-episode conformance cohort, no scheduler contest."""
import argparse,json,subprocess,shutil
from hashlib import sha256
from pathlib import Path
from time import perf_counter_ns
from work_loop_lab.compare import inputs as previous_inputs
from experimental_native_recall.backend import verify_build
from validation_lab.decision_comparison import write,seal
from .cases import ROOT,configuration,PARENTS
from .run import episode

PRESERVED='173c772fb96b5a42d94fda9b4f05d6f4f60719f9'


def inputs():
    names=set(previous_inputs())
    for pattern in ('world_lab/*.py','tests/test_independent_world.py','integration_tests/test_independent_world.py'):
        names.update(str(p.relative_to(ROOT)) for p in ROOT.glob(pattern))
    names.update(('INDEPENDENT_WORLD_VALIDATION.md','reviews/independent-world-v1/PROTOCOL.md','reviews/independent-world-v1/environments.json','reviews/independent-world-v1/verify_review.py'))
    return {n:sha256((ROOT/n).read_bytes()).hexdigest() for n in sorted(names)}


def source_binding(allow_dirty=False):
    rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();files=inputs();dirty=[]
    for n,h in files.items():
        p=subprocess.run(['git','show',rev+':'+n],cwd=ROOT,capture_output=True)
        if p.returncode or sha256(p.stdout).hexdigest()!=h:dirty.append(n)
    if dirty and not allow_dirty:raise ValueError('commit measured inputs first: '+str(dirty))
    return dict(revision=rev,files=files,dirty_inputs=dirty,preserved_publication=PRESERVED,protocol_commit='326c7fe',frozen_consumer_revision='d2a6b6605eaefc32f0c56e2a7c0d5e9bf11cffb8')


def readable(report):
    lines=['# Observation-independent physical outcomes','',
      'Measured source: `'+report['sources']['revision']+'`. Six parent environments, two formula modes. Physical truth and existing observation-based completion remain separate.','',
      '| Environment | Mode | J_world | J_certified | First physical goal | First completion | Final physical / observed loss | Historical stage | Stop |',
      '|---|---|---:|---:|---|---|---|---|---|']
    for r in report['results']:
        m=r['metrics'];values=[r['parent'],r['mode'],m['J_world'],m['J_certified'],m['first_physical_goal'],m['first_observed_completion'],str(m['final_physical_deficit'])+' / '+str(m['final_observed_loss']),r['stage'],r['stop']]
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
    for mode in cfg['modes']:
        for parent in PARENTS:
            result=episode(parent,output/(mode+'-'+parent),native=mode=='native');results.append(result)
            print(mode,parent,result['conformance'],result.get('stop'),flush=True)
    report=dict(schema='independent-world-cohort/v1',sources=source,results=results,elapsed_ns=perf_counter_ns()-start,
                conformance='PASS' if all(r['conformance']=='PASS' for r in results) else 'FAIL',
                cost_scope='Serial descriptive pass; full nested acquisition/evaluation/frontier/selection/admission/execution/monitoring timings and counters in raw traces. Preflight source copy/build verification excluded.',
                unmeasured=['isolated fsync','isolated native arithmetic within subprocess runtime','RSS','physical sensor latency','production decision quality','physical real-world latency or calibrated probability'])
    write(output/'report.json',report);(output/'COMPARISON.md').write_text(readable(report));seal(output);return report


def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True);r=sub.add_parser('run');r.add_argument('--output',required=True);r.add_argument('--allow-dirty',action='store_true');a=sub.add_parser('audit');a.add_argument('directory');a.add_argument('--allow-dirty',action='store_true');args=p.parse_args()
    if args.command=='run':out=run(args.output,args.allow_dirty)
    else:
        from .audit import audit
        out=audit(args.directory,args.allow_dirty)
    print(json.dumps({k:v for k,v in out.items() if k not in ('sources','results')},indent=2))
    if out.get('conformance')=='FAIL':raise SystemExit(1)

if __name__=='__main__':main()
