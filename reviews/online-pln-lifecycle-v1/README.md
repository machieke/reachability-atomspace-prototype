# Online numerical PLN/lifecycle conformance

The bounded slice passed all **24 conformance runs**: the twelve preregistered
fixtures in finite-checker and pinned native modes. Both modes produced matching
semantic decision sequences: **76 selected operations and 15 formula invocations
per mode**. This integrates live work discovery/acquisition with the existing
certified numerical ledger, decision gate and observed deployment lifecycle.
It is not a performance comparison or a stochastic planner.

The measured implementation is **`0cd1f8a53797791321ad974c67286fad0f5b37c4`**.
The fixture inventory was committed before execution at **`1cf88ba`**. Publication
is a later commit; those revisions are not interchangeable. The earlier static
planning comparison remains closed at publication `4fffa74`, measured at `4be8091`.
All existing runtime, pressure, static planner and prior review bytes are unchanged.
The frozen pressure orderer did not justify its overhead against neutral ordering
in that static fragment; no pressure mechanism was retuned in this increment.

## Reproduction and independent review

At the measured checkout, with the adapters built as described in
[ADAPTERS.md](../../ADAPTERS.md), use one fresh output directory:

```bash
uv run --no-project python -m validation_lab.online_pln_conformance --output /tmp/online-pln-review-new
```

This runs both modes and writes source/configuration bindings, public observations,
complete candidate frontiers, selections, certificates, proposals, journals,
native calls, projection/reconstruction receipts and a readable `conformance.md`.
Missing native dependencies fail explicitly; there is no finite fallback.

```bash
uv run --no-project python -m validation_lab.online_pln_conformance --verify /tmp/online-pln-review-new
uv run --no-project python reviews/online-pln-lifecycle-v1/verify_review.py
```

The first command checks sealed artifacts, all 141 bound source files, configuration,
recomputed public frontiers/FIFO choices, prefix expectations, budgets and checked
SQLite replay on copies. The measured run's audit passed **291 files, 24 cases and
152 selections**. The archive verifier reuses the preceding review's integrity
checker with only its archive/schema names changed. It checks the complete archive
inventory and SHA256 values, not publisher authenticity. See `ARCHIVE.json` and
`SHA256SUMS` for the archive's physical identity.

The archive contains the corrected `comparison/`, regression logs/receipts, preservation checks,
publication files and retained development failures. Its `comparison/source/`
contains the 141 measured input files; it is a review snapshot, not a standalone
replacement for the Git checkout and native build. Prior published archives are
preserved in Git rather than recursively duplicated into this archive.

The first source-bound run at `b771ce8` is retained but superseded: manual review
found fixture-expectation wording in a public independence justification. The
[correction record](CORRECTION-v1.1.md) explains its removal. All 24 corrected
semantic decision sequences and numeric forecasts match the retained originals.
No outcome, root, budget, rule or expected status was changed to obtain a pass.

## Implemented boundary

`experimental_online_pln` is a thin coordinator over unchanged public APIs. It
maintains receipt indexes for registered rules, independence declarations and
received reports. Only the existing service can accept estimates, issue permits,
reserve resources, send a request or reconcile goal relief. Native AtomSpace remains
a disposable projection; SQLite remains the authority.

The versioned public snapshot contains current authoritative numeric/hard views,
received reports and observations, registered grounded rules/models, decision and
lifecycle versions, goals, clocks, resources and acquisition descriptors. A
descriptor contains its target, source, type, preconditions, known availability,
cost and current opportunity. Future answers, fixture IDs/expectations and private
event schedules are absent. Forced proposal/dispatch races live in the evaluator
and are labelled seam events.

The agenda is FIFO by first-ready enumeration round, then semantic operation,
target and ordered evidence identities. Logical work identity is separate from
the complete current authority binding. Enumeration never runs a sensor, formula
or certification. Selected work still obtains fresh public gates. Fixed-basis
failures are suppressed; changed relevant inputs or a new observation opportunity
permit bounded attempts. Successful acquisition consumes that opportunity.

The coordinator caps are 16 grounded rules, 32 current estimates, 64 candidates,
128 tuple visits, 32 selections, 64 work units and 16 acquisition units. Receipt
indexes additionally cap models/reports/probes at 16/128/16. Truncated enumeration
stops explicitly. Quiescence or budget exhaustion does not establish impossibility.
The supported channels are report acquisition/adoption, grounded deduction,
declared revision, reservation, dispatch, query, monitoring and certified completion.
Other inference/search/transport channels are unsupported.

## Outcomes, including blocked cases

Results below are identical in both modes. PASS in the conformance column means
the declared behavior was observed; it does **not** mean every deployment succeeded.
Five fixtures remain DRAFT. Seven reach BUILT, with one subsequently reopening need.

