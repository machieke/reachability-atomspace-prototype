# Validation and coverage

All measured inputs and the auditor are frozen at
`b12127556d6d1fe4a7c152dba85f5d71df266194`. The default and native groups each ran
once at this revision, serially, before the final cohort. No suite was rerun to
replace a failure. Source and selected test hashes matched before and after each
group; the full receipts include individual test IDs and actual command arguments.

| Frozen invocation | Passed | Failures | Errors | Skipped | Seconds | Wrapper exit |
|---|---:|---:|---:|---:|---:|---:|
| Applicable default, 24 modules | 439 | 0 | 0 | 0 | 305.623094 | 0 |
| Applicable native, 8 modules | 82 | 0 | 0 | 0 | 123.035806 | 0 |

The new tests contribute 18 default and three native cases. Required controls cover
the independently encoded physical trajectory and six declared outcomes; passive
read count/order/channel suppression and observer removal at fixed commands/times;
no-command polling; actual lost reply and idempotent duplication; the existing
live-A-blocked task; intent without an effect; idle delayed effects; a failed effect;
unobservable physical success; wrong artifact; truthful pre-probe failure; historical
completion/reopening; nonmutation of authority; fixed public availability; and
rejection of misaligned sample times. Native controls use actual pinned formulas
and preserve authority/projection on reopen without rerunning inference.

The retained suites cover the previous consumer, bridge, online numerical service,
obligations, decisions, complete premises, contrary evidence, stale certificates,
execution, durable execution, dispatch, dispatch recovery and races, goals, coverage,
completion and lifecycle. B remains a task-selection constraint rather than live
authority. Existing numerical recovery tests are preservation checks; no recovery
implementation changed.

Exact included and omitted module names and test IDs are in
`validation/inventory.json`. Reproduce the two selected groups into a fresh directory:

```sh
uv run --no-project python -m world_lab.validate default --output artifacts/independent-world-tests
uv run --no-project python -m world_lab.validate native --output artifacts/independent-world-tests
uv run --no-project python -m world_lab.validate inventory --output artifacts/independent-world-tests
uv run --no-project python -m world_lab.validate preservation --output artifacts/independent-world-tests
```

Explicitly omitted: **648 default tests in 47 modules**, **64 native tests in 12
modules**, the separate **15 pressure numerical checks**, and broader scheduling,
attention/transport, planning and generalized recovery/corpus matrices. Those
implementations did not change. Historical passes are not counted as new passes.
Omissions differ from skipped tests: neither executed group skipped any test.
Delayed/out-of-order/noisy observations, multiple deployment attempts, arbitrary
non-idempotent multiplicity and crash resume are outside this protocol.

The twelve finite/native cohort executions all conform, including retained UNKNOWN
and adverse outcomes. The semantic replay checks 108 physical ticks, 280 public
decision/status rows and admitted-goal predicates, 172 unchanged-consumer selections,
94 product/health measurements, 24 actual ordered formula calls including 12 fresh
native calls, all 510 persisted certificates and twelve executor reconstructions.
It also checks no budget/history reset, fixed opportunities, actual source responses,
private transition nonmutation and final authoritative/projection reconstruction.
Recorded native arithmetic is replayed using the independent finite checker;
auditing itself is not another native cohort run.

Eight isolated comparison mutations are rejected: unsealed trace, observation-created
product, observation-created health, world relief copied from observed/controller
loss, hidden truth added to public authority input, adverse health rewritten as
healthy, fabricated executor receipt and duplicated effect. The original bundle
is never rewritten. Exact rejection reasons are in `validation/negative.json`.

Preservation checks compare all **770 prior tracked files** outside the plan and
manifest against `173c772`; every file is unchanged. Both native build receipts
also match the immutable previous review. The archive retains full source hashes,
selected test source files and hashes, start/end regression receipts, logs, wrapper
exit records, audit/mutation results, raw cohort evidence and development failures.

[DEVELOPMENT.md](DEVELOPMENT.md) reports the original failed test assertion and
auditor replay defect, their retained evidence, and corrections before the frozen
run. The earlier publication's wrapper exit 143 remains preserved and unresolved;
the two current zero exits do not reinterpret that earlier invocation.

Archive checksum/inventory verification, extracted semantic replay and rejection of
an altered archive are recorded separately in `PUBLICATION.json` after publication.
Integrity is distinct from publisher authentication and from real-world validation.
