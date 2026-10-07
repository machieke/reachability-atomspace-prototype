# Actual selected operations and terminal work

All core rows below are controller selections, followed by actual API results. The finite/native runs repeat six parent structures. A/B denote numerical status; live hard checks, finite review and observed outcome remain separate. Full JSON traces preserve candidate FIFO keys, exact dependencies, certificates, received reports, contrary/unclassified evidence and environment events.

## finite-positive

| Step | Selected request / API result | Origin | A / B before | Required review | Observed loss before → after |
|---:|---|---|---|---|---:|
| 0 | deduction:r-competing → PASS | exact-work-route | UNKNOWN / UNKNOWN | unresolved | 10 → 10 |
| 1 | request:missing-premise → PASS | exact-work-route | PASS / UNKNOWN | unresolved | 10 → 10 |
| 2 | adopt:premise-4 → PASS | received-report-adapter | PASS / UNKNOWN | unresolved | 10 → 10 |
| 3 | deduction:r-estimate → PASS | exact-work-route | PASS / UNKNOWN | unresolved | 10 → 10 |
| 4 | reserve:attempt → PASS | fresh-live-authorization | PASS / PASS | complete | 10 → 10 |
| 5 | dispatch:attempt → PASS | fresh-live-authorization | PASS / PASS | complete | 10 → 10 |
| 6 | request:product → PASS | existing-operational-control | PASS / PASS | complete | 10 → 10 |
| 7 | request:health → PASS | existing-operational-control | PASS / PASS | complete | 10 → 10 |
| 8 | request:health → PASS | existing-operational-control | PASS / PASS | complete | 10 → 10 |
| 9 | request:health → PASS | existing-operational-control | PASS / PASS | complete | 10 → 0 |
| 10 | complete:attempt → PASS | existing-operational-control | PASS / PASS | complete | 0 → 0 |
| 11 | STOP OBSERVED_COMPLETION | terminal | PASS / PASS | complete | 0 → 0 |

Terminal obligations: forecast=PASS (), method-assessment=PASS ().
Terminal global categories: HARD_OR_SCOPE_CHECK.
Optional unexamined producers: 0.
Actual lifecycle: BUILT; executor effects: 1; observed loss: 0; environment loss: 0.

## finite-shared

| Step | Selected request / API result | Origin | A / B before | Required review | Observed loss before → after |
|---:|---|---|---|---|---:|
| 0 | revision:model-ab → PASS | exact-work-route | PASS / UNKNOWN | unresolved | 10 → 10 |
| 1 | reserve:attempt → PASS | fresh-live-authorization | PASS / PASS | complete | 10 → 10 |
| 2 | dispatch:attempt → PASS | fresh-live-authorization | PASS / PASS | complete | 10 → 10 |
| 3 | request:product → PASS | existing-operational-control | PASS / PASS | complete | 10 → 10 |
| 4 | request:health → PASS | existing-operational-control | PASS / PASS | complete | 10 → 10 |
| 5 | request:health → PASS | existing-operational-control | PASS / PASS | complete | 10 → 10 |
| 6 | request:health → PASS | existing-operational-control | PASS / PASS | complete | 10 → 0 |
| 7 | complete:attempt → PASS | existing-operational-control | PASS / PASS | complete | 0 → 0 |
| 8 | STOP OBSERVED_COMPLETION | terminal | PASS / PASS | complete | 0 → 0 |

Terminal obligations: forecast=PASS (), method-assessment=PASS (), method-review=PASS ().
Terminal global categories: HARD_OR_SCOPE_CHECK.
Optional unexamined producers: 0.
Actual lifecycle: BUILT; executor effects: 1; observed loss: 0; environment loss: 0.

## finite-blocked

| Step | Selected request / API result | Origin | A / B before | Required review | Observed loss before → after |
|---:|---|---|---|---|---:|
| 0 | revision:model-ab → PASS | exact-work-route | UNKNOWN / UNKNOWN | unresolved | 10 → 10 |
| 1 | STOP TASK_RESOLVED_LIVE_BLOCKED | terminal | UNKNOWN / PASS | complete | 10 → 10 |

Terminal obligations: forecast=PASS (), method-assessment=PASS ().
Terminal global categories: LIVE_POLICY_BLOCK, POLICY_DISAGREEMENT.
Optional unexamined producers: 0.
Actual lifecycle: DRAFT; executor effects: 0; observed loss: 10; environment loss: 10.

## finite-unavailable

| Step | Selected request / API result | Origin | A / B before | Required review | Observed loss before → after |
|---:|---|---|---|---|---:|
| 0 | request:source-b → UNKNOWN | exact-work-route | PASS / UNKNOWN | complete | 10 → 10 |
| 1 | STOP WAITING_EXTERNAL_OPPORTUNITY | terminal | PASS / UNKNOWN | complete | 10 → 10 |

