# Bounded native working memory and fixed gated transport

Measured implementation and auditor: `0134092b9766f8fc9a9a1735cee8b7f2372e830c`.
Protocol preregistration: `b8d3df7`. Initial freeze: `ee21201`.
Native-recall publication `77e30ef`, its measured/auditor source `79f4f43`, prior
reviews, authority code, native helper/build receipts, formulas and policies remain
unchanged. Preservation checks cover 648 old tracked files outside plan/manifest.

This is a bounded session-local Recall → Diffuse → Reason integration. WS-queue
orders native expansion jobs by FIFO; WS-local orders by seeded local allocation;
WS-flow adds four fixed masked microsteps before each expansion. All modes share
public roots, LRU eviction, complete ordered premise bundles, selected-tuple pins,
control obligations, query/tuple/operation budgets, first-discovery FIFO operation
ranking, execution-time full membership checks and hard gates. Activation is never
belief, a certificate, observed relief, or execution value.

## Reproduce and inspect

With the existing pinned AtomSpace/PLN/PeTTa/SWI builds installed as documented in
[ATTENTION.md](../../ATTENTION.md), use a fresh output directory:

```sh
uv run --no-project python -m attention_lab.compare --output /tmp/attention-fresh --audit-after
uv run --no-project python reviews/bounded-attention-v1/verify_review.py
```

The first command runs all 192 primary and 16 separate nonbinding executions and
semantic replay. It writes exact source/configuration copies, public snapshots,
query receipts, all candidate/selection sequences, expansion scores, permits,
allocations, occupancy, native costs, actual formulas/certificates, observations,
SQLite state, JSON reports and a readable comparison. Seed 0; eight engineering
parents, not 192 independent tasks. Formula modes both use real native recall.
Only the distinct complete conformance mode permits the frozen full-frontier
fallback. Tight trials can terminate with explicit bounded-search unknown.

The archive contains `comparison/`, `validation/`, `development/`,
`initial-frozen-attempt/`, and `review/`. Extract into a fresh directory. To replay
its `comparison/` semantically, use the measured checkout and matching pinned
builds with `python -m attention_lab.compare --verify <comparison-directory>`.
The archive verifier checks hashes/inventory without native dependencies; this is
integrity against the published checksums, not publisher authentication. Rebuilt
native binaries may have a different build identity and require a new measured run.

Independent audit compares every typed native answer to a source-record scan,
checks exact candidates/choices at recorded snapshots and histories, reconstructs
allocation with a dense transition reference and ledger, checks nonbinding
Goal-native parity, recomputes selected formulas, verifies persisted certificates,
and replays SQLite. Numerical unit tests additionally use rational references.
External outcomes are observations from the declared small evaluator worlds;
these are not independent real-world deployments or a new general planner oracle.

## Measured results

All **208 corrected executions passed** (192 primary + 16 complete controls).
Across the 64 paired primary settings per comparator, flow has **60 neutral and
4 unfavorable external/certified terminal-loss results, with zero favorable
results**, versus both queue and local. The four unfavorable settings are the
alternatives parent at q48, both capacities and both formula modes. These are
repeated settings of eight parents, not independent statistical trials.

Flow changes initial expansion order in **56/64** pairs and selected operations in
**8/64**. Its additional acquisition work on the shared intermediate does not
produce terminal goal relief. The simple control and the other parents supply
neutral outcomes. The intentionally adverse closed-use geometry remains published
although its corrected terminal losses are neutral across arms. There is no policy
promotion or post-result cap/threshold adjustment.

| Primary arm (64 runs each) | Zero external loss | Total wall seconds | Native queries | Native build-check seconds | Field seconds | Actual formula calls |
|---|---:|---:|---:|---:|---:|---:|
| WS-queue | 20 | 224.857 | 4,236 | 69.614 | 0.004 | 28 |
| WS-local | 20 | 222.507 | 4,236 | 69.583 | 0.004 | 28 |
| WS-flow | 16 | 308.399 | 4,340 | 62.727 | 99.316 | 20 |

