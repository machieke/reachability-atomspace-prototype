# Parent sequences and substantive outcomes

All cases are retained. The scan sequence below is the common semantic sequence where parity passes; full native traces are independently retained and audited. An observed sequence explains where the controller stopped; it is not a tested counterfactual causal ablation. Logical tick/slot is separate from wall time. Exact premise IDs, full frontiers and certificates are in each raw trace.

## A1-right-composition

The controller requested and adopted the missing suffix input before running r00 and then r01. Reserve and dispatch followed at tick 0. The immediate product request returned UNKNOWN; tick 1 supplied product evidence and the first health sample. Samples at ticks 1, 2 and 3 established recognized completion at tick 3, matching physical completion. Monitoring continued through tick 8. Two deductions were actual native calls, not an observed final conclusion.

Acquire a missing suffix input, then consume its inferred right-hand conditional.

Final stop: `OBSERVED_COMPLETION`; live A `PASS`, advisory B `PASS`; required review complete: `True`. Conditions: completed-historically, waiting-or-observation-unavailable. Unresolved roles: []; unresolved producers: [].

Physical / recognized first completion: 3 / 3. Final observed loss: 0; physical deficit: 0. Integrals: world 30, recognized 30. Work/acquisitions/selections: {'acquisitions': 12, 'selections': 18, 'work': 18}.

| Tick:slot | Selected operation | Result | Work / acquisitions | Recognized loss after |
|---|---|---|---|---:|
| 0:0 | request observe-02 | PASS | 1 / 1 | 10 |
| 0:1 | adopt input-02 | PASS | 2 / 1 | 10 |
| 0:2 | deduction r00 | PASS | 3 / 1 | 10 |
| 0:3 | deduction r01 | PASS | 4 / 1 | 10 |
| 0:4 | reserve attempt | PASS | 5 / 1 | 10 |
| 0:5 | dispatch attempt | PASS | 6 / 1 | 10 |
| 0:6 | request product | UNKNOWN | 7 / 2 | 10 |
| 1:0 | request product | PASS | 8 / 3 | 10 |
| 1:1 | request health | PASS | 9 / 4 | 10 |
| 2:0 | request health | PASS | 10 / 5 | 10 |
| 3:0 | request health | PASS | 11 / 6 | 0 |
| 3:1 | complete attempt | PASS | 12 / 6 | 0 |
| 4:0 | request health | PASS | 13 / 7 | 0 |
| 4:1 | request product | PASS | 14 / 8 | 0 |
| 5:0 | request health | PASS | 15 / 9 | 0 |
| 6:0 | request health | PASS | 16 / 10 | 0 |
| 7:0 | request health | PASS | 17 / 11 | 0 |
| 8:0 | request health | PASS | 18 / 12 | 0 |

Observed trajectory `(tick, physical loss, recognized loss, stage)`: [(0, 10, 10, 'DRAFT'), (1, 10, 10, 'DRAFT'), (2, 10, 10, 'DRAFT'), (3, 0, 0, 'BUILT'), (4, 0, 0, 'BUILT'), (5, 0, 0, 'BUILT'), (6, 0, 0, 'BUILT'), (7, 0, 0, 'BUILT'), (8, 0, 0, 'BUILT')]

Repeated-work accounting: {'repeated_same_basis_selections': 0, 'same_logical_work_new_basis_retries': 0, 'scope': 'Full relevant-basis identity checked independently for every selected operation'}. Authority effects: 1.

Actual observation replies: [(0, 'observe-02', 'PASS', None), (0, 'product', 'UNKNOWN', 'no installed artifact observed'), (1, 'product', 'PASS', None), (1, 'health', 'PASS', None), (2, 'health', 'PASS', None), (3, 'health', 'PASS', None), (4, 'health', 'PASS', None), (4, 'product', 'PASS', None), (5, 'health', 'PASS', None), (6, 'health', 'PASS', None), (7, 'health', 'PASS', None), (8, 'health', 'PASS', None)].

Monitoring/recognition gaps: [{'reasons': ['UNOBSERVED_CHANGE_OR_CLOCK_NOT_YET_PUBLISHED'], 'tick': 3}].

Interpretation: actual completion establishes this trajectory only. NOT_ESTABLISHED: no counterfactual same-information policy witness.

## A2-two-sided

Both missing inputs required request/adopt pairs, followed by three deductions and reserve. Those eight operations filled tick 0, placing dispatch at tick 1 slot 0. Its immediate product request returned UNKNOWN; the next declared product opportunity was tick 4. The world had completed physically by tick 4, but recognized completion needed health samples at ticks 4, 5 and 6. This locates the 20-unit loss-integral gap at ticks 4 and 5. It does not establish that another same-information scheduler could avoid the gap.

Combine two genuinely inferred AND branches; neither final conditional is an input.

Final stop: `OBSERVED_COMPLETION`; live A `PASS`, advisory B `PASS`; required review complete: `True`. Conditions: completed-historically, waiting-or-observation-unavailable. Unresolved roles: []; unresolved producers: [].

Physical / recognized first completion: 4 / 6. Final observed loss: 0; physical deficit: 0. Integrals: world 40, recognized 60. Work/acquisitions/selections: {'acquisitions': 9, 'selections': 17, 'work': 17}.

| Tick:slot | Selected operation | Result | Work / acquisitions | Recognized loss after |
|---|---|---|---|---:|
| 0:0 | request observe-00 | PASS | 1 / 1 | 10 |
| 0:1 | adopt input-00 | PASS | 2 / 1 | 10 |
| 0:2 | request observe-02 | PASS | 3 / 2 | 10 |
| 0:3 | adopt input-02 | PASS | 4 / 2 | 10 |
| 0:4 | deduction r00 | PASS | 5 / 2 | 10 |
| 0:5 | deduction r01 | PASS | 6 / 2 | 10 |
| 0:6 | deduction r02 | PASS | 7 / 2 | 10 |
| 0:7 | reserve attempt | PASS | 8 / 2 | 10 |
| 1:0 | dispatch attempt | PASS | 9 / 2 | 10 |
| 1:1 | request product | UNKNOWN | 10 / 3 | 10 |
| 4:0 | request product | PASS | 11 / 4 | 10 |
| 4:1 | request health | PASS | 12 / 5 | 10 |
| 5:0 | request health | PASS | 13 / 6 | 10 |
| 6:0 | request health | PASS | 14 / 7 | 0 |
| 6:1 | complete attempt | PASS | 15 / 7 | 0 |
| 7:0 | request health | PASS | 16 / 8 | 0 |
| 8:0 | request health | PASS | 17 / 9 | 0 |

