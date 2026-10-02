"""Expose the existing public authority identity without changing authority."""
from dataclasses import replace
from time import perf_counter_ns
from experimental_goal_pln.session import Session as GoalSession


class Session(GoalSession):
    def read(self):
        start=perf_counter_ns()
        with self.service._lock:
            snapshot=super().read()
            authority=self.service.export_admission(snapshot.context.context_id)[0]
            result=replace(snapshot,contracts=snapshot.contracts+(('authority-identity/v1',authority),))
        self.costs['recall_snapshot_inclusive_ns']+=perf_counter_ns()-start
        return result
