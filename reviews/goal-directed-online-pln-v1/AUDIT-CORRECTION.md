# Cross-session audit correction

Primary source d1d39ab completed all 144 executions and 24 diagnostic siblings.
The first independent audit passed source integrity, candidate/selection replay,
matched-snapshot scan/index parity, formulas, prefix checks and copied SQLite replay,
then rejected its final cross-session equality comparison.

Diagnosis: AdmissionService intentionally creates a fresh UUID authority for each
ledger. Hard certificate IDs therefore differ across fresh runs. These IDs occur
inside full public snapshots and candidate basis inputs. Requiring byte-identical
`basis` and `expected_binding` hashes across separate authorities was erroneous.
The chosen operation, ordered numerical premise IDs, logical identity, semantic tie,
cost, observations and outcomes were unchanged.

The corrected auditor omits only those two opaque hashes from CROSS-SESSION
comparison. It still checks both hashes exactly against the actual recorded
snapshot in each run, and requires exact whole candidates/witnesses/eligibility on
identical replay snapshots and histories. Certification and execution are unchanged.
Two targeted tests cover fresh actual ledgers, preserved exact premise/operation/
outcome checks and non-mutating normalization.

The original execution bundle, failed audit log and measured source are retained.
No episode, policy, runtime, numerical gate or measured result was changed or rerun
to obtain this correction. The corrected auditor has a separate recorded revision;
applicable and native regressions retain their actual original tested revision.