Observed trajectory `(tick, physical loss, recognized loss, stage)`: [(0, 10, 10, 'DRAFT'), (1, 10, 10, 'DRAFT'), (2, 10, 10, 'DRAFT'), (3, 10, 10, 'DRAFT'), (4, 0, 10, 'DRAFT'), (5, 0, 10, 'DRAFT'), (6, 0, 0, 'BUILT'), (7, 0, 0, 'BUILT'), (8, 0, 0, 'BUILT')]

Repeated-work accounting: {'repeated_same_basis_selections': 0, 'same_logical_work_new_basis_retries': 0, 'scope': 'Full relevant-basis identity checked independently for every selected operation'}. Authority effects: 1.

Actual observation replies: [(0, 'observe-00', 'PASS', None), (0, 'observe-02', 'PASS', None), (1, 'product', 'UNKNOWN', 'no installed artifact observed'), (4, 'product', 'PASS', None), (4, 'health', 'PASS', None), (5, 'health', 'PASS', None), (6, 'health', 'PASS', None), (7, 'health', 'PASS', None), (8, 'health', 'PASS', None)].

Monitoring/recognition gaps: [{'reasons': ['MISSING_OR_STALE_OBSERVATION_UNDER_DECLARED_MODEL', 'DIFFERENT_PHYSICAL_AND_OBSERVATION_PREDICATES', 'UNOBSERVED_CHANGE_OR_CLOCK_NOT_YET_PUBLISHED'], 'tick': 4}, {'reasons': ['MISSING_OR_STALE_OBSERVATION_UNDER_DECLARED_MODEL', 'DIFFERENT_PHYSICAL_AND_OBSERVATION_PREDICATES', 'UNOBSERVED_CHANGE_OR_CLOCK_NOT_YET_PUBLISHED'], 'tick': 5}, {'reasons': ['UNOBSERVED_CHANGE_OR_CLOCK_NOT_YET_PUBLISHED'], 'tick': 6}].

Interpretation: actual completion establishes this trajectory only. NOT_ESTABLISHED: no counterfactual same-information policy witness.

## A3-shared-suffix-review

After acquiring the missing suffix input, the controller ran r00, r01, r03 and r02, reviewing both required final routes and reusing the shared inferred suffix. Four numerical calls included accepted depth 3. Dispatch occupied the last slot of tick 0; product observation and the first health sample arrived at tick 1. Both completion measures reached zero loss at tick 3.

Reuse a suffix intermediate across a short final route and a longer required route.

Final stop: `OBSERVED_COMPLETION`; live A `PASS`, advisory B `PASS`; required review complete: `True`. Conditions: completed-historically, waiting-or-observation-unavailable. Unresolved roles: []; unresolved producers: [].

Physical / recognized first completion: 3 / 3. Final observed loss: 0; physical deficit: 0. Integrals: world 30, recognized 30. Work/acquisitions/selections: {'acquisitions': 11, 'selections': 19, 'work': 19}.

| Tick:slot | Selected operation | Result | Work / acquisitions | Recognized loss after |
|---|---|---|---|---:|
| 0:0 | request observe-04 | PASS | 1 / 1 | 10 |
| 0:1 | adopt input-04 | PASS | 2 / 1 | 10 |
| 0:2 | deduction r00 | PASS | 3 / 1 | 10 |
| 0:3 | deduction r01 | PASS | 4 / 1 | 10 |
| 0:4 | deduction r03 | PASS | 5 / 1 | 10 |
| 0:5 | deduction r02 | PASS | 6 / 1 | 10 |
| 0:6 | reserve attempt | PASS | 7 / 1 | 10 |
| 0:7 | dispatch attempt | PASS | 8 / 1 | 10 |
| 1:0 | request product | PASS | 9 / 2 | 10 |
| 1:1 | request health | PASS | 10 / 3 | 10 |
| 2:0 | request health | PASS | 11 / 4 | 10 |
| 3:0 | request health | PASS | 12 / 5 | 0 |
| 3:1 | complete attempt | PASS | 13 / 5 | 0 |
| 4:0 | request health | PASS | 14 / 6 | 0 |
| 4:1 | request product | PASS | 15 / 7 | 0 |
| 5:0 | request health | PASS | 16 / 8 | 0 |
| 6:0 | request health | PASS | 17 / 9 | 0 |
| 7:0 | request health | PASS | 18 / 10 | 0 |
| 8:0 | request health | PASS | 19 / 11 | 0 |

Observed trajectory `(tick, physical loss, recognized loss, stage)`: [(0, 10, 10, 'DRAFT'), (1, 10, 10, 'DRAFT'), (2, 10, 10, 'DRAFT'), (3, 0, 0, 'BUILT'), (4, 0, 0, 'BUILT'), (5, 0, 0, 'BUILT'), (6, 0, 0, 'BUILT'), (7, 0, 0, 'BUILT'), (8, 0, 0, 'BUILT')]

Repeated-work accounting: {'repeated_same_basis_selections': 0, 'same_logical_work_new_basis_retries': 0, 'scope': 'Full relevant-basis identity checked independently for every selected operation'}. Authority effects: 1.

Actual observation replies: [(0, 'observe-04', 'PASS', None), (1, 'product', 'PASS', None), (1, 'health', 'PASS', None), (2, 'health', 'PASS', None), (3, 'health', 'PASS', None), (4, 'health', 'PASS', None), (4, 'product', 'PASS', None), (5, 'health', 'PASS', None), (6, 'health', 'PASS', None), (7, 'health', 'PASS', None), (8, 'health', 'PASS', None)].

Monitoring/recognition gaps: [{'reasons': ['UNOBSERVED_CHANGE_OR_CLOCK_NOT_YET_PUBLISHED'], 'tick': 3}].

