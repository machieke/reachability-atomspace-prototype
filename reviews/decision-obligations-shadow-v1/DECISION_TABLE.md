# Detached decision-obligation comparison

A is the unchanged all-current interpretation. B is an experimental declared obligation interpretation. No shadow result authorizes actions.

| Session / snapshot | Role manifest | A numerical / scoped | B numerical / scoped | B blocking checks |
|---|---|---|---|---|
| finite-adequate-direct / base | alternatives | PASS / PASS | PASS / PASS | COMPLETE |
| finite-weak-augmented / before | alternatives | PASS / PASS | PASS / PASS | COMPLETE |
| finite-weak-augmented / after | alternatives | UNKNOWN / UNKNOWN | PASS / PASS | COMPLETE |
| finite-weak-augmented / after | mandatory_method | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | obligation:method:UNKNOWN |
| finite-weak-augmented / after | all_assessments | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | obligation:forecast:UNKNOWN |
| finite-only-weak / weak | alternatives | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | obligation:forecast:UNKNOWN |
| finite-only-weak / weak | mandatory_method | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | obligation:observed:UNKNOWN, obligation:method:UNKNOWN |
| finite-missing-mandatory / missing | alternatives | PASS / PASS | PASS / PASS | COMPLETE |
| finite-missing-mandatory / missing | two_sources | PASS / PASS | UNKNOWN / UNKNOWN | obligation:source-b:UNKNOWN |
| finite-missing-mandatory / missing | required_model | PASS / PASS | UNKNOWN / UNKNOWN | obligation:revision-model:UNKNOWN |
| finite-objections / outside | alternatives | FAIL / FAIL | FAIL / FAIL | strength_objections:FAIL |
| finite-objections / opposite | alternatives | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | opposite_literal:UNKNOWN |
| finite-lineage-copies / one | alternatives | PASS / PASS | PASS / PASS | COMPLETE |
| finite-lineage-copies / one | two_sources | PASS / PASS | UNKNOWN / UNKNOWN | obligation:source-b:UNKNOWN |
| finite-lineage-copies / copies | alternatives | PASS / PASS | UNKNOWN / UNKNOWN | unclassified:probability-belief/v1:aaa877fcd146c8842b2d06699636197c60510b450475f0151e7f9976f3304197:UNKNOWN |
| finite-lineage-copies / copies | two_sources | PASS / PASS | UNKNOWN / UNKNOWN | unclassified:probability-belief/v1:aaa877fcd146c8842b2d06699636197c60510b450475f0151e7f9976f3304197:UNKNOWN, obligation:source-b:UNKNOWN |
| finite-lineage-copies / distinct-root | alternatives | PASS / PASS | PASS / PASS | COMPLETE |
| finite-lineage-copies / distinct-root | two_sources | PASS / PASS | PASS / PASS | COMPLETE |
| finite-revision-family / parents | alternatives | UNKNOWN / UNKNOWN | PASS / PASS | COMPLETE |
| finite-revision-family / parents | all_assessments | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | obligation:forecast:UNKNOWN |
| finite-revision-family / parents | required_model | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | obligation:revision-model:UNKNOWN |
| finite-revision-family / parents-and-child | alternatives | UNKNOWN / UNKNOWN | PASS / PASS | COMPLETE |
| finite-revision-family / parents-and-child | all_assessments | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | obligation:forecast:UNKNOWN |
| finite-revision-family / parents-and-child | required_model | UNKNOWN / UNKNOWN | PASS / PASS | COMPLETE |
| finite-freshness / before | alternatives | PASS / PASS | PASS / PASS | COMPLETE |
| finite-freshness / sole-revoked | alternatives | STALE / STALE | STALE / STALE | same_literal_ledger:STALE, obligation:forecast:STALE |
| finite-freshness / replacement | alternatives | PASS / PASS | PASS / PASS | COMPLETE |
| finite-freshness / surviving-alternative | alternatives | PASS / PASS | PASS / PASS | COMPLETE |
| finite-scope-bounds / base | alternatives | PASS / PASS | PASS / PASS | COMPLETE |
| finite-scope-bounds / context | alternatives | PASS / FAIL | PASS / FAIL | exact_scope_and_criterion:FAIL |
| finite-scope-bounds / time | alternatives | PASS / STALE | PASS / STALE | logical_time:STALE |
| finite-scope-bounds / unsupported | alternatives | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | UNSUPPORTED_APPLICABILITY |
| finite-scope-bounds / unclassified | alternatives | PASS / PASS | UNKNOWN / UNKNOWN | unclassified:probability-belief/v1:2ef17ee941847f710713a57b48187738a2a82cc1d89e6f1fac7f963dd2a62528:UNKNOWN, obligation:forecast:UNKNOWN |
| finite-scope-bounds / hard-unknown | alternatives | PASS / UNKNOWN | PASS / UNKNOWN | required:owner:UNKNOWN |
| finite-scope-bounds / incomplete | alternatives | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | INCOMPLETE_OR_UNSUPPORTED_CAPTURE |
| finite-scope-bounds / record-bound | alternatives | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | RECORD_BOUND |
| finite-scope-bounds / classification-bound | alternatives | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | CLASSIFICATION_BOUND |
| finite-scope-bounds / witness-bound | alternatives | PASS / PASS | UNKNOWN / UNKNOWN | WITNESS_BOUND |
| finite-adverse-inference / before | alternatives | PASS / PASS | PASS / PASS | COMPLETE |
| finite-adverse-inference / after | alternatives | FAIL / FAIL | FAIL / FAIL | strength_objections:FAIL |
| finite-historical-anchor / published-final | historical-alternatives | UNKNOWN / UNKNOWN | PASS / PASS | COMPLETE |
| finite-historical-anchor / published-final | historical-mandatory | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | obligation:model:UNKNOWN |
| native-weak-augmented / before | alternatives | PASS / PASS | PASS / PASS | COMPLETE |
| native-weak-augmented / after | alternatives | UNKNOWN / UNKNOWN | PASS / PASS | COMPLETE |
| native-weak-augmented / after | mandatory_method | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | obligation:method:UNKNOWN |
| native-weak-augmented / after | all_assessments | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | obligation:forecast:UNKNOWN |
| native-revision-family / parents | alternatives | UNKNOWN / UNKNOWN | PASS / PASS | COMPLETE |
| native-revision-family / parents | all_assessments | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | obligation:forecast:UNKNOWN |
| native-revision-family / parents | required_model | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | obligation:revision-model:UNKNOWN |
| native-revision-family / parents-and-child | alternatives | UNKNOWN / UNKNOWN | PASS / PASS | COMPLETE |
| native-revision-family / parents-and-child | all_assessments | UNKNOWN / UNKNOWN | UNKNOWN / UNKNOWN | obligation:forecast:UNKNOWN |
| native-revision-family / parents-and-child | required_model | UNKNOWN / UNKNOWN | PASS / PASS | COMPLETE |
| native-adverse-inference / before | alternatives | PASS / PASS | PASS / PASS | COMPLETE |
| native-adverse-inference / after | alternatives | FAIL / FAIL | FAIL / FAIL | strength_objections:FAIL |

Every pair JSON contains the exact manifest, full supporting/opposing records, retired records, applicability explanations, all witness IDs and basis hashes. Capture JSON also includes the full unfiltered context ledger, registries and hard checks. Diagnostic input perturbations are explicitly labeled. Historical role assignments are counterfactual.
