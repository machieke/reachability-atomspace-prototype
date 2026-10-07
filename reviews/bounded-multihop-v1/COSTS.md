# Measured costs

The frozen twelve-execution cohort at `b509d2b8d7388a570b5a666e1c845b95d207ad20` took 86.178880 seconds in one serial descriptive pass. Regression groups and the cohort ran serially; lightweight documentation work could overlap. No speedup or statistical timing claim is made.

| Recorded category, seconds | Finite (six) | Native (six) |
|---|---:|---:|
| Whole episodes including output/close | 39.098325 | 46.724918 |
| Full observation/capture/evaluation, inclusive | 9.288932 | 8.533331 |
| Coherent work capture, inclusive | 3.679132 | 3.492749 |
| Frozen A evaluation | 0.265305 | 0.288046 |
| Frozen B evaluation | 0.479682 | 0.282595 |
| Whole multi-hop work projection | 3.336968 | 3.144377 |
| Reused frozen one-step validation/projection | 2.049379 | 2.076280 |
| New dependency graph/serialization | 0.414115 | 0.405790 |
| Public candidate enumeration | 0.854112 | 1.038112 |
| FIFO selection including enumeration | 1.271115 | 1.526298 |
| Formula runtime | 0.001055 | 2.125756 |
| Native finite reference check | 0.000000 | 0.001208 |
| Numerical precertification | 0.635638 | 0.606100 |
| Numerical postcertification | 0.678798 | 0.764824 |
| Numerical commit | 0.691602 | 0.725130 |
| Execution gate and reservation | 0.231179 | 0.201505 |
| Dispatch | 0.133979 | 0.127104 |
| Acquisition/admission inclusive | 7.129256 | 7.595680 |
| Monitoring/admission inclusive | 7.007456 | 7.503194 |
| Goal accounting | 1.719233 | 1.833959 |
| Completion | 0.223663 | 0.174762 |
| Native projection/readback | 0.000000 | 4.449191 |
| Authority reopen | 0.540311 | 0.637060 |
| Physical transitions | 0.001234 | 0.001221 |
| Passive measurement | 0.012953 | 0.013439 |
| Executor effect linking | 0.007797 | 0.008191 |
| Clock/opportunity publication | 2.911783 | 3.324617 |
| Initial nonmutation digests | 0.110860 | 0.113724 |
| Trace serialization | 0.930730 | 1.019717 |
| Final independent dependency check | 0.058866 | 0.064149 |

Timers overlap and must not be summed. The new projection first reuses frozen one-step input/scope/assessment validation, then expands only its deferred deeper fragment. This repeated validation is charged; there is no claim of optimal discovery cost. Selection includes frontier enumeration. Full observation includes coherent capture, A/B and graph rebuilding; projection itself includes repeated frozen assessment checks.

Actual inference includes native subprocess/protocol overhead, and certification/commit remain separately visible. Persistence is included in service mutations, numerical commits, dispatch, monitoring, completion and total elapsed time; isolated SQLite commit/fsync is not measured. Native projection/readback and durable authority reopening are explicit, with zero additional runtime calls on reopen. They do not count as native retrieval or new evidence.

Whole episode time includes setup, guards, references, reconstruction, trace/output writing and close. The cohort timer also includes runner work between episodes. Source copying and native build verification precede it. Compression, extracted audit, mutations and regression invocations are outside the cohort timer. Trace serialization measures JSON encoding/bytes rather than isolated disk flush. Only the first authority guard digest has its own timer; the second remains inside total time.

Also unmeasured: isolated native arithmetic, RSS/peak memory, real-world sensor or deployment latency, calibrated forecasting and production decision quality. Logical ticks, wall time, selection/work credits and acquisition counts are distinct. There is no pressure or transport computation in this increment.

Raw per-row graph/capture/selection costs, per-call runtime values and nested session/environment counters are preserved. `validation/analysis.json` and `render_review.py` reproduce this aggregation. Python bounded scans remain explicit and charged; neither scalability nor a native-storage/query redesign is claimed.

| Parent | Finite episode seconds | Native episode seconds |
|---|---:|---:|
| two-hop | 7.416187 | 8.668087 |
| three-hop | 8.973981 | 9.988201 |
| shared | 10.124138 | 10.888473 |
| unavailable | 1.393324 | 2.128878 |
| replacement | 8.321054 | 10.613712 |
| adverse | 2.869642 | 4.437567 |
