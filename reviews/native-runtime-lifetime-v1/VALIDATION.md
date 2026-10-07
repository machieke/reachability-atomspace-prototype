# Frozen validation and omissions

Measured implementation/auditor `fa6c2674bc5977475f1aad9e6c884405ef7b7414`. Default and native groups each ran once, serially. Source and test hashes matched at start/end; both suite wrappers exited zero. Comparison and audit followed serially.

| Suite | Run / passed | Failures | Errors | Skips | Seconds |
|---|---:|---:|---:|---:|---:|
| default | 476 / 476 | 0 | 0 | 0 | 327.985732 |
| native | 154 / 154 | 0 | 0 | 0 | 253.550191 |

New focused coverage: three default contracts and 29 native tests, including 19 retained native-multihop seam cases through the session backend. Actual tests cover sealed executable/library write/truncate denial, corrupt/missing receipt and artifact, changed lock, original-tree drift, missing/replaced aliases and descriptors, wrong/closed generation, baked-in mutable library detection, hostile loader environment, explicit rebuild with accumulated costs and unchanged consumer state, native intermediate round trip, exact support retirement and stale operation rejection.

An unchanged snapshot repeats actual native queries without a new helper; changing logical time requires a cold replacement in both native arms. The separate eight-observation diagnostic corroborates attribution only; it adds no independent task or native PLN call. Its measured data are in validation/repetitions/.

Omitted: 642 tests in 46 tests modules.
Omitted: 48 tests in 11 integration_tests modules.
Also omitted: 15 standalone pressure reference checks. Broad unchanged scheduler/transport, generalized recovery/corpus and unrelated matrices remain omitted. Historical passes are not fresh coverage; the earlier wrapper exit-143 anomaly remains unresolved. Exact IDs, commands, module hashes and copied test sources are archived.

Preservation: 855 previously tracked files match c088775 byte for byte, except permitted plan/manifest updates. Original build receipt comparisons and complete post-run native verification pass.

Core audit counters (fresh query replay is separate from recorded arithmetic, generation provenance and original native PLN):

```json
{
  "admitted_goal_predicate_replays": 1584,
  "authority_certificates": 3288,
  "closed_loop_pairs": 48,
  "development_allow_dirty": false,
  "episodes": 72,
  "executor_reconstructions": 72,
  "formula_calls": 180,
  "fresh_native_pln_invocations_during_audit": 0,
  "limitation": "Bounded structural/ancestry/fixture witness, physical recurrence and actual admitted-observation replay; native queries reexecuted separately from recorded formula checks; no fresh PLN invocation during audit, real-world truth or calibrated safety.",
  "native_audit": {
    "fresh_generation_integrity_checks_during_replay": 0,
    "fresh_strict_runtime_verifications": 1056,
    "matched_native_graph_reexecutions": 1056,
    "native_epochs": 1056,
    "native_query_reexecutions": 51520,
    "native_rows": 1056,
    "query_request_bytes": 10685640,
    "query_response_bytes": 7591632,
    "recorded_generation_checks": 24,
    "recorded_launch_mapping_checks": 528,
    "recorded_native_query_invocations": 51520,
    "recorded_query_answers": 51520
  },
  "native_formula_calls": 90,
  "physical_samples": 504,
  "physical_ticks": 648,
  "public_rows": 1584,
  "recorded_formula_checks": 180,
  "revision": "fa6c2674bc5977475f1aad9e6c884405ef7b7414",
  "selections": 972,
  "status": "PASS"
}
```

Operation statuses: `{'PASS': 936, 'UNKNOWN': 36}`. Expected UNKNOWN source answers preserve unresolved work; they are not harness errors.

All 17 deliberately altered copies were rejected by the frozen full auditor. These mutation replays use recorded query checks, not another fresh native query run.

- unsealed: audit differs: artifact s0-MH-scan-finite-two-hop/trace.jsonl
- phantom-intermediate: audit differs: unchanged FIFO selection
- wrong-premise-order: audit differs: unchanged FIFO selection
- copied-root-as-independent: audit differs: actual committed numerical record/roots
- stale-descendant-accepted: stale descendant stayed current
- hidden-adverse-estimate: audit differs: frozen work projection
- partial-depth-review-complete: audit differs: frozen work projection
- inference-as-physical-relief: numerical work manufactured relief
- replay-as-fresh-native: audit differs: no formula on reopen
- native-query-omission: audit differs: independent native query membership
- native-wrong-epoch: audit differs: native response epoch
- native-raw-response: audit differs: wire query header
- native-fallback-label: audit differs: no scan fallback
- generation-identity: audit differs: generation descriptor binding
- generation-mapped-digest: audit differs: mapped artifact digest
- generation-retry-erasure: audit differs: one generation attempt in ordinary core
- generation-view-binding: audit differs: whole episode native receipt inventory

Development logs remain in development/. Retained failures: unavailable CPython seal names, test fault injection blocked by read-only alias-directory mode, host-loader receipt misclassification, a script PYTHONPATH error, and a diagnostic counter-name error. The corrected three-arm development audit passed 2,260 native query reexecutions and the final focused run passed 32 tests. No fixture, policy, limits or formula was tuned for timing. Some development runs overlapped and are excluded from paired timing claims.

Archive integrity, extracted recorded replay and corrupted-archive rejection are reported by the later publication receipt, avoiding circular self-binding. The original core audit reexecutes native queries; extracted replay checks recorded queries and arithmetic plus SQLite state, with zero fresh native queries or PLN.

Provenance clarification: the inherited consumer-revision label names the earlier work-loop consumer. PROVENANCE_NOTE.md and CONSUMER_PROVENANCE.json identify the actual unchanged multi-hop consumer and its verified file hash. The full sealed source manifest is authoritative; no frozen results were rewritten.
