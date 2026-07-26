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

## Part A — the token map (Phase 1 gate; check before looking at any screen)

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

**If Part A fails, stop.** The mockups are built on it; reviewing them first wastes the pass.

---

## Part B — the naïve-reader path

Read each screen as someone who has never seen this project. Do not consult the spec while
doing this — answer from the screen alone, then check.

| # | Screen | Question answered from the screen alone | EXPECT |
|---|---|---|---|
| B1 | Situation | What kind of business is this, and how is it doing? | answerable in under 30 seconds |
| B2 | Situation | Order Fulfilment is at 25%. **Why?** | "Organisation" is findable without hunting — the throttle is stated, not inferred |
| B3 | Situation | What should I worry about first? | the critical signal is visually dominant over the two warnings |
| B4 | Situation | Is the budget healthy? | run-rate trend readable as *rising*, not just three numbers |
| B5 | Platform | Where does our stuff run? | the two-panel split is immediately legible |
| B6 | Platform | What do we not have? | "Not provisioned" reads as an **absence**, not an omission or a blank |
| B7 | Platform | Can we add another system? | "No headroom" is unmissable |
| B8 | Applications | Which parts of the business are we good at? | value chain coverage scannable in one pass |
| B9 | Applications | Where should I invest, given my strategy? | strategy-weighted activities visually distinct |
| B10 | Applications | What is missing from Order Fulfilment? | the empty slot reads as empty, not as small |
| B11 | Applications | What does the SaaS option really cost? | both warnings visible **before** "Add to plan" |
| B12 | all three | Is this one product? | shared header, budget strip, card grammar, type scale |

Any "no" is a **UX finding with a screenshot**, not a note.

---

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
Part A:  PASS / FAIL      (if FAIL, stop — do not review screens)
Parts B–F passed:    /
Findings filed:  findings/0.3-<YYYY-MM-DD>-audit.md
Verdict:  PASS / FAIL
```

Findings carry their proof per `SPEC_PROTOCOL.md §2.1` — a grep with output, a
screenshot, or a `file:line`. A single blocking finding = FAIL.

**Then the human review gate.** Even on PASS, these three screens go to the user before
0.4 begins. They set the grammar the other seven copy, and that judgement is not the
auditor's to make.
