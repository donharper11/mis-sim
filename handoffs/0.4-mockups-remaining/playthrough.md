# 0.4 — Review Checklist

**Authored by:** Claude · **Date:** 2026-07-27 · **Before any code:** yes
**Spec:** `spec.md` in this folder

> **Two audits, not one** — `handoffs/README.md` R3.
>
> **AUDIT A** — invariants, scope, figures, states, contracts. Context is an asset.
> **AUDIT B** — Part B only, run by an agent that has **not read the spec**, given the
> table below and the mockups and nothing else. 0.3's auditor is disqualified for these
> seven, having authored findings against six of them.

---

## Setup

```
Open each file from the filesystem — file:///…/mockups/<name>.html
Disconnect the network first. Anything that fails to render is a finding (I6, I12).
```

---

## Part A — inherited grammar *(Audit A)*

The seven must be indistinguishable from 0.3's six in construction.

| # | Check | EXPECT |
|---|---|---|
| A1 | Sidebar, title row, capital strip | byte-comparable to `mockups/components.html` |
| A2 | Every file states its round | present in all eleven |
| A3 | Badge scale | `CONTRACTS.md` — one label, one colour, four distinct (I14) |
| A4 | Selected state wherever a choice is offered | Strategy options · Services tiers · Challenges rationale tags (I15) |
| A5 | Rows that open a detail view | Security · Services vendor table · Challenges inbox (I16) |
| A6 | 0.3's six mockups | **unchanged** — `git diff main -- mockups/platform.html …` empty |
| A7 | No new visual pattern introduced | any novel card, panel or control is a finding |

---

## Part B — the naïve-reader path *(Audit B — fresh agent, no spec)*

Answer from the screen alone. Do not open the spec, the copy list, or prior findings.

| # | Screen | Question | EXPECT |
|---|---|---|---|
| B1 | Dashboard | How is this business doing? | answerable in under 15 seconds |
| B2 | Dashboard | **What needs attention first?** | one thing dominates; not a tie between eight panels |
| B3 | Dashboard | **Why is the warehouse underperforming?** | traceable to a decision — training, process, communication — without inference |
| B4 | Dashboard | Which unit is in the worst shape? | it is the first one listed |
| B5 | Strategy | What is this business competing on, and what does that cost me? | both answerable |
| B6 | Strategy | Could I change it? | possible, and visibly expensive |
| B7 | Security | **What are we missing?** | gaps as prominent as what exists |
| B8 | Security | What would go wrong because of a gap? | stated in business terms, not technical ones |
| B9 | Services | Who fixes it when it breaks? | the current tier is obvious |
| B10 | People | **Do we have enough people?** | "over-committed" is unmissable |
| B11 | People | What does that cost us? | consequences stated, not implied |
| B12 | Challenges | What is being asked of me? | sender, ask and deadline all clear |
| B13 | Challenges | What are my options? | three, with a required reason |
| B14 | Review | **What am I committing to?** | totals legible in one pass |
| B15 | Review | **What have I missed?** | the mirror is visible and reads as advice, not error |
| B16 | Review | Could I lock anyway? | **yes — warnings never block** |
| B17 | all | Is this one product with 0.3's six? | shell, strip, tables, type scale all consistent |
| B18 | any decision screen | Is there a score anywhere outside Dashboard? | **none** |

Any "no" on B1–B15 or B17, or any "yes" on B18, is a **UX finding with a screenshot**.
B16 answering "no" is a finding — the mirror informs, it does not gate.

---

## Part C — states and viewports *(Audit A)*

| # | Check | EXPECT |
|---|---|---|
| C1 | Eleven files, one state each | `grep -c "State:"` → zero everywhere (I8) |
| C2 | `dashboard-empty` | round 1, no results, no invented figures |
| C3 | `strategy-unlocked` | four options, **none selected** |
| C4 | `challenges-item` | one item open, three responses, reason required |
| C5 | `review-locked` | banner present, inputs disabled, mirror still readable |
| C6–C8 | 1440 · 1280 · 1024 | no overflow, no clipping, no rounded corners |

---

## Part D — invariants, run independently *(Audit A)*

Do not trust the builder's paste. Run each. All use `git ls-files` (R4).

```
I1 I3 I4 I5 I6 I7 I8 I9 I12 I13 I14 I15 I16 I17 I18 I19
```

I17, I18, I19 are the new ones: the Review mirror is present and non-blocking; the unit
chain is ordered worst first; Security gaps carry full-row weight.

---

## Part E — scope *(Audit A)*

| # | Check | EXPECT |
|---|---|---|
| E1 | `git diff --name-only main..HEAD` | only `mockups/*`, `docs/*`, this folder's `dod.md`, `screenshots/0.4/*`, `.gitignore` |
| E2 | Debrief | **not built** — deferred by spec §1. Building it is a finding |
| E3 | 0.3's cosmetic findings | **not fixed here** — they belong to 0.5 |
| E4 | `dod.md` | every row filled; each `N-A` carries a reason |

---

## Result

```
Audit A — run date:            Auditor:
Audit B — run date:            Auditor:   (confirm: has NOT read spec.md)
Findings:  findings/0.4-<YYYY-MM-DD>-audit-a.md
           findings/0.4-<YYYY-MM-DD>-audit-b.md
Verdict:  PASS / FAIL
```

Findings carry their proof (`SPEC_PROTOCOL.md §2.1`). A single blocking finding = FAIL.
**0.4 is not done until both audits return.**
