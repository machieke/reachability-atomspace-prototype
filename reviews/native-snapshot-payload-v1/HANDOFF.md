# Codex handoff: isolate duplicated public-snapshot payload in native recall

## 1. Priority and bounded deliverable

Close the runtime-lifetime milestone at publication `d2446bf`. Preserve measured implementation/auditor `fa6c2674bc5977475f1aad9e6c884405ef7b7414`, review publication `6206b83`, the original scan and strict-native implementations, session-generation implementation, builds, receipts, fixtures, policies, failures, omissions, and prior reviews.

Implement **one payload-only experimental comparison**. Determine whether a native view that retains the complete discovery graph and all exact source records, but does not additionally embed a duplicate serialization of the entire public snapshot, preserves the typed recall contract at lower total cost.

This is not a new scheduler, new runtime lifetime, persistent AtomSpace, incremental-update mechanism, or weaker acceptance policy. Do not implement further optimizations in this increment. A neutral, unfavorable, or correctly blocked result is a valid stopping outcome.

## 2. Why this is the next experiment

The completed comparison reports aggregate episode times of 322.242694 seconds for strict native, 234.062324 seconds for session native, and 145.109862 seconds for scan, with unchanged outcomes. The session arm reduced repeated original-build verification from 528 verifications to 24 preparations, but still created 528 fresh knowledge views.

The existing `Projection` also serializes all `snapshot.records()` into named `snapshot:chunk:*` StringValues on a metadata node. Those bytes include public operational state beyond the supported recall query data. Every source record, its serialized payload, its structured projection, and its recall relations are separately represented as well.

The native helper's current allowlisted query handler uses the recall relations and source records. Its `record` query returns `source:payload/v1`; it is not an arbitrary metadata-export query. However, the helper loads and reads back the full public-snapshot chunks on every changed view.

The published native epoch accounting is 76,003,016 public-export bytes and 241,104,212 load-wire bytes per native arm. The chunk values are hex encoded on the load wire, so their value contents account for approximately 152,006,032 bytes, or 63.05% of that load payload. This is an inference from the encoding and recorded byte counts, not a prediction of elapsed-time savings. Keep the full cost of the experiment, including any new hashing or manifest work.

## 3. Experiment arms

Use three arms:

1. **MH-scan**: the frozen scanner.
2. **MH-native-session-full**: the frozen session-generation implementation, including whole-public-snapshot chunks.
3. **MH-native-session-compact**: the same session runtime and cold-view behavior, with only the duplicate whole-public-snapshot embedding replaced by a compact binding envelope.

Do not rerun the strict-native arm merely to enlarge the matrix. Its completed review remains historical evidence. Do not change the session-generation preparation, sealing, loaded-mapping verification, query-time integrity guards, or covered-artifact threat model.

## 4. Exact representation change allowed

In the new projection, retain:

- The complete public snapshot in the Python-side capture and source-bound review evidence.
- All source catalog entries, exact IDs, current and historical membership, current alternatives, both literal polarities, truth-value fields, provenance and ancestry.
- Every source payload and its existing structured representation. Do not remove the `source:structural` representation in this experiment.
- All registered-content structure already projected by the frozen implementation.
- The identical recall relations, ordered five-premise rules, model input revisions/revocation state, and probe opportunity identities.
- Authority identity, exact snapshot binding, logical time, and the existing knowledge/resource/goal/lifecycle revision metadata.
- The full current capture, A/B assessment, frontier revalidation, numerical certification, and real execution checks.

Omit only the extra opaque full-snapshot chunk values and the metadata keys used exclusively for those writes. Replace them with an explicit, versioned envelope containing the canonical full-snapshot digest and length, its exact binding, and a declaration that the complete snapshot is external rather than fully embedded in native Values.

Do not implement this by deleting every atom whose name matches a prefix. Construct the new metadata deliberately; never remove an atom or Value belonging to an actual source record or registered structure.

Keep the existing canonical serialization and input size checks. The 2 MiB complete-public-export bound still applies even when fewer bytes are sent to native code. Other input, atom-command, record, relation, line, query, result, visit, timeout, and episode budgets remain unchanged. This is not a larger-capacity experiment.

The exact envelope encoding and new projection-schema identifier should be declared before the measured run. Preserve legacy receipt readers and clearly distinguish:

