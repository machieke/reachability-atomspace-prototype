"""Fresh-output, source-bound native recall comparison and semantic verifier."""
import argparse
import copy
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
from time import perf_counter_ns

from experimental_online_pln.agenda import Limits,Snapshot,wire,digest
from experimental_goal_pln.agenda import Agenda as ScanAgenda
from experimental_goal_pln.relevance import ClosureLimits
from experimental_native_recall.agenda import Agenda as NativeAgenda
from experimental_native_recall.backend import Backend,verify_build
from experimental_native_recall.schema import QueryLimits,SCHEMA
from goal_pln_lab.cases import ROOT,configuration
from goal_pln_lab.compare import inputs as previous_inputs,check_prefixes,cross_session_semantics
from reachability.service import AdmissionService
from reachability.pln_adapter import TruthValue
from reachability.probability_formula import PinnedFormulaRuntime
from reachability.adapter_runtime import verify_source,checked_run,lockfile,AdapterError
from validation_lab.audit_pressure_comparison import artifact_path
from validation_lab.decision_comparison import write,seal
from .episode import run_case
from .reference import answers

ARMS=('Goal-scan','Goal-native')


def inputs():
    names=set(previous_inputs())
    for pattern in ('experimental_native_recall/*.py','native_recall_lab/*.py','tests/test_native_recall*.py','integration_tests/test_native_recall*.py'):
        names.update(str(p.relative_to(ROOT)) for p in ROOT.glob(pattern))
    names.update(('native/atomspace_recall.cc','scripts/build_native_recall.py','reviews/native-atomspace-recall-v1/PROTOCOL.md','NATIVE_RECALL.md'))
    return {n:sha256((ROOT/n).read_bytes()).hexdigest() for n in sorted(names)}


def source_binding(allow_dirty=False):
    rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();files=inputs();dirty=[]
    for name,value in files.items():
        r=subprocess.run(['git','show',rev+':'+name],cwd=ROOT,capture_output=True)
        if r.returncode or sha256(r.stdout).hexdigest()!=value:dirty.append(name)
    if dirty and not allow_dirty:raise ValueError('commit measured source first: '+str(dirty))
    return dict(revision=rev,files=files,dirty_inputs=dirty,baseline_publication='846053ae0c847a4b973747d3a1733f9bf1cd97af')


def folder(mode,case,budget,arm):return f'{mode}-{case}-w{budget}-{arm}'


def run(output,*,modes=('finite','native'),allow_dirty=False):
    output=Path(output)
    if output.exists():raise ValueError('fresh output required')
    sources=source_binding(allow_dirty);output.mkdir(parents=True)
    config=dict(configuration(),recall_arms=ARMS,formula_modes=modes,limits=asdict(Limits()),closure_limits=asdict(ClosureLimits()),
                query_limits=asdict(QueryLimits()),schema=SCHEMA,order='one ordered descriptive pass; no speed claim')
    write(output/'configuration.json',config);write(output/'sources.json',sources)
    for name in sources['files']:
        target=output/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    try:
        verify_build(ROOT/'artifacts')
        if 'native' in modes:
            verify_source('pln',ROOT/'artifacts');verify_source('petta',ROOT/'artifacts')
            if not checked_run(['swipl','--version']).startswith(f"SWI-Prolog version {lockfile()['toolchain']['swipl']} "):
                raise AdapterError('SWI-Prolog version differs from the runtime pin')
    except Exception as error:
        write(output/'blocked.json',dict(status='BLOCKED',requirement='pinned native AtomSpace recall in all modes; pinned PLN/PeTTa/SWI for native formula mode',error=str(error),python_substitution=False));raise
    for name in ('adapter-build.json','recall-build.json'):shutil.copyfile(ROOT/'artifacts'/name,output/name)
    shutil.copyfile(ROOT/'adapters.lock.json',output/'adapters.lock.json')
    start=perf_counter_ns();results=[]
    for mode in modes:
        for fixture in config['fixtures']:
            for budget in config['budgets']:
                for arm in ARMS:
                    r=run_case(fixture,output/folder(mode,fixture['id'],budget,arm),arm=arm,budget=budget,native=mode=='native')
                    results.append(r);print(mode,fixture['id'],budget,arm,r['conformance'],r.get('error',''),flush=True)
    report=dict(schema='native-recall-comparison/v1',sources=sources,configuration_digest=digest(config),results=results,
                elapsed_ns=perf_counter_ns()-start,conformance='PASS' if all(r['conformance']=='PASS' for r in results) else 'FAIL')
    write(output/'report.json',report)
    (output/'comparison.md').write_text(readable(report))
    seal(output);return report


