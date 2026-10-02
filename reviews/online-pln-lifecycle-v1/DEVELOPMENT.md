# Retained development failures

The twelve fixture definitions were committed at `1cf88ba` before the agenda was
run. They have not been changed in response to results.

- `online-pln-development-1`: first finite run, four conformance checks passed and
  eight stopped at dispatch with a strict event-schema exception. The adapter
  omitted the required `fault="none"` dispatch argument. Its traces, journals,
  dirty source inventory and source copies are retained. The fix only supplies the
  existing required field; no authority or fixture was weakened.
- `online-pln-development-2`: all twelve finite fixtures passed after that fix.
- `online-pln-development-native-1`: all twelve native fixtures passed, including
  projection and reconstruction. These are development runs, not the final source
  revision's measurement evidence.
- `online-pln-tests-1.log`: 13 tests, one failed expectation. A revoked positive
  credential leaves the existing hard FACT requirement UNKNOWN, not STALE. The
  test was corrected to the existing contract; no service code changed.
- `online-pln-tests-2.log` and `online-pln-tests-3.log`: a new retry-basis check
  incorrectly accessed `BeliefView.conclusion`, which that record does not have.
  The implementation now uses the public context's immutable current `usable`
  beliefs. This also avoids retrying solely because an unrelated clock changed.
- `online-pln-tests-4.log`: all 18 new seam tests passed after that correction.
- First source-bound run at `b771ce8`: numerical/lifecycle behavior and replay
  passed, but manual review found evaluator wording in a public independence
  justification. This run is retained and superseded; see `CORRECTION-v1.1.md`.

Logs and failed episode artifacts are included with the publication. Test logs
from uncommitted development snapshots are labelled as such, not attributed to
the later frozen implementation. The original planner benchmark, runtime and
prior publications remain unchanged.
