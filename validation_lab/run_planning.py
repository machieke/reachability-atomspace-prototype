"""Check complete frozen plans and closed-loop service prefixes independently."""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from reachability.grounded_planning import GroundedController, PlanningPublic, SearchBudget
from reachability.planning_session import PlanningSession
from reachability.trace_protocol import canonical, fingerprint
from .admission_oracle import reference_prefix
from .planning_oracle import exact_plan, verify_plan
from .run_deployment import compare

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "validation_lab" / "planning_cases"


def load_cases():
    cases = []
    for path in sorted((CORPUS / "evaluator").glob("*.json")):
        case = json.loads(path.read_text())
        case["public"] = json.loads((CORPUS / "public" / path.name).read_text())
        cases.append(case)
    return cases


def verify_corpus():
    receipt = json.loads((CORPUS / "manifest.json").read_text())
    if receipt["schema"] != "grounded-planning-corpus/v1":
        raise ValueError("unsupported planning corpus")
    files = {str(p.relative_to(ROOT)) for name in ("public", "evaluator") for p in (CORPUS / name).rglob("*.json")}
    if files != set(receipt["fixture_files"]):
        raise ValueError("missing or unlisted planning fixture")
    required = {str(p.relative_to(ROOT)) for p in (ROOT / "reachability").glob("*.py")}
    if not required <= set(receipt["source_files"]):
        raise ValueError("unlisted runtime source")
    for group in ("fixture_files", "source_files"):
        for name, digest in receipt[group].items():
            if sha256((ROOT / name).read_bytes()).hexdigest() != digest:
                raise ValueError("planning corpus/source receipt mismatch: "+name)
    cases = load_cases()
    if len(cases) != receipt["case_count"] or any(c["split"] != receipt["split"] or c["parent_instance_id"] != receipt["parent_instance_id"] for c in cases):
        raise ValueError("planning split ancestry or count mismatch")
    return receipt


class PlanningWorld:
    def __init__(self, session, hooks=(), *, emit=None, restart_every_prefix=True):
        self.session, self.hooks = session, deepcopy(hooks)
        self.emit, self.restart_every_prefix = emit, restart_every_prefix
        self.events, self.records, self.references = [], [], []
        self.requests = self.recovered_prefixes = 0
        self.snapshot = None
        session.emit = self.on_event

    def log(self, **record):
        if self.emit is not None:
            self.emit(record)

    def on_event(self, message, record):
        self.events.append(deepcopy(message))
        self.records.append(record)
        self.log(record_type="runtime", event=message, actual=record)
        expected = reference_prefix(self.session.public.admission.wire(), self.events)
        compare(expected["status"], record["outcome"]["status"], message["event_id"], "outcome.status")
        compare(expected["projection"], record["projection"], message["event_id"], "projection")
        compare(fingerprint(record["projection"]), record["projection_digest"], message["event_id"], "projection_digest")
        if self.restart_every_prefix:
            self.session.restart()
            compare(expected["projection"], self.session.admission.projection(), message["event_id"], "recovered_projection")
            self.recovered_prefixes += 1

    def on_selection(self, record):
        self.log(record_type="controller", actual=record)
        if record["schema"] != "grounded-controller-step/v1":
            return
        # The full actual proposal is already logged. The independent reference
        # receives exactly the public snapshot, not the controller's result/hooks.
        expected = exact_plan(self.session.public.wire(), self.snapshot)
        self.references.append(expected)
        compare(fingerprint(self.snapshot), record["snapshot_digest"], str(record["step"]), "snapshot_digest")
        if expected["status"] == "NOT_COMPUTED":
            raise ValueError("planning reference did not finish; no exact comparison available")
        if record["status"] == "BUDGET_EXHAUSTED":
            compare(None, record["plan"], str(record["step"]), "budget.plan")
            return
        compare(expected["status"], record["status"], str(record["step"]), "search.status")
        if record["plan"] is not None:
            compare(record["snapshot_digest"], record["plan"]["snapshot_digest"], str(record["step"]), "plan.snapshot_digest")
            objective = verify_plan(self.session.public.wire(), self.snapshot, record["plan"])
            compare(expected["objective"], objective, str(record["step"]), "plan.objective")

    def port(self):
        world = self
        class PublicPort:
            def read(self):
                world.snapshot = world.session.read()
                return deepcopy(world.snapshot)

            def execute(self, plan):
                for hook in world.hooks:
                    if hook["request"] == world.requests:
                        for message in hook["events"]:
                            world.session.observe(message)
                world.requests += 1
                return world.session.execute(plan)
        return PublicPort()


def run_case(case, *, trace_path=None, restart_every_prefix=True, controller_factory=GroundedController):
    public = PlanningPublic.parse(case["public"]["profile"])
    output = open(trace_path, "w") if trace_path else None
    def emit(record):
        if output is not None:
            output.write(canonical(record)+"\n")
            output.flush()
    try:
        with TemporaryDirectory() as directory, PlanningSession(public, directory) as session:
            world = PlanningWorld(session, case["hooks"], emit=emit, restart_every_prefix=restart_every_prefix)
            for message in case["public"]["events"]:
                session.observe(message)
            result = controller_factory(public).run(world.port(), search_budget=SearchBudget(**case["search_budget"]), emit=world.on_selection)
            final = session.read()
            completed = final["time"] <= public.deadline and set(public.goals) <= {s["literal"] for s in final["supports"]}
            first = result["records"][0]["plan"] if result["records"] else None
            first_objective = None if first is None else [first["work"], first["finishes_at"], len(first["steps"])]
            if case["expected"] is not None:
                for field, actual in (("completed", completed), ("stop_reason", result["stop_reason"]), ("first_objective", first_objective)):
                    compare(case["expected"][field], actual, case["case_id"], field)
            elif not case["hooks"]:
                compare(world.references[0]["status"] == "SOLVED", completed, case["case_id"], "frozen-realization")
            compare(sum(r.get("receipt", {}).get("work_charged", 0) for r in result["records"]), session.spent, case["case_id"], "charged_work")
            return dict(case_id=case["case_id"], status="PASS", completed=completed, stop_reason=result["stop_reason"],
                first_objective=first_objective, spent=session.spent, steps=session.steps, final_time=final["time"],
                compared_prefixes=len(world.events), recovered_prefixes=world.recovered_prefixes,
                compared_plans=len(world.references), reference_states=sum(r["states"] for r in world.references),
                records=result["records"], events=world.events)
    finally:
        if output is not None:
            output.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "planning-validation")
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
    report = dict(schema="grounded-planning-report/v1", variant="B0-finite-grounded-proof/v1", corpus=receipt,
                  mode="frozen-plans-and-closed-loop", results=results, family_complete_fixtures=0,
                  physical_resource_planning=False, comparative_performance=False, evaluator_process_isolation=False)
    (args.output / "report.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(dict(cases=len(results), passed=sum(r["status"] == "PASS" for r in results), report=str(args.output / "report.json")), indent=2))
    if any(r["status"] != "PASS" for r in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
