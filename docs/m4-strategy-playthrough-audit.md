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

The next M4 calibration task is to author a small set of strategy-distinguishing
plans that deliberately exercise signal response, policy discipline, and portfolio
mix while preserving the negative controls. The matrix harness and the missing
decision producer are now ready for that calibration; no scoring constants were
changed to force a spread.
