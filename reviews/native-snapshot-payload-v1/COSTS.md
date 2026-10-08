# Snapshot payload costs

Inclusive nested timers overlap; each column/category is independently totaled across rows or episodes, never added to another inclusive timer.

| Quantity | MH-scan | MH-native-session-full | MH-native-session-compact |
|---|---:|---:|---:|
| episodes | 24 | 24 | 24 |
| rows | 528 | 528 | 528 |
| formula_calls | 60 | 60 | 60 |
| fresh_native_pln_calls | 30 | 30 | 30 |
| epochs | 0 | 528 | 528 |
| frame_serialized_bytes | 85958644 | 85958644 | 85958644 |
| Total episode seconds | 149.839596 | 241.020144 | 241.274257 |

## Payload quantities

StringValue content is logical payload, not RSS; readback bytes are derived from the fully validated native wire grammar. Both native arms pay the same additional accounting work.

| Quantity | MH-scan | MH-native-session-full | MH-native-session-compact |
|---|---:|---:|---:|
| emitted_atom_commands | 0 | 1286212 | 1284160 |
| envelope_bytes | 0 | 0 | 230060 |
| metadata_key_atoms | 0 | 6276 | 4224 |
| metadata_value_content_bytes | 0 | 76059272 | 286316 |
| metadata_values | 0 | 6276 | 4224 |
| native_atoms | 0 | 502604 | 500552 |
| native_float_value_scalars | 0 | 25264 | 25264 |
| native_load_wire_bytes | 0 | 241104212 | 89477548 |
| native_readback_wire_bytes | 0 | 252583480 | 100938588 |
| native_string_value_content_bytes | 0 | 92508412 | 16735456 |
| native_values | 0 | 65228 | 63176 |
| public_export_bytes | 0 | 76003016 | 76003016 |
| source_payload_bytes | 0 | 16342128 | 16342128 |
| source_records | 0 | 12048 | 12048 |
| whole_snapshot_chunk_bytes | 0 | 76003016 | 0 |

## Disjoint coarse phases

| Seconds | MH-scan | MH-native-session-full | MH-native-session-compact |
|---|---:|---:|---:|
| execution_ns | 52.893969 | 54.809869 | 55.042550 |
| final_output_cleanup_ns | 1.516271 | 3.185632 | 2.996687 |
| observation_excluding_preparation_ns | 27.305145 | 104.223429 | 102.787761 |
| remaining_setup_world_accounting_reconstruction_ns | 60.658691 | 59.597343 | 60.770962 |
| runtime_preparation_ns | 0.000000 | 11.096479 | 11.446642 |
| selection_ns | 4.041472 | 4.211219 | 4.297711 |
| trace_logging_ns | 3.424049 | 3.896172 | 3.931945 |

## Nested detailed timers

