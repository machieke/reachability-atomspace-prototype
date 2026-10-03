"""Independent dense transition and allocation-ledger trace checks."""
from math import fsum,isfinite


def equal(left,right):
    if set(left)!=set(right) or any(abs(left[k]-right[k])>1e-12 for k in left):
        raise ValueError('allocation vector or semantic anchors differ')


class Ledger:
    def __init__(self):self.binding=None
    def audit(self,diagnostic):
        if self.binding!=diagnostic['binding']:
            self.binding=diagnostic['binding'];self.context=diagnostic['scope']['context']
            self.values={};self.reservoir=1.;self.arcs={};self.seeded=set();self.epoch=0
        steps=0
        for e in diagnostic['events']:
            kind=e['kind']
            if kind=='admit' and e['anchor']:self.values.setdefault(e['key'],0.)
            elif kind=='evict':
                self.reservoir+=self.values.pop(e['key'],0.)
                self.arcs={k:a for k,a in self.arcs.items() if e['key'] not in (a['source'],a['target'])}
            elif kind=='route':
                a=e['arc']
                if a['binding']!=self.binding or a['context']!=self.context or a['rate']!=1:raise ValueError('unscoped or nonfixed route')
                if a['source'] not in self.values or a['target'] not in self.values:raise ValueError('unadmitted route')
                self.arcs[a['source'],a['target'],a['purpose']]=a
            elif kind=='seed':
                roots=set(e['roots'])-self.seeded
                expected=.8 if roots and diagnostic['mode']!='WS-queue' else 0.
                if e['transferred']!=expected:raise ValueError('duplicate/new allocation')
                if expected:
                    for k in roots:self.values[k]+=expected/len(roots)
                    self.reservoir-=expected;self.seeded.update(roots)
                equal(self.values,e['activation'])
                if abs(e['reservoir']-self.reservoir)>1e-12:raise ValueError('seed reservoir differs')
            elif kind=='cool':
                moved=fsum(v*.05 for v in self.values.values())
                if abs(moved-e['amount'])>1e-12:raise ValueError('cooling differs')
                self.values={k:v*.95 for k,v in self.values.items()};self.reservoir+=moved
            elif kind=='field':
                equal(self.values,e['before']);keys=sorted(self.values);index={k:i for i,k in enumerate(keys)}
                q=[[0.]*len(keys) for _ in keys];closed=0
                for a in self.arcs.values():
                    if a['status']!='PASS':closed+=1;continue
                    if a['source']!=a['target']:q[index[a['source']]][index[a['target']]]+=1.
                exits=[fsum(row) for row in q];maximum=max(exits,default=0.);dt=.9/maximum if maximum else 0.
                transition=[[dt*q[i][j] if i!=j else 1-dt*exits[i] for j in range(len(keys))] for i in range(len(keys))]
                expected={k:fsum(self.values[a]*transition[i][j] for i,a in enumerate(keys)) for j,k in enumerate(keys)}
                equal(expected,e['activation'])
                expected_flux=[(a['source'],a['target'],self.values[a['source']]*dt) for _,a in sorted(self.arcs.items()) if a['status']=='PASS' and a['source']!=a['target']]
                if len(expected_flux)!=len(e['flux']):raise ValueError('closed/extra flux')
                for (a,b,v),(x,y,w) in zip(expected_flux,e['flux']):
                    if (a,b)!=(x,y) or abs(v-w)>1e-12:raise ValueError('directed/masked flux differs')
                self.epoch+=1;steps+=1
                if e['epoch']!=self.epoch or e['closed_arcs']!=closed or e['arc_evaluations']!=len(self.arcs) or abs(e['dt']-dt)>1e-12:raise ValueError('field work differs')
                if abs(e['reservoir']-self.reservoir)>1e-12:raise ValueError('transport changed reservoir')
                self.values=expected
            if any(not isfinite(v) or v<0 for v in (*self.values.values(),self.reservoir)) or abs(fsum((*self.values.values(),self.reservoir))-1)>1e-12:raise ValueError('allocation ledger not conservative')
            if 'residual' in e and abs(e['residual'])>1e-12:raise ValueError('recorded residual exceeds tolerance')
        if steps!=diagnostic['field_steps']:raise ValueError('microstep accounting differs')
        return steps