These inclusive categories overlap. Lower build-check time for flow comes with
fewer successful trajectories/view replacements, not a faster or cached verifier.
The tiny queue/local field category is timing/branch overhead with zero steps.
Flow executes 11,384 primary microsteps; all controls bring the total to **16,664**.
The largest recorded allocation residual is **6.662e-16**, below the declared
1e-12 tolerance. There are 416 closed-arc evaluations in the complete cohort.

Primary peaks include 36 active entries (under the 48-entry setting), 19,319 encoded
active bytes, 10 pins including 3 control pins, 20 arcs, 41 queued jobs, 20 cached
answer IDs, 20,687 metadata bytes, 8 joint records and 4 native response records.
The separately complete native backing reaches 1,105 atoms/29 source records;
public export reaches 164,889 bytes and native load input 526,976 bytes. Capacity
checks are per run; `validation/profiles.json` contains all settings and phase costs.
`validation/costs.md` is a readable inventory, and `validation/paired-outcomes.json`
contains the full paired operation/outcome sequences and first recall divergences.

For the alternatives parent at c48/q48, the first changed expansion is job 3:
local chooses the positive-target report inspection with score 0.1805, while flow
chooses the negative-target current-support inspection with score 0.1805 after
transport has reduced the positive root's allocation. This alone does not explain
the entire loss difference. The subsequent sequence matters: flow keeps expanding
premise leaves, consumes all 48 native calls and 152 microsteps, visits zero complete
tuples and ends with an empty candidate frontier and loss 10. Queue/local execute
the `c-other` join in their first tranche, retain its exact five-premise candidate,
and select it with first-discovery age 0 and the common semantic FIFO tie-break.
The certified deduction passes, followed by reservation, dispatch, product
observation, health samples and completion; terminal external/certified loss is 0.
They later perform another supported tuple and stop with incomplete remaining
search. Zero goal loss does not imply complete discovery. No stale operation or
contrary observation explains this particular divergence; all its selected
operations pass. The record supports a budget-and-order explanation for this
case, not a universal causal claim from the first changed job.

In contrast, changed-support at c48/q48 records a stale `z-route` request, adoption
of the replacement, and deduction through `outside-new-producer`. Loss remains
10 through inference/reservation/dispatch/product observation. External loss first
falls to zero after health observation; certified loss remains 10 until the required
samples complete. All modes retain the stale/retry costs; there are 12 stale
selections across the full cohort. Monitoring also records wrong-product rejection
and later reopened demand. Pressure/allocation never supplies relief.

Final semantic-audit and regression counts appear in the validation section below.
Flow has shorter elapsed time in 5/64 pairs versus local and 4/64 versus queue;
those descriptive cost results do not establish a quality improvement.
All individual runs, including favorable-by-cost measurements, neutral outcomes
and unfavorable outcomes, remain available; no run is removed for its result.

## Scope and accounting

The complete source export, immutable native projection/catalog and execution-time
full enumeration remain outside the selective workspace. A small working cache
is not a small total system. Encoded payload counts are not physical memory.
Native RSS, physical observation latency, isolated native compute and OS-cache
conditions are unmeasured. Process CPU time and standalone SQLite append/fsync
latency are also unmeasured; numeric commit timing includes persistence and checks.
Native lifetime and repeated pinned-build verification
are unchanged. Inclusive costs overlap and must not be added: field time includes
revision guards and recording; selection includes native view checks. Timings are
one balanced/interleaved exploratory pass, with concurrent regressions and the tail
of the initial cohort overlapping some corrected runs. No uncertainty estimate or
speed/scaling claim is made.

