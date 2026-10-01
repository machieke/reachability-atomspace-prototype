# Reachability AtomSpace prototype

This repository implements the reachability proposals in stages. The current
increment is a single-authority admission service with optional SQLite recovery for a small grounded
propositional fragment. It separates stored reports, proposals and accepted hard
claims, and checks the complete relevant constraint set before acceptance.

Read [the phased implementation plan](IMPLEMENTATION_PLAN.md) for deliverables,
dependencies and exit criteria. The original specifications and validation design
remain the design inputs. [The implementation manifest](implementation_manifest.json)
records their hashes and the capabilities actually implemented.

## Run the prototype

The development interpreter is Python 3.11.14. There are no third-party runtime or
test dependencies. From the repository root, use an existing Python 3.11 or later,
or the pinned interpreter through `uv`:

```bash
uv run --no-project python -m reachability.demo
uv run --no-project python -m reachability.recovery_demo
uv run --no-project python -m unittest discover -s tests -v
uv run --no-project python pressure_field_lifecycle_reference_checks.py
```

For an editable package installation, run `uv sync --frozen`. The lock file has
no third-party runtime dependencies; the package build uses pinned setuptools.

With a suitable Python already active, the equivalent commands begin with
`python` instead of `uv run --no-project python`. The last command runs the
original standalone numerical checks. Those checks do not establish pressure or
transport integration with the admission service.

The demonstration reports these outcomes:

| Operation | Result |
| --- | --- |
| Infer with one missing mandatory premise | UNKNOWN |
| Infer after both exact premises are accepted | PASS |
| Accept a contradictory conclusion | FAIL |
| Commit using permits issued before support revocation | STALE |
| Query the dependent conclusion after revocation | STALE, with history retained |

## Implemented semantics

- Grounded predicate applications have deterministic structural identities;
  argument order matters. Context is separate from statement identity.
- Immutable evidence records retain source, logical observation time and lineage
  roots. Duplicate IDs are idempotent; conflicting reuse is rejected. Recording
  opposing reports alone creates no accepted claims.
- A caller must explicitly propose adoption of a report under the **hard-claim
  interpretation**. This is a finite conformance model, not calibrated empirical
  belief or a PLN strength/confidence formula.
- Registered grounded rules require their complete ordered premise revisions in
  one context. Replacing a rule retires its old derivations and their descendants;
  inference itself has no side effects.
- Context constraints use conjunctive normal form: a tuple of disjunctive clauses.
  A clause may be empty (false); an empty constraint collection is true. Assumptions
  are additional hard literals. Every check considers all active claims.
- The complete checker uses unit propagation and branching, with a default limit
  of 16 variables and a configurable maximum of 20. Exceeding the limit returns
  UNKNOWN; it never certifies a truncated constraint set.
- Precertification binds inputs; pure inference builds a proposal; postcertification
  replays the proposal and checks the proposed state. Only fresh, service-issued
  PASS records permit a commit.
- Every public mutation has an idempotency key. One lock covers revision comparison
  and publication. Two commits from the same old revision cannot both succeed.
- Revoking evidence invalidates all dependent revisions before publishing the new
  context revision. Independent alternative supports remain usable. Historical
  certificates and beliefs remain records of earlier checks.
- Evidence has an optional exclusive `valid_until` tick. The context clock is
  explicit and monotone. Future observations cannot support current claims, and
  expired evidence cannot support pending commits or current dependent beliefs.
- Policy updates recheck the complete scope and invalidate pending permits.
  Individually incompatible claims and their descendants become stale. If the
  remaining claims are jointly inconsistent, this first policy updater retires
  that remaining set conservatively; it does not choose an arbitrary surviving
  world. Claims may then be explicitly re-admitted under the new contract.

`Certificate.status` describes its recorded check results; it is not a current
authorization query. The service checks registry integrity, subject, stage, scope
and revision every time a permit is used. `query_belief` checks the current joint
state and returns its validation revision separately from historical certificates.

