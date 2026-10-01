# Reachability AtomSpace implementation plan

This plan turns the two architecture proposals and the validation design into a
tested implementation. Admission and provenance come first; numerical fields
remain advisory throughout. Completion of a phase requires its exit checks, not
just the presence of the listed modules.

The starting repository contains specifications, illustrative benchmark JSON, and
a standalone numerical reference script. It has no installed AtomSpace or PLN
adapter, executable benchmark, or measured performance results.

## Engineering decisions

- Use Python 3.11 or later for the initial reference service and harness. Use the
  standard library initially so that the semantic tests need no external service.
  Pin the development interpreter and record specification hashes.
- Keep application records independent of backend handles. Use immutable typed
  records for statements, evidence, revisions, rules, transitions and certificates.
  Introduce AtomSpace through a tested storage adapter, not a simulated claim of
  compatibility.
- Start with grounded finite propositional logic and a bounded complete checker.
  Unsupported scope returns UNKNOWN. An explicit hard assertion is a contract
  interpretation; it is not a probabilistic PLN estimate.
- Use one commit authority, coarse context revisions and atomic publication.
  In-process locking is sufficient for the first volatile prototype; durable
  transactions and restart recovery are a separate required deliverable.
- The reference oracle uses a separate algorithm and lives in the test/evaluator
  tree. Runtime code cannot import evaluator labels or future event scripts.
- Preserve the supplied design pack unchanged. Executable fixtures and actual
  results live separately, with their own schema and manifest.
- Scope the first increment to an executable admission foundation. Do not label
  it a full cognitive cycle, PLN integration, or performance benchmark.

## Phase overview

### Immediate priority: executable B0-versus-B3 comparison

This milestone supersedes the recovery expansion listed at the end of the
historical increments below. Existing safety, admission, execution and recovery
contracts remain mandatory. Unsupported interrupted operations stay blocked;
additional recovery automation is backlog work unless a concrete defect prevents
this comparison from running.

1. Implement a deterministic, revision-bound, read-only pressure projection over
   authoritative goal slices, support dependencies, lifecycle state and live
   commitments. Preserve canonical source identities, AND/OR structure,
   outstanding/open/covered loss, observed relief and monitoring. Use a bounded
   fixed contraction operator with residuals, convergence and exhaustion reports.
2. Expose one public reasoning candidate frontier to both controllers. Preserve
   the deployment B0 and its regressions. Compare a competent dependency-aware
   B0 ranking with B3 typed pressure and a direct priority queue. Charge shared
   discovery to both; measure ranking and pressure overhead separately. No
   adaptive activation transport, hidden world access or weakened authority.
3. Add independent numerical checks, revision and authority tests, and the M09
   repeated-source-injection witness. Keep M12 with deferred transport. Exercise
   real certified inference in a bounded closed-loop episode with competing
   routes, missing evidence, a shared prerequisite and changing support. Include
   a simple control and verify that the controller switch changes ranking.
4. Run a reproducible paired comparison under declared work and time limits;
   retain machine-readable traces and a readable report with source/configuration
   bindings, outcomes, failures and measured/unmeasured costs. Run applicable
   regressions, refresh receipts and record the result without requiring a B3 win.

Stop when this bounded milestone is tested and reproducible. It does not complete
the full pressure, attention, transport or benchmark design. Learned conductance,
adaptive transport, generalized recovery and large-scale claims remain deferred.

| Phase | Deliverable | Depends on | Exit evidence |
| --- | --- | --- | --- |
| 0 | Repository contracts and reproducible test entry points | Design inputs | Input hashes, clean test command, explicit supported fragment |
| 1 | Scoped provenance and admission service | 0 | Joint checks, stale/forged permit rejection, serialized commits |
| 2 | Durable lifecycle and operation ledgers | 1 | Event-prefix agreement, restart reconciliation, exact relief |
| 3 | Actual storage and PLN adapters | 1, durable interfaces from 2 | Pinned builds and cross-adapter contract tests |
| 4 | Independent validation lab and strong baseline | 1–3 | 64 fixtures, designated mutants detected, deployment integration |
| 5 | Typed pressure and commitment accounting | 2, 4 | Independent numerical solution and unchanged authority |
| 6 | Bounded attention and adaptive transport | 3–5 | Complete allocation ledger and gate-first arithmetic tests |
| 7 | Controlled mechanism experiments | 4–6 | Equal-budget baselines, canaries, uncertainty and cost reports |
| 8 | Learning, scale and grounded transfer | 7 | Held-out results and prospective Freeciv coordination trials |

The test harness grows with phases 1–3; phase 4 completes its coverage and wires
the real components together. It is not a reason to defer semantic testing.

Current checkpoint (1 October 2026, thirty-second increment): the
bounded B0/B3 milestone above is complete. The authorized follow-up strengthens
saved comparison auditing and reproducibility within that same subset; its full
32-run bundle audit passes. Two fresh matrices now pass all sixteen work-limited
repeatability comparisons across 64 distinct authorities within this same subset.
The prior correction enforces the pressure routing bound on exact stored
binary64 shares and rejects normalization underflow. Its corrected 64-run
experiment passes. The shared candidate generator now orders support lifetimes
exactly, including absence of scheduled expiry. Public operation costs now require
exact integer work units consistent with budgets and saved-run audits; the fresh
64-run repeatability check passes. Typed read-only pressure feeds a real direct
priority queue over the same public inference/observation frontier as
conditional-planning B0. The development matrix runs 16 controller pairs; M09 is
detected and validation is complete. Existing recovery
actions, gates and blocked unsupported cases are preserved. Transport/M12,
learned conductance, family-complete validation, evaluator OS isolation and the
broader phases remain deferred; this subset does not complete phases 5–8.

## Phase 0 Repository contracts

1. Add package metadata, interpreter selection, ignore rules, a root README and
   a standard-library test command.
2. Record source-document hashes separately from the supplied manifest; record
   dependency status honestly, including adapters not yet selected.
3. Define stable structural identities, scope identifiers, four gate statuses,
   immutable check results and operation-bound certificate records.
4. Specify the initial supported logic, resource limits, error behavior and
   in-process trust boundary.
5. Establish an evaluator-only location and a separate finite enumeration oracle.

Exit: a fresh checkout can run the starter suite; changing a design input is
detectable; the runtime does not import the evaluator.

## Phase 1 Provenance and admission

1. Intern grounded typed statements independently of goal, attention or belief
   values. Preserve predicate, argument identity and argument order.
2. Store immutable context-scoped evidence with source lineage. Evidence replay
   is idempotent; an existing ID with different content is an error. Recording a
   report does not accept its content.
3. Add context assumptions, CNF constraints and a complete bounded propositional
   satisfiability checker. Check the whole relevant state, not pairwise edges.
4. Add exact instantiated transitions for direct evidence admission and a small
   registered grounded rule fragment. All premises must be current and in scope.
5. Implement precertification, pure proposal creation, result certification and
   revision-checked commit. Certificate records bind operation, result, context,
   rule, policy, evidence and premise revisions. Service-issued records alone
   authorize writes.
6. Preserve immutable historical beliefs and derivations. Revoke support before
   publishing a current view; keep alternative supported derivations usable.
7. Exercise two concurrent candidates checked at the same revision. At most one
   commits; the other returns STALE and needs re-evaluation.

Exit: executable positive controls and F01/F02/F04/F05/F08/F09/F16 slices;
independent finite truth-table checks; explicit UNKNOWN at checker capacity;
forged, mismatched, failed and stale certificates cannot authorize commits.

Deferred within this phase until the starter works: context inheritance and
translation, variable binding, dynamic rule/policy replacement, time-dependent
supports, full AtomSpace object schemas and numeric truth-value ownership.
Their absence must remain visible in the capability manifest.

## Phase 2 Durable lifecycle and operation ledgers

1. Add a transactional event store with append-once IDs and atomic revision
   publication. Start with SQLite behind an interface; store immutable records
   and rebuild materialized views from the event log.
2. Implement pinned lifecycle schemas, episodes, requirements and witnesses.
   Support AND/OR first, with explicit UNKNOWN for unimplemented temporal forms.
3. Track entity stage, continuing validity, operation milestones and persistent
   goal obligations independently. Historical completion survives later expiry.
4. Add exact resource claims, interval reservations, leases and one resource
   authority. Atomically record intent and ownership before dispatch.
5. Add goal slices and separate outstanding loss, predicted coverage, open loss
   and observed relief. Handle overlap conservatively and reopen expired work.
6. Build an idempotent simulated executor plus a non-idempotent executor class
   that exposes uncertain outcomes. Recover by reconciling the same attempt.
7. Implement exact-product observations, delayed/censored outcomes and declared
   durability windows. ACK and timer expiry cannot discharge goals.
8. Test every crash boundary and each event prefix against a cold independent
   projection, including late callbacks and newly inserted blockers.

Exit: the deployment conformance episode blocks revoked credentials, preserves
test evidence, avoids duplicate effects, rejects wrong products and discharges
the goal only after the three required consecutive healthy observations.

## Phase 3 Storage and PLN integration

1. Inspect the actual target repositories and select compatible exact revisions.
   Record compiler/runtime, AtomSpace, attention, PLN, rule-formula and schema
   revisions. Reproducibly build a small storage smoke test before integration.
2. Map structural records to AtomSpace structures and numerical state to named
   Value schemas. Keep service ownership of protected anchors and indexes.
3. Implement the pure PLN adapter: preconditions, apply, revise and explain.
   Preserve strength/confidence interpretation, formula IDs and common origins.
4. Reject failed probability domains and library fallback values as authority.
   Test exact numerical boundaries with rational evaluator fixtures.
5. Make repeated or cyclic derivations support-idempotent; do not assume distinct
   evidence IDs imply statistical independence.
6. Run the same semantic contract suite through the finite implementation and
   actual adapter. Add the custom FDAS adapter only after its concrete interface
   and revision have been inspected.

Exit: real storage and pure inference participate in certified commits and the
deployment slice; no compatibility claim rests solely on serialized JSON.

## Phase 4 Validation lab and competent baseline

1. Implement versioned public cases, isolated evaluator cases and semantic traces.
   Keep hidden worlds, future events, expected results and reference plans out of
   runtime inputs. Hash generator, oracle, fixtures and split ancestry.
2. Deliver four controls for each F01–F16 family: valid, blocked, delayed/boundary,
   and context/revision change. Track coverage explicitly; do not relabel 64
   variations on one gate as 64 family-complete fixtures.
3. Add deterministic interleaving control, stateful event generation, shrinking
   and metamorphic transformations. Preserve independent alternate proofs.
4. Implement isolated M01–M12 mutants and require a reproducible witness for each.
   Surviving mutants remain reported gaps.
5. Implement B0 dependency-aware best-first/beam scheduling with exact checking,
   an operation ledger and full recomputation. Add B3 when typed pressure exists.
6. Support conformance, forced replay and closed-loop execution as distinct modes.
   Charge candidate discovery, checks, persistence and all field work.

Exit: all 64 fixtures run; designated mutants are detected; feasible positive
controls make progress; deployment uses the actual integrated components.

## Phase 5 Pressure and coverage

1. Derive persistent sources from versioned goal loss, bounded urgency and explicit
   commitment factors. Goal weight changes must leave beliefs unchanged.
2. Materialize bounded typed dependency graphs with AND/OR groups and the infer,
   observe, act, expand and retain channels. Preserve stranded source demand.
3. Implement a frozen-epoch column-substochastic operator and iterative solver.
   Report residual, error bound, iteration cost and incomplete convergence.
4. Compare against an independent rational/direct solver on small cases. Check
   cycles, duplicate paths, zero support and attenuation near one.
5. Add coherent plan packets and commitment-aware ranking. Reserve only ready
   next steps and preserve monitoring allocation for covered work.
6. Convert operational pressure into one bounded task potential; avoid multiplying
   the same goal importance again through STI and the final plan value.

Exit: fields cannot mint source loss, evidence or execution authority; independent
numerical checks pass; complementary prerequisite plans remain discoverable.

## Phase 6 Attention and transport

1. Add session reservoirs, scoped STI and a fair exploration/monitoring budget.
2. Implement permitted routing arcs and lazy rate evaluation: a closed route must
   skip numeric payload evaluation entirely.
3. Add compact kernels, permitted-path neighborhoods, self-support, bounded
   bandwidth adaptation and explicitly labeled neighborhood approximations.
4. Publish conservative transport updates under consistent epochs. Include seed,
   cooling, removal and spending transfers in the complete allocation ledger.
5. Add protected retention and bounded rewards based on attributable outcomes.
   No attention operation can write belief strength or confidence.

Exit: nonnegative finite state, conserved allocation, zero closed-route flux,
correct cancellation after relevant revisions, and tested dependency pinning.

## Phase 7 Mechanism experiments

1. Add B1/B2/B3/B4 and safe replacement variants. Prove each switch changes its
   intended code path with invocation and cost canaries.
2. Run scalar/typed pressure × coverage-blind/aware ranking × queue/transport.
   Keep gates, reservations, operation history and idempotency fixed in all cells.
3. Separate fixed-candidate ranking from discovery experiments. Report frozen
   replacements and equally retuned alternatives under equal tuning budgets.
4. Run bandwidth × density and conductance × attribution studies separately.
5. Predeclare primary comparisons, loss endpoint, practical gain threshold,
   noninferiority margin and multiplicity treatment before confirmation.
6. Report paired cluster-aware intervals, per-family results, total wall time,
   declared work, memory, failures and performance/cost curves.

Exit: a mechanism is promoted only after a confirmed benefit over a competent
alternative. Null and negative results can justify keeping the simpler version.

## Phase 8 Learning and transfer

1. Separate retrieval-cost learning from action-outcome learning. Preserve causal
   attribution, censored labels and exact eligibility sets.
2. Run known-model, frozen-learned and explicitly sequential online regimes.
   Split by parent instance, including renamed and counterfactual relatives.
3. Test structural, compositional, dynamics and lifecycle-schema shifts. Scale
   total storage independently from active frontier, proof depth and route length.
4. Inspect and pin the Freeciv implementation, saves, assets, rules and opponents.
   Keep local execution heuristics unchanged. Start with legal-interface shadow
   checks, then prospective paired coordination episodes.

Exit: claims remain bounded to measured regimes and supported contracts. Shadow
predictions alone cannot establish gameplay or causal benefit.

## Execution record

### First increment on 1 October 2026

Phase 0's repository foundation is implemented: package metadata, pinned Python
3.11.14, a root README, immutable records, a capability/input manifest and test
entry points. The original design files remain unchanged and their hashes match.

Phase 1 is **in progress**. The finite admission slice implements scoped evidence,
source lineage, grounded rule transitions, full CNF consistency checks, pre/post
certificates, pure proposals, idempotent commands, revision-checked commits and
support revocation with retained alternative proofs. The store is volatile.

Verification for this increment:

- `uv run --no-project python -m unittest discover -s tests -v`: 39 tests passed,
  including comparison against an independent oracle on 400 generated formulas.
