# Validation Lab: Reachability, Pressure-Field PLN, and Lifecycle Dependencies
## Dataset, integration-test, and ablation proposal — v0.1

Prepared: 30 September 2026.

**Status:** Proposed research and engineering protocol. This package is not a completed benchmark, an implementation of the cognitive architecture, or a report of measured performance. Its JSON files are illustrative contracts, not an executable environment. The existing reference-check script supplied with the pressure specification is a component-test starting point; it does not replace the integration tests proposed here.

**Design inputs:** `reachability_atomspace_specification.md` and `pressure_field_pln_lifecycle_integration.md` from this conversation. The input hashes are recorded in `manifest.json`.

**Non-negotiable constraint:** Acceptance gates remain hard. All performance baselines preserve the same authoritative admission contract. Deliberately breaking that contract belongs only to isolated mutation testing.

## 1. What the experiment must establish

The research question is not whether the full design can outperform a deliberately weak scheduler on a graph constructed to favor it. It is whether each proposed mechanism provides its claimed benefit, at its actual computational cost, without changing the evidence, authority, or objective it is supposed to serve.

Use a ladder of claims:

1. **Semantic correctness:** accepted transitions satisfy the declared contract; beliefs, contexts, evidence, and lifecycle states are not conflated.
2. **Mechanism correctness:** the implemented pressure, transport, invalidation, and lifecycle algorithms match their mathematical or state-machine specifications.
3. **Computational benefit:** a mechanism improves useful reasoning per unit of total resource consumption.
4. **Decision benefit:** better metareasoning produces lower externally measured goal loss or better decisions, not merely more focused activation.
5. **Transfer:** the benefit survives unfamiliar structures, different dynamics, and a grounded environment.

Passing one level does not imply passing the next. A field can improve premise discovery without improving action selection. A correct lifecycle ledger can improve reliability without improving win rate. Both can still be valuable, but the claim must match the measurement.

### 1.1 Predeclared hypotheses

| ID | Hypothesis | Primary discriminating observation |
|---|---|---|
| H01 | Hard gates remain authoritative under arbitrary pressure and utility. | No unauthorized acceptance or effective execution; valid alternatives remain discoverable. |
| H02 | Attention and pressure cannot manufacture evidence. | Frozen evidence produces unchanged belief revisions despite field perturbations and repeated recall. |
| H03 | Exact dependency maintenance preserves semantics efficiently. | Incremental semantic state matches an independent cold recomputation after each event prefix. |
| H04 | Lifecycle-aware planning avoids redundant work and premature success. | Fewer redundant proposals/attempts, correct outstanding/covered/open loss, and no false relief. |
| H05 | Typed backward pressure improves allocation among inference, observation, action, expansion, and retention. | Lower loss and/or lower total cost than scalar pressure and dependency-aware queues. |
| H06 | Adaptive transport helps on some nonuniform structures beyond best-first search and fixed diffusion. | A beneficial performance/cost frontier on predeclared geometry regimes, with overhead reported elsewhere. |
| H07 | Learned conductance improves future search or decision quality for its declared role. | Held-out improvement under equal training budgets; no unearned evidence or causal credit. |
| H08 | Scoped fields support goal/context switching without belief contamination. | Goal changes modify scheduling, not frozen truth; incompatible contexts do not merge premises. |
| H09 | The system remains responsive to revocations, delays, and concurrency. | Stale permits are unusable; unresolved commitments are reconciled; resource capacity is respected. |
| H10 | Component gains transfer to the user's grounded coordination problems. | Prospective end-to-end improvements with the same local execution heuristics and comparable compute. |

There is no primary metric called “semantic pressure quality” unless a separate, independently justified target is defined. Field concentration is a diagnostic, not an outcome label.

## 2. Benchmark architecture

Build a **versioned generator plus frozen episode packs**, not just a table of atoms with desired answers.

The generator defines task semantics, hidden worlds, observations, actions, deadlines, and constraints. It must not generate labels from the tested pressure or transport algorithm. The same task is rendered into each backend through an adapter.

Use four workload layers:

| Layer | Purpose | Ground-truth source |
|---|---|---|
| A. Finite litmus worlds | Isolate one or a few semantic obligations. | Enumeration, rational arithmetic, independently specified state machines. |
| B. Procedural temporal worlds | Test interactions, search budgets, uncertainty, and learning. | Explicit transition/observation model plus exact small-instance solvers. |
| C. Stateful fault and scale workloads | Test invalidation, races, persistence, numeric stability, and cost. | Event-prefix reference model and operation histories. |
| D. Grounded transfer | Test whether synthetic benefits matter outside the generator. | Environment-authoritative state, legal operations, and observed outcomes. |

For layer D, use the user's Freeciv line as a high-level coordination environment. Keep local tactical heuristics and legal-action execution fixed. The intervention is the proposed reasoning/coordination architecture, not an unrelated change to tactical execution.

Run three modes:

**Conformance mode:** a test driver deliberately constructs operations, queries, and timing races. This guarantees that a dangerous stale certificate is actually exercised rather than hoping the scheduler happens to propose it.

