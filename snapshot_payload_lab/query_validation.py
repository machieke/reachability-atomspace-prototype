"""Separate all-form native boundary diagnostic, not an extra benchmark parent."""
import argparse,json
from integration_tests.test_native_recall import NativeRecallTests
from experimental_runtime_lifetime.backend import Backend as Full
from experimental_snapshot_payload.backend import Backend as Compact
from reachability.pln_adapter import TruthValue,DeductionRule
from reachability.probability_model import ProbabilityRule,ProbabilityIndependence
from reachability.model import Literal,Statement
from .query_checks import check
from .compare import source_binding
from validation_lab.decision_comparison import write


def run(allow_dirty=False):
    helper=NativeRecallTests();full=Full();compact=Compact();out=dict(source=source_binding(allow_dirty),phases=[],native_pln_calls=0)
    try:
        s,w,_=helper.setup_case('route-shared')
        def phase(name):
            offsets=[len(b.events) for b in (full,compact)];result=check(full,compact,s.read())
            out['phases'].append(dict(name=name,public_records=s.read().records(),result=result,full_events=full.events[offsets[0]:],compact_events=compact.events[offsets[1]:]))
        phase('original')
        w.report('adverse',s.forecast.negate(),TruthValue(.3,.4));w.report('unicode',Literal(Statement('π',('λ','λ'))),TruthValue(.5,.8))
        s.register_rule(ProbabilityRule('another','1',DeductionRule('tested','other','healthy')))
        left=w.report('left',s.forecast,TruthValue(.6,.5));right=w.report('right',s.forecast,TruthValue(.7,.5))
        s.register_model(ProbabilityIndependence('two','ctx',(left.belief_revision_id,right.belief_revision_id),'independent'));phase('alternatives-model-opposition')
        s.revoke_model('two');s.emit('revoke',evidence_id='left');phase('retired-model-and-source')
        out['status']='PASS';out['query_pairs']=sum(p['result']['query_pairs'] for p in out['phases']);return out
    finally:full.shutdown();compact.shutdown();helper.doCleanups()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--allow-dirty',action='store_true');a=p.parse_args();r=run(a.allow_dirty);write(a.output,r);print(json.dumps(dict(status=r['status'],query_pairs=r['query_pairs'])))
