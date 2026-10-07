# Codex handoff: verified native-runtime lifetime with fresh knowledge views

## Decision and scope

Close publication `c088775` and retain the native-multihop parity result. Measured implementation/auditor: `068770ea5f7970bfaf65aabfdae3fcfe3d983226`; review publication: `f8007ed`; closure: `c088775`.

Implement **one separately named experimental native-retrieval arm** that separates the lifetime of a verified runtime artifact generation from the lifetime of an authoritative knowledge snapshot. Keep the original MH-scan and MH-native paths as frozen comparators.

The experimental question is:

> Can repeated verification of identical runtime artifacts be avoided within a bounded, explicitly pinned session without changing query membership, freshness, selected work, authority, or physical/observed outcomes?

This is an engineering-lifetime experiment, not a new cognitive mechanism, production rollout, storage redesign, or claim that native recall is generally faster.

The measured baseline reports 264 native views, 252 replacements, and no exact-binding view reuse. Its nested timers include 54.432357 seconds of build verification, 77.333023 seconds of view opening, and 1.076823 seconds of native-query work. Total native and scanner episode times are 160.988507 and 71.913394 seconds. These are descriptive serial measurements; nested timers must not be added. They motivate the target but do not predict a speedup.

## 1. Preserve the scientific and authority baseline

Do not modify:

- Six parent tasks, formula inputs, evidence lineage, declared roles, depth-three scope, thresholds, world events, logical clock, or work budgets.
- Multi-hop discovery semantics, complete ordered five-premise applications, finite review of alternative/adverse routes, consumer priorities, FIFO ordering, monitoring headroom, or retry identities.
- Frozen A and B meanings, full authoritative acceptance scope, exact revision binding, certificates, reservations, dispatch, goal accounting, or observations.
- Native query membership algorithms, response completeness rules, source-ID decoding, or query limits.
- Existing source-bound reviews, original native receipts/binaries, failures, omissions, and original implementations.

The new arm may add a narrow runtime-generation adapter and a separately bound launch receipt. Keep old artifacts runnable. If staging requires a changed launch configuration or relinked helper, identify it as a new build/launch generation, preserving the native query source semantics and the original receipts. Do not falsely claim byte-identical launch artifacts.

Do not remove the full A/B evaluations, unused one-step validation, complete-source loading, independent public-frontier checks, or serialization work in the same experiment. Charge them as before.

## 2. Two different lifetime contracts

### Runtime generation

A runtime generation identifies the executable, receipt-checked libraries, source/lock/build identities, query protocol, and relevant launch configuration actually used. It contains **no knowledge, evidence, view IDs, candidate answers, or authority**.

Verify the complete generation cryptographically at session preparation. Reuse that verification only while the actual executed artifacts remain the same explicitly pinned generation under a documented and tested local integrity contract.

Keep the generation bounded to one episode/consumer session initially. No shared daemon, fleet cache, global installation, background updater, or cross-user service is needed.

### Knowledge view

Every changed public snapshot binding must still cause the same fresh native projection, fresh helper process, full load, structural/Value readback, exact receipt binding, and new query namespace as the frozen implementation.

Same-binding reuse may continue under the existing rules. Do not manufacture such reuse by deleting revision/clock fields or loosening the binding.

Runtime reuse **does not** authorize:

- Reusing an old native knowledge graph after evidence changes.
- Replaying cached membership answers across views.
- Letting historical/retired support appear current.
- Keeping an old executable operation or certificate valid.
- Resetting query, episode, or operation budgets.

Keep process startup and cold graph construction unchanged in this increment. Their cost is not the primary target, and modifying them would introduce another factor.

## 3. Do not turn verification into a boolean cache

A path string or `verified=True` is insufficient. Checking only that a filename or reported build ID is unchanged is insufficient. File metadata may support drift detection, but is not cryptographic evidence of unchanged contents.

Before choosing an implementation, inspect how this repository launches the recall executable and resolves its libraries. The current build embeds library search paths. Copying only the executable into a private directory does not establish that subsequent launches use private pinned libraries.

A suitable bounded design can use a session-local read-only/staged artifact generation, provided:

