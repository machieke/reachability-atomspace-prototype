# Probabilistic deployment decisions

`probability-decision/v1` binds an explicit numerical acceptance policy to one
immutable execution contract version. It uses only current certified revisions
from the [probability ledger](PROBABILITY.md). Passing a decision permits the
declared action gate; it asserts neither the forecast event nor goal success.

The executable deployment slice uses both [pinned native adapters](ADAPTERS.md):

```bash
uv run --no-project python -m reachability.decision_demo
uv run --no-project python -m unittest discover -s integration_tests -v
```

The default tests run the same episode with the deterministic formula checker and
no native dependency. The original `reachability.goal_demo` remains available.

## Declared contract

A trusted caller registers the execution contract, then its decision contract,
before issuing **any** execution certificate for that execution version. Registration
pins the exact lifecycle edge product and advances the shared resource epoch.
There is one immutable binding per execution version. Threshold or policy changes
require a new execution version and newly certified attempts. An existing execution
version without a decision contract retains its declared hard requirements; this
API does not impose a global decision policy on other registered versions.

```python
from reachability.decision_model import DecisionContract, DecisionCriterion
from reachability.pln_adapter import implication

contract = DecisionContract(
    "deployment-acceptance", "1", "deploy", "1", "artifact-v2",
    (DecisionCriterion(
        "healthy-given-tested",
        implication("tested:artifact-v2", "healthy:artifact-v2"),
        min_strength=0.65, max_strength=1.0, min_confidence=0.35,
    ),),
)
service.register_decision_contract(contract, idempotency_key="register-decision")
```

Contracts declare between one and sixteen unique criteria. Each criterion binds
an exact grounded literal and a closed strength interval in
`dimensionless-probability` units. Bounds are finite binary64 values in `[0,1]`;
comparisons are inclusive and have no epsilon tolerance. An upper bound supports
a separately declared risk estimate. The confidence floor lies in `[0,1)` and
means PLN evidence adequacy under the pinned finite `k=1` truth model. It is **not**
a calibrated confidence interval, a lower probability bound, a probability of
success, or a multiplier on strength. Arbitrary units and alternative interpretations
are rejected. The demo thresholds are synthetic acceptance choices, not calibrated
deployment recommendations or measured safety guarantees.

The supported alternative policy is `all-current-exact-literal/v1`:

- Every current certified estimate for each criterion must satisfy its interval
  and confidence floor. Callers cannot nominate a convenient subset, aggregate
  evidence implicitly, or choose the largest strength.
- Missing support is UNKNOWN; wholly retired support is STALE; any current strength
  outside the interval is FAIL; inadequate confidence is UNKNOWN. FAIL describes
  the acceptance policy, not the Boolean falsity of the predicted event.
- Current estimates of the opposite literal make the criterion UNKNOWN. This
  version does not silently ignore them or infer a complementary probability model.
- All criteria and the current enclosing hard-environment check must pass. This
  conjunction is an acceptance rule, not a joint probability calculation across
  forecast events. No combined risk guarantee follows from multiple criteria.

Normal status precedence applies: FAIL, then STALE, then UNKNOWN, then PASS.
Stale historical alternatives do not veto otherwise current adequate support.
Sources, rules, model assumptions and policies retain the ledger's exact retirement
semantics. Uncommitted reports and support in other contexts supply no authority.

## Certification, reservation and dispatch

The existing `certify_execution` API evaluates the registered decision alongside
hard prerequisites, owner, selection, clock and resource checks. Its issued permit
contains a digest of the complete evaluation. An immutable witness, stored in the
same transaction, records the contract, context revision/time, each exact numerical
belief revision and truth value, and all criterion results:

```python
historical = service.execution_decision(permit.certificate_id)
current = service.inspect_probability_decision("attempt", "deploy", "1")
```

These are different questions. `historical` explains the original certificate;
`current` evaluates the policy now. Neither read call reserves or sends anything.
An execution version with no numerical gate returns `None` for its historical
decision. The ordinary reservation API rejects forged or altered permits, and
rechecks the complete context and resource revisions before atomically publishing
claims and an intent.

A pending intent retains its **exact set of numerical alternatives**. New adequate
alternatives, removal of a certified revision, and equal-valued replacement evidence
change that set and make the intent STALE. A new attempt is needed to adopt a changed
basis. Unrelated evidence and clock ticks preserve the basis, while source freshness
is still checked at every gate. The implementation does not silently refresh an
intent onto a different probabilistic justification.

Intent inspection, durable dispatch preparation and the final executor send all
enforce the decision and its support binding. The existing authority lock spans
final checks and synchronous simulator I/O. Neither a recovered submission marker
nor stale numerical evidence can authorize a resend. Authoritative reconciliation
and fenced release remain available after support retirement. An already accepted
effect remains historical; losing its old forecast does not undo that effect.

## Recovery and native representation

New commands and typed witness records are additive. Existing execution record
layouts and command results remain unchanged for versions without a decision
contract. Checked replay rebuilds contracts and decision witnesses and recomputes
their digests without native inference or executor I/O. Failed writes roll back
decision bindings, certificates and reservation state together. Ambiguous writes
reconcile by the original command key. Replay rejects a recorded success produced
by a broken decision checker.

`project_execution_decision(service, attempt_id)` captures hard/numerical views,
the intent, its issued permit and decision witness, and submission history in one
authority snapshot. Native AtomSpace stores their typed structure and Values.
Ordered tuples of numbers also have typed scalar atoms: integers use exact decimal
StringValues, including integers larger than binary64 can represent; floats use
FloatValues with distinct content identities, including signed zero. The projection
is diagnostic and disposable. SQLite and checked replay remain authoritative.

## Deployment result and validation scope

The demo initially blocks missing credentials and missing forecasts. A certified
native deduction produces approximately `(strength=0.68, confidence=0.3584)` and
passes the declared `(strength >= 0.65, confidence >= 0.35)` gate. Its hard query
remains UNKNOWN. The intent covers six of ten obligation units; neither the
forecast nor executor ACK reduces outstanding loss.

The numerical sources and submission credential expire at tick 1. Exact later
product/completion observations and three fresh healthy samples nevertheless
satisfy the separate completion contract. Observed loss is `[10,10,0]` after those
samples. A later unhealthy observation reopens all ten units while the historical
lifecycle stage stays BUILT. No causal credit is inferred. The complete deployment
snapshot and native projection reconstruct identically after journal recovery.

Shared finite/durable/native tests cover thresholds, uncertainty, alternatives,
polarity, scope, hard-gate separation, rule/policy/source retirement, immutable
bindings, exact support replacement and forged permits. Dispatch tests cover
revocation before preparation and final send, concurrent revocation, lost replies,
reconciliation, atomic rollback, ambiguous writes, broken-checker replay, and real
process crashes before and after reservation persistence.

This is a bounded conformance slice with a local executor simulator. Persistent
native authority, calibrated outcome/loss models, an independent full event oracle,
the complete 64-fixture lab, search, pressure, attention and external deployment
remain separate work in [the phased plan](IMPLEMENTATION_PLAN.md).
