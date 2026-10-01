# Reachability-Driven AtomSpace
## Integration specification and reference architecture — Proposal v0.1

**Prepared:** 30 September 2026  
**Design basis:** Kevin Machiels's reachability-driven cognitive architecture, discussed as Phase Reachability Field Theory.  
**Required invariant:** Acceptance gates are hard gates. Attention, utility, similarity, transport intensity, and confidence cannot override a failed or unresolved gate.  
**Status:** A proposed engineering specification, not a claim that this complete integration already exists or has been experimentally validated.

## 1. Purpose and architectural decision

Integrate AtomSpace, Probabilistic Logic Networks (PLN), Economic Attention Allocation (ECAN), adaptive SPH-inspired transport, conductance fields, goal-conditioned utility potentials, contradiction gates, certification geometry, and semantic fields into one cognitive substrate.

The governing separation is:

> AtomSpace represents statements and relationships. PLN maintains uncertain beliefs. ECAN allocates scarce resources. Reachability determines which operations are admissible. Adaptive transport distributes activation over permitted routes. Utility prioritizes permitted work. Certification controls admission and acceptance.

Preserve the conceptual pipeline **Recall → Diffuse → Reason**, with admission before premise use and certification before committing a result. “Nearby does not equal admissible” is a system invariant, not merely a ranking preference.

Most local numeric state belongs in atom-attached Values. However, contexts, inference instances, evidence dependencies, constraints, contradiction witnesses, and certificates must also be represented as first-class graph structures. A field is not merely a number on an atom: it is a context-indexed assignment across a domain of atoms and transitions, together with an update operator.

### 1.1 Implementation baseline

Use the AtomSpace Atoms/Values distinction as the reference storage model. The official repository describes immutable, indexed atom structure and per-atom key-value data; numeric annotations need not alter atom identity. Its current documentation also advises moving away from specialized TruthValue classes toward FloatValue. [R1]

Use a replaceable PLN adapter rather than binding the architecture to the legacy OpenCog PLN package. That repository says it is no longer maintained and points to Hyperon PLN. The modern MeTTa-native implementation documents strength/confidence pairs, evidence IDs, and resource-bounded inference. These implementations are not assumed to have interchangeable runtime APIs. [R3, R4]

ECAN's AttentionValue implementation represents STI, LTI, and VLTI, and replaces attention objects as a unit. This proposal uses those conceptual responsibilities without assuming every historical ECAN agent can run unchanged against a current AtomSpace build. [R5]

Pin exact dependency commits in an implementation manifest. Record the AtomSpace revision, attention implementation revision, PLN implementation and rule-formula revisions, compiler/runtime versions, and schema version. Repository descriptions establish the interface direction; they are not a compatibility test.

### 1.2 Scope

The first implementation is a single-authority, single-host service over one logical AtomSpace. It may run parallel read-only workers, but a single admission/commit authority owns accepted knowledge for each reasoning context. Distributed storage is not necessary to implement this design.

The proposed transport is a **graph-based, SPH-inspired adaptive kernel transport**, not a claim that semantic reasoning obeys fluid mechanics. Classical SPH supplies an inspiration for local kernel support and adaptivity; the conservative graph update below is the explicit algorithm being proposed. [R7]

## 2. Terminology and semantic boundaries

### 2.1 Statement identity

A proposition is a typed AtomSpace expression. Type, node name, link type, argument order where semantically ordered, and outgoing structure determine its structural identity under the backend's canonicalization rules.

Truth estimates, STI, activation, utility, and certificate caches do not participate in that structural identity. An observed event's actual time, modality, subject identity, or proposition-defining context does participate in the represented statement where changing it changes meaning.

A node naming a concept is not automatically a truth-bearing assertion. Attach belief values to well-defined assertions, relations, or explicitly interpreted membership claims. Do not attach an unexplained probability to a bare entity name.

### 2.2 Context, goal, session, and revision

Use separate identifiers:

| Identifier | Meaning | Change consequence |
|---|---|---|
| `context_id` | World/scenario, assumption environment, temporal scope, interpretation and constraint regime | Can change what a statement means or whether premises can be combined |
| `goal_id` | Objective and utility definition | Changes prioritization, not truth by itself |
| `session_id` | One bounded reasoning episode | Separates activation and compute budgets |
| `knowledge_revision` | Version of the usable belief state in a context | Invalidates certificates bound to an earlier state unless explicitly revalidated |
| `field_epoch` | One consistent transport-state update | Changes activation, density and flux without itself changing beliefs |
| `policy_revision` | Required gate checks and constraint versions | Invalidates affected certificates |
| `rule_revision` | Exact rule schema, truth formula and preconditions | Invalidates affected derivations |

A belief is scoped primarily by `(proposition, context_id)`. A transient field sample is scoped by `(anchor, context_id, goal_id, session_id, field_epoch)`. Never overwrite one goal's field state with another goal's state or manufacture a different belief because the goal changed.

Context inheritance is explicit and versioned. A child context can add assumptions but cannot silently remove parent invariants. Crossing contexts requires an explicit translation or discharge rule with a certificate; shared atom identity is not permission to mix premises.

### 2.3 Four different kinds of availability

`STORED` means the system has a representation. `RECALLED` means it was retrieved. `USABLE` means a scoped belief or assumption is allowed as a premise under a specified interpretation. `ACCEPTED` means a particular result revision passed its required admission contract.

None implies absolute truth. In particular, an accepted probabilistic estimate remains an estimate with its original strength and confidence. Its certificate verifies the specified operation and checks, not certainty of the real-world proposition.

A report that a source asserts P can be stored alongside a report that another source asserts not-P. Those are compatible reports about sources. They do not automatically authorize treating both P and not-P as hard premises in the same assumption environment.

## 3. Representation model

### 3.1 Three representation layers

**Semantic graph:** propositions, concepts, relations, rules, contexts, goals, explicit assumptions and constraints.

**Operational graph:** instantiated rule applications, premise bundles, variable bindings, proposed conclusions, evidence records, derivations, certificates, contradictions, and field definitions.

**Value state:** numeric beliefs, attention values, activation, density, smoothing support, utility, conductance, rates, flux, estimated costs, lifecycle caches, and revision pointers.

The operational graph prevents an important modeling error: a binary knowledge link is not necessarily the operation that needs certification. A multi-premise inference needs its own identity and dependencies.

### 3.2 Application-level object types

These are proposed application schemas, not claims about existing built-in AtomSpace types. They can initially be encoded with existing ConceptNode, PredicateNode, ListLink, SetLink, and EvaluationLink structures. Custom registered types can be introduced later without changing their semantics.

