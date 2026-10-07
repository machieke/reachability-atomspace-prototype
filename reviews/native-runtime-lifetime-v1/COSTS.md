# Runtime lifetime costs

Inclusive nested timers overlap; each column/category is independently totaled across rows or episodes, never added to another inclusive timer.

| Quantity | MH-scan | MH-native-strict | MH-native-session |
|---|---:|---:|---:|
| episodes | 24 | 24 | 24 |
| rows | 528 | 528 | 528 |
| formula_calls | 60 | 60 | 60 |
| fresh_native_pln_calls | 30 | 30 | 30 |
| epochs | 0 | 528 | 528 |
| frame_serialized_bytes | 85958644 | 85958644 | 85958644 |
| Total episode seconds | 145.109862 | 322.242694 | 234.062324 |

## Disjoint coarse phases

| Seconds | MH-scan | MH-native-strict | MH-native-session |
|---|---:|---:|---:|
| execution_ns | 51.561488 | 53.716214 | 52.216974 |
| final_output_cleanup_ns | 1.348172 | 2.468235 | 3.032979 |
| observation_excluding_preparation_ns | 26.839764 | 197.827277 | 101.306446 |
| remaining_setup_world_accounting_reconstruction_ns | 57.891190 | 60.189859 | 58.955897 |
| runtime_preparation_ns | 0.000000 | 0.000000 | 10.964941 |
| selection_ns | 4.109278 | 4.209341 | 3.769636 |
| trace_logging_ns | 3.359971 | 3.831767 | 3.815450 |

## Nested detailed timers

