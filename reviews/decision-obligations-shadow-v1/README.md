# Explicit decision obligations — detached shadow review

The live all-current policy remains unchanged. This experiment compares its
numerical predicate (A) with predeclared obligation-qualified support (B), using
complete authoritative captures. B is a policy proposal; neither shadow output
can authorize execution.

Measured implementation and auditor: **5161e19b73f89676edf0b9f772200c12eee02ef1**.
Protocol committed at `ce4ae40`; exact role mappings at `f67a4a0`, before evaluating B.
Publication `3d84c66`, measured source `53d7b0b`, the previous review and its reporting
correction remain preserved. All 689 prior tracked files outside the plan and
manifest are byte-identical. No controller, pressure, transport, native arithmetic,
evidence admission, ledger, decision registration, certificate or recovery code changed.

The cohort has eleven parent structures: ten fresh finite cases and one reused
historical native ledger. Three of those structures are reconstructed with actual
native inference and AtomSpace projection. It yields 26 authoritative captures,
nine labeled diagnostic perturbations, and 54 A/B pairs. These are semantic examples
with reused states and roles, not independent population samples.

| Complete-input policy comparison | Pairs |
|---|---:|
| Same numerical judgment | 31 |
| A UNKNOWN, B PASS | 9 |
| A PASS, B UNKNOWN | 5 |

These 45 complete-input comparisons contain disagreements in both directions.
Nine additional scope/completeness/bound diagnostics close as declared. No outcome
is counted as a false acceptance or false rejection, and greater permissiveness is
not evidence of greater safety or decision quality.

The key paired result uses exactly the same beliefs: direct support `(0.7, 0.8)`
and a certified weak deduction `(0.6799999999999999, 0.0014000000000000002)`.
A is UNKNOWN. B is PASS when these are alternatives for one obligation, and UNKNOWN
when the method is separately mandatory or every assessment is required. The
published historical anchor exhibits the same disagreement under **counterfactual**
role declarations; no claim is made about its original intended task meaning.

Missing mandatory source/model support remains UNKNOWN. Copied lineage cannot
satisfy source-b/root:b and remains unclassified even when all numeric values pass
A. Revision parents and the new child remain current: an adequate child does not
make A ignore its inadequate parent. Only inadequate support stays UNKNOWN under
both policies. Low-confidence contrary estimates remain FAIL or UNKNOWN according
to polarity. Sole-witness revocation is STALE; replacement can restore a new
numerical PASS, while old authority stays stale.

In the new adverse case, all reports arrive before the initial capture. A real
certified deduction produces `(0.1, 0.0002000000000000001)`, below the unchanged
strength floor 0.65. Both policies change PASS to FAIL. Exact evidence lists and
goal observations are unchanged across that inference. Every new cohort case has
zero executor effects and outstanding observed goal loss 10; no hypothetical
shadow execution or successful goal is inferred.

**Decision:** A fits tasks requiring every current assessment to be satisfactory.
B fits tasks with explicitly interchangeable evidence witnesses and separately
specified mandatory obligations. This experiment supports neither as a universal
production policy. Task-role ownership, trusted applicability/completeness,
unknown-source treatment, independence assumptions, contradiction handling and
empirical calibration remain unresolved. See [BOUNDARY.md](BOUNDARY.md).

The full [decision table](DECISION_TABLE.md) includes every snapshot/manifest pair
and blocking checks. The [record catalog](RECORDS.md) shows every relevant belief,
its exact values/lineage and per-obligation witnesses. Each pair's JSON inside the archive contains the exact
criterion and role manifest, all supporting/opposing/retired records, applicability,
all qualifying witness IDs, dispositions, scope status and complete basis hashes.
A's numerical result matches the actual frozen inspector; the additional scoped
summary includes experiment capture and hard-check validation, not an issued live
permission. [VALIDATION.md](VALIDATION.md) lists executed/omitted coverage and
failures; [COSTS.md](COSTS.md) gives measured overhead.

Reproduce from the repository with the existing pinned native build (setup is
documented in [NATIVE_RECALL.md](../../NATIVE_RECALL.md)):

```sh
uv run --no-project python -m obligations_lab.compare run --output artifacts/obligations-local
uv run --no-project python -m obligations_lab.compare audit artifacts/obligations-local
```

The output directory must be fresh. Run sources/configuration, seed 0, explicit
bounds, snapshots, all exact native inputs/outputs, authority journals, costs and
readable comparison are recorded. Current source must match committed inputs.
[SHADOW_OBLIGATIONS.md](../../SHADOW_OBLIGATIONS.md) describes the finite contract.

Verify and inspect the published bundle:

```sh
uv run --no-project python reviews/decision-obligations-shadow-v1/verify_review.py
mkdir -p /tmp/obligations-review
tar -xJf reviews/decision-obligations-shadow-v1/review.tar.xz -C /tmp/obligations-review
uv run --no-project python -m obligations_lab.compare audit /tmp/obligations-review/decision-obligations-shadow-review-v1/comparison
```

Use a fresh extraction directory. The checksum verifier checks safe inventory and
content integrity; semantic audit checks source hashes, both policies, independent
references, complete record/witness sets, final SQLite authority and recorded
native arithmetic. Replay itself makes no new native-execution claim. The archive
contains measured sources and exact reproduction/validation commands, plus all
preserved development failures. `PUBLICATION.json` records the publication commit
separately to avoid a self-referential archive hash.

This closes the bounded semantic experiment. No production policy promotion,
threshold change, evidence suppression, confidence aggregation, parent retirement,
scheduler tuning, generalized recovery or adaptive transport is included.