**Controlled replay mode:** every variant receives the same external observations and forced operation history. This isolates state maintenance and selected mechanism outputs. It is not an estimate of the consequences of different policies.

**Closed-loop mode:** the variant chooses actions, observations, and searches. The environment evolves from those choices. This is required for claims about goal achievement or counterfactual decision benefit.

## 3. Unit of data: a partially observed temporal episode

A case has a public portion, an evaluator-only portion, and execution records. Keep the evaluator-only portion outside the agent process and filesystem namespace wherever practical.

### 3.1 Public case

Required content:

- Initial typed propositions, rule schemas, and their explicitly available evidence.
- Contexts, goals, lifecycle schemas, resources, constraints, and allowed capabilities.
- Declared observation interfaces and action contracts.
- Initial knowledge and policy revisions.
- Event-time, arrival-time, and freshness semantics.
- Loss functions, durability predicates, and stopping conditions.
- Resource budgets and any declared information-acquisition costs.

Do not expose future observations, hidden causal parameters, reference plans, motif labels, expected pressure values, or oracle outcomes. A future event script can exist in the environment without being supplied to the agent.

Use neutral identifiers rather than names such as `correct_branch`, `decoy`, or `blocked_answer`. Randomize names independently of outcomes. Natural-language descriptions can be added later, but the first benchmark should isolate symbolic and lifecycle reasoning from language-model parsing.

### 3.2 Evaluator-only case

Store:

- Full world state and transition/observation model.
- Exogenous event schedule and explicitly indexed random variables.
- Admission expectations relative to the evidence available at each event prefix.
- Satisfying assignments, contradiction witnesses, or numerical feasibility witnesses.
- All acceptable answer sets or reference-plan equivalence classes when feasible.
- Small-instance optimal value or a labeled bound where exact solution is unavailable.
- An explicit label-availability mask for delayed, missing, or censored outcomes.
- Split ancestry, topology family, composition signature, and transformation identity.

A reference can be `UNKNOWN` or `NOT_COMPUTED`. Do not present a solver timeout or heuristic answer as an exact oracle.

### 3.3 Execution record

Record every proposed, rejected, reserved, dispatched, observed, and reconciled operation, including:

```text
case_id / parent_instance_id / run_id / variant_id
backend_commit / model_commit / rule_revision / schema_revision
logical_time / arrival_time / scheduler_step
context_id / goal_id / operation_id / attempt_id / idempotency_key
knowledge_revision / policy_revision / field_epoch
premise_revision_ids / lineage_roots / resource_intervals
certificate_subject / individual_checks / joint_check / certificate_digest
pressure_channels / allocated_activation / queue_age
proposal_status / rejection_reason / execution_status
predicted_outcomes / observed_outcomes / label_availability
outstanding_loss / committed_coverage / open_loss
query_cost / inference_cost / field_cost / certification_cost / memory
```

The run logger observes system outputs. It must not silently correct them with oracle values before the assertions execute.

## 4. Independent ground truth

### 4.1 Three notions that must not be conflated

**World truth:** what the simulator's hidden state actually is.

**Epistemic support:** what is justified by the evidence accessible to the agent at a particular revision.

**Contract admissibility:** whether the proposed operation satisfies the declared policy, uncertainty, freshness, and resource checks at execution/commit time.

An authorized uncertain inference can be empirically wrong without violating the inference contract. Conversely, a lucky unauthorized action is still a contract violation. Report these separately.

An omniscient planner may be a useful upper bound, but it is not a fair competitor to a partially informed system. Same-information exact comparators are feasible only in appropriately bounded cases; otherwise label the comparator's information advantage.

### 4.2 Exact fragments

For Boolean worlds, enumerate complete assignments for very small cases and cross-check a subset with an independently encoded SAT/SMT solver. Z3 is an available reference technology; its official guide and repository document its use as a theorem prover and its programming interfaces [S1]. The independence comes from the encoding and reference implementation, not merely from using another library name.

For selected numerical constraints, use rational inputs and exact arithmetic. Store both valid and invalid witnesses, especially near zero margins. Compare floating implementations with scale-aware tolerances or conservative interval bounds; never make a slightly negative reference margin acceptable merely to hide floating-point noise.

For finite monotone rule fragments, compute a complete supported closure without relevance pruning. For alternatives under incompatible assumptions, compare sets of admissible environments or answer sets rather than requiring one arbitrary global closure.

For tiny fully observed planning worlds, enumerate finite-horizon transitions. For tiny partially observed worlds, an exact belief-state policy can be used only when the stated bounds make that practical. Larger cases use external outcomes and properly labeled best-known bounds, not pretend optimality.

### 4.3 Numerical references

The tested implementation of pressure must not also provide the only expected pressure values. On small fixed operators, compare the iterative result against an independent direct solve of `(I - gamma R)p = d`, and verify its residual bound.

For activation, check nonnegativity and conservation across the **complete** ledger: active anchors, reservoirs, seed transfers, cooling, eviction, and spending. A conserved inner matrix multiplication is insufficient if an outer component creates activation.

