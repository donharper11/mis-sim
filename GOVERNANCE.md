# MIS Simulation — Governance

**Status:** authoritative. Every human and every agent working on this project reads this
file before doing anything else.

---

## 1. What this is

A round-based business simulation for an undergraduate **Management Information Systems**
course (Laudon & Laudon, ~8 chapters, emphasis on Ch 1–3, 5, 6, 12).

Student teams inherit a company's existing IT estate, declare a competitive strategy,
and then run and modify that estate across six rounds — buying and wiring infrastructure,
funding training and change management, assigning governance, setting information policy,
and responding to events. They are scored on **realised business value**:

```
Realised Value  =  Technology Capability × Organisational Readiness × Management Quality
```

Multiplication, not addition. A zero anywhere zeroes the result. That is Laudon's
complementary-assets argument, made mechanical.

## 2. What it must feel like

It must feel like **running the IT function of a business**.

It must NOT feel like:
- an IT or networking course
- a shopping catalogue
- a quiz with a budget attached
- a generic LMS

### 2.1 The standing filter

Before any element ships — a screen, a decision, a metric, a label — it must pass:

> **What does it cost? Who does it affect? What happens if it fails?**

If a student needs to understand how the technology *works* to answer, it is an IT-course
element and it comes out. If they need to understand cost, people, and consequence, it
stays — however technical the engine underneath it is.

**Corollary:** the engine may be as technical as it needs to be; the interface must speak
business. Graph theory finds the single point of failure. The screen never says
"articulation point" — it says *"if the Kelso Road link fails, all 8 stores stop
selling."*

---

## 3. Completion standard

```
The intended user workflow works in the browser, with real data and real contracts,
without visible technical errors, and with audit evidence recorded.
```

A feature is not complete because the route exists, the tests pass, or the build is
green. See `QUALITY_PROTOCOL.md` for the ladder that proves it.

---

## 4. Core principles

### 4.1 No assumptions when systems are inspectable

Every system this project draws on is readable. An agent that guesses at a schema,
route, field, or behaviour instead of reading it has committed a **violation**, not a
shortcut.

| Source | Location | What to read it for |
|---|---|---|
| `mis_lite` DB | `192.168.50.38` · db `mis_lite` · user `donwh` | Harvested content: strategies, objectives, stakeholders, fit multipliers, add-ons, change-management options |
| BECSR | VM `192.168.50.5` `~/projects/BECSR` | Design system (`becsr-design-system.md`), Course/Section/Instance model (`course-section-management.md`), round deadlines (`async-round-deadlines.md`), audit protocol (`handoffs_v1/`) |
| globalstrat | VM `192.168.50.5` `~/projects/globalstrat` | Component library (`frontend/globalstrat-frontend/src/components/design-system/`), sidebar patterns (`Sidebar.js`) |
| aide-platform | `~/projects/aide-platform` | `CONTRACTS.md` format, grading config + instructor override, participation tracking, `TEST_ISSUES_LOG.md` findings format |
| aib-study | `~/projects/aib-study` | Instructor console tabs, exports, clone/archive/reset |
| worklab | `~/projects/worklab` | Governance and quality protocol originals |
| nexus | `~/projects/nexus` | Spec-authoring protocol original |
| mis-tutor | `~/projects/mis-tutor` | Component catalogue, React Flow canvas, personas, textbook RAG |

If access is blocked, **state the blocker explicitly**. Do not fill the gap with
plausible architecture.

### 4.2 Frontend experience defines completion

A feature is complete only when the workflow works in the browser for the intended user.
Required checks: representative authenticated session · the actual page under test · the
action that triggers the feature · visible success state · no user-facing technical error
text · no console errors · no failed network calls.

If the frontend errors, it is a platform defect. The root cause may be backend, schema,
data, routing, auth, or UI — the defect is not acceptable either way.

### 4.3 UX is a build requirement, not a cleanup phase

Every user-facing module specifies and verifies its navigation path, screen hierarchy,
core states, and responsive behaviour **before the backend is wired**. The navigation
path drives what the backend must provide, not the reverse.

