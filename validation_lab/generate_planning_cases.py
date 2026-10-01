"""Reproducible tiny proof-planning controls; future edits stay evaluator-owned."""
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
from random import Random

from reachability.admission_protocol import AdmissionInitial, event
from reachability.grounded_planning import PlanningPublic, RuleCost, SearchBudget
from .generate_admission_cases import context, evidence, op

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "validation_lab" / "planning_cases"


def profile(rules, goals=(4,), *, work=20, deadline=5, steps=5):
    # Each rule is (ordered premises, conclusion, work, duration).
    initial = AdmissionInitial.parse(dict(schema="admission-initial/v1", atoms=["a0", "a1", "a2", "a3"],
        rules=[dict(rule_id=f"r{i}", revision="1", premises=p, conclusion=q) for i, (p, q, _, _) in enumerate(rules)]))
    return PlanningPublic(initial, "c0", tuple(goals), tuple(RuleCost(f"r{i}", w, d) for i, (_, _, w, d) in enumerate(rules)), work, deadline, steps)


def messages(rows, prefix="e"):
    return [event(f"{prefix}{i}", kind, **args) for i, (kind, args) in enumerate(rows)]


def make_case(name, public, rows, controls, *, completed, objective=None, stop=None, hooks=(), budget=None):
    return dict(schema="grounded-planning-case/v1", case_id=name, split="development", parent_instance_id="planning-parent-0",
        public=dict(profile=public.wire(), events=messages(rows)), controls=controls,
        hooks=deepcopy(list(hooks)), search_budget=asdict(budget or SearchBudget()),
        expected=dict(completed=completed, first_objective=objective, stop_reason=stop or ("OBSERVED_GOALS" if completed else "UNREACHABLE")))


def scenarios():
    cases = []
    def case(public, rows, controls, **kw):
        cases.append(make_case(f"p{len(cases)+1:02}", public, rows, controls, **kw))
    base = [context(), evidence(1)]
    chain = profile([([1, 2], 3, 1, 1), ([3], 4, 2, 1)])
    case(chain, [*base, evidence(2, root="s1")], ["F01:ordered-AND-chain"], completed=True, objective=[3, 2, 2])
    case(profile([([1], 2, 1, 0), ([2], 3, 1, 1), ([2], 4, 1, 1)], (3, 4)), base,
         ["F01:shared-subproof-multiple-goals"], completed=True, objective=[3, 2, 3])
    cycle = profile([([2], 3, 1, 0), ([3], 2, 1, 0)], (3,))
    case(cycle, base, ["F01:unseeded-cycle"], completed=False)
    case(cycle, [context(), evidence(2)], ["F01:seeded-cycle"], completed=True, objective=[1, 0, 1])
    alternatives = [([1], 4, 5, 1), ([1], 4, 1, 5)]
    case(profile(alternatives, work=2, deadline=2), base, ["F03:incompatible-work-time-alternatives"], completed=False)
    case(profile(alternatives, work=5, deadline=2), base, ["F03:fast-expensive-alternative"], completed=True, objective=[5, 1, 1])
    case(profile(alternatives, work=1, deadline=5), base, ["F03:slow-cheap-alternative"], completed=True, objective=[1, 5, 1])
    case(profile([([1], 2, 1, 0), ([1], 3, 1, 0)], (2, 3)),
         [context(clauses=[[-2, -3]]), evidence(1)], ["F02:joint-goal-conflict"], completed=False)
    case(profile([([1], -2, 1, 2)], (-2,), deadline=3),
         [context(), evidence(1, until=4), evidence(2, root="s1", until=3)],
         ["F14:wait-before-duration", "F02:temporary-blocker"], completed=True, objective=[1, 3, 2])
    simple = profile([([1], 4, 1, 2)])
    case(simple, [context(), evidence(1, until=2)], ["F14:exclusive-expiry"], completed=False)
    case(simple, [context(assumptions=[1])], ["F04:assumption-is-not-premise"], completed=False)
    case(simple, [context(), evidence(1, truth=(1., .99))], ["F04:numeric-is-not-hard-premise"], completed=False)
    case(simple, [context(), context("c1"), evidence(1, ctx="c1")], ["F04:foreign-context"], completed=False)
    case(simple, base, ["F08:revocation-after-selection"], completed=True, objective=[1, 2, 1], hooks=[dict(request=0,
        events=messages([op("revoke", evidence_id="e1"), evidence(1, root="s1")], "h"))])
    case(simple, [*base, evidence(3, root="s1")], ["F01:rule-replacement-after-selection"], completed=True, objective=[1, 2, 1], hooks=[dict(request=0,
        events=messages([op("rule", rule=dict(rule_id="r0", revision="2", premises=[3], conclusion=4), expected_revision="1")], "h"))])
    case(simple, base, ["F02:policy-change-after-selection"], completed=False, objective=[1, 2, 1], hooks=[dict(request=0,
        events=messages([op("policy", context_id="c0", revision="h2", clauses=[[-4]])], "h"))])
    case(simple, base, ["F13:state-budget"], completed=False, stop="BUDGET_EXHAUSTED", budget=SearchBudget(states=0))
    case(simple, base, ["F13:transition-budget"], completed=False, stop="BUDGET_EXHAUSTED", budget=SearchBudget(transitions=0))
    case(simple, [context(), evidence(1, until=1), evidence(1, until=4, root="s1")],
         ["F14:exact-support-lifetime-alternatives"], completed=True, objective=[1, 2, 1])
    case(profile([], (1,), work=0, steps=0), base, ["F01:already-observed-goal"], completed=True, objective=[0, 0, 0])
    case(profile([([1, 1, -2], 3, 1, 0)], (3,)), [*base, evidence(-2, root="s1")],
         ["F01:ordered-repeated-and-negative-premises"], completed=True, objective=[1, 0, 1])
    case(profile([([1], 3, 1, 1), ([3], 4, 2, 1)], work=2), base,
         ["F03:whole-plan-work-budget"], completed=False)
    return cases


