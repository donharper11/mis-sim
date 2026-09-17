# M4 strategy playthrough audit

Date: 2026-09-17

The production decision harness exercises the real `SimulationService` and persists
six immutable rounds per playthrough. `run_strategy_matrix` uses one detached runtime
pack snapshot per batch, preserving pack isolation while keeping the audit practical.

The first bounded run exposed a producer defect: modern projection left
`TeamState.decisions` empty, so strategic alignment and portfolio discipline were
zero even when the decision sheet contained spend. The projection now derives the
scorer's decision records from current-round action and cost entries, resolves R/G/T
from authored catalog items, and includes recurring maintenance spend in the floor.
The existing pure-engine and legacy snapshot paths are unchanged.

The corrected full matrix covered all four strategies, all four decision archetypes,
and 16 six-round playthroughs (96 persisted rounds):

| Strategy | Playthroughs | Firm-score range | Non-zero rounds |
|---|---:|---:|---:|
| cost_leadership | 4 | 0.000000–0.134310 | 1 |
| differentiation | 4 | 0.000000–0.000000 | 0 |
| customer_supplier_intimacy | 4 | 0.000000–0.000000 | 0 |
| focus_strategy | 4 | 0.000000–0.046672 | 1 |

Across archetypes, only the coherent `balanced` plan produced non-zero rounds
(2 of 24); `all_tech_no_org`, `do_nothing`, and `overspender` remained at zero. This
is a valid calibration finding, not a strategy-balance pass: the fixture's later
rounds leave actionable signals unanswered and several strategy/archetype pairs hit
zero Management sub-factors. No strategy winner or pedagogical balance claim should
be made from this matrix yet.

That first matrix identified the need for a small set of strategy-distinguishing
plans that deliberately exercise signal response, policy discipline, and portfolio
mix while preserving the negative controls. The calibrated pass below addresses
that need through authored plan choices; no scoring constants were changed to
force a spread.

## Calibrated coherent-plan pass

The plan calibration profile was then run once for each declared strategy while retaining the
three negative controls in their original fixture form. It adds explicit policy decisions every
round, supports all five initially live catalog assets that can serve the order/store paths, and
uses strategy-specific customer-system placement.

| Declared strategy | Calibrated balanced firm-score curve (R1–R6) |
|---|---|
| cost leadership | 0.134310, 0.090002, 0.000000, 0.061365, 0.065001, 0.052429 |
| differentiation | 0.000000, 0.031028, 0.000000, 0.000000, 0.076481, 0.066443 |
| customer/supplier intimacy | 0.000000, 0.054818, 0.000000, 0.000000, 0.046517, 0.035878 |
| focus strategy | 0.046672, 0.031388, 0.000000, 0.056006, 0.070744, 0.058472 |

This is a better calibration instrument: later-round Management values are no longer universally
zero, and the strategy curves separate. Round 3 remains zero while the on-order customer system
is in lead time; that is an authored transition consequence, not a scoring override. The pass is
still a human review input, not an automatic balance claim.
