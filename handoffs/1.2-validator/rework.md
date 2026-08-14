# 1.2 — Rework Instruction

**Drafted by:** the AUTHOR of spec v1.2 · **Date:** 2026-08-14
**Branch:** `build/1.2-validator` @ `b02f8ef` · **Spec:** v1.2 @ `main` `3e709a3`
**Audit:** `findings/1.2-2026-08-14-audit.md` — substance PASS WITH FINDINGS · spec FAIL ·
process PASS · **0 blocking**

---

## Read this before reading the audit

**The build was sound. The spec was not.** Ten of the nineteen findings are against the
spec, and they have already been answered in **v1.2** — that document is your input, not the
audit. The audit is the *reason* v1.2 exists.

**Scale check.** Nineteen findings is not nineteen tasks:

```
10  against the SPEC     answered in v1.2. Seven of them now need CODE. ← your work
 3  against the BUILD    1.2-005 · 1.2-006 · 1.2-015                    ← your work
 4  against 1.1          1.2-008 · 011 · 012 · 013   NOT YOURS. Do not touch the pack.
 1  rulings (1.2-016)    four ratified, one rewritten. Mostly confirmations
 1  question (1.2-019)   I8 has no fixture. Accepted. No action
```

**Who reworks, per `handoffs/README.md` — by cause, not severity.** Nothing here came from a
compromised mental model. You followed a spec that contradicted itself in four places, and
where it did, the auditor ruled you followed the more defensible reading three times out of
four. This is the **same builder**, resumed. The reworked branch still returns to a **fresh
auditor** before merge.

**`R1` — what the spec change invalidates.** v1.2 changes §3, §5.1, §5.2, §5.3, §5.4, §5.5,
§6, §7 row 2, §9 and §9.1. In build-step terms it invalidates **steps 1–5**, i.e. all of
them, but only in part: nothing built is discarded. Record this in `dod.md` per R1.

---

## 1. Author rulings you need and do not have

Settled here so you do not stop on them.

| # | Question | Ruling |
|---|---|---|
| 1 | **`E14`'s tolerance** — §5.1 says *"beyond a stated tolerance"* and does not state one | **Zero.** Capital figures are authored integers in minor-unit-free currency; a derived figure and an authored one either match or they do not. No epsilon. If a future field is genuinely fractional, that field states its own tolerance and this ruling is revisited |
| 2 | **`E13`'s scope** — which references inside `initial_state` must resolve | Every key that **names a pack object**: `declared_strategy` → `strategies` · any capability key under `value_chain_coverage`, `unit_responses[].contributing` and `needs_attention` → `capabilities` · any catalog key → `catalog` · `review.lines[].area` → the seven decision areas. A *value* (a number, a label string) is not a reference and is out of scope |
| 3 | **Does `E13` or `E14` fire on a missing `initial_state`?** | **Neither.** `initial_state` is optional; a pack without one is a pack a section has not started. Absence is not a defect. Only what is present must resolve |
| 4 | **Where does `E12` point when a capability is also `E20`?** | **Both fire, and that is correct, not a duplicate.** `E12` names the illegal rule at its own line in `watch_rules.yaml`; `E20` names the capability left unwatched. They have different fixes and different owners. Riverside demonstrates the distinction — see §9.1 |

---

## 2. Build tasks — from spec v1.2

Each names the finding it closes. Verify against v1.2's text, not against this summary.

### 2.1 New codes

| Code | What | Fixture |
|---|---|---|
| `E12` | A watch rule with neither `warn_above` nor `critical_above`. §3 decision 7 | `broken_E12` |
| `E13` | A reference inside `initial_state` resolving to nothing. Ruling 2 above | `broken_E13` |
| `E14` | An authored `initial_state` figure contradicting one derived from the same pack. Ruling 1 above | `broken_E14` |

`E13`'s and `E14`'s fixtures should be derived from `minimal_valid` by mutation — the
auditor already demonstrated the shape (`1.2-014`), and reproducing it is the cheapest route
to a fixture that is minimally broken.

### 2.2 `E20`'s predicate widens — `1.2-001`

From *"appears in no watch rule"* to *"has no watch rule carrying at least one threshold."*
`broken_E20`'s fixture must now cover **both** arms: a capability with no rule, and a
capability watched only by a thresholdless one. The second arm is the one that was missing
and the reason the check under-reported on real content.

### 2.3 Output shape — `1.2-007`, `1.2-009`, `1.2-010`

Rebuild `render_text` to §5.4 of v1.2:

- **The business name leads the locator line.** The field path moves below the fix. It is
  kept, not deleted — it is genuinely useful to whoever opens the YAML; it is simply not
  what an instructor reads first.