- The suite detects isolated mutants M01–M04 using small explicit witnesses.
  M05–M12 remain pending, as recorded in the capability manifest.
- `uv run --no-project python -m reachability.demo`: produces UNKNOWN for a missing
  premise, PASS for complete inference, FAIL for contradiction and STALE after
  evidence revocation, with historical conclusions retained.
- `uv run --no-project python pressure_field_lifecycle_reference_checks.py`:
  all 15 supplied numerical/accounting checks passed unchanged.
- `uv sync --python 3.11.14`: the editable package built and installed successfully;
  `uv.lock` records the project with no third-party runtime dependencies.

This is initial coverage of the missing-premise, joint-consistency, context,
lineage, revocation, concurrent-commit and certificate-integrity contracts. It is
not completion of all cases in their associated F01–F16 families.

### Second increment on 1 October 2026

Implemented dynamic rule and policy replacement, immutable revision identities,
dependency invalidation, explicit context clocks and exclusive evidence expiry.
Changed rules invalidate descendants while independent proofs survive. Policy
changes recheck current claims. Joint conflicts that cannot be resolved without
choosing a world conservatively retire the remaining active set for explicit
re-admission. Relaxing a policy never resurrects stale claims automatically.

Started phase 2 with an optional SQLite command journal. It uses atomic append,
persisted idempotency, a single-authority POSIX lock and checked replay of the full
history. Recovery re-executes admission and compares result digests; saved PASS
records are not trusted independently. Typed JSON has an explicit record allowlist.
Durable mutations roll back their working state on failure and publish only after
commit. An ambiguous storage failure requires reopening and key reconciliation.

Verification for this increment:

- 93 tests pass, including the same 26 admission contracts against both memory and
  durable storage, and recovery after each durable contract.
- Rule replacement, newly inserted blockers, policy relaxation, future evidence,
  expiry boundaries and alternate supports have executable checks.
- Tests terminate real subprocesses immediately before and after journal commit.
  Recovery shows only the durable side of each boundary.
- Other tests inject SQL failures, lost commit responses, corrupted records,
  missing middle events and a saved acceptance produced by a broken checker.
- The recovery demo preserves accepted readiness through restart, then makes it
  stale at credential expiry while retaining the artifact's valid test evidence.
- All 15 supplied numerical/accounting checks still pass unchanged. The durable
  checks ran on Python 3.11.14 with SQLite 3.50.4.

This completes the scheduled rule/policy/expiry increment and the first durable
storage work item. It does not complete phase 2: lifecycle schemas, operation
episodes, resources, goal coverage, external dispatch and durability observations
remain next. Replay uses the same admission engine, supplemented by the independent
Boolean oracle and hand-specified event-prefix expectations; a full independent
lifecycle reference model is still pending. Full-history replay and rollback copies
are correctness-first reference choices, with costs to measure before optimization.

### Third increment on 1 October 2026

Implemented grounded, immutable lifecycle schemas and episode pinning; pure
AND/OR requirement evaluation with exact witnesses; separately certified lifecycle
transitions; and a durable passive operation ledger. Source requirements, observed
outcomes and target validity have separate checks. Stage history survives loss of
current support. Explicit regression/recovery edges can leave an invalid state
only under their own checked requirements and observed outcomes.

Operations have persistent operation and attempt identity, selection time and
independent observations. The ledger rejects wrong products, wrong attempts,
unapproved source IDs, stale supports and synthetic executor observations produced
by inference. ACK is not completion; completion is not an exact-product observation.
Late outcomes remain recordable after cancellation. Selection grants no external
execution authority, and this increment does not infer goal relief or causal credit.

All new mutations share the existing service lock, idempotency and SQLite replay
boundary. Lifecycle changes advance a separate context-scoped lifecycle revision
without modifying belief revisions. New schema versions do not invalidate episodes
pinned to an older schema. Existing admission record layouts remain unchanged.

Verification for this increment:

- 169 tests pass. The lifecycle and operation contract suites run in both memory
  and durable modes; durable cases compare reconstructed projections after replay.
- A separate three-valued requirement oracle checks 240 generated expression/world
  combinations, alongside the existing 400 independent Boolean formula checks.
- New fault tests cover lifecycle commit crashes, failed appends and lost callback
  commit responses. Repeated callbacks and replayed commands do not duplicate history.
- A stored seven-command journal produced by commit `3e2516e` recovers correctly,
  and accepts the new lifecycle commands without changing earlier results.
- The lifecycle demo retains BUILT after credential revocation, then reports STALE
  validity after product support is revoked while preserving the transition.

This completes the scheduled grounded schemas, AND/OR witnesses and passive operation
episode increment. It does not complete phase 2. Contracts that distinguish
submission-time prerequisites from completion-time requirements still need the
intent coordinator and temporal semantics; this fragment checks a transition at
one current snapshot. General schema migration and entity-variable binding remain
unsupported rather than inferred from these grounded tests.

Next implement transactional resource claims, reservations and durable operation
intents; then simulated executor dispatch/reconciliation, goal slices, overlapping
coverage and observation-defined durability. Context inheritance, variable binding
and schema breadth remain explicit phase 1 backlog items. Phases 2–8 have not passed
their exit criteria.

### Fourth increment on 1 October 2026

Implemented exact integer renewable resource definitions, complete interval capacity
checks, pinned execution contracts, execution certificates, atomic reservations and
local operation intents. Resource identities are shared across belief contexts under
one authority. Execution contracts declare all required quantities and units; claims
are generated from that contract rather than supplied by the reservation caller.
Selection, current lifecycle prerequisites, additional action requirements, owner,
schema binding, joint capacity and fresh revisions must all pass.

Every lease and its intent commit in one journal transaction. A failed allocation
leaves no partial ownership. Concurrent workers checked against the same last unit
produce one successful reservation and one stale certificate. Repeated keys and
attempts cannot create duplicate claims. Restart reconstructs the same intent and
reservation identities before accepting further work.

Leases use a single explicit resource clock. The context evidence clock must match
it for action readiness, preventing an older credential snapshot from authorizing
work at a later resource tick. Expiry and owner cancellation release undispatched
local claims while preserving history. Any recorded executor observation makes
remote occupancy unresolved and blocks affected resources, even after lease expiry,
cancellation or evidence revocation. This conservative state cannot yet be cleared:
the next increment must add an authoritative release/reconciliation contract.

Verification for this increment:

- 231 tests pass, including the same 24 coordinator contracts in volatile and
  durable modes, with cold reconstruction of resource and intent projections.
- An independent discrete-time oracle checks 500 generated capacity portfolios
  against the interval sweep. A three-way contention witness passes every pairwise
  check but fails the required complete-portfolio check.
- Atomicity tests cover failed multi-resource appends, lost commit responses,
  failed cancellation and the shared observation/resource-invalidation transaction.
- Real subprocesses terminate immediately before and after the reservation/intent
  journal commit; recovery sees either no claims or both claims and their intent.
- The resource demo recovers the same intent, rejects a competing stale certificate,
  blocks readiness after credential revocation and releases only the local lease
  at its exact expiry boundary. It records no executor milestone or goal relief.
- All 15 supplied numerical/accounting checks remain unchanged and pass.

This completes the scoped local resource/intent increment within phase 2. No
external dispatcher exists yet, and an intent's `execution_authorized` stays false.
There is no future-step booking, lease renewal, dynamic capacity revision, consumable
inventory or remote release authority. These are explicit limits, not implied by
the renewable-capacity checker. The existing lifecycle transition evaluator still
uses one current snapshot; submission/completion temporal contracts remain pending.

Next implement the simulated executor and dispatch boundary: durably mark submission
before I/O; recheck current gates; protect capacity during uncertain outcomes;
reconcile the original attempt with both idempotent and non-idempotent executors;
and accept remote release only under its explicit evidence contract. Then add goal
slices, conservative overlapping coverage and observation-defined durability.
Phase 2 and the later phases have not passed their exit criteria.

### Fifth increment on 1 October 2026

Implemented a durable submission boundary and an independent local executor
simulator. Dispatch policies pin the execution contract, executor identity, durable
executor instance and explicit idempotency/query/release capabilities. The service
records a submission marker with its current witnesses before I/O, then rechecks
the submission gates while holding the same service lock through the synchronous
simulator call. The request retains the exact intent, product and reservation
identities. Command replay never submits or releases an executor request.

The marker protects capacity even if the local lease later expires. Lost replies
leave an uncertain attempt that is reconciled under its original identity. An
idempotent executor can receive the same request again only while current gates
pass. A non-idempotent executor is never automatically retried after the marker
exists; even an authoritative absence does not rule out a delayed earlier request.
The non-idempotent simulator exposes both duplicate effects and unsupported queries
so these assumptions are executable, rather than hidden behind one ideal adapter.

Added authoritative release with a permanent executor tombstone. Releasing an
unseen request prevents its delayed arrival from recreating occupancy. Resource
capacity becomes available only after the local authority durably records that
exact request's release receipt. Release does not erase historical effects or
manufacture completion, product evidence, a lifecycle transition or goal relief.
It is an explicit cleanup capability usable by the recorded owner after action
credentials expire. Passive external observations without a bound dispatch request
remain unresolved; the simulator cannot retroactively take ownership of them.

Verification for this increment:

- 271 tests pass, including 23 dispatcher contracts, six independent-executor
  contracts, ten dispatch recovery/compatibility tests and the dispatch demo.
- Twelve real subprocess crash scenarios cover both sides of the local submission
  marker, executor effect, local receipt, executor release and local release receipt,
  including non-idempotent execution before and after its effect commit.
- Fault injection covers lost remote replies, failed local writes, ambiguous
  executor commits and restart without replayed I/O. Concurrent dispatchers create
  only one non-idempotent effect for the same attempt.
- A nine-command journal generated by the committed `9da7639` package reconstructs
  its original intent and ownership, accepts dispatch commands and recovers again.
  Existing record layouts and earlier command results remain compatible.
- The demo loses a successful submission reply, recovers one effect under the same
  request, retains capacity at lease expiry and fences late submissions after
  release. Lifecycle remains READY and operation outcome remains UNKNOWN.
- All 15 supplied numerical/accounting checks remain unchanged and pass.

This completes the scoped simulated dispatch/reconciliation increment within phase
2. It does not provide a real external adapter, authenticated transport, general
distributed atomicity or an unconditional exactly-once guarantee. The simulator's
release contract is deliberately stronger than ordinary cancellation. An executor
without authoritative release remains unresolved rather than freeing capacity by
timeout. The coordinator still blocks the whole affected resource while occupancy
is unresolved; optimizing that conservative policy needs separate evidence.

Next add persistent goal slices and outcome contracts, with outstanding loss,
predicted coverage and observed relief kept separate. Implement conservative overlap,
expiry/failure reopening and observation-defined durability. Use the captured
submission witnesses to define explicit submission/completion temporal contracts
for the deployment episode; do not discharge goals from ACK or resource release.
Phase 2 still has not passed its deployment exit criterion, and phases 3–8 remain
pending. Context inheritance and variable binding remain phase 1 backlog items.

### Sixth increment on 1 October 2026

Implemented persistent goal contracts and episodes, scoped source identity, exact
integer goal slices, conservative coverage commitments and immutable accounting
revisions. Unknown conditions retain the unresolved obligation budget. Predictions
are capped by current outstanding loss, use the maximum live promise within one
overlapping slice and add only across declared disjoint slices. Duplicate paths,
goal aliases and repeated promises cannot create additional obligations or coverage.
Resource ownership, coverage and observed relief remain separate records.

Added direct, exact-product monitoring evidence and declared sample grids, window
lengths and exclusive freshness deadlines. Whole witness sets must retain support
and have distinct measurement lineage. Missing observations, repeated copies,
revoked support and expired freshness cannot pass durability. The monitor distinguishes
PENDING, OBSERVED_SUCCESS, OBSERVED_FAILURE, UNKNOWN and CENSORED. Explicit resumption
starts a new monitoring window; old coverage stays inactive. New failures, expiry,
uncertain execution and release reopen covered work without manufacturing observed
relief. Copying an already known failed measurement does not cancel a new repair
promise. Goal queries recompute present loss; explicit reconciliation records
durable relief/reopening events without accumulating mutable pressure counters.

Added an optional completion contract connecting a pinned lifecycle edge and goal.
It uses the immutable checked submission witnesses, current exact attempt/product
observations, current completion-specific requirements, sampled goal durability and
target validity. Completion observations must be strictly later than submission.
An expired submission credential therefore blocks new actions without rewriting
the past or preventing otherwise supported completion. This bounded temporal policy
does not modify existing lifecycle schemas or implement general temporal logic.

Verification for this increment:

- 358 tests pass. Nineteen goal and twelve coverage contracts run in both volatile
  and durable modes, with cold reconstruction of current projections and history.
- Independent enumeration checks 405 three-state observation timelines and 40
  generated coverage portfolios represented as explicit atomic obligation sets.
- Dispatch/goal integration tests distinguish accepted, uncertain, expired,
  cancelled and released commitments without treating any of them as goal success.
- Recovery tests inject failed accounting/coverage writes and lost replies, and
  reject a saved success generated by a deliberately broken monitor. Four real
  subprocess crash scenarios cover both sides of accounting and temporal lifecycle
  completion commits. Earlier journal compatibility checks still pass.
- The deployment demo starts with 10 outstanding, 6 covered and 4 open units.
  ACK leaves 10 outstanding; the wrong product is rejected; three healthy readings
  yield losses of 10, 10 and 0. Completion passes after credential expiry. A later
  unhealthy observation reopens loss to 10 while stage BUILT and relief history
  survive restart. No causal credit is assigned.
- All 15 supplied numerical/accounting reference checks remain unchanged and pass.

The finite simulated deployment slice now exercises the phase 2 exit behavior.
This does not complete the full architecture or validation lab. Loss remains binary
per declared slice; slices must be explicitly disjoint; fresh sampled observations
do not prove continuous-time health. Goal/monitor scope and witness search are
bounded. Callers must reconcile each relevant event to record every transient loss
revision. General loss models, causal attribution and a complete independent event
reference model remain pending. Pressure/attention dynamics and real adapters are
still absent, and the 64-fixture benchmark has not been run.

Next begin phase 3 by inspecting actual storage and PLN repositories, selecting
compatible pinned revisions and building a small storage/inference smoke test.
Carry the finite service contracts into adapter validation while retaining the
remaining phase 1 and phase 2 breadth work in the backlog. Phases 3–8 have not passed
their exit criteria.

### Seventh increment on 1 October 2026

Inspected the actual OpenCog AtomSpace/cogutil and trueagi-io PLN/PeTTa sources,
selected exact commits in `adapters.lock.json`, and built the C++ AtomSpace target
with GCC 11 and locally staged Guile development packages. The bootstrap fetches
exact revisions, verifies package hashes and stages installation without system
changes or upstream patches. The compiler/runtime versions and native artifact
hashes are recorded. A second build from empty source/build/install directories
passed a real storage and formula smoke test on the same host.