| Seconds | MH-scan | MH-native-session-full | MH-native-session-compact |
|---|---:|---:|---:|
| consumer.frontier_nested_ns | 2.996851 | 2.863820 | 3.080185 |
| consumer.selection_inclusive_ns | 4.001304 | 4.166708 | 4.253689 |
| environment.effect_link_ns | 0.024817 | 0.024958 | 0.025241 |
| environment.guard_ns | 0.358944 | 0.360388 | 0.353876 |
| environment.independent_dependency_check_ns | 0.206509 | 0.211065 | 0.209677 |
| environment.measurement_ns | 0.045512 | 0.046561 | 0.045030 |
| environment.output_serialization_ns | 3.291287 | 3.747537 | 3.781417 |
| environment.publication_ns | 11.941375 | 11.180253 | 11.902379 |
| environment.world_transition_ns | 0.003375 | 0.003362 | 0.003345 |
| observation.acquisition.inventory_and_state_acquisition_ns | 3.503749 | 3.328509 | 3.569606 |
| observation.acquisition.snapshot_acquisition_ns | 3.973471 | 4.162194 | 4.062933 |
| observation.acquisition.total_acquisition_ns | 11.182047 | 11.309263 | 11.573282 |
| observation.evaluation.A.applicability_classification_ns | 0.001673 | 0.001694 | 0.001630 |
| observation.evaluation.A.complete_evidence_scan_ns | 0.053985 | 0.053781 | 0.054199 |
| observation.evaluation.A.policy_evaluation_ns | 0.003364 | 0.003281 | 0.003359 |
| observation.evaluation.A.total_evaluation_ns | 0.785005 | 1.125774 | 1.049548 |
| observation.evaluation.A.witness_recording_ns | 0.337862 | 0.335082 | 0.336847 |
| observation.evaluation.B.applicability_classification_ns | 0.001532 | 0.001550 | 0.001480 |
| observation.evaluation.B.complete_evidence_scan_ns | 0.049975 | 0.050543 | 0.050007 |
| observation.evaluation.B.policy_evaluation_ns | 0.005509 | 0.005730 | 0.005668 |
| observation.evaluation.B.total_evaluation_ns | 0.763321 | 0.759033 | 0.846346 |
| observation.evaluation.B.witness_recording_ns | 0.333803 | 0.332214 | 0.337186 |
| observation.native_retrieval.costs.envelope_construction_ns | 0.000000 | 0.000000 | 0.013074 |
| observation.native_retrieval.costs.envelope_validation_inclusive_ns | 0.000000 | 0.000000 | 11.038699 |
| observation.native_retrieval.costs.epoch_replacement_inclusive_ns | 0.000000 | 47.119098 | 47.790297 |
| observation.native_retrieval.costs.native_load_and_readback_io_ns | 0.000000 | 17.543069 | 10.687762 |
| observation.native_retrieval.costs.native_query_inclusive_ns | 0.000000 | 2.726937 | 2.711828 |
| observation.native_retrieval.costs.native_startup_ns | 0.000000 | 7.679484 | 7.556195 |
| observation.native_retrieval.costs.projection_construction_ns | 0.000000 | 11.819170 | 10.967913 |
| observation.native_retrieval.costs.projection_snapshot_serialization_ns | 0.000000 | 3.775203 | 3.228061 |
| observation.native_retrieval.costs.projection_wire_ns | 0.000000 | 1.266037 | 1.039469 |
| observation.native_retrieval.costs.readback_validation_ns | 0.000000 | 4.226885 | 3.439604 |
| observation.native_retrieval.costs.runtime_preparation_and_guard_ns | 0.000000 | 20.533491 | 19.564972 |
| observation.native_retrieval.costs.snapshot_hash_ns | 0.000000 | 0.000000 | 0.143855 |
| observation.native_retrieval.costs.view_open_inclusive_ns | 0.000000 | 59.702684 | 60.854130 |
| observation.native_retrieval.python_traversal_tuples_serialization_ns | 0.000000 | 6.089118 | 5.745035 |
| observation.native_retrieval.query_and_decode_inclusive_ns | 0.000000 | 14.152367 | 12.423221 |
| observation.native_retrieval.view_open_inclusive_ns | 0.000000 | 59.786998 | 60.928604 |
| observation.observation_inclusive_ns | 27.292427 | 115.300990 | 114.217210 |
| observation.payload.accounting_ns | 0.000000 | 1.318424 | 1.213016 |
| observation.projection.base.discovery_and_graph_ns | 0.166090 | 0.163031 | 0.164611 |
| observation.projection.base.frozen_assessment_revalidation_ns | 2.632881 | 2.301372 | 2.503873 |
| observation.projection.base.serialization_ns | 0.773283 | 0.762551 | 0.769588 |
| observation.projection.base.total_projection_ns | 7.073282 | 6.430784 | 6.686460 |
| observation.projection.dependency_discovery_ns | 1.233997 | 80.028484 | 79.096860 |
| observation.projection.total_projection_ns | 10.482554 | 88.331083 | 87.797708 |
| revalidation.elapsed_ns | 4.598253 | 4.790731 | 4.215362 |
| runtime.cleanup_ns | 0.000000 | 0.173775 | 0.173543 |
| runtime.copy_ns | 0.000000 | 1.038992 | 1.061789 |
| runtime.integrity_checks_ns | 0.000000 | 9.788749 | 8.491577 |
| runtime.loaded_mapping_checks_ns | 0.000000 | 0.611096 | 0.618883 |
| runtime.loader_resolution_ns | 0.000000 | 0.134275 | 0.099268 |
| runtime.original_verification_ns | 0.000000 | 4.875420 | 5.101529 |
| runtime.preparation_inclusive_ns | 0.000000 | 11.096479 | 11.446642 |
| runtime.sealed_hash_ns | 0.000000 | 4.872577 | 5.002366 |
| session.acquisition_inclusive_ns | 27.526143 | 27.715938 | 28.015926 |
| session.authority_reopen_ns | 2.415953 | 2.390513 | 2.264535 |
| session.completion_ns | 0.658799 | 0.836519 | 0.744723 |
| session.descriptor_snapshot_inclusive_ns | 11.247145 | 11.262788 | 11.555012 |
| session.dispatch_ns | 0.564416 | 0.627304 | 0.596139 |
| session.execution_enumeration_ns | 1.664064 | 1.561070 | 1.543566 |
| session.execution_gate_reservation_ns | 0.695826 | 0.845744 | 0.725081 |
| session.execution_total_ns | 48.284736 | 50.008148 | 50.815941 |
| session.failed_attempt_inclusive_ns | 0.250876 | 0.340587 | 0.366864 |
| session.goal_accounting_ns | 6.241221 | 6.628173 | 7.044964 |
| session.inference_inclusive_ns | 4.136161 | 4.260985 | 4.144808 |
| session.monitor_ns | 27.185434 | 27.282794 | 27.538979 |
| session.numeric_commit_ns | 2.918124 | 2.926091 | 3.053080 |
| session.postcheck_ns | 3.172557 | 3.216921 | 3.349493 |
| session.precheck_ns | 2.505536 | 2.612632 | 2.686067 |
| session.projection_ns | 7.252291 | 7.154349 | 7.085889 |
| session.public_read_ns | 11.199087 | 11.214714 | 11.506305 |
| session.recall_snapshot_inclusive_ns | 13.102843 | 12.958213 | 13.709315 |
| session.report_ingestion_ns | 0.334775 | 0.427629 | 0.471768 |
| session.runtime_ns | 3.882829 | 3.992441 | 3.867585 |
| session.runtime_reference_check_ns | 0.003987 | 0.003866 | 0.004186 |
| session.selected_adopt_inclusive_ns | 1.546416 | 1.687042 | 1.925165 |
| session.selected_complete_inclusive_ns | 1.569123 | 1.692393 | 1.572930 |
| session.selected_deduction_inclusive_ns | 9.262466 | 9.724595 | 9.623852 |
| session.selected_dispatch_inclusive_ns | 1.185879 | 1.188769 | 1.181662 |
| session.selected_request_inclusive_ns | 38.142065 | 39.116078 | 39.469656 |
| session.selected_reserve_inclusive_ns | 1.188020 | 1.400992 | 1.269285 |
| session.setup_ns | 1.809832 | 1.893488 | 1.928997 |

