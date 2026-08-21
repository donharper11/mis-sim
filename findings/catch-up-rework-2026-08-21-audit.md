# Findings — consolidated catch-up rework

**Date:** 2026-08-21 · **Auditor:** fresh agent, independent worktree, no builder context
**Candidate:** `8cb507fe9232e5913928b144f871a54466c93c5b` on `build/catch-up-rework`
**Base:** `main` @ `3ae0b6dd703eae6ced4c918a55de54c106d5c69a` · **origin/main at audit:** `3c8d94807462dcf2593fcfa4a58810350016b014`
**Scope audited:** `handoffs/rework/catch-up-2026-08-21.md` §1 (six items) · complete 57-file diff
**Prompt:** `handoffs/_prompts/catch-up-rework-auditor.txt` (main @ `3c8d948`)

> **Role declaration (`GOVERNANCE §6.1`).** I did not build this branch and did not author its
> scope. The scope file and the builder's dispatch prompt were both written by the previous
> auditor. No prior conclusion in either was inherited: every figure in the builder's DoD was
> re-derived from the tree, the database or a mutation probe before being accepted.

---

## VERDICT

**PASS WITH FINDINGS — mergeable.** Approved for `8cb507fe9232e5913928b144f871a54466c93c5b`
and no other commit.

**No Blocking and no Functional-blocking findings.** All six scoped items are built, every
closing check reproduces independently, the three out-of-scope items are demonstrably not
built, every standing gate is green, and the branch merges cleanly into `origin/main` at
`3c8d948`. The register reconciliation is **honest**: every section-B row marked CLOSED was
re-tested against the tree and every one reproduced.

The findings below are one **Functional** residue (a defect class B7 named that survives
outside `EventPrecondition`, now unowned because B7 is marked CLOSED), three **Data** items
(two document/guard gaps and one remaining second home), and five **Report** items.

---

## 0. Pre-flight — state verified before auditing

| Check | Command | Result |
|---|---|---|
| Local = candidate | `git rev-parse HEAD` | `8cb507fe9232e5913928b144f871a54466c93c5b` |
| Remote = candidate | `git ls-remote origin build/catch-up-rework` | `8cb507fe…` — identical |
| `origin/main` unmoved | `git ls-remote origin main` | `3c8d9480…` before and after the audit |
| Merge base is the intended base | `git merge-base HEAD 3ae0b6d` | `3ae0b6dd703eae6ced4c918a55de54c106d5c69a` |
| One commit on the branch | `git log --oneline 3ae0b6d..8cb507f` | 1 commit |
| Isolated worktree | `pwd` | `.claude/worktrees/agent-aa0e2e5a60e45d2ac` |
| No uncommitted / unrelated files | `git status --porcelain` | empty · 57 files in the diff, 43 of them the migrated fixture packs, 14 in-scope |
| Merges into current `main` | `git merge-tree --write-tree 3c8d948 8cb507f` | exit 0, tree `80e84a62…`, no conflict block |

**Discrepancy reported, not resolved (`GOVERNANCE §7`).** The builder's dispatch prompt
(`handoffs/_prompts/catch-up-rework-builder.txt:4`) names `BASE: main @ caece533…`; the branch
is actually based on `3ae0b6d`, whose only content over `caece53` is the dispatch prompt file
itself. The auditor's prompt names `3ae0b6d` and the builder's DoD declares the same
("branched from `3ae0b6d` (base `caece53` + the prompt file)"). Benign, and declared in place
by the builder rather than glossed. Recorded because `1.1-r3-001` is on the register as a
prompt/branch lineage failure of exactly this shape.

---

## 1. The six scoped items — independently re-derived

### `B13` — `pos_system_2011.people_affected`

**The value is 62, and 62 is correct, not merely consistent.**

`backend/packs/riverside_grocery/catalog.yaml:57` now reads
`people_affected: {org_unit: store_operations, count: 62}`.

*The source was queried in this session* (`SPEC_PROTOCOL §2.1` — external state is queried,
never accepted from paste). `mis_lite` was reached over SSH to `192.168.50.38` as `donwh`:

```
$ ssh donwh@192.168.50.38 "psql -d mis_lite -tAc \
  \"select count(*) from information_schema.tables where table_schema='public'\""
79

$ ssh donwh@192.168.50.38 "psql -d mis_lite -A -F'|' -c \
  \"select table_name, column_name, data_type from information_schema.columns
    where table_schema='public' and (column_name ilike '%head%' or column_name ilike '%count%'
      or column_name ilike '%user%' or column_name ilike '%staff%' or column_name ilike '%people%'
      or column_name ilike '%employee%' or column_name ilike '%fte%' or column_name ilike '%seat%'
      or column_name ilike '%personnel%' or column_name ilike '%worker%') order by 1,2\""
table_name|column_name|data_type
(0 rows)
```

I then enumerated **every** numeric column name in the database (105 distinct) rather than
trusting the pattern list. Not one is a headcount: the nearest are `adoption_units` and
`cumulative_adoptions`, which count product adoptions, not staff. **The builder's claim that
`people_affected` has no harvested source is true, and it is now recorded in the pack's
transform map** (`PROVENANCE.md §1`, new `catalog[].people_affected` row) rather than left as
an unexplained gap.

*The five in-repo homes were read directly*, not taken from the DoD's table:

| Source | Read at | Says |
|---|---|---|
| 0.3 spec, COMPONENTS table | `handoffs/0.3-mockup-pilot/spec.md:301` | `POS System 2011 … Store ops  62` |
| 0.3 spec, ROLLOUT table | `handoffs/0.3-mockup-pilot/spec.md:310` | `POS System 2011  Store ops  62  100%` |
| `mockups/components.html:17` | Users column | `62` |
| `mockups/rollout.html:13` | People column | `62` |
| 1.4 seed, `dep_pos` | `backend/seeds/riverside_r3.py:159` | `people_affected=62, trained_count=62` |

`mockups/dashboard.html:3` gives `STORE OPERATIONS · 140 people` — the unit size, which
`order_mgmt_v42` and `store_spreadsheets` legitimately carry because they serve the whole
unit. The catalog was the sole outlier and no mockup was edited (`git diff --name-only`
lists no file under `mockups/`).

**Nothing else consumed 140 for this item.** `grep -rn "people_affected"` over the tree
returns the fixture packs (unrelated hospital/vet content), `engine/organisation.py:63,79`
(which read `DeploymentState`, not the catalog) and the migrated catalog row.

**The 1.4 Org pin did not move, and I tested the builder's reason rather than accepting it.**

```
$ python3 -c "… load_scenario('riverside_r3'); score_team(…)"
order_fulfilment       tech=0.750008 org=0.507003 mgmt=0.656778 realised=0.249744
order_fulfilment org evidence: {'training': {'trained': 49, 'affected': 140}, …}
```

*Adversarial probe.* A copy of the pack with `count: 62` mutated to `count: 9999` scores
**identically** — `org=0.507003`, `realised=0.249744`, every capability unchanged. The scorer
demonstrably does not read the catalog's headcount; `organisation.py:63` divides
`dep.trained_count / dep.people_affected` off `DeploymentState`, which the seed authors. The
`order_fulfilment` pin is `dep_order_mgmt` (140/49), a different deployment from `dep_pos`.
The claim holds.

**Guard.** `harvest_readback.py` now pins all six rows of the `components.html` Users column;
43 → 47 pinned figures, verified both ways (`43/43` at base, `47/47` on the candidate, and a
mutation of the catalog back to `140` drives it to `46/47 matched, 1 mismatched`, exit 1).

### `B7` — `E00` swallowing a parseable pack

Reproduced at base and at the candidate, from the tree, not from the DoD:

```
BASE (3ae0b6d)   E00  Unreadable pack   file=events.yaml field=casepack line=None
                 "This pack could not be read: events.yaml: events.0.preconditions.0.placement:
                  Input should be 'on_prem', 'cloud' or 'saas'"
                 Fix: restore or repair events.yaml …

CANDIDATE        ERROR  E29  Event saturday_overflow, precondition 1   events.yaml:2
                 Sets placement to 'hybrid'. A precondition's placement can only be on_prem, cloud, saas.
                 Fix: in events.yaml, set placement on precondition 1 of 'saturday_overflow' to
                      one of on_prem, cloud, saas.
                 Field: saturday_overflow.preconditions.0.placement
```