Added a bounded native Atoms/Values transport. Typed records, ordered fields,
context, polarity, provenance and certificate identifiers remain structural;
exact integers use named decimal StringValues. Probabilistic proposals use a
named FloatValue with explicit formula, interpretation and proposal markers.
Native readback verifies canonical identity, outgoing order, final Value updates
and atom counts. A revision-consistent admission export rebuilds from the existing
checked SQLite journal; projection failure cannot change the service's authority.

Added pure grounded PLN deduction and finite-weight revision through the pinned
MeTTa library, using PeTTa on SWI-Prolog 10.0.1. Ordered premise roles and context
are explicit. Exact rational prechecks reject infeasible conditional probabilities;
the runtime also checks upstream's conditions so its failed-precondition `(1,0)`
fallback cannot authorize a proposal. Zero antecedent probability is UNKNOWN.
The heuristic formula and near-one approximation branch are recorded assumptions.
Finite empirical truth rejects nonfinite/out-of-range values and confidence one.

Revision requires an explicit independence declaration bound to both supports.
Common evidence IDs or source roots prevent weight summation even under such a
declaration. Unknown dependence preserves alternatives, duplicate derivations
create no new weight, and ancestry blocks cyclic deduction. Every proposal retains
its snapshot revision, truth model, formula, assumptions and source lineage.
Malformed/ambiguous runtime output, diagnostics, timeouts and dependency drift fail
closed. Runtime calls perform no network imports.

Verification for this increment:

- 381 default tests pass, including the unchanged finite-service recovery suite.
  New checks enumerate 125 exact four-cell probability models and exercise ordered
  binding, scope, duplicate/cycle guards, dependence assumptions and adapter errors.
- 14 separate integration tests execute the real C++ and MeTTa runtimes. They cover
  identity, order, Unicode, numeric Values, exact large integers, alias overwrites,
  malformed native commands, checked journal reconstruction and revocation.
- Real deduction and revision outputs match independent rational fixtures, including
  boundary/near-one cases. Invalid probability domains cannot accept fallback truth;
  malformed or certain empirical output and process timeouts cannot become support.
- The native demo computes approximately `(0.68, 0.3136)`, preserves five source
  roots and verifies the proposal's AtomSpace FloatValue without creating an
  accepted belief. Missing native dependencies fail the optional suite explicitly.
- Both the regular and clean native builds pass a storage/inference smoke test.
  All 15 original standalone numerical/accounting checks remain unchanged and pass.

This completes phase 3's dependency selection/build smoke test and introduces the
bounded storage/proposal contracts. It does not complete phase 3. AtomSpace is a
disposable snapshot projection, not a persistent transactional authority. Full
ledger export, incremental native updates, threshold indexes and native persistence
remain pending. The pure PLN snapshot and independence declarations are supplied
by trusted callers; no issued probabilistic certificate or durable numeric belief
commit exists yet. The adapter does not run PLN search or assert general joint
consistency or calibrated independence. Attention, FDAS and Freeciv remain absent.
Builds pin source/package inputs and record the tested toolchain; they are not
hermetic operating-system images or bit-reproducible artifacts.

Next implement a separately versioned probabilistic belief ledger with exact
snapshot/lineage binding, issued pre/post certificates, checked durable commits and
replay. Keep uncertain beliefs distinct from hard commitments and preserve existing
journal compatibility. Then run common service contracts and the deployment episode
through the real adapters. The broader phase 1/2 backlog and phases 4–8 remain open.

### Eighth increment on 1 October 2026

Implemented `probability-ledger/v1` and `probability-certificate/v1` under the same
single commit authority. Numeric policies pin trusted report sources, truth model,
interpretation, formula revision and checker. Source reports retain immutable
evidence identity, provenance and validity. Grounded rules and explicit independence
models bind exact accepted numeric premise revisions. The new ledger keeps estimates
as alternatives; none become Boolean facts, lifecycle prerequisites or goal samples.

Added issued pre/post certificates and serialized numerical commits. Certificates
bind the authority, full current context revision, policies, rule, input records,
source lineage, time and exact proposal. Native PLN computes outside the authority
lock; postcertification and commit recheck all captured inputs. Revocation during
native computation cannot authorize a stale result. Repeated derivations retain the
same support without new weight. Source expiry/revocation, rule/policy replacement
and revoked independence models invalidate exact descendants while keeping independent
alternatives and immutable history.

Implemented a deterministic checker for the pinned binary64 formula expressions,
including upstream's rounded preconditions. Added a complete exact-rational joint
check for the three selected propositions, their marginals and all three pair
intersections including the proposed conclusion. The certificate records eight
nonnegative world masses. This rejects a concrete near-one upstream approximation
case that passes all pairwise checks but has no compatible joint distribution.
Nonfinite intermediates, undefined conditions and altered output/lineage fail closed.

Extended the explicit codec with canonical finite binary64 hexadecimal values and
new numeric records. Existing finite record layouts and command encodings are
unchanged. Recovery reconstructs guards, formulas and joint witnesses without
PeTTa/AtomSpace I/O, and rejects saved success from a broken checker. Journal failure
rolls back the numeric ledger and its permits; ambiguous commits reconcile by the
original key. History limits return UNKNOWN without partial publication.

Verification for this increment:

- 454 default tests pass, including all existing finite-service and committed-version
  journal compatibility checks. The same 31 numerical contracts run in volatile and
  durable modes with cold reconstruction.
- 46 native integration tests pass. Those 31 contracts also run with real PLN
  inference and AtomSpace projection before/after recovery. Generated conformance
  cases compare 20 deduction and 20 revision results with the replay checker exactly.
- An independent enumerator constructs every multiset of four Boolean observations
  and checks 15,625 marginal/pair constraint combinations against the joint checker,
  including reconstruction of every returned witness.
- Tests cover forged permits and numerical/provenance changes, ordered/scoped
  premises, stale snapshots, concurrent commits, source validity, rule/policy/model
  retirement, alternatives, cycles, idempotency and Boolean gate separation.
- Recovery tests cover partial certificate allocation, failed writes, ambiguous
  replies, corrupt history, broken-checker acceptance and real subprocess crashes
  on both sides of a numerical commit. Native runtime calls are forbidden during
  the recovery test.
- The demo commits native deduction at approximately `(0.68, 0.3584)`, records eight
  exact joint-world masses, recovers an identical numeric view and native projection,
  and becomes STALE after source revocation. Its hard query remains UNKNOWN.
- All 15 original standalone numerical/accounting reference checks pass unchanged.

This completes the scoped certified numeric ledger and checked replay increment,
including common finite/native service contracts. Phase 3 remains open: the native
store is still a disposable projection, and the full deployment episode does not
yet use a declared probabilistic decision contract. Numerical alternatives are not
silently combined into a global joint model. Larger scopes, calibrated loss, PLN
search, persistent native storage and numeric-to-action policy remain pending.
Trust remains the existing in-process authority boundary; independence is an explicit
registered assumption, not an empirical statistical test.

Next define a versioned probabilistic decision contract for the deployment slice,
with declared units, thresholds/uncertainty and exact current numerical support.
Carry its decisions through lifecycle/action gates without promoting estimates into
hard facts, then validate the episode through both real adapters. The remaining
phase 1/2 breadth items and phases 4–8 remain open.

### Ninth increment on 1 October 2026

Executed the deployment decision work in five steps:

1. **Declare policy.** Added `probability-decision/v1`, exact execution/product
   binding, one to sixteen criterion literals, dimensionless strength intervals
   and a separate PLN evidence-adequacy floor. Unsupported units, selection
   policies and confidence interpretations are rejected. Contract registration
   precedes the first certificate for an execution version; changes require a new
   version. Existing versions retain their original declared requirements.
2. **Capture exact witnesses.** Each criterion considers every current certified
   exact-literal estimate. Opposite orientations require an explicit model and
   return UNKNOWN in this fragment. Missing/inadequate support, out-of-policy
   strengths and retired revisions remain distinguishable. Execution certificates
   bind the full evaluation digest and store an immutable numerical witness in the
   same journal transaction. No prediction is inserted into the hard ledger.
3. **Enforce action gates.** Certification, atomic reservation, intent inspection,
   durable preparation and final simulator send enforce the registered contract.
   Pending intents retain the exact certified support set, so even an equal-valued
   replacement needs a new attempt. Current liveness remains mandatory. Unrelated
   context updates do not change that basis. Reconciliation/release and observed
   completion preserve valid historical submissions after forecasts expire.
4. **Integrate the deployment episode.** Added a shared finite/native scenario
   using real pinned PLN deduction, declared acceptance thresholds and a real
   AtomSpace projection of decisions, numerical/hard support, execution records,
   goal accounting and lifecycle completion. Extended native structural projection
   to ordered numerical tuple elements using exact typed Values. The episode
   recovers an identical complete snapshot and native graph.
5. **Validate and document.** Added common volatile/durable/native decision
   contracts, boundary cases, source/rule/policy retirement, forgery checks,
   concurrency at final send, lost replies, ambiguous/failed writes, rollback,
   broken-checker replay rejection and real process crashes around reservation.
   Documented units, uncertainty semantics, exact support retention and scope in
   `DECISIONS.md`; updated the capability manifest and adapter documentation.

The deployment forecast is approximately `(0.68, 0.3584)`, accepted by the explicit
`strength >= 0.65` and `confidence >= 0.35` policy. Its hard query stays UNKNOWN.
The goal initially has ten outstanding units, six covered and four open. ACK leaves
all ten outstanding. Despite expiry of the submission credential and prediction,
exact later product/outcome observations plus three healthy samples permit observed
completion; losses after samples are `[10,10,0]`. A later failure reopens ten units
while the historical stage remains BUILT. No causal credit is assigned. These
thresholds and forecasts are synthetic conformance inputs, not calibration results.

Verification for this increment:

- 507 default tests pass, including the existing committed-version journal
  compatibility checks. Nineteen decision contracts run both volatile and durable,
  plus model, full-episode and thirteen dispatch/recovery tests.
- 67 optional native tests pass, including those nineteen decision contracts,
  the complete deployment episode and exact scalar/ordered-tuple native readback.
- All 15 original standalone reference checks pass unchanged.
- Native I/O is excluded from checked replay. Existing non-decision record layouts
  and command results are unchanged. The supplied design-input hashes still match.

The scoped numerical-to-action deployment integration is complete. Native AtomSpace
remains a disposable projection and SQLite remains authoritative; protected native
storage/index ownership and broader adapter scope are not complete. The current
decision conjunction does not infer a joint risk bound across forecast criteria,
and confidence is not a calibrated probability or interval. Pressure and transport
remain separate reference examples.

Next increment: versioned deployment traces and an independent event oracle for
the implemented finite fragment. First declare public event/trace records and
separate evaluator expectations, then implement a cold reference projection that
does not call service gate/accounting helpers. Compare every event prefix for
submission, expiry/revocation, uncertainty, exact outcomes, durability and reopening;
add restart prefixes and a reproducible mutation witness. Publish explicit coverage
before expanding toward four controls for every F01–F16 family and the B0 scheduler.
This advances the phase 2/4 validation foundation while broader phase 1/3 items and
phases 5–8 remain open; it does not claim the 64-fixture target is already satisfied.

### Tenth increment on 1 October 2026

Implemented the deployment trace/oracle increment in four steps:

1. **Public contract and trace capture.** Added `deployment-initial/v1`,
   `deployment-event/v1` and `deployment-trace/v1`, with strict field/numeric/time
   validation and one-event-at-a-time input. The conformance adapter drives the
   existing public admission, decision, resource, dispatch, goal and completion
   APIs. Its records expose actual accepted/current assertions, numerical support,
   operation/intent state, resource usage, observed goal labels and accounting,
   with real issued certificates and execution diagnostics. Rejected composite
   events retain earlier successful command effects instead of hiding them.
2. **Independent cold projection.** Added an evaluator-only model importing only
   `copy` and `json`. It rebuilds each prefix from public inputs and does not receive
   actual service output or call service logic/accounting helpers. Direct evidence
   tables, enumerated occupancy ticks, sampled time sets and an independent remote
   effect/receipt model cover the declared finite profile. The harness compares
   every prefix, then reopens both actual journals and compares the recovered
   state to the same reference. Out-of-scope references raise explicit gaps.
3. **Fixed and generated controls.** Added eight development cases covering valid
   deployment, missing/revoked/alternative support, lost ACKs, wrong products,
   capacity conflict, uncertain occupancy, exact thresholds, censoring/resumption,
   overlapping promises, sample revocation and freshness reopening. Source and
   fixture receipts bind generator/oracle/harness/mutants/protocol/runtime files;
   extra unlisted fixtures, receipt drift and count/ancestry changes fail validation.
   Twelve seeded cases add stateful fault/observation variation without rejection
   based on outcomes. Identity renaming preserves ancestry and semantics; commuting
   initial observations preserve subsequent results.
4. **Mutation witnesses and scope reporting.** M06 makes an ACK discharge observed
   loss and is detected at d01 prefix 7; M11 labels censoring as observed failure
   and is detected at d07 prefix 3. Invocation canaries prove each faulty branch ran.
   Unmodified controls must pass, and raw offending output is written before
   oracle comparison. The report retains failed cases and errors and exits nonzero
   on mismatches, reference gaps or surviving mutants. `VALIDATION.md` documents
   schemas, execution, evidence boundaries, coverage and remaining work.

Verification for this increment:

- 526 default tests pass; the new suite contains 19 validation/protocol tests.
- All eight fixed cases agree at 137 prefixes and 137 reopened journal states.
  Twelve seed-8417 development cases add 251 compared/recovered prefixes.
- Fixed checkpoints independently anchor critical outcomes. Tests also exercise
  capacity two, exact lease boundaries, partial command effects, release fencing,
  receipt drift, malformed input and preserved raw mutant outputs.
- A real subprocess exchanges public initial state and one current event at a time
  with the streaming worker. The normal differential harness still shares a Python
  process with its runtime adapter; no filesystem/process sandbox is claimed.
- All 67 existing native integration tests and all 15 original standalone reference
  checks pass. Supplied design-input hashes remain unchanged. Core admission,
  dispatch and goal semantics were not modified by this increment.

This completes the independent deployment prefix-validation foundation, within
the declared direct-evidence/single-context profile. It does not establish the full
phase 2 event model or complete phase 4. The eight cases are explicitly zero
family-complete fixture claims against the 64 target, and all descendants remain
in one development parent/split. No benchmark scheduler, normalized cost comparison,
calibration result or closed-loop benefit is claimed. M01–M04 and M06/M11 now have
witnesses; M05, M07–M10 and M12 remain open.

Next extend the public trace and cold reference to grounded rule admission,
multiple contexts, alternate derivations and lineage reuse. Add explicit family/
control coverage for these mechanisms and the next applicable mutation witnesses,
then develop B0 over the verified public interfaces. General shrinking, controlled
concurrent interleavings and evaluator process/filesystem isolation remain phase 4
work. Broader phase 1/3 scope and phases 5–8 remain open.

