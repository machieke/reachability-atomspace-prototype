"""Once-per-frozen-revision regression receipts and explicit coverage inventory."""
import argparse,json,subprocess,sys,time,unittest
from hashlib import sha256
from pathlib import Path
from .compare import ROOT,inputs,source_binding,PRESERVED
from validation_lab.decision_comparison import write

DEFAULT=('snapshot_payload','runtime_lifetime','native_multihop','native_recall','multihop','independent_world','work_loop','dispatch','dispatch_recovery','dispatch_races','work_bridge','online_pln','obligations','decisions','decision_demo','decision_dispatch','probability','probability_joint','probability_recovery',
         'execution','durable_execution','dispatched_goals','goals','durable_goals','goal_coverage','goal_oracles','goal_completion','lifecycle','durable_lifecycle')
NATIVE=('snapshot_payload','runtime_lifetime','native_multihop','native_recall','multihop','independent_world','work_loop','online_pln','work_bridge','obligations','decisions','probability_service','native_adapters')


def ids(suite):
    for item in suite:
        if isinstance(item,unittest.TestSuite):yield from ids(item)
        else:yield item.id()


def inventory():
    selected={'tests.test_'+n for n in DEFAULT}|{'integration_tests.test_'+n for n in NATIVE};out={}
    for package in ('tests','integration_tests'):
        modules=[package+'.'+p.stem for p in sorted((ROOT/package).glob('test_*.py'))]
        for key,values in (('executed',[n for n in modules if n in selected]),('omitted',[n for n in modules if n not in selected])):
            suite=unittest.defaultTestLoader.loadTestsFromNames(values)
            out[package+'_'+key]=dict(modules=values,inventory=list(ids(suite)),count=suite.countTestCases())
    out['numerical_reference']='pressure_field_lifecycle_reference_checks omitted: pressure solver unchanged; historical results are not new passes'
    out['reason']='Numerical decisions, execution hard gates, goal/lifecycle accounting and native adapters are applicable. Scheduler/transport matrices, generalized recovery/corpus and unrelated planner suites omitted. Probability recovery included as numerical-ledger preservation regression.'
    return out


def run(kind,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if (output/(kind+'.json')).exists() or (output/(kind+'-start.json')).exists():raise ValueError('one suite pass per fresh destination')
    sources=source_binding();modules=[('tests.' if kind=='default' else 'integration_tests.')+'test_'+n for n in (DEFAULT if kind=='default' else NATIVE)]
    suite=unittest.defaultTestLoader.loadTestsFromNames(modules);paths=[n.replace('.','/')+'.py' for n in modules]
    hashes={p:sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
    metadata=dict(suite=kind,revision=sources['revision'],source_files_at_start=sources['files'],test_files_at_start=hashes,modules=modules,inventory=list(ids(suite)),planned=suite.countTestCases(),start_unix_ns=time.time_ns(),command=sys.argv,concurrent_load='suite groups and comparison run serially')
    write(output/(kind+'-start.json'),metadata);started=time.perf_counter()
    with (output/(kind+'.log')).open('w') as log:result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    metadata.update(elapsed_seconds=time.perf_counter()-started,run=result.testsRun,failures=[(str(t),why) for t,why in result.failures],errors=[(str(t),why) for t,why in result.errors],skips=[(str(t),why) for t,why in result.skipped],passed=result.wasSuccessful(),source_unchanged=sources['files']==inputs(),test_files_unchanged=hashes=={p:sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
    write(output/(kind+'.json'),metadata);return {k:v for k,v in metadata.items() if k not in ('source_files_at_start','test_files_at_start','inventory')}


def preservation():
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',PRESERVED],cwd=ROOT,text=True).splitlines();changed=[]
    allowed=['IMPLEMENTATION_PLAN.md','implementation_manifest.json']
    for name in names:
        if name in allowed:continue
        data=subprocess.check_output(['git','show',PRESERVED+':'+name],cwd=ROOT)
        if not (ROOT/name).is_file() or (ROOT/name).read_bytes()!=data:changed.append(name)
    return dict(status='PASS' if not changed else 'FAIL',base=PRESERVED,files_checked=len(names)-len(allowed),exceptions=allowed,changed=changed)


def main():
    p=argparse.ArgumentParser();p.add_argument('kind',choices=('default','native','inventory','preservation'));p.add_argument('--output',required=True);args=p.parse_args()
    if args.kind in ('default','native'):result=run(args.kind,args.output)
    else:
        result=inventory() if args.kind=='inventory' else preservation();write(Path(args.output)/(args.kind+'.json'),result)
    print(json.dumps(result,indent=2));sys.exit(result.get('passed') is False or result.get('status')=='FAIL')

if __name__=='__main__':main()
