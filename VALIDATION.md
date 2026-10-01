# Event-prefix validation

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
measurement roots are covered by the separate admission profile below. Numerical
deduction retains its separate unit and native contract suites.

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

## Grounded admission profile

The additive admission profile leaves the deployment v1 wire format unchanged.
It drives the existing public hard/numerical service APIs using grounded rules,
explicit contexts and exact prior-event references:

```bash
uv run --no-project python -m validation_lab.run_admission
uv run --no-project python -m validation_lab.run_admission --native \
  --output artifacts/native-admission-validation
uv run --no-project python -m unittest tests.test_admission_traces -v
```

The default command uses deterministic checked PLN arithmetic. `--native` uses
the pinned PeTTa/PLN adapter for inference; the authority continues to check every
proposal before commit. Both modes compare the same cold reference. The optional
integration suite also verifies actual AtomSpace projections before and after
journal replay. AtomSpace remains a disposable diagnostic projection.

| Schema | Public contents |
| --- | --- |
| `admission-initial/v1` | One to eight neutral atom IDs and up to eight grounded rules with immutable revisions, ordered premises and a conclusion |
| `admission-event/v1` | Unique event ID, command kind and exact argument fields |
| `admission-trace/v1` | Input digests, outcome, historical/current hard and numerical records, exact proof aliases, query statuses, certificates and context revisions |

Signed integers refer to declared atoms; sign denotes polarity. A context contains
up to eight assumptions and 32 CNF clauses of up to eight literals each. At most
four contexts and 128 events are supported per trace. Rules have no variables or
context inheritance. Truth components are finite binary64 values with strength
in `[0,1]` and confidence in `[0,1)`. Time is an integer in `[0,1000]`; evidence
expiry is exclusive. These bounds are public validation limits, not search budgets.

The event kinds are `context`, `evidence`, `estimate`, `adopt`, `derive`, `rule`,
`policy`, `tick`, `revoke`, `independence`, `revise`, `revoke_model` and `restart`.
`context` opens a hard environment and configures the fixed sensor probability
policy. Evidence/estimate events create reports under their event IDs and attempt
admission. `adopt` explicitly requests hard admission of an existing report;
numerical reports alone never become hard assertions. `derive` binds ordered hard
premise event aliases; `revise` binds numerical aliases plus a registered model ID
(or null, which cannot authorize revision). A declaration carries a justification
and two exact numerical references; distinct report IDs cannot override shared roots.
`rule` replaces an existing rule with a caller-supplied expected revision;
`policy` replaces the hard constraints using the current context revision.

Successful admission events become aliases for the actual committed belief
revision. Duplicate admissions can alias the same record. The projection retains
exact parent aliases, leaf evidence IDs, lineage roots, historical/current state,
and separate hard/numerical query statuses for every signed declared atom. An old
retired proof stays retired when another proof of the same literal becomes usable.
Re-admission must occur explicitly and can produce a distinct revision. Context
assumptions constrain consistency but are not automatically admitted premises.

Malformed messages, hidden fields and duplicate event IDs fail at the stream
boundary. Valid commands requesting unavailable references, immutable identity
redefinitions or backwards clocks produce recorded rejection outcomes. Missing
proof premises are UNKNOWN; foreign premises FAIL; retired premises are STALE.
Successful earlier commands in a composite event remain recorded when admission
later fails, so a blocked report can be explicitly readmitted after a policy or
support change. These are per-command journal transactions.

`validation_lab/admission_oracle.py` imports only `copy` and `fractions`. It
reconstructs each prefix from scratch without service output. It enumerates all
`2^N` Boolean assignments for hard consistency instead of calling the DPLL checker.
Its separate proof graph tracks exact dependencies, alternatives, rule/policy
replacement, context-local clocks and full leaf lineage. Numerical revision uses
rational operations rounded after each primitive required by the pinned binary64
expression. Numerical comparisons are exact, with no tolerance that could admit
changed values. Scope gaps and internal reference-model errors remain harness
errors; they are not converted into epistemic UNKNOWN.

Sixteen fixed cases cover four controls within each scoped mechanism:

| Cases | Family mechanism | Positive / blocked / boundary / revision change |
| --- | --- | --- |
| a01–a04 | F01 ordered AND premises | Complete joint proof / missing or wrong ordered premise / exact expiry / replaced rule and dependent proofs |
| a05–a08 | F02 joint consistency | Compatible polarity / globally conflicting assertion / delayed readmission / jointly incompatible replacement policy |
| a09–a12 | F04 context separation | Same atoms in incompatible contexts / cross-context proof and numerical references / separate clocks / local policy and global rule replacement |
| a13–a16 | F05 lineage reuse | Explicit independent revision / shared roots and alternative proof diamond / zero evidence weight / exact model and leaf retirement |

All are development descendants of `admission-parent-0`. The manifest publishes
the family/control mapping and hashes of sources and fixtures. There are 127 fixed
prefixes and eight seed-17041 cases adding 168 prefixes, each compared before and
after checked journal replay. Additional tests cover identity renaming, commuting
contexts, eight-atom bounds, negative ordered premises, nested numerical revision,
subnormal/near-one binary64 boundaries and unmodified raw mutation output.

These remain **zero family-complete fixture claims**: F01 search/distractor behavior,
F04 changing goals and pressure, and F05 broader noisy hidden-source models are not
implemented by these admission controls. They establish bounded admission semantics,
not inference search or calibrated prediction. A scoped deployment B0 controller
is described below; normalized work comparisons remain pending.

To deliberately regenerate this corpus and refresh its source receipts:

```bash
uv run --no-project python -m validation_lab.generate_admission_cases
```

Both corpus manifests bind all runtime Python sources. After a runtime change,
explicitly regenerate both corpora. Validation never refreshes receipts itself.
The admission worker is `python -m reachability.admission_trace --database-dir PATH`
(optionally `--native`), with the same one-line initial/event exchange as deployment.
`restart` reopens the authority while the stream adapter retains observed aliases
and position; a fresh worker cannot resume an arbitrary old stream directory.
The normal harness still shares a process with its adapter, without OS isolation.

## Bounded B0 closed-loop deployment

`reachability/b0.py` implements `B0-finite-deployment/v1`: full recomputation and
deterministic best-first selection over the existing deployment dependency graph.
It uses the existing service's exact admission, numerical, resource, dispatch and
completion gates and operation ledger. This is the first scoped B0 implementation;
general grounded-rule search, beam planning and multi-goal portfolios remain open.

```bash
uv run --no-project python -m validation_lab.run_b0
uv run --no-project python -m unittest tests.test_b0 -v
```

The public `deployment-b0-public/v1` record contains the unchanged deployment
initial state, up to sixteen observation capabilities, their declared integer
costs, and a limit of one to four attempts. Capabilities expose neutral IDs and one
of `tested`, `credential`, `forecast`, `outcome` or `monitor`. They do not expose
availability times, future values, outcome delays, transport faults or reference
answers. The controller receives only a `read()`/`execute(candidate)` port. Its
projection parser rejects extra top-level fields such as physical executor effects.

The provider recomputes ready work from current scoped support and the operation
ledger. Missing prerequisite observations precede attempt creation and reservation;
an eligible intent permits dispatch; uncertain dispatch requires reconciliation;
accepted submission enables outcome queries; product observations enable sampled
monitoring. Observed goal success permits accounting, an applicable completion
transition and fenced resource release. Submission readiness is not reimposed on
later independently observed completion. Old unsubmitted leases can expire before
a new attempt; the provider does not invent cancellation or release receipts.

`deployment-candidate/v1` identifies an action by a content digest and carries
its arguments, remaining-stage distance and observation cost. Selection orders by
distance, then cost, then neutral public kind/argument order. Distance is a heuristic
over this fixed protocol, not an optimal cost or predicted relief. Failed cheap
probes do not indefinitely suppress costlier alternatives. A probe is issued at
most once per candidate and logical tick, so adding historical wrong reports cannot
cause unlimited polling at the same time. Only an explicit `wait` advances logical
time; certification and accounting do not consume simulated health freshness.

