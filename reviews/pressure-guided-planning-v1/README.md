# Bounded planning with pressure used only for search order

The shared planner reduces external-loss gaps against the direct queues once it
has enough search. Pressure guidance does **not** justify its additional cost
against neutral ordering on this cohort. At 64 attempts on the new parents,
neutral has mean episode gap **0.500**, B0 ordering **0.833**, and pressure ordering
**0.875**, versus **9.208** for direct B0 and **12.500** for direct normalized B3.
Neutral also uses less query time. Favorable, neutral and unfavorable pressure
results are retained below; no policy is promoted.

The accepted comparison and full replay audit **PASS**: 2,328 closed runs,
444 common states, 6,884 closed-loop planner queries, 117,179 visited STOP closures
and 7,392 certified operations. There were no harness failures or replay mismatches.
The run phase took 2,044.637 seconds, replay 1,807.854 seconds, and the complete
command 3,858.447 seconds. These include evaluator/recording work; per-controller
costs are reported separately. No measurement correction or rerun was needed.

## Revision and reproduction

The planner, protocol, twelve new parents, budgets, sampling and policy-free
calibration were committed at `a7e5d00b38648147a9bbcc0afa6a2adc7b6c2e56` before
measurement. Measurement source is **`4be809163b93a9cb5a0408a34bc9fff68dfb2816`**:
a pre-measurement follow-up tightened full-configuration audit binding and added
the generated readable comparison. It changed no planner, orderer, case, budget
or calibration. There was no policy-based case replacement or parameter tuning.

Preserved versions remain distinct: runtime `3e8fd7b`, scoped projection
`8542ad5`, corrected decision harness `7bf11d5`, and decision-value publication
`2dfe184`. All 21 prior review files, including accepted and failed artifacts
inside their archives, are hash-bound and unchanged.

From the measurement revision in a repository checkout, this one command creates
a fresh comparison directory, runs every declared cell and audits the result:

```bash
uv run --no-project python -m validation_lab.planning_comparison --output artifacts/planning-review-reproduction
```

The destination must not exist. The command writes `comparison.md`, `summary.json`,
configuration and source hashes, independent reference labels, per-query search
records, decision traces, actual authority journals, costs and audit results.
It takes sustained execution; it is not a cached-reference lookup. Reproduction
of attempt-limited semantic results is deterministic within the declared safety
bounds. Historical wall-limited traces and durations are machine-load-sensitive.

The archive descriptor is `ARCHIVE.json`; `SHA256SUMS` binds its physical files.
If repository size limits require numbered parts, the verifier checks and
reassembles them internally as one logical archive without extracting it.

Archive integrity and offline semantic replay are separate checks:

```bash
uv run --no-project python reviews/pressure-guided-planning-v1/verify_review.py
uv run --no-project python -m validation_lab.planning_comparison --audit-only EXTRACTED_REVIEW/comparison
```

Run semantic replay from the source checkout. The verifier checks the published
archive checksum and every member without extracting it; it does not authenticate
the publisher. The archive includes source snapshots and provenance; the checkout
provides the Git history used to verify the committed source bindings.

## Contract and coverage

The same production-side explicit-stack DFS serves PLAN-neutral, PLAN-B0-order
and PLAN-pressure-order. Neutral uses stable semantic action order; B0 uses its
frozen priority rule; pressure uses frozen normalized `both` scores at every
speculative state. Only child order differs. There are no transpositions,
heuristic pruning, rollouts, oracle lookups or oracle stopping conditions.

Every prefix is closed with STOP and charged for all unresolved loss through
horizon 16. The primary objective is integrated external loss. Equal-primary
incumbents use terminal monitored/certified loss, work, requests and then action
sequence. Monitoring consumes its real request, operation and observation costs.
Hypothetical supports/monitoring are predictions, not authority handles or relief.
Only the first selected operation is resolved against the exact live frontier
and executed through the unchanged certified interfaces. A compatible observed
receipt permits an in-memory suffix; all its remaining steps are revalidated.
No commitment, reservation or recovery mechanism was added.

