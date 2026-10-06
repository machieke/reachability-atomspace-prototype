# Shared protected-assembly recall: bounded comparison

Measured implementation and auditor: `53d7b0b257ea436dc043e9d497fd3c76dcd0e03c`.
Protocol preregistration: `6993c40`. The publication revision is recorded separately
in `PUBLICATION.json` to avoid a self-referential archive hash.
Prior publication `71c32df` and measured/auditor `0134092` are preserved unchanged.

The shared service boundary is implemented and tested. It helps on some of these
small structures and harms another. The unchanged flow orderer adds **no terminal
loss wins** once queue/local receive the same protection, and has two unfavorable
configuration/formula repeats. Neither coordinator nor transport is promoted.

## Reproduce

At the measured checkout, with the existing pinned native dependencies installed
as documented in [NATIVE_RECALL.md](../../NATIVE_RECALL.md), run one command with a
fresh directory:

```sh
uv run --no-project python -m assembly_lab.compare --output /tmp/completion-recall-fresh --audit-after
```

This runs all 192 cells and semantic replay, writing source/configuration copies,
public snapshots, native queries, job/tuple/candidate/service traces, selected
operations, observations, formulas/certificates, SQLite ledgers, costs, JSON reports,
a readable comparison and a hash inventory. Both formula modes use actual native
AtomSpace recall; the native mode also runs selected PeTTa/PLN formulas.

For the published archive, run:

```sh
uv run --no-project python reviews/completion-aware-recall-v1/verify_review.py
```

Extract its `comparison/` into a fresh directory and use the measured checkout and
matching pinned builds with `python -m assembly_lab.compare --verify <directory>`
for semantic replay. The archive verifier checks integrity/inventory against the
published hashes, not publisher authentication. Rebuilt native binaries can have
a different build identity and require a fresh measured run.

## Fixed experiment

Two scheduling contracts × three existing orderers × q16/q48 × finite/native
formulas × eight parents = **192 executions**. Seed 0, workspace 48 entries/512 KiB,
work 16, acquisitions 16, selections 32, all other original bounds unchanged.
Two parents are reused diagnostics; six are preregistered engineering variations.
These are eight parent structures, not 192 independent tasks or a holdout cohort.
The six orderer permutations and contract/formula order are interleaved as declared.

Controls run first. At most one oldest affordable current join receives protection
per tranche, independent of activation or outcome labels. A resident producer needs
12 query credits; an evicted producer needs 13: six ordered premise/conclusion
queries, optional exact producer lookup and six possible exact preparation reads.
The slot is served immediately. Eligible retained work keeps preparation credit;
a negative attempt releases it and ordinary inspection resumes. Final candidate
FIFO age/tie ranking, native views, guards, field equation/four steps/cooling,
LRU/pins and full authoritative acceptance remain unchanged.

This conservative reservation protects a bounded attempt. Actual response/joint
sizes, tuple work and selected-bundle bytes can still exhaust their existing limits.
A missing premise, an unqueried dependency, a stale selection and an authoritative
rejection remain different outcomes. A slot is compute accounting, never evidence,
confidence, resource authority, coverage or observed relief. Preparation protection
is conditional on eligible work after the one protected attempt; it is not a new
promise to every candidate that later ordinary inspection might discover.

## Outcomes

All **192 measured executions passed conformance**. Favorable means lower terminal
loss; external and certified terminal-loss classifications agree in every pair.
Each row below has 32 matched configuration/formula repeats of the eight parents.

| Comparison | Favorable | Neutral | Unfavorable |
|---|---:|---:|---:|
| Protected queue vs frozen queue: shared scheduling effect | 6 | 24 | 2 |
| Protected flow vs frozen flow: shared scheduling effect in flow | 12 | 20 | 0 |
| Protected flow vs protected queue: incremental flow effect | 0 | 30 | 2 |
| Protected flow vs protected local: incremental flow effect | 0 | 30 | 2 |

Shared queue gains occur at q16 on alternatives, ready-broad and
evicted-alternatives, both formula modes. The q16 early-low-confidence producer
case worsens from loss 0 to 10. Shared flow gains occur on those three parents at
both query budgets. Its remaining unfavorable incremental comparison is the
early-producer parent at q48: protected queue/local reach loss 0, flow stays at 10.
Missing-upstream and shared-intermediate remain unresolved; support-change and
monitoring results retain their original hard gates and relevant observations.

