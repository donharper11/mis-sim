# 1.4 Closeout — Builder Report (information-policy dimension)

**Builder:** Claude (opus-4-8) · **Date:** 2026-08-21
**Branch:** `build/1.4-closeout` (cut from `main` at `34238f4`) · **Governing spec:** `closeout-spec.md`
**Verdict authority:** none — a builder does not declare audit approval. Independent audit is required before merge.

> Closes the deliberately paused information-policy path of the merged 1.4 core without
> reopening it. Two firm-wide Management sub-factors added; Tech and Org untouched.

---

## 1. Files changed

**Engine / seed (product code):**

| File | Change |
|---|---|
| `backend/app/engine/state.py` | NEW frozen `PolicyDecisionState`; NEW `TeamState.policy_decisions` field (default `()`) |
| `backend/app/engine/management.py` | Removed the deferred `*args/**kwargs` hook; added `_resolve_policy_decisions`, `_asymmetric_alignment`, `policy_switch_alignment(pack,state)`, `policy_discipline(pack,state)`, `POLICY_DISCIPLINE_FLOOR`; extended `FirmManagement` with `policy_alignment`/`policy_discipline`; wired both into `firm_management` and every capability's `management()` sub-factor map + evidence |
| `backend/app/casepack/models.py` | Docstring only — corrected the now-false "today it raises NotImplementedError" clause on `PolicyOption.options` (see Deviations) |
| `backend/seeds/riverside_r3.py` | NEW `_policy_decisions()` (six attentive decisions at authored defaults); wired into `build_team_state()` |
| `backend/app/seed/demo.py` | `_describe` prints the policy-decision count (seed-in-the-loop visibility) |

**Tests:**

| File | Change |
|---|---|
| `backend/tests/test_policy_dimension.py` | NEW — 18 focused tests (formula C2–C4, aggregation/null/discipline, C5/C6/C11/C12, six negative cases) |
| `backend/tests/test_engine_scoring.py` | Pin test updated to the new computed Mgmt/realised (exact 1e-6); added an attentive-team assertion |

**Living documents:**

| File | Change |
|---|---|
| `handoffs/1.4-scoring-engine/spec.md` | Header note; §5.3 formula + table; NEW §5.3a; §5.7 pin + history; DoD row; Changelog |
| `handoffs/1.4-scoring-engine/dod.md` | Appended a Closeout section (historical audit evidence untouched) |
| `design/02-traceability-matrix.md` | Data currency/freshness → deferred; `strategic_alignment` "dot product" → "cosine similarity"; two new policy rows |
| `findings/OPEN-REGISTER.md` | F4 + E2 closed; G2 marked an explicit named deferral |
| `CONTRACTS.md` | NEW `TeamState.policy_decisions[]` / `PolicyDecisionState` entry; `PolicyOption.options` consumer moved prospective → live; header date |

Tracked diff: **11 files, +458/−56**; plus one new test file. No other files touched.

---

## 2. Source → consumer trace for every new field

| New field | Produced by (this packet) | Producer at runtime (future) | Consumed by | Feeds |
|---|---|---|---|---|
| `PolicyDecisionState.policy` | seed `_policy_decisions()` | 1.6/2.x runtime table (`instance_id`) | `_resolve_policy_decisions`, `policy_switch_alignment`, `policy_discipline` | resolves to a `PolicyOption`; team option index |
| `PolicyDecisionState.selected` | seed (authored default) | 1.6/2.x | same | `options.index(selected)` → asymmetric distance |
| `PolicyDecisionState.actively_decided` | seed (`True` ×6) | 1.6/2.x | `policy_discipline` | `|decided|/|eligible|` ratio |
| `TeamState.policy_decisions` | seed → `build_team_state()` | 1.6/2.x snapshot | both policy helpers | the two Management sub-factors |
| `FirmManagement.policy_alignment` | `firm_management` | — (computed) | `management()` sub-factor map (every capability) | Mgmt geomean |
| `FirmManagement.policy_discipline` | `firm_management` | — (computed) | `management()` sub-factor map (every capability) | Mgmt geomean |

Casepack inputs read: `policies[].{key,options,default}`, `stakeholders[].{key,archetype}`,
`preferences["policies"].defaults_by_archetype.<archetype>.{weight, by_decision.<policy>.{ideal_posture,weight}}`.
No new casepack fields; no casepack content changed.