| Object | Required identity or structural references |
|---|---|
| `RD.Context` | Stable ID; assumption set; parent contexts; temporal and modality scope; logic and policy references |
| `RD.Goal` | Stable ID; objective definition; utility model; termination conditions |
| `RD.ScopedStatement` | Proposition and context |
| `RD.FieldScope` | Anchor, context, goal, session; field-definition reference |
| `RD.Evidence` | Evidence ID; source; asserted content; observation time; lineage and dependence group |
| `RD.BeliefRevision` | Scoped statement; immutable revision ID; evidence/derivation references; interpretation |
| `RD.Rule` | Typed premise patterns; conclusion construction; truth formula; preconditions; assumptions |
| `RD.Transition` | Rule revision; bound premise revision IDs; binding map; proposed conclusion expression; context |
| `RD.Derivation` | Transition; input revisions; result revision; complete provenance root |
| `RD.Constraint` | Constraint ID; scope; checker; parameters; version; exact acceptance condition |
| `RD.Certificate` | Subject operation/result; checker results; dependency revisions; policy and rule revisions; witness/proof references |
| `RD.Contradiction` | Incompatible claims or constraints; context; witness; supporting dependency set |
| `RD.FieldDefinition` | Domain, field components, units, neighborhood policy, update operator and model revision |

Use deterministic content-derived identifiers for inference instances and evidence when suitable, but do not assume the backend's native atom handles are cryptographic hashes. Canonicalization must preserve variable binding and ordered rule-argument semantics.

### 3.3 Encoding scoped state without inventing core APIs

An illustrative Atomese encoding is:

```scheme
(use-modules (opencog))

(define proposition
  (EvaluationLink
    (PredicateNode "powered")
    (ListLink (ConceptNode "machine-M"))))

(define belief-scope
  (ListLink
    (ConceptNode "rd:belief-scope/v1")
    proposition
    (ConceptNode "context:plant-A:t1")))

;; [strength, confidence], interpreted by the registered PLN adapter.
(cog-set-value! belief-scope
  (PredicateNode "rd:pln/sc/v1")
  (FloatValue 0.85 0.90))

(define field-scope
  (ListLink
    (ConceptNode "rd:field-scope/v1")
    belief-scope
    (ConceptNode "goal:diagnose-M")
    (ConceptNode "session:001")))

;; [activation, support_density, bandwidth, utility, routing_reachability]
(cog-set-value! field-scope
  (PredicateNode "rd:transport/state/v1")
  (FloatValue 0.04 12.0 3.0 0.75 0.60))
```

The per-atom Value API pattern follows the project's example. The `rd:` names, scope layout and vector interpretation are this proposal. The snippet illustrates storage only; it does not implement admission or authorize direct mutation of protected belief state. [R2]

Production clients use the service API, not unrestricted `cog-set-value!` access to protected anchors. A user-created atom named “PASS” cannot constitute a valid certificate.

### 3.4 Value schema and ownership

Numeric vectors have a registered schema ID, component order, units, valid ranges and owner. Revision IDs and large integer counters are stored as typed integers or strings, not floating-point numbers that might lose precision.

| Namespace / fields | Scope and type | Writer / validation |
|---|---|---|
| `pln.strength`, `pln.confidence` | Scoped assertion; floats in [0,1] | Belief service via the pinned PLN adapter |
| `pln.evidence_weight` | Nonnegative model-specific weight, or explicit non-empirical tag | Belief service; never inferred from activation |
| `pln.formula_id`, `pln.provenance_ref` | IDs/references | Derivation service |
| `ecan.sti` | Context/session resource priority; backend-native signed scale is allowed | Attention allocator |
| `ecan.lti` | Domain/context retention priority | Retention manager |
| `ecan.pin_count` | Nonnegative count for protected retention dependencies | Reference manager; not a truth score |
| `transport.activation` | Nonnegative allocation units | Transport engine |
| `transport.density` | Nonnegative effective local support; not physical mass per volume | Field estimator |
| `transport.bandwidth` | Positive graph-cost radius | Adaptive support controller |
| `transport.route_reachability` | [0,1] routing heuristic, explicitly not proof probability | Reachability planner |
| `utility.value` | Finite, goal-normalized real | Utility evaluator |
| `utility.expected_cost` | Nonnegative work units | Scheduler profiler |
| `conductance.base` | Nonnegative transition/routing coefficient | Topology configuration or validated learner |
| `conductance.effective` | Nonnegative gated rate | Transport engine; recomputed when dependencies change |
| `conductance.flux` | Nonnegative activation transfer per microstep | Transport engine |
| `gate.route` | Boolean permit for one routing operation under its scope | Admission service |
| `gate.pre`, `gate.post` | PASS/FAIL/UNKNOWN/STALE plus certificate reference | Certifier |
| `cert.margins` | Typed vector of nullable signed numerical slacks | Certifier only |
| `cert.robust_radius` | Nullable nonnegative bound, norm and domain IDs | Verified robustness checker only |
| `runtime.lifecycle` | Enumerated state; non-authoritative convenience cache | State coordinator |
| `runtime.field_epoch`, `runtime.knowledge_revision` | Exact revision identifiers | Coordinator |

The ground truth for a gate is a verified certificate and its current dependencies, not a cached Boolean value. Every getter that could authorize work must verify that binding.

### 3.5 State placement rule

Store rapidly changing, non-search-critical data as Values. Store relationships that must be queried, explained, independently versioned, or reasoned about as Atoms. Preserve important historical evidence, derivations, certificates, contradictions and belief revisions as immutable records. Do not create a new semantic proposition for every activation tick.

AtomSpace Values and their keys are not automatically indexed for arbitrary threshold queries. Maintain explicit membership/index structures and scheduler queues for “high STI,” “pending certificate,” “evidence affected by source X,” and similar queries. [R2]

## 4. PLN integration: epistemic state

### 4.1 Belief interpretation

Store the strength/confidence pair with an explicit truth-model ID. Strength is a probability-like belief estimate; confidence expresses evidential support in the chosen PLN representation. “Frequency” is an appropriate interpretation for some empirical cases, not a universal substitute for strength across every statement or rule. The modern implementation explicitly uses strength/confidence and evidence stamps. [R4]

The adapter must expose:

```text
check_rule_preconditions(rule, premises, bindings, context)
apply_rule(rule, premises, bindings, context) -> ProposedBelief
revise(existing, new_support, dependency_model) -> ProposedBelief
explain(result) -> formula_id + assumptions + provenance
```

Application of a rule is a pure operation on an explicit snapshot. It may propose values and graph structure but cannot commit them to the accepted view.

### 4.2 Evidence weight and confidence

For a simple evidence-weight adapter, define:

\[
c = \frac{w}{w+k},\qquad w = \frac{k c}{1-c},\quad k>0.
\]

