# Development evidence

Development logs and the original failing test sources are retained in the review
archive under `development/`. These runs used uncommitted implementation sources;
they are not labeled measurements at the subsequently frozen revision.

- Initial native build and independent full structural/Value readback passed.
- Initial choices matched Goal-scan for all twelve unchanged parents.
- `tests-1.log`: 21 tests, two errors. The tests sent an exact large integer time
  through the frozen trace driver, whose supported event time is 0–1000. Tests
  now use the public clock APIs; the trace limit remains unchanged.
- `tests-2.log`: 21 tests, one failure and one error. The negative native relation
  canary created an invalid forward reference and was rejected during loading,
  before the intended answer-set comparison. It now targets an existing wrong
  literal. The large integer was already exact in the complete snapshot payload;
  explicit decimal revision/time StringValues were added to the view metadata
  so they can also be checked directly. Pre-expansion record and context checks
  were tightened. The initial sources and logs remain retained.
- `tests-3.log`: all 21 then-current new tests passed (23.294 seconds).
- `tests-4.log`: the additional actual native-PLN/native-recall full route and
  matched replay test passed (7.583 seconds).
- `closed-loop-1/`: all twelve Goal-native, finite-formula, work-16 development
  executions passed. Correctly blocked and reopened cases retained loss. This
  run predates the explicit revision StringValues; it is not the official cohort.

Native dependency preflight now checks the pinned PLN/PeTTa sources and SWI
version when native formulas are requested. Recorded formula runtime errors make
an execution ERROR rather than permitting a successful comparison classification.
Neither failure handling nor test corrections add a Python discovery substitute.
