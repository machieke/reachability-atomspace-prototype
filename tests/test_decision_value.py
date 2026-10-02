"""Bounded reference semantics, independent engines and certified harness checks."""
import ast
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from reachability.pressure_session import ReasoningSession
from reachability.pressure_work import enumerate_work
from reachability.trace_protocol import fingerprint
from validation_lab import decision_reference as reference
from validation_lab.decision_reference import Reference, Bounds, STOP
from validation_lab.decision_enumeration import enumerate_histories
from validation_lab.decision_tasks import cohort, parents, budgets, materialize
from validation_lab.decision_runtime import witness, execute_prefix, POLICIES, public_task
from validation_lab import decision_comparison as experiment
from validation_lab.pressure_episodes import ReasoningWorld
from validation_lab import projection_comparison as projection
from validation_lab import run_pressure_comparison as runner
from validation_lab import audit_pressure_comparison as audit

TASKS={t['task_id']:t for t in cohort()}


class ReferenceTests(unittest.TestCase):
    def test_complete_independent_enumeration_every_cell_and_sample(self):
        for task in cohort():
            for budget in budgets():
                with self.subTest(task=task['task_id'],budget=budget['name']):
                    ref=Reference(task,budget['budget']);label=ref.labels()
                    self.assertEqual(label['status'],'EXACT')
                    other=enumerate_histories(task,budget['budget'])
                    self.assertEqual(other['status'],'EXACT');self.assertEqual(label['root']['q'],other['q'])
                    for state,_ in ref.sampled_states():
                        other=enumerate_histories(task,budget['budget'],state=state.wire())
                        self.assertEqual(ref.solve(state)['q'],other['q'])

    def test_hand_calculated_values_and_complete_ties(self):
        b=budgets()[1]['budget']
        simple=Reference(TASKS['completion-0'],b);root=simple.solve()
        self.assertEqual(root['value'],1);self.assertEqual(root['q'][STOP]['value'],16)
        state=simple.successor(simple.initial(),'derive/r0');label=simple.solve(state)
        self.assertEqual(label['optimal_actions'],[STOP,'monitor/g0'])
        self.assertEqual(label['witness'],['monitor/g0',STOP])
        two=Reference(TASKS['completion-1'],b)
        self.assertEqual(two.solve()['value'],3)
        self.assertEqual(two.solve()['optimal_actions'],['derive/r0','derive/r1'])
        andref=Reference(TASKS['and-0'],b)
        self.assertEqual(andref.solve()['value'],6)
        costly=Reference(TASKS['budget-0'],budgets()[0]['budget'])
        self.assertEqual(costly.solve()['value'],22)
        self.assertEqual(costly.solve()['optimal_actions'],['derive/r0'])
        # Monitoring affects certification but never invents external relief.
        initial=Reference(TASKS['completion-6'],b)
        self.assertEqual(initial.solve()['value'],0)
        self.assertEqual(set(initial.solve()['optimal_actions']),{STOP,'monitor/g0','monitor/g1'})

    def test_monitor_time_and_remaining_budget_states_are_distinct(self):
        ref=Reference(TASKS['completion-1'],budgets()[1]['budget']);ref.solve()
        state=ref.successor(ref.initial(),'derive/r0')
        monitored=ref.successor(state,'monitor/g0')
        self.assertNotEqual(state,monitored)
        self.assertNotEqual(ref.losses(state)[1],ref.losses(monitored)[1])
        no_work=replace(state,operation_work=0)
        self.assertNotEqual(ref.solve(state)['value'],ref.solve(no_work)['value'])
        no_requests=replace(state,requests=0)
        self.assertEqual(ref.actions(no_requests),[STOP])
        later=replace(state,tick=8)
        self.assertNotEqual(ref.solve(no_work)['value'],ref.solve(replace(later,operation_work=0))['value'])

    def test_missing_and_joint_consistency_and_shared_work(self):
        ref=Reference(TASKS['and-6'],budgets()[1]['budget']);label=ref.solve()
        self.assertNotIn('derive/r1',ref.actions(ref.initial()))
        self.assertEqual(label['value'],49)
        self.assertNotIn('monitor/g0',sum((ref.actions(s) for s in ref.memo),[]))
        shared=Reference(TASKS['shared-0'],budgets()[1]['budget']);root=shared.solve()
        self.assertEqual(root['value'],10)
        self.assertEqual(root['witness'].count('derive/r0'),1)
        self.assertEqual(root['operation_work'],5)

    def test_identifier_and_dominated_siblings_keep_optimum_and_old_plan(self):
        for task in cohort():
            if not task['sibling']: continue
            for b in budgets():
                parent=Reference(TASKS[task['parent_id']],b['budget']);child=Reference(task,b['budget'])
                self.assertEqual(parent.solve()['value'],child.solve()['value'])
                state=child.initial()
                for action in parent.solve()['witness']:
                    if action!=STOP: state=child.successor(state,task['rename'].get(action,action))
                if task['sibling_kind']=='identifiers':
                    mapped=sorted(task['rename'].get(a,a) for a in parent.solve()['optimal_actions'])
                    self.assertEqual(mapped,child.solve()['optimal_actions'])
                else:
                    for action,item in parent.solve()['q'].items():
                        self.assertEqual(item['value'],child.solve()['q'][action]['value'])

    def test_bounds_censor_without_inventing_optimum(self):
        task=TASKS['shared-0'];b=budgets()[1]['budget']
        for bounds in (Bounds(states=1),Bounds(transitions=1),Bounds(memory_bytes=1)):
            label=Reference(task,b,bounds=bounds).labels()
            self.assertEqual(label['status'],'REFERENCE_EXHAUSTED');self.assertIsNone(label['root'])
        enum=enumerate_histories(task,b,node_limit=1)
        self.assertEqual(enum['status'],'REFERENCE_EXHAUSTED');self.assertNotIn('value',enum);self.assertNotIn('q',enum)
        with self.assertRaises(ValueError): Bounds(states=0)

    def test_unsupported_future_and_invalid_truth_are_rejected(self):
        for key,value in [('support_validity','expires'),('future_changes','revocation'),('probe_responses','hidden')]:
            t=deepcopy(TASKS['completion-0']);t['contract'][key]=value
            with self.assertRaises(ValueError): Reference(t,budgets()[1]['budget'])
        t=deepcopy(TASKS['completion-0']);t['contract']['truth']=[1,-2]
        with self.assertRaises(ValueError): Reference(t,budgets()[1]['budget'])

    def test_engines_import_only_standard_library(self):
        for name in ('decision_reference','decision_enumeration'):
            tree=ast.parse((Path('validation_lab')/(name+'.py')).read_text())
            modules=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
            modules += [a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
            self.assertTrue(set(modules)<={'dataclasses','itertools','json','time'})

    def test_inventory_is_fixed_and_partitioned_by_parent(self):
        config=experiment.configuration();self.assertEqual(len(config['tasks']),66)
        self.assertEqual(len(parents()),48)
        self.assertEqual(sum(t['partition']=='confirmation' for t in parents()),18)
        self.assertEqual(config,json.loads(Path('reviews/decision-value-v1/inventory.json').read_text()))
        for t in cohort(): self.assertEqual(t['partition'],TASKS[t['parent_id']]['partition'])


class CertifiedHarnessTests(unittest.TestCase):
    def test_all_canonical_reference_witnesses_execute_exactly(self):
        # Policy-free feasibility/parity test; no policy measurements or tuning.
        with TemporaryDirectory() as temp:
            for task in cohort():
                for i,b in enumerate(budgets()):
                    with self.subTest(task=task['task_id'],budget=b['name']):
                        ref=Reference(task,b['budget']);label=ref.solve()
                        out=witness(task,ref,label,Path(temp)/(task['task_id']+str(i)))
                        self.assertEqual(out['integrated_loss'],label['value'])
                        self.assertEqual(out['final']['certified_weighted_loss'],label['terminal_certified'])

    def test_public_model_and_frozen_paths_on_hand_control(self):
        # Committed test fixture, excluded from all cohort measurements.
        task=deepcopy(TASKS['completion-1']);task['task_id']='test-control';task['parent_id']='test-control'
        b=budgets()[1];ref=Reference(task,b['budget']);ref.solve()
        with TemporaryDirectory() as temp:
            for p in POLICIES:
                path=Path(temp)/p
                with public_task(task) as delivered,projection.ranking_policy(p) as measured:
                    result=runner.run_one(materialize(task),'B0' if p=='B0' else 'B3',b,path)
                self.assertEqual(delivered,[fingerprint(task)])
                labels=experiment.decisions(task,b,ref,result,path)
                self.assertGreaterEqual(labels['episode_gap'],0)
                with public_task(task),projection.ranking_policy(p): audit.audit_run(path,materialize(task),b,result)
                rows=[json.loads(x) for x in (path/'trace.jsonl').read_text().splitlines()]
                experiment.check_projection(dict(result=result,**measured),rows)
                self.assertEqual(result['ranking_paths'],[audit.PATHS['B0' if p=='B0' else 'B3']])

    def test_common_snapshot_readonly_and_saved_journal(self):
        task=deepcopy(TASKS['shared-0']);task['task_id']='test-common';task['parent_id']='test-common'
        b=budgets()[1];ref=Reference(task,b['budget']);ref.solve()
        with TemporaryDirectory() as temp:
            path=Path(temp)/'common';sample=experiment.common_sample(task,b,ref,['derive/r0'],path)
            self.assertEqual(len(sample['rankings']),5)
            self.assertEqual(experiment.save_signature(path,task),sample['journal_signature'])
            for r in sample['rankings']:
                self.assertEqual(r['label']['state'],sample['state'])
                self.assertEqual(r['task_digest'],fingerprint(task))
                self.assertEqual(r['discovery_ns'],sample['discovery_ns'])
                self.assertEqual(r['remaining_budget'],sample['remaining_budget'])
            changed=deepcopy(sample['snapshot']);changed['supports'][0]['valid_until']=3
            with self.assertRaises(ValueError): experiment.reference_state(task,changed,sample['remaining_budget'])

    def test_journal_signature_json_roundtrip_across_decimal_revision_boundary(self):
        # v1 failed after all measurements because integer keys sort numerically
        # before serialization but decoded JSON object keys sort lexically.
        task=TASKS['or-4'];ref=Reference(task,budgets()[0]['budget']);label=ref.solve()
        with TemporaryDirectory() as temp:
            path=Path(temp)/'w';witness(task,ref,label,path)
            signature=experiment.save_signature(path,task)
            self.assertTrue(any(int(k)>=10 for k in signature['history']))
            decoded=json.loads(json.dumps(signature))
            audit.equal(signature,decoded,'journal JSON roundtrip')
            self.assertTrue(all(type(k) is str for k in signature['history']))
            altered=deepcopy(decoded);altered['history']['2']['interpretation']='tampered'
            with self.assertRaises(audit.AuditError): audit.equal(signature,altered,'changed belief history')

    def test_corrupt_prefix_and_illegal_reference_action_fail(self):
        task=TASKS['completion-0'];b=budgets()[1];ref=Reference(task,b['budget']);ref.solve()
        with TemporaryDirectory() as temp:
            path=Path(temp)/'w';out=witness(task,ref,ref.solve(),path)
            rows=[json.loads(x) for x in (path/'trace.jsonl').read_text().splitlines()]
            altered=deepcopy(rows);altered[1]['receipt']['status']='STALE'
            with self.assertRaises(audit.AuditError): experiment.compare_prefix_trace(altered,rows)
            with self.assertRaises(ValueError): experiment.selected_label(ref,ref.initial(),'monitor/g0')
            signature=experiment.save_signature(path,task)
            self.assertEqual(signature['logical_time'],16)
            self.assertEqual(signature['goals']['g0']['outstanding'],0)


if __name__=='__main__': unittest.main()
