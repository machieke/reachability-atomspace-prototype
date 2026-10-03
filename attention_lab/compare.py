"""Fresh-output bounded attention cohort and source-bound semantic replay."""
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
from experimental_attention.controller import Agenda,MODES
from goal_pln_lab.cases import ROOT
from goal_pln_lab.compare import check_prefixes,cross_session_semantics
from native_recall_lab.compare import inputs as previous_inputs,request_args
from native_recall_lab.reference import answers
from reachability.adapter_runtime import verify_source,checked_run,lockfile,AdapterError
from reachability.service import AdmissionService
from reachability.pln_adapter import TruthValue
from reachability.probability_formula import PinnedFormulaRuntime
from validation_lab.audit_pressure_comparison import artifact_path
from validation_lab.decision_comparison import write,seal
from .cases import PARENTS
from .episode import run_case,settings
from .reference import Ledger


def inputs():
    names=set(previous_inputs())
    for pattern in ('experimental_attention/*.py','attention_lab/*.py','tests/test_attention*.py','integration_tests/test_attention*.py'):
        names.update(str(p.relative_to(ROOT)) for p in ROOT.glob(pattern))
    names.update(('ATTENTION.md','reviews/bounded-attention-v1/PROTOCOL.md'))
    return {n:sha256((ROOT/n).read_bytes()).hexdigest() for n in sorted(names)}


def source_binding(allow_dirty=False):
    rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();files=inputs();dirty=[]
    for n,v in files.items():
        r=subprocess.run(['git','show',rev+':'+n],cwd=ROOT,capture_output=True)
        if r.returncode or sha256(r.stdout).hexdigest()!=v:dirty.append(n)
    if dirty and not allow_dirty:raise ValueError('commit measured source first: '+str(dirty))
    return dict(revision=rev,files=files,dirty_inputs=dirty,baseline_publication='77e30ef5e51fce3b6236c1d842884738bb43733c')


def configuration():
    order=[];orders=list(permutations(MODES));cell=0
    for p in PARENTS:
        for capacity in (24,48):
            for queries in (16,48):
                for formula in (('finite','native') if cell%2==0 else ('native','finite')):
                    for mode in orders[cell%6]:order.append(dict(case_id=p['id'],capacity=capacity,queries=queries,formula_mode=formula,mode=mode,complete_mode=False))
                cell+=1
    for p in PARENTS[:2]:
        for formula in ('finite','native'):
            for mode in (*MODES,'Goal-native'):order.append(dict(case_id=p['id'],capacity=512,queries=4096,formula_mode=formula,mode=mode,complete_mode=True))
    return dict(schema='bounded-attention-cohort/v1',parents=PARENTS,seed=0,limits=wire(Limits(work=16)),run_order=order,
                primary_count=192,reference_count=16,policy='bounded-relevant-stop/v1',
                allocation=dict(total=1,root_seed=.8,cooling=.05,flow_steps=4,conductance=1),
                timing='one balanced/interleaved descriptive pass; concurrent regressions; no uncertainty estimate',
                unmeasured=['native RSS','physical observation latency','isolated native compute','OS filesystem cache effects'])


def folder(r):return ('complete' if r['complete_mode'] else 'primary')+f"-{r['formula_mode']}-{r['case_id']}-c{r['capacity']}-q{r['queries']}-{r['mode']}"


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
        r=run_case(parent,output/folder(entry),mode=entry['mode'],capacity=entry['capacity'],queries=entry['queries'],native=entry['formula_mode']=='native',complete=entry['complete_mode'])
        results.append(r);print(index+1,folder(entry),r['conformance'],r.get('outstanding'),r.get('error',''),flush=True)
    report=dict(schema='bounded-attention-comparison/v1',sources=sources,configuration_digest=digest(config),results=results,elapsed_ns=perf_counter_ns()-start,
                conformance='PASS' if all(r['conformance']=='PASS' for r in results) else 'FAIL')
    write(output/'report.json',report);(output/'comparison.md').write_text(readable(report));seal(output);return report


