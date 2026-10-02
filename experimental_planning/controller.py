"""Receding-horizon public-port adapter; only real frontier handles execute."""
from copy import deepcopy
from dataclasses import asdict
from time import perf_counter_ns

from reachability.pressure_controller import ComparisonBudget
from reachability.pressure_work import enumerate_work, operation_cost
from reachability.trace_protocol import fingerprint
from .model import Model, STOP, Unsupported, action_name
from .search import ARMS, Limits, search


class Planner:
    def __init__(self,public,arm,*,search_limits=Limits(),limits=None):
        if arm not in ARMS: raise ValueError('unknown planner arm')
        self.public=deepcopy(public);self.arm=arm;self.limits=search_limits
        self.retained=None

    def decide(self,task,snapshot,remaining):
        start=perf_counter_ns()
        model=Model(task,snapshot,remaining)
        model_validation_ns=perf_counter_ns()-start
        suffix=None;retention='absent'
        if self.retained is not None:
            binding,model_binding,semantic,plan=self.retained
            if (binding==fingerprint(snapshot) and model_binding==model.binding
                    and semantic==model.root.semantic()): suffix=plan;retention='revalidated'
            else: retention='discarded_incompatible_binding'
        result=search(model,self.arm,self.limits,suffix=suffix,start_ns=start)
        result['retention']=retention
        result['model_validation_ns']=model_validation_ns
        return model,result

    def retain(self,model,result,candidate,receipt,after,remaining):
        self.retained=None
        if receipt['status']!='PASS': return 'discarded_receipt'
        try:
            predicted=model.advance(model.root,candidate)
            actual=Model(model.task,after,remaining)
            # The observation must match the prediction, all old support
            # identities must survive, and immutable dependency/policy bindings
            # must remain exact. The declared port advances one clock tick after
            # the receipt, which increments knowledge revision once. Bind the
            # suffix to that exact observed revision; no arbitrary drift.
            revisions=model.snapshot['revisions']
            if (predicted.semantic()!=actual.root.semantic()
                    or after['revisions']['knowledge']!=receipt['knowledge_revision']+1
                    or any(after['revisions'][k]!=revisions[k] for k in ('policy','dependencies','priorities'))
                    or any(s not in after['supports'] for s in model.snapshot['supports'])):
                return 'discarded_observation_mismatch'
            self.retained=(fingerprint(after),actual.binding,actual.root.semantic(),result['incumbent']['plan'][1:])
            return 'retained_prediction_only'
        except (ValueError,KeyError): return 'discarded_unsupported_observation'

    def run(self,port,budget=ComparisonBudget(),*,emit=None):
        start=perf_counter_ns();self.retained=None
        work=dict(actions=0,operation_work=0,observation_work=0,candidate_visits=0,
                  ranking_states=0,ranking_transitions=0,ranking_joint_checks=0,
                  pressure_nodes=0,pressure_edges=0,pressure_iterations=0,pressure_edge_visits=0)
        costs=dict(snapshot_ns=0,candidate_discovery_ns=0,ranking_ns=0,
                   pressure_construction_ns=0,pressure_iteration_ns=0,execution_ns=0)
        records=[];reason='ACTION_BUDGET'
        while work['actions']<budget.actions:
            if perf_counter_ns()-start>=budget.wall_ns: reason='WALL_BUDGET';break
            clock=perf_counter_ns();snapshot=port.read();costs['snapshot_ns']+=perf_counter_ns()-clock
            clock=perf_counter_ns()
            frontier=enumerate_work(self.public,snapshot,visit_limit=budget.candidate_visits-work['candidate_visits'])
            costs['candidate_discovery_ns']+=perf_counter_ns()-clock;work['candidate_visits']+=frontier.visits
            if not frontier.complete: reason='CANDIDATE_BUDGET';break
            if frontier.terminal: reason='OBSERVED_GOALS';break
            remaining={k:asdict(budget)[k]-work[k] for k in ('actions','operation_work','observation_work')}
            clock=perf_counter_ns()
            try: model,result=self.decide(port.task_contract,snapshot,remaining)
            except Unsupported as error:
                costs['ranking_ns']+=perf_counter_ns()-clock
                if emit: emit(dict(stage='unsupported',reason=str(error),snapshot=snapshot))
                reason='UNSUPPORTED_MODEL';break
            costs['ranking_ns']+=perf_counter_ns()-clock
            if emit: emit(dict(stage='search',decision=work['actions'],snapshot=snapshot,
                               remaining=remaining,result=result))
            selected_action=result['incumbent']['plan'][0]
            if selected_action==STOP: reason='PLANNED_STOP';break
            # Re-read immediately and require the exact revision/root binding.
            clock=perf_counter_ns();now=port.read();costs['snapshot_ns']+=perf_counter_ns()-clock
            if fingerprint(now)!=model.root_binding: self.retained=None;reason='STALE_PLAN';break
            clock=perf_counter_ns()
            current=enumerate_work(self.public,now,visit_limit=budget.candidate_visits-work['candidate_visits'])
            costs['candidate_discovery_ns']+=perf_counter_ns()-clock;work['candidate_visits']+=current.visits
            if not current.complete: reason='CANDIDATE_BUDGET';break
            choices={action_name(c):c for c in current.candidates if
                operation_cost(self.public,c)<=remaining['operation_work'] and c.observation_cost<=remaining['observation_work']}
            if selected_action not in choices: reason='STALE_PLAN';break
            selected=choices[selected_action]
            if perf_counter_ns()-start>=budget.wall_ns: reason='WALL_BUDGET';break
            work['actions']+=1;work['operation_work']+=operation_cost(self.public,selected)
            work['observation_work']+=selected.observation_cost
            row=dict(schema='planning-comparison-step/v1',variant=self.arm,step=work['actions'],
                ranking_path='shared-explicit-stack-dfs/'+self.arm,snapshot=snapshot,snapshot_digest=fingerprint(snapshot),
                candidates=[c.wire() for c in frontier.candidates],selected=selected.wire(),pressure=None,
                budget=asdict(budget),work=dict(work),plan=result['incumbent'])
            if emit: emit(dict(stage='selection',**row))
            clock=perf_counter_ns();row['receipt']=port.execute(selected,fingerprint(snapshot))
            costs['execution_ns']+=perf_counter_ns()-clock
            records.append(row)
            if emit: emit(dict(stage='receipt',step=work['actions'],receipt=row['receipt']))
            clock=perf_counter_ns();after=port.read();costs['snapshot_ns']+=perf_counter_ns()-clock
            remaining={k:asdict(budget)[k]-work[k] for k in remaining}
            clock=perf_counter_ns()
            retention=self.retain(model,result,selected,row['receipt'],after,remaining)
            costs['ranking_ns']+=perf_counter_ns()-clock
            if emit: emit(dict(stage='retention',status=retention,elapsed_ns=perf_counter_ns()-clock,
                               snapshot_binding=fingerprint(after)))
            if row['receipt']['status']!='PASS': reason='RECEIPT_FAILURE';break
        total=perf_counter_ns()-start
        if emit: emit(dict(stage='stop',reason=reason,work=work,last_pressure=None))
        return dict(variant=self.arm,stop_reason=reason,work=work,costs=costs,total_elapsed_ns=total,
                    wall_overrun_ns=max(0,total-budget.wall_ns),records=records,last_pressure=None)
