# Frozen B0/B3 review

The implementation and original development episodes are frozen at
`3e8fd7be56362ed21944636bbe505b6a4a7aac6f`, tagged
`b0-b3-freeze-2026-10-02`. The separate diagnostic tools and
[predeclared protocol](PROTOCOL.md) are at
`54db172ff760f089476d9642118ccbc52044bc17`. No original runtime, episode, budget,
pressure limit or authority gate changed.

Download [review.tar.gz](review.tar.gz) and verify [SHA256SUMS](SHA256SUMS).
This one archive includes the original comparison, complete logs and source
snapshots, actual traces and journals, decision analysis and separate ablations.
The self-contained file inventory in `review.json` binds every included artifact.

## Frozen regression and comparison evidence

All applicable suites ran once in a clean detached worktree at the frozen commit:

| Suite | Tests | Result | Suite elapsed seconds |
| --- | ---: | --- | ---: |
| Full default regression suite | 912 | PASS; no failures or skips | 1122.555 |
| Full native integration suite | 85 | PASS; no failures or skips | 157.272 |
| Standalone numerical references | 15 | PASS; no failures or skips | See complete log |

No frozen suite was retried, trimmed or repaired. The native run used the pinned
build receipt and dependencies documented in `ADAPTERS.md`. Platform, interpreter,
commands, return codes, times and log hashes are in `regressions.json` inside the
archive. The nine new diagnostic-tool tests passed separately; they are not
included in the frozen suite counts.

The original 32-run comparison passed, with a clean working tree. Its source-bound
audit reproduced 155 selected operations and verified all 71 source inputs against
the frozen commit. M09 was detected. The comparison retains both seeds, all four
original configurations, every operation reply, outcome and measured cost.
Recorded timing is not authenticated or remeasured by replay.

## What the rich-episode sequences show

Under work-16, both seeds give B0 integrated external loss **72** and B3 **78**.
Both reach zero final external and certified loss after 13 issued requests.
The difference can be accounted for across the full sequence:

| Contribution to B3 minus B0 integrated loss | Weighted loss |
| --- | ---: |
| Answer becomes externally supported at tick 12 for B3, versus tick 10 for B0: two ticks at weight 6 | +12 |
| Earlier side-goal support: ticks 2–3 and 8–11, at weight 1 | −6 |
| Total | **+6** |

Equivalently, B3−B0 loss is −1 at ticks 2, 3, 8 and 9, and +5 at ticks 10 and 11;
it is zero at the other included ticks. The horizon sums ticks 0–15, with tick 16
reported as the final observation. This is a descriptive accounting identity.
It does not estimate a causal effect of replacing the first choice while holding
all later decisions fixed.

The material sequence differences are:

1. **Initial identical snapshot.** B0 gives `detour`, `shared` and the measurement
   probe equal primary scores of approximately 0.857143; its deterministic cost
   and identity tie-break selects `detour`. B3 selects `shared` at 3.029939,
   ahead of `detour` at 0.180325 and measurement at 0.173357. These are different
   heuristic scores, not comparable calibrated probabilities.
2. **Early side work and observation timing.** After `shared`, B3 ranks `side`
   at 0.722500, narrowly ahead of `detour` at 0.721298 and measurement at
   0.693428. It derives `side`, then monitors it at tick 2 (monitor score 0.85).
   B0 instead has both shared and detour prerequisites and probes measurement at
   tick 2 (score 1.2, versus `side` at 1.0). Seed 7 returns UNKNOWN and succeeds
   on a tick-3 retry; seed 18 succeeds at tick 2 and derives `alternate` at tick 3.
   B3 derives `detour` at tick 3 and has not yet acquired measurement.
3. **Relevant support change and stale requests.** At tick 4 the world revokes
   `initial-seed` between selection and execution. B0's `alternate` request
   (seed 7), or `alternate-answer` request (seed 18), is STALE. B3's measurement
   request is also STALE; an available simulated answer does not bypass the
   snapshot gate or become admitted evidence. B3's earlier side support and
   certified relief reopen. B0's independently observed measurement survives.
