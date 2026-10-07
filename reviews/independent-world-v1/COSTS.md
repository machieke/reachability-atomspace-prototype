# Measured costs

One serial descriptive cohort at `b12127556d6d1fe4a7c152dba85f5d71df266194` took 74.325568 seconds. Regression groups and cohort ran serially. No comparative speed claim or statistical timing estimate is made.

| Recorded category (seconds) | Finite, six runs | Native, six runs |
|---|---:|---:|
| Whole episodes, including final output | 33.598942 | 40.329226 |
| Public/work observation, inclusive | 7.100082 | 7.230306 |
| Work capture, inclusive | 3.298213 | 3.292906 |
| Frozen A evaluation | 0.257912 | 0.272059 |
| Frozen B evaluation | 0.266669 | 0.240119 |
| Work projection, inclusive | 2.026347 | 2.105872 |
| Graph discovery only | 0.062735 | 0.061605 |
| Public candidate enumeration | 0.815119 | 0.825118 |
| Selection including enumeration | 1.111580 | 1.106587 |
| Actual formula runtime | 0.000802 | 1.838494 |
| Native formula reference checks | 0.000000 | 0.001072 |
| Precheck certification | 0.499396 | 0.571443 |
| Postcheck certification | 0.553597 | 0.656796 |
| Numerical commit | 0.568584 | 0.685554 |
| Execution gate/reservation | 0.290913 | 0.301805 |
| Dispatch | 0.199055 | 0.240811 |
| Observation acquisition, inclusive | 6.122128 | 5.579849 |
| Monitoring admission, inclusive | 6.017197 | 5.433951 |
| Completion | 0.102079 | 0.106686 |
| Goal accounting | 1.586124 | 1.714980 |
| Native authoritative projection/readback | 0.000000 | 4.087497 |
| Authority reopen | 0.614136 | 0.610048 |
| Physical transitions | 0.001218 | 0.001087 |
| Passive measurement port | 0.012950 | 0.012721 |
| Actual executor effect link | 0.008571 | 0.008292 |
| Clock/opportunity publication | 2.731811 | 2.926551 |
| Initial authority guard digests | 0.155448 | 0.173147 |
| Trace JSON serialization | 0.892146 | 0.976906 |

These timers overlap and must not be added. Selection contains frontier enumeration; public observation contains capture, A/B and work projection, including repeated frozen assessment checks. Acquisition includes existing report/observation admission and its persistence. Selected-operation timing includes revalidation and original execution calls. Numerical precheck, runtime, postcheck and commit have separate counters. Native runtime includes subprocess/protocol overhead; reference checks are separate.

Whole episode time includes setup, repeated snapshots, guards, independent checks, reconstruction, output and close. The cohort timer also contains runner/report setup overhead between episodes. Preflight source copying and native build verification precede that timer. Publication compression, audits, tests and extraction are separate, unmeasured by the cohort timer. The deterministic tick duration is a model unit, not elapsed wall time or computational work.

Persistence is included in actual service mutations, numeric commits, observation calls, dispatch, completion and total elapsed time; SQLite commit/fsync is not separately isolated. The guard counter covers the initial digest; the second digest remains included in total time. Trace serialization measures JSON encoding and byte count, not an isolated disk flush. Public descriptor publication includes clock/account operations. Physical event and measurement timers cover only this tiny simulator, not deployment or sensor latency.

Also unmeasured: isolated native arithmetic within the subprocess, RSS/peak memory, production sensor latency, real-world execution latency, production decision quality and probability calibration. No pressure construction or adaptive transport is performed by this unchanged consumer. All raw nested counters and per-operation timings remain in `result.json` and `trace.jsonl`; `validation/analysis.json` and `render_review.py` reproduce this aggregation.

| Environment | Finite elapsed seconds | Native elapsed seconds |
|---|---:|---:|
| observable | 7.357031 | 8.486493 |
| unobservable | 2.810793 | 4.418590 |
| delayed | 5.613230 | 6.825162 |
| wrong-artifact | 3.409511 | 4.379666 |
| early-failure | 7.454599 | 8.292869 |
| regression | 6.953777 | 7.926446 |