Candidate filtering is advisory. A selected candidate can become stale before
execution. It must still pass the service's normal checks. Case b06 revokes a
credential after selection and before dispatch: the old request is blocked, the
local lease expires, and the controller later obtains fresh evidence and uses a
new attempt. A lost reply instead triggers reconciliation; an observed absent
effect permits an idempotent retry of the same request under current gates.

Each `Budget` independently caps issued actions (0–64), full recomputations
(0–128), candidate visits (0–4096), and declared observation cost (0–64000).
The common dependency expansion, each attempt and each capability consume a visit,
including blocked entries. If enumeration runs out of visits, its partial frontier
is discarded and no candidate is selected. Empty/failed observations still consume
their declared cost. A controller is limited to 128 issued requests; the underlying
trace additionally retains its 128-event and twenty-statement bounds. Exceeding a
runtime profile is an error rather than an invented valid result.

`deployment-b0-step/v1` logs the public-view digest, full candidate frontier,
selected request, actual public receipt and cumulative work. The work ledger records
state reads; hard, forecast and attempt rows loaded per read; candidate visits and
returned candidates; actions; observation requests/cost; emitted public events;
admission journal commands; and captured certificates. Row loads do not count every
internal predicate evaluation. Captured certificates and admission journal commands
are the existing adapter's diagnostics, not all checker steps or executor writes.
Elapsed time includes the evaluator's prefix checking and recovery when those are
enabled. Solver internals, native projection, memory peaks, total persistence I/O
and normalized work/wall-time comparisons remain unmeasured. These counters must
not be interpreted as a complete computational cost model.

`deployment-b0-checkpoint/v1` binds the public profile, issued-request fingerprints
and step count. Tests restore it between individual requests while reopening the
actual journals and obtain the same selected action/event stream. This checkpoint
is scheduling history, never an admission permit. It does not provide an atomic
transaction spanning controller history and remote execution, or a fresh worker's
reconstruction of all stream-adapter metadata after a mid-request crash.

The evaluator's `DeploymentWorld` owns capability responses, physical effect time,
scheduled hooks and transport faults. Observation requests determine which reports
arrive; dispatch causes physical effects that enable later outcome observations.
The controller does not receive the hidden world or instrumented physical effects.
Every emitted runtime record is written before the cold oracle compares it and
before the authority is reopened. A selected request is also logged before it
executes, preserving evidence if the adapter or comparator raises an exception.
The main harness remains in one Python process without filesystem isolation.

| Case | Closed-loop control |
| --- | --- |
| b01 | Valid prerequisites, delayed outcome, observed health, completion and release |
| b02 | Empty cheap probe followed by a more expensive available alternative |
| b03 | Credential observable only after a delay |
| b04 | Lost acknowledgement, reconciliation and one physical effect |
| b05 | Failure before effect, reconciliation and idempotent retry |
| b06 | Credential revocation between selection and dispatch, then fresh attempt |
| b07 | Similar-looking wrong product followed by an exact callback |
| b08 | Negative samples followed by a healthy window |
| b09 | Unavailable prerequisite and exhausted action budget |
| b10 | Exhausted observation-cost budget |
| b11 | Exhausted candidate-enumeration budget |
| b12 | Missing samples and delayed observed durability |

The twelve fixed cases emit 197 compared/recovered event prefixes. Nine establish
observed goal success; b09–b11 intentionally remain unresolved. A passing case
means its declared contract/expectation passed, not that its goal was achieved.
Reports separately retain observed goal completion, outstanding/accounted loss,
stage, physical effects and stopping reason. Refusing every action fails the
positive control. Six seeded worlds (seed 2601) add 135 compared/recovered prefixes
with action-dependent variation and no outcome-based filtering. All cases remain development descendants of
`deployment-b0-parent-0`, with zero family-complete fixture claims.

Public capability files and evaluator worlds are separate files. The manifest
also pins a separate conformance mutation fixture, all runtime sources, the
generator, environment, oracle, harness and mutants. Refresh deliberately with
`python -m validation_lab.generate_b0_cases`; after shared runtime changes refresh
the admission and deployment corpus receipts too. The report contains one
controller's closed-loop results and a separately labeled M07 conformance witness;
faulty variants are not compared as task-performance competitors.

## Mutation witnesses and remaining work

The unmodified corpus must pass before the same events are run under evaluator-only
mutations. Invocation canaries prove each changed branch executed. The lab records
the first divergent prefix and writes the offending actual trace:

| Mutant | Witness | Reference → faulty output |
| --- | --- | --- |
| M05 shared lineage treated as independent evidence | a14, prefix 5, event e004 | UNKNOWN → PASS; duplicated reports gain confidence 2/3 |
| M06 ACK treated as durable success | d01, prefix 7, event e006 | PENDING → OBSERVED_SUCCESS immediately after acceptance |
| M07 similar product treated as exact | b0-m07, prefix 2, event m1 | FAIL → PASS for exact-product observation of `p00` instead of `p0` |
| M08 inserted blocker misses invalidation dependents | i01, prefix 3, event policy | Unrelated fact 2 survives → all facts retired by consistency fallback |
| M10 capacity checked outside atomic reservation | i06, prefix 5, event rb | STALE → PASS; two claims on one unit |
| M11 censored outcome labeled failure | d07, prefix 3, event e002 | CENSORED → OBSERVED_FAILURE |

The table records the original first divergent prefixes. The bounded reducer
now produces deletion-minimal event sets for all six trace witnesses.
M05 replaces shared measurement roots with separate report IDs during numerical
revision; its canary confirms this defect ran. It is an evaluator-only patch and
is removed before subsequent controls. M01–M04 retain their unit witnesses.
M07 changes only the product-name matching branch while leaving the remaining
observation checks enabled. Its two-event witness creates an attempt and presents
a wrong-product report. The unmodified control fails registration; the mutant
registers the wrong product. Tests delete each event in turn and confirm that
neither shortened stream detects the mutant. This is deletion minimal in the
declared profile; the new reducer independently reproduces that result.
The interleaving profile below supplies M08/M10; M09 and M12 remain open.

Next extend deterministic interleavings to dispatch and acknowledgement races.
Complete family coverage, argument/initial-state shrinking, hidden-world models,
OS isolation, benchmark cost budgets and all pressure/attention experiments remain
open in [the phased plan](IMPLEMENTATION_PLAN.md).

## Bounded grounded proof planning

Run `uv run --no-project python -m validation_lab.run_planning`. This is a second
finite B0 profile, separate from the deployment controller. Public files contain
only the rule/cost contract, conjunctive goals and already delivered initial
observations. Evaluator files contain control labels, expectations and future
public edits. The controller receives only a detached current snapshot and a
first-step execution port. Import/schema boundaries are tested; this remains a
shared-process harness, not an OS sandbox.

The finite contract declares at most eight atoms, eight grounded rules, eight
conjunctive signed goals, eight planning steps and an absolute deadline at integer
time 0–16. Each rule costs 1–100 proof-work credits and takes 0–8 logical ticks;
the episode has at most 1,000 credits. Rule identities retain their declared costs
when an observed registry edit changes a rule version. Every current hard support
in the selected context carries its exact public alias and earliest leaf expiry.
Assumptions constrain possible worlds but never become accepted premises. Numeric
estimates and foreign-context beliefs cannot seed this hard planner.

Uniform-cost forward search minimizes the tuple `(total declared work, absolute
finish time, step count)` for the current frozen snapshot. It retains all distinct
literal/lifetime alternatives, exact ordered parents, seeded cycles and shared
subproofs. Inference must finish strictly before every premise expires. Every
successor checks the full hard environment against the CNF policy. Integer waits
may end before the next evidence expiry: p09 waits until tick 1, then performs a
two-tick derivation after a blocker expires at tick 3. Waiting until expiry would
miss this plan because the required parent expires at tick 4.

