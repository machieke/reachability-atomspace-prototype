"""Bounded dependency work, exact authority and unchanged one-hop control tests."""
import copy,json,unittest,subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from dataclasses import replace
from experimental_multihop.consumer import Consumer,observe,execute_current
from experimental_multihop.project import Limits,MultiHopView
from experimental_work_loop.consumer import Consumer as OriginalConsumer,observe as original_observe
from experimental_online_pln.agenda import wire,Limits as Budgets,Probe
from experimental_obligations.capture import state_digest
from reachability.pln_adapter import DeductionRule,implication
from reachability.probability_model import ProbabilityRule,ProbabilityIndependence
from world_lab.world import PhysicalWorld
from work_loop_lab.cases import admit,World as OriginalWorld,manifest as original_manifest
from multihop_lab.cases import setup,initialize,fixture,fixtures,manifest,configuration,specification,Port,PARENTS,literal
from multihop_lab.run import episode
from multihop_lab.reference import graph,ancestry,fixture_witness,final


class MultiHopTests(unittest.TestCase):
    def session(self,parent='two-hop',native=False):
        tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup);s=setup(tmp.name,native);self.addCleanup(s.close);responses=initialize(s,parent);w=PhysicalWorld(specification(parent),configuration()['physical_goal']);w.advance(0)
        port=Port(s,w,responses,configuration()['public_opportunities'],numeric_channel=fixture(parent)['numeric_channel']);s.acquire=port.acquire;port.publish(0)
        return s,w,port,Consumer(),manifest(parent)
    def choose(self,s,c,m,limits=Limits()):
        p,f,v,cost=observe(s,m,limits);front,selected,why=c.choose(p,v);return selected,p,f,v,why
    def step(self,s,c,m):
        selected,p,f,v,why=self.choose(s,c,m);self.assertIsNotNone(selected,why);graph(p,m,v.data());r,check=execute_current(s,selected);return selected,r
    def compute(self,s,c,m):
        while True:
            selected,p,f,v,why=self.choose(s,c,m)
            if selected is None or selected.kind in ('reserve','dispatch'):return selected,p,f,v,why
            graph(p,m,v.data());self.assertEqual(execute_current(s,selected)[0]['status'],'PASS')
    def run_episode(self,parent,native=False):
        tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup);root=Path(tmp.name)/'run';r=episode(parent,root,native);self.assertEqual(r['conformance'],'PASS',r.get('traceback'))
        rows=[json.loads(x) for x in (root/'trace.jsonl').read_text().splitlines()];initial=json.loads((root/'initial.json').read_text());changes=json.loads((root/'changes.json').read_text());final(fixture(parent),initial,rows,r,changes);return r,rows
    def test_six_finite_structures_actual_depth_and_physical_outcomes(self):
        for parent in PARENTS:self.run_episode(parent)
    def test_explicit_joint_witnesses_cover_declared_chain_sources(self):
        for f in fixtures()['parents']:
            value,checked=fixture_witness(f);self.assertGreaterEqual(len(checked),7)
    def test_templates_cannot_execute_missing_AND_or_name_hypothetical_estimates(self):
        s,w,port,c,m=self.session();selected,p,f,v,why=self.choose(s,c,m);graph(p,m,v.data());self.assertEqual((selected.kind,selected.target),('request','upstream-leaf'))
        templates=[n for n in v.data()['nodes'] if n['kind']=='producer-template'];self.assertEqual(len(templates),2);self.assertTrue(all(not n['applications'] and not n['executable'] for n in templates));self.assertEqual(len(s.runtime.calls),0)
    def test_second_hop_uses_exact_selected_committed_intermediate(self):
        s,w,port,c,m=self.session()
        for _ in range(3):selected,r=self.step(s,c,m)
        mid=r['commit'].belief;self.assertEqual(selected.target,'r-mid');selected,p,f,v,why=self.choose(s,c,m);self.assertEqual(selected.target,'r-final');self.assertIn(mid.belief_revision_id,selected.premise_ids)
        r,_=execute_current(s,selected);self.assertEqual(r['status'],'PASS');self.assertTrue(set(mid.proposal.support.evidence_ids)<=set(r['commit'].belief.proposal.support.evidence_ids));self.assertEqual(s.executor.total_effects,0);self.assertEqual(s.read().goal.projection.outstanding_loss,10)
    def test_shared_intermediate_is_one_record_referenced_twice(self):
        s,w,port,c,m=self.session('shared');self.compute(s,c,m);hist={b.belief_revision_id:wire(b) for q in s.read().numerical for b in q.historical};mids=[i for i,b in hist.items() if b['transition']['rule_id']=='r-mid'];self.assertEqual(len(mids),1);self.assertEqual(sum(mids[0] in b['transition']['premise_revision_ids'] for b in hist.values()),2);self.assertEqual(max(ancestry(hist)[0].values()),3)
    def test_unavailable_leaf_is_requested_once_without_phantom_confidence(self):
        s,w,port,c,m=self.session('unavailable');self.assertEqual(self.step(s,c,m)[1]['status'],'UNKNOWN');self.assertIsNone(self.choose(s,c,m)[0]);self.assertEqual(len(s.runtime.calls),0);self.assertEqual(c.acquisitions,1);self.assertEqual(s.executor.total_effects,0)
    def test_wrong_order_and_phantom_ids_are_rejected_by_original_authority(self):
        s,w,port,c,m=self.session()
        for _ in range(2):self.step(s,c,m)
        chosen=self.choose(s,c,m)[0];self.assertEqual(chosen.kind,'deduction')
        for ids in (tuple(reversed(chosen.premise_ids)),('imaginary-intermediate',)+chosen.premise_ids[1:]):self.assertNotEqual(s.numeric('deduction',chosen.target,ids)['status'],'PASS')
        self.assertEqual(len(s.runtime.calls),0)
    def test_cycle_without_grounding_is_incomplete_and_cannot_bootstrap(self):
        s,w,port,c,m=self.session();source=next(x for x in fixture('two-hop')['sources'] if x['literal']==wire(implication('tested','b')));s.emit('revoke',evidence_id=source['id']);s.register_rule(ProbabilityRule('cycle','1',DeductionRule('tested','c','b')))
        selected,p,f,v,why=self.choose(s,c,m);self.assertIsNone(selected);self.assertEqual(v.data()['reason'],'DEPENDENCY_CYCLE');graph(p,m,v.data());self.assertEqual(len(s.runtime.calls),0)
    def test_depth_four_stays_visible_even_if_a_current_source_can_fill_slot(self):
        s,w,port,c,m=self.session('three-hop');s.register_rule(ProbabilityRule('fourth','1',DeductionRule('b','x','c')));selected,p,f,v,why=self.choose(s,c,m);self.assertIsNone(selected);self.assertEqual(v.data()['reason'],'DEPENDENCY_DEPTH_BOUND');self.assertTrue(any(n['kind']=='depth-cutoff' for n in v.data()['nodes']));graph(p,m,v.data())
        bad=v.data();bad['complete']=True
        with self.assertRaises(AssertionError):graph(p,m,bad)
    def test_bounds_remain_incomplete_and_do_not_reset_budget(self):
        s,w,port,c,m=self.session();entry=self.choose(s,c,m,Limits(nodes=1));self.assertIsNone(entry[0]);self.assertFalse(entry[3].data()['complete']);self.assertEqual(c.selections,0)
        small=Consumer(Budgets(selections=8));self.assertIsNone(self.choose(s,small,m)[0]);self.assertEqual(small.stop,'WORK_OR_ACQUISITION_EXHAUSTED')
    def test_unchanged_rebuild_is_identical_and_materialized_tuple_not_repeated(self):
        s,w,port,c,m=self.session();before=state_digest(s.service);v1=observe(s,m)[2];v2=observe(s,m)[2];self.assertEqual(v1,v2);self.assertEqual(state_digest(s.service),before)
        self.compute(s,c,m);calls=len(s.runtime.calls);s.emit('tick',time=1);self.assertEqual(self.choose(s,c,m)[0].kind,'reserve');self.assertEqual(len(s.runtime.calls),calls)
    def test_revoke_leaf_retires_every_descendant_but_unrelated_branch_survives(self):
        s,w,port,c,m=self.session();self.compute(s,c,m);prior=[b for q in s.read().numerical for b in q.current if b.transition.kind=='deduction']
        rule=ProbabilityRule('unrelated','1',DeductionRule('u','v','w'));s.register_rule(rule);ids=[]
        for i,lit in enumerate(rule.deduction.premises):ids.append(admit(s,'other-'+str(i),lit,.5 if i<3 else .9375,.96875).belief_revision_id)
        unrelated=s.numeric('deduction','unrelated',tuple(ids))['commit'].belief
        s.emit('revoke',evidence_id=next(x['id'] for x in fixture('two-hop')['sources'] if x['missing']));current={b.belief_revision_id for q in s.read().numerical for b in q.current};self.assertFalse(current & {b.belief_revision_id for b in prior});self.assertIn(unrelated.belief_revision_id,current)
        self.assertTrue(all(q.historical for q in s.read().numerical))
    def test_equal_replacement_cannot_revive_stale_selected_final(self):
        s,w,port,c,m=self.session()
        for _ in range(3):self.step(s,c,m)
        old=self.choose(s,c,m)[0];source=next(x for x in fixture('two-hop')['sources'] if x['missing']);s.emit('revoke',evidence_id=source['id']);admit(s,'equal-new',literal(source['literal']),source['strength'],source['confidence'],source['source'],'root:new',False)
        self.assertEqual(execute_current(s,old)[0]['status'],'STALE');self.assertEqual(self.step(s,c,m)[0].kind,'adopt');self.assertEqual(self.step(s,c,m)[0].target,'r-mid');fresh=self.choose(s,c,m)[0];self.assertEqual(fresh.target,'r-final');self.assertNotEqual(old.premise_ids,fresh.premise_ids)
    def test_rule_revision_invalidates_intermediate_and_pending_tuple(self):
        s,w,port,c,m=self.session()
        for _ in range(3):self.step(s,c,m)
        pending=self.choose(s,c,m)[0];s.register_rule(replace(s.rules['r-mid'],revision='2'),expected_revision='1');self.assertEqual(execute_current(s,pending)[0]['status'],'STALE');entry=self.choose(s,c,m);self.assertFalse(entry[-1]['review_complete']);self.assertEqual(entry[0].target,'r-mid')
    def test_new_relevant_registry_producer_invalidates_completed_review(self):
        s,w,port,c,m=self.session();reserve,p,f,v,why=self.compute(s,c,m);self.assertTrue(why['review_complete']);self.assertEqual(execute_current(s,reserve)[0]['status'],'PASS')
        s.register_rule(ProbabilityRule('new-root','1',DeductionRule('tested','new','healthy')));entry=self.choose(s,c,m);self.assertIsNone(entry[0]);self.assertFalse(entry[-1]['review_complete']);self.assertEqual(s.executor.total_effects,0);self.assertNotEqual(entry[3].data()['bindings']['inventory_digest'],v.data()['bindings']['inventory_digest'])
    def test_pending_adverse_report_adopted_without_value_filter(self):
        s,w,port,c,m=self.session();admit(s,'late-opposite',s.forecast.negate(),.1,.05,'source-b','unknown-root',False);chosen,r=self.step(s,c,m);self.assertEqual((chosen.kind,chosen.target),('adopt','late-opposite'));self.assertEqual(r['status'],'PASS');self.assertEqual(s.executor.total_effects,0);self.assertTrue(self.choose(s,c,m)[3].data()['global_blockers'])
    def test_favorable_final_cannot_skip_unexamined_adverse_route(self):
        s,w,port,c,m=self.session();self.compute(s,c,m);self.assertEqual(s.read().decision.status.value,'PASS')
        rule=ProbabilityRule('adverse-new','1',DeductionRule('tested','z','healthy'));s.register_rule(rule)
        for i,(lit,value) in enumerate(zip(rule.deduction.premises,(.5,.5,.5,.9375,.0625))):
            if lit not in (rule.deduction.premises[0],rule.deduction.premises[2]):admit(s,'adverse-new-'+str(i),lit,value,.96875)
        entry=self.choose(s,c,m);self.assertFalse(entry[-1]['review_complete']);self.assertEqual(entry[0].target,'adverse-new');self.assertEqual(execute_current(s,entry[0])[0]['status'],'PASS');self.assertEqual(s.read().decision.status.value,'FAIL');self.assertEqual(s.executor.total_effects,0)
    def test_copied_roots_and_converging_paths_cannot_be_revised_as_independent(self):
        s,w,port,c,m=self.session('shared');self.compute(s,c,m);finals=s.read().decision.criteria[0].current;ids=tuple(b.belief_revision_id for b in finals);self.assertEqual(len(ids),2);s.register_model(ProbabilityIndependence('converging','ctx',ids,'deliberately false independence boundary'));self.assertNotEqual(s.numeric('revision','converging',ids)['status'],'PASS')
        a=admit(s,'copy-a',s.forecast,.8,.8,'source-a','shared-root');b=admit(s,'copy-b',s.forecast,.8,.8,'source-b','shared-root');ids=(a.belief_revision_id,b.belief_revision_id);s.register_model(ProbabilityIndependence('copied','ctx',ids,'deliberately copied roots'));self.assertNotEqual(s.numeric('revision','copied',ids)['status'],'PASS')
    def test_accepted_uncertain_action_keeps_control_under_incomplete_graph(self):
        s,w,port,c,m=self.session();reserve,*_=self.compute(s,c,m);execute_current(s,reserve);s.emit('dispatch',attempt_id='attempt',fault='lost_reply');port.sync_effect();self.assertEqual(s.read().dispatch.state,'uncertain');s.register_rule(ProbabilityRule('deep','1',DeductionRule('b','x','c')))
        entry=self.choose(s,c,m,Limits(nodes=0));self.assertEqual(entry[0].kind,'query');self.assertEqual(execute_current(s,entry[0])[0]['status'],'PASS');self.assertEqual(s.executor.total_effects,1)
    def test_one_hop_selected_behavior_matches_frozen_consumer(self):
        tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup);s=setup(tmp.name);self.addCleanup(s.close);world=OriginalWorld('positive');world.initialize(s);s.acquire=world.acquire;m=original_manifest('positive');m['multihop_review']=fixture('two-hop')['manifest']['multihop_review'];old=OriginalConsumer();new=Consumer()
        for _ in range(24):
            p,_,old_view,_=original_observe(s,m);p2,_,new_view,_=observe(s,m);self.assertEqual(p.binding,p2.binding);left=old.choose(p,old_view);right=new.choose(p2,new_view);self.assertEqual(wire(left[1]),wire(right[1]));self.assertEqual(old.stop,new.stop)
            if right[1] is None:break
            result=execute_current(s,right[1])[0];world.after(right[1],result)
        self.assertEqual(s.read().goal.projection.outstanding_loss,0)
    def test_frozen_one_step_stays_explicitly_out_of_scope(self):
        s,w,port,c,m=self.session();p,_,v,_=original_observe(s,m);self.assertEqual(v.data()['reason'],'UNEXPANDED_DEEPER_ROUTE');self.assertIsNone(OriginalConsumer().choose(p,v)[1]);self.assertIsNotNone(self.choose(s,c,m)[0])
    def test_read_only_work_and_typed_permission_boundary(self):
        s,w,port,c,m=self.session();before=state_digest(s.service);entry=self.choose(s,c,m);self.assertEqual(state_digest(s.service),before)
        with self.assertRaises(ValueError):s.service.reserve_and_record_intent(entry[3],idempotency_key='bad')
        self.assertEqual(state_digest(s.service),before)
    def test_original_implementations_remain_byte_identical(self):
        for name in ('experimental_work_loop/consumer.py','experimental_work_bridge/project.py','world_lab/world.py','world_lab/adapter.py','experimental_obligations/evaluate.py','reachability/probability_formula.py'):
            self.assertEqual(Path(name).read_bytes(),subprocess.check_output(['git','show','716b4c0:'+name]))