### Eleventh increment on 1 October 2026

Implemented the grounded rule/context/lineage validation increment in four steps:

1. **Additive public admission profile.** Added `admission-initial/v1`,
   `admission-event/v1` and `admission-trace/v1`. Up to eight declared atoms and
   eight grounded rules feed four explicit contexts with finite CNF policies.
   Events cover ordered derivation, rule/policy replacement, expiry, revocation,
   independent or shared-root numerical reports and explicit revision models.
   Nested wire arrays are immutable after validation. Exact event aliases identify
   actual committed revisions, preserving duplicate admission, alternative proofs
   and historical retirement without substituting an equivalent parent.
2. **Independent cold reference and recovery.** Added an evaluator-only oracle
   importing `copy` and `fractions`. Exhaustive Boolean worlds check consistency
   independently of runtime DPLL. A separate dependency graph models context-local
   clocks, exact retirement and shared leaf lineage. Rational operations with
   explicit binary64 rounding check numerical revision without runtime helpers or
   tolerance. The shared harness compares complete actual semantic projections
   and reopens the authority at every prefix. Original deployment schemas, service
   record layouts, journal commands and admission semantics remain unchanged.
3. **Scoped four-control matrix.** Added positive, blocked, boundary and revision
   controls for F01 ordered premises, F02 joint consistency, F04 context separation
   and F05 lineage reuse. Sixteen fixed cases contain 127 prefixes; eight seed-17041
   cases add 168 prefixes without outcome filtering. The corpus records neutral
   public inputs separately from evaluator schedules/checkpoints and pins source
   and fixture receipts. All descendants stay in the development split. These are
   bounded mechanism controls, with zero claims of complete benchmark families.
4. **M05 and native evidence.** The shared-lineage mutant substitutes separate
   report IDs for measurement roots, incorrectly accepting duplicated reports as
   independent evidence. The unmodified a14 control blocks revision at prefix 5;
   M05 instead produces PASS and confidence 2/3. A canary confirms invocation,
   and the raw offending output is saved before comparison. Optional native runs
   use actual PeTTa/PLN inference, and integration tests compare AtomSpace hard and
   numerical projections before and after journal replay.

Verification for this increment:

- 543 default tests pass, including 17 new admission protocol/conformance tests.
- 69 optional native tests pass, including every fixed admission case against the
  cold oracle and projection/replay checks across contexts and retired lineage.
- All 15 original standalone reference checks pass unchanged; supplied design
  input hashes still match. Existing committed-version journal checks pass.
- Fixed/seeded admission checks compare and recover 295 prefixes, in addition to
  the previous 388 deployment prefixes. These counts exclude extra focused and
  metamorphic cases, which cover renamed identities, commuting contexts, eight-atom
  bounds, nested numerical revision, exact model retirement, subnormal/near-one
  rounding, invalid policy replacement and streaming one-event subprocess I/O.
- Both corpus receipts reject unlisted files and source drift. Actual reports retain
  failures and mutation traces; no comparator rewrites or repairs emitted output.

This completes the planned grounded admission trace/oracle extension. It does not
complete phase 4: F01 search, F04 changing goals/fields, broader F05 hidden-source
models, the 64-fixture target, general shrinking, concurrent interleavings and OS
isolation remain open. Native AtomSpace is still a disposable projection, and
numerical deduction retains separate unit/native contracts rather than this trace
oracle. M01–M06 and M11 have witnesses; M07–M10 and M12 remain open.

Next increment: introduce bounded public candidate enumeration and deterministic
B0 scheduling over the verified service interfaces. First specify candidate/cost
records and deterministic ordering, then implement a gate-driven scheduler with
separate work counters, and finally compare closed-loop prefixes against fixed
reference episodes. Add applicable family controls and mutation witnesses before
making comparative performance claims. General shrinking, evaluator OS isolation
and controlled interleavings remain separate phase 4 deliverables; broader phase
1/3 items and phases 5–8 remain open.

### Twelfth increment on 1 October 2026

Implemented the first bounded B0 controller in four steps:

1. **Public candidates and budgets.** Added `deployment-b0-public/v1`,
   `deployment-candidate/v1`, `deployment-b0-step/v1`, a budget-result schema and
   `deployment-b0-checkpoint/v1`. Public inputs expose the existing deployment
   contract and neutral observation capabilities/costs, never future responses or
   hidden state. The provider fully recomputes a bounded dependency frontier from
   current evidence and the real operation ledger. Incomplete enumeration produces
   an explicit budget stop without selecting from a partial frontier.
2. **Deterministic, gate-driven selection.** B0 orders ready work by remaining
   protocol stages, observation cost and public identity. It obtains prerequisites,
   creates/reserves attempts, dispatches, reconciles uncertainty, queries outcomes,
   monitors health, accounts observed loss, advances applicable completion and
   releases resources through existing public service commands. Empty/failed
   probes are charged and suppressed within a logical tick so alternatives receive
   service. A stale selected request still passes through the authority's current
   checks. Submission is never treated as an observed goal outcome.
3. **Action-dependent validation worlds.** Added twelve fixed and six seed-2601
   evaluator-owned worlds. Only selected probes deliver observations, and actual
   physical effects enable delayed outcome reports. Hidden availability, fault
   schedules, effect instrumentation and reference outputs are outside the
   controller's read/execute port. Every actual emitted event is recorded before
   comparison with the existing independent cold oracle and checked journal replay.
   Failed cases and unresolved goals remain explicit in the report.
4. **Work accounting, checkpoints and M07.** Reported full state reads, loaded
   record rows, candidate visits/frontier sizes, issued actions, observation costs,
   public events, admission journal commands and captured certificates. Checkpoint
   restoration between requests preserves the selected action/event stream. Added
   a separate M07 conformance fixture: an attempt followed by a similarly named
   wrong-product report. A canary proves the matching defect ran; the unmodified
   authority returns FAIL and the mutant returns PASS at prefix 2. Deleting either
   event removes the divergence, establishing deletion minimality for this fixture.

Verification for this increment:

- 561 default tests pass, including 18 new B0 candidate, budget, recovery,
  information-boundary, closed-loop and mutation tests.
- 70 optional native tests pass. The new native test projects actual hard,
  numerical and execution-decision state after lost-ACK and wrong-product episodes,
  then verifies identical AtomSpace readback after journal replay.
- All 15 original standalone reference checks pass unchanged. Supplied design
  hashes and existing committed-version journal compatibility checks still pass.
- The fixed worlds compare/recover 197 emitted prefixes; six generated worlds add
  135. Nine fixed worlds reach observed goal success. The unavailable-prerequisite,
  observation-cost and candidate-budget controls remain unresolved as expected.
- Tests verify that an empty cheap probe does not starve an available alternative,
  lost replies reconcile before another submission, pre-effect failure retries the
  same request, and a credential revoked after selection blocks the old dispatch.
  Refusing all work fails the positive control. Work totals include rejected,
  empty and composite requests; raw offending mutation output remains unmodified.

This completes the scoped candidate/B0/closed-loop increment over one deployment
dependency graph. It does not complete general B0 or phase 4. Grounded-rule search,
beam/whole-plan alternatives, multi-goal portfolios, normalized cost measurements,
same-information optimal references and comparative benefit claims remain open.
The counters exclude internal solver steps, repeated predicate evaluations, total
executor/storage I/O and memory; elapsed times include evaluator checks/recovery.
Scheduler checkpoints are not an atomic controller/executor crash transaction.
The harness remains in one process without OS isolation, and no case is claimed
as a complete benchmark family. M01–M07 and M11 have witnesses; M08–M10 and M12
remain open. Core service schemas, journals and authority semantics are unchanged.

Next increment: generalize public candidate access to bounded grounded-rule search
and whole alternative plans, starting with an independently enumerated tiny
same-information planning reference. Add fixed-candidate and closed-loop controls
for alternative resource/time choices before comparative scheduling claims.
General event shrinking, controlled interleavings, evaluator OS isolation and the
64-fixture target remain separate phase 4 work. Broader phase 1/3 scope and phases
5–8 remain open.

### Thirteenth increment on 1 October 2026

Implemented the bounded grounded proof-planning increment in four phases:

1. **Public finite planning contract.** Added immutable public rule-cost/goal
   descriptions, detached current snapshots, complete plan witnesses and explicit
   search budgets. Snapshot digests bind public configuration, current context and
   policy revisions, clock, grounded registry, exact support aliases/lifetimes and
   remaining proof-work/step quotas. Hidden scripts are excluded from this API.
2. **Whole-plan search and gate-driven execution.** Added uniform-cost search over
   grounded AND derivations, shared subproofs, conjunctive goals, cycles and integer
   waits. Complete alternatives must jointly meet their declared cost, deadline,
   premise freshness and hard policy. All distinct support lifetimes remain
   available. The controller recomputes each request and executes only the first
   step through the actual admission gates. Intervening public edits return STALE
   before work is charged; failed issued commands still consume their quotas.
3. **Independent exact reference and closed-loop controls.** Added a separate
   layered state enumerator with exhaustive Boolean worlds, plus complete witness
   replay. It receives exactly the same frozen public problem. Both implementations
   report incomplete search explicitly, and no partial reference result establishes
   an optimum. Twenty-two fixed controls and twelve reproducible seed-4103 graphs
   exercise complete alternatives and actual admission/recovery prefixes. Selected
   plans are logged before reference checking or execution.
4. **Recovery, integration and reproducibility.** Verified exact aliases, symbolic
   plan references, public edit/replan behavior, explicit budget stops, forged step
   rejection, controller recreation, same-wrapper service recovery and native
   AtomSpace readback. Added separate public/evaluator fixtures and a source-pinned
   corpus receipt; refreshed all existing runtime receipts. Core service schemas,
   journals, supplied design inputs and designated mutation witnesses are unchanged.

Verification: all 583 default tests pass, including 22 new planning tests; all
71 optional native tests and all 15 original standalone reference checks pass.
The final corpus CLI passes all 22 fixed controls. Tests also verify constructor
input detachment, complete witness rejection, explicit reference exhaustion and
raw proposal retention when comparison fails. Existing design hashes and
committed-version journal compatibility checks remain intact.

The fixed cases compare/recover 77 emitted prefixes with 11 completed and 11
expected unresolved goals. Seeded graphs add 29 prefixes and three completions.
The exact objective is `(declared proof-work, finish time, steps)` for each frozen
bounded hard-proof problem; it is not measured compute cost or a prediction of
future edits. This profile is separate from deployment scheduling. Physical
resource alternatives, temporal execution portfolios, pressure-driven selection,
comparative benefit and general B0 remain open. Wrapper quotas are not durable
resource reservations or a crash-atomic transaction. There are still zero
family-complete fixtures and no new M08/M09/M10/M12 witnesses.

Next increment, in order:

1. Define bounded alternative execution plans over current renewable resource
   contracts, including total interval occupancy and immutable rule/action identity.
2. Add an independent tiny same-information occupancy/time enumerator before
   connecting plan selection to actual reservation, intent and dispatch gates.
3. Test fixed alternative portfolios and public changes between selection and
   reservation, checking every resulting event prefix and observed completion.
4. Record work separately from declared costs and add applicable family controls
   before any comparative scheduling claim.

General shrinking, controlled interleavings, evaluator OS isolation and the
64-fixture target remain separate phase 4 deliverables. Broader phase 1/3 semantics
and phases 5–8 remain open.

### Fourteenth increment on 1 October 2026

Implemented renewable-resource execution alternatives in four phases:

1. **Bounded whole-contract portfolios.** Added immutable public jobs, renewable
   capacities and alternative execution modes. Each mode binds exact identity and
   revision, all resource quantities/units, declared cost and predicted duration.
   Detached snapshots expose only observed readiness/lifetimes, completed products,
   actual leases/remote uncertainty, active execution and remaining credits.
   Complete serial schedules must fit aggregate capacity, expiry, cost and time.
2. **Independent occupancy/time reference.** Added an evaluator-only enumerator of
   complete job orders, mode products and integer start tuples, using discrete
   occupancy independently of the runtime interval sweep. Complete witness checks
   prevent mixing pieces of alternatives. Exhaustion has an explicit unknown
   outcome and cannot promote an incumbent to an optimum. Optimality concerns only
   the declared frozen serial prediction model.
3. **Actual reservation, dispatch and observed completion.** Connected first-step
   selection to the existing operation, execution-permit and durable intent APIs.
   Current service checks still guard reservation and final send. The controller
   reconciles lost replies, retries a failed idempotent submission with the same
   request, requests outcome observations, advances only with exact outcome support,
   and obtains an authoritative executor fence before starting another job.
   Public edits can stale the selection or block dispatch after reservation.
4. **Closed-loop prefix/recovery validation.** Added twenty fixed and eight seeded
   episodes, an independent cold event model, separate public/evaluator files and
   source-pinned receipts. Actual failures and partial effects are logged before
   comparison. Both journals reopen after each emitted event; native tests project
   actual hard, resource, reservation, intent and dispatch records after replay.
   All four existing corpus receipts include the new runtime modules.

Verification: all 608 default tests pass, including 25 new resource-planning tests;
all 72 optional native tests and all 15 original standalone reference checks pass.
The final corpus CLI passes all twenty fixed controls. Additional regression tests
cover stale observation selection at the deadline, current product/milestone
retirement and the prohibition on implicitly reusing a terminal lifecycle edge.
Original design hashes and committed-version journal compatibility remain intact.

The fixed cases compare/recover 119 prefixes, with eleven completed and nine
expected unresolved episodes. Eight seed-5107 cases add 44 prefixes and five
completions. Controls cover complete resource packets, serial portfolio budgets,
half-open leases, stale selections, revocation, remote occupancy, lost ACKs,
pre-effect failure, wrong products and delayed/missing outcomes. A delayed outcome
can invalidate the remaining schedule; acknowledgement and lease expiry never
manufacture completion or release. F03 coverage remains a finite renewable slice,
not the full consumable/resource-production family.

The service conservatively blocks resources under remote uncertainty; this
increment deliberately scopes its portfolios to serial independent jobs. General
concurrent schedules, combined grounded proof/execution planning and shared
cross-product prerequisites remain open. Duration and cost are declared contracts,
not measured computational cost or guarantees about future observations. Work
credits and selection metadata remain synchronous wrapper state rather than a
crash-atomic controller checkpoint. There are still zero family-complete fixtures,
no new designated mutation witnesses and no comparative scheduling claims.

Next increment, in order:

1. Generalize event-trace shrinking beyond the existing hand-minimized M07 case,
   using the strict public event protocols and bounded independent prefix oracles.
2. Preserve a concrete first-divergence signature and passing unmodified control
   while removing events; reject unsupported oracle cases explicitly.
3. Record original/reduced traces, deletion checks, source receipts and split
   ancestry for existing M05/M06/M07/M11 witnesses.
