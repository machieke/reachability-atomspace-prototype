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
