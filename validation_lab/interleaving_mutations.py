"""Canary-backed defects; mandatory consistency checks remain enabled for M08."""
from contextlib import contextmanager
from threading import local
from unittest.mock import patch

from reachability.execution import ExecutionMixin
from reachability.service import AdmissionService


@contextmanager
def mutate(name):
    canary = dict(calls=0)
    if name == 'M08':
        state = local()
        original_policy, original_invalidate = AdmissionService.replace_policy, AdmissionService._invalidate
        def policy(service, context_id, policy_revision, constraints, expected_revision, *, idempotency_key):
            old = service.snapshot(context_id).constraints
            state.insertion = bool(set(constraints)-set(old))
            try:
                return original_policy(service, context_id, policy_revision, constraints, expected_revision, idempotency_key=idempotency_key)
            finally:
                state.insertion = False
        def missing_index(service, context, invalid):
            if getattr(state, 'insertion', False) and invalid:
                canary['calls'] += 1
                invalid = set()  # The newly added blockers fail to reach their dependents.
            return original_invalidate(service, context, invalid)
        with patch.object(AdmissionService, 'replace_policy', policy), patch.object(AdmissionService, '_invalidate', missing_index):
            yield canary
    elif name == 'M10':
        def non_atomic(service, permit, *, idempotency_key):
            # The identical complete checks still run, but before the transaction.
            # The evaluator can now stop two workers after both have checked.
            canary['calls'] += 1
            intent = service._prepare_execution_intent(permit)
            return service._mutate('reserve_and_record_intent', idempotency_key, dict(permit=permit),
                                   lambda: service._publish_execution_intent(intent))
        with patch.object(ExecutionMixin, 'reserve_and_record_intent', non_atomic):
            yield canary
    else:
        raise ValueError('unsupported interleaving mutant')