Cohort elapsed excludes source-copy/build preflight. Episode elapsed includes per-view build checks/cold replacements, real authority/formula/world work and local reconstruction; no throughput significance.

Unmeasured: isolated fsync, isolated native arithmetic within subprocess runtime, RSS, peak memory, native process memory, serialization copies, physical sensor latency, production decision quality, physical real-world latency or calibrated probability.

Every changed binding remains a cold view load. Sealed bytes staged are not RSS. Logical time does not advance with wall-clock computation.

## End-to-end boundaries

- summed_episode_elapsed_ns: 632.133996 seconds.
- cohort_driver_elapsed_ns: 635.470179 seconds.
- comparison_command_wrapper_ns: 658.247494 seconds.

The wrapper includes source checks/copy, preflight, cost aggregation, sealing and interpreter startup. Episode time includes projection/runtime, all authority and world work, trace output and cleanup; final result writes belong to the outer driver/wrapper. Directory creation precedes the episode timer. Reference checks remain charged in residual time. Detailed nested timers overlap and are never summed together. Both native arms pay the same payload-accounting wrapper. Readback length is derived from actual validated graph values and the frozen C++ grammar, including hex encoding; tests compare actual captured output.

Logical StringValue content is the sum of retained native value payloads over epochs, not RSS or peak memory. Load/readback wire bytes include encoding; archive bytes include compression and are a separate publication property. Full export bytes and source payloads remain equal between native arms. Hash and envelope validation costs stay included. Logical time does not advance with computation, so equal loss does not imply equal real-time performance.

## Separate all-form diagnostic

- original: 408 paired requests, 816 actual native query invocations across both projections. Zero-query budgets are rejected locally.
- alternatives-model-opposition: 564 paired requests, 1128 actual native query invocations across both projections. Zero-query budgets are rejected locally.
- retired-model-and-source: 564 paired requests, 1128 actual native query invocations across both projections. Zero-query budgets are rejected locally.

The diagnostic is semantic boundary evidence only; its costs are outside core timings and its wrapper time is archived. No new independent tasks or PLN calls are added.

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
