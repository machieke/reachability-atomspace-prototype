# Reachability AtomSpace prototype

This repository implements the reachability proposals in stages. The current
increment combines a single-authority admission service, grounded lifecycle
schemas, passive operation ledgers, atomic resource/intent coordination and a
durable simulated dispatcher. Admission can run in memory; dispatch requires
SQLite recovery. It separates
stored reports, proposals, accepted hard claims, lifecycle history and current
validity, and checks the complete relevant constraint set before acceptance.

Read [the phased implementation plan](IMPLEMENTATION_PLAN.md) for deliverables,
dependencies and exit criteria. The original specifications and validation design
remain the design inputs. [The implementation manifest](implementation_manifest.json)
records their hashes and the capabilities actually implemented.

## Run the prototype

The development interpreter is Python 3.11.14. There are no third-party runtime or
test dependencies. From the repository root, use an existing Python 3.11 or later,
or the pinned interpreter through `uv`:

```bash
uv run --no-project python -m reachability.demo
uv run --no-project python -m reachability.recovery_demo
uv run --no-project python -m reachability.lifecycle_demo
uv run --no-project python -m reachability.execution_demo
uv run --no-project python -m reachability.dispatch_demo
uv run --no-project python -m unittest discover -s tests -v
uv run --no-project python pressure_field_lifecycle_reference_checks.py
```

For an editable package installation, run `uv sync --frozen`. The lock file has
no third-party runtime dependencies; the package build uses pinned setuptools.

With a suitable Python already active, the equivalent commands begin with
`python` instead of `uv run --no-project python`. The last command runs the
original standalone numerical checks. Those checks do not establish pressure or
transport integration with the admission service.

The demonstration reports these outcomes:

| Operation | Result |
| --- | --- |
| Infer with one missing mandatory premise | UNKNOWN |
| Infer after both exact premises are accepted | PASS |
| Accept a contradictory conclusion | FAIL |
| Commit using permits issued before support revocation | STALE |
| Query the dependent conclusion after revocation | STALE, with history retained |

## Implemented semantics

- Grounded predicate applications have deterministic structural identities;
  argument order matters. Context is separate from statement identity.
- Immutable evidence records retain source, logical observation time and lineage
  roots. Duplicate IDs are idempotent; conflicting reuse is rejected. Recording
  opposing reports alone creates no accepted claims.
- A caller must explicitly propose adoption of a report under the **hard-claim
  interpretation**. This is a finite conformance model, not calibrated empirical
  belief or a PLN strength/confidence formula.
- Registered grounded rules require their complete ordered premise revisions in
  one context. Replacing a rule retires its old derivations and their descendants;
  inference itself has no side effects.
- Context constraints use conjunctive normal form: a tuple of disjunctive clauses.
  A clause may be empty (false); an empty constraint collection is true. Assumptions
  are additional hard literals. Every check considers all active claims.
- The complete checker uses unit propagation and branching, with a default limit
  of 16 variables and a configurable maximum of 20. Exceeding the limit returns
  UNKNOWN; it never certifies a truncated constraint set.
- Precertification binds inputs; pure inference builds a proposal; postcertification
  replays the proposal and checks the proposed state. Only fresh, service-issued
  PASS records permit a commit.
- Every public mutation has an idempotency key. One lock covers revision comparison
  and publication. Two commits from the same old revision cannot both succeed.
- Revoking evidence invalidates all dependent revisions before publishing the new
  context revision. Independent alternative supports remain usable. Historical
  certificates and beliefs remain records of earlier checks.
- Evidence has an optional exclusive `valid_until` tick. The context clock is
  explicit and monotone. Future observations cannot support current claims, and
  expired evidence cannot support pending commits or current dependent beliefs.
- Policy updates recheck the complete scope and invalidate pending permits.
  Individually incompatible claims and their descendants become stale. If the
  remaining claims are jointly inconsistent, this first policy updater retires
  that remaining set conservatively; it does not choose an arbitrary surviving
  world. Claims may then be explicitly re-admitted under the new contract.

`Certificate.status` describes its recorded check results; it is not a current
authorization query. The service checks registry integrity, subject, stage, scope
and revision every time a permit is used. `query_belief` checks the current joint
state and returns its validation revision separately from historical certificates.

Idempotency replay returns the original operation response, including its original
revision. It does not assert that the response is still current; use `query_belief`
or a fresh snapshot for current state.

## Durable storage and recovery

