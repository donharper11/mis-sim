# Traceability Matrix

Every scoring factor traced to the UI that captures it, the table that persists it, and
the casepack content that parameterises it. Written **before** any spec, as a
completeness audit of the design.

**Read the Status column first.** It is the point of the document.

```
✅ complete    capture point, storage, and authoring all identified
⚠️  gap        factor described but something is missing
🔵 derived     no student input — computed from other captured data
❓ undecided   depends on an open design decision
```

All runtime tables are scoped by `instance_id` (BECSR pattern) — omitted per-row.

---

## A. Technology Capability

| Factor | Captured by (UI) | Persisted in | Authored in casepack | Status |
|---|---|---|---|---|
| Coverage — required roles filled | Applications › capability › slot fill; canvas node placement | `arch_node`, `arch_edge` | `capability.required_roles[]` | ✅ |
| Coverage — required data entities | Canvas data view; entity assignment on purchase | `entity_ownership` | `capability.required_entities[]` + level of detail | ✅ |
| Capacity — platform pool | Platform › shared services sizing | `platform_service.capacity`, `deployment.consumption` | catalog `sizing_driver` + `demand_curve` | ✅ |
| Capacity — application draw | Purchase wizard › config option (Core / +Forecasting / Full) | `deployment.config_tier` | catalog `base_draw`, `per_unit_draw` | ✅ |
| Reliability — path availability | *(none — consequence of what was placed)* | computed from `arch_node.availability` | catalog `availability` | 🔵 |
| Reliability — redundancy | Canvas: add sibling node / failover edge | `arch_node`, `arch_edge` | — (graph-derived) | ✅ |
| Single points of failure | *(none — computed)* | `round_result.spof_list` | — (graph-derived, zero authoring) | 🔵 |
| Data adequacy — integration | Purchase wizard › integrations to build; canvas edges | `arch_edge`, `integration_line` | catalog `must_be_fed_by`, `must_feed` | ✅ |
| Data adequacy — inconsistency | *(none — detected)* | computed from `entity_ownership` | — | 🔵 |
| Data currency / freshness | **deferred** — capture/storage → 3.4 Platform; round-to-round production → 1.6; scoring consumption → a future 1.4 follow-up once both exist | *(no producer yet; `platform_service.settings` is not implemented — 1.4 closeout §Verified facts)* | catalog option costs | ⚠️ **deferred — see register G2 / 1.4 closeout decision 12.** Not folded into `Component currency (EOL)`, which is a distinct EOL factor. |
| Component currency (EOL) | Standing decision › Lifecycle (patch/upgrade/retire) | `deployment.installed_round`, `.retired_round` | catalog `service_life` | ✅ |

---

## B. Organisational Readiness

| Factor | Captured by (UI) | Persisted in | Authored in casepack | Status |
|---|---|---|---|---|
| Training coverage | Purchase form › training tier radio; Organisation › training spend | `deployment_org_state.trained_pct` | catalog `people_affected`, training tiers + costs | ✅ |
| Training decay | *(none)* | recomputed each round | casepack `decay_rate` | 🔵 |
| Process fit | Purchase form › redesign process checkbox | `deployment_org_state.process_redesigned` | catalog `process_option` + cost | ✅ |
| Adoption rate | *(none — simulated)* | `round_result.adoption` | casepack adoption formula params | 🔵 |
| Resistance | Organisation › communication / participation spend | `org_unit.resistance` | casepack `resistance_base`, change-volume sensitivity | ✅ |
| Change volume shock | *(none — counted)* | derived from `decision_line` count/round | casepack sensitivity coefficient | 🔵 |
| IT staffing | Organisation › hire / retain / upskill | `it_staff` | casepack `staff_required_per_service` | ⚠️ **see G1** |
| Stakeholder alignment *(if mis_lite layer adopted)* | *(none — derived)* | `alignment_score` | `*_mapping.ideal_value`, OAR weights | ❓ **see G6** |

---

## C. Management Quality