Terminal obligations: forecast=PASS (), source-b=UNKNOWN (MISSING_ASSESSMENT,NO_REGISTERED_ROUTE).
Terminal global categories: NO_REGISTERED_ROUTE, POLICY_DISAGREEMENT.
Optional unexamined producers: 0.
Actual lifecycle: DRAFT; executor effects: 0; observed loss: 10; environment loss: 10.

## finite-freshness

| Step | Selected request / API result | Origin | A / B before | Required review | Observed loss before → after |
|---:|---|---|---|---|---:|
| 0 | deduction:r-competing → PASS | exact-work-route | UNKNOWN / UNKNOWN | unresolved | 10 → 10 |
| 1 | request:missing-premise → PASS | exact-work-route | PASS / UNKNOWN | unresolved | 10 → 10 |
| 2 | adopt:premise-4 → PASS | received-report-adapter | PASS / UNKNOWN | unresolved | 10 → 10 |
| 3 | deduction:r-estimate → STALE | exact-work-route | PASS / UNKNOWN | unresolved | 10 → 10 |
| 4 | deduction:r-estimate → PASS | exact-work-route | PASS / UNKNOWN | unresolved | 10 → 10 |
| 5 | STOP OBJECTION_OR_UNKNOWN_APPLICABILITY | terminal | PASS / UNKNOWN | complete | 10 → 10 |

Terminal obligations: forecast=PASS (), method-assessment=UNKNOWN (MISSING_ASSESSMENT,NO_REGISTERED_ROUTE).
Terminal global categories: APPLICABILITY_REQUIRES_REVIEW, NO_REGISTERED_ROUTE, POLICY_DISAGREEMENT.
Optional unexamined producers: 0.
Actual lifecycle: DRAFT; executor effects: 0; observed loss: 10; environment loss: 10.

## finite-adverse

| Step | Selected request / API result | Origin | A / B before | Required review | Observed loss before → after |
|---:|---|---|---|---|---:|
| 0 | deduction:r-objection → PASS | exact-work-route | PASS / PASS | unresolved | 10 → 10 |
| 1 | STOP OBJECTION_OR_UNKNOWN_APPLICABILITY | terminal | FAIL / FAIL | complete | 10 → 10 |

Terminal obligations: forecast=PASS (), source-b=PASS ().
Terminal global categories: LIVE_POLICY_BLOCK, OBJECTION_REQUIRES_REVIEW.
Optional unexamined producers: 0.
Actual lifecycle: DRAFT; executor effects: 0; observed loss: 10; environment loss: 10.

## native-positive

| Step | Selected request / API result | Origin | A / B before | Required review | Observed loss before → after |
|---:|---|---|---|---|---:|
| 0 | deduction:r-competing → PASS | exact-work-route | UNKNOWN / UNKNOWN | unresolved | 10 → 10 |
| 1 | request:missing-premise → PASS | exact-work-route | PASS / UNKNOWN | unresolved | 10 → 10 |
| 2 | adopt:premise-4 → PASS | received-report-adapter | PASS / UNKNOWN | unresolved | 10 → 10 |
| 3 | deduction:r-estimate → PASS | exact-work-route | PASS / UNKNOWN | unresolved | 10 → 10 |
| 4 | reserve:attempt → PASS | fresh-live-authorization | PASS / PASS | complete | 10 → 10 |
| 5 | dispatch:attempt → PASS | fresh-live-authorization | PASS / PASS | complete | 10 → 10 |
| 6 | request:product → PASS | existing-operational-control | PASS / PASS | complete | 10 → 10 |
| 7 | request:health → PASS | existing-operational-control | PASS / PASS | complete | 10 → 10 |
| 8 | request:health → PASS | existing-operational-control | PASS / PASS | complete | 10 → 10 |
| 9 | request:health → PASS | existing-operational-control | PASS / PASS | complete | 10 → 0 |
| 10 | complete:attempt → PASS | existing-operational-control | PASS / PASS | complete | 0 → 0 |
| 11 | STOP OBSERVED_COMPLETION | terminal | PASS / PASS | complete | 0 → 0 |

Terminal obligations: forecast=PASS (), method-assessment=PASS ().
Terminal global categories: HARD_OR_SCOPE_CHECK.
Optional unexamined producers: 0.
Actual lifecycle: BUILT; executor effects: 1; observed loss: 0; environment loss: 0.

## native-shared