| Seconds | MH-scan | MH-native-strict | MH-native-session |
|---|---:|---:|---:|
| consumer.frontier_nested_ns | 2.776716 | 2.954782 | 2.750960 |
| consumer.selection_inclusive_ns | 4.070993 | 4.167692 | 3.728909 |
| environment.effect_link_ns | 0.023524 | 0.024221 | 0.024271 |
| environment.guard_ns | 0.345276 | 0.350955 | 0.463800 |
| environment.independent_dependency_check_ns | 0.208660 | 0.203997 | 0.307644 |
| environment.measurement_ns | 0.042428 | 0.042695 | 0.042079 |
| environment.output_serialization_ns | 3.227757 | 3.682154 | 3.666400 |
| environment.publication_ns | 11.493087 | 12.011859 | 11.026894 |
| environment.world_transition_ns | 0.003132 | 0.003142 | 0.003180 |
| observation.acquisition.inventory_and_state_acquisition_ns | 3.300659 | 3.073613 | 3.334958 |
| observation.acquisition.snapshot_acquisition_ns | 3.954994 | 4.075642 | 3.969002 |
| observation.acquisition.total_acquisition_ns | 10.756104 | 10.917501 | 11.091290 |
| observation.evaluation.A.applicability_classification_ns | 0.001585 | 0.001594 | 0.001573 |
| observation.evaluation.A.complete_evidence_scan_ns | 0.051697 | 0.052101 | 0.051213 |
| observation.evaluation.A.policy_evaluation_ns | 0.003425 | 0.003268 | 0.003332 |
| observation.evaluation.A.total_evaluation_ns | 0.968097 | 1.377854 | 0.756582 |
| observation.evaluation.A.witness_recording_ns | 0.327738 | 0.328558 | 0.328246 |
| observation.evaluation.B.applicability_classification_ns | 0.001447 | 0.001393 | 0.001394 |
| observation.evaluation.B.complete_evidence_scan_ns | 0.048426 | 0.048220 | 0.047527 |
| observation.evaluation.B.policy_evaluation_ns | 0.005731 | 0.005571 | 0.005599 |
| observation.evaluation.B.total_evaluation_ns | 1.087807 | 0.826102 | 0.836686 |
| observation.evaluation.B.witness_recording_ns | 0.329953 | 0.326867 | 0.325404 |
| observation.native_retrieval.costs.epoch_replacement_inclusive_ns | 0.000000 | 147.295139 | 46.699984 |
| observation.native_retrieval.costs.native_build_verification_ns | 0.000000 | 107.068837 | 0.000000 |
| observation.native_retrieval.costs.native_load_and_readback_io_ns | 0.000000 | 16.823835 | 17.687855 |
| observation.native_retrieval.costs.native_query_inclusive_ns | 0.000000 | 2.243298 | 2.747351 |
| observation.native_retrieval.costs.native_startup_ns | 0.000000 | 7.639735 | 7.893704 |
| observation.native_retrieval.costs.projection_construction_ns | 0.000000 | 11.199100 | 11.194072 |
| observation.native_retrieval.costs.projection_snapshot_serialization_ns | 0.000000 | 3.493604 | 3.505713 |
| observation.native_retrieval.costs.projection_wire_ns | 0.000000 | 1.024829 | 1.044949 |
| observation.native_retrieval.costs.readback_validation_ns | 0.000000 | 4.111559 | 4.293260 |
| observation.native_retrieval.costs.runtime_preparation_and_guard_ns | 0.000000 | 0.000000 | 20.244075 |
| observation.native_retrieval.costs.view_open_inclusive_ns | 0.000000 | 153.599543 | 59.235902 |
| observation.native_retrieval.python_traversal_tuples_serialization_ns | 0.000000 | 6.153831 | 5.991184 |
| observation.native_retrieval.query_and_decode_inclusive_ns | 0.000000 | 4.599857 | 13.932123 |
| observation.native_retrieval.view_open_inclusive_ns | 0.000000 | 153.680406 | 59.317820 |
| observation.observation_inclusive_ns | 26.827511 | 197.816608 | 112.260715 |
| observation.projection.base.discovery_and_graph_ns | 0.160671 | 0.158312 | 0.159486 |
| observation.projection.base.frozen_assessment_revalidation_ns | 2.370484 | 2.009976 | 2.464810 |
| observation.projection.base.serialization_ns | 0.740315 | 0.735529 | 0.736699 |
| observation.projection.base.total_projection_ns | 6.373619 | 5.887214 | 6.388405 |
| observation.projection.dependency_discovery_ns | 1.192589 | 164.434094 | 79.241128 |
| observation.projection.total_projection_ns | 9.875869 | 172.287285 | 88.060080 |
| revalidation.elapsed_ns | 4.629672 | 4.369117 | 4.270640 |
| runtime.cleanup_ns | 0.000000 | 0.000000 | 0.164031 |
| runtime.copy_ns | 0.000000 | 0.000000 | 1.036588 |
| runtime.integrity_checks_ns | 0.000000 | 0.000000 | 9.619105 |
| runtime.loaded_mapping_checks_ns | 0.000000 | 0.000000 | 0.601565 |
| runtime.loader_resolution_ns | 0.000000 | 0.000000 | 0.115005 |
| runtime.original_verification_ns | 0.000000 | 0.000000 | 4.876451 |
| runtime.preparation_inclusive_ns | 0.000000 | 0.000000 | 10.964941 |
| runtime.sealed_hash_ns | 0.000000 | 0.000000 | 4.767833 |
| session.acquisition_inclusive_ns | 26.158467 | 27.320548 | 26.599152 |
| session.authority_reopen_ns | 2.252523 | 2.305467 | 2.402325 |
| session.completion_ns | 0.833234 | 0.711680 | 0.742234 |
| session.descriptor_snapshot_inclusive_ns | 11.136694 | 11.087920 | 10.949052 |
| session.dispatch_ns | 0.635011 | 0.620804 | 0.586453 |
| session.execution_enumeration_ns | 1.465708 | 1.515378 | 1.372600 |
| session.execution_gate_reservation_ns | 0.921374 | 0.811207 | 0.773847 |
| session.execution_total_ns | 46.921036 | 49.336289 | 47.935754 |
| session.failed_attempt_inclusive_ns | 0.233956 | 0.253238 | 0.257154 |
| session.goal_accounting_ns | 6.133320 | 6.366008 | 6.417681 |
| session.inference_inclusive_ns | 4.071412 | 4.240725 | 4.052930 |
| session.monitor_ns | 25.786041 | 26.852489 | 26.099544 |
| session.numeric_commit_ns | 3.018222 | 3.030511 | 2.963994 |
| session.postcheck_ns | 3.097674 | 3.336757 | 3.223022 |
| session.precheck_ns | 2.385615 | 2.919354 | 2.633197 |
| session.projection_ns | 7.018151 | 7.015697 | 7.041632 |
| session.public_read_ns | 11.088222 | 11.038741 | 10.900301 |
| session.recall_snapshot_inclusive_ns | 12.726195 | 13.105497 | 12.711820 |
| session.report_ingestion_ns | 0.367318 | 0.462889 | 0.494573 |
| session.runtime_ns | 3.827092 | 3.955792 | 3.777737 |
| session.runtime_reference_check_ns | 0.004232 | 0.004239 | 0.004196 |
| session.selected_adopt_inclusive_ns | 1.431431 | 1.699185 | 1.473631 |
| session.selected_complete_inclusive_ns | 1.750893 | 1.550697 | 1.597129 |
| session.selected_deduction_inclusive_ns | 9.200840 | 9.915542 | 9.751176 |
| session.selected_dispatch_inclusive_ns | 1.166666 | 1.197237 | 1.460687 |
| session.selected_request_inclusive_ns | 36.579902 | 37.998124 | 36.640252 |
| session.selected_reserve_inclusive_ns | 1.431756 | 1.355429 | 1.294100 |
| session.setup_ns | 1.838055 | 1.820381 | 1.868774 |

