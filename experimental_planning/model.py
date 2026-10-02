"""Detached, bounded decision-task/v1 model. Predictions never confer authority."""
from copy import deepcopy
from dataclasses import asdict, dataclass
from time import perf_counter_ns

from reachability.pressure_work import enumerate_work, holds, joint_status, operation_cost, validate_public
from reachability.trace_protocol import fingerprint

STOP = 'STOP'


class Unsupported(ValueError):
    pass


def action_name(candidate):
    return candidate.kind+'/'+dict(candidate.arguments)[{'derive':'rule_id','monitor':'goal_id'}[candidate.kind]]


@dataclass(frozen=True)
class State:
    supports: tuple
    monitored: tuple
    tick: int
    requests: int
    operation_work: int
    observation_work: int
    model_binding: str
    root_binding: str

    def wire(self): return asdict(self)
    def semantic(self):
        return {k:v for k,v in asdict(self).items() if k not in ('model_binding','root_binding')}


class Model:
    """Only the declared public static fragment, independently of the evaluator."""
    def __init__(self, task, snapshot, budget):
        self.task = deepcopy(task)
        self.public = deepcopy(validate_public(task['public']))
        contract = task['contract']
        expected = dict(horizon=16, initial=contract['initial'], truth=contract['truth'],
            support_validity='permanent', future_changes='none', probe_responses='no probes',
            monitor_response='declared physical truth', commitments='none',
            proof_permissions='proposition and joint consistency only')
        if task['schema'] != 'decision-task/v1' or contract != expected or self.public['probes']:
            raise Unsupported('unsupported static guarantee')
        n = len(self.public['admission']['atoms'])
        self.rules = {r['rule_id']:r for r in self.public['admission']['rules']}
        self.goals = {g['goal_id']:g for g in self.public['goals']}
        if not 1 <= n <= 6 or len(self.rules)>8 or len(self.goals)>3:
            raise Unsupported('static size bound')
        self.truth = set(contract['truth'])
        if (len(self.truth)!=n or any((i in self.truth)==(-i in self.truth) for i in range(1,n+1))
                or not set(contract['initial']) <= self.truth):
            raise Unsupported('invalid public physical assignment')
        if not all(any(v in self.truth for v in clause) for clause in self.public['clauses']):
            raise Unsupported('public truth violates clauses')
        for goal in self.goals.values():
            weight = self.public['priorities'][goal['goal_id']]['weight']
            if int(weight)!=weight or weight<=0:
                raise Unsupported('integer positive evaluation weights required')
        for rule in self.rules.values():
            check = dict(supports=[dict(literal=v) for v in rule['premises']], clauses=self.public['clauses'])
            if (set(rule['premises']) <= self.truth and rule['conclusion'] not in self.truth
                    and joint_status(check,(rule['conclusion'],))=='PASS'):
                raise Unsupported('admissible rule violates declared physical truth')
        self.binding = fingerprint(dict(public=self.public, contract=contract))
        self.snapshot = deepcopy(snapshot)
        self.root_binding = fingerprint(snapshot)
        if (snapshot['public_digest'] != fingerprint(self.public) or snapshot['rules']!=list(self.rules.values())
                or snapshot['clauses']!=self.public['clauses'] or not 0<=snapshot['time']<=16
                or any(s['valid_until'] is not None for s in snapshot['supports'])):
            raise Unsupported('revision, clock or support validity outside static model')
        facts = tuple(sorted({s['literal'] for s in snapshot['supports']}))
        if not set(facts)<=self.truth or joint_status(snapshot)!='PASS':
            raise Unsupported('inconsistent established state')
        monitored=[]
        if {g['goal_id'] for g in snapshot['goals']} != set(self.goals):
            raise Unsupported('goal set changed')
        for g in snapshot['goals']:
            declared=self.goals[g['goal_id']]
            if (g['condition']!=declared['condition'] or g['source_id']!=declared['source_id']
                    or g['unit']!=declared['unit'] or g['coverage'] or g['selected_commitment']
                    or g['outstanding'] not in (0,declared['loss']) or g['reopened_events']):
                raise Unsupported('dynamic goal accounting unsupported')
            if g['outstanding']==0:
                if not holds(g['condition'],facts): raise Unsupported('unsupported certified state')
                monitored.append(g['goal_id'])
        if any(type(budget[k]) is not int or not 0<=budget[k]<=cap for k,cap in
               [('actions',8),('operation_work',100),('observation_work',8)]):
            raise Unsupported('semantic budget outside fragment')
        self.root=State(facts,tuple(sorted(monitored)),snapshot['time'],budget['actions'],
                        budget['operation_work'],budget['observation_work'],self.binding,self.root_binding)

    def check(self,state):
        if state.model_binding!=self.binding or state.root_binding!=self.root_binding:
            raise Unsupported('stale model binding')

    def view(self,state):
        self.check(state)
        if state==self.root: return deepcopy(self.snapshot)
        view=deepcopy(self.snapshot)
        view['time']=state.tick
        established={s['literal'] for s in view['supports']}
        for literal in state.supports:
            if literal not in established:
                view['supports'].append(dict(reference='prediction:support:'+str(literal),literal=literal,
                    belief_revision='prediction:'+fingerprint(state.wire()),valid_until=None))
        view['supports'].sort(key=lambda s:s['reference'])
        view['revisions']['hypothesis']='prediction:'+fingerprint(state.wire())
        view['prediction_only']=True
        for g in view['goals']:
            ready=holds(g['condition'],state.supports)
            g['condition_status']='PASS' if ready else 'UNKNOWN'
            g['outstanding']=0 if g['goal_id'] in state.monitored else self.goals[g['goal_id']]['loss']
            g['open_loss']=g['outstanding']
            if g['goal_id'] in state.monitored and g['goal_id'] not in self.root.monitored:
                g['relief_events']=['prediction:monitor:'+g['goal_id']]
        return view

    def frontier(self,state,work=None,visit_limit=4096):
        start=perf_counter_ns(); view=self.view(state)
        frontier=enumerate_work(self.public,view,visit_limit=visit_limit)
        if work is not None:
            work['enumeration_calls']+=1;work['candidate_visits']+=frontier.visits
            facts=set(state.supports)
            work['consistency_checks']+=sum(r['conclusion'] not in facts and set(r['premises'])<=facts for r in self.rules.values())
            work['enumeration_ns']+=perf_counter_ns()-start
        if not frontier.complete: raise Unsupported('candidate/model visit bound')
        if state.tick>=16 or not state.requests or frontier.terminal: return ()
        return tuple(c for c in frontier.candidates if operation_cost(self.public,c)<=state.operation_work
                     and c.observation_cost<=state.observation_work)

    def advance(self,state,candidate):
        """Validate again; rejected attempted transitions are still charged by search."""
        self.check(state)
        if state.tick>=16 or not state.requests or len(state.monitored)==len(self.goals):
            raise Unsupported('terminal transition')
        kind,identity=action_name(candidate).split('/',1)
        facts=set(state.supports); monitored=set(state.monitored)
        cost=operation_cost(self.public,candidate)
        if cost>state.operation_work or candidate.observation_cost>state.observation_work:
            raise Unsupported('insufficient remaining work')
        if kind=='derive':
            rule=self.rules[identity]
            if rule['conclusion'] in facts or not set(rule['premises'])<=facts:
                raise Unsupported('missing AND bundle or duplicate inference')
            if joint_status(self.view(state),(rule['conclusion'],))!='PASS':
                raise Unsupported('joint consistency rejection')
            facts.add(rule['conclusion'])
        elif identity not in self.goals or identity in monitored or not holds(self.goals[identity]['condition'],facts):
            raise Unsupported('monitor not enabled')
        elif holds(self.goals[identity]['condition'],self.truth): monitored.add(identity)
        return State(tuple(sorted(facts)),tuple(sorted(monitored)),state.tick+1,state.requests-1,
                     state.operation_work-cost,state.observation_work-candidate.observation_cost,
                     self.binding,self.root_binding)

    def losses(self,state):
        self.check(state)
        external=certified=0
        for identity,goal in self.goals.items():
            loss=goal['loss']*int(self.public['priorities'][identity]['weight'])
            external+=0 if holds(goal['condition'],state.supports) and holds(goal['condition'],self.truth) else loss
            certified+=0 if identity in state.monitored else loss
        return external,certified

    def closure(self,state,prefix=(),accumulated=0):
        external,certified=self.losses(state)
        return dict(plan=list(prefix)+( [STOP] ),value=accumulated+(16-state.tick)*external,
            terminal_external=external,terminal_certified=certified,
            operation_work=self.root.operation_work-state.operation_work,
            observation_work=self.root.observation_work-state.observation_work,
            requests=self.root.requests-state.requests,terminal=state.wire())


def objective(plan):
    return (plan['value'],plan['terminal_certified'],plan['operation_work'],plan['requests'],tuple(plan['plan']))
