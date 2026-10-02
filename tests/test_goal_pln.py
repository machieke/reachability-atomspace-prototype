"""Independent structural checks and actual public-gate negative witnesses."""
import ast
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from experimental_online_pln.agenda import Agenda as FrozenAgenda, Limits, Probe, Snapshot, enumerate_work, wire
from experimental_goal_pln.agenda import Agenda, ARMS
from experimental_goal_pln.enumeration import enumerate_scoped
from experimental_goal_pln.relevance import ClosureLimits, Index, closure, extract_task, witness
from experimental_goal_pln.reference import scan_closure
from experimental_goal_pln.session import Session
from goal_pln_lab.cases import World, configuration
from goal_pln_lab.compare import replay_pair, run_case
from reachability.model import Status
from reachability.pln_adapter import DeductionRule, TruthValue, implication
from reachability.probability_model import ProbabilityIndependence, ProbabilityRule, ProbabilityPolicy
from validation_lab.online_pln_conformance import summary


class GoalPLNTests(unittest.TestCase):
    def setup_case(self, name='route-control'):
        tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup)
        world=World(next(f for f in configuration()['fixtures'] if f['id']==name))
        session=Session(tmp.name,acquire=world.acquire);self.addCleanup(session.close)
        world.setup(session)
        return session,world

    def parity(self,snapshot,limits=Limits(),bounds=ClosureLimits()):
        task=extract_task(snapshot)
        scan=scan_closure(snapshot,task,bounds)
        index=Index(snapshot);fast=closure(snapshot,task,bounds,index)
        self.assertEqual(replace(scan,elapsed_ns=0),replace(fast,elapsed_ns=0))
        full=enumerate_work(snapshot,limits)
        scoped=enumerate_scoped(snapshot,fast,index,limits)
        if fast.complete and full.complete:
            expected=tuple(c for c in full.candidates if witness(c,snapshot,scan))
            self.assertEqual(expected,scoped.candidates)
        return scan,scoped

    def test_registered_roots_readonly_and_codec_roundtrip(self):
        s,_=self.setup_case('route-shared')
        before=s.authority_records();view=s.read()
        journal,calls=s.service._journal_sequence,len(s.runtime.calls)
        for _ in range(3):
            dep,frontier=self.parity(view)
            self.assertTrue(dep.complete)
        self.assertEqual(before,s.authority_records())
        self.assertEqual((journal,calls),(s.service._journal_sequence,len(s.runtime.calls)))
        self.assertEqual(s.executor.total_effects,0)
        self.assertEqual(s.read().binding,view.binding)
        self.assertEqual(Snapshot.from_records(view.records()).binding,view.binding)
        roots=extract_task(view).roots
        self.assertEqual({r.target for r in roots if r.kind=='numeric'}, {s.forecast,s.forecast.negate()})
        self.assertIn(s.fact('credential'),[r.target for r in roots if r.kind=='hard'])
        self.assertTrue(any(r.kind=='health' for r in roots))
        self.assertEqual(extract_task(view).requirements[0][1].operator,'AND')

    def test_missing_multistep_and_shared_distractor(self):
        s,_=self.setup_case('path-three');dep,f=self.parity(s.read())
        self.assertEqual(len(dep.producers),3)
        self.assertTrue(all(len(p[2])==5 for p in dep.producers))
        self.assertEqual([(c.kind,c.target) for c in f.candidates],[('request','source-report')])
        self.assertIn(implication('tested','v'),dep.by_literal)
        other,_=self.setup_case('route-shared');d,f=self.parity(other.read())
        self.assertNotIn(implication('tested','unused'),d.by_literal)
        self.assertEqual(len(d.producers),1)
        self.assertIn('deduction',[c.kind for c in enumerate_work(other.read()).candidates])
        self.assertNotIn('deduction',[c.kind for c in f.candidates])

    def test_all_five_ordered_premises_and_alternative_producers(self):
        s,w=self.setup_case('path-alternatives')
        probe=s.probes['source-report'];s.request(probe)
        _,c=Agenda('Goal-index').choose(s.read());self.assertEqual(c.kind,'adopt');s.execute(c)
        d,f=self.parity(s.read())
        self.assertEqual(len(d.producers),3)
        first=[c for c in f.candidates if c.target=='b-step1']
        self.assertEqual(len(first),2)
        by_id={b.belief_revision_id:b for v in s.read().numerical for b in v.current}
        for c in first:
            self.assertEqual(tuple(by_id[p].proposal.support.conclusion for p in c.premise_ids),
                             s.rules['b-step1'].deduction.premises)
        before=s.authority_records();self.parity(s.read());self.parity(s.read())
        self.assertEqual(before,s.authority_records())
        self.assertEqual(summary(s)['outstanding'],10)

    def test_cycles_are_finite_and_do_not_create_proof(self):
        s,_=self.setup_case()
        s.register_rule(ProbabilityRule('cycle-a','1',DeductionRule('tested','healthy','staged')))
        d,_=self.parity(s.read())
        self.assertTrue(d.complete);self.assertLess(d.nodes,15);self.assertEqual(len(d.producers),2)
        self.assertEqual(len(d.paths),len(set(l for l,p in d.paths)))
        self.assertEqual(summary(s)['effects'],0)

    def test_frozen_arm_behavior_and_real_ranking_difference(self):
        s,_=self.setup_case('route-distractors');view=s.read()
        a=Agenda('FIFO-full');frozen=FrozenAgenda()
        self.assertEqual(a.choose(view)[1],frozen.choose(view)[1])
        b=Agenda('Goal-scan');c=Agenda('Goal-index')
        bc=b.choose(view)[1];cc=c.choose(view)[1]
        self.assertEqual(bc,cc);self.assertEqual(bc.kind,'request')
        self.assertEqual(a.diagnostic['ranking'],'frozen-fifo/v1')
        self.assertNotEqual(a.diagnostic['ranking'],b.diagnostic['ranking'])
        self.assertEqual(len(a.attempted),1)

    def test_rule_insertion_removal_policy_change_and_stale_task(self):
        s,_=self.setup_case();view=s.read();old=extract_task(view);olddep=closure(view,old)
        s.register_rule(ProbabilityRule('new','1',DeductionRule('tested','other','healthy')))
        new=s.read();dep,_=self.parity(new);self.assertEqual(len(dep.producers),2)
        with self.assertRaisesRegex(ValueError,'stale'):
            closure(new,old)
        with self.assertRaisesRegex(ValueError,'stale'):
            enumerate_scoped(new,olddep,Index(new))
        s.register_rule(ProbabilityRule('new','2',DeductionRule('tested','other','unrelated')),'1')
        dep,_=self.parity(s.read());self.assertEqual(len(dep.producers),1)
        s.service.configure_probability_policy('ctx',ProbabilityPolicy('2',('forecast-model',)), '1',idempotency_key=s.key())
        self.assertNotEqual(old.revisions,extract_task(s.read()).revisions)

    def test_equal_replacement_does_not_reuse_exact_basis(self):
        s,_=self.setup_case('change-replacement');a=Agenda('Goal-index')
        _,old=a.choose(s.read());r=s.execute(old)
        self.assertEqual(r['status'],'STALE');self.assertIsNone(r['commit'].belief)
        self.assertEqual(s.execute(old)['status'],'STALE')
        _,adopt=a.choose(s.read());self.assertEqual(adopt.kind,'adopt');s.execute(adopt)
        _,fresh=a.choose(s.read());self.assertNotEqual(old.premise_ids,fresh.premise_ids)
        self.assertNotEqual(old.basis,fresh.basis);self.assertEqual(s.execute(fresh)['status'],'PASS')
        self.parity(s.read())

    def test_revision_exact_model_retirement_and_parents_retained(self):
        s,w=self.setup_case()
        left=w.report('parent-a',s.forecast,TruthValue(.7,.25));right=w.report('parent-b',s.forecast,TruthValue(.7,.25))
        model=ProbabilityIndependence('explicit','ctx',(left.belief_revision_id,right.belief_revision_id),'independent source processes')
        s.register_model(model);d,f=self.parity(s.read())
        c=next(c for c in f.candidates if c.kind=='revision')
        self.assertEqual(c.premise_ids,model.premise_revision_ids)
        self.assertEqual(s.execute(c)['status'],'PASS')
        self.assertEqual(len(s.service.query_probability('ctx',s.forecast).current),3)
        self.assertEqual(s.read().decision.status,Status.UNKNOWN)
        s.revoke_model(model.model_id);d,f=self.parity(s.read())
        self.assertFalse(any(c.kind=='revision' for c in f.candidates))
        self.assertEqual(len(s.service.query_probability('ctx',s.forecast).current),2)

    def test_contrary_outside_preferred_route_blocks_actual_gate(self):
        s,w=self.setup_case();_,c=Agenda('Goal-index').choose(s.read());s.execute(c)
        self.assertEqual(s.read().decision.status,Status.PASS)
        w.report('contrary',s.forecast.negate(),TruthValue(.1,.1))
        self.assertEqual(s.read().decision.status,Status.UNKNOWN)
        self.assertNotEqual(s.reserve()['status'],'PASS')
        self.assertEqual(s.executor.total_effects,0)
        self.assertEqual(summary(s)['outstanding'],10)

    def test_unfavorable_received_report_is_not_suppressed(self):
        s,w=self.setup_case();w.report('unfavorable',s.forecast,TruthValue(.01,.1),adopt=False)
        first,_=self.parity(s.read())
        candidates=enumerate_scoped(s.read(),first,Index(s.read())).candidates
        self.assertIn('unfavorable',[c.target for c in candidates])
        s2,w2=self.setup_case();w2.report('unfavorable',s2.forecast,TruthValue(.99,.9),adopt=False)
        second,f=self.parity(s2.read())
        self.assertEqual(first.paths,second.paths)
        self.assertIn('unfavorable',[c.target for c in f.candidates])
        c=next(c for c in candidates if c.target=='unfavorable');s.execute(c)
        self.assertEqual(s.read().decision.status,Status.FAIL)
        self.assertNotEqual(s.reserve()['status'],'PASS')

    def test_hard_gate_and_stale_intent_survive_relevance(self):
        s,_=self.setup_case('supported-product')
        view=s.read();credential=next(b for b in view.context.usable if b.conclusion==s.fact('credential'))
        s.emit('revoke',evidence_id=credential.proposal.evidence_ids[0])
        _,c=Agenda('Goal-index').choose(s.read());self.assertEqual(c.kind,'reserve')
        self.assertEqual(s.execute(c)['status'],'UNKNOWN');self.assertEqual(s.executor.total_effects,0)
        s2,w=self.setup_case('supported-product');self.assertEqual(s2.reserve()['status'],'PASS')
        s2.emit('revoke',evidence_id='forecast-received')
        d,f=self.parity(s2.read());dispatch=next(c for c in f.candidates if c.kind=='dispatch')
        self.assertEqual(s2.execute(dispatch)['status'],'STALE')
        d,f=self.parity(s2.read());self.assertIn('dispatch',[c.kind for c in f.candidates])
        self.assertEqual(s2.executor.total_effects,0)
        s3,_=self.setup_case('supported-product');self.assertEqual(s3.reserve()['status'],'PASS')
        prepare=s3.service.prepare_dispatch
        def revoke_after_prepare(*args,**kwargs):
            result=prepare(*args,**kwargs)
            s3.emit('revoke',evidence_id='forecast-received')
            return result
        s3.service.prepare_dispatch=revoke_after_prepare
        _,candidate=Agenda('Goal-index').choose(s3.read())
        self.assertEqual(s3.execute(candidate)['status'],'STALE')
        d,f=self.parity(s3.read());self.assertIn('query',[c.kind for c in f.candidates])
        self.assertEqual(s3.executor.total_effects,0)

    def test_monitoring_independent_of_numeric_proof(self):
        s,_=self.setup_case('supported-monitor');d,f=self.parity(s.read())
        self.assertEqual([(c.kind,c.target) for c in f.candidates],[('request','health')])
        s.emit('revoke',evidence_id='forecast-received');d,f=self.parity(s.read())
        self.assertEqual([(c.kind,c.target) for c in f.candidates],[('request','health')])
        self.assertEqual(summary(s)['outstanding'],10)

    def test_task_roots_follow_contract_content_not_labels(self):
        s,_=self.setup_case();view=s.read();old=extract_task(view)
        criterion=replace(view.decision.contract.criteria[0],conclusion=implication('different','target'))
        changed=replace(view,decision=replace(view.decision,contract=replace(view.decision.contract,criteria=(criterion,))))
        roots=extract_task(changed);d,f=self.parity(changed)
        self.assertNotEqual(old.roots,roots.roots);self.assertEqual(len(d.producers),0)
        self.assertIn(criterion.conclusion,d.by_literal)
        # This is a read-only descriptor test, never a replacement service contract.
        self.assertEqual(s.read(),view)

    def test_closure_bounds_fallback_and_global_discovery_bounds(self):
        s,_=self.setup_case('route-distractors');snapshot=s.read()
        for limits in (ClosureLimits(nodes=0),ClosureLimits(edges=0),ClosureLimits(depth=0)):
            d,f=self.parity(snapshot,bounds=limits)
            self.assertFalse(d.complete);self.assertFalse(f.complete)
            for arm in ARMS[1:]:
                a=Agenda(arm,closure_limits=limits);full,c=a.choose(snapshot)
                self.assertTrue(full.complete);self.assertIn('INCOMPLETE_CLOSURE',a.diagnostic['fallback'])
                self.assertFalse(a.diagnostic['discovery_complete'])
        for limits in (Limits(estimates=0),Limits(rules=0),Limits(tuple_visits=0),Limits(candidates=0),Limits(selections=0),Limits(work=0)):
            pair=replay_pair(snapshot,Agenda('Goal-scan',limits),limits)
            self.assertIsNone(pair[0][2]);self.assertIsNone(pair[1][2])
            self.assertIsNotNone(pair[0][0].stop)
        self.assertEqual(summary(s)['outstanding'],10)

    def test_four_mutation_witnesses(self):
        s,_=self.setup_case('path-three');view=s.read();d,f=self.parity(view)
        # M1: omit the deepest prerequisite: full independent scan retains acquisition.
        missing=s.probes['source-report'].target
        mutant=replace(d,paths=tuple(p for p in d.paths if p[0]!=missing))
        self.assertNotEqual(f.candidates,enumerate_scoped(view,mutant,Index(view)).candidates)
        # M2: hide contrary receipt adoption (authority itself remains global).
        s2,w=self.setup_case();w.report('opposite',s2.forecast.negate(),TruthValue(.8,.8),adopt=False)
        v=s2.read();dep,full=self.parity(v)
        hidden=replace(dep,paths=tuple(p for p in dep.paths if p[0]!=s2.forecast.negate()))
        self.assertNotEqual(full.candidates,enumerate_scoped(v,hidden,Index(v)).candidates)
        # M3: reuse old closure after a rule insertion; exact binding rejects it.
        s.register_rule(ProbabilityRule('inserted','1',DeductionRule('tested','new','healthy')))
        with self.assertRaisesRegex(ValueError,'stale'):
            enumerate_scoped(s.read(),d,Index(s.read()))
        # M4: falsely complete a bounded traversal; independent reference disagrees.
        bounded=scan_closure(v,extract_task(v),ClosureLimits(nodes=0))
        self.assertFalse(bounded.complete)
        with patch('tests.test_goal_pln.closure',return_value=replace(bounded,complete=True,reason='COMPLETE_TASK_DEPENDENCIES')):
            with self.assertRaises(AssertionError):
                self.parity(v,bounds=ClosureLimits(nodes=0))

    def test_runtime_has_no_evaluator_or_pressure_dependency(self):
        for path in Path('experimental_goal_pln').glob('*.py'):
            tree=ast.parse(path.read_text())
            imports=[n.module or '' for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
            self.assertFalse(any(x.startswith(('goal_pln_lab','validation_lab','experimental_pressure','experimental_planning')) for x in imports))
        self.assertEqual(ARMS,('FIFO-full','Goal-scan','Goal-index'))

    def test_twelve_goal_runs_and_identical_state_replay(self):
        with TemporaryDirectory() as d:
            for f in configuration()['fixtures']:
                with self.subTest(case=f['id']):
                    r=run_case(f,Path(d)/f['id'],arm='Goal-index',budget=16)
                    self.assertEqual(r['conformance'],'PASS',r.get('traceback'))
                    import json
                    history=Agenda('Goal-index',Limits(work=16))
                    for line in (Path(d)/f['id']/'trace.jsonl').read_text().splitlines():
                        row=json.loads(line);snapshot=Snapshot.from_records(row['public_records'])
                        replay_pair(snapshot,history,history.limits)
                        self.assertEqual(wire(history.choose(snapshot)[1]),row['selected'])


class GoalPLNAuditTests(unittest.TestCase):
    def test_cross_session_hashes_only_are_normalized(self):
        from copy import deepcopy
        from goal_pln_lab.compare import cross_session_semantics
        row=dict(selected=dict(kind='deduction',target='registered',premise_ids=['p1','p2','p3','p4','p5'],
                              logical_id='logical',semantic_tie='tie',cost=1,basis='first-authority',expected_binding='first-snapshot'),
                 result=dict(status='PASS'),after=dict(outstanding=10,decision='PASS'),external_loss=10)
        fresh=deepcopy(row);fresh['selected'].update(basis='second-authority',expected_binding='second-snapshot')
        self.assertEqual(cross_session_semantics(row),cross_session_semantics(fresh))
        for field,value in (('target','different'),('premise_ids',['different']),('cost',2)):
            changed=deepcopy(fresh);changed['selected'][field]=value
            self.assertNotEqual(cross_session_semantics(row),cross_session_semantics(changed))
        changed=deepcopy(fresh);changed['after']['outstanding']=0
        self.assertNotEqual(cross_session_semantics(row),cross_session_semantics(changed))
        # Normalization must not mutate recorded exact bindings used by replay.
        self.assertEqual(row['selected']['basis'],'first-authority')

    def test_fresh_actual_ledgers_differ_only_in_scoped_hashes(self):
        from goal_pln_lab.compare import cross_session_semantics
        records=[]
        for arm in ('Goal-scan','Goal-index'):
            with TemporaryDirectory() as d:
                world=World(configuration()['fixtures'][0])
                with Session(d,acquire=world.acquire) as session:
                    world.setup(session)
                    _,c=Agenda(arm).choose(session.read())
                    records.append(dict(selected=wire(c),result={},after=summary(session),external_loss=world.external_loss))
        self.assertNotEqual(records[0]['selected']['expected_binding'],records[1]['selected']['expected_binding'])
        self.assertEqual(cross_session_semantics(records[0]),cross_session_semantics(records[1]))
