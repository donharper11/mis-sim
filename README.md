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

**Status (2026-10-06):** A playable local platform with a decision-driven six-round
simulation, authenticated student workflows, and substantial instructor operations.
M0–M4 have recorded completion evidence; instructor setup/roster acceptance and browser
proofs for round control, monitoring, grading/export, registry and lifecycle are recorded.
Grounded persona backend support landed October 3. Full AI teaching support, roster
onboarding, a substantive second vertical, and production/pilot acceptance remain open.

**Paused checkpoint:** [next-agent handoff](handoffs/readiness-2026-10-06/NEXT-AGENT.md) records the resume point and accepted next contract.

**Start with [BATTLECARD.md](BATTLECARD.md) and [TODO.md](TODO.md).** These supersede
historical progress headlines in the north star and old handoffs; those files still govern
contracts and preserve audit history. Do not interpret original packet counts as current
product readiness. Latest committed baseline reviewed: `0a535ba` (2026-10-05); the working
tree also contains ongoing infrastructure and rollout changes. Current verification results
and remaining gates are recorded in the task list and [readiness report](docs/readiness-2026-10-06.md).
The [student guide](docs/student-guide.md), [pilot acceptance script](docs/pilot-rehearsal.md)
and [reproduction runbook](docs/readiness-runbook.md) support local rehearsal.

---

> The [implementation north star](design/08-implementation-north-star.md) defines delivery
> milestones and evidence gates. Its historical progress narrative is not current status.
> [BATTLECARD.md](BATTLECARD.md) gives current status; [TODO.md](TODO.md) owns the next actions.
> [Recovery execution and audits](handoffs/recovery/README.md) record exact candidates and limits.
> [Backend development](docs/backend-development.md) provides the fresh-install and disposable PostgreSQL recipe.

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
| 07 | `design/07-decision-consequence-map.md` | **Every decision → its stakeholder preference, scoring path and consequence.** The three-path test, and the two classes that fail it |
| 08 | `design/08-implementation-north-star.md` | Current delivery milestones, recovery ownership, dispatch boundaries and independent audit gates |

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

## Remaining work and verification

Follow the ordered queue in [TODO.md](TODO.md): build on the independently accepted
fixes and host scope/lifecycle migrations, implement the accepted instructor-start contract, repair SQLite archive, and execute the prepared pilot and
deployment rehearsals, finish teaching support and onboarding,
prove a second vertical, and polish the remaining visualizations/performance.

Recorded evidence:

- [October 6 readiness](docs/readiness-2026-10-06.md): 834 backend tests, all guards, frontend
  lint/build, six-round browser loop, host/controls proofs, PostgreSQL migration and restore.
  Fresh reviewers accepted the bounded backend/frontend corrections after rework; host
  scope migration 0012 also passed [independent acceptance](docs/host-scope-2026-10-06.md).
  Host activation/reset migration0013 also passed [independent acceptance](docs/host-lifecycle-2026-10-06.md).
  Instructor startup, SQLite archive and production/pilot gates remain open.

- [M3 browser loop](docs/m3-launch-readiness-audit.md): six rounds and persisted debriefs.
- [M4 completion](docs/m4-coverage-slice.md) and [accepted balance review](docs/m4-strategy-playthrough-audit.md).
- [Instructor setup audit](handoffs/m5/instructor-ops-audit.md): October 2 closure; 14 setup
  browser proofs and 20 M5.3–5.7 proofs recorded; 773 backend tests passed, one skipped then.
- [Operational rehearsal](docs/phase7-operational-audit.md): local migration, restore and
  cohort smoke passed; production deployment and observed pilot remain unverified.
- [M6 portability audit](handoffs/m6/portability-seam-audit.md): synthetic isolation is not
  a substantive second vertical.

Run `make check` in the declared Python environment and `npm run lint` / `npm run build`
in `frontend/`. Historical passes do not certify newer changes. See
[backend development](docs/backend-development.md) for dependency setup and disposable
PostgreSQL verification. Browser proofs must use disposable seeded data.

## Delivery milestones

| Milestone | Current disposition |
|---|---|
| M0 — baseline | Recorded complete |
| M1 — decision-driven simulation | Recorded complete |
| M2 — platform/auth/scheduling | Recorded complete for local/cohort scope |
| M3 — playable browser loop | October 6 six-round/cross-panel proofs and bounded independent reviews passed; pilot acceptance remains open |
| M4 — student coverage and balance | Recorded complete; balance accepted September 18 |
| M5 — instructor operations and teaching support | Instructor tooling implemented; full AI and onboarding remain open |
| M6 — second vertical and pilot | Open; no substantive second vertical or observed pilot acceptance |

The [original 47-packet index](design/06-plan-index.md) preserves scope, not a current
completion percentage. The original “11 closed” count predates the working application.
