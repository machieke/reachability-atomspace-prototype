# Observation-independent world validation

This increment evaluates the unchanged closed-loop consumer in six deterministic
environments where product and health evolve independently of observing them.
The new world, passive port and tick driver reuse the existing deduction task,
finite/native formulas, admission, executor and observation interfaces. The old
scripted acquisition results remain valid within their published scope and are
unchanged.

Measured implementation and auditor: **b12127556d6d1fe4a7c152dba85f5d71df266194**.
Environment preregistration: **326c7fe**. Preserved closure: **173c772**; previous
measured consumer/auditor: **d2a6b66**; previous publication: **3b89d63**. The
[protocol](PROTOCOL.md) and [exact declarations](environments.json) precede measured
runs. No numerical inputs, thresholds, event times, budgets or opportunities were
tuned after outcomes were observed.

The environment links the exact real simulated-executor request and actual effect
receipt. A lost local reply cannot erase an accepted effect; idempotent acceptance
schedules it once. An independent clock applies due effects and declared events
before each public tick. Passive measurements return truthful current values or
UNKNOWN. Private state, event schedules and physical goal flags never enter the
consumer's public snapshot or directly change authority.

One consumer instance persists across ticks 0 through 8, including idle ticks and
ticks after historical completion. It retains its selection history, attempted
bases and original budgets. Every selected operation still passes the existing
public interfaces and hard gates. A public opportunity permits another call; it
does not reset the consumer or retry an ambiguous effect automatically.

[COMPARISON.md](COMPARISON.md) separates physical loss from current observed loss
for twelve executions of six parent environments. [OUTCOMES.md](OUTCOMES.md)
explains the physical events, actual samples, recognized completion, reopening and
unresolved outcomes. [VALIDATION.md](VALIDATION.md) lists executed and omitted
coverage. [COSTS.md](COSTS.md) reports measured costs and exclusions.
[DEVELOPMENT.md](DEVELOPMENT.md) preserves new development failures and corrections.

The physical goal requires the exact artifact to be healthy at three consecutive
physical ticks. The existing completion predicate instead requires an admitted
sampling window and all existing product, execution and hard checks. A physically
successful service can remain uncertified during an outage. Past certification
does not establish current health or continuous-time safety.

Run the twelve executions using the pinned native build described in
[NATIVE_RECALL.md](../../NATIVE_RECALL.md), then replay the resulting bundle:

```sh
uv run --no-project python -m world_lab.compare run --output artifacts/independent-world-local
uv run --no-project python -m world_lab.compare audit artifacts/independent-world-local
uv run --no-project python -m world_lab.negative artifacts/independent-world-local --output artifacts/independent-world-negative.json
```

The output directory must be fresh and measured inputs committed. The run writes
source/configuration, public snapshots and full frontiers, exact choices and
receipts, persisted certificates, private transition/measurement histories, separate
outcomes, costs and a readable comparison. Native dependencies are required; finite
arithmetic never substitutes for absent native execution. Projection/readback
checks ordinary authoritative records, not private truth or retrieval performance.

Verify the published archive before extracting into a fresh directory:

```sh
uv run --no-project python reviews/independent-world-v1/verify_review.py
mkdir -p /tmp/independent-world-review
tar -xJf reviews/independent-world-v1/review.tar.xz -C /tmp/independent-world-review
uv run --no-project python -m world_lab.compare audit /tmp/independent-world-review/independent-world-review-v1/comparison
```

The archive contains comparison, validation, development and review directories.
The comparison's `source/` contains all measured inputs, with hashes and revision
in `sources.json`. Replay requires those exact source files, including the auditor.
It independently checks the physical recurrence, actual measurements and recorded
arithmetic; replays the frozen consumer and observed-goal predicate; and reconstructs
authority and executor journals. Replay is not a fresh native formula experiment.
`PUBLICATION.json` binds the publication commit to the archive and extracted replay
without a self-referential checksum. Checksums provide integrity, not publisher
authentication.

The bounded result makes no controller comparison, pressure-benefit, probability
calibration, retrieval-performance, empirical-safety or production-readiness claim.
Delayed/out-of-order or noisy observations, multiple non-idempotent effects,
crash resume and new observation contracts remain unsupported. Stop at publication;
no tuning, policy promotion, transport, deeper planning, generalized recovery or
native-storage redesign follows.