This is a declared adapter convention, not a guarantee that every PLN variant shares the same calibration. The inspected modern implementation's conversion uses `k=1`; use that only when selecting that adapter. A weight need not equal a literal observation count. [R6]

For independently justified, non-overlapping evidence with a shared interpretation:

\[
w=w_1+w_2,\qquad
s=\frac{w_1s_1+w_2s_2}{w},\qquad
c=\frac{w}{w+k}.
\]

Apply this only when its statistical and provenance assumptions hold. Distinct evidence IDs are necessary for preventing exact duplicate counting, but are not sufficient to establish independence: two sources can share a common origin. Preserve source lineage and dependence groups. If dependence cannot be justified or modeled, keep alternative supports or use a explicitly conservative revision policy rather than summing weights.

The `w=0` case is explicitly unknown; never divide by zero. Finite empirical evidence must not create `c=1` through rounding. Logical identities, stipulated axioms or exact results use an explicit interpretation tag; do not feed a certainty tag into the finite-weight inverse formula.

### 4.3 No attention-to-truth leakage

Repeated recall, high activation, high STI, high utility, diffusion, semantic proximity and frequent reuse do not create evidence. They cannot directly increase strength or confidence. A reasoning cycle that reconstructs the same derivation from the same evidence is idempotent for belief support.

Derived beliefs carry their source lineage. A cycle such as A → B → A must not generate independent evidence for A. Repeated derivations sharing an evidence root can improve search coverage or explanation quality without increasing evidential weight.

### 4.4 Contradiction and uncertain belief

Distinguish:

- incompatible hard commitments within one assumption environment;
- probabilistic values that violate a declared joint model;
- conflicting reports from sources;
- uncertainty or low confidence;
- changes in the world at different times.

Only the relevant first two necessarily block the proposed combined assertion under that contract. Conflicting source reports remain available for investigation. Low confidence alone is not a contradiction. A hard gate can accept a valid uncertain inference without setting its confidence to one.

Each rule's exact probabilistic side conditions, denominator domains and declared independence assumptions are gate inputs. Do not silently interpret a library fallback truth pair as evidence that a failed rule precondition passed. Undefined arithmetic, NaN, infinity and out-of-range results produce FAIL or UNKNOWN as specified by the contract, never acceptance.

## 5. ECAN integration: resource allocation and retention

### 5.1 Responsibilities

STI controls present processing priority. LTI controls longer-term retention/retrieval priority. Pinning protects dependencies that must persist, including live certificate supports and constraints. The historical AttentionValue implementation has STI, LTI and VLTI components; the separate pin count here gives retention protection an explicit reference-management contract. [R5]

Use context/session-scoped STI. A legacy global STI view may be a documented aggregate for compatibility, but it cannot become a global belief or gate decision.

### 5.2 Connection to transport

ECAN allocates the available attention budget and picks seeds. Transport redistributes that allocated budget on permitted routes. Do not let both ECAN's legacy diffusion agents and the new transport engine independently evolve the same activation state.

For recalled seed i, let:

\[
z_i=\max(0,\mathrm{STI}_i-\theta_{\mathrm{STI}}).
\]

Allocate a finite seed budget proportionally to `z_i`; if all are zero, use the explicitly configured exploration allocator. Withdraw the allocation from the session reservoir. Do not create activation merely because a new seed appeared.

After the episode, attributable useful outcomes produce bounded attention rewards. Merely revisiting a node is not useful evidence and should not earn unlimited reward. Resolved contradictions can receive diagnostic value without promoting the rejected claim.

Use a slow bounded retention update, for example:

\[
\mathrm{LTI}_{new}=(1-\eta)\mathrm{LTI}_{old}+\eta\,\widehat{V}_{retention},
\]

where the retention estimate is on the same normalized scale. Raw legacy LTI values require an adapter rather than an assumed numeric match. A low-LTI atom that supports a live certificate or mandatory constraint cannot be evicted until its dependencies are retained elsewhere or invalidated correctly.

## 6. Reachability and conductance

### 6.1 Knowledge links are not automatically inference routes

An AtomSpace link can represent a relation, syntax, a collection or a rule. None automatically means activation may flow in every direction, or that a premise can be used to establish the adjacent atom.

Build a typed operational routing graph and an explicit inference hypergraph. A routing arc records its allowed direction and purpose, such as retrieval, rule discovery, premise inspection or candidate evaluation. An inference transition records all required premises and one exact binding.

For a rule with premises P1...Pk and conclusion Q, preserve the conjunction:

\[
\tau=(\{P_1,\ldots,P_k\},\mathrm{rule},\mathrm{binding},\kappa)\longrightarrow Q.
\]

A factor-node encoding can implement this with an operation atom between the premises and the conclusion. Activating that factor means the operation is worth considering; it does not mean the conclusion has been established. Partial premise availability may trigger targeted recall, not partial acceptance.

### 6.2 Exact semantic reachability

The semantically authoritative state is an assumption environment plus its usable, versioned beliefs and constraints. A transition changes that state only after all relevant gates pass.

Two individually admissible transitions can still have mutually incompatible results. Therefore exact reachability is over **reasoning states and certified transitions**, not the unqualified union of reachable atom IDs.

For starting state Ω and work budget b, define reachable results by the existence of a sequence of state transitions whose total cost fits b and whose gates pass against each preceding state. A projected atom-level reachability score is only a scheduling approximation to that relation. It must not authorize combining alternative worlds or incompatible assumption branches.

This gives two distinct records:

`route_reachability`: a useful projected search heuristic; no proof claim.

`derivation_reachability`: a concrete certified derivation under a specific context and revision, with certificate references.

### 6.3 Hard topology mask

For a proposed routing arc, define:

\[
W_{ij}(t)=g^{route}_{ij}(\kappa,\nu,t)\,W^0_{ij}(\kappa,t),
\qquad g^{route}_{ij}\in\{0,1\}.
\]

`W0` is nonnegative base conductance; `g_route` enforces the routing operation's type, direction, context and permission contract. A gate that is unknown or stale is closed for that operation.

A permitted routing arc is not an acceptance certificate for an inference. The inference instance has its own stronger precondition and result gates, including all joint premises and relevant constraints.

Conductance can reflect validated route usefulness, computational cost, structural relation type and measured throughput. It must not silently encode truth. Coactivation can propose new retrieval associations, but cannot create inference authority without a corresponding checked rule.

### 6.4 Inspection without acceptance

A separate inspection work queue can retrieve rejected claims, negations, attack relations, and contradiction witnesses. That is not a bypass: inspection operations are explicitly permitted operations, while using the rejected claim as an accepted premise remains prohibited.

Gate decisions must consult a dependency-complete constraint/conflict index for the declared checking scope, not merely the high-activation neighborhood. Otherwise ECAN could make a contradiction disappear by forgetting to attend to it.

