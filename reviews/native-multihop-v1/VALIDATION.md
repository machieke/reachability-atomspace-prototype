# Frozen validation and explicit omissions

Measured source/auditor `068770ea5f7970bfaf65aabfdae3fcfe3d983226`. Default and native groups ran once, serially,
then the core comparison and audit ran serially. Sources/test hashes are identical
before and after both suites. Both wrapper exits are zero.

| Suite | Executed | Passed | Failures/errors/skips | Seconds |
|---|---:|---:|---|---:|
| Default | 473 | 473 | 0 / 0 / 0 | 326.855885 |
| Native | 125 | 125 | 0 / 0 / 0 | 204.826525 |

New seam coverage: five non-native contracts and 23 real native integration tests.
Existing native-recall tests retain ordering, polarity, exact large integers,
readback/malformed transport and timeout coverage. Multihop, bridge/consumer,
numerical ledger, decisions, dispatch, goal/lifecycle, independent-world and
native adapter suites are included. All IDs, module names, logs, source hashes,
start/end metadata and commands are in validation/*.json and *.log.

Omitted this time: 642 default tests across
46 modules;
48 native tests across
11 modules; and 15 separate
pressure numerical checks. Broad unchanged scheduler/transport, generalized
recovery, corpus and unrelated matrices remain omitted. Historical passes are
not fresh coverage. The historical wrapper exit 143 anomaly stays unresolved.

Preservation passed for 825 earlier files, with only the
plan/manifest excepted. Both prior native build receipt byte comparisons passed.

Independent review counters: 528 public rows,
324 selections, 216 physical ticks,
168 physical product/health samples,
24 SQLite/executor reconstructions,
1096 actual certificates,
12880 independently checked recorded query answers,
12880 native query reexecutions,
60 recorded arithmetic checks,
30 originally fresh native formula calls, and zero
fresh native formula invocations during audit. Operation result statuses:
`{'PASS': 312, 'UNKNOWN': 12}`. UNKNOWN source answers are expected unresolved outcomes,
not harness failures.

All 13 altered-copy/resealed witnesses were rejected:
phantom and misordered intermediates, forged roots, stale descendants, hidden
adverse evidence, partial review, inference-as-relief, false fresh-native claims,
unsealed corruption, native omission, stale query epoch, raw response alteration
and scan fallback labeling. Mutation replay checks recorded semantics without
extra native query reexecution; original core query reexecution is separate.

Retained development failures: seam1 had two blocker-ordering parity failures;
seam2 had one missing revision-model applicability diagnostic. Both kept work
blocked. Corrections restored frozen diagnostics. Audit1 stopped on a byte-count
field-name mismatch, corrected without changing its raw run. seam3 passed 27 and
seam4 passed 28 focused tests; the corrected development query audit passed
12,678 native query reexecutions and 12 pairs. These are development receipts,
not counted in the frozen suite totals. Development timing overlaps are labeled.

Archive integrity, extracted semantic replay and altered-archive rejection are
reported in the subsequent publication receipt, without circular self-binding.
