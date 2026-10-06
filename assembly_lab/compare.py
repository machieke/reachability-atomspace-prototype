"""Fresh-output shared protected-assembly cohort and source-bound semantic replay."""
import argparse,copy,json,shutil,subprocess
from collections import Counter
from hashlib import sha256
from itertools import permutations
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter_ns
from experimental_online_pln.agenda import Limits,Snapshot,wire,digest
from experimental_native_recall.agenda import Agenda as Reference
from experimental_native_recall.backend import verify_build
from experimental_attention.controller import Agenda as FrozenAgenda,MODES
from experimental_assembly.controller import Agenda,CONTRACTS
from goal_pln_lab.cases import ROOT
from goal_pln_lab.compare import check_prefixes,cross_session_semantics
from attention_lab.compare import inputs as previous_inputs
from native_recall_lab.compare import request_args
from native_recall_lab.reference import answers
from reachability.adapter_runtime import verify_source,checked_run,lockfile,AdapterError
from reachability.service import AdmissionService
from reachability.pln_adapter import TruthValue
from reachability.probability_formula import PinnedFormulaRuntime
from validation_lab.audit_pressure_comparison import artifact_path
from validation_lab.decision_comparison import write,seal
from .cases import PARENTS
from .episode import run_case,settings
from attention_lab.reference import Ledger
from .reference import ServiceLedger


def inputs():
    names=set(previous_inputs())
    for pattern in ('experimental_assembly/*.py','assembly_lab/*.py','tests/test_assembly.py','integration_tests/test_assembly.py'):
        names.update(str(p.relative_to(ROOT)) for p in ROOT.glob(pattern))
    names.update(('ASSEMBLY_RECALL.md','reviews/completion-aware-recall-v1/PROTOCOL.md'))
    return {n:sha256((ROOT/n).read_bytes()).hexdigest() for n in sorted(names)}


def source_binding(allow_dirty=False):
    rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();files=inputs();dirty=[]
    for n,v in files.items():
        r=subprocess.run(['git','show',rev+':'+n],cwd=ROOT,capture_output=True)
        if r.returncode or sha256(r.stdout).hexdigest()!=v:dirty.append(n)
    if dirty and not allow_dirty:raise ValueError('commit measured source first: '+str(dirty))
    return dict(revision=rev,files=files,dirty_inputs=dirty,baseline_publication='71c32df66d1c08143621f1e4c6005da31fac2565',baseline_measured='0134092b9766f8fc9a9a1735cee8b7f2372e830c')


def configuration():
    order=[];orders=list(permutations(MODES));cell=0
    for p in PARENTS:
        for queries in (16,48):
            for formula in (('finite','native') if cell%2==0 else ('native','finite')):
                for contract in (CONTRACTS if cell%2==0 else tuple(reversed(CONTRACTS))):
                    for mode in orders[cell%6]:order.append(dict(case_id=p['id'],capacity=48,queries=queries,formula_mode=formula,contract=contract,mode=mode,complete_mode=False))
            cell+=1
    return dict(schema='completion-aware-recall-cohort/v1',parents=PARENTS,seed=0,limits=wire(Limits(work=16)),run_order=order,
                primary_count=192,reference_count=0,policy='bounded-relevant-stop/v1',
                reservation=dict(join_queries=6,missing_producer=1,prepare_queries=6,slots=1,native_view_queries=4096),
                allocation=dict(total=1,root_seed=.8,cooling=.05,flow_steps=4,conductance=1),
                timing='one balanced/interleaved descriptive pass; concurrent applicable regressions; no uncertainty estimate',
                unmeasured=['native RSS','physical observation latency','isolated native compute','OS filesystem cache effects','standalone SQLite fsync'])


def folder(r):return f"primary-{r['contract']}-{r['formula_mode']}-{r['case_id']}-c{r['capacity']}-q{r['queries']}-{r['mode']}"


