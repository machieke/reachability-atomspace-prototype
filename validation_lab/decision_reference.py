"""Independent exact evaluator for decision-task/v1. Standard library only.

No runtime truth checker, candidate generator, ranking, pressure or projection.
Proof identities can be quotiented only under this static, permanent-support
contract: future permissions depend on propositions, monitors, time and budgets,
never on which sound proof established a proposition. Budgets and monitor state
are never quotiented away. No waiting followed by resumed execution is allowed.
"""
from dataclasses import asdict, dataclass
from itertools import product
import json
from time import perf_counter_ns

SCHEMA = 'decision-task/v1'
STOP = 'STOP'


@dataclass(frozen=True)
class Bounds:
    states: int = 4096
    transitions: int = 32768
    memory_bytes: int = 16*1024*1024
    enumeration_nodes: int = 100000
    atoms: int = 6
    goals: int = 3
    requests: int = 8
    horizon: int = 16

    def __post_init__(self):
        if any(type(value) is not int or value<1 for value in asdict(self).values()):
            raise ValueError('positive integer reference bounds required')


class Exhausted(RuntimeError):
    pass


@dataclass(frozen=True, order=True)
class State:
    supports: tuple[int, ...]
    monitored: tuple[str, ...]
    tick: int
    requests: int
    operation_work: int
    observation_work: int
    validity: str = 'permanent-static/v1'

    def wire(self): return asdict(self)


def condition(tree, facts):
    """Independent syntax interpreter; membership is support, not free inference."""
    if type(tree) is int: return tree in facts
    op, children = next(iter(tree.items()))
    values = [condition(child, facts) for child in children]
    if op == 'AND': return False not in values
    if op == 'OR': return True in values
    raise ValueError('unsupported condition')


def validate(task, bounds=Bounds()):
    if task['schema'] != SCHEMA: raise ValueError('unsupported reference task')
    public, contract = task['public'], task['contract']
    if contract != dict(horizon=16,initial=contract['initial'],truth=contract['truth'],
        support_validity='permanent',future_changes='none',probe_responses='no probes',
        monitor_response='declared physical truth',commitments='none',
        proof_permissions='proposition and joint consistency only'):
        raise ValueError('unsupported deterministic guarantee')
    if public['probes'] or len(public['admission']['atoms'])>bounds.atoms or len(public['goals'])>bounds.goals:
        raise ValueError('reference fragment exceeded')
    if contract['horizon']>bounds.horizon: raise ValueError('reference horizon exceeded')
    n=len(public['admission']['atoms'])
    if not 1<=n<=6 or len(public['admission']['rules'])>8: raise ValueError('bounded task size required')
    truth=set(contract['truth'])
    if len(truth)!=n or any((i in truth)==(-i in truth) for i in range(1,n+1)):
        raise ValueError('declared complete physical assignment required')
    if not set(contract['initial'])<=truth: raise ValueError('initial support contradicts public truth')
    def check(tree, depth=0):
        if depth>8: raise ValueError('condition depth exceeded')
        if type(tree) is int:
            if not 1<=abs(tree)<=n: raise ValueError('invalid proposition')
        elif type(tree) is dict and len(tree)==1 and next(iter(tree)) in ('AND','OR'):
            children=next(iter(tree.values()))
            if type(children) is not list or not 1<=len(children)<=8: raise ValueError('invalid Boolean bundle')
            for child in children: check(child,depth+1)
        else: raise ValueError('unsupported Boolean condition')
    if len({r['rule_id'] for r in public['admission']['rules']})!=len(public['admission']['rules']): raise ValueError('duplicate rule')
    if len({g['goal_id'] for g in public['goals']})!=len(public['goals']): raise ValueError('duplicate goal')
    for r in public['admission']['rules']:
        for literal in r['premises']+[r['conclusion']]: check(literal)
        cost=public['costs'][r['rule_id']]
        if type(cost) is not int or not 1<=cost<=100: raise ValueError('exact positive operation cost required')
    for g in public['goals']:
        check(g['condition'])
        if type(g['loss']) is not int or g['loss']<=0: raise ValueError('positive loss required')
        p=public['priorities'][g['goal_id']]
        if type(p['weight']) not in (int,float) or p['weight']!=int(p['weight']) or p['weight']<=0:
            raise ValueError('integer evaluation weight required for exact labels')
    for clause in public['clauses']:
        if not clause or not any(x in truth for x in clause): raise ValueError('truth violates public clauses')
        for literal in clause: check(literal)
    return task


