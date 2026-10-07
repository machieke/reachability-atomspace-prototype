# Development record

The environment declarations and budgets were committed at `326c7fe` before any
new episode was run. They were never retuned. Measured implementation and auditor
are frozen at `b12127556d6d1fe4a7c152dba85f5d71df266194`. Earlier exploratory runs
below used dirty new inputs; they are retained as development evidence, not pooled
with the frozen cohort. All paths below are under `development/` in the archive.

| Invocation | Recorded result |
|---|---|
| `episodes-1/`, `episodes-1.log` | Six finite exploratory episodes conformed. |
| `tests-1.log` | 18 tests, 17 passes and one failed assertion, 85.656 seconds. |
| `tests-2.log` | Corrected lost-reply test and three actual native tests: four passes, 24.199 seconds. |
| `cohort-1/`, `cohort-1.log` | Twelve finite/native development executions conformed. |
| `audit-1.log` | Goal-predicate replay failed in the new auditor. |
| `cohort-2/`, `cohort-2.log`, `audit-2.log` | Corrected twelve-execution cohort and full semantic audit passed. |
| `negative-2.json` | All eight altered development bundles rejected. |

The failed lost-reply assertion equated a `PASS` command application result with a
received acknowledgment. The existing command result reports that the command was
applied; the actual local dispatch remains `uncertain`, with no latest receipt,
while the executor has accepted one effect. Only the test assertion changed.
`failed-source-1/test_independent_world.py` and `lost-reply-diagnostic.json` preserve
the original assertion and exact command/dispatch/executor/world evidence. The
corrected test checks the uncertainty, absent acknowledgment, physical effect,
idempotent duplicate and existing explicit query path. It adds no automatic retry.

The first audit compared a sample's belief ID with `ContextSnapshot.usable`
objects instead of their IDs. This falsely excluded actual admitted samples.
`failed-source-2/audit.py` and `audit-1.log` preserve that failure. The corrected
replay finds historically received successful samples, resolves their exact ledger
records and passes belief IDs to the unchanged durability predicate. It checks
all 280 public prefixes, including prefixes before same-tick observations.
`audit-diagnostic-1.json` records the diagnosis. An initial diagnostic-print attempt
also failed to JSON-encode a `BeliefRevision`; this was a diagnostic serialization
mistake and did not change any run or authoritative state.

Review also found that the session's transient certificate list is cleared between
events/reopen. Its exploratory export was empty even though receipts and durable
journals retained the real permits. The corrected runner exports every hard,
numerical, execution and completion certificate directly from the persistent
ledger; the auditor checks all 510 against reconstructed authority. The frozen
cohort includes this export. The older exploratory files remain unchanged.

These are new test/auditor/export defects, not changes to the old consumer, formulas,
live authority, environment parameters or controller outcomes. Previous publication
`173c772`, measured source `d2a6b66`, publication `3b89d63`, all earlier failures,
declaration correction and coverage omissions remain untouched. In particular,
the previous default-wrapper exit 143 remains an unresolved wrapper anomaly; it
is not reclassified as a clean invocation by this increment.
