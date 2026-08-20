# 1.1 — Policy-Order Rework · Definition of Done

**Rework packet:** `handoffs/rework/1.1-schema-audit-2026-08-21.md`
(findings `1.1-RA-001`, `1.1-RA-002`)
**Branch:** `build/1.1-policy-order-rework`
**Base:** `main` @ `174e980ff9c922c1a0a8e4e96cc8ae505782f072` ("1.4 builder dispatch prompt")
**Worktree:** `/tmp/claude-1000/-home-ubuntu-projects-mis-sim/03aa0372-65fa-405f-b946-5b8168fbaa54/scratchpad/wt-1.1-policy-order`
**Builder:** RE-BUILDER agent · **Date:** 2026-08-21
**Final commit:** see §12 (filled at commit time)

> Builder ≠ Auditor (`GOVERNANCE §6`). This report is the builder's evidence, not an audit
> verdict. The corrected branch goes back through an independent audit before any merge.

---

## 0. Headline

The settled contract (`design/07 §3.5b`, ruled 2026-08-18) is that `PolicyOption.options` is
**ordinal**, least-constrained at index 0. Three authoring surfaces still asserted the
opposite ("order carries no meaning"): `models.py`, `docs/casepack-schema.md`, and — found
during verification — the Riverside pack's `PROVENANCE.md`. `CONTRACTS.md` had no entry at
all. This packet reconciles all four surfaces to the one ordinal rule and adds a focused
test proving the loader preserves order. **No engine behaviour changes** — the pack data was
already authored ordinal (the 1.3 follow-up on current main); only the documentation and
the cross-cutting contract were out of step.

```
1.1-RA-001  models.py docstring said the opposite ordering rule       FIXED (§2)
1.1-RA-002  no CONTRACTS.md entry for PolicyOption.options/.default    FIXED (§3)
+ found     docs + PROVENANCE.md carried the same wrong statement      FIXED (§4)
+ added     focused loader/schema tests for the ordinal contract       ADDED (§5)
```

Not in scope and **not touched**: scoring, policy-distance computation, validator expansion,
any 1.4 behaviour (see §9 stop-condition review).

---

## 1. Pre-flight — base, branch, worktree

| Check | Command | Result |
|---|---|---|
| Base SHA = report's stated main (`174e980`) | `git rev-parse main` | `174e980ff9c922c1a0a8e4e96cc8ae505782f072` — **matches the audit report exactly**; no material difference |
| Branch | `git branch --show-current` (in worktree) | `build/1.1-policy-order-rework`, cut from `174e980` |
| Worktree | `git worktree add` | `…/scratchpad/wt-1.1-policy-order` — separate worktree, main never modified |
| 1.4 worktree left alone | inspection only | `.claude/worktrees/agent-a5fc18cc573bd810b` [build/1.4-scoring] — not entered, not modified |

### 1.1 Original 1.1 pre-flight register rows (spec §7)

| # | Claim | Result |
|---|---|---|
| 1 | 0.2 merged; `backend/app/` exists | PASS — `git ls-tree origin/main -- backend/app/` lists `__init__.py`, `api`, `casepack`, `config.py`, `database.py`, `main.py`, `models` |
| 2 | `CONTRACTS.md` ≥ 9 entries | PASS — `grep -c "^## "` = 14 (now 15 with the new entry) |
| 3 | mis_lite 14 stakeholders / 4 strategies | **N/A for this rework** — harvest content already landed (1.3, on main) and is not touched here. Host `192.168.50.38:5432` confirmed reachable; content not re-queried because this packet authors no content |
| 4 | mis_lite `component_types_master` = 45 | **N/A for this rework** — same reason as row 3 |
| 5 | pydantic pinned + PyYAML importable | PASS — `requirements.txt`: `pydantic==2.10.4`, `PyYAML==6.0.2`; `python3 -c "import yaml"` OK |
| 6 | No `packs/` dir yet | **Historical/N-A** — this is a rework of an already-built module; `backend/packs/` exists by design |

Nothing failed. No pre-flight surprise, so no stop.

---

## 2. `1.1-RA-001` — `models.py` docstring corrected

**Evidence of the finding on the base tree** (`backend/app/casepack/models.py:438-439`):

```
#: and the box in 1.5 spec 5.4). Ordering is an authoring convention and
#: carries no meaning: do not infer strictness from position.
```

vs. the settled design (`design/07-decision-consequence-map.md:143-145`):

```
### 3.5b `options` is ORDINAL — permissive at index 0
**Ruled 2026-08-18.** `PolicyOption.options` is ordered, **least constrained first** …
```

