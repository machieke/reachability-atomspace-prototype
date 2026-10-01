"""Lose a submission reply, restart both authorities, reconcile and fence release."""
from itertools import count
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from .dispatch import Dispatcher
from .dispatch_model import DispatchPolicy
from .execution_model import ExecutionContract, ResourceDefinition, ResourceDemand
from .lifecycle_model import LifecycleEdge, LifecycleSchema, LifecycleState
from .model import Literal, Statement
from .requirements import Requirement
from .service import AdmissionService
from .simulated_executor import SimulatedExecutor


class LoseSubmissionReply(SimulatedExecutor):
    def submit(self, request):
        super().submit(request)
        raise TimeoutError("demonstration: the effect committed but its reply was lost")


def run() -> dict[str, object]:
    product = Requirement("FACT", Literal(Statement("Available", ("artifact-v2",))))
    schema = LifecycleSchema("artifact", "1", "artifact", "artifact-v2", "READY",
        (LifecycleState("READY"), LifecycleState("BUILT", product)),
        (LifecycleEdge("build", "READY", "BUILT", Requirement("ALWAYS"), product,
                       "artifact-v2", ("executor",)),), ("BUILT",), "dispatch-demo")
    contract = ExecutionContract("build", "1", "artifact", "1", "build", "executor", ("worker",),
                                 (ResourceDemand("slot", 1, "slots"),), 10)
    sequence = count()

    def key():
        return f"dispatch-demo:{next(sequence)}"

    with TemporaryDirectory() as directory:
        local, remote = Path(directory) / "admission.db", Path(directory) / "executor.db"
        with AdmissionService(database=local) as service, LoseSubmissionReply(remote) as executor:
            service.open_context("ctx", idempotency_key=key())
            service.register_lifecycle_schema(schema, idempotency_key=key())
            service.open_lifecycle_episode("episode", "ctx", "artifact", "1", idempotency_key=key())
            service.propose_operation("build", "attempt", "episode", "build", idempotency_key=key())
            service.select_operation("attempt", 0, idempotency_key=key())
            service.register_resource(ResourceDefinition("slot", 1, "slots"), idempotency_key=key())
            service.register_execution_contract(contract, idempotency_key=key())
            service.register_dispatch_policy(DispatchPolicy("dispatch", "1", "build", "1", executor.profile),
                                              idempotency_key=key())
            permit = service.certify_execution("attempt", "build", "1", "worker", 1,
                service.snapshot("ctx").knowledge_revision, service.resource_snapshot().revision,
                idempotency_key=key())
            service.reserve_and_record_intent(permit, idempotency_key=key())
            first = Dispatcher(service, executor).dispatch("attempt", "dispatch", "1", "worker")
        with AdmissionService(database=local) as service, SimulatedExecutor(remote) as executor:
            dispatcher = Dispatcher(service, executor)
            reconciled = dispatcher.reconcile("attempt", "worker")
            service.advance_resource_clock(10, idempotency_key=key())
            service.advance_clock("ctx", 10, idempotency_key=key())
            held = bool(service.inspect_resource("slot").reconciliation_attempts)
            released = dispatcher.release("attempt", "worker")
            late = executor.submit(first.dispatch.request)
            return {
                "scope": "independent local executor simulation; no real external actions",
                "after_lost_reply": first.state,
                "after_restart_reconciliation": reconciled.state,
                "same_request": first.dispatch.request == reconciled.dispatch.request,
                "capacity_held_after_lease_expiry": held,
                "resources_released": released.resources_released,
                "late_submission": late.state,
                "historical_effects": executor.total_effects,
                "lifecycle_stage": service.inspect_lifecycle("episode").episode.stage,
                "operation_outcome": service.inspect_operation("attempt").outcome_status.value,
            }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
