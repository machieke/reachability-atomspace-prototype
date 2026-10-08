"""Actual native full/compact queries, limits, failures and certified round trips."""
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
import json,unittest
from integration_tests import test_native_multihop as seam,test_native_recall as recall
from experimental_snapshot_payload.observe import Observer
from experimental_snapshot_payload.backend import Backend
from experimental_snapshot_payload.schema import Projection
from experimental_runtime_lifetime.backend import Backend as Full,GenerationProcess
from experimental_native_recall.backend import RecallError
from experimental_multihop.consumer import execute_current
from reachability.trace_protocol import canonical
from snapshot_payload_lab.query_checks import check
from snapshot_payload_lab.payload import readback_bytes
from reachability.probability_model import ProbabilityRule,ProbabilityPolicy,ProbabilityIndependence
from reachability.pln_adapter import DeductionRule,TruthValue
from work_loop_lab.cases import admit

class PayloadNative(unittest.TestCase):
    session=seam.NativeMultiHopSeam.session
    step=seam.NativeMultiHopSeam.step
    compute=seam.NativeMultiHopSeam.compute
    choose=seam.NativeMultiHopSeam.choose
    def observer(self,s):
        if not hasattr(s,'_test_compact_observer'):
            s._test_compact_observer=Observer();self.addCleanup(s._test_compact_observer.close)
        return s._test_compact_observer
    def pair(self):
        pair=Full(),Backend()
        for b in pair:self.addCleanup(b.shutdown)
        return pair
    setup_query_case=recall.NativeRecallTests.setup_case
    test_missing_AND=seam.NativeMultiHopSeam.test_missing_AND
    test_shared_identity=seam.NativeMultiHopSeam.test_shared_identity
    test_unavailable_no_reset=seam.NativeMultiHopSeam.test_unavailable_no_reset
    test_wrong_order_authority=seam.NativeMultiHopSeam.test_wrong_order_and_phantom_authority
    test_cycle=seam.NativeMultiHopSeam.test_cycle
    test_depth_four=seam.NativeMultiHopSeam.test_depth_four
    test_revoke_descendants=seam.NativeMultiHopSeam.test_revoke_descendants_unrelated_survives
    test_equal_replacement_stale=seam.NativeMultiHopSeam.test_equal_replacement_stale
    test_rule_revision=seam.NativeMultiHopSeam.test_rule_revision
    test_new_producer=seam.NativeMultiHopSeam.test_new_relevant_registry
    test_opposite_report=seam.NativeMultiHopSeam.test_opposite_report
    test_weak_alternative=seam.NativeMultiHopSeam.test_weak_alternative
    test_readonly_authority=seam.NativeMultiHopSeam.test_readonly_no_authority
    test_no_scanner_rescue=seam.NativeMultiHopSeam.test_native_answers_causal_even_when_validator_graph_is_destroyed
    test_lost_helper_latch=seam.NativeMultiHopSeam.test_helper_loss_latched_explicit_rebuild_and_budget_continuity
    test_accepted_uncertain=seam.NativeMultiHopSeam.test_accepted_uncertain_control_survives_failed_discovery
    test_same_binding=seam.NativeMultiHopSeam.test_unchanged_binding_reuses_helper_but_runs_actual_queries
    test_forged_omission=seam.NativeMultiHopSeam.test_unrelated_inventory_and_forged_complete_omission_audit
    test_unsupported_model=seam.NativeMultiHopSeam.test_relevant_revision_model_stays_unsupported
    test_stale_and_malformed=seam.NativeMultiHopSeam.test_stale_response_and_malformed_readback_close_review
    test_query_bounds=seam.NativeMultiHopSeam.test_empty_bounds_and_interruption_have_distinct_outcomes
    test_native_intermediate=seam.NativeMultiHopSeam.test_actual_native_intermediate_rebound_and_consumed

    def test_all_nine_forms_independent_sources_exact_records_and_tight_bounds(self):
        s,w,_=self.setup_query_case('route-shared');full,compact=self.pair();r=check(full,compact,s.read());self.assertEqual(len(r['kinds']),9);self.assertGreater(r['query_pairs'],300)
        from reachability.model import Literal,Statement
        w.report('adverse',s.forecast.negate(),TruthValue(.3,.4));w.report('unicode',Literal(Statement('π',('λ','λ'))),TruthValue(.5,.8))
        s.register_rule(ProbabilityRule('another','1',DeductionRule('tested','other','healthy')))
        left=w.report('left',s.forecast,TruthValue(.6,.5));right=w.report('right',s.forecast,TruthValue(.7,.5));s.register_model(ProbabilityIndependence('two','ctx',(left.belief_revision_id,right.belief_revision_id),'independent'))
        check(full,compact,s.read());s.revoke_model('two');s.emit('revoke',evidence_id='left');check(full,compact,s.read())
        self.assertTrue(compact.receipt.completeness['native_projection_readback']);self.assertFalse(compact.receipt.completeness['whole_snapshot_embedded'])
    def test_policy_revision_changes_envelope_and_rejects_old_operation(self):
        s,w,p,c,m=self.session();selected,old,*_=self.choose(s,c,m);o=self.observer(s);before=o.backend.receipt;pid=o.backend.process.process.pid;generation=o.backend.generation.generation_id
        s.service.configure_probability_policy('ctx',ProbabilityPolicy('payload-policy/v1',s.read().policy.allowed_sources),s.read().policy.revision,idempotency_key=s.key())
        self.assertEqual(execute_current(s,selected)[0]['status'],'STALE');full,compact=self.pair();check(full,compact,s.read(),False)
        old_ids=before.source_ids;self.choose(s,c,m);after=o.backend.receipt
        self.assertEqual(old_ids,after.source_ids);self.assertNotEqual(before.full_snapshot_envelope['snapshot_sha256'],after.full_snapshot_envelope['snapshot_sha256']);self.assertNotEqual(before.snapshot_binding,after.snapshot_binding)
        self.assertNotEqual(pid,o.backend.process.process.pid);self.assertEqual(generation,o.backend.generation.generation_id)
        with self.assertRaises(RecallError):o.backend.query('models',binding=before.snapshot_binding,context='ctx')
    def test_tampered_native_envelope_cannot_issue_view(self):
        s,w,p,c,m=self.session();snapshot=s.read()
        for field,value in (('snapshot_sha256','0'*64),('snapshot_bytes',1),('snapshot_binding','old'),('projection_schema','wrong'),('snapshot_representation','embedded')):
            class Tampered(Projection):
                def __init__(self,view):
                    super().__init__(view);d=dict(self.envelope);d[field]=value;text=canonical(d)
                    self.batch.values[self.metadata_ref,self.envelope_ref]=text
                    from reachability.atomspace_adapter import _hex
                    self.batch.commands=[('S '+str(self.metadata_ref)+' '+str(self.envelope_ref)+' '+_hex(text)) if x.startswith('S '+str(self.metadata_ref)+' '+str(self.envelope_ref)+' ') else x for x in self.batch.commands]
            b=Backend();self.addCleanup(b.shutdown)
            with patch('experimental_snapshot_payload.backend.Projection',Tampered):
                with self.assertRaisesRegex(RecallError,'envelope differs'):b.open_view(snapshot)
            self.assertIsNone(b.receipt);self.assertEqual(b.costs['native_queries'],0)
    def test_actual_readback_byte_accounting_both_projections(self):
        s,w,p,c,m=self.session();original=GenerationProcess.receive
        for b in self.pair():
            seen=[]
            def received(proc,prefix):
                lines=original(proc,prefix)
                if prefix=='READY ':seen.append(sum(len(x.encode())+1 for x in lines))
                return lines
            with patch.object(GenerationProcess,'receive',received):r=b.open_view(s.read())
            self.assertEqual(seen,[readback_bytes(b.graph,r.snapshot_binding,r.counts['relations'],len(b.projection.catalog))])
    def test_failed_generation_and_real_native_timeout_stay_latched(self):
        s,w,p,c,m=self.session();o=self.observer(s);o(s,m);o.backend.generation.close();public,f,v,_=o(s,m)
        self.assertFalse(v.data()['complete']);self.assertIsNone(c.choose(public,v)[1]);self.assertIsNotNone(o.failed);o.rebuild();o(s,m)
        import signal,os
        proc=o.backend.process;os.kill(proc.process.pid,signal.SIGSTOP);proc.timeout=.01
        public,f,v,_=o(s,m);self.assertIn('timeout',v.data()['reason']);self.assertIsNotNone(o.failed);self.assertIsNone(c.choose(public,v)[1]);self.assertIsNone(o.backend.process)
