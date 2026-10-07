# Native multi-hop recall integration

This bounded experiment changes discovery membership for the existing multi-hop
consumer. `experimental_native_multihop` supplies the same `MultiHopView`;
`experimental_multihop/consumer.py` is unchanged. Native answers determine producer,
current-support, historical-record, numeric-probe and report lookup membership.
Python traverses the bounded graph and forms exact five-slot tuples. There is no
scan fallback. SQLite and the original public APIs retain execution authority.

The complete public capture and frozen A/B evaluation remain full-scope. The old
one-step validator still computes a graph: its cost is charged, its operation
nodes/routes are discarded, and native responses reconstruct the work graph.
Native report queries cover every traversed literal even when current support
exists. The original consumer independently checks pending public reports and
matches exact operations against its full public frontier. That boundary cannot
repair an incomplete native graph. Full historical queries over declared literal
scope retain depth accounting for unrelated and retired records; this is not a
working-set memory reduction.

Every public binding change uses the existing cold view replacement. Query
results are cached only inside one projection call. Same-binding subsequent calls
reuse the helper but execute new queries. Fatal native errors latch the observer
incomplete until an explicit caller rebuild; no restart automation is installed.
Accepted/uncertain external control retains its original priority and headroom.
A complete query result is trusted under the pinned helper/readback contract.
Runtime checks do not cryptographically establish that a malicious helper omitted
nothing; offline independent scans check query membership and semantic parity.

Run from a clean checkout with the existing pinned native builds present:

```sh
uv run --no-project python -m native_multihop_lab.compare run --output /tmp/native-multihop-comparison
uv run --no-project python -m native_multihop_lab.compare audit /tmp/native-multihop-comparison --output /tmp/native-multihop-audit
```

Both directories must be fresh. Twenty-four runs cross two retrieval arms with
finite/native formula modes and the six frozen parents. MH-native uses real
native recall even in finite formula mode. The scanner remains the frozen path.
The audit compares graphs/choices at identical snapshots and consumer histories,
reexecutes native queries, checks recorded arithmetic, and reconstructs SQLite.
Fresh PLN invocation occurs in the cohort/native tests, separately counted.

Raw traces bind sources, configuration, observations, inputs, intermediate IDs,
selected operations, authority certificates, external outcomes and costs. Native
query receipts include actual protocol request/response lines and byte counts.
Costs include full capture, evaluation, unused validator work, construction,
build checks, startup, load/readback, query/decoding, traversal/tuples, selection,
frontier revalidation, execution, persistence, observation and episode time.
Nested inclusive timers must not be summed. RSS, peak/native process memory,
serialization copies, isolated fsync and isolated arithmetic time are unmeasured.
Short native answers do not bound total memory. Logical-time parity says nothing
about real-time performance. No scheduler, pressure or cognitive-speed claim.

Depth remains three. No new formulas, producer families, storage architecture,
adaptive transport, generalized recovery or optimization is part of this work.
Protocol and review: `reviews/native-multihop-v1/`.
