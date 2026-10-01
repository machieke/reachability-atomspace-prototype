"""Public bounded grounded-admission messages, independent of evaluator labels."""
from dataclasses import dataclass
import math

from .trace_protocol import canonical, identifier, integer, read_json

INITIAL_SCHEMA = "admission-initial/v1"
EVENT_SCHEMA = "admission-event/v1"
TRACE_SCHEMA = "admission-trace/v1"


def sequence(value, limit):
    if type(value) is not list or len(value) > limit:
        raise ValueError("expected a bounded JSON array")


def literal(value, atoms=8):
    if type(value) is not int or not 1 <= abs(value) <= atoms:
        raise ValueError("literal must be a nonzero signed declared atom index")


def literals(value, atoms=8):
    sequence(value, 8)
    for item in value:
        literal(item, atoms)


def clauses(value, atoms=8):
    sequence(value, 32)
    for item in value:
        literals(item, atoms)


def rule(value, atoms):
    if type(value) is not dict or set(value) != {"rule_id", "revision", "premises", "conclusion"}:
        raise ValueError("invalid grounded rule fields")
    identifier(value["rule_id"])
    identifier(value["revision"])
    literals(value["premises"], atoms)
    if not value["premises"]:
        raise ValueError("grounded rules need at least one premise")
    literal(value["conclusion"], atoms)


@dataclass(frozen=True)
class AdmissionInitial:
    # Canonical JSON strings keep nested public arrays immutable after validation.
    atoms: tuple[str, ...] = ("a0", "a1", "a2", "a3")
    rules_json: str = "[]"

    def wire(self):
        return dict(schema=INITIAL_SCHEMA, atoms=list(self.atoms), rules=read_json(self.rules_json))

    @classmethod
    def parse(cls, value):
        if type(value) is not dict or set(value) != {"schema", "atoms", "rules"} or value["schema"] != INITIAL_SCHEMA:
            raise ValueError("unsupported admission initial state")
        sequence(value["atoms"], 8)
        sequence(value["rules"], 8)
        for item in value["atoms"]:
            identifier(item)
        if not value["atoms"] or len(set(value["atoms"])) != len(value["atoms"]):
            raise ValueError("declare one to eight distinct atoms")
        for item in value["rules"]:
            rule(item, len(value["atoms"]))
        if len({r["rule_id"] for r in value["rules"]}) != len(value["rules"]):
            raise ValueError("duplicate rule identity")
        return cls(tuple(value["atoms"]), canonical(value["rules"]))


ARGUMENTS = {
    "context": {"context_id", "assumptions", "clauses"},
    "evidence": {"context_id", "literal", "roots", "valid_until"},
    "estimate": {"context_id", "literal", "roots", "valid_until", "strength", "confidence"},
    "adopt": {"context_id", "evidence_id"},
    "derive": {"context_id", "rule_id", "premises"},
    "rule": {"rule", "expected_revision"},
    "policy": {"context_id", "revision", "clauses"},
    "tick": {"context_id", "time"},
    "revoke": {"evidence_id"},
    "independence": {"context_id", "model_id", "premises", "justification"},
    "revise": {"context_id", "premises", "model_id"},
    "revoke_model": {"context_id", "model_id"},
    "restart": set(),
}


@dataclass(frozen=True)
class AdmissionEvent:
    event_id: str
    kind: str
    arguments_json: str

    @property
    def arguments(self):
        return read_json(self.arguments_json)

    def wire(self):
        return dict(schema=EVENT_SCHEMA, event_id=self.event_id, kind=self.kind, arguments=self.arguments)

    @classmethod
    def parse(cls, value, atoms=8):
        if type(value) is not dict or set(value) != {"schema", "event_id", "kind", "arguments"}:
            raise ValueError("invalid admission event fields")
        kind, args = value["kind"], value["arguments"]
        if value["schema"] != EVENT_SCHEMA or type(kind) is not str or kind not in ARGUMENTS:
            raise ValueError("unsupported admission event")
        identifier(value["event_id"])
        if type(args) is not dict or set(args) != ARGUMENTS[kind]:
            raise ValueError("invalid admission event arguments")
        for name, item in args.items():
            if name in ("context_id", "evidence_id", "rule_id", "revision", "expected_revision", "justification"):
                identifier(item)
            elif name == "model_id":
                if item is not None or kind != "revise":
                    identifier(item)
            elif name == "literal":
                literal(item, atoms)
            elif name == "assumptions":
                literals(item, atoms)
            elif name == "clauses":
                clauses(item, atoms)
            elif name in ("roots", "premises"):
                sequence(item, 8 if name == "roots" or kind == "derive" else 2)
                for ref in item:
                    identifier(ref)
                if name == "roots" and not item:
                    raise ValueError("evidence needs lineage roots")
                if kind == "independence" and (len(item) != 2 or len(set(item)) != 2):
                    raise ValueError("independence binds two distinct references")
            elif name == "rule":
                rule(item, atoms)
            elif name in ("time", "valid_until"):
                if item is not None or name == "time":
                    integer(item)
            elif name in ("strength", "confidence"):
                if type(item) not in (int, float) or not math.isfinite(item) or not 0 <= item <= 1:
                    raise ValueError("finite truth components must lie in [0,1]")
                if name == "confidence" and item == 1:
                    raise ValueError("empirical confidence must be below one")
        return cls(value["event_id"], kind, canonical(args))


def event(event_id, kind, **arguments):
    return AdmissionEvent.parse(dict(schema=EVENT_SCHEMA, event_id=event_id, kind=kind, arguments=arguments)).wire()