Interpretation: actual completion establishes this trajectory only. NOT_ESTABLISHED: no counterfactual same-information policy witness.

## A4-intermediate-alternatives

The initially available intermediate producer r01 ran first. After request/adoption of the missing input, r02 ran with that first intermediate; r00 then produced the alternative, and r02 ran again with its distinct exact premise. The second final application is required alternative review, not a repeated unchanged-basis attempt. All four actual formula calls finished before reserve and dispatch at tick 0 slots 6 and 7. Completion occurred at tick 3.

Review both producers of an intermediate and every exact final application.

Final stop: `OBSERVED_COMPLETION`; live A `PASS`, advisory B `PASS`; required review complete: `True`. Conditions: completed-historically, waiting-or-observation-unavailable. Unresolved roles: []; unresolved producers: [].

Physical / recognized first completion: 3 / 3. Final observed loss: 0; physical deficit: 0. Integrals: world 30, recognized 30. Work/acquisitions/selections: {'acquisitions': 11, 'selections': 19, 'work': 19}.

| Tick:slot | Selected operation | Result | Work / acquisitions | Recognized loss after |
|---|---|---|---|---:|
| 0:0 | deduction r01 | PASS | 1 / 0 | 10 |
| 0:1 | request observe-00 | PASS | 2 / 1 | 10 |
| 0:2 | adopt input-00 | PASS | 3 / 1 | 10 |
| 0:3 | deduction r02 | PASS | 4 / 1 | 10 |
| 0:4 | deduction r00 | PASS | 5 / 1 | 10 |
| 0:5 | deduction r02 | PASS | 6 / 1 | 10 |
| 0:6 | reserve attempt | PASS | 7 / 1 | 10 |
| 0:7 | dispatch attempt | PASS | 8 / 1 | 10 |
| 1:0 | request product | PASS | 9 / 2 | 10 |
| 1:1 | request health | PASS | 10 / 3 | 10 |
| 2:0 | request health | PASS | 11 / 4 | 10 |
| 3:0 | request health | PASS | 12 / 5 | 0 |
| 3:1 | complete attempt | PASS | 13 / 5 | 0 |
| 4:0 | request health | PASS | 14 / 6 | 0 |
| 4:1 | request product | PASS | 15 / 7 | 0 |
| 5:0 | request health | PASS | 16 / 8 | 0 |
| 6:0 | request health | PASS | 17 / 9 | 0 |
| 7:0 | request health | PASS | 18 / 10 | 0 |
| 8:0 | request health | PASS | 19 / 11 | 0 |

Observed trajectory `(tick, physical loss, recognized loss, stage)`: [(0, 10, 10, 'DRAFT'), (1, 10, 10, 'DRAFT'), (2, 10, 10, 'DRAFT'), (3, 0, 0, 'BUILT'), (4, 0, 0, 'BUILT'), (5, 0, 0, 'BUILT'), (6, 0, 0, 'BUILT'), (7, 0, 0, 'BUILT'), (8, 0, 0, 'BUILT')]

Repeated-work accounting: {'repeated_same_basis_selections': 0, 'same_logical_work_new_basis_retries': 0, 'scope': 'Full relevant-basis identity checked independently for every selected operation'}. Authority effects: 1.

Actual observation replies: [(0, 'observe-00', 'PASS', None), (1, 'product', 'PASS', None), (1, 'health', 'PASS', None), (2, 'health', 'PASS', None), (3, 'health', 'PASS', None), (4, 'health', 'PASS', None), (4, 'product', 'PASS', None), (5, 'health', 'PASS', None), (6, 'health', 'PASS', None), (7, 'health', 'PASS', None), (8, 'health', 'PASS', None)].

Monitoring/recognition gaps: [{'reasons': ['UNOBSERVED_CHANGE_OR_CLOCK_NOT_YET_PUBLISHED'], 'tick': 3}].

Interpretation: actual completion establishes this trajectory only. NOT_ESTABLISHED: no counterfactual same-information policy witness.

## B1-mixed-opportunities

observe-02 returned PASS and was adopted; observe-06 returned UNKNOWN because its declared source was unavailable. The controller still executed r00 and r01 on the available branch. Live policy A passed, while the other mandatory role and producers r02/r03 remained unresolved and B was UNKNOWN. Complete required review prevented dispatch. No new report or opportunity arrived to justify retrying the unavailable request on the same basis. Both losses remained 10 throughout; the finite conditional derivation is not a witness that the missing information was obtainable.

One branch can be acquired; another registered source returns UNKNOWN. A good route does not finish complete review.

Final stop: `WAITING_EXTERNAL_OPPORTUNITY`; live A `PASS`, advisory B `UNKNOWN`; required review complete: `False`. Conditions: B-mandatory-obligations-unresolved, recognized-loss-remains, required-review-unresolved, waiting-or-observation-unavailable. Unresolved roles: ['required:r03']; unresolved producers: [['r02', '1'], ['r03', '1']].

Physical / recognized first completion: None / None. Final observed loss: 10; physical deficit: 10. Integrals: world 90, recognized 90. Work/acquisitions/selections: {'acquisitions': 2, 'selections': 5, 'work': 5}.

| Tick:slot | Selected operation | Result | Work / acquisitions | Recognized loss after |
|---|---|---|---|---:|
| 0:0 | request observe-02 | PASS | 1 / 1 | 10 |
| 0:1 | adopt input-02 | PASS | 2 / 1 | 10 |
| 0:2 | request observe-06 | UNKNOWN | 3 / 2 | 10 |
| 0:3 | deduction r00 | PASS | 4 / 2 | 10 |
| 0:4 | deduction r01 | PASS | 5 / 2 | 10 |

Observed trajectory `(tick, physical loss, recognized loss, stage)`: [(0, 10, 10, 'DRAFT'), (1, 10, 10, 'DRAFT'), (2, 10, 10, 'DRAFT'), (3, 10, 10, 'DRAFT'), (4, 10, 10, 'DRAFT'), (5, 10, 10, 'DRAFT'), (6, 10, 10, 'DRAFT'), (7, 10, 10, 'DRAFT'), (8, 10, 10, 'DRAFT')]

