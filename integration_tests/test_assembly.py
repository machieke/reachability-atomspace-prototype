"""Native service opportunities, ordered bundles, failures and unchanged authority."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json,unittest
from unittest.mock import patch
from experimental_assembly.controller import Agenda
from experimental_attention.controller import Agenda as Frozen,Search
from experimental_attention.workspace import Caps,Bound
from experimental_attention.field import StaleField
from experimental_native_recall.session import Session
from experimental_native_recall.backend import Backend
from experimental_native_recall.schema import QueryLimits
from experimental_online_pln.agenda import Limits
from reachability.pln_adapter import TruthValue
from assembly_lab.cases import World,PARENTS
from assembly_lab.episode import run_case


class AssemblyIntegrationTests(unittest.TestCase):
    def setup_case(self,name='ready-broad',native=False):
        tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup);w=World(next(p for p in PARENTS if p['id']==name));s=Session(tmp.name,native=native,acquire=w.acquire);self.addCleanup(s.close);w.setup(s);return s,w
    def agenda(self,mode='WS-flow',contract='assembly',q=16,**kw):
        a=Agenda(contract,mode,search=Search(q),**kw);self.addCleanup(a.close);self.addCleanup(a.release);return a
    def test_same_public_snapshot_frozen_choices_and_actual_query_stream(self):
        s,w=self.setup_case('alternatives');view=s.read()
        for mode in ('WS-queue','WS-local','WS-flow'):
            a=self.agenda(mode,contract='frozen',q=48);b=Frozen(mode,caps=Caps(active=48,active_bytes=524288),search=Search(48));self.addCleanup(b.close)
            f,c=a.choose(view);g,d=b.choose(view);self.assertEqual(c,d);self.assertEqual(f.candidates,g.candidates)
            receipts=lambda x:[(e['result']['request'],e['result']['ids']) for e in x.backend.events if e['kind']=='query']
            self.assertEqual(receipts(a),receipts(b));a.release();b.release()
    def test_low_activation_affordable_join_runs_real_native_PLN_without_eager_rescue(self):
        s,w=self.setup_case(native=True);a=self.agenda();view=s.read()
        with (patch('experimental_native_recall.recall.NativeIndex.__init__',side_effect=AssertionError('eager')),
              patch('experimental_goal_pln.relevance.Index.__init__',side_effect=AssertionError('Python index')),
              patch('experimental_assembly.controller.full_frontier',side_effect=AssertionError('rescue'))):
            _,c=a.choose(view)
        self.assertEqual(c.kind,'deduction');self.assertEqual(len(c.premise_ids),5);self.assertEqual(a.service['state'],'SERVED')
        self.assertEqual(a.service['queries'],6);self.assertEqual(a.service['protected_at'],4)
        self.assertEqual(a.used_queries,10);self.assertEqual(len(a.ws.pins),10)
        result=s.execute(c);self.assertEqual(result['status'],'PASS');self.assertTrue(s.runtime.calls[-1]['formula_agreement'])
        self.assertEqual(s.executor.total_effects,0);self.assertEqual(s.read().goal.projection.outstanding_loss,10)
    def test_missing_AND_is_complete_negative_attempt_not_partial_inference(self):
        s,w=self.setup_case('missing-upstream');a=self.agenda(q=48);f,c=a.choose(s.read())
        served=[e for e in a.diagnostic['events'] if e['kind']=='join_end' and e['phase']=='assembly']
        self.assertEqual(served[0]['queries'],6);self.assertEqual(served[0]['reason'],'MISSING_PREMISES')
        self.assertFalse(any(x.kind=='deduction' and x.target=='d-target' for x in f.candidates))
        self.assertEqual(a.service['prepare_hold'],0)
    def test_FIFO_alternatives_do_not_read_success_labels(self):
        s,w=self.setup_case('unproductive-early');view=s.read()
        for mode in ('WS-queue','WS-local','WS-flow'):
            a=self.agenda(mode);_,c=a.choose(view);self.assertEqual(c.target,'a-low-yield')
            self.assertEqual(a.service['producer_read'],0);self.assertEqual(a.service['total'],12)
            self.assertEqual(a.service['protected_at'],4);a.release()
    def test_per_view_joint_tuple_and_indivisible_limits_stay_explicit(self):
        s,w=self.setup_case();view=s.read()
        a=self.agenda(q=48,backend=Backend(limits=QueryLimits(results=32,queries=12)))
        _,c=a.choose(view);self.assertLessEqual(a.backend.query_count,12);self.assertIsNone(a.service)
        self.assertTrue(any(o['reason']=='QUERY_RESERVATION' for e in a.diagnostic['events'] if e['kind']=='assembly_offers' for o in e['offers']))
        for kwargs,reason in ((dict(caps=Caps(active=48,joint_records=4)),'JOINT'),(dict(limits=Limits(work=16,tuple_visits=0)),'TUPLE')):
            b=self.agenda(mode='WS-queue',q=48,**kwargs);_,c=b.choose(view);self.assertIsNone(c);self.assertIn(reason,b.diagnostic['reason']);self.assertLessEqual(b.used_queries,48)
        b=self.agenda(q=48,caps=Caps(active=6));_,c=b.choose(view)
        self.assertIsNone(c);self.assertIsNone(b.service);self.assertLessEqual(b.used_queries,48)
        self.assertTrue(any(o['reason']=='BUNDLE_CAPACITY' for e in b.diagnostic['events'] if e['kind']=='assembly_offers' for o in e['offers']))
    def test_evicted_producer_and_selected_records_use_counted_exact_queries(self):
        s,w=self.setup_case();a=self.agenda(q=48)
        original=a.inspect_offers;evicted=False
        def inspect():
            nonlocal evicted
            if not evicted and any(j['kind']=='join' for j in a.jobs.values()):
                evicted=True
                for i in range(48):a.ws.admit('test-before-'+str(i),dict(kind='diagnostic-inspection'),anchor=True)
            return original()
        a.inspect_offers=inspect
        original_prepare=a.prepare
        def prepare(c):
            for i in range(48):a.ws.admit('test-after-'+str(i),dict(kind='diagnostic-inspection'),anchor=True)
            return original_prepare(c)
        a.prepare=prepare;_,c=a.choose(s.read())
        self.assertIsNotNone(c);self.assertEqual(a.service['producer_read'],1);self.assertEqual(a.service['queries'],7)
        event=next(e for e in a.diagnostic['events'] if e['kind']=='preparation_end');self.assertEqual(event['queries'],6)
        self.assertLessEqual(a.used_queries,48);self.assertLessEqual(a.diagnostic['peaks']['active'],48)
        self.assertEqual(s.execute(c)['status'],'PASS')
    def test_unchanged_joins_not_retried_or_reseeded(self):
        s,w=self.setup_case('missing-upstream');a=self.agenda();view=s.read();a.choose(view);a.release()
        first={e['producer'] for e in a.diagnostic['events'] if e['kind']=='join_begin'};epoch=a.backend.epochs;work=a.work
        a.choose(view)
        second={e['producer'] for e in a.diagnostic['events'] if e['kind']=='join_begin'}
        self.assertFalse(first&second);self.assertEqual(a.backend.epochs,epoch)
        self.assertEqual(next(e for e in a.diagnostic['events'] if e['kind']=='seed')['transferred'],0)
        self.assertTrue(all(e['wait_queries']>=0 for e in a.diagnostic['events'] if e['kind']=='join_begin'))
    def test_equal_support_replacement_and_new_producer_require_native_refresh(self):
        s,w=self.setup_case('refreshed-competing');a=self.agenda(q=48);_,old=a.choose(s.read());self.assertEqual(s.execute(old)['status'],'STALE');a.release()
        binding=a.binding;work=a.work;_,new=a.choose(s.read());self.assertNotEqual(binding,a.binding);self.assertGreater(a.work,work)
        self.assertTrue(any(e['kind']=='query' and e['result']['request']['kind']=='producers' and any('outside-new-producer' in i for i in e['result']['ids']) for e in a.backend.events))
        self.assertNotEqual(s.execute(old)['status'],'PASS')
    def test_stale_service_is_abandoned_without_publishing_selection(self):
        s,w=self.setup_case();a=self.agenda();view=s.read();before=s.authority_records()
        def guard():return 'changed' if a.service and a.service['state']=='SERVED' else view.binding
        with self.assertRaises(StaleField):a.choose(view,guard)
        self.assertEqual(a.service['state'],'ABANDONED_STALE');self.assertEqual(a.prepare_hold,0)
        self.assertEqual(a.work,0);self.assertEqual(s.authority_records(),before);self.assertEqual(s.executor.total_effects,0)
    def test_outside_contrary_evidence_still_blocks_full_authority(self):
        s,w=self.setup_case();a=self.agenda();_,c=a.choose(s.read());self.assertEqual(s.execute(c)['status'],'PASS');a.release()
        _,reserve=a.choose(s.read());self.assertEqual(reserve.kind,'reserve');self.assertIsNone(a.service)
        w.report('outside-contrary',s.forecast.negate(),TruthValue(.7,.8))
        self.assertNotEqual(s.execute(reserve)['status'],'PASS');self.assertNotEqual(s.reserve()['status'],'PASS');self.assertEqual(s.executor.total_effects,0)
    def test_unproductive_early_join_is_an_actual_adverse_control(self):
        results={}
        for contract in ('frozen','assembly'):
            with TemporaryDirectory() as tmp:
                r=run_case(next(p for p in PARENTS if p['id']=='unproductive-early'),Path(tmp)/'case',contract=contract,mode='WS-queue',queries=16,native=True)
                self.assertEqual(r['conformance'],'PASS',r.get('traceback'));results[contract]=r
        self.assertGreater(results['assembly']['outstanding'],results['frozen']['outstanding'])
        self.assertGreater(len(results['assembly']['runtime_calls']),0)
    def test_monitoring_wrong_product_and_later_reopening_under_competition(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/'case';r=run_case(next(p for p in PARENTS if p['id']=='monitor-competition'),path,contract='assembly',mode='WS-flow',queries=16,native=True)
            self.assertEqual(r['conformance'],'PASS',r.get('traceback'));self.assertEqual(r['effects'],1);self.assertEqual(r['outstanding'],10);self.assertIn('reopened',r['relief_kinds'])
            rows=[json.loads(t) for t in (path/'trace.jsonl').read_text().splitlines()]
            self.assertTrue(any(row.get('result',{}).get('status')=='FAIL' and row['selected']['target']=='product' for row in rows))
            self.assertTrue(any(row['selected'] and row['selected']['target']=='health' and row['discovery']['service'] is None for row in rows))

    def test_uncertain_dispatch_keeps_control_service_before_discovery(self):
        s,w=self.setup_case(native=True);a=self.agenda();_,c=a.choose(s.read());self.assertEqual(s.execute(c)['status'],'PASS');a.release()
        _,c=a.choose(s.read());self.assertEqual(c.kind,'reserve');self.assertEqual(s.execute(c)['status'],'PASS');a.release()
        s.emit('dispatch',attempt_id='attempt',fault='lost_reply')
        self.assertEqual(s.read().dispatch.state,'uncertain')
        _,c=a.choose(s.read());self.assertEqual(c.kind,'query');self.assertIsNone(a.service)
        self.assertEqual(a.diagnostic['reason'],'CONTROL_OBLIGATION_SERVICE')
        self.assertEqual(s.execute(c)['status'],'PASS');self.assertEqual(s.executor.total_effects,1)
        self.assertEqual(s.read().goal.projection.outstanding_loss,10)

    def test_six_preparation_credits_cannot_be_spent_by_optional_inspection(self):
        s,w=self.setup_case(native=True);a=self.agenda(q=16);original=a.prepare
        def prepare(c):
            for i in range(48):a.ws.admit('evict-before-pin-'+str(i),dict(kind='diagnostic'),anchor=True)
            return original(c)
        a.prepare=prepare;_,c=a.choose(s.read());self.assertIsNotNone(c)
        start=next(e for e in a.diagnostic['events'] if e['kind']=='preparation_begin')
        end=next(e for e in a.diagnostic['events'] if e['kind']=='preparation_end')
        self.assertEqual((start['held'],start['remaining'],end['queries'],a.used_queries),(6,6,6,16))
        self.assertEqual(s.execute(c)['status'],'PASS')

    def test_independent_service_ledger_rejects_resealed_credit_and_age_mutations(self):
        from copy import deepcopy
        from assembly_lab.reference import ServiceLedger
        from experimental_online_pln.agenda import wire
        s,w=self.setup_case();a=self.agenda();a.choose(s.read());d=wire(a.diagnostic)
        ServiceLedger().audit(d,a.caps,a.search,a.limits,wire(a.backend.events))
        for kind,key in (('assembly_protected','service'),('join_begin','wait_queries'),('query_start','remaining')):
            changed=deepcopy(d);e=next(e for e in changed['events'] if e['kind']==kind)
            if key=='service':e[key]['prepare_queries']=0
            else:e[key]+=1
            with self.assertRaises(ValueError):ServiceLedger().audit(changed,a.caps,a.search,a.limits,wire(a.backend.events))