Confidence tests have two levels: formula/provenance conformance to the pinned PLN adapter, and empirical performance of strength estimates on held-out observations. The modern PLN implementation documents strength/confidence and evidence tracking [S2]. Do not use PLN confidence as though it were itself the probability of the target event.

## 5. Sixteen scenario families

Start with four hand-checked variants per family: a positive control, an invalid/blocked case, a delayed or boundary case, and a changed-context or changed-revision case. That yields **64 litmus fixtures** as a proposed initial target, not a dataset already supplied here.

| ID | Family | Mechanism challenged | Essential oracle assertion |
|---|---|---|---|
| F01 | Missing AND prerequisite among highly similar distractors | Reachability versus similarity; complementary steps | A conclusion is not usable until its complete joint premise contract passes. |
| F02 | Individually plausible but jointly inconsistent premises | Joint certification; inactive constraints | `A`, `B`, and `not(A and B)` cannot coexist as the same hard premise bundle. |
| F03 | OR alternatives with incompatible resource/time choices | Whole packets; branch consistency | Pieces from different alternatives do not form an invented complete plan. |
| F04 | Same atoms under different contexts and changing goals | Scoped beliefs and fields | Goal changes do not revise frozen beliefs; incompatible contexts remain separate. |
| F05 | Evidence diamond, duplicate reports, and shared hidden source | Lineage-aware belief revision | Reused evidence supplies no new independent support. |
| F06 | Cyclic dependencies, duplicate goal paths, and stranded needs | Bounded pressure; source attribution | Circulation creates neither support nor new obligations; blocked demand remains visible. |
| F07 | Dense irrelevant hubs, sparse useful chains, and neutral graphs | Adaptive bandwidth, density, conductance | Task semantics stay fixed; measured search/cost effects may be positive, neutral, or negative. |
| F08 | Revocation, alternative proofs, newly inserted blockers | Exact dependencies and cold/incremental equivalence | Retract only unsupported judgments; newly relevant absence/aggregate dependencies invalidate. |
| F09 | Concurrent proposals for one resource or incompatible commits | Admission authority and reservations | Accepted execution history respects capacity and revision ordering. |
| F10 | Asynchronous operations, lost acknowledgments, wrong products | Persistent episodes and reconciliation | Submission/acknowledgment never establishes exact-product or durable relief. |
| F11 | Overlapping coverage and genuinely shared benefit | Obligation identity and portfolio accounting | Duplicated paths do not duplicate coverage; distinct goals can receive legitimate shared benefit. |
| F12 | Negative observations, delayed effects, and censored outcomes | Typed observation pressure and learning labels | Pending/censored outcomes are not failures; disconfirming observations can be useful. |
| F13 | Memory pressure, retention, and finite-workload starvation | ECAN/LTI and scheduling fairness | Mandatory live dependencies stay pinned; feasible work receives service under stated assumptions. |
| F14 | Tight numerical margins and uncertain risk contracts | Certification geometry | Crossing the actual constraint boundary changes authorization; pressure cannot offset it. |
| F15 | Confounded action histories and changing efficacy | Conductance/outcome learning | Held-out causal improvement is assessed only under the declared identification protocol. |
| F16 | Nonfinite fields, corrupted certificates, and crash boundaries | Robustness and recovery | Fail closed on authority uncertainty; preserve recoverable obligations and consistent ledgers. |

### 5.1 Composite episodes

Single-family cases establish discriminability. Composed cases test integration:

**Deployment:** F01 + F08 + F09 + F10 + F12. Evidence arrives, credentials are revoked, a resource is contested, an acknowledgment disappears, and a delayed callback names the wrong artifact.

**Resource production:** F03 + F06 + F11 + F13. Two goals share a prerequisite, compete for a consumable, and generate cyclic planning routes while memory is constrained.

**Scientific diagnosis:** F02 + F04 + F05 + F12. Two hypotheses share noisy reports, are evaluated in separate contexts, and require a costly disconfirming observation before a safe intervention.

**Service restoration:** F07 + F08 + F14 + F15. A formerly effective action becomes unreliable, new evidence changes route preference, and a nearly binding numerical constraint restricts admissible execution.

Always include equivalent composite worlds with easy, uniform, static structure. Otherwise the benchmark only asks whether adaptivity helps on a workload deliberately built to require adaptivity.

## 6. Flagship integration episode

Use an exact deployment artifact as the first vertical slice. The goal is not “submit deployment”; it is “observe artifact v2 healthy at three consecutive required observation ticks.”

