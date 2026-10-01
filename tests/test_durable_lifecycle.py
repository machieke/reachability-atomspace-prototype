"""Replay the same lifecycle and operation contracts through the durable store."""
from pathlib import Path
from tempfile import TemporaryDirectory

from reachability.service import AdmissionService
from tests import test_lifecycle, test_operations


class DurableFixture:
    def make_service(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "lifecycle.db"
        service = AdmissionService(database=self.path)
        self.addCleanup(service.close)
        return service

    def tearDown(self):
        episodes = {key: self.service.inspect_lifecycle(key) for key in self.service._lifecycle.episodes}
        operations = {key: self.service.inspect_operation(key) for key in self.service._lifecycle.attempts}
        self.service.close()
        with AdmissionService(database=self.path) as recovered:
            self.assertEqual({key: recovered.inspect_lifecycle(key) for key in episodes}, episodes)
            self.assertEqual({key: recovered.inspect_operation(key) for key in operations}, operations)


class DurableLifecycleTests(DurableFixture, test_lifecycle.LifecycleTests):
    pass


class DurableOperationTests(DurableFixture, test_operations.OperationTests):
    pass