---

## 3. Formulas implemented (frozen, closeout §3)

**Asymmetric ordinal alignment** — for options length `n`, `span = n-1`, team index `t`, ideal index `i`:

```
t == i → 1.0
t <  i → clamp(1 − (i − t)/span)          # too permissive: full distance
t >  i → clamp(1 − 0.5·(t − i)/span)      # stricter: half distance
```

**Aggregation** — weighted arithmetic mean over every actual stakeholder's `by_decision`
rows: `effective_weight = archetype.weight × by_decision[policy].weight`;
`policy_alignment = Σ(alignment·w)/Σ(w)`; empty → `1.0`, `preferences: 0`.

**Discipline** — `1.0` if no policy declares options, else
`0.25 + 0.75·(|actively_decided ∩ eligible| / |eligible|)`, `eligible` = policies with options.

**Management** — `geomean(governance, strategic_alignment, portfolio_discipline,
signal_responsiveness, follow_through, stakeholder_alignment, policy_alignment,
policy_discipline)`. The first six are unchanged.

---

## 4. Pre-flight evidence (all 10 reported before code)

| # | Result | Note |
|---|---|---|
| 1 | PASS | ordinal contract (`e2492d0`,`595a13b`) + validator rework (`b7f0420`,`443751f`) present |
| 2 | PASS | Riverside validates `0 errors · 0 warnings · exit 0` |
| 3 | PASS | deferred hook definition/comments only; no scoring call site |
| 4 | PASS | no `policy_decisions`/`PolicyDecisionState` anywhere pre-build |
| 5 | PASS | `check_policy_options.py` — all 13 checks pass; six switches |
| 6 | PASS | `by_decision` + `ideal_posture` present in preferences |
| 7 | PASS | `test_engine_scoring.py` 9 passed before changes |
| 8 | PASS | no data-freshness producer (`freshness`/`platform_service.settings`) |
| 9 | PASS (`[A]`) | `test_raw_fit_isolation.py` present; 1.3 rework merged |
| 10 | PASS | `main` = `HEAD` = merge-base = `34238f4` before any code |

**Computed pins (recorded, not tuned — decision 11):** Tech `0.750008` · Org `0.507003` ·
Mgmt `0.656778` · realised `0.249744` · throttle `org` · firm_score `0.254585`.
Pre-closeout baselines: Mgmt `0.648006`, realised `0.246408` (Tech/Org identical).
`policy_alignment` `0.4676` over 36 preference rows (total weight `19.29`); `policy_discipline` `1.0`.

**Verification run:** full backend `pytest` **32 passed**; validator text and JSON (`[]`,
exit 0) clean; `check_fixture_matrix.py` 42 fixtures; `check_policy_options.py` 13/13;
`test_raw_fit_isolation.py` 2/2; `git diff --check` clean; C9/C10/I1/I2 greps clean.
Harvest read-back: no dedicated script exists; the loader+validator read the harvest-derived
pack cleanly and this packet touches **zero** `backend/harvest/**` files.

---

## 5. Deviations, unresolved contradictions, deferred work

**D1 — `models.py` docstring corrected (out of the §5.5 doc list).** Replacing the deferred
hook (authorised by §5.1) made the `PolicyOption.options` docstring's "today it raises
NotImplementedError and reads no policy value" factually false. I corrected that one clause
to name the live consumer, preserving the ordinal-contract tokens and avoiding
`check_policy_options.py`'s banned present-tense phrases. It is not in the spec's five-doc
list; flagged here rather than made silently.

**D2 — `check_policy_options.py` §6 last assertion is now semantically stale.** It asserts
"the 1.4 policy-distance consumer is PROSPECTIVE, not current." This packet lands that
consumer, so the intent is outdated. It still **passes mechanically**: the phrase it forbids
("reads ordinal distance", etc.) is absent, and the keyword "deferred" it requires still
holds true of the `PolicyDecisionState` **producer** (1.6/2.x) and the 1.2 validator check.
At build time I did not modify this merged guard (out of §5.5 scope) and flagged it. The
independent audit recorded it as **finding 1.4C-R01**; it has since been re-pointed — see §8.