1. Initially, test evidence is missing. A deployment proposal cannot pass. An observation can be permitted.
2. A valid test result arrives. The system can form a complete candidate and certify it against the current credential revision.
3. The test driver revokes that credential between certification and dispatch. The old permit must fail at the dispatch boundary, while the artifact's valid test evidence survives.
4. A replacement credential arrives. Fresh certification and reservation permit one deployment attempt.
5. The executor accepts the attempt but the acknowledgment is lost. Restart the orchestrator. Reconciliation must not create a second external effect for the same idempotency key.
6. A delayed callback from another attempt names artifact v1. It must not satisfy the current attempt's exact-product contract.
7. The executor reports v2 completion. That is not yet durable healthy service.
8. A health observation arrives, followed by a missing required observation and then an unhealthy observation. No durable-success label is justified.
9. Three later consecutive observations establish v2 healthy. Only then may the durability-defined goal be discharged.

Assertions run after every boundary, not only at the end. A separate closed-loop version leaves observation timing and alternative remediation choices to the scheduler. The supplied JSON fixture documents the conformance version; it is not a runnable adapter.

An executor that cannot support idempotent submission or authoritative reconciliation cannot honestly guarantee exactly-once effects after an ambiguous timeout. Include that executor class too: the correct behavior may be `UNKNOWN` plus safe reconciliation rather than an unqualified automatic retry.

## 7. Integration harness

Provide two backend adapters: an independent finite reference model and the actual implementation under test. Where both the user's custom FDAS store and an OpenCog/Hyperon backend are targets, run the same semantic contracts through each adapter. Do not claim compatibility from identical JSON serialization alone.

Suggested logical interface:

```text
reset(public_initial_state, pinned_versions)
observe(event)
advance_clock(logical_time)
run_budget(budget)
propose_operation(...)                     # conformance mode only
try_reserve(proposal)
try_dispatch(proposal, certificate)
try_commit(proposed_belief, certificate)
read_semantic_projection(query_scope)
read_runtime_diagnostics()
snapshot() / restore(snapshot)
reconcile(executor_observations)
```

The adapter hides implementation-specific AtomSpace handles and exposes semantic identities, immutable revisions, and evidence dependencies.

### 7.1 Event-prefix differential testing

After a chosen event prefix, rebuild a fresh reference state from the authoritative public log. Compare its semantic projection with the incremental state.

Compare accepted/useable assertions, current supports, rule and context bindings, operation milestones, exact goal loss and coverage ledgers, and permit validity. Do not require equality of ephemeral activation vectors across different schedulers.

Where full derivation closure is deliberately bounded in the tested system, distinguish an absent uncomputed result from an incorrect accepted result. For cold/incremental equivalence tests, use the same materialization policy or an exhaustive finite test mode. “UNKNOWN because not computed” is different from a stale `PASS`.

When a fact has two independent valid proofs, retracting one proof must not erase support supplied by the other. Compare semantic support sets, not an arbitrary chosen derivation pointer.

### 7.2 Stateful property testing

Generate sequences of ingestion, retraction, context switching, clock advance, goal change, resource reservation, callback arrival, snapshot, and restart. Hypothesis supports rule-based stateful tests, cross-model comparisons, and per-step invariants [S3]. Keep a shrinking/minimization path that produces a small reproducible failing episode.

### 7.3 Concurrency testing

Explicitly enumerate or systematically explore interleavings around read/check/reserve/dispatch/commit boundaries. Microsoft Research's CHESS work is an established reference for controlling and replaying concurrency interleavings [S4]. Adopt that testing principle; do not assume a historical tool is a drop-in dependency for this implementation.

Required races include two workers reserving the last unit, a credential revocation before dispatch, a policy revision before belief commit, and a lease expiry racing with an external acknowledgment. Use a deterministic schedule controller, then supplement with uncontrolled stress tests.

### 7.4 Capability canaries

For every switch, prove that the intended implementation path actually changed. Record whether it was invoked, how often, what it cost, and which state it wrote.

Examples: turning off adaptive bandwidth must stop bandwidth updates; transport-off must bypass transport rather than merely discard its output; pressure-blind scheduling must not inherit cached pressure ranks. A canary detects a no-op ablation before expensive trials.

## 8. Invariants and metamorphic tests

### 8.1 Hard semantic invariants

- A non-PASS required check never authorizes commit or effective execution.
- A passing individual premise set never substitutes for a required joint check.
- An evidence-frozen change to STI, activation, urgency, utility, or pressure never changes belief strength/confidence.
- An ungrounded reasoning cycle never creates its own evidence support.
- Mandatory relevant constraints are checked even when outside the active attention subgraph.
- An expired or revision-mismatched certificate is not current authorization.
- A goal change does not silently redefine proposition identity or context.
- An action cannot be synthesized merely by reversing an implication.
- Resource reservations respect identity, quantity, interval, and owner.
- Observed, predicted, covered, pending, and censored quantities retain separate meanings.

### 8.2 Numerical invariants

For fixed `R`, compare pressure to the direct solve and verify the specified norm/residual bound. A changing operator requires a new epoch; do not apply a fixed-operator theorem to arbitrary adaptation.

For activation, verify nonnegativity, finite values, zero flux on closed routes, and the complete mass ledger. Exercise gamma close to one, disconnected domains, empty neighborhoods, route removal, and extreme utility differences.

Test gate-first evaluation with a proposed-rate function that throws if evaluated on a closed route. Passing an already evaluated scalar does not test whether unsafe arithmetic was skipped.

