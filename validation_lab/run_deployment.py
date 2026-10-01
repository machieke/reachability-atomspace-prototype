"""Evaluator-owned schedules, cold references and unmodified actual trace capture."""
import argparse
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from reachability.deployment_trace import DeploymentSession
from reachability.trace_protocol import DeploymentInitial, canonical, fingerprint
from .deployment_oracle import reference_prefix

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "validation_lab" / "deployment_cases"


class ConformanceMismatch(AssertionError):
    def __init__(self, event_id, path, expected, actual):
        self.event_id, self.path, self.expected, self.actual = event_id, path, expected, actual
        super().__init__(f"{event_id}: {path}: expected {expected!r}, actual {actual!r}")


def compare(expected, actual, event_id, path="projection"):
    if isinstance(expected, dict) and isinstance(actual, dict) and set(expected) == set(actual):
        for key in expected:
            compare(expected[key], actual[key], event_id, path + "." + key)
    elif expected != actual:
        raise ConformanceMismatch(event_id, path, expected, actual)


def at(value, path):
    for key in path.split("."):
        value = value[key]
    return value


def verify_corpus(*, corpus=None, schema="deployment-corpus/v1", loader=None):
    corpus = CORPUS if corpus is None else corpus
    manifest = json.loads((corpus / "manifest.json").read_text())
    if manifest.get("schema") != schema:
        raise ValueError("unsupported corpus schema")
    actual_files = {str(path.relative_to(ROOT)) for directory in ("public", "evaluator")
                    for path in (corpus / directory).rglob("*.json")}
    if actual_files != set(manifest["fixture_files"]):
        raise ValueError("corpus contains missing or unlisted fixture files")
    for section in ("fixture_files", "source_files"):
        for name, expected in manifest[section].items():
            if sha256((ROOT / name).read_bytes()).hexdigest() != expected:
                raise ValueError("corpus/source receipt mismatch: " + name)
    _, cases = (load_cases if loader is None else loader)()
    if (len(cases) != manifest["case_count"] or sum(len(c["events"]) for c in cases) != manifest["event_prefixes"]
            or any(c["split"] != manifest["split"] or c["parent_instance_id"] != manifest["parent_instance_id"] for c in cases)):
        raise ValueError("corpus counts or split ancestry differ from the receipt")
    return manifest


def load_cases():
    initial = DeploymentInitial.parse(json.loads((CORPUS / "public" / "initial.json").read_text()))
    cases = [json.loads(path.read_text()) for path in sorted((CORPUS / "evaluator").glob("*.json"))]
    return initial, cases


def run_case(initial, case, *, restart_every_prefix=True, trace_path=None,
             session_factory=DeploymentSession, reference=reference_prefix):
    # Only public initial data enters the runtime constructor. Future events and
    # checkpoint labels stay here and are never passed to service/checker methods.
    events, records = case["events"], []
    output = open(trace_path, "w") if trace_path is not None else None
    try:
        public_initial = initial.wire() if hasattr(initial, "wire") else asdict(initial)
        with TemporaryDirectory() as directory, session_factory(initial, directory) as session:
            compare(reference(public_initial, ())["projection"], session.projection(), "initial")
            for index, message in enumerate(events):
                record = session.apply(message)
                records.append(record)
                if output is not None:
                    output.write(canonical(record) + "\n")
                    output.flush()  # Preserve actual offending output before evaluating it.
                expected = reference(public_initial, events[:index+1])
                compare(expected["status"], record["outcome"]["status"], message["event_id"], "outcome.status")
                compare(expected["projection"], record["projection"], message["event_id"])
                if "executor_effects" in expected:
                    compare(expected["executor_effects"], record["instrumentation"]["executor_effects"],
                            message["event_id"], "instrumentation.executor_effects")
                if fingerprint(record["projection"]) != record["projection_digest"]:
                    raise ValueError("trace projection digest mismatch")
                for checkpoint in case.get("checkpoints", ()):
                    if checkpoint["step"] == index+1:
                        compare(checkpoint["expected"], at(record, checkpoint["path"]), message["event_id"], checkpoint["path"])
                if restart_every_prefix:
                    session.restart()
                    compare(expected["projection"], session.projection(), message["event_id"], "recovered_projection")
                    if "executor_effects" in expected:
                        compare(expected["executor_effects"], session.executor.total_effects,
                                message["event_id"], "recovered_executor_effects")
        return records
    finally:
        if output is not None:
            output.close()


def mutation_witness(initial, case, name, *, trace_path=None, **run_options):
    from .mutations import mutate
    with mutate(name) as canary:
        try:
            run_case(initial, case, restart_every_prefix=False, trace_path=trace_path, **run_options)
        except ConformanceMismatch as error:
            if canary["calls"] == 0:
                raise AssertionError("mutation was not invoked") from error
            prefix = next(i+1 for i, event in enumerate(case["events"]) if event["event_id"] == error.event_id)
            return dict(mutant=name, detected=True, case_id=case["case_id"], first_divergent_prefix=prefix,
                        event_id=error.event_id, path=error.path, expected=error.expected, actual=error.actual,
                        invocations=canary["calls"])
    return dict(mutant=name, detected=False, case_id=case["case_id"])


def main():
    parser = argparse.ArgumentParser(description="Run the development deployment conformance corpus.")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "deployment-validation")
    args = parser.parse_args()
    manifest = verify_corpus()
    initial, cases = load_cases()
    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    for case in cases:
        entry = dict(case_id=case["case_id"], scheduled_prefixes=len(case["events"]), status="PASS")
        try:
            records = run_case(initial, case, trace_path=args.output / (case["case_id"] + ".jsonl"))
            entry["compared_prefixes"] = len(records)
            entry["recovered_prefixes"] = len(records)
        except Exception as error:
            entry.update(status="FAIL", error_type=type(error).__name__, error=str(error))
            trace = args.output / (case["case_id"] + ".jsonl")
            entry["recorded_prefixes"] = len(trace.read_text().splitlines()) if trace.exists() else 0
        results.append(entry)
    mutants = []
    for name, case_id in (("M06", "d01"), ("M11", "d07")):
        if not any(r["case_id"] == case_id and r["status"] == "PASS" for r in results):
            mutants.append(dict(mutant=name, detected=False, error="unmodified control did not pass"))
            continue
        try:
            mutants.append(mutation_witness(initial, next(c for c in cases if c["case_id"] == case_id), name,
                                            trace_path=args.output / (name + ".jsonl")))
        except Exception as error:
            mutants.append(dict(mutant=name, detected=False, error_type=type(error).__name__, error=str(error)))
    report = dict(schema="deployment-validation-report/v1", mode="conformance", corpus=manifest,
                  results=results, mutants=mutants, family_complete_fixtures=0, closed_loop=False, performance_comparison=False)
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(dict(cases=len(results), prefixes=manifest["event_prefixes"],
        passed=sum(r["status"] == "PASS" for r in results), report=str(args.output / "report.json")), indent=2))
    if any(r["status"] != "PASS" for r in results) or any(not m["detected"] for m in mutants):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
