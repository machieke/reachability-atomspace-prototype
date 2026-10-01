"""Versioned public inputs for the bounded deployment conformance driver.

No schedules, evaluator labels, reference plans or expected outputs enter here.
"""
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math

INITIAL_SCHEMA = "deployment-initial/v1"
EVENT_SCHEMA = "deployment-event/v1"
TRACE_SCHEMA = "deployment-trace/v1"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def fingerprint(value):
    return sha256(canonical(value).encode()).hexdigest()


def read_json(text, *, max_bytes=65536):
    if len(text.encode()) > max_bytes:
        raise ValueError("public message exceeds 64 KiB" if max_bytes == 65536 else "JSON record exceeds its size bound")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON field")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("nonfinite JSON number: " + value)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid)


def identifier(value):
    if type(value) is not str or not value or len(value.encode()) > 256:
        raise ValueError("identifiers require one to 256 UTF-8 bytes")


def integer(value):
    if type(value) is not int or not 0 <= value <= 1000:
        raise ValueError("trace integer must be in [0,1000]")


@dataclass(frozen=True)
class DeploymentInitial:
    context_id: str = "c0"
    product_id: str = "p0"
    goal_id: str = "g0"
    loss: int = 10
    capacity: int = 1
    lease_duration: int = 10
    min_strength: float = .65
    min_confidence: float = .35
    schema: str = INITIAL_SCHEMA

    def __post_init__(self):
        for value in (self.context_id, self.product_id, self.goal_id):
            identifier(value)
        for value in (self.loss, self.capacity, self.lease_duration):
            integer(value)
            if value == 0:
                raise ValueError("loss, capacity and lease duration must be positive")
        for value in (self.min_strength, self.min_confidence):
            if type(value) not in (float, int) or not math.isfinite(value):
                raise ValueError("thresholds must be finite numbers")
        if not 0 <= self.min_strength <= 1 or not 0 <= self.min_confidence < 1:
            raise ValueError("unsupported decision thresholds")
        if self.schema != INITIAL_SCHEMA:
            raise ValueError("unsupported public initial schema")

    @classmethod
    def parse(cls, value):
        if type(value) is not dict or set(value) != set(asdict(cls())):
            raise ValueError("public initial state has missing or unexpected fields")
        return cls(**value)


# Each event is one public command, not a future event script. Defaults are made
# explicit on the wire so its digest has no implicit schema-dependent arguments.
ARGUMENTS = {
    "fact": {"name", "valid_until"},
    "forecast": {"strength", "confidence", "valid_until"},
    "revoke": {"evidence_id"}, "tick": {"time"},
    "attempt": {"attempt_id"}, "reserve": {"attempt_id"},
    "cover": {"attempt_id", "units", "valid_until"},
    "prepare": {"attempt_id"}, "dispatch": {"attempt_id", "fault"},
    "reconcile": {"attempt_id"}, "release": {"attempt_id"},
    "observation": {"attempt_id", "milestone", "product_id"},
    "sample": {"healthy"}, "complete": {"attempt_id"},
    "censor": set(), "resume": set(), "account": set(), "restart": set(),
}


@dataclass(frozen=True)
class DeploymentEvent:
    event_id: str
    kind: str
    arguments: tuple[tuple[str, object], ...]

    @classmethod
    def parse(cls, value):
        if type(value) is not dict or set(value) != {"schema", "event_id", "kind", "arguments"}:
            raise ValueError("public event has missing or unexpected fields")
        if value["schema"] != EVENT_SCHEMA or type(value["kind"]) is not str or value["kind"] not in ARGUMENTS:
            raise ValueError("unsupported public event")
        identifier(value["event_id"])
        args, kind = value["arguments"], value["kind"]
        if type(args) is not dict or set(args) != ARGUMENTS[kind]:
            raise ValueError("event arguments differ from the declared schema")
        for name, item in args.items():
            if name in ("attempt_id", "evidence_id", "product_id"):
                identifier(item)
            elif name in ("time", "units", "valid_until"):
                if name != "valid_until" or item is not None:
                    integer(item)
                if kind == "cover" and (item is None or name == "units" and item == 0):
                    raise ValueError("coverage requires positive units and a finite deadline")
            elif name in ("strength", "confidence"):
                if type(item) not in (float, int) or not math.isfinite(item) or not 0 <= item <= 1:
                    raise ValueError("forecast component must be finite and in [0,1]")
                if name == "confidence" and item == 1:
                    raise ValueError("finite empirical confidence must be below one")
            elif name == "healthy" and type(item) is not bool:
                raise ValueError("sample polarity must be Boolean")
        if kind == "fact" and args["name"] not in ("tested", "credential", "product"):
            raise ValueError("unsupported deployment fact")
        if kind == "dispatch" and args["fault"] not in ("none", "before_effect", "lost_reply"):
            raise ValueError("unsupported simulator fault")
        if kind == "observation" and args["milestone"] not in (
                "completion_observed", "exact_product_observed", "failure_observed", "cancellation_observed"):
            raise ValueError("unsupported operation observation")
        return cls(value["event_id"], kind, tuple(sorted(args.items())))

    def wire(self):
        return dict(schema=EVENT_SCHEMA, event_id=self.event_id, kind=self.kind, arguments=dict(self.arguments))


def event(event_id, kind, **arguments):
    """Construct and validate a single public message."""
    return DeploymentEvent.parse(dict(schema=EVENT_SCHEMA, event_id=event_id, kind=kind, arguments=arguments)).wire()
