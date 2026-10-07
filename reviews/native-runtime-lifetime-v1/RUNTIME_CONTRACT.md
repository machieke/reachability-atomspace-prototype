# Verified runtime lifetime with fresh knowledge views

The experimental session arm separates code lifetime from knowledge freshness.
It verifies the complete original native receipt once per episode, copies all
covered artifacts into Linux memfd objects, applies write/grow/shrink/seal seals,
and hashes the sealed bytes against their expected digests. These immutable bytes
are what subsequent helpers execute. Descriptor identity and seals, alias names,
and the launch configuration are revalidated before native views and queries.
A path, metadata timestamp or `verified=True` never substitutes for the content
contract. Preparation, all guards and cleanup are charged.

The existing executable uses DT_RPATH with original build-tree directories.
The new launch generation uses a separately sealed copy of the host glibc loader,
explicit --inhibit-rpath/--inhibit-cache and an exact private directory of inherited
sealed-library descriptor aliases. Actual /proc/PID/maps device/inode identities
are checked before knowledge loading, against the sealed executable/loader and
receipt-covered library closure determined at preparation. The launch descriptor,
resolution output, aliases and each process's mappings are recorded. Original
binaries, libraries and receipts are unchanged; launch configuration is new.

This local Linux/glibc contract protects against accidental covered-artifact drift
and original-tree replacement. Failed seals, missing/replaced aliases/descriptors,
wrong generation/root/protocol, unexpected mappings or helper failure block work.
Actual content writes/truncation are denied by the kernel. A fresh generation
reverifies originals. A failed observer stays latched until explicit rebuild;
consumer attempts, budgets and unresolved external operations remain intact.

Host Python, kernel/procfs, system libraries outside the original receipt, and
glibc loading semantics are trusted. Actual uncovered host paths are listed.
The additional loader digest identifies the host loader captured at preparation;
it is not an upstream-authenticated build receipt. This is not universal hermetic
execution or protection against a malicious privileged owner, process-memory
modification or a malicious helper's falsely complete answers. Native query
membership still receives an independent offline source check.

The portable CPython build lacks memfd_create and seal constants; a small ctypes
libc wrapper uses Linux UAPI constants, with explicit failures on unsupported
hosts. Reference semantics: [memfd_create](https://man7.org/linux/man-pages/man2/memfd_create.2.html),
[file seals](https://man7.org/linux/man-pages/man2/F_GET_SEALS.2const.html),
[dynamic loader](https://man7.org/linux/man-pages/man8/ld.so.8.html).

Every changed authoritative snapshot still gets a new projection, process, full
load/readback, query namespace and binding. No membership answers survive a view
change. The old capture/A/B/validation, graph semantics, consumer, frontier,
formula/certification and physical-world logic remain. SQLite remains authority.
The original MH-scan and strict native modules remain runnable byte-for-byte.
A separate common driver adds disjoint observation, selection, execution,
logging, final output/cleanup and residual accounting to all three arms.
Preparation is removed from observation's coarse total exactly once. Fine-grained
timers remain nested; residual includes setup, world/monitor accounting and local
reconstruction. Final result-envelope writing and comparison reporting are outside
the episode timer, included in the end-to-end command wrapper time. RSS/peak/native
memory and serialization-copy counts remain unmeasured; bytes staged are not RSS.

With the existing pinned native builds available, use fresh output directories:

```sh
uv run --no-project python -m runtime_lifetime_lab.compare run --output /tmp/runtime-lifetime-comparison
uv run --no-project python -m runtime_lifetime_lab.compare audit /tmp/runtime-lifetime-comparison --output /tmp/runtime-lifetime-audit
```

Two serial sweeps each run 36 cells. Arm order reverses within every parent/mode
group. Six parent tasks are unchanged; 72 executions are not independent tasks.
Strict native query reexecution audits both native arms; recorded arithmetic,
original fresh PLN calls, SQLite reconstruction and generation checks have distinct
counters. The review includes paired times by sweep and local variability, without
broad significance, real-time or cognitive-speed claims.

No persistent storage, pooling, incremental synchronization, new planner/depth,
pressure/transport, policy promotion or generalized recovery is included.

This generation adapter applies to native retrieval helpers. It stages the entire original receipt-covered inventory, including artifacts outside the actually mapped retrieval dependency closure. Native PLN formula calls continue through the existing certified interfaces and their original verification path; this increment does not cache their verification or change their launch.
