"""Reproduce the development-only deployment corpus and its source receipts."""
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
from random import Random

from reachability.trace_protocol import DeploymentInitial, event

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "validation_lab" / "deployment_cases"


def scenarios():
    cases = []
    def case(name, controls, body, checkpoints=()):
        messages = []
        for index, (kind, arguments) in enumerate(body):
            # References use descriptive construction labels here, but the public
            # events receive opaque IDs independent of their success or failure.
            arguments = dict(arguments)
            if "evidence_id" in arguments and type(arguments["evidence_id"]) is int:
                arguments["evidence_id"] = f"e{arguments['evidence_id']:03}"
            messages.append(event(f"e{index:03}", kind, **arguments))
        cases.append(dict(schema="deployment-case/v1", case_id=name, parent_instance_id="deployment-parent-0",
            split="development", controls=controls, events=messages,
            checkpoints=[dict(step=step, path=path, expected=expected) for step, path, expected in checkpoints]))

    def op(kind, **args):
        return kind, args
    def fact(name, expiry=None):
        return op("fact", name=name, valid_until=expiry)
    def forecast(strength=.8, confidence=.8, expiry=None):
        return op("forecast", strength=strength, confidence=confidence, valid_until=expiry)
    def attempt(kind, name="a0", **args):
        return op(kind, attempt_id=name, **args)
    def observed(milestone, product="p0"):
        return attempt("observation", milestone=milestone, product_id=product)
    def sample(healthy=True):
        return op("sample", healthy=healthy)
    ready = [fact("tested"), fact("credential"), forecast(), attempt("attempt"), attempt("reserve")]
    healthy = [op("tick", time=1), fact("product"), observed("completion_observed"),
               observed("exact_product_observed"), sample(), op("tick", time=2), sample(), op("tick", time=3), sample()]
    case("d01", ["F10:valid", "F12:failure-after-success", "F14:expiry"],
        [fact("tested"), fact("credential", 1), forecast(expiry=1), attempt("attempt"), attempt("reserve"),
         attempt("cover", units=6, valid_until=10), attempt("dispatch", fault="none"), *healthy,
         op("account"), attempt("complete"), attempt("release"), op("restart"), op("tick", time=4), sample(False), op("account")],
        [(7, "projection.goal.outstanding", 10), (16, "projection.goal.outstanding", 0),
         (18, "projection.stage", "BUILT"), (23, "projection.goal.outstanding", 10)])
    case("d02", ["F01:missing", "F08:revocation-and-alternative"],
        [fact("tested"), forecast(), attempt("attempt"), attempt("reserve"), fact("credential"), attempt("reserve"),
         op("revoke", evidence_id=4), attempt("dispatch", fault="none"), fact("credential"),
         attempt("dispatch", fault="none"), op("restart")],
        [(4, "outcome.status", "UNKNOWN"), (8, "outcome.status", "UNKNOWN"),
         (10, "instrumentation.executor_effects", 1)])
    case("d03", ["F10:lost-acknowledgement", "F16:recovery"],
        [*ready, attempt("cover", units=6, valid_until=10), attempt("dispatch", fault="lost_reply"), op("restart"),
         op("revoke", evidence_id=2), attempt("reconcile"), attempt("dispatch", fault="none"), attempt("release")],
        [(7, "projection.attempts.a0.dispatch.state", "uncertain"), (7, "projection.goal.outstanding", 10),
         (10, "projection.attempts.a0.dispatch.state", "accepted"), (11, "instrumentation.executor_effects", 1)])
    case("d04", ["F10:wrong-product", "F10:delayed-outcome"],
        [*ready, attempt("dispatch", fault="none"), op("tick", time=1), fact("product"), observed("completion_observed"),
         observed("exact_product_observed", "p00"), sample(), op("tick", time=2), sample(), op("tick", time=3), sample(),
         attempt("complete"), observed("exact_product_observed"), attempt("complete")],
        [(10, "outcome.status", "FAIL"), (16, "outcome.status", "UNKNOWN"), (18, "projection.stage", "BUILT")])
    case("d05", ["F09:capacity", "F10:uncertain-occupancy", "F16:prepared-recovery"],
        [*ready, attempt("attempt", "a1"), attempt("reserve", "a1"), attempt("prepare"), op("restart"),
         op("tick", time=10), attempt("reserve", "a1"), attempt("release"), attempt("reserve", "a1"),
         attempt("dispatch", "a1", fault="none")],
        [(7, "outcome.status", "FAIL"), (11, "outcome.status", "UNKNOWN"), (13, "outcome.status", "PASS"),
         (14, "instrumentation.executor_effects", 1)])
    case("d06", ["F14:boundary", "F08:new-alternative", "F10:revision-change"],
        [fact("tested"), fact("credential"), forecast(strength=.6499999999999999), attempt("attempt"), attempt("reserve"),
         op("revoke", evidence_id=2), forecast(strength=.65, confidence=.3499999999999999), attempt("reserve"),
         op("revoke", evidence_id=6), forecast(strength=.65, confidence=.35), attempt("reserve"),
         forecast(), attempt("dispatch", fault="none"), op("tick", time=10), attempt("attempt", "a1"),
         attempt("reserve", "a1"), attempt("dispatch", "a1", fault="none")],
        [(5, "outcome.status", "FAIL"), (8, "outcome.status", "UNKNOWN"),
         (11, "outcome.status", "PASS"), (13, "outcome.status", "STALE")])
    case("d07", ["F12:censoring", "F12:new-monitor-window"],
        [fact("product"), sample(), op("censor"), sample(), op("account"), op("tick", time=1), op("resume"), sample(),
         op("tick", time=2), sample(), op("tick", time=3), sample(), op("account")],
        [(3, "projection.goal.label", "CENSORED"), (4, "outcome.status", "STALE"),
         (12, "projection.goal.outstanding", 0)])
    case("d08", ["F12:freshness", "F08:sample-revocation", "F11:overlapping-promises"],
        [*ready, attempt("cover", units=6, valid_until=10), attempt("cover", units=8, valid_until=10),
         attempt("dispatch", fault="none"), *healthy, op("account"), op("revoke", evidence_id=12), op("account"),
         op("tick", time=4), sample(), op("tick", time=5), sample(), op("tick", time=6), sample(),
         op("account"), op("tick", time=7), op("account")],
        [(7, "projection.goal.covered", 8), (18, "projection.goal.outstanding", 0),
         (20, "projection.goal.outstanding", 10), (27, "projection.goal.outstanding", 0),
         (29, "projection.goal.outstanding", 10)])
    return cases


