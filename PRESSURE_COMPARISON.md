# Bounded B0-versus-B3 comparison

Run both controllers and write the comparison with one command:

```bash
uv run --no-project python -m validation_lab.run_pressure_comparison --output artifacts/pressure-comparison
```

The output directory must be new. Optional `--seeds 7 18` explicitly selects the
default two seeds. The command exits nonzero on a failed run, inconsistent
candidate frontier, or surviving M09 mutation. A budget stop, an unavailable
observation or a correctly rejected stale request is recorded as an episode
outcome rather than hidden as a harness failure.

This is an implemented subset of pressure proposal sections 6–9, 13–15 and 21,
the reachability specification's separation of authority and scheduling, and the
benchmark design's B0/B3 and equal-information comparisons. It does not complete
the full pressure, attention, transport or benchmark design.

## Authority and pressure

`ReasoningSession` projects the existing `AdmissionService` goal, evidence,
belief, policy and rule records. Goal slices have canonical identities derived
from `(context_id, source_id, slice_id)`. The service owns outstanding loss,
overlap-aware live coverage, observation contracts and relief history. Pressure
reads detached projections and has no service, journal or executor handle.

For each source, the implementation computes `D = w*u*kappa*L` and
`D_open = w*u*kappa*(L-C)`. A policy explicitly converts each declared goal unit
to common priority units. Urgency and commitment factors are finite, versioned
and bounded; they are not belief confidence. Loss, predicted coverage, open loss,
observed relief and reopened obligations remain separate. Covered demand goes to
its observation/monitoring anchor instead of being counted as observed relief.
Maintenance scheduling after a satisfied goal is outside this one-result scope.

An epoch binds the full public snapshot, knowledge/policy/goal/lifecycle/resource
revisions, current rule dependencies, priority policy and solver configuration.
Every epoch recomputes from the source ledger. Repeated reads, duplicate edges
and additional dependency paths cannot append another obligation. Conflicting
records with the same source identity are rejected.

The graph has explicit FACT, AND and OR anchors and whole rule-application
anchors. Epistemic, lifecycle/enabling, teleological and observation dependencies
are supported. Other dependency mechanisms, including causal action modeling,
resource allocation pressure and general temporal operators, are unsupported.
The existing authority still enforces its resource/temporal contracts elsewhere.

AND groups give each missing prerequisite a positive normalized share. OR groups
share pressure between complete rule branches using inverse declared operation
cost; they never combine partial branches into an executable inference. Current
support is supplied by the authority. Strongly connected components are reported,
and cycling pressure cannot establish support. Known joint conflicts retain
`FORBIDDEN_ACTION` diagnostics; missing support/capabilities retain unresolved
demand and reasons. Pure early candidate checks supplement the unchanged public
pre-certificate, inference, post-certificate and commit checks.

The fixed operator is `p_next = d + gamma*R*p`, with nonnegative,
column-substochastic routing. Channel conversion is explicit on typed graph
edges, with source attribution preserved. Only `infer` and `observe` channels
are supported; `act`, `expand` and `retain` are reported as unsupported rather
than populated with placeholder scores. There is no activation state or adaptive
transport. Graph-depth pressure sums are diagnostics, never loss or budgets.

The `binary64-substochastic/v2` routing algorithm checks the exact sum of the
stored shares using integer ratios. Rounded `fsum` alone is insufficient: five
stored `0.2` values exceed one even though their rounded sum is one. When there
is an exact excess, the largest share is rounded downward to the remaining
capacity; every other share is preserved. Sorting makes that correction
deterministic. The routing version is recorded and included in the pressure epoch.
If a positive dependency weight would normalize to zero, the unsupported weight
range raises `ValueError` instead of silently dropping a missing prerequisite.
Equal subnormal weights remain supported when their normalized shares are
representable. This is an input arithmetic limit, not evidence that a goal is
satisfied or an action is authorized. Iteration residuals remain floating-point
diagnostics, not authority certificates or interval-arithmetic proofs.

Defaults are gamma 0.85, tolerance `1e-8`, 128 iterations, 128 nodes, 256 edges
and eight sources. Absolute L1 residual, the residual-based error bound,
convergence, norm bounds, SCCs and exhausted limits are reported per source.
Graph exhaustion blocks selection; unconverged numerical scores remain explicitly
advisory. Public profiles are bounded to eight atoms/rules/probes, four goals and
128-node, depth-eight requirement expressions. The existing authority checker
retains its twenty-variable limit, including observation facts. No capacity is
silently enlarged or unsupported result treated as a PASS.

