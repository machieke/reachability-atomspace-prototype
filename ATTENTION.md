# Bounded Recall → Diffuse → Reason

This separate experiment preserves native-recall publication `77e30ef` and measured
source `79f4f43`. It implements disposable bounded working copies, incremental
typed native queries and fixed gated transport. It does not implement adaptive
SPH, density normalization, learned conductance/retention, ECAN, pressure ranking,
new authority, native persistence or recovery automation.

With the existing pinned native builds installed (`scripts/build_native_recall.py`
and the prerequisites in `NATIVE_RECALL.md`), from a clean committed checkout:

```sh
uv run --no-project python -m attention_lab.compare --output artifacts/attention-fresh --audit-after
```

The output directory must not exist. This executes 192 bounded trials, 16 separate
nonbinding controls and matched-snapshot replay. JSONL traces contain public
snapshots, exact candidates, selected operations, query receipts, workspace
events, field epochs, scores, masked routes, allocations and actual certified
execution/observations. `report.json`, `comparison.md`, source copies and the
existing hash seal bind the run to its source and configuration. Replay separately:

```sh
uv run --no-project python -m attention_lab.compare --verify artifacts/attention-fresh
uv run --no-project python -m unittest discover -s tests -t . -v
uv run --no-project python -m unittest discover -s integration_tests -v
uv run --no-project python pressure_field_lifecycle_reference_checks.py
```

Read [the preregistered protocol](reviews/bounded-attention-v1/PROTOCOL.md) for
caps, interleaving, seeding, budgets and parent cases. WS-queue uses FIFO expansion;
WS-local uses local allocation; WS-flow applies four fixed steps before each
expansion. Every mode uses the same operation FIFO and exact hard gates. Only the
distinct complete conformance setting permits the frozen background fallback.

Native matching-set completeness and explored search completeness are separate.
Queued jobs mean not queried; interrupted jobs remain partly explored. Native
empty/nonempty/incomplete responses are explicit. Stale epochs and helper failures
are errors, never absence or a Python search substitution. A bounded unknown stop
does not prove impossibility. Inference keeps all five ordered slots and exact
identities; selected tuples and the live control ledger count against active pins.
Control monitoring is serviced before forecast discovery in every primary arm.

All timings are inclusive/nonadditive. Field time includes revision guards (full
public reads in live runs) and recording; selection time includes native view
checks. Native build verification and cold/replacement view costs remain unchanged.
The public snapshot, native projection/catalog and execution-time full enumeration
remain complete and separately counted. Response and joint buffers have separate
caps and can coexist. The cache does not bound total process memory; native RSS,
physical observation latency, isolated native compute and OS cache effects are
unmeasured. Full provenance, certificates and SQLite authority remain outside it.

The auditor independently scans source records for every query and reconstructs
the allocation ledger with a dense transition reference, then replays actual native
discovery, exact choices, selected formulas/certificates and SQLite state. Numeric
tests additionally use rational small-instance references and the M12 mutation
witness. Archive integrity verification is portable; semantic replay requires the
matching pinned builds. Different builds must be reported as a new experiment.
