# Preserved frozen boundary

Before new-policy execution, the unchanged frozen coordinator and original
`alternatives` fixture were run at capacity 48, q16/q48, all three orderers, finite
and actual native formulas. All 12 runs passed conformance. This reproduces an
outcome limitation, not a gate failure. The source binding records publication
`71c32df66d1c08143621f1e4c6005da31fac2565`; the frozen measured implementation remains
`0134092b9766f8fc9a9a1735cee8b7f2372e830c`.

The archive's `development/frozen-boundary/` contains untouched runs, SQLite
ledgers, receipts, source binding and seal. `validation/frozen-boundary-analysis.json`
annotates every tranche and preserves selected identities and ordered native answer
sets. Original event records remain authoritative where legacy timing is absent.

| Query budget | Frozen orderer | Producers known after query | First join selected after query | Further queries before attempt/end | Complete tuple visits, episode | Terminal certified/external loss |
|---:|---|---:|---:|---:|---:|---|
| 16 | queue/local | 4 | 13 | 9 | 0 | 10/10 |
| 16 | flow | 4 | never | 12 | 0 | 10/10 |
| 48 | queue/local | 4 | 13 | 9 | 6 | 0/0 |
| 48 | flow | 4 | never | 44 | 0 | 10/10 |

Each row holds in both formula modes. Queue/local at q16 enter the join routine
with only three query credits and stop at `JOIN_QUERY_BUDGET` before its premise
queries. Their selected job is not a completed assembly attempt. Flow at q48 also
discovers `b-step1` at query 41; its join remains pending through seven more queries.
No workspace eviction occurs in these frozen trajectories.

At query 4, `c-other` and `d-target` are known descriptors and their native rules are
resident. Twelve query credits would cover the new conservative resident service
bound (six join reads plus six preparation reads), with the actual result sizes
still unknown. This is an affordable *attempt*, not knowledge of complete premises.
Only the queue/local q48 join subsequently establishes `c-other`'s ordered native
support alternatives and forms candidates. The selected bundle is already resident:
exact rematerialization costs zero additional native queries, and the original
counted bundle is pinned. The q16 and losing flow runs form no candidate to prepare.

The first ordering divergence is expansion 2 (zero based): queue/local inspect
positive reports, while flow inspects the opposite literal's current supports at
activation 0.1805; the two known producer anchors each have activation
0.01008827496 at that choice. Queue's score is zero and its FIFO serial controls the order.
That early difference alone is not assigned the terminal loss. The decisive
recorded boundary spans the whole tranche: flow continues inspecting premise
leaves, reaches q48 without any join, and has no executable candidate. Queue/local
reach `c-other` at q13 and retain the resulting candidate even when the later
`d-target` job at q44 cannot fit its six queries.

The successful path still requires certified deduction, authoritative reserve,
dispatch, exact-product observation and three health observations. Certified outstanding loss stays 10
through deduction, reserve, acknowledgment, product observation and the first two
health samples. It becomes 0 only after the third health observation. The evaluator
external-loss endpoint becomes 0 at the first successful health observation; it
does not replace the three-sample authoritative durability requirement. Completion
then succeeds; the fixed stopping policy also charges later inference/discovery
work before termination. No stale selection occurs in this diagnostic. The failing
flow path executes none of those operations, and its external loss remains 10.

Zero tuple visits do not establish missing premises, global impossibility or
semantic invalidity. These reused cases are diagnostics, not holdout evidence.
