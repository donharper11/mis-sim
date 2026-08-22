# 1.7 — Calibration Harness · Definition of Done (builder evidence)

**Build:** `build/1.7-calibration-harness` from `main` @ `f6bf8e4` · **Builder:** Claude · **Date:** 2026-08-22
**Tier:** Heavy. This is the INSTRUMENT only. It builds the measuring device and runs it once to
produce baseline curves. It does **not** calibrate the ~42 TODO values and does **not** rule the
calibration gate — the review gate is the user's (spec §5.4).

---

## Pre-flight verification register (spec §7)

| # | Claim | Result |
|---|---|---|
| 1 | 1.6 merged; six-round run works on the real runner | **PASS** — `advance` at `runner.py:282`; `--full` runs six rounds, opex ratchet `47000→53000→58300→62200→66000→70000` (run against SQLite: no Postgres in this sandbox, the documented `create_all` fallback) |
| 2 | Engine deterministic; 1.4 pin green at base | **PASS** — `test_engine_scoring.py` 10 passed, identical both runs |
| 3 | Riverside validates clean | **PASS** — `0 errors · 0 warnings · exit 0` |
| 4 | Riverside has all 4 strategies with weights | **PASS** — `4` |
| 5 | `RoundResult` carries the decomposition | **PASS** — payload carries `capabilities`, `scorecard`, `firm_score` |
| 6 | Pack `TODO: calibrate` list | **PASS** — **37 marker sites** (STOP tripwire clear: count matches; list printed live by the harness) |
| 7 | `firm_score` is strategy-weighted realised | **PASS** — `rollup.py:35` |
| 8 | Four BSC dims on the score record | **PASS** — `score.py:96-99` |
| 9 | `--full` seed builder is the archetype template | **PASS** — `run_full_game`/`_seed_round_estate`/`_decision_lines_for_round` present |
| 10 | **No `calibrate` entrypoint / no `gates.py`** (STOP tripwire) | **PASS** — both absent → NEW code; `gates.py` not built (the gate is human, §11) |

Row 6 and Row 10 (the two STOP tripwires) both cleared: 37 markers, no pre-existing `calibrate`
command, no `gates.py`. No spec/reality conflict; no STOP raised.

---

## Definition of Done (spec §9)

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–10, esp. 6 and 10 | ✅ | table above |
| Steps 1–6 verified | ✅ | four archetype builders + `app.calibrate` runner + curve/decomp/diagnostics/inventory report, run for real (below) |
| I1–I7 (each with planted-defect falsification) | ✅ | `tests/check_calibration_harness.py` (I1–I6) + `test_engine_scoring.py` (I7); falsifications shown below |
| O1, O2, O3 recorded | ✅ | O1 = Python seed builders (built); O2 = no sweep in v1 (not built); O3 = report-only (built) |
| Four mandatory archetypes as seed builders on the real runner | ✅ | `seeds/archetype_{do_nothing,all_tech_no_org,balanced,overspender}.py` → `RoundRunner.advance` |
| Curves = 4 BSC dims + realised, per archetype × 6 rounds, from `RoundResult` | ✅ | baseline output below |
| Term decomposition per archetype (tech/org/mgmt/realised) | ✅ | baseline output below |
| Diagnostics printed, informational only (no build-failing gate — I6) | ✅ | I6 guard green; falsified by planted `sys.exit(1)` |
| Curves + diagnostics + inventory handed to the authority; gate ruling is the user's | ✅ | this file + report; harness exits 0, rules nothing |
| Live `TODO: calibrate` inventory printed; count matches §12 / row 6 | ✅ | harness prints **37** live, self-verifying |
| Seed — archetypes run from a clean DB, one command | ✅ | `python -m app.calibrate <pack> [--db-url sqlite:///…]` |
| 1.4 pin byte-identical after a harness run (I7) | ✅ | `test_engine_scoring.py` 10 passed after a run |
| Instance-isolation — four archetypes, zero cross-reads (I4) | ✅ | I4 guard: only instances {11,12,13,14} present, 6 results each, idempotent re-run |
| `make check` green | ✅ | pytest + every `check_*.py` + matrix all green |
| Independent spec review before dispatch | (upstream) | spec v1.1 §11 |
| Independent audit (Heavy tier) | ⏳ | reviews this SHA |
| OPEN-REGISTER reconciliation of §12 register items | ✅ | reconciliation block added (`findings/OPEN-REGISTER.md`); items remain OPEN for the human review loop, now checklisted live |
| Browser / auth canaries | N-A | headless |

---

## The baseline curves (the key deliverable — actual printed output)

Command: `python -m app.calibrate backend/packs/riverside_grocery --db-url sqlite:///<clean>.db`
(SQLite because there is no Postgres in this sandbox; the `create_all` fallback is the documented
headless path — decision 4.) Deterministic score digest (I2): `57dc16703c110c09…5cdfa549`.

