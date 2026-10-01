"""Cold three-atom truth enumeration and discrete single-slot occupancy model.

No runtime imports, certificates or implementation replay are used. Epochs are
relative to the fully initialized public profile. Unsupported input is explicit.
"""
from itertools import product


class OracleGap(ValueError):
    pass


def consistent(clauses, facts):
    return any(all(world[abs(n)-1] == (n > 0) for n in facts) and
               all(any(world[abs(n)-1] == (n > 0) for n in clause) for clause in clauses)
               for world in product((False, True), repeat=3))


def reference_prefix(public, events):
    if (set(public) != {'schema', 'facts', 'capacity'} or public['schema'] != 'interleaving-initial/v1'
            or type(public['capacity']) is not int or not 0 <= public['capacity'] <= 3
            or type(public['facts']) is not list or len(set(public['facts'])) != len(public['facts'])
            or any(type(n) is not int or n not in (1, 2, 3) for n in public['facts']) or len(events) > 64):
        raise OracleGap('unsupported initial state/event bound')
    facts, clauses, policy = set(public['facts']), [], 'finite-hard-policy/v1'
    knowledge, resource, prepared, permits, intents, ids = 0, 0, {}, {}, {}, set()
    status = 'PASS'
    for event in events:
        if (set(event) != {'schema', 'event_id', 'actor', 'kind', 'arguments'} or event['schema'] != 'interleaving-event/v1'
                or not isinstance(event['event_id'], str) or not event['event_id'] or event['event_id'] in ids
                or event['actor'] not in ('a', 'b')):
            raise OracleGap('unsupported event identity/schema')
        name, actor, kind, args = event['event_id'], event['actor'], event['kind'], event['arguments']
        ids.add(name)
        fields = {'read': set(), 'prepare': {'literal'}, 'commit': {'prepared'}, 'policy': {'clauses'}, 'certify': set(), 'reserve': {'permit'}}
        if kind not in fields or type(args) is not dict or set(args) != fields[kind]:
            raise OracleGap('unsupported event kind/arguments')
        status = 'PASS'
        if kind == 'prepare':
            n = args['literal']
            if type(n) is not int or n not in (1, 2, 3):
                raise OracleGap('unsupported report')
            status = 'PASS' if consistent(clauses, facts | {n}) else 'FAIL'
            prepared[name] = dict(actor=actor, literal=n, status=status, epoch=knowledge)
        elif kind == 'commit':
            p = prepared.get(args['prepared'])
            if p is None:
                status = 'UNKNOWN'
            elif p['actor'] != actor:
                status = 'FAIL'
            elif p['epoch'] != knowledge:
                status = 'STALE'
            else:
                status = p['status']
                if status == 'PASS' and p['literal'] not in facts:
                    facts.add(p['literal'])
                    knowledge += 1
        elif kind == 'policy':
            new = args['clauses']
            if type(new) is not list or len(new) > 4 or any(type(c) is not list or len(c) > 3 or
                    any(type(n) is not int or n not in (-3, -2, -1, 1, 2, 3) for n in c) for c in new):
                raise OracleGap('unsupported constraint scope')
            if not consistent(new, set()):
                status = 'FAIL'
            else:
                # Individually compatible reports survive unless they conflict as
                # a whole. There is no arbitrary choice between conflicting facts.
                facts = {n for n in facts if consistent(new, {n})}
                if not consistent(new, facts):
                    facts.clear()
                clauses, policy, knowledge = new, name, knowledge+1
        elif kind == 'certify':
            if actor in intents or len(intents)+1 > public['capacity']:
                status = 'FAIL'
            elif 1 not in facts:
                status = 'UNKNOWN'
            permits[name] = dict(actor=actor, status=status, knowledge=knowledge, resource=resource)
        elif kind == 'reserve':
            p = permits.get(args['permit'])
            if p is None:
                status = 'UNKNOWN'
            elif p['actor'] != actor:
                status = 'FAIL'
            elif actor in intents:
                status = 'PASS' if intents[actor] == args['permit'] else 'FAIL'
            elif (p['knowledge'], p['resource']) != (knowledge, resource):
                status = 'STALE'
            elif p['status'] != 'PASS':
                status = p['status']
            else:
                intents[actor] = args['permit']
                resource += 1
    projection = dict(usable=sorted(facts), clauses=clauses, policy=policy, knowledge_epoch=knowledge, resource_epoch=resource,
        prepared={k: {name: p[name] for name in ('actor', 'literal', 'status')} for k, p in sorted(prepared.items())},
        permits={k: {name: p[name] for name in ('actor', 'status')} for k, p in sorted(permits.items())},
        intents=sorted(intents), used=len(intents), readiness={a: 'PASS' if 1 in facts else 'UNKNOWN' for a in ('a', 'b')})
    return dict(status=status, projection=projection)
