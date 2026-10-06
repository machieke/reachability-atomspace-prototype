"""Independent semantics, exact basis, completeness and authority separation."""
import ast,copy,json,math,unittest
from dataclasses import replace
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from experimental_obligations.capture import capture,immutable,state_digest
from experimental_obligations.evaluate import evaluate,Bounds
from obligations_lab.cases import setup,report,infer,construct,manifests,goal_outcome,prepare_inference
from obligations_lab.reference import frozen,qualified,obligation_table
from reachability.model import Status
from reachability.service import AdmissionDenied


class ObligationTests(unittest.TestCase):
    def session(self):
        tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup);s=setup(tmp.name);self.addCleanup(s.close);return s
    def eval(self,s,name='alternatives',kind='B',**kw):
        cap,_=capture(s.service);return evaluate(cap,manifests()[name],kind,**kw)[0].data()
    def test_exhaustive_small_obligation_boolean_tables(self):
        # Independent hand-declared requirements, also embedded in real captures below.
        for n in range(5):
            for booleans in product((False,True),repeat=n):
                for retired in (False,True):
                    any_expected='PASS' if sum(booleans)>0 else 'STALE' if not n and retired else 'UNKNOWN'
                    all_expected='PASS' if n>0 and sum(booleans)==n else 'STALE' if not n and retired else 'UNKNOWN'
                    self.assertEqual(obligation_table('any',booleans,retired),any_expected);self.assertEqual(obligation_table('all',booleans,retired),all_expected)
    def test_subject_against_exhaustive_boolean_reference_on_real_certified_inputs(self):
        for n in range(4):
            for bits in product((False,True),repeat=n):
                with self.subTest(bits=bits):
                    s=self.session()
                    for i,bit in enumerate(bits):report(s,'bool-'+str(i),confidence=.35 if bit else .349)
                    cap,_=capture(s.service)
                    for mode,name in (('any','alternatives'),('all','all_assessments')):
                        result=evaluate(cap,manifests()[name])[0].data()
                        self.assertEqual(result['numerical_status'],obligation_table(mode,bits,False))
                        self.assertEqual(result['obligations'][0]['status'],obligation_table(mode,bits,False))
                    self.assertEqual(evaluate(cap,manifests()['alternatives'],'A')[0].data()['numerical_status'],cap.data()['live_criterion_statuses'][0])
                    for i in range(n):s.emit('revoke',evidence_id='bool-'+str(i))
                    cap,_=capture(s.service)
                    for name in ('alternatives','all_assessments'):
                        self.assertEqual(evaluate(cap,manifests()[name])[0].data()['numerical_status'],'STALE' if n else 'UNKNOWN')
    def test_precedence_and_interval_boundaries_match_live_inspector(self):
        from experimental_obligations.evaluate import combine
        from obligations_lab.reference import precedence
        for flags in product(('PASS','FAIL','STALE','UNKNOWN'),repeat=3):self.assertEqual(combine(flags),precedence(flags))
        for strength in (.649,.65,1.):
            s=self.session();report(s,strength=strength,confidence=.35);cap,_=capture(s.service)
            self.assertEqual(evaluate(cap,manifests()['alternatives'],'A')[0].data()['numerical_status'],cap.data()['live_criterion_statuses'][0])
        s=self.session();report(s);cap,_=capture(s.service);d=cap.data();d['registry']['certificates']=[]
        self.assertEqual(evaluate(immutable(d),manifests()['alternatives'])[0].status,'FAIL')
        d=cap.data();d.pop('registry');self.assertEqual(evaluate(immutable(d),manifests()['alternatives'])[0].status,'UNKNOWN')
    def test_live_A_and_independent_B_reference_for_declared_complete_parents(self):
        for parent in ('adequate-direct','weak-augmented','only-weak','missing-mandatory','objections','lineage-copies','revision-family','freshness','adverse-inference'):
            with self.subTest(parent=parent),TemporaryDirectory() as tmp:
                rows,_=construct(parent,tmp)
                for row in rows:
                    d=row['capture'].data();self.assertEqual(frozen(d),d['live_criterion_statuses'][0])
                    for name in row['manifests']:
                        m=manifests()[name];a=evaluate(row['capture'],m,'A')[0].data();b=evaluate(row['capture'],m,'B')[0].data();status,groups=qualified(d,m)
                        self.assertEqual(a['numerical_status'],frozen(d));self.assertEqual(b['numerical_status'],status)
                        self.assertEqual({o['id']:(o['status'],o['witnesses']) for o in b['obligations']},groups)
    def test_actual_weak_inference_role_pair_and_all_current_gate(self):
        s=self.session();report(s);before=self.eval(s);infer(s);a=self.eval(s,kind='A');alternative=self.eval(s);mandatory=self.eval(s,'mandatory_method')
        self.assertEqual((a['status'],alternative['status'],mandatory['status']),('UNKNOWN','PASS','UNKNOWN'))
        self.assertEqual([r['belief'] for r in alternative['records']],[r['belief'] for r in mandatory['records']]);self.assertNotEqual(before['basis_hash'],alternative['basis_hash'])
        self.assertEqual(s.reserve()['status'],'UNKNOWN');self.assertEqual(s.executor.total_effects,0)
    def test_no_shadow_mutation_or_typed_permission(self):
        s=self.session();report(s);infer(s);before=state_digest(s.service);cap,_=capture(s.service)
        for kind in ('A','B'):
            shadow,_=evaluate(cap,manifests()['alternatives'],kind)
            with self.assertRaises(ValueError):s.service.reserve_and_record_intent(shadow,idempotency_key='shadow-'+kind)
            with self.assertRaises(ValueError):s.service.register_decision_contract(shadow,idempotency_key='shadow-contract-'+kind)
        self.assertEqual(state_digest(s.service),before);self.assertEqual(s.executor.total_effects,0);self.assertEqual(s.service.inspect_goal('goal').projection.outstanding_loss,10)
    def test_mandatory_sources_missing_copied_lineage_and_valid_alternative(self):
        s=self.session();report(s);self.assertEqual(self.eval(s,'two_sources')['status'],'UNKNOWN');report(s,'copy',source='source-b')
        r=self.eval(s,'two_sources');self.assertEqual(r['status'],'UNKNOWN');self.assertIn('source-b',r['missing_obligations'])
        s.emit('revoke',evidence_id='copy');report(s,'b',source='source-b',root='root:b');self.assertEqual(self.eval(s,'two_sources')['status'],'PASS')
    def test_global_objections_include_low_confidence_and_opposites(self):
        s=self.session();report(s);report(s,'contrary',.2,.0001,'source-b','root:b');self.assertEqual(self.eval(s)['status'],'FAIL')
        s.emit('revoke',evidence_id='contrary');report(s,'negative',.7,.0001,'source-b','root:b',s.forecast.negate());self.assertEqual(self.eval(s)['status'],'UNKNOWN')
    def test_new_actual_outside_interval_inference_changes_status_without_observation(self):
        s=self.session();report(s);prepared=prepare_inference(s,True);before=self.eval(s);goal=goal_outcome(s);evidence=tuple(s.service._evidence.values());infer(s,True,prepared);after=self.eval(s)
        self.assertEqual((before['status'],after['status']),('PASS','FAIL'));self.assertEqual(goal_outcome(s),goal);self.assertEqual(tuple(s.service._evidence.values()),evidence);self.assertEqual(s.executor.total_effects,0)
    def test_revoked_sole_and_equal_replacement_do_not_reuse_permission(self):
        s=self.session();report(s);old=self.eval(s);self.assertEqual(s.reserve()['status'],'PASS');s.emit('revoke',evidence_id='a');self.assertEqual(self.eval(s)['numerical_status'],'STALE')
        report(s,'replacement');new=self.eval(s);self.assertEqual(new['numerical_status'],'PASS');self.assertNotEqual(old['basis_hash'],new['basis_hash']);self.assertEqual(s.service.inspect_execution_intent('attempt').readiness,Status.STALE)
    def test_stable_shadow_status_on_new_alternative_still_stales_intent(self):
        s=self.session();report(s);old=self.eval(s);s.reserve();report(s,'another');new=self.eval(s)
        self.assertEqual((old['numerical_status'],new['numerical_status']),('PASS','PASS'));self.assertNotEqual(old['basis_hash'],new['basis_hash']);self.assertEqual(s.service.inspect_execution_intent('attempt').readiness,Status.STALE)
    def test_hard_requirements_never_replaced_by_shadow_numerical_PASS(self):
        s=self.session();report(s);s.emit('revoke',evidence_id=next(e.evidence_id for e in s.service._evidence.values() if e.content==s.fact('credential')));r=self.eval(s);self.assertEqual(r['numerical_status'],'PASS');self.assertNotEqual(r['status'],'PASS');self.assertNotEqual(s.reserve()['status'],'PASS')
    def test_incomplete_input_opposite_omission_scope_and_explicit_bounds(self):
        s=self.session();report(s);cap,_=capture(s.service);m=manifests()['alternatives']
        for bound in (Bounds(records=0),Bounds(classification=0),Bounds(witnesses=0),Bounds(bytes=0),Bounds(obligations=0)):
            r=evaluate(cap,m,bounds=bound)[0].data();self.assertEqual(r['status'],'UNKNOWN');self.assertIn('BOUND',r['reason'])
        for field in ('complete','hard_checks_complete'):
            d=cap.data();d[field]=False;self.assertNotEqual(evaluate(immutable(d),m)[0].status,'PASS')
        other=copy.deepcopy(m);other['context']='other';self.assertEqual(evaluate(cap,other)[0].status,'FAIL')
        other=copy.deepcopy(m);other['time_window']=[1,2];self.assertEqual(evaluate(cap,other)[0].status,'STALE')
        other=copy.deepcopy(m);other['classes'][0]['kind']='unknown';self.assertEqual(evaluate(cap,other)[0].status,'UNKNOWN')
        report(s,'opposite',source='source-b',root='root:b',literal=s.forecast.negate());cap,_=capture(s.service);d=cap.data();d['pairs'][0][1]['current']=[];self.assertEqual(evaluate(immutable(d),m)[0].status,'UNKNOWN')
    def test_permutation_at_identical_immutable_basis_and_no_confidence_gain(self):
        s=self.session();report(s);report(s,'duplicate');cap,_=capture(s.service);m=manifests()['alternatives'];before=cap.payload_json
        one=evaluate(cap,m)[0].data();two=evaluate(cap,m)[0].data();self.assertEqual(one,two);self.assertEqual(before,cap.payload_json)
        m['classes'].reverse();m['obligations'][0]['classes'].reverse();three=evaluate(cap,m)[0].data();self.assertEqual(one['status'],three['status']);self.assertEqual(one['obligations'][0]['witnesses'],three['obligations'][0]['witnesses']);self.assertNotEqual(one['manifest_hash'],three['manifest_hash'])
        self.assertEqual([r['belief']['proposal']['support']['truth']['confidence'] for r in one['records']],[.8,.8])
    def test_no_production_import_or_evaluator_service_escape(self):
        for directory in ('reachability','experimental_online_pln','experimental_native_recall','experimental_attention','experimental_assembly'):
            for p in Path(directory).glob('*.py'):self.assertNotIn('experimental_obligations',p.read_text())
        tree=ast.parse(Path('experimental_obligations/evaluate.py').read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):self.assertFalse((node.module or '').startswith(('obligations_lab','reachability.service')))
