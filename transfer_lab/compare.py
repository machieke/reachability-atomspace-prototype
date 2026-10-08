"""One source-bound, counterbalanced two-arm transfer cohort."""
import argparse,json,subprocess,shutil
from hashlib import sha256
from pathlib import Path
from time import perf_counter_ns
from snapshot_payload_lab.compare import inputs as previous_inputs
from experimental_native_recall.backend import verify_build
from validation_lab.decision_comparison import write,seal
from .cases import ROOT,PARENTS
from .config import configuration,ARMS,cells,folder
from .run import episode

PRESERVED='d50baa1e9604c9e3df1ea4ead3e18a92fe24b7ec'


def inputs():
    names=set(previous_inputs())
    for pattern in ('transfer_lab/*.py','tests/test_frozen_transfer.py'):
        names.update(str(p.relative_to(ROOT)) for p in ROOT.glob(pattern))
    names.update(('FROZEN_TRANSFER.md',*[str(p.relative_to(ROOT)) for p in (ROOT/'reviews/frozen-transfer-v1').iterdir() if p.name in ('PROTOCOL.md','HANDOFF.md','BASELINE.json','fixtures.json','CONSTRUCTION.json','verify_review.py')]))
    return {n:sha256((ROOT/n).read_bytes()).hexdigest() for n in sorted(names)}


def source_binding(allow_dirty=False):
    rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();files=inputs();dirty=[]
    for n,h in files.items():
        p=subprocess.run(['git','show',rev+':'+n],cwd=ROOT,capture_output=True)
        if p.returncode or sha256(p.stdout).hexdigest()!=h:dirty.append(n)
    if dirty and not allow_dirty:raise ValueError('commit measured inputs first: '+str(dirty))
    return dict(revision=rev,files=files,dirty_inputs=dirty,preserved_publication=PRESERVED,protocol_commit='8dac6c7',consumer=dict(path='experimental_multihop/consumer.py',revision='b509d2b8d7388a570b5a666e1c845b95d207ad20',sha256=files['experimental_multihop/consumer.py']))


def readable(report):
    from .outcomes import render
    return render(report)


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
    for sweep,arm,mode,parent in cells():
        path=output/folder(sweep,arm,mode,parent)
        result=episode(parent,path,native=mode=='native',arm=arm)
        result['sweep']=sweep
        from .outcomes import describe
        result['evaluation']=describe(path,result);write(path/'result.json',result);results.append(result)
        print(sweep,arm,mode,parent,result['conformance'],result.get('error',result.get('stop')),flush=True)
    report=dict(schema='frozen-transfer-result/v1',sources=source,results=results,elapsed_ns=perf_counter_ns()-start,
                conformance='PASS' if all(r['conformance']=='PASS' for r in results) else 'FAIL',
                cost_scope='Serial descriptive pass; full nested acquisition/evaluation/frontier/selection/admission/execution/monitoring timings and counters in raw traces. Preflight source copy/build verification excluded.',
                unmeasured=['isolated fsync','isolated native arithmetic within subprocess runtime','RSS','peak memory','native process memory','serialization copies','physical sensor latency','production decision quality','physical real-world latency or calibrated probability'])
    from .parity import report as parity_report
    write(output/'parity.json',parity_report(output,results))
    write(output/'report.json',report);(output/'COMPARISON.md').write_text(readable(report))
    from .costs import collect,render,paired,render_pairs
    costs=collect(output,report);write(output/'costs.json',costs);(output/'COSTS.md').write_text(render(costs));pairs=paired(report);write(output/'paired-times.json',pairs);(output/'PAIRED_TIMES.md').write_text(render_pairs(pairs));seal(output);return report


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