| Fixture | Selected | Formula calls | Final stage | Goal loss | External loss | Executor effects |
|---|---:|---:|---|---:|---:|---:|
| choice-available | 12 | 3 | BUILT | 0 | 0 | 1 |
| choice-unavailable | 3 | 2 | DRAFT | 10 | 10 | 0 |
| lineage-independent | 1 | 1 | DRAFT | 10 | 10 | 0 |
| lineage-copied | 1 | 0 | DRAFT | 10 | 10 | 0 |
| support-replacement | 10 | 2 | BUILT | 0 | 0 | 1 |
| support-alternative | 9 | 2 | BUILT | 0 | 0 | 1 |
| boundary-valid | 8 | 1 | BUILT | 0 | 0 | 1 |
| boundary-joint | 1 | 0 | DRAFT | 10 | 10 | 0 |
| race-retained | 8 | 1 | BUILT | 0 | 0 | 1 |
| race-revoked | 5 | 1 | DRAFT | 10 | 10 | 0 |
| product-durable | 8 | 1 | BUILT | 0 | 0 | 1 |
| product-reopened | 10 | 1 | BUILT | 10 | 10 | 1 |

Across both modes the selected public operations return **138 PASS, 4 UNKNOWN,
6 STALE and 4 FAIL**. The negative statuses are expected conformance witnesses,
not discarded runs. The dataset consists of six paired families in one synthetic
scenario, not twelve independent performance samples.

**Live choice and acquisition.** The initial frontier has two ready auxiliary
deductions (`audit`, `canary`) competing with `source-report`. FIFO selects both
deductions, then acquisition, adoption of the received numeric report, and the now
ready `deployment` deduction. These are actual selected operations, not a supplied
action script. The auxiliary work consumes budget; this is not a claim of optimal
goal-directed selection. The available sibling then reserves, dispatches, observes
the exact product, collects three health samples and completes. The unavailable
sibling stops after its source reports UNKNOWN; it retains ten units of need.

The deployment estimate is `(0.6799999999999999, 0.35840000000000005)` and its hard
query remains UNKNOWN. Forecast and PASS decision leave external/goal loss at ten.
Reservation and ACK yield `(outstanding, coverage, open) = (10, 6, 4)`, still without
relief. The first healthy observation lowers the simulator's immediate external
loss to zero; durable goal loss follows **10, 10, 0** across the three fresh samples.
Lifecycle completion is a separate certified operation after durable observation.

**Independence and retained alternatives.** Explicit independence plus disjoint
roots permits native revision from two `(0.7, 0.25)` estimates to `(0.7, 0.4)`.
Both parents remain current. The unchanged `all-current-exact-literal/v1` gate
correctly remains UNKNOWN because their confidence is below 0.35. The copied-root
sibling returns UNKNOWN before a formula call, retains two estimates and gains no
confidence. Neither fixture is counted as successful deployment.

**Changed supports.** A forced revocation after selected native inference but
before postcheck makes the pending old commit STALE. One sibling subsequently
adopts an equal-valued replacement; the other retains a distinct independent
premise. Fresh enumeration and fresh certification produce the usable deduction.
The old failed proposal never commits or silently rebinds. The native computations
whose commits became stale remain visible and charged.

**Numerical boundary.** The valid five-premise deduction has an eight-world joint
witness. The existing near-one counterexample (`P=Q=.99995`, `R=.499975`,
`P(Q|P)=1`, `P(R|Q)=.5`) fails whole-joint pre-admission with no native call.
No repaired number, failed-precondition fallback or Boolean assertion is supplied.

**Dispatch race.** Both siblings first obtain a decision certificate and reserve.
The revoked sibling loses relevant support after durable preparation and before
final send. Dispatch returns STALE, effect count remains zero, coverage becomes
zero and all ten units remain open. Two charged queries observe the existing
uncertain dispatch record; unchanged-basis rediscovery then stops. No generalized
recovery or successful-send shortcut is added. The retained sibling dispatches
and completes normally.

**Product, uncertainty and reopening.** In both product cases, forecast retirement
after ACK leaves the accepted effect historical while the current numerical gate
becomes STALE. Exact observations can still satisfy the separate completion
contract. The reopened sibling first rejects the wrong product, then succeeds on
an explicitly offered later observation opportunity. After three healthy samples,
completion records BUILT with zero goal loss. The next clock event makes the fresh
sample missing: the goal becomes UNKNOWN with outstanding ten, coverage six and
open four, while the last observed external condition remains healthy. The actual
unhealthy sample then establishes OBSERVED_FAILURE, external loss ten and zero
coverage. Accounting retains `observed_relief` and `reopened`; BUILT history is
preserved. The trace therefore does not attribute the earlier freshness loss to
the later unhealthy sample.

