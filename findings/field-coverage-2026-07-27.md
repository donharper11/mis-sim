# Field Coverage Scan — mockups vs the traceability matrix

**Date:** 2026-07-27 · **Run by:** Claude (spec author) · **Method:** every factor in
`design/02-traceability-matrix.md` checked against all 19 tracked mockups
**Verdict:** 6 factors have no capture point. One of them is structural.

```
44 factors total
  18  derived — no student input needed, correctly absent from the UI
  26  require a capture point
      19  present
       1  thin
       6  ABSENT
```

---

## The structural one: there is no Governance screen

`grep -i governance` across all 19 mockups returns **one hit** — a line in `review.html`
reading *"Governance · 2 assignments · $0"*. The Review screen totals up governance
decisions that have **no screen to make them on**.

### How it happened

The original sidebar had `Platform · Applications · Organization · Governance · Challenges
· Review`. The restructure to `Strategy · Platform · Components · Rollout · Security ·
Services · People` dropped Governance, and I reflected that sidebar back without checking
it against the matrix. The matrix exists to catch exactly this and was not consulted.

**My error, and a process one:** a sidebar change is a change to which factors can be
captured. It needs the same check as a schema change.

### What it costs

```
MANAGEMENT QUALITY sub-factors

  governance coverage      HOMELESS   owner + sponsor per capability
  strategic alignment      derived    dot product of spend × weights
  portfolio discipline     derived    Herfindahl + RGT + maintenance floor
  signal responsiveness    derived    two timestamps
  follow-through           HOMELESS   continue / pause / kill in-flight
  stakeholder alignment    derived    preferences × realised value
```

**Two of six need student input. Both are homeless.** The other four are derived from
decisions made on other screens.

So a student **cannot currently do management** — it can only be inferred from what they
did elsewhere. Given that the whole sim rests on `Tech × Org × Mgmt`, and that Management
was specified as *the term you cannot buy*, having no screen where a student exercises it
is a hole in the model, not a missing page.

---

## All six absences

| # | Factor | Matrix says it lives on | Reality |
|---|---|---|---|
| **FC-1** | Governance coverage — owner + sponsor per capability | Governance | **no screen exists** |
| **FC-2** | Follow-through — continue / pause / kill in-flight | Governance | **no screen exists** |
| **FC-3** | Information policy — 6 switches | Policy | **no screen exists.** This is the entire Ch 4 ethics layer: consent, retention, access, logging, data egress, staff monitoring |
| **FC-4** | Additional capital request | Budget › request from CFO | no affordance anywhere |
| **FC-5** | TCO forecast accuracy | Purchase wizard step 6 checklist | `components-wizard.html` renders *"What will it cost"* but **not** *"What else do you expect to pay?"* — the checklist has no rendered form |
| **FC-6** | Over-forecast penalty | same checklist | same |
| *FC-7* | Rationale quality (±10%) | Challenges free-text | tags exist, no free-text box. Already open as **G2**, non-blocking |

**FC-5 and FC-6 share one control.** The TCO forecast was designed as the mechanism that
makes students confront that a subscription price is not the price — the checklist they
tick, then get wrong, then see reconciled in the debrief. It exists in copy and in the
schema and has never been drawn.

---

## What this changes

### Seed, not wire

None of these six can be "wired up" — **there is nothing to wire.** They need a screen
first. Distinguishing the two was the point of running this:

```
WIRE    a control exists, showing a hardcoded value → connect it to real data
        applies to the 19 present factors

BUILD   no control exists at all → a screen or control must be designed
        applies to FC-1 … FC-6
```

### Recommended disposition

**Restore Governance as a screen.** It carries FC-1, FC-2, FC-3 and plausibly FC-4. Its
absence is what makes Management uncapturable, and three of the six absences resolve with
one page.

Sidebar becomes:

```
Dashboard

DECISIONS
  Strategy · Platform · Components · Rollout
  Security · Services · People · Governance

Challenges · Review · Debrief
```

**FC-5/FC-6** belong in the Components wizard's step 6, which is specced but unrendered.
That is a mockup gap, not a design gap.

**FC-7** stays open as G2 — it is the only LLM-scored surface in the design and cutting it
remains defensible.

### Sequencing

This does **not** block 1.1. The casepack schema is content, and none of these six change
what a pack must say — they change where a student enters things.

It does block **Phase 3**, where these become real screens. Better found now.

---

## The 19 that are present

Confirmed to have a control, so their work is wiring rather than building: coverage
(roles, entities) · capacity (pool, application draw) · redundancy · integration · data
freshness · component currency · training · process fit · resistance · IT staffing ·
rationale tags · strategy declaration · strategy reopen · hosting placement · hybrid split
rule · capex · opex run-rate.

**One thin:** follow-through matched only `people.html`, on the word "retain" — a false
positive. It is genuinely FC-2.

---

## Method note

The scan is a keyword match over rendered text and will produce false positives where a
word appears for another reason — as it did on follow-through. Every ABSENT result was
confirmed by hand; the PRESENT results were not exhaustively verified beyond the file
match. A control that exists but captures the wrong thing would not be caught by this
method.
