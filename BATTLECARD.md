# MIS Simulation — Battlecard

**For any agent picking this up cold.** Read this first, then `GOVERNANCE.md`.
Verified against `origin/main` on 2026-07-27 · 67 commits · 4 of 47 packets complete.

---

# 1. What this is

A round-based business simulation for an undergraduate **Management Information Systems**
course at BNBU (Laudon & Laudon, trimmed from 12 chapters to ~8, emphasis on Ch 1–3, 5, 6
and 12).

Student teams inherit a company's existing IT estate — deliberately messy, grown by
accretion — declare a competitive strategy, then run and modify that estate across six
rounds. They buy and wire infrastructure, fund training and change management, assign
ownership, set information policy, and answer events.

**The problem it solves.** No good MIS simulation exists, and the reason is structural:
MIS has no natural objective function. Supply-chain sims work because profit is the score.
"Good IT infrastructure" is not a number, so the genre either specialises into security
(CyberCIEGE, HBP's *Cyber Attack!*), into flow (GamingWorks' *Phoenix Project*), or into
ERP process training (MonsoonSIM, ERPsim). None of them is an MIS course sim.

---

# 2. The engine — the one idea everything rests on

```
Realised Value  =  Technology Capability × Organisational Readiness × Management Quality
```

**Multiplication, not addition.** A zero anywhere zeroes the result. This is Laudon's
*complementary assets* argument made mechanical: buy the best system, train nobody, realise
almost nothing.

```
Technology     bought    computed from the architecture graph — coverage, capacity,
                         path availability, single points of failure, data adequacy
Organisation   funded    training, process redesign, communication, adoption, resistance
Management     earned    governance, strategic alignment, portfolio discipline,
                         signal responsiveness, follow-through
```

**Nothing in the catalog raises Management.** That asymmetry is the design.

### What makes it computable rather than judged

Almost nothing is LLM-scored. The rule: *if a factor cannot be computed from a click the UI
already captures or a timestamp the engine already has, it does not go in the engine.*

- **Technology** is graph analysis. Coverage is a set difference. Capacity is `min()` along
  a serving path. Reliability is a product. Single points of failure are articulation
  points. All zero authoring — they fall out of what the student drew.
- **Signal responsiveness** is two timestamps: when a dashboard signal was first shown, and
  whether a resolving action was taken before it fired.
- **Strategic alignment** is a dot product of spending against the declared strategy's
  weights.

### Signals and events

> **Signals are the game telling you what is coming. Events are the bill.**

Every serious event is preceded by a signal, and events fire on **preconditions, never
dice**. A student who loses can always see exactly why. Same event card, two teams,
opposite outcomes — determined by whether one failover edge exists.

---

# 3. The decision hierarchy

```
0  STRATEGY      declared rounds 1–2, then locked. Reopening costs capex and
                 spikes resistance. Sets what is measured and how everything
                 below is weighted.

1  PLATFORM      the FIRM-WIDE stage. Hosting posture (Cloud | On-Premises panels,
                 never radio buttons — hybrid is what you end up with) plus
                 firm-wide components and services. Data warehouse lives here.

2  COMPONENTS    the UNIT-LEVEL stage, entered through a six-step wizard.
                 Data marts live here. Catalog is conditional on what Platform
                 provides — you cannot buy what your foundation cannot run.

3  ROLLOUT       pin a component to a functional unit, then allocate the mix:
                 training · process redesign · communication.
                 Per deployment, never bulk. A marketing mix is product-specific.

—  GOVERNANCE    ownership, portfolio, information policy. Costs nothing but attention.
—  CHALLENGES    events arriving against what you built
—  REVIEW        the decision sheet, the warnings mirror, the lock
```

**1, 2 and 3 are where every dollar goes.** Governance is free, and teams still skip it —
that is the lesson.

**The wizard's steps 3 and 4 are load-bearing:** *for what purpose* and *for whom*. They are
what make a unit's response computable. You declared what it was for and who it was for, so
alignment can be measured. Neither may be skippable.

---

# 4. Design decisions and their reasoning

| Decision | Why |
|---|---|
| **Balanced Scorecard is the visible score; MOT is under the hood** | BSC's four perspectives map onto what the engine produces, and **Learning & Growth** is the only frame with a slot for the organisational term. MOT surfaces in one place: the Debrief, where it explains |
| **Legacy skeleton, never a blank slate** | No MIS manager gets greenfield. The inherited mess *is* the teaching material, and round 1 becomes triage rather than a 50-item shopping trip |
| **Independent teams, not competitive** | IT quality is not naturally zero-sum. Leaderboard deferred; the market layer exists in the harvested data and is switched off |
| **Stakeholder alignment consumes *realised* value, not spend** | Buy the ideal ERP, train nobody, and Operations is still unhappy — because the system is not delivering, not because you bought the wrong box |
| **Casepack-agnostic engine** | No engine code branches on case identity, ever. A hospital pack must be authorable from the documented schema with zero engine changes. That is the Phase 6 gate |
| **Ethics rides the signal machinery** | Privacy obligations are raised, cleared and arm events exactly like capacity signals. No parallel subsystem, and no moralising — the sim ships attributes and consequences, never a stance |
| **The LLM never computes anything scored** | Permitted: stakeholder personas, a concept coach, a debrief narrator. Forbidden: the advisor. An AI that evaluates the student's plan destroys the decision the sim exists to create |
| **Personas may hold opinions, never numbers** | Every figure a persona states is injected from engine state. `aide-platform`'s test log records five hallucinated figures in one session |