def run(output,allow_dirty=False):
    output=Path(output)
    if output.exists():raise ValueError('fresh output required')
    sources=source_binding(allow_dirty);config=configuration();output.mkdir(parents=True)
    write(output/'sources.json',sources);write(output/'configuration.json',config)
    for n in sources['files']:
        p=output/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,p)
    try:
        verify_build(ROOT/'artifacts')
        for name in ('pln','petta'):verify_source(name,ROOT/'artifacts')
        if not checked_run(['swipl','--version']).startswith(f"SWI-Prolog version {lockfile()['toolchain']['swipl']} "):raise AdapterError('SWI pin mismatch')
    except Exception as e:
        write(output/'blocked.json',dict(status='BLOCKED',error=str(e),python_substitution=False));raise
    for name in ('adapter-build.json','recall-build.json'):shutil.copyfile(ROOT/'artifacts'/name,output/name)
    shutil.copyfile(ROOT/'adapters.lock.json',output/'adapters.lock.json')
    start=perf_counter_ns();results=[]
    for index,entry in enumerate(config['run_order']):
        parent=next(p for p in PARENTS if p['id']==entry['case_id'])
        r=run_case(parent,output/folder(entry),contract=entry['contract'],mode=entry['mode'],capacity=entry['capacity'],queries=entry['queries'],native=entry['formula_mode']=='native',complete=entry['complete_mode'])
        results.append(r);print(index+1,folder(entry),r['conformance'],r.get('outstanding'),r.get('error',''),flush=True)
    report=dict(schema='completion-aware-recall-comparison/v1',sources=sources,configuration_digest=digest(config),results=results,elapsed_ns=perf_counter_ns()-start,
                conformance='PASS' if all(r['conformance']=='PASS' for r in results) else 'FAIL')
    write(output/'report.json',report)
    from .analyze import analyze
    analysis=analyze(output,report);write(output/'analysis.json',analysis)
    (output/'comparison.md').write_text(readable(report)+'\nPaired certified-loss results (configuration/formula repeats):\n\n```json\n'+json.dumps(analysis['summary'],indent=2)+'\n```\n');seal(output);return report


def without_times(value):
    if isinstance(value,list):return [without_times(v) for v in value]
    if isinstance(value,dict):return {k:without_times(v) for k,v in value.items() if not k.endswith('_ns') and k!='trace_bytes'}
    return value


def candidates(values):return {c['logical_id']:c for c in wire(values)}


