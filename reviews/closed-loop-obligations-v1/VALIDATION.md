# Validation, omissions and failures

Frozen implementation/auditor: `d2a6b6605eaefc32f0c56e2a7c0d5e9bf11cffb8`.
The applicable suite groups ran once, serially, before the final core cohort.
Source and test hashes were unchanged for both groups.

| Executed suite | Tests | Failures/errors | Skips | Measured elapsed |
|---|---:|---:|---:|---:|
| Applicable default, 23 modules | 421 | 0 | 0 | 199.290 s |
| Applicable native, 7 modules | 79 | 0 | 0 | 91.985 s |

These 500 tests include 20 new finite and four new native consumer tests. Existing
bridge, frozen A/B, online sessions, numerical decisions, probability provenance /
recovery, dispatch safety/reconciliation/races, execution, goal accounting,
durability, lifecycle and native adapters remain covered. Native regression tests
include the old twelve-case online suite; those calls are not added to the new
core-cohort native call count.

The default tool wrapper reported exit **143** after writing the complete 421-test
`OK` log and complete passing JSON receipt. Its cause is not established. This is
an invocation-wrapper anomaly, not a hidden test pass: every counted test has a
recorded result and the source/test hash checks completed. It is preserved in
`validation/default-wrapper.json`; the suite was not repeated. The native wrapper
exited zero. Do not describe both command invocations as clean exits.

Explicitly omitted: **648 default tests in 47 modules**, **64 native tests in 12
modules**, the separate 15 pressure numerical checks, and pressure/attention /
transport controller matrices. Existing dispatch safety race regressions were run;
no new broad scheduling comparison was added. The exact selected and omitted test
IDs/modules are in `validation/inventory.json`. No historical coverage is claimed
as a new pass and this is not a full-repository suite claim.

Focused checks include actual observation → adoption → certified inference →
reservation/dispatch → correct product/health → observed completion; one shared
operation for two obligations; retained weak-parent and adverse blocks; unavailable
and copied/unclassified reports; unknown-source adoption rejection; equal-valued
replacement; exact model-parent non-rebinding; registry race rejection; new review
work after reservation; duplicate reads/unrelated ticks; matched-state mandatory
source perturbation; malformed/deeper/bound-exhausted views; typed work/B rejection;
headroom for monitoring; and reconciliation of an uncertain action without another
effect. Wrong product, missing health and later unhealthy reopening are related
boundary continuations of the positive parent, not new independent cohort tasks.

All core operations are consumer-selected. Setup only admits initial reports and
registers capabilities; its formula-call count is zero. The environment supplies
actual source responses and explicitly recorded clock/opportunity/registry events.
Raw acquisition responses and adopted numerical supports are separate records.
Full current evidence, including contrary/unclassified records, is retained.

The semantic audit reproduces frozen A/B and the exact work graphs, independently
checks obligation witnesses/AND/OR routes and numerical predicates, reproduces
public candidates and FIFO selection, checks selected receipts/certificates and
charged budgets, and reconstructs all twelve final authoritative SQLite states.
Selected accepted numerical commits must occur in those journals. Recorded native
arithmetic is checked against the pinned finite implementation; replay is not a
fresh native call or an independent environmental ground-truth oracle.

The final cohort/audit passes all twelve episodes: 66 work/status rows, 54 selected
operations, 14 formula calls (seven fresh native calls) and two stale-request
rejections. Four executions reach observed completion; the other eight retain
their declared unresolved outcomes. A focused receipt checker independently
reconstructs all 54 current-frontier revalidations, matches all 22 actual source
responses and all 14 ordered formula inputs, and reopens all twelve simulated
executor journals to check effects. Its source and result are archived as
`validation/receipt_checks.py` / `receipt-checks.json`.

All eight isolated mutations are rejected: unsealed evidence, missing AND slot,
skipped review, changed selected tuple, hidden objection, stale acceptance,
invented relief and removed adoption. Mutation copies are separate from the
measured evidence. Exact replay is accompanied by independent semantic and
receipt checks; it is not claimed to establish real-world truth or safety.

Preservation checks pass for all **743** prior tracked files outside the current
plan/manifest, including previous reviews, corrections, source-bound archives,
role mappings and coverage omissions. Both pinned native build receipts are
byte-identical to the prior bridge publication.

Development evidence is archived separately. Four initial episodes stopped before
any selection because of duplicate selector IDs; the committed correction keeps
identical intended eligibility and requirements with distinct selector aliases.
One later blocked-episode checker raised a field-path KeyError despite the correct
blocked trajectory; fixing its read did not alter behavior. Raw failed runs,
source copies, original task declaration, corrected test passes, first development
cohort and its audit are retained. Development passes/calls are not added to final
counts. See [DECLARATION-CORRECTION.md](DECLARATION-CORRECTION.md).

Commands for a fresh run:

```sh
uv run --no-project python -m work_loop_lab.validate default --output artifacts/work-loop-validation
uv run --no-project python -m work_loop_lab.validate native --output artifacts/work-loop-validation
uv run --no-project python -m work_loop_lab.validate inventory --output artifacts/work-loop-validation
uv run --no-project python -m work_loop_lab.validate preservation --output artifacts/work-loop-validation
uv run --no-project python -m work_loop_lab.compare run --output artifacts/work-loop-local
uv run --no-project python -m work_loop_lab.compare audit artifacts/work-loop-local
uv run --no-project python -m work_loop_lab.negative artifacts/work-loop-local --output artifacts/work-loop-validation/negative.json
```

The separate publication receipt records package integrity, extracted semantic
replay and an altered-archive rejection. Raw suite logs and exact source inventories
are inside the archive. Unsupported persistent interruption/resume, broader proof
planning and generalized recovery remain outside this increment.
