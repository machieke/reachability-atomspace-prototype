import ast
from copy import deepcopy
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from reachability.dispatch import Dispatcher
from reachability.model import Status
from reachability.resource_planning import ResourceController, ResourcePublic, search, step
from reachability.resource_planning_session import ResourceSession, event
from reachability.service import AdmissionDenied
from reachability.trace_protocol import fingerprint
from validation_lab.generate_resource_planning_cases import generated_scenarios, lease, profile, ready, scenarios
from validation_lab.resource_planning_oracle import exact_plan, feasible
from validation_lab.run_deployment import ConformanceMismatch
from validation_lab.run_resource_planning import ResourceWorld, load_cases, run_case, verify_corpus

ROOT=Path(__file__).resolve().parents[1]


class ResourcePlanningTests(unittest.TestCase):
    def open_case(self, index=0):
        c=scenarios()[index]
        p=ResourcePublic.parse(c['public']['profile'])
        directory=TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        session=ResourceSession(p,directory.name)
        self.addCleanup(session.close)
        for message in c['public']['events']:
            session.observe(message)
        return p,session

    def action(self, session, kind='reserve'):
        s=session.read()
        return dict(schema='resource-action/v1',kind=kind,snapshot_digest=fingerprint(s),until=None,
                    plan=search(session.public,s)['plan'] if kind=='reserve' else None)

    def test_fixed_plans_and_every_event_match_cold_and_recovered_references(self):
        verify_corpus()
        results=[run_case(c) for c in load_cases()]
        self.assertEqual(sum(r['compared_prefixes'] for r in results),119)
        self.assertEqual(sum(r['completed'] for r in results),11)
        for r in results:
            self.assertEqual(r['compared_prefixes'],r['recovered_prefixes'])

    def test_generated_instances_are_reproducible_unfiltered_and_realize_frozen_plans(self):
        cases=generated_scenarios()
        self.assertEqual(cases,generated_scenarios())
        results=[run_case(c) for c in cases]
        self.assertEqual(sum(r['compared_prefixes'] for r in results),44)
        self.assertEqual(sum(r['completed'] for r in results),5)

    def test_whole_cost_time_resource_packets_and_combined_portfolio_budgets(self):
        results=[run_case(scenarios()[i]) for i in (0,1,2,5,13,14)]
        self.assertEqual([r['objective'] for r in results],[[2,2],[4,1],None,[3,1],[4,3],None])
        plan=results[4]['records'][0]['plan']
        self.assertEqual(len(plan['steps']),2)
        self.assertEqual(sum(s['cost'] for s in plan['steps']),4)
        self.assertEqual(len({s['job_id'] for s in plan['steps']}),2)

    def test_aggregate_capacity_and_half_open_lease_endpoints(self):
        blocked=run_case(scenarios()[3])
        spare=run_case(scenarios()[4])
        self.assertEqual(blocked['records'][0]['plan']['steps'][0]['start'],3)
        self.assertEqual(spare['records'][0]['plan']['steps'][0]['start'],0)
        self.assertEqual(blocked['records'][0]['action']['kind'],'wait')

    def test_selection_stales_after_new_lease_and_replans_without_charging_twice(self):
        r=run_case(scenarios()[6])
        first=r['records'][0]
        self.assertEqual(first['receipt']['status'],'STALE')
        self.assertEqual(first['receipt']['charged'],0)
        self.assertEqual(first['receipt']['public_events'],1)
        self.assertEqual(r['final_time'],5)
        self.assertEqual(r['spent'],2)

    def test_credentials_revoked_after_reservation_block_dispatch_and_observation(self):
        r=run_case(scenarios()[7])
        self.assertEqual(r['executor_effects'],0)
        self.assertEqual(r['stop_reason'],'PREREQUISITE_UNAVAILABLE')
        self.assertEqual(r['projection']['attempts']['run:0']['dispatch'],None)
        self.assertEqual(r['spent'],2)
        self.assertFalse(r['projection']['jobs']['a']['completed'])

    def test_stale_observation_selection_does_not_consume_the_last_deadline_probe(self):
        case=scenarios()[1]
        case['hooks']=[dict(kind='observe',occurrence=2,events=[event('refresh','ready',job_id='a',valid_until=None)])]
        result=run_case(case)
        self.assertTrue(result['completed'])
        probes=[r for r in result['records'] if r['action'] and r['action']['kind']=='observe']
        self.assertEqual([r['receipt']['status'] for r in probes],['PASS','STALE','PASS'])
        self.assertEqual(result['final_time'],1)

    def test_remote_occupancy_change_is_checked_again_before_actual_send(self):
        r=run_case(scenarios()[18])
        self.assertEqual(r['executor_effects'],1)  # Only the injected background operation.
        self.assertIsNone(r['projection']['attempts']['run:0']['dispatch'])
        self.assertEqual(r['records'][-1]['receipt']['status'],'UNKNOWN')

    def test_pending_reservation_certificate_is_stale_after_resource_revision_change(self):
        _,s=self.open_case(4)
        service=s.service
        op=service.propose_operation('job:a','race','job:a','execute',idempotency_key=s.key())
        op=service.select_operation('race',op.revision,idempotency_key=s.key())
        permit=service.certify_execution('race','mode:m0','1','worker',op.revision,service.snapshot('portfolio').knowledge_revision,
                                         service.resource_snapshot().revision,idempotency_key=s.key())
        self.assertEqual(permit.status,Status.PASS)
        s.observe(lease('new',resource='gpu',quantity=1,duration=1))
        with self.assertRaises(AdmissionDenied) as denied:
            service.reserve_and_record_intent(permit,idempotency_key=s.key())
        self.assertEqual(denied.exception.status,Status.STALE)
        self.assertEqual(s.executor.total_effects,0)

    def test_lost_ack_and_failed_first_send_keep_one_exact_request_and_effect(self):
        for index in (8,9):
            r=run_case(scenarios()[index])
            kinds=[x['action']['kind'] for x in r['records'] if x['action']]
            self.assertIn('reconcile',kinds)
            self.assertEqual(r['executor_effects'],1)
            self.assertEqual(list(r['projection']['attempts']),['run:0'])
            self.assertEqual(r['projection']['attempts']['run:0']['dispatch'],'released')

    def test_wrong_product_is_logged_and_never_credited_before_correct_observation(self):
        with TemporaryDirectory() as directory:
            path=Path(directory)/'actual.jsonl'
            r=run_case(scenarios()[10],trace_path=path)
            rows=[json.loads(line) for line in path.read_text().splitlines()]
        failures=[row['actual'] for row in rows if row['record_type']=='runtime' and row['actual']['status']=='FAIL']
        self.assertEqual(len(failures),1)
        self.assertFalse(failures[0]['projection']['jobs']['a']['completed'])
        self.assertEqual(failures[0]['projection']['attempts']['run:0']['milestones'],[])
        self.assertTrue(r['completed'])
        self.assertEqual(r['final_time'],3)

    def test_lease_expiry_and_acknowledgement_do_not_establish_completion_or_release(self):
        r=run_case(scenarios()[11])
        self.assertFalse(r['completed'])
        self.assertEqual(r['executor_effects'],1)
        hold=r['projection']['holds'][0]
        self.assertEqual(hold['end'],r['final_time'])
        self.assertTrue(hold['uncertain'])
        self.assertEqual(r['projection']['attempts']['run:0']['dispatch'],'accepted')
        blocked=run_case(scenarios()[12])
        self.assertEqual(blocked['stop_reason'],'NO_CERTIFIABLE_PLAN')
        self.assertTrue(blocked['projection']['holds'][0]['uncertain'])

    def test_revoked_product_and_milestone_retire_current_views_without_implicit_regression(self):
        p,s=self.open_case()
        # Seed the cold model with the same already-delivered public initialization.
        world=ResourceWorld(s,scenarios()[0])
        world.events=deepcopy(scenarios()[0]['public']['events'])
        ResourceController(p).run(world.port(),emit=world.on_selection)
        product=next(eid for eid,f in s.projection()['facts'].items() if f['predicate']=='Available')
        milestone=next(eid for eid,f in s.projection()['facts'].items() if f['predicate']=='rd:operation/exact_product_observed')
        s.send('revoke',evidence_id=milestone)
        self.assertNotIn('exact_product_observed',s.projection()['attempts']['run:0']['milestones'])
        s.send('revoke',evidence_id=product)
        self.assertFalse(s.read()['jobs']['a']['completed'])
        self.assertFalse(s.read()['jobs']['a']['ready'])
        self.assertEqual(s.service.inspect_lifecycle('job:a').episode.stage,'BUILT')
        self.assertEqual(search(p,s.read())['status'],'NO_CERTIFIABLE_PLAN')

    def test_late_outcome_releases_first_job_but_invalidates_remaining_nominal_plan(self):
        r=run_case(scenarios()[19])
        self.assertEqual(r['objective'],[2,4])
        self.assertEqual(r['final_time'],3)
        self.assertEqual(r['executor_effects'],1)
        self.assertEqual(r['projection']['holds'],[])
        self.assertEqual(r['stop_reason'],'NO_CERTIFIABLE_PLAN')
        self.assertFalse(r['completed'])

    def test_truncated_search_discards_even_a_feasible_incumbent(self):
        p,s=self.open_case()
        before=s.read()
        r=search(p,before,visit_limit=1)
        self.assertEqual(r['status'],'BUDGET_EXHAUSTED')
        self.assertIsNone(r['plan'])
        self.assertEqual(r['work']['complete_plans'],1)
        self.assertEqual(s.read(),before)
        self.assertEqual(exact_plan(p.wire(),before,candidate_limit=0)['status'],'NOT_COMPUTED')

    def test_current_support_must_outlast_the_predicted_completion_boundary(self):
        p,s=self.open_case(15)
        plan=search(p,s.read())['plan']
        self.assertEqual(plan['steps'][0]['mode_id'],'m1')
        self.assertEqual(plan['finishes_at'],1)

    def test_forged_partial_or_typed_mismatched_contract_never_issues_a_command(self):
        _,s=self.open_case()
        action=self.action(s)
        before=s.read()
        for mutate in (lambda first:first.update(demands=[]),lambda first:first.update(revision='2'),
                       lambda first:first.update(cost=True),lambda first:first.update(end=1)):
            bad=deepcopy(action)
            mutate(bad['plan']['steps'][0])
            with self.assertRaises(ValueError):
                s.execute(bad)
            self.assertEqual(s.read(),before)
        stale=deepcopy(action)
        stale['snapshot_digest']='old'
        self.assertEqual(s.execute(stale),dict(status='STALE',public_events=0,charged=0))

    def test_fresh_forged_plan_cannot_reserve_beyond_the_public_deadline(self):
        _,s=self.open_case(1)
        snapshot=s.read()
        action=dict(schema='resource-action/v1',kind='reserve',snapshot_digest=fingerprint(snapshot),until=None,
            plan=dict(schema='resource-plan/v1',snapshot_digest=fingerprint(snapshot),steps=[step(s.modes['m0'],0)],cost=2,finishes_at=2))
        self.assertEqual(s.execute(action)['status'],'FAIL')
        self.assertEqual(s.spent,0)
        self.assertEqual(s.attempts,{})

    def test_failed_actual_reservation_still_charges_issued_declared_work(self):
        _,s=self.open_case(17)
        result=s.send('reserve',mode_id='m0',revision='1',attempt_id='run:manual')
        self.assertEqual(result['status'],'UNKNOWN')
        self.assertEqual(s.spent,2)
        self.assertIsNone(s.active)
        self.assertIsNone(s.projection()['attempts']['run:manual']['intent'])

    def test_public_profile_and_snapshot_are_detached_and_reject_hidden_fields(self):
        p,s=self.open_case()
        wire=p.wire()
        wire['modes'][0]['demands'].clear()
        self.assertTrue(p.wire()['modes'][0]['demands'])
        snap=s.read()
        snap['jobs']['a']['ready']=False
        self.assertTrue(s.read()['jobs']['a']['ready'])
        for field in ('world','responses','expected'):
            raw=p.wire()
            raw[field]={}
            with self.assertRaises(ValueError):
                ResourcePublic.parse(raw)
            raw=s.read()
            raw[field]={}
            with self.assertRaises(ValueError):
                search(p,raw)
        for mutate in (lambda raw:raw['modes'][0]['demands'][0].update(unit='wrong'),
                       lambda raw:raw['modes'][0].update(duration=0),lambda raw:raw.update(deadline=True)):
            raw=p.wire()
            mutate(raw)
            with self.assertRaises(ValueError):
                ResourcePublic.parse(raw)

    def test_independent_witness_check_rejects_missing_job_and_invented_resource_packet(self):
        p,s=self.open_case(13)
        plan=search(p,s.read())['plan']
        self.assertIsNone(feasible(p.wire(),s.read(),plan['steps'][:1]))
        bad=deepcopy(plan['steps'])
        bad[0]['demands']=[]
        self.assertIsNone(feasible(p.wire(),s.read(),bad))

    def test_refusing_all_work_fails_positive_control_and_actual_proposals_precede_oracle(self):
        class Idle(ResourceController):
            def run(self, port, **kw):
                return super().run(port,requests=0,**kw)
        with self.assertRaises(ConformanceMismatch):
            run_case(scenarios()[0],controller_factory=Idle)
        with TemporaryDirectory() as directory:
            path=Path(directory)/'failed.jsonl'
            with patch('validation_lab.run_resource_planning.exact_plan',side_effect=ValueError('injected reference gap')),self.assertRaises(ValueError):
                run_case(scenarios()[0],trace_path=path)
            row=json.loads(path.read_text().splitlines()[-1])
            self.assertEqual(row['actual']['plan']['cost'],2)

    def test_same_wrapper_recovery_does_not_change_reservation_or_selected_event_stream(self):
        case=scenarios()[13]
        a,b=run_case(case,recover=True),run_case(case,recover=False)
        self.assertEqual(a['events'],b['events'])
        self.assertEqual(a['projection'],b['projection'])
        self.assertEqual(a['spent'],b['spent'])

    def test_runtime_and_reference_import_boundaries_and_public_port(self):
        for name in ('resource_planning','resource_planning_session'):
            tree=ast.parse((ROOT/f'reachability/{name}.py').read_text())
            self.assertFalse(any(isinstance(n,ast.ImportFrom) and 'validation_lab' in (n.module or '') for n in ast.walk(tree)))
        tree=ast.parse((ROOT/'validation_lab/resource_planning_oracle.py').read_text())
        self.assertEqual({n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)},{'copy','itertools'})
        _,s=self.open_case()
        port=ResourceWorld(s,scenarios()[0]).port()
        for name in ('session','case','responses','hooks'):
            self.assertFalse(hasattr(port,name))

    def test_fixture_reproducibility_and_source_receipt_drift(self):
        self.assertEqual(load_cases(),scenarios())
        receipt=verify_corpus()
        with TemporaryDirectory() as directory:
            root=Path(directory)
            for name in (*receipt['fixture_files'],*receipt['source_files'],'validation_lab/resource_planning_cases/manifest.json'):
                path=root/name
                path.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/name,path)
            with patch('validation_lab.run_resource_planning.ROOT',root),patch('validation_lab.run_resource_planning.CORPUS',root/'validation_lab/resource_planning_cases'):
                verify_corpus()
                source=root/'reachability/resource_planning.py'
                source.write_text(source.read_text()+'\n# drift\n')
                with self.assertRaisesRegex(ValueError,'receipt mismatch'):
                    verify_corpus()