4. Add reproducibility and failure-retention checks before claiming a general
   minimization facility; keep deterministic interleavings, remaining designated
   mutants, evaluator OS isolation and the 64-fixture target visible as phase 4
   work. Broader phase 1/3 semantics and phases 5–8 remain open.

### Fifteenth increment on 1 October 2026

Implemented the scoped general event-deletion reducer around the independent
admission/deployment prefix oracles. Work proceeded through four stages:

1. **Bounded reduction and exact failure identity.** Added a reusable deterministic
   chunk/single-event deletion engine, unique-event and evaluation bounds, detached
   candidate inputs and structured outcomes. Reductions retain identities,
   arguments and order. The original profile, initial-state digest, mutant,
   divergent event, path and exact expected/actual values bind every acceptance.
2. **Independent controls and live mutation replays.** Added strict protocol
   adapters that run each candidate unmodified against its cold oracle and recover
   every prefix before invoking a canary-backed mutation. Oracle gaps and errors
   cannot establish minimality. Every final deletion is tested and the retained
   witness replays again. Exhaustion and failed final replay stay explicit.
3. **Recorded evidence and reproducibility.** Added source-pinned development
   seeds, deterministic expected decisions, explicit generation, a CLI and bundle
   verification/replay. Candidate requests are flushed before execution; actual
   control/mutant records are retained before comparison. Receipts bind source
   files, the dependency lock, original corpus ancestry and raw file inventories.
   Runs use new directories; timing/UUID variation is kept out of semantic
   reproducibility comparisons while remaining present in raw evidence.
4. **Adversarial verification and native integration.** Added tests for failure
   drift, boolean/numeric distinctions, callback mutation, unknown/error handling,
   budgets, non-global minimality, final replay failure, checkpoint positions,
   canaries, source drift, corrupt evidence and CLI replay/nonzero failure exits.
   Independent fresh replays check all reduced witnesses and every remaining
   deletion. Native PLN reproduces M05 and its five necessary events.

The reductions are M05 12→5 events, M06 23→6, M07 2→2 and M11 13→1. Across 88
predicate calls, each retained failure keeps its original signature and passing
unmodified control. All fourteen final deletion checks remove that failure.
All 638 default tests pass, including thirty new tests for this increment. All
73 optional native tests and all 15 original standalone reference checks pass.
The corpus CLI reproduces all four expected reductions and verifies every saved
bundle. Original design hashes, all earlier corpus receipts and committed-version
journal compatibility checks remain intact.

This completes bounded whole-event deletion for the two public trace protocols
and four existing mutant branches. It makes no global-minimum claim and adds no
new designated mutant or family-complete fixture. The engine is reusable through
an evidence-bearing predicate; initial/argument shrinking, reference repair and
concurrent schedule reduction require separate semantics. Runtime code, authority
schemas, original design inputs and all five prior corpus receipts are unchanged.

Next increment, in order:

1. Add deterministic interleaving control around certified admission and resource
   reservation, with explicit observation points and reproducible schedules.
2. Check newly inserted blockers and competing capacity claims against the
   independent model; wire M08/M10 witnesses only when their changed branches and
   passing unmodified controls are demonstrated.
3. Retain and reduce failing schedules through the new evidence pipeline, keeping
   evaluator scheduling metadata distinct from public event semantics.
4. Continue phase 4 family coverage and evaluator OS isolation. M09/M12 depend on
   their pressure/transport mechanisms; do not mark them covered early. The
   64-family-fixture target, broader phase 1/3 semantics and phases 5–8 remain open.

### Sixteenth increment on 1 October 2026

Implemented the next bounded interleaving increment in four stages:

1. **Expose the real atomic reservation boundary.** Extracted private read/check/
   construct and publication helpers inside the existing authority transaction.
   The public method still holds one RLock across all checks, claims, intent and
   journal publication. Added a strict three-atom/two-worker public adapter with
   actor-bound admission and execution certificates; scheduler data remains in
   the evaluator.
2. **Control actual threads and independently compare state.** Added a controller
   that pauses at completed reservation checks, observes a contender requesting
   the held real lock and chooses publication order. Ownership, not timing,
   establishes blocking. A cold eight-world Boolean/discrete-occupancy reference
   checks every completed prefix. Twenty-two cases include sixteen direct controls
   and all six order-preserving certify/reserve merges. Recovery occurs only after
   threads are quiescent; native projections and uncontrolled stress supplement
   the deterministic controls.
3. **Demonstrate precise M08/M10 defects.** M08 drops newly inserted blockers'
   invalidation dependents while retaining the full consistency fallback. The
   reference catches unnecessary loss of unrelated support, not unsafe admission.
   M10 moves the unchanged complete checks outside atomic publication; both
   workers can pass before either claims capacity, and the raw output records two
   claims on one unit. Invocation canaries distinguish exercised defects from
   no-op patches. The service's normal gates remain enabled in every control.
4. **Reduce and retain reproducible evidence.** Reused the bounded reducer with
   signatures that also bind the evaluator schedule. M08 reduces from five to one
   event, M10 from six to four, in 6 and 21 predicate calls. All five remaining
   single-event deletions remove the failure, and fresh final replays preserve
   it. Separate public/evaluator files, mutation decisions, source receipts,
   schedule logs and raw traces make each run reviewable. A regression catches
   thread-identifier reuse after rejection before a checkpoint.

The corpus compares 79 prefixes and recovers at 70 quiescent checkpoints; nine
cases configure paired reservations, including two early-rejection controls.
The prior four trace reductions reproduce unchanged after refreshing all six
earlier corpus receipts. Initial-state and schedule shrinking are not claimed.
Original design inputs and journal schemas remain unchanged. All 664 default
tests pass, including 26 new tests for this increment. All 74 optional native
tests and 15 original standalone reference checks pass; the affected native test
also passes after the final fresh-attempt schedule guard. The final CLI reproduces
both pinned reductions and verifies its complete evidence report.

This adds two designated mutant witnesses, leaving M09/M12 open. The M08 profile
models a missing invalidation dependency at the full-scan boundary; it does not
introduce or claim to validate an optimized constraint index. There are still
zero family-complete fixtures. General thread scheduling, inter-process isolation,
multi-resource race enumeration and fresh-process wrapper recovery remain open.

Next increment, in order:

1. Extend controlled scheduling to the actual final dispatch gate, inserting
   credential revocation after selection/preparation but before external send.
2. Add lease-expiry versus external-acknowledgement schedules and check durable
   uncertainty, reconciliation and fencing against an independent model.
3. Retain reproducible event/schedule evidence and passing controls; extend the
   reducer's schedule domain only with explicitly defined semantics.
4. Continue phase 4 family coverage and evaluator process isolation before broad
   safety or performance claims. M09/M12, pressure/attention mechanisms and phases
   5–8 remain pending; broader phase 1/3 semantics and the 64-fixture target remain
   visible backlog items.

### Seventeenth increment on 1 October 2026

Implemented the controlled dispatch increment in four stages:

1. **Expose actual deliveries without scheduler knowledge.** Added a strict
   64-event public adapter around the existing authority and durable simulator.
   Queued requests and lost acknowledgements retain actual immutable request and
   receipt objects. Later commands deliver those objects. Public messages carry
   no schedule, expected result or future information. Final-send gates, resource
   uncertainty rules and journal schemas remain unchanged.
2. **Exercise both sides of the atomic send boundary.** The evaluator pauses an
   actual dispatch immediately before simulator submission or after its effect
   but before its receipt returns. A second thread actually tries the held RLock
   without blocking, establishing that revocation or clock advancement cannot
   enter. It then waits outside the lock until the first completed state has
   been recorded. Early rejection and already-accepted retries finish without a
   fabricated submission checkpoint. An unlocked-send negative control verifies
   that the scheduler detects a missing authority lock.
3. **Independently model delayed requests and local knowledge.** Extended the
   standard-library cold deployment model with global remote receipt sequences,
   immutable transport packets and locally observed receipt ordering. Twenty-four
   cases cover final-gate rejection and restored credentials, four real paired
   send/acknowledgement checkpoints, three no-send pairs, lease expiry with lost
   replies, uncertain capacity, authoritative release before delayed arrival,
   old acknowledgements after fencing, duplicate delivery, reconciliation and
   missing references. Every completed prefix is compared before journal reopen;
   native tests project actual hard/numeric/resource/dispatch records on both
   sides of recovery. Replay is also checked with executor I/O disabled.
4. **Retain and reduce diagnostic failures.** Added invocation-backed evaluator
   patches for using preparation-time gates at send and retiring uncertain intent
   state at lease expiry. The former reduces from nine to eight events in 34
   predicate calls; the latter from eight to seven in 30. All fifteen remaining
   single-event deletions remove the exact failure, and fresh final witnesses
   reproduce it. Initial state and scheduling metadata remain fixed. Raw actual
   states and schedule evidence precede oracle comparison; reports verify complete
   file inventories, source receipts, schedule observations and pinned reductions.

The corpus compares 227 prefixes and reopens the authority and executor journals
at 220 quiescent boundaries. Transport inbox metadata survives only in the same
wrapper; no fresh-process inbox recovery or external network protocol is claimed.
Seven prior corpus receipts are refreshed for the two new runtime modules; prior
expected outcomes and reductions remain unchanged. Original design hashes,
authority semantics and journal schemas remain intact.

Verification: 686 default tests, 75 optional native tests and all 15 original
standalone reference checks pass. The new corpus CLI reproduces both diagnostic
reductions and verifies its saved report. These are bounded development controls,
with zero family-complete fixtures and no new designated mutant coverage.

Next increment, in order:

1. Strengthen the separate-process public-command boundary: give workers only
   their public initial state and delivered commands, with evaluator-only
   schedules, labels and reference state retained by the controller.
2. Define and test explicit worker failure/restart semantics, including what
   observed transport metadata must be persisted before fresh-process recovery
   can be claimed. Keep authority/executor journal recovery separate from inbox
   and controller recovery.
3. Preserve raw worker output before independent comparison, source receipts and
   reproducible failure evidence; distinguish process separation from actual
   filesystem/capability isolation.
4. Continue phase 4 family coverage. M09/M12 await pressure/attention and transport
   mechanisms; broader phase 1/3 semantics, the 64-fixture target and phases 5–8
   remain pending.

### Eighteenth increment on 1 October 2026

Implemented the next process-boundary increment in four stages:

1. **Give runtime workers only current public inputs.** Added a shared serial
   JSON-lines worker for the existing admission, deployment and dispatch public
   protocols. The evaluator copies only runtime Python modules into a separately
   receipted bundle, launches Python with isolated startup and bytecode writes
   disabled, supplies a minimal environment and separate empty working directory,
   and exchanges one command per response. The worker imports no evaluator. Pipe
   deadlines, input/output size bounds, response correlation and raw byte logs
   distinguish transport/protocol errors from semantic gate results.
2. **Persist observed dispatch metadata at quiescent boundaries.** Added an
   explicit create/resume wrapper with an independent POSIX ownership lock. An
   atomic, fsynced checkpoint holds observed requests, immutable historical
   receipts, attempt/event aliases, completed commands and their exact replies,
   bound to both journals' genesis, sequence and tail digests. Resume reopens the
   actual authority and executor without issuing executor I/O. Exact completed
   retries return the stored historical reply; changed commands cannot reuse an
   identity. In-session journal reopenings retain wrapper ownership.
3. **Define and test the interruption boundary.** A pending marker is published
   before any command effects, and a completed checkpoint precedes stdout. A
   worker killed after completed publication but before its reply can resume and
   return that reply without resending. Crashes before execution, after the remote
   effect or before completed publication leave an unresolved pending command and
   refuse automatic resume. Changed/missing journals, stale/corrupt checkpoints,
   changed initial data and storage failures also fail closed. This intentionally
   does not claim atomic transactions spanning both journals and wrapper state.
4. **Replay and retain independent process evidence.** Added 16 cases drawn from
   pinned existing development ancestry: four admission, four deployment and eight
   dispatch cases. Every one of their 186 completed prefixes matches the cold
   independent model. All 97 dispatch prefixes are followed by an actual process
   kill, new worker startup and exact retry, giving 113 worker starts overall.
   Evaluator files, scheduling choices and oracle state stay in the parent. Reports
   bind raw stdin/stdout/stderr, launch/exit evidence, recovered stores, source
   bundles, corpus ancestry and all exchange/recovery counts.

Verification: 709 default tests, 76 optional native tests and all 15 standalone
reference checks pass. The new 23 default tests include actual process crashes,
partial-output timeouts, malformed/oversized frames, JSON-null versus EOF,
checkpoint/journal mismatches, ownership after restart, event limits across
recovery, historical retries, source-bound reports and child environment/import
checks. Native admission/numerical/resource/dispatch projections remain identical
across a fresh worker's recovered reply retry. All eight prior corpus receipts are
refreshed; their existing expectations and reductions remain unchanged. Original
design inputs and authority/executor journal schemas remain unchanged.

The new wrapper supports fresh-process recovery only for completed dispatch
commands. Admission/deployment workers still create fresh stream sessions, and
concurrent schedules still belong to the earlier in-process controller. Separate
processes and runtime-only bundles are not an OS sandbox: workers retain the
account's filesystem/network capabilities. Checkpoint hashes detect corruption
and mismatched history, not hostile storage forgery. There are still zero
family-complete fixtures and no additional designated mutant witnesses.

Next increment, in order:

1. Extend quiescent worker checkpoint recovery to admission/deployment aliases,
   active contexts/rules, event budgets and their exact completed responses.
2. Specify an explicit reconciliation protocol for interrupted composite commands
   before allowing automatic forward progress from a pending marker. Preserve
   uncertain remote occupancy and immutable observed receipt history throughout.
3. Add bounded crash/recovery cases and independent raw process evidence for each
   supported boundary. Treat filesystem/capability isolation as a separate exit
   criterion, not as a consequence of process separation.
4. Continue phase 4 family coverage and the 64-fixture target. M09/M12, wider phase
   1/3 semantics and phases 5–8 pressure/attention/transport work remain pending.

### Nineteenth increment on 1 October 2026

Extended completed-command process recovery in four stages:

1. **Persist the remaining stream metadata.** Added a shared serial checkpoint
   transaction for the existing admission and deployment adapters, using
   `trace-worker-checkpoint/v1`. It binds the public initial state, profile and
   admission inference backend to the required journal tips. Admission stores
   ordered hard/numerical alias pairs, active contexts and current rule revisions;
   both profiles retain event/step inventories, command prefixes and counters,
   certificates and exact historical replies. Alias order is significant when
   multiple public names refer to one belief, so it is explicitly preserved in
   arrays rather than relying on sorted JSON object keys.
2. **Restore actual journals and validate wrapper state.** Explicit resume requires
   the existing stores, checks both their integrity and checkpoint binding, and
   validates reply identities/digests, contiguous steps and the recovered stream
   inventory. Admission contexts/rules are checked against the authority; the
   recovered wrapper projection must equal its last completed projection. No
   public event is replayed. Journal replay retains deterministic formula checks
   while avoiding native inference and executor I/O. Completed retries preserve
   the original diagnostics and do not consume budget or alter counters. In-session
   restarts retain the wrapper ownership lock.
