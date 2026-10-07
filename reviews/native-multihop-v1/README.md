# Native multi-hop recall review

Measured implementation and auditor: `068770ea5f7970bfaf65aabfdae3fcfe3d983226`. Preregistered protocol `55ec450`.
Baseline closure `c4686bc`, scanner/consumer `b509d2b`, six fixtures, authority,
world, previous reviews and build receipts remain unchanged.

All 24 executions conformed. Six parents are crossed with MH-scan/MH-native and
finite/native PLN. All 12 retrieval-arm pairs match supported decisions and
outcomes. There are 16 observed completions and
8 unresolved outcomes. This is integration
parity over six structures, not 24 independent samples or a scheduler win.

The audit checks 528 matched-snapshot work views and choices,
324 selections, 60 recorded formula calls
(30 originally executed by native PLN), and
1096 actual persisted certificates. It reexecutes
12880 native queries across 264 cold
views and 264 native graph reconstructions.
Fresh native PLN invocation during audit is zero. SQLite/executor reconstruction
and recorded arithmetic checks are separate counters in the machine receipt.

598 fresh regressions passed (473 default,
125 native), with no failures/errors/skips. Thirteen altered-copy
mutation witnesses must be rejected; see VALIDATION.md for actual receipts,
retained development failures and exact omitted coverage.

The native path is not promoted for performance. Read COMPARISON.md and COSTS.md
for favorable/neutral/unfavorable descriptive measurements. Physical and recognized
losses are neutral in every pair. The simulator's logical clock does not charge
wall time; equal logical outcomes do not establish real-time speed. Full captures,
unused one-step validation graph work, independent consumer frontier scans and
cold native projection costs remain paid. RSS/peak/native memory and serialization
copies are unmeasured; no bounded-total-memory claim.

From a checkout of the measured revision with the existing pinned builds:

```sh
uv run --no-project python -m native_multihop_lab.compare run --output /tmp/native-multihop-comparison
uv run --no-project python -m native_multihop_lab.compare audit /tmp/native-multihop-comparison --output /tmp/native-multihop-audit
uv run --no-project python reviews/native-multihop-v1/verify_review.py
```

Comparison and audit destinations must be fresh. `NATIVE_RECALL.md` documents
native build setup; the archive contains exact source/build/configuration and
query receipts, traces, SQLite journals, certificate inventories, suite logs,
coverage, failures and corrections. `ARCHIVE.json` and `SHA256SUMS` bind the one
review archive. The verifier establishes integrity, not publisher authentication.

Native query responses drive record membership. Full source loading and exact
ID decoding are permitted; no scanner answer substitution occurs. Frozen full
A/B and authority checks remain independent. Failed views latch incomplete until
explicit rebuild, while accepted/uncertain operations retain control priority and
headroom. A trusted helper's arbitrary false completeness is detected by the
independent audit, not claimed cryptographically detectable at runtime.

Stopped here. No adaptive transport, working-set policy, more depth, producer
families, native storage redesign, calibration or generalized recovery.
