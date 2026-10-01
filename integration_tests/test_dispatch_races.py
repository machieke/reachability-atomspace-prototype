"""Native projections of actual dispatch, receipt and uncertain resource state."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from reachability.atomspace_adapter import RecordProjection, project_admission, project_probability
from reachability.dispatch_race_session import DispatchRaceSession
from validation_lab.generate_dispatch_race_cases import scenarios
from validation_lab.run_dispatch_races import run_case


class NativeDispatchRaceTests(unittest.TestCase):
    def test_native_dispatch_numeric_and_resource_state_before_and_after_recovery(self):
        test=self
        class NativeSession(DispatchRaceSession):
            def graph(self):
                records=[self.service.resource_snapshot(),self.service.inspect_resource('slot')]
                for attempt in sorted(self.attempts):
                    try:
                        records.append(self.service.inspect_execution_intent(attempt))
                        records.append(self.service.inspect_dispatch(attempt))
                    except KeyError:
                        pass
                projection=RecordProjection()
                projection.add(tuple(records))
                return (project_admission(self.service,self.initial.context_id),
                        project_probability(self.service,self.initial.context_id),projection.batch.run())
            def restart(self):
                before=self.graph()
                super().restart()
                test.assertEqual(self.graph(),before)
        with TemporaryDirectory() as directory:
            for index in (4,7,10,11):
                case=scenarios()[index]
                run_case(case,Path(directory)/case['case_id'],session_factory=NativeSession)
