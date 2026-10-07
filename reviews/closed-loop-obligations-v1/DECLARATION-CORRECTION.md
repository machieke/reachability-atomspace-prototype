# Selector identity correction before final measurement

The initial declaration at 1d10fbf reused class IDs across the forecast and mandatory
method groups. Frozen evaluators require each selector ID to be assigned once.
Development episodes positive/shared/blocked/freshness therefore returned
AMBIGUOUS_OR_UNASSIGNED_CLASSES before any controller selection. Unavailable and
adverse were well formed. All raw failures and the original declaration are kept
under development/ in the review bundle and in the preregistration commit.

This correction uses distinct selector IDs with exactly the same producer/source
eligibility when the intended requirements share a producer, following the existing
shared-method representation. No source, method revision, root restriction, truth
value, threshold, any/all mode, mandatory requirement or environment response was
retuned. The unused revision selector in the deduction variant is removed; its
existing forecast selector has identical eligibility. Frozen code remains unchanged.
The corrected declaration is committed before running the consumer again.