def semantic_discovery(diag):
    return {k:diag.get(k) for k in ('task','relevant','witnesses','eligible','ages','scope','complete','discovery_complete','fallback')}|{
        'closure':{k:v for k,v in diag.get('closure',{}).items() if k!='elapsed_ns'}}


def parity(snapshot,history,backend):
    native=NativeAgenda(limits=history.limits,backend=backend);scan=ScanAgenda('Goal-scan',history.limits)
    for a in (native,scan):
        for name in ('round','selections','work','acquisitions','first_ready','attempted'):
            setattr(a,name,copy.deepcopy(getattr(history,name)))
    nf,n=native.choose(snapshot);sf,s=scan.choose(snapshot)
    if n!=s or semantic_discovery(native.diagnostic)!=semantic_discovery(scan.diagnostic) or native.stop!=scan.stop:
        raise AssertionError('native/scan closure, candidates, witness, eligibility, ranking or budget parity differs')
    return native,scan,nf,sf,n,s


def request_args(request):
    from reachability.model import Literal,Statement
    def literal(value):return Literal(Statement(value['statement']['predicate'],tuple(value['statement']['arguments'])),value['positive'])
    args=dict(context=request['context'],record_id=request['record_id'],report_type=request['report_type'],target=request['target'])
    if request['literal'] is not None:args['literal']=literal(request['literal'])
    if request['report_type']=='numeric':args['target']=literal(request['target'])
    return args


def verify(output):
    output=Path(output);manifest=json.loads((output/'bundle.json').read_text())
    for name,value in manifest['files'].items():
        if sha256(artifact_path(output,name).read_bytes()).hexdigest()!=value:raise ValueError('bundle artifact changed: '+name)
    report=json.loads((output/'report.json').read_text());config=json.loads((output/'configuration.json').read_text())
    if report['sources']['dirty_inputs'] or digest(config)!=report['configuration_digest']:raise ValueError('dirty source or changed configuration')
    for name,value in report['sources']['files'].items():
        if sha256(artifact_path(output,'source/'+name).read_bytes()).hexdigest()!=value:raise ValueError('source copy changed')
    expected={(m,f['id'],b,a) for m in config['formula_modes'] for f in config['fixtures'] for b in config['budgets'] for a in ARMS}
    actual={(r['mode'],r['case_id'],r['budget'],r['arm']) for r in report['results']}
    if expected!=actual or len(actual)!=len(report['results']):raise ValueError('incomplete/duplicate execution matrix')
    selected_count=pairs=queries=commits=calls=0;sequences={}
    for result in report['results']:
        directory=output/folder(result['mode'],result['case_id'],result['budget'],result['arm'])
        if result['conformance']!='PASS' or json.loads((directory/'result.json').read_text())!=result:raise ValueError('failed or mismatched result')
        rows=[json.loads(line) for line in (directory/'trace.jsonl').read_text().splitlines()];check_prefixes(rows,result)
        history=ScanAgenda('Goal-scan',Limits(work=result['budget']));backend=Backend();observed_calls=[];events=[]
        persisted={b['belief_revision_id']:b for v in result['reconstruction']['authority'][0][3] for b in v['historical']}
        try:
            for row in rows:
                view=Snapshot.from_records(row['public_records'])
                if view.binding!=row['public_binding']:raise ValueError('snapshot binding differs')
                event_start=len(backend.events)
                native,scan,nf,sf,n,s=parity(view,history,backend);pairs+=1
                reference=native if result['arm']=='Goal-native' else scan
                frontier=nf if result['arm']=='Goal-native' else sf
                if wire(n)!=row['selected'] or wire(frontier.candidates)!=row['frontier']['candidates'] or frontier.complete!=row['frontier']['complete']:
                    raise ValueError('recorded candidate/choice differs')
                if semantic_discovery(reference.diagnostic)!=semantic_discovery(row['discovery']):raise ValueError('recorded task discovery differs')
                if row['work']!=reference.work or row['acquisitions']!=reference.acquisitions:raise ValueError('work accounting differs')
                history=scan;selected_count+=n is not None
                # Every recorded native answer is compared with an independent
                # brute-force scan of original immutable public source records.
                for event in row['native_events']:
                    if event['kind']=='query':
                        q=event['result'];args=request_args(q['request'])
                        expected_ids=answers(view,q['request']['kind'],**args)
                        if not q['complete'] or tuple(q['ids'])!=expected_ids or q['view_id']!=view.binding:
                            raise ValueError('recorded native query/reference mismatch')
                        queries+=1
                if result['arm']=='Goal-native':
                    new_events=backend.events[event_start:]
                    def strip_timings(items):
                        data=copy.deepcopy(items)
                        for event in data:
                            if event['kind']=='query':event['result'].pop('elapsed_ns',None)
                            if event['kind']=='open_view':
                                # Replay helper instance may start at a different
                                # epoch counter; actual IDs/content stay exact.
                                event.pop('epoch',None);event.pop('replaced',None)
                        return data
                    if strip_timings(new_events)!=strip_timings(row['native_events']):raise ValueError('native query/load receipt replay differs')
                    events.extend(row['native_events'])
                if n is not None:
                    observed_calls.extend(row['calls']);r=row['result']
                    if len(row['calls'])!=int(n.kind in ('deduction','revision') and 'proposal' in r):raise ValueError('unselected/missing formula call')
                    if 'commit' in r and r['status']=='PASS':
                        belief=r['commit']['belief']
                        if persisted.get(belief['belief_revision_id'])!=belief or belief['proposal']!=r['proposal'] or belief['pre_certificate_id']!=r['pre']['certificate_id'] or belief['post_certificate_id']!=r['post']['certificate_id']:
                            raise ValueError('selected commit not persisted with exact certificates')
                        commits+=1
            if observed_calls!=result['runtime_calls']:raise ValueError('formula call inventory differs')
            if (history.work,history.selections,history.acquisitions,history.stop)!=(result['work'],result['selections'],result['acquisitions'],result['stop']):raise ValueError('terminal budget/stop differs')
            for call in observed_calls:
                expected=wire(PinnedFormulaRuntime().evaluate(call['formula'],tuple(TruthValue(**t) for t in call['inputs'])))
                if expected!=call['result'] or (result['mode']=='native' and call['formula_agreement'] is not True):raise ValueError('formula conformance differs')
                calls+=1
            if result['arm']=='Goal-native' and events!=json.loads((directory/'native-events.json').read_text()):raise ValueError('native event inventory differs')
        finally:backend.close()
        with TemporaryDirectory() as tmp:
            db=Path(tmp)/'authority.db';shutil.copyfile(directory/'admission.db',db)
            with AdmissionService(database=db) as service:
                try:execution=service.export_execution_decision('attempt')
                except KeyError:execution=None
                recovered=(service.export_probability('ctx'),service.export_admission('ctx'),execution,service.inspect_lifecycle('episode'),service.inspect_goal('goal'),service.inspect_resource('slot'))
                if wire(recovered)!=result['reconstruction']['authority']:raise ValueError('checked SQLite replay differs')
        sequences[result['mode'],result['case_id'],result['budget'],result['arm']]=[cross_session_semantics(r) for r in rows]
    for key,seq in sequences.items():
        mode,case,budget,arm=key
        if arm=='Goal-native' and seq!=sequences[mode,case,budget,'Goal-scan']:raise ValueError('closed-loop recall-backend parity differs')
        if mode=='native' and ('finite',case,budget,arm) in sequences and seq!=sequences['finite',case,budget,arm]:raise ValueError('formula-mode parity differs')
    return dict(status='PASS',files=len(manifest['files']),executions=len(actual),matched_native_scan_states=pairs,
                native_query_reference_checks=queries,selected_operations=selected_count,persisted_selected_commits=commits,formulas_recomputed=calls,
                checks='native structural/Value load and query replay; independent source scans; exact candidates/witnesses/ranking/budgets; full SQLite replay; formula and cross-session semantic parity')


