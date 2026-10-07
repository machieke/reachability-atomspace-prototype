# Actual trajectories and scope

Measured implementation/auditor `b509d2b8d7388a570b5a666e1c845b95d207ad20`. All initial estimates are adopted source records of depth zero. Six parent structures run in finite and actual native modes, not twelve independent samples.

| Parent | Accepted depth / calls | Selections / work / queries | First final (tick:slot) | Dispatch / physical effect tick | Physical goal / observed completion tick | J_world / J_certified |
|---|---|---|---|---|---|---|
| two-hop | 2 / 2 | 18 / 18 / 12 | 0:3 | 0 / 1 | 3 / 3 | 30 / 30 |
| three-hop | 3 / 3 | 19 / 19 / 12 | 0:4 | 0 / 1 | 3 / 3 | 30 / 30 |
| shared | 3 / 4 | 19 / 19 / 11 | 0:4 | 0 / 1 | 3 / 3 | 30 / 30 |
| unavailable | 0 / 0 | 1 / 1 / 1 | None | None / None | None / None | 90 / 90 |
| replacement | 2 / 3 | 19 / 19 / 11 | 0:5 | 0 / 1 | 3 / 3 | 30 / 30 |
| adverse | 2 / 3 | 5 / 5 / 1 | 0:4 | None / None | None / None | 90 / 90 |

The two-hop chain requests its missing upstream report, adopts it, commits r-mid, and only then constructs the exact r-final tuple. The three-hop chain adds r-next between those commits. No intermediate/final estimate or sequence of chosen operations comes from the fixture. The independent audit accounts for every accepted estimate as either initial source adoption or a recorded selected commit.

The shared DAG has four deduction calls but longest real depth three. One r-mid record supplies two downstream computations (r-next and r-short); r-next then supplies r-final. Two final estimates coexist with different confidence and shared ancestry. They are not pooled as independent evidence.

The replacement parent is a predeclared forced boundary. After tick-0 slot 2, the original leaf is revoked and an equal-valued report with a new ID/root is received. The existing ledger immediately retires the first r-mid. The consumer selects adoption and a fresh r-mid; r-final uses that new revision. The old record remains historical. This is neither automatic evidence supersession nor an action-repair procedure.

The unavailable parent makes one query and retains UNKNOWN, with no deduction, imaginary intermediate, dispatch or physical success. In the adverse parent r-adverse is investigated alongside the positive chain; its low-strength committed estimate remains in the full authoritative scope. Completing the favorable route does not permit dispatch. Both A and B retain FAIL at the end.

All four positive parents dispatch at tick 0, produce the physical effect at tick 1 and reach physical/observed completion at tick 3. More numerical work fits the existing eight-operation tick bound in this cohort, so modeled loss/time is neutral across those depths. Shared/replacement cases consume all eight slots before product observation and use the next scheduled opportunity. This equality is not a latency or scheduling advantage; wall times and work still differ.

World and recognized state are measured through tick 8. J_certified uses the existing observed projection after each tick's operations; raw rows also preserve temporary stale-window reopening on public clock advancement before new health samples. Numerical inference itself creates no relief. The two negative parents retain physical and observed loss ten; their J_world and J_certified are 90.

| Parent | Commit tick:slot | Rule | Actual depth | Strength | Confidence | Current at horizon |
|---|---|---|---:|---:|---:|---|
| two-hop | 0:2 | r-mid | 1 | 0.828125 | 0.7698440551757812 | True |
| two-hop | 0:3 | r-final | 2 | 0.8076171875 | 0.5983042489970103 | True |
| three-hop | 0:2 | r-mid | 1 | 0.8828125 | 0.8248329162597656 | True |
| three-hop | 0:3 | r-next | 2 | 0.8349609375 | 0.6613288205699064 | True |
| three-hop | 0:4 | r-final | 3 | 0.7930908203125 | 0.5014949909936534 | True |
| shared | 0:2 | r-mid | 1 | 0.8828125 | 0.8248329162597656 | True |
| shared | 0:3 | r-next | 2 | 0.8349609375 | 0.6613288205699064 | True |
| shared | 0:4 | r-short | 2 | 0.7930908203125 | 0.6227513060366618 | True |
| shared | 0:5 | r-final | 3 | 0.7930908203125 | 0.5014949909936534 | True |
| replacement | 0:2 | r-mid | 1 | 0.8828125 | 0.8248329162597656 | False |
| replacement | 0:4 | r-mid | 1 | 0.8828125 | 0.8248329162597656 | True |
| replacement | 0:5 | r-final | 2 | 0.8349609375 | 0.6613288205699064 | True |
| adverse | 0:0 | r-adverse | 1 | 0.1171875 | 0.054988861083984375 | True |
| adverse | 0:3 | r-mid | 1 | 0.8828125 | 0.8248329162597656 | True |
| adverse | 0:4 | r-final | 2 | 0.8349609375 | 0.6613288205699064 | True |

Exact IDs, ordered parents, roots, ancestors and support-change captures are in `validation/ancestry.json`; each raw selected result retains pre/post certificates, proposal and commit. Native and finite values agree under the bit-level contract. The explicit fixture joint checks source strengths and declared Markov-derived conditionals; each runtime certificate still covers only its selected three propositions. The adverse family is not asserted to share that global joint.

Across the twelve executions: 162 selections, 96 acquisitions, 30 formula calls including 15 fresh native calls. Selected results: `{'PASS': 156, 'UNKNOWN': 6}`. The cohort has no stale/rejected numerical calls; the separate native boundary test records a real formula result rejected after upstream revocation. It is not added to the core call population.

The frozen one-step bridge remains out of scope on initially missing deeper paths. A related one-hop test matches selected operations, stop reasons and observed completion between old and new consumers on identical snapshots. Neither comparison supports a general scheduling-performance claim. The new review is finite and registry-bound, not discovery of every possible contrary inference.