The closing check as the scope words it — *"author an out-of-vocabulary `placement`; expect a
targeted code naming `events.yaml` and the field, not `E00`"* — **is met**. `severity` is
covered identically (`severity: urgent` → the same targeted `E29`, verified). Both directions
are asserted by the shipped `backend/tests/check_event_preconditions.py`, and *disabling the
wiring line makes it fail* — mutation probe, `exit=1`, six assertions flip to FAIL.

**On the variant mechanism.** It is legitimate and precedented — `E10_pack_key`,
`E15_default` and `E26_no_options` already ship this way, and the 1.2 spec (`:576-578`)
explicitly records variants as *"catalogue variants, not new codes, so the code list and `I1`
are [unchanged]"*. Reading the closed vocabulary **off the model annotation**
(`checks._closed_vocabulary`) rather than restating it is the right call and avoids creating
the third home that `1.5-RC-002` is about. What is **not** legitimate is shipping the fourth
behaviour without amending the documents that enumerate the other three — see `CU-002`.

*Probe of the wider class:* see `CU-001`. Five other closed vocabularies still collapse.

### `B5` — the four `Labels` sections

Closing check reproduced:

```
$ grep -c -E "\{(entity_name|item_name|rule_name|question_name)\}" backend/app/casepack/validate_messages.yaml
9
$ git show 3ae0b6d:backend/app/casepack/validate_messages.yaml | grep -c -E "…"
0
```

Seven of `1.2-024`'s eight codes (`E05` `E09` `E12` `E23` `W04` `W06` `W07`, plus `E02`'s
entity noun) now resolve their subject through `lens.label(...)`. Demonstrated end to end on
a probe copy of Riverside with one threshold pair deleted:

```
ERROR  E12  Watch rule Order fulfilment capacity   watch_rules.yaml:11
       Fix: … set warn_above or critical_above on 'ord_cap_01' …      <- machine key kept
```

**`E07`'s narrowed `misc` catch-all lets nothing escape, and this is provable rather than
merely tested.** The acceptance predicate went from
`key ∈ labels[section] ∨ (section = misc ∧ key ∈ ⋃ labels)` to `key ∈ labels[section]`. The
new acceptance set is a strict **subset** of the old, so the finding set is a strict
**superset**: no input accepted under the old rule and rejected under it can exist, and every
input the old rule rejected is still rejected. Confirmed empirically both ways — the same
probe pack (Riverside with `redesign_close` moved from `misc:` to `catalog:`) validated
`0 errors · 0 warnings · exit 0` at base and raises `E07` at the candidate; Riverside itself
stays 0/0 and all 43 fixtures still behave as named.