## 7. Adaptive SPH-inspired transport

### 7.1 Field state and units

For each active field anchor i, maintain activation `a_i ≥ 0`, support density `rho_i ≥ 0`, bandwidth `h_i > 0`, utility `U_i`, and a routing reachability estimate. For each directed arc i→j maintain its gate, base conductance, effective rate and last flux.

Activation is an allocation of a finite attention budget, not probability mass over mutually exclusive propositions. Two coactivated propositions are not thereby jointly true. Density is kernel-weighted representational support, not belief confidence or physical density.

Graph distance uses explicit positive routing costs, initially one cost unit per admitted hop. Its metric/version is recorded. Semantic embeddings are not required. An approximate similarity index can nominate recall candidates but cannot certify routes, premises or conclusions.

### 7.2 Kernel and adaptive support

Use the following proposed compact nonnegative kernel:

\[
K(r)=\begin{cases}(1-r)^4(1+4r),&0\le r<1\\0,&r\ge1.\end{cases}
\]

For a bounded permitted neighborhood N_i:

\[
\rho_i=\sum_{j\in N_i}\mu_j K(d(i,j)/h_i),\qquad \mu_j=1\text{ initially}.
\]

Include self-support in density estimation. Do not divide by an invented ambient dimension or treat this as a physical volume density. Neighbors must be in the same declared context/assumption environment, and any directed path used in neighborhood construction must use currently permitted routing arcs.

An effective-neighbor statistic is:

\[
n_i^{eff}=\frac{(\sum_j K_{ij})^2}{\sum_j K_{ij}^2},
\]

with zero-support handled explicitly. Adapt bandwidth toward a target n*:

\[
h_i^{new}=\operatorname{clip}\left(h_i\exp\left[\eta_h\log\frac{n^*}{\max(1,n_i^{eff})}\right],h_{min},h_{max}\right).
\]

Use hysteresis so small changes do not continually rebuild neighborhoods. Dense areas shrink their support; sparse areas expand it only to the configured maximum and only within permitted reachability.

A kernel neighborhood does not create a new inference edge. Multi-hop neighbors can inform support estimation, but actual flux in the reference implementation uses explicit direct routing arcs. No smoothing operation may jump a closed arc or mix incompatible assumption environments.

Bounded or sampled neighborhood estimation is allowed as a scheduling approximation and must be labeled as such. Bounded or sampled contradiction checking is not allowed to masquerade as a complete certificate.

### 7.3 Utility-biased transition rates

For a direct arc i→j, propose:

\[
q_{ij}=g^{route}_{ij}\,b_{ij}
\frac{K(d_{ij}/h_i)}{\sqrt{(\epsilon_\rho+\rho_i)(\epsilon_\rho+\rho_j)}}
\exp\!\left(\beta\,\operatorname{clip}(U_j-U_i,-L,L)\right).
\]

Here `b_ij ≥ 0` is base conductance adjusted for the configured work-cost model; `epsilon_rho > 0` protects the denominator; `beta ≥ 0` controls utility bias; and L bounds the exponent. Apply an explicit finite rate cap if necessary.

The density correction reduces the tendency of densely connected regions to dominate merely through the number of representations. It is a proposed heuristic requiring ablation tests, not a claim of a unique discretization of a physical PDE.

Evaluate the gate first in code. A closed gate sets `q_ij = 0` without evaluating an exponential, division or invalid numeric payload on that arc. This avoids “zero multiplied by infinity/NaN” becoming a hidden bypass or corrupting the update.

Utility changes the relative rate on a permitted route. It never changes whether the route is permitted. A high-conductance route cannot substitute for an inference certificate.

### 7.4 Conservative, nonnegative update

Let `r_i = sum_{j != i} q_ij`. Choose:

\[
\Delta\tau\le\frac{0.9}{\max_i r_i}.
\]

If every exit rate is zero, leave activation in place. Otherwise construct:

\[
T_{ij}=\Delta\tau q_{ij}\quad(i\ne j),\qquad
T_{ii}=1-\Delta\tau\sum_{j\ne i}q_{ij}.
\]

With activation represented as a column vector:

\[
a^{new}=T^\top a.
\]

Every row of T sums to one and has nonnegative entries. Therefore, in exact arithmetic, activation remains nonnegative and its total is conserved during transport. The directed flux is `F_ij = a_i Delta_tau q_ij`.

A graph kernel over a broad neighborhood does not itself establish those invariants. The nonnegative row-stochastic transition update is what establishes them here.

### 7.5 Reservoir, cooling and graph changes

Add an explicit session reservoir `a_reservoir` so total budget includes unallocated attention. Seed injection transfers from that reservoir. Cooling transfers back to it, for example `a_i ← (1-delta) a_i` with the removed amount added to the reservoir. New accepted conclusions receive allocation from the reservoir or a recorded redistribution, not newly minted attention.

If an active anchor becomes unusable, revoke its affected routing permits and move its remaining allocation to the reservoir. Never leave stale activation able to authorize work. Preserve its representation and diagnostic accessibility unless an independent retention/privacy policy requires removal.

Use one consistent gate/field snapshot for each microstep. A concurrent relevant revision cancels or invalidates the step before publication. Enforce finite-number checks before and after updates, and verify budget conservation to a declared numerical tolerance. Do not “repair” material negative values by silently clipping them.

### 7.6 SPH boundary and limitation

This proposal uses adaptive compact support, density estimation and local numerical transport, which are motivated by SPH methodology. It deliberately does not assume Euclidean particle coordinates, momentum, physical pressure, an ambient dimensionality, or a demonstrated continuum limit. [R7]

An embedding-space or fully geometric SPH implementation would be a separately versioned extension requiring its own metric, consistency and boundary conditions. It would still be subordinate to hard admission gates.

## 8. Utility potentials and semantic fields

### 8.1 Utility model

Utility is conditioned on a goal and measures expected value of allocating work, not the desirability of making a claim true. A reference form is:

\[
U_i=w_g V_{goal,i}+w_I V_{information,i}+w_N V_{novelty,i}-w_C C_i.
\]

Normalize each component to a documented common scale. Start with weights `(0.55, 0.25, 0.10, 0.10)` and treat them as tunable initialization rather than fitted cognitive constants. Expected information value concerns the benefit of resolving uncertainty; it is not automatically high simply because confidence is low.

A contradiction investigation may have high information utility. That increases its inspection priority, not the acceptance score of the contradicted claim. Bound learned utility updates and measure success by attributable outcomes or verified information gains, not by self-reported importance.

### 8.2 Field definition

Define the local sample of a semantic field as:

\[
\mathcal F_{\kappa,g,s}(i,t)=
(a_i,\rho_i,h_i,U_i,r_i^{route},\mathrm{diagnostic}_i).
\]