- complete authoritative capture;
- complete supported discovery universe;
- complete readback of the declared native projection;
- whether the entire public snapshot is embedded in that projection.

The compact arm must not claim the fourth property. Raw atom counts, metadata, wire hashes, and readback hashes are expected to differ. All corresponding discovery semantics must remain unchanged.

## 5. Query-semantic obligation

For an admissible captured snapshot S and every supported typed request q, compare the complete result of the old projection and the compact projection:

    query(full_projection(S), q) == query(compact_projection(S), q)

Compare exact record IDs and contents, ordering, ordered-premise details, model details, opportunity counters, completeness status, failure reason, and query-resource accounting. Raw native handle numbers and transport hashes are not semantic identities; decode them through their declared projection before comparing.

Retain all nine current query kinds: producers, current, historical, reports, probes, models, record, all_rules, and all_current. Include empty answers and tight-limit boundary requests, not just the queries selected by successful episodes.

This is equivalence for a declared query protocol, not equivalence under every possible AtomSpace inspection or future query. Any future full-metadata query must explicitly extend the contract instead of assuming the compact projection contains the original blob.

Do not substitute Python-computed answer sets for native answers. Python may construct the complete projection and validate exact identities as it already does; native traversal must still determine response membership.

If any supported query actually depends on the removed data, do not waive that discrepancy. Retain the dependency or report that this specific optimization is blocked.

## 6. Freshness and integrity stay strict

Every changed authoritative snapshot continues to require a new projection, new helper process, complete load/readback of that projection, and an exact new binding. Retain the existing exact-binding-only reuse behavior. There is no cross-view query cache, helper pooling, selective invalidation, or graph-digest reuse.

Validate the compact envelope against the actual canonical snapshot used to construct the view. Its digest is a binding/integrity check, not a certificate that omitted data are irrelevant or that the publisher is authentic. Completeness comes from the declared projection construction and independent query/source comparisons.

The full canonical snapshot remains available to the auditor and to unchanged authority paths. Removing a duplicate transport copy must not remove an observation, opposite estimate, policy input, review obligation, or evidence record from a decision.

Retain exact-input invalidation, intermediate retirement, adverse-evidence handling, query incompleteness, stale response rejection, helper failure, and explicit rebuild. No scan rescue may turn failed native discovery into a completed native work view. Accepted or uncertain external operations retain their existing control priority.

## 7. Tests before measuring

Add focused tests for:

1. **Native query parity.** Compare all supported query forms over bounded snapshots, including current/historical differences, absent IDs, opposing literals, multiple producers, and exact five-premise order.
2. **Record fidelity.** Returned records keep complete payloads, provenance, confidence/strength, and schema identities. Structured source representation and registered content are unchanged.
3. **Binding fidelity.** Change an operational or policy field outside the typed recall payload. The full snapshot digest and binding change even if the recall memberships happen not to. A previous view/request cannot acquire present authority.
4. **Envelope tampering.** Wrong digest, size, snapshot identity, or projection declaration is rejected. A digest from a different full capture must not be accepted.
5. **Fresh numerical round trip.** A selected native deduction commits an intermediate; a freshly loaded compact view returns the exact current intermediate; the next real native deduction uses it.
6. **Retirement and replacement.** Upstream revocation retires dependents; equal-valued replacements need fresh exact inputs and certification.
7. **Boundaries.** Full-input caps still apply despite a smaller wire payload. Zero/tight visits and results retain declared completeness semantics. Native timeout, malformed readback, lost helper, and failed runtime generation remain fail-closed.
8. **No information filtering.** An adverse current estimate outside the chosen derivation remains visible to authoritative checks. Review and dispatch policies are unchanged.

Use both independent source-level expected answers and the frozen native projection as comparators. Keep the audit implementation independent of the compact projection where practical; do not validate it only by rebuilding the same implementation twice.

## 8. Cohort and timing protocol

Reuse the same six parent scenarios, finite/native formula modes, seeds, operation limits, clock model, and world outcomes. Run three arms in two serial counterbalanced sweeps: 72 core executions. Reverse arm order within each parent/mode group in the second sweep. Commit the protocol and implementation before recording comparison results. Label earlier development runs separately.

Use one session generation per applicable episode, including preparation and cleanup costs. No generation sharing across runs. Do not measure arms concurrently.

