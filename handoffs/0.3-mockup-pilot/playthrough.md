# 0.3 — Review Checklist

**Authored by:** Claude (design session) · **Date:** 2026-07-26 · **Before any code:** yes
**Spec:** `spec.md` in this folder
**Executed by:** AUDITOR — **fresh agent mandatory** (`GOVERNANCE.md §6.1`; this module
has a visual surface)

> **Adaptation.** Static mockups have no browser workflow, so this replaces the
> playthrough with a structured review. Part B — normally the negligent path — becomes
> the **naïve-reader path**: can someone who has never seen this project read these
> screens correctly? That is the failure these mockups actually risk.

---

## Setup

```
Open each file directly from the filesystem — file:///…/mockups/<name>.html
NOT through a dev server. If it needs a server, that is a finding (spec §3 decision 2).
Disconnect the network before opening. Anything that fails to render is a finding (I5).
```

---

## Part A — the token map (check first; it underpins every screen)

| # | Check | EXPECT |
|---|---|---|
| A1 | `theme.css` has two clearly separated blocks | primitives, then semantic roles |
| A2 | Every role in spec §5.1's list is declared | exactly once each, none missing |
| A3 | For each `--<role>: var(--x)`, is `--x` a primitive? | yes for all — no role→role chains (I2) |
| A4 | Deprecation table in `dod.md` | accounts for **all 89** original tokens. A token that vanished without a row is a finding |
| A5 | `--accent-*` and `--status-*` | disjoint. An accent reused as a status is a finding |
| A6 | `--chart-*` | disjoint from both accent and status |
| A7 | `CONTRACTS.md` entry | present, in the file's existing format, states the one-step rule |
| A8 | `grep -rn -- "--[a-z-]*:" frontend/src mockups/ \| grep -v theme.css` | zero hits (I7) |

**If Part A fails, keep going but flag it loudly.** The mockups are built on the map, so a
broken map shows up as broken screens — record both. *(v2.2: this is no longer a
separate build gate; the map and the mockups are reviewed together.)*

---

## Part B — the naive-reader path *(v3)*

Read each screen as someone who has never seen this project. Answer from the screen alone,
without consulting the spec, then check. **These four questions are what v2 could not
answer.**

| # | Screen | Question answered from the screen alone | EXPECT |
|---|---|---|---|
| B1 | Components | **What do we own?** | a table, answerable in under 10 seconds |
| B2 | Components | **How would I add one?** | one obvious action, no hunting |
| B3 | Components | **Where do I change a system's settings?** | clicking a row is discoverable |
| B4 | Rollout | **Which units have actually adopted anything?** | the neglected row is visually obvious |
| B5 | Platform | **What runs where?** | the two panels dominate |
| B6 | Platform | **What are we missing?** | "Not provisioned" reads as an absence, not a blank |
| B7 | Platform | **Can we add anything more?** | "No headroom" is unmissable |
| B8 | Wizard | **What does each option really cost?** | all warnings visible before "Add to plan" |
| B9 | Wizard | Could I skip saying what it's for, or who it's for? | **no — steps 3 and 4 are mandatory** |
| B10 | Rollout | Could I train everyone at once? | **no — every control names one deployment** |
| B11 | all three | Is this one product? | shared shell, strip, table grammar, type scale |
| B12 | any | Is there a score anywhere on these pages? | **none — scores live on Dashboard and Debrief** |

Any "no" on B1–B8 or B11, or any "yes" on B9, B10, B12, is a **UX finding with a
screenshot**, not a note.

## Part C — language

| # | Check | EXPECT |
|---|---|---|
| C1 | `grep -niE "capability_key\|instance_id\|articulation\|fit.multiplier\|casepack\|SPOF\b" mockups/*.html` | zero (I3) |
| C2 | Read every visible string against spec §5.6 | no unlisted strings; no lorem ipsum (I6) |
| C3 | Capacity expressed how? | percentage. **Cores or terabytes anywhere is a finding** (`GOVERNANCE.md §2.1`) |
| C4 | Recovery/backup language | plain English — "2 days to recover", never RTO/RPO |
| C5 | Apply the standing filter to every label | *what does it cost, who does it affect, what happens if it fails* — a label serving none of these is a finding |

---

## Part D — content accuracy

| # | Check | EXPECT |
|---|---|---|
| D1 | Every figure against spec §5.4 | exact match. An invented number is a finding |
| D2 | 0.75 × 0.51 × 0.65 | ≈ 0.25 — the arithmetic shown must actually work |
| D3 | Every displayed metric | traceable to `design/02-traceability-matrix.md`. A metric with no engine source is a finding |
| D4 | Casepack-supplied labels | visibly marked with a legend (spec §5.5) |
| D5 | Riverside references | content only, never structural (I4) |

---

## Part E — states and viewports

| # | Check | EXPECT |
|---|---|---|
| E1 | Situation states | ready · round-1-empty · locked — all three, labelled |
| E2 | Platform states | ready · hybrid banner · unprovisioned · 100% capacity |
| E3 | Applications states | ready · empty slot · owner unassigned · wizard step 3 |
| E4 | 1440 | no overlap, no clipping, no horizontal scroll |
| E5 | 1280 | same |
| E6 | 1024 | same |
| E7 | Zero-radius throughout | BECSR is flat. A rounded corner is a finding |
| E8 | 9 screenshots in `screenshots/0.3/` | 3 screens × 3 viewports |

---

## Part F — scope

| # | Check | EXPECT |
|---|---|---|
| F1 | `git diff --name-only main..<branch>` | only `theme.css`, `mockups/*`, `CONTRACTS.md`, `handoffs/0.3-mockup-pilot/dod.md`, `screenshots/0.3/*` |
| F2 | Mockups 4–10 | **not built.** Building ahead is a finding — the review gate exists for a reason |
| F3 | React components | none |
| F4 | `dod.md` | every row filled; each `N-A` carries a reason |
| F5 | O1, O2, O3 | each resolved with rationale recorded |

---

## Result

```
Run date:            Auditor:
Part A:  PASS / FAIL      (record; no longer blocks reviewing the screens)
Parts B–F passed:    /
Findings filed:  findings/0.3-<YYYY-MM-DD>-audit.md
Verdict:  PASS / FAIL
```

Findings carry their proof per `SPEC_PROTOCOL.md §2.1` — a grep with output, a
screenshot, or a `file:line`. A single blocking finding = FAIL.

**Then the human review gate.** Even on PASS, these three screens go to the user before
0.4 begins. They set the grammar the other seven copy, and that judgement is not the
auditor's to make.