Define its transition component by the permitted routes, conductances and fluxes. The complete field also includes its domain, context, goal, update operator and version. Its meaning arises from that structured, evolving assignment, not from treating the vector as a context-free semantic embedding.

Useful readouts include active premise frontiers, activated rule applications, bottlenecks, blocked transitions, competing assumption branches, information-gathering priorities and currently certified derivations. These are views over the field and graph, not new truth values by default.

A contradiction-pressure view may summarize active attacks or failed candidate checks. It is explicitly diagnostic. It must not be inverted into a fabricated “probability of consistency.”

### 8.3 Composition and lifecycle

Field samples may be combined only across compatible contexts, goals and model versions. Different goal fields can share structural atoms and evidence while maintaining separate activation and utility. Resource competition between goals happens at the budget allocator, not by overwriting a shared scalar.

Use lifecycle state rather than inventing an unverified oscillatory “phase” variable:

```text
STORED → RECALLED → ROUTING_READY → CANDIDATE
                                   ↓
                              PRECERTIFIED
                                   ↓
                                DERIVED
                                   ↓
                              POSTCERTIFIED
                                   ↓
                                ACCEPTED

Gate failure → REJECTED record
Unresolved check → PENDING record
Changed dependencies → STALE record and re-evaluation
```

The exact field formulation and lifecycle above are recommended engineering choices; they do not claim to reproduce unspecified equations from the thesis.

## 9. Hard gates and certification geometry

### 9.1 Gate contract

A checker returns PASS, FAIL, UNKNOWN or STALE. Only a fresh PASS satisfies a required predicate. FAIL does not mean the proposition is universally false; it means the specified operation failed that contract. UNKNOWN and STALE are closed for authorization but eligible for bounded re-evaluation.

For required checks k on operation tau:

\[
G(\tau,\kappa,\nu)=\prod_k\mathbf 1[\mathrm{check}_k=\mathrm{PASS}].
\]

Use Boolean conjunction in the implementation. There is no weighted average, compensating utility term, nonzero epsilon floor or stochastic bypass.

There are separate contracts for routing, pre-inference admission, post-inference result acceptance, and any external action execution. An action policy may be stricter than a belief-admission policy. The current architecture does not require actions, but it must not conflate the two.

### 9.2 Required pre-inference checks

Verify structural typing and binding; compatible context, time and modality; exact premise revisions and permission to use them; availability of every jointly required premise; current rule and formula revision; provenance and dependency assumptions; arithmetic domain and probabilistic side conditions; consistency of the joint assumption environment; and all required context policies.

Read required constraints from the authoritative constraint index, including inactive or low-STI constraints. When the supported logic fragment or complete dependency scope is unavailable, return UNKNOWN rather than certifying the truncated check.

### 9.3 Required post-inference checks

Check the generated statement's type and scope, verify or replay the registered truth formula, validate its output and provenance, and check the proposed post-state against all applicable constraints. Verify that the conclusion does not introduce a hard inconsistency or an impossible probabilistic assignment under its declared model. Bind the result certificate to the candidate and all its input revisions.

Precertification prevents invalid premise combinations from entering normal inference. Postcertification verifies the actual result. Constructing a proposal or running a checker in a sandbox is not acceptance.

### 9.4 Joint consistency, not pairwise comfort

Consider hard commitments A, B and `not(A and B)`. Every pair is satisfiable; all three together are not. A per-atom gate or a table of pairwise compatibility values is therefore insufficient.

The certifier evaluates the entire proposed premise bundle and the relevant accepted state/assumptions. Alternative hypotheses reside in distinct assumption environments. The system may compare them, but it may not infer from their uncontrolled union.

For the first version, support finite propositional hard constraints with a complete satisfiability/model check, registered rule-specific numerical checks, and explicit arithmetic bounds. Greater expressivity requires another registered checker with a declared contract. An incomplete general search cannot claim that its failure to find a contradiction establishes consistency.

### 9.5 Certificate structure

Every immutable certificate contains:

```text
certificate_id, schema_version
subject_transition_id, subject_result_revision (when applicable)
context_id, knowledge_revision
rule_id, rule_revision, formula_id
policy_revision, required_checks_digest
premise_revision_ids, evidence_lineage_digest
constraint_scope_id, checked_constraint_digest
checker_ids, checker_versions, checker_results
proof_or_witness_refs, failure_witness_refs
numeric_margin_records
optional_robust_radius, norm_id, perturbation_domain_id
created_at, optional_expires_at
issuer_id, integrity_binding
```

The certificate's scope must say what was checked: for example, satisfiability of a finite hard-constraint set, feasibility of a local joint-probability model, or correct application of a registered uncertain rule. A satisfiability witness proves a feasible assignment for that model; it does not prove the real world has that assignment. A rule-application certificate does not upgrade an uncertain conclusion into a theorem.

Expiry is optional additional protection, not a replacement for revision invalidation. The trusted service verifies certificate provenance; storing a JSON record or an Atom named “certificate” is not itself a certification mechanism.

### 9.6 Signed margins

For a numerical constraint written as `f_k(x) ≥ 0`, record a conservative lower bound on its slack. With a positive, declared normalization scale sigma_k:

\[
m_k=\frac{\underline{f_k(x)}}{\sigma_k}.
\]

Positive means the constraint passes with numerical slack, negative means it fails, and missing or unestablished means unknown. Boundary equality follows the constraint's explicit inclusive/strict rule; strict constraints include their required safety allowance in f_k.

Record both raw units and normalized values. A bottleneck margin is:

\[
m_{min}=\min_k m_k,
\]

but only over numerical constraints with comparable declared normalization. Discrete predicates remain discrete. Do not assign invented distances to type errors, unsatisfied logical formulas or unknown checks. A positive numeric bottleneck cannot compensate for a failed Boolean check.

### 9.7 When a real distance bound is justified

If each numerical constraint has a verified Lipschitz bound L_k under a fixed norm and perturbation domain, then a conservative local radius is:

\[
r_{cert}=\min_{k:L_k>0}\frac{\underline{f_k(x)}}{L_k},
\]

also limited by the domain in which those bounds hold. Discrete assumptions and the constraint set must remain unchanged. This follows from `f_k(x+delta) ≥ f_k(x) - L_k ||delta||`.

Without those bounds, call the quantity a **constraint margin**, not a certified metric distance to contradiction. An estimated gradient or a semantic embedding distance is not sufficient. Even a valid local radius is relative to the checked model and assumptions, not universal consistency of the entire knowledge graph.

The first implementation uses margins for explanation and investigation priority. It does not let a cached radius authorize a different knowledge revision without full revalidation.

## 10. Execution, updates and consistency