def without_times(value):
    if isinstance(value,list):return [without_times(v) for v in value]
    if isinstance(value,dict):return {k:without_times(v) for k,v in value.items() if not k.endswith('_ns')}
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
        history=Reference(limits=limits) if r['mode']=='Goal-native' else Agenda(r['mode'],limits,caps,search)
        reference=Reference(limits=limits) if r['complete_mode'] and r['mode']!='Goal-native' else None
        ledger=Ledger();observed=[]
        persisted={b['belief_revision_id']:b for v in r['reconstruction']['authority'][0][3] for b in v['historical']}
        try:
            for row in rows:
                view=Snapshot.from_records(row['public_records'])
                if view.binding!=row['public_binding']:raise ValueError('snapshot binding differs')
                if reference:
                    for name in ('round','selections','work','acquisitions','first_ready','attempted'):setattr(reference,name,copy.deepcopy(getattr(history,name)))
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
                    if rc!=c or candidates(rf.candidates)!=candidates(f.candidates) or reference.stop!=history.stop:raise ValueError('nonbinding Goal-native parity differs: '+folder(r))
                    if candidates(reference.diagnostic['eligible'])!=candidates(history.diagnostic['eligible']) or reference.diagnostic['ages']!=history.diagnostic['ages']:raise ValueError('nonbinding eligibility/age parity differs')
                    counts['matched_complete_reference_states']+=1;reference.backend.events.clear()
                if r['mode']!='Goal-native':
                    d=row['discovery'];counts['independent_field_steps']+=ledger.audit(d)
                    if not r['complete_mode'] and d['fallback']:raise ValueError('uncharged full-frontier rescue')
                    for metric,limit in {'active':'active','active_bytes':'active_bytes','arcs':'arcs','arc_bytes':'arc_bytes','candidates':'candidates','candidate_bytes':'candidate_bytes','response_records':'response_records','response_bytes':'response_bytes','joint_records':'joint_records','joint_bytes':'joint_bytes','joint_slots':'joint_slots','control_pins':'controls','control_bytes':'control_bytes','cached_answer_ids':'answer_ids','metadata_bytes':'metadata_bytes'}.items():
                        if d['peaks'].get(metric,0)>getattr(caps,limit):raise ValueError('workspace cap exceeded: '+metric)
                    if d['native_queries']>search.queries or d['tuple_visits']>limits.tuple_visits or d['field_steps']>4096:raise ValueError('discovery work cap exceeded')
                    before=len(history.ws.events);history.release()
                    if wire(history.ws.events[before:])!=row.get('release_events',[]):
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
        key=(r['complete_mode'],r['formula_mode'],r['case_id'],r['capacity'],r['queries'],r['mode'])
        sequences[key]=[cross_session_semantics(row) for row in rows];counts['executions']+=1
        print('audited',counts['executions'],folder(r),flush=True)
    for key,seq in sequences.items():
        complete,formula,case,capacity,queries,mode=key
        other=(complete,'finite',case,capacity,queries,mode)
        if formula=='native' and other in sequences and seq!=sequences[other]:raise ValueError('finite/native closed-loop semantics differ')
        other=(complete,formula,case,capacity,queries,'Goal-native')
        if complete and other in sequences and seq!=sequences[other]:raise ValueError('nonbinding closed-loop reference semantics differ')
    return dict(status='PASS',**counts,files=len(manifest['files']),checks='source/config/seal; matched snapshot native and candidate replay; independent source answers and dense transport/allocation ledger; complete-reference parity; exact persisted certificates; full SQLite replay; formulas and cross-session semantics')


def readable(report):
    lines=['# Bounded attention comparison','',f"Source: `{report['sources']['revision']}`.",'',
           'Eight engineering parents; 192 primary executions and 16 separate complete-frontier controls. Native recall in every run. One descriptive timing pass; parents are not independent replicas.','',
           '| Parent | Formula | Capacity | Queries | Mode | Complete mode | Check | Work | Certified loss | External loss | Elapsed s |',
           '|---|---|---:|---:|---|---|---|---:|---:|---:|---:|']
    for r in report['results']:
        lines.append('| '+' | '.join(str(r.get(k,'unavailable')) for k in ('case_id','formula_mode','capacity','queries','mode','complete_mode','conformance','work','outstanding','external_loss'))+f" | {r['elapsed_ns']/1e9:.3f} |")
    lines+=['','All inclusive cost categories in result.json overlap and must not be added. Field time includes revision guards and recording. Full snapshot export, native backing and final execution enumeration remain complete.','',
            'Native build verification/lifetime are unchanged. Native RSS, physical observation latency, isolated native compute and OS cache effects are unmeasured. No pressure-ranking, adaptive transport, persistence, recovery or scaling claim.']
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
