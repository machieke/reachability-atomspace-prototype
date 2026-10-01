from reachability.goal_model import DurabilityContract, GoalContract, GoalSlice, goal_sample_literal
from reachability.model import Evidence
from tests.execution_support import ExecutionFixture
from tests.lifecycle_support import PRODUCT, accept, fact


class GoalFixture(ExecutionFixture):
    def setUp(self):
        super().setUp()
        self.goal_contract = GoalContract("service-goal", "1", "obligation-units", (
            GoalSlice("healthy", 6, "artifact-v2", fact(PRODUCT), DurabilityContract(3, 1, 1, ("monitor",))),
            GoalSlice("available", 4, "artifact-v2", fact(PRODUCT), DurabilityContract(1, 1, 1, ("monitor",)))), "test")
        self.service.register_goal_contract(self.goal_contract, idempotency_key=self.driver.key())
        self.goal = self.service.open_goal_episode("goal", "service-obligation", "ctx", "service-goal", "1",
                                                   idempotency_key=self.driver.key())
        self.intent = self.reserve()

    def tick(self, time):
        self.service.advance_clock("ctx", time, idempotency_key=self.driver.key())
        self.service.advance_resource_clock(time, idempotency_key=self.driver.key())

    def product(self):
        return accept(self.driver, PRODUCT, evidence_id="product")

    def sample(self, time, *, slice_id="healthy", healthy=True, goal_id="goal", product="artifact-v2",
               source="monitor", roots=None, sample_id=None, evidence_id=None, context="ctx"):
        evidence_id = evidence_id or self.driver.key()
        literal = goal_sample_literal(goal_id, slice_id, product, time, healthy)
        evidence = Evidence(evidence_id, context, literal, source, time, tuple(roots or (evidence_id,)))
        self.service.record_evidence(evidence, idempotency_key=self.driver.key())
        transition = self.service.propose_evidence(context, evidence_id, idempotency_key=self.driver.key())
        belief = self.driver.finish(self.driver.prepare(transition)).belief
        if belief is None:
            raise AssertionError("sample did not pass admission")
        return self.service.record_goal_sample(sample_id or self.driver.key(), goal_id, slice_id, healthy,
                                               belief.belief_revision_id, idempotency_key=self.driver.key())

    def projection(self, goal_id="goal"):
        return self.service.inspect_goal(goal_id).projection

    def reconcile(self, goal_id="goal", key=None):
        return self.service.reconcile_goal(goal_id, self.projection(goal_id).fingerprint,
                                            idempotency_key=key or self.driver.key())

    def cover(self, units=6, slice_id="healthy", commitment_id=None, attempt="attempt", goal_id="goal", until=10):
        return self.service.claim_goal_coverage(commitment_id or self.driver.key(), goal_id, slice_id, attempt,
                                                "worker", units, until, idempotency_key=self.driver.key())
