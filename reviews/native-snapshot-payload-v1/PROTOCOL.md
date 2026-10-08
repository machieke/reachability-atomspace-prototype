# Native snapshot payload preregistration

Preserve closure d2446bf, runtime implementation/auditor fa6c267 and publication
6206b83, all earlier code/reviews/builds/receipts, fixtures, policies and failures.
New code names: experimental_snapshot_payload and snapshot_payload_lab.

Three arms: MH-scan, MH-native-session-full, MH-native-session-compact. Exactly
six original parents, original finite/native formula modes, seeds, clocks, events
and budgets. Two serial sweeps: listed arm order within each mode/parent in sweep
0, reversed in sweep 1. Exactly 72 core executions, six fixed tasks. Strict-native
is historical, not an additional measured arm. One unchanged sealed generation
per native episode; unchanged cold projection/helper/load/readback on changed
binding, exact-binding reuse only, unchanged guards/failure latch/rebuild state.

Compact projection schema: native-atomspace-recall-compact/v1. Query protocol and
native executable remain native-atomspace-recall/v1, with all nine query kinds.
Construct metadata explicitly. Retain the original metadata node, authority,
binding, logical time and knowledge/resource/goal/lifecycle revisions. Replace
only the full snapshot StringValue chunks and their exclusive metadata keys with
one PredicateNode key snapshot:external-envelope/v1 and a canonical JSON
StringValue with exactly these fields:

- schema: native-public-snapshot-envelope/v1
- projection_schema: native-atomspace-recall-compact/v1
- canonical_encoding: reachability.trace_protocol.canonical(snapshot.records())/utf-8
- snapshot_sha256: SHA256 of the canonical complete public export
- snapshot_bytes: its UTF-8 byte length
- snapshot_binding: its exact original Snapshot.binding
- snapshot_representation: external-full-capture

Retain canonical serialization and the 2 MiB full-export cap before graph work;
all other caps stay unchanged. Retain all catalog entries/payloads/structured
source representations, registered structure, polarities, current/history,
relations, ordered premises, models/revocation and opportunities. No prefix-based
atom deletion, source filtering, graph reduction or new capacity claim.

Compact receipts extend legacy view receipts with the projection schema,
envelope, and four separate completeness properties: authoritative capture,
supported discovery universe, native declared-projection readback, and whole
snapshot embedding. Only the last is false. Legacy readers and full receipts
remain unchanged. Independently recompute the canonical snapshot and envelope
and compare its exact native StringValue after full structural readback, before
issuing a queryable view receipt. Hashing and validation are charged.

Full uses the existing frozen session backend; compact inherits its unchanged
generation/query/ownership behavior, with a narrow separately named open-view
method selecting the compact projection and validating its envelope. The common
experiment driver adds payload accounting to both native arms. Readback byte
counts are derived from the exact validated native graph and unchanged wire
grammar (independent of Value output order), and checked against real captured
readback in focused tests. Label resident StringValue content separately from
wire bytes, input-export bytes and archive bytes. Retain disjoint coarse phases,
nested timers, all guards, A/B/frontier, certification, real formulas, persistence,
monitoring, logging, cleanup and command time. RSS/peak/native memory remain
unmeasured; smaller payload is not an RSS or speed prediction.

Before interpreting timing, compare source/reference and actual full/compact
native queries: IDs, record contents, order, typed details, opportunity counters,
completeness, reason and resource counts. Include all nine kinds, empty/absent
answers and tight result/visit/query bounds. Raw handle numbers and response
hashes may differ; decode through each declared projection. Independently compare
all nonmetadata graph structure/Values with the frozen full projection. The
auditor may reconstruct the declared compact encoding to check raw transport,
but membership/detail references and fresh native query comparison use original
sources and the frozen full native backend, not a Python answer substitute.

Test envelope tampering, non-recall policy/operational revisions, retained input
caps, actual native intermediate round trip, exact retirement/replacement,
adverse evidence, native failure/latch/rebuild and no scanner rescue. Freeze
implementation/auditor before one applicable default/native suite pass and the
core run. Label development separately and retain failed attempts. Reuse sealed
mutation/archive/replay tools; add focused envelope/projection witnesses without
changing benchmark scenarios. Preserve independent labels for original native
PLN, recorded arithmetic, fresh native queries and extracted recorded replay.
Correct new consumer metadata with actual source revision and file hash; retain
historical metadata intact. Report every pair and two-sweep variation, neutral
outcomes and unfavorable costs. Stop after one reproducible review, even if
compact loses or a supported semantic dependency blocks it. No optimization
chain, runtime change, storage, pooling, cache, scheduler, depth, transport,
evidence supersession, policy promotion or generalized recovery.
