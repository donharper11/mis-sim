# 1.2 — Validator Rework · Definition of Done

**Rework packet:** `handoffs/rework/1.2-validator-audit-2026-08-21.md`
(findings `1.2-RA-001`, `1.2-RA-002`, `1.2-RA-003`)
**Branch:** `build/1.2-validator-rework`
**Base:** `main` @ `d7c6000caaa284740abf1e646d74459dbfedb68c` ("Merge 1.1 policy-order rework")
**Worktree:** `…/scratchpad/wt-1.2-validator`
**Builder:** RE-BUILDER agent · **Date:** 2026-08-21 · **Spec:** v1.3 → **v1.4**
**Final commit:** see §8.

> Builder ≠ Auditor (`GOVERNANCE §6`). This is the builder's evidence, not an audit verdict.
> The branch goes to an independent audit before any merge.

---

## 0. Headline

The 29-row matrix passed and Riverside was clean, but three shipped domains were outside the
validator's reach. All three are now covered, with paired valid/broken fixtures proving each
new code is silent on a correct pack and fires on a broken one, and demonstrated **red on the
pre-rework validator, green after** (§4). Riverside stays `0 errors · 0 warnings`; text and
JSON stay identical in every mode.

```
1.2-RA-001  obligation_rules references never validated   → E24..E28  (typed)   CLOSED
1.2-RA-002  W01 blind to policies/services preference shapes → W01 generalised   CLOSED
1.2-RA-003  policy-vocab errors imprecise / collapse to E00 → E15..E17 (raw)     CLOSED
```

Eight new codes (`E15`–`E17`, `E24`–`E28`), eleven new fixtures, one W01 rewrite. **No engine
scoring code, no model change, no pack repaired** — 1.2 detects, it does not repair (spec §1).

---

## 1. Pre-flight & finding verification (claims verified, not inherited)

