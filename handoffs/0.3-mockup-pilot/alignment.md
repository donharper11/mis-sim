# 0.3 — Alignment

**Date:** 2026-07-27 · **Author:** Claude (spec author)
**Purpose:** reconcile three things that have drifted apart — what the builder built, what
the auditor found, and what the spec now says. One canonical state, one handoff.

> **How we got out of sync.** The builder built against spec v2.2 and did it correctly.
> The auditor audited that build, also correctly. Between the audit and its filing, I
> pushed **v3**, which respecs roughly half of what was built. Nobody did anything wrong;
> the spec moved under them. This document states what survives, what is discarded, and
> what each open finding becomes.

---

## 1. Verified state

Checked against `origin/build/0.3-mockup-pilot` and `origin/main`, 2026-07-27.

| | Built | Spec'd by v3 | Disposition |
|---|---|---|---|
| Token map — 38 `--p-` primitives, 115 roles | ✅ `76d5e3a` | Step 1, unchanged | **KEEP** |
| Consumer remap + throw-on-empty guard | ✅ | Step 1, unchanged | **KEEP** |
| 5 WOFF2 + `LICENSE.txt`, CDN removed | ✅ `d492403` | Step 1b, unchanged | **KEEP** |
| `situation.html` | ✅ built | not in v3 | **DISCARD** |
| `applications.html` | ✅ built | not in v3 | **DISCARD** |
| `platform.html` | ✅ built | v3 §5.2, restructured | **REBUILD** |
| `components.html` + detail + wizard | — | v3 §5.3–5.4 | **BUILD** |
| `rollout.html` + detail + locked | — | v3 §5.5 | **BUILD** |

**Steps 1 and 1b are done and correct.** Nothing in this alignment touches them.

## 2. The scoping decision you asked for

**`situation.html` and `applications.html` are discarded, not kept as superseded.**

Reasons: v3's **I8** (one state per file) and **I9** (no scores on decision pages) both
fire on them, so keeping them means keeping two files that fail the current spec's
invariants. And they are the acceptance criterion for nothing — Dashboard is out of the
pilot, and Components replaces Applications.

Their *screenshots* stay in `screenshots/0.3/` as the record of why the respec happened.

Consequence: **`0.3-013` (the badge scale) transfers to the new screens.** It was found on
`situation.html`, but it is a defect in the *scale*, not the file — and the scale is used
by `components.html` and `rollout.html`, and becomes 0.5's `StatusBadge` contract.

---

## 3. Findings disposition — all of them, explicitly

### Carried forward and fixed in v3.1

**`0.3-013` — the badge scale contradicts itself.** *(The finding that outlives everything.)*
`Partly done` and `Complete` both render `pill ok`. A capability at 25% realised, explicitly
throttled, carries the same green as one at 5/5. A student scanning colour cannot
distinguish them.

**Fix:** the badge scale becomes a **contract**, not a per-screen choice. Four values, four
distinct role tokens, defined once in `CONTRACTS.md` and referenced by v3.1 §5.7. New
invariant **I14** checks conformance. This matters beyond the mockups: they are the
acceptance criterion for 0.5's `StatusBadge`, so a contradictory scale here becomes a
contradictory component contract there.

**`0.3-020` — the renumber cost two guards.** Correct, and it is my regression. v2.1's
`I9` (no third-party font request) and `I10` (both faces + licence shipped) were reused in
v3 for unrelated invariants. Nothing standing prevented a Google Fonts link reappearing —
the substance of an entire rework cycle — and nothing checked that the five WOFF2 files and
`LICENSE.txt` stay shipped. **The SIL Open Font Licence requires the licence to accompany
the fonts**, so this was a licence-compliance hole, not just a tidiness one.

**Fix:** restored as **I12** and **I13** in v3.1, with a standing note that renumbering an
invariant requires checking what the old number guarded.

