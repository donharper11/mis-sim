# M4 student coverage slice

Date: 2026-09-16

M4 is now underway. This bounded slice closes two previously homeless student inputs from the
field-coverage register without changing the typed runtime boundary.

| Coverage item | Implementation | Verification |
|---|---|---|
| TCO forecast accuracy (FC-5) | Component purchase choices expose authored true and decoy cost categories; the purchase command persists the selected `tco_categories`. | Frontend lint/build pass; the existing component API remains green. |
| Over-forecast penalty (FC-6) | The purchase flow explicitly asks “What else will this cost?” and the existing engine compares the selection with actual TCO evidence in Debrief. | Full backend suite and guards pass; TCO remains typed through `CommandV1`. |
| Follow-through (FC-2) | In-flight component projects expose Continue/Pause/Kill actions through the existing `project` lifecycle command. | The command is accepted by the existing lifecycle reducer and is revision/lock checked by `SimulationService`. |

The remaining M4 coverage gaps are deliberately open: authored capital-request approval rules and
the `request_capital` consequence, challenge free-text rationale quality, exhaustive strategy
playthrough balance, data-freshness producers, and the full financial model. They require pack
contract decisions before implementation; this slice does not invent those rules.