**`E21` / DEVIATION `R1` — the stated reason is true, not a convenience.** `labels.events` on
Riverside maps `event_inventory_numbers → "The auditors asked how we know our inventory
numbers are right. I did not have an answer."` — thirteen entries, every one a sentence of
persona prose keyed by `body_key`, not by event key. `docs/casepack-schema.md:625-628`
states it as a call-out (*"`events` is not a name map … There is currently nowhere to author
an event's name"*) and **that call-out is pre-existing** — the only change this branch makes
to that file is the `capital_remaining` note. Routing `E21` through `labels.events` would
print a paragraph as a locator line, or (event keys and body keys being disjoint here) return
the machine key anyway. The deviation is correctly taken and correctly recorded at the call
site (`validate.py:1035-1040`) as well as in the register.

### `B11` — `erp_suite.config_tiers`

**Re-derived from the live source, not from the pack's harvest snapshot:**

```
$ ssh donwh@192.168.50.38 "psql -d mis_lite -A -F'|' -c \
  \"select module_level, count(*), avg(cost_value)::numeric(14,4) from erp_modules_master
    group by module_level order by 1\""
module_level|count|avg
Advanced|10|115000.0000
Basic|7|44571.4286
Mid|4|70000.0000
```

`70000 / 44571.4286 = 1.5705` · `115000 / 44571.4286 = 2.5801`. The authored ladder at
`catalog.yaml:400-403` is `1.0 / 1.57 / 2.58`. **It reproduces exactly.**

**Finding `1.3-004` is therefore wrong**, and the builder was right to say so. The audit read
*"the seven Basic-level module rows"* as seven families sampled at min/mid/max; the source has
a literal `module_level` column with exactly seven `Basic` rows. Both readings give `44571`
for Basic, which is why the error survived review — they diverge only where n is 4 and 10.

**No numeric value changed.** The `catalog.yaml` diff for this item is a comment block only
(`:34-41`); every `config_tiers` multiplier on the file is byte-identical to base.

### `B17` — dispositions for the extracted tables

Closing check reproduced mechanically: **`34 extracted · 34 disposed · missing: []`**. I did
not stop at the builder's script — I re-ran it *and* checked every one of the 34 table names
appears at least once **backticked** in `PROVENANCE.md` (it does), then read the disposition
context for the thirteen with a single occurrence. All thirteen are genuine dispositions
(`§1`'s transform map rows for `integration_services`, `regulatory_penalties`, `objectives`,
`impact_areas`, `stakeholder_infrastructure_preference`; `§5`'s placeholder-seeding table for
the five `*_mapping` rows; `§5a`'s new rows for the six the finding named plus
`ecommerce_features_master` and `business_processes_master`). See `CU-006` on the denominator.

### `B10` — `capital_remaining`'s second home

```
$ grep -c "capital_remaining" backend/app/casepack/models.py
1
```

- **No value changed in any migrated pack.** The 43 fixture diffs are byte-for-byte identical
  to each other: one deleted `capital_remaining: 52000` line plus a re-worded prose note.
  Riverside deletes `review.capital_remaining: 46000` and leaves `budget.capital_remaining:
  46000` untouched. `broken_E14` keeps its deliberately-wrong `40000` in `budget`.
- **All 44 packs still validate.** Loaded every pack directly: Riverside 0 findings,
  and the only fixture producing `E00` is `broken_E00`, by design.
- **Nothing silently reads the removed field.** Repo-wide grep over `*.py *.yaml *.json *.js
  *.jsx`: the surviving reads are `budget.capital_remaining` in `models.py:58`,
  `validate.py:1289-1291` (`E14`), `seed.py:38` and `harvest_readback.py:113`. `seed.py:51`
  and `harvest_readback.py:117` now compute the review figure. `backend/app/engine/` and
  `backend/seeds/` are byte-identical to base (`git diff … | wc -l` → `0`), and the frontend
  scaffold contains no reference.
- **`E14` is preserved, not weakened.** It checked one fact twice against the identical
  expression; it now checks it once. `broken_E14` still fires:
  *"states budget.capital_remaining as 40000, but capital available minus capital committed
  leaves 52000"*.
- **The migration is well guarded.** *Adversarial probe:* restoring `ReviewState.
  capital_remaining` in a scratch copy produces **27 failed, 8 passed** in pytest, fixture
  matrix `exit=1`, and Riverside `1 error`. This change cannot regress silently.
- **`CONTRACTS.md`** gains a full `capital_remaining` entry with producers, consumers, the
  derivation, the migration signal and the standing `B14` conflict; `docs/casepack-schema.md`
  gains the call-out. `GOVERNANCE §8` satisfied for this item.

---

## 2. Out of scope — confirmed NOT built

| Item | Evidence |
|---|---|
| `B14` 16 mockups at `$44,000` | `git diff --name-only 3ae0b6d..8cb507f` lists **no file under `mockups/`**. Independently counted: 16 of 19 mockup files carry `44,000`; `review.html` and `review-locked.html` carry both figures. `harvest_readback.py` still prints it as a **declared conflict** |
| `B15` 630 placeholder mapping rows | `backend/harvest/` untouched; `PROVENANCE.md §5`'s distinct-value table unchanged in the diff |
| `B16` 38 `TODO: calibrate` | No marker removed. One **added**, by `B11`, which is that item's own remit. Counts verified: base directory grep 38 (4 in `PROVENANCE.md`, 34 in YAML, of which one is a convention header comment at `watch_rules.yaml:7` → **33 marked values**); candidate 40 / 5 / 35 → **34 marked values**. The register's corrected `33 → 34` is right |

---

## 3. Standing gates — all re-run, none accepted from the report

| Gate | Result |
|---|---|
| `backend/app/engine/` byte-identical to base | `git diff 3ae0b6d..8cb507f -- backend/app/engine/ \| wc -l` → **0** |
| `backend/seeds/` byte-identical to base | same command → **0** |
| No casepack-identity branching | `grep -rniE "riverside\|grocer" backend/app/engine/` → **0**. Widened to `backend/app/`: 4 hits, all in `app/seed/` (a scenario name in a lookup table and CLI help), all pre-existing on `main` |
| Riverside 0 errors / 0 warnings, **text** | `0 errors · 0 warnings · exit 0` |
| Riverside 0 errors / 0 warnings, **JSON** | `--json` emits `[]`, exit 0 |
| Fixture matrix | `all 43 fixtures behave as named; 37 of 38 codes exercised, ['I8'] recorded as unfixturable` |
| `I1` set equality | `38 = 38`, PASS |
| `I5` text/JSON parity, **both modes** | single-pack and directory mode, `identical=yes` on all four rows, incl. `packs/ text=91 json=91` |
| Full `pytest` | **35 passed** |
| Every `tests/check_*.py` | `check_fixture_matrix` 0 · `check_event_preconditions` 0 · `check_policy_options` 0 · `check_w08_rounds` 0 |
| Seed command | `python3 -m app.casepack.seed riverside_grocery` → `remaining 46000`, **computed**, exit 0 |
| `ruff` on changed files | `All checks passed!` |
| `ruff` on the wider tree | 8 findings — **identical count at base**, all in files this branch does not touch. Not introduced |
| `git diff --check` over the branch | exit **0** |
| Merges cleanly into current `main` | `git merge-tree --write-tree 3c8d948 8cb507f` → exit 0, no conflict block |

---

## 4. Register reconciliation — re-run row by row

Every section-B row marked closed was re-tested **against the tree**, not read from the file.
`findings/OPEN-REGISTER.md` shows 13 rows `✅ CLOSED`, `B9` closing on merge, `B8`/`B12`
mitigated, and `B14`/`B15`/`B16` ruled. **Every closing check I could execute reproduced.**

| Row | Closing check I ran | Result |
|---|---|---|
| `B4` | `E24`–`E28` in `catalogue()` | all five present — reproduces |
| `B5` | catalogue placeholder grep | **9**, was 0 — reproduces |
| `B6` | six switches declare `options`; `E26` checks `permissive_value` | `check_policy_options.py` 13/13 PASS; `broken_E26` and `broken_E26_no_options` both PASS with the field ending `.permissive_value` — reproduces |
| `B7` | out-of-vocabulary `placement` → targeted code | `E29` at `events.yaml:2`, field named — reproduces (residue: `CU-001`) |
| `B10` | `grep -c capital_remaining models.py` → 1 | **1** — reproduces |
| `B11` | each `config_tiers` multiplier derived or marked | `erp_suite` capex derived from the live DB; `catalog.yaml:41` marks the rest — reproduces |
| `B12` | *(not marked closed)* "10 of 42" | `grep -o "lead_time_rounds: [0-9]*" catalog.yaml` → 10 zeros of 42 — accurate |
| `B13` | one consistent figure, cited, `components.html` agreeing | 62 everywhere; DB queried; Org pin unmoved — reproduces |
| `B17` | every mapped table has a disposition | `34 extracted · 34 disposed · missing: []` — reproduces (see `CU-006`) |
| `B18` | default outside its own options → `E17` | probe → `codes=['E17']` — reproduces |
| `B19` | that input → a real diagnostic | `options: ['Indefinite','NOT snake!','9lives']` → **4 × `E15`** — reproduces. The row's *"`E15` + `E26`"* wording needs an obligation on that switch to show `E26`; on a pack without one only `E15` fires. Substance holds |
| `B20` | `options: [on, off]` → `E15` | probe → `codes=['E15']` — reproduces |
| `B21` | `CONTRACTS.md` `PolicyOption.options` entry, ordinal | `check_policy_options.py` asserts it — reproduces |
| `B22` | duplicates → `E16`; empty member → `E15` | probes → `['E16']` and `['E15']` — reproduces |

**No row is marked CLOSED whose check I could not reproduce.** The reconciliation is honest,
and this packet is the first to run `§I` amendment 3 (register updated in the same commit as
the DoD — one commit, `8cb507f`, carries both).

**Owners on the new items:** `J1`/`R1` → **1.1 next**; `J2` → **1.7 calibration**;
`J3` → **no owner** (see `CU-005`).

---

## Functional

- **`CU-001`** — **The `E00` collapse class `B7` names survives on five other closed
  vocabularies, and `B7` is now marked CLOSED with nothing owning the residue.** The fix
  covers `EventPrecondition.placement` and `.severity` only. Probed on the shipped fixtures,
  each producing a bare `E00 "Unreadable pack"` with `field=casepack`, `line=None` and the
  *"restore or repair"* fix line against a file that parses — the exact `GOVERNANCE §4.10`
  defect `B7` was filed for:

  | Field | Declared at | Probe | Result |
  |---|---|---|---|
  | `entities[].sensitivity` | `models.py:307` | `sensitivity: severe` | `codes=['E00']` |
  | `stakeholders[].stakeholder_type` | `models.py:430` | `stakeholder_type: partner` | `codes=['E00']` |
  | `*.provenance.source` | `models.py:32,39` | `source: INVENTED` | `codes=['E00']` |
  | `catalog[].rgt_tag` | `models.py:26,244` | `rgt_tag: sustain` | `codes=['E00']` |
  | `watch_rules[].metric_kind` | `models.py:337` | `metric_kind: rolling` | `codes=['E00']` |

  `provenance.source` is the sharpest of the five: it appears on essentially every object in
  every pack file, so one typo collapses the whole pack. The register's `B7` row is honestly
  scoped (*"`severity`, the other closed vocabulary **on `EventPrecondition`**"*), but
  `dod-catch-up.md §3.3` is headed **"The class, not just the proof"** and DoD row 9 claims
  *"the same class, not only the one proof — PASS"*, which over-states what shipped. With
  `B7` closed and no new register item raised, this class now has **no owner**, which is the
  precise failure this packet exists to end. The mechanism generalises cheaply —
  `checks._closed_vocabulary()` already reads vocabularies off model annotations. Not
  blocking: pre-existing behaviour, not introduced here, and no scoped closing check fails.
  **Recommended:** a register row with an owner before merge, or a one-line ruling that the
  residue is accepted.

## Data

- **`CU-002`** — **`E29` acquired a fourth behaviour and neither document that enumerates
  its three was amended.** `handoffs/1.2-validator/spec.md:219` reads *"E29 an event
  precondition with an unknown type, a missing required field, or a field belonging to
  another type"*; `docs/casepack-schema.md:331` reads *"missing fields, unknown types, and
  fields belonging to another type are `E29` errors"*. Neither file is in this branch's diff,
  yet `E29_vocab` now also fires on a value outside a closed vocabulary — which is none of
  the three. The precedent cuts the other way: the two prior variants **were** recorded, in
  the spec's own changelog (`spec.md:576-578`, v1.4). `SPEC_PROTOCOL §3` — *"Interface
  freezes are explicit … FROZEN or VERSIONED. Silent changes forbidden"* — and the spec's own
  header (*"Code list is versioned, not frozen"*) both apply. `GOVERNANCE §8`: the delta
  should land in the living document with the change, as this packet correctly did for
  `capital_remaining`.

  **`I1` cannot catch this.** `check_fixture_matrix.py:178` computes `implemented =
  set(catalogue()["codes"])` — variants live under `catalogue()["variants"]` and are
  structurally invisible to it. `I1 set equality: PASS` therefore proves the *code list* is
  in sync and says nothing about whether the *behaviour list* is. That is a pre-existing
  property of the invariant, not something this packet broke; but it means "I1 stays
  set-equal" is not the assurance the DoD (row 10) presents it as. The new branch also
  reaches the validator through **no fixture** in the matrix, widening the gap `1.5-RC-003`
  already records for `E29`'s other branches.

- **`CU-003`** — **Neither half of `B5` ships a regression guard; both revert silently.**
  Mutation-proven on a scratch copy of the candidate:

  ```
  mutation: delete `rule_name=lens.label("watch_rules", rule.key),` from validate.py
            and revert `subject: "Watch rule {rule_name}"` to `{rule}`
  → pytest 35 passed · check_fixture_matrix exit 0 · check_event_preconditions exit 0
    check_policy_options exit 0 · check_w08_rounds exit 0 · harvest_readback exit 0

  mutation: restore E07's `everywhere` union fallback for `misc`
  → pytest 35 passed · check_fixture_matrix exit 0
  ```

  `B5` survived **two** prior rework packets before this one. Its closing check is a grep
  someone must remember to run, and the `E07` narrowing's falsification was a one-off manual
  probe. `OPEN-REGISTER §I` amendment 2 states the remedy for exactly this shape — *"the
  check becomes a permanent test"*. Compare `B13` and `B10`, both of which are properly
  guarded (`harvest_readback` exits 1 on a reverted headcount; restoring `ReviewState.
  capital_remaining` fails 27 tests). For contrast, `B7`'s guard **is** real: disabling
  `check_precondition_vocab_raw` makes `check_event_preconditions.py` exit 1 — though
  `pytest` and the matrix both still pass, which is `1.5-RC-004` re-confirmed.

- **`CU-004`** — **`people_affected` still has an unreconciled third home, and it is the one
  the scorer reads.** `B13` made `catalog.yaml`, the 0.3 spec and the two mockups agree, and
  pinned them in `harvest_readback.py`. But the value the Org training sub-factor actually
  divides by is `backend/seeds/riverside_r3.py:159`'s hand-authored `people_affected=62`,
  and **nothing reconciles the seed against the catalog**: mutating the catalog to `9999`
  leaves every score bit-identical (probe above), and no test pins `store_operations`' Org
  term or the seed's headcounts. `SPEC_PROTOCOL §3` — *"One source of truth per fact … prefer
  elimination over reconciliation"*. This is the same defect class `B13` and `B10` were
  filed for, one layer down, and it will bite the 1.6 round-runner when deployments stop
  being hand-authored. Correctly out of this packet's scope (`backend/seeds/` was forbidden
  to it); recorded so it acquires an owner rather than being discovered again.

