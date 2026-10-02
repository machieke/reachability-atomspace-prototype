"""Independent static-model parity, complete witnesses, bounds and hard gates."""
import ast
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from experimental_planning.model import Model, State, STOP, Unsupported, action_name, objective
from experimental_planning.search import search, ARMS, Limits
from experimental_planning.controller import Planner
from reachability.pressure_session import ReasoningSession
from reachability.pressure_work import enumerate_work
from reachability.trace_protocol import fingerprint
from validation_lab.decision_reference import Reference, State as RefState
from validation_lab.decision_tasks import cohort, budgets, materialize
from validation_lab.planning_tasks import new_cohort
from validation_lab.pressure_episodes import ReasoningWorld

TASKS={t['task_id']:t for t in cohort()+new_cohort()}


def with_model(identity,callback,budget=None):
    task=TASKS[identity];budget=budget or budgets()[1]['budget']
    with TemporaryDirectory() as tmp, ReasoningSession(task['public'],tmp) as session:
        world=ReasoningWorld(session,materialize(task));snapshot=session.read()
        return callback(Model(task,snapshot,budget),session,world)


def feasible(test,model,result):
    state=model.root;acc=0
    for action in result['incumbent']['plan'][:-1]:
        choices={action_name(c):c for c in model.frontier(state)}
        test.assertIn(action,choices);acc+=model.losses(state)[0];state=model.advance(state,choices[action])
    test.assertEqual(result['incumbent'],model.closure(state,result['incumbent']['plan'][:-1],acc))


