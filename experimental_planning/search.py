"""One anytime explicit-stack DFS. Scores order children, never incumbents."""
from dataclasses import asdict, dataclass
from time import perf_counter_ns

from experimental_pressure.ranking import rank_projected
from experimental_pressure.projection import ProjectionBlocked
from reachability.pressure import PressureLimits
from reachability.pressure_work import b0_ranking
from reachability.trace_protocol import canonical, fingerprint
from .model import STOP, Unsupported, action_name, objective

ARMS=('PLAN-neutral','PLAN-B0-order','PLAN-pressure-order')


@dataclass(frozen=True)
class Limits:
    attempts: int = 64
    candidate_visits: int = 1_000_000
    ranking_states: int = 2_000_000
    pressure_iterations: int = 262_144
    normalization_visits: int = 1_000_000
    memory_bytes: int = 32*1024*1024
    wall_ns: int = 5_000_000_000

    def __post_init__(self):
        if any(type(v) is not int or v<0 for v in asdict(self).values()):
            raise ValueError('nonnegative integer planner bounds required')
        if self.attempts>100000 or self.memory_bytes>512*1024*1024:
            raise ValueError('planner capacity exceeded')


class Bound(RuntimeError): pass


def counters():
    return dict(attempts=0,rejections=0,visited=0,expanded=0,enumeration_calls=0,candidate_visits=0,
        consistency_checks=0,transition_checks=0,sorting_items=0,ranking_calls=0,ranking_states=0,
        ranking_transitions=0,ranking_joint_checks=0,pressure_calls=0,pressure_iterations=0,
        pressure_edge_visits=0,normalization_visits=0,projected_occurrences=0,
        suffix_steps=0,interrupted_expansions=0,memory_accounting_bytes=4096,
        peak_stack_frames=1,enumeration_ns=0,transition_ns=0,sorting_ns=0,b0_ns=0,
        normalization_ns=0,graph_ns=0,pressure_iteration_ns=0,suffix_validation_ns=0,
        objective_ns=0,trace_accounting_ns=0)