- **The code is shown** (`ERROR  E02  …`). 5.6's UI and every finding ID depend on it.
- **`Fix:` prints at every severity.** §3 decision 3 binds WARN and INFO too. The fix was
  already being constructed and already emitted under `--json`; the human renderer was
  dropping it. This is a renderer change, not a message change.

### 2.4 `--json` parity in directory mode — `1.2-005`, and I5 as rewritten

Single-pack mode is clean. Directory mode drops pack attribution and reorders relative to
the text renderer, which breaks §3.1's one-producer-two-renderers guarantee **in exactly the
mode 5.6 consumes.** Both renderers must emit the same findings in the same order, with the
pack identified in every JSON record.

### 2.5 `ARCHETYPES` relocates — §3 decision 9

To `checks.py`, beside `ACTION_TYPES`. Your sourcing was verified correct by the auditor
against `design/05 §1.4.1`; only its home changes. It is schema vocabulary, and 1.4/1.5 will
want it.

### 2.6 `I1` and `I5` checks rewritten — `1.2-017`

`I1` now compares the **implemented** code set against the codes §5.1–§5.3 **name**, as set
equality. The old check counted two things read from the same file, so adding a code
incremented both sides and it could never fail. Note that under the new check the two
inherited codes `I3`/`I8` and the ratified `E00` are all *named* by v1.2, so a correct
implementation is set-equal, not merely a superset.

### 2.7 `O2`'s message — `1.2-006`

The cross-pack `pack_key` collision reuses `E10`'s wording and tells the reader to remove a
duplicate key within a collection, which is the wrong instruction for two packs colliding in
a registry. Give it its own message and fix.

### 2.8 `dod.md` §3's verbatim block — `1.2-015`

The block headed *"Verbatim per-code output"* is reformatted: it adds a code column the CLI
does not print and drops the header, the ✓ lines and the `Fix:` line. Regenerate it by
pasting actual output. `dod.md:6` sets this standard for its own contents; it is the one
place the report did not meet it.

---

## 3. What you must NOT do

- **Do not touch `backend/packs/`.** Findings `1.2-008`, `011`, `012`, `013` are against 1.1
  and belong to 1.3. Riverside is still expected to **fail**. `git diff` on that directory
  must stay empty, and the auditor will check it again.
- **Do not implement a legal form for presence-style watch rules.** `sec_identity_01` and
  `wh_rollout_01` are now illegal and have no legal shape. **1.5 owns that schema answer**
  (§5.2). They must emit `E12`. Do not invent a `metric_kind`, a `fires_on_presence` flag, or
  any equivalent.
- **Do not add the `WatchRule` constraint to `models.py`.** It belongs there eventually —
  it is filed against **1.1** — but 1.2 detects and does not repair, and adding it would make
  Riverside unloadable, which would take the validator's own evidence with it.
- **Do not add checks for `CG-3`, `CG-4` or `CG-5`.** They are structurally invisible until
  1.1 gives them schema sections. v1.2 §9.1 records the silence deliberately.

---

## 4. Definition of Done

The v1.2 DoD table in §9, in full, plus:

| Item | Evidence required |
|---|---|
| `E12`, `E13`, `E14` implemented, each with a fixture | pasted output, each firing alone |
| `E20` fires on both arms | a fixture per arm |
| §5.4 shape, `Fix:` at every severity | pasted output showing a WARN with its fix |
| Directory-mode `--json` parity | text and JSON tuple sequences diffed, identical |
| `ARCHETYPES` in `checks.py` | `grep -n` in both files |
| `I1` set-equality, `I5` widened | both re-run, both pass, and **state what each would now catch that it could not before** |
| `O2` message distinct from `E10` | both pasted |
| `dod.md` §3 regenerated verbatim | the block, unedited |
| Riverside matches v1.2 §9.1 exactly | full output, every error traced to a CG or reported as a new finding against 1.1 |
| `check_fixture_matrix.py` green | pasted, including the three new codes |
| **`R1` note** naming which build steps v1.2 invalidated | in `dod.md` |

**Declare every substitution.** `1.2-004` survived because a correct engineering substitution
was made silently — the check as written could not fail, you ran one that could, and the
vacuous row lived to reach the audit. If you run something other than what the spec says,
say so and say why.

**Stop and report** on anything v1.2 and this document do not settle. Four of your five
judgement calls last cycle were ruled correct, and none was silent — that is the standard;
the two the auditor flagged (`1.2-004`, `1.2-009`) were the ones recorded as notes rather
than surfaced as conflicts.
