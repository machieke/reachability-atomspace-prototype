# Pressure-Field PLN + Lifecycle Dependency Fields
## Reachability-Driven AtomSpace integration — Proposal v0.2

**Date:** 30 September 2026  
**Extends:** `reachability_atomspace_specification.md`, Proposal v0.1  
**Design context:** Kevin Machiels's reachability architecture, Lifecycle Dependency Field Theory (LDFT), pressure-field PLN, and functional dependent AtomSpace discussions.  
**Status:** Engineering proposal. The equations, application schemas, and service contracts below are proposed integration decisions, not claims about functionality already implemented in an OpenCog, Hyperon, or experimental project branch.  
**Non-negotiable:** All required acceptance gates remain hard and fail closed. Pressure, urgency, attention, utility, confidence, and learned conductance cannot override them.

## 1. Integration decision

Yes: lifecycle dependencies should be the structured domain over which goal pressure is generated and propagated. They should not be an independent planner that competes with PLN, ECAN, or reachability.

The unified responsibilities are:

| Component | Meaning | Authority |
|---|---|---|
| Lifecycle model | What stage an entity or operation occupies; what transitions are possible | Schema-governed, evidence-backed transition records |
| Dependency model | What must hold or become available for a transition or goal | Typed requirement expressions and exact supports |
| Goal pressure | What remains needed, by whom, and with what urgency | Goal manager owns sources; numerical projection owns derived scores |
| PLN | What follows from evidence and rules, under uncertainty | Belief proposals; acceptance through the existing certifier |
| Reachability | Which candidate operations can be admitted under the current context | Hard operation-specific checks |
| ECAN and transport | Where finite computational resources are allocated | Budget authority, not truth or action authority |
| Operation coordinator | Reservations, submission, outcome tracking, recovery | Revision-checked execution and event processing |
| Certification | Whether a specified inference, transition, or result satisfies its contract | Final admission authority within its declared scope |

The central loop is:

> Evidence updates lifecycle judgments. Lifecycle judgments expose deficits. Deficits generate goal-conditioned pressure. Pressure directs recall and bounded transport. PLN and procedural models construct candidate operations. Hard gates admit those operations. Observed outcomes update the lifecycle and discharge only the goal obligations they actually satisfy.

Do not reduce this to one scalar called importance. In particular:

\[
\text{unmet demand}\ne\text{executable demand}\ne\text{allocated attention}\ne\text{observed relief}.
\]

## 2. Compatibility with the previous specification

Retain the existing separation between immutable semantic/operational structures and mutable attached Values. AtomSpace documents immutable indexed atoms, mutable per-atom Values, and graph-described value flows. [S1]

The extension makes five deliberate changes to v0.1:

1. Replace a generic authoritative `runtime.lifecycle` interpretation with explicit, versioned lifecycle events and judgments. The old field remains a cache only.
2. Define goal-conditioned pressure as the principal task-driven input to the prior `utility.value` transport potential. Do not independently multiply the same goal's importance through pressure, utility, STI, and the final candidate bid.
3. Add a backward dependency projection alongside the existing forward evidence/inference path. It is a metareasoning operation, not logical reversal of an implication.
4. Add persistent operation episodes and a reservation ledger. Scheduling, execution, product observation, and durable goal relief become separately observable milestones.
5. Keep advanced bridge/flow models advisory initially. Exact requirements, groundings, certificates, and resource reservations remain authoritative.

These changes are backend-neutral. The historical ECAN AttentionValue includes STI, LTI, and VLTI; its numerical representation is an adapter detail, not a reason to mix epistemic truth with demand. [S3]

## 3. Scope and identifiers

In addition to the v0.1 identifiers, introduce:

| Identifier | Purpose |
|---|---|
| `lifecycle_schema_id`, `schema_revision` | Versioned transition graph and policy references |
| `entity_id`, `episode_id` | The enduring entity and a particular attempt or process |
| `goal_episode_id` | A persistent obligation, distinct from its transient pressure values |
| `requirement_set_id`, `requirement_revision` | Exact AND/OR/temporal/resource contract |
| `operation_id`, `attempt_id` | Stable operation identity and a particular execution attempt |
| `reservation_id`, `lease_revision` | Resource/coverage ownership and expiry |
| `support_fingerprint` | Exact data and rule dependencies of a derived judgment |
| `outcome_contract_id` | What counts as effect, completion, exact product, and relief |
| `field_model_revision` | Routing coefficients, kernel parameters, normalization policy |

A pressure sample is scoped by:

```text
(anchor, context_id, goal_episode_id, mode, session_id,
 knowledge_revision, lifecycle_revision, field_epoch)
```

An enduring source obligation is not session-local. Stopping the reasoning session releases transient attention but must not erase the unresolved goal.

Goals remain separate from contexts. Changing goal importance may alter pressure and scheduling without changing the truth value of an unchanged proposition. Crossing hypothetical contexts requires explicit compatibility/discharge checks.

## 4. Lifecycle model: stage, progress, validity, and history

### 4.1 Dynamic schemas

A lifecycle schema is an executable directed graph, not one globally hard-coded enumeration:

```text
LifecycleSchema:
    schema_id, revision, provenance
    entity_type
    states
    permitted_transitions
    per-transition requirement expressions
    expected effects and outcome contracts
    regression/recovery transitions
    terminal-state semantics
    time, cancellation, and expiry policies
    required checker and policy references
```

A system such as OmegaClaw may propose a new schema. Promotion follows a governed sequence such as `DRAFT -> VALIDATED -> EXPERIMENTAL -> ACTIVE`. The sequence is a proposed administrative policy, not a required lifecycle for every domain entity. Validation checks well-formedness, types, safe transition contracts, regression handling, and compatibility with invariants. Experiments cannot certify arbitrary future behavior.

Active episodes pin a schema revision. Updating a schema does not silently reinterpret existing episodes. Migration is a distinct checked operation. A generated schema cannot weaken the global acceptance policy or grant its author new execution authority.

