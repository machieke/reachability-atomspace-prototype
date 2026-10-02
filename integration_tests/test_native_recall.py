"""Actual pinned native recall, independent source scans and certified execution."""
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from experimental_goal_pln.agenda import Agenda as Scan
from experimental_online_pln.agenda import Limits,Probe
from experimental_native_recall.agenda import Agenda
from experimental_native_recall.backend import Backend,Process,RecallError,IncompleteRecall
from experimental_native_recall.schema import Projection,QueryLimits
from experimental_native_recall.session import Session
from native_recall_lab.reference import check,answers
from goal_pln_lab.cases import World,configuration
from reachability.model import Literal,Statement,Status
from reachability.pln_adapter import DeductionRule,TruthValue
from reachability.probability_model import ProbabilityRule,ProbabilityPolicy,ProbabilityIndependence
from validation_lab.online_pln_conformance import summary


class NativeRecallTests(unittest.TestCase):
    def setup_case(self,name='route-control',session_class=Session):
        t=TemporaryDirectory();self.addCleanup(t.cleanup)
        w=World(next(f for f in configuration()['fixtures'] if f['id']==name))
        s=session_class(t.name,acquire=w.acquire);self.addCleanup(s.close);w.setup(s)
        b=Backend();self.addCleanup(b.close)
        return s,w,b
    def test_independent_all_queries_current_historical_reports_models(self):
        s,w,b=self.setup_case('path-alternatives');self.assertGreater(check(b,s.read()),30)
        self.assertGreater(b.costs['native_queries'],30)
        for ident in b.receipt.source_ids:
            self.assertTrue(b.query('record',binding=b.receipt.snapshot_binding,record_id=ident).complete)
    def test_readonly_reuse_and_binding_receipts(self):
        s,w,b=self.setup_case('route-shared');before=s.authority_records();seq=s.service._journal_sequence
        r=b.open_view(s.read());pid=b.process.process.pid;queries_before=b.costs['native_queries']
        first=b.query('producers',binding=r.snapshot_binding,context='ctx',literal=s.forecast)
        self.assertEqual(b.open_view(s.read()),r);self.assertEqual(b.process.process.pid,pid)
        second=b.query('producers',binding=r.snapshot_binding,context='ctx',literal=s.forecast)
        self.assertEqual(first.ids,second.ids);self.assertEqual(b.costs['native_queries']-queries_before,2)
        self.assertEqual(s.authority_records(),before);self.assertEqual(seq,s.service._journal_sequence)
        self.assertFalse(s.runtime.calls);self.assertEqual(s.executor.total_effects,0)
    def test_live_native_deduction_and_acquisition_without_python_discovery(self):
        for name,kind in (('route-control','deduction'),('route-distractors','request')):
            with self.subTest(case=name):
                s,w,b=self.setup_case(name);a=Agenda(backend=b);view=s.read();expected=Scan('Goal-scan').choose(view)[1]
                with (patch('experimental_native_recall.agenda.enumerate_work',side_effect=AssertionError('Python discovery used')),
                      patch('experimental_native_recall.agenda.scan_closure',side_effect=AssertionError('scan traversal used'))):
                    frontier,candidate=a.choose(view)
                self.assertEqual(candidate,expected);self.assertEqual(candidate.kind,kind)
                self.assertIsNone(a.diagnostic['fallback']);self.assertGreater(b.costs['native_queries'],0)
                self.assertEqual(s.execute(candidate)['status'],'PASS')
                self.assertGreater(s.costs['execution_enumeration_ns'],0)
                self.assertEqual(len(s.runtime.calls),int(kind=='deduction'))
    @staticmethod
    def rewrite_link(projection,ref,outgoing):
        projection.batch.atoms[ref]=('L',tuple(outgoing))
        ordinal=-1
        for i,command in enumerate(projection.batch.commands):
            if command.split()[0] in ('N','P','L'):
                ordinal+=1
                if ordinal==ref:
                    projection.batch.commands[i]='L '+str(len(outgoing))+' '+' '.join(map(str,outgoing))
                    return
        raise AssertionError('missing test relation')

    def test_missing_native_producer_is_detected_not_repaired(self):
        s,w,b=self.setup_case('route-shared');snapshot=s.read();outer=self
        class WrongConclusion(Projection):
            def __init__(self,view):
                super().__init__(view)
                ref=self.relations[0];out=list(self.batch.atoms[ref][1])
                out[2]=self.literal_refs[view.rules[0].deduction.premises[0]]
                outer.rewrite_link(self,ref,out)
        with patch('experimental_native_recall.backend.Projection',WrongConclusion):
            b.open_view(snapshot)
        # Real native graph has no producer edge for the original conclusion.
        actual=b.query('producers',binding=snapshot.binding,context='ctx',literal=s.forecast)
        self.assertEqual(actual.ids,())
        self.assertNotEqual(actual.ids,answers(snapshot,'producers',context='ctx',literal=s.forecast))
        with self.assertRaisesRegex(AssertionError,'native/reference'):
            check(b,snapshot)
        self.assertGreater(b.costs['native_queries'],0)

    def test_wrong_native_ordered_relation_is_rejected(self):
        s,w,b=self.setup_case();snapshot=s.read();outer=self
        class WrongPremises(Projection):
            def __init__(self,view):
                super().__init__(view)
                producer=self.batch.atoms[self.relations[0]][1];ref=producer[4]
                out=list(self.batch.atoms[ref][1]);out[-1],out[-2]=out[-2],out[-1]
                outer.rewrite_link(self,ref,out)
        with patch('experimental_native_recall.backend.Projection',WrongPremises):
            b.open_view(snapshot)
        with self.assertRaisesRegex(RecallError,'ordered premises'):
            b.query('producers',binding=snapshot.binding,context='ctx',literal=s.forecast)
        self.assertIsNone(b.receipt)
    def test_equal_replacement_and_new_outside_producer_revision(self):
        s,w,b=self.setup_case('change-replacement');a=Agenda(backend=b);_,old=a.choose(s.read());binding=b.receipt.snapshot_binding
        self.assertEqual(s.execute(old)['status'],'STALE');check(b,s.read())
        with self.assertRaisesRegex(RecallError,'stale'):b.query('models',binding=binding,context='ctx')
        _,adopt=a.choose(s.read());s.execute(adopt);_,fresh=a.choose(s.read())
        self.assertNotEqual(old.premise_ids,fresh.premise_ids);self.assertNotEqual(old.basis,fresh.basis)
        s.register_rule(ProbabilityRule('new-producer','1',DeductionRule('tested','other','healthy')))
        check(b,s.read());self.assertEqual(len(b.recall('producers',binding=s.read().binding,context='ctx',literal=s.forecast)),2)
        s.register_rule(ProbabilityRule('new-producer','2',DeductionRule('tested','other','elsewhere')),'1')
        check(b,s.read());self.assertEqual(len(b.recall('producers',binding=s.read().binding,context='ctx',literal=s.forecast)),1)
    def test_opposite_and_unfavorable_support_still_block_real_gate(self):
        s,w,b=self.setup_case();a=Agenda(backend=b);_,c=a.choose(s.read());s.execute(c)
        self.assertEqual(s.read().decision.status,Status.PASS)
        w.report('contrary',s.forecast.negate(),TruthValue(.1,.1));check(b,s.read())
        self.assertTrue(b.recall('current',binding=s.read().binding,context='ctx',literal=s.forecast.negate()))
        self.assertEqual(s.read().decision.status,Status.UNKNOWN);self.assertNotEqual(s.reserve()['status'],'PASS')
        w.report('low-unfavorable',s.forecast,TruthValue(.1,.1),adopt=False);check(b,s.read())
        self.assertTrue(b.recall('reports',binding=s.read().binding,context='ctx',literal=s.forecast))
        self.assertEqual(s.executor.total_effects,0)
    def test_context_polarity_unicode_order_duplicate_args_and_exact_integer(self):
        s,w,b=self.setup_case()
        literals=[Literal(Statement('π',args),pol) for args,pol in ((('λ','λ'),True),(('λ','μ'),True),(('μ','λ'),True),(('λ','λ'),False))]
        for i,lit in enumerate(literals):w.report('証拠:'+str(i),lit,TruthValue(.2+i*.1,.8))
        s.service.advance_clock('ctx',2**80+7,idempotency_key=s.key());s.service.advance_resource_clock(2**80+7,idempotency_key=s.key());view=s.read();check(b,view)
        for literal in literals:
            self.assertEqual(len(b.recall('current',binding=view.binding,context='ctx',literal=literal)),1)
            self.assertEqual(b.recall('current',binding=view.binding,context='other',literal=literal),())
        self.assertIn(str(2**80+7),b.graph.values.values())
        class OtherSession(Session):
            def _initialize(self):
                self.initial=replace(self.initial,context_id='other');super()._initialize()
        other,ow,ob=self.setup_case(session_class=OtherSession);check(ob,other.read())
        self.assertTrue(ob.recall('producers',binding=other.read().binding,context='other',literal=other.forecast))
        self.assertEqual(ob.recall('producers',binding=other.read().binding,context='ctx',literal=other.forecast),())
    def test_model_policy_time_and_opportunity_require_new_views(self):
        s,w,b=self.setup_case('route-shared');check(b,s.read());bindings=[b.receipt.snapshot_binding]
        for change in (lambda:s.publish_probe(replace(s.probes['source-report'],opportunity=1)),
                       lambda:s.emit('tick',time=1),
                       lambda:s.service.configure_probability_policy('ctx',ProbabilityPolicy('2',('forecast-model',)),'1',idempotency_key=s.key())):
            change();check(b,s.read());bindings.append(b.receipt.snapshot_binding)
        left=w.report('left',s.forecast,TruthValue(.7,.25));right=w.report('right',s.forecast,TruthValue(.7,.25))
        model=ProbabilityIndependence('sources','ctx',(left.belief_revision_id,right.belief_revision_id),'independent source processes')
        s.register_model(model);check(b,s.read());bindings.append(b.receipt.snapshot_binding)
        self.assertEqual(b.recall('models',binding=s.read().binding,context='ctx'),(model,))
        s.revoke_model(model.model_id);check(b,s.read());bindings.append(b.receipt.snapshot_binding)
        self.assertEqual(len(set(bindings)),len(bindings))
        _,c=Agenda(backend=b).choose(s.read());self.assertNotEqual(c.kind,'revision')
    def test_missing_and_alternative_tuples_cycles_and_matched_closure(self):
        for name in ('path-three','path-alternatives','route-shared'):
            s,w,b=self.setup_case(name);s.register_rule(ProbabilityRule('cycle','1',DeductionRule('tested','healthy','staged')))
            view=s.read();a=Agenda(backend=b);ref=Scan('Goal-scan');f,c=a.choose(view);g,e=ref.choose(view)
            self.assertEqual(c,e);self.assertEqual(a.diagnostic['relevant'],ref.diagnostic['relevant'])
            self.assertEqual(a.diagnostic['witnesses'],ref.diagnostic['witnesses'])
            ad=dict(a.diagnostic['closure']);bd=dict(ref.diagnostic['closure']);ad.pop('elapsed_ns');bd.pop('elapsed_ns')
            self.assertEqual(ad,bd);self.assertTrue(ad['complete']);self.assertEqual(summary(s)['outstanding'],10)
    def test_result_visit_query_limits_and_explicit_python_fallback(self):
        s,w,b=self.setup_case('route-shared');view=s.read();b.open_view(view)
        for limits,reason in ((QueryLimits(visits=0),'VISIT_BOUND'),(QueryLimits(results=0),'RESULT_BOUND'),(QueryLimits(queries=0),'QUERY_BOUND')):
            r=b.query('producers',binding=view.binding,context='ctx',literal=s.forecast,limits=limits)
            self.assertFalse(r.complete);self.assertEqual(r.ids,());self.assertEqual(r.reason,reason)
        bounded=Backend(limits=QueryLimits(visits=0));self.addCleanup(bounded.close)
        a=Agenda(backend=bounded);f,c=a.choose(view)
        self.assertTrue(f.complete);self.assertIn('INCOMPLETE_CLOSURE',a.diagnostic['fallback'])
        self.assertFalse(a.diagnostic['discovery_complete']);self.assertGreater(a.costs['fallback_enumeration_ns'],0)
    def test_partial_invalid_duplicate_load_unknown_query_and_stale_native_request(self):
        s,w,b=self.setup_case();p=Projection(s.read());encoded=p.wire()[0]
        import subprocess
        binary=Path('artifacts/bin/atomspace_recall')
        for data in (b'N 61\n',b'L 1 9\n',encoded.replace(b'T ',p.registrations[0].encode()+b'\nT ',1),
                     encoded+b'Q 1 626164 models 4096 512 637478\n',
                     encoded+b'Q 1 '+p.binding.encode().hex().encode()+b' EVAL 4096 512 637478\n',
                     b'X'*262145+b'\n'):
            result=subprocess.run([str(binary)],input=data,capture_output=True,timeout=30)
            self.assertNotEqual(result.returncode,0);self.assertTrue(result.stderr)
        # Invalid relation shape is rejected before a READY receipt.
        q=Projection(s.read());q.relations.append(q.batch.link((q.tags['producer'],q.ctx('ctx'))))
        result=subprocess.run([str(binary)],input=q.wire()[0],capture_output=True,timeout=30)
        self.assertNotEqual(result.returncode,0);self.assertNotIn(b'READY ',result.stdout)
    def test_malformed_response_timeout_and_no_python_substitution(self):
        s,w,b=self.setup_case();a=Agenda(backend=b)
        with (patch.object(b,'open_view',side_effect=RecallError('native protocol error')),
              patch('experimental_native_recall.agenda.enumerate_work',side_effect=AssertionError('silent substitute'))):
            with self.assertRaises(RecallError):a.choose(s.read())
        b.open_view(s.read())
        with patch.object(b.process,'receive',return_value=['QRESULT invalid','END 1']):
            with self.assertRaises(RecallError):b.query('models',binding=s.read().binding,context='ctx')
        self.assertIsNone(b.receipt)
        process=Process('/bin/cat',timeout=.01);self.addCleanup(process.close)
        with self.assertRaisesRegex(RecallError,'timeout'):process.receive('never-produced')
    def test_helper_loss_rebuild_does_not_reset_work_or_run_inference(self):
        s,w,b=self.setup_case();a=Agenda(backend=b);view=s.read();_,c=a.choose(view)
        counts=(a.work,a.selections,set(a.attempted));authority=s.authority_records();calls=len(s.runtime.calls)
        b.process.process.kill();b.process.process.wait()
        with self.assertRaisesRegex(RecallError,'lost'):b.open_view(view)
        self.assertIsNone(b.receipt);b.open_view(view)
        self.assertEqual((a.work,a.selections,set(a.attempted)),counts)
        self.assertEqual(s.authority_records(),authority);self.assertEqual(len(s.runtime.calls),calls)
        self.assertEqual(s.executor.total_effects,0);self.assertEqual(a.choose(view)[1],None)
    def test_product_and_health_observations_still_required(self):
        s,w,b=self.setup_case('supported-monitor');a=Agenda(backend=b);_,c=a.choose(s.read())
        self.assertEqual((c.kind,c.target),('request','health'));self.assertEqual(summary(s)['outstanding'],10)
        s.emit('revoke',evidence_id='forecast-received');_,c=Agenda(backend=b).choose(s.read())
        self.assertEqual((c.kind,c.target),('request','health'));self.assertEqual(s.execute(c)['status'],'PASS')
        self.assertEqual(summary(s)['outstanding'],10)

    def test_native_discovered_work_completes_with_native_pln_and_replays(self):
        import json
        from native_recall_lab.episode import run_case
        from native_recall_lab.compare import parity,semantic_discovery
        from experimental_online_pln.agenda import Snapshot,wire
        fixture=configuration()['fixtures'][0]
        with TemporaryDirectory() as directory:
            path=Path(directory)/'case'
            result=run_case(fixture,path,arm='Goal-native',budget=8,native=True)
            self.assertEqual(result['conformance'],'PASS',result.get('traceback'))
            self.assertEqual(result['outstanding'],0);self.assertEqual(result['effects'],1)
            self.assertTrue(result['reconstruction']['projection_equal'])
            self.assertTrue(result['runtime_calls']);self.assertTrue(all(c['formula_agreement'] is True for c in result['runtime_calls']))
            backend=Backend();self.addCleanup(backend.close);history=Scan('Goal-scan',Limits(work=8))
            for line in (path/'trace.jsonl').read_text().splitlines():
                row=json.loads(line);snapshot=Snapshot.from_records(row['public_records'])
                native,history,nf,sf,n,s=parity(snapshot,history,backend)
                self.assertEqual(wire(n),row['selected'])
                self.assertEqual(semantic_discovery(native.diagnostic),semantic_discovery(row['discovery']))
