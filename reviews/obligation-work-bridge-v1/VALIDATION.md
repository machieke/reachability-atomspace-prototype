# Validation and preserved failures

Implementation/auditor: `2322512c61f3ff387abcb402f1638c25b92f9add`.
Task/sequence preregistration: `45fb871863025f282df36a74ba5810fe6a826616`.
Each applicable suite ran once at this frozen revision; source/test hashes stayed
unchanged. Default, native and final cohort runs were serial.

| Final executed group | Tests | Failures/errors | Skips | Elapsed |
|---|---:|---:|---:|---:|
| Applicable default | 346 | 0 | 0 | 81.124 s |
| Applicable native | 74 | 0 | 0 | 63.442 s |

The 420 tests include 14 new finite and two new native bridge tests. Existing
shadow evaluator tests, online PLN, numerical decisions, probability/recovery,
execution hard gates, goal/lifecycle accounting and native adapter tests remain
applicable. Full exact module/test IDs and source hashes are in the bundle's
`validation/default.json`, `native.json` and `inventory.json`.

Explicitly omitted: **703 default tests** in 50 modules, **65 native tests** in 13
modules, the separate 15-check pressure numerical script, and large controller /
transport scheduling matrices. No old pass count is presented as new evidence.
The omitted tests concern unchanged planners, pressure/transport, broader recovery,
corpus and other integration surfaces. This is not a full-repository coverage claim.

The final cohort contains six finite parent sequences and two native reconstructions
of those parents: 27 authoritative prefix captures, five labeled input diagnostics,
and 42 role/prefix views. All 37 supported views are complete explanations; all
five diagnostics are explicitly incomplete. Neither state means executable or
observed goal completion. Counted across repeated views: 374 nodes, 389 edges,
50 operation occurrences and 88 obligation occurrences. These are not independent
samples, distinct executions, new goal demand or pressure units.

Independent validation includes hand-declared per-prefix obligation/status/reason
tables, independently constructed semantic IDs and literal requirements, all
coherent alternative tuples, exact AND slots, OR references, frozen witness sets,
full objections and actual lifecycle/goal projection. Tests cover repeated reads,
role-preserving permutation, shared operations, copied sources, missing mandatory
presence, inadequate alternatives, revocation/replacement, stale real intents,
new/revised producers, unknown/unavailable probes, required observation preconditions,
malformed/non-finite/partial inputs, every graph bound and explicitly unexpanded
deeper inference. No graph traversal performs native arithmetic.

Shadow work objects fail real typed permission/registration APIs without authority
mutation. A/B outputs exactly reproduce frozen evaluators; independent predicates
also verify their numerical results. Numerical satisfaction cannot create goal
relief, execute an action or remove a live all-current block. Entire captured data
and actual projection state remain separate from the narrow graph.

Audit reconstructs all eight final SQLite authorities. Eight actual cohort formula
calls are recorded, of which three are fresh native PeTTa/PLN calls. Existing
AtomSpace projection/reopen checks preserve authority and run no extra formulas.
Replay checks recorded arithmetic with the pinned finite implementation; replay is
not labeled new native execution. All eight isolated mutations are rejected:
unsealed change, missing AND dependency, duplicate obligation, hidden objection,
hidden live block, invented relief, removed route and changed inventory.

Preservation checks pass for **717** prior tracked files outside the plan and
manifest, including frozen A/B source, previous archive, historical counterfactual
assignments, corrections and omitted-coverage records. Native build receipts also
remain unchanged.

Development failures are retained under `development/` in the archive. The two
native tests each failed in two early runs because the input identity included an
internal pickle-based nonmutation receipt. Authoritative/public records and the
native projection were identical; heap serialization differed after reopen.
The proof was moved to diagnostic acquisition receipts, leaving semantic inputs
bound to actual records. Both native tests then passed. One configuration import
had an unmatched parenthesis and executed no cohort; its source/log is preserved.
No numerical rule, task role, value, threshold or live gate was changed to fix these
issues. Development passes are not additional final passes.

Commands (fresh validation/output directories):

```sh
uv run --no-project python -m work_bridge_lab.validate default --output artifacts/work-bridge-validation
uv run --no-project python -m work_bridge_lab.validate native --output artifacts/work-bridge-validation
uv run --no-project python -m work_bridge_lab.validate inventory --output artifacts/work-bridge-validation
uv run --no-project python -m work_bridge_lab.validate preservation --output artifacts/work-bridge-validation
uv run --no-project python -m work_bridge_lab.compare run --output artifacts/work-bridge-local
uv run --no-project python -m work_bridge_lab.compare audit artifacts/work-bridge-local
uv run --no-project python -m work_bridge_lab.negative artifacts/work-bridge-local --output artifacts/work-bridge-validation/negative.json
```

Official output is under `artifacts/work-bridge-v1`. Package integrity, safe
extraction/replay and an altered-archive rejection are recorded in the separate
publication receipt. Integrity is not publisher authentication or empirical safety.
