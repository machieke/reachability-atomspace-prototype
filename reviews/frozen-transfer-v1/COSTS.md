# Frozen transfer costs

Inclusive nested timers overlap; each column/category is independently totaled across rows or episodes, never added to another inclusive timer.

| Quantity | TRANSFER-scan | TRANSFER-native |
|---|---:|---:|
| episodes | 12 | 12 |
| rows | 259 | 259 |
| formula_calls | 52 | 52 |
| fresh_native_pln_calls | 52 | 52 |
| epochs | 0 | 259 |
| frame_serialized_bytes | 46414516 | 46414516 |
| Total episode seconds | 83.003540 | 131.041007 |

## Payload quantities

StringValue content is logical payload, not RSS; readback bytes are derived from the fully validated native wire grammar. The native arm retains the existing accounting work; scan costs are reported separately.

| Quantity | TRANSFER-scan | TRANSFER-native |
|---|---:|---:|
| emitted_atom_commands | 0 | 792666 |
| envelope_bytes | 0 | 0 |
| metadata_key_atoms | 0 | 3154 |
| metadata_value_content_bytes | 0 | 39730795 |
| metadata_values | 0 | 3154 |
| native_atoms | 0 | 293926 |
| native_float_value_scalars | 0 | 15392 |
| native_load_wire_bytes | 0 | 136484929 |
| native_readback_wire_bytes | 0 | 143565397 |
| native_string_value_content_bytes | 0 | 50655611 |
| native_values | 0 | 39520 |
| public_export_bytes | 0 | 39703230 |
| source_payload_bytes | 0 | 10857364 |
| source_records | 0 | 7669 |
| whole_snapshot_chunk_bytes | 0 | 39703230 |

## Disjoint coarse phases

| Seconds | TRANSFER-scan | TRANSFER-native |
|---|---:|---:|
| execution_ns | 29.167867 | 29.130849 |
| final_output_cleanup_ns | 0.633820 | 1.550699 |
| observation_excluding_preparation_ns | 13.711930 | 55.752289 |
| remaining_setup_world_accounting_reconstruction_ns | 35.535793 | 35.064393 |
| runtime_preparation_ns | 0.000000 | 5.500524 |
| selection_ns | 2.307574 | 2.111212 |
| trace_logging_ns | 1.646555 | 1.931041 |

## Nested detailed timers