| Factor | Captured by (UI) | Persisted in | Authored in casepack | Status |
|---|---|---|---|---|
| Governance coverage | Governance › owner + sponsor dropdowns per capability | `capability_assignment` | `capability[]` list only | ✅ |
| Strategic alignment | *(none — cosine similarity)* | `decision_line.capability_id` × `strategy_weight` | `strategy.capability_weights[]` | 🔵 |
| Portfolio concentration | *(none — Herfindahl over spend)* | `decision_line` | `strategy.expected_concentration` | 🔵 |
| Run/Grow/Transform mix | *(none — from catalog tags)* | `decision_line` + catalog `rgt_tag` | `strategy.target_rgt_mix` | 🔵 |
| Maintenance floor | *(none — ratio)* | `decision_line` category | casepack `maintenance_floor_pct` | 🔵 |
| Signal responsiveness | *(none — two timestamps)* | `signal.first_shown_round`, `decision.locked_round` | `watch_rule[]`, `signal.cleared_by[]` | ✅ |
| Follow-through | Governance › continue / pause / kill in-flight | `project.status_history` | catalog `duration_rounds` | ✅ |
| Deployed-but-never-trained | *(none — cross-check)* | `deployment` × `deployment_org_state` | — | 🔵 |
| Decision rationale consistency | Challenges › Fund/Defer/Reject + rationale tag | `inbox_response.rationale_tag` | `event.option[].tags` | ✅ |
| Rationale quality (±10% modifier) | Challenges › free-text box | `inbox_response.note` | rubric prompt | ⚠️ **see G2** |
| Policy alignment | Security/Policy › the six information-policy switches | `policy_decision.selected` (runtime; producer 1.6/2.x) | `policies[].options` (ordinal) + `preferences/policies.yaml` archetype ideals | ✅ *(scored 2026-08-21, 1.4 closeout §5.3a)* |
| Policy discipline (active decisions) | Security/Policy › committing each switch | `policy_decision.actively_decided` (runtime; producer 1.6/2.x) | `policies[]` with options; floor `0.25` | ✅ *(scored 2026-08-21, 1.4 closeout decision 7)* |

---

## D. Strategy, Policy, Cost

| Factor | Captured by (UI) | Persisted in | Authored in casepack | Status |
|---|---|---|---|---|
| Strategic intent declaration | Governance › strategy selector (locks R1–R2) | `team_strategy` (versioned) | `strategy[]` + measured-on metric | ✅ |
| Strategy reopen cost | Governance › reopen button | `team_strategy.version` | casepack `reopen_cost`, resistance spike | ✅ |
| Hosting placement | Platform › Cloud / On-Prem panels | `platform_service.placement` | catalog placement options + costs | ✅ |
| Hybrid split rule | Platform › split-rule selector (appears when both panels populated) | `platform_config.split_rule` | fixed option list | ✅ |
| Split-rule consistency | *(none — tag check)* | `platform_service.tags` vs `split_rule` | service tags | 🔵 |
| Information policy | Policy › 6 switches | `info_policy` | fixed switch set + cost/benefit per option | ✅ |
| Policy vs practice contradiction | *(none — tag check)* | `info_policy` vs `entity_placement` | entity `sensitivity` flag | 🔵 |
| Open privacy obligations | *(none — raised like signals)* | `obligation` | `obligation_rule[]` | ✅ |
| Capex committed | Review & Lock; Budget strip | `decision_line.capex` | catalog costs | ✅ |
| Opex run-rate | Budget strip (trend across rounds) | `round_result.opex_runrate` | catalog `opex_per_round` | ✅ |
| Debt ledger | *(none — accrues on deferral)* | `debt_item` | casepack `debt_accrual_rate` | 🔵 |
| Additional capital request | Budget › request from CFO (justification form) | `capital_request` | casepack approval rules | ✅ |
| TCO forecast accuracy | Purchase form › "what else will this cost?" checklist | `tco_forecast.selected[]` vs `actual_cost[]` | catalog `true_cost_categories[]` + decoys | ✅ |
| Over-forecast penalty | same checklist | `tco_forecast` reserved-vs-used | — | ✅ |
| Integration count | *(none — edge count)* | `arch_edge` | — | 🔵 |

---

## E. Outcomes and Feedback

| Element | Reads from | Status |
|---|---|---|
| Realised value per capability | Tech × Org × Mgmt per capability | ✅ |
| Causal trace ("throttled by …") | the three term decompositions | ✅ |
| Signals you missed, with round first shown | `signal` ledger | ✅ |
| Event resolution + blast radius | `arch_edge` traversal, `event.precondition` | ✅ |
| **Balanced Scorecard — Financial · Customer · Internal Process · Learning & Growth** | roll-up of §A/B/C/D per `design/03`; computed in 1.4 §5.4 | ✅ |
| Management question answerability | `entity_ownership`, `arch_edge`, level-of-detail | ❓ **see G3** |
| Competitor moves | `competitor_action` | ⚠️ **see G4** |
| Debrief written reflection | Debrief › reflection box | ⚠️ **see G5** |
| Instructor override of engine score | Instructor › grading view | ✅ (aide-platform pattern) |

