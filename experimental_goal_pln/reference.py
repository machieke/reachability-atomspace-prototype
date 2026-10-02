"""Separate scan traversal; intentionally no optimized closure or index calls."""
from time import perf_counter_ns
from .relevance import Closure, ClosureLimits, Path, key


def scan_closure(snapshot, task, limits=ClosureLimits()):
    started = perf_counter_ns()
    if task.binding != snapshot.binding:
        raise ValueError('stale task descriptor')
    records, waiting, expanded, rules = [], [], set(), []
    count = depth_seen = 0
    complete, reason = True, 'COMPLETE_TASK_DEPENDENCIES'
    def remember(literal, path, level):
        nonlocal complete, reason, depth_seen
        if any(item[0] == literal for item in records):
            return
        if level > limits.depth:
            complete, reason = False, 'DEPTH_BOUND'
        elif len(records) == limits.nodes:
            complete, reason = False, 'NODE_BOUND'
        else:
            records.append((literal, path))
            waiting.append((literal, path, level))
            depth_seen = max(level, depth_seen)
    for root in sorted([r for r in task.roots if r.kind == 'numeric'], key=key):
        remember(root.target, Path(root), 0)
    while waiting and complete:
        literal, path, level = waiting.pop(0)
        if literal in expanded:
            continue
        expanded.add(literal)
        for rule in sorted(snapshot.rules, key=lambda r:r.rule_id):
            if rule.deduction.conclusion != literal:
                continue
            required = rule.deduction.premises
            if count+len(required) > limits.edges:
                complete, reason = False, 'EDGE_BOUND'
                break
            rules.append((rule, path, required))
            for i in range(len(required)):
                count += 1
                remember(required[i], Path(path.root, path.steps+((rule.rule_id, rule.revision,
                         i, literal, required[i]),)), level+1)
    return Closure(task, tuple(sorted(records, key=lambda p:key(p[0]))),
                   tuple(sorted(rules, key=lambda r:r[0].rule_id)), complete, reason,
                   len(records), count, depth_seen, perf_counter_ns()-started)
