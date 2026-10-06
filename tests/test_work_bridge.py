"""Independent semantic graph checks and read-only authority boundary."""
import ast,copy,json,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from experimental_work_bridge.capture import acquire,detached,digest,WorkInput
from experimental_work_bridge.project import project,Limits
from experimental_obligations.capture import state_digest,immutable
from experimental_obligations.evaluate import evaluate,ShadowAssessment,Bounds
from obligations_lab.cases import setup,report,goal_outcome
from work_bridge_lab.cases import construct,manifests,assess,probe,model,revision,PARENTS,diagnostics
from work_bridge_lab.reference import validate
from reachability.model import Status


class WorkBridgeTests(unittest.TestCase):
    def session(self):
        tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup);s=setup(tmp.name);self.addCleanup(s.close);return s
    def view(self,s,variant='primary',limits=Limits()):
        frame,_=acquire(s);m=manifests()[variant];ab,_=assess(frame,m);v,_=project(frame,m,ab['A'],ab['B'],limits);return v.data()
    def rows(self,parent):
        tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup);return construct(parent,tmp.name)[0]
    def for_row(self,row,variant=None):
        m=row.get('manifest',manifests()[variant or row['variants'][0]]);ab,_=assess(row['frame'],m);v,_=project(row['frame'],m,ab['A'],ab['B'],row.get('limits',Limits()));return v
    def test_all_predeclared_prefixes_independent_structure_and_frozen_outputs(self):
        for parent in PARENTS:
            for row in self.rows(parent):
                for variant in row['variants']:
                    with self.subTest(parent=parent,label=row['label'],variant=variant):
                        m=manifests()[variant];ab,_=assess(row['frame'],m);v,_=project(row['frame'],m,ab['A'],ab['B']);self.assertTrue(v.data()['complete'],v.data()['reason']);validate(row['frame'],m,ab['A'],ab['B'],v)
    def test_positive_method_presence_and_shared_execution_reference(self):
        rows=self.rows('method-gap');views=[self.for_row(r).data() for r in rows]
        groups=lambda v:{o['obligation_id']:o for o in v['obligations']}
        self.assertEqual([groups(v)['method-assessment']['status'] for v in views],['UNKNOWN','UNKNOWN','PASS'])
        self.assertIn('NO_REGISTERED_ROUTE',groups(views[0])['method-assessment']['reasons'])
        route=groups(views[1])['method-assessment']['routes'];self.assertEqual(len(route),1)
        deps=[e for e in views[1]['edges'] if e['source']==route[0] and e['type']=='AND_PREREQUISITE'];self.assertEqual(len(deps),2)
        shared=self.for_row(rows[1],'shared_method').data();g=groups(shared);self.assertEqual(g['method-assessment']['routes'],g['method-review']['routes'])
        self.assertEqual(views[-1]['A']['numerical_status'],'UNKNOWN');self.assertEqual(views[-1]['B']['numerical_status'],'PASS');self.assertEqual(views[-1]['observed']['goal']['projection']['outstanding_loss'],10)
    def test_optional_all_and_separate_mandatory_work_meanings(self):
        before,after=self.rows('optional-weak')
        a=self.for_row(after,'primary').data();b=self.for_row(after,'forecast_all').data();c=self.for_row(after,'mandatory_weak').data()
        self.assertEqual((a['B']['numerical_status'],b['B']['numerical_status'],c['B']['numerical_status']),('PASS','UNKNOWN','UNKNOWN'))
        self.assertEqual(a['A']['records'],b['A']['records']);self.assertEqual(a['A']['records'],c['A']['records'])
        fore=next(o for o in b['obligations'] if o['obligation_id']=='forecast');self.assertIn('INADEQUATE_SUPPORT',fore['reasons'])
        self.assertTrue(any(x['category']=='LIVE_POLICY_BLOCK' for x in a['global_blockers']))
        ops=[n for n in a['nodes'] if n['kind']=='operation' and n['producer']['kind']=='deduction'];self.assertTrue(all(n['materialized_result_ids'] and not n['reexecution_as_repair'] for n in ops))
        self.assertEqual({o['id'] for o in self.for_row(before).data()['obligations']},{o['id'] for o in a['obligations']})
    def test_copied_source_stays_unclassified_after_lawful_witness(self):
        rows=self.rows('copied-source');views=[self.for_row(r).data() for r in rows]
        self.assertEqual([v['B']['numerical_status'] for v in views],['UNKNOWN','UNKNOWN','PASS'])
        self.assertEqual(next(o for o in views[1]['obligations'] if o['obligation_id']=='source-b')['status'],'PASS')
        self.assertTrue(any(x['category']=='APPLICABILITY_REQUIRES_REVIEW' for x in views[1]['global_blockers']))
        routes=[n for n in views[0]['nodes'] if n['kind']=='operation' and n['producer']['kind']=='observation'];self.assertEqual(len(routes),1);self.assertEqual(routes[0]['adequacy'],'UNKNOWN_UNTIL_NEW_CERTIFIED_RESULT')
    def test_revocation_replacement_survivor_and_old_intent_staleness(self):
        views=[self.for_row(r).data() for r in self.rows('freshness')]
        self.assertEqual([v['B']['numerical_status'] for v in views],['PASS','STALE','PASS','PASS'])
        self.assertEqual(len({tuple(o['id'] for o in v['obligations']) for v in views}),1)
        self.assertEqual(len({v['view_identity'] for v in views}),4)
        s=self.session();report(s);report(s,'b',source='source-b',root='root:b');s.reserve();v=self.view(s,'distinct_source');report(s,'replacement');w=self.view(s,'distinct_source')
        self.assertEqual((v['B']['numerical_status'],w['B']['numerical_status']),('PASS','PASS'));self.assertNotEqual(v['view_identity'],w['view_identity']);self.assertEqual(s.service.inspect_execution_intent('attempt').readiness,Status.STALE)
    def test_concurrent_objections_preserved_with_positive_witnesses(self):
        rows=self.rows('objection');views=[self.for_row(r).data() for r in rows]
        self.assertEqual([v['B']['numerical_status'] for v in views],['PASS','FAIL','FAIL'])
        self.assertEqual([len([b for b in v['global_blockers'] if b['category']=='OBJECTION_REQUIRES_REVIEW']) for v in views],[0,1,2])
        self.assertTrue(all(o['status']=='PASS' for o in views[-1]['obligations']))
    def test_new_revision_missing_AND_and_unavailable_route(self):
        rows=self.rows('registry');v=[self.for_row(r).data() for r in rows]
        for idx,missing in ((1,5),(2,1),(3,0)):
            op=next(n for n in v[idx]['nodes'] if n['kind']=='operation' and n['producer']['kind']=='deduction');self.assertEqual(len(op['missing_slots']),missing)
            self.assertEqual(len([e for e in v[idx]['edges'] if e['source']==op['id'] and e['type']=='AND_PREREQUISITE']),5)
        self.assertNotEqual(v[3]['bindings']['inventory_digest'],v[4]['bindings']['inventory_digest'])
        self.assertEqual(next(o for o in v[4]['obligations'] if o['obligation_id']=='weak-method')['routes'],[])
        self.assertTrue(any(n['producer']['record'].get('availability')=='unavailable' for n in v[5]['nodes'] if n['kind']=='operation'))
    def test_repeated_reads_role_preserving_permutation_and_nonduplication(self):
        s=self.session();a=report(s);b=report(s,'b',source='source-b',root='root:b');model(s,a,b)
        frame,_=acquire(s);again,_=acquire(s);self.assertEqual(frame,again);m=manifests()['shared_method'];ab,_=assess(frame,m)
        v=project(frame,m,ab['A'],ab['B'])[0];self.assertEqual(v,project(frame,m,ab['A'],ab['B'])[0])
        m['classes'].reverse();m['obligations'].reverse()
        for g in m['obligations']:g['classes'].reverse()
        ab,_=assess(frame,m);w=project(frame,m,ab['A'],ab['B'])[0].data();v=v.data()
        self.assertEqual(v['nodes'],w['nodes']);self.assertEqual(v['edges'],w['edges']);self.assertNotEqual(v['bindings']['manifest_hash'],w['bindings']['manifest_hash'])
        report(s,'duplicate');n=self.view(s,'shared_method');self.assertEqual([o['id'] for o in n['obligations']],[o['id'] for o in v['obligations']])
    def test_bounds_partial_scope_and_stale_bindings_are_explicitly_incomplete(self):
        row=self.rows('registry')[3]
        for r in diagnostics(row):self.assertFalse(self.for_row(r).data()['complete'])
        m=manifests()['mandatory_weak'];ab,_=assess(row['frame'],m)
        for bounds in (Limits(bytes=0),Limits(inventory=0),Limits(estimates=0),Limits(tuples=0),Limits(operations=0),Limits(nodes=0),Limits(edges=0),Limits(comparisons=0)):
            v=project(row['frame'],m,ab['A'],ab['B'],bounds)[0].data();self.assertFalse(v['complete']);self.assertTrue(v['partial_nodes_are_diagnostic']);self.assertIn('BOUND',v['reason'])
        f=row['frame'].data();f['inventory']['rules']=[];v=project(detached(f),m,ab['A'],ab['B'])[0].data();self.assertFalse(v['complete'])
        bad=ab['B'].data();bad['status']='PASS';v=project(row['frame'],m,ab['A'],ShadowAssessment(json.dumps(bad)))[0].data();self.assertFalse(v['complete'])
        incomplete,_=evaluate(immutable(row['frame'].data()['capture']),m,'B',Bounds(records=0));self.assertFalse(project(row['frame'],m,ab['A'],incomplete)[0].data()['complete'])
    def test_no_mutation_no_native_formula_and_typed_authority_rejection(self):
        s=self.session();a=report(s);b=report(s,'b',source='source-b',root='root:b');model(s,a,b);before=state_digest(s.service);calls=len(s.runtime.calls);frame,_=acquire(s);m=manifests()['primary'];ab,_=assess(frame,m);value,_=project(frame,m,ab['A'],ab['B'])
        with self.assertRaises(ValueError):s.service.reserve_and_record_intent(value,idempotency_key='work-view')
        with self.assertRaises(ValueError):s.service.register_decision_contract(value,idempotency_key='work-view-contract')
        self.assertEqual(before,state_digest(s.service));self.assertEqual(len(s.runtime.calls),calls);self.assertEqual(s.executor.total_effects,0)
        for folder in ('reachability','experimental_obligations','experimental_online_pln','experimental_native_recall','experimental_attention','experimental_assembly'):
            for p in Path(folder).glob('*.py'):self.assertNotIn('experimental_work_bridge',p.read_text())
        tree=ast.parse(Path('experimental_work_bridge/project.py').read_text())
        for n in ast.walk(tree):
            if isinstance(n,ast.ImportFrom):self.assertFalse((n.module or '').startswith(('work_bridge_lab','reachability.service')))
    def test_alternative_bundles_shared_missing_premises_and_direct_observation(self):
        from reachability.probability_model import ProbabilityRule
        from reachability.pln_adapter import DeductionRule
        from experimental_online_pln.agenda import Probe
        s=self.session();report(s);rule=ProbabilityRule('r-estimate','1',DeductionRule('tested','weak','healthy'));s.register_rule(rule);s.register_rule(ProbabilityRule('r-objection','1',rule.deduction))
        s.publish_probe(Probe('premise-observation','forecast-model','numeric',rule.deduction.premises[2],availability='available'))
        v=self.view(s);self.assertTrue(v['complete']);missing=[n for n in v['nodes'] if n['kind']=='missing-premise'];self.assertEqual(len(missing),5)
        self.assertEqual(len([e for e in v['edges'] if e['type']=='AND_PREREQUISITE']),10);self.assertEqual(len([e for e in v['edges'] if e['type']=='OR_OBSERVATION_OPPORTUNITY']),1)
        ids={o['id'] for o in v['obligations']}
        for i,lit in enumerate(rule.deduction.premises):report(s,'slot-'+str(i),.5,.8,'forecast-model','root:'+str(i),lit)
        report(s,'duplicate-slot',.5,.8,'forecast-model','root:0',rule.deduction.premises[0]);frame,_=acquire(s);m=manifests()['primary'];ab,_=assess(frame,m);w,_=project(frame,m,ab['A'],ab['B']);validate(frame,m,ab['A'],ab['B'],w);w=w.data()
        self.assertEqual(len([n for n in w['nodes'] if n['kind']=='operation' and n['producer']['kind']=='deduction']),4);self.assertEqual({o['id'] for o in w['obligations']},ids);self.assertEqual(s.runtime.calls,[])
    def test_probe_preconditions_unknown_availability_and_unsupported_channels(self):
        from experimental_online_pln.agenda import Probe
        s=self.session();report(s);s.publish_probe(Probe('unknown','source-b','numeric',s.forecast,availability='unknown'));v=self.view(s,'distinct_source')
        self.assertEqual(next(n for n in v['nodes'] if n['kind']=='operation')['readiness'],'OBSERVATION_AVAILABILITY_UNKNOWN')
        s.publish_probe(Probe('guarded','source-b','numeric',s.forecast,preconditions=('acknowledged','exact_product'),availability='available'))
        s.publish_probe(Probe('product-observation','sensor','product','artifact-v2',availability='available'));v=self.view(s,'distinct_source')
        self.assertEqual(len([e for e in v['edges'] if e['type']=='AND_OBSERVATION_PRECONDITION']),2)
        self.assertTrue(any(n.get('readiness')=='OBSERVATION_PRECONDITION_UNRESOLVED' for n in v['nodes']));self.assertEqual(len(v['unsupported_observation_channels']),1)
    def test_full_contract_scope_malformed_inputs_and_producer_digest_binding(self):
        s=self.session();report(s);frame,_=acquire(s);m=manifests()['primary'];ab,_=assess(frame,m)
        for raw in ([],{},dict(schema='obligation-work-input/v0',complete=True),dict(frame.data(),inventory=[])):
            v=project(detached(raw),m,ab['A'],ab['B'])[0].data();self.assertFalse(v['complete'])
        bad=frame.data();bad['inventory']['probes']=None;bad['inventory_digest']=digest(bad['inventory']);self.assertFalse(project(detached(bad),m,ab['A'],ab['B'])[0].data()['complete'])
        self.assertFalse(project(WorkInput('{"observed":NaN}'),m,ab['A'],ab['B'])[0].data()['complete'])
        self.assertFalse(project(frame,m,ShadowAssessment('{"status":NaN}'),ab['B'])[0].data()['complete'])
        changed=copy.deepcopy(m);changed['criterion']['min_confidence']=.1;other,_=assess(frame,changed)
        self.assertFalse(project(frame,changed,other['A'],other['B'])[0].data()['complete'])
        f=frame.data();f['inventory']['models']=[{}];f['inventory_digest']=digest(f['inventory']);self.assertFalse(project(detached(f),m,ab['A'],ab['B'])[0].data()['complete'])
    def test_unexpanded_deeper_route_is_incomplete_not_no_work(self):
        from reachability.probability_model import ProbabilityRule
        from reachability.pln_adapter import DeductionRule
        s=self.session();report(s);s.register_rule(ProbabilityRule('r-estimate','1',DeductionRule('tested','weak','healthy')))
        s.register_rule(ProbabilityRule('deeper','1',DeductionRule('tested','middle','weak')))
        v=self.view(s);self.assertFalse(v['complete']);self.assertEqual(v['reason'],'UNEXPANDED_DEEPER_ROUTE');self.assertTrue(v['nodes']);self.assertTrue(v['partial_nodes_are_diagnostic'])
