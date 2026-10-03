"""Live selected native recall → unchanged certified execution → observations."""
from pathlib import Path
from time import perf_counter_ns
import traceback
from experimental_online_pln.agenda import Limits,wire
from experimental_native_recall.session import Session
from experimental_native_recall.agenda import Agenda as Reference
from experimental_native_recall.backend import RecallError
from experimental_attention.controller import Agenda,Search
from experimental_attention.workspace import Caps,Bound
from experimental_attention.field import StaleField
from goal_pln_lab.compare import check_prefixes
from validation_lab.online_pln_conformance import summary
from validation_lab.decision_comparison import write
from reachability.trace_protocol import canonical
from .cases import World


def settings(capacity,queries,complete=False):
    if complete:return Caps(active=512,active_bytes=4194304,jobs=512,metadata_bytes=262144,answer_ids=2048,arcs=512,arc_bytes=262144,candidates=64,candidate_bytes=262144),Search(4096,True)
    if capacity not in (24,48) or queries not in (16,48):raise ValueError('undeclared primary setting')
    return Caps(active=capacity,active_bytes=capacity//24*262144),Search(queries)


def run_case(parent,directory,*,mode,capacity=24,queries=16,native=False,complete=False):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    caps,search=settings(capacity,queries,complete);limits=Limits(work=16)
    agenda=Reference(limits=limits) if mode=='Goal-native' else Agenda(mode,limits,caps,search)
    world=World(parent);rows=[];started=perf_counter_ns();result=dict(case_id=parent['id'],mode=mode,capacity=capacity,queries=queries,formula_mode='native' if native else 'finite',complete_mode=complete,recall_backend='native-AtomSpace',caps=wire(caps),search=wire(search))
    with Session(directory,native=native,limits=limits,acquire=world.acquire) as session:
        try:
            setup=perf_counter_ns();world.setup(session);session.costs['world_setup_ns']+=perf_counter_ns()-setup
            with (directory/'trace.jsonl').open('x') as trace:
                while True:
                    snapshot=session.read();events_start=len(agenda.backend.events)
                    if mode=='Goal-native':frontier,selected=agenda.choose(snapshot)
                    else:frontier,selected=agenda.choose(snapshot,current_binding=lambda:session.read().binding)
                    serialize=perf_counter_ns()
                    row=dict(public_records=snapshot.records(),public_binding=snapshot.binding,frontier=wire(frontier),selected=wire(selected),discovery=wire(agenda.diagnostic),work=agenda.work,acquisitions=agenda.acquisitions)
                    session.costs['public_serialization_ns']+=perf_counter_ns()-serialize
                    if selected is not None:
                        calls=len(session.runtime.calls);receipts=len(session.receipts)
                        try:actual=session.execute(selected)
                        finally:
                            if mode!='Goal-native':agenda.release()
                        row['result']=wire(actual);row['before_external_event']=summary(session)
                        world.after(selected,actual)
                        row.update(calls=wire(session.runtime.calls[calls:]),receipts=wire(session.receipts[receipts:]))
                    else:row['stop']=agenda.stop
                    row.update(after=summary(session),external_loss=world.external_loss,logical_tick=session.service.snapshot('ctx').logical_time,
                               native_events=agenda.backend.events[events_start:])
                    if mode!='Goal-native':row['release_events']=wire(agenda.ws.events[len(row['discovery']['events']):])
                    t=perf_counter_ns();trace.write(canonical(row)+'\n');trace.flush();session.costs['trace_serialization_write_ns']+=perf_counter_ns()-t
                    rows.append(row);agenda.backend.events.clear()
                    if selected is None:break
            result.update(summary(session),external_loss=world.external_loss,stop=agenda.stop,selections=agenda.selections,work=agenda.work,acquisitions=agenda.acquisitions,tuple_visits=agenda.tuple_visits)
            result['reconstruction']=session.project_and_reopen();check_prefixes(rows,result)
            if any(c['status']=='ERROR' for c in session.runtime.calls):raise RecallError('formula runtime error')
            result['conformance']='PASS'
        except Exception as error:
            result.update(conformance='ERROR' if isinstance(error,(RecallError,StaleField)) else 'FAIL',error=type(error).__name__+': '+str(error),traceback=traceback.format_exc())
        finally:
            result.update(costs_ns=dict(session.costs),discovery_costs_ns=dict(agenda.costs),recall_costs=dict(agenda.backend.costs),runtime_calls=wire(session.runtime.calls),seams=wire(world.seams))
            write(directory/'receipts.json',wire(session.receipts));agenda.backend.close()
    result['elapsed_ns']=perf_counter_ns()-started;write(directory/'result.json',result);return result