For certification margins, test exact rational points below, at, and above each declared boundary. Verify strict versus non-strict predicates explicitly. Only test a claimed robustness radius when its norm, domain, constraints, and Lipschitz assumptions are part of the fixture.

### 8.3 Metamorphic transformations

Rename atoms bijectively, permute storage order, move unrelated records between equivalent storage partitions, duplicate the same evidence event, replay an idempotent callback, or add a proven irrelevant disconnected component.

The expected invariance concerns semantic answers and authority, not necessarily byte-identical paths or unchanged latency. A bounded search may need more work after distractors are added. It must not manufacture false support or authority.

Permute independent events only when their temporal contracts commute. Rescale units only when every corresponding threshold, loss conversion, and time contract is transformed consistently. Inserting graph hops is not automatically field-invariant; hop-sensitive transport is precisely one hypothesis to measure.

## 9. Metrics

Publish separate scorecards rather than burying everything in one composite number.

### 9.1 Correctness and admissibility

Report false acceptance, unauthorized effective execution, stale permit use, invalid joint inference, lineage double counting, false goal relief, reservation conflict, and cold/incremental semantic mismatch. Include exact numerators and opportunity denominators.

Also report unnecessary rejection, unresolved feasible work, and time/budget to a valid completion. A system that rejects every action must not appear successful merely because it has zero unsafe actions.

### 9.2 Epistemic quality

Check registered truth formulas and evidence accounting separately from empirical prediction quality. Where the strength is explicitly a Bernoulli-event forecast, report Brier score and reliability by evidence amount, source dependence, and shift regime. Do not score confidence as the Bernoulli probability.

Only independently observed outcomes provide labels. Preserve delayed/censored masks. A recurrent monitor event is not automatically an independent sample.

### 9.3 Task quality

Use an external, versioned goal-loss definition. A useful primary endpoint is integrated unresolved loss:

`J_loss = sum_t sum_g fixed_evaluation_weight[g] * L_g(world_at_t) * delta_t`.

Report observation-based certified completion separately when the world is partially observed. Hidden world loss can evaluate outcomes, but it must not leak to the decision process.

Report durable completion, missed deadlines, action/resource cost, time to legitimate relief, redundant effective work, redundant rejected proposals, abandonment, recovery latency, and actual causal-credit error where the simulator makes that identifiable.

For exact small worlds, report regret against a same-information reference. For larger worlds, report paired performance against comparable baselines. Never relabel a heuristic's result as optimal regret.

### 9.4 Efficiency

Count retrieval queries, scanned/loaded atoms, instantiated rules, certified premise bundles, checker/solver work, pressure iterations, neighbor searches, transport edges processed, field materialization, invalidation work, persistence I/O, and model inference.

Measure total wall time and CPU/GPU use under controlled hardware, plus peak memory and tail latency. Keep environment time distinct from compute time.

Report both matched-work and matched-wall-time comparisons. An avoided PLN invocation is not necessarily a saving if the field costs more than the invocation. Show performance-versus-budget curves rather than selecting one favorable cap.

### 9.5 Diagnostics, not primary evidence

Activation concentration, pressure at useful blockers, bridge score, queue age, flux, and source attribution explain results. They cannot establish decision improvement by themselves. A valid solution may have several equally useful proof paths; one arbitrary oracle trace is not the only “relevant” region.

## 10. Baselines

All baselines receive the same allowed observations, rule library, action model, candidate-access interface, constraints, and mandatory gate authority.

**B0 — Simple competent controller:** dependency-aware best-first/beam scheduling with exact requirement checking, an operation ledger, and full recomputation. This is the essential low-complexity comparator.

**B1 — ECAN-style priority:** attention-driven priority without backward pressure or adaptive transport, preserving mandatory retention and admission.

**B2 — Scalar dependency pressure:** backward relevance represented as a scalar, without typed channels or adaptive transport.

**B3 — Typed pressure plus priority queue:** the full lifecycle-aware pressure design, but scheduling directly from its work priorities instead of diffusion.

**B4 — Full proposal:** typed pressure, scoped semantic fields, lifecycle-aware coverage, ECAN allocation, adaptive transport, and specified conductance model.

**B5 — Planning reference:** exact finite search for tiny cases and established heuristic planning for a declared deterministic planning subset. Fast Downward documents A*, greedy, and other best-first search options [S5]. Its result is comparable only on the subset its encoding actually represents; it is not a direct baseline for arbitrary stochastic temporal PLN worlds.

**B6 — Omniscient diagnostic bound:** optional, clearly labeled as privileged and not a fair competitor.

Freeze candidate sets for one set of tests to isolate ranking. In another set, let discovery differ and charge its actual cost. Otherwise an advantage in candidate generation can be mistaken for an advantage in candidate evaluation.

## 11. Safe ablation replacements

Every performance ablation replaces a mechanism with a valid alternative. It does not delete the problem requirement.

