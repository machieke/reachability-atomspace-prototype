"""Independent labels plus deterministic search replay and real authority replay."""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter_ns

from experimental_planning.model import Model, STOP, action_name
from experimental_planning.controller import Planner
from experimental_planning.search import search, Limits
from reachability.pressure_session import ReasoningSession
from reachability.pressure_work import enumerate_work, operation_cost
from reachability.trace_protocol import fingerprint
from . import audit_pressure_comparison as audit
from . import decision_comparison as old
from . import projection_comparison as projection
from .decision_reference import State as RefState
from .decision_runtime import public_task, execute_prefix, rank_fixed, reference_state
from .decision_tasks import materialize
from .pressure_episodes import ReasoningWorld
from .planning_comparison import (load, rows, verify_sources, inventory, REVIEW, decision_labels,
                                  search_summary, action_name_wire)


def timeless(value):
    if isinstance(value,dict): return {k:timeless(v) for k,v in value.items() if not k.endswith('_ns')}
    if isinstance(value,(list,tuple)):return [timeless(v) for v in value]
    return value


def ref_state(wire):
    return RefState(tuple(wire['supports']),tuple(wire['monitored']),wire['tick'],wire['requests'],wire['operation_work'],wire['observation_work'])


def check_plan(ref,root,plan):
    state=root;acc=0
    audit.require(bool(plan['plan']) and plan['plan'][-1]==STOP and STOP not in plan['plan'][:-1],'complete STOP continuation')
    for action in plan['plan'][:-1]:
        audit.require(action in ref.actions(state),'independent plan legality')
        acc+=ref.losses(state)[0];state=ref.successor(state,action)
    external,certified,_=ref.losses(state)
    audit.require(plan['value']==acc+(16-state.tick)*external,'independent STOP tail value')
    audit.equal(plan['terminal_certified'],certified,'independent terminal certified loss')
    audit.equal(plan['terminal_external'],external,'independent terminal external loss')
    audit.equal(plan['operation_work'],root.operation_work-state.operation_work,'exact plan operation charge')
    audit.equal(plan['observation_work'],root.observation_work-state.observation_work,'exact plan observation charge')
    audit.equal(plan['requests'],root.requests-state.requests,'exact plan requests')
    audit.equal(ref_state(plan['terminal']).wire(),state.wire(),'plan terminal budgets and support state')


def check_search(task,snapshot,remaining,result,ref,*,suffix=None):
    model=Model(task,snapshot,remaining);root=reference_state(task,snapshot,remaining)
    audit.equal(result['root'],model.root.wire(),'model root')
    audit.equal(result['snapshot_binding'],fingerprint(snapshot),'exact search snapshot')
    audit.equal(result['model_binding'],model.binding,'exact public model binding')
    limits=Limits(**result['limits'])
    audit.require(result['work']['attempts']<=limits.attempts,'attempt bound')
    check_plan(ref,root,result['incumbent'])
    for row in result['records']:
        if row['kind']=='visit':
            check_plan(ref,root,row['closure'])
            audit.equal(ref_state(row['state']).wire(),ref_state(row['closure']['terminal']).wire(),'visited state closure')
        elif row['kind']=='expansion':
            state=ref_state(row['state'])
            audit.equal(row['candidates'],[a for a in ref.actions(state) if a!=STOP],'same speculative legal successor set')
    for plan in result['improvements']:check_plan(ref,root,plan)
    # Replay from recorded public inputs only, never reference labels. Primary
    # deterministic executions must reproduce the full search prefix/counters.
    # Wall runs reproduce the visited prefix at their recorded attempt count;
    # terminal boundary interruption may have omitted the final visited closure.
    replay_limits=replace(limits,wall_ns=60_000_000_000)
    timed='wall_ns' in result['bounds']
    if timed: replay_limits=replace(replay_limits,attempts=result['work']['attempts'])
    replay=search(model,result['arm'],replay_limits,suffix=suffix)
    if not timed:
        for key in ('incumbent','work','records','improvements','status','bounds','suffix_status'):
            audit.equal(timeless(result[key]),timeless(replay[key]),'deterministic search '+key)
    else:
        # Verify recorded expansion/visit sequence as a prefix, including ranks;
        # a final expansion may complete after the deadline and be interrupted
        # before recording, so require only the recorded prefix, never invent it.
        saved=timeless(result['records']);fresh=timeless(replay['records'])
        if len(saved)>len(fresh):
            # The cap stopped replay before an expansion at the final visited
            # state, while wall search may already have ordered that state.
            replay=search(model,result['arm'],replace(replay_limits,attempts=replay_limits.attempts+1),suffix=suffix)
            fresh=timeless(replay['records'])
        audit.equal(saved,fresh[:len(saved)],'wall-limited deterministic search prefix')
        candidates=[r.get('closure',r.get('incumbent')) for r in result['records'] if r['kind'] in ('visit','initial_stop')]
        candidates+=result['improvements']
        from experimental_planning.model import objective
        audit.equal(objective(result['incumbent']),min(map(objective,candidates)),'wall incumbent selected by common objective')
    if result['status']=='COMPLETE_SEARCH':
        audit.equal(result['incumbent']['value'],ref.solve(root)['value'],'complete search reference optimum')
        audit.equal(result['incumbent']['plan'],ref.solve(root)['witness'],'complete search canonical witness')
    return len([r for r in result['records'] if r['kind']=='visit'])


