"""Cold finite-world reference. No runtime, checker, formula or fixture imports.

Hard consistency enumerates all Boolean assignments (runtime uses DPLL).
Numerical revision uses rational operations rounded at declared binary64 formula
boundaries. Event names stand for exact historical revisions, never predicates.
"""
from copy import deepcopy
from fractions import Fraction


class OracleGap(ValueError):
    pass


class _MissingReference(Exception):
    pass


def lookup(table, key):
    if key not in table:
        raise _MissingReference(key)
    return table[key]


def combined(statuses):
    for status in ("FAIL", "STALE", "UNKNOWN"):
        if status in statuses:
            return status
    return "PASS"


def revised_truth(left, right):
    # Each primitive is evaluated over rationals before binary64 rounding; no
    # runtime formula or numeric-consistency helper supplies the expected value.
    def rounded(value):
        return Fraction(float(value))
    strengths = [Fraction(b["strength"]) for b in (left, right)]
    confidences = [Fraction(b["confidence"]) for b in (left, right)]
    weights = [rounded(c / rounded(1-c)) for c in confidences]
    weight = rounded(sum(weights))
    if not weight:
        return None
    positive = rounded(sum(rounded(w*s) for w, s in zip(weights, strengths)))
    strength = min(1., float(positive / weight))
    confidence = min(1., max(float(weight / rounded(weight+1)), *map(float, confidences)))
    return strength, confidence


