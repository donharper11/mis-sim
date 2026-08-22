# 1.7 — Calibration Harness · Build Spec

**Authored under** `SPEC_PROTOCOL.md` v1.3 · **Author:** Claude · **Date:** 2026-07-26 · **Reconciled:** 2026-08-22 (v1.1)
**Phase:** 1 · **Depends on:** 1.1–1.6 (all built + merged) · **Blocks:** the Phase 1 gate, and therefore Phase 3
**Gate tier:** **Heavy** (`GOVERNANCE §6.3`, ruled by the user 2026-08-22) — 1.7 exercises the
whole scoring path (1.4 realised value, 1.5 signals/events, 1.6 round resolution) and its output is
the evidence the **Phase-1 calibration gate** rests on. Full four-gate cycle: independent spec review
**and** independent audit; the *calibration-review gate itself is the user's* (§5.4).
**Independent spec review** *(SPEC_PROTOCOL §11, before dispatch)*: **pending** — this v1.1
reconciliation returns for an independent consistency pass before a builder is dispatched.

> **The highest-value packet in the project.** Every number in this simulation is currently
> a guess (`GOVERNANCE §4.9`; 37 `TODO: calibrate` marker sites, §12). This is where we find out
> whether the model produces genuine decisions or a dominant strategy — from a script, before a
> single screen exists, instead of from thirty students in week 9. **The harness runs the maths
> and prints the curves; a human reviews them and rules** (`design/05` §5 Phase-1 gate).

---

## 0. Spec Basis

**Read in full (original authoring, 2026-07-26):** `design/05-implementation-plan.md` §5 (Phase 1
gate) · `handoffs/1.4-scoring-engine/spec.md`, `1.5`, `1.6` · `design/02-traceability-matrix.md` ·
`design/03-scoring-frame-options.md` (BSC output).

**Read in full (2026-08-22 reconciliation) — the built engine, round-runner, and pack that landed
AFTER this spec was authored:**
- `GOVERNANCE.md` v1.4 (§6.3 gate tiering — 1.7 is Heavy), `SPEC_PROTOCOL.md` v1.3,
  `QUALITY_PROTOCOL.md` v1.4 (§3.3 full-game playthroughs);
- `handoffs/1.6-round-runner/spec.md` v1.1 (the resolution order, `RoundResult` shape, the `--full`
  seed) and `handoffs/1.5-event-signal-engine/{spec.md,contract-spec.md v1.2}`;
- the round-runner: `backend/app/round/{runner.py,snapshot.py,actions.py,models.py,db.py}`; the seed:
  `backend/app/seed/demo.py` (`--full` entrypoint), `backend/seeds/{riverside_full.py,riverside_r3.py,
  riverside_signals.py}`; the engine `backend/app/engine/{score.py,rollup.py,ledger.py,events.py}`;
- `backend/packs/riverside_grocery/*` (the reference pack, incl. `PROVENANCE.md` §7 and every
  `TODO: calibrate` marker);
- `findings/OPEN-REGISTER.md` §B (B11/B12/B16/B17/J2), §M (CC-D1/CC-D3/CC-D4), §P (1.6-A-003/A-004),
  which name the calibration deferrals 1.7 owns.

