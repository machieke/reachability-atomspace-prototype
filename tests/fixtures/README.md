# Stored compatibility fixtures

`admission_v2_journal.json` contains SQLite metadata and seven command records
produced by commit `3e2516ea2205a90aa6d414588b810dde7324e65c`. That committed version
opened a context, recorded and certified expiring evidence, committed a belief,
and advanced the clock to the expiry tick.

The recovery test reconstructs a temporary database from these records and checks
that the current implementation preserves the historical belief and its stale
current status. It then appends lifecycle commands and checks recovery again.
This is a compatibility fixture, not a completed benchmark scenario family.
