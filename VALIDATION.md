# Deployment event-prefix validation

The first validation-lab increment adds a versioned public event stream, actual
semantic traces, an independent cold reference model, and a development corpus.
It tests the implemented deployment fragment. It is not the full 64-fixture
benchmark, a scheduler comparison, a calibration study, or a closed-loop experiment.

```bash
uv run --no-project python -m validation_lab.run_deployment
uv run --no-project python -m unittest tests.test_deployment_traces -v
```

The command verifies pinned corpus/source hashes, runs eight fixed cases, compares
all 137 event prefixes, reopens both journals after every prefix, and checks two
isolated mutants. It writes actual JSONL traces and `report.json` under
`artifacts/deployment-validation/`. A mismatch, reference gap, runtime exception,
receipt mismatch, or surviving mutant produces a nonzero exit. Failed cases stay
in the report with their scheduled prefix counts and available actual records.
Output is written before comparison; the evaluator never repairs runtime results.

## Public profile and records

`reachability.trace_protocol` defines three versioned schemas:

| Schema | Contents |
| --- | --- |
| `deployment-initial/v1` | Context, exact product and goal IDs; loss, capacity, lease length, numerical acceptance thresholds |
| `deployment-event/v1` | Unique event ID, one command kind and its exact argument set |
| `deployment-trace/v1` | Step, input digests, actual outcome, semantic projection/digest, checker certificates and diagnostics |

The public profile fixes a DRAFT→BUILT lifecycle, tested/credential prerequisites,
one exact product, one goal slice in integer obligation units, integer renewable
slots, a three-sample health window with unit interval and exclusive unit freshness,
and an idempotent, queryable executor with permanent release fencing. A separately
certified direct forecast must meet the declared dimensionless strength threshold
and PLN confidence adequacy floor. It creates no hard assertion. Context, rule and
contract versions are fixed by this profile; cross-context and rule-change events
are outside this oracle's current scope.

Loss/capacity/lease inputs are positive integers bounded by 1000. Event time is
nonnegative, monotone and bounded by 1000. Evidence expiry is optional and exclusive.
The profile supports at most 128 unique events and twenty simultaneously relevant
hard statements. A reference exceeding its statement scope is an explicit
`OracleGap`, not an epistemic UNKNOWN or a guessed answer. All source lineage in
this fragment is direct and distinct by event ID. General derived proofs, shared
measurement roots and probabilistic deduction/revision retain their separate unit
and native contract suites.

Available events are `fact`, `forecast`, `revoke`, `tick`, `attempt`, `reserve`,
`cover`, `prepare`, `dispatch`, `reconcile`, `release`, `observation`, `sample`,
`censor`, `resume`, `account`, `complete`, and `restart`. The `dispatch` fault
argument controls the local environment transport: normal delivery, failure before
effect, or lost acknowledgement after effect. It does not change service policy.
Logical event time equals the current evidence clock; stream order is arrival
order. Independently timestamped out-of-order observations are not yet modeled.

An event can invoke multiple public service commands. For example, a wrong-product
callback first admits its literal as direct evidence and then fails registration
against the exact operation product. That evidence remains in the trace. A failed
composite event is not represented as if all earlier commands rolled back. Journal
transactions retain their existing per-command atomicity.

The actual semantic projection records:

- Accepted direct hard literals and their current support status, including wrong
  callbacks that failed subsequent operation registration.
- Historical/current forecasts and their exact evidence identities and values.
- Operation readiness and historical/current milestones; intent intervals, exact
  numerical basis and present readiness; known dispatch state/effect count.
- Historical lifecycle stage, observed goal label, outstanding/covered/open loss,
  selected commitment, separately reconciled loss and relief/reopening history.
- Current local resource usage and unresolved remote occupancy.

Diagnostics retain actual issued pre/post, execution and completion certificates,
including individual checks, revision bindings, evidence lineage and joint witnesses.
They also record context/resource revisions, appended journal-command count and
elapsed event nanoseconds. These are observations, not a normalized work budget or
an end-to-end performance comparison. Automatic evaluator restart/reference costs
are outside that per-event timer.

`instrumentation.executor_effects` is evaluator-facing simulator instrumentation,
distinct from the service's known receipt state. In a lost-ACK trace it can show an
effect while the service correctly remains uncertain. It is never passed into
service admission or action selection. There is no autonomous planner in this
conformance mode.

## Evaluator and runtime boundary

The runtime lives under `reachability/`; schedules, coverage labels, checkpoints,
the oracle and mutants live under `validation_lab/`. The evaluator package is not
included by the existing runtime package-discovery rules. Runtime import checks
reject imports from tests, supplied evaluator design, or `validation_lab`.

The runtime constructor receives only a public initial record. The evaluator passes
one observed event at a time and retains the future schedule and expected results.
The public parser rejects unknown fields, duplicate JSON fields, invalid numeric
types, nonfinite values, duplicate event IDs, unsupported schemas and malformed
time/expiry values. In particular, schedules and `expected` fields are not accepted
in either public initial state or events.

A standalone streaming worker is also available:

```bash
uv run --no-project python -m reachability.deployment_trace \
  --database-dir artifacts/my-new-trace
```

