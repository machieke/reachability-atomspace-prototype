"""Public simulator deliveries; scheduling metadata never enters this protocol."""
from copy import deepcopy
from .trace_protocol import DeploymentEvent, identifier

BASE_KINDS = {'fact', 'forecast', 'attempt', 'reserve', 'prepare', 'dispatch', 'reconcile', 'release', 'revoke', 'tick', 'restart'}


def parse(value):
    if type(value) is not dict or set(value) != {'schema', 'event_id', 'kind', 'arguments'} or value['schema'] != 'dispatch-race-event/v1':
        raise ValueError('unsupported dispatch-race message fields/schema')
    identifier(value['event_id'])
    kind, args = value['kind'], value['arguments']
    if type(kind) is not str or type(args) is not dict:
        raise ValueError('typed event kind and arguments required')
    if kind in ('arrive', 'deliver'):
        field = 'request_event' if kind == 'arrive' else 'receipt_event'
        if set(args) != {field}:
            raise ValueError('one exact transport event reference required')
        identifier(args[field])
    elif kind in BASE_KINDS:
        base = deepcopy(value)
        base['schema'] = 'deployment-event/v1'
        if kind == 'dispatch' and args.get('fault') == 'queued':
            base['arguments']['fault'] = 'before_effect'
        DeploymentEvent.parse(base)
    else:
        raise ValueError('unsupported dispatch-race event kind')
    return deepcopy(value)