### 4.2 Hybrid maturity

For an episode, maintain:

- `stage` \(\sigma_i\): authoritative under the schema and current evidence;
- `progress` \(\chi_i\): optional within-stage measurement;
- `maturity` \(\phi_i\): optional derived display/planning coordinate;
- `validity`: current support state, independent of stage history.

For an explicitly selected comparable transition \(\sigma\rightarrow\sigma'\), a schema may define:

\[
\phi_i=\mu(\sigma_i)+\chi_i[\mu(\sigma'_i)-\mu(\sigma_i)],
\qquad 0\le\chi_i\le1.
\]

If no forward target or valid progress measure exists, use \(\phi_i=\mu(\sigma_i)\) or omit the scalar. Different branches need not have comparable maturity coordinates. Never interpret \(\phi\) as PLN strength, confidence, or a universal probability of completion.

A scalar progress value reaching one does not itself execute a transition. The transition still needs fresh evidence, requirement satisfaction, and its certificate. Where no reliable progress measurement exists, record `UNKNOWN`, not fabricated partial completion.

### 4.3 Regression without rewriting history

An event that happened remains part of the history. Its continuing consequences may become invalid.

Example: a credential was valid when a deployment was submitted. It may expire before a later privileged step. The historical submission remains true; the current authorization judgment becomes stale or false and the later step is blocked.

Separate:

```text
historical event: Completed(build-17, time-T)
current judgment: Usable(artifact-17, context-K, revision-R)
```

A dependent entity regresses only in the dimensions that actually depend on the invalidated support. Do not erase a finished artifact simply because another prerequisite for deployment failed.

## 5. Three related lifecycles, not one overloaded state machine

### 5.1 Entity lifecycle

Describes domain development: for example, specified, built, tested, usable, retired. State names and transitions are schema-defined.

### 5.2 Operation lifecycle

Describes an attempt to do work. A useful envelope is:

```text
PROPOSED -> SELECTED -> RESERVED -> SUBMITTED -> ACKNOWLEDGED
                               -> EXECUTING -> WAITING_FOR_OUTCOME
                               -> COMPLETED / FAILED / CANCELLED
```

This is only an envelope. Operations can have multiple effects, branch, retry, or observe effects before formal completion. Track independent milestones rather than assuming every operation follows one linear sequence:

```text
candidate_generated
selected
submitted
accepted_by_executor
immediate_effect_observed
completion_observed
exact_product_observed
goal_relief_observed
durable_relief_observed
```

`accepted_by_executor` is not the same as a reasoning certificate's acceptance. Use distinct event types.

### 5.3 Goal episode lifecycle

Describes the enduring obligation and whether it has been relieved. For example:

```text
DORMANT / ACTIVE / COMMITTED / WAITING / STRANDED
RELIEVED / DURABLY_RELIEVED
FAILED / ABANDONED / SUPERSEDED
```

A failed operation does not necessarily fail its goal. A goal can return from waiting to active or stranded. Abandoning or superseding a goal is an authorized goal-management decision, not a pressure-engine trick for lowering its loss.

A maintenance goal can remain active after its current deficit reaches zero. It may require monitoring and reacquire pressure when the maintained condition degrades.

## 6. Typed dependencies and requirement expressions

Do not use a single unqualified `depends_on` relation.

| Dependency | Meaning | Example |
|---|---|---|
| Epistemic | A judgment requires particular evidence/rules | An inference depends on premise revisions |
| Lifecycle/enabling | A transition requires a state to hold | Deploy requires Tested(artifact) |
| Causal/procedural | An operation can change a modeled state | RenewCredential may establish valid authorization |
| Teleological | A state or operation can relieve a goal deficit | ServiceHealthy relieves RestoreService |
| Resource | A quantity/capability must be bound, consumed, or held | One deployment slot during an interval |
| Temporal | Order, overlap, duration, deadline, or freshness | Health must persist throughout an observation window |
| Inhibitory | A stated condition blocks a transition | Revoked(credential) blocks privileged deployment |
| Observation | A predicate needs a specified measurement | Exact artifact hash and service version must be observed |

PLN may reason about these relations, but their type determines what operations they authorize. An evidential correlation does not become an action capability by reversing its arrow.

### 6.1 RequirementSet

A requirement is a typed expression rather than a loose set of incoming edges:

```text
Deploy(artifact-A, service-S) requires AND(
    Tested(artifact-A, exact_revision),
    OR(ValidCredential(C1), ValidCredential(C2)),
    Reserved(deploy_slot, service-S, execution_interval),
    Compatible(service-S, artifact-A),
    PolicyPermits(actor, deploy, service-S)
)
```

Supported operators may include `AND`, `OR`, `K_OF_N`, quantitative comparisons, temporal operators, and schema-approved negation. The initial implementation should support a small fully checked subset before extending it.

Each witness carries its grounding, context, validity interval, provenance, and exact support revisions. A probabilistic prerequisite must specify its risk/acceptance contract explicitly. It is not automatically satisfied because its strength is nonzero, and passing a risk contract does not make the event certain.

### 6.2 AND versus OR

For an AND transition, all required witnesses must hold jointly. High pressure on one prerequisite cannot compensate for another missing prerequisite.

For OR, one complete compatible branch suffices. A planner can investigate alternatives, but resource allocation is over coherent branch plans, not disconnected high-score atoms.

If normalized satisfaction scores \(s_i\in[0,1]\) are explicitly meaningful for a particular schema, \(\min_i s_i\) can be an AND progress proxy and \(\max_i s_i\) an OR proxy. These are not substitutes for joint certification, quantitative resource checks, or general PLN conjunction/disjunction formulas.

### 6.3 Dependencies are not automatically additive

Two distinct goals can genuinely benefit from one operation. One goal represented by several paths is still one obligation. Preserve goal/source identity so that duplicate paths do not create duplicate loss or duplicated resources.

A resource atom also does not imply unlimited reuse. Distinguish reusable information, consumable inventory, exclusive ownership, and temporally held capacity.

## 7. Pressure sources: unresolved obligations, not belief strength

### 7.1 Goal loss

Each goal defines a versioned nonnegative loss \(L_g(x_t)\). Its definition includes units, observable completion predicates, temporal scope, and treatment of uncertainty.

For a world-changing goal, the authoritative goal monitor determines the currently supported deficit. For an epistemic goal, a valid evidence/inference result can legitimately reduce uncertainty-related loss. Do not treat improved confidence about an action's success as proof that the action happened.

When state is unknown, preserve that uncertainty and generate observation pressure. Unknown is not automatically zero deficit. Goals whose loss itself is an estimate must distinguish estimated loss from certified completion.

### 7.2 Source demand

Define:

\[
D_g(t)=w_g\,u_g(t)\,\kappa_g(t)\,L_g(x_t).
\]

Here \(w_g\) is a goal-importance conversion into common priority units, \(u_g\) is bounded urgency, and \(\kappa_g\) is an explicit policy-level commitment factor. **\(\kappa_g\) is not PLN confidence.**

Use bounded, versioned urgency functions. Expired deadlines must trigger the declared late/recovery/failure policy, not an infinite number. If two losses have incompatible units, normalize or convert them explicitly before aggregation.

Do not multiply this source by route availability, confidence, or an acceptance gate. A vital but presently impossible goal remains a source of demand.

### 7.3 Outstanding, covered, and open demand

A commitment can cover some outstanding work without establishing observed relief. Let \(\widehat C_g\) be the conservative, overlap-aware estimate of loss coverage from live commitments, with \(0\le\widehat C_g\le L_g\). Then:

\[
D_g^{open}=w_gu_g\kappa_g\max(0,L_g-\widehat C_g).
\]

Keep all of the following separately:

```text
outstanding_loss
estimated_committed_coverage
open_loss
observed_relief_events
maintenance_and_observation_obligations
```

Do not add predicted coverage to the evidence ledger as success. Reservations have expiry, owner, heartbeat/cancellation policy, and exact intended products. Losing a reservation or observing failure removes coverage and reopens work. Covered work still requires sufficient monitoring attention to detect failure.

Coverage is computed from the committed portfolio, not by blindly summing individual predictions. Different operations promising the same benefit overlap. Effects can also be complementary or antagonistic. When no reliable overlap model exists, use explicit goal-slice ownership and conservative coverage.

### 7.4 Stranded demand

If no admissible operational route exists, preserve the source with a reason:

```text
NO_CAUSAL_ROUTE
UNMET_REQUIREMENTS
UNKNOWN_OR_STALE_CHECK
FORBIDDEN_ACTION
MISSING_CAPABILITY
RESOURCE_UNAVAILABLE
DEADLINE_INFEASIBLE
INSUFFICIENT_OBSERVATION
SEARCH_BUDGET_EXHAUSTED
```

`SEARCH_BUDGET_EXHAUSTED` is not proof of impossibility. Stranded demand may generate admissible inference, observation, search, retention, or escalation work. It cannot make a forbidden action legal.

## 8. Typed pressure channels

Maintain a goal-conditioned vector:

\[
\mathbf P_{i,g}=(P^{infer},P^{observe},P^{act},P^{expand},P^{retain}).
\]

| Channel | Trigger | What can satisfy it |
|---|---|---|
| `infer` | A relevant judgment is unresolved but existing premises/rules might suffice | A checked derivation or a useful refutation |
| `observe` | Missing, stale, conflicting, or outcome-specific evidence | An appropriately sourced observation |
| `act` | A modeled world transition could reduce a deficit | An admissible grounded operation and its observed effect |
| `expand` | No sufficiently explored route or operation model exists | Authorized search/model/schema proposal |
| `retain` | Future work depends on preserving knowledge, paths, or live operation context | Budgeted retention and required dependency pinning |

A failed `act` gate does not necessarily close a separately authorized `observe` or `infer` operation. These have different subjects and contracts. Inspecting a rejected claim is not accepting it as a premise.

A negative result can satisfy an epistemic subgoal and prevent useless work. Do not train the scheduler to prefer observations that merely confirm its existing plan.

Channel conversion must be explicit and preserve source attribution. It is a reasoned reassignment of an obligation, not creation of additional independent goal value.

## 9. Bounded backward dependency pressure

### 9.1 Projection graph

Materialize a bounded context/goal-specific graph containing goals, requirement groups, unresolved obligations, candidate operations, and useful intermediate judgments. Include operational hypernodes for AND/OR structure.

Backward demand follows typed dependency explanations. It may inspect blocked or hypothetical plans under their inspection policy without granting execution authority. Hard execution gates are checked later on the complete operation, not applied to erase the goal at the source.

### 9.2 Proposed numerical operator

For one goal and channel, let \(d\ge0\) contain its current source injections. Let \(R_{ij}\ge0\) describe the share of demand at anchor \(j\) propagated to prerequisite/explanation anchor \(i\). Require:

\[
\sum_iR_{ij}\le1,\qquad 0<\gamma<1.
\]

Hold \(R\) fixed for one field epoch and solve:

\[
p^{(k+1)}=d+\gamma Rp^{(k)}.
\]

Because \(\|R\|_1\le1\), this map is a contraction in the 1-norm. Its unique fixed point is:

\[
p^*=(I-\gamma R)^{-1}d,
\qquad \|p^*\|_1\le\frac{\|d\|_1}{1-\gamma}.
\]

This is an engineering choice for bounded relevance propagation. It is not a PLN truth rule, a probability distribution, or a physical conservation law. The sum of pressure scores across graph depth may exceed the original demand because several nodes describe the same obligation. Never use that sum as an attention budget or a goal-loss ledger.

The residual \(\|d+\gamma Rp-p\|_1\) gives an error bound after division by \(1-\gamma\). If coefficients change with the state, rebuild or start a new epoch; the fixed-operator convergence argument does not prove stability for arbitrary adaptive changes.

Recompute from the source ledger or update by a mathematically equivalent delta. Do not add \(D_g\) repeatedly to an accumulating stock every tick while the same deficit remains unchanged.

### 9.3 AND routing

Pressure is distributed to missing requirements using bounded blocker, residual-work, and critical-path estimates. Reserve a positive exploration share for each genuinely unresolved necessary requirement. This reduces heuristic starvation; an age-aware queue and explicit finite-workload/service assumptions are needed for an eventual-service guarantee. Positive numerical weights alone do not guarantee execution under persistent overload.

Do not wait for an AND group to become ready before sending pressure to its missing prerequisites: that would deadlock the planner. Do not restrict decisions to immediate marginal loss reduction: complementary prerequisites can each have zero one-step goal benefit while their joint plan has high value.

Requirement feasibility is exact at admission; intermediate pressure distribution is a scheduling heuristic.

### 9.4 OR routing

Alternative complete branches share a goal's planning allocation through normalized branch weights. An unknown branch can receive investigation allocation; it cannot reserve execution resources as though its requirements were proven.

When selecting actual work, compare coherent branch plans. Resource contention and overlap are handled at that layer. A bounded exploration budget may investigate several alternatives, but it does not grant each a full duplicate execution budget.

### 9.5 Cycles and bridge scores

Use strongly connected components for inspection of cyclic dependency structure. Acyclic condensation can support bounded critical-path summaries; cycles require explicit fixed-point or temporal semantics. A cycle with no grounded support cannot bootstrap a satisfied requirement merely by circulating pressure.

A forward/backward bridge score can combine forward feasibility estimates \(f_i\) and backward relevance estimates \(b_{i,g}\). The product \(f_i b_{i,g}\) remains a discovery heuristic unless separately calibrated. It is not a probability of proof, a resource reservation, or an extra multiplier in goal value.

Retain raw demand even where the forward feasibility estimate is zero. The zero may mean unavailable now, unresolved, model-limited, or genuinely forbidden; those cases need distinct diagnostics.

## 10. Connecting pressure to ECAN and adaptive transport

### 10.1 One task-driven prioritization path

Use pressure to construct the prior specification's task utility potential, rather than layering an independently weighted duplicate goal signal on top of it.

The operational projection selects the appropriate mode for each unresolved obligation. An ungrounded or currently blocked action is not a dispatch candidate; its raw dependency pressure remains visible and may generate separately authorized inference or observation work. Synthetic goal/source anchors are not executable work items. Readiness and resolvability may affect this operational projection, never the existence of the source demand.

For operational anchor \(i\), channel \(m\), define a bounded potential from the channel's operational pressure:

\[
\Phi_i^{(m)}=\operatorname{clip}\!\left(
\log(1+P_i^{(m)}/P_0),0,\Phi_{max}\right).
\]

The scale \(P_0>0\), aggregation across goals, and clipping limit are versioned. Comparison across goals uses common importance units. A single shared prerequisite still retains separate source attributions even when a combined field is computed.

ECAN maps this potential and explicitly budgeted non-goal obligations into STI/seeding. LTI retains its slower retention role. No second independent ECAN diffusion should also move the same activation budget.

### 10.2 Keep demand and activation distinct

The existing activation \(a_i\) remains a finite allocation measure. Pressure is not mass, and kernel density \(\rho_i\) is not goal deficit. There is no default equation of state that identifies semantic density with pressure.

For the SPH-inspired graph transport, reuse the prior nonnegative row-rate scheme:

\[
q_{ij}^{(m)}=H_{ij}^{route,m}\,C_{ij}^{(m)}\,K_{ij}^{adaptive}
\exp\{\beta\operatorname{clip}(\Phi_j^{(m)}-\Phi_i^{(m)},-L,L)\}.
\]

Here \(H^{route,m}\in\{0,1\}\) is an operation-specific route permit, \(C\) is a nonnegative conductance, and \(K^{adaptive}\) contains the admitted neighborhood and density normalization from v0.1. Evaluate the gate first; an unauthorized route returns zero without evaluating an overflowing expression.

\(q\) is a rate, not a transferred amount. The directed activation transfer in a microstep is:

\[
F_{ij}=\Delta\tau\,a_iq_{ij}.
\]

Choose the existing time-step bound so that outgoing transfers cannot exceed available activation. The resulting row-stochastic update conserves activation between anchors and the reservoir. Seeding, cooling, graph removal, and operational spending have explicit ledger entries.

Backward pressure projection and forward/bidirectional activation transport are different operators. Do not add their numerical outputs as though they share units.

### 10.3 Congestion is a separate field

If desired for a later experiment, maintain a resource price \(\lambda_r\) with units of scheduling value per resource unit:

\[
\lambda_r^{new}=[\lambda_r+\eta(\widehat{load}_r-capacity_r)]_+.
\]

The proposed load is the finite provisional demand before exact allocation, not already capacity-clipped actual allocation. Apply bounded control and monitor oscillation. The equation alone does not prove stability of the cognitive system.

A congestion price can inform scheduling cost once. It is neither epistemic confidence nor an acceptance margin. Exact capacity remains a hard constraint regardless of price or pressure.

## 11. Planning packets and resource allocation

### 11.1 Whole operations, not individually attractive atoms

A candidate packet contains:

```text
operation/attempt identity
mode and context
source goals and obligation slices
schema/rule/model revisions
participants and complete variable bindings
RequirementSet and witness dependencies
causal/procedural effect model, where relevant
resource claims and temporal intervals
observation and completion predicates
exact-product identity rule
relief and durability contract
cancellation/recovery/idempotency policy
required certificates and expiry
```

Selection of a multi-step plan can be provisional before all future steps are ready. Executing the next step requires its own current requirements and certificate. Do not hold every future resource indefinitely merely because a plan was selected.

### 11.2 Candidate value

Pressure locates important regions and decides how much planning effort to spend. The final scheduler evaluates incremental expected goal-loss reduction of a plan or portfolio relative to existing commitments.

For an additional portfolio \(S\), baseline commitments \(C\), and a declared horizon \(T\), use the conceptual objective:

\[
V(S\mid C)=\sum_g w_gu_g\kappa_g\delta_g(T)
\mathbb E[L_g(X_T^{C})-L_g(X_T^{C\cup S})]
-\operatorname{cost}(S)-\operatorname{riskPenalty}(S).
\]

The expectation requires an explicit outcome model, not an arbitrary multiplication of PLN strength and confidence. Confidence can qualify model uncertainty; it is not automatically a success probability. Correlated effects and jointly necessary steps require a joint model or conservative treatment.

This is a selection objective, not a claim of computationally cheap global optimization. Start with bounded coherent plans and feasible greedy/beam selection, and measure regret against small exact test cases.

Do not multiply this objective again by raw pressure, flux, or bridge score. Goal importance and relief already appear in it. Learned conductance guides discovery and work cost; any use in outcome prediction must be explicit and must not double-count the same evidence.

For information gathering, value the possible improvement to a subsequent decision rather than pretending that the observation itself changes the external world. Retain explicit exploration/monitoring budgets where a reliable value-of-information model is unavailable.

### 11.3 Hard feasibility

For every resource and time interval, enforce the actual claim constraint:

\[
\sum_{o\in S\cup C}claim_{o,r}(t)\le capacity_r(t).
\]

Check all required premise, context, contradiction, policy, causal-model, resource, and freshness gates. Reserve with a single authority or transactionally equivalent resource coordinator. Two workers cannot both rely on an unreserved last unit.

Pressure can change which admissible plan wins. It cannot make an inadmissible plan feasible.

## 12. PLN integration and the causal action boundary

The inspected MeTTa-native PLN implementation documents strength/confidence truth values, evidence IDs, deductive/inductive/abductive rules, and bounded inference controls. These are the integration points; they do not by themselves implement this lifecycle engine. [S4]

Keep four uses of reasoning distinct:

1. **Belief:** derive or revise a scoped assertion from evidence.
2. **Requirement checking:** establish whether a grounded prerequisite contract passes.
3. **Planning:** propose an operation or hypothesis that might lead to a desired state.
4. **Outcome attribution:** relate observed events and products to prior attempts and goals.

Pressure may trigger any of these, but must not appear as evidence in a truth formula. Increasing urgency, repeating a derivation, or rediscovering an operation does not provide independent support. The existing library's evidence-overlap tracking is useful; the extension must also preserve common-source lineage where different IDs refer to dependent evidence. [S4]

For example, `A implies B` does not authorize an action that establishes A. Backward goal expansion identifies A as a candidate prerequisite; an independent capability or procedural/causal model must support the operation proposed to establish it. Abductive hypotheses remain hypotheses until their role is justified.

The library's concrete deduction implementation contains explicit probability-consistency checks and a fallback truth value when conditions fail. The adapter must expose invalid preconditions as a failed/unknown operation, not treat a returned fallback pair as certification. [S5]

A prerequisite can be satisfied under a declared uncertain-risk contract without certainty. Hard gating means exact enforcement of that contract, not pretending all admitted premises are known with probability one.

## 13. Outcome contracts and pressure discharge

### 13.1 Submission is not success

Preserve independent milestones and require each to reference an observation, authoritative executor record, or checked derivation appropriate to that predicate.

An acknowledgment proves at most what the executor's acknowledgment contract says. It does not establish that the correct artifact exists, that the goal improved, or that the improvement persisted.

### 13.2 Exact product identity

A product observation specifies the exact relevant identity and scope: artifact digest/version, entity, owner/location when applicable, creation time, and operation linkage. A similarly named or pre-existing object does not necessarily satisfy the contract.

Differentiate goal satisfaction from causal credit. A goal may become satisfied through an external event even when the selected operation had no effect. Conversely, temporal succession alone does not prove that the operation caused relief. Conductance/outcome learning needs an explicit attribution model and confounder policy.

### 13.3 Delayed and durable relief

A durability contract defines the monitored predicate, window, sampling/freshness requirements, and failure policy. A timer reaching its end without observations does not prove continuous success.

Outcome labels include:

```text
PENDING: required outcome window has not matured
OBSERVED_SUCCESS: declared observed outcome satisfied
OBSERVED_FAILURE: supported failure condition satisfied
UNKNOWN: available data do not resolve the contract
CENSORED: observation ended before the contract could be resolved
```

A declared operational timeout can end an attempt without providing a valid training label for its eventual causal outcome. Do not automatically train censored outcomes as failures or successes.

Release/renew reservations according to the operation policy. Monitoring, recovery, or maintenance pressure may remain after provisional relief.

### 13.4 Reopening demand

Loss is recomputed from current supported conditions. If a maintained benefit disappears, create a new loss revision and reopen demand. Avoid incrementing a mutable cumulative pressure counter simply because multiple supports reported the same failure.

A partially successful operation discharges only the observed goal slices it satisfies. Other slices and unrelated goals remain unresolved.

## 14. Hard gates and certification geometry

Retain `PASS`, `FAIL`, `UNKNOWN`, and `STALE`. Only a current `PASS` authorizes the specified operation.

Use separate subjects for:

```text
inspection route
inference premise bundle
lifecycle transition
resource reservation
external operation submission
result admission
goal relief/durability judgment
```

The gate for a selected action does not automatically cover all subsequent steps or observations.

For a candidate operation \(o\):

\[
H_o=\bigwedge_{k\in required(o)}[check_k(o)=PASS].
\]

Pressure, demand, urgency, and utility do not enter this conjunction. For flow or dispatch, a closed gate produces zero permitted execution. For source demand, a closed gate does not produce zero need.

Preserve certification geometry as in v0.1: numerical margins measure slack against specified constraints. A verified robustness radius exists only where the norm, constraint functions, and bounds justify it. Discrete contradiction, unsupported predicates, and stale proofs do not acquire a numeric distance by fiat.

A small positive margin can create separately authorized monitoring or revalidation pressure. It cannot change a FAIL to a PASS or substitute for dependency-based invalidation. Utility must never compensate for a negative margin.

Joint checking includes the entire requirement bundle and relevant invariant closure, even constraints that have low STI or lie outside the pressure field's truncated search neighborhood.

## 15. Functional dependent AtomSpace and incremental invalidation

### 15.1 Authoritative records versus derived projections

Keep external observations, policy revisions, accepted belief revisions, lifecycle events, goals, and reservations as authoritative records owned by their respective services.

Derive the following as side-effect-free functions of an explicit snapshot:

```text
requirement satisfaction
usable lifecycle stage/progress summaries
open goal deficit and commitment coverage
current candidate readiness
pressure graph and pressure values
current transport coefficients
certificate validity views
```

The computed objects carry support fingerprints. A derived function does not silently execute a tool, change a goal, or reserve a resource.

### 15.2 Complete dependency tracking

Track reads of facts, belief revisions, schema/rule versions, policy versions, resource leases, observations, and time/freshness boundaries.

Also track negative and aggregate dependencies: absence of a blocker, all-members conditions, counts, or range queries can become invalid when a new atom appears. Recording only atoms found by the last query is insufficient.

For the first implementation, any relevant context revision may conservatively invalidate affected classes of certificate. Finer-grained invalidation is an optimization only after completeness tests pass.

### 15.3 Delta path

On an event:

```text
append/deduplicate event
advance snapshot revision
invalidate affected judgments and certificates
recompute dependent lifecycle and requirement projections
reconcile reservation/coverage obligations
recompute goal deficits and typed source demand
update pressure graph/operator for a new epoch
refresh candidate queues and attention seeds
```

Pressure-field truncation is an optimization for search, not a justification for excluding a potentially applicable hard constraint.

### 15.4 Cold/incremental equivalence

For the same authoritative event log, revision, schema/model versions, and deterministic inference/derivation policy, a cold projection and an incremental projection must produce the same authoritative derived judgments. Compare numeric fields within an explicit tolerance and bound their solver residuals.

If stochastic sampling is used, pin random seeds or compare the specified deterministic summary rather than demanding impossible bitwise equality across different samples.

A partial search result may legitimately differ from a fully explored one, but must carry its horizon/budget and unknown status. Neither may falsely report a certified negative merely because no witness was found.

## 16. Storage schema extension

These are application-level schemas, not newly claimed built-in AtomSpace types.

| Structural object | Contents |
|---|---|
| `RD.LifecycleSchema` | States, typed transitions, outcomes, regressions, versions |
| `RD.LifecycleEpisode` | Entity, schema revision, context, event history |
| `RD.LifecycleTransition` | Grounded from/to state, witnesses, certificate |
| `RD.RequirementSet` | AND/OR/temporal/resource expression |
| `RD.RequirementWitness` | Supports, interpretation, context, time interval |
| `RD.GoalEpisode` | Loss definition, importance, completion and durability contract |
| `RD.ObligationSlice` | Source identity and overlap/discharge semantics |
| `RD.PressureScope` | Anchor, goal, channel, context, epoch |
| `RD.OperationEpisode` | Persistent attempt identity, packet, independent milestones |
| `RD.ResourceClaim` | Quantity, resource, interval, mode, release policy |
| `RD.Reservation` | Owner, claim, lease, revision, status |
| `RD.OutcomeObservation` | Exact product/effect identity and provenance |
| `RD.ReliefJudgment` | Goal slices, observed relief, attribution, durability status |
| `RD.DependencySupport` | Positive/negative/aggregate/time dependencies |
| `RD.StrandedObligation` | Source, blocking reason, next admissible diagnostic operations |

Suggested Value namespaces:

```text
lifecycle.progress                 # nullable, typed by schema
lifecycle.maturity                 # derived and schema-specific
pressure.outstanding               # source priority units
pressure.open                      # uncovered source priority units
pressure.infer / observe / act / expand / retain
pressure.stranded                  # attributed source diagnostic, not sum over paths
field.pressure_potential            # dimensionless normalized attraction
field.activation                   # finite allocation units
field.kernel_density               # local support density, not demand
conductance.mode_rate               # nonnegative routing coefficient
resource.congestion_price           # optional cost per resource unit
outcome.predicted_coverage           # estimate, not evidence of success
cert.margin                         # check-specific units
runtime.next_check_at                # exact time/turn type
runtime.source_revision / epoch      # exact IDs, not floats
```

Lifecycle status, schema identity, dependency links, and certificate provenance need first-class searchable representations. Convenience caches do not become authority simply because they are attached to an atom.

AtomSpace's Value example documents that Value keys are not automatically indexed for arbitrary threshold queries. Maintain explicit indexes/queues for pending operations, live leases, stale supports, pressure frontiers, and outcome windows rather than scanning every atom each tick. [S2]

## 17. Reference orchestration

The following is pseudocode for service responsibilities, not a runnable AtomSpace API:

```text
on_event(event):
    revision = event_store.append_once(event)
    snapshot = snapshot_service.read(revision)

    affected = dependency_index.invalidate(event, snapshot)
    lifecycle_view = lifecycle_projector.refresh(snapshot, affected)
    reservation_view = reservation_service.reconcile(snapshot, lifecycle_view)
    goal_view = goal_monitor.evaluate(snapshot, lifecycle_view, reservation_view)

    sources = pressure_sources.derive(goal_view)
    view = dependency_materializer.build_bounded_view(snapshot, sources)
    fields = pressure_solver.solve_new_epoch(view, sources)
    budget = attention_allocator.rebalance(fields, monitoring_obligations)

    recalled = recall(snapshot, fields, budget)
    working_set = gated_transport(recalled, fields, budget)
    candidate_packets = reason_and_plan(snapshot, working_set, budget)
    candidate_packets += resume_ready_existing_episodes(snapshot)

    provisional_selection = scheduler.select_coherent_portfolio(
        candidate_packets, existing_commitments=reservation_view)

    for packet in provisional_selection:
        current = snapshot_service.latest()
        certificate = certifier.check_complete_next_operation(packet, current)
        if not certificate.current_pass:
            record_unresolved_obligation(packet, certificate.reason)
            continue

        committed = coordinator.reserve_and_record_intent_atomically(
            packet, certificate, expected_revision=current.revision)
        if not committed:
            requeue_for_revalidation(packet)
            continue

        dispatcher.submit_idempotently(committed)

    outcome_monitor.schedule_required_observations()
```

For a purely internal inference, the commit is admission of a belief proposal, not an external submission. For an observation, its actual observation record returns through `on_event`. Dispatch cannot invent the result event.

## 18. External consistency, restart, and cancellation

A local transaction cannot generally make an arbitrary remote side effect and a local write atomic. Record an operation intent and durable attempt ID before submission. Use the executor's idempotency capability where available. On uncertainty, reconcile the same attempt rather than issuing a fresh action blindly.

Where the executor offers no idempotency or authoritative reconciliation, mark the outcome uncertain and require a policy-defined recovery procedure. Do not promise exactly-once external effects from local persistence alone.

Restart rebuilds live operation episodes, leases, observation deadlines, goals, and supports before deriving new pressure. Transient activation can be reset; persistent obligations cannot.

Cancellation stops or compensates only as supported by the executor and schema. A cancelled request can still have taken effect. Record and reconcile late outcomes. Releasing a local reservation does not prove that a remote resource or effect has been released.

## 19. Worked example: a deployment goal

Assume an illustrative software service goal: run the intended artifact version and observe healthy behavior for a declared window. This example specifies behavior; it is not an operational recommendation for a particular real service.

Requirements for submission are an exact tested artifact, a valid permitted credential, and an exclusive deployment slot. The desired health observation is a result condition, not a prerequisite pretending the deployment already succeeded.

| Event | Lifecycle/requirement consequence | Pressure consequence |
|---|---|---|
| Goal created; artifact untested; credential status unknown | Goal active; two unresolved requirements | Test/inference pressure plus credential-observation pressure |
| Artifact test succeeds with valid evidence | Artifact requirement becomes usable | Its production deficit closes; remaining pressure concentrates elsewhere |
| Credential is observed expired | Credential prerequisite false | Authorized renewal/alternative-route pressure; no deployment authority |
| Renewal submitted and acknowledged | A live attempt is pending | Suppress duplicate renewal through a lease; preserve need and monitor |
| New valid credential observed | Credential requirement satisfied | Deployment can compete for the slot |
| Slot reserved; submission gate passes | Operation has current binding/certificate | Execute once under attempt identity |
| Executor acknowledges deployment | Submission milestone only | Outstanding goal remains; observation pressure continues |
| Wrong artifact version observed | Exact-product contract fails | Do not credit success; generate admissible diagnosis/recovery pressure |
| Correct version and immediate health observed | Provisional goal relief supported | Close satisfied slices; retain durability monitoring |
| Health window supported by adequate observations | Durability contract passes | Discharge the episode or retain maintenance goal |
| Later failure during maintenance | Current goal condition regresses | Reopen the appropriate deficit, not all historical work |

A failure cannot be overcome by increasing goal urgency. A valid alternative operation may be selected, but it requires its own complete certificate.

### 19.1 Coverage accounting

Suppose current loss is 10 normalized units and live commitments conservatively cover 6. With unit goal weight, urgency, and commitment factor:

```text
outstanding source demand = 10
estimated committed coverage = 6
open source demand = 4
observed relief = 0 unless evidence establishes it
```

Monitoring of the covered 6 remains necessary. If the commitment expires without supported relief, coverage returns to zero and open demand returns to 10. A duplicate promise for the same 6-unit goal slice does not create 12 units of coverage.

### 19.2 Complementary prerequisites

Suppose A and B are both needed for a final operation that removes 4 loss units. Completing A alone or B alone has zero immediate goal relief. A complete feasible plan costing 1 unit for each prerequisite can still have value 2 before other costs/risks.

A planner that only dispatches work with positive one-step observed relief would never start. Pressure must expose both blockers and the planner must evaluate the complete enabling sequence. This does not permit running the final operation before both requirements pass.

### 19.3 Cyclic pressure is not new demand

For a source of 10, attenuation 0.8, and routes source -> A -> B -> A, the fixed point is:

```text
source pressure score = 10
A pressure score = 22.222222...
B pressure score = 17.777777...
sum of graph scores = 50
actual source demand = 10
```

The scores are bounded path relevance. There are not 50 loss units, 50 attention units, or 50 independent pieces of evidence. This example is why source ledgers, field values, and execution budgets must remain separate.

## 20. Acceptance tests

| Test | Required result |
|---|---|
| Increase pressure on a failed action gate | No authorization or execution |
| Increase pressure on a stale certificate | Revalidation required |
| Failed action but permitted observation | Observation may run; action remains blocked |
| No available route | Source remains unresolved with reason |
| Unknown requirement | No false satisfaction; inference/observation work can be proposed |
| Missing AND conjunct | Final transition blocked; missing conjunct retains planning pressure |
| Individually compatible but jointly inconsistent witnesses | Whole requirement set rejected |
| Two alternative OR branches | No incoherent partial branch can execute |
| Complementary zero-immediate-reward prerequisites | Complete feasible plan can be discovered |
| Duplicate paths to one goal | No duplicated source loss or allocation |
| One operation helps distinct goals | Real shared benefit can be counted once per distinct goal contract |
| Duplicate commitments for the same slice | Coverage is not doubled |
| Submission/acknowledgment only | No observed-success or relief label |
| Exact product mismatch | Product/relief contract fails |
| Observation window ends without sufficient data | Unknown/censored, not durable success |
| Evidence/rule/schema change | Affected supports and certificates stale |
| New blocker not present in old query | Negative/aggregate support invalidation works |
| Expired prerequisite | Dependent future step blocked; historical event preserved |
| Two workers reserve last capacity unit | At most one current reservation |
| Crash after remote submission | Reconcile same attempt; do not blindly duplicate |
| Cycle with no ground support | No bootstrapped truth or lifecycle satisfaction |
| Fixed pressure operator | Nonnegative solution; norm bound and residual tolerance |
| Activation transport | Nonnegative allocation, conserved between transfers/reservoir |
| High urgency versus resource capacity | Capacity remains enforced |
| Cold versus incremental projection | Same supported judgments for the same complete snapshot/policy |
| Goal weight changed without evidence | Pressure changes; belief revision does not |
| Selected-but-never-executed operation | Not trained as a completed attempt |
| Censored/late outcome | Label remains distinct and is reconciled if evidence arrives |
| Retention cleanup | No live support lost; terminal episodes release unneeded pins |

The companion `pressure_field_lifecycle_reference_checks.py` checks only selected numerical/accounting models in this proposal. It is not a full AtomSpace/PLN/lifecycle implementation or an end-to-end correctness proof.

## 21. Defaults and staged implementation

### Initial defaults

| Choice | Default |
|---|---|
| Authoritative execution | Existing exact requirement/gate/reservation path |
| Pressure role | Advisory metareasoning and task-driven attention input |
| Bridge/flow authority | Shadow/advisory until separately evaluated |
| Goal source storage | Persistent and revisioned |
| Typed channels | infer, observe, act, expand, retain |
| Pressure attenuation | 0.85, configurable in (0,1) |
| Pressure operator | Nonnegative column-substochastic, frozen per field epoch |
| Solver | Bounded iteration; report residual/error bound, not a false converged flag |
| Initial iteration cap | 128; incomplete convergence remains advisory and is reported |
| Pressure tolerance target | Relative/absolute 1e-8 where affordable; application-specific scales |
| Activation budget and kernel policy | Inherit v0.1, with pressure-derived task potential |
| Schema changes | Pinned version; checked migration |
| Unknown or stale gate | Closed for that operation |
| Invalidated goal support | Recompute loss and reopen unmet obligations |
| Resource allocation | Single coordinator per resource authority initially |
| Observation windows | Domain/outcome-contract-specific; no universal timeout |
| Retention | Pin live supports, reservations, goals, and outcome obligations |

The defaults are starting points for tests, not measured optimal parameters.

### Delivery sequence

**A. Lifecycle and support substrate:** implement dynamic schemas, requirement expressions, exact supports, event projection, regression, and certificates. Test without any pressure model.

**B. Persistent goal and operation ledgers:** introduce source losses, episode identity, reservations, overlap-aware coverage, outcome contracts, and crash reconciliation.

**C. Scalar/typed pressure projection:** compute goal-conditioned backward pressure; maintain stranded obligations; use it to order bounded recall while the existing verified path retains authority.

**D. Transport integration:** feed pressure into ECAN seeding and the existing conservative transport. Measure duplicate work, starvation, completion, and gate rejection behavior.

**E. Plan packets and attribution:** support coherent multi-step alternatives, causal/epistemic distinctions, delayed outcomes, and conservative goal credit.

**F. Adaptive bridge/congestion experiments:** compare shadow predictions and candidate orderings against the baseline. Only consider bounded scheduling influence after invariants and equal-budget evaluations pass. These models never acquire permission to bypass gates.

## 22. Evaluation criteria and limits

Compare equal total compute, observation, and action budgets. Track goal loss over time, timely/durable relief, wasted duplicate work, stranded-demand duration, stale-check attempts, resource conflicts, evidence double-counting, and calibration of outcome/coverage predictions.

Ablate lifecycle persistence, typed channels, adaptive transport, bridge scores, and coverage accounting separately. A useful integration should improve observed task outcomes or reduce wasted work without hiding unresolved demand or relaxing acceptance contracts.

No claim is made here that pressure-field dynamics automatically produce optimal planning, calibrated probabilities, global consistency of arbitrary logic, or physical-fluid behavior. The formal guarantees stated are local to their assumptions: a fixed contraction operator, a conservative transport update, explicit resource checks, and certified operations within the declared checker scope.

The architectural conclusion is:

> Lifecycle dependencies specify what can develop and what it needs. Goal pressure identifies unresolved need across that dependency structure. Reachability and hard certification determine which operations are admissible. ECAN and transport allocate finite effort. PLN supplies evidence-sensitive judgments. Persistent operation lifecycles ensure that only appropriately observed outcomes discharge the corresponding obligations.

## Sources and provenance

The application design and equations are proposed here. Earlier user discussions and the accompanying v0.1 file supply the architectural constraints; they are not treated as evidence of currently deployed implementation features. Public sources below support the specific backend descriptions only. Consulted 30 September 2026; an implementation must pin tested commits rather than rely on moving branches.

**[S1] OpenCog AtomSpace — Atoms/Values, immutable indexed structure and mutable value flows.**  
`https://github.com/opencog/atomspace`

**[S2] OpenCog AtomSpace values example — per-atom Values and lack of automatic Value-key indexing.**  
`https://raw.githubusercontent.com/opencog/atomspace/master/examples/atomspace/values.scm`

**[S3] OpenCog AttentionValue — STI, LTI, VLTI and whole-object replacement.**  
`https://raw.githubusercontent.com/opencog/attention/master/opencog/attentionbank/avalue/AttentionValue.h`

**[S4] TrueAGI PLN README — MeTTa-native inference, strength/confidence, evidence tracking and bounded search.**  
`https://raw.githubusercontent.com/trueagi-io/PLN/main/README.md`

**[S5] TrueAGI lib_pln.metta — concrete truth formulas and rule preconditions.**  
`https://raw.githubusercontent.com/trueagi-io/PLN/main/lib_pln.metta`