Run-level `pressure_exhausted` is the sorted unique union of bounds reported by
every evaluated pressure field, including a final evaluation that selected no
operation. A cached last field does not add duplicate entries, and later fields
cannot erase an earlier exhaustion. Per-source iteration entries retain their
canonical source identities. Convergence uses all the same fields; individual
residuals, limits and evaluations remain in the trace. An empty exhaustion list
does not establish goal completion or imply pressure was evaluated. The audit
checks this summary against the verified fields, and the readable comparison
lists runs with exhausted pressure bounds.
Pressure-session budget exhaustion remains in `stop_reason`, including when no
field could be evaluated.

## Controllers and fairness

The existing deployment B0 is unchanged and remains covered by its regression
suite. The new reasoning B0 and B3 reuse its public `Candidate`/`Frontier` types
and one shared `enumerate_work` function. Exact current premise aliases and rule
revisions bind inference candidates. Observations are declared capabilities,
not promised answers. Both controllers see the same candidates, public facts,
constraints, goals, observation capabilities and operation costs at an identical
snapshot. Discovery is recomputed and charged to each controller.

When several current supports establish a premise, the shared frontier chooses
one with no scheduled expiry first, then the latest exact integer expiry, then
the public alias as a deterministic tie-breaker. No finite timestamp stands in
for absence of expiry, and timestamps are not converted to floating point. Each
AND premise retains its own exact selected alias. Absence of scheduled expiry is
not a durability guarantee: revocation and relevant revisions still invalidate
bound requests and certificates through the existing authority checks.

Public support references remain stable for the session. Generated operation
names skip every occupied alias or evidence name, including revoked support and
evidence retained after an unsuccessful admission. An observation cannot reuse
an inference's reference; it is rejected before any authority write. Repeating
an unchanged observation retains the same evidence and belief identity through
the existing authority APIs. This namespacing rule does not resume or reconcile
interrupted sessions.

Reasoning B0 uses dependency-aware best-first conditional planning over the
finite fact state space. It keeps all AND premises, coherent OR routes, shared
prerequisites, public joint constraints and declared costs. It ranks weighted
unresolved goal value per minimum conditional remaining work. Positive future
probe answers are possibilities, not accessed hidden answers or calibrated
probabilities. Plans are optimistic about future support and observation timing;
actual results trigger full recomputation and remain subject to authority.

B3 computes the typed field and uses a heap directly, ranking candidate pressure
per declared operation work, with the same deterministic public tie-breakers.
It does not multiply goal importance again. Neither controller reads evaluator
state, future events or outcome labels. Runtime modules cannot import the
evaluator. The evaluator passes a narrow read/execute port; this is a trusted
Python interface, not an OS isolation or hostile-code security claim.

`ranking-isolation.json` runs both ranking paths against exactly the same initial
snapshot and candidates. Its separately recorded diagnostic work never feeds
episode choices. Each recorded live frontier is also recomputed from its saved
public snapshot. Once choices differ, subsequent states may legitimately differ.
In the rich episode, the routes initially tie on total declared work: B0's public
tie-breaker selects `detour`, while B3's pressure rank selects `shared`. A separate
cost-sensitivity test makes the direct route cheaper and verifies B0 switches to
`shared`; that test modification is not used in the comparison episodes.

## Episodes and budgets

The frozen development cases are in `validation_lab/pressure_episodes.py`:

- **Competing routes:** two certified inference routes to an answer, missing
  measurement evidence, a prerequisite shared with a side goal, and revocation
  of the initial seed support at logical tick four. Observation availability is
  delayed by two or three ticks according to the seed. Revocation happens between
  the public read and execution, producing a stale request; fresh evidence and
  actual re-derivation are needed. No inference result is scripted.
- **Simple control:** one available rule application followed by one outcome
  observation. Both controllers should perform the same useful work.

The public goal monitor requires the supported result and one direct exact-product
sample. The independent evaluator checks the inferred result against its finite
truth interpretation. External verified-result loss and authority-certified
observed loss are reported separately. This is an epistemic result episode, not
a deployment action or a multi-sample health/durability claim.

| Configuration | Requests | Operation work | Observation work | Wall cap |
| --- | ---: | ---: | ---: | ---: |
| work-8 | 8 | 16 | 16 | 30 s |
| work-16 | 16 | 32 | 16 | 30 s |
| time-100ms | 16 | 128 | 64 | 100 ms |
| time-500ms | 16 | 128 | 64 | 500 ms |

