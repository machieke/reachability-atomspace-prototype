# Native snapshot payload review

Measured implementation/auditor: `28f9dad3543de46725121f8b48079d020991e566`. Protocol preregistration: `f4d2e39`. Preserved closure: `d2446bf`.
Load-wire bytes fell 62.89%, but compact had no aggregate speedup: 241.274257 seconds versus 241.020144 for full and 149.839596 for scan. Semantic outcomes were unchanged.
This experiment removes only the extra whole-public-snapshot embedding from the native view. All source payloads, structured representations, registered content and recall relations remain. Both native arms retain the same sealed session runtime, cold changed-binding views, controller and authority gates.

All 72 executions conformed; 48 scan/native comparisons and repeated sweeps matched exact decisions, inputs, observations, losses, budgets and stops. There were 48 observed completions and 24 unresolved outcomes. This is a neutral semantic result, not a new cognitive capability.

| Arm | Episode seconds | Cold views | Runtime preparations | Load-wire bytes | Readback-wire bytes | Logical StringValue bytes |
|---|---:|---:|---:|---:|---:|---:|
| MH-scan | 149.839596 | 0 | 0 | 0 | 0 | 0 |
| MH-native-session-full | 241.020144 | 528 | 24 | 241104212 | 252583480 | 92508412 |
| MH-native-session-compact | 241.274257 | 528 | 24 | 89477548 | 100938588 | 16735456 |

Both native arms retain 76,003,016 canonical public-export bytes and 16,342,128 source-payload bytes across their views. Compact removes 76,003,016 duplicate chunk bytes and adds 230,060 envelope bytes. These are sums across views, not peak memory.

All individual wall-time pairs and between-sweep ranges are in [PAIRED_TIMES.md](PAIRED_TIMES.md). Favorable means compact took less elapsed time, unfavorable more, neutral equal. Counts are descriptive local observations over six fixed tasks, not independent samples or significance estimates.

```json
{
  "full": {
    "0": {
      "unfavorable": 7,
      "favorable": 5
    },
    "1": {
      "favorable": 7,
      "unfavorable": 5
    }
  },
  "scan": {
    "0": {
      "unfavorable": 12
    },
    "1": {
      "unfavorable": 12
    }
  }
}
```

Compact still pays full capture, canonical serialization, hashing, envelope validation, source structure, runtime preparation and query guards. It does not promise a total speedup proportional to the transfer reduction. Scan comparisons remain visible even if unfavorable. No budgets, policies, formulas or tasks were adjusted to improve timing.

The core audit checks 1,584 public rows, 972 selections, 3,288 persisted certificates and 180 recorded arithmetic calls. Original executions made 90 actual native PLN calls. The auditor separately reexecutes 51,520 native discovery queries using the frozen full projection; audit native PLN calls are zero.

The separate diagnostic checks 1536 full/compact query pairs across all nine forms, exact records, alternatives, historical membership, models, opposing literals, absent answers and tight limits. It is not an extra benchmark task. 663 applicable tests passed once at frozen source. All 11 new targeted altered-copy witnesses were rejected. See [VALIDATION.md](VALIDATION.md) for exact coverage, omissions and retained failures.

Reproduce from measured source with the pinned native build installed:

```sh
uv run --no-project python -m snapshot_payload_lab.compare run --output /tmp/payload-comparison
uv run --no-project python -m snapshot_payload_lab.compare audit /tmp/payload-comparison --output /tmp/payload-audit
```

Use fresh output paths. From this publication, verify the archive with:

```sh
uv run --no-project python reviews/native-snapshot-payload-v1/verify_review.py
```

The archive contains exact measured source, captures, raw native responses, SQLite states, certificates, physical trajectories, costs and validation receipts. To replay extracted evidence, checkout the measured revision and call `snapshot_payload_lab.audit.audit(extracted_comparison, reexecute=False)`. This checks recorded query semantics and arithmetic; it does not recreate closed kernel-sealed generations or rerun native PLN. Later PUBLICATION.json records archive verification, extracted replay and corrupt-archive rejection. Checksums establish integrity, not publisher authentication.

New metadata correctly identifies `experimental_multihop/consumer.py` at `b509d2b8d7388a570b5a666e1c845b95d207ad20` with SHA256 `3ec9c16ed98f2aff48a0db15b88d9c368edc4cdcb133a9789dff6ed96b68c19a`. Earlier consumer labels and reviews are untouched.

Stopped at this bounded payload experiment. No helper pooling, persistent/incremental AtomSpace, cross-view caching, selective invalidation, scheduler/depth changes, adaptive transport, source supersession, policy promotion, generalized recovery or large-scale claim.

Measured interpretation: load-wire bytes fell 62.89% and readback-wire
bytes fell 60.04%. Goal and decision semantics were neutral.
Compact aggregate episode time was 0.254114 seconds higher than full
(0.105%), with 12 favorable and 12 unfavorable individual
pairs. All 24 compact-versus-scan pairs were slower. This run establishes no total
speedup or native advantage over scanning. Between-sweep variation is published;
no significance inference is made from the small aggregate difference.

Load/readback I/O totaled 17.543069
seconds for full and 10.687762 for compact.
Compact's new envelope-validation inclusive timer totaled
11.038699 seconds, including independent
full serialization/binding work. These nested timers show paid work, not a causal
wall-time decomposition. Hashing, validation and accounting were retained as
preregistered. No follow-on optimization is included.

Outer-session discrepancy: tool session 91861 returned exit 143 after the phase logs were collected. All eight phase subprocess receipts are complete and report exit zero, including preservation after the full audit. The cause of the outer-shell result is unresolved; it is not classified as a clean wrapper pass. validation/outer-shell-exit.json preserves this new occurrence separately from the earlier historical anomaly. Frozen suites were not repeated.
