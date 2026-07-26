# MIS Simulation — Implementation Plan

Covers all modules, the governance apparatus that constrains builder/auditor agents,
the UX approach, and the verification protocol. Written 2026-07-26.

Companion docs: `01-mis_lite-harvest.md` · `02-traceability-matrix.md` ·
`03-scoring-frame-options.md` · `04-decisions-g1-g6.md`

---

# 0. The problem this plan is actually solving

Two failure modes, in order of cost:

1. **Agent negligence** — code written without reading existing code, "done" claimed
   without browser proof, open decisions resolved silently, screens wired but unusable.
2. **Design drift** — the spec was right, the build diverged, nobody noticed until a
   student hit it in week 9.

The Camdani ecosystem already contains the counters. They are scattered across
`nexus/handoffs_v2/nexus-spec-authoring-protocol.md`, `worklab/GOVERNANCE.md`,
`worklab/docs/QUALITY_PROTOCOL.md`, `aide-platform/CONTRACTS.md`, and
`BECSR/handoffs_v1/AUDIT_readiness_protocol.md`. **This project adopts them as a set
from day one rather than accreting them after being burned.**

---

# 1. Module inventory

## 1.1 Engine and content

| Module | Description |
|---|---|
| **E1 Casepack schema** | The authored content contract: capabilities, catalog, entities, demand curves, watch rules, events, strategies, stakeholder preferences, policies |
| **E2 Casepack loader + registry** | Seeds packs from files; versioned; multiple packs coexist |
| **E3 Casepack validator** | CLI. Blocks a broken pack from ever reaching a section |
| **E4 Scoring engine** | Tech × Org × Mgmt per capability; graph analysis; pools; stakeholder alignment |
| **E5 Event/signal engine** | Watch rules, signal ledger, preconditions, blast-radius traversal |
| **E6 Round runner** | Lock → resolve → persist → produce round result |
| **E7 Calibration harness** | Headless. Scripted teams, printed score curves. **Built before any UI** |

## 1.2 Platform scaffolding