| Ablation | Replacement | What remains fixed | Question |
|---|---|---|---|
| No backward pressure | Dependency-aware best-first queue | Goals, observations, exact requirements | Is propagated relevance useful beyond explicit dependency traversal? |
| Scalar instead of typed pressure | One pressure channel with generic work scheduling | All capabilities and gate contracts | Do channels improve mode selection? |
| No transport | Direct priority/beam scheduler | Same candidate API, rules, and hard gates | Does diffusion help beyond its input priority signal? |
| Fixed bandwidth | Tuned constant radius | Same neighbor caps and kernel family | Is local bandwidth adaptation worth its overhead? |
| No density normalization | Unnormalized permitted kernel | Same active support and other coefficients | Does normalization help in nonuniform graphs? |
| Uniform conductance | Equal permitted-route conductance | Same connectivity and constraints | Does conductance information matter? |
| Frozen versus learned conductance | Fixed weights from the same allowed training phase | Same training data/access and evaluation budget | Does adaptation generalize? |
| No utility bias | Flat potential on permitted work | Explicit goal task and common safety policy | Is priority information responsible for the benefit? |
| Fixed attention allocation | Fair bounded allocation | Same total compute, mandatory monitoring and pins | Does ECAN-style allocation improve scheduling? |
| No lifecycle planning projection | Recompute readiness from authoritative event history | Actual lifecycle contracts and operation identity | Does persistent derived state save work or improve planning? |
| No commitment-aware prioritization | Ignore predicted coverage for ranking | Ledger, reservations, idempotency, true-loss accounting | Does coverage reduce redundant proposals and improve allocation? |
| No learned LTI policy | LRU/FIFO for evictable state | Required live dependencies remain pinned | Is learned retention beneficial beyond required persistence? |
| No incremental invalidation | Full correct recomputation after events | Same evidence, contexts, and authority | What is the efficiency benefit of exact dependencies? |
| No margin-based prioritization | Boolean admission plus fixed revalidation schedule | Identical hard constraints | Does certification geometry improve monitoring/robustness planning? |
| No bridge score | The same search without that advisory score | Same admissibility and value model | Does forward/backward matching improve discovery? |

Context mixing, disabled gates, treating duplicate evidence as independent, accepting all formula fallbacks, or treating acknowledgments as success are not credible performance baselines. They are mutants used to verify that the test suite detects specification violations.

### 11.1 Two kinds of ablation report

**Frozen deletion/replacement:** hold other parameters fixed to locate immediate mechanistic dependence.

**Fairly retuned reduced model:** give the simpler variant an equal declared tuning budget. This tests whether the additional component is worth keeping after the alternative is competently configured.

For learned components, distinguish an inference-time switch-off from a separately trained reduced architecture. Both are useful, but they answer different questions. Log the total training and hyperparameter-search cost.

### 11.2 Interaction experiments

Use a targeted 2×2×2 factorial:

- P: scalar versus typed pressure.
- L: commitment-aware planning off versus on.
- T: priority queue versus adaptive transport.

All eight cells preserve hard gates, true lifecycle contracts, the authoritative ledger, resource reservations, and idempotent execution. “L off” does not authorize forgetting that an operation actually exists.

For a performance quantity Y, the P–L interaction at a fixed T is:

`I_PL = Y(P1,L1) - Y(P1,L0) - Y(P0,L1) + Y(P0,L0)`.

Estimate it using the same blocked episode set, with uncertainty. Do not infer synergy because the complete system happens to have the largest point estimate.

Then use separate 2×2 experiments for adaptive bandwidth × density normalization, and learned conductance × attribution quality. Do not begin with a full factorial over every engineering toggle.

## 12. Causal evaluation and delayed learning

A stored trajectory provides outcomes of the operations that actually ran. It does not reveal the outcomes of unchosen operations.

### 12.1 Simulator protocol

Branch small simulator states and evaluate alternative **safe, same-target** plans against explicit exogenous event variables. Use the same observation restrictions for policy comparators. Alternative outcomes remain evaluator-only.

A global PRNG seed alone is not enough to align randomness: policies can consume draws in different orders. Index randomness by an explicitly designed event identity, entity, time, and causal channel. Define the cross-policy coupling in the simulator manifest. Do not assume that any convenient shared random tape is a faithful model of counterfactual correlation.

### 12.2 Grounded protocol

When operationally appropriate within the game/simulator, randomize among pre-screened safe same-target alternatives and log assignment probabilities, eligibility sets, target identity, and delayed outcomes. Keep local execution fixed. Compare goal-relief outcomes when the windows mature.

When only observational logs are available, report descriptive associations unless the identification assumptions and overlap are established. Do not label an unchosen action a failure, fill in unknown outcomes as zero, or use shadow proposals as if they had been executed.

### 12.3 Separate learning problems

Conductance for low-cost retrieval can learn from measured search cost. An action-success model needs outcome evidence. A field should not get causal success credit merely because an unrelated event satisfied the same goal.

Run a known-model phase to test scheduling without learning noise, a frozen-learned phase for generalization, and an explicitly sequential online-learning phase. Reset evaluation state between independent episodes unless persistent cross-episode learning is part of the registered protocol.

