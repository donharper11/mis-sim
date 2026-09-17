# M4 strategy playthrough audit

Date: 2026-09-17

The production decision harness now supports a strategy matrix with one detached
runtime-pack snapshot per batch. That preserves the pack isolation contract while
making the audit practical. The audit command exercises the real `SimulationService`
and persists six immutable rounds per playthrough.

The first bounded review covered the four declared strategies against the coherent
`balanced` and negligent `do_nothing` decision plans:

| Strategy | Playthroughs | Rounds | Firm-score range |
|---|---:|---:|---:|
| cost_leadership | 2 | 12 | 0.000000–0.000000 |
| differentiation | 2 | 12 | 0.000000–0.000000 |
| customer_supplier_intimacy | 2 | 12 | 0.000000–0.000000 |
| focus_strategy | 2 | 12 | 0.000000–0.000000 |

This is a **failed balance review**, not evidence that the strategies are balanced.
All eight playthroughs (48 persisted rounds) completed and remained finite, but the Management term was
zero for the exercised runtime states, so the multiplicative realised-value model
correctly produced zero firm score for every strategy. The result is useful: the next
M4 calibration task is to identify why the decision-driven fixture leaves Management
at zero and then rerun this matrix. No strategy winner or pedagogical balance claim is
made until that throttle is resolved.

The full four-archetype matrix remains available through
`app.simulation.games.run_strategy_matrix`; it should be run after the Management
throttle is understood, because a larger matrix cannot turn a zero-score fixture into
balance evidence.