## Report

- **`CU-005`** — **`J3` is filed with no owner**, against the register's own closing rule:
  *"A finding is closed, owned, or being fixed. There is no fourth state, and 'flagged' is
  not one of them."* `findings/OPEN-REGISTER.md` §J gives `J3` the owner cell
  *"(recorded — no owner required)"* and the closing check *"none needed"*. The substance is
  defensible — `1.3-004` is factually wrong (independently confirmed above) and `GOVERNANCE
  §8` favours recording the correction in the living document over editing a dated audit —
  but `findings/1.3-2026-08-18-audit.md:220-250` still asserts the derivation *"does not
  reproduce under any grouping"*, with nothing at that location pointing to the correction.
  A reader who opens the audit is still misled. Either `J3` takes an owner, or the audit
  file gets a one-line pointer to `PROVENANCE.md §2a`.

- **`CU-006`** — **`B17`'s denominator is the extraction manifest, not the §5.1 transform
  map, and the two are conflated.** `handoffs/1.3-harvest/spec.md:240-262` names **24**
  tables (plus the zero-row `*_decisions` class); `backend/harvest/mis_lite/_manifest.json`
  records **34** extracted. The shipped check iterates the manifest, so it is a **superset**
  of the stated closing check and the disposition claim is stronger, not weaker — but
  `OPEN-REGISTER.md`'s `B17` row and `dod-catch-up.md` row 23 both word it as *"every table
  in the §5.1 transform map"* while pasting a 34-table result, which reads as though §5.1
  names 34. Secondary: the check is `t not in prov`, a naive substring test over the whole
  file, so a table name occurring anywhere in prose satisfies it. I verified the stronger
  form by hand (every one of the 34 appears backticked, and each single-occurrence name sits
  in a genuine disposition row), and it holds — but the check as written would not catch a
  regression on names like `strategy` or `stakeholders`.

