"""Unchanged development cohort; two recall backends and two formula modes."""
from pathlib import Path
from time import perf_counter_ns
import traceback
from experimental_online_pln.agenda import Limits,wire
from experimental_goal_pln.agenda import Agenda as ScanAgenda
from experimental_native_recall.agenda import Agenda as NativeAgenda
from experimental_native_recall.session import Session
from experimental_native_recall.backend import RecallError
from goal_pln_lab.cases import World
from goal_pln_lab.compare import check_prefixes
from validation_lab.online_pln_conformance import summary
from validation_lab.decision_comparison import write
from reachability.trace_protocol import canonical


def run_case(fixture, directory, *, arm, budget, native=False, rename=False, reverse=False):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    limits = Limits(work=budget)
    world = World(fixture)
    agenda = NativeAgenda(limits=limits) if arm=='Goal-native' else ScanAgenda('Goal-scan',limits)
    start, rows, landmarks = perf_counter_ns(), [], {}
    result = dict(case_id=fixture['id'], arm=arm, budget=budget, mode='native' if native else 'finite',
                  diagnostic=dict(rename=rename,reverse=reverse),recall_backend='native-AtomSpace' if arm=='Goal-native' else 'Python-scan',
                  formula_runtime='native-PLN' if native else 'finite-checker')
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
                    native_event_start=len(agenda.backend.events) if arm=='Goal-native' else 0
                    frontier, selected=agenda.choose(snapshot)
                    serial_start=perf_counter_ns()
                    row=dict(step=agenda.selections,public_records=snapshot.records(),public_binding=snapshot.binding,
                             frontier=wire(frontier),selected=wire(selected),discovery=agenda.diagnostic,
                             work=agenda.work,acquisitions=agenda.acquisitions,
                             native_events=agenda.backend.events[native_event_start:] if arm=='Goal-native' else [])
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
            if any(call.get('status')=='ERROR' for call in session.runtime.calls):
                raise RecallError('selected formula runtime failed; inspect recorded runtime calls')
            result['conformance']='PASS'
        except Exception as error:
            result.update(conformance='ERROR' if isinstance(error,RecallError) else 'FAIL',error=type(error).__name__+': '+str(error),traceback=traceback.format_exc())
        finally:
            result.update(costs_ns=dict(session.costs),discovery_costs_ns=dict(agenda.costs),
                          runtime_calls=wire(session.runtime.calls),seams=wire(world.seams))
            write(directory/'receipts.json',wire(session.receipts))
            if arm=='Goal-native':
                result['recall_costs']=dict(agenda.backend.costs)
                result['native_epochs']=agenda.backend.epochs
                write(directory/'native-events.json',agenda.backend.events)
                agenda.backend.close()
    result['elapsed_ns']=perf_counter_ns()-start
    write(directory/'result.json',result)
    return result
