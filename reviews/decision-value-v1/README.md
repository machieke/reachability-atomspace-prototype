# Independent bounded decision-value validation

The fixed policies have mixed results. None is an optimal scheduler for the
integrated external-loss objective. The normalized pressure variants agree with
the exact reference on more of the sampled decisions than B0, but that does not
translate into a lower aggregate closed-loop loss gap on these parent cases.
Large budget failures and premature monitoring matter more than the number of
locally correct choices. This supports investigating the distinction between
backward demand and execution value within this bounded fragment; it does not
establish that hypothesis for general workloads or evaluate pressure-guided
search.

This review closes the requested increment. Runtime
`3e8fd7be56362ed21944636bbe505b6a4a7aac6f` and projection
`8542ad538649fd0b967c7047057dd5cebf831be8` remain unchanged. The accepted experiment
uses corrected harness `decision-value/v1.1` at
`7bf11d5282542c870dfd270613db2b46fc031321`. The protocol, complete inventory,
reference-only feasibility, sampling and budgets were committed at
`d7fa0625151a88dc55857f1c4cedadd228aea6db` before any policy measurement.
Both earlier published reviews and their archive checksums are preserved.

The first attempt completed its measurements but failed the final audit because
integer revision keys sorted differently after JSON decoding. Its complete
artifacts and failure log are retained, not relabeled as an accepted run. The
[explicit correction](CORRECTION-v1.1.md) documents the defect, narrow repair and
new regression. The second attempt uses fresh authorities and the same
configuration. All 660 paired closed-loop runs have identical semantic traces/outcomes/work and all 132 initial reference labels match between attempts. The 1320 closed-loop authorities are distinct. Timing and exact opaque event bindings are excluded only from this cross-attempt comparison; the accepted audit checks each binding independently.

## Contract and coverage

[Protocol](PROTOCOL.md), [complete case inventory](inventory.json),
[reference-only feasibility](feasibility.json), and [machine-readable review
summary](summary.json) are adjacent. The full family/budget/partition tables,
candidate ranks, Q/V labels and continuations, observations, receipts and journals
are in the [comparison bundle](review.tar.gz).

There are 48 structurally varied parent tasks: eight each for OR alternatives,
AND requirements, shared prerequisites, real operation depth, budget sensitivity,
and goal competition/completion. Thirty parents are development and eighteen are
locked confirmation. No policy was tuned after either partition was observed.
Twelve identifier siblings and six dominated-option siblings remain grouped with
their parents; they are not additional independent instances. Seed 0 denotes no
random sampling. This is an engineering cohort, not a statistical power claim.

The deterministic task descriptor is available to every controller on its public
port. It declares permanent supports, no future events or probes, the complete
physical assignment, monitoring semantics and no commitments. The frozen rankers
ignore this extra metadata; the reference is allowed no additional hidden future.
Runtime evidence, exact support references and gates remain authoritative.

The DP and separate complete-history enumerator import only the standard
library and encode transitions independently. They agree on all 132 initial
cells and all 359 sampled public states, including complete first-action Q
values, witness continuations and primary-optimal sets. The 359 include the
132 roots, so these are not 491 independent states. No reference is censored or
replaced. Maximum initial search: 42 DP states, 96 transitions, 378652 accounted
bytes and 867 enumeration nodes. All are inside the predeclared 4096-state,
32768-transition, 16 MiB accounting and 100000-enumeration-node bounds.

All 150 preselected distinct reference continuations run through real certified
inference and monitoring. Observable states, admissible frontiers, per-goal loss
and monitor outcomes match the independent model. The completed audit replays
2352 policy selections, 1795 common-state rankings and those 150
witnesses, checking saved journals as well as newly reproduced effects.

The horizon is ticks 0–15, with one tick per request. Work credits are not
durations. STOP is termination with no free work during the tail; no wait/resume
operation exists. The full budget vectors are:

| Configuration | Requests | Operation work | Observation work | Candidate visits | B0 states | Pressure iterations | Wall limit |
|---|---:|---:|---:|---:|---:|---:|---:|
| requests-4-work-4 | 4 | 4 | 3 | 4096 | 65536 | 8192 | 30 s |
| requests-8-work-12 | 8 | 12 | 3 | 4096 | 65536 | 8192 | 30 s |

