"""Source-bound bounded planner comparison; fresh output and mandatory audit."""
import argparse
from contextlib import contextmanager
from collections import Counter
from dataclasses import asdict, replace
from hashlib import sha256
import json
from pathlib import Path
import platform
import statistics
import subprocess
from tempfile import TemporaryDirectory
from time import perf_counter_ns

from experimental_planning.controller import Planner
from experimental_planning.model import Model, action_name, STOP
from experimental_planning.search import ARMS, Limits
from reachability.pressure_session import ReasoningSession
from reachability.pressure_work import enumerate_work, operation_cost
from reachability.trace_protocol import canonical, fingerprint
from . import audit_pressure_comparison as audit
from . import decision_comparison as old
from . import projection_comparison as projection
from . import run_pressure_comparison as runner
from .decision_reference import Reference
from .decision_runtime import public_task, rank_fixed, reference_state, execute_prefix
from .decision_tasks import budgets, materialize
from .planning_tasks import cohort, new_cohort
from .planning_mutations import witnesses
from .pressure_episodes import ReasoningWorld

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'reviews/pressure-guided-planning-v1'
VERSION='pressure-guided-planning/v1'
DIRECT=('B0','B3-normalized-both')


def write(path,value): old.write(path,value)
def load(path): return json.loads(Path(path).read_text())
def rows(path): return [json.loads(x) for x in Path(path).read_text().splitlines()]


def configurations(calibration):
    main=[dict(name=p,arm=p,mode='direct',limits=None) for p in DIRECT]
    main += [dict(name=arm+'-n'+str(n),arm=arm,mode='attempts',limits=asdict(Limits(attempts=n)))
             for n in (1,4,16,64) for arm in ARMS]
    wall=[dict(name=arm+'-time'+str(ns),arm=arm,mode='wall',
               limits=asdict(Limits(attempts=100000,wall_ns=ns)))
          for ns in calibration['wall_caps_ns'] for arm in ARMS]
    return main,wall


