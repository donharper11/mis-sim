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

The remaining M4 coverage gaps are deliberately open: challenge free-text rationale quality,
exhaustive strategy playthrough balance, data-freshness producers, and the full financial model.
The capital-request contract is now explicit and executable; these other gaps still require
separate pack and product decisions.