Every raw decision/result has its full vector. Common states use remaining
semantic budgets and fresh equal auxiliary budgets; candidate discovery is
measured once and charged equally to all policies. Samples are root plus fixed
lexicographic reachable-state strata at ticks 1–3, not states selected by a
favored policy. Siblings use mapped parent prefixes. Historical `work-8` still
means eight requests with its separately declared operation-work budget.

## Decision quality and closed-loop outcomes

Primary correctness means membership in the entire exact external-loss-optimal
action set, not matching an arbitrary identifier. Secondary criteria select a
witness only: certified terminal loss, operation work, requests, action sequence.
Decision regret is Q*(chosen) minus V* at one state. Episode gap is actual whole
trajectory loss minus initial V*. These remain separate; no attribution below
sums overlapping continuation regrets.

| Policy | Optimal choices / 276 | Mean decision regret | Mean episode gap | Max episode gap | Zero-gap episodes / 96 | Vs B0 favorable / neutral / unfavorable |
|---|---:|---:|---:|---:|---:|---|
| B0 | 193 | 1.699 | 4.812 | 42 | 33 | 0 / 96 / 0 |
| B3 both | 196 | 1.315 | 5.229 | 48 | 35 | 8 / 77 / 11 |
| B3 route | 199 | 1.268 | 5.229 | 48 | 37 | 11 / 74 / 11 |
| B3 queue | 195 | 1.333 | 5.229 | 48 | 35 | 8 / 77 / 11 |
| B3 neither | 211 | 1.315 | 5.031 | 52 | 43 | 23 / 62 / 11 |

The table covers 96 parent/budget cells, with 48 independent parent identities;
no confidence interval or population generalization is claimed. Agreement is
out of the same 276 sampled parent states for each policy. Regret means are
state-weighted descriptive values; summary.json additionally reports equal
weighting of each parent's mean. Siblings are excluded from this table.

| Partition | Requests / work | Policy | Mean episode gap | Vs B0 favorable / neutral / unfavorable |
|---|---|---|---:|---|
| confirmation | 4 / 4 | B0 | 10.889 | 0 / 18 / 0 |
| confirmation | 4 / 4 | B3 both | 12.389 | 1 / 13 / 4 |
| confirmation | 4 / 4 | B3 neither | 12.333 | 3 / 11 / 4 |
| confirmation | 4 / 4 | B3 queue | 12.389 | 1 / 13 / 4 |
| confirmation | 4 / 4 | B3 route | 12.833 | 2 / 11 / 5 |
| confirmation | 8 / 12 | B0 | 4.500 | 0 / 18 / 0 |
| confirmation | 8 / 12 | B3 both | 4.778 | 1 / 13 / 4 |
| confirmation | 8 / 12 | B3 neither | 2.167 | 7 / 9 / 2 |
| confirmation | 8 / 12 | B3 queue | 4.778 | 1 / 13 / 4 |
| confirmation | 8 / 12 | B3 route | 4.333 | 3 / 12 / 3 |
| development | 4 / 4 | B0 | 3.900 | 0 / 30 / 0 |
| development | 4 / 4 | B3 both | 4.400 | 3 / 25 / 2 |
| development | 4 / 4 | B3 neither | 6.167 | 5 / 21 / 4 |
| development | 4 / 4 | B3 queue | 4.400 | 3 / 25 / 2 |
| development | 4 / 4 | B3 route | 4.400 | 3 / 25 / 2 |
| development | 8 / 12 | B0 | 2.267 | 0 / 30 / 0 |
| development | 8 / 12 | B3 both | 2.033 | 3 / 26 / 1 |
| development | 8 / 12 | B3 neither | 1.233 | 8 / 21 / 1 |
| development | 8 / 12 | B3 queue | 2.033 | 3 / 26 / 1 |
| development | 8 / 12 | B3 route | 2.033 | 3 / 26 / 1 |

The full six-family breakdown, with the complete budget vector on every row,
is in `comparison/analysis.json` and `comparison/comparison.md` after extraction.
Every placement has favorable, neutral and unfavorable results versus B0. More
zero-gap episodes or higher sampled-state agreement does not ensure smaller mean
episode gap. No cost placement is promoted.

## What the recorded decisions explain