Required: primary user path · loading / empty / ready / blocked / completed states ·
clear next actions and return paths · no overlapping or clipped controls at supported
viewports · no raw JSON or diagnostics as the primary interface · screenshots attached.

**Design-system adherence is mandatory.** Every screen adopts the component library in
`frontend/src/components/design-system/` (BECSR → globalstrat lineage: IBM Plex Sans,
dark navy sidebar `#0F1724`, flat zero-radius cards, content background `#F1F5F9`,
accent left-border metric cards). Builders creating or changing UI must:

- read this section and at least one existing reference screen before writing UI
- reuse existing design-system classes and components rather than introducing new visual
  patterns — **new patterns require explicit approval**
- attach before/after screenshots and the passing playthrough

A screen that is wired but off-template is not complete.

### 4.4 Settled vs Open — never decide silently

Anything an agent might decide on its own is either **settled** in the spec or listed
**Open** with decision criteria and a reporting obligation.

> **"Obvious" is not a category.**

A builder that encounters an unspecified case **stops and reports**. It does not
improvise, and it does not resolve a spec/code conflict on its own authority.

### 4.5 Instance scoping is non-negotiable

Every runtime table carries `instance_id` **from the moment it is created**. Every query
that reads game state filters on it. No exceptions, no "we'll add it later."

BECSR had to retrofit this with a backfill migration and the standing note *"No data
should ever leak between sections."* We do not repeat that.

### 4.6 The engine is casepack-agnostic

No case-specific logic in engine code. Ever. If Riverside Grocers needs behaviour that
a hospital would not, that behaviour is **authored content in the casepack**, not a
branch in the engine.

Test of compliance: a new casepack in a different vertical must be authorable using only
the documented schema and the validator, with **zero engine changes**. This is the
Phase 6 gate.

### 4.7 The LLM never computes anything that is scored

> **The LLM explains, role-plays, and teaches. The engine judges.**

Permitted AI roles:

- **Stakeholder personas** — in-world characters the student interviews (Tier-3
  information)
- **Coach** — concept explanation grounded in the `mis_textbook` collection, filtered to
  the course's active chapters
- **Debrief narrator** — renders the engine's computed causal trace as prose and attaches
  chapter links

**Forbidden: the advisor.** No AI surface answers *"what should we do?"*, *"is this a
good architecture?"*, or *"should we go cloud?"* An AI that evaluates the student's plan
destroys the decision the simulation exists to create. A coach explains the world; it
never evaluates the plan.

Any proposal to have an LLM produce a score, a ranking, or a recommendation is a
governance exception requiring explicit approval, and must state what the engine cannot
compute and why.

### 4.8 Personas may hold opinions. They may not hold numbers.

Every figure a persona states — a percentage, a cost, a count, a rate — is **injected
into the prompt from engine state**. A persona that is left to recall or infer a number
will state a wrong one.

This is not hypothetical. `aide-platform/TEST_ISSUES_LOG.md` records it five times in a
single test session:

> **STU-001:** COO Zhao cited waste rate 18% (actual 12.8%), SLA 78% (actual 72%),
> CSAT 4.05 (actual 3.6)
> **STU-005:** Zhao's reaction says "roughly ¥0 in annual savings" while the deployment
> summary shows CNY 535,920

**Rules:**
- A persona prompt carries an explicit state block of every figure that persona may cite
- If a figure is not in the state block, the persona does not mention figures
- The auditor cross-checks every number appearing in persona output against engine state.
  A mismatch is a **Blocking** finding, not a UX nit

### 4.9 Seed data, never stubs

**A screenshot of a screen with hardcoded content proves the HTML renders. It proves
nothing about whether the code works.** Roughly half the evidence gathered in Phase 0 was
of that kind.

The distinction is not pedantry:

```
STUB          a value written into the artifact to make it look complete
              proves rendering · proves nothing about computation
              e.g. <p>25%</p> in a mockup

SEED          real, coherent demo content loaded into the database, schema or
              config, from which the artifact COMPUTES what it shows
              proves the path from data to display actually runs
              e.g. a seeded team state the scorer reads and returns 0.249 from
```

**Rules:**

