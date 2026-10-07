"""Independent physical traces, passive boundary and actual executor controls."""
import copy,json,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from dataclasses import replace
from world_lab.world import PhysicalWorld
from world_lab.adapter import Port
from world_lab.cases import setup,initialize,configuration,specification,manifest,PARENTS
from world_lab.run import episode
from world_lab.reference import physical_trace,validate,public_boundary
from experimental_work_loop.consumer import Consumer,observe,execute_current
from experimental_online_pln.agenda import Probe,wire
from experimental_obligations.capture import state_digest


class IndependentWorldTests(unittest.TestCase):
    def session(self,parent='observable',task='positive'):
        tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup);s=setup(tmp.name);self.addCleanup(s.close)
        cfg=configuration();w=PhysicalWorld(specification(parent),cfg['physical_goal']);w.advance(0)
        port=Port(s,w,initialize(s,task),cfg['public_opportunities']);s.acquire=port.acquire;port.publish(0)
        return s,w,port,Consumer(),manifest(task)
    def command(self,lost=False):
        s,w,port,c,m=self.session()
        for _ in range(8):
            p,_,v,_=observe(s,m);candidate=c.choose(p,v)[1];self.assertIsNotNone(candidate)
            if candidate.kind=='dispatch' and lost:
                result=s.emit('dispatch',attempt_id='attempt',fault='lost_reply')['outcome']
            else:result=execute_current(s,candidate)[0]
            port.sync_effect()
            if candidate.kind=='dispatch':return s,w,port,c,m,result
        self.fail('no actual command selected')
    def run_episode(self,parent,**kw):
        tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup);root=Path(tmp.name)/'run';r=episode(parent,root,**kw);self.assertEqual(r['conformance'],'PASS',r.get('traceback'))
        return r,json.loads((root/'ticks.json').read_text()),json.loads((root/'private.json').read_text()),root
    def test_all_six_predeclared_finite_worlds_and_separate_goal_metrics(self):
        for parent in PARENTS:
            with self.subTest(parent=parent):
                r,t,p,_=self.run_episode(parent);self.assertEqual(len(t),9);self.assertEqual(r['effects'],1);self.assertEqual(len(p['state']['accepted']),1)
                self.assertEqual(p['state']['history'],physical_trace(specification(parent),p['state']['accepted'],8,configuration()['physical_goal']))
    def test_passive_count_order_outage_and_observer_removal_same_physical_commands(self):
        s,world,port,c,m,r=self.command();request=s.read().dispatch.dispatch.request;receipt=s.executor.query(request);cfg=configuration();histories=[]
        for mode in ('none','product-health','health-product','many','outage'):
            spec=specification('regression')
            if mode=='outage':spec['outages']={'product':list(range(9)),'health':list(range(9))}
            w=PhysicalWorld(spec,cfg['physical_goal']);w.advance(0);w.accept(request,receipt)
            for tick in range(1,9):
                w.advance(tick);before=w.state()
                channels=[] if mode=='none' else ['health','product'] if mode=='health-product' else ['product','health']*(10 if mode=='many' else 1)
                for channel in channels:w.measure(channel)
                self.assertEqual(w.state(),before)
            histories.append(w.history)
        self.assertTrue(all(h==histories[0] for h in histories))
    def test_actual_lost_reply_effect_survives_and_idempotent_duplicate_does_not_repeat(self):
        s,w,port,c,m,result=self.command(lost=True);self.assertEqual(result['status'],'PASS');self.assertEqual(s.read().dispatch.state,'uncertain');self.assertIsNone(s.read().dispatch.latest_receipt);self.assertEqual(len(w.accepted),1)
        request=s.read().dispatch.dispatch.request;receipt=s.executor.submit(request);self.assertEqual(receipt.effect_count,1);self.assertFalse(w.accept(request,receipt));port.sync_effect();self.assertEqual(len(w.accepted),1)
        before=state_digest(s.service);w.advance(1);self.assertEqual(state_digest(s.service),before);self.assertEqual(w.installed,'artifact-v2');self.assertEqual(s.read().dispatch.state,'uncertain')
        port.publish(1);p,_,v,_=observe(s,m);candidate=c.choose(p,v)[1];self.assertEqual(candidate.kind,'query');self.assertEqual(execute_current(s,candidate)[0]['status'],'PASS');self.assertEqual(s.executor.total_effects,1)
    def test_no_accepted_command_polling_cannot_install_or_satisfy_world_goal(self):
        s,w,port,c,m=self.session();before=state_digest(s.service)
        for tick in range(9):
            if tick:w.advance(tick)
            for channel in ('product','health'):
                w.measure(channel);w.measure(channel)
            self.assertIsNone(w.installed);self.assertFalse(w.healthy);self.assertEqual(w.history[-1]['goal_deficit'],10)
        self.assertEqual(state_digest(s.service),before);self.assertEqual(s.executor.total_effects,0)
    def test_port_itself_is_passive_for_physics_and_authority(self):
        s,w,port,c,m=self.session();before=state_digest(s.service);physical=w.state()
        for channel,source in (('product','executor'),('health','monitor')):
            for _ in range(3):port.acquire(Probe(channel,source,channel,'artifact-v2'))
        self.assertEqual(w.state(),physical);self.assertEqual(state_digest(s.service),before);self.assertEqual(len(port.measurements),6)
    def test_absent_executor_receipt_never_schedules_a_deployment(self):
        s,w,port,c,m=self.session()
        for _ in range(5):
            p,_,v,_=observe(s,m);candidate=c.choose(p,v)[1];execute_current(s,candidate);port.sync_effect()
        self.assertIsNotNone(s.read().intent);self.assertEqual(len(w.accepted),0);self.assertEqual(s.executor.total_effects,0);w.advance(1);self.assertIsNone(w.installed)
    def test_live_A_blocked_remains_unauthorized_through_independent_ticks(self):
        r,t,p,_=self.run_episode('observable',task='blocked');self.assertEqual(r['effects'],0);self.assertEqual(r['metrics']['J_world'],90);self.assertEqual(r['selections'],1);self.assertTrue(all(x['consumer_stop']=='TASK_RESOLVED_LIVE_BLOCKED' for x in t));self.assertFalse(p['state']['accepted'])
    def test_idle_world_advances_delayed_effect_without_successful_queries(self):
        r,t,p,_=self.run_episode('delayed');self.assertEqual(t[0]['physical_end']['operation'],'pending');self.assertEqual(t[0]['authority_after']['dispatch'],'accepted')
        self.assertFalse(t[2]['steps_summary']);self.assertFalse(t[3]['steps_summary']);self.assertIsNone(t[3]['physical_sample']['installed']);self.assertEqual(t[4]['physical_sample']['installed'],'artifact-v2');self.assertEqual(r['metrics']['first_physical_goal'],6)
    def test_unobservable_physical_success_remains_uncertified(self):
        r,t,p,_=self.run_episode('unobservable');self.assertEqual((r['metrics']['J_world'],r['metrics']['J_certified']),(30,90));self.assertIsNone(r['metrics']['first_observed_completion']);self.assertTrue(any(x['mismatch_reasons'] for x in t))
    def test_first_health_query_reports_already_existing_failure(self):
        r,t,p,_=self.run_episode('early-failure');health=[x for x in p['measurements'] if x['probe']['report_type']=='health'];self.assertEqual(health[0]['time'],1);self.assertFalse(t[1]['physical_sample']['healthy']);self.assertFalse(health[0]['sample']['value']);self.assertEqual(health[0]['response']['events'],[['sample',{'healthy':False}]]);self.assertEqual(r['stage'],'DRAFT')
    def test_history_preserved_and_regression_is_recognized_after_outage(self):
        r,t,p,_=self.run_episode('regression');self.assertEqual(r['stage'],'BUILT');self.assertEqual(r['outstanding'],10);self.assertEqual(r['metrics']['recognition'],[dict(change=6,first_adverse_sample=7,lag=1)]);self.assertTrue({'observed_relief','reopened'}<=set(r['relief_kinds']));self.assertEqual(t[6]['physical_sample']['goal_deficit'],10)
    def test_wrong_artifact_truth_is_not_relabelled_to_satisfy_contract(self):
        r,t,p,_=self.run_episode('wrong-artifact');self.assertEqual(r['outstanding'],10);self.assertEqual(p['state']['installed'],'artifact-v1');self.assertTrue(any(x.get('result',{}).get('status')=='FAIL' for tick in t for x in tick['steps_summary']));self.assertFalse(r['product_observed'])
    def test_failed_effect_is_recorded_without_product_or_observed_completion(self):
        spec=specification('observable');spec['effect']='failed';r,t,p,_=self.run_episode('observable',spec_override=spec);self.assertEqual(r['effects'],1);self.assertEqual(p['state']['operation'],'failed');self.assertIsNone(p['state']['installed']);self.assertEqual(r['metrics']['J_world'],90);self.assertIsNone(r['metrics']['first_observed_completion'])
    def test_physical_mutation_cannot_write_evidence_or_permission(self):
        s,w,port,c,m,r=self.command();before=state_digest(s.service)
        for tick in (1,2,3):w.advance(tick)
        self.assertEqual(w.history[-1]['goal_deficit'],0);self.assertEqual(state_digest(s.service),before);self.assertEqual(s.read().goal.projection.outstanding_loss,10)
    def test_public_schedule_does_not_reveal_hidden_health_or_channels(self):
        cfg=configuration();records=[]
        for parent in PARENTS:
            s,w,port,c,m=self.session(parent)
            for tick in range(1,9):w.advance(tick);port.publish(tick)
            records.append(port.public_events)
        self.assertTrue(all(r==records[0] for r in records));self.assertTrue(all(p['availability']=='unknown' for event in records[0] for p in event['probes']))
    def test_delayed_or_misaligned_sample_is_not_relabeled_current(self):
        s,w,port,c,m=self.session();w.advance(1);before=state_digest(s.service)
        with self.assertRaises(ValueError):port.acquire(Probe('product','executor','product','artifact-v2'))
        self.assertEqual(state_digest(s.service),before);self.assertFalse(port.measurements)
    def test_hidden_truth_input_event_and_observation_side_effect_mutations_rejected(self):
        s,w,port,c,m=self.session();public=s.read();contracts=public.contracts
        with self.assertRaises(AssertionError):public_boundary(replace(public,received=public.received+({'kind':'hidden-world','goal_deficit':0},)),contracts)
        r,t,p,_=self.run_episode('observable');cfg=configuration();spec=specification('observable')
        for field,value in (('installed','artifact-v2'),('healthy',True)):
            bad=copy.deepcopy(p);bad['measurements'][0]['physical_after'][field]=value
            with self.assertRaises(AssertionError):validate(spec,cfg,t,bad,r)
        bad=copy.deepcopy(r);bad['metrics']['J_world']=bad['metrics']['final_observed_loss']
        with self.assertRaises(AssertionError):validate(spec,cfg,t,p,bad)
    def test_reference_does_not_import_world_and_consumer_is_unchanged(self):
        source=Path('world_lab/reference.py').read_text();self.assertNotIn('from .world',source);self.assertNotIn('PhysicalWorld',source)
        import subprocess
        for path in ('experimental_work_loop/consumer.py','experimental_work_bridge/project.py','experimental_obligations/evaluate.py'):
            self.assertEqual(Path(path).read_bytes(),subprocess.check_output(['git','show','173c772:'+path]))
