# 1.7 — Calibration Harness · Build Spec

**Authored under** `SPEC_PROTOCOL.md` v1.1 · **Author:** Claude · **Date:** 2026-07-26
**Phase:** 1 · **Depends on:** 1.1–1.6 · **Blocks:** the Phase 1 gate, and therefore Phase 3

> **The highest-value packet in the project.** Every number in this simulation is currently
> a guess. This is where we find out whether the model produces genuine decisions or a
> dominant strategy — from a script, before a single screen exists, instead of from thirty
> students in week 9.

---

## 0. Spec Basis

**Read in full:** `design/05-implementation-plan.md` §5 (Phase 1 gate) ·
`handoffs/1.4-scoring-engine/spec.md`, `1.5`, `1.6` · `design/02-traceability-matrix.md` ·
`design/03-scoring-frame-options.md` (BSC output).

**Extraction sufficiency:** covered.

---

## 1. Purpose and scope

**In scope:** scripted team archetypes that play a full pack headlessly · a runner over
(pack × archetype × rounds) · output showing score trajectories, term decomposition, and
factor sensitivity · **dominance detection** · a report an instructor can read.

**Out of scope:** tuning the numbers (the harness *reveals*; changes go back to 1.3 or the
pack) · UI · any browser · the full-game *playthrough* (Phase 3 — this proves the maths,
that proves a student can reach it).

---

## 2. Project-specific statements

**Scoring factors touched:** exercises all of them; owns none.
**Casepack keys read:** all. **Casepack-identity branching:** none — must run any pack
unchanged, which is a preview of the Phase 6 gate. I1.
**Instance scoping:** creates throwaway instances, one per run, torn down after. I4.
**Business-language check:** output is for an instructor. Factor names resolve through
`labels.yaml`; raw keys in a report are a finding. I3.

---

## 3. Settled decisions

1. **Four archetypes minimum** (§5.1). More may be added; these four are mandatory.
2. **Deterministic.** Same pack + same archetype → identical trajectory, every run.
   Guaranteed by 1.4/1.5 purity.
3. **The harness never edits the pack.** It reports; humans decide.
4. **Runs headless in CI-less local dev.** One command, no services beyond the DB.
5. **Dominance is defined numerically** (§5.3), not by eyeballing curves.

---

## 4. Open decisions

| # | Question | Criteria | Reporting |
|---|---|---|---|
| **O1** | Should archetypes be scripted in Python or authored as YAML decision sheets? | **Default: YAML sheets per round**, loaded like a student's decisions. Python scripts drift from what the API actually accepts; YAML exercises the same path a real team will | Record |
| **O2** | How many rounds of sensitivity sweep? | **Default: full 6, single-factor, one factor at a time.** A full factorial is combinatorially silly at this stage | Record |
| **O3** | Should the harness assert, or only report? | **Default: both.** Report always; assert on the three gate conditions in §5.3 so it can fail a build | Record |

---

## 5. Design

### 5.1 The mandatory archetypes

| Key | Behaviour | What it must demonstrate |
|---|---|---|
| `do_nothing` | declares a strategy, then spends nothing | the floor. Debt accrues, EOL bites, signals fire unanswered |
| `all_tech_no_org` | buys the best of everything, funds zero training, assigns no owners | **the sim's central lesson.** High Tech, collapsed Org, low realised value |
| `balanced` | coherent strategy, proportionate Tech/Org/Mgmt, acts on signals | the intended good play. Should score best |
| `overspender` | funds everything generously, ignores strategy alignment | punished by cost efficiency and portfolio discipline, not by outcomes |

Two more worth adding once the four run: `signal_chaser` (perfect responsiveness, panic
spending — must **not** win, or responsiveness is a dominant lever) and `strategy_drifter`
(declares cost leadership, spends on differentiation).

### 5.2 Output

```
$ calibrate packs/riverside_grocery

  riverside_grocery 1.0.0 · 6 rounds · 4 archetypes

  REALISED VALUE (firm, strategy-weighted)
             R1     R2     R3     R4     R5     R6
  balanced   0.31   0.44   0.52   0.58   0.63   0.67
  overspend  0.29   0.41   0.46   0.47   0.49   0.51
  all_tech   0.22   0.28   0.24   0.19   0.17   0.16
  do_nothing 0.28   0.24   0.19   0.13   0.09   0.06

  TERM DECOMPOSITION at R6
             tech   org    mgmt   realised
  balanced   0.81   0.79   0.76   0.486
  all_tech   0.88   0.21   0.44   0.081    ← the lesson, in one row

  GATE CHECKS
  ✓ no dominant strategy         spread 0.11 across 4 declared strategies
  ✓ balanced beats all_tech      0.67 vs 0.16
  ✓ all three terms bind         removing any one changes rank order
  ✗ signal_chaser ranks 2nd      responsiveness may be over-weighted

  3 of 4 gate checks passed · exit 1
```