Repeated-work accounting: {'repeated_same_basis_selections': 0, 'same_logical_work_new_basis_retries': 0, 'scope': 'Full relevant-basis identity checked independently for every selected operation'}. Authority effects: 0.

Actual observation replies: [(0, 'observe-02', 'PASS', None), (0, 'observe-06', 'UNKNOWN', 'declared source unavailable')].

Monitoring/recognition gaps: [].

Interpretation: UNKNOWN; no same-information counterfactual controller supplied. NOT_ESTABLISHED: no counterfactual same-information policy witness.

## B2-source-role-copies

The controller evaluated r00, both exact r02 applications and r01, so producer review was complete. The copied-lineage r02 result had strength 0.8862380981 and confidence 0.8291325010, but its lineage failed the declared r02 role. It remained a visible unclassified current record; live A passed and B remained UNKNOWN. The controller stopped on that applicability disagreement without dispatch. The eligible alternative did not erase the copied assessment. Root identity here is an explicit role requirement, not proof of statistical independence.

Eligible independent provenance and a copied source coexist as separate current estimates. The copied route cannot acquire the missing declared role.

Final stop: `OBJECTION_OR_UNKNOWN_APPLICABILITY`; live A `PASS`, advisory B `UNKNOWN`; required review complete: `True`. Conditions: objection-or-applicability-unresolved, recognized-loss-remains. Unresolved roles: []; unresolved producers: [].

Physical / recognized first completion: None / None. Final observed loss: 10; physical deficit: 10. Integrals: world 90, recognized 90. Work/acquisitions/selections: {'acquisitions': 0, 'selections': 4, 'work': 4}.

| Tick:slot | Selected operation | Result | Work / acquisitions | Recognized loss after |
|---|---|---|---|---:|
| 0:0 | deduction r00 | PASS | 1 / 0 | 10 |
| 0:1 | deduction r02 | PASS | 2 / 0 | 10 |
| 0:2 | deduction r02 | PASS | 3 / 0 | 10 |
| 0:3 | deduction r01 | PASS | 4 / 0 | 10 |

Observed trajectory `(tick, physical loss, recognized loss, stage)`: [(0, 10, 10, 'DRAFT'), (1, 10, 10, 'DRAFT'), (2, 10, 10, 'DRAFT'), (3, 10, 10, 'DRAFT'), (4, 10, 10, 'DRAFT'), (5, 10, 10, 'DRAFT'), (6, 10, 10, 'DRAFT'), (7, 10, 10, 'DRAFT'), (8, 10, 10, 'DRAFT')]

Repeated-work accounting: {'repeated_same_basis_selections': 0, 'same_logical_work_new_basis_retries': 0, 'scope': 'Full relevant-basis identity checked independently for every selected operation'}. Authority effects: 0.

Monitoring/recognition gaps: [].

Interpretation: UNKNOWN; no same-information counterfactual controller supplied. NOT_ESTABLISHED: no counterfactual same-information policy witness.

Distinct/copy lineage is an explicit applicability requirement; no empirical or statistical independence is inferred from IDs.

## B3-low-confidence-branch

r00 ran before acquisition; the missing report was then requested and adopted with its declared confidence 0.125. r01, r02 and r03 all executed, producing a depth-3 result and completing producer review. Live A and B stayed UNKNOWN because the completed evidence was inadequate. The registry was populated and four formulas ran: the raw no-route label means no further eligible work remained, not that no rules existed. Both losses stayed 10 and there was no dispatch. No reference supplies a justified confidence-improving operation under this contract.

A fully available three-hop path has an inadequately confident primitive input; keep all-current policy A.

Final stop: `NO_KNOWN_SUPPORTED_ROUTE`; live A `UNKNOWN`, advisory B `UNKNOWN`; required review complete: `True`. Conditions: B-mandatory-obligations-unresolved, live-policy-not-passing, no-registered-supported-route, recognized-loss-remains. Unresolved roles: ['required:r03']; unresolved producers: [].

Physical / recognized first completion: None / None. Final observed loss: 10; physical deficit: 10. Integrals: world 90, recognized 90. Work/acquisitions/selections: {'acquisitions': 1, 'selections': 6, 'work': 6}.

| Tick:slot | Selected operation | Result | Work / acquisitions | Recognized loss after |
|---|---|---|---|---:|
| 0:0 | deduction r00 | PASS | 1 / 0 | 10 |
| 0:1 | request observe-04 | PASS | 2 / 1 | 10 |
| 0:2 | adopt input-04 | PASS | 3 / 1 | 10 |
| 0:3 | deduction r01 | PASS | 4 / 1 | 10 |
| 0:4 | deduction r02 | PASS | 5 / 1 | 10 |
| 0:5 | deduction r03 | PASS | 6 / 1 | 10 |

Observed trajectory `(tick, physical loss, recognized loss, stage)`: [(0, 10, 10, 'DRAFT'), (1, 10, 10, 'DRAFT'), (2, 10, 10, 'DRAFT'), (3, 10, 10, 'DRAFT'), (4, 10, 10, 'DRAFT'), (5, 10, 10, 'DRAFT'), (6, 10, 10, 'DRAFT'), (7, 10, 10, 'DRAFT'), (8, 10, 10, 'DRAFT')]

Repeated-work accounting: {'repeated_same_basis_selections': 0, 'same_logical_work_new_basis_retries': 0, 'scope': 'Full relevant-basis identity checked independently for every selected operation'}. Authority effects: 0.

Actual observation replies: [(0, 'observe-04', 'PASS', None)].

Monitoring/recognition gaps: [].

Interpretation: UNKNOWN; no same-information counterfactual controller supplied. NOT_ESTABLISHED: no counterfactual same-information policy witness.

This raw controller stop does not mean the registry was empty: inspect the completed applications and remaining confidence/role requirements. It means the frozen policy found no further eligible work.

## B4-acquisition-headroom

Three cost-4 requests and their adoptions consumed 12 acquisition units and 15 work units; r02 then consumed one more work unit. The fourth necessary cost-4 request could not fit under the unchanged pre-dispatch acquisition allowance of 12 (16 total, with 4 reserved for monitoring/control). Only one formula ran, producer review stayed incomplete, and both judgments remained UNKNOWN. This is a declared capacity limit, not a safety failure or a reason to enlarge the cap after seeing the outcome.

