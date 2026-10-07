# Observation-independent environmental validation

This layer keeps the published consumer, bridge, A/B, role assignments, numerical
formulas, original authority and controllers unchanged. It evaluates the existing
deduction task in six separately declared deterministic environments. It does not
rewrite the old scripted observation/lifecycle conformance results.

`world_lab.world.PhysicalWorld` holds private product, health, accepted-command
schedule and physical goal history. Only independent ticks, actual executor effects
and declared exogenous events change these fields. `world_lab.adapter.Port` links
exact typed requests to actual executor query receipts, regardless of whether an
acknowledgment reached the caller. Duplicate idempotent acceptance schedules once.
Its passive measurement port returns truthful instantaneous values or UNKNOWN.
No private goal flag or event schedule enters the consumer's input.

`world_lab.run` retains one existing Consumer through ticks 0..8, idle intervals and
past historical completion. At most eight operations per tick; original budgets,
attempt suppression and FIFO history persist. Due effects precede exogenous events,
which precede public clock/opportunities and selected operations. Physical updates
are checked not to mutate authoritative state. Public clock/account calls and
actual admitted observations alone affect recognized goal state.

The physical goal is artifact-v2 healthy at three consecutive physical ticks.
The frozen certificate predicate instead requires an exact admitted observation
window, accepted effect, product/completion observations and original hard gates.
Loss integrals, first physical achievement, historical completion, current loss
and recognition lag are reported separately through the whole horizon.

Product channels use existing product fact/milestone interfaces. Missing products
return UNKNOWN; wrong products retain their real identity and face existing
admission rejection. A failed wrong-product milestone does not itself supply a
new generic negative-product contract. Delayed/out-of-order delivery is deferred:
sample time must equal both clocks, never relabeled current. Sensor availability
descriptors have a fixed public schedule and remain unknown independently of truth.

One command runs all twelve core executions with the existing pinned native build:

```sh
uv run --no-project python -m world_lab.compare run --output artifacts/independent-world-local
uv run --no-project python -m world_lab.compare audit artifacts/independent-world-local
```

The directory must be fresh and measured inputs committed. Missing native builds
block execution rather than substituting finite arithmetic. See NATIVE_RECALL.md.
Traces keep public choices/receipts and private physical evidence separately. Native
projection/readback concerns existing authority records, never private world truth
or native retrieval performance. The independent physical reference imports no
world transition function; observed-goal replay uses actual admitted samples and
the frozen predicate.

See reviews/independent-world-v1 for exact declarations, costs, limits, coverage,
failures and source-bound publication. Six parent worlds are repeated in two modes;
controls and metamorphic repeats are not additional independent samples. No
controller comparison, calibration, real-world safety, pressure benefit or policy
promotion is claimed. Stop here without another scheduler, deeper planner,
transport change, generalized recovery or native-storage redesign.
