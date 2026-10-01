from pathlib import Path
from tempfile import TemporaryDirectory

from reachability.dispatch import Dispatcher
from reachability.dispatch_model import DispatchPolicy
from reachability.service import AdmissionService
from reachability.simulated_executor import SimulatedExecutor
from tests.execution_support import ExecutionFixture


class DispatchFixture(ExecutionFixture):
    def make_service(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.path = self.directory / "admission.db"
        return AdmissionService(database=self.path)

    def setUp(self):
        super().setUp()
        self.executor_path = self.directory / "executor.db"
        self.executor = SimulatedExecutor(self.executor_path)
        self.addCleanup(lambda: self.executor.close())
        self.policy = DispatchPolicy("dispatch", "1", self.contract.contract_id,
                                     self.contract.revision, self.executor.profile)
        self.service.register_dispatch_policy(self.policy, idempotency_key=self.driver.key())
        self.intent = self.reserve()

    def configure_executor(self, **kwargs):
        self.executor.close()
        revision = str(int(self.policy.revision) + 1)
        self.executor_path = self.directory / f"executor-{revision}.db"
        self.executor = SimulatedExecutor(self.executor_path, **kwargs)
        self.policy = DispatchPolicy("dispatch", revision, self.contract.contract_id,
                                     self.contract.revision, self.executor.profile)
        self.service.register_dispatch_policy(self.policy, idempotency_key=self.driver.key())

    @property
    def dispatcher(self):
        return Dispatcher(self.service, self.executor)

    def prepare(self):
        return self.service.prepare_dispatch("attempt", self.policy.policy_id, self.policy.revision,
                                              "worker", idempotency_key=self.driver.key())

    def dispatch(self):
        return self.dispatcher.dispatch("attempt", self.policy.policy_id, self.policy.revision, "worker")

    def restart(self):
        self.service.close()
        self.executor.close()
        self.service = AdmissionService(database=self.path)
        self.driver.service = self.service
        self.executor = SimulatedExecutor(self.executor_path)