Four required primitive requests each cost four; investigate work/headroom exhaustion without enlarging the original caps.

Final stop: `WORK_OR_ACQUISITION_EXHAUSTED`; live A `UNKNOWN`, advisory B `UNKNOWN`; required review complete: `False`. Conditions: B-mandatory-obligations-unresolved, exhausted-budget, live-policy-not-passing, recognized-loss-remains, required-review-unresolved. Unresolved roles: ['required:r03']; unresolved producers: [['r01', '1'], ['r00', '1'], ['r03', '1']].

Physical / recognized first completion: None / None. Final observed loss: 10; physical deficit: 10. Integrals: world 90, recognized 90. Work/acquisitions/selections: {'acquisitions': 12, 'selections': 7, 'work': 16}.

| Tick:slot | Selected operation | Result | Work / acquisitions | Recognized loss after |
|---|---|---|---|---:|
| 0:0 | request observe-00 | PASS | 4 / 4 | 10 |
| 0:1 | adopt input-00 | PASS | 5 / 4 | 10 |
| 0:2 | request observe-02 | PASS | 9 / 8 | 10 |
| 0:3 | adopt input-02 | PASS | 10 / 8 | 10 |
| 0:4 | request observe-06 | PASS | 14 / 12 | 10 |
| 0:5 | adopt input-06 | PASS | 15 / 12 | 10 |
| 0:6 | deduction r02 | PASS | 16 / 12 | 10 |

Observed trajectory `(tick, physical loss, recognized loss, stage)`: [(0, 10, 10, 'DRAFT'), (1, 10, 10, 'DRAFT'), (2, 10, 10, 'DRAFT'), (3, 10, 10, 'DRAFT'), (4, 10, 10, 'DRAFT'), (5, 10, 10, 'DRAFT'), (6, 10, 10, 'DRAFT'), (7, 10, 10, 'DRAFT'), (8, 10, 10, 'DRAFT')]

Repeated-work accounting: {'repeated_same_basis_selections': 0, 'same_logical_work_new_basis_retries': 0, 'scope': 'Full relevant-basis identity checked independently for every selected operation'}. Authority effects: 0.

Actual observation replies: [(0, 'observe-00', 'PASS', None), (0, 'observe-02', 'PASS', None), (0, 'observe-06', 'PASS', None)].

Monitoring/recognition gaps: [].

Interpretation: UNKNOWN; no same-information counterfactual controller supplied. NOT_ESTABLISHED: no counterfactual same-information policy witness.

All four missing conditionals are necessary, with total acquisition cost 16; the frozen pre-dispatch acquisition headroom leaves 12. This is a policy-budget limitation, not proof no other same-information policy exists.

## C1-shared-replacement

The scheduled replacement arrived after tick 0 slot 2, following r00, r01 and r02. It retired input-02 and two dependent derived beliefs while retaining the unrelated route. The controller adopted the same-valued replacement with its new root and reviewed all newly available exact alternatives. Ten formula calls in total included valid recomputation and alternative applications. Reserve and dispatch occurred at tick 1 slots 3 and 4. The immediate product reply was UNKNOWN; the next product opportunity at tick 4 began health sampling through tick 6. Physical completion was tick 4, recognized completion tick 6. Neither the replacement alone nor the first changed application is asserted to cause the entire delay.

Replace an exact source on one of two shared suffix producers at a fixed public boundary; retain unrelated ancestry.

Final stop: `OBSERVED_COMPLETION`; live A `PASS`, advisory B `PASS`; required review complete: `True`. Conditions: completed-historically, waiting-or-observation-unavailable. Unresolved roles: []; unresolved producers: [].

Physical / recognized first completion: 4 / 6. Final observed loss: 0; physical deficit: 0. Integrals: world 40, recognized 60. Work/acquisitions/selections: {'acquisitions': 7, 'selections': 21, 'work': 21}.

| Tick:slot | Selected operation | Result | Work / acquisitions | Recognized loss after |
|---|---|---|---|---:|
| 0:0 | deduction r00 | PASS | 1 / 0 | 10 |
| 0:1 | deduction r01 | PASS | 2 / 0 | 10 |
| 0:2 | deduction r02 | PASS | 3 / 0 | 10 |
| 0:3 | adopt replacement:input-02 | PASS | 4 / 0 | 10 |
| 0:4 | deduction r02 | PASS | 5 / 0 | 10 |
| 0:5 | deduction r04 | PASS | 6 / 0 | 10 |
| 0:6 | deduction r00 | PASS | 7 / 0 | 10 |
| 0:7 | deduction r03 | PASS | 8 / 0 | 10 |
| 1:0 | deduction r02 | PASS | 9 / 0 | 10 |
| 1:1 | deduction r04 | PASS | 10 / 0 | 10 |
| 1:2 | deduction r03 | PASS | 11 / 0 | 10 |
| 1:3 | reserve attempt | PASS | 12 / 0 | 10 |
| 1:4 | dispatch attempt | PASS | 13 / 0 | 10 |
| 1:5 | request product | UNKNOWN | 14 / 1 | 10 |
| 4:0 | request product | PASS | 15 / 2 | 10 |
| 4:1 | request health | PASS | 16 / 3 | 10 |
| 5:0 | request health | PASS | 17 / 4 | 10 |
| 6:0 | request health | PASS | 18 / 5 | 0 |
| 6:1 | complete attempt | PASS | 19 / 5 | 0 |
| 7:0 | request health | PASS | 20 / 6 | 0 |
| 8:0 | request health | PASS | 21 / 7 | 0 |

Observed trajectory `(tick, physical loss, recognized loss, stage)`: [(0, 10, 10, 'DRAFT'), (1, 10, 10, 'DRAFT'), (2, 10, 10, 'DRAFT'), (3, 10, 10, 'DRAFT'), (4, 0, 10, 'DRAFT'), (5, 0, 10, 'DRAFT'), (6, 0, 0, 'BUILT'), (7, 0, 0, 'BUILT'), (8, 0, 0, 'BUILT')]

Repeated-work accounting: {'repeated_same_basis_selections': 0, 'same_logical_work_new_basis_retries': 0, 'scope': 'Full relevant-basis identity checked independently for every selected operation'}. Authority effects: 1.

