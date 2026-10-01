"""Diagnostic sensitivity checks, not additional designated benchmark mutants."""
from contextlib import contextmanager
from unittest.mock import patch

from reachability.dispatch import DispatchMixin
from reachability.model import Status, conjunction


@contextmanager
def mutate(name):
    canary = dict(calls=0)
    if name == 'cached-send-gate':
        original = DispatchMixin._dispatch_submission_checks
        def cached(service, attempt):
            result = original(service, attempt)
            prepared = service._dispatch.attempts.get(attempt)
            if prepared and conjunction(result[0]) is not Status.PASS:
                canary['calls'] += 1
                return prepared.checks, prepared.prerequisites, prepared.action_requirements
            return result
        scope = patch.object(DispatchMixin, '_dispatch_submission_checks', cached)
    elif name == 'expire-uncertain':
        original = DispatchMixin._dispatch_resource_state
        def expire(service, attempt):
            result = original(service, attempt)
            intent = service._execution.intents.get(attempt)
            if result == 'reconciliation_required' and intent and service._execution.logical_time >= intent.lease_until:
                canary['calls'] += 1
                return None
            return result
        scope = patch.object(DispatchMixin, '_dispatch_resource_state', expire)
    else:
        raise ValueError('unsupported dispatch diagnostic mutation')
    with scope:
        yield canary
