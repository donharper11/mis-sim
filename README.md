# MIS Simulation

A round-based business simulation for an undergraduate **Management Information Systems**
course (Laudon & Laudon; ~8 chapters, emphasis on Ch 1–3, 5, 6, 12).

Student teams inherit a company's existing IT estate, declare a competitive strategy, and
run that estate across six rounds — buying and wiring infrastructure, funding training and
change management, assigning governance, setting information policy, and responding to
events. They are scored on **realised business value**:

```
Realised Value  =  Technology Capability × Organisational Readiness × Management Quality
```

Multiplication, not addition — Laudon's complementary-assets argument made mechanical.
Buy the ideal system, train nobody, realise almost nothing.

**Status:** Phase 0 **closed** · Phase 1 in progress · 4 of 47 packets complete.
FastAPI + React scaffold, two-tier design tokens, 19 reference mockups, and the casepack
module with a populated `riverside_grocery` pack are on `main`.

---

> **New to this project? Read [`BATTLECARD.md`](BATTLECARD.md) first.** Objective, the
> engine, the decision hierarchy, current state, open blockers, and the plan end to end —
> enough to pick up any packet and start.

## Read these first

| Document | What it governs |
|---|---|
| **`GOVERNANCE.md`** | Principles, the standing filter, completion standard, roles, standing laws |
| **`QUALITY_PROTOCOL.md`** | The six-rung verification ladder, playthrough scripts, findings format, pre-merge gate |
| **`SPEC_PROTOCOL.md`** | How specs are authored — evidence tags, pre-flight register, definition-of-done |
| **`CONTRACTS.md`** | Cross-cutting field formats. Read before touching any field listed |

Agents: read all four **in full** before your first action. The opening instructions for
builder and auditor roles are in `handoffs/README.md`.

---

## Repository layout

```
design/       settled design decisions — the thinking behind the build
handoffs/     one folder per module: spec · playthrough · definition-of-done
mockups/      static reference HTML; the acceptance criterion for visual specs
findings/     audit output, stable IDs, one file per module per audit
screenshots/  evidence attached to playthroughs
```

## Design documents

| # | Document | Contents |
|---|---|---|
| 01 | `design/01-mis_lite-harvest.md` | What transfers from the prior `mis_lite` build — and the component-master problem |
| 02 | `design/02-traceability-matrix.md` | Every scoring factor → UI that captures it → table that stores it. Plus the gap audit |
| 03 | `design/03-scoring-frame-options.md` | Balanced Scorecard vs Ch 1 objectives; recommendation |
| 04 | `design/04-decisions-g1-g6.md` | IT staffing as a load pool; stakeholder layer adopted, market layer deferred |
| 05 | `design/05-implementation-plan.md` | Module inventory, phases, gates, risks |
| 06 | `design/06-plan-index.md` | **The authoritative packet list** — every packet, one page |

---

## The one rule that decides everything

Before any element ships — a screen, a decision, a metric, a label:

> **What does it cost? Who does it affect? What happens if it fails?**

If a student needs to know how the technology *works* to answer, it is an IT-course
element and it comes out. The engine may be as technical as it needs to be. The interface
speaks business.

---

## External systems this project reads

Never guess at these — they are all inspectable. Full table in `GOVERNANCE.md §4.1`.

- **`mis_lite`** on `192.168.50.38` — the prior build; harvested content
- **BECSR** and **globalstrat** on `192.168.50.5` — design system, component library,
  Course/Section/Instance model, round scheduling
- **aide-platform**, **aib-study**, **worklab**, **nexus**, **mis-tutor** — local

---

## Open decisions

| # | Decision | Notes |
|---|---|---|
| 1 | Casepack verticals for packs 2–5 | Candidates: hospital, community bank, logistics, light manufacturing. Needed by Phase 6 |
| 2 | `G2` — the ±10% LLM rationale modifier | The only LLM-scored surface in the design. Cutting it remains defensible |

**Settled:** repository location (new repo, pieces ported from `mis-tutor`) ·
stack (FastAPI + React + Ant Design + Vite) · Balanced Scorecard as the visible score ·
stakeholder layer adopted, market layer deferred.

## Open blockers

See `BATTLECARD.md` §6. **No blocking findings open.** Carried work: six content gaps owned
by 1.3 (`findings/content-coverage-2026-07-27.md`, plus CG-6 from the 1.1 audit) and six
scoring factors with no UI capture point (`findings/field-coverage-2026-07-27.md`), which
land in Phase 3/4.

---

## Phase gates

```
0  Foundation             4 packets    CLOSED
1  Engine                 7 packets    ← current. 1.1 built and audited; 1.2 ready
   GATE: 6 rounds × 4 scripted teams, no dominant strategy
2  Platform scaffolding   5 packets    specced
3  Student core loop      8 packets    direction only
4  Student + AI          11 packets    direction only
5  Instructor console     7 packets    direction only
6  Second casepack        2 packets    direction only
7  Pilot readiness        3 packets    direction only
                         ──
                         47 · 4 complete
```

Authoritative packet list: `design/06-plan-index.md`.