Passing `database` enables a SQLite command journal; omitting it keeps the volatile
service useful for small conformance tests. Use a context manager to release the
single-authority lock:

```python
from reachability.service import AdmissionService

with AdmissionService(database="artifacts/admission.db") as service:
    service.open_context("plant-A", idempotency_key="create-plant-A")

with AdmissionService(database="artifacts/admission.db") as recovered:
    print(recovered.snapshot("plant-A"))
```

The journal stores typed command inputs and result digests in atomic transactions.
Accepted revisions, their certificate records and idempotency responses are
reconstructed together by replaying those commands through the checks. Recovery
rejects mismatched results, unknown schemas and corrupted event chains. Initial
rules and checker capacity are recovered from the journal; explicitly supplied
initial configuration must match. Later rule replacements are replayed normally.

An exclusive POSIX file lock enforces one live authority for the database path.
SQLite uses WAL mode and full synchronous commits. The service holds its own lock
through durable commit before publishing a changed view. A storage failure closes
authorization until the caller closes and reopens the service, then reconciles
the original idempotency key. Executor simulation uses a separate durable journal;
neither journal's recovery sends requests to the other authority.

The hash chain detects corruption within the trusted database boundary; it is not
signed attestation or protection against a database administrator rewriting history.
The clock measures declared logical ticks, not elapsed wall time. A restarted
caller must advance it before performing work at a later logical time.

Recovery currently replays the complete history, and durable mutations copy working
state for rollback. These intentionally simple algorithms have unoptimized time
and memory costs. Schema migration and snapshot acceleration are future work.

## Lifecycle schemas and operation episodes

Schemas are immutable, explicitly registered revisions for a grounded entity. An
episode pins its schema revision. Registering a new revision cannot silently
reinterpret an existing episode or change an operation's expected product.

Requirements support `FACT`, `AND`, `OR` and an explicit `ALWAYS` predicate.
`FACT` requires an exact usable scoped belief revision; absent support is UNKNOWN,
not false. An OR selects one complete branch, recording its branch path and exact
witnesses. It cannot combine partial alternatives. Evaluation checks all current
hard constraints, and returns UNKNOWN beyond the supported operator or expression
limits (256 nodes, depth 32). Unsupported contracts cannot be registered as active
schemas. Every transition outcome must require evidence on every permitted branch.

`certify_lifecycle_transition` checks the source stage, current prerequisites,
observed outcome and target validity. Its permit binds the episode revision,
context revision, lifecycle revision, policy, schema and exact supports.
`advance_lifecycle` rechecks that binding and atomically records the historical
transition. A lifecycle change does not manufacture a new truth-bearing belief.

`inspect_lifecycle` reports historical stage and present validity separately.
Revoking an old credential need not invalidate a completed artifact whose current
validity depends on different evidence. Losing the artifact's own support makes
its validity stale while retaining the stage and events. A declared recovery or
regression edge can leave an invalid state, but still needs its own complete
requirements and observed outcome.

The operation ledger records stable operation/attempt identity, planning selection
and its time, and independent observed milestones. It is **passive**: selection
does not dispatch an action, reserve resources or authorize execution. Observations
require accepted direct evidence matching the exact attempt, product and milestone,
from a source ID allowed by the pinned schema. Evidence ingestion is still a trusted
in-process API; a real executor adapter must authenticate those sources.

ACK, completion and exact-product observation remain separate. An operation's
outcome passes only when its completion and product observations are current and
its declared outcome contract passes. Observations may arrive out of order; a late
completion after cancellation is retained. Revocation removes the observation's
current authority without deleting history. These records make no claim of causal
credit or goal relief.

In this fragment, lifecycle prerequisites and outcomes are checked at the same
current snapshot. Dispatch captures submission-time witnesses, but lifecycle
transitions do not yet consume temporal contracts spanning submission and completion.
Generic entity binding, schema migration, goal coverage and durability windows
remain pending. Stored journals from commits `3e2516e` and `9da7639` are tested for
recovery and extension with lifecycle and dispatch commands, respectively.

## Resource reservations and execution intents

`register_resource` declares immutable renewable capacity with an exact integer
quantity and unit. Resources belong to the single service authority and are shared
across belief contexts. `register_execution_contract` pins the lifecycle schema and
edge, executor identity, allowed owners, every required resource demand, additional
action requirements and local lease duration. Contract promotion is a trusted API;
it does not authenticate the caller or discover an operation's real-world needs.