Public changes (fixed before execution):

```json
[
  {
    "after_slot": 2,
    "kind": "replace",
    "report": {
      "availability": "unknown",
      "confidence": 0.96875,
      "cost": 1,
      "delivery": "event",
      "id": "replacement:input-02",
      "joint_scope": true,
      "literal": {
        "positive": true,
        "statement": {
          "arguments": [
            "b",
            "c"
          ],
          "predicate": "pln:implication"
        }
      },
      "probe_id": "observe-02",
      "response": "PASS",
      "root": "root:replacement:input-02",
      "source": "forecast-model",
      "strength": 0.96875
    },
    "target": "input-02",
    "tick": 0
  }
]
```
Exact retirement evidence: [{'retired': ['probability-belief/v1:faf54320ad349b571240672eb654701ed61e18f99c17f4997581aeb2af7e3dc8', 'probability-belief/v1:e76e320d54375810d634c10e19414102c26cc1dd9dc13ca5481bb1b0536c6dda', 'probability-belief/v1:a759ef03918489d71809b2591bba352119bf21535580b6be730effff241e9cb5'], 'target': 'input-02'}]

Actual observation replies: [(1, 'product', 'UNKNOWN', 'no installed artifact observed'), (4, 'product', 'PASS', None), (4, 'health', 'PASS', None), (5, 'health', 'PASS', None), (6, 'health', 'PASS', None), (7, 'health', 'PASS', None), (8, 'health', 'PASS', None)].

Monitoring/recognition gaps: [{'reasons': ['MISSING_OR_STALE_OBSERVATION_UNDER_DECLARED_MODEL', 'DIFFERENT_PHYSICAL_AND_OBSERVATION_PREDICATES', 'UNOBSERVED_CHANGE_OR_CLOCK_NOT_YET_PUBLISHED'], 'tick': 4}, {'reasons': ['MISSING_OR_STALE_OBSERVATION_UNDER_DECLARED_MODEL', 'DIFFERENT_PHYSICAL_AND_OBSERVATION_PREDICATES', 'UNOBSERVED_CHANGE_OR_CLOCK_NOT_YET_PUBLISHED'], 'tick': 5}, {'reasons': ['UNOBSERVED_CHANGE_OR_CLOCK_NOT_YET_PUBLISHED'], 'tick': 6}].

Interpretation: actual completion establishes this trajectory only. NOT_ESTABLISHED: no counterfactual same-information policy witness.

## C2-late-adverse-route

The available chain r00/r01/r02 completed at tick 0, while required review still awaited the other route. The fixed adverse primitive report arrived after the tick-2 quiescent row and was adopted at tick 3; r03 then executed through native PLN. Its strength was 0.1620416641, creating a current strength objection. Both A and B failed, producer review was now complete, and no deployment occurred. The controller had not been authorized by partial review before that report arrived. No future adverse value was exposed in its earlier public state.

Deliver an adverse primitive conditional through the public report path; require real inference and complete contrary assessment.

Final stop: `OBJECTION_OR_UNKNOWN_APPLICABILITY`; live A `FAIL`, advisory B `FAIL`; required review complete: `True`. Conditions: B-mandatory-obligations-unresolved, live-policy-not-passing, no-registered-supported-route, objection-or-applicability-unresolved, recognized-loss-remains. Unresolved roles: ['required:r03']; unresolved producers: [].

Physical / recognized first completion: None / None. Final observed loss: 10; physical deficit: 10. Integrals: world 90, recognized 90. Work/acquisitions/selections: {'acquisitions': 0, 'selections': 5, 'work': 5}.

| Tick:slot | Selected operation | Result | Work / acquisitions | Recognized loss after |
|---|---|---|---|---:|
| 0:0 | deduction r00 | PASS | 1 / 0 | 10 |
| 0:1 | deduction r01 | PASS | 2 / 0 | 10 |
| 0:2 | deduction r02 | PASS | 3 / 0 | 10 |
| 3:0 | adopt input-06 | PASS | 4 / 0 | 10 |
| 3:1 | deduction r03 | PASS | 5 / 0 | 10 |

Observed trajectory `(tick, physical loss, recognized loss, stage)`: [(0, 10, 10, 'DRAFT'), (1, 10, 10, 'DRAFT'), (2, 10, 10, 'DRAFT'), (3, 10, 10, 'DRAFT'), (4, 10, 10, 'DRAFT'), (5, 10, 10, 'DRAFT'), (6, 10, 10, 'DRAFT'), (7, 10, 10, 'DRAFT'), (8, 10, 10, 'DRAFT')]

Repeated-work accounting: {'repeated_same_basis_selections': 0, 'same_logical_work_new_basis_retries': 0, 'scope': 'Full relevant-basis identity checked independently for every selected operation'}. Authority effects: 0.

Public changes (fixed before execution):

```json
[
  {
    "after_slot": 0,
    "kind": "report",
    "report": {
      "availability": "unknown",
      "confidence": 0.96875,
      "cost": 1,
      "delivery": "event",
      "id": "input-06",
      "joint_scope": false,
      "literal": {
        "positive": true,
        "statement": {
          "arguments": [
            "d",
            "healthy"
          ],
          "predicate": "pln:implication"
        }
      },
      "probe_id": "observe-06",
      "response": "PASS",
      "root": "root:input-06",
      "source": "forecast-model",
      "strength": 0.0625
    },
    "tick": 2
  }
]
```
Exact retirement evidence: []

Monitoring/recognition gaps: [].

Interpretation: UNKNOWN; no same-information counterfactual controller supplied. NOT_ESTABLISHED: no counterfactual same-information policy witness.

## C3-replacement-unobservable

Three deductions, reserve and dispatch completed at tick 0. Product requests at ticks 0, 1 and 4 all returned UNKNOWN because the channel was unavailable. The fixed replacement after tick 1 slot 0 retired the primitive and three derived beliefs; adoption and three fresh deductions restored current numerical support, for six formula calls total. A and B passed and review completed, but health sampling required an observed product. Physical completion at tick 3 therefore never became recognized completion: the final losses were 0 physical and 10 recognized, and the integral gap was 60. The old execution-support binding was explicitly STALE; no stale operation was selected and no new deployment was invented.

