"""Bounded attribution witness, separate from the six-parent comparison."""
import argparse,json
from pathlib import Path
from time import perf_counter_ns
from experimental_multihop.consumer import Consumer
from experimental_runtime_lifetime.observe import Observer
from experimental_native_multihop.observe import Observer as StrictObserver
from multihop_lab.cases import setup,initialize,manifest
from validation_lab.decision_comparison import write
from .compare import source_binding


def run(output,allow_dirty=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=False);source=source_binding(allow_dirty);rows=[]
    for arm,cls in (('MH-native-strict',StrictObserver),('MH-native-session',Observer)):
        (output/arm).mkdir();s=setup(output/arm,False);initialize(s,'two-hop');o=cls();m=manifest('two-hop')
        try:
            for repetition in range(3):
                start=perf_counter_ns();public,frame,view,costs=o(s,m);elapsed=perf_counter_ns()-start
                rows.append(dict(arm=arm,repetition=repetition,public_binding=public.binding,view=view.data(),elapsed_ns=elapsed,costs=costs,epochs=o.backend.epochs,pid=o.backend.process.process.pid,generation_id=getattr(o.backend.receipt,'runtime_generation_id',None)))
            s.emit('tick',time=1);start=perf_counter_ns();public,frame,view,costs=o(s,m)
            rows.append(dict(arm=arm,repetition=3,public_binding=public.binding,view=view.data(),elapsed_ns=perf_counter_ns()-start,costs=costs,epochs=o.backend.epochs,pid=o.backend.process.process.pid,generation_id=getattr(o.backend.receipt,'runtime_generation_id',None)))
        finally:
            o.close();s.close()
        group=rows[-4:];assert len({r['public_binding'] for r in group[:3]})==1
        assert len({r['pid'] for r in group[:3]})==1 and group[3]['pid']!=group[0]['pid']
        assert group[3]['public_binding']!=group[0]['public_binding'];assert [r['epochs'] for r in group]==[1,1,1,2]
        for row in group:assert row['costs']['native_retrieval']['costs']['native_queries']>0
        if arm=='MH-native-session':
            assert len({r['generation_id'] for r in group})==1
            write(output/'generation.json',dict(descriptor=o.backend.generation.descriptor,costs=o.backend.runtime_costs(),events=o.backend.generation.events))
    report=dict(status='PASS',sources=source,rows=rows,scope='One fixed snapshot, three actual query passes, then changed logical clock and cold view. Attribution only; no independent tasks, selection, native PLN or world benefit claim.')
    write(output/'diagnostic.json',report);return dict(status=report['status'],observations=len(rows),scope=report['scope'])


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--allow-dirty',action='store_true');a=p.parse_args();print(json.dumps(run(a.output,a.allow_dirty),indent=2))
if __name__=='__main__':main()
