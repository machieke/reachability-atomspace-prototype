# Decision-value validation v1 — committed protocol

This is an evaluator-only engineering experiment. Runtime
`3e8fd7be56362ed21944636bbe505b6a4a7aac6f` and projection
`8542ad538649fd0b967c7047057dd5cebf831be8` remain byte-for-byte frozen, as do
both prior review bundles. No policy, routing, gamma, candidate discovery,
normalization, hard gate, observation, source-accounting or recovery contract
changes. No policy tuning on development or confirmation results is permitted.

## Inventory and information boundary

`inventory.json` is the full, deterministic machine-readable inventory generated
by `validation_lab.decision_tasks`: 48 parents, eight in each of OR, AND, shared
prerequisites, real depth, budget sensitivity and completion/competition. Parent
indices 0–4 are development (30); 5–7 are locked confirmation (18). These are
structurally varied declared templates, not a random population or statistical
power claim. Seed 0 means no stochastic sampling. Twelve identifier siblings
(indices 1 and 6 per family) and six dominated-option siblings (index 0) stay
with their parent and are excluded from independent-parent headline aggregates.
No difficult case can be replaced after policy measurement.

Every task uses the narrowly versioned `decision-task/v1` public descriptor:
complete rules and clauses, costs, goals/priorities, initial signed facts,
complete physical assignment, permanent supports, no future changes, no probes,
immediate truthful goal-monitor response and no commitments. Both live
controllers receive the full descriptor as `public_port.task_contract`; common
ranking wrappers receive the same descriptor. Existing rankers ignore the new
metadata; their algorithms are unchanged. The world fixture is a deterministic
serialization of that public contract, not an extra evaluator-only future.
Q/V labels, witnesses and evaluator answers never enter a policy or authority.
The original hidden-event episodes and schemas remain unchanged.

Proof identities are quotiented by the reference only because this fragment
explicitly guarantees future permissions depend on propositions and joint
consistency, not proof identity. Actual execution still uses exact support
handles, revisions, certification and all ordinary admission gates. The
reference state includes signed established supports, permanent validity tag,
monitored goals, logical tick, remaining requests, operation and observation
work. It does not merge states merely because their fact sets coincide.

## Objective, budgets and stopping

The primary objective is the frozen evaluator's sum of externally unresolved
weighted goal loss at ticks 0 through 15. A conclusion must be established and
physically true to remove external loss. Authoritatively observed/certified
relief requires a real monitor operation and remains a separate measure. Report
terminal external loss, terminal certified loss, outstanding goals and
commitments, operation/observation work, requests and measured cost categories
separately. There is no arbitrary loss/time/credit scalar.

The two complete ComparisonBudget vectors are:

- `requests-4-work-4`: actions 4, operation_work 4, observation_work 3,
  candidate_visits 4096, ranking_states 65536, pressure_iterations 8192,
  wall_ns 30000000000.
- `requests-8-work-12`: actions 8, operation_work 12, observation_work 3,
  candidate_visits 4096, ranking_states 65536, pressure_iterations 8192,
  wall_ns 30000000000.

Each request advances one logical tick; operation-work credits are not simulated
durations. All cells use the same 16-tick evaluation horizon, including an idle
tail after the controller stops. STOP is voluntary permanent termination; it
confers no inference, observations or monitoring during that tail. There is no
wait-and-resume operation. The old historical name `work-8` means eight requests
and its separately declared operation-work budget, never eight work credits.

The exact reference optimizes the semantic request/work limits. Auxiliary
candidate/solver/wall limits constrain policy computation, are reported in full,
and are not charged to a reference selectively; reference work is entirely
offline. Auxiliary exhaustion or a wall stop must remain visible. The semantic
model requires no history of discarded ranking computation for future
admissibility. It is not a scalable runtime competitor.

Secondary ordering selects a witness continuation only: lower terminal
certified loss, lower operation work, fewer requests, then lexicographic action
sequence. The reported primary-optimal action set includes *every* action with
minimum integrated external loss, including STOP when applicable. Secondary
criteria do not narrow that set and do not change decision regret.

## Exact engines, feasibility and explicit bounds

`decision_reference.py` independently encodes Boolean satisfaction, joint
consistency by complete assignments, rule readiness, monitoring, operation
charges and external loss. It imports only the standard library, never runtime
truth helpers, candidates, B0, pressure or normalization. The complete memoized
DP calculates every admissible first-action Q*, V*, complete primary-optimal set
and witness continuation. `decision_enumeration.py` is a second independent
standard-library implementation using complete history enumeration, an iterative
Boolean interpreter and no shared transition code or memoization. Cross-check
all initial Q labels and every common sampled state, not just selected actions.

Bounds: six atoms, three goals, eight rules (cohort maximum six), eight requests,
16 evaluation ticks, 4096 DP states, 32768 DP transitions, 16 MiB conservative
allocation accounting, 100000 history-enumeration nodes per query. Allocation
charges include state/label/witness estimates; this is an explicit conservative
work/memory accounting limit, not measured process RSS. Actual peak RSS is
unmeasured. Enumerated history depth is bounded by eight requests and only
first-action minima plus the current path are retained. Integer loss/weights
make exact primary comparisons possible; runtime float serialization represents
these small integers exactly.

`feasibility.json` records all 132 reference-only cells before policy measurement:
all solved exactly and matched complete enumeration; maxima 42 states,
96 transitions, 378652 accounted bytes and 867 enumeration nodes. A temporary
preflight parity check found an integer-versus-float JSON comparison mismatch;
the bridge now compares numerical loss equality without altering either engine
or runtime. No policy outcomes informed this correction or cohort selection.

