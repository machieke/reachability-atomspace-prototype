# Representation-invariant pressure projection

This increment adds an experimental read-only projection before pressure graph
construction. The frozen B0/B3 runtime at `3e8fd7b`, original benchmark, and
[earlier published review](../b0-b3-3e8fd7b/README.md) are unchanged. None of the
four cost placements is promoted. Gamma remains 0.85 and all existing hard gates
retain authority.

Experimental implementation and protocol: `8542ad5`.

## Recorded results

All 639 controller runs finish with PASS status. The run phase takes 453.41
seconds. Expected operation rejections remain visible: 73 UNKNOWN and 54 STALE;
these are gate/observation outcomes, not harness failures. All evaluated pressure
fields converge and none exhausts its declared pressure bounds. Replay passes
all 639 distinct authorities, reproduces 2,757 selected requests and verifies
2,458 ranking calls. Its separate audit takes 604.35 seconds; the complete
comparison command takes 1059.51 seconds. All 71 frozen source files and ten
experimental/tool inputs are bound to their committed revisions.

All 160 normalized equivalence pairs match throughout their 676 selected
snapshots: identical real candidates, source accounting, per-source semantic
pressures, rankings, choices and external outcomes. The maximum observed pressure
difference is zero. There are 168 pair/snapshot records with unresolved primary
ties, retained explicitly in the report. Each of the 160 corresponding raw pairs
has different initial semantic pressure. This does not mean every raw pair has
different choices or loss.

The frozen wrapper failure is reproduced: at equal operation cost, eight unary
wrappers change raw B3's integrated loss from 6 to 10. Its high-operation pressure
falls from `3 × 0.85² = 2.1675` to `3 × 0.85¹⁰ ≈ 0.590623`, below the competing
operation's `0.7225`. Every normalized placement keeps loss 6 and the unwrapped
pressure at all tested AND/OR depths 0–8. The mixed transformation families also
match across complete normalized trajectories, including permutations,
reassociation and duplication together with alternating unary operators.

Normalization preserves actual work. The real-operation-depth controls retain
one, two and three certified high-goal inference steps; total operation work is
4, 5 and 6, with integrated losses 6, 10 and 14 respectively for every policy.
Normalization does not remove those edges or costs. Parallel-route controls are
neutral on external loss. Distinct evidence, validity/revision changes, scoped
temporal contexts and unsupported resource quantities are covered by negative
tests, without claiming support for a generalized temporal/resource grammar.

Every original work-budget outcome and request sequence remains unchanged by
normalization at the same cost placement. For both seeds, rich work-8/work-16
integrated losses remain: B0 `112/72`, both placements `102/78`, routing only
`112/72`, queue only `112/72`, and neither `64/58`. Work-16 finishes with zero
external loss. Both/route/queue use 13 requests; neither uses 11 but charges more
operation work. The simple work-budget control remains neutral at loss 1.
These retained cost-policy differences do not justify promoting an ablation.

A setup preflight stopped before any comparison or test ran because a temporary
virtual-environment symlink made the detached checkout non-clean. The symlink was
removed and the driver restarted; `preflight.log` retains that failure. No
comparison cell was discarded or retried.

The following counts classify integrated external loss; final loss, work and
cost remain separate. Each row has 55 diagnostic cases and eight original
wall-budget cases. All 32 normalized-versus-corresponding-raw original work-budget
cells are neutral.

| Normalized placement | Diagnostic vs same raw: favorable / neutral / unfavorable | Diagnostic vs B0: favorable / neutral / unfavorable | Original wall caps vs same raw: favorable / neutral / unfavorable |
| --- | --- | --- | --- |
| Both | 12 / 43 / 0 | 0 / 42 / 13 | 0 / 7 / 1 |
| Routing only | 12 / 43 / 0 | 5 / 42 / 8 | 1 / 7 / 0 |
| Queue only | 12 / 43 / 0 | 0 / 42 / 13 | 0 / 7 / 1 |
| Neither | 12 / 43 / 0 | 5 / 42 / 8 | 0 / 7 / 1 |

