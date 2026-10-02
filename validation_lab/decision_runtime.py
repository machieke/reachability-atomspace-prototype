"""Evaluator bridge only: fixed policies, original authority, public static task.

The task contract is actually supplied on each policy's public port. Existing
rankers ignore the additional guarantees, preserving the frozen algorithms. No
reference answer, Q value, optimal action or witness crosses that boundary.
"""
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from time import perf_counter_ns

from reachability.pressure import PressureLimits
from reachability.pressure_session import ReasoningSession
from reachability.pressure_work import b0_ranking, enumerate_work, operation_cost
from reachability.trace_protocol import canonical, fingerprint
from . import run_pressure_comparison as runner
from . import audit_pressure_comparison as audit
from .pressure_episodes import ReasoningWorld
from .projection_comparison import ranking_policy
from .decision_tasks import materialize
from .decision_reference import State, STOP

POLICIES=['B0','B3-normalized-both','B3-normalized-route','B3-normalized-queue','B3-normalized-neither']


@contextmanager
def public_task(task):
    previous=runner.ReasoningWorld,audit.ReasoningWorld
    delivered=[]
    class StaticWorld(ReasoningWorld):
        def __init__(self,session,case):
            if case!=materialize(task): raise ValueError('world differs from public task contract')
            super().__init__(session,case)
        def port(self):
            port=super().port();port.task_contract=deepcopy(task)
            delivered.append(fingerprint(port.task_contract))
            return port
    try:
        runner.ReasoningWorld=audit.ReasoningWorld=StaticWorld
        yield delivered
    finally: runner.ReasoningWorld,audit.ReasoningWorld=previous


def semantic_action(candidate):
    row=candidate.wire() if hasattr(candidate,'wire') else candidate
    args=row['arguments'];kind=row['kind']
    return kind+'/'+args['rule_id' if kind=='derive' else 'goal_id']


def reference_state(task,snapshot,remaining):
    if snapshot['public_digest']!=fingerprint(task['public']): raise ValueError('unbound public state')
    if snapshot['rules']!=task['public']['admission']['rules'] or snapshot['clauses']!=task['public']['clauses']:
        raise ValueError('changed static task semantics')
    if any(s['valid_until'] is not None for s in snapshot['supports']): raise ValueError('unsupported support expiry')
    original={g['goal_id']:g for g in task['public']['goals']}
    for goal in snapshot['goals']:
        if (goal['condition']!=original[goal['goal_id']]['condition'] or goal['coverage'] or goal['selected_commitment'] is not None
            or goal['outstanding'] not in (0,original[goal['goal_id']]['loss'])):
            raise ValueError('unsupported goal lifecycle state')
    return State(tuple(sorted({s['literal'] for s in snapshot['supports']})),
        tuple(sorted(g['goal_id'] for g in snapshot['goals'] if g['outstanding']==0)),snapshot['time'],
        remaining['actions'],remaining['operation_work'],remaining['observation_work'])


def remaining_budget(budget,work):
    return {key:(None if key=='wall_ns' else budget[key]-work.get(key,0)) for key in budget if key in ('actions','operation_work','observation_work',
        'candidate_visits','ranking_states','pressure_iterations','wall_ns')}


def rank_fixed(task,snapshot,candidates,remaining,policy):
    """Each policy receives the identical complete model and affordable frontier."""
    from reachability import pressure_controller as controller
    start=perf_counter_ns();before=fingerprint(dict(task=task,snapshot=snapshot,candidates=[c.wire() for c in candidates]))
    with ranking_policy(policy) as measured:
        if policy=='B0':
            ranks,work,complete=b0_ranking(task['public'],snapshot,candidates,state_limit=remaining['ranking_states'])
            field=None
        else:
            if len(snapshot['goals'])*PressureLimits().iterations>remaining['pressure_iterations']:
                return dict(status='RANKING_EXHAUSTED',policy=policy,task_digest=fingerprint(task))
            ranks,field,_,_=controller.rank_b3(task['public'],snapshot,candidates,PressureLimits())
            complete=not any(x in field['exhausted'] for x in ('nodes','edges','sources'))
            work=field['work']
    audit.equal(fingerprint(dict(task=task,snapshot=snapshot,candidates=[c.wire() for c in candidates])),before,'ranking input immutability')
    selected=min(candidates,key=lambda c:(ranks[c.candidate_id],c.candidate_id)) if complete and candidates else None
    return dict(status='PASS' if complete else 'RANKING_EXHAUSTED',policy=policy,task_digest=fingerprint(task),
        selected=STOP if selected is None else semantic_action(selected),ranks=ranks,pressure=field,work=work,
        elapsed_ns=perf_counter_ns()-start,**measured)


