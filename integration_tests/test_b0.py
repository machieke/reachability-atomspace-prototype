"""Actual AtomSpace projections of autonomous B0 deployment state and recovery."""
from tempfile import TemporaryDirectory
import unittest

from reachability.atomspace_adapter import project_admission, project_probability, project_execution_decision
from reachability.b0 import B0Controller, B0Public, Budget
from reachability.deployment_trace import DeploymentSession
from validation_lab.b0_environment import DeploymentWorld
from validation_lab.generate_b0_cases import scenarios


class NativeB0Tests(unittest.TestCase):
    def test_closed_loop_operation_and_evidence_projections_survive_replay(self):
        for index in (3, 6):
            case = scenarios()[index]
            public = B0Public.parse(case["public"])
            with self.subTest(case=case["case_id"]), TemporaryDirectory() as directory, DeploymentSession(public.deployment, directory) as session:
                env = DeploymentWorld(session, public, case["world"])
                result = B0Controller(public).run_budget(env.port(), Budget(**case["budget"]))
                self.assertEqual(result["stop_reason"], "observed_success")
                hard = project_admission(session.service, public.deployment.context_id)
                numeric = project_probability(session.service, public.deployment.context_id)
                decisions = {a: project_execution_decision(session.service, a) for a in session.attempts}
                session.restart()
                self.assertEqual(project_admission(session.service, public.deployment.context_id), hard)
                self.assertEqual(project_probability(session.service, public.deployment.context_id), numeric)
                self.assertEqual({a: project_execution_decision(session.service, a) for a in session.attempts}, decisions)
