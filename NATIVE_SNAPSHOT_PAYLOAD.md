# Bounded native snapshot payload experiment

The compact projection omits only the duplicate whole public capture Values.
It retains complete exact source payloads, structural representations, registered
content, recall relations, ordered premises, alternatives and revisions. Its
versioned envelope binds the canonical full capture, which remains subject to
the original 2 MiB input bound. All authority and runtime generation paths stay
unchanged. This is equivalence for the existing nine-query protocol, not arbitrary
AtomSpace inspection. It is not a capacity or scheduler experiment.

Protocol: [preregistration](reviews/native-snapshot-payload-v1/PROTOCOL.md).
Consumer: `experimental_multihop/consumer.py`, introduced at
`b509d2b8d7388a570b5a666e1c845b95d207ad20`; exact measured hash is in sources.json.
Historical consumer labels remain unmodified.

Run from committed source, with the existing pinned native builds installed:

```sh
uv run --no-project python -m snapshot_payload_lab.compare run --output /tmp/payload-comparison
uv run --no-project python -m snapshot_payload_lab.compare audit /tmp/payload-comparison --output /tmp/payload-audit
```

The first command runs 72 serial executions: six unchanged parents, two formula
modes, three retrieval arms, two reversed-order sweeps. It writes complete public
captures, actual raw native query responses, traces, SQLite authorities, physical
world evidence, exact sources and human-readable comparisons. The audit checks
original arithmetic and authority records and separately reexecutes discovery
through the frozen full native projection. It does not rerun native PLN.

```sh
uv run --no-project python -m snapshot_payload_lab.validate default --output /tmp/payload-validation
uv run --no-project python -m snapshot_payload_lab.validate native --output /tmp/payload-validation
uv run --no-project python -m snapshot_payload_lab.query_validation --output /tmp/payload-queries.json
uv run --no-project python -m snapshot_payload_lab.negative /tmp/payload-comparison --output /tmp/payload-mutations.json
```

Cost accounting retains full capture, serialization, hashing, envelope validation,
structured projection, sealed runtime preparation/guards, load/readback, query,
authority, inference, persistence and monitoring work. Inclusive nested timers
must not be summed. A common measured wrapper counts both projections' logical
StringValue payload and actual validated graph's readback wire length; focused
tests compare that length with actual captured native output. Wire bytes and
archive bytes are not native RSS. RSS, peak memory and isolated fsync remain
unmeasured. Timing is descriptive for these fixed tasks only.

Recorded-only extracted replay validates archived evidence and raw query meaning;
it cannot recreate closed kernel-sealed runtime generations. New targeted
mutations exercise the same row/source audit used in the complete audit. Earlier
runtime mutation evidence remains historical. No transport, scheduler, policy,
recovery or runtime-lifetime work follows this milestone automatically.
