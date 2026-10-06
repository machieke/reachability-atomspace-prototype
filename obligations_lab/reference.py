"""Independent finite policy predicates. No import from subject evaluator."""
from itertools import product


def precedence(statuses):
    flags=set(statuses)
    if 'FAIL' in flags:return 'FAIL'
    if 'STALE' in flags:return 'STALE'
    if 'UNKNOWN' in flags or not flags:return 'UNKNOWN'
    return 'PASS' if flags=={'PASS'} else 'UNKNOWN'


def obligation_table(mode,live,retired):
    # Exhaustive Boolean interpretation: alternatives are existential, mandatory
    # assessments universal. No arithmetic on confidence and no independence rule.
    if not live:return 'STALE' if retired else 'UNKNOWN'
    satisfied=(True in live) if mode=='any' else (False not in live)
    return 'PASS' if satisfied else 'UNKNOWN'


def frozen(data):
    same,opposite=data['pairs'][0];c=data['contract']['criteria'][0]
    truths=[b['proposal']['support']['truth'] for b in same['current']]
    flags=[ch['status'] for ch in same['checks']]+[same['status']]
    flags.append('UNKNOWN' if opposite['current'] else 'PASS')
    flags.append('UNKNOWN' if not truths else 'FAIL' if any(t['strength']<c['min_strength'] or t['strength']>c['max_strength'] for t in truths) else 'PASS')
    flags.append('UNKNOWN' if not truths or any(t['confidence']<c['min_confidence'] for t in truths) else 'PASS')
    return precedence(flags)


def qualified(data,manifest):
    c=manifest['criterion'];same,opposite=data['pairs'][0];live={b['belief_revision_id'] for view in (same,opposite) for b in view['current']}
    evidence={e['evidence_id']:e for e in data['registry']['evidence']};mapping={}
    for view in (same,opposite):
        for belief in view['historical']:
            t=belief['transition'];tags=[]
            if t['kind']=='observation':identity=[evidence[t['evidence_id']]['source']]
            elif t['kind']=='deduction':identity=[t['rule_id'],t['rule_revision']]
            else:identity=[t['independence_id']]
            for selector in manifest['classes']:
                if t['kind']!=selector['kind'] or identity!=selector['identity']:continue
                if all(root in belief['proposal']['support']['lineage_roots'] for root in selector['roots']):tags.append(selector['id'])
            mapping[belief['belief_revision_id']]=set(tags)
    statuses=[same['status'],*(ch['status'] for ch in same['checks'])]
    if opposite['current']:statuses.append('UNKNOWN')
    for b in same['current']:
        value=b['proposal']['support']['truth']['strength']
        if value<c['min_strength'] or value>c['max_strength']:statuses.append('FAIL')
    if any(not mapping[i] for i in live):statuses.append('UNKNOWN')
    groups={}
    for obligation in manifest['obligations']:
        now=[];old=[];witnesses=[]
        for b in same['historical']:
            i=b['belief_revision_id']
            if not mapping[i].intersection(obligation['classes']):continue
            if i not in live:old.append(i);continue
            tv=b['proposal']['support']['truth'];ok=c['min_strength']<=tv['strength']<=c['max_strength'] and tv['confidence']>=c['min_confidence'];now.append(ok)
            if ok:witnesses.append(i)
        status=obligation_table(obligation['mode'],now,old);groups[obligation['id']]=(status,sorted(witnesses));statuses.append(status)
    return precedence(statuses),groups