def search(model,arm,limits=Limits(),*,suffix=None,start_ns=None):
    if arm not in ARMS: raise ValueError('unknown ordering arm')
    started=perf_counter_ns() if start_ns is None else start_ns
    work=counters(); records=[]; updates=[]; bounds=[]
    incumbent=model.closure(model.root)
    def elapsed(): return perf_counter_ns()-started
    def guard():
        if elapsed()>=limits.wall_ns: raise Bound('wall_ns')
        if work['memory_accounting_bytes']>limits.memory_bytes: raise Bound('memory_bytes')
    def record(row):
        clock=perf_counter_ns()
        row['elapsed_ns']=elapsed();row['attempts']=work['attempts']
        # Conservative serialized allocation charge including Python container
        # allowance. Not measured RSS; stack is depth <= 9 with <= 11 children.
        work['memory_accounting_bytes']+=1088+4*len(canonical({k:v for k,v in row.items() if k!='elapsed_ns'}))
        records.append(row);work['trace_accounting_ns']+=perf_counter_ns()-clock
    def improve(plan,origin):
        nonlocal incumbent
        if objective(plan)<objective(incumbent):
            incumbent=plan
            updates.append(dict(attempts=work['attempts'],elapsed_ns=elapsed(),origin=origin,**plan))
    def frontier(state):
        guard()
        required=len(model.rules)+len(model.goals)
        if work['candidate_visits']+required>limits.candidate_visits: raise Bound('candidate_visits')
        return model.frontier(state,work,visit_limit=required)
    def ordered(state,candidates):
        guard();clock=perf_counter_ns(); field=None
        if arm=='PLAN-neutral':
            ranks={c.candidate_id:(action_name(c),) for c in candidates}
            path='stable-semantic-action'
        elif arm=='PLAN-B0-order':
            ranks,extra,complete=b0_ranking(model.public,model.view(state),candidates,
                state_limit=max(0,limits.ranking_states-work['ranking_states']))
            work['ranking_calls']+=1;work['b0_ns']+=perf_counter_ns()-clock
            for key in ('states','transitions','joint_checks'): work['ranking_'+key]+=extra[key]
            if not complete: raise Bound('ranking_states')
            path='frozen-b0-conditional-plan-best-first'
        else:
            pl=PressureLimits()
            if work['pressure_iterations']+len(model.goals)*pl.iterations>limits.pressure_iterations:
                raise Bound('pressure_iterations')
            # Reserve the frozen normalizer's entire allowed traversal.
            if work['normalization_visits']+512>limits.normalization_visits: raise Bound('normalization_visits')
            try:
                ranks,field,construction,iteration=rank_projected(model.public,model.view(state),candidates,pl,metrics=work)
            except ProjectionBlocked as error:
                work['normalization_visits']+=error.work.get('visits',0)
                work['normalization_ns']+=perf_counter_ns()-clock
                record(dict(kind='projection_failure',reason=error.reason,work=error.work))
                raise Bound('projection_'+error.reason) from error
            work['pressure_calls']+=1;work['pressure_iteration_ns']+=iteration
            work['pressure_iterations']+=field['work']['iterations']
            work['pressure_edge_visits']+=field['work']['edge_visits']
            if field['exhausted'] or not field['converged']:
                record(dict(kind='field_failure',state=state.wire(),field=field))
                raise Bound('field_exhaustion_or_nonconvergence')
            path='frozen-normalized-both-at-speculative-state'
        guard();clock=perf_counter_ns()
        # Preserve the frozen queue's complete tie key; neutral alone uses IDs.
        result=sorted(candidates,key=lambda c:(ranks[c.candidate_id],c.candidate_id))
        work['sorting_items']+=len(candidates);work['sorting_ns']+=perf_counter_ns()-clock
        record(dict(kind='expansion',state=state.wire(),ranking_path=path,
            candidates=sorted(action_name(c) for c in candidates),order=[action_name(c) for c in result],
            ranks={action_name(c):ranks[c.candidate_id] for c in candidates},
            pressure=None if field is None else dict(binding_digest=fingerprint(field['binding']),
                **{k:field[k] for k in ('epoch','scores','work','converged','exhausted','error_bound_l1')})))
        return result

    suffix_status='absent'
    record(dict(kind='initial_stop',incumbent=incumbent))
    try:
        if suffix is not None:
            clock=perf_counter_ns();state=model.root;prefix=[];accumulated=0
            suffix_status='invalid'
            try:
                if not suffix or suffix[-1]!=STOP or STOP in suffix[:-1]: raise Unsupported('invalid suffix')
                for action in suffix[:-1]:
                    if len(prefix)>=8: raise Unsupported('suffix length')
                    choices={action_name(c):c for c in frontier(state)}
                    if action not in choices: raise Unsupported('suffix no longer feasible')
                    work['suffix_steps']+=1
                    accumulated+=model.losses(state)[0]
                    state=model.advance(state,choices[action]);prefix.append(action)
                improve(model.closure(state,prefix,accumulated),'validated_suffix');suffix_status='validated'
            except Unsupported:
                suffix_status='invalid'
            finally: work['suffix_validation_ns']+=perf_counter_ns()-clock
        # Frames: state, prefix, accumulated pre-state loss, ordered children,
        # next child. No transpositions, pruning, oracle stopping, or rollouts.
        stack=[dict(state=model.root,prefix=(),loss=0,children=None,index=0)]
        while stack:
            guard();frame=stack[-1]
            if frame['children'] is None:
                state=frame['state'];clock=perf_counter_ns()
                plan=model.closure(state,frame['prefix'],frame['loss'])
                work['objective_ns']+=perf_counter_ns()-clock
                improve(plan,'visited_stop_closure');work['visited']+=1
                record(dict(kind='visit',state=state.wire(),prefix=list(frame['prefix']),closure=plan,
                            incumbent_value=incumbent['value']))
                # Close the last visited state before honoring the attempt cap.
                if work['attempts']>=limits.attempts: raise Bound('attempts')
                try:
                    choices=frontier(state)
                    frame['children']=ordered(state,choices) if choices else []
                    work['expanded']+=1
                except (Bound,Unsupported):
                    work['interrupted_expansions']+=1;raise
            if frame['index']==len(frame['children']): stack.pop();continue
            if work['attempts']>=limits.attempts: raise Bound('attempts')
            candidate=frame['children'][frame['index']];frame['index']+=1
            # An attempt begins immediately before transition validation,
            # including any rejection. Enumeration and rank work are separate.
            work['attempts']+=1;work['transition_checks']+=1;clock=perf_counter_ns()
            try: child=model.advance(frame['state'],candidate)
            except Unsupported as error:
                work['rejections']+=1;record(dict(kind='rejected',action=action_name(candidate),reason=str(error)));continue
            finally: work['transition_ns']+=perf_counter_ns()-clock
            stack.append(dict(state=child,prefix=frame['prefix']+(action_name(candidate),),
                loss=frame['loss']+model.losses(frame['state'])[0],children=None,index=0))
            work['peak_stack_frames']=max(work['peak_stack_frames'],len(stack))
        status='COMPLETE_SEARCH'
    except (Bound,Unsupported) as error:
        bounds.append(str(error));status='SEARCH_EXHAUSTED'
    return dict(schema='bounded-plan-search/v1',arm=arm,model_binding=model.binding,
        snapshot_binding=model.root_binding,root=model.root.wire(),limits=asdict(limits),status=status,
        bounds=bounds,incumbent=incumbent,suffix_status=suffix_status,work=work,records=records,
        improvements=updates,elapsed_ns=elapsed(),unmeasured=['actual peak RSS','OS scheduling attribution'])
