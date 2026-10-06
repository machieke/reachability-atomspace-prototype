# Executed validation

Measured implementation and auditor: `53d7b0b257ea436dc043e9d497fd3c76dcd0e03c`.
Protocol preregistration: `6993c40`. All source/test hashes matched at regression
start and completion. Regression timing overlaps the measured comparison.

| Suite at measured revision | Executed | Passed | Failures/errors | Skipped |
|---|---:|---:|---:|---:|
| Applicable default tests | 358 | 358 | 0 | 0 |
| All native integration tests | 132 | 132 | 0 | 0 |
| Numerical reference checks | 15 | 15 | 0 | 0 |

The six new default and fifteen new native tests are included in these totals;
they are not an additional 21 tests to add. M12 gate-before-arithmetic and rational
small-instance transport checks are included in the attention/default suite.

Commands executed from the measured checkout:

```sh
PYTHONPATH=. uv run --no-project python artifacts/completion-recall-v1/validation/run_suite.py applicable
PYTHONPATH=. uv run --no-project python artifacts/completion-recall-v1/validation/run_suite.py native
PYTHONPATH=. uv run --no-project python artifacts/completion-recall-v1/validation/run_suite.py numerical
```

The runner and complete test-ID inventories, source/test hashes, commands, logs,
start times and outcomes are included under the archive's `validation/` directory.
The native runner uses explicit package-qualified modules; it does not attempt
package discovery through the namespace directory. The applicable default modules
are assembly, attention, native recall, goal PLN, online PLN, pressure, pressure
projection/comparison/audit/planning/planning harness, decision value, decisions,
decision dispatch, probability, probability joint, lifecycle, durable lifecycle,
goal completion and grounded planning. Native coverage includes the existing
admission, adapter, probability, discovery, decision, dispatch, worker, interleaving,
planning and trace integration modules as well as the new service tests.

The broader full default suite was **not rerun** in this increment: 662 of 1,020
available default tests were omitted. `coverage-inventory.json` names them all.
The earlier full default pass (1,014 tests at `0134092`) is historical coverage,
not a current pass. No native dependency was substituted or skipped.

Development history is preserved separately. The first 18-test run had one wrong
boundary assertion; a targeted retry also had one wrong final-stop assertion.
The tests were corrected to distinguish refused protected slots from subsequent
ordinary inspection stopping. The runtime policy, caps and fixtures were not tuned.
Subsequent 19-test and 21-test development runs passed, as did separate 8-run and
2-run semantic-audit preflights. An unqualified system-Python generation command
failed for lack of `pathlib`; the declared uv interpreter was used afterward.
`validation/failures.json`, the original logs and failed-test source copies retain
these events. They are not silently counted as measured passes.

The preservation check compares all 666 previously tracked files outside the
plan/manifest against publication `71c32df`. They and the pinned native build
receipt are unchanged. Prior protocols, corrected and failed runs, review archive
bytes, numerical policies, authority, lifecycle and recovery implementations remain
preserved. The new coordinator lives in separate namespaces.

The full measured semantic audit passed: 192 executions, 1,150 states, 460 frozen
matches, 14,814 independent native answers, 10,648 field steps, 218 persisted
commits and 206 formula recomputations. Five disposable-copy attacks were rejected.
A duplicated raw audit convenience count is retained and explicitly corrected in
`audit-counters.json`: actual control queries are 2,300, not the raw 4,600. This
is a known reporting defect in the frozen audit summary, not a failed reservation
balance check; per-query traces and primary metrics were already correct.
