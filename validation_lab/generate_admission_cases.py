"""Reproducible development controls for the bounded admission trace profile."""
from hashlib import sha256
import json
from pathlib import Path
from random import Random

from reachability.admission_protocol import AdmissionInitial, event

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "validation_lab" / "admission_cases"


def initial():
    return AdmissionInitial.parse(dict(schema="admission-initial/v1", atoms=["a0", "a1", "a2", "a3"], rules=[
        dict(rule_id="r0", revision="1", premises=[1, 2], conclusion=3),
        dict(rule_id="r1", revision="1", premises=[3], conclusion=4),
        dict(rule_id="r2", revision="1", premises=[1], conclusion=3),
        dict(rule_id="r3", revision="1", premises=[2], conclusion=3)]))


def op(kind, **args):
    return kind, args


def context(ctx="c0", assumptions=(), clauses=()):
    return op("context", context_id=ctx, assumptions=list(assumptions), clauses=list(map(list, clauses)))


def evidence(lit, *, ctx="c0", root="s0", until=None, truth=None):
    args = dict(context_id=ctx, literal=lit, roots=[root], valid_until=until)
    if truth is not None:
        args.update(strength=truth[0], confidence=truth[1])
    return op("evidence" if truth is None else "estimate", **args)


def derive(rule, *refs, ctx="c0"):
    return op("derive", context_id=ctx, rule_id=rule, premises=list(refs))


def tick(time, ctx="c0"):
    return op("tick", context_id=ctx, time=time)


def policy(clauses, ctx="c0", revision="h2"):
    return op("policy", context_id=ctx, revision=revision, clauses=clauses)


def adopt(ref, ctx="c0"):
    return op("adopt", context_id=ctx, evidence_id=ref)


def independence(*refs, ctx="c0", model="m0"):
    return op("independence", context_id=ctx, model_id=model, premises=list(refs), justification="declared-study")


def revise(*refs, ctx="c0", model="m0"):
    return op("revise", context_id=ctx, model_id=model, premises=list(refs))


def make_case(name, family, control, rows, checkpoints=()):
    messages = []
    def ref(value):
        return f"e{value:03}" if type(value) is int else value
    for index, (kind, a) in enumerate(rows):
        a = dict(a)
        if "premises" in a:
            a["premises"] = list(map(ref, a["premises"]))
        if "evidence_id" in a:
            a["evidence_id"] = ref(a["evidence_id"])
        messages.append(event(f"e{index:03}", kind, **a))
    return dict(schema="admission-case/v1", case_id=name, parent_instance_id="admission-parent-0", split="development",
                family=family, control=control, family_complete=False, events=messages,
                checkpoints=[dict(step=s, path=p, expected=v) for s, p, v in checkpoints])


