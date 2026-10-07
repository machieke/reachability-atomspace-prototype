# Validation and coverage

Measured implementation/auditor are frozen at
`b509d2b8d7388a570b5a666e1c845b95d207ad20`. The two applicable regression groups ran
once each, serially, before the frozen cohort. Source and selected test hashes
matched before and after both groups. Full receipts retain test IDs, modules,
arguments, elapsed times, logs and wrapper exits.

| Frozen invocation | Passed | Failures | Errors | Skipped | Seconds | Wrapper exit |
|---|---:|---:|---:|---:|---:|---:|
| Applicable default, 25 modules | 462 | 0 | 0 | 0 | 386.689413 | 0 |
| Applicable native, 9 modules | 86 | 0 | 0 | 0 | 164.598893 | 0 |

The new contribution is 23 default and four native tests. It covers complete
AND/OR dependencies, symbolic versus executable work, actual depth two/three,
shared ancestry, missing/unavailable inputs, explicit joint witnesses, wrong order,
phantom IDs, cycles, depth four, graph/session bounds, unchanged refresh and tuple
suppression, descendant invalidation, equal replacement, unrelated survival, rule
changes, new review producers, pending opposing reports, adverse investigation,
copied/converging roots, one-hop parity, the frozen deeper-route boundary, typed
permission rejection and operational control under incomplete numerical work.

Native tests use actual pinned formulas and authoritative AtomSpace projection/
readback. The stale-result unit boundary revokes a leaf between inference and
postcertification. The related retained diagnostic in `validation/late-native/`
holds an actual native result before runtime return, revokes the leaf through the
public API, then permits the result to return on the stale snapshot. Its single
native call cannot commit. This is a forced boundary repeat with full raw evidence,
not another parent structure, cohort run, sensor contract or native retrieval claim.
Its script/hash/source binding are retained separately from the core call totals.

Retained regression groups cover the original bridge and consumer, frozen A/B,
obligations, online numerical service, local joint checks, numerical recovery,
decisions, hard execution gates, dispatch/recovery/races, goal accounting/completion,
lifecycle and the observation-independent world. Model changes, contrary evidence,
exact certificates, copied roots and stale permits retain the old admission rules.
No production policy or recovery implementation changes in this increment.

Reproduce the selected groups into a fresh directory:

```sh
uv run --no-project python -m multihop_lab.validate default --output artifacts/multihop-tests
uv run --no-project python -m multihop_lab.validate native --output artifacts/multihop-tests
uv run --no-project python -m multihop_lab.validate inventory --output artifacts/multihop-tests
uv run --no-project python -m multihop_lab.validate preservation --output artifacts/multihop-tests
```

Explicit omissions: **648 default tests in 47 modules**, **64 native tests in 12
modules**, the separate **15 pressure numerical checks**, and broader unchanged
scheduling/transport, planning and generalized recovery/corpus matrices. Exact
included/omitted module names and test IDs appear in `validation/inventory.json`.
Omissions are not skipped tests: neither executed group skipped a test. Historical
passes are never counted as new passes.

The twelve core executions conform, including unresolved unavailable/adverse cases.
Replay independently enumerates the bounded structure and exact current tuples,
checks complete AND/OR, matches selected operations to the public frontier, replays
the unchanged control/FIFO policy, checks every actual formula and committed record,
reconstructs exact depth/ancestry, validates the fixture joint/source declarations,
and checks physical and admitted-observation histories separately. It verifies
264 public decision/status rows, 162 selections, 30 formula calls including 15 fresh
native calls, 108 physical ticks, 84 product/health measurements, 548 persisted
certificates and twelve executor journals. Replay is not fresh native inference.

Nine isolated altered bundles are rejected: unsealed trace, phantom intermediate,
wrong premise order, forged independent roots, stale descendant accepted, hidden
adverse estimate, partial review marked complete, inference counted as physical
relief, and replay counted as a fresh native call. Exact rejection reasons are in
`validation/negative.json`. The original bundle is never rewritten. Actual opposite
report adoption and a depth-four cutoff falsely marked complete are additional
focused test checks, separate from those nine bundle mutations.

All **797 prior tracked files** outside the plan/manifest remain byte-identical to
`716b4c0`, including every older implementation and review. Both native build
receipts match the immutable previous archive. Selected test sources and hashes,
source snapshots, prior-record preservation checks, suite receipts, the related
late-native diagnostic, raw cohort/audit/mutation records and development evidence
are included in the archive.

[DEVELOPMENT.md](DEVELOPMENT.md) records the initial fixture-launch import error,
formatting/discovery corrections, unfavorable numerical exploration, passing
focused tests and development audits. There were no failed development tests or
semantic audits. The prior publication's exit-143 anomaly and all older failures
remain unchanged; current zero exits do not reinterpret them.

Archive integrity, extracted semantic replay and rejection of an altered archive
are bound in `PUBLICATION.json` after publication. Checksums provide integrity,
not publisher authentication, global probabilistic consistency or real-world safety.