| Module | Description | Source |
|---|---|---|
| **P1 Course → Section → Instance → Team → Enrollment** | Multi-cohort hierarchy | adopt BECSR `course-section-management.md` |
| **P2 Instance scoping** | `instance_id` on every state table, from creation | adopt BECSR (they retrofitted; we won't) |
| **P3 Round scheduling** | Deadlines, auto-lock, auto-advance, grace period, bulk schedule | adopt BECSR `async-round-deadlines.md` |
| **P4 Auth / roles / routes** | Student, instructor, admin | adapt mis-tutor or BECSR |
| **P5 Grading config + override** | Weights, team/individual split, grade scale, `COALESCE(instructor, engine)` | adopt aide `aide_grading_config`, `aide_deliverable_grades` |
| **P6 Participation tracking** | Individual contribution within team | adopt aide `aide_participation` |

## 1.3 Student screens

| Module | Screen | Notes |
|---|---|---|
| **S0** | Shell — sidebar, top bar, persistent budget bar, round/countdown | see §3 |
| **S1** | Situation — scorecard, signals, capability cards | Tier-1 information |
| **S2** | Platform — hosting panels (Cloud \| On-Prem), shared services, split rule |
| **S3** | Applications — value chain view, capability slots, purchase wizard |
| **S4** | Organization — training, process, communication, IT staffing pool |
| **S5** | Governance — owners/sponsors, strategy declaration, portfolio, policy |
| **S6** | Challenges — inbox, event responses with rationale tags |
| **S7** | Review & Lock — decision sheet, warnings mirror, lock |
| **S8** | Debrief — causal trace, signals missed, TCO variance, BSC scorecard |
| **S9** | People — persona/stakeholder interviews (Tier-3 information) |

## 1.4 AI layer

Governed by `GOVERNANCE.md §4.7` (the LLM never computes anything scored) and `§4.8`
(personas may hold opinions, not numbers).

| Module | Description | Ported from |
|---|---|---|
| **A1 Coach + RAG** | Concept explanation grounded in the `mis_textbook` Qdrant collection, filtered to the course's active chapters. Explains the world; never evaluates the plan | mis-tutor `services/rag.py` (134 ln), `embedding.py` (23 ln) |
| **A2 Persona engine** | Stakeholders as interviewable characters — the Tier-3 information channel. **State-grounded:** every figure injected, never recalled | mis-tutor `services/conversation.py` (709 ln) |
| **A3 Debrief narrator** | Renders the engine's computed causal trace as prose with chapter links. Explains a result; does not produce one | new |
| **A4 LLM ops** | Three-tier fallback, timeouts, cost/latency logging, graceful degradation | mis-tutor `services/llm.py` (373 ln) |

**Live infrastructure** *(verified 2026-07-26)*:

```
Qdrant     192.168.50.186:6333 · collection mis_textbook · status green
           1,049 points · 1024-dim BGE-M3 · cosine
           payload indexed on: chapter (int) · section (kw) · content_type (kw)

LLM        primary   qwen-max via DashScope intl
           fallback  Qwen2.5-72B via Together
           local     Qwen2.5-14B-AWQ via vLLM @ 192.168.50.128:8000
```

The `chapter` payload index matters directly: the course is trimmed from 12 chapters to
~8, and `Course.active_chapters` already exists in mis-tutor as a JSONB list. The coach
filters retrieval to that list — a config change, not a code change.

### 1.4.1 Personas are casepack content, not platform content

Two layers, mirroring the stakeholder-preference structure in
`04-decisions-g1-g6.md`:

```
PLATFORM     14 stakeholder archetypes (harvested from mis_lite):
             C-Suite · Finance · Employees · Operations · IT · HR · Marketing
             Investor · Customer · Vendor · Security Auditor · Regulator ·
             General Public · Media

CASEPACK     persona instances that inhabit those archetypes:
             riverside_grocery →  Dana Ruiz, Warehouse Manager   = Operations
                                  Tom Beckett, COO               = C-Suite
                                  ...
             community_bank    →  a different roster, same archetypes
```

Consequence: **mis-tutor's existing personas do not port as content.** They are SCWIS
(University of Innovation) characters and belong to that case. What ports is the
*engine* (`conversation.py`) and the archetype layer. Each casepack authors its own
roster against the same 14 archetypes.

This is the same archetype-default mechanism already required for stakeholder
preferences — one structure serves both, and neither is authorable without it.

## 1.5 Instructor console

| Module | Screen | Source |
|---|---|---|
| **I1** | Course configuration + casepack selection | new + aib-study pattern |
| **I2** | Student roster / enrollment / CSV | adopt aide + aib-study |
| **I3** | Round control — schedule, lock, advance, pause | adopt BECSR |
| **I4** | Cross-team monitoring dashboard | adapt aib-study `Instructor.jsx` |
| **I5** | Grading view + override + export | adopt aide + aib-study |
| **I6** | Casepack registry + validator report | **new — no prior art** |
| **I7** | Clone / archive / reset course | adopt aib-study |

---

# 2. Governance apparatus — write these before any code

Four documents, adapted from proven originals. Every builder and auditor agent is
pointed at them in its opening instruction.

| Doc | Adapted from | What it constrains |
|---|---|---|
| `GOVERNANCE.md` | `worklab/GOVERNANCE.md` | Completion standard, browser-first rule, UX-as-build-requirement, design-system adherence, no-assumptions-when-inspectable |
| `QUALITY_PROTOCOL.md` | `worklab/docs/QUALITY_PROTOCOL.md` | The six-rung verification ladder; pre-merge gate |
| `SPEC_PROTOCOL.md` | `nexus/handoffs_v2/nexus-spec-authoring-protocol.md` | Spec Basis, `[V]`/`[A]` evidence tags, Pre-Flight Verification Register, Definition-of-Done table, falsifiable invariants, visual-acceptance rule |
| `CONTRACTS.md` | `aide-platform/CONTRACTS.md` | Cross-cutting field formats that drift between producers and consumers |

## 2.1 The five rules that do the most work

Lifted near-verbatim because they are already battle-tested:

1. **"The user experience is the truth. Backend wiring is incomplete until the browser
   proves the workflow works for the intended user."** *(worklab)*

2. **No assumptions when systems are inspectable.** mis_lite, BECSR, globalstrat,
   aide, aib-study, nexus are all readable. An agent that guesses at a schema instead of
   reading it has committed a violation, not a shortcut. *(worklab)*

3. **Evidence tags on every claim about existing code.** `[V]` verified — cites the
   quoted artifact. `[A]` assumption — names its confirmation step. No invented
   identifiers; names are quoted from verified code or marked **NEW**. *(nexus)*

4. **Settled vs Open, exhaustively.** Anything an agent might decide silently is either
   settled in the spec or listed Open with decision criteria and a reporting obligation.
   *"Obvious" is not a category.* *(nexus)* — this is the direct counter to silent
   improvisation.

5. **Visual-acceptance rule.** Any spec whose acceptance is how a screen reads ships
   with acceptance images. Prose UX standards alone are prohibited. *(nexus — noted
   there as "twice-proven")*

## 2.2 CONTRACTS.md seeds

Start it with the fields we already know will drift:

- `capability.required_roles[]` — bare role keys, never display names
- `entity.grain` / level-of-detail — canonical vocabulary, never free text
- `decision_line.category` — fixed enum shared by engine, UI, and scoring
- `signal.cleared_by[]` — action-type keys matched exactly by the responsiveness scorer
- `placement` — `on_prem` \| `cloud` \| `saas`, one spelling everywhere
- `instance_id` — present on every runtime row, no exceptions

---

# 3. UX approach — design system before screens

## 3.1 Lineage

The house style is settled and has a clear line of descent:

```
BECSR (becsr-design-system.md)
  ├─ IBM Plex Sans · dark navy sidebar #0F1724 · flat zero-radius cards
  ├─ content bg #F1F5F9 · accent left-border metric cards
  └─ reference-*.html mockups: "match these pixel-for-pixel"
        ↓  forked
globalstrat  — adds src/components/design-system/ as a real component library
        ↓  parallel
worklab (static/styles.css) — same lineage, mandated in GOVERNANCE
```

## 3.2 Adopt globalstrat's component library shape

`globalstrat/frontend/globalstrat-frontend/src/components/design-system/`:

```
PageHeader · PanelCard · MetricCard · MetricRow · DataTable
StatusBadge · SeverityIndicator · DeltaValue · ChartContainer
DSBudgetBar · InputField · TopBar · design-system.css · theme.css
```

This is the most evolved version in the ecosystem and it maps onto our screens almost
directly. Build the library **first**, as module S0, and forbid new visual patterns
without approval (worklab's rule).

## 3.3 Steal these specific patterns

| Pattern | Where | Why we need it |
|---|---|---|
| **Per-category status badges in the sidebar** (`configured` / `partial` / `error` / `empty`, fed by `getDecisionSummary`) | globalstrat `Sidebar.js` | Our Decisions sections need exactly this — a student must see at a glance what's incomplete before locking |
| **`canLock` derived from category status** | globalstrat `Sidebar.js` | Drives the Review & Lock gate |
| **Server-supplied `sidebarLabels`** | globalstrat `Sidebar.js` | **Casepack-configurable navigation labels** — a hospital pack can rename "Store Operations" without a code change |
| **PersistentBudgetBar / BudgetStatusBar** | BECSR `components/` | Our budget monitor is exactly this, plus the run-rate trend |
| **CountdownTimer + LockedBanner** | BECSR `components/` | Round deadline UX, already solved |
| **DecisionChecklist** | BECSR `components/` | Review & Lock mirror |
| **CreateProgramWizard** | BECSR `components/` | Template for the multi-step purchase wizard (S3) |
| **i18n via `react-i18next`, en + zh-CN** | globalstrat | BNBU cohort. Cheaper to build in than retrofit |

## 3.4 Mockup-first, per BECSR

For each student screen, produce a **static reference HTML mockup before the spec is
written**, in the BECSR manner (`reference-workbench.html`, `reference-dashboard.html`).
The spec then references the mockup, and the visual-acceptance rule makes the mockup the
acceptance criterion. Ten mockups; they are cheap and they prevent the "rearranged, not
designed" outcome nexus recorded.

---

# 4. The anti-negligence protocol

This is the part intended to stop the burning.

## 4.1 Three roles, never the same agent

```
  AUTHOR    writes the spec under SPEC_PROTOCOL.md
            produces: Spec Basis · Pre-Flight Register · DoD table ·
                      Playthrough Script (see 4.2)

  BUILDER   runs the Pre-Flight Register FIRST, reporting each row
            implements · fills the DoD table with evidence
            stops and reports on any spec/code conflict — never resolves silently

  AUDITOR   independent pass. Re-runs the Playthrough Script in a browser.
            Files findings with IDs. Does not fix.
```

The auditor never inherits the builder's context. That separation is the point.

## 4.2 Playthrough Scripts — written before the build, in student language

Your walkthrough practice, formalized as a **spec deliverable rather than a testing
afterthought**. Every student screen module ships with a numbered script written the way
a student would experience it, not the way a developer would test it:

```
PLAYTHROUGH — S3 Applications · purchase wizard
Persona: student on Team 4, round 3, strategy = Cost Leadership

  1. From Situation, click "Order Fulfillment — needs work"
     EXPECT: capability detail, coverage 4/5, missing slot flagged
  2. Click the empty INTEGRATION slot → "browse options"
     EXPECT: 3 options, each showing deploy mode, capex, opex, lead time
  3. Choose the SaaS option
     EXPECT: 3 required integrations listed with costs;
             warning that INVENTORY data leaves the platform;
             warning about no central identity
  4. Leave "Business sponsor" as none. Leave training at none.
     EXPECT: form still submits — no blocking validation
  5. Submit → open Review & Lock
     EXPECT: warning "you added capacity, funded no training"
     EXPECT: sidebar Applications badge = configured
  6. Lock the round
     EXPECT: LockedBanner appears; all decision inputs disabled
  7. Advance the round (instructor), return as student to Debrief
     EXPECT: realised value decomposition names Organisation as the throttle
```

**Rules that make these work:**

- Written by the AUTHOR, from the spec, **before any code exists**
- Every step has an `EXPECT` — a step without one is not a test
- Includes the *negligent* path deliberately (steps 4–5 above), because that's where the
  teaching is and where the engine is most likely wrong
- Executed by the AUDITOR in a real browser with a real session, per worklab's
  browser-first rule; Playwright where automatable, agent-driven where not
- Failures logged with stable IDs in the aide style
  (`S3-001`, `S3-002`) in `findings/` — see `aide-platform/TEST_ISSUES_LOG.md` for
  the format that worked
- A module is **not done** until its script passes end to end with zero console errors
  and screenshots attached

## 4.3 The full-game playthrough

Per-screen scripts miss engine defects. So one script plays **all six rounds as a team**,
through the UI, following a declared strategy — and a second plays the same rounds as
the *negligent* team (buys everything, trains nobody, ignores signals).

This is the UI-level counterpart to the calibration harness (E7). The harness proves the
maths; the playthrough proves the student can actually reach it. Run both before any
cohort touches it.

## 4.4 Verification ladder — the completion standard

Adopted from worklab, unchanged. No module is done without all six rungs, or a stated
reason a rung is N/A:

```
  1  Contract verification   schema, routes, request/response shape, auth
  2  Implementation          typecheck, lint, build, backend tests, migration dry-run
  3  Runtime                 dev servers up, health checks, browser login
  4  Browser diagnostics     zero console errors, zero failed network calls,
                             no user-facing technical error text
  5  UX / navigation         reachable from normal navigation; loading / empty /
                             ready / blocked / completed states; no overlap or
                             clipping at supported viewports; no raw JSON as UI
  6  Audit                   independent pass, playthrough re-run, findings filed
```

## 4.5 Standing canaries

Cheap checks that catch the failures that actually recur:

- **Auth canary** *(nexus standing law)* — before any browser-gated module is marked
  landed, prove one representative user logs in through the browser and completes one
  authenticated API call **on the same host pair under test**
- **Instance-isolation canary** — two sections on different casepacks; assert zero
  cross-reads. Run on every module that touches state
- **Casepack validator** — must pass for all packs before any round advances
- **Design-system canary** — grep new screens for hardcoded colours and font families;
  any hit is a violation

---

# 5. Phased plan

Each phase ends with a gate. No phase starts before the previous gate passes.

## Phase 0 — Governance and foundation *(no application code)*

- Write the four governance docs (§2)
- Decide repo location; stand it up
- Build the design-system component library (S0) + `theme.css`
- Produce all 10 student-screen reference mockups (§3.4)
- **Gate:** governance docs reviewed; mockups approved; component library renders a
  sample page matching a mockup

## Phase 1 — Domain, engine, calibration *(headless, no UI)*

- Spec A (Domain & Scoring Model) under `SPEC_PROTOCOL.md`
- E1 casepack schema · E3 validator · E4 engine · E5 events/signals · E6 round runner
- E7 calibration harness with four scripted teams
- Harvest mis_lite into Riverside pack v0 (per `01-mis_lite-harvest.md`)
- **Gate:** harness runs 6 rounds × 4 scripted teams; curves reviewed; **no dominant
  strategy**; validator passes on Riverside pack

> This gate is the highest-value moment in the project. If the model is broken, it is
> discovered here — by a script, not by thirty students.

## Phase 2 — Platform scaffolding

- P1 hierarchy · P2 instance scoping · P3 round scheduling · P4 auth
- E2 casepack loader + registry
- **Gate:** two sections, two different casepacks, instance-isolation canary passes,
  auth canary passes

## Phase 3 — Student core loop

S0 shell → S1 Situation → S2 Platform → S3 Applications → S7 Review & Lock → S8 Debrief

One module at a time: mockup → spec → build → audit → playthrough.

- **Gate:** the full-game playthrough (§4.3) completes 6 rounds through the UI

## Phase 4 — Student remainder + AI layer

S4 Organization · S5 Governance · S6 Challenges · S9 People
A4 LLM ops → A2 Persona engine → A1 Coach → A3 Debrief narrator

A4 first (fallback and timeout behaviour before anything depends on it). A2 pairs with
S9 — the People screen is the persona engine's only surface.

- **Gate 1:** negligent-team playthrough produces the intended teaching outcome —
  low realised value with a correct causal trace
- **Gate 2 (AI):** persona number-grounding audit — every figure in 20 sampled persona
  responses cross-checked against engine state, **zero mismatches**
  (`GOVERNANCE.md §4.8`)
- **Gate 3 (AI):** adversarial coach probe — 15 attempts to extract a recommendation
  ("what should I buy?", "is this good?", "would you go cloud?"). Zero may yield a
  decision recommendation (`GOVERNANCE.md §4.7`)

## Phase 5 — Instructor console

I1–I7. I6 (casepack registry + validator report) is the only genuinely new build.

- **Gate:** an instructor who has not seen the codebase can set up a section, load a
  pack, enrol students, schedule rounds, advance, and export grades — observed, not
  assumed

## Phase 6 — Second casepack

Author a pack in a different vertical (hospital or community bank) **using only the
documented schema and the validator**, with no engine changes permitted.

- **Gate:** if the engine needs changing, the domain model was not case-agnostic and
  the finding goes back to Phase 1. This is the real test of E1.

## Phase 7 — Pilot readiness

Launch-readiness audit in the BECSR manner
(`handoffs_v1/AUDIT_readiness_protocol.md`, `LAUNCH_READINESS_PLAYTHROUGH_spec.md`),
plus load check at cohort size, plus the student manual.

---

# 6. Known risks

| Risk | Mitigation |
|---|---|
| Calibration produces a dominant strategy | Phase 1 gate catches it before UI investment |
| Stakeholder preference authoring blocks pack 2 | Archetype-default mechanism is a **required** Spec A element (`04-decisions-g1-g6.md`) |
| Engine correct, UI unusable | Mockup-first + visual-acceptance rule + playthrough scripts |
| Agent invents identifiers | Evidence tags + Pre-Flight Register + CONTRACTS.md |
| Two sections leak data | Instance scoping from creation + standing canary |
| Scope creep back toward IT-course fidelity | The standing filter: *what does it cost, who does it affect, what happens if it fails* |
| **Coach drifts into advisor** — students ask it what to buy and it answers | `GOVERNANCE.md §4.7`; Phase 4 Gate 3 adversarial probe; prompt refuses evaluation of the student's own plan |
| **Personas state wrong numbers** — five occurrences in aide's test log | `GOVERNANCE.md §4.8`; state block injected into every persona prompt; Phase 4 Gate 2; auditor treats a mismatch as Blocking |
| LLM provider outage mid-round | A4 three-tier fallback (DashScope → Together → local vLLM). Persona/coach unavailability degrades to a stated status, never blocks a round lock |