Require identical-state query and work-view parity before interpreting closed-loop timings. Closed-loop selected operations, exact inputs, admitted observations, formula outcomes, physical and recognized trajectories, budgets, and stop reasons must match after normalizing only genuinely arm-specific transport/projection metadata.

The six parents and repeated formula/timing runs are not independent population samples. Report individual pairs and between-sweep variation. Do not claim significance, broad scalability, or native superiority from the totals.

Do not introduce a new controller cohort or increase limits to make compact projection win. Small metadata perturbations can be targeted fixtures, not extra independent tasks.

## 9. Cost accounting

Retain the current disjoint coarse phases and separately reported nested timers. Charge:

- Complete capture and all canonical serialization, even when not sent to native code.
- Full-snapshot hashing, envelope construction, and validation.
- Structured graph construction, emitted metadata atoms/Values, source payload bytes, complete-public-export bytes, native load-wire bytes, and native readback bytes.
- Runtime verification, sealed generation preparation, integrity guards, helper startup, loading, readback checking, and cleanup.
- Actual query count/visits/results and returned source bytes.
- Existing frontier scans, A/B checks, certification, native formula execution, persistence, monitoring, reconstruction, trace output, and end-to-end driver/wrapper time.

Do not sum overlapping timers. Distinguish native resident payload from wire encoding and archive bytes. Reduced transfer size is not an RSS or peak-memory measurement; retain those omissions unless measured with a clearly specified method that does not expand this milestone.

This experiment may show a smaller native transfer without a meaningful total speedup. Report that directly. Do not suppress full capture cost or remove validation work to turn a payload reduction into a performance claim.

## 10. Publication and stopping condition

Reuse the existing audit, mutation, archive, extracted replay, and provenance tooling. Extend it only to recognize the new projection envelope, validate complete external source binding, and compare old/new typed query semantics.

Distinguish original native PLN calls, recorded arithmetic checks, fresh native query reexecution, and extracted replay. Do not claim that loading a raw archive recreates kernel-sealed runtime integrity checks from the original run.

Run applicable default and actual native suites once at frozen source; publish the exact passed/failed/skipped/omitted inventory and process exits. Preserve failed development attempts and correction history without rewriting them. Fix the inherited consumer-label issue in new informational metadata while leaving historical artifacts unchanged; identify the actual consumer by measured source and file hash.

Stop after one source-bound comparison with:

- A conformant compact projection or a documented blocking semantic dependency.
- Complete query/operation/outcome comparisons, including unfavorable results.
- Full payload and elapsed-cost accounting.
- Applicable test receipts and retained omissions.
- One reproducible review bundle.

No persistent helper, incremental AtomSpace, new identity-reuse scheme, cross-view cache, changed work scheduler, additional inference depth, pressure tuning, adaptive transport, evidence supersession, policy promotion, generalized recovery, or further optimization chain. Do not require native recall to beat scanning before closing the milestone or proceeding with future cognitive research.

## Source notes

This handoff is a proposed increment based on a source/documentation review, not an independently reproduced experiment.

- [Publication and accounting](https://github.com/machieke/reachability-atomspace-prototype/commit/d2446bf)
- [Runtime-lifetime review](https://raw.githubusercontent.com/machieke/reachability-atomspace-prototype/d2446bf/reviews/native-runtime-lifetime-v1/README.md)
- [Measured cost breakdown](https://raw.githubusercontent.com/machieke/reachability-atomspace-prototype/d2446bf/reviews/native-runtime-lifetime-v1/COSTS.md)
- [Validation and omissions](https://raw.githubusercontent.com/machieke/reachability-atomspace-prototype/d2446bf/reviews/native-runtime-lifetime-v1/VALIDATION.md)
- [Current projection schema](https://raw.githubusercontent.com/machieke/reachability-atomspace-prototype/d2446bf/experimental_native_recall/schema.py)
- [Native query implementation](https://raw.githubusercontent.com/machieke/reachability-atomspace-prototype/d2446bf/native/atomspace_recall.cc)
- [Session-generation backend](https://raw.githubusercontent.com/machieke/reachability-atomspace-prototype/d2446bf/experimental_runtime_lifetime/backend.py)
- [Runtime integrity contract](https://raw.githubusercontent.com/machieke/reachability-atomspace-prototype/d2446bf/reviews/native-runtime-lifetime-v1/RUNTIME_CONTRACT.md)