Both variants receive identical limits within each pair. Discovery has a
4096-visit session limit; B0 has 65536 search-state visits, and B3 has 8192
numerical iterations. These algorithm-specific bounds are explicit safety limits,
not assertions that a search visit equals a pressure iteration. The common
operation budgets and measured wall caps provide the comparison axes. In-flight
certified operations are never interrupted to enforce time; overrun is reported.
No training or controller-specific tuning runs are used.

The `pressure-work-public/v1` subset requires rule and probe costs to be exact
integers from 1 through 100 work units. Floats (including `1.0`), booleans,
nonfinite values and out-of-range integers are unsupported and rejected before
opening an authority session. No rounding or clamping occurs. Every inference,
probe and monitor consumes its declared operation work; probes also consume their
declared observation work, and monitoring consumes one unit of each. Budget
counters and saved-run audits therefore use exact integer counts. Pressure values
and measured elapsed times remain distinct from these declared work units.

All outcomes use the same sixteen-tick evaluation horizon and fixed goal weights.
When a controller stops, time and exogenous support changes continue, but it gets
no free inference or observation. This evaluation tail is timed and accounted
separately. Budget curves include unfinished and negative results. Wall-capped
outcomes can vary with host load and are not bitwise reproducibility claims.

## Artifacts and measured costs

The command writes:

- `configuration.json`: complete public profiles, evaluator episodes, seeds and budgets.
- `report.json`: source Git revision and file hashes, dirty-tree inventory,
  configuration digest, platform, selections, external/observed outcomes, failures,
  cost counters, paired differences, limits, convergence and unsupported capabilities.
- `ranking-isolation.json`: identical-snapshot candidate sets, both ranking paths and costs.
- `<run>/trace.jsonl`: pre-execution selections, full public snapshots, rankings,
  pressure/source diagnostics, receipts and stop reasons.
- `<run>/admission.db`: the real certified command/certificate/support/goal journal.
- `comparison.md`: readable paired results and limitations.
- `bundle.json`: exact SHA-256 inventory of required report/configuration/ranking,
  trace and closed authority-journal files.
- `audit.json`: post-run reproduction and consistency checks, with audit elapsed
  time recorded separately from controller costs.

Timings use a monotonic nanosecond clock. Candidate discovery, snapshot loading,
ranking, pressure graph construction, pressure solve/diagnostics, actual inference,
certification/commit checks, SQLite append/commit persistence, authority bookkeeping,
controller elapsed time, process CPU time and complete run elapsed time are
reported. Pressure iteration timing includes routing validation and SCC diagnostics.
Certification and authority timing exclude the nested measured persistence time.
Execution time is inclusive and must not be added again to its component times.
Setup, evaluation-tail costs and remaining controller overhead are separate.

Peak memory, GPU attribution (no GPU is used), individual fsync/byte attribution,
OS scheduling attribution and real external sensor latency are unmeasured.
Trace serialization and evaluator observation checks are included in total time
without separate attribution. SQLite initialization before its timing hook is
included in setup elapsed time. Avoided inference alone is not a cost saving claim.

Source/configuration bindings reproduce semantic work-limited runs. Authority IDs
and timing are intentionally not promised byte-for-byte across fresh authorities.
Existing directories are refused: this adapter does not introduce recovery or
weaken the existing explicit handling of interrupted operations.

## Auditing saved results

The comparison command now automatically seals and audits a completed bundle.
Source inputs are hashed before execution and checked again before sealing; a
source change during execution fails the command. Failed or interrupted runs do
not acquire a passing audit. The audit is a bounded evaluator addition; it does
not change B0/B3, their budgets, the episodes, admission or recovery behavior.

To check a saved bundle again without modifying it:

```bash
uv run --no-project python -m validation_lab.audit_pressure_comparison artifacts/pressure-comparison
```

The auditor requires matching local source inputs and verifies the complete
episode/seed/budget/controller matrix. It checks the artifact inventory, frozen
configuration, public frontiers, both ranking paths, pressure fields, selected
operations, work and stop accounting. It replays the recorded requests through
fresh temporary certified authorities, checking snapshots, rejection statuses,
external outcome histories, the evaluation tail and integrated loss. It also
replays copies of the saved journals to check belief history, current support,
receipt belief references and recorded goal-event IDs. Original files and
SQLite sidecars remain untouched. Paired differences, M09, same-snapshot ranking
diagnostics and the readable report must agree with the checked results.