- **`CU-007`** — **`dod-catch-up.md` row 39's N-A justification is false.** It reads *"There
  is no frontend in this repo to exercise."* `frontend/` exists — 18 tracked files, a Vite
  config, `package.json`, `src/App.jsx`, `src/main.jsx`, `src/pages/DevTokens.jsx`,
  `src/styles/theme.css`. The **substance** of the N-A is correct (this packet ships no
  user-facing surface, and grep confirms the scaffold reads none of the changed fields), so
  the rung is properly skipped — but `QUALITY_PROTOCOL §2` requires the reason to be stated,
  and a reason that is not true is not a reason. Say *"the frontend scaffold consumes none of
  the changed fields"*, which is checkable.

- **`CU-008`** — **`OPEN-REGISTER.md` row `B9` is stale.** It reads *"(done, pending merge)"*
  and *"Closes on merge"*, but `git merge-base --is-ancestor 1f060b4 3c8d948` exits **0** —
  the 1.5 readiness branch is already on `main` (merge commit `caece53`). This row does not
  name the catch-up packet, so it was outside the builder's reconciliation remit; it is
  inside the auditor's under `§I` amendment 4, which is why it is here. A row that says
  "pending" about something already merged is the same class of untested status the sweep was
  created to end.

- **`CU-009`** — **`CONTRACTS.md`'s new `capital_remaining` entry mis-counts the mockups.**
  It says *"**16 of the 18** Phase 0 mockups display `$44,000`"*; `mockups/` holds **19**
  html files, 16 of which carry `44,000` and two of which (`review.html`,
  `review-locked.html`) carry both figures. `OPEN-REGISTER.md`'s `B14` row states it
  correctly (*"16 mockup files carry `44,000`, 2 carry `46,000`"*). The `CONTRACTS.md`
  wording is new in this commit, so it is this packet's to correct.