**Change:** the `options` attribute docstring now states the ordinal contract — index 0 is
least constrained / most permissive, higher indexes progressively more restrictive, ordinal
distance is a real quantity that may be consumed downstream, and the `staff_monitoring` axis
note (`design/07 §3.5a`). It cites `design/07 §3.5b` and the new `CONTRACTS.md` entry. The
`default` docstring (already correct on the distinction from `permissive_value`) is
unchanged. The one enforced constraint (`default_is_a_declared_option`) is unchanged — no
new validation rule was invented.

Full hunk in §11.

---

## 3. `1.1-RA-002` — `CONTRACTS.md` entry added (versioned)

**Evidence of the finding on the base tree:** `grep -niE "policyoption|policies\.options|permissive_value" CONTRACTS.md` → **no match**.

**Change:** new PROSPECTIVE entry `## PolicyOption.options / PolicyOption.default`, placed
directly after its sibling ordinal vocabulary `entity.level_of_detail`. It covers every
item the packet required:

- **canonical ordering** — ordered, ordinal, index 0 least constrained / most permissive;
- **`PolicyOption.default`** — where a team starts; must be a member of a non-empty
  `options`; may sit at any index;
- **`default` vs obligation `permissive_value`** — distinct concepts, distinct files, with
  the starts-permissive / starts-compliant consequence of them coinciding or differing;
- **producers** — `models.py` `PolicyOption`; pack `policies.yaml`;
- **consumers** — loader (order-preserving), alignment scorer (1.4), validator
  `permissive_value`-in-`options` check (1.2, pending), Security screen (4.3);
- **invalid / ambiguous shapes** — default-outside-options (rejected at load),
  permissive-not-first (loads but content defect), permissive_value naming a non-option,
  both-omitted legacy shape;
- **why ordering matters** — without it a stricter-than-asked team scores identically to one
  that ignored the ask.

**Version bump** (`CONTRACTS.md` uses its "Last updated" line as its version marker; the
change is merged into the living document per `GOVERNANCE §8`, not a delta file):

```
- **Last updated:** 2026-07-27 (design-token two-tier contract; status badge scale added — finding `0.3-013`).
+ **Last updated:** 2026-08-21 (`PolicyOption.options` / `.default` ordinal-ordering contract added — rework finding `1.1-RA-002`; prior: 2026-07-27 …).
```

---

## 4. Additional surfaces reconciled to the same contract

The rework authorised reconciling `docs/casepack-schema.md` "if verification shows it is
incomplete or contradictory" (packet item 3), and required the consistency grep to leave
**no surviving statement that option order is meaningless** across "the relevant casepack
comments". Verification surfaced two such statements:

### 4a. `docs/casepack-schema.md`

`docs/casepack-schema.md:487-489` (base tree):

```
**Ordering is an authoring convention, not semantics.** Listing `minimal` first does not
make it the strict end. Nothing reads position …
```

Corrected to state the ordinal rule. **Also corrected the worked examples**, which authored
the permissive value *last* — the reverse of the newly-stated rule, and internally
contradictory once the rule is stated. Three `options` lists changed from
`[minimal, standard, indefinite]` to `[indefinite, standard_period, minimal]`
(permissive-first, matching the shipped Riverside vocabulary), plus the field-table `options`
/ `default` rows and one prose `default: standard` → `default: standard_period` for
vocabulary consistency. No content/behaviour depends on this file (authoring doc only).

### 4b. `backend/packs/riverside_grocery/PROVENANCE.md` — an extension, declared

`PROVENANCE.md:337-340` (base tree) still read:

```
**Order carries no meaning.** `models.py` is explicit — *"do not infer strictness from
position"*. The lists read permissive-to-restrictive only for a human …
```

This is a **surviving "order is meaningless" statement inside the shipped casepack**, and it
cites the exact `models.py` docstring this packet removes — so after RA-001 it would cite a
docstring that no longer exists *and* assert the opposite of the settled contract. The
mandatory verification grep names "the relevant casepack comments"; leaving it would mean
that verification could not be reported clean.

**Deviation declared:** `PROVENANCE.md` was not named in the packet's explicit change list
(items 1–4 name `models.py`, `CONTRACTS.md`, `docs`, and tests). It was corrected here
because (a) the required verification explicitly extends to casepack comments; (b) the
statement is the identical contradiction class as RA-001, not a new/independent design
conflict; (c) the change is pure provenance prose — `PROVENANCE.md` is not read by the
loader, validator, or any test, so behaviour is unaffected; (d) the correction matches the
pack's own already-corrected `policies.yaml` header (lines 37–42) and the 1.3-follow-up
table in the same file. It invents nothing. Corrected to the ordinal statement; full hunk in
§11.

