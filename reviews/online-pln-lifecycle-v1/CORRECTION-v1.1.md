# Public-boundary correction before publication

The first source-bound execution at `b771ce8` passed its numerical/lifecycle
expectations and replay checks. Subsequent manual review found a public-boundary
defect: the registered independence justification said
`trusted explicit assumption; copied sibling must still fail lineage checks`.
That text exposed a fixture expectation in the public snapshot. It was identical
in both siblings and was not read as a ranking score, but it violates the declared
boundary. The original run is **not** accepted as the final publication evidence.

The correction changes that text to
`trusted source declaration of independent report-generating processes` and adds
a public-justification leakage check. No operation rule, numeric value, root,
model ID, policy, budget, fixture ID, expected outcome or agenda ordering changes.
The copied-root case still has an explicit trusted independence assumption which
the unchanged lineage checker correctly refuses to use for revision.

The original source copies, traces, journals, checksums and initially successful
audit are retained under `development/source-bound-before-public-boundary-correction`
in the review archive. Fresh finite and native executions and affected coordinator
tests are required at the corrected source. The full default/native regressions
already launched at `b771ce8` retain that exact revision in their receipts; they
must not be relabelled as tests at the corrected revision. Unchanged existing
runtime and regression sources are checked separately.
