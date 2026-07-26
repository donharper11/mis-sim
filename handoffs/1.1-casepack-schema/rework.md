# 1.1 — Rework Instruction

**Drafted by:** the AUDITOR of `findings/1.1-2026-07-27-audit.md` · **Date:** 2026-07-27
**Branch:** `build/1.1-casepack` @ `a27e6cc` · **Verdict:** substance PASS · lineage FAIL

> # ⛔ GATE LIFTED — 2026-07-27. NO BUILDER ACTION REQUIRED. THIS PACKET IS CLOSED.
>
> **The gate was over-calibrated and it is withdrawn.** A builder reached it, correctly
> refused to choose a value, and reported — exactly as instructed. The instruction was the
> problem, not the response.
>
> `1.1-002` is a **Data** finding, and the audit never rated it blocking. Gating a builder on
> it treated a display fixture as though the engine read it as ground truth. It does not:
> `seed.py` persists nothing, the 0.2 baseline migration is still `pass`, and neither the
> scoring engine (1.4) nor the round runner (1.6) exists. Nothing consumes these figures, and
> **1.3 rebuilds the pack from the mis_lite harvest**, at which point authored fixtures are
> replaced wholesale. Blocking work now to correct $2,000 in a figure that is about to be
> regenerated buys nothing.
>
> **Disposition:** carried to `handoffs/1.3-harvest/spec.md` §5.1a as **CG-6**, where §5.4a
> already reads the pinned figures back against 0.4 §5.4 — the check that makes it matter.
> Closing CG-6 also closes `0.4-002`.
>
> **1.1-001 (lineage) is unaffected and still open.** It is a separate finding, it is not a
> builder task, and it is recorded below. Do not read this closure as covering it.
>
> Nothing below requires action. It is retained as the record of what was asked and why.

---

**Scale check.** The 1.1 audit produced three findings and **only one is builder work.** The
other two are a decision about `main` and a withdrawal of the auditor's own error. Do not read
the audit's length as the size of this packet.

**Who reworks.** `handoffs/README.md`, by cause not severity: nothing here came from a
compromised mental model — the builder worked the branch it was given and its DoD was honest —
so this is the **same builder**. The corrected branch still returns to a fresh auditor before
merge.

---

## Blocked on the author

| # | Decision | Why a builder cannot take it |
|---|---|---|
| 1 | **Which round-3 capital figure is authoritative, and where is the other derived from?** `pack.yaml:22` authors `capital_remaining: 44000`; `pack.yaml:84` carries `46000`, which is exactly `220000 − 174000`. Both claim round 3 against the same `capital_available`. Remaining cannot rise after committing `174000` | Picking a number *is* the design decision. `SPEC_PROTOCOL.md §3` — *"one source of truth per fact… prefer elimination over reconciliation"* — says which shape to prefer, not which value is right |

---

## Not in this packet — the user's call, no builder action

**1.1-001, the lineage breach.** Module 1.1's implementation reached `main` in `621b8d2`, a
commit whose subject and body describe only a 0.5 spec: `models.py` (400 lines), `loader.py`,
`seed.py`, `checks.py`, and the 14-file Riverside pack. No build branch, no audit, and nothing
in the history that discloses it.

A builder cannot fix where a commit landed. What is needed is a choice —

1. **retro-audit in place.** `findings/1.1-2026-07-27-audit.md` already audits that content in
   full (I1–I8 re-run, `CONTRACTS.md` checked field by field, seeder executed). Accepting that
   as the audit of record closes it, provided the gap is *recorded* rather than normalised; or
2. **revert and re-land** the engine content through `build/1.1-casepack` so the history reads
   correctly.

— plus the same check applied to `fc08c08` *"Seed data, never stubs"* and `267907f` *"Fix
0.4-001 and 0.4-002"*, which also touch `main` directly and which the audit did not examine.

**Why it cannot wait for 1.2.** 1.2 is the validator, and it will be written against whatever
`main` says the schema is. If engine code keeps landing on `main` inside spec commits, the
validator is built against an unaudited target and the Phase 1 gate stops meaning anything.

