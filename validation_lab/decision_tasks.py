"""Fixed deterministic parent cohort; no policy or reference result selection."""
from copy import deepcopy
from dataclasses import asdict

from reachability.pressure_controller import ComparisonBudget
from .pressure_episodes import goal, profile, rule

FAMILIES=('or','and','shared','depth','budget','completion')
def A(*x): return {'AND':list(x)}
def O(*x): return {'OR':list(x)}


def prototypes(family):
    # (initial propositions, (premises, conclusion, cost) rules,
    #  (condition, physical loss, explicit priority weight) goals, clauses)
    rows={
      'or':[
        ([1],[([1],2,2)],[(2,3,1)],[]),
        ([1],[([1],2,1),([1],2,1)],[(2,3,1)],[]),
        ([1],[([1],2,1),([1],2,3)],[(2,3,1)],[]),
        ([1],[([1],2,3),([1],3,1),([3],2,1)],[(2,3,1)],[]),
        ([1],[([1],2,1),([1],3,1),([1],4,1)],[(O(2,3),3,1),(4,1,1)],[]),
        ([1],[([1],2,1),([1],3,1),([1],4,4)],[(O(A(2,3),4),4,1)],[]),
        ([1],[([1],2,1),([2],3,1),([2],4,1),([1],5,2)],[(O(3,4),3,1),(5,2,1)],[]),
        ([1],[([1],2,1),([2],3,1),([1],4,3),([1],5,1)],[(O(A(2,3),4),2,2),(5,2,1)],[]),
      ],
      'and':[
        ([1],[([1],2,1),([1],3,1)],[(A(2,3),3,1)],[]),
        ([1,2],[([1],2,1),([1],3,1)],[(A(2,3),3,1)],[]),
        ([1],[([1],2,1),([1],3,1),([1],4,1)],[(A(2,3,4),3,1)],[]),
        ([1],[([1],2,1),([2],3,1),([1],4,1)],[(A(2,3),3,1),(4,1,1)],[]),
        ([1],[([1],2,1),([1],3,2),([1],4,1)],[(A(2,O(3,4)),4,1)],[]),
        ([1],[([1],2,1),([1],3,1),([2],4,1),([3],5,1)],[(A(4,5),4,1)],[]),
        ([1],[([1],2,1),([1],3,1),([1],4,1)],[(A(2,3),3,1),(4,1,1)],[[-3]]),
        ([1],[([1],2,1),([2],3,1),([2],4,1),([2],5,1),([1],6,1)],[(A(3,4,5),3,2),(6,1,1)],[]),
      ],
      'shared':[
        ([1],[([1],2,1),([2],3,1),([2],4,1)],[(3,2,1),(4,2,1)],[]),
        ([1],[([1],2,1),([2],3,1)],[(2,2,1),(A(2,3),3,1)],[]),
        ([1],[([1],2,1),([2],3,1),([2],4,1),([1],5,2)],[(O(3,5),3,1),(4,2,1)],[]),
        ([1],[([1],2,1),([2],3,1),([3],4,1)],[(A(2,3),3,1),(4,4,1)],[]),
        ([1],[([1],2,1),([1],3,1),([1],4,1)],[(A(2,3),3,1),(O(3,4),2,1)],[]),
        ([1],[([1],2,1),([1],3,1),([2,3],4,1),([2],5,1)],[(4,4,1),(5,2,1)],[]),
        ([1],[([1],2,1),([2],3,1),([3],4,1),([2],5,1)],[(3,1,1),(4,3,1),(5,2,1)],[]),
        ([1],[([1],2,1),([1],3,1),([2,3],4,1),([1],4,4)],[(2,2,1),(4,4,1)],[]),
      ],
      'depth':[
        ([1],[([1],2,4),([1],3,1),([3],2,1)],[(2,4,1)],[]),
        ([1],[([1],2,4),([1],3,1),([3],2,1),([1],4,1)],[(2,4,1),(4,1,1)],[]),
        ([1],[([1],2,5),([1],3,1),([3],4,1),([4],2,1),([1],5,1)],[(2,4,1),(5,2,1)],[]),
        ([1],[([1],2,3),([2],5,3),([1],3,1),([3],4,1),([4],5,1)],[(5,4,1)],[]),
        ([1],[([1],2,6),([1],3,1),([3],2,1),([1],4,1)],[(A(2,3),3,1),(4,2,1)],[]),
        ([1],[([1],2,3),([1],3,2),([3],2,2)],[(2,3,1)],[]),
        ([1],[([1],2,4),([1],3,1),([3],2,1),([1],4,2)],[(2,2,3),(4,2,1)],[]),
        ([1],[([1],2,1),([2],3,1),([3],4,1),([1],4,5)],[(2,1,1),(4,3,2)],[]),
      ],
      'budget':[
        ([1],[([1],2,4),([1],3,1)],[(2,6,1),(3,1,1)],[]),
        ([1],[([1],2,4),([1],3,1)],[(2,1,1),(3,6,1)],[]),
        ([1],[([1],2,4),([2],3,1),([1],4,1)],[(3,6,1),(4,1,1)],[]),
        ([1],[([1],2,2),([1],3,2),([1],4,1)],[(A(2,3),6,1),(4,1,1)],[]),
        ([1],[([1],2,2),([1],3,2),([1],4,2)],[(2,2,1),(3,3,1),(4,5,1)],[]),
        ([1],[([1],2,6),([1],3,1),([3],4,1),([4],2,1),([1],5,1)],[(2,6,1),(5,1,1)],[]),
        ([1],[([1],2,3),([2],3,1),([2],4,1)],[(3,4,1),(4,3,1)],[]),
        ([1],[([1],2,1),([1],3,1),([1],4,1),([2],5,1)],[(A(2,3,4),4,1),(5,2,1)],[]),
      ],
      'completion':[
        ([1],[([1],2,1)],[(2,1,1)],[]),
        ([1],[([1],2,1),([1],3,1)],[(2,1,1),(3,1,1)],[]),
        ([1],[([1],2,1),([1],3,1)],[(2,1,3),(3,2,1)],[]),
        ([1,2],[([1],2,1),([1],3,1)],[(2,3,1),(3,2,1)],[]),
        ([1],[([1],2,1)],[(2,2,1),(2,3,1)],[]),
        ([1],[([1],2,1),([1],3,1),([1],4,1)],[(2,1,1),(3,1,1),(4,1,1)],[]),
        ([1,2,3],[([1],2,1),([1],3,1)],[(2,3,1),(3,2,1)],[]),
        ([1],[([1],2,1),([1],3,1),([1],4,1),([2],5,1)],[(A(2,3),3,1),(O(2,4),2,1),(5,2,1)],[]),
      ]}
    return rows[family]