### 5.3 Gate conditions — numeric, not eyeballed

```
G1  NO DOMINANT STRATEGY
    Play `balanced` under each of the 4 declared strategies.
    max(final) − min(final) ≤ 0.15.
    A wider spread means one strategy is simply better, and the
    declaration is decoration.

G2  COMPLEMENTARY ASSETS BIND
    all_tech_no_org final < 0.5 × balanced final.
    If not, the Org term is not biting and the sim's whole thesis fails.

G3  ALL THREE TERMS LOAD-BEARING
    Pin each term to 1.0 in turn and re-rank.
    Each pinning must change the rank order.
    A term that changes nothing is decoration and should be cut.

G4  NO SINGLE DOMINANT LEVER
    Single-factor sensitivity: vary each sub-factor ±20%, hold the rest.
    No sub-factor may move the final score by more than 0.10.
    A larger swing means the sim is really about that one thing.
```

**These four are the Phase 1 gate.** Failing any is not a harness bug — it is a finding
against the model, and it goes back to 1.3 (content) or 1.4 (weights).

### 5.4 Sensitivity report

Per sub-factor: swing, rank-order changes caused, and whether it is within G4. This is what
tells you which of the ~30 guessed numbers actually matter — most will not, and knowing
which do is where calibration effort belongs.

---

## 6. Invariants

| # | Invariant | Check | Expected |
|---|---|---|---|
| I1 | Runs any pack unchanged | run against Riverside and a minimal synthetic pack | both complete |
| I2 | Deterministic | same pack + archetype 10× → one hash | 1 |
| I3 | No raw keys in the report | `calibrate … \| grep -E "[a-z]+_[a-z]+_[a-z]+"` | zero, or only in a `--debug` section |
| I4 | Instances torn down | count instances before and after | equal |
| I5 | Never mutates the pack | `md5sum` pack files before/after | identical |
| I6 | Gate conditions computed, not asserted by hand | `grep -n "0.15\|0.5 \*\|0.10" backend/app/calibrate/gates.py` | all four present as code |

---

## 7. Pre-Flight Verification Register

| # | Claim | Tag | Check | Expected |
|---|---|---|---|---|
| 1 | 1.6 merged; six-round run works | `[V]` | `grep -n "def advance" backend/app/round/runner.py` | present |
| 2 | Engine deterministic | `[V]` | run 1.4 twice on one fixture, diff | identical |
| 3 | Riverside validates clean | `[V]` | `validate_casepack packs/riverside_grocery` | exit 0 |
| 4 | Riverside has all 4 strategies with weights | `[V]` | `grep -c "^- key:" packs/riverside_grocery/strategies.yaml` | 4 |
| 5 | `RoundResult` carries the decomposition | `[V]` | `grep -n "terms\|throttle" backend/app/round/models.py` | present |
| 6 | Riverside pack has no `TODO: calibrate` left, or a list of them | `[A]` | `grep -rn "TODO: calibrate" packs/` | **if any remain, the harness runs on stubs — report the list before interpreting results** |

Row 6 is the one to take seriously. Calibrating against placeholder values produces
confident nonsense.

---

## 8. Build phases

1. **Archetype loader** — YAML decision sheets per round (O1). *Verify:* `balanced` loads
   and produces six valid sheets.
2. **Runner** over (pack × archetype). *Verify:* four archetypes × six rounds complete;
   I2, I4, I5.
3. **Trajectory + decomposition report.** *Verify:* output matches the §5.2 shape; I3.
4. **Gate checks G1–G4 as code.** *Verify:* I6; each fires against a deliberately broken
   pack (e.g. zero out the Org weights → G2 must fail).
5. **Sensitivity sweep** (O2). *Verify:* every sub-factor reported with its swing.
6. **Run it for real.** *Verify:* the actual gate result, whatever it is, in `dod.md`.

Phase 6 is not "make it pass." It is "run it and report the truth." A failing gate here is
the harness doing its job.

---

## 9. Definition of Done

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–6, esp. row 6 | | |
| Phases 1–6 verified | | |
| I1–I6 | | |
| O1, O2, O3 recorded | | |
| Four mandatory archetypes implemented | | |
| G1–G4 computed as code and **run** | | |
| Sensitivity report for every sub-factor | | |
| **Gate outcome reported honestly, pass or fail** | | |
| Any remaining `TODO: calibrate` listed | | |
| Browser / auth canaries | | **N-A** — headless |

---

## 10. What happens next

**If the gate passes:** Phase 1 is complete and Phase 3 may begin.

**If it fails:** it goes back — G1 or G4 to 1.4's weights, G2 to 1.3's content or 1.4's
Org sub-factors, G3 to whether a term should exist at all. **Do not adjust numbers to make
the gate pass without understanding why it failed.** A tuned-to-pass model is worse than a
failing one, because it looks finished.
