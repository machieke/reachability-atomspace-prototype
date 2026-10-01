"""Native authority projections across actual dispatch-worker process recovery."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from reachability.atomspace_adapter import RecordProjection, project_admission, project_probability
from reachability.dispatch_worker_state import DurableDispatchSession
from reachability.trace_protocol import DeploymentInitial
from validation_lab.generate_dispatch_race_cases import scenarios
from validation_lab.public_worker import PublicWorker, runtime_bundle


class NativePublicWorkerTests(unittest.TestCase):
    def test_native_records_and_observed_inbox_survive_fresh_worker_retry(self):
        case=scenarios()[8]
        with TemporaryDirectory() as directory:
            root=Path(directory)
            runtime_bundle(root/'runtime')
            worker=PublicWorker(root/'runtime','dispatch',root/'state',root/'first')
            try:
                worker.request(case['public'])
                for event in case['events'][:6]:
                    worker.request(event)
            finally:
                worker.stop()
            def graph():
                with DurableDispatchSession(DeploymentInitial(),root/'state',resume=True) as session:
                    s=session.service
                    p=RecordProjection()
                    p.add((s.resource_snapshot(),s.inspect_resource('slot'),s.inspect_execution_intent('a'),s.inspect_dispatch('a')))
                    return project_admission(s,'c0'),project_probability(s,'c0'),p.batch.run(),session.projection()
            before=graph()
            worker=PublicWorker(root/'runtime','dispatch',root/'state',root/'second',resume=True)
            try:
                self.assertEqual(worker.request(case['public'])['executor_effects'],1)
                self.assertTrue(worker.request(case['events'][5])['replayed'])
            finally:
                worker.stop()
            self.assertEqual(graph(),before)


class NativeTraceWorkerTests(unittest.TestCase):
    def test_native_projections_survive_admission_and_deployment_process_retries(self):
        from reachability.admission_protocol import AdmissionInitial
        from reachability.trace_worker_state import DurableAdmissionSession,DurableDeploymentSession
        from validation_lab.generate_public_worker_cases import scenarios as worker_cases
        for index,cls in ((18,DurableAdmissionSession),(31,DurableDeploymentSession)):
            case=worker_cases()[index]
            initial=AdmissionInitial.parse(case['public']) if case['profile']=='admission' else DeploymentInitial.parse(case['public'])
            with self.subTest(profile=case['profile']),TemporaryDirectory() as directory:
                root=Path(directory); runtime_bundle(root/'runtime')
                worker=PublicWorker(root/'runtime',case['profile'],root/'state',root/'first')
                try:
                    worker.request(case['public'])
                    for message in case['events']:
                        worker.request(message)
                finally:
                    worker.stop()
                def graph():
                    with cls(initial,root/'state',resume=True) as session:
                        s=session.service
                        records=[]
                        if case['profile']=='deployment':
                            records=[s.resource_snapshot(),s.inspect_resource('slot'),s.inspect_goal('g0'),s.inspect_lifecycle('episode')]
                            for attempt in session.attempts:
                                records.extend((s.inspect_execution_intent(attempt),s.inspect_dispatch(attempt)))
                        p=RecordProjection(); p.add(tuple(records))
                        return project_admission(s,'c0'),project_probability(s,'c0'),p.batch.run(),session.projection()
                before=graph()
                worker=PublicWorker(root/'runtime',case['profile'],root/'state',root/'second',resume=True)
                try:
                    self.assertEqual(worker.request(case['public'])['completed'],len(case['events']))
                    self.assertTrue(worker.request(case['events'][-1])['replayed'])
                finally:
                    worker.stop()
                self.assertEqual(graph(),before)

    def test_native_pln_revision_continues_with_restored_aliases_and_bound_backend(self):
        from reachability.trace_worker_state import DurableAdmissionSession
        from validation_lab.generate_admission_cases import initial,scenarios as cases
        messages=cases()[12]['events']
        with TemporaryDirectory() as directory:
            with DurableAdmissionSession(initial(),directory,native=True) as session:
                for message in messages[:-1]:
                    row=session.apply(message)
                before=project_probability(session.service,'c0')
            with DurableAdmissionSession(initial(),directory,resume=True,native=True) as session:
                self.assertEqual(project_probability(session.service,'c0'),before)
                self.assertEqual(session.apply(messages[-2]),row)
                last=session.apply(messages[-1])
                self.assertEqual(last['outcome']['status'],'PASS')
                self.assertEqual(last['projection']['aliases']['numeric']['e006'],'e005')
                self.assertEqual(last['projection']['numeric']['e005']['confidence'],2/3)


class NativeWorkerInspectionTests(unittest.TestCase):
    def test_captured_authority_records_preserve_native_projection(self):
        from reachability.codec import decode
        from reachability.trace_worker_state import DurableDeploymentSession
        from reachability.worker_inspection import inspect_worker,verify_inspection,capture_names,file_inventory
        from validation_lab.generate_deployment_cases import scenarios as deployment_cases
        with TemporaryDirectory() as directory:
            root=Path(directory); state=root/'state'
            with DurableDeploymentSession(DeploymentInitial(),state) as session:
                for event in deployment_cases()[0]['events']:
                    session.apply(event)
                s=session.service
                records=(s.snapshot('c0'),s.inspect_lifecycle('episode'),s.inspect_goal('g0'),
                    s.inspect_resource('slot'),s.inspect_dispatch('a0'),s.inspect_execution_intent('a0'))
                p=RecordProjection(); p.add(records); before=p.batch.run()
            evidence=file_inventory(state,capture_names(state))
            report=inspect_worker('deployment',state,root/'inspection')
            self.assertEqual(verify_inspection(root/'inspection'),report)
            views=report['authority']['views']
            recovered=tuple(decode(views[name][key]) for name,key in (
                ('contexts','c0'),('lifecycle','episode'),('goals','g0'),('resources','slot'),('dispatch','a0'),('intents','a0')))
            p=RecordProjection(); p.add(recovered)
            self.assertEqual(p.batch.run(),before)
            self.assertEqual(file_inventory(state,capture_names(state)),evidence)