3. **Exercise the extended crash and rejection contract.** Added tests for alias
   ordering, changed rules, multiple contexts, goal/monitor/completion history,
   128-event budgets across recovery, exact rejected/historical replies and the
   four-context bound. Tests detect malformed metadata, missing/changed journals,
   incompatible profile/initial/backend data, storage failure and altered reply
   identities. Actual child crashes before execution, after a composite command,
   after a deployment effect and after completed publication distinguish pending
   refusal from safe exact-reply recovery. No pending-command repair is inferred
   from a completed command's idempotency behavior.
4. **Expand independent process conformance and native evidence.** The worker
   harness now accepts recovery schedules for every profile. The corpus contains
   all 16 existing admission and all eight deployment cases, plus eight dispatch
   delivery cases. It compares 127/137/97 prefixes respectively, kills and resumes
   after all 361, and checks all 361 exact retries across 393 process starts. All
   events and development ancestry are unchanged; recovery schedules remain in
   the evaluator. Native projections survive admission/deployment process retries,
   and real native PLN revision continues after restoring its bound backend and
   numerical aliases.

All 727 default tests, 78 optional native tests and 15 standalone reference checks
pass. Eighteen new default tests cover the wrapper/recovery boundaries, and the
expanded 32-case CLI report verifies raw process evidence and recovery counts.
The eight earlier corpus receipts are refreshed; their outcomes and reductions
are unchanged. The process corpus is intentionally expanded and now schedules
fresh-process recovery for all profiles. Original design inputs, authority and
executor journal schemas, and the existing dispatch checkpoint schema are
unchanged. There are still zero family-complete fixtures and no new designated
mutant witnesses.

The supported recovery transition is from a fully published checkpoint to a new
worker, with exact completed replies available for retry. A pending marker, journal
mismatch or corrupted metadata remains an explicit refusal. Existing pre-checkpoint
admission/deployment stream directories have no wrapper checkpoint and cannot be
silently upgraded or reconstructed by replaying public events.

Next increment, in order:

1. Add evidence-preserving inspection for interrupted worker commands: report the
   pending public command, saved versus current journal boundaries and actual
   authority/executor state without sending requests or rewriting checkpoints.
2. Define explicit reconciliation decisions for each supported interruption
   boundary before enabling forward progress. Partial admission, numerical,
   lifecycle and dispatch effects require different evidence; absence of a reply
   never proves absence of a remote effect.
3. Test actual process failures and raw inspection/reconciliation receipts against
   independent models. Keep operator decisions separate from automated recovery
   and retain conservative resource uncertainty until authoritative fencing or
   equivalent supported evidence permits release.
4. Continue phase 4 family coverage, evaluator OS isolation and the 64-fixture
   target. M09/M12, broader phase 1/3 semantics and phases 5–8 remain open.

### Twentieth increment on 1 October 2026

1. Capture stopped-worker evidence under the existing worker and journal locks.
   Read existing files without opening the source databases through SQLite; retain
   checkpoint, database and WAL bytes, and replay only disposable private copies.
2. Report checkpoint integrity, the pending public command, saved/current journal
   boundaries and verified prefix relationships. Expose actual recovered authority
   and executor records separately from checkpointed observations and replies.
3. Publish a reproducible inspection bundle and verify it from captured bytes.
   Exercise real process crashes, partial composite commands, remote effects,
   corruption, missing stores and ownership conflicts without issuing executor I/O.
4. Document the evidence and decision matrix, refresh source receipts and run the
   regression/native/reference suites. Inspection does not clear pending markers,
   replay public commands, release resources or authorize continuation; explicit
   reconciliation remains the next implementation boundary.

Implemented `worker-inspection/v1` with existing-file ownership locks, bounded
capture, source-byte/inventory checks and checked replay on disposable copies.
The output retains raw evidence separately from the derived report and receipt.
Offline verification recomputes the report without reopening the original stores.
No pending marker or other worker state is rewritten. Missing, corrupt, unbound
or divergent stores are reported explicitly while retaining available evidence.

Sixteen development crash probes exercise pending-before-execution,
after-composite execution and lost stdout after publication in every profile,
plus partial context/policy setup, numerical-report admission, hard-fact adoption,
operation selection, goal-sample registration and remote effects in both executor
profiles. Independent primitive expectations and public-prefix models check raw
child-process evidence. The verifier binds exact injected source bytes and launch
records, retains actual WAL evidence, and checks that inspection left source
bytes unchanged. Historical observed receipts remain separate from current remote
fences and effects; no inspection query is sent to the executor.

Sixteen new default tests cover capture/ownership, bounds, corruption, missing
stores, profile mismatch, prefix divergence, exact evidence preservation,
reproducibility, report tampering and actual crashes. A new native test compares
captured typed authority records with their original native projection. Existing
nine corpus receipts are refreshed without changing any public case, outcome,
schedule or reduced mutation witness. Original design inputs and authority,
executor, worker and checkpoint schemas remain unchanged. Family-complete fixture
count remains zero.

Verification: 743 default tests, 79 optional native integration tests and all
15 standalone reference checks pass. The fresh 16-probe CLI report and its raw
inspection receipts verify successfully; the full default suite also repeats the
32-case, 361-prefix completed-command process corpus. Existing mutation reductions
remain M05 12→5, M06 23→6, M07 2→2, M11 13→1, M08 5→1, M10 6→4,
cached-send-gate 9→8 and expire-uncertain 8→7.

Next increment, in order:

1. Define explicit reconciliation request/result records bound to the exact
   pending command and inspected authority/executor genesis/sequence/tail digests.
   Reject stale evidence before considering a decision; retain the original bundle.
2. Implement a narrowly specified per-profile reconciliation transition only
   where the required evidence and wrapper-state reconstruction are defined.
   Distinguish partial admission/numerical records, lifecycle/goal registration,
   lost transport observations and actual executor effects. Unchanged journal tips
   alone do not authorize clearing a pending marker or releasing occupancy.
3. Exercise each allowed and refused transition with actual crashes, independent
   state expectations and durable decision receipts before enabling continuation.
4. Continue phase 4 family coverage, evaluator OS isolation and the 64-fixture
   target. M09/M12, broader phase 1/3 semantics and phases 5–8 remain open.


### Twenty-first increment on 1 October 2026

1. Define explicit cancellation requests bound to the inspected pending command,
   checkpoint bytes, report digest and exact journal tips. Require unchanged
   captured evidence and validate the complete saved wrapper on private copies.
2. Support cancellation only for admission and local deployment events with no
   journal progress. Consume the event ID and stream budget with an explicit
   historical UNKNOWN reply. Preserve authority/executor state and existing
   uncertainty; refuse dispatch, executor I/O and partial composite progress.
3. Persist a prepared decision before publishing the replacement checkpoint.
   Gate worker startup while a reconciliation marker exists, durably record the
   result before clearing it, and make exact decision retries finish either side
   of publication. Preserve the original inspection and before/after checkpoints.
4. Exercise actual crashes at each publication boundary, stale/corrupt evidence,
   ownership conflicts, unchanged resource uncertainty, historical retries and
   fresh worker continuation. Refresh receipts, run all required suites, commit
   and push; wider per-profile reconciliation remains explicitly pending.


Implemented the four stages above with request/prepared/result schemas, an explicit
local-event whitelist and private-copy wrapper validation. Cancellation preserves
all authority/executor bytes and consumes one stream event with a historical
UNKNOWN reply. No public event or executor operation is replayed. Decision IDs
bind immutable prepared archives; same-request retries complete interrupted
publication or return their original result after later worker progress.

The existing inspector now captures reconciliation markers and shares its stopped-
worker ownership locks with the reconciler. All current durable profiles gate
startup while a marker exists, including after checkpoint publication and before
a result is durable. The original inspection and exact before/after checkpoints
remain available for offline reproduction. Direct journal changes during a
prepared decision leave the gate in place and refuse completion.

Eighteen new default tests and one native test cover evidence/identity binding,
full-wrapper validation, event budgets, no-I/O behavior, storage failure, preserved
remote uncertainty after expiry and subsequent native PLN inference. Twelve actual
process probes interrupt archive staging, prepared assets, marker publication,
checkpoint publication, result publication and stdout, then verify exact decision
retry and fresh-worker continuation against independent expectations. The nine
existing source receipts are refreshed; original design inputs and all earlier
cases, schedules, expected outcomes and mutation reductions remain unchanged.

Verification: 761 default tests, 80 optional native integration tests and all
15 standalone reference checks pass. The fresh 12-probe reconciliation CLI report
verifies exact decision retries and continued worker behavior; the full suite also
repeats the 16 inspection probes and the 32-case, 361-prefix public-worker corpus.
Existing reductions remain M05 12→5, M06 23→6, M07 2→2, M11 13→1,
M08 5→1, M10 6→4, cached-send-gate 9→8 and expire-uncertain 8→7.
There are still zero family-complete fixtures and no new designated mutants.

Next increment, in order:

1. Specify a bounded reconciliation transition for a concrete partial local
   composite command, using exact appended journal commands and saved counters to
   distinguish already persisted work from the remaining operation. Keep explicit
   decision/evidence binding and the durable publication gate.
2. Define additional admission/numerical/lifecycle/goal outcomes separately; do not
   generalize unchanged-journal cancellation into blind replay or discard.
3. Before adding dispatch/executor reconciliation, account for queued requests,
   lost observations, immutable older acknowledgements and authoritative fencing.
   Preserve unresolved occupancy until supported evidence permits its release.
4. Continue phase 4 family coverage, evaluator OS isolation and the 64-fixture
   target. M09/M12, broader phase 1/3 semantics and phases 5–8 remain open.


### Twenty-second increment on 1 October 2026

1. Define the admission context boundary precisely: one matching open_context
   entry after the saved wrapper tip, with arguments and idempotency key derived
   from the original pending command and saved global counter. Refuse all other
   progress, existing contexts, exhausted context/event bounds and stale evidence.
2. Reconstruct and validate the prior wrapper and completed candidate on private
   journals. Retain the exact missing probability-policy entry in a versioned
   prepared archive; preserve all existing aliases, rules and historical replies.
3. Publish the worker gate before a single FULL synchronous SQLite append under
   retained worker/journal ownership. Recognize either the inspected boundary or
   its exact completed suffix on retry. Publish the PASS checkpoint and result
   before clearing the gate, without copying a private database into the source.
4. Exercise refusal cases, crashes inside/beyond COMMIT, exact decision/event
   retries, native PLN continuation and independent process expectations. Refresh
   all nine corpus receipts and run the full default/native/reference suites
   before committing and pushing.

Implemented all four stages above. The new explicit complete_partial_context
action uses prepared v2 records, while cancellation
retains prepared v1. Request/result, worker and authority journal schemas remain
unchanged. The result binds the completed journal tip; it remains historical after
later events. Offline reproduction checks the exact missing entry as well as the
before/after checkpoint bytes. No public composite event or executor I/O executes.

Thirteen new unit tests exercise exact prefix/alias/counter preservation, refused
progress and limits, checkpoint storage failure, absent inspection during retry,
extra authority progress, missing committed work and retained ownership. Eight
new process probes extend the existing twelve cancellation probes to twenty,
including interruption before and after the SQLite COMMIT. Independent public
models verify the completed context and subsequent numerical admission. A native
integration check continues through real PLN revision after context completion.

Verification: 774 default tests, 81 optional native integration tests and all
15 standalone reference checks pass. The fresh 20-probe reconciliation report
verifies successfully, as does the new CLI request binding. The full suite also
repeats the 16 inspection probes and 32-case, 361-prefix public-worker corpus.
All nine corpus receipts are refreshed; original design inputs, prior case
schedules and expected outcomes remain unchanged. Existing reductions remain
M05 12→5, M06 23→6, M07 2→2, M11 13→1, M08 5→1, M10 6→4,
cached-send-gate 9→8 and expire-uncertain 8→7. There are still zero family-complete
fixtures and no new designated mutants.

Next increment, in order:

1. Define adoption of an entirely persisted local composite whose final wrapper
   checkpoint was lost, starting with the two-command admission context. Require
   exact command/key/result chains and reconstructed counters, rather than a
   blanket journal-advanced decision. Preserve immutable historical diagnostics.
2. Specify additional partial admission/numerical/lifecycle/goal transitions
   separately, with explicit alias, permit and revision reconstruction rules.
3. Before dispatch/executor reconciliation, account for queued requests, lost
   observations, immutable older acknowledgements and authoritative fencing;
   preserve unresolved occupancy until supported evidence permits release.
4. Continue phase 4 family coverage, evaluator OS isolation and the 64-fixture
   target. M09/M12, broader phase 1/3 semantics and phases 5–8 remain open.


### Twenty-third increment on 1 October 2026

1. Specify adoption only for a pending new admission context with exactly its two
   matching journal commands after the saved checkpoint boundary. Bind arguments,
   global counters, keys, results and the full chain to the inspected journal tip.
2. Validate the prior wrapper and reconstruct the completed candidate on private
   copies. Preserve historical replies and aliases; give the recovered event an
   explicit adoption diagnostic without fabricating its lost elapsed time.
3. Retain both entries in prepared v3 records and publish through the existing
   durable worker gate. Preserve all source journal bytes, append nothing and
   support exact decision retries before/after publication and later progress.
4. Add real publication crashes, refused-progress and archive/storage tests,
   independent continuation checks and native projection/PLN continuation. Refresh
   the nine receipts and run all suites before committing and pushing.

Implemented all four stages above. The new explicit adopt_persisted_context action validates both entries by reconstructing the known
primitive context commands on private journals. Publication opens no source
SQLite connection; unchanged database and sidecar bytes are required throughout.
Prepared v3 records retain the two entries and both checkpoints; request/result,
worker and journal schemas remain unchanged. Existing cancellation and partial
completion retain prepared v1/v2. The adopted reply consumes the original event ID
and stream slot, preserves every earlier completed reply, and records its decision
with elapsed_ns zero because the lost original timing cannot be recovered.

Twelve new unit tests cover full entry/counter/policy binding, previous reply and
alias preservation, event/context bounds, absent source I/O, extra progress,
archive corruption, large typed entries, publication failure and historical
retries. Six new actual process probes extend the reconciliation report to 26 cases. They begin with a
worker crash after both context commands and verify unchanged journal bytes,
exact decision/event retries and independent numerical continuation. An added
native test checks unchanged projections and real PLN revision after adoption.

Verification: 786 default tests, 82 optional native integration tests and all
15 standalone reference checks pass. The fresh 26-probe reconciliation report
and explicit adoption CLI request binding verify successfully. The full default
suite also repeats the 16 inspection probes and 32-case, 361-prefix public-worker
corpus. All nine source receipts are refreshed. Original design hashes, earlier
cases, schedules and expected outcomes remain unchanged. Existing reductions stay
M05 12→5, M06 23→6, M07 2→2, M11 13→1, M08 5→1, M10 6→4,
cached-send-gate 9→8 and expire-uncertain 8→7. There are still zero family-complete
fixtures and no new designated mutants.

