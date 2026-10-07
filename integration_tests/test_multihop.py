"""Actual pinned native dependency paths and a forced stale completion boundary."""
from tests import test_multihop as helpers
from multihop_lab.cases import fixture


# Use helpers without inheriting the default test inventory.
import unittest
class NativeMultiHopTests(unittest.TestCase):
    session=helpers.MultiHopTests.session
    choose=helpers.MultiHopTests.choose
    step=helpers.MultiHopTests.step
    run_episode=helpers.MultiHopTests.run_episode
    def check(self,parent,depth):
        r,rows=self.run_episode(parent,True);self.assertEqual(r['longest_dependency_path'],depth);self.assertEqual(r['stage'],'BUILT');self.assertTrue(r['reconstruction']['projection_equal']);self.assertEqual(r['reconstruction']['native_calls_before'],r['reconstruction']['native_calls_after'])
        for call in r['runtime_calls']:self.assertEqual(call['mode'],'native');self.assertTrue(call['formula_agreement'])
    def test_two_hop_native_exact_committed_dependency(self):self.check('two-hop',2)
    def test_three_hop_native_exact_committed_dependency(self):self.check('three-hop',3)
    def test_shared_native_intermediate_is_not_an_independent_copy(self):self.check('shared',3)
    def test_late_native_result_after_leaf_revocation_cannot_commit(self):
        s,w,port,c,m=self.session(native=True)
        for _ in range(2):self.step(s,c,m)
        source=next(x for x in fixture('two-hop')['sources'] if x['missing'])
        s.after_proposal=lambda session,transition,proposal:session.emit('revoke',evidence_id=source['id'])
        selected,result=self.step(s,c,m);self.assertEqual(result['status'],'STALE');self.assertEqual(len(s.runtime.calls),1);self.assertEqual(s.runtime.calls[0]['mode'],'native');self.assertEqual(s.runtime.calls[0]['commit_status'],'STALE');self.assertFalse(any(b.transition.kind=='deduction' for q in s.read().numerical for b in q.current));self.assertEqual(s.executor.total_effects,0)
