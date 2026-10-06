# Measured work and descriptive costs

One serial pass at `2322512`, seed 0; no ranking, tuning sweep or speed claim.
All costs are inclusive where stated. Acquisition is charged once per authoritative
prefix; role variants share that captured input. Five diagnostics transform existing
inputs and do not claim fresh acquisition.

| Measured phase | Total (ms) |
|---|---:|
| Full acquisition, including diagnostics/serialization overhead | 304.709 |
| Frozen complete numerical capture, inside acquisition | 129.544 |
| Public inventory/state read, inside acquisition | 74.995 |
| Initial frozen A evaluation, 42 views | 48.682 |
| Initial frozen B evaluation, 42 views | 47.178 |
| Total work projection, 42 views | 301.274 |
| Frozen A/B revalidation, inside projection | 101.257 |
| Producer discovery and route graph, inside projection | 7.553 |
| Work-view serialization, inside projection | 43.037 |

Initial frozen evaluation retains its scan, applicability classification, policy
evaluation and witness serialization counters separately in each row. Remaining
projection time includes input validation/binding, initial obligation/global node
construction and other common work. The route-graph timer is not an isolated
whole-graph or whole-projector cost; all graph work is charged within total
projection. Early closed diagnostics can omit counters for stages not completed;
this does not mean they required no work. Nested values must not be added together.

Cohort elapsed is **6.263 s**, including **5.265 s** constructing fixtures, admitting
reports, certifying/persisting selected computations, and doing native projection /
reopen. Acquisition is nested in session construction. The cohort timer starts
after source-copy and native-build preflight, so those are not measured in that
total. All sessions preserve existing setup, certification, inference, commit,
native runtime and reconstruction timing fields with their original meanings.

Across repeated views: 50 inventory-item occurrences, 172 current-premise records,
50 tuple visits, 254 history-scan visits, 254 role comparisons, 50 operation nodes,
374 total nodes and 389 edges. Serialized work-view payloads total 1,681,661 bytes.
These are descriptive work counts over reused states/roles, not independent
population sizes, unique demand, pressure budgets or predicted goal relief.
Raw acquisition counts and per-view limits remain available in the bundle.

The initial graph rebuilds from bounded complete inputs. Isolated native arithmetic,
fsync, RSS, physical observation latency and hypothetical autonomous repair costs
are unmeasured. No scalable incremental index, efficiency gain or superior
reasoning is claimed. Prior controller and shadow-comparison timings remain frozen.