1. The files actually used are verified against their expected digests.
2. The loader resolves the covered dependencies to that same generation, rather than mutable originals through baked-in paths or environment overrides.
3. Preparation/copying/verification and any loader checks are measured, not hidden outside total cost.
4. Edits to the original build tree either leave the isolated generation demonstrably unaffected or invalidate reuse before further native work. A new episode must not silently accept an altered original build under an old receipt.
5. Modification, replacement, missing files, unrecognized generation IDs, or ambiguous lifetime validity in the active generation prevent further use. Do not silently trust the cached verification or downgrade to scan discovery.
6. The local threat model is explicit. Do not claim protection from a malicious privileged owner or universal hermetic execution merely because files have read-only permissions. Preserve at least the existing declared accidental-drift protection for artifacts actually executed; list host/toolchain dependencies outside the existing receipt scope.

Do not add a packaging/security platform to satisfy this. If a reliable bounded artifact lifetime cannot be established on the existing setup, keep strict per-view verification and document the blocker. An optimization may not obtain its result by executing unchecked mutable binaries.

## 4. Minimal interface and accounting

A small immutable descriptor may contain:

```text
RuntimeGeneration:
    generation_id
    original build and lock identities
    covered artifact digests and resolved launch paths
    launch configuration identity
    integrity/lifetime policy version
    preparation receipt and measured costs
    validity / closed / failed state
```

The generation is backend-internal and is not a live authority token. Do not introduce a durable recovery journal for it. The current controlled session owns cleanup; a new process after failure needs explicit preparation under the existing failure discipline.

A view receipt should bind both its runtime generation and its original complete snapshot binding. Record runtime preparations, verification/revalidation counts, bytes hashed/copied, helper launches, graph/view replacements, queries, and errors separately.

Do not relabel existing cold views as warm: they remain cold knowledge loads even when the executable generation was verified earlier.

The observer must retain its existing latch after helper/protocol failure. Explicit reconstruction must preserve consumer attempts, elapsed logical time, remaining work, and unresolved external operations. Existing accepted/uncertain-effect controls retain priority even when discovery is unavailable.

## 5. Comparison design

Preregister these three arms:

- `MH-scan`: frozen scan discovery.
- `MH-native-strict`: frozen verification for each changed view.
- `MH-native-session`: the proposed runtime-generation lifetime; unchanged cold views and query policy.

Use the same six parents and both finite-checker/native-PLN formula modes. This is 36 executions per serial sweep. Run two predeclared sweeps with arm order reversed/counterbalanced within matched parent/mode groups: 72 core executions. These remain six parent tasks, not 72 independent samples.

Do not share an already prepared generation between arms, episodes, or repeats without charging that preparation to every arm that benefits. The first comparison is one generation per episode.

At identical public snapshots/history, compare native membership, exact ordered premises, alternative/adverse evidence, work graphs, selected operations, and stop reasons. Then compare entire executions. Normalize authority-specific IDs and the declared transport/runtime receipt metadata; never normalize evidence identities, operation order, changed supports, or unfavorable outcomes away.

Expect the same semantic trace, native query sequence/count, graph/view replacement pattern, numerical operations, certificates, world trajectory, and observed outcome under supported ordinary operation. A difference caused by this lifetime change is a defect, not an improvement.

Different timing or runtime-preparation receipts are legitimate. On targeted artifact-failure cases, explicit failure is correct and need not mimic the no-failure trajectory.

Retain strict-native and scanner results even if session preparation makes the new arm slower. No fixture tuning, added scale, or benchmark-search for a win.

## 6. Required focused tests

### Runtime integrity and use

- A correct generation verifies once per episode and launches all its knowledge-view helpers from the same recorded covered artifact generation.
- Wrong/missing receipts, changed lock, altered executable, and altered covered library reject before use.
- Original-tree replacement after preparation cannot switch an active episode silently to new bytes. A fresh generation rechecks the new originals.
- Covered artifact drift or ambiguous validity in the active generation closes it. Do not assume a metadata-only cache proves immutability.
- Library-resolution test detects a staged binary still loading a mutable original library. Record the actual scope of that check.
- Closed generation cannot issue a view; a generation from another root/build/protocol cannot be confused with this one.
- Setup, failed preparation, integrity checks, teardown, and retries remain charged.