State and transition limits count popped states, attempted rules/waits and parent
combinations. Incomplete search returns `BUDGET_EXHAUSTED` with no executable
partial plan, distinct from exhaustively established `UNREACHABLE`. Joint checks,
duplicate states and loaded supports are reported separately. These are search
counters, not normalized computational measurements; DPLL internals, memory and
storage/native I/O remain outside the model.

The independent reference imports only `itertools`. It enumerates Boolean worlds
and layered lifetime states, including redundant derivations, without runtime
search, heap ordering, DPLL or runtime pruning. It receives the same public frozen
problem and no future edits. Its own state/transition limits return `NOT_COMPUTED`
without an optimality claim. A separate witness replay checks the entire proposed
plan, including symbolic references to earlier steps, all ordered premises, every
joint state, total cost/time and final goals. Actual proposals are logged before
any reference call; reference failure remains a failed comparison with the raw
proposal retained.

| Controls | Coverage |
| --- | --- |
| p01–p04 | Ordered AND chain, shared subproof for two goals, unseeded/seeded cycle |
| p05–p07, p22 | Complete cost/time alternatives and combined work limits |
| p08–p10 | Jointly conflicting goals, required wait, exclusive expiry boundary |
| p11–p13 | Assumptions, numeric estimates and foreign contexts cannot supply hard premises |
| p14–p16 | Revocation, rule replacement and policy edits after selection |
| p17–p18 | Explicit state/transition exhaustion without execution |
| p19–p21 | Exact support lifetimes, already observed goal, repeated/negative premises |

The 22 fixed controls produce 77 compared/recovered admission event prefixes,
with 11 goal completions and 11 expected unresolved outcomes. Twelve seed-4103
graphs add 29 prefixes and three completions without outcome filtering. All
34 cases are development descendants of `planning-parent-0`, with zero complete
family fixtures. F03 labels here cover declared proof-work/time alternatives;
they do not establish physical renewable/consumable resource planning. The frozen
exact reference does not predict hidden future edits or establish globally optimal
closed-loop behavior. No new designated mutation witness is claimed.

Each request replans, then submits only the first step. A changed snapshot digest
or rule version returns `STALE` without issuing a command or charging work. Once
issued, a step consumes its declared credits and step quota even if the authority
rejects its premises. Time advancement and hard derivation use the existing
admission trace adapter and pre/infer/post/commit checks. All resulting event
prefixes are compared with the cold admission oracle and recovered journal state.
Native tests also compare actual AtomSpace projections before/after recovery for
chains, expiry, revocation and rule replacement.

Proof-work quotas and observed stream metadata survive service reopenings within
the same wrapper, and recreating the stateless controller between requests yields
the same events. They are synchronous wrapper state, not durable reservations or
an atomic controller/action crash transaction. Physical execution remains under
the existing resource/intent/dispatch authority. This increment does not change
that authority, the journal schema, original design inputs or their hashes.

The corpus receipt pins public/evaluator files, all runtime modules, the generator,
harness and independent references. Regenerate deliberately with
`python -m validation_lab.generate_planning_cases`; regenerate the admission,
deployment and deployment-B0 receipts after shared runtime changes. Validation
checks receipts without silently refreshing them.

## Serial renewable-resource execution portfolios

Run `uv run --no-project python -m validation_lab.run_resource_planning`.
This finite B0 profile chooses one complete immutable mode for each outstanding
product, including resource quantities/units, cost and predicted duration. It
supports at most three independent products, three renewable resources with
integer capacities 0–4, and six modes. Each mode lasts 1–4 logical ticks and costs
1–20 declared credits; the episode deadline is at most tick 8 and its budget is
at most 100 credits. Every product has its own directly observed readiness fact
and grounded lifecycle. This is separate from grounded proof search and from the
original single-deployment numerical/health controller.

The runtime enumerates serial schedules, checking the complete combined interval
portfolio against existing local leases using the service's interval-capacity
checker. Every mode retains its complete resource packet; resources, duration and
cost cannot be taken from different alternatives. It minimizes `(declared cost,
final predicted completion time)` and uses neutral public identity for ties.
Prerequisites must remain valid strictly beyond predicted completion. Readiness
also includes the lifecycle source stage: a terminal episode with revoked
product support cannot silently execute its original forward edge again. Revoking
an observation retires its current view while preserving historical lifecycle events.
Known local leases end at exclusive boundaries. Any resource with unresolved remote occupancy
is unavailable throughout the frozen planning horizon, even after its lease ends.
The current service does not admit concurrent reuse of such resources, including
spare capacity; this planner preserves that rule.

The independent reference imports only `copy` and `itertools`. It enumerates job
permutations, mode combinations and integer start-time tuples, checks unit-time
occupancy instead of reusing the runtime interval sweep, and validates the complete
returned witness. It receives the same frozen public snapshot without future
responses, hooks or actual search results. Its 200,000-candidate limit returns
`NOT_COMPUTED`. Runtime search defaults to 50,000 candidate visits (maximum
500,000); exhaustion discards any incumbent and returns `BUDGET_EXHAUSTED`.
`NO_CERTIFIABLE_PLAN` describes the current bounded model; it does not prove that
future observations or reconciliation cannot enable a plan.

Schedules are predictions conditional on the declared observation durations.
They are not reservations, completion evidence or permission to free resources.
The controller executes only the first reservation after checking its snapshot
binding and complete immutable contract. Actual service certificates bind current
knowledge, operation and resource revisions; the service checks them again when
publishing the intent. Dispatch independently checks current prerequisites and
occupancy. Losing acknowledgement triggers reconciliation, and a failed first
send may retry the same idempotent request. No ACK establishes product completion.

Observation requests deliver evaluator-owned reports only after an actual simulated
effect and the response's availability time. The authority checks the exact
attempt/product milestones and outcome support before advancing the lifecycle.
The controller then requests a permanent executor fence before planning the next
job. Wrong-product reports remain failed observations with their actual partial
hard-record effects retained; they never count as completion. Missing reports or
late outcomes leave explicit unresolved states or force a new schedule. Revoked
readiness after reservation stops this controller with its local intent retained;
it does not fabricate replacement support or claim automatic cancellation.

| Controls | Coverage |
| --- | --- |
| r01–r03 | Cheap/fast alternatives and rejection of mixed cost/time pieces |
| r04–r06 | Half-open lease boundary, aggregate capacity and complete multi-resource packets |
| r07–r08 | Occupancy after selection and readiness revoked before dispatch |
| r09–r11 | Lost acknowledgement, failed first send and wrong then correct product |
| r12–r13 | Missing outcome and unresolved remote occupancy after lease expiry |
| r14–r16 | Joint serial portfolio cost/time and exclusive prerequisite expiry |
| r17–r18 | Explicit enumeration exhaustion and missing readiness |
| r19 | New remote occupancy blocks final dispatch despite an existing local intent |
| r20 | A late observed first completion invalidates the remaining predicted schedule |

The twenty fixed controls produce 119 compared/recovered prefixes, with eleven
completed and nine expected unresolved episodes. Eight seed-5107 cases add 44
prefixes and five completions, without outcome filtering. A cold event model
reconstructs readiness facts, retirement, operation milestones, lifecycle
completion, local/remote occupancy, charged costs and executor effects after every
actual public event. Records are logged before comparison, then both authority
and executor journals are reopened and checked. Native tests also compare actual
AtomSpace hard-belief, resource, reservation, intent and dispatch projections before
and after recovery. These are development descendants of
`resource-planning-parent-0`; none is a family-complete fixture or a new designated
mutation witness.

Counters separate declared execution cost from search candidate/capacity visits,
issued requests, public events, journal commands and captured certificates. Setup
costs, internal checker operations, total I/O and memory are not normalized.
Public events include hook deliveries and rejected commands; failed issued
reservations consume their declared credits, while stale selection alone consumes
none. Search proposals are logged before the independent reference is called.
An always-idle controller fails the positive control.