### 10.1 The cognitive cycle

1. **Ingest.** Store observations with source lineage, scope and timestamps. Generate proposed belief revisions separately; storage of raw evidence is not acceptance of its content.
2. **Snapshot.** Bind the session to a context, goal, usable belief revision, rule registry, constraint index and policy revision.
3. **Recall.** Retrieve goal-relevant propositions, rule patterns, needed premises and counterevidence. Track the retrieval method without treating retrieval scores as belief support.
4. **Admit routing.** Validate routing operations and construct the current permitted routing graph. Preserve a separate diagnostic inspection queue for disputed material.
5. **Diffuse.** Initialize allocations from the reservoir, estimate support, update bandwidth, compute hard-masked rates and run bounded conservative transport microsteps.
6. **Form candidates.** Instantiate rule applications from activated structures. Missing jointly required premises trigger targeted recall; they never count as partially satisfied acceptance conditions.
7. **Precertify.** Validate the complete premise bundle, rule preconditions, assumption compatibility and applicable constraints against the snapshot.
8. **Reason.** Run the registered PLN operation in a side-effect-free sandbox using only the precertified inputs. Produce a proposed result and derivation record.
9. **Postcertify.** Check the actual result and its proposed post-state, formula, evidence dependencies and contradictions.
10. **Commit.** Under the context commit authority, verify that the bound revision is still current and atomically publish the accepted result, provenance and certificate.
11. **Feed back.** Update indexes, queue affected goals, allocate bounded resource rewards and invalidate any dependent records made stale by an explicit revision.
12. **Stop or repeat.** Continue until the goal's termination rule, work budget, candidate exhaustion or explicit cancellation. Budget exhaustion reports incomplete search, not proof of absence or consistency.

### 10.2 Orchestrator pseudocode

The following specifies responsibilities and failure paths. It is pseudocode, not an implemented AtomSpace API.

```python
def cognitive_cycle(context_id, goal_id, session_id, budget):
    snapshot = coordinator.snapshot(context_id)
    recalled, inspections = recall.collect(snapshot, goal_id, budget)
    routes = admission.authorize_routes(snapshot, recalled)
    field = transport.initialize(snapshot, goal_id, session_id, routes)
    transport.advance(field, budget.transport_steps)

    for transition in planner.rank_ready_instances(field, snapshot):
        if budget.exhausted():
            return Result(status="BUDGET_EXHAUSTED", revision=snapshot.revision)

        pre = certifier.precheck(transition, snapshot)
        if pre.status != "PASS":
            diagnostics.record(transition, pre)
            continue

        proposal = pln.apply_pure(transition, snapshot, permit=pre)
        post = certifier.postcheck(proposal, snapshot, permit=pre)
        if post.status != "PASS":
            diagnostics.record(proposal, post)
            continue

        outcome = coordinator.commit_if_current(
            expected_revision=snapshot.revision,
            proposal=proposal,
            pre_certificate=pre,
            post_certificate=post,
        )
        if outcome.status == "STALE":
            planner.requeue_for_fresh_evaluation(transition)
            continue

        yield outcome
        # Commit changed the premise universe. Rebuild against a fresh snapshot
        # rather than continuing with old permissions or stale field candidates.
        return Result(status="COMMITTED_RESTART", revision=outcome.revision)

    return Result(status="NO_READY_CANDIDATE", revision=snapshot.revision)
```

Inspection and certification work also consume explicit compute budgets. The fact that a belief inference failed does not forbid running a diagnostic computation that explains the failure.

### 10.3 Atomic acceptance and the write-skew problem

In v0.1, serialize accepted-state commits by context and compare the complete context revision. Two workers can evaluate against the same snapshot, but only the first commits; the other must revalidate against the new state. This prevents mutually inconsistent candidates from both passing checks against an old snapshot and then committing independently.

The accepted belief revision, its evidence/derivation references, certificates and current-state index become visible together through the service. Implement this as a coordinator transaction or write-ahead operation with atomic revision publication. Do not assume that several independent AtomSpace Value writes provide multi-record serializability.

The same authority handles source corrections and belief revisions. Retracting support can invalidate accepted descendants; mark them stale before exposing an accepted view that would treat them as current. Preserve history for explanation. Historical certificates remain valid records of what was checked then, but not authorization for the present.

Later fine-grained validation can replace coarse context serialization, but it must include predicate/absence dependencies. A certificate based on “no contrary assertion exists” must be invalidated by a newly inserted contrary assertion, not only by edits to already-read atoms.

### 10.4 Field update ownership

Use one writer per `(context, goal, session)` field. Dense arrays may be working buffers for computation, but they are not a second independently mutable source of truth. Publish field state with an epoch boundary under the service's read/write discipline; readers either obtain a consistent snapshot or explicitly request approximate diagnostics.

Truth/certification revisions and field epochs are separate. An activation change alone does not invalidate a belief certificate. An evidence, rule, assumption or relevant policy change does. Cache keys must follow those actual dependencies instead of invalidating everything on every transport tick.

### 10.5 Public service contracts

| Operation | Essential input | Result and restrictions |
|---|---|---|
| `intern_statement` | Typed statement expression | Canonical atom reference; does not accept it as true |
| `record_evidence` | Evidence ID, source, content, scope, lineage | Immutable observation record; duplicate IDs are idempotent |
| `open_context` | Assumptions, inherited constraints, scope | Versioned reasoning context |
| `begin_session` | Context, goal, compute/attention budget | Isolated field session |
| `propose_transition` | Rule revision, premise revisions, bindings | Candidate operation; no accepted-state mutation |
| `precertify` | Candidate and expected revision | Bound permit or FAIL/UNKNOWN/STALE |
| `infer` | Candidate and verified pre-permit | Proposed result only |
| `postcertify` | Proposal, context revision, pre-permit | Bound result certificate or non-PASS |
| `commit` | Proposal, certificates, expected revision | Atomic accepted revision or STALE |
| `query_belief` | Proposition, context, current/historical selector | Belief value, provenance, certificate status and interpretation |
| `inspect_field` | Context, goal, session, epoch selector | Non-authoritative field diagnostics |
| `explain_block` | Candidate/certificate ID | Failed checks, contradiction witnesses, unresolved dependencies |

Every mutation takes an idempotency key. Evidence producers and inference workers cannot mint certificates or directly modify accepted truth values. Typed permission boundaries, not just naming conventions, enforce ownership.

## 11. Worked examples

### 11.1 A highly useful but inconsistent premise bundle

Let A and B be individually investigable hypotheses, and let the context contain the hard constraint `not(A and B)`. A goal strongly favors a proposed result requiring both A and B.

