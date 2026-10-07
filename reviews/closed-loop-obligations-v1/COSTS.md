# Measured costs and finite work

One serial twelve-episode pass at `d2a6b6605eaefc32f0c56e2a7c0d5e9bf11cffb8`; seed 0. Cohort elapsed **17.158 s**. Setup, work-view construction, selected APIs, observations, reconstruction and output are included. Source-copy/native-build preflight and post-run audit/publication are outside this total.

| Phase | Total ms |
|---|---:|
| Coherent observation, inclusive | 1813.545 |
| Full frozen bridge acquisition (inside observation) | 790.449 |
| Authoritative numerical capture (inside acquisition) | 293.965 |
| Inventory/state acquisition (inside acquisition) | 235.366 |
| Initial frozen A evaluation | 104.421 |
| Initial frozen B evaluation | 78.487 |
| Bridge projection, inclusive | 532.444 |
| Frozen A/B revalidation (inside projection) | 195.244 |
| Producer discovery/route graph (inside projection) | 16.249 |
| Work-view serialization (inside projection) | 70.085 |
| Public frontier construction (inside selection) | 182.388 |
| Queue selection including frontier | 249.780 |
| Immediate public revalidation | 351.644 |
| Selected execution including revalidation | 5055.492 |
| All report ingestion | 58.963 |
| Selected report adoption, inclusive | 233.443 |
| Inference, inclusive (all session admissions) | 951.216 |
| Formula runtime (finite/native combined, inside inference) | 892.041 |
| Precertification (all session admissions) | 576.584 |
| Postcertification (all session admissions) | 721.363 |
| Numerical commit/persistence (all session admissions) | 663.585 |
| Execution gate and reservation | 112.810 |
| Simulated dispatch | 100.108 |
| Monitoring, inclusive | 1540.368 |
| Completion API | 147.965 |
| Goal accounting | 641.226 |
| Native AtomSpace projection/readback | 3060.760 |
| Authority reopen | 525.526 |
| Trace serialization | 235.206 |
| Trace file writes | 9.202 |

These are nested measurements, not additive cost components. Coherent observation includes full acquisition, an additional public read, initial frozen assessments and bridge revalidation. Selection includes enumeration; selected execution includes immediate revalidation plus the unchanged session's own repeat checks and full APIs. Monitoring overlaps acquisition/execution. Pre/post/commit and inference counters include setup report admissions as well as selected work. The constructor setup timer is only a subset of setup; all setup is charged in episode/cohort elapsed.

The discovery timer covers producer route construction; initial obligation/global nodes and other graph validation remain inside total projection. Runtime includes process/adapter overhead; isolated native arithmetic is unmeasured. Public reads from diagnostic summaries and coherent captures are retained in raw session totals. No full-state scan is represented as a cheap graph-only lookup.

Across 12 executions: **54 selected requests/operations**, **54 operation-work credits**, **22 acquisition credits**, **66 full authoritative captures**, **14 formula calls**, including **7 fresh native calls**. The 82 candidate occurrences and 64 tuple visits repeat public states; graph totals are 810 node occurrences and 986 edge occurrences. These are not unique obligations, observations or independent population samples.

Work-view payloads total 4,024,504 bytes; full JSONL traces total 16,752,022 bytes. Raw per-episode counters and per-row limits remain available. Each episode is bounded by 32 selections, 64 operation-work credits and 16 acquisition credits; eight selection/work and four acquisition credits are reserved from numerical work for original execution/monitoring duties. Public/graph input, tuple, node and edge limits remain unchanged.

Simulated logical time, request counts, charged work, acquisitions, native calls, wall time and serialized bytes are distinct quantities. Health durability requires actual admitted observations at the existing logical times; wall-time speed is not outcome quality. Initial data and external responses are synthetic.

RSS, isolated fsync, physical sensor latency, isolated native arithmetic and production outcome quality are unmeasured. Memory scope is bounded input/graph/queue state, not a measured resident-memory claim. Existing AtomSpace projection/readback verifies a boundary; it is not a native retrieval-performance experiment. There is no scheduler comparison, speedup claim, calibration result or scalability claim.