| Step | Selected request / API result | Origin | A / B before | Required review | Observed loss before → after |
|---:|---|---|---|---|---:|
| 0 | revision:model-ab → PASS | exact-work-route | PASS / UNKNOWN | unresolved | 10 → 10 |
| 1 | reserve:attempt → PASS | fresh-live-authorization | PASS / PASS | complete | 10 → 10 |
| 2 | dispatch:attempt → PASS | fresh-live-authorization | PASS / PASS | complete | 10 → 10 |
| 3 | request:product → PASS | existing-operational-control | PASS / PASS | complete | 10 → 10 |
| 4 | request:health → PASS | existing-operational-control | PASS / PASS | complete | 10 → 10 |
| 5 | request:health → PASS | existing-operational-control | PASS / PASS | complete | 10 → 10 |
| 6 | request:health → PASS | existing-operational-control | PASS / PASS | complete | 10 → 0 |
| 7 | complete:attempt → PASS | existing-operational-control | PASS / PASS | complete | 0 → 0 |
| 8 | STOP OBSERVED_COMPLETION | terminal | PASS / PASS | complete | 0 → 0 |

Terminal obligations: forecast=PASS (), method-assessment=PASS (), method-review=PASS ().
Terminal global categories: HARD_OR_SCOPE_CHECK.
Optional unexamined producers: 0.
Actual lifecycle: BUILT; executor effects: 1; observed loss: 0; environment loss: 0.

## native-blocked

| Step | Selected request / API result | Origin | A / B before | Required review | Observed loss before → after |
|---:|---|---|---|---|---:|
| 0 | revision:model-ab → PASS | exact-work-route | UNKNOWN / UNKNOWN | unresolved | 10 → 10 |
| 1 | STOP TASK_RESOLVED_LIVE_BLOCKED | terminal | UNKNOWN / PASS | complete | 10 → 10 |

Terminal obligations: forecast=PASS (), method-assessment=PASS ().
Terminal global categories: LIVE_POLICY_BLOCK, POLICY_DISAGREEMENT.
Optional unexamined producers: 0.
Actual lifecycle: DRAFT; executor effects: 0; observed loss: 10; environment loss: 10.

## native-unavailable

| Step | Selected request / API result | Origin | A / B before | Required review | Observed loss before → after |
|---:|---|---|---|---|---:|
| 0 | request:source-b → UNKNOWN | exact-work-route | PASS / UNKNOWN | complete | 10 → 10 |
| 1 | STOP WAITING_EXTERNAL_OPPORTUNITY | terminal | PASS / UNKNOWN | complete | 10 → 10 |

Terminal obligations: forecast=PASS (), source-b=UNKNOWN (MISSING_ASSESSMENT,NO_REGISTERED_ROUTE).
Terminal global categories: NO_REGISTERED_ROUTE, POLICY_DISAGREEMENT.
Optional unexamined producers: 0.
Actual lifecycle: DRAFT; executor effects: 0; observed loss: 10; environment loss: 10.

## native-freshness

| Step | Selected request / API result | Origin | A / B before | Required review | Observed loss before → after |
|---:|---|---|---|---|---:|
| 0 | deduction:r-competing → PASS | exact-work-route | UNKNOWN / UNKNOWN | unresolved | 10 → 10 |
| 1 | request:missing-premise → PASS | exact-work-route | PASS / UNKNOWN | unresolved | 10 → 10 |
| 2 | adopt:premise-4 → PASS | received-report-adapter | PASS / UNKNOWN | unresolved | 10 → 10 |
| 3 | deduction:r-estimate → STALE | exact-work-route | PASS / UNKNOWN | unresolved | 10 → 10 |
| 4 | deduction:r-estimate → PASS | exact-work-route | PASS / UNKNOWN | unresolved | 10 → 10 |
| 5 | STOP OBJECTION_OR_UNKNOWN_APPLICABILITY | terminal | PASS / UNKNOWN | complete | 10 → 10 |

Terminal obligations: forecast=PASS (), method-assessment=UNKNOWN (MISSING_ASSESSMENT,NO_REGISTERED_ROUTE).
Terminal global categories: APPLICABILITY_REQUIRES_REVIEW, NO_REGISTERED_ROUTE, POLICY_DISAGREEMENT.
Optional unexamined producers: 0.
Actual lifecycle: DRAFT; executor effects: 0; observed loss: 10; environment loss: 10.

## native-adverse

| Step | Selected request / API result | Origin | A / B before | Required review | Observed loss before → after |
|---:|---|---|---|---|---:|
| 0 | deduction:r-objection → PASS | exact-work-route | PASS / PASS | unresolved | 10 → 10 |
| 1 | STOP OBJECTION_OR_UNKNOWN_APPLICABILITY | terminal | FAIL / FAIL | complete | 10 → 10 |

Terminal obligations: forecast=PASS (), source-b=PASS ().
Terminal global categories: LIVE_POLICY_BLOCK, OBJECTION_REQUIRES_REVIEW.
Optional unexamined producers: 0.
Actual lifecycle: DRAFT; executor effects: 0; observed loss: 10; environment loss: 10.
