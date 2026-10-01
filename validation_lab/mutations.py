"""Isolated, evaluator-only M06/M11 defects, with invocation canaries."""
from contextlib import contextmanager
from dataclasses import replace
from unittest.mock import patch

from reachability.goals import GoalMixin
import reachability.goals as goals


@contextmanager
def mutate(name):
    canary = {"calls": 0}
    if name == "M06":
        original = GoalMixin._project_goal
        def acknowledgement_is_success(service, goal_id):
            result = original(service, goal_id)
            if any(service.inspect_dispatch(attempt).state == "accepted" for attempt in service._dispatch.attempts):
                canary["calls"] += 1
                return replace(result, outstanding_loss=0, estimated_committed_coverage=0, open_loss=0,
                    slices=tuple(replace(s, label="OBSERVED_SUCCESS", outstanding_loss=0, estimated_coverage=0,
                                         selected_commitment=None) for s in result.slices))
            return result
        target = patch.object(GoalMixin, "_project_goal", acknowledgement_is_success)
    elif name == "M11":
        original = goals.evaluate_durability
        def censorship_is_failure(*args, **kwargs):
            result = original(*args, **kwargs)
            if result.label == "CENSORED":
                canary["calls"] += 1
                return replace(result, label="OBSERVED_FAILURE")
            return result
        target = patch.object(goals, "evaluate_durability", censorship_is_failure)
    else:
        raise ValueError("unsupported deployment mutant")
    with target:
        yield canary
