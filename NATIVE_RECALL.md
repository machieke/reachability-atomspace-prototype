# Bounded native task recall

The experimental Goal-native path supplies discovery records through actual pinned
AtomSpace queries. It preserves the existing goal-directed FIFO policy and full
service-side membership, certification, persistence and dispatch checks. SQLite
remains authoritative. Formula execution is independently selected as the finite
checker or pinned native PLN; finite formulas do not make native recall optional.

Build the existing locked adapter per ADAPTERS.md, then build the separate helper:

```sh
uv run --no-project python scripts/build_native_recall.py
uv run --no-project python -m native_recall_lab.compare --output /tmp/native-recall-fresh
uv run --no-project python -m native_recall_lab.compare --verify /tmp/native-recall-fresh
```

Use a fresh output path. The existing adapter helper/receipt, lockfile and older
experiments remain unchanged. `recall-build.json` binds the new helper, build script,
compiler command, binary hash and existing pinned library/build receipt. Runtime
verification checks these inputs. This detects workspace drift, not authenticity
against a malicious owner or a hermetically reproducible toolchain.

`Session.read()` adds the existing public authority identity to the complete coherent
snapshot. `Projection` loads every declared rule, current/historical numerical
support, report, probe and model before roots/closure are considered. Registered
contract content is structural; complete public operational state/history is retained
in exact bounded snapshot chunks. Typed query relations use role-tagged ordered
ListLinks; literals preserve polarity, predicate and ordered arguments. Producer
links contain all five ordered premises. Scoped record Values preserve exact source
metadata and strength/confidence; there is no global proposition truth value.
Integer/timestamp metadata stays exact, including integers beyond binary64 range.

The helper seals only after all commands and full graph/Value readback agree. It
uses `Atom::getIncomingSetSizeByType`, `getIncomingSetByType`, ordered outgoing sets
and keyed Values from the pinned C++ API. Incoming size is checked before copying
its bounded set. No Atomese/MeTTa evaluator or parallel answer index is involved.
Python performs the existing bounded dependency traversal and tuple joins using
returned exact records; roots, operational readiness and selection remain Python.
An ID-to-source table decodes native answers; it does not determine membership.

Views are immutable and bind authority, context, whole snapshot, schema, build,
complete record IDs/counts and load/readback hashes. Every changed binding requires
a cold rebuild. Same-epoch repeated queries may reuse the helper; responses still
come from native queries. Query receipts record typed requests, exact result IDs,
completeness/reasons and measured native visits/results. They are not certificates.
Native handles are transport-local; durable provenance uses application IDs.

Limits: the existing finite discovery caps (16 rules, 32 current estimates, 128
reports, 16 probes/models), 512 projected source records, 1,024 query relations,
100,000 load commands, 8 MiB load, 2 MiB complete public JSON, 64 KiB strings,
4,096 native visits/query, 512 results/query, 4,096 queries/view, and 30 seconds per
request. A malformed/partial/stale view, protocol corruption, timeout or helper loss
fails the native path. Explicit query/closure capacity exhaustion can use only the
logged frozen Python full-frontier fallback. No inferred answers are supplied by a
Python substitute after native failures. Helper loss requires explicit view discard/
rebuild; it cannot reset task budgets, infer, create evidence or repeat dispatch.

Costs include whole export/serialization, cold projection, build checking, startup,
load/readback validation and replacement, query counts/visits/results, closure/tuples/
ranking/fallback, full execution enumeration, formulas/certification/persistence,
dispatch/monitoring and episode elapsed time. Nested timings are not additive. Query
reuse tests do not establish a realistic warm workload. Native RSS and physical
sensor latency are unmeasured. Local joint certificates remain three-proposition
checks, not a global consistency guarantee for arbitrary overlapping estimates.

The fixed twelve cases and two budgets are reused conformance/development evidence.
No native persistence, incremental synchronization, scheduler tuning, pressure,
transport, generalized recovery, large-scale or speed promotion is claimed.