## 13. Split design and generator coverage

Random seed separation is necessary but insufficient. Group all variants of a parent instance, renamed isomorphs, trace prefixes, and counterfactual twins into the same split.

Use:

- Development/training cases for implementation and learned parameters.
- Tuning cases for selecting parameters and baselines.
- A locked IID confirmation cohort.
- A compositional cohort with unseen combinations of known motifs.
- A structural shift cohort with new degree distributions, proof widths, or planning horizons.
- A dynamics shift cohort with different delay, censoring, churn, or efficacy regimes.
- A semantic/lifecycle schema transfer cohort with new but representable transition structures.

Do not reject generated test cases because the full model performs poorly. Rejection is allowed only for predeclared validity conditions, such as malformed semantics or a promised exact oracle failing to produce a result. Log rejection rates by family and difficulty.

Audit leakage by shuffling superficial labels, using alternate renderers, training trivial predictors on metadata, and verifying the agent cannot access evaluator-only files. Hash the generator, templates, oracle, split manifest, and dataset artifacts before confirmation.

A reasonable development target is 64 litmus cases plus roughly 2,000 inexpensive generated episodes, followed by separate pilot and locked confirmation cohorts. These are engineering suggestions, not power calculations. Final confirmation size depends on the measured paired variance and the smallest improvement worth the extra complexity.

## 14. Scale axes

Vary these independently rather than reporting one ambiguous “AtomSpace size”:

| Axis | Suggested exploratory values |
|---|---|
| Total stored atoms | 10^3, 10^4, 10^5, 10^6, subject to hardware |
| Active field anchors | 128, 512, 2,048, 8,192 |
| Actual inference depth | 1, 4, 16, 64 rule applications |
| Transport distance | Short/medium/long, independently rendered from proof depth |
| Joint premise width | 1, 2, 4, 8, 16 |
| Alternative branches | 1, 2, 8, 32 |
| Active goals/contexts | 1, 4, 16, 64 |
| Dependency churn | 0%, 0.1%, 1%, 10% of eligible records per event block |
| Async outcome delay | Immediate, short, long relative to horizon |
| Source reuse/correlation | Independent, shared-source, repeated-observation |

A chain of 128 transport links is not a proof of depth 128. Distinguish stored atoms from active anchors, represented rule schemas from instantiated candidates, and support depth from graph distance.

The main locality experiment holds the active problem fixed while adding irrelevant stored knowledge. Charge retrieval/index construction and cold startup separately from steady-state query processing. A constant-time inner transport step does not establish scalable whole-system materialization.

Memory eviction and constraint indexing are correctness-sensitive: added inactive knowledge may contain a relevant constraint in separate adversarial cases. Do not call those additions irrelevant.

## 15. Statistics, budgets, and reporting

Use paired evaluations where variants share a parent episode and explicitly coupled environment randomness. Randomize execution order to reduce hardware/cache drift. Separate training seeds from environment seeds. Many events in one episode are not many independent experimental subjects.

For fixed benchmark families, report paired intervals within families and a predeclared weighted aggregate. Bootstrap the actual independent clusters; do not treat renamed variants, repeated checkpoints, or shared training seeds as independent. A hierarchical procedure is appropriate when several dependence levels exist. Broader claims about unseen families require a sampling design that supports them.

The reliable-evaluation work by Agarwal and colleagues motivates interval estimates and robust aggregate reporting rather than point estimates alone [S6]. Its rliable implementation offers corresponding statistical tools [S7]. Use them with the correct dependence structure, not as a substitute for one.

Choose a small set of primary comparisons and endpoints before confirmation. Suggested priorities: correctness gate first; then integrated external goal loss; then total compute at noninferior goal performance. Report performance/cost frontiers, per-family effects, and negative results. Predeclare multiplicity treatment for additional confirmatory contrasts; mark unregistered ablations exploratory.

A practical-gain threshold and a noninferiority margin are task choices, not universal constants. For example, a 10% CPU reduction at essentially unchanged outcome may matter in one deployment, while a 1% outcome gain at twice the compute may not. Set these before observing confirmation outcomes.

Zero observed failures is not a general safety proof. Under an independent identical-risk Bernoulli model, zero failures in n trials gives the one-sided 95% upper bound `1 - 0.05^(1/n)`, approximately `3/n`. Clustered events and distribution shift invalidate a naive transition-count interpretation. Report what the trial unit and sampled regime actually were.

Timeouts, OOMs, crashes, aborted confirmations, and oracle gaps remain visible in the denominator or separate failure accounting. Never remove a run merely because it makes a variant look bad.

## 16. Mutation testing of the benchmark itself

Plant bugs intentionally in an isolated, non-actuating test build:

```text
M01 UNKNOWN gate treated as PASS
M02 stale revision ignored
M03 one AND premise skipped
M04 joint consistency check replaced by pairwise checks
M05 duplicate lineage treated as independent evidence
M06 ACK treated as durable success
M07 wrong artifact accepted by name similarity
M08 newly inserted blocker not indexed for invalidation
M09 repeated source injection accumulates an artificial demand stock
M10 capacity checked without atomic reservation
M11 censored outcome labeled as failure
M12 closed-route rate arithmetic evaluated before checking the gate
```

