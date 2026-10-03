"""Real native recall/PLN and full authority under bounded field scheduling."""
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import json,unittest
from unittest.mock import patch
from experimental_attention.controller import Agenda,Search,anchor
from experimental_attention.workspace import Caps,Bound
from experimental_attention.field import StaleField
from experimental_native_recall.session import Session
from experimental_native_recall.backend import Backend,RecallError
from experimental_native_recall.agenda import Agenda as Complete
from experimental_online_pln.agenda import Limits,Probe,wire
from reachability.pln_adapter import TruthValue,DeductionRule
from reachability.probability_model import ProbabilityRule
from reachability.requirements import Requirement
from attention_lab.cases import World,PARENTS
from attention_lab.episode import run_case,settings


class AttentionIntegrationTests(unittest.TestCase):
    def setup_case(self,name='control'):
        tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup);w=World(next(p for p in PARENTS if p['id']==name));s=Session(tmp.name,acquire=w.acquire);self.addCleanup(s.close);w.setup(s);return s,w
    def agenda(self,mode='WS-flow',**kw):
        a=Agenda(mode,search=Search(48),**kw);self.addCleanup(a.close);self.addCleanup(a.release);return a
    def test_live_native_query_without_eager_discovery_and_real_deduction(self):
        s,w=self.setup_case();a=self.agenda();view=s.read()
        with (patch('experimental_native_recall.recall.NativeIndex.__init__',side_effect=AssertionError('eager native index')),
              patch('experimental_goal_pln.relevance.Index.__init__',side_effect=AssertionError('Python answer index')),
              patch('experimental_attention.controller.full_frontier',side_effect=AssertionError('full rescue'))):
            _,c=a.choose(view)
        self.assertEqual(c.kind,'deduction');self.assertEqual(len(c.premise_ids),5)
        self.assertNotIn('all_current',[e['result']['request']['kind'] for e in a.backend.events if e['kind']=='query'])
        self.assertTrue(a.pending_pins);before=set(a.ws.pins);self.assertGreaterEqual(len(before),9)
        self.assertEqual(s.execute(c)['status'],'PASS');a.release();self.assertFalse(a.pending_pins)
        self.assertGreater(s.costs['execution_enumeration_ns'],0)
    def test_missing_AND_is_acquisition_never_partial_deduction(self):
        s,w=self.setup_case('distractors');a=self.agenda();f,c=a.choose(s.read())
        self.assertEqual((c.kind,c.target),('request','source-report'));self.assertFalse(any(x.kind=='deduction' for x in f.candidates))
        self.assertEqual(s.execute(c)['status'],'PASS')
    def test_live_closed_masks_and_nontrivial_transport(self):
        s,w=self.setup_case('closed-sinks');a=self.agenda();_,c=a.choose(s.read())
        routes=[e['arc'] for e in a.diagnostic['events'] if e['kind']=='route'];closed={(r['source'],r['target']) for r in routes if r['status']!='PASS'}
        self.assertTrue(closed);steps=[e for e in a.diagnostic['events'] if e['kind']=='field'];self.assertTrue(any(e['closed_arcs'] for e in steps))
        self.assertTrue(any(value>0 for e in steps for _,_,value in e['flux']))
        self.assertFalse(any((source,target) in closed and amount for e in steps for source,target,amount in e['flux']))
        self.assertFalse(c and c.target.startswith('closed-'))
    def test_tuple_and_control_capacity_are_explicit(self):
        s,w=self.setup_case();a=Agenda('WS-flow',caps=Caps(active=6),search=Search(4096,True));self.addCleanup(a.close);_,c=a.choose(s.read())
        self.assertIsNone(c);self.assertIn('CAPACITY',a.diagnostic['reason']);self.assertEqual(s.executor.total_effects,0)
        b=self.agenda(caps=Caps(controls=0));_,c=b.choose(s.read());self.assertIsNone(c);self.assertIn('CONTROL',b.diagnostic['reason'])
    def test_activation_repeated_snapshot_and_queries_leave_authority_unchanged(self):
        s,w=self.setup_case();a=self.agenda();view=s.read();before=s.authority_records();seq=s.service._journal_sequence
        a.choose(view);a.release();epochs=a.backend.epochs;work=a.work
        _,c=a.choose(view)
        seeds=[e for e in a.diagnostic['events'] if e['kind']=='seed'];self.assertEqual(seeds[0]['transferred'],0)
        self.assertIsNone(c);self.assertEqual(a.work,work);self.assertEqual(a.backend.epochs,epochs)
        self.assertEqual(s.authority_records(),before);self.assertEqual(s.service._journal_sequence,seq);self.assertFalse(s.runtime.calls)
        self.assertEqual(s.executor.total_effects,0)
    def test_equal_replacement_new_producer_and_exact_stale_selection(self):
        s,w=self.setup_case('changed-support');a=self.agenda();_,old=a.choose(s.read());self.assertEqual(s.execute(old)['status'],'STALE');a.release()
        old_binding=a.binding;before=a.work;_,new=a.choose(s.read());self.assertNotEqual(a.binding,old_binding);self.assertGreater(a.work,before)
        self.assertTrue(any(e['kind']=='workspace_invalidated' for e in a.diagnostic['events']))
        self.assertNotEqual(s.execute(old)['status'],'PASS')
        producers=[e for e in a.backend.events if e['kind']=='query' and e['result']['request']['kind']=='producers']
        self.assertTrue(any('outside-new-producer' in i for e in producers for i in e['result']['ids']))
    def test_contrary_outside_workspace_blocks_authoritative_gate(self):
        s,w=self.setup_case();a=self.agenda();_,c=a.choose(s.read());s.execute(c);a.release()
        _,reserve=a.choose(s.read());self.assertEqual(reserve.kind,'reserve')
        w.report('outside-contrary',s.forecast.negate(),TruthValue(.7,.8))
        self.assertNotIn('outside-contrary',str(a.ws.entries))
        self.assertNotEqual(s.execute(reserve)['status'],'PASS');self.assertNotEqual(s.reserve()['status'],'PASS');self.assertEqual(s.executor.total_effects,0)
    def test_helper_loss_has_no_python_fallback_or_budget_reset(self):
        s,w=self.setup_case();a=self.agenda();a.choose(s.read());a.release();work=a.work;state=s.authority_records()
        a.backend.process.process.kill();a.backend.process.process.wait()
        with patch('experimental_attention.controller.full_frontier',side_effect=AssertionError('rescue')):
            with self.assertRaises(RecallError):a.choose(s.read())
        self.assertEqual(a.work,work);self.assertEqual(s.authority_records(),state);self.assertEqual(s.executor.total_effects,0)
    def test_explicit_lru_eviction_revisit_keeps_native_backing(self):
        s,w=self.setup_case('alternatives');a=self.agenda();a.choose(s.read())
        self.assertGreater(a.ws.costs['evictions'],0);self.assertLessEqual(len(a.ws.entries),24)
        self.assertGreater(a.backend.receipt.counts['atoms'],len(a.ws.entries))
        self.assertLessEqual(a.diagnostic['peaks'].get('joint_records',0),32);self.assertLessEqual(a.diagnostic['native_queries'],48)
        a.release()
        before=s.authority_records();record=next(i for i in a.ws.seen if i.startswith('["support"') and i not in a.ws.entries)
        a.used_queries=0;found=a.query('record',record_id=record);a.retain(found)
        self.assertIn(record,a.ws.entries);self.assertGreater(a.ws.costs['rematerializations'],0);self.assertEqual(s.authority_records(),before)
    def test_nonbinding_matched_candidate_selection_parity(self):
        for name in ('control','distractors'):
            s,w=self.setup_case(name);view=s.read();caps,search=settings(24,48,True)
            for mode in ('WS-queue','WS-local','WS-flow'):
                a=Agenda(mode,Limits(work=16),caps,search);ref=Complete(limits=Limits(work=16));self.addCleanup(a.close);self.addCleanup(ref.backend.close)
                f,c=a.choose(view);g,d=ref.choose(view)
                self.assertEqual(c,d);self.assertEqual({x.logical_id:x for x in f.candidates},{x.logical_id:x for x in g.candidates});a.release()
    def test_stale_field_guard_leaves_authority_unchanged(self):
        s,w=self.setup_case();a=self.agenda();view=s.read();before=s.authority_records();calls=0
        def guard():
            nonlocal calls
            calls+=1;return view.binding if calls<4 else 'changed'
        with self.assertRaises(StaleField):a.choose(view,current_binding=guard)
        self.assertEqual(s.authority_records(),before);self.assertEqual(a.work,0)
    def test_wrapper_geometry_and_record_order_metamorphisms(self):
        from experimental_pressure.projection import normalize,Scope
        s,w=self.setup_case();base=s.read();record=dict((c[1],c[2]) for c in base.contracts if c[0]=='registered-content/v1')['execution_contract']
        original=record.requirements
        for depth in range(4):
            wrapped=original
            for _ in range(depth):wrapped=Requirement('AND',children=(wrapped,))
            changed=replace(record,requirements=wrapped)
            contracts=tuple((c[0],c[1],changed) if c[0]=='registered-content/v1' and c[1]=='execution_contract' else c for c in base.contracts)
            view=replace(base,contracts=contracts,rules=tuple(reversed(base.rules)),reports=tuple(reversed(base.reports)))
            a=self.agenda();b=self.agenda();a.choose(base);b.choose(view)
            # Bindings/certificates remain different; only semantic routing geometry
            # and allocation are compared, not arbitrary equivalence or ID ties.
            geometry=lambda x:{(r.source,r.target,r.purpose,r.status) for r in x.ws.arcs.values()}
            self.assertEqual(geometry(a),geometry(b))
            for k in a.ws.field.activation:self.assertAlmostEqual(a.ws.field.activation[k],b.ws.field.activation[k],places=12)
            a.release();b.release()
        scope=Scope('ctx','goal','source','slice','same-event')
        for form in (1,{'AND':[1]}, {'OR':[{'AND':[1,1]}]}):self.assertEqual(normalize(form,scope,())['condition'],1)
    def test_native_PLN_completion_and_monitoring_under_competition(self):
        for name in ('control','monitor-reopen'):
            with TemporaryDirectory() as tmp:
                r=run_case(next(p for p in PARENTS if p['id']==name),Path(tmp)/'case',mode='WS-flow',capacity=24,queries=48,native=True)
                self.assertEqual(r['conformance'],'PASS',r.get('traceback'));self.assertEqual(r['effects'],1)
                if name=='control':self.assertEqual(r['outstanding'],0);self.assertTrue(r['runtime_calls']);self.assertTrue(all(c['formula_agreement'] for c in r['runtime_calls']))
                else:
                    self.assertEqual(r['outstanding'],10);self.assertIn('reopened',r['relief_kinds'])
                    rows=[json.loads(t) for t in (Path(tmp)/'case/trace.jsonl').read_text().splitlines()]
                    self.assertTrue(any(row.get('result',{}).get('status')=='FAIL' and row['selected']['target']=='product' for row in rows))
    def test_closed_inspection_source_remains_unknown_after_use_route_opens(self):
        with TemporaryDirectory() as tmp:
            r=run_case(next(p for p in PARENTS if p['id']=='closed-sinks'),Path(tmp)/'case',mode='WS-flow',capacity=48,queries=48,native=True)
            self.assertEqual(r['conformance'],'PASS',r.get('traceback'));self.assertEqual(r['outstanding'],0)
            rows=[json.loads(t) for t in (Path(tmp)/'case/trace.jsonl').read_text().splitlines()]
            requests=[row for row in rows if row['selected'] and row['selected']['target'].startswith('closed-')]
            self.assertTrue(requests)
            self.assertTrue(all(row['result']['status']=='UNKNOWN' and not row['calls'] for row in requests))
