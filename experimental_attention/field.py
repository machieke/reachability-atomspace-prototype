"""Fixed direct-arc transport. Allocation is neither truth nor CPU credit."""
from dataclasses import dataclass
from math import fsum,isfinite


class StaleField(ValueError):pass


@dataclass(frozen=True)
class Arc:
    source: str
    target: str
    purpose: str
    context: str
    binding: str
    status: str
    reason: str
    rate: object=1.0


class Field:
    def __init__(self,binding,context):
        self.binding=binding;self.context=context;self.epoch=0
        self.activation={};self.reservoir=1.0;self.seeded=set()
    def residual(self):return fsum((self.reservoir,*self.activation.values()))-1.0
    def check(self):
        values=(self.reservoir,*self.activation.values())
        if any(not isfinite(v) or v<0 for v in values) or abs(self.residual())>1e-12:
            raise ValueError('nonfinite/negative allocation or conservation failure')
    def add(self,key):self.activation.setdefault(key,0.0)
    def remove(self,key):self.reservoir+=self.activation.pop(key,0.0);self.check()
    def seed(self,events,total=.8):
        new=sorted(set(events)-self.seeded)
        if not new:return 0.0
        if not 0<=total<=self.reservoir:raise ValueError('seed exceeds reservoir')
        if any(k not in self.activation for k in new):raise ValueError('seed anchor missing')
        amount=total/len(new)
        for key in new:self.activation[key]+=amount
        self.reservoir-=total;self.seeded.update(new);self.check();return total
    def cool(self,fraction=.05):
        if not isfinite(fraction) or not 0<=fraction<=1:raise ValueError('cooling bound')
        moved=fsum(v*fraction for v in self.activation.values())
        self.activation={k:v*(1-fraction) for k,v in self.activation.items()}
        self.reservoir+=moved;self.check();return moved
    def step(self,arcs,current_binding):
        if current_binding()!=self.binding:raise StaleField('stale field before step')
        old=dict(self.activation);rates=[];exits={k:0.0 for k in old};closed=0
        for arc in sorted(arcs,key=lambda a:(a.source,a.target,a.purpose)):
            # M12: closed masks are checked before touching rate arithmetic.
            if arc.status!='PASS' or arc.binding!=self.binding or arc.context!=self.context:
                closed+=1;continue
            if arc.source not in old or arc.target not in old:raise ValueError('unadmitted routing endpoint')
            rate=float(arc.rate)
            if not isfinite(rate) or not 0<=rate<=1:raise ValueError('fixed finite rate bound')
            if arc.source==arc.target:continue
            exits[arc.source]+=rate;rates.append((arc.source,arc.target,rate))
        maximum=max(exits.values(),default=0.0);dt=.9/maximum if maximum else 0.0
        fresh={k:v*(1-dt*exits[k]) for k,v in old.items()};flux=[]
        for source,target,rate in rates:
            amount=old[source]*dt*rate;fresh[target]+=amount;flux.append((source,target,amount))
        residual=fsum((self.reservoir,*fresh.values()))-1.0
        if any(not isfinite(v) or v<0 for v in fresh.values()) or abs(residual)>1e-12:
            raise ValueError('invalid field proposal')
        if current_binding()!=self.binding:raise StaleField('stale field publication cancelled')
        self.activation=fresh;self.epoch+=1
        return dict(epoch=self.epoch,dt=dt,before=dict(sorted(old.items())),activation=dict(sorted(fresh.items())),reservoir=self.reservoir,
                    residual=residual,closed_arcs=closed,arc_evaluations=len(arcs),flux=flux)