4. **Later decisions still matter.** Both reacquire seed at tick 5. B0 chooses
   `detour` then `shared`; B3 again chooses `shared` then `side`. At B0's tick-8
   snapshot, `alternate` scores 2.0 versus 1.5 for either `side` or
   `direct-answer`. At B3's tick-7 snapshot, the same near-tie favoring `side`
   reappears. B3 then derives detour and finally observes measurement at tick 9.
   These are different public world states, so their candidate sets need not
   match each other. The analysis rescoring uses identical candidates within
   each individual recorded snapshot.
5. **Answer route and goal accounting.** B0 derives `alternate-answer` at tick 9,
   supports the answer at tick 10, monitors it at tick 10, then derives and
   monitors side. B3 derives `alternate` at tick 10 and `alternate-answer` at
   tick 11, supporting the answer at tick 12 before its final monitor. At B3's
   tick-11 snapshot, ready `alternate-answer` scores 2.7635625 versus 0.3070625
   for `direct-answer`: a 9:1 score ratio for costs 1:3. That local ratio motivates
   the cost-placement ablation; it does not explain the entire episode by itself.
   Both original controllers ultimately use the alternate route.

External supported-goal loss and certified relief are distinct. B0's answer
becomes externally supported at tick 10 but certified loss falls at tick 11,
after monitoring. B3's side loss reopens at tick 4; when side is re-established at
tick 8, the existing still-valid monitoring evidence supports certified relief
under the frozen contract. B3's answer is externally supported at tick 12 and
certified at tick 13. No new monitoring shortcut was introduced.

The original comparison also retains favorable and neutral results: at work-8,
B3 has integrated loss 102 versus B0's 112, with final loss 6 versus 7, for both
seeds. The simple control is neutral in work-limited operation sequence and loss:
two requests, integrated loss 1 and final loss 0. Wall-limited results and all
overheads remain in `comparison/comparison.md` and `comparison/report.json`.
Complete rich decision tables and full-precision candidate scores for every
original seed/budget pair are in `analysis/decisions.md` and `decisions.json`.

## Separate cost-placement results

All **200 runs passed**: 80 original-episode ablation runs and 120 separate
diagnostic runs. Offline replay reproduced **835 selections** and checked **670
pressure-ranking invocations**. Every initial public snapshot/frontier matched
across policies within each cell, and every selection was checked against the
shared candidate generator and certified authority. The experiment took 108.85
seconds before its separate 111.11-second audit. All original inputs remain
unchanged; the matrix was declared and committed before running it.

There are no harness failures or skipped runs. Expected hard-gate/observation
replies remain visible: the original comparison records 3 UNKNOWN and 12 STALE
replies; the ablation records 39 UNKNOWN and 30 STALE replies. Unresolved goals
remain unresolved when a budget stops the controller. All evaluated pressure
fields converge within their declared bounds in these cases; the existing
regressions separately cover exhaustion. All 232 authority IDs are distinct.

For both rich-episode seeds, integrated external loss is:

| Policy | Work-8 loss | Work-8 final loss | Work-16 loss | Work-16 final loss | Work-16 requests | Work-16 charged operation work, seeds 7 / 18 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| B0 | 112 | 7 | 72 | 0 | 13 | 15 / 14 |
| B3-cost-both, frozen original | 102 | 6 | 78 | 0 | 13 | 15 / 15 |
| B3-cost-route | 112 | 7 | 72 | 0 | 13 | 16 / 15 |
| B3-cost-queue | 112 | 7 | 72 | 0 | 13 | 16 / 15 |
| B3-cost-neither | 64 | 1 | 58 | 0 | 11 | 18 / 17 |

The simple control remains neutral in the work-limited cells. Routing-only and
queue-only thus improve the larger rich budget but lose the original B3's
advantage under the smaller budget. Removing both score factors improves these
work-limited losses while charging more operation work. It is not a cost-free
improvement, nor proof that operation-cost weighting should always be removed.

Against frozen B3, the eight original-episode work-limited cells classify as:

| Ablation | Favorable | Neutral | Unfavorable |
| --- | ---: | ---: | ---: |
| Routing only | 2 | 4 | 2 |
| Queue only | 2 | 4 | 2 |
| Neither score placement | 4 | 4 | 0 |

In the eight original-episode **wall-limited** cells, routing-only and queue-only
each have 0 favorable, 4 neutral and 4 unfavorable results against frozen B3;
neither has 2 favorable, 4 neutral and 2 unfavorable results. These are observed
single-run classifications under host load, not estimated performance rates.
All individual cells, including unfavorable ones, are retained in
`ablation/comparison.md` and `ablation/report.json` inside the archive.

