"""Public-API scenario helpers for reservation and intent contracts."""
from reachability.execution_model import ExecutionContract, ResourceDefinition, ResourceDemand
from reachability.service import AdmissionService
from tests.lifecycle_support import CREDENTIAL, TESTED, accept, schema
from tests.support import Driver


class ExecutionFixture:
    def make_service(self):
        return AdmissionService()

    def setUp(self):
        self.service = self.make_service()
        self.addCleanup(lambda: self.service.close())
        self.driver = Driver(self.service)
        self.driver.context()
        self.service.register_lifecycle_schema(schema(), idempotency_key=self.driver.key())
        self.service.open_lifecycle_episode("episode", "ctx", "artifact", "1", idempotency_key=self.driver.key())
        accept(self.driver, TESTED, evidence_id="tested")
        accept(self.driver, CREDENTIAL, evidence_id="credential")
        self.service.register_resource(ResourceDefinition("slot", 1, "slots"), idempotency_key=self.driver.key())
        self.contract = ExecutionContract("build", "1", "artifact", "1", "build", "executor", ("worker",),
                                          (ResourceDemand("slot", 1, "slots"),), 10)
        self.service.register_execution_contract(self.contract, idempotency_key=self.driver.key())
        self.operation()

    def operation(self, attempt="attempt", episode="episode", select=True):
        operation = self.service.propose_operation("build:" + episode, attempt, episode, "build",
                                                   idempotency_key=self.driver.key())
        if select:
            operation = self.service.select_operation(attempt, operation.revision, idempotency_key=self.driver.key())
        return operation

    def permit(self, attempt="attempt", contract=None, owner="worker", **revisions):
        contract = contract or self.contract
        operation = self.service.inspect_operation(attempt).operation
        revisions.setdefault("expected_operation_revision", operation.revision)
        revisions.setdefault("expected_knowledge_revision", self.service.snapshot(operation.context_id).knowledge_revision)
        revisions.setdefault("expected_resource_revision", self.service.resource_snapshot().revision)
        return self.service.certify_execution(attempt, contract.contract_id, contract.revision, owner,
                                               **revisions, idempotency_key=self.driver.key())

    def reserve(self, permit=None, key=None):
        return self.service.reserve_and_record_intent(permit or self.permit(), idempotency_key=key or self.driver.key())
