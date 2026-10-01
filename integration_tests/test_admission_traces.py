"""Native formula execution and disposable AtomSpace projections of trace state."""
from tempfile import TemporaryDirectory
import unittest

from reachability.admission_trace import AdmissionSession
from reachability.atomspace_adapter import project_admission, project_probability
from validation_lab.generate_admission_cases import initial, scenarios
from validation_lab.run_admission import run_case


class NativeAdmissionTraceTests(unittest.TestCase):
    def test_fixed_public_cases_match_cold_oracle_with_native_inference_and_recovery(self):
        for case in scenarios():
            with self.subTest(case=case["case_id"]):
                run_case(initial(), case, native=True)

    def test_context_lineage_and_retirement_projections_survive_replay(self):
        for index in (11, 13, 15):
            with self.subTest(case=index), TemporaryDirectory() as directory, AdmissionSession(initial(), directory, native=True) as session:
                for message in scenarios()[index]["events"]:
                    session.apply(message)
                graphs = {(ctx, kind): project(session.service, ctx) for ctx in session.contexts
                          for kind, project in (("hard", project_admission), ("numeric", project_probability))}
                actual = session.projection()
                session.restart()
                self.assertEqual(session.projection(), actual)
                for (ctx, kind), graph in graphs.items():
                    project = project_admission if kind == "hard" else project_probability
                    self.assertEqual(project(session.service, ctx), graph)
