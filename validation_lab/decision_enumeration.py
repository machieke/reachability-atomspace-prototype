"""Second independent engine: enumerate complete histories without memoization.

Standard library only; no imports from the dynamic program or runtime semantics.
This intentionally repeats the small declared transition semantics so a shared
implementation mistake does not trivially make the two algorithms agree.
"""
from itertools import product
from time import perf_counter_ns


def enumerate_histories(task, budget, *, state=None, node_limit=100000):
    start=perf_counter_ns(); public=task['public']; contract=task['contract']
    n=len(public['admission']['atoms']); rules=public['admission']['rules']; goals=public['goals']
    def satisfied(expression, available):
        pending=[(expression,False)]; stack=[]
        while pending:
            tree,done=pending.pop()
            if isinstance(tree,int): stack.append(tree in available)
            elif done:
                op,children=next(iter(tree.items()));values=stack[-len(children):];del stack[-len(children):]
                stack.append(sum(values)==len(values) if op=='AND' else sum(values)>0)
            else:
                pending.append((tree,True)); pending.extend((child,False) for child in reversed(next(iter(tree.values()))))
        return stack[0]
    worlds=[{i+1 if b else -(i+1) for i,b in enumerate(bits)} for bits in product((False,True),repeat=n)]
    allowed=[w for w in worlds if all(set(clause)&w for clause in public['clauses'])]
    weights={g['goal_id']:g['loss']*int(public['priorities'][g['goal_id']]['weight']) for g in goals}
    if state is None:
        facts=set(contract['initial']);monitored=set();tick=0
        requests=budget['actions'];work=budget['operation_work'];observations=budget['observation_work']
    else:
        facts=set(state['supports']);monitored=set(state['monitored']);tick=state['tick']
        requests=state['requests'];work=state['operation_work'];observations=state['observation_work']
    first_work,first_requests=work,requests
    best={};nodes=leaves=0
    def walk(facts,monitored,tick,requests,work,observations,loss,path):
        nonlocal nodes,leaves
        nodes+=1
        if nodes>node_limit: raise OverflowError('enumeration_nodes')
        unresolved=sum(weights[g['goal_id']] for g in goals if not(satisfied(g['condition'],facts) and satisfied(g['condition'],set(contract['truth']))))
        final=loss+(contract['horizon']-tick)*unresolved
        certificate=sum(weights[g['goal_id']] for g in goals if g['goal_id'] not in monitored)
        witness=path+['STOP'];first=path[0] if path else 'STOP'
        row=dict(value=final,terminal_certified=certificate,operation_work=first_work-work,
                 requests=first_requests-requests,witness=witness)
        quality=lambda x:(x['value'],x['terminal_certified'],x['operation_work'],x['requests'],x['witness'])
        if first not in best or quality(row)<quality(best[first]): best[first]=row
        leaves+=1
        if not requests or tick>=contract['horizon'] or len(monitored)==len(goals): return
        for rule in rules:
            price=public['costs'][rule['rule_id']];conclusion=rule['conclusion']
            if (price<=work and conclusion not in facts and all(p in facts for p in rule['premises'])
                and any(facts|{conclusion}<=w for w in allowed)):
                walk(facts|{conclusion},monitored,tick+1,requests-1,work-price,observations,
                     loss+unresolved,path+['derive/'+rule['rule_id']])
        for g in goals:
            if g['goal_id'] not in monitored and work>=1 and observations>=1 and satisfied(g['condition'],facts):
                done=monitored|({g['goal_id']} if satisfied(g['condition'],set(contract['truth'])) else set())
                walk(facts,done,tick+1,requests-1,work-1,observations-1,loss+unresolved,path+['monitor/'+g['goal_id']])
    try:
        walk(facts,monitored,tick,requests,work,observations,0,[])
        value=min(v['value'] for v in best.values())
        result=dict(status='EXACT',value=value,optimal_actions=sorted(a for a,v in best.items() if v['value']==value),q=best)
    except OverflowError:
        result=dict(status='REFERENCE_EXHAUSTED',reason='enumeration_nodes')
    return dict(result,nodes=nodes,leaves=leaves,node_limit=node_limit,elapsed_ns=perf_counter_ns()-start,
        memory_contract='Depth bounded by request budget (8); only per-first-action minima and the current path retained; actual peak RSS unmeasured.')