**Extraction sufficiency:** covered. The reconciliation re-verified against the working tree every
claim the 2026-07-26 draft made about a `calibrate` command, a numeric dominance gate, and
YAML-decision-sheet archetypes — three of which no longer match reality (§11). Pack path is
`backend/packs/riverside_grocery/` (the draft's bare `packs/` is stale).

---

## 1. Purpose and scope

**In scope:** four scripted team archetypes that play the reference pack **through the real
round-runner** (`RoundRunner.advance`, the `--full` path — §5.1) · a runner over
(archetype × 6 rounds) that produces, per archetype per round, the **four Balanced-Scorecard
dimensions and realised value** as printed score curves a human reviews (§5.2) · a per-archetype
term decomposition (tech/org/mgmt/realised) · an **inventory** of every `TODO: calibrate` value
1.7 resolves (§12) · a report an instructor can read.

**Out of scope:** tuning the numbers — the harness *reveals*; changes go back to the pack or to
1.3/1.4 (§5.4) · UI · any browser · live decision-sheet→estate mutation (deferred, `1.6-A-002`;
scripted archetypes supply authored per-round estates, §5.1) · the full-game *browser* playthrough
(Phase 3; `QUALITY_PROTOCOL §3.3` — this proves the maths, that proves a student can reach it) ·
**a build-failing numeric dominance assertion** (removed in reconciliation — the gate is human,
§5.3/§5.4).

---

## 2. Project-specific statements

**Scoring factors touched:** exercises all of them; **owns none** (it reads `RoundResult`, it does
not score). Keyed to `design/02` — the Balanced Scorecard row (Financial · Customer · Internal
Process · Learning & Growth, `design/02:102`, computed 1.4 §5.4) and realised value (`GOVERNANCE §1`).
**Casepack keys read:** all, indirectly — the harness never parses the pack itself; it loads it
through `app.casepack.loader.load_casepack` (the same loader `demo.load_scenario` uses,
`backend/app/seed/demo.py:33`) and hands it to `RoundRunner`. **Casepack-identity branching:** none —
must run any pack unchanged, a preview of the Phase 6 gate (`GOVERNANCE §4.6`). I1.
**Instance scoping:** creates throwaway instance/team rows, torn down per run (`_wipe_instance` is
idempotent, `riverside_full.py:176`). Every table it seeds already carries `instance_id` non-null
(1.6 I4). I4.
**Business-language check:** output is for an instructor. Factor names resolve through `labels.yaml`;
a raw engine key in the printed report is a finding. I3.

---

## 3. Settled decisions

1. **Four archetypes minimum** (§5.1). More may be added; these four are mandatory.
2. **Deterministic — over the computed scores, not the raw database.** Same pack + same archetype →
   identical **`RoundResult` score payloads** (`firm_score`, per-capability `terms`/`realised`,
   `scorecard`) every run. Guaranteed by 1.4/1.5 purity and the deterministic seed; **not** a byte
   hash of DB rows (autoincrement ids, insert order differ). I2 hashes the score fields only.
3. **The harness never edits the pack.** It reports; humans decide (I5).
4. **Runs headless in CI-less local dev.** One command, no services beyond the DB (the round-runner's
   Postgres, or its `create_all` fallback — `demo._run_full`, `demo.py:147`).
5. **The gate is a HUMAN judgment, not a numeric assertion by code** *(reconciled 2026-08-22 — see
   §11; aligns the spec to `design/05` §5, which rules the Phase-1 gate as **"curves reviewed; no
   dominant strategy"**).* The harness is **mechanical and deterministic**: it runs, produces the
   score curves and the term decomposition, and may print diagnostic summaries (spread, ratios,
   rank order — §5.3). The **judgment** — is there a dominant strategy? — is made by the calibration
   authority reviewing those curves (§5.4). The harness does **not** exit non-zero on a dominance
   condition, and it does **not** assert `G1–G4` as pass/fail code (the 2026-07-26 draft did both;
   both are removed).

### Reconciliation decisions (added 2026-08-22 — the built engine/runner/pack)

6. **An archetype supplies an authored per-round *estate* AND a decision sheet, not a decision sheet
   alone.** Live decision-sheet→estate mutation is a ruled deferral (`1.6-A-002`): the round-runner
   reads the *post-decision estate* the seed authors (`runner.advance` step 2/4–6 are seed-authored,
   `runner.py:289-290`; `riverside_full._seed_round_estate`). So each archetype is a seed builder in
   the shape of `backend/seeds/riverside_full.py`: per round it authors nodes/edges/deployments/
   governance/staff/policy/stakeholder rows **and** a `decision_line` sheet, then the runner runs the
   fixed resolution order over it (§5.2 of the 1.6 spec) and writes the immutable `RoundResult`. This
   is still **seed, not stub** (`GOVERNANCE §4.9`): the scores are computed by the real engine from
   real DB rows, never asserted beside them. (§13 names the compliant route + rejected alternative.)
7. **The harness consumes `RoundResult`, the 1.4 pin, and the 1.5/1.6 contracts; it redefines none of
   them.** Every curve is read from the persisted `RoundResult.payload` (`models.py:300`) the runner
   already writes — `firm_score`, `capabilities[].{terms,realised}`, `scorecard`, `signals`,
   `missed_signals` (`runner.py:349-363`). A harness change that moves the 1.4 pin
   (`test_engine_scoring.py`) is a defect. Any genuine conflict is a **STOP** to the authority
   (`GOVERNANCE §7`), not a silent resolution.
8. **The output is the four BSC dimensions + realised, per archetype, across 6 rounds** (the mandate,
   `design/02:102`). `realised` per archetype per round is `payload["firm_score"]` (strategy-weighted
   Σ realised(c), `rollup.firm_score`, `rollup.py:35`); the four BSC dims are
   `payload["scorecard"].{financial,customer,internal_process,learning_growth}` — produced by
   `runner._rolled_scorecard` (`runner.py:376`), which takes the engine BSC (`score.py:96-99`) and
   applies fired-event scorecard deltas on top, so in an event-firing round the payload scorecard
   differs from the raw engine BSC (finding 1.7-SR-001).
9. **1.7 resolves the `TODO: calibrate` inventory of §12** — 37 pack-YAML marker sites plus five
   register-owned code/seed calibration items — so calibration is a checklist, not a hunt. Row 6 of
   the pre-flight (§7) prints the live list before any curve is interpreted: calibrating against
   placeholder values produces confident nonsense.

---

## 4. Open decisions

| # | Question | Criteria | Reporting |
|---|---|---|---|
| **O1** | How is an archetype's per-round play expressed? | **Default: a Python seed builder per archetype, in the shape of `seeds/riverside_full.py`, authoring the post-decision estate + a `decision_line` sheet per round** (decision 6). The 2026-07-26 draft said "YAML decision sheets loaded through the same path a student's decisions take"; that path does not exist yet (live mutation is deferred, `1.6-A-002`), so a sheet alone cannot produce the estate. A builder mirrors exactly what `--full` already does — one command, clean DB, real engine — which is the strongest available "same path". If/when live mutation lands, archetypes migrate to sheet-only. | Record |
| **O2** | Is a sensitivity sweep in scope for v1? | **Default: NO — optional, a follow-up.** The mandatory deliverable is the curves + decomposition + inventory (the Phase-1 gate inputs). A ±20% single-factor sweep is a useful *diagnostic* for the human review but is not what the gate requires, and it multiplies runs across 37 marker sites. If added, it is a `--sweep` flag printing swing per factor; it never gates. | Record |
| **O3** | Should the harness assert, or only report? | **RULED (mandate, 2026-08-22): report only.** The harness prints curves and optional diagnostics; it does not assert a dominance gate or exit non-zero on one (decision 5). The 2026-07-26 draft's "assert on the three gate conditions so it can fail a build" is reversed — the judgment is the authority's (§5.4). | Record |

---

## 5. Design

### 5.1 The mandatory archetypes — real seed builders on the real runner

Each archetype is a seed builder (decision 6 / O1) in the shape of
`backend/seeds/riverside_full.py`: a distinct `(instance_id, team_id)`, a declared strategy, and a
per-round `(estate + decision sheet)`. The harness seeds all four and runs `RoundRunner.advance`
over six rounds each, collecting the six `RoundResult` payloads per archetype.

| Key | Behaviour | Expressed as | What it must demonstrate |
|---|---|---|---|
| `do_nothing` | declares a strategy, then spends nothing | empty/maintenance-only `decision_line` sheets; a static minimal estate that ages (no new nodes, training stays 0, no owners) | the floor. Debt accrues, EOL bites, signals fire unanswered |
| `all_tech_no_org` | buys the best of everything, funds zero training, assigns no owners | a rich node estate each round; deployments with `trained_count=0`/`process="none"`; `governance` rows with no `owner_assigned`/`sponsor_assigned` | **the sim's central lesson.** High Tech, collapsed Org (the geomean throttle zeroes realised), low realised value |
| `balanced` | coherent strategy, proportionate Tech/Org/Mgmt, acts on signals | the `riverside_full.py` playthrough shape: scaled estate + training + `fund_response`/`add_training`/`scale_node` action lines that clear signals before they fire | the intended good play. Should score best |
| `overspender` | funds everything generously, ignores strategy alignment | large capex across all capabilities each round, but a `declared_strategy` the spend does not match (weak strategic-alignment cosine, `score.py`) | punished by cost efficiency and portfolio discipline, not by outcomes |

Two more worth adding once the four run (not mandatory): `signal_chaser` (perfect responsiveness,
panic spending — must **not** win, or responsiveness is a dominant lever) and `strategy_drifter`
(declares cost leadership, spends on differentiation).

**Determinism note.** `riverside_full.py` fixes `INSTANCE_ID=1, TEAM_ID=1`. The harness assigns each
archetype its own `(instance_id, team_id)` and wipes it first (`_wipe_instance`, idempotent) so the
four runs neither collide nor leak (instance-isolation, `GOVERNANCE §4.5`).

### 5.2 Output — score curves a human reads

The four BSC dimensions and realised, per archetype, across the six rounds — read from the persisted
`RoundResult.payload`, computed by the real engine (`GOVERNANCE §4.9`). Illustrative shape (numbers
are **placeholders**, not pinned — the harness prints whatever the engine computes):

```
$ python -m app.calibrate backend/packs/riverside_grocery

  riverside_grocery 1.0.0 · 6 rounds · 4 archetypes
  (37 TODO: calibrate marker sites live — see the inventory before trusting any curve)

  REALISED VALUE (firm, strategy-weighted)      [payload.firm_score]
             R1     R2     R3     R4     R5     R6
  balanced   0.31   0.44   0.52   0.58   0.63   0.67
  overspend  0.29   0.41   0.46   0.47   0.49   0.51
  all_tech   0.22   0.28   0.24   0.19   0.17   0.16
  do_nothing 0.28   0.24   0.19   0.13   0.09   0.06

  BALANCED SCORECARD at R6                        [payload.scorecard]
             financial  customer  internal_process  learning_growth
  balanced      0.64      0.61          0.66              0.58
  all_tech      0.31      0.29          0.44              0.12   ← Org collapse

  TERM DECOMPOSITION at R6 (order_fulfilment)     [payload.capabilities[].terms]
             tech   org    mgmt   realised
  balanced   0.81   0.79   0.76   0.486
  all_tech   0.88   0.21   0.44   0.081     ← the lesson, in one row

  DIAGNOSTICS (informational — not a gate)
    realised spread at R6: max 0.67 − min 0.06 = 0.61
    all_tech / balanced final: 0.16 / 0.67 = 0.24
    rank order R6: balanced > overspend > all_tech > do_nothing

  → reviewed by the calibration authority (§5.4). No exit-code judgment.
```

Every value is read from `RoundResult.payload` (`runner.py:349-363`): `firm_score`,
`scorecard.{financial,customer,internal_process,learning_growth}`, `capabilities[].terms`/`realised`.
The `--full` describe helper (`demo._describe_full`, `demo.py:117`) is the existing precedent for
printing computed round payloads — this reuses that pattern across four archetypes.

### 5.3 Diagnostics — computed, never asserted

The harness *may* compute and print, as **informational** lines only (never an exit code):
- **realised spread** at the final round — `max(final) − min(final)` across the four archetypes;
- **complementary-asset ratio** — `all_tech_no_org` final ÷ `balanced` final (the Org throttle, the
  sim's thesis);
- **rank order** per round.

These are the numbers the 2026-07-26 draft hard-wired into a build-failing `G1–G4`. **They are kept
as diagnostics and stripped of their gate authority** (decision 5, §11). They inform the human
review; they do not replace it. A sensitivity sweep (O2) is likewise diagnostic if built.

### 5.4 The calibration-review loop — mechanical vs human, made explicit

```
MECHANICAL (the harness — this packet)          HUMAN (the calibration authority — the user)
────────────────────────────────────────        ──────────────────────────────────────────
seeds 4 archetypes on the real runner            reads the printed curves + inventory
runs 6 rounds × 4, deterministic                 asks: is there a dominant strategy?
prints realised + BSC curves per archetype       asks: does all_tech collapse on Org?
prints term decomposition + diagnostics          rules: gate PASS → Phase 3 may begin
prints the live TODO: calibrate inventory        rules: gate FAIL → numbers go back (below)
```

**The harness proves the maths are deterministic and prints the truth; it never rules on it.** This
is `design/05` §5 verbatim: *"harness runs 6 rounds × 4 scripted teams; **curves reviewed**; no
dominant strategy."* If the authority rules FAIL, the fix goes back — a runaway lever or spread to a
pack number or 1.4 weight, an Org term that does not bite to pack content or 1.4 Org sub-factors, a
term that changes nothing to whether it should exist. **Do not adjust numbers to make the review
pass without understanding why it failed.** A tuned-to-pass model is worse than a failing one,
because it looks finished. This review is `QUALITY_PROTOCOL §3.3`'s counterpart: the harness proves
the maths, the Phase-3 browser playthrough proves a student can reach it.

---

## 5.5 Seed — the four archetypes are real playthroughs *(GOVERNANCE §4.9)*

```
seed        backend/seeds/archetype_*.py — one seed builder per archetype, in the shape of
            seeds/riverside_full.py: per-round authored estate + decision sheet, run through
            RoundRunner.advance (the same path --full already exercises)
command     python -m app.calibrate backend/packs/riverside_grocery   (NEW entrypoint)
demonstrate the §5.2 curves (realised + 4 BSC dims), computed from the persisted RoundResults
            the §5.2 term decomposition, computed
            the §5.3 diagnostics, computed (informational)
            the §12 TODO: calibrate inventory, printed live from the pack
```

Archetypes as **seed builders on the real runner** (not hypothetical API calls, not stubbed tables)
is what makes this a seed rather than a script — it exercises the real decision-resolution path the
merged 1.6 round-runner ships. The `--full` command (`demo.py --full`) is the single-team precedent;
`app.calibrate` generalises it to four archetypes and prints the comparison.

---

## 6. Invariants

| # | Invariant | Check | Expected · falsification |
|---|---|---|---|
| I1 | Runs any pack unchanged (no case-identity branching) | `grep -rniE "riverside\|grocer" backend/app/calibrate/` | zero. **Falsify:** plant `if pack.metadata.pack_key == "riverside...":` → grep is non-zero |
| I2 | Deterministic over the computed scores | hash the concatenated `RoundResult` score fields (`firm_score`, `capabilities[].terms/realised`, `scorecard`) across 4 archetypes × 6 rounds, 3 runs → one hash | 1 hash. **Falsify:** perturb one archetype estate value between runs → hashes differ |
| I3 | No raw engine keys in the printed report | `python -m app.calibrate … \| grep -E "[a-z]+_[a-z]+_[a-z]+"` | zero outside a `--debug` section. **Falsify:** print `capability_key` instead of its `labels.yaml` name → grep hits |
| I4 | Instances torn down; no leak between archetypes | count `round_result` rows for an instance the harness did not run, before/after | equal (0). **Falsify:** drop the `_wipe_instance` call → a re-run doubles rows / cross-reads appear |
| I5 | Never mutates the pack | `md5sum backend/packs/riverside_grocery/**/*.yaml` before/after a run | identical. **Falsify:** plant a pack file write → md5 differs |
| I6 | The gate is not asserted by code | `grep -rnE "sys.exit\(1\)\|assert.*spread\|<= *0\.15" backend/app/calibrate/` | zero — no dominance assertion, no build-failing exit (decision 5). **Falsify:** add `if spread > 0.15: sys.exit(1)` → grep hits |
| I7 | The 1.4 pin is untouched | `cd backend && PYTHONPATH=. python3 -m pytest tests/test_engine_scoring.py -q` after a harness run | pass (tech `0.750008` / org `0.507003` / mgmt `0.656778` / realised `0.249744`). **Falsify:** the harness cannot move it — it reads `RoundResult`, scores nothing; a change that does move it is a STOP (decision 7) |

**Note (I6, reconciliation).** The 2026-07-26 draft's I6 was the opposite — *"gate conditions
computed as code"* verified by `grep "0.15\|0.5 \*\|0.10" gates.py`. That invariant is **inverted**:
the reconciled I6 proves the harness does **not** encode a build-failing gate, because the gate is
human (decision 5, §11). Diagnostics may still compute those numbers (§5.3); they may not `exit(1)`.

---

## 7. Pre-Flight Verification Register

| # | Claim | Tag | Check | Expected |
|---|---|---|---|---|
| 1 | 1.6 merged; the six-round run works on the real runner | `[V]` | `grep -n "def advance" backend/app/round/runner.py`; `cd backend && PYTHONPATH=. python3 -m app.seed.demo --full` | `advance` at `runner.py:282`; six RoundResults, opex 47000→…→70000 |
| 2 | Engine deterministic; 1.4 pin green at base | `[V]` | `cd backend && PYTHONPATH=. python3 -m pytest tests/test_engine_scoring.py -q` (twice) | pass, identical both runs |
| 3 | Riverside validates clean | `[A]` | `cd backend && PYTHONPATH=. python3 -m app.casepack.validate backend/packs/riverside_grocery` (or the module's actual entrypoint) | exit 0, 0 errors |
| 4 | Riverside has all 4 strategies with weights | `[V]` | `grep -c "^- key:" backend/packs/riverside_grocery/strategies.yaml` | 4 |
| 5 | `RoundResult` carries the decomposition the curves need | `[V]` | `grep -n "capabilities\|scorecard\|firm_score" backend/app/round/runner.py` | payload carries `capabilities` (from `final_score.record()`, `runner.py:351`), `scorecard` (:346), `firm_score` (:362); `RoundResult.payload` JSON (`models.py:300`) |
| 6 | **Pack `TODO: calibrate` list — the harness runs on stubs until it is resolved** | `[V]` | `grep -rn "TODO: calibrate" backend/packs/riverside_grocery/ --include=*.yaml \| grep -v "watch_rules.yaml:7:" \| wc -l` | **37 marker sites** (34 in `PROVENANCE.md §7` + 3 outage-schema, §12). **If any remain, report the list before interpreting any curve.** |
| 7 | `firm_score` is the strategy-weighted realised (the "realised" curve) | `[V]` | `grep -n "def firm_score" backend/app/engine/rollup.py` | `firm_score(pack, declared_strategy, realised) = Σ realised(c) × weight` (`rollup.py:35-36`) |
| 8 | The four BSC dims exist on the score record | `[V]` | `grep -n "financial\|customer\|internal_process\|learning_growth" backend/app/engine/score.py` | all four in `record()["balanced_scorecard"]` (`score.py:96-99`) |
| 9 | The `--full` seed builder is the archetype template | `[V]` | `grep -n "def run_full_game\|_seed_round_estate\|_decision_lines_for_round" backend/seeds/riverside_full.py` | present — the per-round `(estate + sheet)` shape decision 6/O1 mirrors |
| 10 | **No `calibrate` entrypoint exists yet** (this packet builds it) | `[V]` | `ls backend/app/calibrate backend/calibrate 2>&1` | absent → **NEW code**, not a re-verify. `app/calibrate/gates.py` from the draft is **not** built (the gate is human, §11). |

**Row 6 is the one to take seriously** (unchanged intent from the draft; count corrected).
Calibrating against placeholder values produces confident nonsense. **Row 10 flags the draft's two
build assumptions that no longer hold**: there is no `calibrate` command and there must be no
`gates.py` — a builder who finds either present has hit a spec/reality conflict and **STOPs**
(`GOVERNANCE §7`).

---

## 8. Build steps

1. **Archetype seed builders** — four `seeds/archetype_*.py` in the `riverside_full.py` shape
   (decision 6 / O1): per round, authored estate + `decision_line` sheet + declared strategy, each on
   its own `(instance_id, team_id)`. *Verify:* `balanced` seeds six rounds and its `RoundResult`
   realised curve is non-degenerate.
2. **The `app.calibrate` runner** over (archetype × 6 rounds), reusing `RoundRunner.advance` and the
   loader. *Verify:* four archetypes × six rounds complete; I1, I2, I4, I5.
3. **Curve + decomposition report** — realised (firm_score) + the four BSC dims + term decomposition,
   read from `RoundResult.payload`, matching the §5.2 shape. *Verify:* I3 (no raw keys).
4. **Diagnostics (informational)** — spread, complementary-asset ratio, rank order, printed but never
   asserted. *Verify:* I6 (no `sys.exit(1)` / dominance assertion).
5. **Print the live `TODO: calibrate` inventory** (§12) at the top of the report. *Verify:* the
   printed count equals pre-flight row 6's grep.
6. **Run it for real and report the truth.** *Verify:* the actual curves, whatever they are, in
   `dod.md`; hand them to the calibration authority (§5.4). **The harness passing is the harness
   running deterministically and printing correctly — not the model passing the gate.**

Step 6 is not "make it pass." It is "run it and report the truth." A dominant strategy revealed here
is the harness doing its job; the authority rules on it (§5.4), not the exit code.

---

## 9. Definition of Done

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–10, esp. rows 6 and 10 | | |
| Steps 1–6 verified | | |
| I1–I7 (each with its planted-defect falsification, §4.3) | | |
| O1, O2, O3 recorded | | |
| Four mandatory archetypes implemented as seed builders on the real runner | | |
| Curves = 4 BSC dims + realised, per archetype × 6 rounds, read from `RoundResult` | | |
| Term decomposition per archetype (tech/org/mgmt/realised) | | |
| Diagnostics printed, informational only (no build-failing gate — I6) | | |
| **Curves + diagnostics + inventory handed to the calibration authority; the gate ruling is the user's (§5.4)** | | |
| Live `TODO: calibrate` inventory printed; count matches §12 / pre-flight row 6 | | |
| **Seed** — archetypes run through the real runner from a clean DB, one command | | |
| 1.4 pin byte-identical after a harness run (I7) | | |
| Instance-isolation — four archetypes, zero cross-reads (I4) | | |
| `make check` green (harness guards reachable from it, `QUALITY_PROTOCOL §2`) | | |
| Independent spec review before dispatch (SPEC_PROTOCOL §11, Heavy tier) | | |
| Independent audit (Heavy tier) | | |
| OPEN-REGISTER reconciliation — every §12 register item (B11/B12/B16/J2, CC-D1, 1.6-A-003/A-004) re-tested and its row updated in the same commit (GOVERNANCE §9) | | |
| Browser / auth canaries | | **N-A** — headless |

---

## 10. What happens next

**If the authority rules the gate PASSES:** Phase 1 is complete and Phase 3 may begin.

**If it rules FAIL:** it goes back — a dominant strategy or a runaway lever to a pack number or 1.4's
weights; `all_tech` failing to collapse to 1.3's content or 1.4's Org sub-factors; a term that
changes nothing to whether it should exist at all. **Do not adjust numbers to make the review pass
without understanding why it failed.** A tuned-to-pass model looks finished and is not.

---

## 11. Reconciliation changelog

- **v1.1** (2026-08-22) — **bounded reconciliation** of the 2026-07-26 draft against the built,
  merged 1.4/1.5/1.6 (`GOVERNANCE §6.3`: 1.7 confirmed **Heavy**). No scope expansion. Three draft
  assumptions were verified against the working tree and **corrected**:
  1. **The `calibrate` command and `app/calibrate/gates.py` were assumed built; neither exists**
     (pre-flight row 10). The harness is NEW code over the real `RoundRunner`/`--full` path
     (`runner.py`, `seeds/riverside_full.py`), not a hypothetical API.
  2. **The gate was drafted as a numeric, build-failing assertion** (draft settled-decision 5,
     `G1–G4` as code, O3 "assert so it can fail a build", exit 1). **Reversed to a human judgment**
     to match `design/05` §5 (*"curves reviewed; no dominant strategy"*) and the dispatch mandate:
     the harness is mechanical/deterministic and prints curves + diagnostics; the authority rules
     (§5.3/§5.4). I6 is inverted (proves *no* code gate). O3 ruled report-only. `G1–G4` survive only
     as **informational diagnostics** (§5.3). *This reverses two draft "settled" items; it is
     authorised by the dispatching authority and is the pre-existing `design/05` gate, so it is a
     reconciliation, not a new decision — recorded here per `GOVERNANCE §4.4`.*
  3. **Archetypes were drafted as "YAML decision sheets on the same path a student's decisions
     take"; that path does not exist** (live decision→estate mutation is deferred, `1.6-A-002`).
     Reconciled to authored per-round *estate + sheet* seed builders in the `riverside_full.py` shape
     (decision 6 / O1 / §13) — still seed-not-stub, still the real engine.
  - **Header/§0/§2:** re-based on `SPEC_PROTOCOL v1.3`; added the 2026-08-22 read set; declared Heavy
    tiering and the human calibration gate; corrected the pack path to `backend/packs/…`.
  - **§1/§3/§4/§5:** scope, decisions, open decisions, and design reconciled to the real
    `RoundResult` payload fields (`firm_score`, `scorecard`, `capabilities[].terms/realised`) and the
    real command; output re-expressed as the four BSC dims + realised (the mandate).
  - **§6/§7:** invariants re-expressed against real paths, each with a planted-defect falsification
    (`SPEC_PROTOCOL §4.3`); I6 inverted; pre-flight rows re-pointed at built code, rows 6/10 flag the
    stub-count and the absent-command reality.
  - **§12 (new):** the `TODO: calibrate` inventory 1.7 resolves — 37 pack-YAML marker sites +
    5 register-owned items — each with where it lives and what it affects.
  - **§13 (new):** compliant route + rejected alternative for the archetype-expression seam.
  - **No `CONTRACTS.md` change:** the harness reads existing frozen shapes and defines no new field.
- **v1.0** (2026-07-26) — initial authoring under `SPEC_PROTOCOL v1.1`, before the engine, round-runner,
  and pack existed. Four archetypes, YAML decision sheets, a `calibrate` command, and a numeric
  `G1–G4` dominance gate — the last three superseded by v1.1.

---

## 12. The `TODO: calibrate` inventory — the checklist, not a hunt

Every value 1.7 is expected to move, with where it lives and what it affects. **Calibrate against
these knowingly; do not interpret a curve while a load-bearing one is a placeholder** (pre-flight
row 6).

### 12.1 Pack-YAML `TODO: calibrate` marker sites — 37

Verified live: `grep -rn "TODO: calibrate" backend/packs/riverside_grocery/ --include=*.yaml | grep -v
"watch_rules.yaml:7:"` → 37 sites (the excluded `watch_rules.yaml:7` is the convention header, not a
marker). 34 are tabulated in `PROVENANCE.md §7`; the **3 outage-schema sites** below were added by
the 1.5 engine build (`OPEN-REGISTER §M`, CC-D3/CC-D4) after that table and are additional.

| File | Sites | What is unjustified | Affects |
|---|---|---|---|
| `watch_rules.yaml` | 5 | thresholds on `store_cap_01`, `fin_close_01`, `cust_data_01`, `mkt_channel_01`, `svc_backlog_01` (only `ord_cap_01`'s 0.80/0.95 is pinned) | when a signal raises/escalates → the whole 1.5 signal ledger and responsiveness curve |
| `events.yaml` | 7 | scorecard deltas + option costs on the seven non-pinned cards | BSC deltas at `runner._rolled_scorecard`; the customer/financial curves |
| `policies.yaml` | 6 | every effect vector; `data_egress` 12000; `data_access` 9000 (inherited); `staff_monitoring` cost + effects | policy alignment/discipline (Mgmt term) |
| `catalog.yaml` (base) | 5 | `store_back_office_pc` capex; the cloud/saas ladders on three new items; `erp_suite` compute/opex/lead-times; **and the whole lead-time band** (B12/F5) | capex/opex/lead-time → Tech term, TCO, follow-through |
| `catalog.yaml` (`config_tiers`) | 1 | every `config_tiers` multiplier except `erp_suite`'s harvested capex (B11) | tiered capex → Tech term |
| `catalog.yaml` (`base_rto_hours`) | 2 | `base_rto_hours` on two items (4.0, 12.0) — **NEW, CC-D3** | outage duration (`events.outage_duration`), blast-radius evidence |
| `capabilities.yaml` (`agreed_availability`) | 1 | `financial_reporting.agreed_availability` 0.995 — **NEW, CC-D4** | `availability_shortfall` metric |
| `platform.yaml` (placement) | 4 | cloud/saas figures on `failover_cluster`, `threat_detection`, `end_user_email`, `data_platform` | placement capex/opex → Tech term |
| `platform.yaml` (`support_tiers[].fte_equivalent`) | 3 | FTE on basic/standard/premium (0.6/1.4/2.4) — 1.3-RA-001 | IT staff load pool → Tech term |
| `preferences/platform.yaml` | 1 | the `weight` column throughout | stakeholder view weighting |
| `preferences/policies.yaml` | 1 | both `weight` columns | policy-preference weighting (Mgmt) |
| `preferences/services.yaml` | 1 | both `weight` columns | service-tier preference weighting |

### 12.2 Register-owned calibration items 1.7 owns that are **not** pack-YAML markers

| # | Item | Where it lives | What it affects |
|---|---|---|---|
| `B12`/`F5` | `lead_time_rounds` residual (10 of 42 at 0 as last swept) | `catalog.yaml` / `platform.yaml` `*.lead_time_rounds` (covered by the catalog "whole band" marker) | follow-through sharpness; in-flight arrival timing (1.6 O2) |
| `CC-D1` | `capacity_utilisation` R2/R3 exact history numbers (illustrative `0.83`/`1.11` not reproduced) | seed history / `seeds/riverside_signals.py` + the `--full` demo numbers | the `--with-signals` demonstration figures (formula is executable now) |
| `1.6-A-003` | the `--full` opex per-node values (back-distributed to hit the ratchet targets) | `seeds/riverside_full.py` `OPEX_TARGET_BY_ROUND` + `_distribute_opex` | opex run-rate curve (recompute path I7 is real; the values are placeholders) |
| `1.6-A-004` | `people_affected` derivation from the catalog (still hand-authored in the seed) | `seeds/riverside_r3.py` + `catalog.yaml` `people_affected.count` | Org training denominator (`organisation.py`); reconciliation guard prevents drift meanwhile |
| `J2` | `preferences/training.yaml` provenance overstates the harvest; 8 change-mgmt options + 20 fit cells never authored | `preferences/training.yaml` + `PROVENANCE.md §5a` | training-preference content; the provenance claim |

**Count for the report:** 37 pack-YAML marker sites + 5 register-owned items = the 1.7 calibration
checklist. Note many marker sites cover *multiple* numbers ("both weight columns throughout", "the
whole band", "every `config_tiers` multiplier") — the count is of marker *sites*, not of individual
figures, which is larger.

---

## 13. Compliant route + rejected alternative — expressing an archetype's play *(SPEC_PROTOCOL §4.1)*

**How a scripted team's per-round decisions become the runner's inputs (decision 6 / O1).**
*Compliant route:* each archetype is a seed builder in the shape of `seeds/riverside_full.py` —
per round it authors the post-decision *estate* (nodes/edges/deployments/governance/staff/policy/
stakeholder rows) **and** a `decision_line` sheet with the action-bearing lines that drive the
`ActionRecord` history (`actions.py`), then the harness calls `RoundRunner.lock(r)` and
`RoundRunner.advance(r)` — the exact path `--full` uses. The scores are computed by the real engine
from real DB rows (seed, not stub, `GOVERNANCE §4.9`); the harness reads them back from
`RoundResult.payload`. *Rejected alternative:* supply only a `decision_line` sheet and let the runner
derive the estate from it — **rejected: that path does not exist** (live decision→estate mutation is
the ruled deferral `1.6-A-002`; `runner.advance` reads the seed-authored estate, steps 2/4–6). A
sheet-only archetype would score against an empty estate and produce meaningless curves. When live
mutation lands (Phase 2/3), archetypes migrate to sheet-only with no change to the harness's
read-back.

**Whether the harness asserts the gate (decision 5 / O3).**
*Compliant route:* the harness prints curves + informational diagnostics and exits 0; the calibration
authority reviews and rules (§5.4), matching `design/05` §5. *Rejected alternative:* the 2026-07-26
draft's `gates.py` computing `G1–G4` and `sys.exit(1)` on a spread threshold — **rejected: it encodes
a human calibration judgment as a hard-coded constant** (is 0.15 the right spread? that *is* the
question the review exists to answer), and a red build would pressure a builder to tune numbers to
pass (§10, the one thing this packet must not cause). The thresholds survive as diagnostics, stripped
of exit authority (I6).