Next increment, in order:

1. Define adoption for a fully persisted admission evidence event, reconstructing
   its exact evidence/transition/certificate/commit chain, final belief alias and
   global counter. Require independent crash evidence before enabling that case.
2. Specify partial numerical/lifecycle/goal transitions separately, including
   their alias, permit and revision reconstruction rules; do not generalize from
   context adoption to arbitrary advanced journals.
3. Before dispatch/executor reconciliation, account for queued requests, lost
   observations, immutable older acknowledgements and authoritative fencing;
   preserve unresolved occupancy until supported evidence permits release.
4. Continue phase 4 family coverage, evaluator OS isolation and the 64-fixture
   target. M09/M12, broader phase 1/3 semantics and phases 5–8 remain open.


### Twenty-fourth increment on 1 October 2026

1. Specify the successful hard-evidence boundary: exactly record, proposal,
   pre-certificate, post-certificate and commit entries after the saved wrapper
   tip. Bind the new report identity, arguments, five keys, counter and complete
   result chain. Refuse partial chains, failed outcomes and unrelated progress.
2. Validate the previous wrapper and reconstruct only those primitives on private
   journals. Restore the committed hard-belief alias and both certificates,
   preserve alias order and earlier replies, and validate the completed candidate
   through ordinary resume and exact retry. Preserve current validity checks
   independently of historical PASS diagnostics.
3. Retain the five exact entries in prepared v4 records and publish through the
   existing durable worker gate. Preserve every source journal byte, issue no
   source SQLite/native/executor I/O, and support explicit retries after storage
   failures, unavailable inspection paths and later worker progress.
4. Inject real worker crashes before alias assignment and before final checkpoint
   publication, then exercise six reconciliation publication cuts for each.
   Check independent projections and alias-based continuation, add native graph
   and PLN continuation, refresh all nine corpus receipts, and run every suite
   before committing and pushing.

The new explicit `adopt_persisted_evidence` action implements the bounded
transition above. A pure grounded proposal is reconstructed locally between
pre- and post-certification; no public composite event or native inference engine
executes during adoption. Both certificates and the commit must pass, and the
commit must name the recovered belief. The saved counter advances by five and
the original event consumes one stream slot. Its new historical PASS reply
identifies the decision and records elapsed_ns zero for unavailable original
timing. Prior completed replies, alias order and numerical state are preserved.

Prepared v4 records retain all five entries and before/after checkpoint bytes;
request/result, worker and journal schemas remain unchanged. Existing actions
retain prepared v1/v2/v3. Preparation and offline audit reconstruct the same
candidate; exact journal bytes remain required for unfinished adoption. Later
expiry leaves the historical reply unchanged but causes a new derivation to
return STALE.

Twelve new unit tests cover every primitive key, payload/counter identity,
refused partial/extra/failed chains, exact alias/certificate/history restoration,
budgets, storage failures, tampered archives, changed authority and no source I/O.
Two new inspection cases bring that report to 18 cases. Twelve new reconciliation
probes bring its v4 report to 38 cases and verify derivation through the restored
alias against the independent public model. One new native test checks unchanged
AtomSpace projection and continued real PLN revision.

Verification: 798 default tests, 83 optional native integration tests and all
15 standalone reference checks pass. The fresh 18-probe inspection report and
38-probe reconciliation report verify against final sources; explicit evidence
adoption CLI request binding also passes. The full default suite repeats both
probe sets and the 32-case, 361-prefix public-worker corpus. All nine source
receipts are refreshed. Original design hashes, earlier cases, schedules and
expected outcomes remain unchanged. Existing reductions stay M05 12→5,
M06 23→6, M07 2→2, M11 13→1, M08 5→1, M10 6→4,
cached-send-gate 9→8 and expire-uncertain 8→7. There are still zero family-complete
fixtures and no new designated mutants. All four stages above are complete.

Next increment, in order:

1. Define adoption of a fully persisted numerical estimate with its exact six
   report/proposal/certificate/commit entries, restored numerical alias and saved
   counters. Specify deterministic adapter/revision reconstruction and failed
   outcomes before enabling that action.
2. Specify other hard-admission, partial numerical, lifecycle and goal outcomes
   separately, including their alias, permit and revision reconstruction rules.
3. Before dispatch/executor reconciliation, account for queued requests, lost
   observations, immutable older acknowledgements and authoritative fencing;
   preserve unresolved occupancy until supported evidence permits release.
4. Continue phase 4 family coverage, evaluator OS isolation and the 64-fixture
   target. M09/M12, broader phase 1/3 semantics and phases 5–8 remain open.


### Twenty-fifth increment on 1 October 2026

1. Define successful observation-estimate adoption around exactly six persisted
   evidence/report/proposal/certificate/commit entries. Bind the original report
   identity, finite truth values, source lineage, policy/revision state, six saved
   counter keys and complete result chain. Refuse other numerical operations,
   partial progress, failed certificates and unsuccessful commits.
2. Reconstruct those primitives only on private journals, validating the prior
   wrapper and completed candidate through ordinary resume. Observation proposal
   construction needs no native inference. Restore the exact numerical alias and
   both historical certificates, preserving prior ordered aliases and replies;
   keep numerical truth separate from hard assertions and current validity.
3. Retain six exact entries in prepared v5 and publish through the existing
   durable worker gate, with unchanged source journal bytes and no source SQLite,
   public composite, native inference or executor I/O. Preserve exact decision
   retries through interrupted publication and after later progress.
4. Inject process crashes before numerical alias assignment and before final
   checkpoint publication. Cross both with the six publication cuts; independently
   check model registration and numerical revision through the recovered alias.
   Add exact-value, failure, expiry/revocation and native projection checks,
   refresh all nine receipts, then run every suite before committing and pushing.

The explicit `adopt_persisted_estimate` action implements the six-entry observation
transition. Both probability certificates and the numerical commit must pass.
The candidate restores the numerical alias, advances the counter by six, consumes
one stream slot and publishes a historical PASS reply identifying the decision;
elapsed_ns remains zero for unavailable original timing. Exact signed zero and
zero-confidence estimates are preserved without creating a hard assertion.

Prepared v5 retains all six entries and before/after checkpoint bytes. Existing
actions retain prepared v1 through v4; request/result, worker and journal schemas
remain unchanged. Earlier replies keep their historical certificates; existing
hard/numerical alias order and the configured backend are retained. The recovered
event records its own two original certificates. Expiry and revocation still
prevent a new revision using retired numerical support, while exact old replies
remain historical.

Fourteen new unit tests cover every command key, exact report values, partial and
extra progress, failed post-certification, stale/history-limit commits, budgets,
ordered history, source changes, publication failures, archive integrity and
absent source/native/executor I/O. Two new inspection cases bring that report to
20 cases. Twelve new reconciliation probes bring its v5 report to 50 cases and
verify independence registration followed by numerical revision against the
independent public model. One new native integration test checks the numerical
AtomSpace graph and subsequent real PLN revision.

Verification: 812 default tests, 84 optional native integration tests and all
15 standalone reference checks pass. The fresh 20-probe inspection report and
50-probe reconciliation report verify against final sources, as does explicit
estimate-adoption CLI request binding. The full default suite repeats both probe
sets and the 32-case, 361-prefix public-worker corpus. All nine source receipts
are refreshed. Original design hashes, earlier cases, schedules and expected
outcomes remain unchanged. Existing reductions stay M05 12→5, M06 23→6,
M07 2→2, M11 13→1, M08 5→1, M10 6→4, cached-send-gate 9→8 and
expire-uncertain 8→7. There are still zero family-complete fixtures and no new
designated mutants. All four stages above are complete.

Next increment, in order:

1. Define adoption of a fully persisted numerical revision with exactly its four
   proposal/certificate/commit entries. Bind both prior numerical aliases, the
   registered independence declaration, formula identity/result, policy revisions
   and saved counters. Reconstruct its deterministic proposal without native I/O
   and retain explicit refusal of failed or partial outcomes.
2. Specify other hard-admission, partial numerical, lifecycle and goal outcomes
   separately, including their alias, permit and revision reconstruction rules.
3. Before dispatch/executor reconciliation, account for queued requests, lost
   observations, immutable older acknowledgements and authoritative fencing;
   preserve unresolved occupancy until supported evidence permits release.
4. Continue phase 4 family coverage, evaluator OS isolation and the 64-fixture
   target. M09/M12, broader phase 1/3 semantics and phases 5–8 remain open.


### Twenty-sixth increment on 1 October 2026

1. Specify adoption of successful numerical revisions only: four exact
   proposal/certificate/commit entries after the saved tip. Require two saved
   aliases for distinct numerical beliefs and the active independence declaration
   binding that pair. Bind event identity, four counter keys and complete journal
   results; distinguish new-belief and idempotent commit outcomes.
2. Validate the prior wrapper and reconstruct the four primitives on private
   journals. Use the pinned binary64 formula runtime explicitly, even for native
   workers. Verify exact formula/value/provenance/permit bindings and restore the
   commit's belief alias plus the event's historical certificates. Preserve prior
   alias order and replies without fabricating new weight or authority revisions.
3. Retain four entries in prepared v6 and publish through the existing durable
   worker gate. Preserve source journal bytes, avoid source SQLite/native/executor
   I/O and public composite replay, and retain exact retries after interrupted
   publication, absent inspection paths and later worker progress.
4. Cross new-belief/idempotent outcomes with both source crash cuts and six
   publication cuts. Check independent three-event continuation through the
   restored alias, altered formula/results, later report/model retirement and
   actual native graph parity. Refresh all nine receipts and run every suite
   before committing and pushing.

The explicit `adopt_persisted_revision` action implements this bounded transition.
Both numerical certificates and the commit must pass. The reconciler explicitly
uses PLNAdapter(PinnedFormulaRuntime()) for proposal reconstruction; no native
inference engine runs during adoption. The restored checkpoint consumes one
stream slot and four keys and records the recovered event's original two
certificates, decision binding and zero elapsed_ns for unavailable original timing.

A commit may have returned an existing numerical belief. Its canonical alias,
original belief certificates and authority revision remain unchanged; only the
new alias and event diagnostics are restored. New-belief commits retain their
original exact belief identity. Earlier replies and ordered aliases survive both
cases. Later leaf expiry, report revocation or independence-model revocation still
blocks a new revision using retired support, while exact old replies stay historical.

Prepared v6 retains four entries and both checkpoints. Earlier actions keep
prepared v1–v5, and request/result, worker and journal schemas are unchanged.
Publication preserves exact database/sidecar bytes; offline verification rebuilds
the pinned proposal and complete candidate from the original inspection.

Fourteen new unit tests cover all four keys, saved premise/model bindings,
altered formula/truth/assumptions/provenance, failed and history-limit outcomes,
partial/extra chains, idempotent aliases, budgets, archive/storage failures,
source changes, absent I/O and later dependency retirement. Four inspection cases
bring that report to 24 cases. Twenty-four reconciliation probes bring v6 to 74
cases; continuation admits a fresh report, registers independence with the
recovered alias, and revises again against the independent public model. One new
native integration test covers both commit outcomes, denies native inference
during recovery, compares numerical AtomSpace graphs, and resumes native revision.

Verification: 826 default tests, 85 optional native integration tests and all
15 standalone reference checks pass. The fresh 24-probe inspection report and
74-probe reconciliation report verify against final sources, as does explicit
revision-adoption CLI request binding. The full default suite repeats both probe
sets and the 32-case, 361-prefix public-worker corpus. All nine source receipts
are refreshed. Original design hashes, earlier cases, schedules and expected
outcomes remain unchanged. Existing reductions stay M05 12→5, M06 23→6,
M07 2→2, M11 13→1, M08 5→1, M10 6→4, cached-send-gate 9→8 and
expire-uncertain 8→7. There are still zero family-complete fixtures and no new
designated mutants. All four stages above are complete.

Next increment, in order:

1. Deferred by the twenty-seventh increment: adoption of fully persisted hard
   derivations with their exact four transition/certificate/commit entries.
   Bind saved hard aliases and the rule
   revision, reconstruct the grounded proposal and handle both new and idempotent
   belief commits without source writes or changes to historical replies.
2. Specify other hard-admission, partial numerical, lifecycle and goal outcomes
   separately, including their alias, permit and revision reconstruction rules.
3. Before dispatch/executor reconciliation, account for queued requests, lost
   observations, immutable older acknowledgements and authoritative fencing;
   preserve unresolved occupancy until supported evidence permits release.
4. Continue phase 4 family coverage, evaluator OS isolation and the 64-fixture
   target. M09/M12, broader phase 1/3 semantics and phases 5–8 remain open.


### Twenty-seventh increment: bounded B0-versus-B3 comparison

The user's priority change supersedes further recovery expansion. The immediate
four-step milestone near the top of this plan is implemented as a bounded subset;
existing unsupported interrupted cases remain explicitly blocked.

1. Added `reachability.pressure`, a deterministic derived view with canonical
   context/source/slice identities and separate outstanding, predicted-covered,
   open and observed-relief records. Exact unit conversion and versioned bounded
   priority factors precede normalized AND/OR propagation. The fixed binary64
   routing columns are substochastic; contraction iteration reports residuals,
   error/norm bounds, convergence, SCCs, stranded reasons and exhausted limits.
   Supported channels are inference and observation only. Covered work retains
   monitoring pressure. No pressure API receives an authority or executor handle.
2. Reused the existing public Candidate/Frontier records for both reasoning
   controllers. Shared discovery binds complete current premise bundles and
   performs the same pure early joint checks. B0 recomputes competent best-first
   conditional plans, including shared prerequisites and exact public constraints.
   B3 schedules typed pressure per declared work using a heap. The existing
   deployment B0 is unchanged. Every actual result uses the existing certified
   admission APIs and authoritative goal sample/accounting operations.
3. Added 25 focused tests, including independent exact rational linear solutions,
   unchanged reads, duplicate paths, cycles, AND/OR semantics, blocked demand,
   coverage expiry, relevant revisions, unit conversion, all declared bounds,
   immutable numerical truth, invalid/stale gate rejection and journal replay.
   The actual M09 source-injection mutation is detected on an unchanged snapshot.
   M12 is deferred with transport, not a blocker for this milestone.
4. Added one command, documented in `PRESSURE_COMPARISON.md`, that writes real
   authority journals, JSONL traces, source/configuration bindings, selected
   operations, losses, failures and a readable comparison. Two fixed development
   seeds, two episodes and four common budget configurations produce 32 runs.
   Identical-snapshot ranking diagnostics and per-record frontier audits isolate
   ranking from candidate generation. Both variants use a common sixteen-tick
   evaluation horizon, including exogenous changes after budget stops without
   free work. Costs include discovery, pressure, inference, certification,
   persistence, elapsed/CPU time, setup and evaluation; unmeasured categories are
   explicit. No training, retuning or performance advantage is claimed.

