# Certified probabilistic estimate ledger

The service now accepts separately typed probabilistic estimates through issued
pre/post certificates and checked durable commits. Native PLN inference produces
proposals; the commit authority verifies their exact result, provenance and
declared probability model. The Boolean ledger retains its existing interpretation.

After the [native build](ADAPTERS.md), run:

```bash
uv run --no-project python -m reachability.probability_demo
```

The demo admits five source estimates, executes native deduction, certifies and
commits the result, projects it into real AtomSpace Atoms/Values and reopens SQLite.
It produces approximately `(0.68, 0.3584)`, retains an eight-world joint witness and
reconstructs the same view/projection. Source revocation makes the derived estimate
STALE while retaining history. The ordinary hard query remains UNKNOWN throughout.

## Interpretation and policy

`ProbabilityPolicy` declares `scoped-estimate-alternatives/v1`, trusted sources,
`trueagi-pln-stv-finite-k1/v1`, the upstream formula revision and the
`pln-binary64-joint3/v1` checker. Policies are immutable versions with an
expected-revision comparison on replacement. Replacing one retires estimates
admitted under it. Old version IDs cannot be reused to revive those estimates.

These are source estimates and derived estimates under explicit assumptions.
They are not hard assertions. Strength one with finite empirical confidence cannot
satisfy an existing FACT requirement, lifecycle gate, resource gate or goal sample.
Confidence zero may describe an unknown source estimate; zero total evidence
weight cannot authorize revision.

Different estimates for a literal remain separate alternatives. The view neither
selects a preferred estimate nor adds their weights. A revised estimate coexists
with its parents; lineage prevents feeding those parents back as fresh independent
evidence. Numerical alternatives are not all asserted jointly or automatically
embedded into Boolean constraints. The enclosing hard environment must itself
pass its current consistency check. Changing its policy requires numeric readmission.

## Public flow

1. Open the ordinary context and call `configure_probability_policy`.
2. `record_evidence` retains the scoped source report, roots and validity interval.
   `record_probability_report` adds an immutable finite truth estimate. Recording
   either object does not accept it. One evidence ID cannot change interpretation.
3. `configure_probability_rule` registers a grounded `DeductionRule(P,Q,R)` with
   an immutable rule ID/revision. Revision instead requires a registered
   `ProbabilityIndependence`: a trusted assumption with justification and two
   exact numerical belief revision IDs.
4. `propose_probability` registers an observation, deduction or revision transition.
   Deduction binds five ordered numerical premises; hard belief IDs cannot stand
   in for them. Revision binds two exact estimates and the registered model.
5. `precertify_probability` checks current scope, evidence, policy, rule, model,
   lineage, formula domains and whole declared joint state against the expected
   context revision. `infer_probability` requires this issued PASS permit. It
   captures immutable inputs under the lock, then runs native inference outside
   the lock. Direct report adoption needs no formula subprocess.
6. `postcertify_probability` rechecks the snapshot and reconstructs the complete
   proposal with the pinned deterministic checker. Values, formula, interpretation,
   ancestry, roots, context and revision must match exactly, with no tolerance.
7. `commit_probability` rechecks both issued permits, their common transition,
   the exact pre/post/proposal binding and current inputs under the authority lock.
   It publishes a `ProbabilityBeliefRevision` after the journal commit succeeds.
8. `query_probability` separates current estimates from historical revisions.
   `export_probability` captures a consistent diagnostic view; `project_probability`
   verifies its native AtomSpace projection.

Numerical operations share the service's knowledge revision. Evidence, clock,
rule, policy, model and competing belief changes stale pending permits. Certificates
cannot be constructed or amended by callers. Native inference may finish after
revocation, but its old snapshot cannot pass postcertification or commit.

Repeated command keys return the original historical response, not a current
authorization. Query for current validity. Repeated derivation under fresh permits
returns existing current support without adding weight or another belief. Commit
checks a default limit of 256 historical numeric revisions per context, configurable
up to 512. Reaching it returns UNKNOWN without partial publication. Compaction and
schema migration remain pending.

