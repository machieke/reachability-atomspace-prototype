"""Twelve predeclared new structures, plus the entire inspected old cohort."""
from .decision_tasks import A, O, cohort as old_cohort, budgets
from .pressure_episodes import goal, profile, rule

# No policy imports or selection. Two new structures in each existing family.
STRUCTURES={
 'or':[
  ([1],[([1],2,1),([1],3,2),([2,3],4,1),([1],5,3),([5],6,1)],[(O(4,6),5,1),(2,1,1)],[]),
  ([1],[([1],2,2),([2],3,1),([1],4,1),([4],5,2),([3,5],6,1)],[(O(3,5),2,1),(6,4,1)],[]),
 ],
 'and':[
  ([1],[([1],2,1),([2],3,1),([1],4,2),([4],5,1)],[(A(3,5),5,1),(O(2,4),1,1)],[]),
  ([1],[([1],2,1),([1],3,1),([2,3],4,1),([1],5,2)],[(A(2,O(4,5)),4,1),(3,2,1)],[[-4]]),
 ],
 'shared':[
  ([1],[([1],2,1),([1],3,1),([2,3],4,2),([4],5,1),([4],6,1)],[(5,4,1),(6,3,1),(A(2,3),1,1)],[]),
  ([1],[([1],2,2),([2],3,1),([2],4,1),([3,4],5,1),([1],6,1)],[(5,5,1),(O(3,6),2,1)],[]),
 ],
 'depth':[
  ([1],[([1],2,1),([2],3,1),([3],4,1),([4],5,1),([1],6,3),([6],5,2)],[(5,5,1),(3,1,1)],[]),
  ([1],[([1],2,2),([2],6,2),([1],3,1),([3],4,1),([4],5,1),([5],6,1)],[(6,4,1),(A(3,4),2,1)],[]),
 ],
 'budget':[
  ([1],[([1],2,3),([1],3,1),([2,3],4,2),([3],5,1)],[(4,6,1),(2,1,1),(5,2,1)],[]),
  ([1],[([1],2,2),([2],3,3),([1],4,1),([4],5,2),([3,5],6,1)],[(O(3,5),3,1),(6,5,1)],[]),
 ],
 'completion':[
  ([1,2],[([1],3,1),([2,3],4,1),([1],5,2)],[(2,2,1),(A(2,3),3,1),(O(4,5),4,1)],[]),
  ([1,2,3],[([2,3],4,2),([4],5,1)],[(A(2,3),3,1),(O(2,5),2,1),(5,4,1)],[]),
 ]}


def new_cohort():
    tasks=[]
    for family,rows in STRUCTURES.items():
        for index,(initial,rules,goals,clauses) in enumerate(rows):
            identity=f'new-{family}-{index}';n=max(initial+[r[1] for r in rules])
            public=profile(['p'+str(i+1) for i in range(n)],
                [rule('r'+str(i),p,c) for i,(p,c,_) in enumerate(rules)],
                [goal('g'+str(i),tree,loss) for i,(tree,loss,_) in enumerate(goals)],[],
                {'r'+str(i):r[2] for i,r in enumerate(rules)},{'g'+str(i):g[2] for i,g in enumerate(goals)})
            public['context_id']='planning:'+identity;public['clauses']=clauses
            false={abs(c[0]) for c in clauses if len(c)==1 and c[0]<0}
            tasks.append(dict(schema='decision-task/v1',task_id=identity,parent_id=identity,family=family,
                partition='new-confirmation',sibling=False,sibling_kind=None,rename={},public=public,
                contract=dict(horizon=16,initial=initial,truth=[-i if i in false else i for i in range(1,n+1)],
                    support_validity='permanent',future_changes='none',probe_responses='no probes',
                    monitor_response='declared physical truth',commitments='none',
                    proof_permissions='proposition and joint consistency only')))
    return tasks


def cohort(): return old_cohort()+new_cohort()
