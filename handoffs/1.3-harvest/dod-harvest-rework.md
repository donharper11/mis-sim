# 1.3 — Harvest Rework · Definition of Done

**Rework packet:** `handoffs/rework/1.3-harvest-audit-2026-08-21.md` (findings `1.3-RA-001`, `1.3-RA-002`)
**Branch:** `build/1.3-harvest-rework`
**Base:** `main` @ `dad098980fa122fc0cfe413f05cfc3b48f4ebaf1` ("Merge 1.2 validator rework")
**Worktree:** `…/scratchpad/wt-1.3-harvest`
**Builder:** RE-BUILDER agent · **Date:** 2026-08-21 · **Final commit:** see §12

> Builder ≠ Auditor (`GOVERNANCE §6`). This is the builder's evidence, not an audit verdict.
> The branch goes to an independent re-audit before any merge.

---

## 0. Headline

Two provenance/contract issues, both fixed without touching a numeric value or any scoring
code:

```
1.3-RA-001  support-tier FTE estimates unmarked at the value  → per-value rationale + 3 TODO markers
1.3-RA-002  harvested_raw_fit provenance-only, but unguarded   → executable regression guard + falsification
```

Files changed: `platform.yaml`, `PROVENANCE.md`, `preferences/services.yaml` (documentation/
provenance only), and one new test file. **No FTE number changed. No weight changed. No
scorer changed. No validator code added.**

---

## 1. Pre-flight & baseline (base `dad0989`)

| Check | Result |
|---|---|
| Base SHA = dispatch's `dad0989` | **Yes** — `git rev-parse main` = `dad0989…` ("Merge 1.2 validator rework") |
| Full pytest suite | **11 passed** |
| `check_fixture_matrix.py` | exit 0 (all 1.2 fixtures green) |
| `validate_casepack riverside` text | `0 errors · 0 warnings · exit 0` |
| `validate_casepack --json riverside` | exit 0, **0 findings** (text/JSON parity) |
| `harvest_readback.py` | `43/43 matched, 0 mismatched, 2 declared conflicts`, exit 0 |

---

## 2. Independent verification of both findings (verified on `dad0989`, not inherited)

### `1.3-RA-001` — support-tier FTE estimates unjustified at the value — **CONFIRMED**
Base `platform.yaml` support_tiers each carried only a cost justification:
```
- {key: basic, ... fte_equivalent: 0.6, provenance: {source: HARVESTED, note: "... cost_value 20000 carried exactly"}}
- {key: standard, ... fte_equivalent: 1.4, provenance: {... "cost_value 50000 carried exactly"}}
- {key: premium, ... fte_equivalent: 2.4, provenance: {... "cost_value 100000 carried exactly"}}
```
The harvested source has **no FTE column** — direct inspection of the extraction:
```
$ python3 -c "import json; d=json.load(open('backend/harvest/mis_lite/maintenance_support_levels.json')); print(sorted(d[0]))"
['cost_value', 'description', 'max_value', 'min_value', 'support_level_id', 'support_level_name']
```
So 0.6 / 1.4 / 2.4 are authored estimates whose provenance justified the *cost*, not the FTE
— and `preferences/services.yaml` rests `it`'s strongest view on them ("premium 2.4 FTE
against a 2.0 pool"). `GOVERNANCE §4.9` requires estimates to carry rationale and unjustified
values to be marked. Confirmed material.

### `1.3-RA-002` — harvested_raw_fit adjacent to authoritative weights, no machine guard — **CONFIRMED**
`strategies.yaml` stores `harvested_raw_fit` beside `capability_weights`; `CONTRACTS.md`
(`strategy.capability_weights`) says the raw multipliers are a different scheme and must not
be mixed. No test made that executable. Confirmed (producer/consumer trace, §3).

Neither finding is stale on `dad0989`. No STOP condition: the scorer *is* testable against
the loaded strategy (§4), and the fix needs no new scoring/validator rule.

---

## 3. Producer / consumer trace (grep evidence)

**`support_tiers[].fte_equivalent`**
- Producer: `backend/packs/riverside_grocery/platform.yaml` (basic/standard/premium) and the
  fixture packs' authored tiers.
