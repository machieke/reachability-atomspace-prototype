"""Observation-based durability; scheduling predictions never enter this checker."""
from .goal_model import DurabilityContract, DurabilityResult, GoalMonitor, GoalSample
from .model import Check, Status


def evaluate_durability(contract: DurabilityContract, monitor: GoalMonitor,
                        samples: tuple[GoalSample, ...], usable: frozenset[str], now: int,
                        condition_status: Status) -> DurabilityResult:
    def result(label, status, detail, witnesses=()):
        return DurabilityResult(label, witnesses, (Check("sampled_durability", status, detail),))

    if contract.samples > 16:
        return result("UNKNOWN", Status.UNKNOWN, "unsupported sample window size")
    if monitor.censored_at is not None:
        return result("CENSORED", Status.UNKNOWN, "monitoring ended without declaring a causal outcome")
    if condition_status is Status.FAIL:
        return result("OBSERVED_FAILURE", Status.FAIL, "current slice condition is contradicted")
    relevant = tuple(sample for sample in samples if sample.monitor_id == monitor.monitor_id
                     and monitor.opened_at <= sample.observed_at <= now)
    if not relevant:
        pending = now < monitor.opened_at + (contract.samples - 1) * contract.interval
        return result("PENDING" if pending else "UNKNOWN", Status.UNKNOWN, "no qualifying observations")
    latest = max(sample.observed_at for sample in relevant)
    if now >= latest + contract.fresh_for:
        return result("UNKNOWN", Status.STALE, "the latest observation is no longer fresh")
    times = tuple(latest - offset * contract.interval for offset in reversed(range(contract.samples)))
    current = tuple(sample for sample in relevant if sample.observed_at in times
                    and sample.belief_revision_id in usable)
    failed = tuple(sample for sample in current if not sample.healthy)
    if failed:
        return result("OBSERVED_FAILURE", Status.FAIL, "a required observation records failure", failed)
    if condition_status is not Status.PASS:
        return result("UNKNOWN", condition_status, "current slice condition is unsupported")
    if times[0] < monitor.opened_at:
        return result("PENDING", Status.UNKNOWN, "the observation window has not matured")
    choices = [tuple(sorted((sample for sample in current if sample.observed_at == tick),
                            key=lambda sample: sample.sample_id)) for tick in times]
    if any(not group for group in choices):
        return result("UNKNOWN", Status.UNKNOWN, "missing or revoked observation in the exact sampling window")
    if sum(map(len, choices)) > 256:
        return result("UNKNOWN", Status.UNKNOWN, "sample witness alternatives exceed the supported limit")
    # Search whole witness sets. A greedy selection could discard an independent
    # alternative and fail despite a complete valid window. Bound search, not scope.
    work = 0

    def choose(index, roots, witnesses):
        nonlocal work
        if work >= 4096:
            return None
        work += 1
        if index == len(choices):
            return witnesses
        for sample in choices[index]:
            if work >= 4096:
                break
            if not roots.intersection(sample.lineage_roots):
                selected = choose(index + 1, roots.union(sample.lineage_roots), (*witnesses, sample))
                if selected is not None:
                    return selected
        return None

    witnesses = choose(0, frozenset(), ())
    if witnesses is None:
        return result("UNKNOWN", Status.UNKNOWN, "no distinct supported measurement lineage within search limit")
    return result("OBSERVED_SUCCESS", Status.PASS, "complete fresh sampled window; no continuous-time claim", witnesses)
