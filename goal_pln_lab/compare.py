"""Source-bound three-arm finite/native experiment. Use a fresh --output path."""
import argparse
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
from time import perf_counter_ns
import traceback

from experimental_online_pln.agenda import Limits, Snapshot, digest, wire
from experimental_goal_pln.agenda import Agenda, ARMS
from experimental_goal_pln.session import Session
from experimental_goal_pln.relevance import ClosureLimits
from reachability.adapter_runtime import verify_native_build
from reachability.probability_formula import PinnedFormulaRuntime
from reachability.pln_adapter import TruthValue
from reachability.service import AdmissionService
from reachability.trace_protocol import canonical
from validation_lab.online_pln_conformance import inputs as baseline_inputs, summary
from validation_lab.audit_pressure_comparison import artifact_path
from validation_lab.decision_comparison import seal, write
from .cases import ROOT, World, configuration


def check_prefixes(rows, result):
    for row in rows:
        state = row['after']
        if state['hard_forecast'] != 'UNKNOWN':
            raise AssertionError('numeric estimate became hard authority')
        if not state['product_observed'] and (state['outstanding'] != 10 or row['external_loss'] != 10):
            raise AssertionError('forecast/reservation/ACK became relief')
        if row.get('selected'):
            actual = row['result']
            if row['selected']['kind'] == 'deduction' and actual['status'] == 'PASS':
                if actual['post_status'] != 'PASS' or len(actual['post']['joint_witness']) != 8:
                    raise AssertionError('missing full selected three-proposition certificate')
            if actual.get('post_status') == 'STALE' and actual.get('commit',{}).get('belief'):
                raise AssertionError('stale numeric commit')
        if state['effects'] > 1:
            raise AssertionError('duplicate executor effect')
    if result['case_id'] == 'change-blocked' and result['effects']:
        raise AssertionError('contrary/low confidence bypassed globally informed gate')
    if result['case_id'] in ('change-replacement','change-producer') and not any(
        r.get('result',{}).get('post_status') == 'STALE' for r in rows):
        raise AssertionError('declared boundary injection did not reject stale proposal')


def run_case(fixture, directory, *, arm, budget, native=False, rename=False, reverse=False):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    limits = Limits(work=budget)
    world, agenda = World(fixture), Agenda(arm, limits)
    start, rows, landmarks = perf_counter_ns(), [], {}
    result = dict(case_id=fixture['id'], arm=arm, budget=budget, mode='native' if native else 'finite',
                  diagnostic=dict(rename=rename,reverse=reverse))
    with Session(directory,native=native,limits=limits,acquire=world.acquire) as session:
        try:
            setup_start=perf_counter_ns()
            world.setup(session,rename=rename,reverse=reverse)
            session.costs['world_setup_ns'] += perf_counter_ns()-setup_start
            initial=summary(session)
            for name,ready in dict(decision=initial['decision']=='PASS',dispatch=initial['dispatch']=='accepted',
                                   product=initial['product_observed'],durable_relief=initial['outstanding']==0).items():
                if ready:
                    landmarks[name]=dict(work=0,requests=0,selections=0,
                        logical_tick=session.service.snapshot(session.initial.context_id).logical_time,
                        wall_ns=perf_counter_ns()-start,initial_condition=True)
            with (directory/'trace.jsonl').open('x') as trace:
                while True:
                    snapshot=session.read()
                    frontier, selected=agenda.choose(snapshot)
                    serial_start=perf_counter_ns()
                    row=dict(step=agenda.selections,public_records=snapshot.records(),public_binding=snapshot.binding,
                             frontier=wire(frontier),selected=wire(selected),discovery=agenda.diagnostic,
                             work=agenda.work,acquisitions=agenda.acquisitions)
                    session.costs['public_serialization_ns']+=perf_counter_ns()-serial_start
                    if selected is not None:
                        calls,receipts=len(session.runtime.calls),len(session.receipts)
                        actual=session.execute(selected)
                        row['result']=wire(actual)
                        row['before_external_event']=summary(session)
                        world.after(selected,actual)
                        row.update(calls=wire(session.runtime.calls[calls:]),receipts=wire(session.receipts[receipts:]))
                    else:
                        row['stop']=agenda.stop
                    row.update(after=summary(session),external_loss=world.external_loss,
                               logical_tick=session.service.snapshot(session.initial.context_id).logical_time)
                    for name,ready in dict(decision=row['after']['decision']=='PASS',
                        dispatch=row['after']['dispatch']=='accepted',product=row['after']['product_observed'],
                        durable_relief=row['after']['outstanding']==0).items():
                        if ready and name not in landmarks:
                            landmarks[name]=dict(work=agenda.work,requests=agenda.acquisitions,
                                selections=agenda.selections,logical_tick=row['logical_tick'],wall_ns=perf_counter_ns()-start)
                    rows.append(row)
                    serial_start=perf_counter_ns()
                    trace.write(canonical(row)+'\n');trace.flush()
                    session.costs['trace_serialization_write_ns']+=perf_counter_ns()-serial_start
                    if selected is None:
                        break
            result.update(summary(session),external_loss=world.external_loss,stop=agenda.stop,
                          selections=agenda.selections,work=agenda.work,acquisitions=agenda.acquisitions,
                          landmarks=landmarks,tuple_visits=agenda.tuple_visits)
            result['reconstruction']=session.project_and_reopen()
            check_prefixes(rows,result)
            result['conformance']='PASS'
        except Exception as error:
            result.update(conformance='FAIL',error=type(error).__name__+': '+str(error),traceback=traceback.format_exc())
        finally:
            result.update(costs_ns=dict(session.costs),discovery_costs_ns=dict(agenda.costs),
                          runtime_calls=wire(session.runtime.calls),seams=wire(world.seams))
            write(directory/'receipts.json',wire(session.receipts))
    result['elapsed_ns']=perf_counter_ns()-start
    write(directory/'result.json',result)
    return result