The controller and adapter are synchronous and operate in a shared process.
Observed-stream metadata, the active selection and charged-credit ledger survive
service reopenings in the same wrapper; they are not a fresh-process checkpoint
or an atomic controller/executor crash transaction. Resource ownership and request
fencing remain in the actual durable service/executor journals. Concurrent
execution, consumables, renewal, cross-product dependencies, combined proof and
execution planning, optimal behavior under future changes and comparative benefit
remain open. Native storage remains a disposable projection, not commit authority.

The new corpus receipt pins separate public/evaluator files and every runtime
module, generator, harness and independent reference. Refresh explicitly with
`python -m validation_lab.generate_resource_planning_cases`. Shared runtime changes
also require refreshing all four earlier corpus receipts; validators never rewrite
receipts automatically. The original design pack and core authority/journal
schemas are unchanged.

## Bounded event-trace shrinking

Run the four source-pinned development seeds with a fresh destination:

```sh
uv run --no-project python -m validation_lab.run_shrink --output artifacts/shrink-run-1
uv run --no-project python -m validation_lab.run_shrink --replay-bundle artifacts/shrink-run-1/M05 --output artifacts/shrink-replay-1
```

The reusable `validation_lab.trace_shrink.shrink` engine accepts at most 128
uniquely identified events and a replay predicate. It tries contiguous chunk
deletions, then single-event deletions, without changing event identities,
arguments, references or order. Each accepted reduction restarts the necessary
deletion audit. A final fresh replay must reproduce the original structured
signature: profile, initial-state digest, mutant, event ID, comparison path and
exact JSON expected/actual values. Prefix positions can change when events are
removed; they are evidence, not part of failure identity.

`ReplayPredicate` supports the strict admission and deployment protocols and
existing M05/M06/M07/M11 mutation branches. Each candidate first runs against the
unmodified service and independent cold oracle, reopening durable journals after
every event. Only a passing control permits mutation replay. A mutation invocation
canary and a matching first divergence are required to accept a deletion. The
original seed's positional checkpoints are checked on its first replay; reduced
streams use the independent prefix oracle, without transplanting those positions.
The runtime receives only public initial data and one event at a time.

| Mutant | Original events | Reduced events | Predicate calls | Preserved failure |
| --- | ---: | ---: | ---: | --- |
| M05 | 12 | 5 | 25 | e004: outcome.status UNKNOWN → PASS |
| M06 | 23 | 6 | 47 | e006: projection.goal.label PENDING → OBSERVED_SUCCESS |
| M07 | 2 | 2 | 6 | m1: outcome.status FAIL → PASS |
| M11 | 13 | 1 | 10 | e002: projection.goal.label CENSORED → OBSERVED_FAILURE |

All fourteen final single-event deletion checks remove the required divergence;
the four final witnesses pass fresh replays. The 88 predicate calls include all
attempts, rejected deletions, originals and final replays. The native integration
test separately reproduces reduced M05 with actual pinned PLN inference and
checks all five deletions. These counts describe validation work, not normalized
runtime or performance improvements. No new designated mutant is claimed.

The default limit is 256 predicate calls; `--max-evaluations` accepts 0–4096.
Exhaustion preserves the last witnessed candidate, reports `BUDGET_EXHAUSTED`, and
does not claim minimality. A zero budget has no witnessed candidate. A failed
initial witness yields `SEED_NOT_WITNESSED`; a failed final replay yields
`FINAL_REPLAY_FAILED`. Unsupported oracle cases and unexpected errors remain
explicit `ORACLE_GAP`/`ERROR` evidence and cannot prove a deletion impossible.
If either occurs in the final deletion audit, status is `MINIMALITY_UNPROVEN`.
Protocol rejection and a failing unmodified control exclude a candidate from this
declared witness domain. A different failure signature also cannot replace the
original. The CLI exits nonzero for incomplete or unexpected reductions.

Each bundle includes `seed.json`, `original.json`, `reduced.json`, a flushed
`attempts.jsonl`, and per-trial candidate, assessment, control and mutant files.
Actual outputs are logged before oracle comparison, including the offending
mutation record. `report.json` binds source hashes, ancestry, replay outcomes,
accepted reductions, deletion audits and a complete file inventory. Output
directories cannot be reused. `verify_bundle` checks recorded file integrity and
evidence consistency; it does not execute the runtime or authenticate who made
the receipt. `--replay-bundle` verifies current source bindings, reruns the saved
seed and requires identical semantic decisions. Raw elapsed times and generated
certificate IDs can differ across runs and remain preserved in each bundle.

The separate `validation_lab/shrink_cases/manifest.json` pins evaluator/runtime
sources, the native dependency lock, seeds, expected semantic decisions and the
three upstream corpus receipts/fixtures. Reductions retain their original
development split and parent instance; they create no held-out or family-complete
fixtures. Regenerate explicitly with
`uv run --no-project python -m validation_lab.generate_shrink_cases --output artifacts/shrink-generation-1`.
Validation never refreshes receipts automatically. The five earlier corpora,
runtime authority and original design files are unchanged.

Minimality means no **single** whole-event deletion preserves this exact witness
and passing control. It is not a globally shortest trace: multiple simultaneous
deletions can expose a smaller witness even after this audit passes. Initial-state
or argument simplification, identity renaming, dependency repair, arbitrary new
mutants, concurrent schedule reduction, process isolation and wall-clock bounds
are not provided. Mutation patches remain process-global and replays run
sequentially within each evaluator process.

## Deterministic two-worker interleavings

```sh
uv run --no-project python -m validation_lab.run_interleaving --output artifacts/interleaving-run-1
```

The bounded public profile contains three grounded atoms, direct evidence,
two independent lifecycle attempts, one renewable resource with capacity 0–3,
one-unit claims and fixed four-tick leases. Initial reports are registered before
the event stream; selected initial facts are explicitly admitted. It supports
at most 64 unique events: read, prepare, commit, policy, certify and reserve.
Policies have at most four clauses of three literals. Actor-local certificates
bind separate preparation and publication calls. Public messages reject evaluator
labels and scheduling fields. There are no dispatched external effects in this
profile.

Admission events run in a declared order at public API boundaries. The reservation
controller additionally uses two actual threads and pauses the first worker after
the complete reservation checks and before publication. The second worker then
requests the same real authority RLock. Ownership records establish that it is
blocked; the controller releases the first worker to publish and observes the
second worker's stale-certificate rejection. The controller preserves the real
lock and introduces no production bypass. Watchdog timeouts report evaluator
failure; elapsed time is never evidence that a worker was blocked.
Paired checkpoints require fresh attempts with no prior reservation command in
the schedule; historical retries remain serial. This bound is validated before
threads start, because a historical retry can pass without advancing occupancy.

The production reservation implementation now has separate private preparation
and publication helpers, both called inside the original `_mutate` transaction
and RLock. Certificate checks, prerequisite replay, capacity checks, journal
publication and duplicate-intent behavior retain their existing contracts.
This exposes a precise evaluation boundary without adding scheduler controls to
the public service API or changing journal schemas.

The cold oracle imports only the standard library. It enumerates all eight
Boolean assignments and reconstructs accepted facts, policy epochs, actor-bound
certificates and integer occupancy from the public initial state and event prefix.
It does not use the runtime checker, reservation helpers or actual certificates.
There are 22 development cases: sixteen direct controls and all six order-preserving
merges of the two workers' certify/reserve sequences. Nine cases configure a
reservation pair; two of those reject before reaching the check checkpoint.
Controls include both first-worker priorities, missing prerequisites, zero
capacity, unrelated and joint blockers, inconsistent policies, wrong ownership,
stale admission/reservation and successful fresh two-unit reservations. Six
additional uncontrolled two-thread rounds check last-unit exclusion.

All 79 emitted prefixes match the cold oracle. Recovery runs at 70 quiescent
boundaries, after individual serial events or after both workers finish a pair.
There is deliberately no service reopening in the middle of an active
transaction. This checks actual durable authority state plus certificates retained
by the same wrapper; it is not a fresh-process controller recovery protocol.
Native tests project actual admission and resource/intent records before and
after recovery for blocker and last-unit episodes.