**D3 — "unknown stakeholder archetype" raise (decision 9) not enforced.** Decision 9 lists
it as a `ValueError`, but decision 3 and the §5.3 table make an archetype with no policy row
an **exclusion**, and there is no archetype registry model to validate "unknown" against.
Per decision 4 ("STOP rather than invent"), I implemented the exclusion behaviour (tested)
and did **not** invent a registry to raise on. The other five negative cases in §5.3 all
raise as specified.

> **RESOLVED 2026-08-21 (re-audit finding 1.4-CR-001, spec-owner decision — see §9).** The
> exclusion rule is now the frozen contract: the raise requirement was removed from decision
> 9. A subsequent verification found the archetype-vocabulary owner already exists — validator
> **E08** — so the tension fully dissolves. This D3 text is retained as history; the current
> rule is §9.

**D4 — `overrides` for the policies domain not consumed.** `PreferenceDefaults.overrides` is
`list[dict[str, Any]]` with no per-domain schema; Riverside's is `[]`. Decision 4 forbids
inventing a second resolver, so the resolver reads `defaults_by_archetype` only. A non-empty
policies-domain overrides list is not silently ignored *and* not guessed — it simply has no
verified shape yet; when one is defined it returns as a follow-up. No behaviour change for
any current pack.

> **CORRECTED 2026-08-21 (re-audit finding 1.4-CR-002, spec-owner decision — see §9).** This
> disclosure was wrong on one point: the build **did** silently ignore a non-empty policies
> overrides list (the resolver never inspected `overrides`). The scorer now **raises** on a
> non-empty `preferences["policies"].overrides` before returning a score. This D4 text is
> retained as history; the current rule is §9.

**Deferred (named, not silent):**
- **Data currency/freshness (G2):** capture/storage → 3.4 Platform, production → 1.6,
  scoring consumption → a future 1.4 follow-up. `design/02` row marked deferred.
- **PolicyDecisionState runtime producer:** 1.6/2.x; the seed constructs the snapshot today.

No unresolved contradictions block the packet. The `C8` "byte-identical existing evidence"
note: the per-capability `stakeholder_alignment` evidence retains its
`policy_switch_dimension: "deferred"` marker unchanged — it still reads true of *that*
per-capability scalar, which deliberately excludes policy switches (now scored separately).

---

## 6. Confirmations

- **`main` untouched.** `main` is `34238f4` — identical to the branch base and unchanged; no
  commit, checkout, or edit touched it. Work is entirely on `build/1.4-closeout`.
- **Unrelated worktrees/files untouched.** The auditor-owned untracked files
  (`findings/1.1-…`, `findings/1.2-…`, `findings/1.3-…-rework-*.md`, `handoffs/rework/`,
  `.claude/`) are preserved and were never staged. Sibling worktrees
  (`build/1.4-scoring`, `build/1.1-policy-order-rework`, etc.) were not touched.
- **Nothing pushed, merged, deployed, activated, or migrated.** No `git push`, no merge, no
  deploy, no DB/migration (there is none — the engine is pure). At hand-off the branch holds
  the commit(s) below locally only.
- **No browser-visible behaviour changed.** This packet is a pure headless scorer: no UI,
  route, template, or served surface is added or altered (`git diff --stat` touches only
  engine/seed/test/doc files; nothing under a frontend or API path). The browser/desktop/
  mobile/zoom/keyboard/console/network checks are therefore **N-A**, proven by the diff scope.

---

## 7. Hand-off

Branch `build/1.4-closeout`, tip recorded at commit time. Independent audit required before
merge; the verification script for the auditor is `closeout-spec.md` §10. A builder does not
declare audit approval.

---

## 8. Post-audit finding dispositions (2026-08-21)

Independent audit `findings/1.4-closeout-2026-08-21-audit.md`: **PASS WITH FINDINGS,
mergeable** — no Blocking, no Functional. All three findings (Report/Data) applied by the
same builder as mechanical corrections; no engine logic changed, so the verified behaviour
and all pins are unchanged (full suite re-run **32 passed**, validator 0/0, both
ordinal-contract guards green).

