"""Pure evaluation of grounded requirements against an explicit belief snapshot."""
from __future__ import annotations

from dataclasses import asdict, dataclass

from .logic import check_consistency
from .model import Check, ContextSnapshot, Literal, Status, conjunction, identity, nonempty

SUPPORTED = frozenset(("FACT", "AND", "OR", "ALWAYS"))


@dataclass(frozen=True, slots=True)
class Requirement:
    operator: str
    literal: Literal | None = None
    children: tuple[Requirement, ...] = ()

    def __post_init__(self):
        nonempty(self.operator)
        object.__setattr__(self, "children", tuple(self.children))
        if any(not isinstance(child, Requirement) for child in self.children):
            raise ValueError("requirement children must be typed expressions")
        if self.literal is not None and not isinstance(self.literal, Literal):
            raise ValueError("requirement fact must be a grounded literal")
        if self.operator == "FACT" and (self.literal is None or self.children):
            raise ValueError("FACT requires exactly one literal")
        if self.operator in ("AND", "OR") and (self.literal is not None or not self.children):
            raise ValueError("AND/OR require a nonempty group without a literal")
        if self.operator == "ALWAYS" and (self.literal is not None or self.children):
            raise ValueError("ALWAYS has no arguments")


@dataclass(frozen=True, slots=True)
class RequirementWitness:
    path: tuple[int, ...]
    context_id: str
    literal: Literal
    belief_revision_id: str
    evidence_ids: tuple[str, ...]
    lineage_roots: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RequirementResult:
    status: Status
    witnesses: tuple[RequirementWitness, ...]
    selected_branches: tuple[tuple[tuple[int, ...], int], ...]
    checks: tuple[Check, ...]
    context_id: str
    knowledge_revision: int
    policy_revision: str
    logical_time: int
    support_fingerprint: str


def validate_requirement(requirement: Requirement) -> Status:
    if not isinstance(requirement, Requirement):
        return Status.UNKNOWN
    pending, count = [(requirement, 0)], 0
    while pending:
        node, depth = pending.pop()
        count += 1
        if count > 256 or depth > 32 or node.operator not in SUPPORTED:
            return Status.UNKNOWN
        pending.extend((child, depth + 1) for child in node.children)
    return Status.PASS


def requires_evidence(requirement: Requirement) -> bool:
    """True only when every supported satisfying branch needs at least one fact."""
    if requirement.operator == "FACT":
        return True
    if requirement.operator == "AND":
        return any(requires_evidence(child) for child in requirement.children)
    if requirement.operator == "OR":
        return all(requires_evidence(child) for child in requirement.children)
    return False


def evaluate(requirement: Requirement, snapshot: ContextSnapshot, *,
             max_variables: int = 16) -> RequirementResult:
    def visit(node, path):
        name = "requirement:" + ".".join(map(str, path))
        if node.operator == "ALWAYS":
            return Status.PASS, (), (), (Check(name, Status.PASS, "explicit unconditional requirement"),)
        if node.operator == "FACT":
            matches = sorted((belief for belief in snapshot.usable
                              if belief.context_id == snapshot.context_id and belief.conclusion == node.literal),
                             key=lambda belief: belief.belief_revision_id)
            if matches:
                belief = matches[0]
                witness = RequirementWitness(path, snapshot.context_id, node.literal,
                                             belief.belief_revision_id, belief.proposal.evidence_ids,
                                             belief.proposal.lineage_roots)
                return Status.PASS, (witness,), (), (Check(name, Status.PASS, "exact usable belief revision"),)
            contrary = any(b.context_id == snapshot.context_id and b.conclusion == node.literal.negate()
                           for b in snapshot.usable)
            status = Status.FAIL if contrary else Status.UNKNOWN
            return status, (), (), (Check(name, status, "contrary support" if contrary else "missing support"),)
        results = [visit(child, path + (index,)) for index, child in enumerate(node.children)]
        if node.operator == "OR":
            for index, result in enumerate(results):
                if result[0] is Status.PASS:
                    return result[0], result[1], ((path, index),) + result[2], result[3]
            status = Status.FAIL if all(r[0] is Status.FAIL for r in results) else Status.UNKNOWN
            return status, (), (), tuple(check for result in results for check in result[3])
        status = conjunction(tuple(Check(str(i), result[0], "AND member")
                                   for i, result in enumerate(results)))
        return (status, tuple(w for r in results for w in r[1]),
                tuple(branch for r in results for branch in r[2]),
                tuple(check for r in results for check in r[3]))

    supported = validate_requirement(requirement) is Status.PASS
    if not supported:
        status, witnesses, branches, checks = (Status.UNKNOWN, (), (),
            (Check("supported_scope", Status.UNKNOWN, "unsupported operator or expression capacity"),))
    else:
        status, witnesses, branches, checks = visit(requirement, ())
        if status is Status.PASS:
            # Include the entire accepted state and constraint index. A selected
            # branch is never a reason to omit a mandatory unrelated constraint.
            joint = check_consistency(snapshot.constraints, snapshot.assumptions + tuple(
                belief.conclusion for belief in snapshot.usable), max_variables=max_variables)
            checks += (Check("joint_requirements", joint.status, joint.detail),)
            status = joint.status
    if status is not Status.PASS:
        # Partial witnesses are diagnostics, never a bundle authorized for use.
        witnesses, branches = (), ()
    binding = (asdict(requirement) if supported else "unsupported", snapshot.context_id,
               snapshot.knowledge_revision, snapshot.policy_revision,
               snapshot.logical_time, [asdict(w) for w in witnesses], branches)
    return RequirementResult(status, witnesses, branches, checks, snapshot.context_id,
                             snapshot.knowledge_revision, snapshot.policy_revision,
                             snapshot.logical_time, identity("requirement-support/v1", binding))
