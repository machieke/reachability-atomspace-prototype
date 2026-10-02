# Frozen B0/B3 review and exploratory cost-placement ablation

Frozen implementation and development episodes:
`3e8fd7be56362ed21944636bbe505b6a4a7aac6f`.
All 71 comparison source inputs must match that commit. Runtime files, original
episodes, configurations, pressure limits, source identities and authority gates
remain unchanged. The diagnostic tools are committed separately before their
experiment and bind their own source hashes and revision.

Run the full default suite, the full native integration suite and the original
numerical reference suite once in a clean detached worktree at the frozen commit.
Record every command, return code, test count, skipped/failed result, duration,
interpreter/platform and pinned native build receipt. Do not repair the frozen
revision or silently retry a failing suite. Then run the original 32-run comparison
and verify it against that exact commit. Publish one review archive in this
directory, including logs, receipts, source archives, traces, databases, analysis
and the separate ablation results. Its SHA256 is committed alongside the archive.

## Named ablation

| Policy | Inverse operation cost in routing | Divide queue score by operation cost |
| --- | --- | --- |
| B0 | Frozen conditional planner | Frozen conditional planner |
| B3-cost-both | Yes | Yes; exact frozen B3 |
| B3-cost-route | Yes | No |
| B3-cost-queue | No | Yes |
| B3-cost-neither | No | No |

Only the two score placements change. Removing routing cost sets the existing
rule/probe routing-edge weights to one before the same normalization and solve.
Every other dependency edge, AND/OR requirement and source factor is unchanged.
Queue scoring still uses the same candidate anchors. Declared costs always charge
the original operation/observation budgets and remain the secondary tie-break;
this ablates score weighting, not cost awareness or execution authority.

The evaluator temporarily binds the selected pure ranking function in the frozen
controller and auditor, restoring it after each run. It never replaces candidate
discovery, snapshots, observations, world events, certified inference or gates.
Ranking invocations and complete fields are recorded and verified. All five
policies receive identical initial snapshots/frontiers in each cell. Each recorded
selection is replayed using the same snapshot and shared frontier; later states
may differ. The evaluator remains a trusted local process, without OS isolation.

The original two episodes, seeds 7/18 and all four frozen configurations are used
for 80 ablation runs. They are an exploratory rerun, separate from the published
32-run original comparison. Policy order rotates across cells. Work-8/work-16
provide matched work budgets; 100/500 ms cells retain their original wall caps.
Wall variation is reported without treating it as a deterministic advantage.
No tuning, filtered seeds, chosen winning budgets or replacement baseline.

## Separate sensitivity cases

Twenty equivalent-condition cases cross unary AND wrapper depth `{0,2,4,6,8}`
with high-goal inference cost `{1,2,4,8}`. Two one-premise inferences share an
observed seed and produce distinct goals with losses 3 and 1, both at unit
priority. The low-goal inference costs one. Wrappers preserve truth, admissible
operations, loss and required work; they add only pressure graph depth. All three
atoms are true, and no exogenous change occurs. Monitoring still uses the same
certified interfaces. These cases investigate representation dependence rather
than claiming each additional graph edge is additional real work.

Four parallel-route cases use two ready inferences of one result, with costs one
and `{1,2,4,8}`. The single goal has unit loss/priority. At the identical initial
snapshot, the score ratio should be `cost^(routing_flag + queue_flag)` because
the alternatives share a target and depth. This relationship does not generally
hold in a branching graph with different depths and shared prerequisites.

All 24 diagnostic cases use seed 7 and the unchanged work-8 configuration for
120 runs. Combined with the 80 original-episode ablation runs, the matrix contains
200 runs. It is fixed before running this experiment and remains outside
`pressure_episodes.py`. Report every cell, with favorable/neutral/unfavorable
integrated-loss differences against both B0 and frozen B3, alongside final loss,
requests and measured costs. Do not force a result class to appear.

## Decision analysis and interpretation

Use the frozen comparison's actual selection/receipt pairs, candidate ranks,
observations, stale requests and external/certified goal-loss history. Recompute
both policies on each recorded snapshot and identical affordable candidates as
a ranking diagnostic only. Sum the per-tick, per-goal weighted loss difference
over the full sixteen-tick horizon. Distinguish transient side-goal benefit,
later answer completion, monitoring and reopening. This is a descriptive
decomposition, not an intervention assigning the entire outcome to the first
divergence. Explain scores at later material decisions as well as the first one.

These are bounded exploratory diagnostics. They do not promote an ablation to
the production B3, establish statistical significance or complete the broader
pressure/benchmark design. Adaptive transport/M12, learned conductance and
generalized recovery remain deferred.

## Commands for the separate tools

```bash
uv run --no-project python -m validation_lab.pressure_cost_ablation --output artifacts/cost-placement-review
uv run --no-project python -m validation_lab.pressure_cost_ablation --audit artifacts/cost-placement-review
uv run --no-project python -m validation_lab.analyze_pressure_decisions PATH_TO_FROZEN_COMPARISON --output artifacts/frozen-decision-analysis
```

The original comparison command and offline auditor remain documented in
`PRESSURE_COMPARISON.md`. Diagnostics require the committed extension source and
the exact frozen runtime inputs; a changed original implementation is rejected.