---

# 5. Current state, verified

```
Phase 0  Foundation             4   CLOSED
Phase 1  Engine                 7   1.1 built and audited; 1.2 ready
Phase 2  Platform scaffolding   5   specced
Phase 3  Student core loop      8   not specced
Phase 4  Student + AI          11   not specced
Phase 5  Instructor console     7   not specced
Phase 6  Second casepack        2   not specced
Phase 7  Pilot readiness        3   not specced
                               ──
                               47   4 complete
```

**On `main`:** FastAPI + React scaffold · two-tier design tokens (38 primitives, 115
semantic roles) · self-hosted IBM Plex · **19 static mockups** · the casepack module
(models, loader, checks, seed) · a fully populated `riverside_grocery` pack with no `TODO`s.

**Specs written:** 12 across Phases 1 and 2, plus `0.5-coverage-gaps` which is now design
input to Phase 3/4 rather than a packet.

---

# 6. Open items — read before touching anything

### 1.1-001 · CLOSED 2026-07-27 by user decision · no action

1.1's implementation reached `main` inside a commit titled *"Add 0.5 coverage-gaps spec"* —
swept there by a `git add -A` on a shared working directory. The audit's verdict was
**substance PASS, lineage FAIL**: I1–I8 re-run independently, `CONTRACTS.md` checked field
by field, the seeder executed.

**Disposition:** `findings/1.1-2026-07-27-audit.md` stands as the record of audit for
`621b8d2`'s engine content. No revert, no re-land. The provenance is documented rather than
rewritten — history cannot be un-committed, and the code was verified on its merits.

*Carried forward:* `1.1-002` (two authored homes for round-3 capital) became **CG-6** in
1.3 — derive the roll-ups rather than authoring them twice. Closing CG-6 also closes
`0.4-002`.

### Content gaps in the shipped pack — all owned by 1.3, which has not run

```
CG-6  round-3 capital authored in two places → derive it   (from 1.1-002)
CG-1  5 of 7 capabilities have no watch rule → they can never raise a signal,
      are invisible to responsiveness scoring, and can never arm an event
CG-2  3 event cards for 6 rounds × 4 strategies → strategies that draw nothing
CG-3  nothing defines project duration → follow-through cannot detect abandonment
CG-4  3 policy switches against the 6 designed
CG-5  no obligation_rules.yaml → the whole Ch 4 ethics layer is inert
```

### UI gaps — six factors have no capture point anywhere

Governance ownership · in-flight portfolio · information policy · capital request · the TCO
forecast checklist (×2). Carried into Phase 3/4 by `handoffs/0.5-coverage-gaps/spec.md`.

**Two of Management Quality's six sub-factors need student input and both are homeless**, so
a student currently cannot *do* management, only have it inferred.

---

# 7. How work moves

Three roles that **never share context**. The auditor never inherits the builder's.

```
AUTHOR    writes the spec under SPEC_PROTOCOL.md
          delivers: Spec Basis · Pre-Flight Register · settled/open decisions ·
                    build steps with verify · Definition-of-Done · Playthrough

BUILDER   runs the Pre-Flight Register FIRST and reports every row
          implements · fills the DoD with evidence
          STOPS on anything unspecified — never resolves a spec/code conflict

AUDITOR   fresh context. Re-runs everything. Files findings with stable IDs.
          Does not fix.
```

Verbatim dispatch prompts live in `handoffs/_prompts/`. **Paste them; do not paraphrase.**

### The rules that exist because something went wrong

| Rule | What it cost to learn |
|---|---|
| `GOVERNANCE §4.9` **seed data, never stubs** | Half of Phase 0's screenshots proved HTML renders and nothing more |
| `SPEC_PROTOCOL §4.1` **name one compliant route** | A spec shipped three jointly unsatisfiable invariants; no build could pass |
| `SPEC_PROTOCOL §4.2` **out-of-scope claims are verified** | A spec forbade touching files that consumed what it changed |
| `SPEC_PROTOCOL §2.1` **findings carry their proof** | A reviewer twice asserted a dependency fix existed; a builder queried the registry and was right |
| `QUALITY_PROTOCOL §1` **verify state, not exit codes** | Four consecutive false "pushed" claims — `git push origin main` exits 0 when `main` has not moved |
| `README R5` **a finding against an artifact is not closed by amending the spec** | A defect was marked fixed while the broken file stayed merged |
| `README R3` **Part B is run by an agent that has not read the spec** | An auditor who had read the copy list four times correctly refused |

