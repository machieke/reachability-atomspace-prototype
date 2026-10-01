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
| M11 censored outcome labeled failure | d07, prefix 3, event e002 | CENSORED → OBSERVED_FAILURE |

The witnesses are first divergent prefixes, not generally minimized event sets.
M05 replaces shared measurement roots with separate report IDs during numerical
revision; its canary confirms this defect ran. It is an evaluator-only patch and
is removed before subsequent controls. M01–M04 retain their unit witnesses.
M07 changes only the product-name matching branch while leaving the remaining
observation checks enabled. Its two-event witness creates an attempt and presents
a wrong-product report. The unmodified control fails registration; the mutant
registers the wrong product. Tests delete each event in turn and confirm that
neither shortened stream detects the mutant. This is deletion minimal in the
declared profile, not a general-purpose shrinking algorithm.
M08–M10 and M12 remain open.

Next generalize trace shrinking while preserving independent failure signatures
and passing controls before comparative claims. Complete family coverage,
general event shrinking, deterministic concurrent interleavings, hidden-world models,
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
