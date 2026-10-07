"""Real native query membership driving the unchanged multi-hop consumer."""
import copy,unittest
from dataclasses import replace
from unittest.mock import patch
from tests import test_multihop as helpers
from experimental_native_multihop.observe import Observer
from experimental_native_multihop.backend import RecordedBackend
from experimental_native_recall.backend import QueryResult,RecallError
from experimental_native_recall.schema import QueryLimits
from experimental_multihop.consumer import observe as scanner,execute_current
from experimental_multihop.project import Limits
from experimental_work_bridge.project import project as validator,ObligationWorkView
from experimental_online_pln.agenda import wire
from reachability.trace_protocol import canonical
from reachability.probability_model import ProbabilityRule,ProbabilityIndependence
from reachability.pln_adapter import DeductionRule,implication
from multihop_lab.reference import graph
from multihop_lab.cases import fixture
from work_loop_lab.cases import admit


class NativeMultiHopSeam(unittest.TestCase):
    session=helpers.MultiHopTests.session
    step=helpers.MultiHopTests.step
    compute=helpers.MultiHopTests.compute
    def observer(self,s):
        if not hasattr(s,'_test_native_observer'):
            s._test_native_observer=Observer();self.addCleanup(s._test_native_observer.close)
        return s._test_native_observer
    def choose(self,s,c,m,limits=Limits()):
        p,f,v,cost=self.observer(s)(s,m,limits);_,selected,why=c.choose(p,v)
        expected=scanner(s,m,limits)[2];self.assertEqual(v.data(),expected.data())
        return selected,p,f,v,why

    # Same boundary assertions now exercise native membership through choose().
    test_missing_AND=helpers.MultiHopTests.test_templates_cannot_execute_missing_AND_or_name_hypothetical_estimates
    test_shared_identity=helpers.MultiHopTests.test_shared_intermediate_is_one_record_referenced_twice
    test_unavailable_no_reset=helpers.MultiHopTests.test_unavailable_leaf_is_requested_once_without_phantom_confidence
    test_wrong_order_and_phantom_authority=helpers.MultiHopTests.test_wrong_order_and_phantom_ids_are_rejected_by_original_authority
    test_cycle=helpers.MultiHopTests.test_cycle_without_grounding_is_incomplete_and_cannot_bootstrap
    test_depth_four=helpers.MultiHopTests.test_depth_four_stays_visible_even_if_a_current_source_can_fill_slot
    test_revoke_descendants_unrelated_survives=helpers.MultiHopTests.test_revoke_leaf_retires_every_descendant_but_unrelated_branch_survives
    test_equal_replacement_stale=helpers.MultiHopTests.test_equal_replacement_cannot_revive_stale_selected_final
    test_rule_revision=helpers.MultiHopTests.test_rule_revision_invalidates_intermediate_and_pending_tuple
    test_new_relevant_registry=helpers.MultiHopTests.test_new_relevant_registry_producer_invalidates_completed_review
    test_opposite_report=helpers.MultiHopTests.test_pending_adverse_report_adopted_without_value_filter
    test_weak_alternative=helpers.MultiHopTests.test_favorable_final_cannot_skip_unexamined_adverse_route
    test_readonly_no_authority=helpers.MultiHopTests.test_read_only_work_and_typed_permission_boundary

    def test_actual_native_intermediate_rebound_and_consumed(self):
        s,w,port,c,m=self.session(native=True);o=self.observer(s)
        for _ in range(3):chosen,r=self.step(s,c,m)
        mid=r['commit'].belief;before=o.backend.receipt.snapshot_binding;epoch=o.backend.epochs
        selected,p,f,v,why=self.choose(s,c,m);self.assertEqual(selected.target,'r-final');self.assertIn(mid.belief_revision_id,selected.premise_ids)
        self.assertNotEqual(o.backend.receipt.snapshot_binding,before);self.assertEqual(o.backend.epochs,epoch+1)
        queries=[e['result'] for e in o.last['events'] if e['kind']=='query' and e['result']['request']['kind']=='current']
        self.assertTrue(any(mid.belief_revision_id in i for q in queries for i in q['ids']))
        self.assertEqual(execute_current(s,selected)[0]['status'],'PASS');self.assertEqual([x['mode'] for x in s.runtime.calls],['native','native'])
    def test_native_answers_causal_even_when_validator_graph_is_destroyed(self):
        s,w,port,c,m=self.session();o=self.observer(s);expected=scanner(s,m)[2]
        def validation_only(*args):
            view,cost=validator(*args);d=view.data();keep={'task','obligation','existing-execution','observed-goal'}
            d['nodes']=[n for n in d['nodes'] if n['kind'] in keep];ids={n['id'] for n in d['nodes']};d['edges']=[e for e in d['edges'] if e['source'] in ids and e['target'] in ids]
            for item in d['obligations']:item['routes']=['poisoned-scanner-id']
            return ObligationWorkView(canonical(d)),cost
        with patch('experimental_multihop.project.project',side_effect=AssertionError('scan discovery forbidden')),patch('experimental_native_multihop.project.one_step',side_effect=validation_only):
            p,f,v,cost=o(s,m)
        self.assertEqual(v,expected);self.assertGreater(o.backend.costs['native_queries'],0);self.assertIsNotNone(c.choose(p,v)[1])
    def test_empty_bounds_and_interruption_have_distinct_outcomes(self):
        s,w,port,c,m=self.session()
        for limits,reason in ((QueryLimits(visits=0),'VISIT_BOUND'),(QueryLimits(results=0),'RESULT_BOUND'),(QueryLimits(queries=0),'QUERY_BOUND')):
            o=Observer(RecordedBackend(limits=limits));self.addCleanup(o.close);p,f,v,_=o(s,m)
            self.assertEqual(v.data()['reason'],'NATIVE_INCOMPLETE:'+reason);self.assertIsNone(c.choose(p,v)[1]);self.assertEqual(c.selections,0)
        o=self.observer(s);p,f,v,_=o(s,m);self.assertTrue(v.data()['complete'])
        self.assertTrue(any(e['kind']=='query' and e['result']['complete'] and not e['result']['ids'] for e in o.last['events']))
        real=o.backend.query
        def interrupted(kind,**kwargs):
            r=real(kind,**kwargs)
            if kind=='producers':return replace(r,ids=(),complete=False,reason='VISIT_BOUND')
            return r
        with patch.object(o.backend,'query',side_effect=interrupted):p,f,v,_=o(s,m)
        self.assertFalse(v.data()['complete']);self.assertIsNone(c.choose(p,v)[1]);self.assertIsNone(o.last['fallback'])
    def test_helper_loss_latched_explicit_rebuild_and_budget_continuity(self):
        s,w,port,c,m=self.session();o=self.observer(s);chosen,*_=self.choose(s,c,m);before=(c.selections,c.work,c.acquisitions,set(c.attempted))
        o.backend.process.process.kill();o.backend.process.process.wait();p,f,v,_=o(s,m);self.assertIn('lost',v.data()['reason']);epochs=o.backend.epochs
        p,f,v,_=o(s,m);self.assertEqual(o.backend.epochs,epochs);self.assertFalse(v.data()['complete']);self.assertIsNone(c.choose(p,v)[1])
        self.assertEqual(before,(c.selections,c.work,c.acquisitions,set(c.attempted)));o.rebuild();p,f,v,_=o(s,m);self.assertTrue(v.data()['complete']);self.assertIsNone(c.choose(p,v)[1])
    def test_stale_response_and_malformed_readback_close_review(self):
        s,w,port,c,m=self.session();o=self.observer(s);real=o.backend.query
        with patch.object(o.backend,'query',side_effect=lambda *a,**k:replace(real(*a,**k),view_id='old-epoch')):
            p,f,v,_=o(s,m)
        self.assertEqual(v.data()['reason'],'NATIVE_STALE_RESPONSE');self.assertIsNone(c.choose(p,v)[1]);o.rebuild()
        with patch('experimental_native_recall.backend.readback',side_effect=RecallError('invalid native readback')):p,f,v,_=o(s,m)
        self.assertIn('invalid native readback',v.data()['reason']);self.assertIsNone(c.choose(p,v)[1])
    def test_accepted_uncertain_control_survives_failed_discovery(self):
        s,w,port,c,m=self.session();reserve,*_=self.compute(s,c,m);execute_current(s,reserve);s.emit('dispatch',attempt_id='attempt',fault='lost_reply');port.sync_effect()
        o=self.observer(s);o.failed='NATIVE_QUERY_FAILED:helper lost';p,f,v,_=o(s,m);selected=c.choose(p,v)[1]
        self.assertFalse(v.data()['complete']);self.assertEqual(selected.kind,'query');self.assertEqual(execute_current(s,selected)[0]['status'],'PASS');self.assertEqual(s.executor.total_effects,1)
    def test_unchanged_binding_reuses_helper_but_runs_actual_queries(self):
        s,w,port,c,m=self.session();o=self.observer(s);a=o(s,m);pid=o.backend.process.process.pid;n=o.backend.costs['native_queries'];b=o(s,m)
        self.assertEqual(a[2],b[2]);self.assertEqual(o.backend.epochs,1);self.assertEqual(o.backend.costs['view_reuses'],1);self.assertEqual(o.backend.process.process.pid,pid);self.assertGreater(o.backend.costs['native_queries'],n)
    def test_unrelated_inventory_and_forged_complete_omission_audit(self):
        s,w,port,c,m=self.session();admit(s,'unrelated-evidence',implication('u','v'),.4,.8);s.register_rule(ProbabilityRule('unrelated-rule','1',DeductionRule('u','v','w')))
        o=self.observer(s);p,f,v,_=o(s,m);graph(p,m,v.data());self.assertNotIn('unrelated-rule',[n['producer']['record']['rule_id'] for n in v.data()['nodes'] if n['kind']=='producer-template'])
        real=o.backend.query
        def forged(kind,**kwargs):
            r=real(kind,**kwargs)
            return replace(r,ids=(),details=()) if kind=='producers' else r
        # Trusted helper arbitrary omission is NOT cryptographically detected.
        with patch.object(o.backend,'query',side_effect=forged):p,f,v,_=o(s,m)
        self.assertTrue(v.data()['complete'])
        with self.assertRaises(AssertionError):graph(p,m,v.data())

    def test_relevant_revision_model_stays_unsupported(self):
        s,w,port,c,m=self.session('shared');self.compute(s,c,m)
        ids=tuple(b.belief_revision_id for b in s.read().decision.criteria[0].current)
        s.register_model(ProbabilityIndependence('unsupported-merge','ctx',ids,'diagnostic only'))
        selected,p,f,v,why=self.choose(s,c,m);self.assertIsNone(selected)
        self.assertEqual(v.data()['reason'],'RELEVANT_REVISION_TEMPLATE_UNSUPPORTED')

    def test_capture_and_native_snapshot_cannot_mix_epochs(self):
        from experimental_native_multihop.access import Access
        from experimental_native_multihop.project import project
        from experimental_obligations.capture import immutable
        from experimental_obligations.evaluate import evaluate
        s,w,port,c,m=self.session();p,f,v,_=scanner(s,m)
        s.emit('tick',time=1);backend=RecordedBackend();self.addCleanup(backend.close)
        ab={k:evaluate(immutable(f.data()['capture']),m,k)[0] for k in ('A','B')}
        v,_=project(f,m,ab['A'],ab['B'],Access(backend,s.read()))
        self.assertEqual(v.data()['reason'],'NATIVE_STALE_CAPTURE_BINDING');self.assertFalse(v.data()['complete']);self.assertEqual(backend.epochs,0)