The primary matrix has 66 inspected old tasks (48 parents and 18 paired
diagnostics), 12 new parents, two semantic budgets, two direct controls, and
three orderers at 1/4/16/64 attempted transitions: **2,184 runs**. The new parents
also receive the three orderers at policy-free calibrated per-query wall caps
of **5 ms and 21 ms**, adding **144 runs**. All use seed 0 and the same permanent
static public contract. The six families have two new parents each. Old
confirmation labels are historical; all old cases are inspected diagnostics.

There are **444 identical-state samples / 6,714 queries**, and **2,328 closed
runs / 7,392 actual operations**. All actual requests return PASS. This says
nothing about whether every goal was completed: unresolved external and
uncertified loss remain in the results. Goal failures and bound hits are not
reclassified as harness failures. Every reference cell passes DP/enumeration
agreement; no case was swapped or censored for a reference-bound failure.

The [protocol](PROTOCOL.md), [input inventory](inventory.json),
[calibration](calibration.json) and [reference-only feasibility](feasibility.json)
are immutable inputs. The accepted data retain task/parent/family, old/new,
semantic budget, arm, search cap, observations, scores, requests and costs.
Parent tables exclude siblings and pool the two budgets equally. Decision-regret
means count the preregistered common states; these are not independent parents.

## Separate planning benefit from guidance benefit

Lower episode gap and decision regret are better. Episode gap is total actual
external loss minus the initial reference optimum. Decision regret compares a
selected action with the optimal continuation at that observed state; overlapping
regrets are **not** summed as a causal explanation. Query time excludes the
separately charged common discovery, which is identical within a sample.

| Cohort | Policy | Mean episode gap | Worst gap | Mean decision regret | Mean query ms |
| --- | --- | ---: | ---: | ---: | ---: |
| old-inspected | B0 | 4.812 | 42 | 1.699 | 0.493 |
| old-inspected | B3-normalized-both | 5.229 | 48 | 1.315 | 1.519 |
| old-inspected | PLAN-neutral-n1 | 37.479 | 97 | 18.457 | 1.050 |
| old-inspected | PLAN-B0-order-n1 | 43.115 | 118 | 20.261 | 1.363 |
| old-inspected | PLAN-pressure-order-n1 | 41.490 | 118 | 18.058 | 2.666 |
| old-inspected | PLAN-neutral-n4 | 1.583 | 52 | 0.587 | 2.331 |
| old-inspected | PLAN-B0-order-n4 | 1.781 | 27 | 0.649 | 3.060 |
| old-inspected | PLAN-pressure-order-n4 | 2.573 | 48 | 0.457 | 6.454 |
| old-inspected | PLAN-neutral-n16 | 0.615 | 11 | 0.207 | 4.255 |
| old-inspected | PLAN-B0-order-n16 | 1.188 | 14 | 0.399 | 5.885 |
| old-inspected | PLAN-pressure-order-n16 | 0.896 | 14 | 0.239 | 12.093 |
| old-inspected | PLAN-neutral-n64 | 0.167 | 6 | 0.058 | 7.143 |
| old-inspected | PLAN-B0-order-n64 | 0.469 | 12 | 0.134 | 9.497 |
| old-inspected | PLAN-pressure-order-n64 | 0.323 | 12 | 0.087 | 22.032 |
| new | B0 | 9.208 | 56 | 2.988 | 0.574 |
| new | B3-normalized-both | 12.500 | 65 | 4.012 | 1.616 |
| new | PLAN-neutral-n1 | 56.833 | 102 | 27.120 | 0.964 |
| new | PLAN-B0-order-n1 | 56.500 | 117 | 23.349 | 1.289 |
| new | PLAN-pressure-order-n1 | 56.250 | 117 | 25.157 | 2.557 |
| new | PLAN-neutral-n4 | 3.917 | 42 | 1.157 | 2.256 |
| new | PLAN-B0-order-n4 | 3.583 | 12 | 1.060 | 3.075 |
| new | PLAN-pressure-order-n4 | 5.458 | 52 | 0.940 | 7.167 |
| new | PLAN-neutral-n16 | 0.542 | 8 | 0.169 | 4.611 |
| new | PLAN-B0-order-n16 | 1.917 | 8 | 0.554 | 6.969 |
| new | PLAN-pressure-order-n16 | 1.583 | 8 | 0.494 | 15.678 |
| new | PLAN-neutral-n64 | 0.500 | 8 | 0.145 | 10.580 |
| new | PLAN-B0-order-n64 | 0.833 | 8 | 0.241 | 15.354 |
| new | PLAN-pressure-order-n64 | 0.875 | 8 | 0.253 | 37.387 |