Scores below are primary rank values: smaller (more negative) ranks first. Full
rank tuples, budgets and complete continuations remain in each cell's JSON.
All new deterministic-episode receipts are PASS; there are no stale or unknown
requests to explain these losses. The hard-gate regressions separately test
invalid/stale requests. Conclusions supported by inference and goals certified
by monitoring are reported separately throughout.

**A later decision, not the first divergence: `depth-2`, four requests/work 4.**
There is a three-step cheap route to a loss-4 goal and a one-step route to a
loss-2 goal. The exact loss is 18: take the side result, then the three main-route
steps. B0 loses 44; each B3 placement loses 66.

B0 first ranks the main prerequisite and side result equally at -1.0, then its
fixed secondary ordering chooses the prerequisite. That action's Q is 20 versus
V=18. At the last request it ranks `monitor/g0` at -4.0 ahead of the unfinished
side inference at -2.0; their Q values are 26 and 2. Its final external loss is 2
and certified loss is 2.

B3-both first ranks the side inference at -1.445 ahead of the main prerequisite
at -1.257165052. The chosen action has Q=V=18: the first divergence is favorable.
At the next request, however, `monitor/g1` scores -1.7 versus -1.257165052 for the
main prerequisite. Their Q values are 60 and 12. Monitoring leaves only two
requests and two work credits for a three-step route, so the main goal remains
externally unresolved. Final external and certified losses are both 4.

The actual per-goal totals explain the 22-unit B3-versus-B0 difference: main-goal
loss rises from 12 to 64 (+52), while side-goal loss falls from 32 to 2 (-30).
This uses the recorded tick sequences. The isolated Q comparisons describe
counterfactual optimal continuations, not an additive causal decomposition of
that 22-unit difference. Paths:
`depth-2/requests-4-work-4/{B0,B3-normalized-both}/result.json` and `trace.jsonl`.

**Real depth can favor an expensive immediate inference.** In `depth-0`, the
reference loss is 4. B3-neither takes the one-step cost-4 proof and loses 4;
B0 and the other placements take two cost-1 inferences and lose 8. At the tight
budget, B3-neither's certified terminal loss remains 4 because monitoring is
unaffordable; the other policies' certified loss is 0. Under the larger budget,
B3-neither also monitors. This favorable external-loss result is not permission
to call unmonitored support certified success.

**The opposite budget case is unfavorable.** In `depth-3` with work 4,
B3-neither ranks the cost-3 prerequisite of a two-step cost-6 route at
-1.0440125 ahead of the cost-1 prerequisite of a three-step cost-3 route at
-0.754299031. Q values are 64 versus 12. It cannot complete the expensive route
or recover within the remaining work, losing 64 versus 12 for B0 and the other
placements. Under work 12 the shorter route is feasible and B3-neither instead
loses 8 versus B0's 12. Actual work and remaining budgets, not syntax depth,
explain the reversal.

**Neutral comparisons can still be suboptimal.** In `shared-0`, every policy
uses the shared prerequisite once, finishes one goal, monitors it, then finishes
the other. All lose 12 versus the exact 10. The monitor delays the second result
one tick at loss 2. With four requests, one goal remains uncertified; with eight,
both become certified. In `completion-0`, all policies match the exact loss 1.
In blocked `and-6`, demand for the impossible AND bundle remains unresolved;
B3's initial investment in its feasible half delays the side result, losing 50
versus B0/reference 49. No policy executes the forbidden prerequisite.

## Identifier and dominated-route diagnostics

| Policy | Primary score ties / 276 | Identifier changed choices / 62 common queries | Identifier changed trajectories / 24 | Identifier changed losses / 24 | Dominated changed losses / 12 |
|---|---:|---:|---:|---:|---:|
| B0 | 63 | 10 | 8 | 2 | 0 |
| B3 both | 37 | 8 | 6 | 0 | 2 |
| B3 route | 35 | 6 | 5 | 0 | 0 |
| B3 queue | 38 | 8 | 6 | 0 | 2 |
| B3 neither | 43 | 6 | 5 | 0 | 0 |

The reference has multiple primary-optimal actions in 106/276 parent states. All identifier-induced changes in common choices occur at primary ranking ties under the declared tolerance. Real-route diagnostics need not preserve candidates or pressure; their optimum and old feasible plan are the invariants.