`certify_execution` checks selection, current lifecycle readiness, the separate
action contract, ownership, resource capacity and snapshot revisions. Claims are
generated from the pinned contract so a reservation caller cannot omit a required
resource. The capacity checker sums the **whole portfolio** at every interval
boundary; pairwise feasibility alone is insufficient. Intervals are half-open
`[starts_at, ends_at)`, with no rounding or implicit unit conversion.

`reserve_and_record_intent` accepts only a fresh registered PASS certificate,
rechecks the contract, then records every reservation and the stable intent/attempt
identity in one mutation. With `database=...`, that mutation is one durable journal
transaction. Failure leaves all resources unclaimed. Competing certificates for a
last unit cannot both commit. Replaying the same key returns the original response;
use `inspect_execution_intent` for the present lease and readiness.

The monotone resource clock is explicit and authority-wide. Before certification
or current readiness can pass, the operation's context clock must equal it. Advance
both clocks to the declared current tick; a restarted authority has no wall-clock
freshness guarantee. Local leases start immediately and expire at the contract's
exclusive deadline. This increment does not book future steps, renew leases,
change capacities, allocate consumable inventory or call a real external service.

An undispatched intent can be cancelled by its recorded owner. Cancellation or
expiry releases local claims while retaining intent and reservation history. A
new attempt needs a new identity. Losing a prerequisite blocks current readiness
without silently deleting the lease or rewriting the earlier certificate.

If an executor observation is recorded for an intent, its resource view becomes
`reconciliation_required`, even after cancellation, expiry or later evidence
revocation. The same durable observation transaction invalidates resource permits
across contexts. All affected resources remain blocked until a supported executor
release contract is reconciled. An ACK, completion or cancellation
observation alone does not establish that remote occupancy ended. `used_now` counts
scheduled quantities inside their original intervals; it does **not** measure remote
occupancy or imply availability when `reconciliation_attempts` is nonempty.

Intent views do not carry reusable I/O authority: `execution_authorized` remains
false. The dispatcher performs its own current checks at the submission boundary.

## Simulated dispatch and resource reconciliation

`SimulatedExecutor` is an independent local authority with a second SQLite journal.
Its immutable profile declares executor identity, durable instance identity,
idempotency, authoritative query and permanent release capabilities.
`register_dispatch_policy` pins that profile to an execution contract. Replacing
an executor database produces a different instance identity and cannot silently
inherit a prepared attempt. The provided `NonIdempotentSimulatedExecutor` exposes
duplicate effects if called twice and, by default, cannot query or release them.

`Dispatcher.dispatch` requires a durable service, the recorded owner and the exact
pinned executor profile. It checks current prerequisites, policy, resource ownership,
clock alignment and the live lease. It then durably records `prepare_dispatch`
before calling the executor. The request contains the exact immutable intent,
product and reservations; retries retain its identity and payload. Readiness is
checked again before submission. The reference service lock spans these checks and
synchronous simulator I/O, so another worker cannot insert a revision in between.

The submission marker immediately protects capacity beyond local lease expiry.
A lost reply leaves the attempt uncertain; it does not establish that no effect
occurred. Reconciliation queries the same request. An idempotent executor may
receive that same request again only while current submission gates pass. A
non-idempotent executor is never automatically resubmitted after the marker exists,
even when a query says absent: an earlier request could still arrive later.

| Dispatch state | Meaning |
| --- | --- |
| `uncertain` | Submission may or may not have taken effect; affected resources stay blocked |
| `accepted` | An authoritative executor receipt records acceptance; resources stay held |
| `released` | The executor has released the request and permanently fenced future effects under its identity |

`Dispatcher.release` is the separate cleanup operation allowed by a pinned release
contract and the recorded owner. It remains available after action credentials
expire. The simulator durably installs a release tombstone even if the request has
not arrived; late submissions return that tombstone without creating an effect.
Local capacity becomes available only after the authority commits the matching
release receipt. A lost release reply is reconciled without assuming success.
Historical callbacks remain recordable after release and do not undo that permanent
fence. A passive observation with no bound dispatch request remains unresolved;
there is no automatic adoption of legacy external work into the simulator.

`inspect_dispatch` reports the authoritative submission receipts separately from
the operation's completion/product observations. Submission creates no accepted
belief, lifecycle transition, product evidence or goal relief. Release ends modeled
resource occupancy; it does not undo a historical effect or prove task success.

Executor profiles and receipts are trusted in-process contracts, not authenticated
network messages. The included adapter performs local simulation only. A real
transport needs authentication, bounded I/O and an executor-specific release/fencing
contract. Local persistence alone makes no exactly-once promise about remote effects.

