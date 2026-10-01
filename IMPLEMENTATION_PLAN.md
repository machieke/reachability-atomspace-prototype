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