def scenarios():
    cases = []
    def case(family, control, rows, checkpoints):
        cases.append(make_case(f"a{len(cases)+1:02}", family, control, rows, checkpoints))
    base = [context(), evidence(1), evidence(2, root="s1")]
    case("F01", "positive", [*base, derive("r0", 1, 2), derive("r1", 3), adopt(1), derive("r0", 5, 2)],
         [(5, "projection.contexts.c0.hard.4", "PASS"), (7, "projection.aliases.hard.e006", "e003")])
    case("F01", "blocked", [context(), evidence(1), evidence(4), derive("r0", 1), derive("r0", 1, 2),
         derive("r0", 2, 1), derive("r0", "absent", 1)],
         [(4, "outcome.status", "UNKNOWN"), (5, "outcome.status", "FAIL"), (7, "outcome.status", "FAIL")])
    case("F01", "boundary", [context(), evidence(1, until=3), evidence(2), tick(2), derive("r0", 1, 2), tick(3),
         derive("r0", 1, 2), evidence(1, root="s2"), derive("r0", 7, 2)],
         [(5, "outcome.status", "PASS"), (7, "outcome.status", "STALE"), (9, "projection.hard.e004.current", False)])
    change = op("rule", rule=dict(rule_id="r0", revision="2", premises=[1, 4], conclusion=3), expected_revision="1")
    case("F01", "revision_change", [*base, derive("r0", 1, 2), derive("r1", 3), change,
         evidence(4), derive("r0", 1, 6), change],
         [(6, "projection.hard.e004.current", False), (8, "outcome.status", "PASS"), (9, "outcome.status", "STALE")])
    constrained = context(clauses=[[-1, -2]])
    case("F02", "positive", [constrained, evidence(1), evidence(-2), derive("r2", 1)],
         [(4, "outcome.status", "PASS"), (4, "projection.contexts.c0.hard.-2", "PASS")])
    case("F02", "blocked", [constrained, evidence(1), evidence(2), adopt(2), evidence(2, truth=(.75, .5)), derive("r0", 1, 2)],
         [(3, "outcome.status", "FAIL"), (5, "projection.contexts.c0.hard.2", "UNKNOWN"),
          (5, "projection.contexts.c0.numeric.2", "PASS"), (6, "outcome.status", "UNKNOWN")])
    case("F02", "boundary", [constrained, evidence(1, until=2), evidence(2), tick(1), adopt(2), tick(2), adopt(2)],
         [(5, "outcome.status", "FAIL"), (7, "outcome.status", "PASS")])
    case("F02", "revision_change", [*base, derive("r0", 1, 2), policy([[-1, -2]]), adopt(1), adopt(2)],
         [(5, "projection.contexts.c0.hard.1", "STALE"), (5, "projection.contexts.c0.hard.2", "STALE"),
          (6, "outcome.status", "PASS"), (7, "outcome.status", "FAIL")])
    case("F04", "positive", [context(assumptions=[1]), context("c1", assumptions=[-1]), evidence(2),
         evidence(2, ctx="c1"), derive("r3", 2), derive("r3", 3, ctx="c1")],
         [(6, "projection.contexts.c0.hard.3", "PASS"), (6, "projection.contexts.c1.hard.3", "PASS")])
    case("F04", "blocked", [context(), context("c1"), evidence(1), evidence(2, ctx="c1"), derive("r0", 2, 3), adopt(2, "c1"),
         evidence(1, truth=(.25, .5)), evidence(1, ctx="c1", truth=(.75, .5)), independence(6, 7), revise(6, 7)],
         [(5, "outcome.status", "FAIL"), (6, "outcome.status", "FAIL"), (9, "outcome.status", "FAIL"), (10, "outcome.status", "FAIL")])
    case("F04", "boundary", [context(), context("c1"), evidence(2, until=2), evidence(2, ctx="c1", until=2), tick(2),
         derive("r3", 3, ctx="c1"), tick(2, "c1"), derive("r3", 3, ctx="c1")],
         [(6, "outcome.status", "PASS"), (6, "projection.contexts.c0.hard.2", "STALE"), (8, "outcome.status", "STALE")])
    case("F04", "revision_change", [context(), context("c1"), evidence(2), evidence(2, ctx="c1"),
         derive("r3", 2), derive("r3", 3, ctx="c1"), policy([[-2]]),
         op("rule", rule=dict(rule_id="r3", revision="2", premises=[2], conclusion=4), expected_revision="1"),
         derive("r3", 3, ctx="c1")],
         [(7, "projection.hard.e004.current", False), (7, "projection.hard.e005.current", True),
          (8, "projection.hard.e005.current", False), (9, "projection.contexts.c1.hard.4", "PASS")])
    numeric = [context(), evidence(1, root="s0", truth=(.25, .5)), evidence(1, root="s1", truth=(.75, .5))]
    case("F05", "positive", [*numeric, revise(1, 2, model=None), independence(1, 2), revise(1, 2), revise(2, 1)],
         [(4, "outcome.status", "UNKNOWN"), (6, "projection.numeric.e005.strength", .5),
          (6, "projection.numeric.e005.confidence", 2/3), (7, "projection.aliases.numeric.e006", "e005")])
    case("F05", "blocked", [context(), evidence(1, truth=(.25, .5)), evidence(1, truth=(.75, .5)), independence(1, 2),
         revise(1, 2), evidence(1), evidence(2), derive("r2", 5), derive("r3", 6), derive("r1", 7), derive("r1", 8),
         op("revoke", evidence_id=5)],
         [(5, "outcome.status", "UNKNOWN"), (12, "projection.hard.e009.current", False),
          (12, "projection.hard.e010.current", True), (12, "projection.hard.e010.roots", ["s0"])])
    case("F05", "boundary", [context(), evidence(1, truth=(.25, 0)), evidence(1, root="s1", truth=(.75, 0)),
         independence(1, 2), revise(1, 2), evidence(1, root="s2", truth=(.5, .5)),
         independence(1, 5, model="m1"), revise(1, 5, model="m1")],
         [(5, "outcome.status", "UNKNOWN"), (8, "projection.numeric.e007.confidence", .5)])
    case("F05", "revision_change", [*numeric, independence(1, 2), revise(1, 2),
         op("revoke_model", context_id="c0", model_id="m0"), revise(1, 2), independence(1, 2, model="m1"),
         revise(1, 2, model="m1"), op("revoke", evidence_id=1), policy([])],
         [(6, "projection.numeric.e004.current", False), (7, "outcome.status", "STALE"),
          (9, "outcome.status", "PASS"), (10, "projection.numeric.e008.current", False),
          (10, "projection.numeric.e002.current", True), (11, "projection.numeric.e002.current", False)])
    return cases