def check_observable(task,reference,state,session,world):
    actual=reference_state(task,session.read(),dict(actions=state.requests,operation_work=state.operation_work,
        observation_work=state.observation_work))
    audit.equal(actual.wire(),state.wire(),'reference observable state')
    outcome=world.sample_outcomes();external,certified,goals=reference.losses(state)
    audit.require(outcome['external_weighted_loss']==external,'reference external loss')
    audit.require(outcome['certified_weighted_loss']==certified,'reference certified loss')
    for goal in outcome['goals']:
        weight=task['public']['priorities'][goal['goal_id']]['weight']
        audit.equal(goal['external_loss']*weight,goals[goal['goal_id']]['external'],'reference per-goal external loss')
        audit.equal(goal['certified_outstanding']*weight,goals[goal['goal_id']]['certified'],'reference per-goal certified loss')


def execute_prefix(task,reference,session,world,prefix,emit=None):
    state=reference.initial()
    for action in prefix:
        check_observable(task,reference,state,session,world)
        if action==STOP: break
        snapshot=session.read();frontier=enumerate_work(task['public'],snapshot)
        affordable=[c for c in frontier.candidates if operation_cost(task['public'],c)<=state.operation_work and c.observation_cost<=state.observation_work]
        audit.equal(sorted(semantic_action(c) for c in affordable),sorted(a for a in reference.actions(state) if a!=STOP),'independent admissible frontier')
        if action==STOP: break
        candidate=next(c for c in affordable if semantic_action(c)==action)
        if emit: emit(dict(stage='selection',snapshot=snapshot,candidates=[c.wire() for c in frontier.candidates],selected=candidate.wire(),state=state.wire()))
        receipt=world.execute(candidate,fingerprint(snapshot))
        audit.equal(receipt['status'],'PASS','certified reference witness execution')
        state=reference.successor(state,action)
        if emit: emit(dict(stage='receipt',receipt=receipt,state=state.wire()))
    check_observable(task,reference,state,session,world)
    return state


def witness(task,reference,label,path):
    """Reference labels request real operations; they confer no authority."""
    path=Path(path);path.mkdir(parents=True,exist_ok=False);start=perf_counter_ns()
    with (path/'trace.jsonl').open('w') as stream,ReasoningSession(task['public'],path) as session:
        world=ReasoningWorld(session,materialize(task));world.sample_outcomes()
        state=execute_prefix(task,reference,session,world,label['witness'],lambda row:stream.write(canonical(row)+'\n'))
        world.idle_until(task['contract']['horizon']);final=world.sample_outcomes()
        loss=sum(row['external_weighted_loss'] for row in world.outcomes[:-1])
        audit.require(loss==label['value'],'certified witness integrated loss')
        audit.require(final['certified_weighted_loss']==label['terminal_certified'],'certified witness terminal relief')
        metrics=dict(session.metrics.values);tip=session.service._journal_sequence
        stream.write(canonical(dict(stage='stop',state=state.wire(),final=final,integrated_loss=loss))+'\n')
        return dict(status='PASS',witness=label['witness'],integrated_loss=loss,final=final,outcomes=world.outcomes,
            terminal_state=state.wire(),metrics=metrics,journal_commands=tip,elapsed_ns=perf_counter_ns()-start)
