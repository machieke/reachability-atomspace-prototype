"""Fixed in-process tick driver; unchanged consumer instance and public APIs."""
from pathlib import Path
from time import perf_counter_ns
import traceback
from experimental_multihop.consumer import Consumer,observe,execute_current
from experimental_online_pln.agenda import Limits,wire
from experimental_obligations.capture import state_digest
from validation_lab.online_pln_conformance import summary
from validation_lab.decision_comparison import write
from reachability.trace_protocol import canonical
from work_loop_lab.reference import check_step
from world_lab.world import PhysicalWorld
from multihop_lab.cases import Port,fixture,apply_events
from multihop_lab.cases import setup,initialize,configuration,specification,manifest
from world_lab.reference import metrics,classify,validate
from experimental_multihop.project import depths
from multihop_lab.reference import final as dependency_check


def episode(parent,directory,native=False,task=None,spec_override=None,observer=True):
    task=task or parent;directory=Path(directory);directory.mkdir(parents=True,exist_ok=False);start=perf_counter_ns()
    cfg=configuration();spec=spec_override or specification(parent);world=PhysicalWorld(spec,cfg['physical_goal'])
    consumer=Consumer(Limits(**cfg['limits']));s=setup(directory,native);s.limits=consumer.limits;m=manifest(task)
    ticks=[];rows=[];changes=[];result=dict(parent=parent,mode='native' if native else 'finite',task=task,observer=observer)
    costs=dict(world_transition_ns=0,guard_ns=0,output_serialization_ns=0,output_bytes=0)
    from experimental_native_multihop.observe import Observer
    observe=Observer();port=None
    try:
        responses=initialize(s,task);port=Port(s,world,responses,cfg['public_opportunities'],numeric_channel=fixture(parent)['numeric_channel']);s.acquire=port.acquire
        initial=dict(public_records=s.read().records(),receipts=wire(s.receipts),setup_formula_calls=len(s.runtime.calls));write(directory/'initial.json',initial)
        with (directory/'trace.jsonl').open('x') as stream:
            for tick in range(cfg['horizon_inclusive']+1):
                before=summary(s);t=perf_counter_ns();guard=state_digest(s.service);costs['guard_ns']+=perf_counter_ns()-t
                t=perf_counter_ns();sample=world.advance(tick);costs['world_transition_ns']+=perf_counter_ns()-t
                after_guard=state_digest(s.service)
                if guard!=after_guard:raise AssertionError('physical transition wrote authority')
                port.publish(tick);measure_offset=len(port.measurements);begin_row=len(rows);tick_stop='NO_OBSERVER' if not observer else 'PER_TICK_OPERATION_BOUND'
                for slot in range(cfg['max_operations_per_tick'] if observer else 0):
                    public,frame,view,observed_costs=observe(s,m);frontier,candidate,choice=consumer.choose(public,view)
                    row=dict(index=len(rows),tick=tick,slot=slot,public_records=public.records(),public_binding=public.binding,frame=frame.data(),view=view.data(),frontier=wire(frontier),choice=choice,
                      selected=wire(candidate),costs=observed_costs,before=summary(s),measurement_offset=len(port.measurements),receipt_offset=len(s.receipts))
                    if candidate is None:
                        row.update(stop=consumer.stop,after=summary(s));tick_stop=consumer.stop
                    else:
                        ri=len(s.receipts);ci=len(s.runtime.calls);ei=len(s.received);t=perf_counter_ns()
                        actual,revalidation=execute_current(s,candidate);elapsed=perf_counter_ns()-t;s.costs['selected_'+candidate.kind+'_inclusive_ns']+=elapsed
                        row.update(result=wire(actual),revalidation=revalidation,execution_inclusive_ns=elapsed,calls=wire(s.runtime.calls[ci:]),receipts=wire(s.receipts[ri:]),received=wire(s.received[ei:]),
                                   before_environment=summary(s),after=summary(s))
                        # Real executor state is read irrespective of returned status/ACK.
                        port.sync_effect()
                    rows.append(row);t=perf_counter_ns();payload=canonical(row)+'\n';costs['output_serialization_ns']+=perf_counter_ns()-t;costs['output_bytes']+=len(payload.encode());stream.write(payload);stream.flush()
                    apply_events(s,parent,tick,slot,changes)
                    if candidate is None:break
                record=dict(time=tick,physical_sample=sample,physical_end=world.state(),authority_before_clock=before,authority_guard_before=guard,authority_guard_after=after_guard,
                  public_event=port.public_events[-1],authority_after=summary(s),row_start=begin_row,row_end=len(rows),measurements=port.measurements[measure_offset:],
                  steps_summary=[dict(kind=r['selected']['kind'],target=r['selected']['target'],result=r.get('result')) for r in rows[begin_row:] if r['selected']],
                  consumer_stop=tick_stop,budget=dict(selections=consumer.selections,work=consumer.work,acquisitions=consumer.acquisitions))
                record['mismatch_reasons']=classify(record);ticks.append(record)
        private=dict(spec=spec,state=world.state(),measurements=port.measurements,effect_links=port.links,public_events=port.public_events)
        result.update(summary(s),stop=ticks[-1]['consumer_stop'],selections=consumer.selections,work=consumer.work,acquisitions=consumer.acquisitions,
                      metrics=metrics(ticks,port.measurements,cfg['tick_duration']),reconstruction=s.project_and_reopen())
        attempts=set()
        for row in rows:check_step(row,attempts)
        validate(spec,cfg,ticks,private,result,core=False)
        history={b.belief_revision_id:wire(b) for q in s.read().numerical for b in q.historical}
        result['committed_depths']=depths(history);result['longest_dependency_path']=max(result['committed_depths'].values(),default=0)
        result['runtime_calls']=wire(s.runtime.calls);t=perf_counter_ns();result['dependency_reference']=dependency_check(fixture(parent),initial,rows,result,changes);costs['independent_dependency_check_ns']=perf_counter_ns()-t
        result['conformance']='PASS'
    except Exception as exc:result.update(conformance='FAIL',error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc())
    finally:
        private=dict(spec=spec,state=world.state(),measurements=port.measurements if port else [],effect_links=port.links if port else [],public_events=port.public_events if port else [])
        result.update(costs_ns=dict(s.costs),environment_costs_ns=dict(costs,**(port.costs if port else {})),runtime_calls=wire(s.runtime.calls),elapsed_ns=perf_counter_ns()-start)
        write(directory/'changes.json',changes);write(directory/'receipts.json',wire(s.receipts));write(directory/'received.json',wire(s.received));write(directory/'authority-certificates.json',{kind:wire(tuple(store[k] for k in sorted(store))) for kind,store in (('hard',s.service._certificates),('probability',s.service._probability.certificates),('execution',s.service._execution.permits),('completion',s.service._completion.permits))});write(directory/'ticks.json',ticks);write(directory/'private.json',private);write(directory/'native-events.json',observe.backend.events);result['native_costs']=dict(observe.backend.costs);result['native_epochs']=observe.backend.epochs;observe.close();write(directory/'result.json',result);s.close()
    result['elapsed_ns']=perf_counter_ns()-start;write(directory/'result.json',result);return result