1. **Every packet producing a user-visible surface or a computed result ships seed data**
   and demonstrates the result computed *from* that seed. Not alongside it — from it.
2. **`TODO` in shipped content is a defect**, not a placeholder. Content that cannot yet
   be authored is marked `TODO: calibrate` **and listed in the report**, so it is visible
   rather than assumed.
3. **Evidence shows the seed in the loop.** A screenshot accompanied by the command that
   produced the data, or it is not evidence.
4. **One command produces a complete demo environment.** Any agent, any session, from a
   clean database. If a builder cannot reproduce the demo state in one step, neither can
   the next one.
5. **Estimates are allowed; unmarked estimates are not.** An authored value carries its
   rationale. Values that cannot be justified are marked and reported.

Static mockups are the one exception — they have nothing to compute from, which is
precisely why they cannot demonstrate that anything works, and why Phase 0's evidence is
weaker than it looked.

### 4.10 No user-facing failure notices as product behaviour

"Something went wrong, try again" is not an acceptable outcome. Users may see guidance,
status, progress, or next-step messages. They may not see our errors.

---

## 5. Standing laws

Cheap checks that catch the failures that actually recur. Each is a hard gate.

**Auth canary.** Before any browser-gated module is marked landed, prove that one
representative user logs in through the browser and completes one authenticated API
request **using the same session, on the same app-host/API-host pair under test**.
Cookie host mismatch invalidates otherwise-correct credentials.

**Instance-isolation canary.** Two sections running two different casepacks. Assert zero
cross-reads. Run on every module that touches game state.

**Validator gate.** No casepack reaches a section until `validate_casepack` passes clean.
No round advances on a pack with validator errors.

**Design-system canary.** Grep new frontend files for hardcoded colour values and
font-family declarations. Any hit is a violation.

---

## 6. Roles

Three roles. **They are never the same agent, and the auditor never inherits the
builder's context.**

```
AUTHOR    Writes the spec under SPEC_PROTOCOL.md.
          Delivers: Spec Basis · Pre-Flight Verification Register ·
                    settled/open decisions · build phases · Definition-of-Done table ·
                    Playthrough Script.

BUILDER   Runs the Pre-Flight Register FIRST and reports every row before writing code.
          Implements. Fills the DoD table with evidence.
          Stops and reports on any spec/code conflict — never resolves it.

AUDITOR   Independent pass with fresh context. Re-runs the Playthrough Script in a real
          browser. Files findings with stable IDs in findings/. Does not fix.
```

### 6.1 When the auditor must be a fresh agent

**Builder ≠ Auditor is absolute.** You verify what you intended to write, not what you
wrote. No exceptions, ever.

**Author ≠ Auditor scales with blast radius.** An author auditing their own spec shares
its blind spots — they will check the build against a mental model that may itself be
wrong. That matters enormously on some modules and barely at all on others:

| Module class | Auditor |
|---|---|
| Engine, scoring, casepack schema (`E*`), student screens (`S*`) | **Fresh agent, mandatory.** Spec errors here are expensive and reach students |
| Platform scaffolding, instructor console (`P*`, `I*`) | Fresh agent, strongly preferred |
| Infrastructure with **no student surface and no scoring factor** | Author-audit permitted, with the caveat declared in the findings file |

The author-audit exception requires **all** of: the module captures and displays no
scoring factor; it ships no student-facing screen; the builder ran the Playthrough Script
in a real browser and attached evidence; and the reviewer independently re-ran the
invariant checks rather than accepting pasted output.

**Applied once:** module 0.2 (scaffold), closed 2026-07-26 by user decision. See
`findings/0.2-2026-07-26-author-review.md`.

Fresh auditors are mandatory from **0.3 onward** — the first module with a visual
surface.

**An auditor's ACCEPT does not substitute for an author's ruling.** An auditor may *flag* a
decision a builder resolved without authority, but cannot bless it — the question routes to
the named authority regardless of the auditor's opinion. *(Proven: CR-001/CR-002, where the
first auditor accepted two decisions resolved without authority and a second, independent
auditor reversed them. One auditor's ACCEPT nearly shipped both.)*

