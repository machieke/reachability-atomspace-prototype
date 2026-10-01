"""Native projections of actual interleaved authority state before/after recovery."""
from tempfile import TemporaryDirectory
from pathlib import Path
import unittest

from reachability.atomspace_adapter import RecordProjection, project_admission
from reachability.interleaving_session import InterleavingSession
from validation_lab.generate_interleaving_cases import scenarios
from validation_lab.run_interleaving import run_case


class NativeInterleavingTests(unittest.TestCase):
    def test_blocker_and_competing_reservation_state_project_and_recover(self):
        test=self
        class NativeSession(InterleavingSession):
            def graph(self):
                records=[self.service.resource_snapshot(),self.service.inspect_resource('slot')]
                for actor in ('a','b'):
                    try:
                        records.append(self.service.inspect_execution_intent(actor))
                    except KeyError:
                        pass
                p=RecordProjection()
                p.add(tuple(records))
                return project_admission(self.service,'ctx'),p.batch.run()
            def restart(self):
                before=self.graph()
                super().restart()
                test.assertEqual(self.graph(),before)
        with TemporaryDirectory() as directory:
            for case in (scenarios()[0],scenarios()[5]):
                run_case(case,Path(directory)/case['case_id'],session_factory=NativeSession)