class Reference:
    def __init__(self, task, budget, *, bounds=Bounds()):
        self.task=validate(task,bounds); self.public=task['public']; self.budget=dict(budget); self.bounds=bounds
        if not 0<=budget['actions']<=bounds.requests or not 0<=budget['operation_work']<=100 or not 0<=budget['observation_work']<=8:
            raise ValueError('reference budget outside fragment')
        self.horizon=task['contract']['horizon']; self.truth=set(task['contract']['truth'])
        self.rules={r['rule_id']:r for r in self.public['admission']['rules']}
        self.goals={g['goal_id']:g for g in self.public['goals']}
        n=len(self.public['admission']['atoms'])
        self.worlds=[frozenset(i+1 if bit else -i-1 for i,bit in enumerate(bits))
            for bits in product((False,True),repeat=n)]
        self.worlds=[w for w in self.worlds if all(any(x in w for x in clause) for clause in self.public['clauses'])]
        self.memo={}; self.active=set(); self.transitions=0; self.memory=0; self.elapsed_ns=0
        for r in self.rules.values():
            if set(r['premises'])<=self.truth and self.consistent(set(r['premises'])|{r['conclusion']}) and r['conclusion'] not in self.truth:
                raise ValueError('admissible inference violates declared physical truth')

    def initial(self):
        return State(tuple(sorted(set(self.task['contract']['initial']))),(),0,self.budget['actions'],
            self.budget['operation_work'],self.budget['observation_work'])

    def consistent(self, facts): return any(set(facts)<=w for w in self.worlds)

    def losses(self, state):
        external=certified=0; per_goal={}
        for identity,g in self.goals.items():
            value=g['loss']*int(self.public['priorities'][identity]['weight'])
            remaining=0 if condition(g['condition'],set(state.supports)) and condition(g['condition'],self.truth) else value
            monitored=0 if identity in state.monitored else value
            external+=remaining; certified+=monitored
            per_goal[identity]=dict(external=remaining,certified=monitored)
        return external,certified,per_goal

    def actions(self, state):
        if state.validity!='permanent-static/v1': raise ValueError('unsupported validity state')
        actions=[STOP]
        if state.tick>=self.horizon or state.requests==0 or len(state.monitored)==len(self.goals): return actions
        facts=set(state.supports)
        for identity,r in self.rules.items():
            if (r['conclusion'] not in facts and set(r['premises'])<=facts and
                self.public['costs'][identity]<=state.operation_work and self.consistent(facts|{r['conclusion']})):
                actions.append('derive/'+identity)
        if state.operation_work>=1 and state.observation_work>=1:
            for identity,g in self.goals.items():
                if identity not in state.monitored and condition(g['condition'],facts): actions.append('monitor/'+identity)
        return sorted(actions)

    def successor(self, state, action):
        if action==STOP or action not in self.actions(state): raise ValueError('no admissible reference transition')
        kind,identity=action.split('/',1); facts=set(state.supports); monitored=set(state.monitored)
        cost=self.public['costs'][identity] if kind=='derive' else 1
        if kind=='derive': facts.add(self.rules[identity]['conclusion'])
        elif condition(self.goals[identity]['condition'],self.truth): monitored.add(identity)
        return State(tuple(sorted(facts)),tuple(sorted(monitored)),state.tick+1,state.requests-1,
            state.operation_work-cost,state.observation_work-(kind=='monitor'),state.validity)

    def solve(self, state=None):
        state=self.initial() if state is None else state
        if state in self.memo: return self.memo[state]
        if len(self.memo)+len(self.active)>=self.bounds.states: raise Exhausted('states')
        self.active.add(state)
        current,certified,_=self.losses(state)
        q={STOP:dict(value=(self.horizon-state.tick)*current,terminal_certified=certified,
                    operation_work=0,requests=0,witness=[STOP])}
        for action in self.actions(state):
            if action==STOP: continue
            self.transitions+=1
            if self.transitions>self.bounds.transitions: raise Exhausted('transitions')
            following=self.successor(state,action); child=self.solve(following)
            q[action]=dict(value=current+child['value'],terminal_certified=child['terminal_certified'],
                operation_work=state.operation_work-following.operation_work+child['operation_work'],
                requests=1+child['requests'],witness=[action]+child['witness'])
        value=min(v['value'] for v in q.values())
        optimal=sorted(k for k,v in q.items() if v['value']==value)
        # Secondary criteria choose witnesses only. Primary-optimal sets and
        # decision regret retain every action minimizing external loss.
        chosen=min(q,key=lambda a:(q[a]['value'],q[a]['terminal_certified'],q[a]['operation_work'],q[a]['requests'],q[a]['witness']))
        result=dict(state=state.wire(),value=value,optimal_actions=optimal,q=q,**{k:v for k,v in q[chosen].items() if k!='value'})
        # Conservative deterministic allocation charge, including witnesses and
        # keys. This is a bounded accounting limit, not a claim of measured RSS.
        charge=4096+4*len(json.dumps(result,sort_keys=True))+512*len(q)
        if self.memory+charge>self.bounds.memory_bytes: raise Exhausted('memory_accounting')
        self.memory+=charge; self.active.remove(state); self.memo[state]=result
        return result

    def labels(self):
        start=perf_counter_ns()
        try:
            root=self.solve(); status='EXACT'; reason=None
        except Exhausted as error:
            root=None; status='REFERENCE_EXHAUSTED'; reason=str(error)
        self.elapsed_ns+=perf_counter_ns()-start
        return dict(status=status,reason=reason,root=root,bounds=asdict(self.bounds),
            states=len(self.memo),transitions=self.transitions,memory_accounting_bytes=self.memory,
            elapsed_ns=self.elapsed_ns,unmeasured=['actual peak RSS'],
            objective='sum of external unresolved loss over ticks 0..15',
            secondary='Witness only: terminal certified loss, operation work, requests, lexicographic action sequence; optimal-action set uses primary loss only.')

    def sampled_states(self, limit=4):
        """Predeclared chronological state strata, independent of all policy visits."""
        if self.initial() not in self.memo: raise ValueError('exact root required')
        selected=[self.initial()]
        for tick in range(1,limit):
            eligible=sorted(s for s in self.memo if s.tick==tick and len(self.actions(s))>=3)
            if eligible: selected.append(eligible[0])
        # Recover feasible prefixes without using any Q or V value.
        prefixes={self.initial():[]}; pending=[self.initial()]
        for state in pending:
            if all(s in prefixes for s in selected): break
            for action in self.actions(state):
                if action==STOP: continue
                nxt=self.successor(state,action)
                if nxt not in prefixes: prefixes[nxt]=prefixes[state]+[action];pending.append(nxt)
        return [(state,prefixes[state]) for state in selected]