## Source layout

| Location | Responsibility |
| --- | --- |
| `reachability/model.py` | Immutable records, structural IDs and gate statuses |
| `reachability/logic.py` | Bounded complete CNF checker |
| `reachability/service.py` | Evidence, certificates, commits and invalidation |
| `reachability/journal.py` | SQLite transactions, integrity and authority locking |
| `reachability/codec.py` | Explicit typed JSON records without executable deserialization |
| `reachability/requirements.py` | Grounded AND/OR evaluation and exact support witnesses |
| `reachability/lifecycle_model.py` | Immutable schemas, lifecycle and operation records |
| `reachability/lifecycle.py` | Lifecycle certification and passive operation ledger |
| `reachability/execution_model.py` | Resource contracts, leases, certificates and intent records |
| `reachability/resources.py` | Complete integer interval-capacity checker |
| `reachability/execution.py` | Atomic reservations, local cancellation and intent recovery |
| `reachability/dispatch_model.py`, `reachability/dispatch.py` | Pinned executor contracts, durable submission and reconciliation |
| `reachability/simulated_executor.py` | Independent executor journal, idempotent/non-idempotent effects and release tombstones |
| `reachability/demo.py` | Executable public-API walkthrough |
| `reachability/recovery_demo.py` | Restart and credential expiry walkthrough |
| `reachability/lifecycle_demo.py` | Operation milestones and lifecycle validity walkthrough |
| `reachability/execution_demo.py` | Competing reservations, intent recovery and local lease expiry |
| `reachability/dispatch_demo.py` | Lost submission reply, recovery and fenced resource release |
| `tests/oracle.py` | Independent exhaustive Boolean evaluator |
| `tests/test_admission.py` | Authority, scope, lineage and concurrency checks |
| `tests/test_mutations.py` | Isolated witnesses for mutants M01–M04 |
| `tests/test_revisions.py` | Rule/policy changes and temporal boundaries |
| `tests/test_recovery.py` | Recovery, corruption, storage failures and process crashes |
| `tests/test_durable_contract.py` | Same admission contracts through durable storage |
| `tests/test_lifecycle.py`, `tests/test_operations.py` | Lifecycle and observation contracts |
| `tests/test_durable_lifecycle.py` | The same lifecycle and operation contracts with recovery |
| `tests/test_lifecycle_recovery.py` | Fault boundaries and committed-version compatibility |
| `tests/test_resources.py`, `tests/test_execution.py` | Independent capacity checks and coordinator contracts |
| `tests/test_durable_execution.py`, `tests/test_execution_recovery.py` | Recovered ownership and atomic crash boundaries |
| `tests/test_dispatch.py`, `tests/test_dispatch_recovery.py` | Submission gates, uncertainty, fencing and process crash boundaries |
| `tests/test_simulated_executor.py` | Executor identity, duplicate effects, tombstones and storage failures |
| `reachability_validation_design/` | Original proposed benchmark, not runtime inputs |

The oracle uses signed-integer formulas and exhaustive truth tables. It imports no
runtime implementation. Tests compare the runtime checker and returned witnesses
against it on 400 seeded generated formulas, in addition to hand-authored cases.
A separate three-valued oracle covers 240 generated requirement/world combinations.
An independent discrete-time occupancy oracle checks 500 generated claim portfolios
against the runtime interval sweep.
The evaluator is separated by imports and file location; OS-level isolation is
still pending.

## Current limits and next work

This is an in-process API with trusted callers, not a sandbox for hostile Python
code. The current storage lock implementation targets POSIX hosts. Schema migration,
context inheritance, variable matching and general temporal requirement expressions
are not implemented. Resource contracts cover integer renewable capacity, local
leases and simulated executor fencing. Under unresolved occupancy, the coordinator
conservatively blocks all use of an affected resource, even if its capacity exceeds
one. Context assumptions constrain
admission but are not automatically materialized as premise revisions in this slice.

There is no actual AtomSpace, FDAS, PLN, ECAN or Freeciv adapter yet. Pressure and
transport remain the supplied standalone numerical examples. The 64-fixture
target, full deployment episode, M05–M12 mutants and performance experiments are
still pending. Existing tests establish the stated finite contracts only.

The next increment adds goal slices, coverage accounting and observation-defined
durability, along with submission/completion temporal contracts for the deployment
episode. General context inheritance and variable binding remain explicit phase 1
backlog items.
