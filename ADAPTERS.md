# Pinned native adapter increment

Phase 3 now has a real C++ AtomSpace projection and a pure PLN formula adapter.
They run independently of the finite admission service. AtomSpace holds actual
Nodes, ordered ListLinks and named Values; PeTTa executes the selected upstream
MeTTa formulas. Neither adapter can commit an uncertain proposal to the hard-claim
ledger. This increment establishes native compatibility and the initial contracts,
not the phase 3 deployment exit criterion.

## Dependencies and reproduction

[adapters.lock.json](adapters.lock.json) selects these inspected source revisions:

| Component | Revision | Used interface |
| --- | --- | --- |
| [OpenCog AtomSpace](https://github.com/opencog/atomspace/tree/c8d633bf272b838c2132c21b7c8ddf169a18dd22) | `c8d633bf272b838c2132c21b7c8ddf169a18dd22` | C++ AtomSpace, ConceptNode, PredicateNode, ListLink, FloatValue, StringValue |
| [OpenCog cogutil](https://github.com/opencog/cogutil/tree/64dca9083dcfa485dcb70fd6fe7ba1f80e0f4082) | `64dca9083dcfa485dcb70fd6fe7ba1f80e0f4082` | AtomSpace build dependency |
| [trueagi-io PLN](https://github.com/trueagi-io/PLN/tree/4405956947c4b53c7ff01bd565aa3b114bc970a1) | `4405956947c4b53c7ff01bd565aa3b114bc970a1` | `Truth_Deduction`, `Truth_Revision`, conditional probability checks |
| [PeTTa](https://github.com/trueagi-io/PeTTa/tree/ae66fa8e41dcd5539d614706bd4e5cfb34f9608d) | `ae66fa8e41dcd5539d614706bd4e5cfb34f9608d` | SWI-Prolog runner, direct local library import |

The tested host is Ubuntu 20.04, x86_64 Linux, Python 3.11.14, GCC 11.4.0,
CMake 3.16.3, Guile 3.0.1 and SWI-Prolog 10.0.1 with its Janus module. The compiler
must support C++20; the script explicitly selects `gcc-11`/`g++-11`. Source commits
and staged Debian package hashes are fixed. Compiler/CMake versions are recorded
in the local build receipt; other versions have not been tested. The PLN runtime
requires the exact recorded SWI-Prolog version.

The build needs Git, CMake, make, GCC 11, pkg-config, GMP development headers and
SWI-Prolog installed. On the tested Ubuntu host the following stages Guile and its
support packages inside `artifacts/`, without sudo or changes to `/etc`:

```bash
uv run --no-project python scripts/build_adapters.py --debian-sysroot
uv run --no-project python -m unittest discover -s integration_tests -v
uv run --no-project python -m reachability.adapter_demo
```

The Debian option requires the locked Ubuntu amd64 package versions to remain
available from the host's configured apt repositories. It verifies each downloaded
SHA256 before extraction. On a host with Guile development packages already
installed, omit `--debian-sysroot`; that host configuration needs its own validation.
The script does not install SWI-Prolog or compiler toolchains. The default finite
suite continues to need only Python's standard library.

Builds use isolated source trees, reject mismatched or modified tracked source,
and never update an upstream branch. Only AtomSpace's C++ `atomspace` target and
its dependencies are built. Scheme/Python bindings and their upstream test suites
are not part of this build. A temporary DESTDIR contains cogutil's absolute-path
install actions; only the requested local prefix is copied out. There are no
patches to the upstream repositories.

`artifacts/adapter-build.json` records the lock digest, native helper source digest,
compiler/runtime versions and native binary/library hashes. Native calls check
this receipt; PLN calls check the source revisions, tracked changes and formula
file hash. This detects accidental drift, not malicious replacement by a workspace
owner. System libraries and the whole operating system are not hermetically pinned;
the build is not claimed to be bit reproducible. A second build from empty source,
build and install directories was exercised on the same host.

The optional integration suite fails when dependencies are absent; it does not
turn missing adapters into successful skipped tests. `artifacts/` remains ignored.
No dependency checkout or native binary is committed.

## AtomSpace projection contract

`AdmissionService.export_admission(context)` captures the authority identity,
context snapshot and freshly checked belief views under one service lock. The views
retain historical revisions and their proposal, evidence, lineage and certificate
identifiers. `project_admission` projects that immutable export after releasing the
lock. It describes a particular revision, not present authorization.

`RecordProjection` maps typed records and field roles into ordered ListLinks.
Predicates, arguments, polarity, tuple order and context remain structural. A
content identity distinguishes immutable revisions even when only numeric fields
change. Exact integer fields, including arbitrarily large revisions and timestamps,
use decimal StringValues under named PredicateNode keys. They are never rounded
through a double. `add_probability` stores a proposal's truth pair in a FloatValue,
with structural formula/truth-model IDs, assumptions, premises, source lineage and
an explicit proposal marker. Uncertain support never becomes a hard BeliefRevision.

Each bounded batch creates a private native AtomSpace. The helper reads canonical
handles, outgoing sets and final Values back from the C++ API. Python compares the
readback with the requested graph, including alias identity and overwrite order.
The native store automatically adds its `*-IsKeyFlag-*` metadata PredicateNode when
needed; it is accounted for separately from projected records. No Atomese evaluator,
Scheme evaluator or arbitrary command execution is exposed by this transport.

The transport permits at most 100,000 commands, 8 MiB of input, 64 KiB per string,
4,096 outgoing references/value components, and 30 seconds per native call. A batch
failure publishes no projection and changes no service state. SQLite checked replay
can rebuild the projection. Native persistence, incremental updates, numeric
threshold indexes, complete ledger export and mutable service-owned AtomSpace
transactions remain pending. This is a disposable projection, not a second authority.

## Pure PLN contract

`DeductionRule(P,Q,R)` is a grounded schema with ordered premises `P`, `Q`, `R`,
`P⇒Q`, `Q⇒R`, concluding `P⇒R`. The labels denote proposition identities; there
is no variable matcher. `ProbabilitySnapshot` binds exact immutable supports to a
context and knowledge revision. This snapshot is caller supplied and has not yet
been certified by the admission service.

`PLNAdapter` exposes `check_rule_preconditions`, `apply_rule`, `revise` and `explain`.
The selected truth model is `trueagi-pln-stv-finite-k1/v1`. Input/output strengths
must be finite in `[0,1]`; empirical confidences must be finite in `[0,1)`. Logical
certainty requires a different future interpretation. Confidence equal to one,
including rounding to one, is rejected.

Deduction first checks exact binary-rational marginal/conditional bounds. Zero
antecedent probability returns UNKNOWN. Infeasible bounds return FAIL before any
formula call. The runtime independently evaluates upstream's conditions; a numeric
disagreement returns UNKNOWN. This prevents upstream's `(stv 1 0)` failed-condition
fallback from passing as a valid inference. The selected formula's heuristic and
`Q > 0.9999` approximation branch are recorded as assumptions. This is not a
general joint-distribution solver or a calibration claim.

Revision follows the selected `k=1` evidence-weight convention only with an explicit
independence model declaration bound to both exact supports. Distinct evidence IDs
and roots alone do not justify summing weights. Overlap in either IDs or roots
retains alternatives even if a caller asserts independence. Zero total weight is
UNKNOWN. Duplicate support produces no new weight; premise ancestry prevents a
cyclic deduction from creating new support. Derived proposals preserve the union
of source evidence and roots. Revision of a derived support with its own ancestor
therefore cannot count those roots again.

Independence declarations are trusted caller assumptions, not statistical tests.
Formula output is a proposal with a deterministic ID and explanation. This adapter
does not create evidence, commit accepted beliefs, change goal loss, allocate
attention or run the upstream resource-bounded reasoning search. Malformed,
multiple, empty or nonfinite runtime results, diagnostics, process errors and
timeouts fail closed. Only validated numeric arguments enter MeTTa expressions;
domain labels are never interpolated into executable code. Import uses a checked
local path and performs no Git import/network fetch at inference time.

## Verification and next increment

The default suite adds probability-domain enumeration over 125 four-cell models,
ordered bindings, scope, lineage overlap, cycle and duplicate guards, explicit
independence assumptions and runtime/artifact drift boundaries. The optional suite
executes both real runtimes: native identity, ordered links, Value updates, Unicode,
exact integers, malformed requests, journal reconstruction, revocation, rational
deduction/revision fixtures, runtime errors, timeout and proposal-to-FloatValue
readback. The demo produces approximately `(0.68, 0.3136)` and creates no accepted
beliefs.

Next add a separately versioned probabilistic ledger and its issued pre/post
certificates, exact snapshot binding and checked durable commit/replay. Numeric
proposals must remain distinct from hard claims. Then carry the native projection
and inference adapter through the same service contracts and deployment episode.
Phase 3 remains open until that integration passes. Attention, FDAS and Freeciv
adapters, general context inheritance and variable binding remain pending.
