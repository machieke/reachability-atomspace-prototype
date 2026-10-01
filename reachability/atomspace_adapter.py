"""Real AtomSpace snapshot projection; the admission journal remains authoritative.

Each batch owns a private native AtomSpace and reads it back before returning.
No native handle or mutable Value is an admission permit. Failed projection has
no effect on the service. Exact integer fields use decimal StringValues.
"""
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import math
from pathlib import Path

from .adapter_runtime import AdapterError, ROOT, checked_run, lockfile, verify_native_build
from .codec import dumps
from .model import identity


def _hex(text: str) -> str:
    if not isinstance(text, str) or len(text.encode()) > 65536:
        raise ValueError("native string exceeds 64 KiB")
    return text.encode().hex() or "-"


def _unhex(text: str) -> str:
    return "" if text == "-" else bytes.fromhex(text).decode()


@dataclass(frozen=True)
class NativeGraph:
    aliases: tuple[int, ...]
    atoms: dict[int, tuple]
    values: dict[tuple[int, int], str | tuple[float, ...]]
    size: int


class AtomSpaceBatch:
    """Explicit structural atoms and named Values, transported without eval."""
    def __init__(self):
        self.commands: list[str] = []
        self.atoms: list[tuple] = []
        self.values: dict[tuple[int, int], str | tuple[float, ...]] = {}
        self._writes: list[tuple[int, int, str | tuple[float, ...]]] = []

    def node(self, name: str, *, predicate: bool = False) -> int:
        kind = "P" if predicate else "N"
        self.commands.append(f"{kind} {_hex(name)}")
        self.atoms.append((kind, name))
        return len(self.atoms) - 1

    def _ref(self, ref: int) -> None:
        if type(ref) is not int or not 0 <= ref < len(self.atoms):
            raise ValueError("invalid batch atom reference")

    def link(self, outgoing: tuple[int, ...]) -> int:
        outgoing = tuple(outgoing)
        if len(outgoing) > 4096:
            raise ValueError("native arity limit exceeded")
        for ref in outgoing:
            self._ref(ref)
        self.commands.append("L " + str(len(outgoing)) + " " + " ".join(map(str, outgoing)))
        self.atoms.append(("L", outgoing))
        return len(self.atoms) - 1

    def set_value(self, atom: int, key: int, value: str | tuple[float, ...]) -> None:
        self._ref(atom)
        self._ref(key)
        if self.atoms[key][0] != "P":
            raise ValueError("value key must be a PredicateNode")
        if isinstance(value, str):
            self.commands.append(f"S {atom} {key} {_hex(value)}")
        else:
            if (not isinstance(value, tuple) or len(value) > 4096 or
                    any(type(x) not in (float, int) or not math.isfinite(x) for x in value)):
                raise ValueError("FloatValue requires a bounded finite numeric tuple")
            value = tuple(float(x) for x in value)
            self.commands.append(f"F {atom} {key} {len(value)} " + " ".join(map(repr, value)))
        self.values[atom, key] = value
        self._writes.append((atom, key, value))

    def run(self, root: Path = ROOT / "artifacts") -> NativeGraph:
        root = Path(root)
        verify_native_build(root)
        wire = "\n".join(self.commands) + "\n" if self.commands else ""
        if len(self.commands) > 100000 or len(wire.encode()) > 8388608:
            raise ValueError("native batch limit exceeded")
        lines = checked_run([str(root / "bin" / "atomspace_batch")], input=wire).splitlines()
        header = "reachability-atomspace-batch/v1 " + lockfile()["sources"]["atomspace"]["commit"]
        if not lines or lines[0] != header:
            raise AdapterError("native protocol/revision mismatch")
        aliases, atoms, values = [], {}, {}
        try:
            for line in lines[1:-1]:
                tokens = line.split()
                if tokens[0] == "A":
                    _, ref, canonical, kind, *data = tokens
                    if int(ref) != len(aliases):
                        raise ValueError("out-of-order atom")
                    canonical = int(canonical)
                    aliases.append(canonical)
                    if kind == "L":
                        if int(data[0]) != len(data) - 1:
                            raise ValueError("wrong arity")
                        atom = (kind, tuple(map(int, data[1:])))
                    elif kind in ("N", "P") and len(data) == 1:
                        atom = (kind, _unhex(data[0]))
                    else:
                        raise ValueError("invalid atom")
                    if canonical in atoms and atoms[canonical] != atom:
                        raise ValueError("inconsistent alias")
                    atoms[canonical] = atom
                elif tokens[0] in ("S", "F"):
                    kind, ref, key, *data = tokens
                    if kind == "S" and len(data) == 1:
                        value = _unhex(data[0])
                    elif kind == "F" and int(data[0]) == len(data) - 1:
                        value = tuple(map(float, data[1:]))
                    else:
                        raise ValueError("invalid value")
                    pair = (int(ref), int(key))
                    if pair in values:
                        raise ValueError("duplicate value response")
                    values[pair] = value
                else:
                    raise ValueError("invalid response")
            size_tag, size = lines[-1].split()
            # This pinned AtomSpace marks Value keys with an internal PredicateNode.
            # It is native metadata, not a user record or an admission flag.
            marker = int(any(a != k for a, k in values) and
                         ("P", "*-IsKeyFlag-*") not in atoms.values())
            if size_tag != "SIZE" or int(size) != len(atoms) + marker or len(aliases) != len(self.atoms):
                raise ValueError("incomplete graph")
            # Check readback against independently canonicalized requested structure.
            expected_atoms, index, expected_aliases = {}, {}, []
            for i, atom in enumerate(self.atoms):
                normalized = (("L", tuple(expected_aliases[x] for x in atom[1]))
                              if atom[0] == "L" else atom)
                canonical = index.setdefault(normalized, i)
                expected_aliases.append(canonical)
                expected_atoms[canonical] = normalized
            expected_values = {(expected_aliases[a], expected_aliases[k]): v
                               for a, k, v in self._writes}
            if (aliases != expected_aliases or atoms != expected_atoms or values != expected_values):
                raise ValueError("native readback mismatch")
        except (ValueError, IndexError, KeyError) as exc:
            raise AdapterError(f"invalid native readback: {exc}") from exc
        return NativeGraph(tuple(aliases), atoms, values, int(size))