---

## F. Instructor-side

| Element | Source pattern | Status |
|---|---|---|
| Course → Section → Instance → Team → Enrollment | BECSR `course-section-management.md` | ✅ adopt |
| Round deadlines / auto-lock / auto-advance / grace | BECSR `async-round-deadlines.md` | ✅ adopt |
| Grading config: weights, team/individual split, grade scale | aide `aide_grading_config` | ✅ adopt |
| Deliverable grades with instructor override (`COALESCE`) | aide `aide_deliverable_grades` | ✅ adopt |
| Participation / individual contribution | aide `aide_participation` | ✅ adopt |
| Console tabs: Config · Roster · Dashboard · Brief | aib-study `Instructor.jsx` | ✅ adopt |
| Export grades / engagement | aib-study `instructor.py` | ✅ adopt |
| Clone / archive / reset course | aib-study `instructor.py` | ✅ adopt |
| **Casepack registry** — which pack, version, validity | *none — new* | ⚠️ **see G7** |
| **Casepack validator** | *none — new* | ⚠️ **see G7** |

---

## G. Gaps found

The audit's output. Seven items, in priority order.

> **Status update (2026-07-26):** G1, G3, and G6 are settled — see
> `04-decisions-g1-g6.md`. G4 is deferred with the market layer. G2 and G5 remain open
> but non-blocking. G7 is a build item, not a design gap. **Spec A is unblocked.**

**G1 — IT staffing has no consequence.** ~~Cutting build-vs-buy removed its main purpose.~~
**SETTLED:** staff is an operational load pool; over-commitment degrades incident
recovery (Tech), lifecycle completion (Tech), and adoption support (Org). Capacity added
by hiring or by managed support tiers (harvested from mis_lite
`maintenance_support_levels`).

**G2 — Rationale quality is the only LLM-scored element.** Everything else is
mechanical. Either accept one small LLM surface (±10% modifier, instructor-visible) or
cut free text to an ungraded note. *Recommend: keep, capped, non-blocking.*

**G3 — Management question mechanic undecided.** **SETTLED:** no Analysis screen, no
query model. Instead, **ordinary round reporting is gated by data capability** — teams
without the data architecture see coarse results, teams with it see the detail. Scored
only through data adequacy (already present). Personas remain the channel for what no
report can reach, which also resolves the persona orphan in §H.

**G4 — Competitor moves not authored.** `competitors` has 5 rows; `competitor_actions`
has 0. The archetypes exist, their round-by-round behaviour does not. ~5 rivals × 6
rounds = 30 authored moves per casepack. *Add to casepack schema.*

**G5 — Reflection prompt has no home in the scoring model.** It's a gradeable artifact
(mis-tutor already has a journal feature) but nothing consumes it. Decide: instructor-
graded only, or feeds participation. *Low priority.*

**G6 — Stakeholder-alignment layer conditional.** **SETTLED:** the mis_lite chain
decomposes into three separable layers. Adopt layer 1 (stakeholder alignment) in v1 —
it preserves ~2,100 harvested rows, gives personas mechanical purpose, and feeds
Management Quality. Carry layer 2 (OAR weights) unconsumed. Defer layer 3 (market share
vs rivals) to the competitive phase. Adds a **required** new element to Spec A:
default-by-stakeholder-archetype, without which pack 2 is unauthorable.

**G7 — Casepack registry and validator do not exist in any prior platform.** Nothing in
mis-tutor, aide, aib-study, or BECSR does multi-pack content validation. This is genuinely
new build and it is what makes packs 2–5 authorable without head-scratching.

## H. Orphans

UI elements described in conversation that feed no scoring factor. Cut or justify:

- **Component-type browse view** (Hardware / Software / Database / Network by chapter) —
  pure reference. *Keep — it's the textbook mapping and costs almost nothing.*
- **Persona interviews (Tier-3 hidden info)** — currently feed no factor. Either they
  reveal information that changes decisions (justified), or they're decoration.
  *Resolve with G3 — same question.*
- **Value-chain framing on the Applications screen** — presentation only; capabilities
  are the scored unit. *Keep — Ch 3 mapping, zero cost.*
