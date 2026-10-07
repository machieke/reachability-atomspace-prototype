# Verified runtime lifetime preregistration

Baseline c088775; frozen implementation/auditor 068770e; publication f8007ed.
Preserve every previous implementation, fixture, review, build, receipt and
failure. New names: experimental_runtime_lifetime and runtime_lifetime_lab.

Arms: MH-scan, MH-native-strict, MH-native-session. Use the original six parents,
finite/native PLN modes, seed, limits, depth-three review and physical clock.
Two serial sweeps: within each mode/parent group, sweep 0 uses the listed arm
order, sweep 1 reverses it. Exactly 72 core executions, six parent structures.
One prepared generation per session episode; no sharing with another run.

Target only repeated runtime build verification. Existing complete capture,
full A/B, discarded one-step graph, native membership, cold helper/view/load,
readback, exact tuples, consumer/FIFO, authority and world all remain unchanged.
No query cache across snapshots, persistent storage, daemon or restart service.

Proposed Linux/glibc-specific integrity contract: cryptographically verify the
original receipts, lock, sources and all covered binaries/libraries at preparation;
copy covered artifacts to memfd objects, seal against write/grow/shrink and further
seal changes, then hash those actual sealed bytes against expected digests.
Load helpers with explicit loader options suppressing embedded RPATH and an
isolated directory of exact descriptor aliases. Keep original binaries/receipts.
This is a new launch generation, not an identical launch configuration.
Check seals, live descriptor inode/device/size identity and alias integrity before
views and queries; check actual loaded mappings before graph loading. These checks
rely on kernel-enforced seals, not metadata as evidence of unchanged contents.
An attempted content write must fail; replacement/missing descriptors or aliases,
invalid generation/root/protocol, unexpected library resolution or helper failure
must close discovery. Explicit reconstruction never resets consumer state.

A private copy of the host dynamic loader may be sealed and recorded as an
additional launch artifact. Other host system libraries, Python, kernel/procfs,
loader semantics and toolchain remain trusted host dependencies outside the old
build receipt. No protection against a malicious privileged owner, process-memory
mutation, kernel compromise or arbitrary malicious helper omissions is claimed.
List actual host dependencies and scope of resolution checks. Original-tree edits
must not alter an active sealed generation; a new preparation must reverify them.
If reliable lifetime cannot be established, retain strict verification and record
a blocker. No unchecked mutable binaries to force an improvement.

Register generation preparations, digest passes/bytes, copies, integrity checks,
loaded paths, launches, views/replacements, queries, failed preparation/teardown,
all nested costs and end-to-end times. Add nonoverlapping coarse phases in a
separate common tick-driver copy; use the original discovery and consumer paths
unchanged. Residual costs are explicit, never sum nested fine-grained timers.
Memory/RSS/peak remain unmeasured; byte counts alone are not memory usage.

Compare semantic graphs/choices on identical snapshots and full independent
executions. Normalize only authority-specific candidate bindings and new runtime
receipt/transport metadata. Keep exact evidence/premise IDs, operation order,
world trajectories and failures. Audit uses fresh strict native query execution
as an independent comparator; recorded arithmetic and fresh PLN counts remain
separate. Preserve old extracted replay versus native reexecution distinction.

Test receipt/lock/binary/library corruption, original versus active drift,
seals, alias replacement, actual library resolution, closed/wrong generations,
intermediate/fresh-view round trip, descendant retirement and stale operations,
old query/failure gates and control headroom. Use disposable source copies for
artifact mutation tests, never alter the original build. Run applicable suites
once at frozen source; record exact omitted coverage. A small fixed-snapshot
query repetition corroborates reuse only, not an independent task or warm view
performance claim. Report every paired time in both sweeps and local variability.

Stop after a reproducible source-bound review, regardless of performance.
No selective invalidation, pooling, new planning/depth, transport, policy-B
promotion, supersession or generalized recovery.