Measured rich work-16 pressure construction/solve overhead spans 24.90–24.97 ms
for the original B3 rerun, 20.37–25.11 ms for routing-only, 17.81–25.27 ms for
queue-only and 17.94–19.65 ms for neither. B0 uses no pressure computation but
its conditional planning is timed separately. These two-seed ranges are not
confidence intervals. Candidate discovery, ranking, inference, certification,
persistence, other controller time, setup, evaluation and total elapsed costs
remain separately recorded for every run, with unmeasured costs explicit.

## What the separate diagnostics establish

**Representation depth matters without changing the task.** With both inference
costs equal to one and no wrappers, every policy has integrated loss 6. Adding
eight logically redundant unary AND wrappers around the high-loss condition
leaves its truth and actual ready operations unchanged. B0 still has loss 6;
every B3 cost placement has loss 10. The high-goal inference pressure falls from
`3 * 0.85^2 = 2.1675` to `3 * 0.85^10 ≈ 0.590623`, below the unchanged low-goal
score 0.7225. Cost placement does not remove this representation dependence.

**Cost placement is not equivalent across graph structures.** At zero wrapper
depth and high-goal cost 8, B0, frozen B3 and queue-only have integrated loss 10;
routing-only and neither have loss 6. A sole production route normalizes its
routing share to one, so routing cost alone does not discount this candidate.
Queue cost still does. All policies pay the same declared cost when they execute
the inference. These cases isolate loss timing under this fixed budget and
one-tick-per-request world; they do not establish a general cost-optimal policy.

Across all 24 diagnostic cells, routing-only and neither each have 10 favorable
and 14 neutral results against frozen B3; queue-only is neutral in all 24.
Against **B0**, routing-only and neither each have 4 favorable, 17 neutral and
3 unfavorable results. Frozen B3 and queue-only each have 15 neutral and
9 unfavorable results. This includes the representation-depth failures.

**Parallel proofs isolate score sensitivity but show neutral outcomes.** For two
ready proofs of the same result, with costs 1 and `c`, the cheap/costly primary
score ratio is `c²` for both placements, `c` for either single placement and 1
for neither. Independent formula checks cover `c = 1, 2, 4, 8`. The common cost
tie-break still chooses the cheap proof when primary scores tie. All four
parallel-route cases have identical outcome loss across all five policies.
The algebraic score effect alone therefore does not establish an episode benefit.

## Independent verification

From a checkout containing this review directory:

```bash
python reviews/b0-b3-3e8fd7b/verify_review.py
tar -xzf reviews/b0-b3-3e8fd7b/review.tar.gz -C /tmp
uv run --no-project python -m validation_lab.audit_pressure_comparison /tmp/b0-b3-review-3e8fd7b/comparison --source-commit 3e8fd7be56362ed21944636bbe505b6a4a7aac6f
uv run --no-project python -m validation_lab.pressure_cost_ablation --audit /tmp/b0-b3-review-3e8fd7b/ablation
```

Use a new extraction directory if that destination already exists. The verifier
checks the archive checksum, safe file inventory and every artifact hash without
extracting. The two audit commands then replay actual recorded operations through
temporary certified authorities. They do not rerun controllers or overwrite the
supplied evidence. The repository must contain the two named source commits;
the full source snapshots are also included for inspection. Native binaries are
not distributed; the lock, build receipt and complete native test log are included.

For fresh execution, follow the commands in [PROTOCOL.md](PROTOCOL.md). The frozen
test commands are recorded in `regressions.json`; use a detached worktree at the
freeze tag for that exact full-suite version. The comparison's source audit and
the ablation's own source bindings remain distinct.

## Scope and interpretation

Costs always charge the original work budgets, including rejected requests.
Each issued request advances the world by one logical tick regardless of its
declared cost; therefore loss timing and charged work answer different questions.
Cost-score effects under loose work limits need not match effects under tight
budgets or real operations whose durations scale with cost.

All wall measurements include host-load variation. Replays check recorded
decisions and consistency, not historical elapsed time, publisher authentication
or independent inference. The pressure solver's numerical reference checks remain
separate. This is bounded exploratory evidence, without statistical significance,
large-scale claims, adaptive transport/M12, learned conductance or generalized
recovery. No ablation is promoted to the frozen implementation.
