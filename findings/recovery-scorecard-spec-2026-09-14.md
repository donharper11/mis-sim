# Scorecard contract independent spec review

Date: 2026-09-14. Author: `scorecard_author`. Reviewer: `report_auditor`, a separate
agent with no scorecard author/build role. Supervisor transcribes the returned review
here and owns the separate authority ruling in the handoff's `review.md`.

Initial candidate `6caf40ba7ed34dd835441805fa69d3b714751c03`: **RETURN**.
Corrected candidate `0716eb9e49f9dbe38d0505dca81f42a8c3ee3ca8`: **PASS**.
The supervisor's integration status annotation does not change the reviewed contract.

| Finding | Reproduced defect | Correction / closing evidence |
|---|---|---|
| SC-SR-001 | Same-model `model_validate(instance)` can return a mutated invalid outcome unchanged. Reviewer reproduced bool corruption through direct map mutation, `model_copy` and `model_construct`. | **CLOSED at spec review.** §3.3 and the compliant route explicitly reconstruct `dict(event.outcomes)` before model validation. Reviewer independently verified all three invalid forms are rejected without input mutation. N3 requires the eventual implementation to test all three. |
| SC-SR-002 | The proposed living 1.6 line replacement remained under a loop restricted to events with bound nodes. Actual Balanced R1 ransomware/phishing events have `node=None` and still contribute penalties. | **CLOSED at spec review.** The exact replacement now covers the entire loop: record every fired event, condition only outage evidence on node/capability, keep ledger advancement outside. Reviewer checked the replacement against the actual old loop and persisted event records. |

All five `SPEC_PROTOCOL §11` checks pass on the corrected candidate: acceptance mapping,
falsification, cross-document consistency, concrete compliant route, schema consumers
and vocabulary. The author's executable probes were independently run: six source/consumer
plants, two baseline plants, eight invalid input classes; **251 shipped event rows** are
compatible with the proposed stricter shape. Proposed unknown Literal-key failures route
to the existing **E18**. Historical scoring/round pins: **14 passed**. The proposed
acceptance probe fails on the old helper, as required.

Independent persisted-event arithmetic reproduces the proposed Balanced R1 values:
Financial **0.696932**, Customer **0.6083**, Internal Process **0.313523**, Learning &
Growth **0.369272**; unchanged firm score **0.35825**. These are contract expectations,
not a claim that the correction is implemented. Earlier arrivals/debt writes remain the
caller's rollback responsibility; late validation promises no ledger/result/pointer
publication, not full atomicity. The exclusion agrees with actual runner ordering.

Evidence directory: `/tmp/scorecard-spec-review-396z5_uz/`. Targeted re-review reproduced
both corrections; unrelated unchanged arithmetic and pin runs were not repeated.
No code was built by the author or reviewer. **NS-003 remains open** until an independent
implementation audit and supervisor reproduction close it. PF6 and an exact dispatch
base remain builder-start requirements.