Require a minimized witness for each detected mutant. Report which mutants survive, not just an overall percentage. A surviving mutant reveals a blind spot in the benchmark. It does not show that the mutant is safe.

Mutation runs cannot be ranked alongside valid variants for task performance. A disabled acceptance contract may appear faster because it is no longer solving the same problem.

## 17. Grounded Freeciv transfer

Use frozen save states or scenario cohorts, pinned code/assets/rulesets, fixed opponents, and fixed local execution heuristics. Select vertical slices involving high-level dependencies: city stability/defense, multi-unit coordination, or ferry/founder coordination, according to the capabilities actually present in the checked-out implementation.

Start in shadow mode to verify that the proposed planner sees the same legal action set, exact entity identities, resources, and observation boundaries. Shadow mode establishes interface validity and proposed choice differences; it does not establish gameplay benefit.

Then run prospective closed-loop paired cohorts. Require at least two viable same-target plans in the discriminating subset. Measure targeted durable relief, packet completion, resource contention, invalid proposals, and coordination cost before interpreting broad game score or wins.

Keep scenario-specific findings distinct from full-game generalization. No claim about the current implementation's performance is made in this package, and no current repository revision was inspected here.

## 18. Development sequence and decision rules

**Stage 0 — Contracts and fixtures.** Implement the oracle boundary, 64 small cases, semantic trace schema, and selected mutants. Establish exact admission and lifecycle behavior before tuning fields.

**Stage 1 — Integrated vertical slice.** Wire actual storage, PLN adapter, gates, ledger, pressure, transport, and executor simulation through the deployment episode. Verify it uses real components rather than a stand-alone mock that merely agrees with itself.

**Stage 2 — Strong baselines.** Implement the competent dependency queue and typed-pressure-without-transport variants. Equalize information, candidates, and safety authority.

**Stage 3 — Mechanism experiments.** Run fixed-input/candidate and closed-loop tests; the eight-cell P/L/T interaction study; adaptive-bandwidth/density ablations; total-store versus active-frontier scale sweeps.

**Stage 4 — Learning and transfer.** Freeze models, use sealed cohorts, then test supported online learning and grounded coordination under the registered protocol.

Promotion requires no known correctness failures in the required suite, a test suite that detects the designated mutants, preserved progress on feasible positive controls, and an independently confirmed benefit matching the intended claim. A null or negative result is a reason to retain the simpler implementation or keep a mechanism advisory—not to redefine the endpoint after the fact.

## 19. Reporting template

Every experimental report includes:

```text
Claim and hypothesis IDs
Input specification and implementation hashes
Dataset/generator/oracle/split hashes
Variant definitions and proof that switches were exercised
Information access and candidate-access equivalence
Training, tuning, and evaluation budgets
Independent sample units and coupling scheme
Correctness violations and opportunity denominators
Goal-loss, completion, and compute results with intervals
Per-family effects and held-out shift results
All timeouts, crashes, missing labels, and exclusions
Representative minimized failures
Conclusions limited to the tested regime
```

The decisive result is not “the field looks sensible.” It is that a specified mechanism preserves the required semantics and buys measurable reliability, efficiency, or decision quality over a simpler, competently configured alternative.

## Sources

Architectural requirements come from the two supplied design specifications. The workload families, hypotheses, numbers, metrics, adapters, and experimental decisions in this document are proposals, not externally established empirical findings.

[S1] Z3 official guide and repository — independent theorem-prover reference technology. Accessed 30 September 2026.
`https://microsoft.github.io/z3guide/`
`https://github.com/Z3Prover/z3`

[S2] Modern PLN repository — strength/confidence and evidence-tracking implementation context. Accessed 30 September 2026.
`https://github.com/trueagi-io/PLN`

[S3] Hypothesis documentation, Stateful tests — generated operation sequences, model comparison, and invariants. Accessed 30 September 2026.
`https://hypothesis.readthedocs.io/en/latest/stateful.html`

[S4] Microsoft Research, CHESS: Find and Reproduce Heisenbugs in Concurrent Programs — systematic and reproducible interleaving tests. Accessed 30 September 2026.
`https://www.microsoft.com/en-us/research/project/chess-find-and-reproduce-heisenbugs-in-concurrent-programs/`

[S5] Fast Downward documentation, SearchAlgorithm — established search alternatives for supported planning subsets. Accessed 30 September 2026.
`https://www.fast-downward.org/latest/documentation/search/SearchAlgorithm/`

[S6] Agarwal et al. (2021), Deep Reinforcement Learning at the Edge of the Statistical Precipice — uncertainty-aware benchmark evaluation.
`https://arxiv.org/abs/2108.13264`

[S7] Authors' rliable repository — evaluation statistics implementation. Accessed 30 September 2026.
`https://github.com/google-research/rliable`
