"""The resource/intent contract suite, followed by checked cold reconstruction."""
from pathlib import Path
from tempfile import TemporaryDirectory

from reachability.service import AdmissionService
from tests import test_execution


class DurableExecutionTests(test_execution.ExecutionTests):
    def make_service(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "execution.db"
        return AdmissionService(database=self.path)

    def tearDown(self):
        resources = {key: self.service.inspect_resource(key) for key in self.service._execution.resources}
        intents = {key: self.service.inspect_execution_intent(key) for key in self.service._execution.intents}
        self.service.close()
        with AdmissionService(database=self.path) as recovered:
            self.assertEqual({key: recovered.inspect_resource(key) for key in resources}, resources)
            self.assertEqual({key: recovered.inspect_execution_intent(key) for key in intents}, intents)