def inputs():
    names=set(baseline_inputs())
    for pattern in ('experimental_goal_pln/*.py','goal_pln_lab/*.py','tests/test_goal_pln*.py',
                    'integration_tests/test_goal_pln*.py'):
        names.update(str(p.relative_to(ROOT)) for p in ROOT.glob(pattern))
    names.update(('reviews/goal-directed-online-pln-v1/PROTOCOL.md','reviews/goal-directed-online-pln-v1/fixtures.json'))
    return {n:sha256((ROOT/n).read_bytes()).hexdigest() for n in sorted(names)}


def source_binding(allow_dirty=False):
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    files=inputs();dirty=[]
    for name,value in files.items():
        old=subprocess.run(['git','show',revision+':'+name],cwd=ROOT,capture_output=True)
        if old.returncode or sha256(old.stdout).hexdigest()!=value:
            dirty.append(name)
    if dirty and not allow_dirty:
        raise ValueError('commit measured inputs first: '+str(dirty))
    return dict(revision=revision,files=files,dirty_inputs=dirty,
                baseline_publication='3f433ed1cfe31758be40128a4466935599e38714')


def folder_name(mode,case,budget,arm):
    return f'{mode}-{case}-w{budget}-{arm}'


def run(output, *, modes=('finite','native'), allow_dirty=False):
    output=Path(output)
    if output.exists():
        raise ValueError('use a fresh output directory')
    sources=source_binding(allow_dirty)
    output.mkdir(parents=True)
    config=dict(configuration(),arms=ARMS,modes=modes,limits=wire(Limits()),closure_limits=wire(ClosureLimits()),
                execution_revalidation='frozen-full-enumeration/v1',wall_cap=None)
    write(output/'configuration.json',config);write(output/'sources.json',sources)
    for name in sources['files']:
        target=output/'source'/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/name,target)
    if 'native' in modes:
        try:
            verify_native_build(ROOT/'artifacts')
        except Exception as error:
            write(output/'blocked.json',dict(status='BLOCKED',requirement='pinned native build',error=str(error),fallback=False))
            raise
        shutil.copyfile(ROOT/'artifacts/adapter-build.json',output/'adapter-build.json')
        shutil.copyfile(ROOT/'adapters.lock.json',output/'adapters.lock.json')
    start,results=perf_counter_ns(),[]
    for mode in modes:
        for fixture in config['fixtures']:
            for budget in config['budgets']:
                for arm in ARMS:
                    r=run_case(fixture,output/folder_name(mode,fixture['id'],budget,arm),arm=arm,budget=budget,native=mode=='native')
                    results.append(r)
                    print(mode,fixture['id'],budget,arm,r['conformance'],r.get('error',''),flush=True)
    diagnostics=[]
    for fixture in (f for f in config['fixtures'] if f['id'] in ('route-distractors','path-alternatives')):
        for transformation in ('rename','reorder'):
            for budget in config['budgets']:
                for arm in ARMS:
                    mode='diagnostic-'+transformation
                    r=run_case(fixture,output/'diagnostics'/folder_name(mode,fixture['id'],budget,arm),
                        arm=arm,budget=budget,rename=transformation=='rename',reverse=transformation=='reorder')
                    diagnostics.append(dict(transformation=transformation,**r))
                    print(mode,fixture['id'],budget,arm,r['conformance'],flush=True)
    report=dict(schema='goal-pln-comparison/v1',diagnostics=diagnostics,sources=sources,configuration_digest=digest(config),results=results,
                elapsed_ns=perf_counter_ns()-start,conformance='PASS' if all(r['conformance']=='PASS' for r in results+diagnostics) else 'FAIL')
    write(output/'report.json',report)
    (output/'comparison.md').write_text(readable(report))
    from .analyze import analyze
    write(output/'analysis.json',analyze(output))
    seal(output)
    return report


