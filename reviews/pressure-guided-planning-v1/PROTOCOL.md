# Bounded pressure-guided planning v1 — preregistration

This is a new experiment after publication `2dfe184`; accepted and failed
measurement artifacts from that publication remain immutable. Frozen runtime
`3e8fd7b`, scoped projection `8542ad5`, corrected decision harness `7bf11d5`
and the new implementation revision are separately bound. No policy promotion.

## Model, objective and algorithms

Production code is isolated in `experimental_planning` and imports no evaluator.
It accepts only the existing public `decision-task/v1` permanent static contract,
with horizon 16, one tick per real request, no probes/events/commitments. An
explicit immutable state contains established propositions, predicted monitored
goals, tick, all remaining semantic budgets and exact model/root bindings.
Hypothetical supports and relief tokens are prefixed `prediction:`. Only live
candidate references and exact live snapshot bindings can execute through the
unchanged certified authority. A prediction has no authorization power.

Primary objective: integrated external unresolved weighted loss over ticks 0–15.
Common secondary order: terminal certified loss, operation work, requests,
lexicographic complete action sequence. Observation work is separately reported.
Monitoring consumes one request, one operation and one observation unit and one
tick. No primary reward for certification. STOP has its entire unresolved tail.

All planner arms use the same explicit-stack depth-first enumeration without
transpositions, pruning, rollouts or oracle stopping. Every visited prefix is
closed with STOP. Start with legal STOP; replace only under the common objective.
A bound returns the best fully evaluated feasible incumbent, never impossibility
or certified success. Complete-search claims concern one optimal witness only.

Only child ordering differs:

* PLAN-neutral: lexicographic semantic action, then candidate identity.
* PLAN-B0-order: frozen B0 rank tuple, then candidate identity.
* PLAN-pressure-order: frozen scoped-normalized B3 `both` at each speculative
  state, frozen rank tuple then candidate identity. Pressure is neither reward,
  admissible bound nor incumbent selector.

Direct B0 and direct B3-normalized-both are unchanged controls. Full public task,
snapshot, capabilities and current frontier are available equally. Evaluator
Q/V, witnesses and private state never enter planner code.

After actual execution, replan. A suffix is retained only in memory, after its
predicted state/budgets match the real observation, old supports remain exact,
immutable policy/dependency bindings agree, and the clock's one expected revision
increment matches. Bind to that exact observed snapshot. Revalidate all suffix
steps and costs before using it in the next query; charge separately. Restart,
unsupported change or incompatible binding drops it. No coverage or commitment.

## Bounds and accounting

Primary ladder: 1, 4, 16, 64 attempted simulated transitions **per decision**.
An attempt is charged immediately before transition validation, including rejects.
Each visited state receives a complete successor enumeration before ordering;
candidate visits, consistency checks, sorting, interrupted expansions and all
auxiliary B0/pressure work are separate counters. The final visited state gets
its STOP closure before the attempt cap. Equality with the cap may conservatively
report exhaustion even when that final state would be terminal.

Identical independent per-query auxiliary caps: 1,000,000 candidate visits,
2,000,000 B0 rank states, 262,144 pressure iterations, 1,000,000 normalization
visits, 32 MiB conservative serialized memory accounting and 5 seconds elapsed.
Pressure uses the unchanged per-field limits (128 nodes, 256 edges, 8 sources,
128 iterations, tolerance 1e-8). Normalization uses frozen defaults. Any incomplete
rank/field/normalization/model expansion stops search with its incumbent; no
invented scores or partial ordering. Atomic work is checked at boundaries and any
wall overrun is reported. Memory accounting is not a measured peak-RSS claim.

Semantic budgets remain requests-4/work-4/observations-3 and
requests-8/work-12/observations-3. The frozen direct controllers retain all their
original auxiliary limits, including 30-second session wall cap and 4096 real
candidate visits. Planners have the same real session limits, plus separately
charged speculative computation above. Equal successor counts do not mean equal
cost. All timing categories are retained, with inclusive categories identified.
No controller receives extra environmental work for simulated requests.

## Cohort, sampling and rotation

Full primary matrix: all 66 inspected old tasks (48 parents, 12 identifier
siblings, 6 dominated-route siblings), plus the 12 new parent structures in
`validation_lab/planning_tasks.py`; both semantic budgets; two direct controls
and three planner arms at four caps. This is 156 task/budget cells, 2184 closed
runs. New parents are two per existing family. No policy-based selection or case
replacement. Old confirmation labels are historical: all 66 old tasks are now
inspected diagnostics. Siblings are excluded from parent headline aggregates.

Common-state samples: root plus the same reference-only lexicographic reachable
state at ticks 1, 2, 3 with at least two non-STOP actions used in the prior
preregistration. Sample each task independently by this rule (identifier siblings
may therefore use different lexical strata; only within-task identical-state
claims). Every query receives identical live snapshot, frontier and remaining
semantic budget. Root/sampled queries start without a carried suffix. Shared
live candidate discovery is timed once and charged equally to each query.

Rotate arm/configuration order left by cell index modulo number of arms. Seed 0;
no randomness is used. No tuning on either old or new outcomes. Feasibility is
checked only with the two independent reference engines before measurement.
Reference-exhausted cells remain explicit censored failures, never replacements.

Supplementary equal-wall comparison is locked in `calibration.json` before
policy measurements: policy-free Model construction, full frontier and one
legal transition, 100 repeats on old completion-1, with no ranker or search.
Two per-decision caps are ceil-milliseconds of 10x and 50x the median full
calibration call, each at least 1 ms. Attempts limited to 100000, other auxiliary
caps identical. This small matrix uses exactly 12 new parents, both budgets,
three orderers and two calibrated wall caps, rotating order by cell index.
Direct controls are the unchanged primary results. Timing is supplementary,
single-run, machine-load-sensitive and not a significance claim.

## Validation and analysis

Before measurement: independent model/state/frontier/transition/loss parity;
complete-search optimal witnesses for all arms on existing hand cases; bounded
feasibility and monotone incumbent tests; ordering-path and distinct branch
checks; immutable authority and rejected hypothetical/stale requests; shared
prerequisites; remaining-budget identity; unsupported models and all bounds.
Four deliberate mutants: free unfinished completion, omitted monitoring costs,
omitted remaining-budget cache key, pressure-selected final incumbent. Mutants
are excluded from rankings. New cases receive reference-only feasibility and
production-model parity, not performance-based acceptance.

Report parent/family/old-new/budget/arm/cap, reference decision regret separately
from episode gap, terminal external/certified loss, completed goals, all real
work, speculative counters and costs, bound hits, failures and worst gaps.
Compare planning vs direct, pressure vs neutral, pressure vs B0 ordering, and
larger caps separately. Do not sum decision regret as causal attribution.
At roots, retain every STOP closure and incumbent improvement with attempts and
elapsed time; label work/time to first reference-optimal witness offline only.
Compare expanded semantic states as well as ordering. Preserve premature
monitoring, unaffordable continuation, impossible AND, real depth, dominated
option and identifier tie diagnostics. No retrospective normalizer adjustment.

Run new tests and applicable admission/pressure/projection/source/decision
regressions. Enumerate unrun suites explicitly. Publish input/source hashes,
protocol/calibration, all results/traces/search records/journals, test logs,
failures and a verifier with a fresh-directory audited command. Retain any failed
measurement attempt with a versioned correction. Stop at publication: no
transport, learning, numerical PLN scheduling, generalized recovery, new pressure
formula, new objective, expanded normalization, duration or scale claim.