class PlanningTests(unittest.TestCase):
    def test_no_evaluator_or_authority_dependency(self):
        for path in Path('experimental_planning').glob('*.py'):
            tree=ast.parse(path.read_text())
            for node in ast.walk(tree):
                names=([node.module or ''] if isinstance(node,ast.ImportFrom) else
                       [a.name for a in node.names] if isinstance(node,ast.Import) else [])
                for name in names:
                    self.assertFalse(name.startswith(('validation_lab','reachability.service','reachability.pressure_session')))

    def test_model_every_reference_state_and_transition(self):
        # Reference-only enumeration; no orderer measurements on new cases.
        for identity,task in TASKS.items():
            for config in budgets():
                ref=Reference(task,config['budget']);ref.solve()
                def check(model,session,world):
                    for r in ref.memo:
                        state=replace(model.root,supports=r.supports,monitored=r.monitored,tick=r.tick,
                            requests=r.requests,operation_work=r.operation_work,observation_work=r.observation_work)
                        self.assertEqual(model.losses(state),ref.losses(r)[:2])
                        choices={action_name(c):c for c in model.frontier(state)}
                        self.assertEqual(sorted(choices),[a for a in ref.actions(r) if a!=STOP])
                        for action,candidate in choices.items():
                            nxt=model.advance(state,candidate);expected=ref.successor(r,action)
                            self.assertEqual(nxt.semantic(),{k:v for k,v in expected.wire().items() if k!='validity'})
                with self.subTest(task=identity,budget=config['name']): with_model(identity,check,config['budget'])

    def test_complete_search_all_arms_independent_optimal_witness(self):
        # Existing hand diagnostics only; not new confirmation measurements.
        for identity in ('or-0','or-4','completion-0','completion-1','completion-6','and-0','and-6','shared-0','depth-0','depth-2','budget-2'):
            for config in budgets():
                ref=Reference(TASKS[identity],config['budget']);label=ref.solve()
                def check(model,session,world):
                    for arm in ARMS:
                        out=search(model,arm,Limits(attempts=100000,wall_ns=60_000_000_000))
                        self.assertEqual(out['status'],'COMPLETE_SEARCH',(identity,arm,out['bounds']))
                        feasible(self,model,out)
                        self.assertEqual(out['incumbent']['value'],label['value'])
                        self.assertEqual(out['incumbent']['plan'],label['witness'])
                with_model(identity,check,config['budget'])

    def test_bounded_feasible_prefixes_monotone_and_hooks(self):
        def check(model,session,world):
            orderings=[]
            for arm in ARMS:
                last=None
                for cap in (1,4,16,64):
                    out=search(model,arm,Limits(attempts=cap));feasible(self,model,out)
                    value=objective(out['incumbent'])
                    if last is not None: self.assertLessEqual(value,last)
                    last=value
                    self.assertLessEqual(out['work']['attempts'],cap)
                    expanded=[r for r in out['records'] if r['kind']=='expansion']
                    self.assertTrue(expanded)
                    self.assertEqual(expanded[0]['candidates'],sorted(action_name(c) for c in model.frontier(model.root)))
                orderings.append((expanded[0]['ranking_path'],expanded[0]['order']))
            self.assertEqual(len({p for p,_ in orderings}),3)
            self.assertGreater(len({tuple(o) for _,o in orderings}),1)
        with_model('depth-2',check,budgets()[0]['budget'])

    def test_pressure_readonly_prediction_and_stale_gates(self):
        def check(model,session,world):
            before=fingerprint(session.read());commands=session.service._journal_sequence
            result=search(model,'PLAN-pressure-order',Limits(attempts=16))
            self.assertEqual(fingerprint(session.read()),before);self.assertEqual(session.service._journal_sequence,commands)
            first=model.frontier(model.root)[0];child=model.advance(model.root,first)
            hypothetical=model.frontier(child)
            if hypothetical:
                reply=session.execute(hypothetical[0],fingerprint(model.view(child)),response=True)
                self.assertEqual(reply['status'],'STALE')
                reply=session.execute(hypothetical[0],fingerprint(session.read()),response=True)
                self.assertEqual(reply['status'],'FAIL')
            session.tick(1)
            reply=session.execute(first,model.root_binding)
            self.assertEqual(reply['status'],'STALE')
            with self.assertRaises(Unsupported): model.losses(replace(model.root,model_binding='changed'))
        with_model('shared-0',check)

    def test_invalid_models_bounds_and_budget_identity(self):
        def check(model,session,world):
            for key,value in [('future_changes','event'),('support_validity','expires'),('commitments','yes')]:
                task=deepcopy(model.task);task['contract'][key]=value
                with self.assertRaises(Unsupported): Model(task,model.snapshot,budgets()[1]['budget'])
            state=replace(model.root,operation_work=0)
            self.assertNotEqual(state,model.root);self.assertEqual(model.frontier(state),())
            for limits in (Limits(attempts=0),Limits(candidate_visits=0),Limits(memory_bytes=0),Limits(wall_ns=0)):
                for arm in ARMS:
                    out=search(model,arm,limits);self.assertEqual(out['status'],'SEARCH_EXHAUSTED')
                    feasible(self,model,out);self.assertGreater(out['incumbent']['terminal_certified'],0)
            out=search(model,'PLAN-B0-order',Limits(ranking_states=0))
            self.assertIn('ranking_states',out['bounds'])
            out=search(model,'PLAN-pressure-order',Limits(pressure_iterations=0))
            self.assertIn('pressure_iterations',out['bounds'])
        with_model('and-0',check)

    def test_suffix_validation_observation_binding_and_restart(self):
        def check(model,session,world):
            planner=Planner(model.public,ARMS[0],search_limits=Limits(attempts=64))
            m,out=planner.decide(model.task,session.read(),budgets()[1]['budget'])
            first=out['incumbent']['plan'][0]
            candidate=next(c for c in enumerate_work(model.public,session.read()).candidates if action_name(c)==first)
            predicted=m.advance(m.root,candidate)
            reply=world.execute(candidate,m.root_binding)
            remain=dict(actions=predicted.requests,operation_work=predicted.operation_work,observation_work=predicted.observation_work)
            self.assertEqual(planner.retain(m,out,candidate,reply,session.read(),remain),'retained_prediction_only')
            _,next_plan=planner.decide(model.task,session.read(),remain)
            self.assertEqual(next_plan['retention'],'revalidated');self.assertEqual(next_plan['suffix_status'],'validated')
            altered=deepcopy(session.read());altered['revisions']['policy']='changed-policy'
            _,stale=planner.decide(model.task,altered,remain)
            self.assertEqual(stale['retention'],'discarded_incompatible_binding')
            self.assertIsNone(Planner(model.public,ARMS[0]).retained)
        with_model('shared-0',check)

    def test_mutation_witnesses(self):
        from validation_lab.planning_mutations import witnesses
        result=witnesses()
        self.assertEqual(set(result),{'free-unfinished-completion','omitted-monitor-cost','omitted-budget-state','pressure-incumbent'})
        self.assertTrue(all(row['detected'] for row in result.values()),result)


if __name__=='__main__': unittest.main()
