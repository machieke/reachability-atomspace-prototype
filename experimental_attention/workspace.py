"""Counted LRU working copies and explicit independent metadata/buffer caps."""
from collections import OrderedDict,Counter
from dataclasses import dataclass
from experimental_online_pln.agenda import wire
from reachability.trace_protocol import canonical
from .field import Field


def size(value):return len(canonical(wire(value)).encode())


class Bound(ValueError):pass


@dataclass(frozen=True)
class Caps:
    active: int=24
    active_bytes: int=262144
    jobs: int=128
    metadata_bytes: int=65536
    answer_ids: int=256
    arcs: int=128
    arc_bytes: int=65536
    candidates: int=16
    candidate_bytes: int=65536
    response_records: int=32
    response_bytes: int=262144
    joint_records: int=32
    joint_bytes: int=262144
    joint_slots: int=256
    controls: int=8
    control_bytes: int=65536
    trace_events: int=8192
    trace_bytes: int=8388608
    def __post_init__(self):
        maximum=(512,4194304,512,262144,2048,512,262144,64,262144,32,262144,32,262144,256,8,65536,8192,8388608)
        if any(type(v) is not int or not 0<=v<=m for v,m in zip(wire(self).values(),maximum)):
            raise ValueError('workspace cap outside declared scope')


class Workspace:
    def __init__(self,binding,context,caps=Caps()):
        self.binding,self.context,self.caps=binding,context,caps
        self.entries=OrderedDict();self.pins=set();self.controls=set();self.arcs={}
        self.field=Field(binding,context);self.costs=Counter();self.events=[];self.event_bytes=0
        self.seen=set();self.peak=Counter()
    def log(self,kind,**values):
        event=dict(kind=kind,**values);n=size(event)
        if len(self.events)>=self.caps.trace_events or self.event_bytes+n>self.caps.trace_bytes:raise Bound('TRACE_BOUND')
        self.events.append(event);self.event_bytes+=n
    def sample(self):
        metrics=dict(active=len(self.entries),active_bytes=sum(e[1] for e in self.entries.values()),
                     active_anchors=sum(e[2] for e in self.entries.values()),active_records=sum(not e[2] for e in self.entries.values()),
                     pins=len(self.pins),control_pins=len(self.controls),control_bytes=sum(self.entries[k][1] for k in self.controls),
                     arcs=len(self.arcs),arc_bytes=size(tuple(self.arcs.values())),trace_bytes=self.event_bytes)
        for k,v in metrics.items():self.peak[k]=max(self.peak[k],v)
        return metrics
    def admit(self,key,value,*,anchor=False,pin=False,protected=()):
        n=size(value)
        if key in self.entries:
            if self.entries[key][0]!=value:raise ValueError('same epoch identity conflict')
            self.entries.move_to_end(key)
            if pin:self.pins.add(key)
            return
        if n>self.caps.active_bytes or not self.caps.active:raise Bound('ENTRY_CAPACITY')
        protected=set(protected)|self.pins
        while len(self.entries)>=self.caps.active or sum(e[1] for e in self.entries.values())+n>self.caps.active_bytes:
            victim=next((k for k in self.entries if k not in protected),None)
            if victim is None:raise Bound('ALL_PINNED_CAPACITY')
            self.entries.pop(victim);self.field.remove(victim)
            self.arcs={k:a for k,a in self.arcs.items() if victim not in (a.source,a.target)}
            self.costs['evictions']+=1;self.log('evict',key=victim,residual=self.field.residual())
        rematerialized=key in self.seen
        if key not in self.seen and (len(self.seen)>=2048 or size(sorted(self.seen|{key}))>self.caps.metadata_bytes):raise Bound('SEEN_ID_BOUND')
        self.seen.add(key)
        # Seen identities are diagnostic metadata, bounded separately.
        if len(self.seen)>2048:raise Bound('SEEN_ID_BOUND')
        self.entries[key]=(value,n,anchor)
        if anchor:self.field.add(key)
        if pin:self.pins.add(key)
        self.costs['rematerializations']+=rematerialized
        self.log('admit',key=key,bytes=n,anchor=anchor,rematerialized=rematerialized)
        self.sample()
    def arc(self,arc):
        if arc.source not in self.field.activation or arc.target not in self.field.activation:return
        key=(arc.source,arc.target,arc.purpose)
        if key not in self.arcs and len(self.arcs)>=self.caps.arcs:raise Bound('ARC_BOUND')
        proposed=dict(self.arcs);proposed[key]=arc
        if size(tuple(proposed.values()))>self.caps.arc_bytes:raise Bound('ARC_BYTE_BOUND')
        self.arcs[key]=arc;self.log('route',arc=wire(arc));self.sample()
    def get(self,key):
        if key not in self.entries:return None
        self.entries.move_to_end(key);return self.entries[key][0]
    def control(self,key,value):
        if key not in self.controls and len(self.controls)>=self.caps.controls:raise Bound('CONTROL_LEDGER_BOUND')
        total=sum(self.entries[k][1] for k in self.controls if k in self.entries)
        if key not in self.controls and total+size(value)>self.caps.control_bytes:raise Bound('CONTROL_BYTE_BOUND')
        self.admit(key,value,anchor=True,pin=True);self.controls.add(key);self.sample()
    def pin_bundle(self,records):
        unique=dict(records);all_pins=self.pins|set(unique)
        count=len(all_pins)
        bytes_needed=sum(size(unique[k]) if k in unique else self.entries[k][1] for k in all_pins)
        if count>self.caps.active or bytes_needed>self.caps.active_bytes:raise Bound('INDIVISIBLE_BUNDLE_CAPACITY')
        for key,value in unique.items():self.admit(key,value,pin=True,protected=all_pins)
        self.log('pin_bundle',keys=sorted(unique));self.sample()
    def release(self):
        released=sorted(self.pins-self.controls);self.pins=set(self.controls)
        self.log('release_bundle',keys=released)
    def invalidate(self):
        for key in list(self.field.activation):self.field.remove(key)
        self.log('invalidate',binding=self.binding,reservoir=self.field.reservoir,residual=self.field.residual())
        self.entries.clear();self.pins.clear();self.controls.clear();self.arcs.clear()
