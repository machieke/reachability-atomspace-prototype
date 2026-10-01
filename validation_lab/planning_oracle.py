"""Same-information exact tiny planner: layered state enumeration and truth tables.

No runtime/planner/fixture imports. It receives only the frozen public problem,
not a future script or the actual planner's result. Timeout is explicitly unknown.
"""
from itertools import product


class OracleGap(ValueError):
    pass


def exact_plan(public, snapshot, *, state_limit=100000, transition_limit=500000):
    if any(type(v) is not int or v < 0 for v in (state_limit, transition_limit)):
        raise OracleGap("invalid reference work limit")
    if public.get("schema") != "grounded-planning-public/v1" or snapshot.get("schema") != "grounded-planning-snapshot/v1":
        raise OracleGap("unsupported planning schema")
    n = len(public["admission"]["atoms"])
    if n > 8 or len(snapshot["rules"]) > 8 or snapshot["remaining_steps"] > 8 or public["deadline"] > 16:
        raise OracleGap("reference exceeds the tiny planning profile")
    literals = tuple(range(1, n+1))+tuple(range(-1, -n-1, -1))
    index = {lit: i for i, lit in enumerate(literals)}
    # A Boolean world must satisfy the full environment, not pairwise checks.
    worlds = []
    for mask in range(2**n):
        truth = {lit for lit in literals if bool(mask & (1 << (abs(lit)-1))) == (lit > 0)}
        if set(snapshot["assumptions"]) <= truth and all(set(c) & truth for c in snapshot["clauses"]):
            worlds.append(truth)
    def consistent(lifetimes):
        asserted = {literals[i] for i, expiries in enumerate(lifetimes) if expiries}
        return any(asserted <= w for w in worlds)
    initial = [set() for _ in literals]
    for support in snapshot["supports"]:
        expiry = 1001 if support["valid_until"] is None else support["valid_until"]
        initial[index[support["literal"]]].add(expiry)
    initial = tuple(tuple(sorted(values)) for values in initial)
    if not consistent(initial):
        raise OracleGap("inconsistent initial planning state")
    if snapshot["time"] > public["deadline"]:
        return dict(status="UNREACHABLE", objective=None, states=0)
    costs = {c["rule_id"]: (c["work"], c["duration"]) for c in public["costs"]}
    layer = {(snapshot["time"], initial): 0}
    optimum, visited, transitions = None, 0, 0
    for depth in range(snapshot["remaining_steps"]+1):
        following = {}
        for (time, lifetimes), spent in layer.items():
            if visited >= state_limit:
                return dict(status="NOT_COMPUTED", objective=None, states=visited)
            visited += 1
            if all(lifetimes[index[g]] for g in public["goals"]):
                objective = (spent, time, depth)
                if optimum is None or objective < optimum:
                    optimum = objective
            if depth == snapshot["remaining_steps"]:
                continue
            # Enumerate every declared rule, including redundant derivations, and
            # every integral wait endpoint. No runtime pruning/priority is reused.
            actions = [(r, time+costs[r["rule_id"]][1], costs[r["rule_id"]][0]) for r in snapshot["rules"]]
            actions += [(None, end, 0) for end in range(time+1, public["deadline"]+1)]
            for rule, end, charge in actions:
                if transitions >= transition_limit:
                    return dict(status="NOT_COMPUTED", objective=None, states=visited)
                transitions += 1
                total = spent+charge
                if end > public["deadline"] or total > snapshot["remaining_work"]:
                    continue
                after = [tuple(expiry for expiry in expiries if expiry > end) for expiries in lifetimes]
                if rule is not None:
                    inputs = [after[index[p]] for p in rule["premises"]]
                    output = index[rule["conclusion"]]
                    successors = set()
                    for chosen in product(*inputs):
                        if transitions >= transition_limit:
                            return dict(status="NOT_COMPUTED", objective=None, states=visited)
                        transitions += 1
                        candidate = list(after)
                        candidate[output] = tuple(sorted(set(candidate[output]) | {min(chosen)}))
                        successors.add(tuple(candidate))
                else:
                    successors = {tuple(after)}
                for successor in successors:
                    if not consistent(successor):
                        continue
                    key = end, successor
                    if key not in following or total < following[key]:
                        following[key] = total
        layer = following
    return dict(status="SOLVED" if optimum is not None else "UNREACHABLE",
                objective=None if optimum is None else list(optimum), states=visited)


def verify_plan(public, snapshot, plan):
    """Replay an entire proposed witness independently, including symbolic parents."""
    rules = {r["rule_id"]: r for r in snapshot["rules"]}
    costs = {c["rule_id"]: c for c in public["costs"]}
    facts = {("belief", s["reference"]): (s["literal"], s["valid_until"])
             for s in snapshot["supports"]}
    time, spent = snapshot["time"], 0
    if len(plan["steps"]) > snapshot["remaining_steps"]:
        raise OracleGap("plan exceeds its step budget")
    for index, step in enumerate(plan["steps"]):
        end = step["finishes_at"]
        if type(end) is not int or not time <= end <= public["deadline"]:
            raise OracleGap("invalid plan time")
        facts = {ref: data for ref, data in facts.items() if data[1] is None or data[1] > end}
        if step["kind"] == "wait":
            if end == time or step["work"] != 0 or step["premises"] or step["rule_id"] is not None or step["rule_revision"] is not None:
                raise OracleGap("invalid waiting witness")
        elif step["kind"] == "derive":
            rule, cost = rules[step["rule_id"]], costs[step["rule_id"]]
            if step["rule_revision"] != rule["revision"] or end != time+cost["duration"] or step["work"] != cost["work"]:
                raise OracleGap("wrong rule version or cost/time contract")
            parents = []
            for ref in step["premises"]:
                key = ("belief", ref["reference"]) if ref["kind"] == "belief" else ("step", ref["index"])
                if key not in facts:
                    raise OracleGap("absent or expired exact plan premise")
                parents.append(facts[key])
            if [p[0] for p in parents] != rule["premises"]:
                raise OracleGap("incomplete or misordered plan premises")
            facts[("step", index)] = rule["conclusion"], min((p[1] for p in parents if p[1] is not None), default=None)
            spent += cost["work"]
        else:
            raise OracleGap("unknown plan operation")
        asserted = {data[0] for data in facts.values()} | set(snapshot["assumptions"])
        possible = False
        for mask in range(2**len(public["admission"]["atoms"])):
            def holds(lit):
                return bool(mask & (1 << (abs(lit)-1))) == (lit > 0)
            if all(map(holds, asserted)) and all(any(map(holds, clause)) for clause in snapshot["clauses"]):
                possible = True
                break
        if not possible:
            raise OracleGap("jointly inconsistent plan state")
        time = end
    if spent > snapshot["remaining_work"] or spent != plan["work"] or time != plan["finishes_at"]:
        raise OracleGap("wrong total plan objective")
    if not set(public["goals"]) <= {data[0] for data in facts.values()}:
        raise OracleGap("plan does not realize all current goals")
    return [spent, time, len(plan["steps"])]
