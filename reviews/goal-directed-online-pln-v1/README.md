# Goal-directed online PLN discovery — independent review

Bounded experiment at source `d1d39ab` (full revision recorded in the bundle).
Preregistered at `e1f6b94`. Baseline publication `3f433ed` and all historical review
bytes are preserved. This review closes only the task-directed discovery increment.

The three arms are frozen FIFO-full, Goal-scan (full enumeration plus task-first
FIFO), and Goal-index (cold scoped discovery with the same FIFO selection).
Task roots come from actual successful registration receipts and the current
public decision contract. Both criterion polarities, all five ordered rule
premises, all registered producer routes, exact support alternatives and current
monitoring/operation obligations survive relevance classification. Relevance is
never evidence, authorization or a probability estimate.

The whole public snapshot is still exported. All selected candidates still undergo
full enumeration for membership validation, followed by unchanged certification,
atomic commits, hard/resource gates, reservations and final dispatch checks. A
conservative capacity preflight falls back to full enumeration when background work
could exhaust a global bound. Missing prerequisites direct acquisition but never
make an incomplete inference executable. Incomplete dependency scopes are labeled
and use the declared full fallback. Shared inputs do not make unrelated outputs
relevant. Costs affect affordability only.

Each of twelve parents runs two budgets (8 and 16), three arms and two execution
modes: 144 primary executions. Twenty-four additional finite rename/reorder
siblings are diagnostics, not additional parents. Source availability is fixed
privately; proposal and continuing-monitor boundary injections are explicitly
identified. No future responses, fixture IDs, expected answers or evaluator losses
enter the controller. Native selected work uses pinned PLN, and native AtomSpace
projection/readback checks the persisted exercised authority before/after reopening.
SQLite remains authoritative; this is not live AtomSpace retrieval.

## Reproduce and inspect

Use auditor/publication source `795963c` (measurement source `d1d39ab`) and the pinned native build described in
[ADAPTERS.md](../../ADAPTERS.md). The following command requires a fresh output path:

```sh
uv run --no-project python -m goal_pln_lab.compare --output /tmp/goal-pln-fresh
```

It writes `report.json`, `analysis.json`, `comparison.md`, source/configuration
inventories, every public snapshot/frontier/relevance witness/selection/receipt,
SQLite journals, native build metadata, and checksums. Missing native dependencies
produce an explicit blocked requirement; finite is never substituted for native.

```sh
uv run --no-project python -m goal_pln_lab.compare --verify /tmp/goal-pln-fresh
uv run --no-project python reviews/goal-directed-online-pln-v1/verify_review.py
```

The measured bundle retains source `d1d39ab`; the corrected verifier is at
`795963c`. Its only runtime-file change is the cross-session audit normalization
explained in [AUDIT-CORRECTION.md](AUDIT-CORRECTION.md). The initial failed audit is
retained. The fresh-output command at `795963c` records that revision itself;
the published execution measurements are explicitly those from `d1d39ab`.

The first command independently replays traversal and full candidate enumeration,
checks Goal-scan/Goal-index parity at matched histories, validates choices/budgets,
recomputes recorded formulas, compares finite/native trajectories and replays copied
SQLite journals. The second verifies the review archive inventory/checksums; it is
an integrity check, not publisher authentication. Existing publication/seal helpers
are reused. The source-bound bundle includes development failures and corrections.

## Results and recorded decisions

All **144 primary executions** and **24 diagnostic siblings** passed their prefix
contracts. Corrected audit: **1,188 matched-snapshot comparisons**, **1,044 selected
operations**, finite/native parity, and exact Goal-scan/Goal-index semantic parity.
Offline analysis matched **300 selected successful numerical commits** to persisted
certified beliefs. Primary statuses: 1,008 PASS, 24 intentionally STALE proposals,
and 12 UNKNOWN source responses. No unauthorized effect, stale commit, suppressed
blocker, evidence inflation, missed relevant candidate or false completion was found.

Favorable selection result: in `route-distractors`, FIFO-full uses work 1–2 for
`a-separate` and `a-shared`, then requests/adopts the missing report at work 3–4,
deduces the forecast at 5, reserves at 6, dispatches at 7, and observes the product
at 8. Health observations occur at 9, 10 and 11; certified loss falls from 10 to 0
only at 11. Both goal arms request/adopt at 1–2, deduce at 3, reserve at 4, dispatch
at 5, observe product at 6, and monitor at 7, 8 and 9. They complete lifecycle at
10 and perform the two background deductions at 11–12 via full fallback.

Thus at work budget 8, FIFO external loss is 10 and both goal arms' external loss
is 0, but **all three certified losses remain 10**. This difference follows the
recorded acquisition/product/health sequence, not an assertion that the first
choice alone explains every outcome. At work 16, all three have zero terminal
loss and execute three formulas: background work was deferred, not eliminated.
The shared-input case advances dispatch by one work unit; the no-distractor control
has identical operations and outcomes. Across 24 runs per mode/arm, each arm has
12 terminal certified-zero outcomes; the goal arms have one additional external-zero
outcome (15 versus 14). These are repeated engineering cases, not independent samples.