def verify(output,allow_development=False):
    output=Path(output);manifest=json.loads((output/'bundle.json').read_text())
    for n,v in manifest['files'].items():
        if sha256(artifact_path(output,n).read_bytes()).hexdigest()!=v:raise ValueError('bundle artifact changed: '+n)
    report=json.loads((output/'report.json').read_text());config=json.loads((output/'configuration.json').read_text())
    if (report['sources']['dirty_inputs'] and not allow_development) or digest(config)!=report['configuration_digest'] or wire(config)!=wire(configuration()):raise ValueError('dirty source or changed preregistered configuration')
    for n,v in report['sources']['files'].items():
        if sha256(artifact_path(output,'source/'+n).read_bytes()).hexdigest()!=v or sha256((ROOT/n).read_bytes()).hexdigest()!=v:raise ValueError('auditor/source mismatch: '+n)
    if not allow_development and [folder(r) for r in report['results']]!=[folder(e) for e in config['run_order']]:raise ValueError('incomplete/duplicate/out-of-order matrix')
    counts=Counter();sequences={}
    for r in report['results']:
        directory=output/folder(r)
        if r['conformance']!='PASS' or json.loads((directory/'result.json').read_text())!=r:raise ValueError('failed or mismatched result: '+folder(r))
        rows=[json.loads(t) for t in (directory/'trace.jsonl').read_text().splitlines()];check_prefixes(rows,r)
        caps,search=settings(r['capacity'],r['queries'],r['complete_mode']);limits=Limits(work=16)
        history=Agenda(r['contract'],r['mode'],limits,caps,search)
        reference=FrozenAgenda(r['mode'],limits,caps,search) if r['contract']=='frozen' else None
        ledger=Ledger();service_ledger=ServiceLedger();observed=[]
        persisted={b['belief_revision_id']:b for v in r['reconstruction']['authority'][0][3] for b in v['historical']}
        try:
            for row in rows:
                view=Snapshot.from_records(row['public_records'])
                if view.binding!=row['public_binding']:raise ValueError('snapshot binding differs')
                f,c=history.choose(view);counts['replayed_states']+=1
                if wire(c)!=row['selected'] or candidates(f.candidates)!=candidates(row['frontier']['candidates']) or f.complete!=row['frontier']['complete']:raise ValueError('candidate/selection replay differs: '+folder(r))
                if without_times(wire(history.diagnostic))!=without_times(row['discovery']):raise ValueError('discovery/field/workspace replay differs: '+folder(r))
                if (history.work,history.acquisitions)!=(row['work'],row['acquisitions']):raise ValueError('work accounting differs')
                if without_times(wire(history.backend.events))!=without_times(row['native_events']):raise ValueError('native receipt replay differs')
                history.backend.events.clear()
                for e in row['native_events']:
                    if e['kind']=='query':
                        q=e['result'];expected=answers(view,q['request']['kind'],**request_args(q['request']))
                        if not q['complete'] or tuple(q['ids'])!=expected or q['view_id']!=view.binding:raise ValueError('native/reference query differs')
                        counts['independent_native_query_checks']+=1
                if reference:
                    rf,rc=reference.choose(view)
                    if rc!=c or candidates(rf.candidates)!=candidates(f.candidates) or reference.stop!=history.stop:raise ValueError('frozen scheduling parity differs: '+folder(r))
                    if candidates(reference.diagnostic['eligible'])!=candidates(history.diagnostic['eligible']) or reference.diagnostic['ages']!=history.diagnostic['ages']:raise ValueError('frozen eligibility/age parity differs')
                    if without_times(wire(reference.backend.events))!=without_times(row['native_events']):raise ValueError('frozen query stream differs')
                    fields=lambda d:[e for e in d['events'] if e['kind'] in ('seed','field','cool','route','evict','pin_bundle')]
                    clean=lambda d:[{k:v for k,v in e.items() if k not in ('at_query','at_episode_query','at_ns')} for e in fields(d)]
                    if clean(reference.diagnostic)!=clean(history.diagnostic):raise ValueError('frozen allocation/retention differs')
                    counts['matched_frozen_states']+=1;reference.backend.events.clear()
                    if c is not None:reference.release()
                if r['mode']!='Goal-native':
                    d=row['discovery'];counts['independent_field_steps']+=ledger.audit(d)
                    service_ledger.audit(d,caps,search,limits,row['native_events'])
                    if not r['complete_mode'] and d['fallback']:raise ValueError('uncharged full-frontier rescue')
                    for metric,limit in {'active':'active','active_bytes':'active_bytes','arcs':'arcs','arc_bytes':'arc_bytes','candidates':'candidates','candidate_bytes':'candidate_bytes','response_records':'response_records','response_bytes':'response_bytes','joint_records':'joint_records','joint_bytes':'joint_bytes','joint_slots':'joint_slots','control_pins':'controls','control_bytes':'control_bytes','cached_answer_ids':'answer_ids','metadata_bytes':'metadata_bytes','trace_bytes':'trace_bytes'}.items():
                        if d['peaks'].get(metric,0)>getattr(caps,limit):raise ValueError('workspace cap exceeded: '+metric)
                    if d['native_queries']>search.queries or d['tuple_visits']>limits.tuple_visits or d['field_steps']>4096:raise ValueError('discovery work cap exceeded')
                    before=len(history.ws.events);history.release()
                    if without_times(wire(history.ws.events[before:]))!=without_times(row.get('release_events',[])):
                        # Terminal rows have no selected bundle to release.
                        if c is not None:raise ValueError('selected pins release differs')
                if c is not None:
                    counts['selected_operations']+=1;actual=row['result'];observed.extend(row['calls'])
                    if len(row['calls'])!=int(c.kind in ('deduction','revision') and 'proposal' in actual):raise ValueError('unselected/missing formula call')
                    if actual['status']=='STALE':counts['stale_selections']+=1
                    if actual['status']=='PASS' and 'commit' in actual:
                        b=actual['commit']['belief']
                        if persisted.get(b['belief_revision_id'])!=b or b['proposal']!=actual['proposal'] or b['pre_certificate_id']!=actual['pre']['certificate_id'] or b['post_certificate_id']!=actual['post']['certificate_id']:raise ValueError('commit/certificate persistence differs')
                        counts['persisted_selected_commits']+=1
            if observed!=r['runtime_calls']:raise ValueError('formula inventory differs')
            if (history.work,history.selections,history.acquisitions,history.stop)!=(r['work'],r['selections'],r['acquisitions'],r['stop']):raise ValueError('terminal accounting differs')
            for call in observed:
                expected=wire(PinnedFormulaRuntime().evaluate(call['formula'],tuple(TruthValue(**t) for t in call['inputs'])))
                if expected!=call['result'] or (r['formula_mode']=='native' and call['formula_agreement'] is not True):raise ValueError('formula disagreement')
                counts['formulas_recomputed']+=1
        finally:
            history.backend.close()
            if reference:reference.backend.close()
        with TemporaryDirectory() as tmp:
            db=Path(tmp)/'authority.db';shutil.copyfile(directory/'admission.db',db)
            with AdmissionService(database=db) as service:
                try:execution=service.export_execution_decision('attempt')
                except KeyError:execution=None
                recovered=(service.export_probability('ctx'),service.export_admission('ctx'),execution,service.inspect_lifecycle('episode'),service.inspect_goal('goal'),service.inspect_resource('slot'))
                if wire(recovered)!=r['reconstruction']['authority']:raise ValueError('SQLite replay differs')
        counts.update({'service_'+k:v for k,v in service_ledger.counts.items()})
        key=(r['contract'],r['formula_mode'],r['case_id'],r['capacity'],r['queries'],r['mode'])
        sequences[key]=[cross_session_semantics(row) for row in rows];counts['executions']+=1
        print('audited',counts['executions'],folder(r),flush=True)
    for key,seq in sequences.items():
        contract,formula,case,capacity,queries,mode=key
        other=(contract,'finite',case,capacity,queries,mode)
        if formula=='native' and other in sequences and seq!=sequences[other]:raise ValueError('finite/native closed-loop semantics differ')
    from .analyze import analyze
    if json.loads((output/'analysis.json').read_text())!=analyze(output,report):raise ValueError('derived recorded analysis differs')
    return dict(status='PASS',**counts,files=len(manifest['files']),checks='source/config/seal; matched snapshot native and candidate replay; independent source answers and dense transport/allocation ledger; frozen policy parity; independent FIFO reservation and service ledger; exact persisted certificates; full SQLite replay; formulas and cross-session semantics')