---

## Observations — not findings

- **`E29`'s 1-based prose vs 0-based locator.** The rendered finding says *"precondition 1"*
  while `Field:` says `preconditions.0`. This is the **pre-existing** house convention — the
  original `E29` caller at `validate.py:806-808` does exactly the same (`f"…preconditions.
  {index}"` with `number=index + 1`) — so the variant is consistent with what shipped in 1.5
  and this packet introduced nothing. Recorded because it is confusing to an instructor and
  is cheap to settle when someone owns `E29` next.
- **`B16`'s corrected count is right, its explanation is slightly short.** The row attributes
  the whole `38 → 34` gap to four prose mentions inside `PROVENANCE.md`. There is a fifth
  non-value mention, the convention header at `watch_rules.yaml:7`. Base: 38 directory / 4
  `PROVENANCE.md` / 34 YAML − 1 header = **33 marked values**. The arithmetic lands where the
  register says it does.
- **The `_closed_vocabulary` helper is the right shape.** Reading the vocabulary off
  `EventPrecondition.model_fields[...].annotation` instead of restating it means `B7`'s fix
  cannot become the second home that `1.5-RC-002` and `CONTRACTS.md` (`placement`) are about.
  If either field ever loses its `| None`, `get_args` returns bare strings and the helper
  raises `RuntimeError` at import — loud, not silent, which is the correct failure mode.