The reference optimum is unchanged for every sibling. All old optimal plans
remain feasible after a dominated route is added. Identifier changes sometimes
alter arbitrary secondary choices without changing loss. B0's `shared-6`
permutation changes loss by +13 with work 4 and +2 with work 12; these are real
tie-sensitive trajectory differences, not failures to match a canonical ID.

The dominated-route control is a stronger negative pressure result. In
`budget-0`, the cost-4 direct proof removes loss 6 while a cost-1 proof removes
loss 1. Add a genuine parallel proof with identical premise/conclusion and cost
5. The old reference optimum, 22 under work 4, and its cost-4 witness remain.
The extra cost-5 proof is not affordable under that budget and cannot be issued.

B3-both's original high-result rank is -1.08375 versus -0.7225 for the side
result. Adding the real route splits the same demand between alternatives;
the affordable high-result rank becomes approximately -0.602083333, so the side
result now wins. B3-queue has the same qualitative change (high-result rank
-0.541875 after equal route splitting). Both then lack work for the high result:
loss rises from 22 to 97 (+75). At work 12 the delay raises loss from 9 to 19
(+10). B0, route-only and neither retain the original outcomes. Source demand
was not duplicated: there is still one canonical obligation for each goal. The
change is in allocation among real routes and subsequent queue weighting.

These controls do not justify merging real proof operations or modifying the
normalizer. They reveal a sensitivity of the unchanged heuristic, with identical
candidates required across policies at each identical state. The original
representation-invariance suite remains a separate passing regression.

## Costs, accounting and applicability

| Policy | Mean requests / work / observations | Discovery ms | Ranking ms | Normalization ms | Graph ms | Pressure solve ms |
|---|---|---:|---:|---:|---:|---:|
| B0 | 3.75 / 4.11 / 1.43 | 0.871 | 1.210 | 0.000 | 0.000 | 0.000 |
| B3 both | 3.76 / 4.12 / 1.42 | 0.893 | 0.370 | 1.984 | 1.698 | 4.120 |
| B3 route | 3.71 / 4.17 / 1.41 | 0.880 | 0.369 | 1.986 | 1.691 | 4.176 |
| B3 queue | 3.76 / 4.12 / 1.42 | 0.909 | 0.379 | 2.039 | 1.811 | 4.193 |
| B3 neither | 3.48 / 4.40 / 1.38 | 0.834 | 0.344 | 1.877 | 1.619 | 4.034 |

| Policy | Inference ms | Certification ms | Persistence ms | Total elapsed ms | Terminal external / certified loss |
|---|---:|---:|---:|---:|---|
| B0 | 0.307 | 53.004 | 123.958 | 662.675 | 0.427 / 0.906 |
| B3 both | 0.302 | 53.797 | 124.715 | 672.962 | 0.469 / 1.000 |
| B3 route | 0.300 | 52.918 | 123.664 | 668.049 | 0.479 / 1.052 |
| B3 queue | 0.306 | 54.630 | 124.238 | 673.716 | 0.469 / 1.010 |
| B3 neither | 0.269 | 48.828 | 117.666 | 648.520 | 0.531 / 1.219 |

These are means over 96 parent/budget runs per policy, from one accepted
measurement. Timing is supplementary. No causal speedup, significance test or
confidence interval is claimed. Full rows retain discovery, ranking,
normalization, graph construction, pressure iteration, actual inference,
certification, persistence, authority overhead, setup/evaluation, work counts and
total elapsed time. Normalization plus graph equals pressure construction;
execution includes authority categories and must not be added again.

On the 276 identical parent-state queries, B0 ranking averaged 0.850 ms and the pressure variants 2.058–2.571 ms, with the same 0.238 ms discovery charge per query. These include the shared diagnostic wrapper; common-query order is fixed, while closed-loop order rotates. This is direct overhead evidence, not a speedup claim. Pressure's extra computation sometimes selects a better immediate operation, notably short expensive routes under slack work budgets, but does not buy a uniformly better scheduler: aggregate episode gaps and dominated-route failures remain unfavorable. A workload-specific value for lower loss would be needed to justify that overhead; this experiment supplies no arbitrary cost/loss exchange rate. It does not evaluate whether pressure-guided plan search would justify its computation.

Accepted experiment phase: 663.725 s; separately measured DP/enumeration: 0.275 s (included in the experiment phase); replay audit: 691.529 s; full command: 1356.276 s. These are elapsed categories, not independent repetitions.