See [the preserved frozen boundary](BOUNDARY.md) and [complete-sequence explanation](SEQUENCES.md).
The archive retains all scores, candidate ages/ties, observations, stale requests
and loss changes. The first divergence is not assumed to cause the entire delta.

There were **260 protected opportunities, all served**, with 106 yielding no
eligible candidate at the end of that slot. No in-discovery stale abandonment or
preparation-credit failure occurred in the primary matrix; both are exercised by
separate native tests. There were 3,568 repeated unaffordable-offer observations,
not 3,568 distinct obligations. Every discovery tranche with pending join offers
had an affordable offer at some point; this does not imply later offers still fit.

Across all arms: 14,814 native queries, 1,110 tuple visits, 206 formula calls (103
actual native), 218 selected certified numerical commits including direct observations,
18 stale selected operations and 24 expected failed product observations. All formula
calls returned PASS; stale postchecks did not publish their proposed belief. The
six observed LRU evictions occur in protected flow's q48 eviction variation. No
primary selected bundle required rematerialization; forced-eviction tests separately
charge the one producer read and six preparation reads. This limitation is retained
rather than adjusting the case or capacity to force a result.

## Measured costs and memory

Each aggregate below contains 32 runs. Inclusive timings overlap; do not add them.
They are a single descriptive pass with concurrent regression load, not a timing
experiment with confidence intervals. Fewer calls with fewer achieved goals are
not reported as an efficiency gain.

| Contract/orderer | Zero certified loss / 32 | Native queries | Formula calls | Total seconds |
|---|---:|---:|---:|---:|
| Frozen queue | 12 | 2,498 | 26 | 138.545 |
| Frozen local | 12 | 2,498 | 26 | 140.000 |
| Frozen flow | 2 | 1,572 | 4 | 113.602 |
| Protected queue | 16 | 2,774 | 50 | 175.001 |
| Protected local | 16 | 2,774 | 50 | 176.092 |
| Protected flow | 14 | 2,698 | 50 | 264.206 |

Protected flow records 6,200 field steps, 0.343 s in the kernel excluding measured
guards, and 92.791 s in full field-guard snapshot callbacks. Event recording across
all its phases is 1.483 s. These categories are nested: kernel time still includes
bookkeeping, and guard time is also present in public-read totals. The measured
flow arms together execute 10,648 conservative steps; maximum allocation residual
is `6.661338147750939e-16`. No closed route is reopened by service scheduling.

Active occupancy reaches 48 entries and 47,931 bytes; response/joint peaks are 7/18
records, with 18 joint slots and at most 7 retained candidates. Complete native
backing reaches 1,403 atoms, 41 source records, 243,695 public-export bytes and
815,173 load bytes. The active workspace is not total memory. See [cost definitions](COSTS.md)
and the archive's per-run profiles, phase costs, reservation/latency metrics and
all bound reasons. RSS/physical memory, physical observation latency, isolated native
arithmetic, standalone fsync and cache effects are unmeasured; no scaling claim.

## Validation and scope

[Validation](VALIDATION.md) records 358 applicable default, all 132 native integration
and 15 numerical tests passing at the measured revision, with zero failures/errors
or skips. The broader default suite was not rerun: 662 tests are explicitly omitted.
The historical full default pass at `0134092` is not relabeled as current coverage.
Original development assertion failures and their corrections are preserved.

The review archive contains `comparison/`, `validation/`, `development/` (including
the unchanged 12-run frozen reproduction and development preflights) and `review/`.
Source binding, independent native answers, dense allocation checks, independent
FIFO reservation/no-overspend checks, exact frozen policy parity, formula checking,
persisted certificates and SQLite reconstruction form the semantic audit.
The audit passed 1,150 decision states, 14,814 independent native-answer checks,
460 exact frozen-policy matches, 10,648 field steps and 218 persisted selected
commits. All five unsealed/resealed trace attacks were rejected.

One frozen audit convenience counter double-counts control queries by adding
both the control-end summaries and individual query events: its raw value is
4,600. `validation/audit-counters.json` explicitly records the actual **2,300**
control queries (10,954 inspection + 1,560 assembly + 0 preparation = 14,814 total
when control is included). Raw audit output is preserved. This reporting defect
does not affect the per-query balance checks, primary metrics, coordinator,
selection or measured timing. The publication correction script is included;
the frozen measured/auditor files are not silently rewritten.

This completes one bounded shared-service experiment. It does not complete the
full pressure, attention, transport, storage or benchmark designs. No adaptive
transport, coefficient tuning, learned retention, build-check caching, global
planning, generalized recovery or larger cohort was added. Stop here.
