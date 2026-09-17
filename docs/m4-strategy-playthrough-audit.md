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
be made from this matrix at that stage.

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

This was a better calibration instrument than the original fixture: later-round Management values
were no longer universally zero, and the strategy curves separated. In that pre-revision model,
round 3 remained zero while the on-order customer system was in lead time. The pass was a human
review input, not an automatic balance claim.

## Weighted-term scoring pass

The scoring model was then revised so Technology, Organisation, and Management use authored
weighted averages for partial evidence. Structural blockers remain hard gates: no serving path,
no primary rollout, or no governance assignment still produces a zero term. The top-level
realised-value product remains `Technology × Organisation × Management`.

Replaying the same four calibrated balanced firms produced:

| Declared strategy | Weighted calibrated firm-score curve (R1–R6) | Six-round average |
|---|---|---:|
| cost leadership | 0.175300, 0.144619, 0.079602, 0.104325, 0.117863, 0.119957 | 0.123611 |
| differentiation | 0.055909, 0.048585, 0.031841, 0.093595, 0.120945, 0.115819 | 0.077782 |
| customer/supplier intimacy | 0.104699, 0.088109, 0.054584, 0.098335, 0.123624, 0.123190 | 0.098757 |
| focus strategy | 0.060861, 0.049578, 0.031841, 0.098383, 0.112438, 0.101584 | 0.075781 |

The revised model removes the artificial all-zero transition rounds: every balanced firm now
retains partial value in every round. Later-round scores remain relatively close because the four
plans still share most of the same authored estate and rollout path; this is still not a
competitive-market simulation. All three negative-control archetypes remained at zero.

## M4 balance gate — accepted

On 2026-09-18 the user accepted the weighted-term curves for pedagogical review and closed the
M4 balance gate. The accepted criteria are met: no balanced strategy has an artificial all-zero
round; all three negative controls remain at zero; strategy-specific differences remain visible;
and later-round convergence is explained by shared authored plans rather than competitor
interaction. This ruling closes the M4 balance review; it does not claim that the harness is a
competitive-market simulation. M5 course operations and teaching support is now the active
product phase.