---

## Reviewer self-check (`SPEC_PROTOCOL §2.2`)

1. Every finding cites `file:line`, a grep with output, or a command with output — yes.
2. Every claim about external state was **queried in this session**: `mis_lite`'s table
   count, its full column inventory and the `erp_modules_master` aggregation were all run
   over SSH to `192.168.50.38` during the audit, with output pasted above. Nothing was taken
   from the builder's pasted psql output.
3. Every remediation suggestion was checked to achieve what it claims.
4. No version, range or availability is asserted.
5. **Authorship declared:** I authored neither the spec/scope nor the build
   (`GOVERNANCE §6.1`). The scope's author is the previous auditor; that is recorded in the
   scope file itself and is why this pass is a fresh agent.
6. Anything unverifiable in-session is filed as an observation, not a finding.

---

## Approval

```
PASS WITH FINDINGS — MERGEABLE
Approved SHA: 8cb507fe9232e5913928b144f871a54466c93c5b   (and no other)
Merges cleanly into origin/main @ 3c8d94807462dcf2593fcfa4a58810350016b014
```

None of `CU-001`–`CU-009` blocks the merge. `CU-001` is the one that should acquire an owner
before it is forgotten, and `CU-003` is the one most likely to cost a third rework packet.
The dispatcher merges; this auditor does not.
