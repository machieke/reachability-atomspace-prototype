# Validation receipt and limits

Implementation and auditor frozen at `5161e19b73f89676edf0b9f772200c12eee02ef1`.
Each applicable suite ran once at this revision; source and test hashes were
unchanged throughout. The suite groups and publication cohort ran serially.

| Executed group | Tests | Failures/errors | Skips | Elapsed |
|---|---:|---:|---:|---:|
| Applicable default | 314 | 0 | 0 | 49.685 s |
| Applicable native | 72 | 0 | 0 | 63.795 s |

The 386 executed tests include 15 new finite shadow tests and five new focused
native/historical tests. Actual native tests are not finite substitutions. The
new checks cover independent Boolean tables, real certified inputs for every
Boolean witness pattern up to three reports, all 64 three-check precedence
combinations, interval/confidence boundaries, exact live-policy parity, copied
lineage, missing methods, parent/child coexistence, low-confidence objections,
revocation/replacement, stale existing intents, scope/completeness/bounds and
nonmutation. Shadow PASS objects fail the real typed registration/permission APIs;
unchanged live all-current failures remain UNKNOWN in real reservation attempts.

The comparison has 54 pairs, 90 independent reference checks for the 45 complete
pairs, 95 B record inspections and 57 B witness occurrences. Reused snapshots and
role variants contribute repeated inspections; these counts are not independent
observations. Audit reconstructs all 14 final SQLite ledgers, checks seven new
cohort formula calls (three native), and exact before/after evidence and goal
records around adverse inference. All results conform to their declared rules.
All six isolated audit mutations are rejected, including resealed status/witness
changes, changed role assignment, omitted record and dropped pair.

All 689 files tracked at publication `3d84c66`, except the explicitly mutable plan
and implementation manifest, remain byte-identical. The previous archive, its raw
and corrected evidence, and its reporting correction are preserved.

Executed default modules: `test_obligations`, `test_decisions`, `test_decision_demo`,
`test_decision_dispatch`, `test_probability`, `test_probability_joint`,
`test_probability_recovery`, `test_execution`, `test_durable_execution`,
`test_dispatched_goals`, `test_goals`, `test_durable_goals`, `test_goal_coverage`,
`test_goal_oracles`, `test_goal_completion`, `test_lifecycle`, `test_durable_lifecycle`.
Executed native modules: `test_obligations`, `test_decisions`,
`test_probability_service`, `test_native_adapters`.

**Omitted, not newly passed:** 721 default tests in 51 modules; 65 native tests in
13 modules; the separate 15-check pressure numerical script; large scheduler and
transport comparison matrices. The exact complete executed and omitted test IDs,
module lists and source hashes are in `validation/inventory.json`, `default.json`
and `native.json`. Omitted coverage concerns unchanged planners, pressure/transport,
broader corpus/recovery and other integration surfaces. Historical test counts are
not recycled as new evidence. This is an applicable boundary regression pass, not
a new full-repository coverage claim.

Reproduction commands used:

```sh
uv run --no-project python -m obligations_lab.validate default --output artifacts/obligations-validation
uv run --no-project python -m obligations_lab.validate native --output artifacts/obligations-validation
uv run --no-project python -m obligations_lab.validate inventory --output artifacts/obligations-validation
uv run --no-project python -m obligations_lab.validate preservation --output artifacts/obligations-validation
uv run --no-project python -m obligations_lab.compare run --output artifacts/obligations-local
uv run --no-project python -m obligations_lab.compare audit artifacts/obligations-local
uv run --no-project python -m obligations_lab.negative artifacts/obligations-local --output artifacts/obligations-validation/negative.json
```

The official publication directories are `artifacts/decision-obligations-v1`.
The archive preserves exact logs and receipts. `development/DEVELOPMENT.md` records
all development failures: three initial test assertions (wrong revocation ID and
two overbroad goal-view equality checks), one auditor indentation error, and an
insufficient unchanged-observation flag in the first development cohort. The
corrected official adverse case compares exact complete evidence lists and actual
goal observations around only the deduction. Earlier data and failure sources
are retained; no role mapping, numerical value, threshold or production gate was
changed to obtain passing results. Development passes are not extra official runs.

Final check review also found an inaccurate A confidence-check label when strength
failed but confidence met its floor. A new regression failed on `81a648a`; the
corrected source `5161e19` checks confidence independently. Overall cohort judgments
and all thresholds are unchanged. The earlier 314/72 pass and archive are preserved
as a superseded prerelease under `development/superseded-81a648a`; they are not extra
passes at the final source. The final applicable suites and cohort were rerun once
at the corrected frozen revision.

Package integrity verification and an altered-archive rejection are recorded in
`PUBLICATION.json`; semantic audit of the safely extracted bundle is recorded there
as a separate check. Integrity is not publisher authentication or empirical safety.
