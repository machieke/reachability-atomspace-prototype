"""Compare grounded public admission traces against a cold independent model."""
import argparse
from functools import partial
import json
from pathlib import Path

from reachability.admission_protocol import AdmissionInitial
from reachability.admission_trace import AdmissionSession
from .admission_oracle import reference_prefix
from . import run_deployment as common

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "validation_lab" / "admission_cases"


def load_cases():
    initial = AdmissionInitial.parse(json.loads((CORPUS / "public" / "initial.json").read_text()))
    return initial, [json.loads(p.read_text()) for p in sorted((CORPUS / "evaluator").glob("*.json"))]


def verify_corpus():
    manifest = common.verify_corpus(corpus=CORPUS, schema="admission-corpus/v1", loader=load_cases)
    _, cases = load_cases()
    coverage = {family: {c["control"]: c["case_id"] for c in cases if c["family"] == family}
                for family in sorted({c["family"] for c in cases})}
    if coverage != manifest["control_coverage"] or any(c["family_complete"] for c in cases):
        raise ValueError("admission control coverage differs from the receipt")
    return manifest


def run_case(initial, case, *, native=False, **kwargs):
    return common.run_case(initial, case, session_factory=partial(AdmissionSession, native=native),
                           reference=reference_prefix, **kwargs)


def mutation_witness(initial, case, *, trace_path=None, native=False):
    return common.mutation_witness(initial, case, "M05", trace_path=trace_path,
                                   session_factory=partial(AdmissionSession, native=native), reference=reference_prefix)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "admission-validation")
    parser.add_argument("--native", action="store_true", help="use pinned native PeTTa/PLN inference")
    args = parser.parse_args()
    manifest = verify_corpus()
    initial, cases = load_cases()
    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    for case in cases:
        entry = dict(case_id=case["case_id"], scheduled_prefixes=len(case["events"]), status="PASS")
        path = args.output / (case["case_id"]+".jsonl")
        try:
            records = run_case(initial, case, native=args.native, trace_path=path)
            entry.update(compared_prefixes=len(records), recovered_prefixes=len(records))
        except Exception as error:
            entry.update(status="FAIL", error_type=type(error).__name__, error=str(error),
                         recorded_prefixes=len(path.read_text().splitlines()) if path.exists() else 0)
        results.append(entry)
    mutant = dict(mutant="M05", detected=False, error="unmodified control did not pass")
    if any(r["case_id"] == "a14" and r["status"] == "PASS" for r in results):
        try:
            mutant = mutation_witness(initial, next(c for c in cases if c["case_id"] == "a14"),
                                      trace_path=args.output / "M05.jsonl", native=args.native)
        except Exception as error:
            mutant = dict(mutant="M05", detected=False, error_type=type(error).__name__, error=str(error))
    report = dict(schema="admission-validation-report/v1", mode="conformance", native_inference=args.native,
                  corpus=manifest, results=results, mutants=[mutant], family_complete_fixtures=0,
                  closed_loop=False, performance_comparison=False, evaluator_process_isolation=False)
    (args.output / "report.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(dict(cases=len(cases), passed=sum(r["status"] == "PASS" for r in results),
                         prefixes=manifest["event_prefixes"], report=str(args.output / "report.json")), indent=2))
    if any(r["status"] != "PASS" for r in results) or not mutant["detected"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