Authority work counts are checked at each recorded phase boundary. Setup,
controller execution and the evaluation tail must report the exact replayed
inference, certificate and journal-command counts. The audit rejects transfers
between phases even when the total balances, as well as invented or omitted
counters. Controller counts include clock advances and other authority commands
outside individual operation receipts; every receipt's counter inventory is
checked separately. Timing remains measured data subject to consistency checks.

Fresh authorities issue different opaque goal-event IDs. Fresh-run comparison
normalizes those IDs to counts while retaining all other snapshot fields;
the original journal replay verifies the recorded IDs exactly. Replay uses the
existing certified authority and ranking implementations, so it is a consistency
and reproducibility check, not a second independent inference implementation.
The existing rational numerical reference and independent outcome interpreter
remain separate checks.

Elapsed measurements are checked for consistent categories and nonnegative
accounting; audit time is never charged to B0/B3. Historical wall times cannot
be reproduced or authenticated, and a wall-capped selection is replayed as saved
without pretending that today's machine load will make the same stop decision.
The hash inventory detects changes relative to its contents; it is not publisher
authentication. The evaluator remains inside the existing trusted boundary.

After committing the measured source, optionally bind every recorded source hash
to that Git commit as well:

```bash
uv run --no-project python -m validation_lab.audit_pressure_comparison artifacts/pressure-comparison --source-commit HEAD --output artifacts/pressure-source-audit.json
```

`--output` must name a new file. The original run-base revision and dirty-tree
inventory remain in `report.json`; `verified_source_commit` in this separate audit
is set only after all source blobs match. An older bundle without `bundle.json`
must be rerun with the documented comparison command; the auditor does not repair,
resume or reseal it. Audit failures print JSON and exit nonzero.

## Checking fresh-run repeatability

```bash
uv run --no-project python -m validation_lab.repeat_pressure_comparison --output artifacts/pressure-repeatability
```

This bounded evaluator command runs the unchanged matrix twice in separate Python
processes, using fresh authorities, and audits both resulting bundles before
comparing them. Defaults remain seeds 7 and 18, two episodes, four budgets and
both controllers: 64 controller runs in total. It writes the two complete bundles,
child-process logs, `repeatability.json` and `repeatability.md`. Existing output
directories are refused, and a failed child is retained without automatic retry.

For the work-limited configurations, the check requires identical selected
operations, public snapshots, ranks, pressure diagnostics, work counts, rejection
statuses, outcome histories and stop reasons. Only measured durations and opaque
authority IDs are normalized. Both bundle audits first verify exact identity
bindings, pressure epochs and original journal event prefixes. Different source
inputs or configurations are refused, and copied bundles cannot count as repeats:
their authority identities must be disjoint. This checks evidence reuse within the
trusted evaluator boundary; it does not attest execution against a hostile writer.

Wall-limited runs retain their measured variations in selections, costs and
outcomes. They are reported as `MATCH` or `OBSERVED_VARIATION`, without an equality
requirement. If a work-limited run reaches its wall safety cap, that comparison is
`INCONCLUSIVE`; two equally truncated runs cannot establish work repeatability.
The overall exit status is 0 for passing work comparisons, 1 for a failure and 2
for inconclusive work comparisons. Failures take precedence over inconclusive
results. No neutral or negative B3 result is discarded.

Already generated bundles can be checked without rerunning the controllers:

```bash
uv run --no-project python -m validation_lab.repeat_pressure_comparison --bundles artifacts/pressure-repeatability/repeat-1 artifacts/pressure-repeatability/repeat-2 --output artifacts/pressure-repeatability-recheck --source-commit HEAD
```

The output must be new and outside both input bundles. This performs fresh audits;
it does not trust their cached `audit.json` files. `--source-commit` is optional and
verifies all 71 comparison source inputs plus the separate repeatability checker
against the requested commit. The repeatability report records that checker's
hash and revision, both bundle audit bindings, semantic hashes, bounded difference
paths, complete controller cost categories and the separate experiment/verification
elapsed times. The repeated-run tooling does not change the original bundle schema
or source inventory. Controller budgets never include audit costs.

Two repeats establish only bounded development repeatability. They do not establish
statistical significance, a B3 speedup, generalization, process security isolation,
or completion of the broader benchmark/transport design.

## Checks and result interpretation

```bash
uv run --no-project python -m unittest tests.test_pressure tests.test_pressure_comparison -v
uv run --no-project python -m unittest tests.test_pressure_audit -v
uv run --no-project python -m unittest tests.test_pressure_repeatability -v
```