**I9 grep scoping** *(builder's recorded deviation — accepted).* The command scanned
`node_modules` and false-matched `existingStaticNonFields` in `@babel/helpers` under
case-insensitive `gstatic`. The builder was right, the auditor confirmed it and corrected
their own initial read. **Fix:** all repo-wide greps in v3.1 run over **tracked files
only**.

**Programme total $400,000 vs $220,000.** Both are correct — the casepack budget curve is
`[400000, 260000, 220000, …]`, so round 1 is 400k and round 3 is 220k. They read as a
contradiction only because v2 stacked both states on one page with no round label. v3's
one-state-per-file resolves it; v3.1 additionally requires **every file to state its
round** in the shell.

**Third deployment mode had no copy.** §5.6 assigned two warnings to SaaS; the builder
gave one to cloud subscription because the spec had no copy for it. That gap got filled
rather than reported — a legitimate finding against **me**, since an unspecified string is
exactly what `GOVERNANCE §4.4` says to stop on. **Fix:** v3.1 §5.7 gives all three modes
their own copy, and the cloud option now has none by design, stated explicitly.

### Moot as written, causes re-tested in v3.1

Five findings were against screens that no longer exist. The auditor recorded their
**causes** rather than deleting them, which was right — `0.3-014` was "the wizard
enumerates options that need copy," and v3's six-step wizard enumerates more options than
v2 did. So the cause is live even though the finding isn't.

| Was | Cause | Re-tested in v3.1 by |
|---|---|---|
| `0.3-014` | enumerated options with no authored copy | §5.7 covers all six wizard steps; **I5** |
| "Weighted by your strategy" as a subtitle asserting all activities are weighted | a marker used as a heading | §5.7 makes it a per-item marker only |
| weighted activities were the only ones with no coverage badge | inconsistent badge application | **I14** requires a badge on every status-bearing item |
| stacked states | v2 decision O2 | v3 **I8**, one state per file |
| scores on a decision page | v2 §5.3 | v3 **I9** |

### Not a finding, a process fix

**Part B was not run, and the auditor was right not to run it.** They had read §5.6's copy
list and §5.4's figures four times; they would have seen what they knew was meant to be
there, which is precisely what Part B detects.

**This is now a standing rule** — see §5.

---

## 4. What I got wrong, recorded so it stops recurring

1. **Pushed v3 while a build and audit were in flight.** The spec moved under two agents
   mid-cycle. A spec change during an open build cycle must be announced to the branch, not
   just merged to `main`.
2. **Reused invariant numbers.** I9 and I10 meant something in v2.1 and something else in
   v3. Renumbering silently dropped two guards.
3. **Specced two warnings for one option and none for another**, then relied on a builder
   to notice.
4. **Specced v2 as a content inventory**, which is the root of the respec. Already recorded
   in v3 §11.

## 5. Standing rules added by this alignment

**R1 — A spec change during an open build cycle is announced on the branch.** Merging to
`main` does not reach a builder. The change lands on the branch with a one-line note in
`dod.md` saying which steps it invalidates.

**R2 — Renumbering an invariant requires checking what the old number guarded.** State in
the changelog which guards moved where, or that none did.

**R3 — Part B is run by an agent that has not read the spec.** It is dispatched with the
playthrough's Part B table and the mockups, and nothing else. An auditor who has read the
copy list is disqualified from Part B and says so rather than running it anyway.

**R4 — Repo-wide greps run over tracked files.** `git ls-files | xargs grep …`, never
`grep -r` over a tree containing `node_modules`.

---

## 6. The single handoff

One builder pass, against **spec v3.1**, on `build/0.3-mockup-pilot`:

```
KEEP      theme.css · main.jsx · DevTokens.jsx · fonts/     (Steps 1, 1b — done)
DELETE    mockups/situation.html · mockups/applications.html
REBUILD   mockups/platform.html            per v3 §5.2
BUILD     components.html · -detail · -wizard
          rollout.html · -detail · -locked
          platform-empty.html
FIX       badge scale per CONTRACTS.md     (0.3-013)
RESTORE   I12, I13 font guards             (0.3-020)
```

Then **two** separate audits, not one:

```
AUDIT A   the same auditor. Invariants, scope, figures, states, licence.
          They have context and it is an asset here.
AUDIT B   a fresh agent, given ONLY the playthrough's Part B table and the
          mockups. No spec, no copy list, no findings. Twelve questions,
          answered from the screen.
```

`0.3` is not done until both return.

---

# Addendum — 2026-07-27, after audit `038f54e`

**Verdict: PASS, 0 blocking.** Part B ran blind on six respec'd screens, and that window is
now permanently shut — nobody who has read v3.1 can run it again.

## Carried into v3.2 because they propagate to the next seven screens

| Finding | Why it could not wait | Fixed by |
|---|---|---|
| **B9** — wizard showed steps 1–4 at once, live commit, no selected state; a component could be added with no purpose and no unit | **No selected state exists anywhere in the design.** Seven more screens and a component library would have copied the absence | `CONTRACTS.md` *Selected state* · **I15** · **I11 rewritten** |
| **B3** — nothing signalled a Components row opens anything | Same — every future table inherits it | `CONTRACTS.md` *Row opens detail* · **I16** |
| **0.3-021** — §5.4's structural description rendered as tab content | §5.4 is written the same way for every future detail screen | §5.4 marked **STRUCTURAL, NOT COPY** · I4 now greps `level of detail` |

**I11 is the instructive one.** It read *"no skip/later affordance"* and passed, while the
requirement it existed to protect failed completely — the wizard never asked at all. An
invariant phrased as *the absence of a control* is satisfiable by a design that has no
controls. Rewritten as a positive requirement.

## Mine, fixed in v3.2

- **`0.3-018`** — the label was wrong, not the numbers. `$220,000` and `$400,000` are
  rounds 3 and 1 of the budget curve, but *"Capital remaining $X of $Y"* with Y changing
  each round reads as two programme totals for one company. Now **"Capital this round —
  $44,000 remaining of $220,000."**
- **`platform-empty`** showed *"Round 1 of 6"* beside *"locked in round 2."* Round 1 now
  reads **"Strategy not yet declared."**

## Recorded, not fixed — carried to 0.4 / 0.5

Single-screen and cosmetic; they do not shape what comes next.

```
.button lacks display:inline-flex; width:fit-content   → [upgrade][retire] as one slab
.close stretches to full flex height                   → reads as a broken box
~440px dead white in the Cloud panel
split-rule options run together as prose
```

The first two belong to **0.5** — they are `Button` and a dismiss control, which become
real components there rather than mockup CSS.

## What B4 confirmed

> Store spreadsheets · 140 people · — trained · process unchanged · no communication ·
> 48% adoption

That row teaches complementary assets with no theory attached. It is the clearest evidence
so far that the Rollout table is the right structure, and it is worth protecting when 0.4
and 0.5 restyle it.