| Check | Result |
|---|---|
| Base = current main `d7c6000` | **Yes** — `git rev-parse main` = `d7c6000…`. (The rework header says it audited `174e980`; `d7c6000` is that plus the merged 1.1 policy-order rework, which is the dispatch's named base.) |
| Baseline: fixture matrix + Riverside on the base | `check_fixture_matrix.py` exit 0 (29 fixtures); Riverside `0 errors · 0 warnings · exit 0` |
| `1.2-RA-001` — obligations unvalidated | **Confirmed.** `grep -n obligation backend/app/casepack/validate.py backend/app/casepack/checks.py` → zero hits. `loader.py:27,89` loads `obligation_rules.yaml`; nothing read it |
| `1.2-RA-002` — W01 reads one legacy shape | **Confirmed.** `check_placeholder_preferences` read only `defaults_by_archetype` values + `overrides`, counting rows with `ideal_value`. `preferences/policies.yaml` nests `by_decision.<key>.ideal_posture`; `services.yaml` uses `ideal_tier`. Neither seen |
| `1.2-RA-003` — vocab imprecise, collapses to E00 | **Confirmed.** Model only enforces `default ∈ options` (`models.py` `default_is_a_declared_option`), raising `CasepackLoadError` → the `validate_pack_dir` except-branch appends a single `E00`. No check for empty/dup/non-snake options or `permissive_value` resolution |

No STOP condition: the base matched the dispatch, all three findings reproduced, and every
change stayed within "detect, don't repair."

---

## 2. What changed

### 2.1 `1.2-RA-001` — obligation references (E24–E28), typed stage
`check_obligation_references(lens)` added to `validate()`. For each `pack.obligation_rules`
rule: `E24` policy exists · `E25` entity exists · `E26` `permissive_value` is a **declared
option** of that policy (only when the policy resolves and declares options — a legacy policy
with no options has no vocabulary to check) · `E27` `cleared_by` actions ∈ `ACTION_TYPES`
(same set as E05) · `E28` armed events exist. `obligation_rules.yaml` is optional; a pack
without it has `pack.obligation_rules == []` and the loop does not run.

### 2.2 `1.2-RA-002` — W01 generalised
`check_placeholder_preferences` rewritten to walk each domain by semantic fields via
`_preference_rows`: a *row* is any mapping carrying `ideal_value`, `ideal_posture` or
`ideal_tier`, and its weight is the `weight` in that same mapping (not the archetype-level
aggregate). Signature `(ideal_field, ideal, weight)`; N still bound to 6. Now fires on all
five preference domains, not one.

### 2.3 `1.2-RA-003` — policy value vocabulary (E15–E17), raw stage
`check_policy_vocab(raw, source)` added to `validate_pack_dir` **before** the pydantic load
(like `check_weights_raw`/`check_demand_raw`): `E15` an option/default that is empty or not
snake_case · `E16` a duplicated option · `E17` a `default` outside its `options`, mirroring
`models.py` exactly. Because `E17` fires at raw stage, the model-load failure it corresponds
to no longer collapses into a lone `E00` — the precise code appears and **co-reports** with
the other raw checks. `E15`/`E16` are the validator's only line on malformed vocabularies,
which the model (a plain `list[str]`) never checked.

### 2.4 Catalogue, spec, docs, matrix
`validate_messages.yaml`: 8 codes (business-language subject/message/fix), W01 message
generalised (`ideal_value` → `ideal`). `spec.md`: header ranges `E00`–`E17` / `E20`–`E28`,
§5.1/§5.2 code lines + rationale blocks, §5.3 W01 note, §10 v1.4 changelog, version bump.
`docs/casepack-schema.md`: the `permissive_value` "validator does not yet check this" line
corrected — it now names `E24`–`E28`. `check_fixture_matrix.py`: 11 MATRIX rows.

---

## 3. Verification — full matrix (after)

```
all 40 fixtures behave as named; 36 of 37 codes exercised, ['I8'] recorded as unfixturable
I1  implemented codes : 37    I1  spec-named codes : 37    I1  set equality : PASS
I5  minimal_valid / warn_heuristics / riverside / packs(dir)  — text==json, identical=yes
I5  directory-mode pack attribution — every record names its pack
EXIT=0
```

New fixture rows (all PASS):
```
broken_E15  +[E15]                broken_E24  +[E24]        ok_obligations_valid  +[-] -[*] (clean)
broken_E16  +[E16]                broken_E25  +[E25]        warn_W01_by_decision  +[W01]
broken_E17  +[E17] -[E00]         broken_E26  +[E26]
broken_policy_aggregate +[E03,E17] -[E00]   broken_E27 +[E27]   broken_E28 +[E28]
```

`broken_E17` forbids `E00` (the collapse is gone). `broken_policy_aggregate` proves the
aggregate-diagnostics requirement: a bad policy default **and** an independent weight error
both surface (`E17` + `E03`), not a lone `E00`.

Other gates: Riverside `exit 0` (0/0) · `compileall` ok · 1.2 I4 (no pack-identity branching
in `validate*`) zero hits · 1.1 I2 (no displayed English in `casepack/*.py`) zero hits ·
`git diff --check` clean.

---

## 4. Acceptance: red-on-base / green-at-tip

The rework's acceptance requires each new fixture to behave differently on the pre-rework
validator. New fixtures run under the base (`d7c6000`) validator, unchanged:

```
fixture                     PRE-REWORK (d7c6000)      AFTER REWORK
broken_E15                  exit 0, clean          →  E15
broken_E16                  exit 0, clean          →  E16
broken_E24..E28             exit 0, clean (×5)     →  E24 / E25 / E26 / E27 / E28
broken_E17                  E00 (opaque collapse)  →  E17 (precise, no E00)
broken_policy_aggregate     E03 only (default hidden) → E03 + E17
warn_W01_by_decision        exit 0, no W01         →  W01
ok_obligations_valid        exit 0 (clean on both) →  exit 0
```

Six broken packs validated **clean** on the base — the silent gaps `1.2-RA-001`/`RA-003`
described; `E17`'s default collapsed to `E00`; the aggregate pack hid its bad default
entirely; and W01 was blind to `by_decision`. Every one behaves as named after the rework,
while the valid pack stays clean on both.

---

## 5. Business-language rendering (spec §5.4, `GOVERNANCE §2.1`)

Every new code leads its locator with the business subject, carries a `Fix:` line, and puts
the field path below. Samples:

```
ERROR  E26  Obligation client_pii_retention  obligation_rules.yaml:4
       Says the permissive position is 'forever', which is not one of policy
       'client_record_retention' options indefinite, standard_period, minimal. It would
       watch for a switch position that cannot occur, so it can never open.
       Fix: in obligation_rules.yaml, set permissive_value to one of ...
WARN   W01  Policies preferences            preferences/policies.yaml:5
       6 rows carry the same ideal indefinite and the same weight 0.5, which looks like
       placeholder seeding rather than authored judgement.
       Fix: vary the ideal and weight per stakeholder ...
```

All copy lives in `validate_messages.yaml`; the `.py` files name no displayed English
(1.1 I2, verified).

---

## 6. Scope & boundaries (declared)

- **Typed vs raw split.** Obligation checks (E24–E28) are typed: they need the loaded pack
  and are skipped if the pack cannot load. Policy-vocab checks (E15–E17) are raw so they
  survive a model-load failure. "One invalid policy default must not hide independent errors
  elsewhere" is satisfied for every raw-stage check (E03/E04/E10/E11/E15/E16 co-report with
  E17); fully running the *typed* stage on an unloadable pack would need a model change, which
  is 1.1's and out of scope (spec §1; `GOVERNANCE §7`). The aggregate fixture demonstrates the
  co-reporting that this architecture makes possible.