| Mutant | Changed branch | Original → reduced events | Predicate calls | Preserved divergence |
| --- | --- | ---: | ---: | --- |
| M08 | Newly inserted blockers omit their invalidation dependents | 5 → 1 | 6 | policy: usable facts `[2]` → `[]` |
| M10 | Complete checks run before the atomic reservation transaction | 6 → 4 | 21 | rb: STALE → PASS; occupancy 2 with capacity 1 |

M08 retains all revision checks and the mandatory full-state consistency check.
Its missed dependency set makes that fallback retire the whole inconsistent
bundle, unnecessarily losing the unrelated valid fact. The witness detects this
loss of support; it does **not** claim that an inconsistent state or stale commit
was accepted. This finite profile has no optimized constraint index: the mutation
models its missed-dependency failure at the existing invalidation boundary.
Removing the policy event removes the divergence, with initial facts held fixed.

M10 runs the same preparation checks before acquiring the publication transaction.
The controller records both workers finishing those checks without holding the
authority lock, then publishes them in the declared order. Both claims pass and
the raw record shows over-allocation. The unmodified control holds the lock across
checking and publication and publishes only one claim. The four reduced events certify
both workers and reserve both; every single deletion removes the exact failure.
The defect is an evaluator-only patch, removed before the next control.

Both witnesses require passing unmodified cold-model/recovery controls, invocation
canaries, identical first-divergence signatures and fresh final replays. Their
signatures also bind the unchanged evaluator schedule. Dropping one scheduled
endpoint leaves the surviving command serial; references are not repaired and
remaining events keep their identities and arguments. All five final deletion
checks return no witness. This is whole-event deletion minimality with fixed
initial state and schedule, not global or schedule minimality.

The corpus separates public initial files, evaluator events/schedules and pinned
mutation decisions. Every candidate, schedule checkpoint, actual output and
assessment is retained before comparison in a fresh output directory. The root
report pins the complete output inventory, current sources and corpus ancestry;
`validation_lab.run_interleaving.verify_report(path)` checks those receipts, all
recorded unmodified prefixes and the pinned reduction decisions. Rerunning the
CLI performs fresh executions. Regenerate explicitly with
`uv run --no-project python -m validation_lab.generate_interleaving_cases --output artifacts/interleaving-generation-1`.
The existing six corpus receipts were refreshed for the helper refactor and new
runtime modules; their expected outcomes and earlier reductions are unchanged.

These cases share `interleaving-parent-0` in the development split. They add no
family-complete fixtures, scheduling-performance claims, arbitrary thread-schedule
exploration, process isolation or proof of general concurrency safety. The next
section extends controlled scheduling to final dispatch and lease-expiry/
acknowledgement races. M09/M12 still await their pressure and transport mechanisms,
and the 64-family-fixture target remains open.

## Controlled dispatch and delivery races

Run `uv run --no-project python -m validation_lab.run_dispatch_races --output artifacts/dispatch-race-run-1`
with a new directory. The 24 development cases compare 227 completed prefixes and
reopen both real journals at 220 quiescent boundaries. The runtime accepts one
strict `dispatch-race-event/v1` command at a time; the separate evaluator schedule
selects one adjacent dispatch/revocation or dispatch/clock pair. Four cases pause
before send or before acknowledgement, and three paired controls finish without
sending because the dispatch is rejected or already accepted.

At a submission checkpoint, the first thread owns the actual authority RLock. The
second thread tries that same lock with `blocking=False`; failure proves blocking
without a timing assumption. The evaluator then holds the contender outside the
lock until the first completed state is recorded. It does not add an outer lock
around dispatch. A test replacing dispatch with an unlocked send is detected.
Watchdog timeouts terminate broken evaluator runs; they never count as a semantic
PASS or proof of blocking. Recovery starts only after both threads are quiescent.

The public adapter stores only requests and receipts it has actually observed.
`queued` retains an exact request without submitting it yet; `arrive` later sends
it to the real simulator. `lost_reply` retains the real accepted receipt while
leaving the authority uncertain; `deliver` supplies that immutable receipt later.
`before_effect` retains no deliverable request. Duplicate arrivals use the same
idempotency identity. No future delivery schedule or expected result is passed to
the runtime. The inbox is in memory and survives same-wrapper journal reopenings;
reconstructing it in a fresh process is outside this profile.

The cold evaluator model builds on the independent standard-library deployment
model and separately enumerates remote request state, global executor sequence,
immutable packet contents and local receipt knowledge. It imports no runtime
service or projection code. Compared output includes hard and numerical support,
intent and dispatch state, renewable occupancy and uncertainty, lifecycle/goal
state, transport buffers, remote state and historical effect counts. The cases
establish that:

- Revocation or lease expiry before the final gate rejects sending; restoring a
  credential permits a valid send. Changes contending inside the locked boundary
  are applied after the dispatch and receipt recording finish.
- Lease expiry can drop local lease usage to zero while durable remote uncertainty
  still blocks another reservation. A delayed accepted acknowledgement does not
  create completion observations or goal relief.
- A request queued before expiry may take effect after expiry. An authoritative
  release fence before arrival instead prevents that effect permanently.
- An older accepted acknowledgement cannot undo a newer release or erase the
  historical effect count. Repeated arrivals, receipts and retries do not add
  effects; an absent query does not prove release.

Two evaluator-only diagnostic mutations check sensitivity. These are additional
checks of existing dispatch invariants, not designated M09/M12 witnesses:

| Diagnostic | Original → reduced events | Predicate calls | Preserved first divergence |
| --- | ---: | ---: | --- |
| cached-send-gate | 9 → 8 | 34 | send after revocation: UNKNOWN → PASS |
| expire-uncertain | 8 → 7 | 30 | expired prepared intent: reconciliation_required → expired |

Both require passing unmodified controls, an exercised invocation canary, the
identical first-failure signature and a fresh final replay. All fifteen remaining
single-event deletions remove that exact failure. The initial state and schedule
are fixed; deleting a paired endpoint makes its survivor serial. These witnesses
are serial and do not establish schedule minimality. No global-minimum claim,
argument repair or timing-based schedule exploration is made.

Public initial inputs, evaluator commands/schedules and mutation decisions are
stored separately under `validation_lab/dispatch_race_cases`. Each run preserves
raw states and checkpoint logs before reference comparison. Its report records
the complete artifact inventory and source/corpus receipts.
`validation_lab.run_dispatch_races.verify_report(path)` checks those receipts,
all saved prefixes/effects, recovery counts, schedule observations and pinned
reduction decisions. Hashes are integrity receipts, not authenticated execution
certificates; rerunning the CLI performs fresh executions. Regenerate explicitly
with `uv run --no-project python -m validation_lab.generate_dispatch_race_cases --output artifacts/dispatch-race-generation-1`.

Native tests project actual admission, numerical, resource, intent and dispatch
records before and after recovery. A default test disables simulator submit,
query and release methods while reopening journals to check replay does no
executor I/O. All seven earlier corpus receipts were refreshed for the new runtime
adapter modules; their existing expectations and reductions are unchanged.

This profile shares `dispatch-race-parent-0` in the development split. It adds no
family-complete fixture, new designated mutant, authenticated external transport,
arbitrary concurrency exploration, fresh-process inbox recovery, evaluator
filesystem isolation or performance claim. The 64-fixture target, M09/M12 and the
remaining phase 4 coverage remain open.

## Separate-process public workers and dispatch checkpoints

Run `uv run --no-project python -m validation_lab.run_public_workers --output artifacts/public-worker-run-1`
with a new directory. Thirty-two cases replay pinned development commands: all
16 admission and eight deployment cases, plus eight dispatch cases. They compare
361 event prefixes (127 admission, 137 deployment and 97 dispatch). Every prefix
is followed by a worker kill, fresh process startup and exact completed-command
retry, for 393 worker starts overall.
Dispatch commands are serial here; the earlier thread-schedule profile remains
the evidence for concurrent lock behavior.