At one attempted transition, all planners perform poorly on multi-step tasks:
a promising unfinished branch does not beat a properly charged STOP incumbent.
This is a negative result, not free future completion. At 64 attempts on the new
24 parent/budget cells, each planner beats direct B0 in **13**, ties in **11**,
and loses in **0** cells. The gain from evaluating complete sequences is not
evidence that pressure supplied that gain.

At 64 attempts, pressure versus neutral is **2 favorable / 89 neutral / 5
unfavorable** on old parent/budget cells and **0 / 21 / 3** on new cells. Pressure
versus B0 ordering is **4 / 92 / 0** on old cells and **1 / 22 / 1** on new cells.
Thus pressure sometimes helps this search skeleton, but neutral has lower mean
gap and lower cost in both cohorts. This conclusion concerns the tested `both`
orderer, not every possible pressure heuristic.

The bounded trees do not all collapse to identical exact answers at 64 attempts.
On the new roots, neutral finds a primary-optimal witness in **21/24**, B0 ordering
in **18/24**, and pressure in **19/24**. Among successful roots only, median work
to the first primary-optimal witness is **4, 4 and 6 attempts** respectively;
median elapsed time is **2.669, 3.663 and 8.910 ms**. These conditional medians
exclude roots still censored by the search cap; they are not unconditional time
to optimality. Runtime search never sees the reference label or stops on it.

All fixed-root attempt-ladder primary incumbents are non-worsening. All tested
parent closed-loop cap increases also improve or tie, but this observation is
not a general monotonic-episode guarantee. Replanning can improve a root plan,
so root plan gap and final episode gap remain separate. For example, new B0-order
at 64 attempts has mean root gap 1.000 and episode gap 0.833.

Guidance changes actual visited branches, not just displayed scores. At 4
attempts, pressure expands a different semantic-state set from neutral in
**241/444** samples and from B0 ordering in **69/444**. At 64, these are **38/444**
and **18/444**; expanded order differs in **275/444** and **136/444** respectively.
At one attempt only the root is expanded; child visits and chosen closures still
can differ. Full ordered prefixes, rather than just set hashes, remain in traces.

## Equal nominal wall caps and actual cost

The wall caps came from 100 policy-free model/frontier/transition repetitions,
with ten warmups, before policy measurement. They were not selected using arm
outcomes. Arm order rotates; these are single engineering measurements without
confidence intervals or a timing-significance claim.

| New cases: per-query cap | Neutral mean gap | B0-order mean gap | Pressure-order mean gap |
| --- | ---: | ---: | ---: |
| 5 ms | 10.792 | 28.458 | 57.375 |
| 21 ms | 0.500 | 1.583 | 2.208 |

At 5 ms pressure versus neutral is **0 favorable / 5 neutral / 19 unfavorable**;
at 21 ms it is **0 / 16 / 8**. Pressure versus B0 ordering is **1 / 10 / 13** and
**3 / 15 / 6** respectively. These include neutral and favorable pressure results,
but do not establish a cost advantage. Atomic model/rank work is checked at
boundaries: actual time can exceed the nominal cap. Across 595 closed-loop wall
queries, the maximum overrun is **6.546 ms**, and the mean nonnegative overrun
including zero-overrun queries is **0.220 ms**. No episode hit the 30-second real
session cap. Historical wall prefixes are replayed semantically, not timed anew.

Mean costs below are milliseconds per **new-cohort closed episode**. Candidate
discovery includes both live and speculative enumeration. Ranking excludes the
separately shown pressure phases and includes other model/search/suffix work.
Execution is an inclusive category in the raw files and must not be added again
to inference, certification, persistence and authority bookkeeping.