Change a relevant exact premise while product sensing is unavailable; distinguish physical completion from recognition.

Final stop: `WAITING_EXTERNAL_OUTCOME`; live A `PASS`, advisory B `PASS`; required review complete: `True`. Conditions: recognized-loss-remains, waiting-or-observation-unavailable. Unresolved roles: []; unresolved producers: [].

Physical / recognized first completion: 3 / None. Final observed loss: 10; physical deficit: 0. Integrals: world 30, recognized 90. Work/acquisitions/selections: {'acquisitions': 3, 'selections': 12, 'work': 12}.

| Tick:slot | Selected operation | Result | Work / acquisitions | Recognized loss after |
|---|---|---|---|---:|
| 0:0 | deduction r00 | PASS | 1 / 0 | 10 |
| 0:1 | deduction r01 | PASS | 2 / 0 | 10 |
| 0:2 | deduction r02 | PASS | 3 / 0 | 10 |
| 0:3 | reserve attempt | PASS | 4 / 0 | 10 |
| 0:4 | dispatch attempt | PASS | 5 / 0 | 10 |
| 0:5 | request product | UNKNOWN | 6 / 1 | 10 |
| 1:0 | request product | UNKNOWN | 7 / 2 | 10 |
| 1:1 | adopt replacement:input-02 | PASS | 8 / 2 | 10 |
| 1:2 | deduction r00 | PASS | 9 / 2 | 10 |
| 1:3 | deduction r01 | PASS | 10 / 2 | 10 |
| 1:4 | deduction r02 | PASS | 11 / 2 | 10 |
| 4:0 | request product | UNKNOWN | 12 / 3 | 10 |

Observed trajectory `(tick, physical loss, recognized loss, stage)`: [(0, 10, 10, 'DRAFT'), (1, 10, 10, 'DRAFT'), (2, 10, 10, 'DRAFT'), (3, 0, 10, 'DRAFT'), (4, 0, 10, 'DRAFT'), (5, 0, 10, 'DRAFT'), (6, 0, 10, 'DRAFT'), (7, 0, 10, 'DRAFT'), (8, 0, 10, 'DRAFT')]

Repeated-work accounting: {'repeated_same_basis_selections': 0, 'same_logical_work_new_basis_retries': 0, 'scope': 'Full relevant-basis identity checked independently for every selected operation'}. Authority effects: 1.

Public changes (fixed before execution):

```json
[
  {
    "after_slot": 0,
    "kind": "replace",
    "report": {
      "availability": "unknown",
      "confidence": 0.96875,
      "cost": 1,
      "delivery": "event",
      "id": "replacement:input-02",
      "joint_scope": true,
      "literal": {
        "positive": true,
        "statement": {
          "arguments": [
            "c",
            "d"
          ],
          "predicate": "pln:implication"
        }
      },
      "probe_id": "observe-02",
      "response": "PASS",
      "root": "root:replacement:input-02",
      "source": "forecast-model",
      "strength": 0.96875
    },
    "target": "input-02",
    "tick": 1
  }
]
```
Exact retirement evidence: [{'retired': ['probability-belief/v1:d98f2f9881b3eb1635c82eee0736bb24944cacf4cc6e129d24112916dcfec102', 'probability-belief/v1:65e2c247268ca0e2591a6c408a15b066cd7c1fb0597be5d982756e098a1f78f0', 'probability-belief/v1:4ca8dd3e44403ecdeeecb6d8f1595219d2232a716366d58dd8028d430cd1472d', 'probability-belief/v1:4f5411dfbfbbf4bdb690eafcb3fe5c0bcc91a0fba337f7068d9b328f8e91cc98'], 'target': 'input-02'}]

Actual observation replies: [(0, 'product', 'UNKNOWN', 'observation channel unavailable'), (1, 'product', 'UNKNOWN', 'observation channel unavailable'), (4, 'product', 'UNKNOWN', 'observation channel unavailable')].

Monitoring/recognition gaps: [{'reasons': ['MISSING_OR_STALE_OBSERVATION_UNDER_DECLARED_MODEL', 'DIFFERENT_PHYSICAL_AND_OBSERVATION_PREDICATES', 'UNOBSERVED_CHANGE_OR_CLOCK_NOT_YET_PUBLISHED'], 'tick': 3}, {'reasons': ['OBSERVATION_UNAVAILABLE', 'MISSING_OR_STALE_OBSERVATION_UNDER_DECLARED_MODEL', 'DIFFERENT_PHYSICAL_AND_OBSERVATION_PREDICATES', 'UNOBSERVED_CHANGE_OR_CLOCK_NOT_YET_PUBLISHED'], 'tick': 4}, {'reasons': ['MISSING_OR_STALE_OBSERVATION_UNDER_DECLARED_MODEL', 'DIFFERENT_PHYSICAL_AND_OBSERVATION_PREDICATES', 'UNOBSERVED_CHANGE_OR_CLOCK_NOT_YET_PUBLISHED'], 'tick': 5}, {'reasons': ['MISSING_OR_STALE_OBSERVATION_UNDER_DECLARED_MODEL', 'DIFFERENT_PHYSICAL_AND_OBSERVATION_PREDICATES', 'UNOBSERVED_CHANGE_OR_CLOCK_NOT_YET_PUBLISHED'], 'tick': 6}, {'reasons': ['MISSING_OR_STALE_OBSERVATION_UNDER_DECLARED_MODEL', 'DIFFERENT_PHYSICAL_AND_OBSERVATION_PREDICATES', 'UNOBSERVED_CHANGE_OR_CLOCK_NOT_YET_PUBLISHED'], 'tick': 7}, {'reasons': ['MISSING_OR_STALE_OBSERVATION_UNDER_DECLARED_MODEL', 'DIFFERENT_PHYSICAL_AND_OBSERVATION_PREDICATES', 'UNOBSERVED_CHANGE_OR_CLOCK_NOT_YET_PUBLISHED'], 'tick': 8}].

Interpretation: UNKNOWN; no same-information counterfactual controller supplied. NOT_ESTABLISHED: no counterfactual same-information policy witness.

## C4-regression-reassessment