Independent small-instance checks solve the linear system with rational Gaussian
elimination, not the runtime iteration algorithm. Tests cover unchanged views,
duplicate paths/sources, grounded and ungrounded cycles, missing AND prerequisites,
OR branches, stranded demand, coverage overlap/expiry, observed relief, policy,
rule, time and support revisions, graph/iteration/session bounds and unit conversion.
They also verify unchanged numerical belief values, certificates/reservations and
goal state under pressure/priority changes, plus actual invalid/stale gate rejection.

M09 mutates the actual source-injection line to accumulate its previous demand.
Two reads of the same snapshot produce 10 then 20, while the independent reference
and production solver remain at 10. M12 remains scheduled with transport.

The development run completes all 32 controller runs (16 pairs). At eight requests,
B3 leaves external weighted loss 6 versus B0's 7 in the rich episode. At sixteen
requests, both finish in thirteen requests, but integrated loss is **78 for B3
versus 72 for B0**, for both seeds. The simple control has identical two-operation
traces and integrated loss 1. Pressure adds measurable construction/iteration
work; observed elapsed differences are noisy and do not establish a performance
advantage. The final generated report records the actual wall-capped outcomes.

Validation of the full regression suites is recorded in `IMPLEMENTATION_PLAN.md`.
The final run passes 32/32 configurations, audits 155 live frontiers and four
identical-snapshot comparisons, and detects M09. It retains three UNKNOWN and
twelve STALE operation replies, with no harness failures. All recorded fields
converge. Maximum atomic-operation wall-cap overrun is 71.49 ms, so wall-cap
comparisons must use the actual elapsed times rather than assume exact cutoffs.
The 851-test default, 85-test native and 15-check reference suites pass; all 25
affected tests pass again after the final bounded-route diagnostic correction.

The subsequent saved-bundle audit increment passes 16 new audit tests, 43 focused
tests in total, 70 applicable B0/deployment/admission/recovery regressions and 15
reference checks. Its fresh 32-run matrix reproduces 159 saved selections and
verifies 71 source inputs; audit time is 19.88 seconds, separately accounted.
There are no remaining failures or skipped tests in these runs. Full default and
native suites were not rerun for this evaluator-only addition. The prior complete
suite results above remain historical evidence, not a claim of a new full run.
The frozen work-limited outcomes are unchanged. New artifacts are under
`artifacts/pressure-comparison-audited/`.

The fresh-run repeatability extension passes 14 new tests, 43 existing focused
regressions and 15 reference checks. Its two full matrices pass 64 controller
runs across distinct authorities, with 154 audited selections per bundle. All 16
work-limited repeat comparisons match; three wall-limited comparisons show
semantic variation. None of the work comparisons failed or became inconclusive.
M09 is detected in both bundles, and the prior neutral/negative work-limited
outcomes are unchanged. Full default/native and unrelated deployment/recovery
suites were not rerun for this evaluator-only extension. Results are in
`artifacts/pressure-repeatability/repeatability.md` and `repeatability.json`.

The exact stored-routing correction passes 61 focused tests, 70 deployment/
admission/recovery regressions and 15 reference checks, with no remaining failures
or skipped tests. Nine refreshed corpus receipts verify without changing fixture
semantics. The corrected 64-run repeatability experiment passes all sixteen
work-limited comparisons and retains seven wall-limited variations. Independent
exact-rational checks confirm the routing bound in all 183 recorded pressure
fields. Rich work-16 B3 pressure construction/solve time is 17.73–33.60 ms,
including normalization; work-limited outcomes are unchanged. Full default/native
suites were not rerun for this isolated calculation fix. New artifacts are under
`artifacts/pressure-routing-repeatability/`.

The shared support-lifetime correction passes 67 focused tests, 70 deployment/
admission/recovery regressions and 15 reference checks. Six new tests cover exact
large integer expiries, absent expiry, deterministic ties, whole AND bundles and
identical B0/B3 frontiers. Actual certified inference preserves a selected proof
when an unused competing support expires, while revocation rejects old bindings
and certificates even at high goal priority. Fresh finite-support fallback still
expires through the existing authority. All nine refreshed corpus receipts verify
with unchanged fixture semantics. No failures remain or tests were skipped in
these runs; full default/native suites were not rerun for this isolated correction.