def semantic_diagnostic(d):
    return {k:v for k,v in d.items() if k not in ('arm','index_entries','source_tuple_visits','capacity_full_scan') and k!='closure'} | {
        'closure':{k:v for k,v in d.get('closure',{}).items() if k!='elapsed_ns'}}


def replay_pair(snapshot, history, limits):
    pair=[]
    for arm in ARMS[1:]:
        a=Agenda(arm,limits)
        for name in ('round','selections','work','acquisitions','first_ready','attempted'):
            import copy
            setattr(a,name,copy.deepcopy(getattr(history,name)))
        frontier,selected=a.choose(snapshot)
        pair.append((a,frontier,selected))
    left,right=pair
    if (left[2]!=right[2] or left[0].diagnostic.get('relevant')!=right[0].diagnostic.get('relevant')
        or left[0].diagnostic.get('witnesses')!=right[0].diagnostic.get('witnesses')
        or left[0].diagnostic.get('eligible')!=right[0].diagnostic.get('eligible')
        or left[0].stop!=right[0].stop):
        raise AssertionError('scan/index relevant candidates, witnesses, eligibility or choice differ')
    return pair


def verify(output):
    output=Path(output)
    manifest=json.loads((output/'bundle.json').read_text())
    for name,checksum in manifest['files'].items():
        if sha256(artifact_path(output,name).read_bytes()).hexdigest()!=checksum:
            raise ValueError('bundle artifact changed: '+name)
    report=json.loads((output/'report.json').read_text());config=json.loads((output/'configuration.json').read_text())
    if report['sources']['dirty_inputs'] or digest(config)!=report['configuration_digest']:
        raise ValueError('dirty source or altered configuration')
    for name,checksum in report['sources']['files'].items():
        if sha256(artifact_path(output,'source/'+name).read_bytes()).hexdigest()!=checksum:
            raise ValueError('source changed: '+name)
    expected={(m,f['id'],b,a) for m in config['modes'] for f in config['fixtures'] for b in config['budgets'] for a in config['arms']}
    actual={(r['mode'],r['case_id'],r['budget'],r['arm']) for r in report['results']}
    if expected!=actual or len(actual)!=len(report['results']):
        raise ValueError('incomplete/duplicated run matrix')
    checked=selected_count=0;semantics={}
    for result in report['results']:
        folder=output/folder_name(result['mode'],result['case_id'],result['budget'],result['arm'])
        if json.loads((folder/'result.json').read_text())!=result or result['conformance']!='PASS':
            raise ValueError('failed or mismatched result')
        rows=[json.loads(line) for line in (folder/'trace.jsonl').read_text().splitlines()]
        check_prefixes(rows,result)
        a=Agenda(result['arm'],Limits(work=result['budget']))
        calls=[]
        for row in rows:
            snapshot=Snapshot.from_records(row['public_records'])
            if snapshot.binding!=row['public_binding']:
                raise ValueError('snapshot binding changed')
            replay_pair(snapshot,a,a.limits);checked+=1
            frontier,selected=a.choose(snapshot)
            if wire(selected)!=row['selected'] or wire(frontier.candidates)!=row['frontier']['candidates'] or frontier.complete!=row['frontier']['complete']:
                raise ValueError('selection/frontier replay differs')
            if row['work']!=a.work or row['acquisitions']!=a.acquisitions:
                raise ValueError('work accounting changed')
            if result['arm']!='FIFO-full' and semantic_diagnostic(a.diagnostic)!=semantic_diagnostic(row['discovery']):
                raise ValueError('relevance/ranking replay differs')
            selected_count+=selected is not None
            calls.extend(row.get('calls',[]))
        if calls!=result['runtime_calls']:
            raise ValueError('unrecorded numerical call')
        for call in calls:
            value=PinnedFormulaRuntime().evaluate(call['formula'],tuple(TruthValue(**t) for t in call['inputs']))
            if wire(value)!=call['result'] or (result['mode']=='native' and call['formula_agreement'] is not True):
                raise ValueError('selected formula differs from independent finite checker')
        if (a.selections,a.work,a.acquisitions,a.stop)!=(result['selections'],result['work'],result['acquisitions'],result['stop']):
            raise ValueError('budget/stop replay differs')
        with TemporaryDirectory() as tmp:
            db=Path(tmp)/'authority.db';shutil.copyfile(folder/'admission.db',db)
            with AdmissionService(database=db) as s:
                try: execution=s.export_execution_decision('attempt')
                except KeyError: execution=None
                recovered=(s.export_probability('ctx'),s.export_admission('ctx'),execution,s.inspect_lifecycle('episode'),s.inspect_goal('goal'),s.inspect_resource('slot'))
                if wire(recovered)!=result['reconstruction']['authority']:
                    raise ValueError('persisted authority reconstruction differs')
        semantics[result['mode'],result['case_id'],result['budget'],result['arm']]=[
            (r['selected'],r.get('result',{}).get('status'),r['after'],r['external_loss']) for r in rows]
    for mode,case,budget,arm in semantics:
        if arm=='Goal-scan' and semantics[mode,case,budget,arm]!=semantics[mode,case,budget,'Goal-index']:
            raise ValueError('closed-loop scan/index semantic trajectories differ')
        if mode=='native' and ('finite',case,budget,arm) in semantics and semantics[mode,case,budget,arm]!=semantics['finite',case,budget,arm]:
            raise ValueError('finite/native semantic trajectories differ')
    return dict(status='PASS',files=len(manifest['files']),executions=len(actual),matched_snapshot_pairs=checked,
                selected_operations=selected_count,checked='integrity, source/config, independent traversal/full-enumeration parity, exact ranking, budgets, formulas, prefixes, SQLite replay, semantic mode/arm parity')


