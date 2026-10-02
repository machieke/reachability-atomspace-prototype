# Explicit harness correction v1.1

The first measured attempt at source
`d7fa0625151a88dc55857f1c4cedadd228aea6db` completed all 660 policy runs and
132 reference cells, then failed its final audit. Its entire comparison,
configuration, journals, labels, results, checksum inventory, FAILED.json and
execution log are retained in the publication as `failed-attempt-v1/`.
It is not the accepted audited measurement and must not be silently substituted
for the corrected run.

The first mismatch was the optimal witness for
`or-4/requests-4-work-4`. Its belief history contained revisions 2, 3, 5, 8 and 11.
The signature producer used integer dictionary keys. Canonical JSON sorted
those keys numerically before encoding, whereas a loaded JSON object necessarily
has string keys and sorted them lexicographically. Thus identical histories had
different canonical *strings*: the number 11 moved ahead of 2. Decoding both
strings produced identical values. The saved journal was not corrupt.

Version `decision-value/v1.1` serializes belief-history revision keys as strings
at the signature boundary. It retains strict equality for the entire journal
signature and all other checks. A regression exercises revisions across 9/10,
checks the JSON round trip, and verifies changed history content still fails.
This is an audit serialization correction only. Neither reference transition
model, Q/V calculation, loss definition, policies, task inventory, partitions,
sampling, budget, witness selection, candidate discovery nor hard gates changed.
The configuration digest remains identical. No policy was tuned after results.

The corrected source is committed before a fresh, separately named measurement
and full replay audit. All original measurements, including unfavorable and
neutral results, remain reviewable. Compare source-bound semantic outcomes
between attempts; do not treat the two runs as independent statistical evidence
or reproduce historical timings.

Documentation erratum: the committed protocol says the cohort maximum is six
rules. The unchanged inventory actually has at most five; the declared reference
limit remains eight. This does not alter any case or experimental bound.
