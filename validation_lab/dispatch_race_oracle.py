"""Cold delivery/receipt ordering on the independent deployment reference model.

Remote versions, immutable transport packets and local knowledge are distinct.
Only evaluator models and standard-library values are imported.
"""
from copy import deepcopy
from .deployment_oracle import _World, OracleGap


class DeliveryWorld(_World):
    def __init__(self, initial):
        super().__init__(initial)
        self.sequence, self.versions, self.latest = 0, {}, {}
        self.requests, self.receipts = {}, {}

    def remote_receipt(self, name):
        remote = self.attempts[name]['remote']
        return dict(state=('released' if remote['fenced'] else 'accepted') if remote else 'absent',
                    sequence=self.versions.get(name,self.sequence),effects=remote['effects'] if remote else 0,
                    fenced=remote['fenced'] if remote else False)

    def accept(self,name):
        if self.attempts[name]['remote'] is None:
            self.attempts[name]['remote'] = dict(fenced=False,effects=1)
            self.sequence += 1
            self.versions[name] = self.sequence
        return self.remote_receipt(name)

    def observe(self,name,receipt):
        if receipt['sequence'] >= self.latest.get(name,-1):
            self.latest[name] = receipt['sequence']
            self.attempts[name]['dispatch'].update(state=receipt['state'] if receipt['state'] in ('accepted','released') else 'uncertain',
                                                  effect_count=receipt['effects'])

    def execute(self,event):
        if event.get('schema') != 'dispatch-race-event/v1':
            raise OracleGap('unsupported delivery schema')
        kind, args, key = event['kind'],event['arguments'],event['event_id']
        name = args.get('attempt_id')
        if kind == 'arrive':
            if args['request_event'] not in self.requests:
                return 'FAIL'
            name = self.requests[args['request_event']]
            self.receipts[key] = dict(attempt=name,**self.accept(name))
        elif kind == 'deliver':
            if args['receipt_event'] not in self.receipts:
                return 'FAIL'
            receipt = self.receipts[args['receipt_event']]
            self.observe(receipt['attempt'],receipt)
        elif kind in ('prepare','dispatch','reconcile','release'):
            if name not in self.attempts or self.attempts[name]['intent'] is None:
                return 'FAIL'
            a = self.attempts[name]
            fresh = a['dispatch'] is None
            if fresh:
                if kind in ('reconcile','release'):
                    return 'FAIL'
                checked = self.action(name,submission=True)
                if checked != 'PASS':
                    return checked
                a['dispatch'] = dict(state='uncertain',prepared_at=self.now,effect_count=None)
            if kind in ('dispatch','reconcile') and not fresh:
                self.observe(name,self.remote_receipt(name))
            if kind == 'release':
                if not a['remote'] or not a['remote']['fenced']:
                    a['remote'] = dict(fenced=True,effects=a['remote']['effects'] if a['remote'] else 0)
                    self.sequence += 1
                    self.versions[name] = self.sequence
                self.observe(name,self.remote_receipt(name))
            if kind == 'dispatch' and a['dispatch']['state'] not in ('accepted','released'):
                checked = self.action(name,submission=True)
                if checked != 'PASS':
                    return checked
                fault = args['fault']
                if fault not in ('none','queued','before_effect','lost_reply'):
                    raise OracleGap('unsupported transport fault')
                if fault != 'before_effect':
                    self.requests[key] = name
                if fault in ('none','lost_reply'):
                    receipt = self.accept(name)
                    self.receipts[key] = dict(attempt=name,**receipt)
                    if fault == 'none':
                        self.observe(name,receipt)
        else:
            if kind not in {'fact','forecast','attempt','reserve','revoke','tick','restart'}:
                raise OracleGap('unsupported delivery command')
            return super().execute(dict(event,schema='deployment-event/v1'))
        return 'PASS'

    def projection(self):
        projection = super().projection()
        projection['transport'] = dict(requests=dict(sorted(self.requests.items())),receipts=deepcopy(dict(sorted(self.receipts.items()))))
        projection['executor'] = {name:self.remote_receipt(name) for name,a in sorted(self.attempts.items()) if a['dispatch'] is not None}
        return projection


def reference_prefix(initial,events):
    if len(events)>64:
        raise OracleGap('delivery trace exceeds 64 events')
    world,seen,result = DeliveryWorld(initial),set(),'PASS'
    for event in events:
        if event['event_id'] in seen:
            raise OracleGap('duplicate event identity')
        seen.add(event['event_id'])
        result = world.execute(event)
    return dict(status=result,projection=world.projection(),executor_effects=sum(a['remote']['effects'] for a in world.attempts.values() if a['remote']))