Idempotency replay returns the original operation response, including its original
revision. It does not assert that the response is still current; use `query_belief`
or a fresh snapshot for current state.

## Durable storage and recovery

Passing `database` enables a SQLite command journal; omitting it keeps the volatile
service useful for small conformance tests. Use a context manager to release the
single-authority lock:

```python
from reachability.service import AdmissionService

with AdmissionService(database="artifacts/admission.db") as service:
    service.open_context("plant-A", idempotency_key="create-plant-A")

with AdmissionService(database="artifacts/admission.db") as recovered:
    print(recovered.snapshot("plant-A"))
```

The journal stores typed command inputs and result digests in atomic transactions.
Accepted revisions, their certificate records and idempotency responses are
reconstructed together by replaying those commands through the checks. Recovery
rejects mismatched results, unknown schemas and corrupted event chains. Initial
rules and checker capacity are recovered from the journal; explicitly supplied
initial configuration must match. Later rule replacements are replayed normally.

An exclusive POSIX file lock enforces one live authority for the database path.
SQLite uses WAL mode and full synchronous commits. The service holds its own lock
through durable commit before publishing a changed view. A storage failure closes
authorization until the caller closes and reopens the service, then reconciles
the original idempotency key. No external executor is involved yet.

The hash chain detects corruption within the trusted database boundary; it is not
signed attestation or protection against a database administrator rewriting history.
The clock measures declared logical ticks, not elapsed wall time. A restarted
caller must advance it before performing work at a later logical time.

Recovery currently replays the complete history, and durable mutations copy working
state for rollback. These intentionally simple algorithms have unoptimized time
and memory costs. Schema migration and snapshot acceleration are future work.

## Source layout

| Location | Responsibility |
| --- | --- |
| `reachability/model.py` | Immutable records, structural IDs and gate statuses |
| `reachability/logic.py` | Bounded complete CNF checker |
| `reachability/service.py` | Evidence, certificates, commits and invalidation |
| `reachability/journal.py` | SQLite transactions, integrity and authority locking |
| `reachability/codec.py` | Explicit typed JSON records without executable deserialization |
| `reachability/demo.py` | Executable public-API walkthrough |
| `reachability/recovery_demo.py` | Restart and credential expiry walkthrough |
| `tests/oracle.py` | Independent exhaustive Boolean evaluator |
| `tests/test_admission.py` | Authority, scope, lineage and concurrency checks |
| `tests/test_mutations.py` | Isolated witnesses for mutants M01–M04 |
| `tests/test_revisions.py` | Rule/policy changes and temporal boundaries |
| `tests/test_recovery.py` | Recovery, corruption, storage failures and process crashes |
| `tests/test_durable_contract.py` | Same admission contracts through durable storage |
| `reachability_validation_design/` | Original proposed benchmark, not runtime inputs |

The oracle uses signed-integer formulas and exhaustive truth tables. It imports no
runtime implementation. Tests compare the runtime checker and returned witnesses
against it on 400 seeded generated formulas, in addition to hand-authored cases.
The evaluator is separated by imports and file location; OS-level isolation is
still pending.

## Current limits and next work

This is an in-process API with trusted callers, not a sandbox for hostile Python
code. The current storage lock implementation targets POSIX hosts. Schema migration,
context inheritance, variable matching, general temporal requirement expressions
and resource reservations are not implemented. Context assumptions constrain admission but are not automatically
materialized as premise revisions in this first slice.

There is no actual AtomSpace, FDAS, PLN, ECAN or Freeciv adapter yet. Pressure and
transport remain the supplied standalone numerical examples. The 64-fixture
target, full deployment episode, M05–M12 mutants and performance experiments are
still pending. Existing tests establish the stated finite contracts only.

The next increment builds phase 2's lifecycle/operation ledgers on the durable
boundary, followed by resource reservations, executor reconciliation and exact
outcome monitoring. General context inheritance and variable binding remain
explicit phase 1 backlog items.
