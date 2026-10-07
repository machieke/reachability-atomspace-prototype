# Descriptive cost accounting

Inclusive nested timers overlap; each column/category is independently totaled across rows or episodes, never added to another inclusive timer.

| Quantity | MH-scan | MH-native |
|---|---:|---:|
| episodes | 12 | 12 |
| rows | 264 | 264 |
| formula_calls | 30 | 30 |
| fresh_native_pln_calls | 15 | 15 |
| epochs | 0 | 264 |
| frame_serialized_bytes | 42979322 | 42979322 |
| Total episode seconds | 71.913394 | 160.988507 |

| Timer (seconds, nested) | MH-scan | MH-native |
|---|---:|---:|
| consumer.frontier_nested_ns | 1.444050 | 1.325928 |
| consumer.selection_inclusive_ns | 2.005625 | 1.884925 |
| environment.effect_link_ns | 0.012091 | 0.012195 |
| environment.guard_ns | 0.172649 | 0.364783 |
| environment.independent_dependency_check_ns | 0.101989 | 0.104915 |
| environment.measurement_ns | 0.022024 | 0.022600 |
| environment.output_serialization_ns | 1.486548 | 1.811371 |
| environment.publication_ns | 5.321175 | 6.002209 |
| environment.world_transition_ns | 0.001626 | 0.001687 |
| observation.acquisition.inventory_and_state_acquisition_ns | 1.647806 | 1.681141 |
| observation.acquisition.snapshot_acquisition_ns | 1.903315 | 1.972113 |
| observation.acquisition.total_acquisition_ns | 5.469425 | 5.403614 |
| observation.evaluation.A.applicability_classification_ns | 0.000837 | 0.000832 |
| observation.evaluation.A.complete_evidence_scan_ns | 0.026434 | 0.026366 |
| observation.evaluation.A.policy_evaluation_ns | 0.001591 | 0.001582 |
| observation.evaluation.A.total_evaluation_ns | 0.418796 | 0.557265 |
| observation.evaluation.A.witness_recording_ns | 0.168549 | 0.165472 |
| observation.evaluation.B.applicability_classification_ns | 0.000757 | 0.000723 |
| observation.evaluation.B.complete_evidence_scan_ns | 0.024764 | 0.024085 |
| observation.evaluation.B.policy_evaluation_ns | 0.002717 | 0.002674 |
| observation.evaluation.B.total_evaluation_ns | 0.653338 | 0.508021 |
| observation.evaluation.B.witness_recording_ns | 0.168892 | 0.164316 |
| observation.native_retrieval.costs.epoch_replacement_inclusive_ns | 0.000000 | 74.208511 |
| observation.native_retrieval.costs.native_build_verification_ns | 0.000000 | 54.432357 |
| observation.native_retrieval.costs.native_load_and_readback_io_ns | 0.000000 | 8.197374 |
| observation.native_retrieval.costs.native_query_inclusive_ns | 0.000000 | 1.076823 |
| observation.native_retrieval.costs.native_startup_ns | 0.000000 | 3.806418 |
| observation.native_retrieval.costs.projection_construction_ns | 0.000000 | 5.633308 |
| observation.native_retrieval.costs.projection_snapshot_serialization_ns | 0.000000 | 1.693415 |
| observation.native_retrieval.costs.projection_wire_ns | 0.000000 | 0.515206 |
| observation.native_retrieval.costs.readback_validation_ns | 0.000000 | 1.926841 |
| observation.native_retrieval.costs.view_open_inclusive_ns | 0.000000 | 77.290405 |
| observation.native_retrieval.python_traversal_tuples_serialization_ns | 0.000000 | 3.351856 |
| observation.native_retrieval.query_and_decode_inclusive_ns | 0.000000 | 2.233268 |
| observation.native_retrieval.view_open_inclusive_ns | 0.000000 | 77.333023 |
| observation.observation_inclusive_ns | 13.388171 | 99.783033 |
| observation.projection.base.discovery_and_graph_ns | 0.083216 | 0.080805 |
| observation.projection.base.frozen_assessment_revalidation_ns | 1.052991 | 1.371864 |
| observation.projection.base.serialization_ns | 0.374075 | 0.375475 |
| observation.projection.base.total_projection_ns | 3.029519 | 3.346608 |
| observation.projection.dependency_discovery_ns | 0.602254 | 82.918147 |
| observation.projection.total_projection_ns | 4.757733 | 87.421113 |
| revalidation.elapsed_ns | 2.125769 | 2.181680 |
| session.acquisition_inclusive_ns | 12.943590 | 13.211551 |
| session.authority_reopen_ns | 1.101870 | 1.140711 |
| session.completion_ns | 0.394698 | 0.312907 |
| session.descriptor_snapshot_inclusive_ns | 5.415139 | 5.457439 |
| session.dispatch_ns | 0.248621 | 0.344158 |
| session.execution_enumeration_ns | 0.733897 | 0.752864 |
| session.execution_gate_reservation_ns | 0.348376 | 0.370914 |
| session.execution_total_ns | 23.530678 | 23.997311 |
| session.failed_attempt_inclusive_ns | 0.112538 | 0.126951 |
| session.goal_accounting_ns | 3.098576 | 3.191805 |
| session.inference_inclusive_ns | 1.995644 | 2.130877 |
| session.monitor_ns | 12.793158 | 13.018446 |
| session.numeric_commit_ns | 1.429026 | 1.403721 |
| session.postcheck_ns | 1.617467 | 1.531012 |
| session.precheck_ns | 1.265328 | 1.362212 |
| session.projection_ns | 3.611132 | 3.566743 |
| session.public_read_ns | 5.390539 | 5.432582 |
| session.recall_snapshot_inclusive_ns | 6.288922 | 6.318358 |
| session.report_ingestion_ns | 0.147805 | 0.190058 |
| session.runtime_ns | 1.863208 | 1.995962 |
| session.runtime_reference_check_ns | 0.002210 | 0.002265 |
| session.selected_adopt_inclusive_ns | 0.779331 | 0.721941 |
| session.selected_complete_inclusive_ns | 0.831654 | 0.771799 |
| session.selected_deduction_inclusive_ns | 4.678193 | 4.958958 |
| session.selected_dispatch_inclusive_ns | 0.520655 | 0.600464 |
| session.selected_request_inclusive_ns | 18.255912 | 18.497723 |
| session.selected_reserve_inclusive_ns | 0.596323 | 0.633885 |
| session.setup_ns | 0.939684 | 0.912921 |

Cohort elapsed excludes source-copy/build preflight. Episode elapsed includes per-view build checks/cold replacements, real authority/formula/world work and local reconstruction; no throughput significance.

Unmeasured: isolated fsync, isolated native arithmetic within subprocess runtime, RSS, peak memory, native process memory, serialization copies, physical sensor latency, production decision quality, physical real-world latency or calibrated probability.

Whole snapshots are loaded. Neither short native responses nor same-binding reuse establishes bounded total memory or realistic warm-workload performance. Logical time does not advance with wall-clock computation.

Native-minus-scan episode wall time: 0 favorable, 0 neutral, 12 unfavorable. All 12 physical/recognized loss comparisons are neutral. This is one serial descriptive pass, not timing significance.
