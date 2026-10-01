"""Closed-loop bounded B0 episodes; actual traces checked at every event prefix."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from reachability.b0 import B0Controller, B0Public, Budget
from reachability.deployment_trace import DeploymentSession
from reachability.trace_protocol import canonical
from .b0_environment import DeploymentWorld
from .run_deployment import compare
from . import run_deployment

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "validation_lab" / "b0_cases"


def load_cases():
    cases = []
    for path in sorted((CORPUS / "evaluator").glob("*.json")):
        case = json.loads(path.read_text())
        case["public"] = json.loads((CORPUS / "public" / path.name).read_text())
        cases.append(case)
    return cases


def verify_corpus():
    receipt = json.loads((CORPUS / "manifest.json").read_text())
    if receipt["schema"] != "deployment-b0-corpus/v1":
        raise ValueError("unsupported B0 corpus")
    files = {str(p.relative_to(ROOT)) for name in ("public", "evaluator", "mutations") for p in (CORPUS / name).rglob("*.json")}
    if files != set(receipt["fixture_files"]):
        raise ValueError("missing or unlisted B0 fixture")
    for group in ("fixture_files", "source_files"):
        for name, digest in receipt[group].items():
            if sha256((ROOT / name).read_bytes()).hexdigest() != digest:
                raise ValueError("B0 corpus/source receipt mismatch: "+name)
    cases = load_cases()
    if len(cases) != receipt["case_count"] or any(c["split"] != receipt["split"] or
            c["parent_instance_id"] != receipt["parent_instance_id"] for c in cases):
        raise ValueError("B0 split ancestry or count mismatch")
    return receipt


def mutation_witness(*, trace_path=None):
    case = json.loads((CORPUS / "mutations" / "M07.json").read_text())
    initial = B0Public().deployment
    run_deployment.run_case(initial, case)
    result = run_deployment.mutation_witness(initial, case, "M07", trace_path=trace_path)
    return dict(mode="conformance", **result)


def run_case(case, *, trace_path=None, restart_every_prefix=True, controller_factory=B0Controller):
    public = B0Public.parse(case["public"])
    output = open(trace_path, "w") if trace_path else None
    def emit(record):
        if output is not None:
            output.write(canonical(record)+"\n")
            output.flush()
    try:
        with TemporaryDirectory() as directory, DeploymentSession(public.deployment, directory) as session:
            world = DeploymentWorld(session, public, case["world"], emit=emit, restart_every_prefix=restart_every_prefix)
            world.initialize()
            controller = controller_factory(public)
            result = controller.run_budget(world.port(), Budget(**case["budget"]), emit=lambda r: emit(dict(record_type="selection", actual=r)))
            projection = session.projection()
            actual = dict(completed=projection["goal"]["outstanding"] == 0, effects=session.executor.total_effects)
            for key in ("completed", "effects"):
                compare(case["expected"][key], actual[key], case["case_id"], key)
            selected = [r["selected"]["kind"] for r in result["records"]]
            for action in case["expected"]["required_actions"]:
                if action not in selected:
                    raise AssertionError("required observed action missing: "+action)
            # Charge every emitted service event/command/certificate, including
            # rejection and an environment event injected between read and commit.
            work = result["work"]
            compare(sum(r["receipt"]["public_events"] for r in result["records"]), work["public_events"], case["case_id"], "work.public_events")
            compare(sum(r["diagnostics"]["journal_commands"] for r in world.records[len(case["world"].get("initial_events", [])):]),
                    work["admission_journal_commands"], case["case_id"], "work.admission_journal_commands")
            return dict(case_id=case["case_id"], status="PASS", **actual, stop_reason=result["stop_reason"],
                        outstanding_loss=projection["goal"]["outstanding"], accounted_loss=projection["goal"]["accounted_loss"],
                        final_time=projection["logical_time"], stage=projection["stage"], selected=selected,
                        compared_prefixes=len(world.events), recovered_prefixes=world.recovered_prefixes,
                        work=work, elapsed_ns=result["elapsed_ns"], records=result["records"], events=world.events)
    finally:
        if output is not None:
            output.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "b0-validation")
    args = parser.parse_args()
    receipt = verify_corpus()
    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    for case in load_cases():
        path = args.output / (case["case_id"]+".jsonl")
        try:
            result = run_case(case, trace_path=path)
            results.append({k: v for k, v in result.items() if k not in ("records", "events")})
        except Exception as error:
            results.append(dict(case_id=case["case_id"], status="FAIL", error_type=type(error).__name__, error=str(error),
                                recorded_lines=len(path.read_text().splitlines()) if path.exists() else 0))
    try:
        mutant = mutation_witness(trace_path=args.output / "M07.jsonl")
    except Exception as error:
        mutant = dict(mutant="M07", detected=False, error_type=type(error).__name__, error=str(error))
    report = dict(schema="deployment-b0-report/v1", variant="B0-finite-deployment/v1", mode="closed-loop", corpus=receipt,
        results=results, mutants=[mutant], family_complete_fixtures=0, comparative_performance=False, normalized_work_budget=False,
        evaluator_process_isolation=False)
    (args.output / "report.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(dict(cases=len(results), passed=sum(r["status"] == "PASS" for r in results),
                         report=str(args.output / "report.json")), indent=2))
    if any(r["status"] != "PASS" for r in results) or not mutant["detected"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
