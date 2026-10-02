"""Deliberately faulty variants. Test witnesses only, never experiment arms."""
from dataclasses import replace
from tempfile import TemporaryDirectory
from unittest.mock import patch

from experimental_planning.model import Model, action_name
from experimental_planning.search import Limits, search
from experimental_pressure.ranking import rank_projected
from reachability.pressure import PressureLimits
from reachability.pressure_session import ReasoningSession
from .decision_reference import Reference
from .decision_tasks import parents, budgets, materialize
from .pressure_episodes import ReasoningWorld


def witnesses():
    tasks={t['task_id']:t for t in parents()};result={}
    for mutation,identity in [('free-unfinished-completion','and-0'),('omitted-monitor-cost','completion-6'),
                              ('omitted-budget-state','completion-0'),('pressure-incumbent','depth-0')]:
        task=tasks[identity];budget=budgets()[1]['budget'];ref=Reference(task,budget)
        with TemporaryDirectory() as tmp,ReasoningSession(task['public'],tmp) as session:
            ReasoningWorld(session,materialize(task));model=Model(task,session.read(),budget)
            if mutation=='free-unfinished-completion':
                original=Model.closure
                def faulty(self,state,prefix=(),accumulated=0):
                    plan=original(self,state,prefix,accumulated);plan['value']=accumulated;return plan
                with patch.object(Model,'closure',faulty): out=search(model,'PLAN-neutral',Limits(attempts=1))
                expected=ref.solve()['value'];actual=out['incumbent']['value'];detected=actual<expected
            elif mutation=='omitted-monitor-cost':
                original=Model.advance
                def faulty(self,state,candidate):
                    nxt=original(self,state,candidate)
                    return replace(nxt,operation_work=nxt.operation_work+1,observation_work=nxt.observation_work+1) if candidate.kind=='monitor' else nxt
                with patch.object(Model,'advance',faulty): out=search(model,'PLAN-neutral',Limits(attempts=1000))
                expected=ref.solve()['operation_work'];actual=out['incumbent']['operation_work'];detected=actual!=expected
            elif mutation=='omitted-budget-state':
                cache={}
                def faulty(state):
                    key=(state.supports,state.monitored,state.tick)  # deliberately drops every remaining budget
                    if key not in cache: cache[key]=model.frontier(state)
                    return cache[key]
                faulty(model.root);empty=replace(model.root,operation_work=0)
                expected=[action_name(c) for c in model.frontier(empty)]
                actual=[action_name(c) for c in faulty(empty)];detected=actual!=expected
            else:
                candidates=model.frontier(model.root)
                ranks,_,_,_=rank_projected(model.public,model.view(model.root),candidates,PressureLimits())
                scores={action_name(c):ranks[c.candidate_id][0] for c in candidates}
                def faulty(plan):
                    return (scores.get(plan['plan'][0],0),plan['value'],plan['terminal_certified'],tuple(plan['plan']))
                with patch('experimental_planning.search.objective',faulty):
                    out=search(model,'PLAN-neutral',Limits(attempts=1000))
                expected=ref.solve()['value'];actual=out['incumbent']['value'];detected=actual!=expected
            result[mutation]=dict(detected=detected,expected=expected,mutant=actual,task=identity,
                scope='fault injected only in targeted correctness witness; excluded from measurements')
    return result
