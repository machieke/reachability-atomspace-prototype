# Descriptive shadow overhead

One serial pass at `5161e19`, seed 0. Acquisition was charged once for each of 26
authoritative captures (including the historical ledger); nine transformations use
already captured inputs. Each of 54 role/diagnostic pairs separately evaluates A
then B. The ordering is fixed, not randomized; these times do not establish a
speed advantage or general performance result.

| Charged phase | A (ms) | B (ms) |
|---|---:|---:|
| Complete evidence scan | 6.209 | 5.155 |
| Applicability classification | 0.607 | 0.706 |
| Policy evaluation | 0.405 | 1.285 |
| Witness/basis serialization | 28.706 | 29.462 |
| Other inclusive work/residual | 28.645 | 26.827 |
| Total evaluation | **64.573** | **63.435** |

Shared acquisition: **124.021 ms**. Complete cohort elapsed: **12.077 s**, including
fixture construction, certified real inference, historical archive verification,
SQLite persistence, native projection/reopen and artifact writing. Session
construction totals **11.631 s** and includes acquisition; do not add nested totals.
The cohort timer begins after source copying and native build verification, so
those preflight costs are not included in its elapsed value.

Scan/classification/evaluation/serialization times nest within total evaluation.
Parsing, manifest/scope validation, hashing and work performed before an exhausted
stage returns are in the inclusive residual. Three runs per interpretation do not
complete the scan stage; four do not complete classification. Policy evaluation
does not complete in four A and five B diagnostic evaluations. Missing stage
counters mean **not completed**, not zero computational work.

A uses the same complete validation/classification/reporting path, so this is not
a benchmark of the production inspector's minimum possible cost. B's recorded
witness stage retains all witnesses and inspected records; it selects no winning
estimate. Output JSON persists exact nanosecond values and finite work limits.

Each fresh session also preserves the existing `setup_ns`, `precheck_ns`,
`inference_inclusive_ns`, `postcheck_ns`, `numeric_commit_ns`, `runtime_ns` and,
where applicable, native projection/reopen and finite-reference-check costs.
These include their existing persistence/runtime overheads; they are not disjoint.
The three native cohort formulas are actual PeTTa/PLN executions checked against
the pinned finite implementation. Replay performs finite checks of the recorded
outputs; it does not relabel them as fresh native executions.

Isolated native arithmetic, isolated fsync, RSS, source-copy/build-verification
preflight time, physical observation latency and hypothetical counterfactual
execution cost were not measured. No scheduling/controller timing is remeasured
or changed. The machine-readable sums and raw records are in
`validation/analysis.json` and each `comparison/*/receipts.json` in the archive.