The evaluator copies only `reachability/*.py` into a receipted runtime bundle,
starts Python with `-I -B`, supplies a minimal environment, and gives each worker
an empty working directory. The worker receives its profile and store directory
as arguments, then public initial JSON and one current public event per response.
Future commands, evaluator labels, recovery scheduling, corpus paths and reference
state are retained by the parent. The actual child environment and import path
are tested against parent environment/PYTHONPATH contamination. This is process
separation and accidental-leakage prevention, **not OS filesystem/network or
hostile-code isolation**; the worker still has the account's capabilities.

`reachability.stream_worker` emits versioned `public-stream-worker/v1` ready and
event envelopes around the existing actual trace records. Inputs must be complete
UTF-8 JSON lines of at most 64 KiB. The parent bounds responses to 4 MiB and each
exchange to 15 seconds. Partial lines, duplicate fields, malformed JSON,
unsolicited bytes, size violations, deadlines and nonzero exits are evaluator or
protocol failures, never semantic UNKNOWN. JSON null is not EOF. Raw stdout bytes
are saved before parsing, and decoded envelopes are saved before oracle comparison.
Stderr, intended input bytes, process IDs, arguments, environment and termination
status are retained separately. Each event reply is correlated to its profile,
event digest, sequence/identity and projection digest.

All profiles now wrap their existing trace adapters with durable completed-command
checkpoints. Admission/deployment metadata is described below. Dispatch uses
`DurableDispatchSession`, whose checkpoint is separate from the authority and
executor journals. The `dispatch-worker-checkpoint/v1` file contains:

- Public initial configuration and the genesis, sequence and tail digest of both
  journals, binding the wrapper to the exact recovered stores.
- Observed request objects and immutable receipt objects, including older accepted
  receipts that must remain older after a newer release fence.
- Attempt/event aliases, certificates, completed command identities and exact
  historical replies. The 64-event limit persists across process restarts; exact
  retries do not consume another event or call the executor.
- An explicit pending command marker during execution.

The wrapper takes its own POSIX ownership lock, writes a temporary checkpoint,
fsyncs it, atomically replaces the checkpoint file, then fsyncs the directory.
The pending marker precedes command execution; the completed checkpoint precedes
stdout. Explicit `--resume` requires both existing journals, matching initial
configuration and matching journal tips. It never creates a missing journal or
silently accepts a changed one. Constructor recovery and exact reply retry are
also tested with simulator submit/query/release methods disabled. A retry returns
its stored historical reply, which is identified by `replayed: true`; it does not
assert that the historical projection is the current state.

The tested failure contract is deliberately precise:

| Failure boundary | Resume behavior |
| --- | --- |
| Completed checkpoint, then lost stdout | Recover inbox and exact reply; retry issues no send |
| Pending marker, before command execution | Refuse automatic resume |
| Remote effect, before completed checkpoint | Refuse automatic resume; actual executor effect remains durable |
| Command completed in memory, before checkpoint publication | Refuse automatic resume |
| Changed/missing journal, stale/corrupt checkpoint or changed initial state | Refuse automatic resume |

Actual child-process exits exercise the three pending-command boundaries and lost
stdout. Mid-command automatic reconciliation is not implemented: the stores must
be retained for explicit reconciliation rather than replaying a composite event
and guessing whether an external effect occurred. Storage errors also prevent
continued use of the live wrapper. Atomic publication of the wrapper checkpoint
does not make its writes and both journal transactions one distributed atomic
operation. The files remain trusted local storage; integrity hashes are not
cryptographic issuer authentication or protection against deliberate forgery.

The independent models remain in the evaluator and reconstruct each public prefix.
The dispatch model separately checks remote effects, locally observed receipt
ordering, uncertain occupancy, release fencing and transport buffers. The new
corpus pins existing case/public files and their manifests as ancestry, preserving
their development parent identities. Recovery scheduling never enters public
messages. Regenerate with
`uv run --no-project python -m validation_lab.generate_public_worker_cases`.

`validation_lab.run_public_workers.verify_report(path)` checks complete artifact
hashes, current source/corpus receipts, the exact runtime bundle, saved public
inputs and response order, every cold-model comparison, identical recovered
replies, process indices, raw pipe records, exit evidence and recovery counts.
The raw receipt records are evidence of a run, not authenticated execution
certificates. Rerun the CLI in a new directory for fresh execution. Native tests
compare actual admission, probability, resource, intent and dispatch projections
before and after a new worker resumes and returns a completed reply.

All eight prior corpus receipts were refreshed for the current runtime modules;
earlier expected outcomes and reduced witnesses remain unchanged. This increment
adds no family-complete fixture or designated mutant. Pending-command
reconciliation, evaluator OS isolation, M09/M12 and the 64-fixture target remain
open.

### Admission and deployment checkpoint recovery

`DurableAdmissionSession` and `DurableDeploymentSession` extend the same explicit
create/resume contract to `admission-event/v1` and `deployment-event/v1` streams.
`reachability.stream_worker --profile admission|deployment --resume` requires the
public initial message and a completed `trace-worker-checkpoint/v1` checkpoint.
Resume never creates a missing authority or executor journal. Earlier fresh-only
stream directories have no such checkpoint and are refused rather than silently
reconstructed from input events.

The checkpoint binds the profile, exact public initial state and admission
inference backend to the genesis, sequence and tail digest of every required
journal: authority only for admission, authority and executor for deployment.
It persists the 128-event budget, completed-event inventory, step number, command
prefix/counter, certificates and exact replies. Admission additionally persists
active contexts, current grounded rule revisions and **ordered** hard/numerical
alias pairs. Deployment persists its attempt aliases. Goal monitors, observations,
coverage, accounting, lifecycle state and executor effects are recovered from the
actual authority/executor journals, not independently recreated in wrapper data.

Alias order determines which public name represents a belief with multiple
aliases. A late alias that sorts before its original must not rename historical
beliefs after recovery. The ordered-pair codec and nonlexical hard/numerical alias
tests enforce this. Rules and contexts are checked against the recovered authority;
reply identities, digests and contiguous steps are validated, and the wrapper's
recovered projection must match its last completed projection. The four-context
and 128-event limits survive fresh processes. Rejected completed commands are
retriable historical replies, while malformed inputs and exceeded stream limits
are errors. Exact retries do not consume another event or generate new diagnostics.

Pending and completed publication use the existing fsynced temporary-file/atomic-
replace/directory-fsync mechanism and independent wrapper ownership lock. Internal
journal restart commands keep that lock. As with dispatch, a pending marker precedes
execution, and the completed checkpoint precedes stdout. An exact retry returns
the original saved row, including original elapsed-time and certificate diagnostics;
`replayed: true` identifies it as historical. A recovered worker does not re-execute
public events. Authority journal replay still performs its deterministic formula
and consistency checks, but invokes neither native inference I/O nor the executor.
These distinctions are directly tested with public execution, native formula I/O
and simulator submit/query/release disabled during recovery and exact retry.

The actual process crash tests cover pending-before-execution, completed in memory
before checkpoint publication, and lost stdout after completed publication for
both new profiles. A deployment crash after a remote effect leaves that effect
durable and local dispatch uncertainty intact. Pending commands refuse automatic
resume at all these pre-publication boundaries, even if a particular command
happened to write no journal entries. Storage failure also prevents further use
of the live wrapper. Profile/backend mismatch, missing or changed journals,
invalid reply inventories and corrupted metadata refuse recovery.

The expanded process corpus preserves the existing public commands and development
ancestry. All 361 completed prefixes are independently compared, recovered in new
processes and exactly retried. Reports retain raw stdin/stdout/stderr, launch/exit
records and actual recovered stores before comparison. Native tests compare
admission/probability/resource/lifecycle/goal/dispatch projections across worker
retries; a separate test continues actual native PLN revision after restoring its
backend binding and numerical aliases. The command-line worker uses the pinned
formula backend; native inference remains an explicitly selected API mode.

This extension adds 18 default tests and two optional native tests. It does not
provide pending-command reconciliation, automatic migration of old stream
metadata, a cross-store atomic transaction, hostile-storage authentication,
evaluator OS isolation, family-complete fixtures or additional designated mutants.


