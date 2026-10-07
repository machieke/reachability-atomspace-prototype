"""Run one actual work-view consumer; environment events stay outside its inputs."""
from pathlib import Path
from time import perf_counter_ns
import traceback
from experimental_work_loop.consumer import Consumer,observe,execute_current
from experimental_online_pln.agenda import Limits,wire
from experimental_work_bridge.project import Limits as GraphLimits
from validation_lab.decision_comparison import write
from validation_lab.online_pln_conformance import summary
from reachability.trace_protocol import canonical
from .cases import World,setup,manifest,configuration


def episode(parent,directory,native=False,continuation=None,graph_limits=GraphLimits()):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    t=perf_counter_ns();world=World(parent,continuation);limits=Limits(**configuration()['limits']);agenda=Consumer(limits);m=manifest(parent)
    s=setup(directory,native);s.limits=limits;s.acquire=world.acquire
    rows=[];result=dict(parent=parent,mode='native' if native else 'finite',continuation=continuation)
    try:
        world.initialize(s);setup_receipts=len(s.receipts);setup_calls=len(s.runtime.calls)
        with (directory/'trace.jsonl').open('x') as stream:
            while True:
                public,frame,view,cost=observe(s,m,graph_limits);frontier,selected,choice=agenda.choose(public,view)
                row=dict(index=len(rows),public_records=public.records(),public_binding=public.binding,frame=frame.data(),view=view.data(),
                         frontier=wire(frontier),choice=choice,selected=wire(selected),costs=cost,
                         before=summary(s),environment_event_offset=len(world.events),received_offset=len(s.received))
                if selected is None:
                    row.update(stop=agenda.stop,after=summary(s),external_loss=world.external_loss)
                else:
                    receipts=len(s.receipts);calls=len(s.runtime.calls);world.before(selected)
                    begin=perf_counter_ns();actual,check=execute_current(s,selected)
                    elapsed=perf_counter_ns()-begin
                    s.costs['selected_'+selected.kind+'_inclusive_ns']+=elapsed
                    row.update(result=wire(actual),revalidation=check,execution_inclusive_ns=elapsed,
                               calls=wire(s.runtime.calls[calls:]),receipts=wire(s.receipts[receipts:]),before_environment=summary(s))
                    world.after(selected,actual)
                    row.update(after=summary(s),external_loss=world.external_loss,environment_events=world.events[row['environment_event_offset']:],received=wire(s.received[row['received_offset']:]))
                rows.append(row);started=perf_counter_ns();payload=canonical(row)+'\n'
                s.costs['trace_serialization_ns']+=perf_counter_ns()-started
                s.costs['trace_bytes']+=len(payload.encode());started=perf_counter_ns();stream.write(payload);stream.flush()
                s.costs['trace_write_ns']+=perf_counter_ns()-started
                if selected is None:break
        result.update(summary(s),stop=agenda.stop,selections=agenda.selections,work=agenda.work,acquisitions=agenda.acquisitions,
                      external_loss=world.external_loss,reconstruction=s.project_and_reopen(),setup_receipts=setup_receipts,setup_formula_calls=setup_calls)
        from .reference import check_episode
        check_episode(parent,rows,result,continuation)
        result['conformance']='PASS'
    except Exception as exc:
        result.update(conformance='FAIL',error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc())
    finally:
        result.update(costs_ns=dict(s.costs),runtime_calls=wire(s.runtime.calls),elapsed_ns=perf_counter_ns()-t)
        write(directory/'receipts.json',wire(s.receipts));write(directory/'events.json',world.events);write(directory/'result.json',result)
        s.close()
    result['elapsed_ns']=perf_counter_ns()-t;write(directory/'result.json',result)
    return result