def calibrate():
    # No search, scores, policy or evaluator answer. Warmup and 100 recorded
    # repetitions of public Model + enumeration + one lexical transition.
    task=next(t for t in cohort() if t['task_id']=='completion-1');b=budgets()[1]['budget']
    samples=[]
    with TemporaryDirectory() as tmp,ReasoningSession(task['public'],tmp) as session:
        ReasoningWorld(session,materialize(task));snapshot=session.read()
        for index in range(110):
            start=perf_counter_ns();model=Model(task,snapshot,b)
            candidates=model.frontier(model.root)
            model.advance(model.root,min(candidates,key=action_name))
            if index>=10: samples.append(perf_counter_ns()-start)
    median=statistics.median(samples)
    caps=[max(1_000_000,int((median*mult+999999)//1000000)*1000000) for mult in (10,50)]
    return dict(schema='policy-free-planning-calibration/v1',policy_measurements=0,task='completion-1',
        samples_ns=samples,median_ns=median,wall_caps_ns=caps,python=platform.python_version(),platform=platform.platform(),
        rule='ceil to milliseconds of 10x and 50x median model+frontier+one transition, minimum 1ms')


def inventory(calibration):
    main,wall=configurations(calibration)
    return dict(schema=VERSION,tasks=cohort(),budgets=budgets(),primary=main,supplementary=wall,
        seeds=[0],primary_closed_runs=len(cohort())*2*len(main),supplementary_closed_runs=12*2*len(wall),
        common_sampling='root plus lexicographic reference state at ticks 1..3 with >=2 operations; independent per task',
        rotation='left by task/budget cell index',objective='integrated external loss ticks 0..15',
        secondary='terminal certified loss, operation work, requests, lexicographic action sequence')


def preflight():
    REVIEW.mkdir(exist_ok=True,parents=True)
    calibration=load(REVIEW/'calibration.json') if (REVIEW/'calibration.json').exists() else calibrate()
    write(REVIEW/'calibration.json',calibration)
    config=inventory(calibration);write(REVIEW/'inventory.json',config)
    feasible=[]
    for task in new_cohort():
        for b in budgets():
            _,data=old.reference_cell(task,b)
            feasible.append(dict(configuration=b['name'],**data))
    write(REVIEW/'feasibility.json',dict(policy_measurements=0,cells=feasible))
    print(json.dumps(dict(new_cells=len(feasible),exact=sum(r['reference']['status']=='EXACT' for r in feasible),
        wall_caps_ns=calibration['wall_caps_ns'],primary_runs=config['primary_closed_runs'],wall_runs=config['supplementary_closed_runs'])))


def own_files():
    return sorted(str(p.relative_to(ROOT)) for pattern in ('experimental_planning/*.py','validation_lab/planning_*.py',
        'tests/test_pressure_planning*.py') for p in ROOT.glob(pattern))+[
        'reviews/pressure-guided-planning-v1/'+x for x in ('PROTOCOL.md','inventory.json','calibration.json','feasibility.json')]


def sources():
    previous=old.source_binding()
    previous['experiment_revision']='7bf11d5282542c870dfd270613db2b46fc031321'
    old.verify_sources(previous)
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();files={}
    for name in own_files():
        blob=(ROOT/name).read_bytes()
        if blob!=subprocess.check_output(['git','show',head+':'+name],cwd=ROOT): raise ValueError('uncommitted input '+name)
        files[name]=sha256(blob).hexdigest()
    preserved={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for name in
        ('decision-value-v1','pressure-projection-v1','b0-b3-3e8fd7b') for p in (ROOT/'reviews'/name).glob('*') if p.is_file()}
    return dict(schema=VERSION,experiment_revision=head,previous_publication='2dfe1846c1c870d7daa9268b9e700289fbd34b8d',
        previous=previous,files=files,preserved_reviews=preserved)


def verify_sources(binding):
    audit.equal(binding['schema'],VERSION,'planning harness version');old.verify_sources(binding['previous'])
    audit.equal(sorted(binding['files']),sorted(own_files()),'planning source inventory')
    for name,digest in binding['files'].items():
        audit.equal(sha256((ROOT/name).read_bytes()).hexdigest(),digest,'planning source '+name)
        audit.equal(sha256(subprocess.check_output(['git','show',binding['experiment_revision']+':'+name],cwd=ROOT)).hexdigest(),digest,'committed planning input')
    for name,digest in binding['preserved_reviews'].items():
        audit.equal(sha256((ROOT/name).read_bytes()).hexdigest(),digest,'preserved review '+name)


@contextmanager
def planner_controller(config):
    previous=runner.ComparisonController
    try:
        runner.ComparisonController=lambda public,variant,limits: Planner(public,config['arm'],search_limits=Limits(**config['limits']))
        yield
    finally: runner.ComparisonController=previous


def decision_labels(task,budget,ref,result,trace):
    labels=[]
    for i,row in enumerate(trace):
        if row['stage']!='selection':continue
        work=dict(row['work']);action=action_name_wire(row['selected'])
        work['actions']-=1
        work['operation_work']-=task['public']['costs'][row['selected']['arguments']['rule_id']] if row['selected']['kind']=='derive' else 1
        work['observation_work']-=row['selected']['observation_cost']
        remaining={k:budget[k]-work[k] for k in ('actions','operation_work','observation_work')}
        state=reference_state(task,row['snapshot'],remaining)
        labels.append(dict(step=row['step'],**old.selected_label(ref,state,action),
            receipt=trace[i+1]['receipt'],outcome_before=result['outcomes'][state.tick],outcome_after=result['outcomes'][state.tick+1]))
    remaining={k:budget[k]-result['work'][k] for k in ('actions','operation_work','observation_work')}
    state=reference_state(task,result['controller_stop_snapshot'],remaining)
    return dict(decisions=labels,stop=old.selected_label(ref,state,STOP),episode_gap=result['integrated_external_loss']-ref.solve()['value'])


def action_name_wire(row): return row['kind']+'/'+row['arguments']['rule_id' if row['kind']=='derive' else 'goal_id']


def search_summary(result,reference_value):
    records=result['records'];qualities=[r for r in records if r['kind'] in ('initial_stop','visit')]
    found=[]
    for row in qualities:
        plan=row.get('closure',row.get('incumbent'))
        if plan['value']==reference_value: found.append(dict(attempts=row['attempts'],elapsed_ns=row['elapsed_ns']))
    for row in result['improvements']:
        if row['value']==reference_value:found.append(dict(attempts=row['attempts'],elapsed_ns=row['elapsed_ns']))
    return dict(status=result['status'],bounds=result['bounds'],work=result['work'],elapsed_ns=result['elapsed_ns'],
        model_validation_ns=result.get('model_validation_ns',0),
        value=result['incumbent']['value'],plan=result['incumbent']['plan'],suffix_status=result['suffix_status'],
        first_optimal_witness=min(found,key=lambda r:(r['attempts'],r['elapsed_ns'])) if found else None,
        expanded_states=[fingerprint({k:v for k,v in r['state'].items() if k not in ('model_binding','root_binding')})
                         for r in records if r['kind']=='expansion'],
        visited_states=[fingerprint({k:v for k,v in r['state'].items() if k not in ('model_binding','root_binding')})
                        for r in records if r['kind']=='visit'],improvements=result['improvements'])


def run_closed(task,b,config,ref,path):
    start=perf_counter_ns()
    if config['mode']=='direct':
        with public_task(task) as delivered,projection.ranking_policy(config['arm']) as measured:
            result=runner.run_one(materialize(task),'B0' if config['arm']=='B0' else 'B3',b,path)
        extra=measured
    else:
        with public_task(task) as delivered,planner_controller(config):
            result=runner.run_one(materialize(task),'B0',b,path)
        extra={};result['variant']=config['arm']
    audit.equal(delivered,[fingerprint(task)],'identical public descriptor delivery')
    trace=rows(path/'trace.jsonl');labels=decision_labels(task,b['budget'],ref,result,trace)
    searches=[]
    for row in trace:
        if row['stage']=='search':
            state=reference_state(task,row['snapshot'],row['remaining'])
            searches.append(search_summary(row['result'],ref.solve(state)['value']))
    if config['mode']!='direct':
        construction=sum(s['work']['normalization_ns']+s['work']['graph_ns'] for s in searches)
        iteration=sum(s['work']['pressure_iteration_ns'] for s in searches)
        enumeration=sum(s['work']['enumeration_ns'] for s in searches)
        result['costs_ns']['ranking_ns']-=construction+iteration+enumeration
        result['costs_ns']['candidate_discovery_ns']+=enumeration
        result['costs_ns']['pressure_construction_ns']=construction
        result['costs_ns']['pressure_iteration_ns']=iteration
        result['planner_retention_ns']=sum(r['elapsed_ns'] for r in trace if r['stage']=='retention')
        fields=[r['pressure'] for row in trace if row['stage']=='search' for r in row['result']['records']
                if r['kind']=='expansion' and r['pressure'] is not None]
        fields += [r['field'] for row in trace if row['stage']=='search' for r in row['result']['records'] if r['kind']=='field_failure']
        result['pressure_converged']=all(f['converged'] for f in fields)
        result['pressure_exhausted']=sorted({bound for f in fields for bound in f['exhausted']})
    entry=dict(schema=VERSION,task_id=task['task_id'],configuration=b,policy=config,
        result=result,labels=labels,searches=searches,projection=extra,journal_signature=old.save_signature(path,task),
        wrapper_elapsed_ns=perf_counter_ns()-start)
    write(path/'result.json',entry);return entry


def common(task,b,ref,state,prefix,configs,path):
    path.mkdir(parents=True);start=perf_counter_ns();rankings=[]
    with ReasoningSession(task['public'],path) as session, (path/'prefix.jsonl').open('w') as stream:
        world=ReasoningWorld(session,materialize(task));world.sample_outcomes()
        execute_prefix(task,ref,session,world,prefix,lambda row:stream.write(canonical(row)+'\n'))
        snapshot=session.read();clock=perf_counter_ns();frontier=enumerate_work(task['public'],snapshot)
        discovery_ns=perf_counter_ns()-clock
        remaining=dict(actions=state.requests,operation_work=state.operation_work,observation_work=state.observation_work,
            candidate_visits=b['budget']['candidate_visits']-frontier.visits,ranking_states=b['budget']['ranking_states'],
            pressure_iterations=b['budget']['pressure_iterations'],wall_ns=None)
        candidates=[c for c in frontier.candidates if operation_cost(task['public'],c)<=state.operation_work and c.observation_cost<=state.observation_work]
        before=fingerprint(snapshot);commands=session.service._journal_sequence
        for config in configs:
            if config['mode']=='direct':
                out=rank_fixed(task,snapshot,candidates,remaining,config['arm']);selected=out['selected'];summary=None
            else:
                planner=Planner(task['public'],config['arm'],search_limits=Limits(**config['limits']))
                _,out=planner.decide(task,snapshot,remaining);selected=out['incumbent']['plan'][0]
                summary=search_summary(out,ref.solve(state)['value'])
            filename=config['name']+'.json';write(path/filename,out)
            rankings.append(dict(configuration=config,selected=selected,label=old.selected_label(ref,state,selected),
                search=summary,elapsed_ns=out['elapsed_ns'],discovery_ns=discovery_ns,candidate_visits=frontier.visits,path=filename))
        audit.equal(fingerprint(session.read()),before,'planner public input immutability')
        audit.equal(session.service._journal_sequence,commands,'read-only planning journal')
    result=dict(task_id=task['task_id'],budget=b,remaining=remaining,state=state.wire(),prefix=prefix,snapshot=snapshot,
        candidates=[c.wire() for c in candidates],all_candidates=[c.wire() for c in frontier.candidates],
        discovery_ns=discovery_ns,rankings=rankings,elapsed_ns=perf_counter_ns()-start,
        journal_signature=old.save_signature(path,task))
    write(path/'result.json',result);return result


def seal(directory):
    files={str(p.relative_to(directory)):sha256(p.read_bytes()).hexdigest() for p in directory.rglob('*')
           if p.is_file() and p.name!='bundle.json'}
    write(directory/'bundle.json',dict(schema='planning-review-bundle/v1',files=files))


def run(output):
    output.mkdir(parents=True,exist_ok=False);started=perf_counter_ns();binding=sources()
    calibration=load(REVIEW/'calibration.json');config=inventory(calibration)
    audit.equal(config,load(REVIEW/'inventory.json'),'preregistered inventory')
    write(output/'source.json',binding);write(output/'configuration.json',config)
    write(output/'environment.json',dict(python=platform.python_version(),platform=platform.platform(),seeds=[0]))
    write(output/'mutations.json',witnesses())
    main,wall=configurations(calibration);index=[];failures=[]
    for ti,task in enumerate(cohort()):
        for bi,b in enumerate(budgets()):
            cell_index=ti*2+bi;name=task['task_id']+'/'+b['name'];cellpath=output/name
            ref,data=old.reference_cell(task,b);write(cellpath/'reference.json',data)
            cell=dict(task=task,configuration=b,name=name,closed=[],common=[],status=data['reference']['status'])
            index.append(cell)
            if data['reference']['status']!='EXACT': failures.append(dict(cell=name,error='REFERENCE_EXHAUSTED'));continue
            configs=main+(wall if task['partition']=='new-confirmation' else [])
            rotated=configs[cell_index%len(configs):]+configs[:cell_index%len(configs)]
            for configrow in rotated:
                relative=name+'/closed/'+configrow['name'];path=output/relative
                try:
                    run_closed(task,b,configrow,ref,path);cell['closed'].append(relative)
                except Exception as error:
                    path.mkdir(parents=True,exist_ok=True)
                    failure=dict(cell=name,configuration=configrow,error_type=type(error).__name__,error=str(error))
                    write(path/'failure.json',failure);failures.append(failure)
            for sample_index,(state,prefix) in enumerate(ref.sampled_states()):
                relative=name+'/common/'+str(sample_index)
                try:
                    common(task,b,ref,state,prefix,rotated,output/relative);cell['common'].append(relative)
                except Exception as error:
                    failure=dict(cell=name,sample=sample_index,error_type=type(error).__name__,error=str(error))
                    write(output/relative/'failure.json',failure);failures.append(failure)
            write(output/'index.json',index);write(output/'failures.json',failures)
            print(json.dumps(dict(cell=cell_index+1,total=156,task=task['task_id'],budget=b['name'],failures=len(failures))),flush=True)
    verify_sources(binding)
    write(output/'execution.json',dict(status='PASS' if not failures else 'FAIL',elapsed_ns=perf_counter_ns()-started,
        cells=len(index),closed=sum(len(c['closed']) for c in index),common=sum(len(c['common']) for c in index)))
    from .planning_analysis import summarize,readable
    summary=summarize(output,index)
    write(output/'summary.json',summary)
    (output/'comparison.md').write_text(readable(summary,binding['experiment_revision']))
    seal(output)
    from .planning_audit import audit_experiment
    try: report=audit_experiment(output)
    except Exception as error:
        write(output/'audit.json',dict(status='FAIL',error_type=type(error).__name__,error=str(error)));raise
    write(output/'audit.json',report);seal(output)
    if failures: raise RuntimeError('retained experiment failures')
    print(json.dumps(report),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path);parser.add_argument('--preflight',action='store_true')
    parser.add_argument('--audit-only',type=Path)
    args=parser.parse_args()
    if args.preflight:preflight()
    elif args.audit_only:
        from .planning_audit import audit_experiment
        print(json.dumps(audit_experiment(args.audit_only),indent=2))
    elif args.output:run(args.output)
    else:parser.error('supply --preflight, --output NEW_DIRECTORY, or --audit-only DIRECTORY')


if __name__=='__main__':main()
