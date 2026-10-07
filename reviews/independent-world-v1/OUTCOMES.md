# Physical and observed outcomes

Measured source `b12127556d6d1fe4a7c152dba85f5d71df266194`. Finite and native outcomes and operation counts agree for each parent; only measured costs differ. Six parents are not twelve independent samples.

| Environment | Accepted / physical effect tick | First physical / completion tick | J_world / J_certified | Final physical / observed loss | Selections / work / queries |
|---|---|---|---|---|---|
| observable | 0 / 1 | 3 / 3 | 30 / 30 | 0 / 0 | 18 / 18 / 12 |
| unobservable | 0 / 1 | 3 / None | 30 / 90 | 0 / 10 | 9 / 9 / 4 |
| delayed | 0 / 4 | 6 / 6 | 60 / 60 | 0 / 0 | 15 / 15 / 9 |
| wrong-artifact | 0 / 1 | None / None | 90 / 90 | 10 / 10 | 9 / 9 / 4 |
| early-failure | 0 / 1 | None / None | 90 / 90 | 10 / 10 | 17 / 17 / 12 |
| regression | 0 / 1 | 3 / 3 | 60 / 60 | 10 / 10 | 18 / 18 / 12 |

Each execution uses two selected certified deductions, one actual accepted executor effect and the same public opportunity schedule. There are 172 selected operations, 106 acquisitions, 24 formula calls (12 fresh native), 280 public decision/status rows and 108 physical ticks. Every run reaches the fixed horizon. `None` means not achieved during that horizon; lag is censored when completion is absent.

At tick 0 the unchanged consumer computes the competing route, requests and adopts the missing numerical premise, computes the declared required route, reserves, dispatches and requests product status. The product does not yet exist. An acknowledgment and a favorable forecast therefore leave physical and observed loss at ten. Later actions arise from the fixed public clock and opportunities, with the same consumer history and budgets.

The observable control installs artifact-v2 and becomes healthy at tick 1. Actual product and health reports enter through the original APIs. Three physical ticks and three admitted health samples mature at tick 3; existing completion is selected and recorded. Monitoring continues through tick 8.

The unobservable case has exactly the same physical evolution, achieving its physical goal at tick 3, but all three product opportunities return UNKNOWN. The exact-product prerequisite prevents health requests, the lifecycle remains DRAFT and observed loss remains ten. J_world is 30 while J_certified is 90. This is unavailable observation, not a physical failure or permission to fabricate evidence.

The delayed case accepts the command at tick 0 but schedules its effect for tick 4. The product requests before then report absence; ticks 2 and 3 have no selected work, while physical time still advances. The tick-4 product opportunity permits actual product and health observations. Both goals mature at tick 6. No query causes deployment.

The wrong-artifact case installs artifact-v1 at tick 1. Product reports retain that actual identity and the original exact-product interface rejects them. No exact-product milestone, health request or completion follows. The numerical assessment and accepted command do not repair the physical defect. The early-failure case installs artifact-v2, then the declared tick-1 failure runs before the first health query; that query truthfully reports unhealthy. All later health samples remain adverse. Both cases retain physical and observed loss ten.

The regression case completes historically at tick 3 and is healthy through tick 5. At tick 6 an exogenous event makes the service unhealthy while its health channel is unavailable. Before the public clock is published, authoritative loss is still zero and world loss has become ten; the physical transition itself does not write authority. Publishing the clock makes the old observation window stale: recognized loss reopens to ten as UNKNOWN. The first actual adverse health sample arrives at tick 7 and establishes OBSERVED_FAILURE. Thus adverse-sample recognition lag is one tick, whereas loss reopening occurs at tick 6. Historical BUILT remains recorded through tick 8. Equal loss integrals here do not imply continuous observation or identical predicates.

| Regression tick | Physical loss | Observed loss before clock | Observed loss after operations | Current label |
|---|---:|---:|---:|---|
| 0 | 10 | 10 | 10 | PENDING |
| 1 | 10 | 10 | 10 | PENDING |
| 2 | 10 | 10 | 10 | UNKNOWN |
| 3 | 0 | 10 | 0 | OBSERVED_SUCCESS |
| 4 | 0 | 0 | 0 | OBSERVED_SUCCESS |
| 5 | 0 | 0 | 0 | OBSERVED_SUCCESS |
| 6 | 10 | 0 | 10 | UNKNOWN |
| 7 | 10 | 10 | 10 | OBSERVED_FAILURE |
| 8 | 10 | 10 | 10 | OBSERVED_FAILURE |

Selected-operation results across the cohort: `{'PASS': 148, 'UNKNOWN': 20, 'FAIL': 4}`. UNKNOWN responses and wrong-product rejections are retained unresolved outcomes; they are not suite or conformance failures. There are no selected STALE requests in this cohort. Existing stale-permit and uncertain-action boundaries are covered by the applicable regression suites and targeted lost-reply test.

All final unresolved runs stop with WAITING_EXTERNAL_OUTCOME. No controller repair, extra opportunity, larger budget or favorable replacement observation was introduced. Six historical completions include two that later reopen; four executions finish with current observed loss zero. Six finish physically satisfied, including two without certified completion. These are descriptive synthetic outcomes, not safety rates.

Raw evidence is in each comparison subdirectory: `trace.jsonl` retains exact public inputs/frontiers/choices and received responses; `ticks.json` separates phases and cumulative budgets; `private.json` records accepted identities, due effects, physical history and passive samples; `authority-certificates.json` records persistent permits; `admission.db` and `executor.db` support reconstruction. The evaluator archive is not a controller input.
