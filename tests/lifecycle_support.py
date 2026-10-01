from reachability.lifecycle_model import LifecycleEdge, LifecycleSchema, LifecycleState, milestone_literal
from reachability.model import Evidence, Literal, Statement, Status
from reachability.requirements import Requirement

TESTED = Literal(Statement("Tested", ("artifact-v2",)))
CREDENTIAL = Literal(Statement("CredentialValid", ("credential-a",)))
ALTERNATIVE = Literal(Statement("CredentialValid", ("credential-b",)))
PRODUCT = Literal(Statement("Available", ("artifact-v2",)))
RETIRED = Literal(Statement("Retired", ("artifact-v2",)))


def fact(literal):
    return Requirement("FACT", literal)


def schema(revision="1"):
    requirements = Requirement("AND", children=(fact(TESTED), Requirement(
        "OR", children=(fact(CREDENTIAL), fact(ALTERNATIVE)))))
    return LifecycleSchema("artifact", revision, "artifact", "artifact-v2", "DRAFT",
        (LifecycleState("DRAFT"), LifecycleState("BUILT", fact(PRODUCT)), LifecycleState("RETIRED", fact(RETIRED))),
        (LifecycleEdge("build", "DRAFT", "BUILT", requirements, fact(PRODUCT), "artifact-v2", ("executor",)),
         LifecycleEdge("retire", "BUILT", "RETIRED", Requirement("ALWAYS"), fact(RETIRED),
                       "artifact-v2", ("executor",), "regression")),
        ("BUILT", "RETIRED"), "test-grounded-schema")


def accept(driver, literal, *, source="sensor", evidence_id=None, observed_at=None, valid_until=None, context="ctx"):
    service = driver.service
    evidence_id = evidence_id or driver.key()
    now = service.snapshot(context).logical_time
    service.record_evidence(Evidence(evidence_id, context, literal, source,
                                     now if observed_at is None else observed_at, (f"origin:{evidence_id}",),
                                     valid_until), idempotency_key=driver.key())
    transition = service.propose_evidence(context, evidence_id, idempotency_key=driver.key())
    result = driver.finish(driver.prepare(transition))
    if result.status is not Status.PASS:
        raise AssertionError(result)
    return result.belief


def certify(driver, episode="episode", edge="build", attempt=None):
    service = driver.service
    view = service.inspect_lifecycle(episode)
    snapshot = service.snapshot(view.episode.context_id)
    return service.certify_lifecycle_transition(episode, edge, view.episode.revision,
        snapshot.knowledge_revision, attempt_id=attempt, idempotency_key=driver.key())


def observe(driver, milestone, *, attempt="attempt", product="artifact-v2", source="executor", observation_id=None):
    belief = accept(driver, milestone_literal(attempt, product, milestone), source=source)
    return driver.service.record_operation_observation(observation_id or driver.key(), attempt, milestone,
                                                       belief.belief_revision_id, idempotency_key=driver.key())
