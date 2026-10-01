"""Versioned JSON record codec with an explicit type allowlist; never pickle."""
from dataclasses import fields, is_dataclass
import json
import math

from . import model
from . import lifecycle_model as lifecycle
from . import execution_model as execution
from . import dispatch_model as dispatch
from . import goal_model as goal
from .completion import CompletionContract, CompletionPermit
from .requirements import Requirement, RequirementResult, RequirementWitness
from . import probability_model as probability
from .pln_adapter import (DeductionRule, PLNProposal, ProbabilisticSupport, ProbabilitySnapshot,
                          TruthValue, IndependenceDeclaration)

RECORDS = {cls.__name__: cls for cls in (
    model.Statement, model.Literal, model.Clause, model.Evidence, model.Rule,
    model.Check, model.Transition, model.Proposal, model.Certificate,
    model.BeliefRevision, model.CommitResult, model.BeliefView, model.ContextSnapshot,
    Requirement, RequirementResult, RequirementWitness,
    lifecycle.LifecycleState, lifecycle.LifecycleEdge, lifecycle.LifecycleSchema,
    lifecycle.LifecycleEvent, lifecycle.LifecycleEpisode, lifecycle.LifecycleView,
    lifecycle.LifecyclePermit, lifecycle.OperationObservation, lifecycle.OperationEpisode,
    lifecycle.OperationView,
    execution.ResourceDefinition, execution.ResourceDemand, execution.ResourceClaim,
    execution.ExecutionContract, execution.ExecutionPermit, execution.Reservation,
    execution.ExecutionIntent, execution.ExecutionIntentView, execution.ResourceView, execution.ResourceSnapshot,
    dispatch.ExecutorProfile, dispatch.DispatchPolicy, dispatch.DispatchRequest,
    dispatch.ExecutorReceipt, dispatch.DispatchAttempt, dispatch.DispatchView,
    goal.DurabilityContract, goal.GoalSlice, goal.GoalContract, goal.GoalMonitor, goal.GoalEpisode,
    goal.GoalSample, goal.CoverageCommitment, goal.DurabilityResult, goal.GoalSliceView,
    goal.GoalProjection, goal.GoalReliefEvent, goal.GoalAccountingRevision, goal.GoalView,
    CompletionContract, CompletionPermit,
    TruthValue, ProbabilisticSupport, ProbabilitySnapshot, DeductionRule, PLNProposal, IndependenceDeclaration,
    probability.ProbabilityPolicy, probability.ProbabilityReport, probability.ProbabilityRule,
    probability.ProbabilityIndependence, probability.ProbabilityTransition, probability.ProbabilityCertificate,
    probability.ProbabilityBeliefRevision, probability.ProbabilityCommitResult, probability.ProbabilityView,
)}


def encode(value):
    if isinstance(value, model.Status):
        return {"$status": value.value}
    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("nonfinite durable number")
        return {"$float64": value.hex()}
    if is_dataclass(value) and RECORDS.get(type(value).__name__) is type(value):
        return {"$record": type(value).__name__, "fields": {
            field.name: encode(getattr(value, field.name)) for field in fields(value)}}
    if isinstance(value, tuple):
        return {"$tuple": [encode(item) for item in value]}
    if isinstance(value, list):
        return [encode(item) for item in value]
    if isinstance(value, dict) and all(type(key) is str for key in value):
        return {"$map": {key: encode(item) for key, item in value.items()}}
    raise ValueError(f"unsupported durable value: {type(value).__name__}")


def decode(value):
    if value is None or type(value) in (str, int, bool):
        return value
    if isinstance(value, list):
        return [decode(item) for item in value]
    if not isinstance(value, dict):
        raise ValueError("unsupported durable JSON value")
    if set(value) == {"$float64"} and type(value["$float64"]) is str:
        try:
            number = float.fromhex(value["$float64"])
        except OverflowError as error:
            raise ValueError("durable binary64 overflow") from error
        if not math.isfinite(number) or number.hex() != value["$float64"]:
            raise ValueError("noncanonical or nonfinite durable binary64")
        return number
    if set(value) == {"$status"}:
        return model.Status(value["$status"])
    if set(value) == {"$tuple"} and isinstance(value["$tuple"], list):
        return tuple(decode(item) for item in value["$tuple"])
    if set(value) == {"$map"} and isinstance(value["$map"], dict):
        return {key: decode(item) for key, item in value["$map"].items()}
    if set(value) == {"$record", "fields"} and value["$record"] in RECORDS:
        record = RECORDS[value["$record"]]
        data = value["fields"]
        if not isinstance(data, dict) or set(data) != {field.name for field in fields(record)}:
            raise ValueError("durable record fields do not match the registered schema")
        return record(**{key: decode(item) for key, item in data.items()})
    raise ValueError("unknown durable record encoding")


def dumps(value) -> str:
    return json.dumps(encode(value), sort_keys=True, separators=(",", ":"), allow_nan=False)


def loads(value: str):
    return decode(json.loads(value))
