# Plan Index — every work packet, one page

The authoritative list. `design/05-implementation-plan.md` explains *why*; this says
*what and in what order*.

**8 phases · 43 work packets.**

## Numbering

One scheme: **`<phase>.<n>`**, sequential, no gaps, no letters.

The old module codes (`E4`, `S3`, `I1`, `A2`) survive only as **labels** so the
implementation plan's §1 inventory stays readable. They are not identifiers. Folder names
under `handoffs/` use the packet ID.

> **Numbering corrected, 2026-07-26.** Phase 0 previously used `0.4a`, `0.4b`, `0.6` —
> an artefact of reordering the mockups ahead of the component library. Now sequential:
> `0.3` = token map + mockup pilot (formerly `0.4a`), `0.4` = mockups ×7, `0.5` =
> component library. Folder `handoffs/0.3-mockup-pilot/` renamed accordingly.
>
> **"Phase" now means one thing.** Build steps inside a spec are **Steps**, not Phases —
> `0.3` Step 1 is the token map; project Phase 1 is the engine (`1.1`–`1.7`). The two
> were colliding.

---

## Phase 0 — Foundation · 5 packets

*No product code. Establishes governance, the repo, and the visual grammar.*

| ID | Packet | Label | Status |
|---|---|---|---|
| 0.1 | Governance set — GOVERNANCE, QUALITY_PROTOCOL, SPEC_PROTOCOL, CONTRACTS | — | ✅ merged |
| 0.2 | Repo scaffold, FastAPI + React skeleton, design tokens | — | ✅ merged `d638939` |
| 0.3 | Canonical token map + mockup pilot ×3 | — | spec written |
| 0.4 | Reference mockups ×7 | — | blocked on 0.3 review |
| 0.5 | Design-system component library | S0 lib | blocked on 0.4 |

**Gate:** governance reviewed · 10 mockups approved · library renders a mockup pixel-close

---

## Phase 1 — Engine · 7 packets

*Headless. No UI. The highest-risk phase and the highest-value gate.*

| ID | Packet | Label |
|---|---|---|
| 1.1 | Casepack schema — capabilities, catalog, entities, demand, watch rules, events, strategies, stakeholder preferences, policies | E1 |
| 1.2 | Casepack validator (CLI) | E3 |
| 1.3 | mis_lite harvest → Riverside pack v0 | — |
| 1.4 | Scoring engine — Tech × Org × Mgmt, graph analysis, pools, stakeholder alignment | E4 |
| 1.5 | Event / signal engine — watch rules, signal ledger, preconditions, blast radius | E5 |
| 1.6 | Round runner — lock, resolve, persist, round result | E6 |
| 1.7 | Calibration harness — 4 scripted teams, printed score curves | E7 |

**Gate:** 6 rounds × 4 scripted teams (do-nothing · all-tech-no-org · balanced ·
overspender) · curves reviewed · **no dominant strategy** · validator clean on Riverside

> If the model is broken it is found here, by a script, before a single screen exists.

---

## Phase 2 — Platform scaffolding · 5 packets

| ID | Packet | Label | Source |
|---|---|---|---|
| 2.1 | Course → Section → SimulationInstance → Team → Enrollment | P1 | adopt BECSR |
| 2.2 | `instance_id` on every runtime table, from creation | P2 | adopt BECSR |
| 2.3 | Round scheduling — deadlines, auto-lock, auto-advance, grace, bulk | P3 | adopt BECSR |
| 2.4 | Auth, roles, routes | P4 | adapt mis-tutor |
| 2.5 | Casepack loader + registry | E2 | new |

**Gate:** two sections on two different casepacks · instance-isolation canary ·
auth canary

---

## Phase 3 — Student core loop · 6 packets

