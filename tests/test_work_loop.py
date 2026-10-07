"""Focused live consumer checks; outcomes and choices asserted independently."""
import ast,copy,json,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from dataclasses import replace
from experimental_work_loop.consumer import Consumer,observe,execute_current
from experimental_work_bridge.project import Limits as GraphLimits,ObligationWorkView
from experimental_online_pln.agenda import Probe,Limits,enumerate_work,wire
from experimental_obligations.capture import state_digest,immutable
from experimental_obligations.evaluate import evaluate
from work_loop_lab.cases import setup,World,manifest,admit
from work_loop_lab.run import episode
from reachability.pln_adapter import DeductionRule
from reachability.probability_model import ProbabilityRule
from reachability.model import Status


class WorkLoopTests(unittest.TestCase):
    def session(self,parent='positive'):
        tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup);s=setup(tmp.name);self.addCleanup(s.close);w=World(parent);s.acquire=w.acquire;w.initialize(s);return s,w,manifest(parent)
    def capture(self,s,m,limits=GraphLimits()):return observe(s,m,limits)
    def choose(self,s,m,c=None,limits=GraphLimits()):
        p,f,v,cost=self.capture(s,m,limits);a=c or Consumer();front,selected,why=a.choose(p,v);return a,p,f,v,front,selected,why
    def run_episode(self,parent='positive',continuation=None,native=False):
        tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup);root=Path(tmp.name)/'run';r=episode(parent,root,native,continuation);self.assertEqual(r['conformance'],'PASS',r.get('traceback'));rows=[json.loads(line) for line in (root/'trace.jsonl').read_text().splitlines()];return r,rows
    def test_positive_controller_selects_information_adoption_inference_and_observed_completion(self):
        r,rows=self.run_episode();self.assertEqual((r['stage'],r['outstanding'],r['effects']),('BUILT',0,1));k=[x['selected']['kind'] for x in rows if x['selected']];self.assertIn('adopt',k);self.assertEqual(k.count('deduction'),2);self.assertEqual(len(rows[0]['choice']['eligible']),2)
    def test_shared_operation_runs_once_and_weak_parent_stays_blocked(self):
        for parent in ('shared','blocked'):
            r,rows=self.run_episode(parent);self.assertEqual(sum(x['selected']['kind']=='revision' for x in rows if x['selected']),1)
            self.assertEqual(r['effects'],int(parent=='shared'))
    def test_unavailable_unknown_once_copied_report_still_adopted_and_unclassified(self):
        r,rows=self.run_episode('unavailable');self.assertEqual(r['selections'],1);self.assertEqual(rows[0]['result']['status'],'UNKNOWN')
        r,rows=self.run_episode('unavailable','copied');self.assertEqual([x['selected']['kind'] for x in rows if x['selected']],['request','adopt']);self.assertEqual(r['effects'],0);self.assertEqual(r['stop'],'OBJECTION_OR_UNKNOWN_APPLICABILITY')
    def test_adverse_registered_review_is_executed_before_any_authorization(self):
        r,rows=self.run_episode('adverse');self.assertEqual(rows[0]['view']['A']['numerical_status'],'PASS');self.assertEqual(rows[0]['view']['B']['numerical_status'],'PASS');self.assertEqual(rows[0]['selected']['kind'],'deduction');self.assertEqual(rows[-1]['view']['A']['numerical_status'],'FAIL');self.assertEqual(r['effects'],0)
    def test_freshness_rejects_old_candidate_and_preserves_old_method_requirement(self):
        r,rows=self.run_episode('freshness');self.assertTrue(any(x.get('result',{}).get('status')=='STALE' for x in rows));self.assertEqual(r['effects'],0);self.assertTrue(any(o['status']!='PASS' for o in rows[-1]['view']['obligations']))
    def test_pending_adverse_and_unknown_source_reports_not_filtered_by_value(self):
        for source,literal_opposite in (('source-b',True),('unclassified-source',False)):
            s,w,m=self.session('shared');admit(s,'pending',s.forecast.negate() if literal_opposite else s.forecast,.1,.05,source,'unknown-root',False)
            a,p,f,v,front,c,d=self.choose(s,m);self.assertEqual((c.kind,c.target),('adopt','pending'));self.assertEqual(s.execute(c)['status'],'PASS');self.assertTrue(self.choose(s,m,a)[3].data()['global_blockers']);self.assertEqual(s.executor.total_effects,0)
    def test_source_not_allowed_adoption_rejected_and_pending_retained(self):
        s,w,m=self.session('shared');admit(s,'unknown',s.forecast,.7,.8,'not-allowed','unknown',False);a,p,f,v,front,c,d=self.choose(s,m);self.assertEqual(c.target,'unknown');self.assertNotEqual(s.execute(c)['status'],'PASS');next_choice=self.choose(s,m,a);self.assertIn('unknown',next_choice[-1]['pending_reports']);self.assertFalse(next_choice[-1]['review_complete'])
    def test_repeated_reads_and_unrelated_tick_do_not_create_retry(self):
        s,w,m=self.session('unavailable');p,f,v,_=self.capture(s,m);a=Consumer();_,c,_=a.choose(p,v);self.assertIsNotNone(c);_,again,_=a.choose(p,v);self.assertIsNone(again);s.emit('tick',time=1);p,_,v,_=self.capture(s,m);_,again,_=a.choose(p,v);self.assertIsNone(again)
        s.publish_probe(replace(s.probes['source-b'],opportunity=1));p,_,v,_=self.capture(s,m);self.assertIsNotNone(a.choose(p,v)[1])
    def test_tiny_graph_bound_and_deeper_route_never_dispatch_partial_nodes(self):
        s,w,m=self.session();self.assertIsNone(self.choose(s,m,limits=GraphLimits(nodes=1))[5]);r=ProbabilityRule('deep','1',DeductionRule('staged','middle','healthy'));s.register_rule(r);entry=self.choose(s,m);self.assertFalse(entry[3].data()['complete']);self.assertEqual(entry[0].stop,'INPUT_OR_WORK_INCOMPLETE');self.assertIsNone(entry[5])
    def test_malformed_and_mismatched_view_rejected_without_new_graph_work(self):
        s,w,m=self.session();p,f,v,_=self.capture(s,m)
        for bad in (ObligationWorkView('{}'),ObligationWorkView('[]'),ObligationWorkView('{'),None):self.assertIsNone(Consumer().choose(p,bad)[1])
        bad=v.data();bad['nodes']=[{}];self.assertIsNone(Consumer().choose(p,ObligationWorkView(json.dumps(bad)))[1])
        s.emit('tick',time=1);self.assertIsNone(Consumer().choose(s.read(),v)[1])
    def test_work_view_and_shadow_assessment_cannot_be_permissions(self):
        s,w,m=self.session('shared');p,f,v,_=self.capture(s,m);b,_=evaluate(immutable(f.data()['capture']),m,'B');before=state_digest(s.service)
        for value in (v,b):
            with self.assertRaises(ValueError):s.service.reserve_and_record_intent(value,idempotency_key='bad')
            with self.assertRaises(ValueError):s.service.register_decision_contract(value,idempotency_key='bad-contract')
        self.assertEqual(state_digest(s.service),before)
    def test_exact_model_parent_does_not_rebind_equal_replacement(self):
        s,w,m=self.session('shared');a,p,f,v,front,c,d=self.choose(s,m);s.emit('revoke',evidence_id='a');admit(s,'equal',s.forecast,.7,.8,'source-a','root:a');r,check=execute_current(s,c);self.assertEqual(r['status'],'STALE');next_entry=self.choose(s,m,a);self.assertIsNone(next_entry[5]);self.assertTrue(any(n.get('missing_slots') for n in next_entry[3].data()['nodes'] if n['kind']=='operation'))
    def test_support_change_rejects_selected_tuple_then_fresh_tuple_is_rediscovered(self):
        s,w,m=self.session();a,p,f,v,front,c,d=self.choose(s,m);self.assertEqual(c.kind,'deduction');old=next(b for q in p.numerical for b in q.current if b.belief_revision_id==c.premise_ids[0]);s.emit('revoke',evidence_id=old.transition.evidence_id);admit(s,'equal',old.proposal.support.conclusion,old.proposal.support.truth.strength,.8);self.assertEqual(execute_current(s,c)[0]['status'],'STALE');fresh=self.choose(s,m,a)[5];self.assertIsNotNone(fresh);self.assertNotEqual(fresh.basis,c.basis)
    def test_new_review_after_reservation_prevents_dispatch(self):
        s,w,m=self.session('shared');a,p,f,v,front,c,d=self.choose(s,m);s.execute(c);reserve=self.choose(s,m,a)[5];self.assertEqual(reserve.kind,'reserve');self.assertEqual(s.execute(reserve)['status'],'PASS')
        s.register_rule(ProbabilityRule('new-investigation','1',DeductionRule('tested','new','healthy')));entry=self.choose(s,m,a);self.assertIsNone(entry[5]);self.assertFalse(entry[-1]['review_complete']);self.assertEqual(s.executor.total_effects,0)
    def test_wrong_product_missing_health_and_later_unhealthy_have_distinct_outcomes(self):
        for variant in ('wrong-product','missing-health','later-unhealthy'):
            r,rows=self.run_episode('positive',variant);self.assertEqual(r['effects'],1);self.assertEqual(r['outstanding'],10);self.assertEqual(r['stop'],'WAITING_EXTERNAL_OUTCOME')
            if variant=='wrong-product':self.assertTrue(any(x.get('result',{}).get('status')=='FAIL' for x in rows));self.assertFalse(r['product_observed'])
            if variant=='missing-health':self.assertTrue(r['product_observed']);self.assertFalse(any(x['selected'] and x['selected']['target']=='health' for x in rows))
            if variant=='later-unhealthy':self.assertEqual(r['stage'],'BUILT');self.assertTrue({'observed_relief','reopened'}<=set(r['relief_kinds']))
    def test_monitoring_continues_after_live_block_and_even_incomplete_work_view(self):
        s,w,m=self.session('shared');a=Consumer()
        for _ in range(3):
            c=self.choose(s,m,a)[5];r=s.execute(c);w.after(c,r)
        self.assertEqual(s.read().dispatch.state,'accepted');admit(s,'adverse',s.forecast.negate(),.7,.8,'source-b','root:b')
        p,f,v,_=self.capture(s,m,GraphLimits(nodes=0));front,c,d=a.choose(p,v);self.assertEqual((c.kind,c.target),('request','product'));self.assertEqual(d['selected_origin'],'existing-operational-control');self.assertEqual(s.execute(c)['status'],'PASS')
    def test_uncertain_action_reconciles_without_another_effect_despite_numeric_block(self):
        s,w,m=self.session('shared');a=Consumer()
        for _ in range(2):s.execute(self.choose(s,m,a)[5])
        s.emit('dispatch',attempt_id='attempt',fault='lost_reply');self.assertEqual(s.read().dispatch.state,'uncertain');self.assertEqual(s.executor.total_effects,1)
        admit(s,'adverse',s.forecast.negate(),.7,.8,'source-b','root:b')
        c=self.choose(s,m,a,GraphLimits(nodes=0))[5];self.assertEqual(c.kind,'query');self.assertEqual(s.execute(c)['status'],'PASS');self.assertEqual(s.read().dispatch.state,'accepted');self.assertEqual(s.executor.total_effects,1)
    def test_matched_state_mandatory_source_changes_eligible_work(self):
        s,w,m=self.session('unavailable');s.publish_probe(Probe('source-c','unclassified-source','numeric',s.forecast));other=copy.deepcopy(m)
        selector=next(x for x in other['classes'] if x['id']=='b');selector['identity']=['unclassified-source'];selector['roots']=['root:c'];other['work_task']['revision']='matched-source-c/v1'
        left=self.choose(s,m);right=self.choose(s,other);self.assertEqual(left[1].binding,right[1].binding);self.assertEqual((left[5].target,right[5].target),('source-b','source-c'));self.assertEqual(left[3].data()['A']['numerical_status'],right[3].data()['A']['numerical_status'])
    def test_numeric_budget_preserves_monitoring_headroom_and_reports_exhaustion(self):
        s,w,m=self.session();a=Consumer(Limits(selections=8));entry=self.choose(s,m,a);self.assertIsNone(entry[5]);self.assertEqual(a.stop,'WORK_OR_ACQUISITION_EXHAUSTED')
    def test_public_only_import_boundary_and_read_only_capture(self):
        s,w,m=self.session();before=state_digest(s.service);calls=len(s.runtime.calls);self.choose(s,m);self.assertEqual(before,state_digest(s.service));self.assertEqual(calls,len(s.runtime.calls))
        tree=ast.parse(Path('experimental_work_loop/consumer.py').read_text())
        for n in ast.walk(tree):
            if isinstance(n,ast.ImportFrom):self.assertFalse((n.module or '').startswith(('work_loop_lab','validation_lab','obligations_lab')))
        source=Path('experimental_work_loop/consumer.py').read_text();self.assertNotIn('Candidate(',source);self.assertNotIn('.fixture',source)