def check_common(path,task,b,ref):
    sample=load(path/'result.json');snapshot=sample['snapshot'];remaining=sample['remaining']
    state=reference_state(task,snapshot,remaining)
    audit.equal(state.wire(),sample['state'],'common independent state')
    frontier=enumerate_work(task['public'],snapshot)
    candidates=[c for c in frontier.candidates if operation_cost(task['public'],c)<=state.operation_work and c.observation_cost<=state.observation_work]
    audit.equal([c.wire() for c in frontier.candidates],sample['all_candidates'],'common complete frontier')
    audit.equal([c.wire() for c in candidates],sample['candidates'],'common affordable frontier')
    visits=0
    for row in sample['rankings']:
        config=row['configuration'];result=load(path/row['path'])
        if config['mode']=='direct':
            fresh=rank_fixed(task,snapshot,candidates,remaining,config['arm'])
            audit.equal(timeless(result),timeless(fresh),'common frozen direct ranking')
            selected=result['selected']
        else:
            visits+=check_search(task,snapshot,remaining,result,ref)
            selected=result['incumbent']['plan'][0]
            audit.equal(row['search'],search_summary(result,ref.solve(state)['value']),'common offline search labels')
        audit.equal(row['label'],old.selected_label(ref,state,selected),'independent common decision label')
        audit.equal(row['discovery_ns'],sample['discovery_ns'],'equal charged discovery time')
        audit.equal(row['candidate_visits'],frontier.visits,'equal charged discovery visits')
    with TemporaryDirectory() as tmp,ReasoningSession(task['public'],tmp) as session:
        world=ReasoningWorld(session,materialize(task));world.sample_outcomes()
        execute_prefix(task,ref,session,world,sample['prefix'])
        audit.equal(audit.semantic_snapshot(session.read()),audit.semantic_snapshot(snapshot),'common actual prefix replay')
        audit.equal(old.journal_signature(session.service,task['public']['context_id']),sample['journal_signature'],'common journal replay')
    audit.equal(old.save_signature(path,task),sample['journal_signature'],'common saved journal')
    old.check_saved_prefix(path,task,rows(path/'prefix.jsonl'),snapshot)
    return visits


def check_closed(path,task,b,ref):
    entry=load(path/'result.json');result=entry['result'];config=entry['policy'];trace=rows(path/'trace.jsonl')
    audit.equal(entry['labels'],decision_labels(task,b['budget'],ref,result,trace),'closed independent decision labels')
    if config['mode']=='direct':
        with public_task(task),projection.ranking_policy(config['arm']):
            audit.audit_run(path,materialize(task),b,result)
        old.check_projection(dict(result=result,**entry['projection']),trace)
        return dict(searches=0,visits=0,operations=len(result['selected']))
    searches=visits=0;previous=None;suffix=None;receipts=[];selected=[];summaries=[]
    retention_checker=Planner(task['public'],config['arm'])
    with TemporaryDirectory() as tmp,ReasoningSession(task['public'],tmp) as session:
        world=ReasoningWorld(session,materialize(task));world.sample_outcomes()
        audit.equal(audit.semantic_snapshot(session.read()),audit.semantic_snapshot(result['initial_snapshot']),'planner initial public snapshot')
        for i,row in enumerate(trace):
            if row['stage']=='search':
                audit.equal(audit.semantic_snapshot(session.read()),audit.semantic_snapshot(row['snapshot']),'planner observed state replay')
                model=Model(task,row['snapshot'],row['remaining'])
                retained=retention_checker.retained
                expected_retention='absent' if retained is None else ('revalidated' if
                    retained[:3]==(fingerprint(row['snapshot']),model.binding,model.root.semantic()) else 'discarded_incompatible_binding')
                audit.equal(row['result']['retention'],expected_retention,'observed revision suffix binding')
                suffix=retained[3] if expected_retention=='revalidated' else None
                visits+=check_search(task,row['snapshot'],row['remaining'],row['result'],ref,suffix=suffix)
                state=reference_state(task,row['snapshot'],row['remaining'])
                summaries.append(search_summary(row['result'],ref.solve(state)['value']))
                previous=row['result'];searches+=1
            elif row['stage']=='selection':
                snapshot=session.read();frontier=enumerate_work(task['public'],snapshot)
                audit.equal(row['snapshot_digest'],fingerprint(row['snapshot']),'planner live request binding')
                audit.equal([c.wire() for c in frontier.candidates],row['candidates'],'planner shared candidate frontier')
                action=action_name_wire(row['selected'])
                audit.equal(action,previous['incumbent']['plan'][0],'execute first selected plan operation')
                candidate=next(c for c in frontier.candidates if c.wire()==row['selected'])
                receipt=world.execute(candidate,fingerprint(snapshot));saved=trace[i+1]['receipt']
                audit.equal(receipt['status'],saved['status'],'actual gate result');audit.equal(saved['status'],'PASS','unexpected operation failure')
                audit.equal(receipt['knowledge_revision'],saved['knowledge_revision'],'receipt revision')
                audit.equal(audit.authority_work(receipt['costs']),audit.authority_work(saved['costs']),'receipt work')
                receipts.append(saved);selected.append(dict(kind=candidate.kind,arguments=dict(candidate.arguments),status=receipt['status']))
                after=next((future['snapshot'] for future in trace[i+2:] if future['stage']=='search'),result['controller_stop_snapshot'])
                audit.equal(audit.semantic_snapshot(after),audit.semantic_snapshot(session.read()),'observed post-operation suffix state')
                remain={k:b['budget'][k]-row['work'][k] for k in ('actions','operation_work','observation_work')}
                before=dict(remain);before['actions']+=1;before['operation_work']+=operation_cost(task['public'],candidate)
                before['observation_work']+=candidate.observation_cost
                saved_model=Model(task,row['snapshot'],before)
                retention=retention_checker.retain(saved_model,previous,candidate,saved,after,remain)
                audit.equal(trace[i+2]['stage'],'retention','retention trace framing')
                audit.equal(trace[i+2]['status'],retention,'common suffix validation')
                audit.equal(trace[i+2]['snapshot_binding'],fingerprint(after),'observed post-receipt binding')
        audit.equal(audit.semantic_snapshot(session.read()),audit.semantic_snapshot(result['controller_stop_snapshot']),'planner stop snapshot')
        world.idle_until(16);final=world.sample_outcomes()
        audit.equal(world.outcomes,result['outcomes'],'independent real external outcome sequence')
        audit.equal(final,result['final'],'terminal external versus monitored outcomes')
        audit.equal(sum(r['external_weighted_loss'] for r in world.outcomes[:-1]),result['integrated_external_loss'],'integrated closed loss')
        audit.equal(old.journal_signature(session.service,task['public']['context_id']),entry['journal_signature'],'planner replay journal')
    audit.equal(selected,result['selected'],'selected operations result')
    audit.equal(summaries,entry['searches'],'closed search summaries')
    audit.equal(old.save_signature(path,task),entry['journal_signature'],'planner saved journal')
    old.check_saved_prefix(path,task,trace,result['final_snapshot'])
    audit.audit_costs(result,receipts)
    return dict(searches=searches,visits=visits,operations=len(selected))