Its 64-run experiment passes all sixteen work-limited repeat comparisons and
retains five wall-limited variations. Both bundles detect M09 and all 189 pressure
fields converge. The neutral/negative work-limited outcomes are unchanged; rich
work-16 B3 pressure construction/solve time is 14.78–21.49 ms. Complete costs and
traces are under `artifacts/pressure-support-repeatability/`, including
`repeatability.md` and `repeatability.json`. These are development measurements,
not evidence of a performance improvement.

The integer-work contract correction passes 71 focused tests, 70 deployment/
admission/recovery regressions and 15 reference checks. Four new tests exercise
unsupported cost rejection before authority creation, eight certified/audited
runs at the supported cost boundaries and five budget-stop cases per controller.
All nine refreshed corpus receipts verify with unchanged fixture semantics. No
failures remain or tests were skipped in these runs. Full default/native suites
were not rerun for this isolated input-contract correction.

Its 64-run experiment passes all sixteen work-limited repeat comparisons and
retains eight wall-limited variations. Both bundles detect M09 and all 181 fields
converge. Work-limited outcomes are unchanged, including B3's worse rich-episode
integrated loss. Rich work-16 B3 pressure construction/solve time is 15.24–30.95 ms.
Reports, complete measured costs and traces are under
`artifacts/pressure-cost-repeatability/`. The plan and manifest record the scope;
these measurements do not establish a performance improvement.

The exhaustion-reporting correction passes 78 focused tests and 15 reference
checks. Seven new tests exercise final unselected graph/iteration bounds, unique
summaries, preservation of earlier exhaustion after later convergence, no-field
cases, readable output and audit rejection of missing or invented bounds. The
default-limit graph witness issues no operation and retains four units of
unresolved loss. All nine existing corpus receipts verify without regeneration;
runtime controllers, authority, frozen episodes and fixtures are unchanged.
Full default, native integration and unrelated deployment/admission/recovery
suites were not rerun for this evaluator-only correction. No failures remain or
tests were skipped in the executed suites.

Its 64-run comparison passes all sixteen work-limited repeat checks and retains
five wall-limited variations. Both bundles detect M09, and all 186 fields in the
frozen comparison converge. Work-limited outcomes remain unchanged, including
B3's worse rich-episode integrated loss. Rich work-16 B3 pressure construction/
solve time is 15.43–24.90 ms. Reports and complete measured costs are under
`artifacts/pressure-exhaustion-repeatability/`; these measurements do not establish
a performance improvement.

The public-reference correction passes 83 focused tests, 70 B0/deployment/
admission/recovery regressions and 15 reference checks. Five new tests cover
certified and audited collision runs for both controllers, rejection of reference
rebinding before authority writes, unchanged repeated observation, revoked names
and evidence retained after failed admission. Nine refreshed corpus receipts
verify with unchanged fixture semantics and design hashes. No failures remain or
tests were skipped in these runs; full default/native suites were not rerun.

Its 64-run experiment passes all sixteen work-limited repeat checks and retains
five wall-limited variations. Both bundles detect M09, and all 187 recorded fields
converge. Work-limited work counts and outcomes match the previous frozen run,
including B3's worse rich work-16 integrated loss (78 versus B0's 72) and the
neutral control. Rich work-16 B3 pressure construction/solve time is 14.53–23.68 ms.
Reports, traces and complete measured costs are under
`artifacts/pressure-reference-names-repeatability/`. These measurements do not
establish a performance improvement.

The phase-count auditing correction passes 88 focused tests and 15 reference
checks. Five new tests reject nineteen corruption cases, including balanced
cross-phase journal transfers, invented work and missing/extra counters. Real
B0/B3 runs with stale replies and evaluation tails still audit. Nine existing
corpus receipts verify without regeneration; runtime and frozen episodes are
unchanged. No failures remain or tests were skipped in the executed suites.
Full default, native integration and unrelated deployment/admission/recovery
suites were not rerun for this evaluator-only correction.

Its 64-run experiment passes all sixteen work-limited repeat checks and retains
six wall-limited variations. Both bundles detect M09, and all 187 recorded fields
converge. Work counts and outcomes remain unchanged under work limits: rich
work-16 integrated loss is 78 for B3 versus 72 for B0, and the control is neutral.
Rich work-16 B3 pressure construction/solve time is 17.17–25.89 ms. Reports, traces
and complete measured costs are under `artifacts/pressure-phase-counts-repeatability/`.
These measurements do not establish a performance improvement.

This milestone stops here. Adaptive transport, learned conductance, generalized
recovery, numerical PLN scheduling, broader channels, evaluator OS isolation,
family-complete fixtures and large-scale claims remain deferred.