| Finding | Sev | Disposition |
|---|---|---|
| 1.4C-R01 | Report | **Fixed.** `check_policy_options.py` §6 re-pointed to assert the consumer is **LIVE** (closeout landed), producer deferred — no longer the stale "PROSPECTIVE" claim. CONTRACTS canonical block updated (`scorer does not read it yet` → reads it, live; PROSPECTIVE tag dropped from that heading). |
| 1.4C-R02 | Report | **Fixed.** Test count corrected 24 → **18** in `closeout.md §1` and `dod.md`. |
| 1.4C-R03 | Data | **Fixed.** `spec.md §5.6` illustrative decomposition updated to the closeout pins (`mgmt 0.656778`, `realised 0.249744`) with the two new sub-factors shown and a note. |

A builder does not declare audit approval. These corrections are cosmetic (docs + one guard
assertion re-point); the merge decision, and whether the re-point warrants a confirming
re-audit, rest with the coordinator/user.

---

## 9. Contract corrections — CR-001, CR-002 (2026-08-21)

A second independent re-audit (`findings/1.4-closeout-2026-08-21-codex-reaudit.md`) confirmed
the arithmetic, seed pins and Riverside behaviour but blocked merge because two **input
contracts** (D3, D4) had been resolved without decision authority. The spec owner then froze
both. Applied here (no arithmetic, formula, aggregation, seed, or pin changed):

### 1.4-CR-001 — archetype absence is exclusion, never a raise

**One rule, now stated identically in code, tests, closeout-spec (decisions 3/4/9), CONTRACTS
and this doc:** a present archetype policy-preference row is scored; an absent row is
**excluded** from the alignment denominator — no neutral row, no weight — *regardless of why*.
The scorer does **not** classify absence as "known" vs "unknown"; the casepack **model** has no
archetype registry to classify against.

The contradictory decision-9 requirement to raise on an "unknown archetype" was **removed**.

**Verified upstream owner (not a claim — checked):** stakeholder-archetype vocabulary is
already validated by **E08** `check_archetypes` (`backend/app/casepack/validate.py:794`) against
the canonical 14-archetype set `ARCHETYPES` (`backend/app/casepack/checks.py:31`, whose own
comment reads *"1.4 and 1.5 will want it"*), fixture-tested by `broken_E08`
(`tests/check_fixture_matrix.py:60`, expects exactly one E08 error). The validator gate
(`GOVERNANCE.md §5`) runs before any pack is scored, so an off-vocabulary archetype cannot
reach the scorer. Archetype-vocabulary validation is therefore **already assigned** (E08) — no
new register item is needed for it.

**Regression test:** `test_absent_archetype_row_is_excluded_without_weight` — adds a stakeholder
with an off-vocabulary archetype and proves the score, `total_weight`, and evidence-row count
are all identical to baseline (excluded, no neutral row, no raise).

### 1.4-CR-002 — policy-domain overrides unsupported; non-empty raises

`preferences["policies"].overrides` has no defined shape or precedence contract.
`policy_switch_alignment` now **raises `ValueError` before returning a score** when that list
is non-empty, naming the policies domain and the undefined shape/precedence — it does not
parse, guess, partially apply, or silently ignore it (`management.py`, the CR-002 guard).
Empty (`[]`, as Riverside declares) scores normally; the verified `policy_alignment 0.4676`
stands.

**Named future owner:** `findings/OPEN-REGISTER.md` item **policy-preference overrides** —
typed shape, stakeholder/archetype targeting, replacement precedence, duplicate/conflict
handling, validator coverage, scorer consumption. Override support is **not implemented and
not complete**.

**Tests:** `test_negative_nonempty_policy_overrides_raise` (non-empty → raises);
`test_empty_policy_overrides_preserve_the_verified_score` (empty → 0.4676 unchanged).

### Verification of this correction

Full backend `pytest` **35 passed** (18→21 policy-dimension tests); validator text `0/0` and
JSON `[]`; `check_fixture_matrix.py` 42/42; `check_policy_options.py` 13/13; harvest read-back
43/43; `test_raw_fit_isolation.py` 2/2; seed demo + scorer CLI; `git diff --check` clean.
Exact frozen values all hold: Tech `0.750008`, Org `0.507003`, Mgmt `0.656778`, realised
`0.249744`, `policy_alignment 0.4676`, `policy_discipline 1.0`; the six existing Management
sub-factors are byte-identical. No passage in code, tests, closeout-spec, CONTRACTS, DoD,
this doc, or the register now says an absent archetype row must raise, that unknown archetypes
are distinguishable from uninterested ones by the scorer, that policy overrides are consumed,
or that a non-empty overrides list may be ignored.