On exhaustion report REFERENCE_EXHAUSTED and the bound; do not emit a fabricated
optimum or substitute another task. Retain the inventory and censored artifacts.
This fixed exact experiment fails closed before policy comparisons if initial
DP labels are incomplete. Any measured-attempt harness/reference defect must
retain the failed attempt and use an explicitly identified corrected source
revision; it must never be silently retried.

## Ranking isolation, trajectories, ties and witnesses

Primary policies: B0, B3-normalized-both, B3-normalized-route,
B3-normalized-queue, B3-normalized-neither. Closed-loop policy order rotates left
by cell index modulo five. They use the same public candidates, task descriptor,
budgets and authority APIs. States may subsequently diverge. Raw policies are
regression/diagnostic references, not additional primary contenders.

Common-state sampling is independent of all policies: the root plus the
lexicographically first reachable DP State at each tick 1, 2 and 3 that has at
least two non-STOP admissible actions. Lexicographic ordering uses the complete
State tuple. Recover a feasible prefix with lexicographic breadth-first
traversal, without consulting Q/V or policy choices. Maximum four states per
cell. Siblings map the parent's prefixes, preserving paired semantic states.
Each prefix executes through the certified runtime, then every policy ranks the
identical snapshot and affordable candidates with identical remaining semantic
budgets. Each query starts with full shared auxiliary computation/wall budgets;
common-state ranking is diagnostic, not a continuation with unreported prior
policy compute. Discovery is measured once and charged equally to each policy;
prefix execution, label construction and audits are separate offline costs.

The frozen ranking tuple and final candidate-ID ordering are unchanged. Near
ties are diagnostic only: primary score distance at most twice pressure's L1
error bound plus 1e-12 (B0 uses 1e-12). Retain exact ranks and all exact reference
optima; selecting a different arbitrary ID among optimal actions is correct.
Identifier siblings measure tie sensitivity. A dominated sibling adds a real
rule with the same premise/conclusion and cost one greater than an existing
rule. Its candidate set can change; the old optimal plan must remain feasible
and its exact optimum must remain unchanged. Do not collapse real routes.

Replay each cell's canonical initial optimal witness and, for the six parent
index-0 controls at both budgets, all initial Q witness continuations,
deduplicated by the complete action sequence. Every selected operation passes
through the actual candidate interface and certified authority. Check the
independently predicted frontier, observable state, per-goal external loss,
monitor status and integrated loss at every transition. Retain actual receipts,
traces and journals. Labels confer no execution authority.

For each common choice and closed-loop selection retain Q/V, complete optimal
set, every first-action continuation, candidate scores, full budget vector,
selected regret and subsequent actual receipt/outcome. Episode gap is total
closed-loop integrated loss minus initial V*. Never sum overlapping decision
regrets to attribute an episode difference. Terminal STOP is labeled separately. Selection labels report auxiliary budgets after
that ranking pass; remaining wall time is null because the frozen trace does not
record a per-selection clock. The full wall limit and run elapsed time remain
reported. Common queries report their full fresh wall allowance.
The original rich hidden-event episode has no same-information Q/V label here;
its previous descriptive comparison and loss decomposition remain in the
preserved reviews. No hindsight bound is mixed into the headline.

## Execution, validation and publication

One command, from the committed source with Python 3.11:

```sh
uv run --no-project python -m validation_lab.decision_comparison --output artifacts/decision-value-v1/comparison
```

The output directory must be new. The command verifies frozen and committed
source digests; writes the complete configuration, reference labels, common
state traces and ranks, 660 closed-loop traces/journals/results, selected
certified witness checks, readable comparison and checksum inventory; then
independently replays/audits the artifacts and writes audit.json. Failed attempts
remain on disk with FAILED.json. Audit separately with `--audit DIRECTORY`.

Report reference coverage and second-engine checks; agreement, regret and episode
gap by parent partition/family/budget; identifier and dominated siblings
separately; favorable/neutral/unfavorable results versus B0 for every placement.
Retain source ledgers, convergence/bounds, failed runs, stale/unknown replies,
outstanding goals/commitments and all timings. Inference, certification,
persistence, discovery, ranking, normalization, graph and pressure-solve costs
remain visible. Normalization plus graph equals pressure construction;
execution includes authority categories. Do not double count inclusive fields.
Reference generation and artifact audit have their own elapsed times. Peak RSS,
OS scheduling attribution, individual SQLite bytes/fsync latency and real sensor
latency remain unmeasured. Single-run times are descriptive, not causal or
statistical evidence. No trace-level confidence intervals or sibling replication
claims are permitted.

Run new reference/harness tests and applicable admission, deployment, B0,
pressure/source-accounting, projection invariance, comparison/audit regressions
and standalone numerical checks. Record exact commands, source, elapsed time,
pass/fail/skip counts and logs. Any omitted full-suite/native/recovery tests must
be explicitly identified; historical passes are not newly executed checks.
Publish a source-bound archive with source/configuration, traces, journals,
labels, witnesses, test logs, readable interpretation and artifact checksums.

Stop after this bounded fixed-policy evidence is published. No adaptive
transport/M12, learned conductance, ECAN, new heuristics, broader normalization,
native PLN scheduling, recovery expansion, caching, scale or duration model.
The later choice among pressure-guided search, a simpler scheduler, or thin
numerical-PLN scheduling is outside this increment.