```
  riverside_grocery 0.1.0 · 6 rounds · 4 archetypes

  REALISED VALUE (firm, strategy-weighted)      [from RoundResult.firm_score]
                            R1        R2        R3        R4        R5        R6
  Do Nothing            0.0000    0.0000    0.0000    0.0000    0.0000    0.0000
  All Tech, No Org      0.0000    0.0000    0.0000    0.0000    0.0000    0.0000
  Balanced              0.0000    0.0000    0.1946    0.2431    0.2039    0.1217
  Overspender           0.0000    0.0000    0.2108    0.2125    0.1811    0.1081

  BALANCED SCORECARD at R6                       [from RoundResult.scorecard]
                     Financial  Customer  Internal Process  Learning & Growth
  Do Nothing             0.001     0.467     0.000     0.010
  All Tech, No Org       0.029     0.630     0.000     0.011
  Balanced               0.864     0.590     0.315     0.439
  Overspender            0.537     0.590     0.303     0.439

  TERM DECOMPOSITION at R6 -- Order Fulfilment   [from RoundResult.capabilities]
                    Technology  Organisation  Management  Realised
  Do Nothing             0.358     0.000     0.000    0.0000
  All Tech, No Org       0.956     0.000     0.000    0.0000
  Balanced               0.447     0.507     0.665    0.1508
  Overspender            0.447     0.507     0.590    0.1339

  DIAGNOSTICS (informational -- not a gate)
    realised spread at R6: max 0.1217 - min 0.0000 = 0.1217
    All Tech, No Org / Balanced final: 0.0000 / 0.1217 = 0.000
    rank order at R6: Balanced > Overspender > Do Nothing > All Tech, No Org
```

The full report also prints the 37-site calibration checklist + 5 register items at the top, and the
declared strategy per archetype. `--debug` adds the raw pack sub-keys and the per-round,
per-capability decomposition.

---

## First read for the calibration authority (OBSERVATIONS — not a ruling)

These are for the human review loop (spec §5.4); the harness rules nothing.

1. **The complementary-assets thesis holds, starkly.** `All Tech, No Org` reaches Technology 0.956
   at R6 yet realised value **0.0** — Organisation and the governance sub-factor of Management are
   both zero (no training, no owners), and a plain product across the three terms zeroes it. The
   lesson is in one row.
2. **`Do Nothing` floors at realised 0** (no training → Organisation 0), while its BSC *Customer*
   dimension visibly decays (0.467 at R6) as the static estate ages past end-of-life and falls
   behind demand — the aging is real, the value is floored.
3. **`Balanced` scores best at R6** and its punishment of `Overspender` is isolated to Management:
   identical Technology (0.447) and Organisation (0.507), Management 0.665 vs 0.590 — the discipline
   factors (strategic alignment, portfolio discipline) bite, outcomes do not. **But the margin is
   thin** (firm 0.1217 vs 0.1081) and `Overspender` briefly *leads* at R3 (0.2108 vs 0.1946): raw
   generous spending gets close. A reviewer may judge the discipline penalty too weak — this is a
   calibration question for the review loop, not a defect of the instrument.
4. **Realised value is 0 for every archetype in R1–R2.** `signal_responsiveness` starts at 0 (there
   are actionable, unaddressed signals before any clearing action lands at R3), and a single zero in
   the Management geometric mean zeroes the whole Management term, hence realised. Worth the
   reviewer's attention: the responsiveness sub-factor is currently an all-or-nothing gate on early
   rounds. (This reproduces the merged `--full` playthrough, where R2 order realised is also 0.)
5. **Three of seven capabilities never score** (customer_insight, marketing_sales, service) — the
   reference estate seeds no serving nodes for them, so their Technology is 0 across all archetypes.
   Consistent, and low-weighted under cost leadership, but it caps the achievable firm score.

**No dominant strategy is evident** at R6 (Balanced leads), but the thinness of the Balanced /
Overspender gap and the R3 crossover are the two things a reviewer should weigh before ruling.

---

## Invariant falsifications (spec §4.3) — shown to FAIL on a planted defect

| Inv | Falsification demonstrated |
|---|---|
| I1 | planted `_CASE = "riverside_grocery"` in `harness.py` → guard **FAIL** (grep hits) |
| I2 | perturbed one archetype's `adoption` between runs → score digest **differs** (`57dc16…` → `ad2db8…`) |
| I3 | leaked `internal_process_score raw_engine_key` into the report → guard **FAIL** (triple-underscore grep hits) |
| I4 | idempotent-wipe re-run keeps 6 results/instance; dropping the wipe makes the runner raise on a duplicate `RoundResult` |
| I5 | pack yaml md5 identical before/after (a planted pack write would differ) |
| I6 | planted `sys.exit(1)  # dominance gate` in `report.py` → guard **FAIL** (grep hits) |
| I7 | `test_engine_scoring.py` 10 passed after a harness run (the harness reads `RoundResult`, scores nothing) |

**Guard-path bug caught during falsification:** the first draft of `check_calibration_harness.py`
grepped `backend/app/calibrate` with `cwd=backend`, so the I1/I6 greps matched a nonexistent path
and were inert (silently PASS). Fixed to `app/calibrate` (relative to `cwd=backend`); both now fail
correctly on a planted defect. This is the `1.5-RC-004`/`CU-003` failure mode (an unguarded guard);
fixing it before merge is the point of the falsification step.

---

## What changed

New only — no existing engine/scoring/pack/runner file was modified:
- `backend/seeds/archetype_base.py`, `archetype_do_nothing.py`, `archetype_all_tech_no_org.py`,
  `archetype_balanced.py`, `archetype_overspender.py`
- `backend/app/calibrate/{__init__,__main__,harness,report,inventory}.py`
- `backend/tests/check_calibration_harness.py`
- `findings/OPEN-REGISTER.md` (reconciliation block), `handoffs/1.7-calibration-harness/dod.md`