| Seconds | TRANSFER-scan | TRANSFER-native |
|---|---:|---:|
| consumer.frontier_nested_ns | 1.498616 | 1.276971 |
| consumer.selection_inclusive_ns | 2.287498 | 2.090087 |
| environment.effect_link_ns | 0.009448 | 0.009911 |
| environment.guard_ns | 0.323123 | 0.181654 |
| environment.independent_dependency_check_ns | 0.122221 | 0.113940 |
| environment.measurement_ns | 0.014358 | 0.013995 |
| environment.output_serialization_ns | 1.576599 | 1.851619 |
| environment.publication_ns | 5.607792 | 5.942000 |
| environment.world_transition_ns | 0.001636 | 0.001566 |
| observation.acquisition.inventory_and_state_acquisition_ns | 1.548336 | 1.548538 |
| observation.acquisition.snapshot_acquisition_ns | 2.100193 | 2.137559 |
| observation.acquisition.total_acquisition_ns | 5.518092 | 5.533951 |
| observation.evaluation.A.applicability_classification_ns | 0.001007 | 0.000990 |
| observation.evaluation.A.complete_evidence_scan_ns | 0.028695 | 0.029315 |
| observation.evaluation.A.policy_evaluation_ns | 0.001585 | 0.001591 |
| observation.evaluation.A.total_evaluation_ns | 0.477341 | 0.504328 |
| observation.evaluation.A.witness_recording_ns | 0.181503 | 0.182767 |
| observation.evaluation.B.applicability_classification_ns | 0.000896 | 0.000896 |
| observation.evaluation.B.complete_evidence_scan_ns | 0.084963 | 0.027490 |
| observation.evaluation.B.policy_evaluation_ns | 0.002872 | 0.002825 |
| observation.evaluation.B.total_evaluation_ns | 0.619568 | 0.495047 |
| observation.evaluation.B.witness_recording_ns | 0.182251 | 0.184244 |
| observation.native_retrieval.costs.epoch_replacement_inclusive_ns | 0.000000 | 25.365233 |
| observation.native_retrieval.costs.native_load_and_readback_io_ns | 0.000000 | 10.080297 |
| observation.native_retrieval.costs.native_query_inclusive_ns | 0.000000 | 1.602211 |
| observation.native_retrieval.costs.native_startup_ns | 0.000000 | 3.812660 |
| observation.native_retrieval.costs.projection_construction_ns | 0.000000 | 6.341528 |
| observation.native_retrieval.costs.projection_snapshot_serialization_ns | 0.000000 | 1.831838 |
| observation.native_retrieval.costs.projection_wire_ns | 0.000000 | 0.622982 |
| observation.native_retrieval.costs.readback_validation_ns | 0.000000 | 2.282677 |
| observation.native_retrieval.costs.runtime_preparation_and_guard_ns | 0.000000 | 10.693519 |
| observation.native_retrieval.costs.view_open_inclusive_ns | 0.000000 | 31.661298 |
| observation.native_retrieval.python_traversal_tuples_serialization_ns | 0.000000 | 3.496214 |
| observation.native_retrieval.query_and_decode_inclusive_ns | 0.000000 | 7.966654 |
| observation.native_retrieval.view_open_inclusive_ns | 0.000000 | 31.704713 |
| observation.observation_inclusive_ns | 13.706046 | 61.243878 |
| observation.payload.accounting_ns | 0.000000 | 0.742493 |
| observation.projection.base.discovery_and_graph_ns | 0.097845 | 0.097516 |
| observation.projection.base.frozen_assessment_revalidation_ns | 1.311042 | 1.718326 |
| observation.projection.base.serialization_ns | 0.370208 | 0.373850 |
| observation.projection.base.total_projection_ns | 3.394706 | 3.757854 |
| observation.projection.dependency_discovery_ns | 0.682806 | 43.167581 |
| observation.projection.total_projection_ns | 5.119120 | 47.940509 |
| revalidation.elapsed_ns | 2.238198 | 2.136476 |
| runtime.cleanup_ns | 0.000000 | 0.078597 |
| runtime.copy_ns | 0.000000 | 0.504977 |
| runtime.integrity_checks_ns | 0.000000 | 5.350534 |
| runtime.loaded_mapping_checks_ns | 0.000000 | 0.293986 |
| runtime.loader_resolution_ns | 0.000000 | 0.056738 |
| runtime.original_verification_ns | 0.000000 | 2.463619 |
| runtime.preparation_inclusive_ns | 0.000000 | 5.500524 |
| runtime.sealed_hash_ns | 0.000000 | 2.392512 |
| session.acquisition_inclusive_ns | 9.084070 | 9.464431 |
| session.authority_reopen_ns | 1.345097 | 1.279513 |
| session.completion_ns | 0.258965 | 0.298542 |
| session.descriptor_snapshot_inclusive_ns | 4.618249 | 4.645018 |
| session.dispatch_ns | 0.273585 | 0.315434 |
| session.execution_enumeration_ns | 0.808278 | 0.725824 |
| session.execution_gate_reservation_ns | 0.399864 | 0.416015 |
| session.execution_total_ns | 26.924423 | 26.988992 |
| session.failed_attempt_inclusive_ns | 0.407764 | 0.276916 |
| session.goal_accounting_ns | 2.975473 | 2.923190 |
| session.inference_inclusive_ns | 6.851926 | 6.789942 |
| session.monitor_ns | 8.907793 | 9.244456 |
| session.numeric_commit_ns | 2.424941 | 2.432758 |
| session.postcheck_ns | 2.928563 | 2.827823 |
| session.precheck_ns | 2.202494 | 2.112993 |
| session.projection_ns | 7.196921 | 7.017077 |
| session.public_read_ns | 4.594966 | 4.621268 |
| session.recall_snapshot_inclusive_ns | 5.178494 | 5.370306 |
| session.report_ingestion_ns | 0.175131 | 0.218788 |
| session.runtime_ns | 6.617675 | 6.568924 |
| session.runtime_reference_check_ns | 0.007648 | 0.007353 |
| session.selected_adopt_inclusive_ns | 1.130949 | 1.207787 |
| session.selected_complete_inclusive_ns | 0.603048 | 0.637728 |
| session.selected_deduction_inclusive_ns | 12.892730 | 12.848608 |
| session.selected_dispatch_inclusive_ns | 0.587914 | 0.591986 |
| session.selected_request_inclusive_ns | 13.288882 | 13.181884 |
| session.selected_reserve_inclusive_ns | 0.664345 | 0.662856 |
| session.setup_ns | 0.977183 | 0.941276 |

Cohort elapsed excludes source-copy/build preflight. Episode elapsed includes per-view build checks/cold replacements, real authority/formula/world work and local reconstruction; no throughput significance.

Unmeasured: isolated fsync, isolated native arithmetic within subprocess runtime, RSS, peak memory, native process memory, serialization copies, physical sensor latency, production decision quality, physical real-world latency or calibrated probability.

Every changed binding remains a cold view load. Sealed bytes staged are not RSS. Logical time does not advance with wall-clock computation.

## Command boundaries

- summed_episode_ns: 214.044546 seconds.
- driver_ns: 220.026921 seconds.
- comparison_wrapper_ns: 239.076345 seconds.

The wrapper includes source checks/copies, preflight, aggregation and sealing. Episode time includes capture, full assessment/frontier work, original runtime generation/guards, inference/certification/persistence, world/monitoring, trace output and cleanup. Reference checks remain paid in residual accounting. The driver includes per-episode outcome extraction; its timer ends before the final cross-arm parity and cost aggregation. Those later operations are included in the wrapper. Inclusive nested timers overlap and are not added. Logical simulation time does not advance with processing time.

RSS, peak/native process memory, isolated fsync, isolated native arithmetic inside its subprocess, physical sensor latency, real-world response time and calibrated probability are unmeasured. Logical value content, hex-encoded wire data and compressed publication size are different quantities. No further timing sweep or significance test was run.
