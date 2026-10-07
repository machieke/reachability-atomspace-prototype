# Native runtime lifetime review

Measured implementation and auditor: `fa6c2674bc5977475f1aad9e6c884405ef7b7414`. Preregistered protocol `aab9673`.
Baseline closure `c088775`, all earlier implementations/reviews/builds, six parents, formula inputs, consumer, budgets, authority and world remain preserved. This is a bounded code-lifetime experiment with cold knowledge views.

All 72 executions and 48 scan/native pair checks passed. There were 48 observed completions and 24 unresolved outcomes. Decisions, exact premises, observations, losses, budgets and stop reasons matched; repeated sweeps reproduced the same semantic sequences. No semantic divergence is treated as a benefit.

| Arm | Episode seconds | Cold views | Runtime preparations | Original build verifications |
|---|---:|---:|---:|---:|
| MH-scan | 145.109862 | 0 | 0 | 0 |
| MH-native-strict | 322.242694 | 528 | 0 | 528 |
| MH-native-session | 234.062324 | 528 | 24 | 24 |

Every paired wall time and range across sweeps is in PAIRED_TIMES.md. Counts below classify session minus comparator elapsed time; negative is favorable, positive unfavorable, zero neutral. These are descriptive local measurements, not independent samples or significance estimates.

```json
{
  "strict": {
    "0": {
      "favorable": 12
    },
    "1": {
      "favorable": 12
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

Neutral: all logical outcomes and loss trajectories match. Unfavorable overhead remains: the session arm stages and hashes 2,499,909,312 sealed bytes across 24 episodes, runs integrity guards, and still opens 528 cold views. Bytes staged are not RSS or peak memory. Full capture/A/B, unused one-step validation and consumer frontier work remain paid.

The audit reexecutes 51,520 native queries using the frozen strict backend and checks 1,584 public work views/choices, 972 selections, 3,288 persisted certificates and 180 recorded formula calls. Of the original formula calls, 90 used fresh native PLN. Audit fresh PLN calls: zero. Recorded generation provenance checks: 24; original actual helper mapping checks: 528. Closed generation memfds are not rehashed during archive replay.

630 fresh regression tests passed, with no failures, errors or skips. All 17 altered-copy witnesses were rejected. VALIDATION.md lists executed and omitted coverage, retained development failures and exact replay distinctions.

With the pinned native build available, run the comparison with one command:

```sh
uv run --no-project python -m runtime_lifetime_lab.compare run --output /tmp/runtime-lifetime-comparison
```

For independent audit and archive integrity:

```sh
uv run --no-project python -m runtime_lifetime_lab.compare audit /tmp/runtime-lifetime-comparison --output /tmp/runtime-lifetime-audit
uv run --no-project python reviews/native-runtime-lifetime-v1/verify_review.py
```

Use fresh output directories. Run the experiment from the measured source; run the archive verifier from the later publication containing ARCHIVE.json and review.tar.xz. NATIVE_RECALL.md documents native build setup. Source/build/launch identities, raw queries, traces, journals, certificates, failures, costs and test receipts are in the single archive. Checksums establish integrity, not publisher authentication.

RUNTIME_CONTRACT.md states the Linux/glibc accidental-drift contract and uncovered host dependencies. Logical simulation time does not advance with computation; equal losses do not imply equal real-time performance. RSS, peak/native memory, isolated fsync and other omissions remain explicit. No production, cognitive-speed or general native-recall advantage is claimed.

Stopped here. No pooling, persistent/incremental AtomSpace, query caching across views, selective invalidation, planning/depth change, transport, policy-B promotion, source supersession or generalized recovery.

The fixed-snapshot diagnostic also reports costs against the new arm: initial session preparation is paid on the first observation, and unchanged-binding passes can vary in either direction. Read the eight raw observations in COSTS.md; none is a new independent task or throughput claim.

Provenance clarification: the inherited consumer-revision label names the earlier work-loop consumer. PROVENANCE_NOTE.md and CONSUMER_PROVENANCE.json identify the actual unchanged multi-hop consumer and its verified file hash. The full sealed source manifest is authoritative; no frozen results were rewritten.
