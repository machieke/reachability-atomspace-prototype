# Bounded multi-hop outcomes

Measured source: `b509d2b8d7388a570b5a666e1c845b95d207ad20`. Six parent structures in two formula modes; no scheduler comparison.

| Structure | Mode | Actual depth | Formula calls | First completion | J_world / J_certified | Final observed loss | Stop |
|---|---|---:|---:|---|---|---:|---|
| two-hop | finite | 2 | 2 | 3 | 30 / 30 | 0 | OBSERVED_COMPLETION |
| three-hop | finite | 3 | 3 | 3 | 30 / 30 | 0 | OBSERVED_COMPLETION |
| shared | finite | 3 | 4 | 3 | 30 / 30 | 0 | OBSERVED_COMPLETION |
| unavailable | finite | 0 | 0 | None | 90 / 90 | 10 | WAITING_EXTERNAL_OPPORTUNITY |
| replacement | finite | 2 | 3 | 3 | 30 / 30 | 0 | OBSERVED_COMPLETION |
| adverse | finite | 2 | 3 | None | 90 / 90 | 10 | OBJECTION_OR_UNKNOWN_APPLICABILITY |
| two-hop | native | 2 | 2 | 3 | 30 / 30 | 0 | OBSERVED_COMPLETION |
| three-hop | native | 3 | 3 | 3 | 30 / 30 | 0 | OBSERVED_COMPLETION |
| shared | native | 3 | 4 | 3 | 30 / 30 | 0 | OBSERVED_COMPLETION |
| unavailable | native | 0 | 0 | None | 90 / 90 | 10 | WAITING_EXTERNAL_OPPORTUNITY |
| replacement | native | 2 | 3 | 3 | 30 / 30 | 0 | OBSERVED_COMPLETION |
| adverse | native | 2 | 3 | None | 90 / 90 | 10 | OBJECTION_OR_UNKNOWN_APPLICABILITY |
