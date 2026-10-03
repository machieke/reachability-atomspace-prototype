# Native AtomSpace-backed task recall — independent review

Measured implementation and auditor: `79f4f439a510cfb6c94a831985e8daee1cfbd84e`.
Preregistered at `c4147f5`. Publication `846053a`, its measured sources, policies,
fixtures, corrections, failures and review bytes remain unchanged.

This bounded integration gives Goal-native a real, immutable AtomSpace read view.
Native incoming links, ordered outgoing relations and keyed Values supply producer
rules, all current support alternatives, received reports, public probes and exact
revision-model records. The complete declared discovery universe is loaded before
querying. An ID table decodes answers; it does not calculate their membership.
Historical-support and exact record readback queries are tested separately.

Python still extracts task roots, traverses dependencies, joins returned records,
ranks candidates and handles operational readiness. Goal-native retains the frozen
Goal-scan priority, ties, ages, costs, retry rules and full-frontier fallback. Every
selected operation still undergoes full authoritative enumeration and the unchanged
certification, lineage, resource, reservation and dispatch gates. SQLite remains
authoritative. Native query receipts are diagnostic bindings, not certificates. A complete empty
query establishes absence only within that declared epoch; it does not prove a goal
impossible. An incomplete query never becomes a complete empty answer.

## Reproduce and verify

Build the existing pinned adapter as documented in [ADAPTERS.md](../../ADAPTERS.md),
then build the separate recall helper. Use a fresh comparison output directory:

```sh
uv run --no-project python scripts/build_native_recall.py
uv run --no-project python -m native_recall_lab.compare --output /tmp/native-recall-fresh
uv run --no-project python -m native_recall_lab.compare --verify /tmp/native-recall-fresh
uv run --no-project python reviews/native-atomspace-recall-v1/verify_review.py
```

The comparison command writes source/configuration inventories, all public snapshots,
native view/query receipts, candidates, relevance witnesses, choices, budgets,
formula calls, certificates, external outcomes, SQLite journals, costs and a readable
comparison. The unchanged twelve parents, seed 0, budgets 8/16, two recall arms and
two formula modes produce **96 executions**. They are reused engineering cases,
not new independent confirmation tasks. Native recall requires actual AtomSpace
even with finite formulas; native-formula Goal-native runs both native components.
Missing dependencies and protocol failures are BLOCKED/ERROR, never silent Python
substitution. Declared query/closure exhaustion retains the logged full fallback.

The first verification command replays actual native loads/queries and frozen scan
selection at matched snapshots and histories, compares recorded answers against
independent source scans, checks formula outputs/certified commits and replays copied
SQLite journals. The final command checks the review archive inventory/checksums;
it establishes integrity against those checksums, not publisher authentication.
The archive contains `comparison/`, `validation/`, `development/` and `review/`.
Extract it into a fresh directory and run semantic verification on its `comparison/`
subdirectory with the pinned build and measured auditor source. Published semantic
replay also checks the recorded native build identity: a different compiler/build
receipt is not silently treated as identical. A fresh comparison in another verified
build environment records its own build identity. Bit-identical native builds across
machines or filesystem layouts have not been established; archive integrity checks
do not require the native runtime.

## Findings

All **96 executions passed**. Semantic replay passed at the same frozen source:
**792 matched native/scan states**, **19,388 native-query/reference checks**,
**696 selected operations**, **196 persisted selected numerical commits**, and
**156 recomputed formula calls**. Exact matched-state candidates, witnesses,
eligibility, choices and budgets agree; cross-session recall/formula trajectories
agree under the previously documented authority-local identity normalization.
The run took 328.70 seconds and semantic verification took 310.67 seconds.

Both recall arms have the same certified and external terminal outcomes, selected
formula counts and operation sequences. Each 24-run mode/arm group has 12 certified
zero-loss outcomes, 15 external zero-loss outcomes, 174 selected operations and 39
formula calls. Across the comparison, selected replies are 672 PASS, 16 intentionally
STALE proposals and eight UNKNOWN source responses. These expected replies are not
harness failures. No stale proposal became a committed belief or dispatched effect.

Favorable conformance result: actual native answers drive acquisition, deduction,
authorization, dispatch, product observation and health monitoring through the public
interfaces. Selection-only tests disable Python discovery and demonstrate a native
selected deduction and request; separate full execution revalidation remains enabled.
A wrong/missing native producer and a wrong ordered-premise relation are detected.
The native scoped path visits 296 tuples per group versus scan's 311. It does not
reduce the 39 selected formula calls, work or full execution checks.

Neutral outcome result: the simple `route-control` selects deduction, reservation,
dispatch and product observation at work 1–4, then health observations at 5–7 and
lifecycle completion at 8. Certified loss stays 10 until the third health observation
at work 7. Both recall arms match. In `route-distractors`, request/adoption/deduction
occur at work 1–3, dispatch at 5, product observation at 6, and health observations
at 7–9. External loss becomes zero at 7, while certified loss becomes zero at 9.
Completion is at 10; unchanged fallback performs the two background deductions at
11–12. At budget 8, certified loss is still 10. No scheduler improvement is claimed.

