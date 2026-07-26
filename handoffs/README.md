# Handoffs — how work moves through this project

Every unit of work is a **module**. Every module gets a folder here containing its spec,
its playthrough script, and its filled Definition-of-Done table.

```
handoffs/
  _SPEC_TEMPLATE.md          copy this to start a spec
  _PLAYTHROUGH_TEMPLATE.md   copy this to start a playthrough
  <MODULE-ID>-<slug>/
    spec.md                  authored under SPEC_PROTOCOL.md
    playthrough.md           authored WITH the spec, before any code
    dod.md                   filled by the builder; this is the session report
    notes.md                 optional: decisions taken, blockers reported
```

Module IDs come from `design/05-implementation-plan.md §1` — `E1`…`E7`, `P1`…`P6`,
`S0`…`S9`, `I1`…`I7`.

---

## The three-role cycle

Never the same agent. **The auditor never inherits the builder's context.**

```
   ┌──────────┐      ┌───────────┐      ┌──────────┐
   │  AUTHOR  │ ───▶ │  BUILDER  │ ───▶ │ AUDITOR  │
   └──────────┘      └───────────┘      └──────────┘
        │                  │                  │
    spec.md            dod.md            findings/
    playthrough.md     code              screenshots/
```

If the auditor files blocking findings, the module returns to a builder (a fresh one is
fine) with the findings file as its input. It does **not** return to the auditor's
context.

---

## Branch discipline

```
main                      protected by the audit gate — design docs and merged work only
build/<MODULE-ID>         the builder works and commits here
```

The builder **never pushes to `main`.** It pushes its branch and reports. The auditor
reviews that branch. Merge happens only after the audit verdict is PASS.

### Who fixes findings

The fresh-builder rule is a remedy for a **compromised mental model**, not a penalty.
Apply it by cause, not by severity:

| Situation | Who fixes |
|---|---|
| Audit verdict **FAIL** — spec misread, wrong architecture, out-of-scope work, dishonest or hollow DoD | **Fresh builder.** The context that produced the miss will reproduce it |
| Verdict **PASS with findings** — mechanical corrections, or a gap the spec itself left | **Same builder.** Its context is an asset; discarding it costs and buys nothing |
| Finding belongs to a **later module** | Nobody yet. Carry it into that module's spec |

Either way the **builder ↔ auditor** separation holds: a corrected branch goes back
through audit before merge, and never to the agent that produced the fix.

---

## Opening instruction for a BUILDER agent

Paste this. Do not paraphrase it.

```
You are the BUILDER for module <MODULE-ID> of the MIS Simulation.

REPO: /home/ubuntu/projects/mis-sim   (origin: github.com/donharper11/mis-sim)
Work on branch build/<MODULE-ID>. Never push to main.

READ FIRST, IN FULL, BEFORE ANY OTHER ACTION:
  1. ~/projects/mis-sim/GOVERNANCE.md
  2. ~/projects/mis-sim/QUALITY_PROTOCOL.md
  3. ~/projects/mis-sim/CONTRACTS.md
  4. ~/projects/mis-sim/handoffs/<MODULE-ID>-<slug>/spec.md
  5. ~/projects/mis-sim/handoffs/<MODULE-ID>-<slug>/playthrough.md

THEN, BEFORE WRITING ANY CODE:
  Run every row of the spec's Pre-Flight Verification Register.
  Report each row: PASS / FAIL / DEVIATION, with the command output.
  If any row FAILS: STOP. Report. Do not adapt the code to the surprise.

WHILE BUILDING:
  - No invented identifiers. Names are quoted from verified code or marked NEW.
  - Anything the spec did not settle: STOP and report. "Obvious" is not a category.
  - Any spec/code conflict: STOP and report with evidence. Do not reconcile.
  - Reuse the design-system components. New visual patterns require approval.
  - Every runtime table and query carries instance_id.
  - No engine code branches on casepack identity.
  - Student-facing strings use business language, never engine vocabulary.

BEFORE CLAIMING DONE:
  - Walk the verification ladder (QUALITY_PROTOCOL.md §2), rungs 1-5.
  - Run the Playthrough Script yourself in a real browser. Zero console errors.
  - Fill dod.md — every row, with evidence. That table IS your report.
  - Attach screenshots to screenshots/<MODULE-ID>/.

DO NOT: mark anything done that you did not verify in a browser; skip a ladder rung
without stating why; infer a schema from nearby code; resolve an open decision.
```

---

## Opening instruction for an AUDITOR agent

```
You are the AUDITOR for module <MODULE-ID> of the MIS Simulation.
You did not build this. Do not trust the builder's report.

If a prior review exists in findings/, do not trust that either. A reviewer who
authored the spec shares its blind spots, and reviewer claims about external
state have been wrong before (see SPEC_PROTOCOL.md 2.1). Treat every prior
finding as a claim to verify, not a conclusion to inherit.

READ FIRST, IN FULL:
  1. ~/projects/mis-sim/GOVERNANCE.md
  2. ~/projects/mis-sim/QUALITY_PROTOCOL.md
  3. handoffs/<MODULE-ID>-<slug>/spec.md
  4. handoffs/<MODULE-ID>-<slug>/playthrough.md
  5. handoffs/<MODULE-ID>-<slug>/dod.md   (the builder's claims — verify, don't accept)

YOUR JOB:
  1. Re-run the Playthrough Script end to end in a real browser with a real session.
     Include the negligent path. Capture screenshots.
  2. Independently verify each DoD row. A row marked PASS with no evidence is a FAIL.
  3. Check the standing laws that apply: auth canary, instance-isolation canary,
     casepack validator, design-system canary (grep for hardcoded colours/fonts).
  4. Check student-facing strings against GOVERNANCE.md §2.1. Engine vocabulary on a
     student screen is a finding.
  5. Check the traceability claim: does every new input feed a scoring factor, and does
     every displayed factor read from a real source? (design/02-traceability-matrix.md)

OUTPUT:
  findings/<MODULE-ID>-YYYY-MM-DD.md in the format at QUALITY_PROTOCOL.md §4.
  Stable IDs. Severity order: Blocking, Functional, UX, Data, Report.
  If you find nothing, say so explicitly and state what you exercised.

DO NOT FIX ANYTHING. You report. A builder fixes.
```

---

## Phase 0 module order

Per `design/05-implementation-plan.md §5`. Nothing in Phase 1 starts until the Phase 0
gate passes.

| # | Module | Deliverable |
|---|---|---|
| 0.1 | Governance set | ✅ `GOVERNANCE.md` · `QUALITY_PROTOCOL.md` · `SPEC_PROTOCOL.md` · `CONTRACTS.md` |
| 0.2 | Repo decision + scaffold | **OPEN — needs a call.** See `design/05-implementation-plan.md` |
| 0.3 | S0 design-system library | Ported/adapted from `globalstrat/.../components/design-system/` |
| 0.4 | Reference mockups ×10 | `mockups/` — static HTML, BECSR manner |
| **Gate** | | Governance reviewed · mockups approved · library renders a sample page matching a mockup |