**Invariants are phrased as positive requirements.** One phrased as *"no skip affordance"*
passed while the wizard never asked at all — an invariant written as the absence of a
control is satisfiable by a design with no controls.

---

# 8. External systems — all inspectable, never guess

| System | Where | For |
|---|---|---|
| `mis_lite` | `192.168.50.38` db `mis_lite` user `donwh` | **A prior build of this same sim.** 79 tables, ~2,100 authored preference rows, 168 fit multipliers, 14 stakeholders. Harvest source |
| BECSR | VM `192.168.50.5` `~/projects/BECSR` | Design system · `reference-workbench.html` and `reference-management.html` are the list→detail→tabs grammar · Course/Section/Instance model · round scheduling |
| globalstrat | VM `.5` `~/projects/globalstrat` | Component library shape · sidebar with per-category status badges and server-supplied labels |
| aide-platform | `~/projects/aide-platform` | `CONTRACTS.md` format · grading config with instructor override · findings format |
| aib-study | `~/projects/aib-study` | Instructor console tabs · exports · clone/archive/reset |
| worklab · nexus | `~/projects/` | Governance and spec-protocol originals |
| mis-tutor | `~/projects/mis-tutor` | Persona engine · RAG · LLM fallback chain · Course/Team models |
| Qdrant | `192.168.50.186:6333` | `mis_textbook`, 1,049 points, BGE-M3, chapter-filterable |

---

# 9. The plan, end to end

**Phase 1 — Engine (7, specced).** `1.1` casepack schema · `1.2` validator · `1.3` harvest
· `1.4` scoring · `1.5` events and signals · `1.6` round runner · `1.7` calibration harness.

> **`1.7`'s gate is the highest-value moment in the project.** Four scripted archetypes ×
> six rounds, four numeric conditions: **no dominant strategy** (spread ≤ 0.15) ·
> complementary assets bind (`all_tech_no_org` < half of `balanced`) · all three terms
> load-bearing · no single dominant lever. **Do not tune numbers to pass it without
> understanding the failure** — a tuned-to-pass model is worse than a failing one because
> it looks finished.

**Phase 2 — Platform scaffolding (5, specced).** Course→Section→Instance→Team hierarchy ·
`instance_id` on every runtime table from creation · round scheduling · auth · casepack
registry.

**Phase 3 — Student core loop (8, direction only).** Component library first, built against
real screens. Then shell, Dashboard, Platform, Components, Rollout, Review, Debrief. The
19 mockups are the visual reference; `CONTRACTS.md` wins where they disagree. *Gate: six
rounds through the UI, and the field-coverage scan returns zero absences.*

**Phase 4 — Student remainder + AI (11, direction only).** Strategy · Governance · Security
· Services · People · Challenges, then LLM ops → persona engine → interviews → coach →
debrief narrator. *Gates: persona number-grounding audit with zero mismatches; adversarial
coach probe, 15 attempts to extract a recommendation, zero may succeed.*

**Phase 5 — Instructor console (7, direction only).** Mostly assembly from aide, aib-study
and BECSR. The genuinely new build is the **casepack registry and validator report** — no
prior art anywhere. *Gate: an instructor who has not seen the codebase sets up a section,
loads a pack, enrols students, advances rounds and exports grades — observed, not assumed.*

**Phase 6 — Second casepack (2, direction only).** Author a hospital or community-bank pack
using **only** the documented schema and the validator. *Gate: if the engine needs changing,
the domain model was not case-agnostic and it goes back to 1.1.*

**Phase 7 — Pilot readiness (3, direction only).** Launch-readiness audit in the BECSR
manner · load check at cohort size · student manual.

---

# 10. Start here

```bash
git clone https://github.com/donharper11/mis-sim && cd mis-sim
cp .env.example .env && docker compose up -d
curl -s localhost:8000/api/health          # {"status":"ok"}
python -m app.casepack.seed riverside_grocery
```

Then read, in order: `GOVERNANCE.md` → `QUALITY_PROTOCOL.md` → `SPEC_PROTOCOL.md` →
`CONTRACTS.md` → `design/06-plan-index.md` → the spec for your packet.

**Before your first commit:** never `git add -A`. This working directory is shared with
other agents, and three separate times that command swept someone else's uncommitted work
into the wrong commit — including an entire module.

**The standing filter, applied to everything:**

> **What does it cost? Who does it affect? What happens if it fails?**

If a student needs to know how the technology *works* to answer, it is an IT-course element
and it comes out. The engine may be as technical as it needs to be. The interface speaks
business.
