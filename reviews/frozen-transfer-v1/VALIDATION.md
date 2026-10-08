# Validation, omissions and source identities

Frozen source `c28a7dce95f446a6e2590c1910a9e7c1fe6d423a`. Default and native regression groups ran once at this source, serially before the 24 new executions. This validates the new input/evaluator plumbing against retained contracts; it does not rerun the earlier payload frozen revision or its timing matrix.

| Suite | Passed / run | Errors | Failures | Skips | Seconds |
|---|---:|---:|---:|---:|---:|
| default | 485 / 485 | 0 | 0 | 0 | 339.524907 |
| native | 154 / 154 | 0 | 0 | 0 | 252.666786 |

Omitted: 648 tests in 47 tests modules. Exact IDs and rationale are in validation/inventory.json.

Omitted: 75 tests in 12 integration_tests modules. Exact IDs and rationale are in validation/inventory.json.

Also omitted: 15 standalone pressure checks and earlier full-cohort mutation, runtime-lifetime and compact-payload matrices. Historical results remain historical. The compact implementation and its focused tests are preserved; this new experiment uses full-session native recall. No larger-scale, memory, probability calibration or alternate cognitive-controller claims were tested.

Preservation: 926 earlier tracked files match d50baa1, except authorized plan/manifest updates. Both build receipts match the payload study and complete post-run build verification passes. The actual consumer is `experimental_multihop/consumer.py`, introduced at `b509d2b8d7388a570b5a666e1c845b95d207ad20`, SHA256 `3ec9c16ed98f2aff48a0db15b88d9c368edc4cdcb133a9789dff6ed96b68c19a`. Publication and measured-source identities are distinct.

BASELINE.json was recorded before implementation. Its advisory-policy/formula/controller/world/capture/backend identities and whole-repository baseline are retained. Explicit live-policy file paths were subsequently expanded from the same unchanged d50baa1 source, before any measured parent ran; this timing is recorded rather than backdated.

Development: nine static checks passed, including all twelve primitive-input adapters without constructing a consumer or executing numerical derivations. The only controller smoke cases were familiar two-hop and adverse examples, once per arm (four total). First parity checks exposed an authority-specific goal fingerprint and review ordering by opaque node hashes; the evaluator now normalizes that named binding and sorts review inventory by complete producer content. The original failure logs remain. The positive smoke runs were reused, not repeated, and the negative smoke plus corrected query audit passed. No new parent was used for tuning.

Full audit counters:

```json
{
  "admitted_goal_predicate_replays": 518,
  "authority_certificates": 1130,
  "closed_loop_pairs": 12,
  "development_allow_dirty": false,
  "episodes": 24,
  "executor_reconstructions": 24,
  "formula_calls": 104,
  "fresh_native_pln_invocations_during_audit": 0,
  "limitation": "Bounded structural/ancestry/fixture witness, physical recurrence and actual admitted-observation replay; native queries reexecuted separately from recorded formula checks; no fresh PLN invocation during audit, real-world truth or calibrated safety.",
  "native_audit": {
    "fresh_session_preparations": 12,
    "matched_native_graph_reexecutions": 259,
    "native_epochs": 259,
    "native_query_reexecutions": 15635,
    "native_rows": 259,
    "original_closed_generations_reverified": 0,
    "query_request_bytes": 3228988,
    "query_response_bytes": 2403126,
    "recorded_generation_checks": 12,
    "recorded_launch_mapping_checks": 259,
    "recorded_native_query_invocations": 15635,
    "recorded_query_answers": 15635
  },
  "native_formula_calls": 104,
  "physical_samples": 118,
  "physical_ticks": 216,
  "public_rows": 518,
  "recorded_formula_checks": 104,
  "revision": "c28a7dce95f446a6e2590c1910a9e7c1fe6d423a",
  "selections": 312,
  "status": "PASS"
}
```

Cross-arm normalization is explicitly enumerated in parity.json. It removes per-authority identities/bindings and elapsed timers; selected premise IDs, values, policies, ordered candidate applications, priority/age, budgets and certificate check contents remain. Each authority binding and all certificates are separately checked against its actual SQLite state.

Conformance does not require every source to be available or every task to finish. Every rejected/stale operation, unresolved role, incomplete capture/query, unsupported scope, original rule/application and physical/recognized mismatch remains in traces. Local formula checks and fixture witnesses do not establish a global probabilistic model for later adverse assessments.

The original full-session native generation and its query guards are unchanged. Audit-created sessions are counted separately from original recorded generation provenance; original closed memfds are not reverified by extracted replay. Archive checks appear in a later publication receipt.