The protocol declares 24/48 active entries, 16/48 queries per decision, finite
response/joint buffers, bounded queues/completeness metadata, arc/candidate bytes,
control pins and separate episode work limits. Both capacities fit a normal exact
five-premise operation. Requery can rematerialize evicted data; forgetting a cache
entry never retracts evidence or an obligation. Only current PASS permits transport;
unknown/unavailable use routes close while inspection stays possible. Partly
explored jobs never become complete absence. Revisions invalidate derived state;
field epochs do not change the native knowledge epoch. M12 gate-before-arithmetic
is exercised; frozen M09/source-duplication protections remain in the regressions.

Deferred: adaptive SPH/bandwidth/density, learned conductance or retention, full
ECAN, pressure/utility changes, native persistence or incremental storage, evidence
supersession, distribution, generalized recovery and large-scale performance claims.
No policy is promoted on conformance alone. Stop at this published bounded slice.

## Failures and corrections retained

- Development attempt 1: 19/21 checks passed. The eviction test indexed an absent
  zero-occupancy metric, and the six-entry bundle boundary reached the query limit
  first. The assertions were isolated with a zero default and a nonbinding query
  budget; both corrected boundary checks passed. A partly explored completeness
  issue found during review was also corrected before the first freeze.
- Development attempt 3 exposed JSON encoding of a set in new history accounting
  (one failure, 11 errors). Canonically sorted attempts fixed it. Attempts 4 and 5
  each passed all 21 focused checks. Logs and relevant source copies are retained.
- A development replay first rejected source drift while documentation and the
  control-only early-service condition were being finalized. Replaying its archived
  source in isolation passed 44 states, 1,781 native query checks, 2,880 field steps
  and 22 matched complete-reference states. It is development evidence only.
- At `ee21201`, the initial declared cohort completed with 196 passing runs and
  12 closed-sink failures. Once product observation satisfied a route precondition,
  the test world had no handler for that now-permitted inspection (`KeyError:
  closed-1`). The correction at `0134092` returns UNKNOWN/no report for that source.
  It adds no evidence or success shortcut. Controllers, budgets, masks, seeding,
  parent structure, operation ranking, formulas and hard gates did not change.
  All 208 executions were rerun; the initial cohort remains archived separately.
- Initial native discovery with `-s integration_tests -t .` failed before any test
  ran because that directory is a namespace directory. Explicit qualified modules
  passed 116 tests at the first freeze. The corrected documentation uses native
  discovery without `-t .`; the final recorded runner uses explicit qualified
  modules. Default discovery retains `-s tests -t .` to preserve mock identity.
- The first frozen default attempt was interrupted after 641 passing checks when
  the fixture defect required a corrected freeze. It is not labeled a full pass.
  A full package-qualified default run was restarted at the corrected source.

## Validation at the corrected freeze

- Full package-qualified default suite: **1,014 tests passed** in 1,363.788 seconds.
- All native integration tests: **117 passed** in 299.193 seconds.
- Existing pressure/lifecycle numerical references: **15 passed**.
- The completed suites have **zero failures, errors or skips**. Start/end source
  and test-file inventories match. Logs include exact inventories and commands.
- Four tamper audits rejected an unsealed trace change and resealed selection,
  allocation and native-answer changes. The original measured bundle was untouched.

The corrected full suites ran at `0134092`; neither the interrupted initial default
run nor the original 12 cohort failures is counted as a pass. No applicable default
or native test file was omitted. Historical recovery tests were executed unchanged.

Semantic audit: **208 executions**, **1120
recorded decision states**, **20,870 independent native
query checks**, **16,664 independently checked field steps**,
**132 matched complete Goal-native states**,
**912 selected operations**, **132
persisted selected commits**, and **108 recomputed formula calls**.
All 208 SQLite reconstructions and finite/native semantic comparisons passed.
The auditor source was unchanged throughout its 464.782-second run.

This closes only the bounded workspace/fixed-transport milestone. Development,
initial failed cohort, correction, full corrected cohort, source inventories and
verification scripts are retained in the single review archive. No automatic
continuation into adaptive transport or generalized recovery is authorized by
this milestone.