def generated_scenarios(seed=8417, count=12):
    """Bounded stateful development cases; no outcome-based rejection or filtering."""
    rng = Random(seed)
    generated = []
    for case_index in range(count):
        rows = []
        def add(kind, **args):
            rows.append(event(f"e{len(rows):03}", kind, **args))
        add("fact", name="tested", valid_until=None)
        add("fact", name="credential", valid_until=rng.choice((None, 2)))
        add("forecast", strength=.8, confidence=.8, valid_until=None)
        add("attempt", attempt_id="a0")
        add("reserve", attempt_id="a0")
        add("cover", attempt_id="a0", units=6, valid_until=10)
        add("dispatch", attempt_id="a0", fault=rng.choice(("none", "lost_reply", "before_effect")))
        censored = False
        for time in range(1, 5):
            add("tick", time=time)
            if time == 1:
                add("fact", name="product", valid_until=None)
                add("reconcile", attempt_id="a0")
            if time == 2 and rng.randrange(3) == 0:
                add("censor")
                censored = True
            if time == 3 and censored:
                add("resume")
            observation = rng.choice((True, False, None))
            if observation is not None:
                add("sample", healthy=observation)
            add("account")
        add("complete", attempt_id="a0")
        generated.append(dict(schema="deployment-case/v1", case_id=f"generated-{seed}-{case_index}",
            parent_instance_id="deployment-parent-0", split="development", controls=["stateful-development"],
            events=rows, checkpoints=[]))
    return generated


def write():
    public, evaluator = CORPUS / "public", CORPUS / "evaluator"
    public.mkdir(parents=True, exist_ok=True)
    evaluator.mkdir(parents=True, exist_ok=True)
    files = {public / "initial.json": asdict(DeploymentInitial())}
    files.update({evaluator / (case["case_id"] + ".json"): case for case in scenarios()})
    for path, value in files.items():
        path.write_text(json.dumps(value, indent=2) + "\n")
    sources = ["validation_lab/deployment_oracle.py", "validation_lab/generate_deployment_cases.py",
               "validation_lab/run_deployment.py", "validation_lab/mutations.py"]
    sources += [str(p.relative_to(ROOT)) for p in sorted((ROOT / "reachability").glob("*.py"))]
    receipt = dict(schema="deployment-corpus/v1", split="development", parent_instance_id="deployment-parent-0",
        case_count=len(files)-1, event_prefixes=sum(len(c["events"]) for c in scenarios()),
        fixture_files={str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in sorted(files)},
        source_files={p: sha256((ROOT / p).read_bytes()).hexdigest() for p in sources},
        family_complete_fixtures=0, target_family_complete_fixtures=64,
        scope="bounded deployment conformance; partial family coverage; no performance or calibration claim")
    (CORPUS / "manifest.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    write()