def audit_experiment(directory):
    directory=Path(directory);started=perf_counter_ns();binding=load(directory/'source.json');verify_sources(binding)
    config=load(directory/'configuration.json');audit.equal(config,inventory(load(REVIEW/'calibration.json')),'immutable configuration')
    bundle=load(directory/'bundle.json')
    actual={str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file() and p.name!='bundle.json'}
    audit.equal(sorted(actual),sorted(bundle['files']),'complete bundle inventory')
    for name,digest in bundle['files'].items():audit.equal(sha256(audit.artifact_path(directory,name).read_bytes()).hexdigest(),digest,'artifact '+name)
    index=load(directory/'index.json');audit.equal(len(index),156,'complete task/budget cells')
    closed=common=visits=searches=operations=0
    for cell in index:
        task=cell['task'];b=cell['configuration'];ref,data=old.reference_cell(task,b)
        saved=load(directory/cell['name']/'reference.json')
        audit.equal(timeless(saved),timeless(data),'independent reference DP/enumeration')
        audit.require(cell['status']=='EXACT','reference-exhausted cell retained')
        expected=config['primary']+(config['supplementary'] if task['partition']=='new-confirmation' else [])
        audit.equal(sorted(Path(p).name for p in cell['closed']),sorted(c['name'] for c in expected),'closed configuration matrix')
        samples=ref.sampled_states();audit.equal(len(cell['common']),len(samples),'common sample coverage')
        for relative in cell['closed']:
            counts=check_closed(directory/relative,task,b,ref)
            closed+=1;visits+=counts['visits'];searches+=counts['searches'];operations+=counts['operations']
        for relative,(state,prefix) in zip(cell['common'],samples):
            sample=load(directory/relative/'result.json')
            audit.equal(sample['prefix'],prefix,'predeclared reference-only sampling')
            audit.equal(sorted(r['configuration']['name'] for r in sample['rankings']),sorted(c['name'] for c in expected),'common configuration matrix')
            visits+=check_common(directory/relative,task,b,ref);common+=1
        if (closed%100)<20: print(f'audit: {closed} closed runs, {common} common states',flush=True)
    from .planning_analysis import summarize
    audit.equal(load(directory/'summary.json'),summarize(directory,index),'complete analysis reproduction')
    audit.require(not load(directory/'failures.json'),'retained failures require explicit correction')
    verify_sources(binding)
    return dict(status='PASS',closed=closed,common=common,closed_searches=searches,visited_closures=visits,
        actual_operations=operations,elapsed_ns=perf_counter_ns()-started,
        timing_limitation='Historical durations are checked for accounting, not reproduced; wall search semantic prefixes are replayed.')