def readable(report):
    lines=['# Native AtomSpace-backed task recall','',f"Measured source: `{report['sources']['revision']}`.",
        'Same twelve development parents and work budgets; no new policy. Timings descriptive.','',
        '| Case | Formula | Budget | Recall arm | Check | Work | Certified loss | External loss |',
        '|---|---|---:|---|---|---:|---:|---:|']
    for r in report['results']:
        lines.append('| '+' | '.join(str(r.get(k,'unavailable')) for k in ('case_id','mode','budget','arm','conformance','work','outstanding','external_loss'))+' |')
    lines+=['','Goal-native/finite still uses actual native AtomSpace; Goal-native/native uses both native runtimes.',
      'Cold projection/startup/load/readback and same-epoch query costs are separate. Inclusive categories overlap.',
      'Full coherent export and full execution membership enumeration remain. SQLite is authoritative.',
      'Native process RSS and physical observation latency are unmeasured. Atom counts are not memory measurements.',
      'No pressure, persistent/incremental store, recovery subsystem or speed/scaling claim.']
    return '\n'.join(lines)+'\n'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);p.add_argument('--verify',type=Path)
    p.add_argument('--formula-modes',nargs='+',choices=('finite','native'),default=['finite','native']);p.add_argument('--allow-dirty',action='store_true')
    args=p.parse_args()
    if args.verify:print(json.dumps(verify(args.verify),indent=2))
    elif args.output:
        if run(args.output,modes=tuple(args.formula_modes),allow_dirty=args.allow_dirty)['conformance']!='PASS':raise SystemExit(1)
    else:p.error('--output or --verify required')


if __name__=='__main__':main()