- Schema: `backend/app/casepack/models.py:279` `fte_equivalent: float = Field(ge=0)`.
- Consumer (semantic): `preferences/services.yaml:40` (the `it` view's rationale). No engine
  reads it yet — G1 staffing (spec 4.5) is unbuilt. So its only present consumer is the
  provenance argument, which is exactly why the value's own provenance had to be correct.

**`harvested_raw_fit`** — referenced in exactly two places, both non-consuming:
```
backend/app/casepack/models.py:252   harvested_raw_fit: dict[SnakeKey, float] = Field(default_factory=dict)   # field decl
backend/packs/riverside_grocery/strategies.yaml (×4)                                                            # data
```
**No engine, scorer, or validator file reads `harvested_raw_fit`.** (Also note the two maps
carry *different key sets*: `harvested_raw_fit` has 7 keys incl. `service`; each strategy's
`capability_weights` has 6.)

**`capability_weights`** — the authoritative input, consumed by:
```
engine/score.py:127        weights = dict(s.capability_weights)         # balanced scorecard
engine/rollup.py:40        weights = dict(s.capability_weights)         # firm rollup
engine/management.py:70    _cosine(spend, dict(strat.capability_weights))  # strategic alignment
casepack/checks.py:96, models.py:257  sum-to-1.0 invariant
casepack/validate.py (E03/E22/W02)    validation
```

---

## 4. RA-001 remediation — per-value FTE provenance

`platform.yaml` `support_tiers` expanded from inline rows to blocks. **The numeric FTE values
are unchanged** (verified: loader reads `basic 0.6 · standard 1.4 · premium 2.4`, costs
20000/50000/100000). Each row now:
- keeps `source: HARVESTED` for the cost (`cost_value` carried exactly — the tier identity is
  harvested and that is honest);
- states, at the value, that `fte_equivalent` is an **authored estimate, not harvested**,
  with a value-specific rationale (basic = business-hours part-person; standard = ~1.5 with
  out-of-hours; premium = a dedicated team just above the 2.0 pool — the figure the `it` view
  turns on);
- carries `TODO: calibrate -- mis_lite has no FTE column; owner 1.7`.

`preferences/services.yaml` provenance and `PROVENANCE.md §10.3` now state that the `it`
view's FTE basis is authored/marked, and that the view's *direction* (premium exceeds the
pool) survives any calibration while the *margin* is what 1.7 would move.

**Calibration owner:** module **1.7** (its harness), consistent with `PROVENANCE.md §7`'s
standing statement.

### TODO inventory — before / after, reconciled

| File | before | after | Δ |
|---|---|---|---|
| `watch_rules.yaml` | 5 | 5 | — |
| `events.yaml` | 7 | 7 | — |
| `policies.yaml` | 6 | 6 | — |
| `catalog.yaml` | 5 | 5 | — |
| `platform.yaml` (placement figures) | 4 | 4 | — |
| **`platform.yaml` (support_tiers FTE)** | **0** | **3** | **+3** |
| `preferences/platform.yaml` | 1 | 1 | — |
| `preferences/policies.yaml` | 1 | 1 | — |
| `preferences/services.yaml` | 1 | 1 | — |
| **Total real YAML markers** | **30** | **33** | **+3** |

Counting method: `grep -c "TODO: calibrate"` over tracked pack `*.yaml`, minus the one
`watch_rules.yaml` convention-header line (line 7) that describes the marker rather than being
one. My added header comment and the services.yaml/PROVENANCE prose deliberately avoid the
literal string so they do not inflate the count; the only new literal markers are the three
FTE lines. `PROVENANCE.md §1` and `§7` are updated to 33 with the +3 attributed to
`1.3-RA-001`. Every difference is the three FTE estimates and nothing else.

---

## 5. RA-002 remediation — executable raw-fit isolation guard

New file `backend/tests/test_raw_fit_isolation.py`, two paired tests exercising the **real
1.4 scorer** (`score_team`) over the **real loaded Riverside R3 strategy shape**
(`app.seed.demo.load_scenario("riverside_r3")`, the same fixture the 1.4 pin tests use):

1. `test_raw_fit_mutation_cannot_change_score` — mutates `harvested_raw_fit` on every strategy
   three ways (zeroed, reflected `9.9 - v`, emptied) while holding `capability_weights` fixed,
   via `model_copy(update=…)`, and asserts the score record is byte-identical.
2. `test_isolation_guard_is_not_vacuous` — routes the raw-fit numbers in through
   `capability_weights` (the map the scorer *does* read) and asserts the score **changes**, so
   the isolation test passes because raw fit is ignored, not because raw fit equals the weights.

```
tests/test_raw_fit_isolation.py::test_raw_fit_mutation_cannot_change_score PASSED
tests/test_raw_fit_isolation.py::test_isolation_guard_is_not_vacuous PASSED
2 passed
```

### Falsification (dispatch requirement 5) — the guard would fail if the scorer read raw fit
Scratch demonstration, **reverted immediately, not committed**: `score.py:127`,
`rollup.py:40`, `management.py:70` temporarily switched from `capability_weights` to
`harvested_raw_fit`, then the isolation test re-run:
```
tests/test_raw_fit_isolation.py::test_raw_fit_mutation_cannot_change_score  FAILED
AssertionError: scoring changed under harvested_raw_fit mutation 'zeroed'   (line 55)
1 failed
```
Then `git checkout -- backend/app/engine/{score,rollup,management}.py`; `grep harvested_raw_fit
backend/app/engine/` → clean. The guard detects the prohibited consumer. **No scorer behaviour
was changed in the committed tree** — the engine diff vs base is empty.

Constraints honoured: `harvested_raw_fit` not removed/renamed; no weight changed; no
re-normalisation; **no validator ERROR/WARN code added** (the dispatch prefers a regression
test and forbids an unspecified code); scorer behaviour unchanged.

---

## 6. Required test evidence (dispatch list) & full verification

| # | Requirement | Result |
|---|---|---|
| 1 | Provenance problem shown on base | §2 RA-001 — source JSON has no FTE column |
| 2 | Each FTE individually justified or in TODO inventory | §4 — all three marked, per-value rationale |
| 3 | Old/new TODO counts reconciled | §4 — 30 → 33, Δ is the 3 FTE, itemised |
| 4 | Regression test: raw_fit mutation cannot change scoring | §5 test 1 — PASS |
| 5 | Guard fails if scorer switched to raw_fit | §5 falsification — FAILED as required, reverted |
| 6 | Riverside 0 errors / 0 warnings | text exit 0; JSON 0 findings |
| 7 | Harvest read-back 43/43 | `43/43 matched` |
| 8 | 1.2 validator fixtures green | `check_fixture_matrix.py` exit 0 |
| 9 | 1.4 scoring tests green | `pytest` 13 passed (11 prior incl. `test_engine_scoring` + 2 new) |
| 10 | No casepack-identity branching introduced | engine+casepack grep zero; I touched no engine/casepack/seed code (diff empty); new test uses `load_scenario("riverside_r3")` exactly as the existing 1.4 pin test |
| 11 | Text/JSON parity intact | both 0 findings on Riverside; matrix I5 green |
| 12 | `git diff --check` | clean |

---

## 7. Deviations, substitutions, extensions

- **Extension (declared): `preferences/services.yaml` and `PROVENANCE.md §10.3` updated**, not
  only `PROVENANCE.md §7`. Dispatch A explicitly authorises updating services.yaml provenance
  "if its conclusions depend on those FTE estimates" — the `it` view does. Behaviour-neutral
  prose.
- **Substitution (declared): RA-002 fixed by a regression test, not a validator/schema guard.**
  The audit's Required-rework text floats "a validator or schema-level guard"; the dispatch's
  authorized rework B narrows this to "prefer a regression test over new runtime behaviour" and
  forbids "a new validator ERROR/WARN code without a settled specification." I followed the
  dispatch: the test is the executable guard. No new code path, no new severity.
- **No numeric FTE change.** The dispatch forbids it absent a verified source; the source has
  no FTE column, so all three stay as authored and are marked instead.
- No unresolved questions. No STOP condition triggered.

## 8. Safety confirmations
- **No scoring behaviour changed.** Engine diff vs `dad0989` is empty; the falsification patch
  was reverted; committed changes are 3 pack docs/data files + 1 test.
- **Nothing pushed, merged, deployed, or migrated.** `origin/build/1.3-harvest-rework` does not
  exist. Headless content/provenance change; no runtime artifact or schema.
- **main not modified** (`dad0989`); the active 1.4 worktrees (`da4e7a7`) not touched.

## 9. Note to the dispatcher — 1.4 cleanliness (asked mid-task)
Not a verdict (Builder ≠ Auditor; I only read the strategy-consuming slices). On the RA-002
dimension specifically, 1.4 is correct today: `harvested_raw_fit` is consumed by nothing, the
scorer reads `capability_weights`, and the deferred `policy_switch_alignment` hook raises
`NotImplementedError` by design. 1.4's own tests pass here. A full 1.4 verdict needs an
independent auditor with fresh context.

## 12. Commit
Implementation + this DoD committed to `build/1.3-harvest-rework`. Final commit SHA recorded in
the branch log. Worktree left clean; nothing pushed — awaits independent re-audit before merge.