Neutral and unfavorable results: the two- and three-deduction chains produce actual
certified numerical results but remain below the unchanged decision strength
threshold. Missing evidence and contrary/low-confidence support remain blocked.
Continuing monitoring reopens the goal after an observed failure. Goal-scan and
Goal-index never differ in task quality. Goal-directed selection adds overhead;
indexing is more expensive still in the measured selection pipeline.

Aggregates below are per arm over 24 runs in each mode. Times are seconds; rows
are not additive cost components. Full details and per-decision losses are in
[summary.json](summary.json) and the bundled traces.

| Measure | FIFO-full | Goal-scan | Goal-index |
|---|---:|---:|---:|
| Native selected formula calls | 42 | 39 | 39 |
| Native unrelated formula calls | 6 | 3 | 3 |
| Selection tuple visits (either mode) | 305 | 311 | 296 |
| Finite selection inclusive time | 0.744 | 2.119 | 2.749 |
| Native selection inclusive time | 0.828 | 2.026 | 2.663 |
| Native cold index build | — | — | 0.006 |
| Native full execution enumeration | 0.581 | 0.735 | 0.581 |
| Native formula time, including startup/checks | 5.203 | 4.872 | 4.947 |
| Finite total episode time | 32.708 | 34.539 | 34.092 |
| Native total episode time | 51.505 | 53.117 | 53.622 |

Indexing reduced tuple visits by 15 relative to scan but increased selection time
by about 31% in native runs (and 30% in finite runs). Map construction alone was
small; the scoped enumerator additionally validates its dependency binding, which
computes another whole-snapshot digest. That cost is included. This is a comparison
of these complete implementations, not an idealized index lookup. Small differences
in total episode time do not establish a repeatable speed advantage.

Primary maxima: 19 current estimates of 32 allowed, 3 rules of 16 allowed, and
53 index entries. No primary scope was incomplete. The 108 logged full-fallback
rows are declared behavior. Bounds and cycles are tested separately. Renaming
changed four of 24 diagnostic operation sequences (two FIFO prefixes and two
post-completion goal-arm background orders); losses and total work were unchanged.
Reversing report receipt order caused no normalized operation-sequence changes.
Identifier tie-breaking is not an optimality guarantee.

## Validation and preservation

At measured `d1d39ab`: **281 applicable tests** across 17 default-suite files,
**87 native tests** across all 13 integration files, and **15 standalone numerical
checks** passed with zero failures, errors or skips. The native tests include real
composed deductions, stale proposal rejection and task-state projection/readback.
At auditor `795963c`: **2 targeted audit-correction tests** passed. The full default
suite was **not run** in this increment; 47 other default test files are explicitly
listed as omitted in the bundle. No historical pass count is relabeled as new.

The failed first development assertion and original source, corrected 17-test run,
first finite development cohort, failed cross-session audit, corrected audit and
checksum/selection tamper rejections are retained. Exact original hashes remain
validated against each run's own snapshot; only cross-session comparison omits the
two authority-dependent candidate hashes. See the correction document for details.
A byte comparison preserves 185 baseline measured-source and historical review
files. Frozen FIFO code and its twelve-case publication remain unchanged.

## Interpretation and limits

Compare Goal-scan with FIFO-full for the selection effect, and Goal-index with
Goal-scan for discovery costs. Both goal arms must produce identical semantic
trajectories at equal work budgets. There is no wall-cap arm. Timings are one ordered
pass, with no randomized order or uncertainty estimate. Inclusive measurements
contain nested categories and must not be added together.

Measured categories include public reads and serialization, roots, closure, cold
index construction, tuple visits/materialization, classification/ranking, full
fallback and execution revalidation, actual formulas including stale results,
admission/persistence, reservation, dispatch, monitoring, goal accounting, projection,
reopen and total episode time. Index entry counts are recorded; RSS is unmeasured.
SQL/fsync cost is included inside public mutation timings but not isolated. Native
startup and pin checks are included inside runtime costs, not separated from native
compute. Simulation request work, local wall time, and unmeasured physical sensing
latency are distinct.

Logical time advances on received events, so fewer declared operations does not
establish an elapsed real-world benefit. Low-confidence or unfavorable estimates
remain visible to all-current acceptance. Correct rejection and unresolved goals
are not successful deployments. Composed local three-proposition certificates do
not establish a globally consistent joint distribution over arbitrary overlaps.

No pressure promotion, transport, learned scheduling, evidence aggregation,
persistent indexing, generalized recovery, calibration, inference optimality or
large-storage scaling claim follows. This increment stops here.