`design/07-decision-consequence-map.md` was **not** edited: it is the settled authority this
rework reconciles *to*, its statements are ordinal-affirming, and its line 161 ("models.py's
docstring says order carries no meaning **and must be corrected** … 1.1") is a fix-directive
whose action is now satisfied — not a "meaningless" assertion. Editing the authority was out
of scope.

---

## 5. Focused tests added

`backend/tests/check_policy_options.py` — standalone script, exit 0/1, matching this repo's
convention (`check_fixture_matrix.py`); the repo has **no pytest infrastructure on this
base** (`pytest --collect-only` → "no tests collected"; the only pytest module,
`test_engine_scoring.py`, lives on the unmerged 1.4 branch). Nine checks, all PASS:

```
PASS  riverside declares options on its switches (fixture for the order check)  6 switches …
PASS  YAML list order survives loading unchanged (all six switches)
PASS  first and last option retain their positions (all six switches)
PASS  index 0 is the permissive end (default and permissive_value both name it)
        data_collection: index0='everything_by_default' … data_retention: index0='indefinite' …
        staff_monitoring: index0='untracked' …
PASS  default is distinct from permissive_value (compliant-start pack is valid)  default='standard_period' permissive_value='indefinite'
PASS  on Riverside, default (PolicyOption) and permissive_value (ObligationRule) are separate attributes on separate models
PASS  legacy PolicyOption (no options/default) loads with options==[] default==None
PASS  legacy-shape pack ok_obligations_empty loads; every policy is options==[] default==None  2 policies, all legacy shape
PASS  options order survives model_dump -> model_validate round-trip

all 9 policy-option contract checks pass   (EXIT=0)
```

Mapping to the four required proofs:

| Required proof | Check(s) |
|---|---|
| YAML list order survives loading unchanged | "order survives loading" — loaded `options` compared element-for-element against an independent `yaml.safe_load` of the same file |
| first and last option retain intended positions | "endpoints retained" + "index 0 is the permissive end" |
| default remains distinct from permissive_value | "default is distinct" (compliant-start pack, `default != permissive_value`) + "separate attributes on separate models" |
| legacy without options/default retains compatibility | "legacy PolicyOption …" (in-memory) + "legacy-shape pack ok_obligations_empty …" (real pack) |

(The round-trip check is an extra — it guards 1.1 invariant I8 for the two fields.)

---

## 6. Full test & validator output (definitive runs, all four changes present in the worktree)

An earlier run sequence executed while the model/docs/CONTRACTS edits were still in the main
working tree (see §10); those are superseded. The runs below are the authoritative ones,
taken with every change present on the branch.

```
check_fixture_matrix.py     → EXIT=0
  all 29 fixtures behave as named; 28 of 29 codes exercised, ['I8'] recorded as unfixturable
  I1 set-equal against the spec; I5 identical in single-pack and directory mode
validate_casepack riverside → EXIT=0
  riverside_grocery 0.1.0 (schema 1) — grocery_retail, 6 rounds
  ✓ 7 capabilities · ✓ 4 strategies (weights 1.000) · ✓ 13 events · ✓ demand curves 1–6
  0 errors · 0 warnings · exit 0
check_policy_options.py     → EXIT=0  (all 9 checks pass)
I3–I8 (checks.py on riverside): I3 PASS I4 PASS I5 PASS I6 PASS I7 PASS I8 PASS
I1 (grep pack-identity in backend/app/casepack): zero hits
I2 (grep displayed English):                     zero hits
seed riverside_grocery: 7 capabilities, 14 catalog items, 4 strategies; all weights 1.000; pinned figures read back
compileall backend/app/casepack: compileall_ok
git diff --check: clean
```

**Baseline (before any change), for comparison** — identical: `check_fixture_matrix.py`
EXIT=0, Riverside `0 errors · 0 warnings · exit 0`, I1–I8 all PASS. The change is
documentation + one new test file; no fixture, validator, or check result moved.

---

## 7. Consistency grep — no surviving "order is meaningless" statement

Pattern: `authoring convention|carries no meaning|not semantics|nothing reads position|order …(no meaning|meaningless|does not matter|is not meaningful)|convention, not`

Scoped to the named surfaces (`models.py`, `CONTRACTS.md`, `docs/casepack-schema.md`,
`design/07-decision-consequence-map.md`, and the whole `backend/packs/riverside_grocery/`):

```
design/07-decision-consequence-map.md:161:- **`models.py`'s docstring says order carries no meaning** and must be corrected …
```

**One hit, and it is not a violation.** It is `design/07 §3.5b`'s own record of the finding —
it asserts order *should* be ordinal and that `models.py` *must be corrected*. It is the
authority, left untouched. Every other surface — including `PROVENANCE.md` and every
`.yaml` in the pack — is now free of any "order is meaningless" statement.

Ordinal-affirming lines now present: `CONTRACTS.md` (new entry), `docs/casepack-schema.md`
(rewritten paragraph + field table), `models.py` (rewritten docstring),
`policies.yaml` (pre-existing header), `PROVENANCE.md` (corrected).

---

## 8. Isolation & safety confirmations

- **1.4 branch/worktree not modified by me.** `build/1.4-scoring` advanced `174e980 →
  972bcc1` **during this session — that is the active 1.4 builder committing to their own
  branch** ("1.4: scoring engine — pure MOT composition…"), not my doing. Its 16 changed
  files are all under `backend/app/engine/`, `backend/app/seed/`, `backend/seeds/`, and its
  own `tests/`/`handoffs/` — **zero overlap** with my four files (verified per-file with
  `git diff --quiet 174e980..build/1.4-scoring -- <file>`). The two branches merge without
  conflict. I never entered its worktree; my only touch was read-only `git` inspection.
- **main not modified.** `main` HEAD is still `174e980`. Its working tree shows only the
  pre-existing untracked `.claude/` and `handoffs/rework/` (present at session start). See
  §10 for a working-tree correction made mid-session.
- **Nothing pushed / merged / deployed / migrated.** `origin/build/1.1-policy-order-rework`
  does not exist (`git rev-parse --verify` → "Needed a single revision"). No push, no merge,
  no deploy, no migration. This is a headless documentation/contract change; there is no
  runtime artifact to deploy and no schema to migrate.

---

## 9. Stop-condition review

| Stop condition | Encountered? |
|---|---|
| Spec/code/design conflict beyond RA-001/RA-002 | **No new one.** The `docs` and `PROVENANCE.md` statements are the *same* contradiction class as RA-001 (authoring text vs the settled ordinal ruling), which the packet's item 3 and the verification requirement explicitly cover. No independent, unresolved design conflict was found |
| A required change would alter 1.4 scoring | **No.** Zero engine files touched; `default_is_a_declared_option` unchanged; no distance/scoring/validator code written |
| A test failure whose resolution isn't settled | **No.** No test failed |
| Need to invent a field/identifier/validation rule/compatibility behaviour | **No.** Only prose/docstring/contract text and one test; no new field, enum, rule, or behaviour |

No stop was required. Every question the packet raised was settled by the documents.

---

## 10. Working-tree correction (declared)

Mid-session, the three code/doc edits (`models.py`, `CONTRACTS.md`, `docs/casepack-schema.md`)
were first applied to the **main** working tree by path instead of the worktree. This was
caught by the consistency grep still showing old content in the worktree. Corrected: the
edits were captured as a patch from main (`git diff`), `git apply --check`ed and applied to
the worktree, and main was restored (`git restore`) to a clean tree. **`main`'s branch HEAD
was never moved** (no commit, no add), so nothing reached `main`; the net effect is
identical to having edited the worktree directly. All §6 definitive runs post-date the
correction. This is recorded rather than hidden per `GOVERNANCE §7` / `QUALITY_PROTOCOL §1`.

---

## 11. Change hunks

`git diff main` touches exactly four tracked files (+1 new test file):

```
 CONTRACTS.md                                  | +63   (new PolicyOption.options entry + version line)
 backend/app/casepack/models.py                | +/-19 (options docstring → ordinal)
 backend/packs/riverside_grocery/PROVENANCE.md | +/-10 (order-carries-no-meaning → ordinal)
 docs/casepack-schema.md                       | +/-30 (paragraph + 3 examples + field table)
 backend/tests/check_policy_options.py         | new   (9 focused checks)
```

The full unified diff was reviewed line by line before commit; `git diff --check` is clean
(no whitespace errors, no conflict markers).

---

## 12. Commit

Implementation + this DoD committed to `build/1.1-policy-order-rework`. Final commit SHA:
recorded in the branch log (`git log -1 --format=%H` on the branch). Worktree left clean.
Nothing pushed — the branch awaits independent audit before any merge.
