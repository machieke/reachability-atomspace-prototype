"""Private physical state. No authority, controller, sensor-response or goal-flag inputs."""
import copy
from reachability.dispatch_model import DispatchRequest,ExecutorReceipt
from experimental_online_pln.agenda import wire


class PhysicalWorld:
    def __init__(self,spec,goal):
        self.spec=copy.deepcopy(spec);self.goal=copy.deepcopy(goal)
        self.time=-1;self.installed=None;self.healthy=False;self.operation='absent'
        self.accepted={};self.effects=[];self.history=[];self.events=[]
    def accept(self,request,receipt):
        if type(request) is not DispatchRequest or type(receipt) is not ExecutorReceipt:raise ValueError('actual typed executor evidence required')
        if (request.request_id!=receipt.request_id or request.fingerprint!=receipt.request_fingerprint
            or request.intent.product_id!=self.goal['product'] or receipt.executor_id!=request.intent.executor_id):raise ValueError('executor effect identity mismatch')
        if receipt.state not in ('accepted','released') or receipt.effect_count==0:return False
        if receipt.effect_count!=1:raise ValueError('unsupported non-idempotent multiplicity')
        key=(receipt.instance_id,request.request_id)
        if key in self.accepted:
            if self.accepted[key]['request']!=wire(request):raise ValueError('effect request rebound')
            return False
        if self.accepted:raise ValueError('one accepted deployment per bounded world')
        if self.time<0:raise ValueError('clock must start before acceptance')
        record=dict(accepted_at=self.time,due=self.time+self.spec['delay'],request=wire(request),receipt=wire(receipt))
        self.accepted[key]=record;self.operation='pending';self.events.append(dict(kind='accepted-effect-link',**copy.deepcopy(record)))
        return True
    def advance(self,tick):
        if type(tick) is not int or tick!=self.time+1:raise ValueError('consecutive independent ticks required')
        self.time=tick
        for key,record in sorted(self.accepted.items()):
            if record['due']==tick:
                if self.spec['effect']=='failed':self.operation='failed'
                else:self.installed=self.spec['installed'];self.healthy=True;self.operation='completed'
                event=dict(kind='physical-effect',time=tick,request_id=record['request']['request_id'],installed=self.installed,healthy=self.healthy,operation=self.operation)
                self.effects.append(event);self.events.append(event)
        for event in self.spec['events']:
            if event['tick']==tick:
                self.healthy=event['healthy'];self.events.append(dict(kind='exogenous-health',time=tick,healthy=self.healthy))
        streak=0
        if self.installed==self.goal['product'] and self.healthy:
            streak=1+(self.history[-1]['healthy_streak'] if self.history else 0)
        deficit=0 if streak>=self.goal['consecutive_healthy_ticks'] else self.goal['deficit_units']
        sample=dict(time=tick,installed=self.installed,healthy=self.healthy,operation=self.operation,healthy_streak=streak,goal_deficit=deficit)
        self.history.append(sample);return copy.deepcopy(sample)
    def state(self):
        return copy.deepcopy(dict(time=self.time,installed=self.installed,healthy=self.healthy,operation=self.operation,
          accepted=sorted(self.accepted.values(),key=lambda r:r['request']['request_id']),effects=self.effects,history=self.history,events=self.events))
    def measure(self,channel):
        if channel not in ('product','health'):raise ValueError('unknown sensor')
        unavailable=self.time in self.spec['outages'].get(channel,[])
        return dict(channel=channel,sample_time=self.time,status='UNKNOWN' if unavailable else 'PASS',
                    value=None if unavailable else self.installed if channel=='product' else self.healthy)