class RecordProjection:
    """Typed structural mapping of finite immutable records to real Atoms."""
    def __init__(self):
        self.batch = AtomSpaceBatch()
        self._records: dict[str, int] = {}

    def add_probability(self, proposal) -> int:
        """Store an explicitly proposed TV with its full structural explanation.

        The proposal marker is structural; no accepted-belief entry is created.
        """
        from .pln_adapter import PLNProposal
        if not isinstance(proposal, PLNProposal):
            raise ValueError("expected a probabilistic proposal")
        support = proposal.support
        atom = self.add(("proposed-probabilistic-support/v1", proposal.proposal_id,
                         proposal.context_id, support.support_id, support.conclusion,
                         proposal.formula_id, support.truth.truth_model, proposal.assumptions,
                         proposal.premise_ids, support.evidence_ids, support.lineage_roots,
                         support.ancestors))
        key = self.batch.node("pln:strength-confidence", predicate=True)
        self.batch.set_value(atom, key, (support.truth.strength, support.truth.confidence))
        key = self.batch.node("snapshot:knowledge-revision", predicate=True)
        self.batch.set_value(atom, key, str(proposal.knowledge_revision))
        return atom

    def add(self, value) -> int:
        if is_dataclass(value):
            # Numeric fields remain Values; a content ID keeps revisions distinct.
            content_id = identity("atomspace-record/v1", dumps(value))
            if content_id in self._records:
                return self._records[content_id]
            members = [self.batch.node("record:" + type(value).__name__),
                       self.batch.node(content_id)]
            numeric = []
            for field in fields(value):
                item = getattr(value, field.name)
                key = self.batch.node("field:" + field.name, predicate=True)
                if type(item) is int:
                    numeric.append((key, str(item)))
                else:
                    members.append(self.batch.link((key, self.add(item))))
            atom = self.batch.link(tuple(members))
            for key, number in numeric:
                self.batch.set_value(atom, key, number)
            self._records[content_id] = atom
            return atom
        if isinstance(value, Enum):
            return self.batch.node(f"enum:{type(value).__name__}:{value.value}")
        if value is None or type(value) is bool:
            return self.batch.node("scalar:" + repr(value))
        if isinstance(value, str):
            return self.batch.node("text:" + value)
        if isinstance(value, tuple):
            return self.batch.link((self.batch.node("tuple"), *(self.add(x) for x in value)))
        raise ValueError(f"unsupported structural type: {type(value).__name__}")


def project_admission(service, context_id: str, *, root: Path = ROOT / "artifacts") -> NativeGraph:
    """Capture a consistent diagnostic export, then build a disposable projection.

    The returned graph describes that revision, never a current authorization.
    It can be rebuilt from checked journal replay after a projection failure.
    """
    authority, snapshot, views = service.export_admission(context_id)
    projection = RecordProjection()
    projection.add((authority, snapshot, views))
    return projection.batch.run(root)