## Measured costs

The two-mode case loop took **41.046 seconds**, overlapping regression processes
on this host. These are single-run engineering measurements, not performance claims.
All fifteen native formula invocations matched the existing deterministic checker
exactly; two produced proposals whose later commits correctly became stale.
Native calls are fourteen deductions and one revision. Native projection/readback
and quiescent reconstruction passed in all twelve cases without new inference.

| Measured category (seconds, summed over twelve cases) | Finite | Native |
|---|---:|---:|
| Episode elapsed, including closing authorities | 16.734 | 24.094 |
| Candidate enumeration at selection | 0.298 | 0.275 |
| Candidate revalidation enumeration | 0.225 | 0.213 |
| Acquisition, including ingestion/monitoring | 3.722 | 3.274 |
| Formula runtime, including native startup and pin checks | 0.001127 | 1.835 |
| Independent selected native-result reference check | n/a | 0.001168 |
| Numerical prechecks, including persistence | 0.756 | 0.735 |
| Numerical postchecks, including persistence | 0.840 | 0.841 |
| Numerical commits, including persistence | 0.904 | 0.853 |
| Dispatch | 0.240 | 0.225 |
| Product/health monitoring and operation queries | 3.716 | 3.264 |
| Failed attempts, inclusive | 0.413 | 0.528 |
| Retries after failed operation, inclusive | 0.453 | 0.539 |
| Native projection/readback, both sides of reopening | n/a | 6.534 |
| Authority reopening | 0.672 | 0.649 |

Do not sum these overlapping categories. Acquisition contains observation
ingestion/monitoring; inference contains runtime and its reference check; failed
attempts and retries overlap execution. Setup, read queries, reservation,
completion, goal accounting and remaining timings are in `summary.json` and the
raw reports. Initial report adoption costs are included in setup and numeric
categories. All 152 selected attempts consume declared budgets regardless of status.

Not separately measured: SQL/fsync versus checker time, OS scheduling, memory/RSS,
native computation versus subprocess startup, trace serialization, and physical
sensor/network latency. The external executor and sources are local simulators.
Episode totals include setup through authority closure. The case-loop timer also
includes per-case output writing; CLI startup, initial source/build preflight and
final report/seal writing fall outside it and are not separately measured. Offline
audit and publication packaging are separate from the episode costs.
No inference-savings or native-speed claim follows from these numbers.

## Validation and limits

The full suites at **`b771ce8`** passed **981 default tests**, **86 native
integration tests** and **15 standalone numerical reference checks**, with zero
failures, errors or skips. Their elapsed times including discovery were
1376.395, 188.798 and 0.040 seconds, respectively.

After the public-justification wording correction, **all 19 affected coordinator
tests passed at `0cd1f8a`** in 52.278 seconds: 18 finite seam tests plus
the native twelve-fixture/projection test. These repeat earlier executions and
are not nineteen additional unique tests. The full suites were not repeated after
that one-line evaluator metadata correction; existing runtime and regression
sources are byte-identical, and the changed coordinator leakage check was rerun.
Receipts preserve exact revision, suite, count, failure/skip and timing information.

The default suite includes independent numeric-domain/joint checks, the existing
deployment/regression corpus and M09. Three test-only mutants are detected:
silently refreshing a stale request, forgetting fixed-basis failed attempts, and
reporting a forecast as world relief. The bundle audit also rejects both changed
artifacts and resealed altered selections. Offline publication checks match all
30 selected numerical commits to persisted beliefs and recompute all 30 formula
results, with no omitted or unselected formula calls.

Tests cover read-only frontier construction, exact retry/duplicate suppression,
alternate-tuple exhaustion, candidate/proposal staleness, relevant rule/policy/model
changes, immutable hard gates, retained low-confidence parents, harmless rule
renaming/report reordering for equivalent executed operations, and missing/failed/
malformed/mismatching native results. This does not claim identifier-invariant
bounded agenda outcomes. Existing integration tests exercise actual native parser,
timeout, source/build-drift and readback failure boundaries.

See `DEVELOPMENT.md` and the retained artifacts for the first dispatch wiring
failure, a corrected test expectation and a retry-basis implementation error.
No fixture was altered to force a success. The archived development executions
are distinct from the frozen implementation's regression and comparison evidence.

No default/native test files were omitted from the full executions at `b771ce8`.
The final source reran every affected coordinator test as described above.
Upstream projects' full suites
are outside this repository's conformance scope. The coordinator may explicitly
stop on interruption while preserving the authority journal; new coordinator crash
continuation is unsupported. General uncertainty planning, autonomous independence
learning, mutable native authority, broader joint models, adaptive transport/M12,
learned conductance, generalized recovery and scale claims remain deferred.
This milestone stops at the source-bound conformance publication.