Unfavorable results are substantive and retained. In the cost-four unwrapped
case, normalized both-placement B3 still chooses the low goal first and has loss
10 versus B0's 6, with the same seven operation units. For the three-child AND
case, its loss is 16 versus B0's 14; for the three-alternative OR case, 10 versus
6. Fixing representation sensitivity does not establish optimal scheduling.
Under the original 500 ms cap at seed 7, normalized both/queue/neither lose
8/36/6 more integrated units than their corresponding raw runs, while normalized
routing-only loses 36 fewer. Wall-cap outcomes reflect measured runtime and host
variation; these single runs cannot isolate normalization as the cause of each
timing difference or establish significance.

Normalization has an explicit cost. On rich work-16, its measured time ranges
from 3.54 to 6.66 ms across the four placements and two seeds. For normalized
both-placement B3, construction plus solving costs 19.9–34.8 ms, controller time
956.15–1004.29 ms, and complete setup/controller/evaluation time
1122.14–1164.11 ms. Full timing categories and raw counterparts are retained in
the comparison; lower isolated wall times are not claimed as general speedups.

Run the complete original-plus-diagnostic comparison from this repository:

```sh
uv run --no-project python -m validation_lab.projection_comparison --output artifacts/my-projection-review
```

The output must be a fresh directory. The command runs all nine policies across
the fixed 639-run matrix, writes machine-readable reports, traces and SQLite
journals, writes `comparison.md`, seals the file inventory and replays every run.
Source files must match a committed experimental revision. It does not rerun
the full regression suites; their commands and results are recorded separately
in the published review bundle.

## Bounded contract

`experimental_pressure/projection.py` normalizes detached signed FACT/AND/OR
requirements within an explicit context, goal, source, slice and temporal
contract. It removes unary operators, flattens the same operator, orders children
canonically, and deduplicates identical idempotent Boolean requirements. It does
not distribute, absorb different Boolean operators, identify arbitrary equivalent
formulas, or normalize actual proof operations.

The projection retains every original requirement occurrence, its path and
digest, its containing projected node, its scope, and conservative dependencies
on public revisions, support references, support validity and logical time.
Flattened subexpressions use an explicit `flattened_into` relationship; this
does not assert equivalence between a proper subexpression and its parent.
Mappings describe the normalized requirement form; already satisfied goals route
to monitoring without materializing unnecessary requirement nodes.

The original goal contracts are used unchanged for certification, invalidation,
monitoring and relief. The original candidate interface binds exact support
references and revisions. Projection only supplies advisory ranks. Facts can
remain shared prerequisites; scoped requirement nodes and canonical obligation
accounts do not merge goals or create an obligation for each syntax path.

Default limits are 512 input occurrences, depth eight, 512 children, 512 output
occurrences and four goals. The existing public profile imposes its additional
128-occurrence/eight-child limits per original condition. Limits are validated
and explicitly recorded. Exceeding a projection limit raises `ProjectionBlocked`
with unchanged source accounts before returning any partial graph or ranking.
The current ranking call issues no operation. No interrupted-session recovery
or partial-plan continuation is introduced. Existing pressure graph, iteration,
session and operation budgets apply after successful normalization.

Resource quantities, evidence predicates and temporal predicates are unsupported
requirement types here; rejection is tested rather than claiming their general
normalization. Different temporal scopes remain distinct, support references and
validity remain revision-bound, and real epistemic steps survive graph building.

## Validation and comparison method

All suites ran once in a clean detached checkout at experimental revision
`8542ad538649fd0b967c7047057dd5cebf831be8`, after the measured comparison. No tests
failed or were skipped, and no implementation repairs or suite retries were needed.

| Suite | Passed | Test time (seconds) |
| --- | ---: | ---: |
| Full default suite, including all 17 new tests | 938 | 1273.434 |
| Full native integration suite | 85 | 157.689 |
| Standalone numerical reference checks | 15 | 0.037 |