### Changing knowledge and authority

Retain the existing intermediate-round-trip, source replacement, new-producer, opposite-report, depth/cycle, incomplete-answer, malformed-readback, lost-helper, and no-scanner-fallback tests.

Specifically demonstrate:

1. Native deduction commits an intermediate.
2. The next snapshot builds a fresh native view using the same runtime generation.
3. The current-support query returns the exact intermediate revision.
4. A subsequent selected deduction consumes it.
5. Revocation invalidates the exact descendant and old selected operation despite continued runtime reuse.

Equal-valued support replacements must still require fresh exact bindings. Runtime generation equality never implies evidence equality.

### Independence of the audit

Keep query reexecution, recorded arithmetic checking, fresh native PLN calls, structural replay, certificate counts, and integrity checks separately labeled.

The original audit used fresh native query reexecution; extracted replay used recorded queries. Preserve that distinction. Reuse the existing native scanner/reference only inside the evaluator, not as a runtime rescue.

## 7. Report cost where it occurs

Provide a nonoverlapping coarse breakdown of total episode cost wherever possible, retaining fine-grained nested timers with clear containment. Include:

- Runtime preparation, cryptographic verification, bytes read/hashed, staging and launch-generation checks.
- Every public capture/export and frozen A/B evaluation.
- Projection construction, serialization, helper startup, load/readback, and validation per view.
- Actual native queries, decoding, traversal, tuple construction, remaining frontier scans, and selection.
- Native PLN, numerical checks, certification, commit/persistence, dispatch, measurement and monitoring.
- Logging, cleanup, and total end-to-end elapsed time.

Use small controlled fixed-snapshot/query repetitions only to corroborate attribution; they are not additional independent tasks or substitutes for the changed-evidence episodes. Do not obtain warm performance by reusing stale views.

Report paired times and variability for each sweep. Two sweeps support a local reproducibility check, not a broad significance claim. Logical time remains independent of wall time; matching goal losses does not establish equal real-time performance.

Memory/copy counts do not establish RSS or peak memory. Measure them explicitly or retain the omission. Do not sum nested timers or claim that removing all of one recorded timing category predicts the exact new end-to-end runtime.

## 8. Deliverables and stopping condition

Deliver one documented reproduction command, exact executed/omitted tests, source/build/launch identities, original and new receipts, all three arm results, native query traces, failures, costs, and a source-bound review using the existing archive/audit tools.

The milestone is complete when the runtime-generation contract is implemented and tested, evidence-view freshness and semantic parity are preserved, and a reproducible measurement reports the full benefit or overhead. The new arm does not have to beat scan retrieval. Failure to establish reliable artifact lifetime must remain a blocker, not motivate weaker checking.

Stop after this increment. No automatic move into selective invalidation, persistent/incremental AtomSpace storage, runtime pooling, query caching, new planner, deeper inference, pressure/transport, policy B promotion, source supersession, or generalized recovery.

The intended lesson is the separation of **code identity** from **knowledge freshness**. It is not a shortcut around either one.

## Evidence inspected for this handoff

All paths below are under the frozen publication `c088775` of `machieke/reachability-atomspace-prototype`:

- `reviews/native-multihop-v1/README.md`, `COSTS.md`, `VALIDATION.md`, `PROTOCOL.md`, `COMPARISON.md`, `PUBLICATION.json`.
- `experimental_native_recall/backend.py`: changed-view verification, cold process/load, exact receipt and query checks.
- `reachability/adapter_runtime.py`: complete receipt-covered artifact hashing.
- `scripts/build_native_recall.py` and `scripts/build_adapters.py`: native build identity and embedded library search paths.
- `experimental_native_multihop/access.py`, `observe.py`, and `backend.py`: coherent capture, native membership, failure latch, raw query evidence.
- `integration_tests/test_native_multihop.py`: actual intermediate round trips, helper failure, currentness and independent omission detection.

Repository source was inspected; this handoff does not claim independent execution of the published tests or archive.