The rich episode has alternative inference routes, a missing observation, a
shared prerequisite, and a seed-support revocation between read and execution.
Both controllers complete under the sixteen-request cap, while the eight-request
cap exposes incomplete results. B3 leaves less final loss at the smaller cap but
has worse integrated loss at the larger cap: 78 versus B0's 72, for both seeds.
The simple control has the same two operations and integrated loss 1. Pressure
construction and iteration add measurable overhead. These neutral and negative
results are retained without changing the comparator or episode to force a win.

Verification: the full default suite passes 851 tests; the native integration
suite passes 85, and all 15 standalone reference checks pass. After the final
bounded-route diagnostic correction, all 25 affected pressure/comparison tests
pass again, including cost-sensitive B0 ranking. No tests were skipped and no
failures remain. The full suite retains the deployment regressions, 24 inspection
probes, 74 reconciliation probes and 361 public-worker recovery prefixes.

The final isolated comparison passes 32 runs (16 pairs), audits 155 recorded
candidate frontiers and records four identical-snapshot ranking comparisons.
M09 is detected and all recorded pressure solves converge. Expected operations
include three unavailable-observation UNKNOWN replies and twelve STALE replies;
these are retained, not relabeled as success. Atomic operations may finish beyond
a wall cap; the maximum observed overrun is 71.49 ms and every run reports its
actual elapsed time. All nine existing receipts match final sources. Earlier
fixtures, expected outcomes, reduction results and original design hashes remain
unchanged. There are still zero family-complete fixtures.

Results and complete cost categories are in
`artifacts/pressure-comparison/comparison.md` and `report.json`; the command and
bounded scope are documented in `PRESSURE_COMPARISON.md`. All four immediate
milestone steps are complete.

Stop at this milestone after final verification. Adaptive activation transport,
learned conductance, generalized recovery, broader channels, numerical PLN
scheduling, evaluator OS isolation, the 64-fixture target and large-scale claims
remain deferred. This subset does not complete the full pressure/attention/
transport/benchmark design or the broader phases 5–8.


### Twenty-eighth increment: saved comparison audit

The follow-up is bounded to verification of the completed comparison. The frozen
episodes, both controllers, authority and recovery contracts remain unchanged.

1. Bind the required configuration, report, ranking, trace and journal artifacts
   with a complete digest inventory; check source inputs before and after a run.
2. Add an offline command that verifies the full paired matrix, recorded rankings
   and budgets, replays saved requests in fresh temporary authorities, and checks
   copied journals. Account for audit time separately from controller timings.
3. Add corruption witnesses for missing artifacts, changed rankings, receipts,
   outcomes, budgets and provenance, including mutations after resealing.
4. Run the comparison and applicable regressions, record results and limitations,
   then commit and push. Stop here; deferred transport/recovery work stays deferred.

Status: complete. The comparison now seals all required artifacts and automatically
runs the audit. An offline command checks the exact source and configuration,
full paired matrix, frontiers, ranks, pressure, work and stop accounting. Recorded
requests reproduce through fresh certified authorities; copied original journals
verify belief history, current support, receipt references and exact goal-event
prefixes. Uncheckpointed journals fail closed. Audit elapsed time is reported
separately and never charged to either controller. Hashes are consistency evidence,
not publisher authentication; historical wall-clock measurements are not replayed.

Verification: 16 new audit tests pass, including resealed corruption witnesses.
The focused pressure/comparison/audit/manifest suite passes 43 tests; the existing
B0, deployment-trace, admission-trace and recovery suites pass 70 tests; all 15
standalone reference checks pass. There are no remaining failures or skipped
tests in these runs. The full default and native integration suites were not
rerun for this evaluator-only increment; their prior results remain recorded
above. All nine existing corpus receipts still match, with no regeneration or
fixture changes needed.

The new comparison passes 32/32 runs and independently replays 159 recorded
selections, verifies 71 source files and detects M09. Audit elapsed time is
19.88 seconds. Work-limited results remain unchanged, including B3's worse
integrated loss of 78 versus B0's 72 at the sixteen-request budget and the
identical simple control. Wall-limited results retain their measured host-load
dependence. Results are in `artifacts/pressure-comparison-audited/`, with commands
and limitations in `PRESSURE_COMPARISON.md`.

This follow-up ends at saved-result verification. It does not change controllers,
episodes, admission, recovery or the deferred capability list.

### Twenty-ninth increment: fresh-run comparison repeatability

1. Add a bounded evaluator command that runs the frozen matrix twice in separate
   processes and fresh authority directories, then audits both evidence bundles.
2. Compare work-limited selections, snapshots, pressure/ranks, work counts,
   rejections, outcome histories and stop reasons. Normalize only measured times
   and opaque authority identifiers already checked by each bundle audit.
3. Report wall-limited differences without treating them as deterministic failures.
   A wall cap reached in a work-limited configuration makes that comparison
   inconclusive. Reject reused authorities and source/configuration mismatches.
4. Add positive and corruption checks, run the repeated matrix and applicable
   regressions, record the evidence, then commit and push.

Status: complete. `validation_lab.repeat_pressure_comparison` runs two fresh
comparison processes, audits both bundles and compares semantic results/traces.
It also accepts two existing bundles for a fresh audit and comparison. Reused
output directories, reused authorities, source/configuration mismatches and
changed artifacts are rejected. Measured durations remain visible but are not
required to match. Reaching a wall safety cap in a work-limited run is explicitly
inconclusive, with a distinct nonzero exit status. Failed children remain recorded
and receive no automatic retry. The checker records its own source hash separately
and supports commit verification alongside the 71 unchanged comparison inputs.

Verification: 14 new repeatability tests, 43 existing pressure/comparison/audit/
manifest tests and all 15 standalone reference checks pass. No failures remain
and none of these tests were skipped. The full default, native integration and
unrelated deployment/recovery suites were not rerun for this evaluator-only
extension. The runtime controllers, authority, existing auditor, frozen episodes
and all nine source/corpus receipts remain unchanged.

The full experiment passes 64 controller runs, with 64 distinct authorities and
154 audited selections in each bundle. All sixteen work-limited repeat comparisons
match, with no failures or inconclusive cases. Three of sixteen wall-limited
comparisons retain semantic variation; these are reported rather than erased.
Both bundles detect M09 and all recorded pressure fields converge. Work-limited
results preserve the prior neutral/negative outcomes: rich-episode integrated
loss is 78 for B3 versus 72 for B0 at sixteen requests, and the simple control is
identical. Total experiment elapsed time is 114.76 seconds, including a separately
recorded 38.30-second final verification phase; neither is charged to controllers.

Results are in `artifacts/pressure-repeatability/repeatability.json` and
`repeatability.md`; `PRESSURE_COMPARISON.md` documents fresh-run and saved-bundle
commands. This is development repeatability evidence, not a statistical or
scaling claim. Stop here. Transport/M12, learned conductance, generalized recovery
and the broader benchmark remain deferred.

### Thirtieth increment: exact stored pressure routing bounds

The rounded `fsum` guard can miss a positive exact column excess: five binary64
`0.2` shares exceed one by `1/18014398509481984` even though `fsum` returns one.
Extreme positive dependency weights can also normalize to zero, silently dropping
a missing prerequisite from propagation. Correct these two bounded numerical
defects without expanding the implemented channels or changing authority.

1. Compute the exact sum of stored binary64 shares using integer ratios; when
   necessary, round the largest share downward to the remaining column capacity.
   Reject an unrepresentable positive share and version the routing algorithm in
   the pressure epoch.
2. Add independent exact-rational witnesses, including equal-weight columns,
   extreme ranges, subnormals, cycles and deterministic input permutations.
3. Refresh all nine corpus/source receipts, preserve fixture semantics, run
   applicable regressions and the frozen B0/B3 repeatability experiment. Record
   measured overhead and neutral/negative outcomes, then commit and push.

Status: complete. The normalizer uses exact integer ratios of the stored shares
and downward rounding only when the column exceeds one. It rejects positive
shares that underflow to zero, while retaining representable subnormal cases.
`binary64-substochastic/v2` is recorded and binds the pressure epoch. No authority
API, candidate generator, controller policy or frozen episode was changed.

Verification: all 61 pressure/comparison/audit/repeatability/manifest tests pass,
as do 70 B0/deployment/admission/recovery regressions and all 15 standalone
reference checks. Four new tests include the former rounded-sum counterexample,
90 equal/random/extreme-weight configurations, underflow rejection without input
mutation, cyclic reference solutions and routing-revision binding. No tests were
skipped and no failures remain. Full default and native integration suites were
not rerun for this isolated pressure calculation correction.

All nine corpus receipts were refreshed and all nine corpus verifiers pass.
Fixture semantics, expected outcomes, shrink reductions and design hashes remain
unchanged. The fresh experiment passes 64 controller runs over 64 distinct
authorities, with 148 and 156 audited selections. All sixteen work-limited repeat
comparisons match; seven wall-limited comparisons retain their measured variation.
Exact rational checks of all 183 recorded pressure fields confirm positive
stored routing shares and column sums at most one. Both bundles detect M09 and
all fields converge. The prior work-limited outcomes remain unchanged: rich B3
integrated loss is 78 versus B0's 72 at sixteen requests; the simple control is
neutral. B3 pressure construction/solve time in those rich work-16 runs spans
17.73–33.60 ms, including normalization; no performance improvement is claimed.

Results are in `artifacts/pressure-routing-repeatability/repeatability.json` and
`repeatability.md`. This closes the bounded numerical correction. Transport/M12,
learned conductance, generalized recovery and the broader benchmark remain deferred.

### Thirty-first increment: exact support lifetime ordering in shared candidates

The common frontier treats a support with no scheduled expiry as time 1,000,000.
A later finite expiry can therefore displace it and unnecessarily invalidate a
derived result. Correct this ordering equally for B0 and B3 without changing the
frozen episodes, ranking policies, authority or recovery contracts.

1. Order support by absence of expiry, then exact descending integer expiry and
   deterministic public alias. Preserve each whole AND premise bundle.
2. Check large integer times, equal-expiry permutations and identical controller
   frontiers. Use actual certified inference to check competing support expiry,
   revocation, stale binding/certificate rejection and finite-support fallback.
3. Refresh all nine source receipts without changing fixtures, run applicable
   regressions and the frozen repeatability experiment, then record and commit
   the results. Stop within the completed comparison subset.

Status: complete. The common candidate generator now gives support without a
scheduled expiry precedence over every finite logical time. Finite timestamps
retain exact integer ordering; equal lifetimes use the same public alias
tie-breaker for both controllers. Whole AND bundles and all existing authority
checks remain intact. No ranking policy or frozen episode was changed.

Verification: all 67 pressure/comparison/audit/repeatability/manifest tests pass,
including six new support-selection tests. The 70 B0/deployment/admission/recovery
regressions and all 15 standalone reference checks also pass. Five of the new
tests reproduced the original defect before the correction. Actual certified
inference verifies that an unused competing support's expiry does not invalidate
the selected proof, while revocation still rejects stale requests/certificates.
A fresh request can use the remaining finite support and remains subject to its
expiry. No failures remain and no tests were skipped in these runs. Full default
and native integration suites were not rerun for this isolated frontier correction.

All nine corpus receipts were refreshed and their verifiers pass. Fixture
semantics, expected outcomes, shrink reductions and pinned design hashes are
unchanged. The fresh experiment passes 64 controller runs over 64 distinct
authorities, with 159 and 156 audited selections. All sixteen work-limited repeat
comparisons match, with no failures or inconclusive cases; five wall-limited
comparisons retain measured variation. Both bundles detect M09 and all 189
recorded pressure fields converge. Seven UNKNOWN and 24 STALE operation replies
remain visible as expected rejections, with no harness failures.

Work-limited outcomes are unchanged: rich work-16 integrated loss remains 78 for
B3 versus 72 for B0; the simple control is neutral. B3 pressure construction/solve
time in those rich runs spans 14.78–21.49 ms. Complete discovery, ranking,
inference, certification, persistence and elapsed costs remain in the reports;
no performance improvement is claimed. Results are in
`artifacts/pressure-support-repeatability/repeatability.json` and
`repeatability.md`. This closes the bounded support-selection correction.
Transport/M12, learned conductance, generalized recovery and the broader benchmark
remain deferred.

### Thirty-second increment: consistent integer operation-work contracts

The public profile accepts fractional rule/probe costs, but saved-result auditing
requires integer work counts. Both controllers can therefore finish an accepted
profile that its auditor rejects. Align the input boundary with the bounded
integer work contract without changing the frozen episodes or comparison budgets.

1. Require exact integers from 1 through 100 for rule and probe costs. Reject
   floats, booleans, nonfinite values and out-of-range integers before authority
   creation; do not round, clamp or reinterpret unsupported costs.
2. Test both controller entry points, valid endpoint costs, exact operation and
   observation budget boundaries, actual certified execution and saved-run audit.
   Include observation and monitoring charges as well as inference work.
3. Refresh source receipts without changing corpus fixtures, run applicable
   regressions and the frozen repeatability experiment, record the results, then
   commit and push. Keep broader pressure/transport/recovery work deferred.

Status: complete. Rule and probe costs now require exact integers from 1 through
100 work units, shared by B0 and B3. Unsupported values fail before opening an
authority session, without rounding or clamping. Float-valued costs such as
`1.0` are also rejected, matching the existing integer audit contract. Monitor
charges remain one operation and one observation unit. Frozen episodes, budgets,
rankings and authority/recovery behavior are unchanged.

Verification: all 71 pressure/comparison/audit/repeatability/manifest tests, 70
B0/deployment/admission/recovery regressions and 15 standalone reference checks
pass. Four new tests cover invalid costs, absence of authority creation, eight
certified and audited runs at the valid cost boundaries, and five budget-stop
cases per controller. Stops preserve unresolved demand when a probe, inference
or monitor cannot fit its budget. No failures remain and no tests were skipped
in these runs. Full default and native integration suites were not rerun for
this isolated input-contract correction.

All nine refreshed corpus receipts verify. Fixture semantics, expected outcomes,
shrink reductions and pinned design hashes remain unchanged. The fresh experiment
passes 64 controller runs over 64 distinct authorities, with 148 and 153 audited
selections. All sixteen work-limited repeats match, with no failures or
inconclusive cases; eight wall-limited comparisons retain measured variation.
Both bundles detect M09 and all 181 recorded pressure fields converge. Six UNKNOWN
and 24 STALE operation replies remain visible, with no harness failures.

Rich work-16 integrated loss remains 78 for B3 versus 72 for B0, and the simple
control remains neutral. B3 pressure construction/solve time in those rich runs
spans 15.24–30.95 ms. Total experiment time is 122.11 seconds, including a separately
recorded 38.60-second final verification phase. Complete cost categories remain
in the reports; no performance improvement is claimed. Results are in
`artifacts/pressure-cost-repeatability/repeatability.json` and `repeatability.md`.
This closes the bounded cost-contract correction. Transport/M12, learned
conductance, generalized recovery and the broader benchmark remain deferred.
