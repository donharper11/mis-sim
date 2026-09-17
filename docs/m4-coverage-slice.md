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
| Challenge rationale quality (G2 governed path) | Responses now persist an explicit, bounded `rationale_review` record. The disabled default is instructor-visible and neutral (`status=not_scored`, `modifier=1.0`); an injected evaluator is validated for the ±10% envelope and provider failures degrade to `unavailable` without blocking a round. The engine never applies the modifier to scored results. | Typed fallback/provider tests and consequence persistence checks pass. |
| Data-freshness settings and scoring (G2 follow-up) | Runtime packs author capture-enabled and retention-round settings for platform services; Platform displays those settings, round results record required entities as fresh, produced-but-unserved, or unavailable, and Technology caps data adequacy by the produced coverage. Legacy callers without freshness evidence retain the prior score contract. | Runtime-load, consequence, scorer, API, and frontend checks cover settings, evidence, and consumption. |
| Full financial model | Modern round results now emit authored-revenue, capex, operating-cost, event-loss, debt, margin, capex-efficiency, debt-burden, and closing-balance evidence. The model allocates the authored annual `revenue_musd` evenly across the authored rounds; the modern Balanced Scorecard Financial base consumes the bounded model and marks `financial_partial=false`; legacy 1.4 callers retain the historical partial proxy. | Consequence and scorecard tests cover model bounds, persistence, and the financial base. Calibration of the allocation and weighting remains a review gate. |

The remaining M4 review gate is pedagogical calibration. The strategy harness now supports a
coherent-plan calibration profile that maintains policy discipline, supports every live order
data rollout, and varies customer-system placement by declared strategy; the three negative
controls remain unchanged. The full matrix remains evidence for human review rather than an
automatic balance verdict. The rationale path is executable and governance-safe, but the default
provider remains disabled until an instructor explicitly opts into an approved evaluator. The
scoring model now preserves partial Technology, Organisation, and Management evidence through
authored weighted aggregation while retaining structural hard gates; the revised matrix is
recorded in `docs/m4-strategy-playthrough-audit.md`.