### 6.2 Independent spec review before dispatch

Drift originates in the spec (`SPEC_PROTOCOL.md`, opening line), yet only the *build* was
ever independently audited — the spec got the author's own self-check, run by the agent with
the blind spot. That asymmetry is the common cause behind the spec-error findings of
Phase 1 (the same author wrote the acceptance list, the check set, and the invariants, and
never ran one against another).

**From here, a spec passes an independent review before a builder is dispatched.** A fresh
agent (not the author) runs the bounded checklist in `SPEC_PROTOCOL.md §11` — a consistency
pass, not a re-derivation. It gates *dispatch* the way the audit gates *merge*, and the
independence rule of §6.1 applies: for `E*`/`S*` modules the reviewer is a fresh agent,
mandatory. A spec review is minutes; a build-rework loop is days — this moves the cheapest
reviewer pass to where a spec defect is a text edit, not a rebuild.

---

## 7. Conflict rule

Spec vs README vs code disagreement → **stop, surface with evidence, await direction.**

Do not reconcile. Do not pick the one that seems right. The disagreement is itself the
finding.

**A spec that contradicts itself, and an input contract the spec never defined, are the same
class.** Neither is the builder's to resolve nor the auditor's to bless — both STOP to the
named authority. Choosing one arm of a contradiction "because the outcome is defensible" is
still resolving without authority. *(Proven: CR-001 — decision 3 vs decision 9 resolved by
the builder; CR-002 — an undefined `overrides` shape silently ignored. Both reached `main`'s
doorstep before the second auditor stopped them.)*

---

## 8. Document deltas

Contract changes are **merged into the living document** (version bump + changelog
entry), never shipped as standalone delta files. Unapplied deltas are letters nobody
opened.

---

## 9. Findings discipline

**A finding is closed, owned, or being fixed. There is no fourth state, and "flagged" is
not one of them.** Every audit appends its findings to `findings/OPEN-REGISTER.md` with an
owner before the packet that produced them merges.

- **Instance vs class.** A finding cannot be marked CLOSED at the instance level. Closing a
  defect *class* requires either the class-wide fix, or an explicit residue row naming an
  owner. **The auditor re-runs the class, not the builder's proof.** *(Proven: CU-001/B7 —
  the E00 collapse was fixed for one field and marked closed while five other closed
  vocabularies still collapsed the whole pack.)*
- **Every finding ships an executable closing check** — the command that fails while the
  finding is open and passes once it is fixed. A finding with no closing check is a claim,
  not an action.
- **Register reconciliation.** A packet that touches any finding ends with a reconciliation
  row in its DoD: every finding it fixed, re-tested on the *shipped* commit, its register
  row updated in the *same* commit. *(Proven: the 1.2 rework fixed five register rows and
  updated none; the entire catch-up-rework packet existed because owners were recorded but
  never converted into a dispatch — and it then reproduced the same defect, CU-001.)*

---

## Changelog

- **1.3** (2026-08-22) — plugged the Phase-1 rework gaps identified by the root-cause pass
  over 124 findings. Added §6.2 *Independent spec review before dispatch* (the spec was never
  independently reviewed, only self-checked — the common cause behind the spec-error
  findings); §9 *Findings discipline* (instance-vs-class closure, executable closing checks,
  register reconciliation — the catch-up-rework class); and strengthened §6.1 / §7 so a
  decision resolved without authority is a STOP the auditor may flag but not bless (CR-001/2).
- **1.2** (2026-07-27) — added §4.9 *Seed data, never stubs*. Every packet producing a
  visible surface or computed result ships seed data and demonstrates the result computed
  from it. One command produces a complete demo environment.
- **1.1** (2026-07-26) — added §6.1: auditor independence scales with blast radius.
  Builder≠Auditor absolute; Author≠Auditor mandatory for E*/S*, permitted-with-caveat for
  infrastructure with no student surface and no scoring factor. User decision, applied to
  module 0.2.
- **1.0** (2026-07-26) — initial. Adapted from `worklab/GOVERNANCE.md` and
  `nexus/governance_md_camdani_nexus.md`.