Revision behavior is preserved. In `change-replacement`, the first proposal is STALE;
work 2 adopts the equal-valued replacement, and work 3 deduces from the new exact
support IDs. In `change-producer`, the stale first proposal is followed by a deduction
using `new-producer`. Both changes force new views. Missing evidence, contrary and
unfavorable estimates remain visible. The two/three-step chains perform real
certified deductions but stay below the unchanged decision contract. In
`path-alternatives`, later unfavorable results block future authorization after an
earlier valid dispatch; observation/monitoring of that actual product continues.
The reopened case retains loss after the continuing-monitor boundary and observed
failure. None of these unresolved states is reclassified as successful deployment.

Unfavorable cost result: native recall is substantially slower here. The table sums
24 episodes per mode/arm; times are seconds. Inclusive categories overlap and must
not be added together. This is one ordered pass with concurrent regression load,
without randomization, balanced repetitions or uncertainty estimates.

| Measure | Finite / scan | Finite / native recall | Native PLN / scan | Native PLN / native recall |
|---|---:|---:|---:|---:|
| Selection inclusive | 2.210 | 57.044 | 2.536 | 57.809 |
| Cold view open inclusive | — | 52.881 | — | 53.322 |
| Native build verification within opens | — | 42.389 | — | 41.831 |
| Projection construction | — | 2.601 | — | 2.820 |
| Native helper startup | — | 2.015 | — | 2.350 |
| Load and readback I/O | — | 3.471 | — | 3.725 |
| Readback validation | — | 0.754 | — | 0.858 |
| Queries within sealed views | — | 0.628 | — | 0.662 |
| Full execution enumeration | 0.555 | 0.643 | 0.671 | 0.557 |
| Formula runtime, including startup/checks | 0.002 | 0.002 | 4.730 | 4.834 |
| Total episode elapsed | 34.177 | 90.112 | 73.571 | 129.885 |

There are 198 cold views and 9,694 queries per Goal-native formula-mode group.
Every recorded selection snapshot changes its full binding, so this cohort contains
no cross-selection view reuse. Many queries run inside each sealed view. Same-epoch
identical-query reuse is separately tested; it is not a realistic warm-cache claim.
The 19,388 primary native queries visit 102,592 incoming links and return 15,118
records. All primary query results and dependency scopes are complete. The 108
logged full-frontier fallback rows are the frozen no-affordable-untried-relevant-work
behavior, not native errors. Exhaustion and incomplete scopes are tested separately.

Peak per view: 1,278 atoms, 53 query relations, 177 Values, 34 source records,
747,235 encoded load bytes and 224,832 full public-export bytes. These are bounded
small-instance counts, not native memory measurements. Per-view receipts and all
cost categories are in [summary.json](summary.json) and the archive. Cold view cost
includes rechecking hashes of the pinned build artifacts at each changed epoch;
it is retained in the comparison. No optimization follows in this increment.

## Validation and evidence limits

At frozen `79f4f43`, the package-qualified full default suite passed **1,006 tests** across all 65 test files in **1242.175 seconds**. All **103 native integration tests** across 14 files passed in **239.817 seconds**, and all **15 numerical reference checks** passed. These passing runs had no failures, errors or skips. The new tests comprise six default and 16 native tests; no default/native test file was omitted. Start/end checks confirm unchanged implementation and test hashes.

The initial full-default discovery attempt completed 1,006 tests with one failure in a pre-existing module-specific mutation mock. A package-qualified invocation of that test passed; the entire suite was then rerun with qualified module names. The original 1,005-pass/one-failure result is retained, not relabeled. See [VALIDATION-NOTE.md](VALIDATION-NOTE.md) for both commands, inventories and the diagnosis. Neither implementation nor historical tests changed.

New tests cover independent brute-force query references, exact readback, matched
closure/candidates/witnesses/eligibility/selection, native participation canaries,
replacement and new/revised producers, contrary estimates, model/policy/time/probe
changes, contexts, polarity, ordered/duplicate arguments, Unicode, exact integers
beyond binary64, missing AND prerequisites, alternatives, cycles, malformed/partial/
duplicate loads, stale and unknown queries, explicit limits, timeout, helper loss,
read-only rebuild and continuing observation obligations.

Development failures and corrections are retained in [DEVELOPMENT.md](DEVELOPMENT.md)
and `development/`. No official execution matrix rerun was needed. Semantic audit
rejects an unsealed trace alteration, a resealed selected-target alteration and a
resealed native-query answer alteration. Archive integrity and a changed-archive rejection are recorded separately in
[publication-validation.json](publication-validation.json).
All 621 pre-existing tracked files except the plan and manifest are byte-identical
to `846053a`, including 58 historical review files. Dependency pins and original
helper/build receipts remain unchanged.

The complete public export and full execution enumeration remain costs. Projection
snapshot serialization is nested inside construction; epoch replacement is nested
inside view opening; query work is nested inside traversal, joins and selection.
Public reads, serialization, roots, closure, tuple construction, ranking/fallback,
pre/post certification, numeric commits, acquisition/ingestion, dispatch, monitoring,
goal accounting, projection/reopen and whole episode time are recorded. SQL/fsync
and native PLN startup are included in their public-operation/runtime costs but
are not isolated. Native RSS, isolated C++ compute, physical sensor latency and host
load are unmeasured. No timing or statistical performance promotion follows.

Views are immutable, bind the complete epoch and authority identity, and rebuild
on change. There is no persistent/incremental native store, concurrent native writer,
remote query service, pressure/transport, new evidence aggregation, scheduler tuning,
generalized recovery, global probabilistic-consistency or large-storage claim.
This bounded milestone stops here.
