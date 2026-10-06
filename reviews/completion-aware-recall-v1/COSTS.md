# Cost inventory and interpretation

The archive retains raw nanosecond fields per run, native query receipts, event
positions, source/backing sizes, buffer/workspace peaks and publication summaries.
Timing is one balanced/interleaved pass under concurrent regression load. It is
descriptive, without replication or uncertainty intervals. No benchmark retuning
or coefficient search was performed.

| Category | Recorded field(s) | Relationship |
|---|---|---|
| Whole episode | `elapsed_ns` | Includes setup, decisions, selected execution, evaluator callbacks, serialization and reopen verification; excludes cohort source copying and later semantic audit |
| Public snapshot acquisition | `recall_snapshot_inclusive_ns`, `descriptor_snapshot_inclusive_ns`, `public_read_ns` | Nested wrappers; includes coordinator/field guard reads as well as ordinary snapshots |
| Coordinator | `coordinator_total_ns`, `selection_inclusive_ns` | Nested; includes native view opening, control/discovery, field, guards, preparation and event recording |
| Native view | `view_open_inclusive_ns` | Includes pinned-build checks, full export/projection, helper startup, load/readback and validation |
| View components | `native_build_verification_ns`, `projection_construction_ns`, `projection_snapshot_serialization_ns`, `projection_wire_ns`, `native_startup_ns`, `native_load_and_readback_io_ns`, `readback_validation_ns` | Several components nest; snapshot serialization is inside projection construction |
| Native queries | `native_query_inclusive_ns`, `native_queries`, `native_relation_visits`, `native_results` | Query time includes I/O/protocol handling; `query_facade_inclusive_ns` wraps it plus metadata/buffer work and events |
| Service affordability | `affordability_inclusive_ns` | Bounded FIFO scan plus offer-event recording; measured in both contracts, acted on only in assembly |
| Control service | `control_inclusive_ns` | Includes control queries, candidates/pins and metadata; a subset of coordinator work |
| Field including checks | `field_ns` | Includes four fixed steps, guard callbacks, bookkeeping and field-event logging |
| Field excluding guards | `field_kernel_excluding_guards_ns` | Step-call time less measured guard callback time; includes kernel bookkeeping, not isolated arithmetic; excludes the subsequent field-event log call |
| Field guards | `field_guard_read_ns` | Full unchanged public snapshot callbacks; nested in field time and public-read wrappers |
| Other coordinator guards | `coordinator_guard_read_ns` | Full snapshots before expansion/publication; nested in coordinator and public-read wrappers |
| Event recording | `event_recording_ns` | Size checking and event append across phases; nested in their enclosing categories |
| Serialization | `public_serialization_ns`, `trace_serialization_write_ns` | Row snapshot serialization and trace JSON/write respectively; query/event encoding can also appear inside other wrappers |
| Actual formulas | `runtime_ns`, per-call `elapsed_ns`, `runtime_reference_check_ns` | Actual selected finite/PeTTa calls and separate finite result agreement check; inference wrapper includes related adapter work |
| Certification/persistence | `precheck_ns`, `postcheck_ns`, `numeric_commit_ns`, `execution_gate_reservation_ns` | Existing authoritative API calls; commit includes persistence, not an isolated fsync measurement; setup observation admissions are included in these session counters |
| Execution | `execution_total_ns`, `execution_enumeration_ns`, `inference_inclusive_ns`, `acquisition_inclusive_ns`, `dispatch_ns`, `monitor_ns`, `completion_ns`, `goal_accounting_ns` | Inclusive and nested operation wrappers; execution still uses the full public frontier and original gates |
| Reconstruction | `projection_ns`, `authority_reopen_ns` | End-of-episode native projection and SQLite reopen verification |

Do not add inclusive categories to derive a total. Native formula call counts are
reported separately from other admitted numerical observations. Failed and stale
operations remain in the traces and charged work. Fewer calls or queries cannot be
claimed as efficiency when less external/certified loss is resolved.

Active workspace occupancy is not total memory. Each trace retains native view
counts for source records, atoms, relations, values, public export bytes and load
bytes. Full public snapshot/source catalog/native backing and final authority
enumeration remain outside the active-workspace cap. Native/Python RSS, physical
memory, physical observation latency, isolated native arithmetic, standalone SQLite
fsync and OS filesystem-cache effects are unmeasured. These small tasks support no
storage or throughput scaling claim.
