# Plan Index — every work packet, one page

The authoritative list. `design/05-implementation-plan.md` explains *why*; this says
*what and in what order*.

**8 phases · 43 work packets.**

## Numbering

One scheme: **`<phase>.<n>`**, sequential, no gaps, no letters.

The old module codes (`E4`, `S3`, `I1`, `A2`) survive only as **labels** so the
implementation plan's §1 inventory stays readable. They are not identifiers. Folder names
under `handoffs/` use the packet ID.

> **Numbering corrected, 2026-07-26.** Phase 0 previously used `0.3`, `0.4`, `0.5` —
> an artefact of reordering the mockups ahead of the component library. Now sequential:
> `0.3` = token map + mockup pilot (formerly `0.3`), `0.4` = mockups ×7, `0.5` =
> component library. Folder `handoffs/0.3-mockup-pilot/` renamed accordingly.
>
> **"Phase" now means one thing.** Build steps inside a spec are **Steps**, not Phases —
> `0.3` Step 1 is the token map; project Phase 1 is the engine (`1.1`–`1.7`). The two
> were colliding.

---

## Phase 0 — Foundation · 4 packets · **CLOSED**

*No product code. Establishes governance, the repo, and the visual grammar.*

| ID | Packet | Label | Status |
|---|---|---|---|
| 0.1 | Governance set — GOVERNANCE, QUALITY_PROTOCOL, SPEC_PROTOCOL, CONTRACTS | — | ✅ merged |
| 0.2 | Repo scaffold, FastAPI + React skeleton, design tokens | — | ✅ merged `d638939` |
| 0.3 | Canonical token map + mockup pilot ×3 | — | ✅ merged `3395de8` |
| 0.4 | Reference mockups ×7 | — | ✅ merged `172de97` |

> **Closed 2026-07-27 at four packets.** Two items previously listed here were misfiled:
> the coverage-gap screens and the component library. Both are Phase 3 work — building
> them as mockups or as a library against unfinished layouts means building them twice.
> Moved to Phase 3 inputs.

**Gate:** ✅ met — governance in force, 19 mockups merged, visual grammar established

### Carried findings — must be consumed by the packet named, not just read here

Written in by the auditor of `0.3`, per `GOVERNANCE.md §8` — a finding parked in
`findings/` is a letter nobody opened. **Whoever authors the component-library spec must
fold these into it and say so in that spec's Spec Basis.** Until then they are open.

| Source | Item | Destination packet |
|---|---|---|
| `0.3-011` | **`IBM Plex Mono` is declared and never delivered.** `frontend/index.html:7` requests `IBM+Plex+Sans` only; `frontend/src/styles/theme.css:32` declares `--p-font-mono: 'IBM Plex Mono', 'Courier New', monospace`. No `@font-face`, no font file tracked, no font package in `package.json` — all three verified 2026-07-26. Body text is correct in production; **every monospace surface renders Courier New** (Liberation Mono on Linux). Only `/_dev/tokens` consumes the mono role today, so nothing student-facing is affected yet. **The spec must settle font delivery:** extend the CDN request to both faces, or self-host both and drop the third-party call — which for a BNBU cohort also removes a Google Fonts request from every student's browser. Hard-stops at Phase 7 pilot readiness | **component library** *(`0.5`)* |
| `0.3-002`, `0.3-009` | Both were value drift hidden under a deprecation note reading "rename". The 89-row table in `handoffs/0.3-mockup-pilot/dod.md` is the **only** map from the old token names to the new ones, and this packet ports globalstrat components against it. Read the notes, not just the columns | **component library** |

> **Numbering conflict, unresolved — flagged, not decided.** The correction block above states
> Phase 0 keeps its historical IDs (`0.3` · `0.4` · `0.5`); the Phase 0 table immediately
> below uses the clean scheme (`0.3` · `0.4` · `0.5`). `handoffs/README.md:159-162` and
> **RESOLVED 2026-07-26.** The contradiction is gone: Phase 0 is now `0.1 · 0.2 · 0.3 ·
> 0.4 · 0.5` everywhere — table, prose, README, spec, and folder name. Finding `0.3-012`
> is closed.

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

## Phase 3 — Student core loop · 8 packets

The loop a student actually runs: see where you stand → decide → lock → read what happened.

| ID | Packet | Label |
|---|---|---|
| 3.1 | **Design-system component library** *(was 0.6)* — built against real screens, not mockups. Implements the four `CONTRACTS.md` contracts; clears the four cosmetic findings parked from 0.3 | S0 lib |
| 3.2 | Shell — sidebar, top bar, capital strip with *Request more*, round countdown | S0 |
| 3.3 | Dashboard — Balanced Scorecard, unit-response chain, signals | S1 |
| 3.4 | Platform — hosting panels, firm-wide services, split rule | S2 |
| 3.5 | Components — the workbench table, detail tabs, six-step wizard | S3 |
| 3.6 | Rollout — deployments table, per-deployment mix | S4 |
| 3.7 | Review — decision sheet, warnings mirror, lock | S7 |
| 3.8 | Debrief — the downloadable business status report | S8 |

Phase 4 carries the rest of the sidebar: Strategy · Security · Services · People ·
Governance · Challenges, plus the AI layer.

**Inputs carried in from Phase 0:**

- `handoffs/0.5-coverage-gaps/spec.md` — **design input, not a mockup packet.** The
  Governance screen, the six information-policy switches, the TCO checklist and the
  capital request. Six scoring factors currently have no capture point anywhere
  (`findings/field-coverage-2026-07-27.md`). Built once here, wired, rather than twice.
  Governance itself lands in Phase 4; the policy switches, checklist and capital request
  land in 3.2, 3.5 and 3.2 respectively
- the four cosmetic findings parked from 0.3 — `.button`, `.close`, dead white in the
  Cloud panel, split-rule prose. They become real components at **3.1**
- the nineteen merged mockups as the visual reference

**Gate:** the full-game playthrough completes six rounds through the UI, **and** a re-run
of the field-coverage scan returns **zero** absences.

---

## Phase 4 — Student remainder + AI layer · 11 packets

| ID | Packet | Label |
|---|---|---|
| 4.1 | Strategy — declare, lock, what it measures you on | S5 |
| 4.2 | Governance — capability ownership, in-flight portfolio *(carries FC-1, FC-2 from the coverage scan)* | S5 |
| 4.3 | Security — components, gaps, and the six information-policy switches | — |
| 4.4 | Services — support tiers, integration tiers, vendor support | — |
| 4.5 | People — IT staffing capacity against operational load | S4 |
| 4.6 | Challenges — inbox, event responses, rationale tags | S6 |
| 4.7 | LLM ops — three-tier fallback, timeouts, cost logging | A4 |
| 4.8 | Persona engine — state-grounded, numbers injected never recalled | A2 |
| 4.9 | Stakeholder interviews — the Tier-3 information channel, not a decision | S9 |
| 4.10 | Coach + RAG — `mis_textbook`, chapter-filtered, explains never advises | A1 |
| 4.11 | Debrief narrator — renders the computed trace as prose | A3 |

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
Phase 0  Foundation             4   ████  CLOSED
Phase 1  Engine                 7
Phase 2  Platform scaffolding   5
Phase 3  Student core loop      8
Phase 4  Student + AI          11
Phase 5  Instructor console     7
Phase 6  Second casepack        2
Phase 7  Pilot readiness        3
                               ──
                               47   4 complete
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