Cohort elapsed excludes source-copy/build preflight. Episode elapsed includes per-view build checks/cold replacements, real authority/formula/world work and local reconstruction; no throughput significance.

Unmeasured: isolated fsync, isolated native arithmetic within subprocess runtime, RSS, peak memory, native process memory, serialization copies, physical sensor latency, production decision quality, physical real-world latency or calibrated probability.

Whole snapshots remain cold loads. Sealed bytes staged are not RSS. Logical time does not advance with wall-clock computation.

## End-to-end boundaries

- summed_episode_elapsed_ns: 701.414880 seconds.
- cohort_driver_elapsed_ns: 704.626498 seconds.
- comparison_command_wrapper_ns: 727.245154 seconds.

The command wrapper includes source checks/copies, build preflight, final cost aggregation, sealing and interpreter startup. Episode time includes runtime preparation, all native views/guards, world/authority work, trace writes and cleanup; final result-envelope writes are charged by the outer driver/wrapper. Detailed nested timers are not added to coarse categories.

## Separate fixed-snapshot diagnostic

One snapshot is observed three times, then logical time changes once. This is attribution evidence, not additional independent tasks or an optimized workload.

| Arm | Pass | Cold epoch | Observation seconds | Actual native queries |
|---|---:|---:|---:|---:|
| MH-native-strict | 0 | 1 | 0.290744 | 41 |
| MH-native-strict | 1 | 1 | 0.048793 | 41 |
| MH-native-strict | 2 | 1 | 0.037065 | 41 |
| MH-native-strict | 3 | 2 | 0.296480 | 41 |
| MH-native-session | 0 | 1 | 0.552948 | 41 |
| MH-native-session | 1 | 1 | 0.041335 | 41 |
| MH-native-session | 2 | 1 | 0.041706 | 41 |
| MH-native-session | 3 | 2 | 0.117101 | 41 |

Passes 0–2 have one exact binding and one PID per arm. Pass 3 has a changed binding and new PID. The session generation ID stays the same. Actual query passes are issued every time. Diagnostic cleanup is recorded in its generation receipt; these observation times are not total episode times.

Episode-directory creation occurs before the episode timer and is included in the driver/wrapper. Independent end-of-episode reference checks remain charged in residual accounting, as in the original harness. Original receipt verification, sealed-content hashing, copying and launch guards are distinct nested categories; their durations are not predictions of exact wall-time savings.