class _World:
    def __init__(self, initial):
        if initial.get("schema") != "admission-initial/v1" or not 1 <= len(initial["atoms"]) <= 8:
            raise OracleGap("unsupported initial finite world")
        self.size = len(initial["atoms"])
        self.rules = {r["rule_id"]: deepcopy(r) for r in initial["rules"]}
        self.rule_versions = {(r["rule_id"], r["revision"]) for r in initial["rules"]}
        self.contexts, self.evidence, self.models = {}, {}, {}
        self.hard, self.numeric = {}, {}
        self.aliases = dict(hard={}, numeric={})
        self.policy_versions, self.revoked, self.revoked_models = set(), set(), set()

    def consistent(self, context, assertions=(), clauses=None):
        requirements = [*context["assumptions"], *assertions]
        constraints = context["clauses"] if clauses is None else clauses
        for assignment in range(1 << self.size):
            def true(lit):
                if type(lit) is not int or not 1 <= abs(lit) <= self.size:
                    raise OracleGap("literal outside finite world")
                return bool(assignment & (1 << (abs(lit)-1))) == (lit > 0)
            if all(map(true, requirements)) and all(any(map(true, clause)) for clause in constraints):
                return True
        return False

    def fresh(self, evidence_id, ctx):
        e = self.evidence[evidence_id]
        now = self.contexts[ctx]["time"]
        if evidence_id in self.revoked or e["until"] is not None and now >= e["until"]:
            return "STALE"
        return "UNKNOWN" if now < e["observed"] else "PASS"

    def retire(self):
        # Exact edges form a DAG in commit order. Retired hard supports never
        # spring back into service when an equivalent alternative arrives.
        for row in self.hard.values():
            if any(not self.hard[p]["current"] for p in row["premises"]):
                row["current"] = False
        for row in self.numeric.values():
            row["current"] = (row["policy"] == self.contexts[row["context"]]["policy"]
                and (row["context"], row["model"]) not in self.revoked_models
                and all(self.numeric[p]["current"] for p in row["premises"])
                and all(self.fresh(e, row["context"]) == "PASS" for e in row["evidence"]))

    def assertions(self, ctx):
        return [b["literal"] for b in self.hard.values() if b["context"] == ctx and b["current"]]

    def accept(self, name, kind, ctx, lit, premises, leaves, signature, **extra):
        ledger = getattr(self, kind)
        for old, row in ledger.items():
            if row["current"] and row["signature"] == signature:
                self.aliases[kind][name] = old
                return "PASS"
        row = dict(context=ctx, literal=lit, current=True, premises=premises, evidence=sorted(set(leaves)),
                   roots=sorted({root for e in leaves for root in self.evidence[e]["roots"]}), signature=signature, **extra)
        ledger[name] = row
        self.aliases[kind][name] = name
        return "PASS"

    def hard_admission(self, name, ctx, evidence_id=None, rule_id=None, references=()):
        if evidence_id is not None:
            e = lookup(self.evidence, evidence_id)
            status = combined(["PASS" if e["context"] == ctx else "FAIL", self.fresh(evidence_id, ctx)])
            lit, parents, leaves = e["literal"], [], [evidence_id]
            signature = (ctx, "evidence", evidence_id)
        else:
            r = lookup(self.rules, rule_id)
            parents = [self.aliases["hard"].get(p) for p in references]
            checks = ["PASS" if len(parents) == len(r["premises"]) else "UNKNOWN"]
            for i, p in enumerate(parents):
                b = self.hard.get(p)
                checks.append("UNKNOWN" if b is None else "FAIL" if b["context"] != ctx else
                              "STALE" if not b["current"] else "FAIL" if i >= len(r["premises"]) or
                              b["literal"] != r["premises"][i] else "PASS")
            status, lit = combined(checks), r["conclusion"]
            leaves = [e for p in parents if p is not None for e in self.hard[p]["evidence"]]
            signature = (ctx, "rule", rule_id, r["revision"], tuple(parents))
        if status != "PASS":
            return status
        if not self.consistent(self.contexts[ctx], [*self.assertions(ctx), lit]):
            return "FAIL"
        return self.accept(name, "hard", ctx, lit, parents, leaves, signature, rule=rule_id)

    def apply(self, event):
        if event.get("schema") != "admission-event/v1":
            raise OracleGap("unsupported event schema")
        a, name, kind = event["arguments"], event["event_id"], event["kind"]
        if kind not in ("context", "evidence", "estimate", "adopt", "derive", "rule", "policy", "revoke", "tick",
                        "independence", "revoke_model", "revise", "restart"):
            raise OracleGap("unsupported event kind: " + str(kind))
        ctx = a.get("context_id")
        if ctx is not None and kind != "context" and ctx not in self.contexts:
            return "FAIL"
        if kind == "context":
            data = dict(time=0, policy="finite-hard-policy/v1", assumptions=a["assumptions"], clauses=a["clauses"])
            if ctx in self.contexts:
                old = self.contexts[ctx]
                return "PASS" if all(old[k] == data[k] for k in ("policy", "assumptions", "clauses")) else "FAIL"
            if len(self.contexts) >= 4:
                raise OracleGap("more than four contexts")
            if not self.consistent(data):
                return "FAIL"
            self.contexts[ctx] = deepcopy(data)
            self.policy_versions.add((ctx, data["policy"]))
        elif kind in ("evidence", "estimate"):
            now = self.contexts[ctx]["time"]
            if a["valid_until"] is not None and a["valid_until"] <= now:
                return "FAIL"
            self.evidence[name] = dict(context=ctx, literal=a["literal"], roots=a["roots"], observed=now, until=a["valid_until"])
            if kind == "evidence":
                return self.hard_admission(name, ctx, evidence_id=name)
            return self.accept(name, "numeric", ctx, a["literal"], [], [name], (ctx, "estimate", name),
                strength=float(a["strength"]), confidence=float(a["confidence"]), policy=self.contexts[ctx]["policy"], model=None)
        elif kind == "adopt":
            return self.hard_admission(name, ctx, evidence_id=a["evidence_id"])
        elif kind == "derive":
            return self.hard_admission(name, ctx, rule_id=a["rule_id"], references=a["premises"])
        elif kind == "rule":
            r = a["rule"]
            old = lookup(self.rules, r["rule_id"])
            if old["revision"] != a["expected_revision"]:
                return "STALE"
            if old == r:
                return "PASS"
            if (r["rule_id"], r["revision"]) in self.rule_versions:
                return "FAIL"
            self.rules[r["rule_id"]] = deepcopy(r)
            self.rule_versions.add((r["rule_id"], r["revision"]))
            for b in self.hard.values():
                if b["rule"] == r["rule_id"]:
                    b["current"] = False
        elif kind == "policy":
            c = self.contexts[ctx]
            if (c["policy"], c["clauses"]) == (a["revision"], a["clauses"]):
                return "PASS"
            if (ctx, a["revision"]) in self.policy_versions or not self.consistent(c, clauses=a["clauses"]):
                return "FAIL"
            for b in self.hard.values():
                if b["context"] == ctx and not self.consistent(c, [b["literal"]], a["clauses"]):
                    b["current"] = False
            c.update(policy=a["revision"], clauses=deepcopy(a["clauses"]))
            self.policy_versions.add((ctx, a["revision"]))
            self.retire()
            if not self.consistent(c, self.assertions(ctx)):
                for b in self.hard.values():
                    if b["context"] == ctx:
                        b["current"] = False
        elif kind == "revoke":
            evidence_id = a["evidence_id"]
            lookup(self.evidence, evidence_id)
            self.revoked.add(evidence_id)
            for b in self.hard.values():
                if evidence_id in b["evidence"]:
                    b["current"] = False
        elif kind == "tick":
            if a["time"] < self.contexts[ctx]["time"]:
                return "FAIL"
            self.contexts[ctx]["time"] = a["time"]
            for b in self.hard.values():
                if b["context"] == ctx and any(self.fresh(e, ctx) != "PASS" for e in b["evidence"]):
                    b["current"] = False
        elif kind == "independence":
            parents = sorted(self.aliases["numeric"].get(p, "missing:"+p) for p in a["premises"])
            if len(set(parents)) != 2 or any(p not in self.numeric or self.numeric[p]["context"] != ctx for p in parents):
                return "FAIL"
            value = (parents, a["justification"])
            if (ctx, a["model_id"]) in self.models and self.models[ctx, a["model_id"]] != value:
                return "FAIL"
            self.models[ctx, a["model_id"]] = value
        elif kind == "revoke_model":
            lookup(self.models, (ctx, a["model_id"]))
            self.revoked_models.add((ctx, a["model_id"]))
        elif kind == "revise":
            parents = sorted(self.aliases["numeric"].get(p, "missing:"+p) for p in a["premises"])
            model = self.models.get((ctx, a["model_id"]))
            checks = ["PASS" if len(parents) == 2 else "UNKNOWN"]
            checks += ["UNKNOWN" if p not in self.numeric else "FAIL" if self.numeric[p]["context"] != ctx else
                       "PASS" if self.numeric[p]["current"] else "STALE" for p in parents]
            checks.append("UNKNOWN" if model is None else "STALE" if (ctx, a["model_id"]) in self.revoked_models else
                          "PASS" if parents == model[0] else "FAIL")
            status = combined(checks)
            if status != "PASS":
                return status
            left, right = (self.numeric[p] for p in parents)
            if left["literal"] != right["literal"]:
                return "FAIL"
            if set(left["evidence"]) & set(right["evidence"]) or set(left["roots"]) & set(right["roots"]):
                return "UNKNOWN"
            truth = revised_truth(left, right)
            if truth is None:
                return "UNKNOWN"
            if truth[1] >= 1:
                return "FAIL"
            return self.accept(name, "numeric", ctx, left["literal"], parents, left["evidence"]+right["evidence"],
                (ctx, "revision", tuple(parents), a["model_id"], self.contexts[ctx]["policy"]),
                strength=truth[0], confidence=truth[1], model=a["model_id"], policy=self.contexts[ctx]["policy"])
        elif kind != "restart":
            raise OracleGap("unsupported event kind: " + kind)
        return "PASS"

    def projection(self):
        result = dict(contexts=deepcopy(self.contexts), aliases=deepcopy(self.aliases), hard={}, numeric={})
        for kind in ("hard", "numeric"):
            for name, b in getattr(self, kind).items():
                result[kind][name] = {k: deepcopy(v) for k, v in b.items() if k not in ("signature", "rule", "model", "policy")}
            for ctx, data in result["contexts"].items():
                data[kind] = {}
                for atom in range(1, self.size+1):
                    for lit in (atom, -atom):
                        history = [b for b in getattr(self, kind).values() if b["context"] == ctx and b["literal"] == lit]
                        data[kind][str(lit)] = "PASS" if any(b["current"] for b in history) else "STALE" if history else "UNKNOWN"
        return result


def reference_prefix(initial, events):
    if len(events) > 128:
        raise OracleGap("more than 128 events")
    world, seen, status = _World(initial), set(), "PASS"
    for event in events:
        if event["event_id"] in seen:
            raise OracleGap("duplicate event identity")
        seen.add(event["event_id"])
        try:
            status = world.apply(event)
        except _MissingReference:
            status = "FAIL"  # Unavailable public command reference, not a proof.
        world.retire()
    return dict(status=status, projection=world.projection())