| Policy | Discovery | Other ranking/model | Pressure build | Pressure solve | Inference | Certification | Persistence | Controller | Total incl. setup/tail |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B0 | 1.340 | 2.414 | 0.000 | 0.000 | 0.388 | 85.825 | 169.292 | 479.781 | 872.742 |
| B3-normalized-both | 1.529 | 0.529 | 6.656 | 7.455 | 0.371 | 83.510 | 166.382 | 482.666 | 870.750 |
| PLAN-neutral-n64 | 39.001 | 39.549 | 0.000 | 0.000 | 0.331 | 69.641 | 160.228 | 518.564 | 904.347 |
| PLAN-B0-order-n64 | 34.825 | 60.156 | 0.000 | 0.000 | 0.338 | 72.991 | 159.648 | 536.998 | 919.596 |
| PLAN-pressure-order-n64 | 31.811 | 56.377 | 51.891 | 48.414 | 0.337 | 67.940 | 156.377 | 611.759 | 994.762 |

Detailed counters retain enumeration and frontier consistency checks, transition
validations/rejections, sorting, B0's extra optimistic search, normalization,
pressure iterations/edge visits, interrupted expansions, memory accounting and
suffix validation. Consistency timing inside enumeration, transitions, B0 or
graph construction belongs to that measured phase; it is not separately timed.
Model validation and post-receipt suffix checks have additional timing fields.
These are nested measurements, not extra additive costs.

There are **6,884 closed-loop planner queries**: **3,784 complete searches** and
**3,100 exhausted searches** (2,804 attempt-cap hits, 296 wall hits). No recorded
model/ranker/field safety-cap failure occurred. Suffix status is absent on 2,016
initial queries and validated on 4,868 subsequent queries. Maximum per-query
conservative memory accounting is **715,488 bytes**; this is not measured RSS.
Actual peak RSS, OS scheduling attribution, per-fsync/byte costs, real sensor
latency and an isolated timing for every consistency subcall are unmeasured.
No GPU is used. Setup, evaluation tail, trace I/O and total elapsed remain visible.

The lower primary loss does not imply more monitored completion. On new cells,
mean terminal external/certified losses are **1.792/2.500** for direct B0 and
**1.375/2.792** for each 64-attempt planner. Those remaining uncertified
obligations are retained. The primary objective was not changed to hide them.

## Recorded sequence diagnostics

* **Premature monitoring, depth-2, tight budget.** Direct B0 requests
  `r1,r2,r3,monitor/g0` and loses 44; direct B3 requests
  `r4,monitor/g1,r1,r2` and loses 66. The first B3 choice is favorable under the
  independent continuation labels; it does not explain the entire difference.
  Pressure planning at four attempts still loses 66, whereas neutral/B0 planning
  lose 20. At 16 attempts pressure finds `r4,r1,r2,r3`, loss 18; neutral/B0 remain
  at 20. At 64 all three lose 18. Later decisions, available budgets and complete
  continuations matter; decision regrets are not added as causal credit.
* **An unfavorable new case, new-completion-0, wide budget, 64 attempts.** Both
  neutral and pressure first select `derive/r0`. Its reference Q is 11 versus
  optimal value 10. Neutral then derives `r1`; pressure selects `monitor/g0`
  before deriving `r1`. At that identical state, deriving `r1` has Q=4 and
  monitoring has Q=8. Pressure's candidate ranks are monitor/g1=-2.55,
  monitor/g0=-1.70, derive/r1=-1.22825, derive/r2=-0.614125 (lower ranks first).
  Yet the returned incumbent selects monitor/g0, illustrating that scores order
  search rather than choose the final plan. The retained feasible plan has
  remaining value 8 versus neutral's 4. All requests PASS; there are no stale
  requests. The additional tick delays the remaining loss-4 goal and accounts
  for the paired episode loss **15 versus 11**. Both already share a separate
  one-unit gap from their common first action; the final five-unit pressure gap
  must not all be blamed on that first choice.
* **All orderers can miss the better route.** In new-depth-0 with the wide budget,
  all 64-attempt planners take `r0,r1,r2,r3`, then monitor both goals: loss **22**
  versus optimum **14**. Every goal ends supported and monitored, but later
  relief costs eight units of integrated loss. The declared search cap remains;
  the experiment was not expanded until an orderer won.