Reference solver/enumeration time is measured separately. Model initialization,
label/report serialization, witness close/copy and harness orchestration are
included in total experiment time but not individually separated. Prefix and
witness execution are offline validation, not selectively charged to a policy.
Peak RSS, individual SQLite bytes/fsync latency, scheduling attribution and real
sensor latency remain unmeasured. Memory bounds are deterministic allocation
accounting, not measured RSS.

All 2352 new operation receipts are PASS. There are zero stale/unknown replies, authority violations detected, failed accepted runs, pressure-bound exhaustions or nonconverged fields. Source identities and relief-event prefixes match saved journals. Stops: 418 observed-goal completions, 153 request limits, 69 work limits and 20 blocked frontiers. Unresolved goals remain visible; there are no commitments in this declared fragment. The one failed first-attempt audit remains a separate reported failure.

The deterministic reference cannot label the original rich episode, whose
future support revocation and probe timing are evaluator-hidden. Its preserved
[descriptive review](../b0-b3-3e8fd7b/README.md) retains B0/B3 work-16 losses 72/78:
later answer relief adds 12 and earlier side relief removes 6. That comparison
is not an exact same-information target here. No hindsight bound is folded into
these decision-regret results.

## Validation, omissions and reproduction

- 242 applicable tests at protocol/measurement-v1 source `d7fa062`: passed,
  zero failures/errors/skips. They cover admission and deployment traces, B0,
  goal/operation/resource contracts, pressure/source accounting, M09, cost
  placements, decision analysis, projection invariance, audit corruption checks,
  manifest and the first 13 decision-value tests.
- 15 standalone numerical checks at `d7fa062`: passed, zero failures/errors/skips.
- 14 decision-value tests at corrected source `7bf11d5`: passed, including the
  added decimal-revision JSON round-trip regression and all 132 canonical
  certified witness replays. This rerun validates the correction; it is not 14
  additional independent behavioral capabilities.
- Policy-free preflight (10 tests), policy wiring (3 tests), and the focused
  serialization regression (1 test) are logged separately. The failed first
  artifact audit is explicitly retained. The accepted full audit is PASS.

Full commands, revisions, elapsed measurements and complete logs are bundled.
The full default suite, unrelated recovery/worker/planning/native suites and
standalone repeatability suite were not rerun in this evaluator-only increment;
`regressions/omissions.json` lists every omitted default module. The earlier
938 default / 85 native suite results belong to the projection review and are
historical, not new passes. No native backend code changed. Transport-specific
M12 remains deferred. No deferred capability is marked complete.

Run the complete accepted experiment from the committed source into a new
output directory:

```sh
uv run --no-project python -m validation_lab.decision_comparison --output artifacts/decision-value-v1.1/comparison
```

This writes independent labels, common rankings, actual closed-loop traces,
journals, witness checks, costs, a readable report and a full replay audit. It
checks the frozen runtime/projection and committed experiment inputs. Interrupted
runs remain blocked; no resume or repair automation is introduced.

Verify the published archive without extraction:

```sh
uv run --no-project python reviews/decision-value-v1/verify_review.py
```

Extract and replay the accepted evidence from a repository containing the
recorded Git commits:

```sh
mkdir /tmp/decision-independent-review
tar -xzf reviews/decision-value-v1/review.tar.gz -C /tmp/decision-independent-review
uv run --no-project python -m validation_lab.decision_comparison --audit /tmp/decision-independent-review/decision-value-review-v1/comparison
```

The archive includes the accepted comparison, failed first attempt, source
snapshots, both execution logs, fixed protocol/inventory, tests, summaries and
checksums. Source snapshots omit only the previously published binary review
archives; their existing checksums and documentation are preserved and their
original repository files remain unchanged. Saved journals are audited via
copies. Integrity checks do not authenticate a publisher, and replay does not
reproduce historical timing. Inspect the [protocol correction](CORRECTION-v1.1.md)
for the five-versus-six-rule documentation erratum; no bound or case changed.

Stop here. No adaptive transport, learned conductance, ECAN, new pressure policy,
normalization expansion, native PLN scheduling, generalized recovery, caching,
scale or duration model was added. Choosing a later search or scheduling
experiment is outside this milestone.
