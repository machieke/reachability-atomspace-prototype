"""Actual native records for serial portfolio reservations, dispatch and outcomes."""
from tempfile import TemporaryDirectory
import unittest

from reachability.atomspace_adapter import RecordProjection, project_admission
from reachability.resource_planning import ResourceController, ResourcePublic
from reachability.resource_planning_session import ResourceSession
from validation_lab.generate_resource_planning_cases import scenarios
from validation_lab.run_resource_planning import ResourceWorld


class NativeResourcePlanningTests(unittest.TestCase):
    def test_native_hard_resource_intent_and_dispatch_records_survive_replay(self):
        for index in (8,11,13,18):
            case=scenarios()[index]
            public=ResourcePublic.parse(case['public']['profile'])
            with self.subTest(case=case['case_id']),TemporaryDirectory() as directory,ResourceSession(public,directory) as session:
                world=ResourceWorld(session,case)
                for message in case['public']['events']:
                    session.observe(message)
                ResourceController(public).run(world.port(),emit=world.on_selection)
                def resources():
                    projection=RecordProjection()
                    records=[session.service.resource_snapshot()]
                    records.extend(session.service.inspect_resource(r['resource_id']) for r in public.wire()['resources'])
                    for attempt in sorted(session.attempts):
                        try:
                            records.append(session.service.inspect_execution_intent(attempt))
                            records.append(session.service.inspect_dispatch(attempt))
                        except KeyError:
                            pass
                    projection.add(tuple(records))
                    return projection.batch.run()
                hard,held=project_admission(session.service,'portfolio'),resources()
                session.restart()
                self.assertEqual(project_admission(session.service,'portfolio'),hard)
                self.assertEqual(resources(),held)