def readable(report):
    lines=['# Goal-directed discovery comparison','',f"Measured source: `{report['sources']['revision']}`. Twelve parents; seed 0.",'',
      '| Case | Mode | Work budget | Arm | Check | Used | Loss | External | Calls | Stop |',
      '|---|---|---:|---|---|---:|---:|---:|---:|---|']
    for r in report['results']:
        lines.append('| '+' | '.join(str(r.get(k,'unavailable')) for k in ('case_id','mode','budget','arm','conformance','work','outstanding','external_loss'))+
                     ' | '+str(len(r['runtime_calls']))+' | '+r.get('stop','failure')+' |')
    lines+=['','B versus A changes selection; C versus B changes discovery only. Cold index construction and',
       'full execution membership enumeration are charged. SQLite stays authoritative; native AtomSpace is',
       'a disposable projection. Local three-proposition certificates do not imply global joint consistency.',
       'Inclusive timings overlap: do not add them. SQL/fsync, RSS, native compute separate from startup, and',
       'physical sensor latency are unmeasured. Logical time advances on received events; it is not wall benefit.',
       'Correct blocking is not deployment success. No pressure/transport/recovery/persistent-index claim.']
    return '\n'.join(lines)+'\n'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path);p.add_argument('--verify',type=Path)
    p.add_argument('--modes',nargs='+',choices=('finite','native'),default=['finite','native'])
    p.add_argument('--allow-dirty',action='store_true')
    args=p.parse_args()
    if args.verify: print(json.dumps(verify(args.verify),indent=2))
    elif args.output:
        r=run(args.output,modes=tuple(args.modes),allow_dirty=args.allow_dirty)
        if r['conformance']!='PASS': raise SystemExit(1)
    else: p.error('--output or --verify required')


if __name__=='__main__': main()
