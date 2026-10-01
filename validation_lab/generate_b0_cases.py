"""Development-only closed-loop worlds. Future observations remain evaluator data."""
from copy import deepcopy
from dataclasses import asdict, replace
from hashlib import sha256
import json
from pathlib import Path
from random import Random

from reachability.b0 import B0Public, Budget, Probe
from reachability.trace_protocol import event

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "validation_lab" / "b0_cases"


def world():
    return dict(schema="deployment-b0-world/v1", probes={
        "q0": {}, "q1": {}, "q2": dict(strength=.8, confidence=.8),
        "q3": dict(delay=1), "q4": {}}, dispatch_faults=[], initial_events=[], hooks=[])


def scenarios():
    cases = []
    def case(world, controls, *, public=None, budget=None, completed=True, effects=1, selected=()):
        cases.append(dict(schema="deployment-b0-case/v1", case_id=f"b{len(cases)+1:02}",
            parent_instance_id="deployment-b0-parent-0", split="development", controls=controls,
            public=(public or B0Public()).wire(), budget=asdict(budget or Budget()), world=deepcopy(world),
            expected=dict(completed=completed, effects=effects, required_actions=list(selected))))
    case(world(), ["F01:positive", "F10:positive", "F12:delayed"], selected=("observe", "attempt", "reserve", "dispatch", "complete", "release"))
    w = world()
    w["probes"]["q0"] = None
    w["probes"]["q5"] = {}
    public = replace(B0Public(), probes=B0Public().probes+(Probe("q5", "tested", 3),))
    case(w, ["F01:blocked-cheap-observation", "F03:observation-alternative"], public=public)
    w = world()
    w["probes"]["q1"] = dict(available_at=2)
    case(w, ["F01:delayed-prerequisite"], selected=("wait",))
    w = world()
    w["dispatch_faults"] = ["lost_reply"]
    case(w, ["F10:lost-acknowledgement", "F16:recovery"], selected=("reconcile",))
    w = world()
    w["dispatch_faults"] = ["before_effect"]
    case(w, ["F10:pre-effect-failure", "F10:idempotent-retry"], selected=("reconcile", "dispatch"))
    w = world()
    w["hooks"] = [dict(kind="dispatch", occurrence=1, events=[dict(kind="revoke", arguments=dict(evidence_id="latest:credential"))])]
    case(w, ["F08:revocation-after-selection", "F14:lease-expiry"], public=replace(B0Public(), deployment=replace(B0Public().deployment, lease_duration=2)))
    w = world()
    w["probes"]["q3"]["wrong_until"] = 3
    case(w, ["F10:wrong-product-then-correct"], selected=("wait",))
    w = world()
    w["probes"]["q4"]["healthy_after"] = 3
    case(w, ["F12:negative-then-healthy-observation"])
    w = world()
    w["probes"]["q1"] = None
    case(w, ["F01:unavailable-prerequisite"], budget=Budget(actions=12), completed=False, effects=0)
    case(world(), ["F13:observation-cost-exhaustion"], budget=Budget(observation_cost=2), completed=False, effects=0)
    case(world(), ["F13:candidate-visit-exhaustion"], budget=Budget(candidate_visits=2), completed=False, effects=0)
    w = world()
    w["probes"]["q4"]["missing_at"] = [2, 3]
    case(w, ["F12:missing-samples", "F14:exclusive-freshness"])
    return cases


def minimal_product_case():
    return dict(schema="deployment-case/v1", case_id="b0-m07", parent_instance_id="deployment-b0-parent-0",
        split="development", controls=["M07:deletion-minimal"], events=[
            event("m0", "attempt", attempt_id="a0"),
            event("m1", "observation", attempt_id="a0", milestone="exact_product_observed", product_id="p00")],
        checkpoints=[dict(step=2, path="outcome.status", expected="FAIL")])


def generated_scenarios(seed=2601, count=6):
    rng, cases = Random(seed), []
    for i in range(count):
        w = world()
        w["probes"]["q0"] = dict(available_at=rng.randrange(3))
        w["probes"]["q1"] = dict(available_at=rng.randrange(3))
        w["probes"]["q3"]["delay"] = rng.randrange(1, 4)
        w["probes"]["q4"]["healthy_after"] = rng.randrange(4)
        w["dispatch_faults"] = [rng.choice(("none", "lost_reply", "before_effect"))]
        cases.append(dict(schema="deployment-b0-case/v1", case_id=f"generated-{seed}-{i}",
            parent_instance_id="deployment-b0-parent-0", split="development", controls=["seeded-closed-loop"],
            public=B0Public().wire(), budget=asdict(Budget(actions=40)), world=w,
            expected=dict(completed=True, effects=1, required_actions=[])))
    return cases


def write():
    cases = scenarios()
    # Capability/cost descriptions are public; worlds, stopping checks and family
    # labels never enter the controller's constructor or candidate interface.
    files = {CORPUS / "public" / (c["case_id"]+".json"): c["public"] for c in cases}
    files.update({CORPUS / "evaluator" / (c["case_id"]+".json"): {k: v for k, v in c.items() if k != "public"} for c in cases})
    files[CORPUS / "mutations" / "M07.json"] = minimal_product_case()
    for path, value in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2)+"\n")
    sources = ["validation_lab/"+name+".py" for name in ("b0_environment", "generate_b0_cases", "run_b0", "deployment_oracle", "run_deployment", "mutations")]
    sources += [str(p.relative_to(ROOT)) for p in sorted((ROOT / "reachability").glob("*.py"))]
    manifest = dict(schema="deployment-b0-corpus/v1", split="development", parent_instance_id="deployment-b0-parent-0",
        case_count=len(cases), fixture_files={str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in sorted(files)},
        source_files={p: sha256((ROOT / p).read_bytes()).hexdigest() for p in sources},
        family_complete_fixtures=0, closed_loop=True, comparative_performance=False,
        scope="one deployment dependency graph; fixed capability discovery; no general planning or normalized cost claim")
    (CORPUS / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")


if __name__ == "__main__":
    write()
