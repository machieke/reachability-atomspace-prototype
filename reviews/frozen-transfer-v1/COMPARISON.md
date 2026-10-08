# Frozen transfer evaluation

Measured source: `c28a7dce95f446a6e2590c1910a9e7c1fe6d423a`. Twelve declared parent structures, two retrieval arms, native PLN in both. Conformance is separate from effectiveness.

| Parent | Arm | Conformance | Depth / calls | Physical / recognized first completion | J physical / recognized | Final stop | Seconds |
|---|---|---|---|---|---|---|---:|
| A1-right-composition | TRANSFER-scan | PASS | 2 / 2 | 3 / 3 | 30 / 30 | OBSERVED_COMPLETION | 7.410625 |
| A1-right-composition | TRANSFER-native | PASS | 2 / 2 | 3 / 3 | 30 / 30 | OBSERVED_COMPLETION | 11.704171 |
| A2-two-sided | TRANSFER-native | PASS | 2 / 3 | 4 / 6 | 40 / 60 | OBSERVED_COMPLETION | 10.543503 |
| A2-two-sided | TRANSFER-scan | PASS | 2 / 3 | 4 / 6 | 40 / 60 | OBSERVED_COMPLETION | 6.417152 |
| A3-shared-suffix-review | TRANSFER-scan | PASS | 3 / 4 | 3 / 3 | 30 / 30 | OBSERVED_COMPLETION | 9.565434 |
| A3-shared-suffix-review | TRANSFER-native | PASS | 3 / 4 | 3 / 3 | 30 / 30 | OBSERVED_COMPLETION | 14.490591 |
| A4-intermediate-alternatives | TRANSFER-native | PASS | 2 / 4 | 3 / 3 | 30 / 30 | OBSERVED_COMPLETION | 14.530490 |
| A4-intermediate-alternatives | TRANSFER-scan | PASS | 2 / 4 | 3 / 3 | 30 / 30 | OBSERVED_COMPLETION | 9.468608 |
| B1-mixed-opportunities | TRANSFER-scan | PASS | 2 / 2 | None / None | 90 / 90 | WAITING_EXTERNAL_OPPORTUNITY | 3.286260 |
| B1-mixed-opportunities | TRANSFER-native | PASS | 2 / 2 | None / None | 90 / 90 | WAITING_EXTERNAL_OPPORTUNITY | 6.076309 |
| B2-source-role-copies | TRANSFER-native | PASS | 2 / 4 | None / None | 90 / 90 | OBJECTION_OR_UNKNOWN_APPLICABILITY | 6.052594 |
| B2-source-role-copies | TRANSFER-scan | PASS | 2 / 4 | None / None | 90 / 90 | OBJECTION_OR_UNKNOWN_APPLICABILITY | 4.161197 |
| B3-low-confidence-branch | TRANSFER-scan | PASS | 3 / 4 | None / None | 90 / 90 | NO_KNOWN_SUPPORTED_ROUTE | 3.999399 |
| B3-low-confidence-branch | TRANSFER-native | PASS | 3 / 4 | None / None | 90 / 90 | NO_KNOWN_SUPPORTED_ROUTE | 7.101045 |
| B4-acquisition-headroom | TRANSFER-native | PASS | 1 / 1 | None / None | 90 / 90 | WORK_OR_ACQUISITION_EXHAUSTED | 5.822117 |
| B4-acquisition-headroom | TRANSFER-scan | PASS | 1 / 1 | None / None | 90 / 90 | WORK_OR_ACQUISITION_EXHAUSTED | 3.013403 |
| C1-shared-replacement | TRANSFER-scan | PASS | 3 / 10 | 4 / 6 | 40 / 60 | OBSERVED_COMPLETION | 11.993057 |
| C1-shared-replacement | TRANSFER-native | PASS | 3 / 10 | 4 / 6 | 40 / 60 | OBSERVED_COMPLETION | 18.237767 |
| C2-late-adverse-route | TRANSFER-native | PASS | 2 / 4 | None / None | 90 / 90 | OBJECTION_OR_UNKNOWN_APPLICABILITY | 6.992798 |
| C2-late-adverse-route | TRANSFER-scan | PASS | 2 / 4 | None / None | 90 / 90 | OBJECTION_OR_UNKNOWN_APPLICABILITY | 4.486307 |
| C3-replacement-unobservable | TRANSFER-scan | PASS | 3 / 6 | 3 / None | 30 / 90 | WAITING_EXTERNAL_OUTCOME | 5.641227 |
| C3-replacement-unobservable | TRANSFER-native | PASS | 3 / 6 | 3 / None | 30 / 90 | WAITING_EXTERNAL_OUTCOME | 9.484284 |
| C4-regression-reassessment | TRANSFER-native | PASS | 3 / 8 | 3 / 3 | 60 / 60 | WAITING_EXTERNAL_OUTCOME | 20.005338 |
| C4-regression-reassessment | TRANSFER-scan | PASS | 3 / 8 | 3 / 3 | 60 / 60 | WAITING_EXTERNAL_OUTCOME | 13.560870 |

Every result retains simultaneous conditions, exact sequences, live/mandatory status, observations, replacements, monitoring gaps and both loss trajectories in result.json/report.json. Scan shares the same cognitive policy; parity is not superiority. A completed history can coexist with current reopened loss. Unresolved does not mean correct abstention; counterfactual task feasibility remains explicitly limited.
