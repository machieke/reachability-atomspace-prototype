"""Public commands for a tiny two-worker admission/reservation profile.

Scheduling checkpoints and expected results are evaluator data, never wire fields.
The profile fixes three grounded atoms and two independent operation attempts.
"""
from copy import deepcopy
from .trace_protocol import identifier


def literal(value):
    if type(value) is not int or value not in (-3, -2, -1, 1, 2, 3):
        raise ValueError('literal must be a signed atom in [1,3]')


def clauses(value):
    if type(value) is not list or len(value) > 4:
        raise ValueError('up to four clauses required')
    for clause in value:
        if type(clause) is not list or len(clause) > 3:
            raise ValueError('up to three literals per clause required')
        for item in clause:
            literal(item)


def initial(value):
    if type(value) is not dict or set(value) != {'schema', 'facts', 'capacity'} or value['schema'] != 'interleaving-initial/v1':
        raise ValueError('unsupported public initial fields/schema')
    facts = value['facts']
    if type(facts) is not list or len(facts) > 3 or any(type(x) is not int or x not in (1, 2, 3) for x in facts) or len(set(facts)) != len(facts):
        raise ValueError('distinct positive initial facts required')
    if type(value['capacity']) is not int or not 0 <= value['capacity'] <= 3:
        raise ValueError('capacity must be an integer in [0,3]')
    return deepcopy(value)


FIELDS = {'read': set(), 'prepare': {'literal'}, 'commit': {'prepared'}, 'policy': {'clauses'},
          'certify': set(), 'reserve': {'permit'}}


def event(value):
    if type(value) is not dict or set(value) != {'schema', 'event_id', 'actor', 'kind', 'arguments'} or value['schema'] != 'interleaving-event/v1':
        raise ValueError('unsupported public event fields/schema')
    identifier(value['event_id'])
    if value['actor'] not in ('a', 'b') or type(value['kind']) is not str or value['kind'] not in FIELDS:
        raise ValueError('unsupported actor/command')
    args = value['arguments']
    if type(args) is not dict or set(args) != FIELDS[value['kind']]:
        raise ValueError('unexpected command arguments')
    if 'literal' in args and (type(args['literal']) is not int or args['literal'] not in (1, 2, 3)):
        raise ValueError('only three positive registered reports can be prepared')
    for name in ('prepared', 'permit'):
        if name in args:
            identifier(args[name])
    if 'clauses' in args:
        clauses(args['clauses'])
    return deepcopy(value)