def readable(report):
    lines=['# Shared protected-assembly comparison','',f"Source: `{report['sources']['revision']}`.",'',
           'Eight engineering parents (two reused diagnostics, six constructed variations); 192 executions. Native recall in every run. One descriptive timing pass; configurations are not independent tasks.','',
           '| Parent | Formula | Queries | Contract | Orderer | Check | Work | Certified loss | External loss | Elapsed s |',
           '|---|---|---:|---|---|---|---:|---:|---:|---:|']
    for r in report['results']:
        lines.append('| '+' | '.join(str(r.get(k,'unavailable')) for k in ('case_id','formula_mode','queries','contract','mode','conformance','work','outstanding','external_loss'))+f" | {r['elapsed_ns']/1e9:.3f} |")
    lines+=['','Inclusive/nested costs must not be added. Field kernel excludes guard reads and field-event logging but includes bookkeeping. Full snapshot export, native backing and final execution enumeration remain complete.','',
            'Native build verification/lifetime are unchanged. Native RSS, physical observation latency, isolated native compute, standalone SQLite fsync and OS cache effects are unmeasured. No tuning, adaptive transport, persistence, recovery or scaling claim.']
    return '\n'.join(lines)+'\n'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);p.add_argument('--verify',type=Path);p.add_argument('--allow-dirty',action='store_true');p.add_argument('--audit-after',action='store_true')
    a=p.parse_args()
    if a.verify:print(json.dumps(verify(a.verify),indent=2))
    elif a.output:
        report=run(a.output,a.allow_dirty)
        if report['conformance']!='PASS':raise SystemExit(1)
        if a.audit_after:print(json.dumps(verify(a.output),indent=2))
    else:p.error('--output or --verify required')


if __name__=='__main__':main()
