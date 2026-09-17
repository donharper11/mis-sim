# M4 student coverage slice

Date: 2026-09-16

M4 is now underway. This bounded slice closes two previously homeless student inputs from the
field-coverage register without changing the typed runtime boundary.

| Coverage item | Implementation | Verification |
|---|---|---|
| TCO forecast accuracy (FC-5) | Component purchase choices expose authored true and decoy cost categories; the purchase command persists the selected `tco_categories`. | Frontend lint/build pass; the existing component API remains green. |
| Over-forecast penalty (FC-6) | The purchase flow explicitly asks “What else will this cost?” and the existing engine compares the selection with actual TCO evidence in Debrief. | Full backend suite and guards pass; TCO remains typed through `CommandV1`. |
| Follow-through (FC-2) | In-flight component projects expose Continue/Pause/Kill actions through the existing `project` lifecycle command. | The command is accepted by the existing lifecycle reducer and is revision/lock checked by `SimulationService`. |
| Capital request (FC-7) | Budget now exposes the pack-authored CFO contract: one request per round, a maximum amount, a minimum justification length, and explicit approval rounds. Approved requests add a typed `capital_request` ledger entry and are included in capital availability, Review, and Debrief accounting. | Both shipped runtime packs load with provenance; consequence tests cover approval, persistence, amount bounds, and justification bounds. |
| Challenge rationale note (G2 safe path) | Challenge responses accept an optional bounded free-text note, persist it in response history and round results, and expose it in Debrief. The optional LLM modifier remains unimplemented and non-blocking. | Command, consequence, and frontend lint/build checks cover capture and persistence. |
| Data-freshness settings and scoring (G2 follow-up) | Runtime packs author capture-enabled and retention-round settings for platform services; Platform displays those settings, round results record required entities as fresh, produced-but-unserved, or unavailable, and Technology caps data adequacy by the produced coverage. Legacy callers without freshness evidence retain the prior score contract. | Runtime-load, consequence, scorer, API, and frontend checks cover settings, evidence, and consumption. |
| Full financial model | Modern round results now emit authored-revenue, capex, operating-cost, event-loss, debt, margin, capex-efficiency, debt-burden, and closing-balance evidence. The model allocates the authored annual `revenue_musd` evenly across the authored rounds; the modern Balanced Scorecard Financial base consumes the bounded model and marks `financial_partial=false`; legacy 1.4 callers retain the historical partial proxy. | Consequence and scorecard tests cover model bounds, persistence, and the financial base. Calibration of the allocation and weighting remains a review gate. |

The remaining M4 coverage gaps are deliberately open: LLM-based challenge rationale scoring
and strategy-balance calibration. The first bounded strategy review is recorded in
`docs/m4-strategy-playthrough-audit.md`; it is a failed balance review because every
exercised runtime state is Management-throttled at zero. The financial model is implemented
as a ledger-backed modern-runtime consumer; calibration and balance review remain separate gates.
The capital-request contract and the safe ungraded rationale-note path are now explicit and
executable; these other gaps still require separate pack and product decisions.