## Interrupted-worker inspection

`uv run --no-project python -m reachability.worker_inspection --profile deployment --database-dir /path/to/worker --output artifacts/inspection-1`
creates a new `worker-inspection/v1` evidence bundle. Admission and dispatch use
the same command with their profile names. The output must be outside the source
worker directory and must not already exist. Stop the worker and any direct
journal owners first. Busy ownership locks refuse capture; missing lock files are
never recreated. This is an explicit diagnostic action, not a worker resume path.

The inspector acquires the existing worker and journal locks through read-only
file descriptors. It captures checkpoint, database, WAL, SHM, rollback-journal,
lock and abandoned checkpoint-temporary files when present. Missing known files
are recorded explicitly. Capture is bounded to 64 files and 256 MiB; symbolic
links and nonregular evidence files are refused. Hashes and exact inventory are
compared before and after copying under the locks. Source databases are **never
opened through SQLite**: a normal recovery connection could create, checkpoint or
remove WAL/SHM files. Tests retain source bytes, filenames and modification times.
Access-time changes caused by reading files are outside this guarantee.

The captured `snapshot/` stays untouched. Analysis copies each required database,
its WAL and any rollback journal into a disposable directory, rebuilds SHM there,
checks SQLite structure, and invokes the existing checked journal recovery on that
private copy. Empty or malformed databases are reported as unavailable; they are
not accepted as new empty stores. Journal result replay still checks deterministic
formulas. No public stream event is replayed and no simulator submit/query/release or
native inference I/O is called. Ownership locks protect capture, not future use of
the source directory: the report describes the captured boundary, not live state
that may change after the locks are released.

`report.json` contains:

- The decoded-and-reencoded checkpoint, including its original completed replies,
  ordered aliases, observed requests/receipts and pending command, when schema,
  integrity, profile and public-wire checks succeed. Invalid checkpoint data is
  retained in the raw snapshot and reported as an error; a null pending value in
  that situation means unknown, not proof that no command was pending.
- Saved and current journal genesis/sequence/tail digests. `equal` means identical
  boundaries; `advanced` requires the saved boundary to be an actual prefix of
  the verified current chain, and includes the appended journal entries. A changed
  genesis, missing prefix, incorrect tail or backwards sequence is `diverged`.
  Missing/corrupt stores are `unavailable`; a readable journal with no valid
  checkpoint binding is `unbound`.
- Typed authority ledgers and current views, including hard/numerical beliefs,
  certificates, rule/policy history, operations, intents, resource uncertainty,
  lifecycle state, goals, samples, coverage and accounting. These do not depend on
  possibly stale wrapper aliases during an interrupted composite command.
- Actual simulator profile, request/receipt inventory and effect count, separately
  from the checkpoint's observed transport buffers. A historical accepted packet
  stays historical even when the current executor has a newer permanent fence.
  Newly recovered remote effects do not become locally observed acknowledgements.

The top-level diagnostic classifications and supported decisions are:

| Report status | Evidence | Current supported decision |
| --- | --- | --- |
| `no_pending_marker` | Valid checkpoint wire data, no pending marker, equal journal tips | Retain evidence; ordinary explicit resume still performs its own full wrapper validation |
| `pending_no_journal_change` | Pending marker, both required boundaries unchanged | Retain pending state; separately request bounded explicit cancellation if supported below |
| `pending_journal_progress` | Pending marker, at least one verified journal extension | Inspect partial effects; retain resource uncertainty and pending state |
| `checkpoint_journal_mismatch` | No pending marker but a journal extended beyond the checkpoint | Retain evidence; automatic resume remains refused |
| `unverified` | Corruption, missing stores, divergence, profile mismatch or unbound evidence | Preserve available bytes; do not infer a reconciliation outcome |
| `reconciliation_in_progress` | A captured reconciliation control marker exists | Retry its original decision; worker startup remains blocked |

Every report has `continuation_authorized: false`. No status is a repair permit.
In particular, unchanged journal tips do not establish that all wrapper-only work
or transport observations are reconstructible. The inspector does not perform the
full alias/completed-reply validation of the resume adapters. It never clears a
pending marker, adopts new replies, sends a request, advances a goal, or releases
resources. Partial numerical evidence, an unselected operation, an admitted but
unregistered monitor sample and an accepted remote effect are distinct states
requiring distinct future reconciliation rules.

`receipt.json` binds the report and captured file inventory. Call
`reachability.worker_inspection.verify_inspection(Path('artifacts/inspection-1'))`
to check bytes and reproduce the report on new private copies without accessing
the original worker. Added/missing/changed evidence and a rehashed report that
contradicts the captured state are rejected. These hashes establish reproducibility
and accidental-corruption detection, not hostile-storage authentication. Partial
output left by an interrupted inspector has no valid complete receipt and is not a
usable inspection bundle.

Run `uv run --no-project python -m validation_lab.run_worker_inspection --output artifacts/inspection-probes-1`
in a new directory for 16 actual child-process crash probes. The evaluator controls
fault injection and keeps original runtime hashes, exact injected-source receipts,
launch records, stdin/stdout/stderr, exit codes, worker stores and inspection bundles.
Independent primitive expectations check partial context/policy creation, numerical
report admission, operation selection, hard fact adoption and goal-sample
registration. All three profiles cover pending-before-execution, after-composite
execution and completed-checkpoint/lost-stdout boundaries. Deployment and dispatch
also crash after a committed remote effect, retaining the executor WAL and local
uncertainty. Completed stdout-loss replies and earlier prefixes are compared with
the independent public models. `validation_lab.run_worker_inspection.verify_report`
checks the source bindings, injection bytes, raw exchanges, expectations, bundles
and unchanged captured source evidence.

Sixteen new default tests exercise the inspection and evidence contracts. One new
native test compares the captured typed authority records with the original native
projection. The existing nine corpus receipts are refreshed without changing their
cases, outcomes, schedules or mutation reductions. No authority/executor/checkpoint
schema changes, additional family-complete fixtures, designated mutants or OS
sandbox guarantees are introduced. Broader pending-command reconciliation,
M09/M12, the 64-fixture target and broader phases remain open. The bounded explicit
cancellation transition below is now available separately from inspection.


## Bounded explicit worker reconciliation

The `cancel_unstarted_local` action is the first supported reconciliation
transition. It cancels one interrupted admission or local deployment event when
all inspected journal boundaries and captured source bytes are unchanged. It
never replays that event. A cancelled event consumes one stream step and its
original ID; exact event retries return its saved `UNKNOWN` reply with
`diagnostics.reconciliation` identifying the decision and request digest. This
status describes an explicitly cancelled, unevaluated command, not a successful
execution or a proven domain failure. Retrying its intended operation requires a
new event ID after reconciliation completes.

Create a request without changing the worker:

```sh
uv run --no-project python -m reachability.worker_reconciliation request \
  --inspection artifacts/inspection-1 --decision-id cancel-1 > artifacts/cancel-1.json
```

Apply that explicit request, or retry the same request after interruption:

```sh
uv run --no-project python -m reachability.worker_reconciliation apply \
  --request artifacts/cancel-1.json --inspection artifacts/inspection-1 \
  --database-dir /path/to/worker
```

`worker-reconciliation-request/v1` binds the decision ID, action, profile, entire
inspection report digest, exact original checkpoint bytes, pending-command digest
and every inspected journal genesis/sequence/tail. Reconciliation requires the
existing worker and journal ownership locks. Before preparing a new decision it
verifies the original inspection and compares the complete captured source file
inventory. Even a physical database/WAL layout change with identical logical tips
requires a fresh inspection. The original inspection bundle is retained unchanged.