| ID | Packet | Label |
|---|---|---|
| 3.1 | Shell — sidebar, top bar, budget strip, round countdown | S0 |
| 3.2 | Situation — scorecard, signals, capability cards | S1 |
| 3.3 | Platform — hosting panels, shared services, split rule | S2 |
| 3.4 | Applications — value chain, capability slots, purchase wizard | S3 |
| 3.5 | Review & Lock — decision sheet, warnings mirror | S7 |
| 3.6 | Debrief — causal trace, signals missed, TCO variance, scorecard | S8 |

**Gate:** full-game playthrough completes 6 rounds through the UI

---

## Phase 4 — Student remainder + AI layer · 8 packets

| ID | Packet | Label |
|---|---|---|
| 4.1 | Organization — training, process, communication, IT staffing pool | S4 |
| 4.2 | Governance — owners/sponsors, strategy declaration, portfolio, policy | S5 |
| 4.3 | Challenges — inbox, event responses, rationale tags | S6 |
| 4.4 | LLM ops — three-tier fallback, timeouts, cost logging | A4 |
| 4.5 | Persona engine — state-grounded, numbers injected never recalled | A2 |
| 4.6 | People — persona/stakeholder interviews (Tier-3 information) | S9 |
| 4.7 | Coach + RAG — `mis_textbook`, chapter-filtered, explains never advises | A1 |
| 4.8 | Debrief narrator — renders the computed trace as prose | A3 |

**Gates:** negligent-team playthrough produces a correct causal trace ·
persona number-grounding audit, zero mismatches · adversarial coach probe,
15 attempts, zero recommendations

---

## Phase 5 — Instructor console · 7 packets

| ID | Packet | Label | Source |
|---|---|---|---|
| 5.1 | Course configuration + casepack selection | I1 | new + aib-study |
| 5.2 | Roster, enrollment, CSV | I2 | adopt aide + aib-study |
| 5.3 | Round control — schedule, lock, advance, pause | I3 | adopt BECSR |
| 5.4 | Cross-team monitoring dashboard | I4 | adapt aib-study |
| 5.5 | Grading config, instructor override, participation, export | I5 · P5 · P6 | adopt aide |
| 5.6 | Casepack registry + validator report | I6 | **new — no prior art** |
| 5.7 | Clone / archive / reset course | I7 | adopt aib-study |

**Gate:** an instructor who has not seen the codebase sets up a section, loads a pack,
enrols students, schedules rounds, advances, exports grades — observed, not assumed

---

## Phase 6 — Second casepack · 2 packets

| ID | Packet |
|---|---|
| 6.1 | Author a pack in a different vertical (hospital / community bank) using only the documented schema and the validator |
| 6.2 | Verify zero engine changes were required |

**Gate:** if the engine needed changing, the domain model was not case-agnostic and the
finding returns to 1.1. This is the real test of the casepack schema.

---

## Phase 7 — Pilot readiness · 3 packets

| ID | Packet |
|---|---|
| 7.1 | Launch-readiness audit (BECSR `handoffs_v1/AUDIT_readiness_protocol.md` manner) |
| 7.2 | Load check at cohort size |
| 7.3 | Student manual |

---

## Totals

```
Phase 0  Foundation             5   ██░░░  2 merged
Phase 1  Engine                 7
Phase 2  Platform scaffolding   5
Phase 3  Student core loop      6
Phase 4  Student + AI           8
Phase 5  Instructor console     7
Phase 6  Second casepack        2
Phase 7  Pilot readiness        3
                               ──
                               43   2 complete
```

## Parallel tracks

Phases are not strictly serial. Two tracks can run once 0.3 is dispatched, because they
share no files:

```
TRACK A  visual    0.3 → review → 0.4 → 0.5
TRACK B  engine    1.1 → review → 1.2 + 1.4 → 1.5 → 1.6 → 1.7 → GATE
```

Phase 2 needs neither and can start any time after 1.1 settles the schema shape.
Phase 3 needs **both** tracks complete.

**The binding constraint is review capacity, not agents.** Two tracks is the ceiling —
beyond that the human gate becomes a rubber stamp, which converts this process into
theatre.
