"""Real AtomSpace readback of planned proofs and their recovered exact lineage."""
from tempfile import TemporaryDirectory
import unittest

from reachability.atomspace_adapter import project_admission
from reachability.grounded_planning import GroundedController, PlanningPublic
from reachability.planning_session import PlanningSession
from validation_lab.generate_planning_cases import scenarios
from validation_lab.run_planning import PlanningWorld


class NativeGroundedPlanningTests(unittest.TestCase):
    def test_planned_proofs_expiry_and_rule_replacement_project_and_recover(self):
        for index in (0, 8, 13, 14, 18):
            case = scenarios()[index]
            public = PlanningPublic.parse(case['public']['profile'])
            with self.subTest(case=case['case_id']), TemporaryDirectory() as directory, PlanningSession(public, directory, native=True) as session:
                world = PlanningWorld(session, case['hooks'])
                for message in case['public']['events']:
                    session.observe(message)
                result = GroundedController(public).run(world.port(), emit=world.on_selection)
                self.assertEqual(result['stop_reason'], 'OBSERVED_GOALS')
                actual = project_admission(session.admission.service, public.context_id)
                snapshot = session.read()
                session.restart()
                self.assertEqual(session.read(), snapshot)
                self.assertEqual(project_admission(session.admission.service, public.context_id), actual)
