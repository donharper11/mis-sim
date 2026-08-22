# DoD — 1.2 findings packet CU-001 / CU-002 / CU-003

**Builder:** integration agent · **Date:** 2026-08-22 · **Branch:** `build/1.2-e00-and-variants`
**Base:** `main` at `24e62fb` · **Spec:** 1.2 v1.6

Closes three findings on the `findings/OPEN-REGISTER.md` register, all owned by 1.2. This
branch requires an independent audit before merge (README audit gate). Nothing merged to
`main` by this builder.

---

## CU-001 (Functional) — the E00 collapse class

**Claim (verified):** A `Literal`/`StrEnum` field set out of range makes `models.py` refuse
the whole pack, which reached the instructor as a bare `E00 "unreadable pack"` naming no
field. `B7`/`E29` fixed this for precondition `placement`/`severity` only; five other closed
vocabularies still collapsed. Reproduced before the fix: `entities.sensitivity` and
`stakeholders.stakeholder_type` each returned `codes=['E00']`.

**Fix:** new code **`E18`**. `loader.py` now attaches the full `ValidationError` to
`CasepackLoadError`; `validate.check_closed_vocab_load` reads pydantic's own error report on
the load-failure path and emits one targeted `E18` per `enum`/`literal_error`, naming file,
field (resolved to the row key), bad value and allowed set. It closes the **class**, not five
instances: nested (`provenance.source`) and future closed fields are covered automatically,
and no vocabulary is restated (`allowed` comes off the model). Defers to `E29_vocab` for
precondition fields so nothing double-reports.

| Evidence | Result |
|---|---|
| Five vocabularies now targeted | `sensitivity`, `stakeholder_type`, `rgt_tag`, `metric_kind`, `provenance.source` each → `E18`, field resolved to the row key, zero `E00` |
| Two bad values co-report | both surface as `E18`; neither masks the other |
| `broken_E18` fixture | raises `E18`, forbids `E00`, exit 1 — passes matrix |
| Riverside unaffected | `0 errors · 0 warnings · exit 0` |

## CU-002 (Data) — I1 blind to E29 variants

**Claim (verified):** `I1` compares `catalogue()["codes"]` only; variants live under
`catalogue()["variants"]` and were invisible, so `E29_vocab` (E29's fourth behaviour) shipped
with no spec change and `I1` stayed set-equal.

**Fix:** (1) spec §5.2 and `docs/casepack-schema.md` now enumerate all four E29 behaviours;
(2) new invariant **`I1v`** in `check_fixture_matrix.py` holds `catalogue()["variants"]`
set-equal against a **variant register** the spec owns (§6). A new variant now fails the
matrix until the spec names it.

| Evidence | Result |
|---|---|
| `I1v` set equality | implemented `{E10_pack_key, E15_default, E26_no_options, E29_vocab}` = spec-named, PASS |
| Four E29 behaviours documented | spec §5.2 + schema guide |

## CU-003 (Data) — B5 label routing had no guard

**Claim (verified):** reverting either half of B5 (the `Lens.label` routing, the E07 `misc`
narrowing) still passed the whole suite.

**Fix:** `tests/test_label_routing.py`, two guards:
- routing: `broken_E20`'s E20 subject must be the authored label `Clinical Records`, not the
  key `clinical_records`. Mutation-checked: monkeypatching `Lens.label` to return the key
  flips the subject and fails the guard.
- narrowing: a `role_key` re-homed from `misc` to another section must still raise `E07`;
  baseline `minimal_valid` is E07-clean (non-vacuous).

---

## Verification ladder

| Rung | Result |
|---|---|
| `pytest` | **37 passed** (was 35; +2 label-routing) |
| `check_fixture_matrix.py` | exit 0 — **44 fixtures**, 38/39 codes exercised, I1 **39=39**, I1v **4=4**, I5 identical |
| `check_event_preconditions.py` | exit 0 |
| `check_policy_options.py` | exit 0 (13/13) |
| `check_w08_rounds.py` | exit 0 |
| I4 canary (`grep -niE riverside\|grocer validate*`) | clean |
| `git diff --check` | clean |
| Scope | validator + tests + fixture + spec + schema doc only; no engine files touched |