def generated_scenarios(seed=4103, count=12):
    rng, cases = Random(seed), []
    for i in range(count):
        rules = [([rng.randrange(1, 4)], rng.choice((2, 3, 4, -4)), rng.randrange(1, 4), rng.randrange(3)) for _ in range(4)]
        public = profile(rules, (4,), work=rng.randrange(1, 9), deadline=4, steps=4)
        rows = [context(clauses=[[-2, -3]] if rng.randrange(3) == 0 else []), evidence(1, until=rng.choice((None, 2, 4)))]
        # No outcome filtering or oracle-generated labels. Each emitted decision
        # is checked independently, and frozen episodes must realize its result.
        case = make_case(f"generated-{seed}-{i}", public, rows, ["seeded-frozen-graph"], completed=None)
        case["expected"] = None
        cases.append(case)
    return cases


def write():
    cases = scenarios()
    files = {CORPUS / "public" / (c["case_id"]+".json"): c["public"] for c in cases}
    files.update({CORPUS / "evaluator" / (c["case_id"]+".json"): {k: v for k, v in c.items() if k != "public"} for c in cases})
    for path, value in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2)+"\n")
    sources = ["validation_lab/"+name+".py" for name in ("generate_planning_cases", "run_planning", "planning_oracle", "admission_oracle", "generate_admission_cases", "run_deployment")]
    sources += [str(p.relative_to(ROOT)) for p in sorted((ROOT / "reachability").glob("*.py"))]
    receipt = dict(schema="grounded-planning-corpus/v1", split="development", parent_instance_id="planning-parent-0", case_count=len(cases),
        fixture_files={str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in sorted(files)},
        source_files={p: sha256((ROOT / p).read_bytes()).hexdigest() for p in sources}, family_complete_fixtures=0,
        scope="frozen hard proof-work/time planning plus public-edit replanning; no physical resource scheduling or performance comparison")
    (CORPUS / "manifest.json").write_text(json.dumps(receipt, indent=2)+"\n")


if __name__ == "__main__":
    write()