- **`arms` events (E28) included.** RA-001's evidence named entity/policy/action; the Required
  rework said "all obligation references." A dangling `arms` reaches downstream event work
  (RA-001's stated harm), so it is validated too — no new rule invented, same class as E06.
- **No new schema field, identifier, or validation rule beyond the audit's enumerated
  concerns.** `ACTION_TYPES` reused for E27; `PolicyOption.options` semantics taken from
  `CONTRACTS.md`. Nothing in `models.py`, `loader.py`, or any pack was changed.

## 7. Isolation & safety

- **Main not modified.** `main` HEAD is `d7c6000`; working tree shows only pre-existing
  untracked files (`.claude/`, `findings/1.1-…`, `handoffs/rework/`).
- **1.4 not disturbed.** `build/1.4-scoring` and its worktrees stay at `da4e7a7`; I only ran
  read-only inspection of shared files earlier in the session, none this task. My changes
  touch `backend/app/casepack/` + tests + spec/docs; the 1.4 engine lives in
  `backend/app/engine/` — disjoint.
- **Nothing pushed / merged / deployed / migrated.** Headless CLI change; no runtime artifact
  or schema.

## 8. Commit

Implementation + fixtures + this DoD committed to `build/1.2-validator-rework`. The scaffold
that generated the fixtures is kept under the session scratchpad (`build_fixtures.py`), not in
the repo. Worktree left clean; nothing pushed — awaits independent re-audit before merge.

---

## 9. Audit closeout — findings `1.2-VR-001` / `1.2-VR-002`

Independent audit (`findings/1.2-validator-rework-2026-08-21-audit.md`) returned **PASS WITH
FINDINGS**, two mechanical corrections, same-builder authorised. Both reproduced against the
audited tip `b7f0420` and fixed.

### `1.2-VR-001` — E26 skipped a policy with no options
`check_obligation_references` only emitted `E26` when `policy.options` was non-empty, so an
obligation whose referenced policy declares **no** options validated clean — the
`permissive_value` pointed at no declared state, the exact dangling reference E26 exists to
prevent. Fixed: E26 now fires whenever the policy resolves — a no-options policy uses the
`E26_no_options` variant ("policy declares no options at all…"); a non-empty options list uses
the existing not-a-member message. Backward-compatible: a policy with no options and **no**
obligation referencing it is untouched (the loop only runs over declared obligations).

### `1.2-VR-002` — E15 reported a malformed default as an option, wrong field
`check_policy_vocab` appended malformed options and a malformed default to one list and always
emitted `field: <policy>.options` with the option message. A `default: 42` therefore read
"Lists an option '42' … remove it from options", sending an author to the wrong field. Fixed:
options and default are checked separately; a malformed default emits the `E15_default`
variant against `field: <policy>.default` with a default-specific message and fix. `E17` is
now guarded to a **well-formed** default not among options, so the two never both fire on one
default.

### Reproduced on the audited tip, fixed at the new tip
```
                        b7f0420 (audited)                     new tip
broken_E26_no_options   exit 0, clean (E26 skipped)        →  E26 (no_options variant)
broken_E15_default      E15, field ...options (WRONG)      →  E15, field ...default
```

### New guards
- Fixtures `broken_E26_no_options` and `broken_E15_default` added to the matrix (both raise
  their code, exit 1).
- `check_field_locators()` added to `check_fixture_matrix.py`: asserts the JSON `field` of
  `broken_E15` ends `.options`, `broken_E15_default` ends `.default`, and both E26 fixtures
  end `.permissive_value` — VR-002's "assert the rendered field, not only the code".

### Post-fix verification (new tip)
```
check_fixture_matrix.py → EXIT=0   (42 fixtures; field-locators all PASS; I1 37/37 set-equal;
                                     I5 text==json in single-pack and directory mode)
Riverside               → 0 errors · 0 warnings · exit 0
compileall              → ok
```
Files changed by this closeout: `backend/app/casepack/validate.py`,
`backend/app/casepack/validate_messages.yaml`, `backend/tests/check_fixture_matrix.py`,
`handoffs/1.2-validator/spec.md`, and two new fixture packs. No new code; two catalogue
variants; the code list and `I1` are unchanged. Branch returned clean for a short independent
re-audit; still nothing pushed or merged.
