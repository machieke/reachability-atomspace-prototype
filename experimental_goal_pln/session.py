"""Read-only registration receipts added to the frozen coherent public snapshot.

No discovery seam is needed: execute still performs the frozen full membership
check and all original gates. Captures are actual successful registration returns.
"""
from dataclasses import replace
from time import perf_counter_ns
from experimental_online_pln.session import Session as FrozenSession


class Session(FrozenSession):
    def _initialize(self):
        self.contract_receipts = {}
        names = ('lifecycle_schema', 'execution_contract', 'goal_contract',
                 'completion_contract', 'dispatch_policy')
        originals = {}
        for name in names:
            method = 'register_' + name
            originals[method] = getattr(self.service, method)
            def capture(value, *args, _name=name, _call=originals[method], **kwargs):
                result = _call(value, *args, **kwargs)
                # Successful registration returns the exact immutable contract.
                if result != value:
                    raise AssertionError('unexpected registration receipt')
                self.contract_receipts[_name] = result
                return result
            setattr(self.service, method, capture)
        try:
            super()._initialize()
        finally:
            for method in originals:
                delattr(self.service, method)

    def read(self):
        start = perf_counter_ns()
        with self.service._lock:
            snapshot = super().read()
            result = replace(snapshot, contracts=snapshot.contracts + tuple(
                ('registered-content/v1', name, value)
                for name, value in sorted(self.contract_receipts.items())))
        self.costs['descriptor_snapshot_inclusive_ns'] += perf_counter_ns()-start
        return result