The recall layer can retrieve both hypotheses and the constraint. The inspection layer can give both high attention. Their individual source reports can have high confidence. However, a transition that requires their joint hard assertion fails the bundle-consistency check. Its acceptance gate is zero regardless of utility or activation.

The planner can instead compare a context assuming A with a context assuming B, seek additional evidence, or choose another admissible route. It cannot combine the two branches by transporting enough activation between them.

### 11.2 Numerical contradiction geometry

Consider a declared joint model for two Boolean events:

```text
P(A) = 0.60
P(B) = 0.70
Proposed P(A and B) = 0.65
```

The exact joint-probability bounds are:

\[
\max(0,P(A)+P(B)-1)\le P(A\land B)\le\min(P(A),P(B)).
\]

Here the allowed intersection is [0.30, 0.60]. The candidate's upper-bound slack is `0.60 - 0.65 = -0.05`, so its numerical gate fails. A high utility, confidence or semantic proximity cannot compensate.

A candidate `P(A and B)=0.55` is feasible. One explicit witness is:

| Assignment | Probability |
|---|---:|
| A and B | 0.55 |
| A and not-B | 0.05 |
| not-A and B | 0.15 |
| not-A and not-B | 0.25 |

All cells are nonnegative and sum to one. The smallest cell margin is 0.05. This certifies feasibility of this local model, not the empirical accuracy of the probabilities.

For `x=(P(A),P(B),P(A and B))`, the four cell inequalities have infinity-norm Lipschitz constants 1, 2, 2 and 3 respectively. The minimum slack/L ratio is 0.025. Consequently an infinity-norm perturbation no greater than 0.025 preserves nonnegativity of these cells, with the same model and discrete assumptions. This is a meaningful local robustness bound because the norm, constraints and constants are specified.

### 11.3 Transport is not deduction

Suppose a rule requires both `Powered(M)` and `NotFaulty(M)` to derive `Operable(M)`. If activation reaches the rule from `Powered(M)` alone, the rule becomes a candidate for premise retrieval. It does not emit `Operable(M)` as an accepted belief.

If `NotFaulty(M)` is available only in an incompatible context or relies on retracted evidence, admission fails. If both premises pass, PLN can calculate an uncertain result, which still needs postcertification and a current-state commit.

### 11.4 A contradiction discovered later

A result was accepted at context revision 41. New evidence at revision 42 invalidates one of its premise supports. The invalidation index marks affected belief revisions, derivations, candidate permits and routing views stale. The old certificate remains an auditable historical record.

The current accepted view must not present that result as currently certified until it has been re-evaluated. Raising its LTI or retaining its historical atom cannot prevent invalidation.

## 12. Defaults, budgets and operational policy

These are recommended initialization values for a reference implementation, not experimentally established optima.

| Setting | Initial choice | Reason |
|---|---|---|
| Acceptance behavior | Fresh PASS required for every required check | Preserves the hard-gate contract |
| Unknown or unsupported check | Close authorization; retain pending diagnostic record | Does not confuse uncertainty with falsehood or permission |
| Commit authority | Single writer per context, full revision comparison | Simple protection against inconsistent concurrent commits |
| Truth storage | Named FloatValue schema plus explicit truth-model ID | Avoids hard dependency on specialized legacy truth classes |
| Attention budget | 1.0 allocation unit including reservoir | Convenient conservation invariant, not a probability interpretation |
| Initial kernel bandwidth | 3 routing-cost units | Avoids zero support on ordinary one-hop arcs |
| Bandwidth bounds | 2 to 8 routing-cost units | Bounded local adaptation |
| Effective-neighbor target | 32 | Initial sparse/dense support target |
| Bandwidth learning rate | 0.1 with 20% hysteresis | Reduces support oscillation |
| Density denominator epsilon | 1e-8 | Numerical guard only; never inserted into a gate |
| Utility bias beta / exponent clip | 1 / 4 | Bounded relative rate bias |
| Transport step factor | 0.9 / maximum exit rate | Nonnegative conservative update |
| Maximum direct effective rate | 10 per algorithmic time unit | Finite numerical cap before step selection |
| Transport microsteps per cycle | 8 | Bounded field work before candidate evaluation |
| Active field anchors / arcs | 4,096 / 65,536 | Initial local working-set caps |
| Ready candidate queue | 256 | Bounded scheduling state |
| Inference operations per session | 128 | Explicit search horizon |
| Inspection/exploration allocation | 10% of compute budget, with fair queue service | Reduces self-reinforcing attention lock-in without bypassing gates |
| Retention learning rate | 0.01 on a normalized scale | Slower evolution than activation |
| Transport numerical tolerance | 1e-10 × max(1, budget) | Detects conservation errors; not an acceptance loophole |

Backend-specific compute units and timeout policies belong in the deployment manifest. A checker timeout returns UNKNOWN. It must not relax constraints, drop a required premise, reinterpret the policy or mark a certificate complete.

If a neighborhood exceeds its scheduling cap, retain a bounded approximation and flag it. If a certificate's required scope exceeds its supported capacity, do not issue that certificate. These are different kinds of resource limitation.

Novelty and exploration cannot open an invalid transition. Their legitimate effect is to fund another permitted inspection, gather missing evidence, or explore another assumption branch.

## 13. Complexity, persistence and security

A direct sparse transport microstep is O(N+E) for active anchors and routing arcs, excluding neighborhood estimation and certification. Adaptive-neighborhood construction, rule matching, premise joins and satisfiability checks can dominate; do not advertise the whole reasoner as linear-time because its numerical transport kernel is linear-time.

Cache neighborhoods by context, routing-gate revision and support settings. Cache rule matches by pattern and relevant structural revisions. Cache certificates by exact subjects, premise revisions, policies, rule formulas and constraint scope. Do not reuse a cached certificate across an unchecked context or knowledge change.

Use dependency indexes for source corrections, derivation descendants, rule-version changes, constraint changes, context inheritance and pending premise joins. Protect live dependency closures against forgetting. Eviction is a memory-management decision, not belief retraction unless explicitly recorded as such.

Persist evidence, accepted belief revisions, derivations, constraints, certificates and context definitions durably. Transient fields can be periodically checkpointed; losing a field checkpoint loses prioritization progress, not proof. A restarted process reconstructs usable beliefs from valid records rather than trusting a saved Boolean `accepted` flag.

Untrusted input cannot modify checker code, constraint ownership, rule preconditions or certificate records. Treat imported rule proposals as data pending validation. Attribute all state writes to a responsible subsystem and keep an audit log. The first implementation's trust boundary is the service and its checker registry; stronger sandboxing or cryptographic attestation can be added independently.

A future distributed backend may merge replicated structural/evidence records. Such convergence does not itself establish logical consistency or permit independent replicas to merge `PASS` statuses. Accepted-state authorization would need an explicit compatible concurrency protocol. This is intentionally outside the initial single-host scope.