It reads a complete public initial JSON object as its first line, emits its initial
projection, then reads/emits one event/trace per line. The directory must contain no
existing service/executor journal; use a fresh path for a new run. `restart` reopens
both journals while retaining the observed stream position. A subprocess test
actually exchanges one message at a time without sending the future schedule.

The main differential harness currently runs its runtime adapter and oracle in one
Python process; the streaming worker demonstrates a separate-process transport.
Neither path provides filesystem isolation or a sandbox against hostile Python.
These are explicit import/API/data boundaries, not a claim that an adversarial
agent cannot inspect evaluator files. Process/filesystem isolation for benchmark
agents remains pending.

## Independent cold oracle

`validation_lab/deployment_oracle.py` imports only `copy` and `json`. It receives
public initial data and an observed event prefix, then reconstructs a new reference
world from scratch. It receives no service outputs, saved service snapshots,
certificate results or previously computed reference state.

Its own evidence/retirement table determines current direct assertions. Numerical
acceptance is calculated from every live reported alternative and the public
thresholds. Resource capacity is checked by enumerating integer occupancy ticks,
independently of the runtime's interval sweep. Durability uses sets of current
measurement times and an explicit three-tick window; it does not call the runtime's
witness search. Its remote effect/receipt model distinguishes physical effects,
knowledge, uncertainty and permanent fencing. Goal relief is computed from observed
windows and recorded only on explicit accounting events.

For each prefix, the evaluator compares outcome status, the entire semantic
projection, and instrumented effects. It then closes and reopens both actual
journals and compares the recovered state/effects to that same reference. Hand-set
checkpoints provide a second anchor for critical results, including ACK leaving
loss outstanding, wrong-product rejection, exact threshold boundaries and later
reopening. Generated references are not substituted for these fixed expectations.

## Corpus, ancestry and coverage

All eight cases and their transformations belong to `deployment-parent-0` and the
**development** split. None is confirmation or held-out evaluation data.
Public identifiers are neutral; family labels and control descriptions are retained
only in evaluator case files. Fixture generation does not inspect runtime outcomes
or reject cases based on model performance.

| Case | Controls exercised within the deployment fragment |
| --- | --- |
| d01 | Valid deployment, prediction/credential expiry, observed completion, later failure/reopening |
| d02 | Missing prerequisite, credential revocation, alternate direct support |
| d03 | Lost ACK, recovered uncertainty, forecast retirement, reconciliation, one effect |
| d04 | Similar-looking wrong product, delayed exact callback, blocked then valid completion |
| d05 | Contested last slot, prepared-request recovery, expired lease with unresolved occupancy, fenced release |
| d06 | Exact strength/confidence boundary, changed numerical basis, new attempt after lease expiry |
| d07 | Censoring, rejected sample registration while censored, fresh resumed monitoring window |
| d08 | Overlapping coverage, revoked sample, recovery of observed health, freshness reopening |

These partially exercise F01, F08–F12, F14 and F16. They supply **zero claims of
family-complete fixtures** against the 64-fixture target. Missing family mechanisms
such as F01 distractor search, F08 indexing, general F09 concurrency and wider F16
fault injection are not inferred from these examples. Their existing unit coverage
also does not automatically count as complete benchmark fixtures.

The tests additionally run twelve seeded stateful cases (seed 8417, 251 prefixes),
with every prefix cold-checked and recovered. They vary health observations,
censoring/resumption, credential expiry and transport faults without outcome-based
filtering. Metamorphic checks rename identities while preserving parent ancestry,
and reorder commuting initial observations. Further checks exercise capacity two,
exact lease expiry, rejected composite events and release before an effect.

`deployment_cases/manifest.json` pins the fixed public/evaluator files, generator,
oracle, harness, mutants, protocol and runtime source files. To deliberately
regenerate the development corpus and refresh receipts after a reviewed change:

```bash
uv run --no-project python -m validation_lab.generate_deployment_cases
```

Regeneration is explicit; validation does not quietly refresh changed expectations.

## Mutation witnesses and remaining work

The unmodified corpus must pass before the same events are run under evaluator-only
mutations. Invocation canaries prove each changed branch executed. The lab records
the first divergent prefix and writes the offending actual trace:

| Mutant | Witness | Reference → faulty output |
| --- | --- | --- |
| M06 ACK treated as durable success | d01, prefix 7, event e006 | PENDING → OBSERVED_SUCCESS immediately after acceptance |
| M11 censored outcome labeled failure | d07, prefix 3, event e002 | CENSORED → OBSERVED_FAILURE |

The witnesses are first divergent prefixes, not generally minimized event sets.
M01–M04 retain their existing unit witnesses. M05, M07–M10 and M12 remain open.

Next extend the public trace and independent reference to grounded rule admission,
multiple contexts, alternate derivations and lineage reuse. Expand the family/control
matrix before implementing B0 and comparative scheduling. Complete family coverage,
general event shrinking, deterministic concurrent interleavings, hidden-world models,
OS isolation, benchmark cost budgets and all pressure/attention experiments remain
open in [the phased plan](IMPLEMENTATION_PLAN.md).
