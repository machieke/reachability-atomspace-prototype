from pathlib import Path
from tempfile import TemporaryDirectory

from reachability.service import AdmissionService
from tests import test_goals, test_goal_coverage


class DurableGoalFixture:
    def make_service(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "goals.db"
        return AdmissionService(database=self.path)

    def tearDown(self):
        views = {goal_id: self.service.inspect_goal(goal_id) for goal_id in self.service._goals.goals}
        self.service.close()
        with AdmissionService(database=self.path) as recovered:
            self.assertEqual({goal_id: recovered.inspect_goal(goal_id) for goal_id in views}, views)


class DurableGoalTests(DurableGoalFixture, test_goals.GoalTests):
    pass


class DurableCoverageTests(DurableGoalFixture, test_goal_coverage.CoverageTests):
    pass