## Complete three-proposition model

The deduction supplies `P`, `Q`, `R`, `P(Q|P)` and `P(R|Q)`. Exact binary-rational
input checks reject infeasible conditional probabilities. The checker also reproduces
upstream's rounded preconditions; floating-boundary disagreement is UNKNOWN.
Nonfinite intermediate arithmetic and confidence rounded to one are rejected.

The proposed `P(R|P)` must fit all three marginals and pair intersections in one
joint distribution. Taking `t = P(P∧Q∧R)`, all eight Boolean-world masses are affine
in `t`. Their nonnegativity gives a complete lower and upper bound. The checker
requires a nonempty interval, chooses its lower endpoint and records the eight
exact rational masses in pre/post certificates. World order is
`111,110,101,011,100,010,001,000`. The masses reproduce all supplied constraints.

This catches an upstream approximation boundary. With `P=Q=0.99995` and
`P(Q|P)=1`, P and Q coincide. Given `P(R|Q)=0.5` and `R=0.499975`, the near-one
branch proposes `P(R|P)=0.499975`. Every pair is feasible, but no joint model can
give coincident P and Q different conditionals. The service rejects the proposal
without silently replacing the formula's output.

This guarantee covers the selected three-proposition snapshot, not a network of
arbitrary overlapping models. Larger joint scopes and automatic aggregation are
unsupported. The formula remains heuristic; feasibility does not prove calibration
or empirical independence.

## Retirement and recovery

Evidence revocation/expiry, rule/policy replacement and model revocation retire
every exact dependent numerical revision. Current queries recompute this through
the acyclic commit graph and leaf evidence. Independent alternatives remain usable;
they are not silently substituted into old derivations. Histories survive.
Independence registration is a trusted assumption, not a statistical test.
Overlapping evidence IDs or roots prevent weight summation even under a registered
declaration. A revoked model cannot be revived by registering it again.

All new mutations use the existing SQLite journal, exclusive authority lock,
integrity chain, idempotency map and rollback boundary. Failed writes publish no
numeric change and require reopening. An ambiguous commit is reconciled under
its original key. Recovery re-executes guards, deterministic arithmetic and exact
joint checks without trusting saved PASS flags or launching native runtimes.
Replay rejects a saved success generated by a broken numerical checker.

`probability-ledger/v1` and `probability-certificate/v1` are distinct record schemas.
The codec adds a canonical `$float64` hexadecimal tag, preserving finite doubles,
subnormals and signed zero exactly. Untagged fractional JSON numbers, nonfinite
numbers and noncanonical encodings are rejected. Existing finite record/command
encodings remain unchanged; committed older journal fixtures still replay.
An incompatible future formula/checker needs explicit version handling.

The deterministic arithmetic follows the pinned MeTTa expression grouping in
binary64. Native conformance tests require exact agreement; different result bits
fail postcertification. Recovery needs the finite Python checker, not a native
installation. Native inference requires the pins in ADAPTERS.md.

## Verification and next work

The same 31 service contracts run in volatile mode, durable mode with cold replay,
and durable mode with native PLN plus AtomSpace projection before/after restart.
They cover bindings, authority, forged values/permits, stale snapshots, concurrent
commits, retirement, alternatives, cycles, dependence, whole-joint rejection and
separation from Boolean requirements. Recovery tests include failed/ambiguous
writes, partial certificate allocation, corruption, broken-checker success and
real subprocess crashes on both sides of commit. An independent enumeration of
four-observation Boolean worlds checks 15,625 joint constraint combinations.
Generated cases compare native and replay arithmetic bit for bit.

This completes the scoped numerical certificate/commit/recovery increment.
AtomSpace remains a disposable projection. Numeric-to-action decision contracts,
calibrated loss models, the complete deployment episode using numerical estimates,
general joint solving, PLN search and native persistent storage remain pending.
Next define an explicit probabilistic decision contract for the deployment slice,
without promoting estimates to hard facts, and validate it through both adapters.
Phase 3 remains open.