* **External relief versus certification.** In depth-0 with the tight budget,
  the 64-attempt planners take the immediate cost-4 proof, achieving loss **4**
  with terminal uncertified loss **4**. Both direct controls take the two cheap
  proof steps and monitor, losing **8** but ending with uncertified loss **0**.
  This is the declared objective tradeoff, not certified success without a sample.
* **Dominated-route sensitivity remains.** Adding the costlier parallel route to
  budget-0 leaves the reference optimum **22** (tight) / **8** (wide) unchanged.
  Direct B3 losses change **22→97** / **9→19**; direct B0 is unchanged. Pressure
  planning at one attempt inherits that sensitivity. Four attempts recover 22
  in the tight case but still lose 19 in the wide case. At 64 all three planners
  recover 22/8 for both parent and sibling. Normalization and source accounting
  were not altered to erase the diagnostic.
* **Impossible AND remains blocked.** In and-6, the 64-attempt planners derive the
  feasible side goal and monitor it, losing the optimal **49** while retaining
  the blocked goal's uncertified loss **3**. The forbidden prerequisite is not
  admitted. The budget-2 unaffordable continuation and shared-0 shared-prerequisite
  histories are also retained in the machine-readable diagnostics.
* **Identifier order is a limitation of neutral too.** At 64 attempts, identifier
  permutation changes neutral loss by -1 on or-6/wide, +3 on depth-1/wide and +4
  on depth-6/wide. B0-order and pressure-order losses are unchanged in these
  paired identifier cases; direct B0 still changes by +13/+2 on shared-6.
  Neutral's better cohort average is not an invariance or universal-superiority
  claim. All sibling reference optima remain unchanged.
* **Simple control.** All arms on completion-0 lose **1** and execute the same
  proof and monitor, ending with zero external and uncertified loss. Search and
  pressure computation add no outcome benefit here.

The complete per-step observations, scores, Q labels, selected operations,
status replies and outcomes remain in the archive. `summary.json` beside this
README is a compact descriptive view; the archive's `comparison/summary.json`
contains the complete original aggregate rows. `summarize_review.py` derives
the publication view without changing any policy input or source data.

## Validation, omissions and limits

* **252 applicable regression tests passed** at `a7e5d00`, in 330.059 seconds
  including process startup; no failures, errors or skips. This includes the new
  model/planner tests and applicable admission, deployment, hard gates, goals,
  resources, pressure/source duplication/M09, projection and decision-harness
  suites. Production model successors/losses/budgets are checked against every
  reachable reference state in all 78 tasks at both budgets. Complete-search
  witnesses for all three orderers are checked against the independent reference
  on the predeclared existing hand cases.
* **15 standalone numerical reference checks passed** at that revision. Their
  unchanged field code is also the measurement code.
* **3 audit-binding/wiring tests passed** at `4be8091`, in 10.241 seconds including
  startup, after the pre-measurement audit-only follow-up. They include rejection
  of changed search limits under the same arm name and actual execution/replay
  of every orderer at attempt and short wall caps. The model/search/controller,
  fixed policies, cohort, calibration and semantic budget bytes are unchanged
  from the 252-test revision. These are separate executions, not 255 unique tests.
* All four deliberately faulty variants are detected: free unfinished completion,
  omitted monitoring cost, omitted remaining-budget state, and pressure-selected
  final incumbent. Mutants are never legitimate comparison arms.
* Stale first requests and hypothetical references are rejected in tests; read-only
  planning cannot append evidence, alter beliefs, certify goals or create relief.
  Unsupported dynamic models fail explicitly. Exhaustion does not prove no route.
* The full default/native suites were **not rerun**. Exact omitted default modules
  and native test files are listed in `regressions/omissions.json` in the archive.
  No native, generalized recovery or frozen authority interface changed. Historical
  full-suite counts remain historical, not evidence from this increment.

This is a twelve-new-parent engineering confirmation set with inspected old
diagnostics, not a statistical generalization, scaling result or full benchmark.
The static guarantees do not extend to revocation, hidden events, probes,
commitments, uncertain durations or proof-identity-sensitive permissions.
Pressure uses only the historical normalized `both` orderer. No equation,
normalizer, learned conductance, adaptive transport, native numerical PLN
scheduler, recovery automation or new objective was added. M12 stays deferred
with transport. This increment stops at the audited publication.