## 14. Acceptance tests and evaluation plan

### 14.1 Required invariant tests

| Test | Required result |
|---|---|
| Closed-gate utility stress | Set utility and base conductance arbitrarily high on a closed arc; effective rate remains exactly zero |
| Unknown/stale permit | Neither authorizes inference or commit |
| Nonnegative transport | Every published activation is nonnegative within the specified numeric contract |
| Budget conservation | Activation plus reservoir is conserved except explicitly logged budget changes |
| No numeric gate leakage | NaN, infinity or an overflow in a closed arc cannot influence rates or gate status |
| Evidence idempotence | Replaying identical evidence or a provenance-equivalent derivation does not increase confidence |
| Common-origin evidence | Different IDs with a shared dependence source are not automatically treated as independent |
| Goal isolation | Changing the goal changes utility/activation, not the underlying belief record |
| Context isolation | Hypotheses in incompatible assumption environments cannot be combined |
| Missing premise | A partially activated rule never produces an accepted conclusion |
| Joint contradiction | A, B and not(A and B) fail as a joint hard premise set despite pairwise satisfiability |
| Inactive contradiction | A low-STI mandatory constraint still blocks an incompatible proposal |
| Numeric feasibility | The 0.65 intersection example fails; the 0.55 example passes the declared local feasibility check |
| Certificate scope | A certificate for local feasibility cannot be presented as proof of empirical truth or global consistency |
| Revoked support | Affected descendants become stale before exposure as current certified beliefs |
| Concurrent conflict | Two individually evaluated conflicting writes cannot both commit from one old revision |
| Forged metadata | User-inserted gate/certificate-looking atoms do not authorize operations |
| Index completeness | New contrary assertions invalidate absence-dependent checks |
| Recovery | Restarted accepted state is reconstructed from valid, current certificate/dependency records |

### 14.2 Functional evaluations

Compare fixed-budget runs on controlled tasks against ablations: PLN with a standard queue; ECAN-only prioritization; transport without utility; fixed-bandwidth versus adaptive support; full design without density correction; and the complete hard-gated architecture.

Measure task accuracy and probabilistic calibration, useful conclusions per work unit, time/work to first valid answer, rate of uncertified proposals, percentage of UNKNOWN checks, evidence double-counting incidents, invalidation latency, contradiction detection coverage, attention concentration and exploration coverage, memory consumption, and restart reproducibility.

A hard-gated system can make fewer accepted mistakes simply by answering nothing. Report coverage and abstention together with correctness. Likewise, a conservative proof checker can be sound for its supported fragment but incomplete for the task; report that boundary explicitly.

Do not claim improved reasoning, convergence, calibration, semantic quality or scalability until those comparisons have been run. The mathematical conservation property of the transport update is narrower than an empirical claim about the architecture's cognitive performance.

### 14.3 Implementation sequence

**Milestone 1 — substrate and provenance.** Implement context-scoped statement anchors, evidence lineage, immutable belief revisions, schema registry and protected write ownership. Verify goal/context separation and duplicate-evidence handling.

**Milestone 2 — admission first.** Implement instantiated transition records, complete checks for a limited logic fragment, pre/post certificates, coarse serializable commits, invalidation and explanation. Demonstrate that joint contradictions and concurrent conflicts are blocked before adding sophisticated transport.

**Milestone 3 — PLN adapter.** Connect a pinned rule engine through pure inference interfaces. Preserve its documented truth semantics and identify every fallback, approximation and precondition. Use the reference rule tests plus adapter-specific provenance tests.

**Milestone 4 — bounded attention and transport.** Add scoped STI, the reservoir, permitted routing arcs, conservative updates and field snapshots. Test mass/nonnegativity invariants and show that diffusion cannot manufacture evidence.

**Milestone 5 — adaptive semantic fields.** Add adaptive kernel support, goal utility, density correction, bounded learning, exploration and retention. Evaluate ablations at equal work budgets.

**Milestone 6 — optimization.** Add fine-grained invalidation, optimized premise joins and packed working buffers only after the reference admission semantics are stable. Distribution or alternate storage backends come after these invariants are retained across an explicit adapter.

## 15. Resulting architecture

The design is not “PLN plus a few additional metadata columns.” It is a shared representational substrate with separate epistemic, resource, transport and admission mechanisms:

```text
                                  GOAL + CONTEXT
                                        |
                         ECAN budget / utility model
                                        |
ATOMSPACE STRUCTURE -> RECALL -> PERMITTED ROUTING -> ADAPTIVE TRANSPORT
       |                                                        |
       |                                              premise / rule frontier
       |                                                        |
 EVIDENCE + RULES -----------------------------> JOINT PRECERTIFICATION
       |                                                        |
       |                                                PURE PLN INFERENCE
       |                                                        |
 CONSTRAINTS + PROVENANCE ----------------------> RESULT CERTIFICATION
                                                                |
                                                REVISION-CHECKED COMMIT
                                                                |
                                         accepted belief + derivation + certificate
                                                                |
                                         feedback, invalidation and next recall
```

This preserves the thesis-level distinction: **stored structure describes what is represented; the current certified operational topology describes what may be done; attention and utility determine which permitted work receives resources.**

## References and provenance

The architectural choices, schemas, exact transport algorithm, defaults and evaluation plan above are proposals. These primary sources ground the statements about the existing projects and the methodological inspiration. Retrieved 30 September 2026; implementation must pin exact revisions rather than following moving branches.

**[R1] OpenCog AtomSpace repository — Atoms/Values and current compatibility guidance.**  
`https://github.com/opencog/atomspace`

**[R2] OpenCog AtomSpace, values.scm — per-atom Value storage, Value types, explicit indexing.**  
`https://github.com/opencog/atomspace/blob/master/examples/atomspace/values.scm`

**[R3] Legacy OpenCog PLN repository — maintenance notice and migration direction.**  
`https://github.com/opencog/pln`

**[R4] TrueAGI PLN repository — MeTTa-native reasoner, strength/confidence and evidence tracking.**  
`https://github.com/trueagi-io/PLN`

**[R5] OpenCog AttentionValue implementation — STI/LTI/VLTI and whole-object replacement.**  
`https://github.com/opencog/attention/blob/master/opencog/attentionbank/avalue/AttentionValue.h`

**[R6] TrueAGI lib_pln.metta — concrete confidence/weight conversions and rule preconditions.**  
`https://github.com/trueagi-io/PLN/blob/main/lib_pln.metta`

**[R7] Daniel J. Price, Smoothed Particle Hydrodynamics and Magnetohydrodynamics — methodological background, not validation of the proposed semantic transport.**  
`https://arxiv.org/abs/1012.1885`