| Pending state | Supported action |
| --- | --- |
| Admission event; no journal progress; complete saved wrapper validates | Explicit cancellation |
| Local deployment event; no journal progress; complete saved wrapper validates | Explicit cancellation |
| New admission context; exactly its matching `open_context` entry persisted | Explicit `complete_partial_context` |
| Deployment `dispatch`, `reconcile` or `release` event | Refuse, including unchanged journal tips |
| Any dispatch-profile event | Refuse in this increment |
| Other partial admission, numerical, lifecycle, goal or executor progress | Refuse and preserve evidence |
| Stale/unverified evidence, changed command, invalid wrapper metadata or exhausted event budget | Refuse before publishing a decision |

Local deployment events are `fact`, `forecast`, `revoke`, `tick`, `attempt`,
`reserve`, `cover`, `prepare`, `observation`, `sample`, `censor`, `resume`, `account`,
`complete` and `restart`. Admission includes its existing bounded event kinds.
The whitelist excludes operations that might have performed executor I/O or lost
transport-only observations without a new journal entry. Unchanged tips alone
remain insufficient outside this explicitly supported set.

For cancellation, the original wrapper is fully validated on private copies with the pending field
removed there only. Its inventory, aliases, current rules, counters, historical
replies and last projection must satisfy ordinary resume validation. The candidate
checkpoint adds a cancellation reply, updates the event inventory/step/prefix,
and preserves journal tips, aliases and counters. It is reopened on another
private session and its exact cancellation reply checked before publication.
Neither original SQLite database is opened through SQLite. No authority append,
public event execution, native inference I/O or simulator submit/query/release is
issued. Existing uncertain remote occupancy and actual effects remain unchanged,
including after lease expiry. Native numerical inference can continue later in a
normally resumed worker with its original backend and aliases.

Cancellation publication uses fsynced files, atomic replacement and directory fsync:

1. Retain an immutable prepared record and exact before/after checkpoint files in
   `worker-reconciliations/<hash-of-decision-id>/`. Public IDs are hashed before
   being used as path components. Partial preparation can be retried under the
   same original evidence; incompatible contents never get overwritten.
2. Publish `reconciliation-pending.json` before replacing the worker checkpoint.
   All three current durable worker profiles refuse startup while this marker
   exists, including when the candidate checkpoint has already been published.
3. Atomically publish the checked cancellation checkpoint. On decision retry,
   the checkpoint must match either its exact before bytes or its exact after
   bytes, and all original database/sidecar bytes must still match the preparation.
4. Durably publish `worker-reconciliation-result/v1` before removing the marker.
   Marker removal is followed by directory fsync. Only then can ordinary worker
   resume accept new events.

| Interrupted reconciliation boundary | Exact decision retry |
| --- | --- |
| During checkpoint-archive staging or before marker publication | Revalidate original inspection and finish preparation; original pending event still blocks workers |
| Marker published, checkpoint still original | Validate preparation and unchanged journals, then publish the cancellation |
| Candidate checkpoint published, result not durable | Workers remain blocked; record the result before clearing the marker |
| Result durable, marker still present | Verify the same result and boundary before clearing the marker |
| Marker cleared, stdout lost or later worker events completed | Return the archived historical result without changing current state |

After marker publication, the complete prepared archive suffices to finish the
exact request even if the external inspection path is temporarily unavailable.
The original inspection is still required for independent offline audit through
`reachability.worker_reconciliation.verify_reconciliation(archive, inspection)`.
That function recomputes the candidate and checks the retained before/after files,
request, journal bindings, reply digest and any completed result. An `APPLIED`
result is historical; `replayed: true` never asserts the worker is still at that
checkpoint. These remain trusted local records, not authenticated execution
attestations. Corruption, direct external journal changes or conflicting decision
identities refuse completion and preserve the gate for explicit investigation.

Inspection remains read-only. It now captures an existing reconciliation marker
and reports `reconciliation_in_progress`; it neither completes that decision nor
clears it. A malformed marker blocks workers, while the separate reconciliation
path checks its integrity and exact prepared-record binding.

Run `uv run --no-project python -m validation_lab.run_worker_reconciliation --output artifacts/reconciliation-probes-1`
in a new directory. Twenty actual process probes include twelve cancellation
probes spanning six crash boundaries for both supported profiles, and eight
partial-context completion probes described below. Raw
launch arguments/environment, stdout/stderr, exit codes, source/fault receipts,
original inspections, decision archives and continued worker exchanges are
retained. Independent public models check unchanged state for the cancellation
and the next real event, while explicit reconciliation expectations check UNKNOWN,
step consumption, exact replies and the worker gate. The verifier reproduces each
decision and validates captured process evidence and journal preservation.

Eighteen new default tests and one new native test cover the supported transition,
refusals, archive integrity, budgets, native continuation and crash publication.
Existing worker/checkpoint, authority and executor schemas are unchanged. All nine
existing corpus receipts are refreshed without changing cases, expected outcomes,
schedules or reduced witnesses. No automatic interrupted-event replay, remote
release, general partial-command repair, new designated mutant, family-complete fixture
or evaluator OS sandbox is introduced. Broader reconciliation remains open.

### Completing a partially persisted context

`complete_partial_context` supports a new admission context whose journal contains
exactly the `open_context` entry after the saved wrapper boundary. Generate its
bound request using:

```sh
uv run --no-project python -m reachability.worker_reconciliation request \
  --inspection artifacts/inspection-1 --decision-id finish-context-1 \
  --action complete_partial_context > artifacts/finish-context-1.json
```

Apply or retry it with the same `apply` command above and the new request path.
Cancellation remains the default action and still refuses every partial command.

Preparation rewinds only a disposable copy of the captured journal to the saved
checkpoint boundary. Ordinary worker restoration validates all prior wrapper
metadata, aliases, rules, replies and projection. The pending command must name a
new context, fit the context and event bounds, and use a fresh event ID. The
reconciler constructs the two known primitive commands on that private copy.
Its first journal entry must exactly equal the captured `open_context`, including
key, payload, result digest, sequence and hash chain. The key uses the saved global
counter; the policy command uses the next value. No public composite event runs.

The candidate adds the context alias, consumes one stream event, advances the
counter by two, and stores a `PASS` reply with reconciliation diagnostics. Ordinary
private restoration checks that checkpoint and its exact reply. A prepared v2
record retains the single proposed policy entry in addition to the original and
candidate checkpoints. Request/result schemas and existing worker/journal schemas
are unchanged; cancellation continues using prepared v1 records.

After the durable marker gates worker startup, the reconciler retains the same
worker and journal locks and opens the existing authority SQLite database. A FULL
synchronous transaction verifies the genesis and entire journal chain. It accepts
only the inspected boundary or that boundary plus the exact prepared policy row.
At the inspected boundary it inserts that one validated row. At the completed
boundary it recognizes the earlier commit without inserting again. It never
replaces a source database with its private candidate. Unrelated executor and
ownership files must remain unchanged. SQLite may legitimately change authority
database/WAL/SHM layout after preparation; logical journal boundaries govern these
retries. Before preparation, the full captured byte inventory must still match.

The completed checkpoint is published only after the policy commit. A published
checkpoint with a missing policy entry is refused, as are extra or divergent
journal entries. The durable result records the resulting journal tip and precedes
marker removal. Exact retries can finish without the external inspection after
preparation, and remain historical after later worker events. Offline verification
reconstructs both the checkpoint and exact policy suffix from the original bundle.

Eight process probes cover the six archive/checkpoint/result boundaries plus
interruption inside the SQLite transaction and immediately after COMMIT. Each
requires a gated worker until completion, exactly one appended command, an exact
historical PASS reply and successful subsequent numerical admission checked by
the independent public model. The v2 probe receipt retains original and completed
inspections, process exchanges, fault/source hashes and decision archives.
Thirteen additional unit tests cover mismatched arguments/counters/identity,
budgets, existing contexts, wrong or extra progress, storage failure, retained
ownership, historical retries and absent public/native/executor replay. One added
native test continues through real PLN revision after completing the context.

This action refuses unchanged journals, a fully persisted two-command context
without a completed wrapper reply, existing-context events and all other partial
admission/numerical/lifecycle/goal/dispatch commands. Those outcomes require
separate transitions; none is inferred from this policy-suffix repair.