def parents():
    tasks=[]
    for family in FAMILIES:
        for index,(initial,rules,goals,clauses) in enumerate(prototypes(family)):
            identity=f'{family}-{index}'
            count=max(initial+[r[1] for r in rules])
            rr=[rule('r'+str(i),premises,conclusion) for i,(premises,conclusion,_) in enumerate(rules)]
            gg=[goal('g'+str(i),tree,loss) for i,(tree,loss,_) in enumerate(goals)]
            public=profile(['p'+str(i+1) for i in range(count)],rr,gg,[],
                {'r'+str(i):r[2] for i,r in enumerate(rules)}, {'g'+str(i):g[2] for i,g in enumerate(goals)})
            public['context_id']='decision:'+identity; public['clauses']=clauses
            false={abs(c[0]) for c in clauses if len(c)==1 and c[0]<0}
            tasks.append(dict(schema='decision-task/v1',task_id=identity,parent_id=identity,family=family,
                partition='development' if index<5 else 'confirmation',sibling=False,sibling_kind=None,rename={},public=public,
                contract=dict(horizon=16,initial=initial,truth=[-i if i in false else i for i in range(1,count+1)],
                    support_validity='permanent',future_changes='none',probe_responses='no probes',
                    monitor_response='declared physical truth',commitments='none',
                    proof_permissions='proposition and joint consistency only')))
    return tasks


def permutation(parent):
    task=deepcopy(parent);p=task['public'];task['task_id']+='-permuted';task['sibling']=True;task['sibling_kind']='identifiers'
    mapping={}
    rules=p['admission']['rules'];costs={}
    for index,r in enumerate(rules):
        old=r['rule_id'];new='z'+str(len(rules)-index)
        mapping['derive/'+old]='derive/'+new;costs[new]=p['costs'][old];r['rule_id']=new
    p['costs']=costs;priorities={}
    for index,g in enumerate(p['goals']):
        old=g['goal_id'];new='z'+str(len(p['goals'])-index)
        mapping['monitor/'+old]='monitor/'+new;priorities[new]=p['priorities'][old];g['goal_id']=new
    p['priorities']=priorities;task['rename']=mapping
    return task


def dominated(parent):
    task=deepcopy(parent);task['task_id']+='-dominated';task['sibling']=True;task['sibling_kind']='dominated-option'
    p=task['public'];extra=deepcopy(p['admission']['rules'][0]);old=extra['rule_id'];extra['rule_id']='dominated-'+old
    p['admission']['rules'].append(extra);p['costs'][extra['rule_id']]=p['costs'][old]+1
    return task


def cohort():
    base=parents()
    return (base+[permutation(p) for p in base if p['task_id'].rsplit('-',1)[1] in ('1','6')]
            +[dominated(p) for p in base if p['task_id'].endswith('-0')])


def budgets():
    return [dict(name='requests-4-work-4',mode='matched-task-work',budget=asdict(ComparisonBudget(actions=4,operation_work=4,observation_work=3))),
            dict(name='requests-8-work-12',mode='matched-task-work',budget=asdict(ComparisonBudget(actions=8,operation_work=12,observation_work=3)))]


def materialize(task):
    """World data is a serialization of the public contract, never extra answers."""
    return dict(case_id=task['task_id'],version='decision-task/v1',seed=0,public=deepcopy(task['public']),
        world=dict(initial=[dict(literal=v,name='initial-'+str(v)) for v in task['contract']['initial']],
            truth=task['contract']['truth'],probes={},revoke_at=None,revoke_evidence=None),
        description='Deterministic contract is supplied to every fixed policy on its public port.')
