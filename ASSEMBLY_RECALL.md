# Bounded shared protected assembly

This separate experiment preserves `experimental_attention.controller.Agenda`.
`experimental_assembly.controller.Agenda` supports `frozen` and `assembly` contracts
with the same WS-queue, WS-local and WS-flow orderers. Authority, native recall,
exact supports, inference, fields, workspace and lifecycle remain inherited.

The protected service reserves 12 native queries (13 for a nonresident producer):
six current-premise/conclusion queries, optional exact producer lookup, six exact
selected-record preparation reads. Controls run first; oldest affordable join gets
one slot per tranche; optional inspection cannot spend its preparation credit.
No probability, outcome label or activation enters reservation affordability.
Native response/joint/tuple/byte limits can still end an attempted assembly.

See [the preregistered protocol](reviews/completion-aware-recall-v1/PROTOCOL.md).
After building the pinned native dependencies as documented in NATIVE_RECALL.md,
run from the measured checkout with a fresh output path:

```sh
uv run --no-project python -m assembly_lab.compare --output /tmp/completion-recall-review-fresh --audit-after
```

The command runs the 192 declared cells through actual native recall, exercises
both finite and native formulas, and writes source copies, configuration, decisions,
query/tuple/retention/service events, SQLite authorities, receipts, costs, a readable
comparison and a hash inventory. The audit replays the frozen and experimental
coordinators, compares native answers to an independent source reference, checks
the allocation and service ledgers, and verifies formula/certificate persistence.

`at_ns` records decision-relative event time; `at_episode_query` counts intervening
native work across tranches. Guard reads remain full public snapshot checks.
Coordinator, backend and session cost categories are inclusive/nested; do not add
them. Kernel timing excludes measured guard callbacks and field-event logging but
includes bookkeeping. Trace-byte occupancy varies with timestamp encoding and is
checked against its cap rather than required identical during semantic replay.

This is minimum opportunity service under declared bounds. It does not establish
semantic completeness, universal starvation freedom, field value or scaling.
