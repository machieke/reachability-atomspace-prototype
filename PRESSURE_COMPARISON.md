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

Defaults are gamma 0.85, tolerance `1e-8`, 128 iterations, 128 nodes, 256 edges
and eight sources. Absolute L1 residual, the residual-based error bound,
convergence, norm bounds, SCCs and exhausted limits are reported per source.
Graph exhaustion blocks selection; unconverged numerical scores remain explicitly
advisory. Public profiles are bounded to eight atoms/rules/probes, four goals and
128-node, depth-eight requirement expressions. The existing authority checker
retains its twenty-variable limit, including observation facts. No capacity is
silently enlarged or unsupported result treated as a PASS.

## Controllers and fairness

The existing deployment B0 is unchanged and remains covered by its regression
suite. The new reasoning B0 and B3 reuse its public `Candidate`/`Frontier` types
and one shared `enumerate_work` function. Exact current premise aliases and rule
revisions bind inference candidates. Observations are declared capabilities,
not promised answers. Both controllers see the same candidates, public facts,
constraints, goals, observation capabilities and operation costs at an identical
snapshot. Discovery is recomputed and charged to each controller.

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

## Checks and result interpretation

```bash
uv run --no-project python -m unittest tests.test_pressure tests.test_pressure_comparison -v
uv run --no-project python -m unittest tests.test_pressure_audit -v
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

This milestone stops here. Adaptive transport, learned conductance, generalized
recovery, numerical PLN scheduling, broader channels, evaluator OS isolation,
family-complete fixtures and large-scale claims remain deferred.