def generated_scenarios(seed=17041, count=8):
    rng = Random(seed)
    cases = []
    for i in range(count):
        rows = [context(), context("c1"), evidence(1, until=rng.choice((None, 2))), evidence(2, root="s1"),
                derive("r0", 2, 3), derive("r1", 4), evidence(1, root="s2"), derive("r2", 6), derive("r1", 7)]
        rows += [evidence(1, root="s3", truth=(rng.random(), rng.choice((0, .1, .5, .9)))),
                 evidence(1, root=rng.choice(("s3", "s4")), truth=(rng.random(), rng.choice((0, .2, .5, .8)))),
                 independence(9, 10), revise(9, 10), tick(rng.choice((1, 2, 3))), op("revoke", evidence_id=rng.choice((2, 3, 6, 9))),
                 derive("r0", 2, 3), derive("r1", rng.choice((4, 7))), revise(9, 10),
                 policy(rng.choice(([], [[-1]], [[-1, -2]]))), adopt(6), op("restart")]
        cases.append(make_case(f"generated-{seed}-{i}", "composite", "stateful", rows))
    return cases


def write():
    files = {CORPUS / "public" / "initial.json": initial().wire()}
    cases = scenarios()
    files.update({CORPUS / "evaluator" / (c["case_id"]+".json"): c for c in cases})
    for path, data in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2)+"\n")
    sources = ["validation_lab/"+name+".py" for name in ("admission_oracle", "generate_admission_cases", "run_admission",
                                                         "run_deployment", "mutations")]
    sources += [str(p.relative_to(ROOT)) for p in sorted((ROOT / "reachability").glob("*.py"))]
    manifest = dict(schema="admission-corpus/v1", split="development", parent_instance_id="admission-parent-0",
        case_count=len(cases), event_prefixes=sum(len(c["events"]) for c in cases),
        fixture_files={str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in sorted(files)},
        source_files={p: sha256((ROOT / p).read_bytes()).hexdigest() for p in sources},
        control_coverage={family: {c["control"]: c["case_id"] for c in cases if c["family"] == family}
                          for family in sorted({c["family"] for c in cases})},
        family_complete_fixtures=0, target_family_complete_fixtures=64,
        scope="grounded finite admission mechanisms only; no goals, search, inheritance or family-completeness claim")
    (CORPUS / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")


if __name__ == "__main__":
    write()