**1.1-003** is closed by the audit entry itself and needs nothing from a builder. The auditor
struck 0.4-003 from the 0.4 record in the same pass.

---

## Opening instruction for the REWORK BUILDER

Paste this. Do not paraphrase it.

```
You are the REWORK BUILDER for module 1.1 of the MIS Simulation.
The module PASSED on substance. You are closing one Data finding. That is the
whole job — do not start 1.2, and do not touch the lineage question.

REPO: /home/ubuntu/projects/mis-sim   (origin: github.com/donharper11/mis-sim)
Work on branch build/1.1-casepack, pushed at a27e6cc. Never push to main.

READ FIRST, IN FULL:
  1. ~/projects/mis-sim/GOVERNANCE.md
  2. ~/projects/mis-sim/QUALITY_PROTOCOL.md
  3. ~/projects/mis-sim/CONTRACTS.md
  4. handoffs/1.1-casepack-schema/spec.md
  5. findings/1.1-2026-07-27-audit.md    — finding 1.1-002 is your work list

Treat the finding as a claim carrying its proof. Re-run the proof before acting.
An auditor on this project has filed a wrong finding before and withdrawn it
(1.1-003) — you are entitled to check.

GATE — CHECK BEFORE EDITING pack.yaml:
  1.1-002 needs a decision the auditor did not make: which round-3 capital figure
  is authoritative. Confirm the spec or an author note now states it.
  If it does not: STOP AND REPORT. Do not choose a value, and do not "make the
  arithmetic work" by adjusting whichever number is easier (GOVERNANCE §4.4).

YOUR SCOPE — one finding:
  1.1-002  backend/packs/riverside_grocery/pack.yaml gives round 3 two capital
           remainders: 44000 authored at :22, and 46000 at :84 which equals
           220000 - 174000. Same round, same capital_available. Remaining rises
           after committing 174000, which is impossible.
           Give the fact ONE home. Prefer elimination over reconciliation
           (SPEC_PROTOCOL §3): derive the dependent figure rather than authoring
           it twice. If the model cannot express that, report why.

DO NOT:
  - touch anything on main, or revert/rewrite 621b8d2. Not your call.
  - start 1.2, or extend the schema, the loader, or checks.py beyond this fix.
  - fix the mockups. The same contradiction sits in review.html as 0.4-002; it
    should be fixed once, here, and the mockup spec then follows the pack.
  - edit findings/1.1-2026-07-27-audit.md. Report disagreement instead.

BEFORE CLAIMING DONE — verify state, not exit codes (QUALITY_PROTOCOL §1):
  1. Paste the round-3 capital block of pack.yaml before and after.
  2. PYTHONPATH=backend python3 -m app.casepack.seed riverside_grocery
     The pinned-figure line must still print, and its capital figures must now
     agree with each other. Paste the whole line.
  3. Re-run I3-I8 via handoffs/1.1-casepack-schema/verify.md and paste the output.
     A schema or pack edit can break any of them.
  4. Re-run I5 specifically: all four strategies must still sum to 1.000.
  5. Append to dod.md under "Rework — 1.1-002". Do not overwrite the Phase 1
     report.
  6. Push, then verify by ref AND by tree: git ls-remote origin build/1.1-casepack
     against git rev-parse HEAD, and git ls-tree for the changed file.

Report every stop. A reported blocker costs an hour; a chosen number costs a
casepack nobody can reconcile.

This branch returns to a FRESH AUDITOR before merge — not to me, and not to you.
```

---

## Why the gate is shaped this way

The tempting failure here is small and expensive: a builder sees `220000 − 174000 = 46000`,
concludes `44000` is a typo, changes it, and the arithmetic closes. That may even be right —
but it decides, silently, that the strip figure rather than the derived one was wrong, in a
pack that six later modules read as ground truth. `GOVERNANCE.md §4.4` exists for exactly this
shape of "obvious".

The instruction also tells the builder it may check the auditor. That is not politeness:
`1.1-003` in the same findings file is an auditor error carried across three audits, and a
builder that had queried the pack would have caught it sooner than the auditor did.