Five deductions preceded reserve and dispatch at tick 0; admitted product/health observations produced recognized completion at tick 3. Physical health regressed at tick 6, when the health channel returned UNKNOWN. Recognized loss had already reopened to 10 in that row before adoption of the scheduled changed estimate. The replacement retired one primitive and three derived beliefs; three fresh calls produced a current adverse final estimate (strength 0.2284263372), making both A and B fail. Health replies at ticks 7 and 8 successfully reported false health; PASS here describes obtaining a report, not a healthy product. Historical BUILT remained, while current loss stayed 10. The first confirming adverse sample lagged physical regression by one tick. The numeric change cannot be credited with causing the earlier observed-loss change; old execution support remained STALE and was not reused.

Combine supported three-hop work with the existing physical regression/outage and a public changed estimate; preserve historical completion.

Final stop: `WAITING_EXTERNAL_OUTCOME`; live A `FAIL`, advisory B `FAIL`; required review complete: `True`. Conditions: B-mandatory-obligations-unresolved, completed-historically, live-policy-not-passing, objection-or-applicability-unresolved, recognized-loss-remains, waiting-or-observation-unavailable. Unresolved roles: ['required:r04']; unresolved producers: [].

Physical / recognized first completion: 3 / 3. Final observed loss: 10; physical deficit: 10. Integrals: world 60, recognized 60. Work/acquisitions/selections: {'acquisitions': 11, 'selections': 23, 'work': 23}.

| Tick:slot | Selected operation | Result | Work / acquisitions | Recognized loss after |
|---|---|---|---|---:|
| 0:0 | deduction r00 | PASS | 1 / 0 | 10 |
| 0:1 | deduction r01 | PASS | 2 / 0 | 10 |
| 0:2 | deduction r02 | PASS | 3 / 0 | 10 |
| 0:3 | deduction r03 | PASS | 4 / 0 | 10 |
| 0:4 | deduction r04 | PASS | 5 / 0 | 10 |
| 0:5 | reserve attempt | PASS | 6 / 0 | 10 |
| 0:6 | dispatch attempt | PASS | 7 / 0 | 10 |
| 0:7 | request product | UNKNOWN | 8 / 1 | 10 |
| 1:0 | request product | PASS | 9 / 2 | 10 |
| 1:1 | request health | PASS | 10 / 3 | 10 |
| 2:0 | request health | PASS | 11 / 4 | 10 |
| 3:0 | request health | PASS | 12 / 5 | 0 |
| 3:1 | complete attempt | PASS | 13 / 5 | 0 |
| 4:0 | request health | PASS | 14 / 6 | 0 |
| 4:1 | request product | PASS | 15 / 7 | 0 |
| 5:0 | request health | PASS | 16 / 8 | 0 |
| 6:0 | request health | UNKNOWN | 17 / 9 | 10 |
| 6:1 | adopt replacement:input-06 | PASS | 18 / 9 | 10 |
| 6:2 | deduction r02 | PASS | 19 / 9 | 10 |
| 6:3 | deduction r03 | PASS | 20 / 9 | 10 |
| 6:4 | deduction r04 | PASS | 21 / 9 | 10 |
| 7:0 | request health | PASS | 22 / 10 | 10 |
| 8:0 | request health | PASS | 23 / 11 | 10 |

Observed trajectory `(tick, physical loss, recognized loss, stage)`: [(0, 10, 10, 'DRAFT'), (1, 10, 10, 'DRAFT'), (2, 10, 10, 'DRAFT'), (3, 0, 0, 'BUILT'), (4, 0, 0, 'BUILT'), (5, 0, 0, 'BUILT'), (6, 10, 10, 'BUILT'), (7, 10, 10, 'BUILT'), (8, 10, 10, 'BUILT')]

Repeated-work accounting: {'repeated_same_basis_selections': 0, 'same_logical_work_new_basis_retries': 0, 'scope': 'Full relevant-basis identity checked independently for every selected operation'}. Authority effects: 1.

Public changes (fixed before execution):

```json
[
  {
    "after_slot": 0,
    "kind": "replace",
    "report": {
      "availability": "unknown",
      "confidence": 0.96875,
      "cost": 1,
      "delivery": "event",
      "id": "replacement:input-06",
      "joint_scope": false,
      "literal": {
        "positive": true,
        "statement": {
          "arguments": [
            "d",
            "e"
          ],
          "predicate": "pln:implication"
        }
      },
      "probe_id": "observe-06",
      "response": "PASS",
      "root": "root:replacement:input-06",
      "source": "forecast-model",
      "strength": 0.125
    },
    "target": "input-06",
    "tick": 6
  }
]
```
Exact retirement evidence: [{'retired': ['probability-belief/v1:7147cd2640c5e90674c7d8cb9b94e9ced84c8f25a79f48584cb949cd4f226264', 'probability-belief/v1:17a808dbe31c3847ac53f7208ecd1d48769c3a5f534b8b4643267dc77a365bd4', 'probability-belief/v1:21388ef1946d0cdc56300652233d444cab77d087dacebafaa77d6107d14bc38a', 'probability-belief/v1:053a60978f46c9f9d0140c7d10e3c8dbbbede74abe485bc75062c013727d6b14'], 'target': 'input-06'}]

Actual observation replies: [(0, 'product', 'UNKNOWN', 'no installed artifact observed'), (1, 'product', 'PASS', None), (1, 'health', 'PASS', None), (2, 'health', 'PASS', None), (3, 'health', 'PASS', None), (4, 'health', 'PASS', None), (4, 'product', 'PASS', None), (5, 'health', 'PASS', None), (6, 'health', 'UNKNOWN', 'observation channel unavailable'), (7, 'health', 'PASS', None), (8, 'health', 'PASS', None)].

Monitoring/recognition gaps: [{'reasons': ['UNOBSERVED_CHANGE_OR_CLOCK_NOT_YET_PUBLISHED'], 'tick': 3}, {'reasons': ['UNOBSERVED_CHANGE_OR_CLOCK_NOT_YET_PUBLISHED'], 'tick': 6}].

Interpretation: actual completion establishes this trajectory only. NOT_ESTABLISHED: no counterfactual same-information policy witness.