Full logs, outer elapsed measurements and before/after clean-checkout receipts
are included. Deployment, all existing corpus receipts, hard-gate, recovery and
M09 regressions remain covered. Transport-specific M12 is deferred, as before;
no deferred capability is marked complete. The earlier frozen review's 912/85/15
results remain its own historical evidence and are not relabeled as this run.

Generated tests combine alternating unary AND/OR, reassociation, permutations and
duplicates over mixed Boolean trees, including signed literals. An independent
truth-set oracle checks all 32 assignments for 160 generated transformations.
Across four actual support states, 512 transformation/policy comparisons check
the common candidates, canonical source ledgers, per-source pressure values and
ranks. Determinism, idempotence, provenance, every bound, actual stale/invalid
gate rejection, and unchanged authority state are also checked.

The experiment has B0, all four raw cost placements and four named
`B3-normalized-*` variants. Frozen `B3-cost-both` delegates to the exact original
ranking function. Every variant shares candidate discovery, budgets, operation
charges, certification and world events. All 144 original-episode runs retain the
original seeds and four budgets. The 495 diagnostic runs cover the old 24
depth/cost/parallel cases, all previously missing unary depths and OR wrappers,
four mixed Boolean families with three generated transformations each, and three
real-operation-depth negative controls. These cases do not change the benchmark.

For normalized equivalent cases, the auditor compares every selected snapshot,
candidate set, source account, per-source semantic-node pressure, rank, choice
and external outcome. Raw runs may diverge; their pressure comparison uses the
common initial state and separately reports actual closed-loop outcomes. The
allowed numerical difference is the sum of both solver L1 error bounds plus
1e-12. Unresolved primary-score ties are explicit; the shared secondary
cost/identity tie-break is retained. Raw hashes, provenance and runtime need not
match across different representations.

Normalization time and graph construction time are separate subcategories whose
sum is the controller's charged pressure-construction time. Numerical solving,
candidate discovery, inference, certification, persistence, setup/evaluation and
total elapsed costs are recorded separately. Inclusive execution and construction
categories must not be counted twice. Peak memory, scheduling attribution and
real sensor latency remain explicitly unmeasured. This is a single exploratory
run per cell, with no statistical performance or general superiority claim.

The current single-process experiment binds a ranking function for live selection
and replay, then restores it. The runtime extension imports no evaluator module
and receives only the public snapshot/candidates. This is an import boundary, not
OS process isolation. Unsupported act/expand/retain, adaptive transport/M12,
learned conductance, generalized recovery and a new duration model remain deferred.

## Independent review

`review.tar.gz` contains the complete comparison, traces, all 639 journals,
source snapshots, protocol, validation logs, execution receipts, adapter build
receipt and readable findings. `SHA256SUMS` pins the archive; the internal
`review.json` inventories every included file. Check byte integrity without
extracting:

```sh
uv run --no-project python reviews/pressure-projection-v1/verify_review.py
```

To replay the published evidence, extract into a fresh directory and use a
repository checkout containing the recorded commits:

```sh
mkdir /tmp/projection-independent-review
tar -xzf reviews/pressure-projection-v1/review.tar.gz -C /tmp/projection-independent-review
uv run --no-project python -m validation_lab.projection_comparison --audit /tmp/projection-independent-review/pressure-projection-review-v1/comparison
```

The saved comparison is read-only during audit; the verifier replays copies of
journals. The archive checksum establishes byte integrity against the published
checksum, not publisher authentication. Source archives support inspection;
commit-bound replay also needs the Git objects for `3e8fd7b` and `8542ad5`.
Historical timing is consistency-checked, not reproduced by replay. Fresh
wall-budget runs can legitimately differ under different host load.

To rerun validation at the experimental source revision, use:

```sh
uv run --no-project python -m unittest discover -s tests -v
uv run --no-project python -m unittest discover -s integration_tests -v
uv run --no-project python pressure_field_lifecycle_reference_checks.py
```

The native suite requires the pinned dependencies described in [ADAPTERS.md](../../ADAPTERS.md).
The numerical and default suites use the repository's ordinary test entry points.
