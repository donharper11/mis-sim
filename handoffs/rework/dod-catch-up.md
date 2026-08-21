# DoD — consolidated catch-up rework

**Packet:** `handoffs/rework/catch-up-2026-08-21.md` §1 (six items)
**Prompt:** `handoffs/_prompts/catch-up-rework-builder.txt` (main @ `3ae0b6d`)
**Branch:** `build/catch-up-rework`, branched from `3ae0b6d` (base `caece53` + the prompt file)
**Builder:** re-builder agent, 2026-08-21. **This file is the session report** (`SPEC_PROTOCOL §6`).

> **Builder ≠ Auditor.** Nothing in this file is an audit. An independent agent with fresh
> context reviews this branch before it merges (`GOVERNANCE §6.1`).

---

## 0. Headline

| | |
|---|---|
| Items built | **6 of 6** — `B13` `B7` `B5` `B11` `B17` `B10`, in the dispatched order |
| Items not built (ruled in §2 of the scope) | `B14` `B15` `B16` — untouched |
| Blockers stopped on | **none.** `mis_lite` was reachable and was queried; see `B13` |
| **Did the 1.4 Org pin move?** | **No.** `order_fulfilment` Org stays `0.507003`, exact to `1e-6`. Reason in `B13` below |
| Engine / scoring logic changed | **none.** `backend/app/engine/` is byte-identical on this branch |
| Schema change shipped | **one**, and it is `B10`: `ReviewState.capital_remaining` removed |

```
$ git diff --stat 3ae0b6d -- backend/app/engine backend/app/seed backend/seeds
(no output — no engine, seed-loader or seed-scenario file changed)
```

---

## 1. Definition-of-Done table

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | **`B13`** — establish the harvested truth for `pos_system_2011.people_affected` from `mis_lite` | **PASS** | `mis_lite` queried live (§2.1). It holds **no headcount column in any of its 79 tables**, so the field has no harvested source. Ruling and its five citations: `PROVENANCE.md` §11 |
| 2 | `B13` — author ONE value, cite its source in `PROVENANCE.md` | **PASS** | `catalog.yaml:57` now `count: 62`; source table in `PROVENANCE.md` §11; new `§1` transform-map row for `catalog[].people_affected` |
| 3 | `B13` — make `components.html` agree | **PASS (already agreed)** | `mockups/components.html:17` and `mockups/rollout.html:13` both read `62` and were **not edited**. The pack was the outlier; the pack was corrected |
| 4 | `B13` — re-derive the 1.4 Org pin and report whether it moved | **PASS — pin did not move** | §2.2. `test_pin_riverside_r3_order_fulfilment` passes unchanged at `org == 0.507003` |
| 5 | `B13` closing check — one consistent figure across pack and mockups | **PASS** | §2.3 |
| 6 | `B13` guard — the row was unpinned by `I7`, which is how it drifted | **PASS** | `harvest_readback.py` now pins the whole `Users` column: **43 → 47 pinned figures, 47/47 matched, exit 0** (§2.4) |
| 7 | **`B7`** — reproduce the defect first | **PASS** | §3.1 — bare `E00 "This pack could not be read"`, `Field: casepack`, on an `events.yaml` that parsed |
| 8 | `B7` — an out-of-vocabulary `placement` returns a targeted code naming `events.yaml` and the field | **PASS** | §3.2 — `E29`, `events.yaml:2`, `Field: saturday_overflow.preconditions.0.placement` |
| 9 | `B7` — the same class, not only the one proof | **PASS** | `severity` was the second closed vocabulary and collapsed identically; both are covered (§3.3) |
| 10 | `B7` — no new code invented, `I1` still set-equal | **PASS** | Shipped as the `E29_vocab` **variant**; `I1 set equality : PASS`, 38 = 38 (§6.2) |
| 11 | `B7` — regression check, both directions | **PASS** | 7 new assertions in `backend/tests/check_event_preconditions.py`; asserts `E29` IS raised **and** `E00` is NOT (§3.4) |
| 12 | **`B5`** — the four `Labels` sections are consulted by a message | **PASS** | §4.1 — `catalog ×4 · entities ×2 · watch_rules ×2 · questions ×1`, previously zero |
| 13 | `B5` closing check — label-section placeholders in the catalogue, expect non-zero | **PASS** | §4.2 — **9**, previously 0 |
| 14 | `B5` — demonstrated end to end on a pack that authors the sections | **PASS** | §4.3 — `Watch rule Order fulfilment capacity`, not `Watch rule ord_cap_01` |
| 15 | `B5` — `E07`'s silently widened `misc` catch-all | **PASS** | §4.4 — fallback narrowed; falsification run: a label authored under `catalog:` no longer satisfies a `misc` reference |
| 16 | `B5` — `E21` is one of the eight and is **not** fixed | **DEVIATION, reported** | §4.5. `labels.events` maps `body_key` → a paragraph of in-world prose, not a name (`docs/casepack-schema.md`). Routing `E21` through it would print a persona's message as a locator line. Open item `R1`, a schema change. Left raw with the reason in code |
| 17 | **`B11`** — show the derivation, or mark the multipliers as estimates | **PASS — derivation shown** | §5.1. It reproduces **exactly** on the source's own `module_level` column: `1.0000 / 1.5705 / 2.5801`. `PROVENANCE.md` §2a carries the runnable script and its output |
| 18 | `B11` — finding `1.3-004` said *"does not reproduce under any grouping"* | **REPORTED — the finding is wrong** | §5.2. The audit's `R2` reconstructed families; the note meant the seven rows whose `module_level` is literally `Basic`. Both give `44571`, which is why it held. Not silently overwritten — stated in place |
| 19 | `B11` closing check — each `config_tiers` multiplier carries a derivation or a `TODO: calibrate` | **PASS** | §5.3. `erp_suite` capex → derivation (§2a). Every other multiplier on the file → one new `TODO: calibrate` at `catalog.yaml:41`, listed in `PROVENANCE.md` §7. **No numeric value changed** |
| 20 | **`B17`** — six extracted tables with no `PROVENANCE.md` disposition | **PASS** | `PROVENANCE.md` §5a, one row each, written against the extracted JSON |
| 21 | `B17` — the two the audit called *"recorded in prose, not tabulated"* | **PASS** | Same section — `ecommerce_features_master`, `business_processes_master` now have rows |
| 22 | `B17` — `security_incidents.probability`, the audit's smaller note | **PASS** | `PROVENANCE.md` §5a closing paragraph |
| 23 | `B17` closing check — every table in the transform map has a disposition line | **PASS** | §6.1 — `34 extracted · 34 disposed · missing: []`. The check is pasted into `PROVENANCE.md` §5a so it stays runnable |
| 24 | **`B10`** — `capital_remaining` has one schema-required home | **PASS** | §7.1 — `grep -c` → `1` |
| 25 | `B10` — does removing the second home break a loader, seed or scorer contract? | **PASS — it does not; reported in full** | §7.2. No engine path reads it. The loader breaks only for packs that still author the removed key, and all 44 in-repo packs were migrated in this commit |
| 26 | `B10` — the invariant `E14` enforced is preserved | **PASS** | §7.3 — one derivation row now enforces what two enforced against the identical expression; `broken_E14` still fires `E14` |
| 27 | `B10` — cross-cutting field changed → `CONTRACTS.md` | **PASS** | New `capital_remaining` entry; `docs/casepack-schema.md` note added |
| 28 | Riverside validates 0 errors / 0 warnings, **text and JSON** | **PASS** | §6.3 |
| 29 | 43/43 fixture matrix | **PASS** | §6.2 — `all 43 fixtures behave as named` |
| 30 | `I1` set equality | **PASS** | §6.2 |
| 31 | `I5` text/JSON parity, both modes | **PASS** | §6.2 |
| 32 | Full `pytest` | **PASS** | §6.4 — `35 passed` |
| 33 | Every `backend/tests/check_*.py` | **PASS** | §6.5 — all four, exit 0 |
| 34 | Seed command reproduces the demo state (`GOVERNANCE §4.9` rule 4) | **PASS** | §6.6 |
| 35 | No casepack-identity branching | **PASS** | §6.7 — `grep -rniE "riverside\|grocer" backend/app/engine/` → 0 |
| 36 | No new required casepack fields | **PASS** | §6.8 — the only schema delta is a **removal** |
| 37 | `ruff` clean on changed files | **PASS** | §6.9 |
| 38 | `git diff --check` clean over the whole branch | **PASS** | §6.10 |
| 39 | Ladder rung 3–5 (browser, screenshots, auth canary, design-system canary) | **N-A, reason stated** | This packet ships **no user-facing surface**: the changed artifacts are the casepack schema, the validator's message catalogue, pack content and provenance documents. There is no frontend in this repo to exercise. `mockups/*.html` were read and **not modified** |
| 40 | Register Reconciliation | **PASS** | §8 — all nine register items naming this packet re-tested, `findings/OPEN-REGISTER.md` updated **in this same commit** |

---

## 2. `B13` — `pos_system_2011.people_affected` · **PRIORITY**

### 2.1 The source was reachable, and it was queried

`GOVERNANCE §4.1` — no assumptions when systems are inspectable. The instruction was to stop
if the database was unreachable. **It was reachable.**

```
$ PGPASSWORD=… PGOPTIONS='-c default_transaction_read_only=on' \
  psql -h 192.168.50.38 -U donwh -d mis_lite -tAc "select 1;"
1

$ … -tAc "select count(*) from information_schema.tables where table_schema='public';"
79

$ … -tAc "select table_name||'.'||column_name from information_schema.columns
          where table_schema = 'public'
            and (column_name ilike '%user%'   or column_name ilike '%people%'
              or column_name ilike '%staff%'  or column_name ilike '%head%'
              or column_name ilike '%employee%' or column_name ilike '%count%'
              or column_name ilike '%affected%') order by 1;"
(0 rows)
```

**`mis_lite` carries no headcount, user-count or staffing column at all.** `people_affected`
has no harvested source and never had one — which is exactly why `PROVENANCE.md` §1's
transform map had no row for it until this rework added one. The harvested truth is that
there is no harvested truth, and that is a queried answer, not an assumption.

### 2.2 The ruling: **62**, and why the pack was the outlier

| Source | Says | Read at |
|---|---|---|
| 0.3 mockup-pilot spec, COMPONENTS table | `62` | `handoffs/0.3-mockup-pilot/spec.md:301` |
| 0.3 mockup-pilot spec, ROLLOUT table | `62` | `handoffs/0.3-mockup-pilot/spec.md:310` |
| `mockups/components.html`, Users column | `62` | `mockups/components.html:17` |
| `mockups/rollout.html`, People column | `62` | `mockups/rollout.html:13` |
| 1.4 Riverside R3 seed, `dep_pos` | `62` | `backend/seeds/riverside_r3.py:159` |
| `catalog.yaml` | `140` | was `catalog.yaml:49`, now `catalog.yaml:57` **← corrected to 62** |

`140` is the size of the **whole** `store_operations` unit (`mockups/dashboard.html`,
*"STORE OPERATIONS · 140 people"*). It is the right count for `order_mgmt_v42` and
`store_spreadsheets`, which serve the entire unit and already carry `140`; it is the wrong
count for a point-of-sale system used by till operators. The item's own provenance tag is
`source: PINNED`, and the pinned figure is `62`.

### 2.3 Closing check — one consistent figure

```
$ grep -n "people_affected" backend/packs/riverside_grocery/catalog.yaml | grep pos -A0
  (item pos_system_2011)
  people_affected: {org_unit: store_operations, count: 62}   # 0.3 s5.6 / components.html: 62 users …

$ grep -n "POS System 2011" mockups/components.html mockups/rollout.html
mockups/components.html:17:  POS System 2011 … Store ops  62  100%  $3,100
mockups/rollout.html:13:    POS System 2011   Store ops  62  100%  redesigned  done  97%
```

### 2.4 **Did the 1.4 Org pin move? No.**

**It could not have.** The scorer reads the runtime `DeploymentState`, not the catalog
(`backend/app/engine/organisation.py:63` takes `dep.people_affected`), and
`backend/seeds/riverside_r3.py:159` has carried `people_affected=62, trained_count=62` since
1.4 landed. Two further reasons the pinned figure is untouched:

1. The pinned Org is for **`order_fulfilment`**, whose primary rollout is `dep_order_mgmt`
   (140 affected, 49 trained). `dep_pos` is `is_primary_for="store_operations"` — a
   different capability.
2. `test_engine_scoring.py` asserts Org to `1e-6` and passes unchanged:

```
$ python3 -m pytest -q tests/test_engine_scoring.py
...........                                                              [100%]
11 passed
```

`org == 0.507003`. **No re-pin was needed and none was performed.** Had it moved, this row
would report it and stop, not re-pin it.

### 2.5 The guard, so this cannot recur

`1.3-008` was possible because `I7` pinned only two of `components.html`'s six Users values.
All six are pinned now.

```
$ python3 backend/scripts/harvest_readback.py | tail -1
  47/47 matched, 0 mismatched, 2 declared conflicts
```
*(43 pinned figures before this packet, 47 after. Exit 0.)*

---

## 3. `B7` — `E00` swallowing a parseable pack

### 3.1 Reproduced first (`GOVERNANCE §4.10`)

`minimal_valid`, one precondition changed to `{type: placement_count, placement: hybrid, count: 2}`.
`events.yaml` parses as YAML perfectly.

```
  ERROR  E00  Unreadable pack                 events.yaml
         This pack could not be read: events.yaml: events.0.preconditions.0.placement:
         Input should be 'on_prem', 'cloud' or 'saas'
         Fix: restore or repair events.yaml in the pack directory, then run the validator again.
         Field: casepack
```

Three separate failures in four lines: the subject is *"Unreadable pack"* for a readable
file; `Field:` is `casepack`, naming nothing; and the `Fix:` tells the author to **restore or
repair** a file whose one wrong value they cannot see.

### 3.2 After

```
  ERROR  E29  Event saturday_overflow, precondition 1  events.yaml:2
         Sets placement to 'hybrid'. A precondition's placement can only be on_prem, cloud, saas.
         Fix: in events.yaml, set placement on precondition 1 of 'saturday_overflow' to one of
              on_prem, cloud, saas.
         Field: saturday_overflow.preconditions.0.placement
```

### 3.3 The class, not just the proof

`severity` is the other closed vocabulary on `EventPrecondition` and collapsed identically
(`severity: urgent` → the same bare `E00`). It is covered by the same check:

```
  ERROR  E29  Event saturday_overflow, precondition 1  events.yaml:2
         Sets severity to 'urgent'. A precondition's severity can only be warning, critical.
```

### 3.4 How

Same mechanism the 1.2 rework used for `E15`/`E17` (`validate.py check_policy_vocab`): a
**raw-stage** check that runs *before* the pydantic load, so the load refusal never becomes
the diagnostic. `E00` is emitted only when no other `ERROR` exists, so a targeted finding
displaces it by construction.

- `backend/app/casepack/checks.py` — `PRECONDITION_VOCABULARIES`, **read off the model's own
  annotations** via `_closed_vocabulary()`. Deliberately not restated: a copied closed
  vocabulary is the defect `CONTRACTS.md` `placement` and finding `1.5-RC-002` are about,
  and this check exists to give that vocabulary a diagnostic, not a third home.
- `backend/app/casepack/validate.py` — `check_precondition_vocab_raw`, wired in beside
  `check_policy_vocab`.
- `backend/app/casepack/validate_messages.yaml` — `E29_vocab` **variant**. No new code:
  `E29` already means *"every event precondition has one known, exact field shape"*, and
  `I1`'s set equality would break on an invented code.
- `backend/tests/check_event_preconditions.py` — 7 new assertions, both directions
  (`E29` raised · `E00` **not** raised · `events.yaml` and the field named · `minimal_valid`
  still clean).

```
$ python3 backend/tests/check_event_preconditions.py | tail -8
PASS  closed precondition vocabularies are placement and severity
PASS  out-of-vocabulary placement does not collapse to E00
PASS  out-of-vocabulary placement raises E29 and nothing else
PASS  E29 names events.yaml, the placement field, and the offending value
PASS  out-of-vocabulary severity does not collapse to E00
PASS  out-of-vocabulary severity raises E29 and nothing else
PASS  E29 names events.yaml, the severity field, and the offending value
PASS  minimal_valid still validates clean with the raw vocabulary check in place
```

---

## 4. `B5` — the four `Labels` sections

### 4.1 Before and after

```
                                   BEFORE                     AFTER
$ grep -o '.label("[a-z_]*"' backend/app/casepack/validate.py | sort | uniq -c
      7 capabilities              7 capabilities
      1 roles                     4 catalog        <-- new
      1 stakeholders              2 entities       <-- new
      2 strategies                1 events
                                  1 questions      <-- new
                                  1 roles
                                  1 stakeholders
                                  2 strategies
                                  2 watch_rules    <-- new
```

`1.1-r2-003` closes when *"1.2's next rework routes those eight subjects through
`lens.label(...)` against the sections this packet added."* Seven of the eight now do:
`E05` · `E09` · `E12` · `E23` · `W04` · `W06` · `W07`, plus `E02`'s entity noun, which sits
in the same prose position as `E23`'s and would otherwise have rendered inconsistently
against it.

### 4.2 Closing check — placeholders in the catalogue, expect non-zero

```
$ grep -c -E "\{(entity_name|item_name|rule_name|question_name)\}" \
    backend/app/casepack/validate_messages.yaml
9
```
Previously **0**. The subject templates were renamed (`{rule}` → `{rule_name}` etc.) so that
the **machine key is still what the `Fix:` line names** — `E12`'s fix says *"set warn_above
on 'ord_cap_01'"*, which is the string an author edits, while the locator line leads with
the business name. Both halves of `GOVERNANCE §2.1` at once.

### 4.3 Demonstrated on a pack that authors the sections

Riverside, one threshold pair nulled:

```
BEFORE   ERROR  E12  Watch rule ord_cap_01              watch_rules.yaml:11
AFTER    ERROR  E12  Watch rule Order fulfilment capacity  watch_rules.yaml:11
         Fix: … set warn_above or critical_above on 'ord_cap_01' …     <-- machine key kept
```

And `W07`, with the item's authored label:

```
  WARN   W07  Catalog item POS System 2011    catalog.yaml:54
```

`E23`, which reads **two** of the four sections at once — `questions` for the subject and
`entities` for the noun in the message — with the machine key kept in the `Fix:` line:

```
  ERROR  E23  Question Do we know our stock figures are right?  questions.yaml:1
         Needs Stock information at 'individual_transaction' detail, and nothing this
         company can buy produces it.
         Fix: add inventory at 'individual_transaction' or finer to owns_entities on an item
              in catalog.yaml …
         Field: inventory_accuracy.requires_entities.inventory
```

Before this packet that read *"Question inventory_accuracy … Needs inventory information"* —
engine vocabulary in the two places an instructor actually reads (`GOVERNANCE §2.1`).

Fixture packs that author **no** label sections still fall back to the machine key
(`broken_E02`, `broken_E23` render unchanged), so the change adds a business name where one
was authored and changes nothing where one was not.

### 4.4 `E07`'s widened `misc` catch-all (`1.1-r2-004`)

`check_labels` built `everywhere` from **every** section and used it as the fallback for
`misc`-class references, so the fix line *"add '{key}' under **misc**"* named one of twelve
accepted answers. The fallback is removed: a label is accepted in the section its reference
names, and nowhere else.

**Falsification run** — `redesign_close` moved out of `misc:` and into `catalog:` in a probe
copy of Riverside. Before the change this validated clean. Now:

```
  ERROR  E07  redesign_close                  catalog.yaml:117
         This authored label has no wording anyone can read, so a screen would show the raw key.
         Fix: add 'redesign_close' under misc in labels.yaml.
         Field: accounting_package.process_option.label_key
```

Riverside authors all its `misc`-class labels under `misc` and still validates 0/0; all 43
fixtures still behave as named.

### 4.5 `E21` — DEVIATION, reported not resolved

`E21` is the eighth code and it is **not** routed. `labels.events` maps an event's
`body_key` to *a sentence or a paragraph of in-world prose* — `docs/casepack-schema.md`
says so in a call-out box: *"`events` is not a name map … There is currently nowhere to
author an event's **name**."* Routing `E21`'s subject through it would print a persona's
message as a locator line, which is worse than the machine key.

That is open item **`R1`**, a schema change (a new `event_titles` section), and it belongs to
whoever owns the `labels.yaml` schema — not to this packet, which was told not to extend
scope. The reason is recorded **in the code at the call site**, not only here, so the next
reader does not re-derive it.

---

## 5. `B11` — `erp_suite.config_tiers`

### 5.1 The derivation reproduces, exactly

```
$ python3 - <<'EOF'
import json, statistics
from collections import defaultdict
rows = json.load(open('backend/harvest/mis_lite/erp_modules_master.json'))
g = defaultdict(list)
for r in rows: g[r['module_level']].append(r['cost_value'])
base = statistics.mean(g['Basic'])
for level in ('Basic', 'Mid', 'Advanced'):
    m = statistics.mean(g[level])
    print(f'{level:<9} n={len(g[level]):>2}  mean={m:>9.2f}  multiplier={m/base:.4f}')
EOF
Basic     n= 7  mean= 44571.43  multiplier=1.0000
Mid       n= 4  mean= 70000.00  multiplier=1.5705
Advanced  n=10  mean=115000.00  multiplier=2.5801
```

`catalog.yaml` authors `1.0 / 1.57 / 2.58`. Those are the three multipliers rounded to two
places, and `44571` is the same Basic mean the `on_prem` capex carries. **Shown, in
`PROVENANCE.md` §2a, with the script that regenerates it.**

### 5.2 Finding `1.3-004` is wrong, and that is reported rather than quietly dropped

The audit's `R2` reading took *"the seven Basic-level module rows"* to mean seven **families**
sampled at min / mid / max. The note means the seven rows whose `module_level` column is
literally `Basic`. Both readings return `44571` for Basic — which is why the coincidence
survived a careful audit — and they diverge only on Mid and Advanced, where `n` is 4 and 10,
not 7 and 7. `GOVERNANCE §7` says a disagreement is itself the finding; it is stated in place
in `PROVENANCE.md` §2a rather than resolved by silently rewriting either side.

### 5.3 Closing check — every `config_tiers` multiplier is derived or marked

| Multipliers | Disposition |
|---|---|
| `erp_suite` **capex** ladder | **Harvested.** Derivation shown, `PROVENANCE.md` §2a |
| `erp_suite` **compute** ladder, opex, lead times | Already marked — `catalog.yaml:413`, `TODO: calibrate` |
| Every **other** item's `config_tiers`, capex and compute | **Newly marked.** `catalog.yaml:41`, `TODO: calibrate -- every config_tiers multiplier except erp_suite's capex. Owner 1.7.` Listed as its own row in `PROVENANCE.md` §7 |

`GOVERNANCE §4.9` rule 5 — *estimates are allowed; unmarked estimates are not*. **No numeric
value in the pack was changed by this item.** `TODO: calibrate` markers on authored values:
33 → **34**, and `PROVENANCE.md` §7's header, table and total were all updated to match.

---

## 6. `B17` and the standing gates

### 6.1 `B17` closing check — every extracted table has a disposition

```
$ python3 - <<'EOF'
import json, pathlib
manifest = json.load(open('backend/harvest/mis_lite/_manifest.json'))
prov = pathlib.Path('backend/packs/riverside_grocery/PROVENANCE.md').read_text()
tables = sorted(manifest['rows_per_table'])
missing = [t for t in tables if t not in prov]
print(f"{len(tables)} extracted · {len(tables) - len(missing)} disposed · missing: {missing}")
EOF
34 extracted · 34 disposed · missing: []
```

Before this packet: **8 missing** — the six `1.3-009` names, plus `ecommerce_features_master`
and `business_processes_master`, which the audit correctly recorded as *"recorded in §2's
prose, just not tabulated"*. All eight now have rows in `PROVENANCE.md` §5a, each written
against the extracted JSON. The check itself is pasted into §5a so it stays runnable rather
than becoming a claim.

`change_management_master` (8 costed rollout options) and `change_management_strategy_fit`
(20 fit cells) are recorded as a **real gap with a named owner (1.7)**, not as a discard —
including that `preferences/training.yaml`'s provenance string overstates what was done with
them.

### 6.2 Fixture matrix · `I1` · `I5`

```
$ python3 backend/tests/check_fixture_matrix.py ; echo "exit=$?"
…
I1  implemented codes : 38 [E00 … W08]
I1  spec-named codes  : 38 [E00 … W08]
I1  set equality      : PASS

I5  minimal_valid                      text=  0 json=  0 identical=yes
I5  warn_heuristics                    text=  8 json=  8 identical=yes
I5  riverside_grocery                  text=  0 json=  0 identical=yes
I5  packs/  (directory mode)           text= 91 json= 91 identical=yes
I5  directory-mode pack attribution    every record names its pack

all 43 fixtures behave as named; 37 of 38 codes exercised, ['I8'] recorded as unfixturable
I1 set-equal against the spec; I5 identical in single-pack and directory mode
exit=0
```

### 6.3 Riverside — 0 errors / 0 warnings, text and JSON

```
$ python3 -m app.casepack.validate packs/riverside_grocery
  riverside_grocery 0.1.0 (schema 1) — grocery_retail, 6 rounds
  ✓  7 capabilities · all required roles resolve
  ✓  4 strategies · weights sum to 1.000
  ✓  13 events · all preconditions resolve
  ✓  demand curves cover rounds 1–6
  0 errors · 0 warnings · exit 0

$ python3 -m app.casepack.validate --json packs/riverside_grocery ; echo "exit=$?"
[]
exit=0
```

### 6.4 `pytest`

```
$ cd backend && python3 -m pytest -q
...................................                                      [100%]
35 passed in 5.86s
```

### 6.5 Every `check_*.py`

```
$ python3 backend/tests/check_fixture_matrix.py       -> exit 0  (43/43, I1, I5)
$ python3 backend/tests/check_event_preconditions.py  -> exit 0  ("All focused precondition checks passed")
$ python3 backend/tests/check_policy_options.py       -> exit 0  ("all 13 policy-option contract checks pass")
$ python3 backend/tests/check_w08_rounds.py           -> exit 0
```

### 6.6 Seed command (`GOVERNANCE §4.9` rule 4)

```
$ cd backend && python3 -m app.casepack.seed riverside_grocery
7 capabilities, 14 catalog items, 4 strategies
cost_leadership weights sum 1.000
differentiation weights sum 1.000
customer_supplier_intimacy weights sum 1.000
focus_strategy weights sum 1.000
pinned figures: round 3; capital 46000 of 220000; run_rate 58300; scorecard 61/48/39/27;
signals 3; inbox 3; staff 2.0; load 3.4; over 170; review_capital 174000 of 220000;
remaining 46000; run_rate_after 62200; run_rate_before 58300
warehouse people 34 contribution 25
store_operations people 140 contribution 44
finance people 8 contribution 81
```

`remaining 46000` is now **computed** from the review block rather than read from a second
authored field — the `B10` change proving itself in the seed path.

### 6.7 No casepack-identity branching

```
$ grep -rniE "riverside|grocer" backend/app/engine/ | wc -l
0
```

Widened to `backend/app/` there are **4** hits, all pre-existing on `main` and none of them a
branch: they are the demo CLI's scenario registry and its `--scenario riverside_r3` help text
(`app/seed/__init__.py:4`, `app/seed/demo.py:8,24,65`) — a name in a lookup table, not engine
behaviour conditioned on pack identity. This branch added none of them and changed no file
under `backend/app/seed/`.

### 6.8 No new required casepack fields

The only schema delta on this branch is a **removal** (`B10`). No field was added to any
model, required or optional.

### 6.9 `ruff`

```
$ cd backend && ruff check app/casepack/checks.py app/casepack/models.py app/casepack/seed.py \
      app/casepack/validate.py scripts/harvest_readback.py tests/check_event_preconditions.py
All checks passed!
```

The constraint is *ruff clean on changed files*, and it is met. For the record, the wider
tree is **not** clean and this branch did not make it so — `ruff check app/ scripts/ tests/`
reports 8 pre-existing findings in three files none of which this branch touches
(`git status` lists none of them):

```
app/engine/state.py:20:36        F401  `dataclasses.field` imported but unused
app/engine/technology.py:55:5    F841  local variable `serving` assigned but never used
tests/test_policy_dimension.py   E702  ×6, multiple statements on one line
```

Reported rather than fixed: `app/engine/*` is engine code this packet is forbidden to
change, and drive-by lint edits inside a rework packet are how scope escapes.

### 6.10 `git diff --check`

```
$ git diff --check 3ae0b6d ; echo "exit=$?"
exit=0
```

---

## 7. `B10` — `capital_remaining`'s second home

### 7.1 Closing check

```
$ grep -c "capital_remaining" backend/app/casepack/models.py
1
```
Was **2** (`models.py:58` `RoundBudgetState`, `models.py:99` `ReviewState`).

### 7.2 Which home went, and what it could have broken

Both were **derived from the identical expression** —
`review.capital_available - review.capital_committed` — and both were schema-**required**,
which is why 1.3 correctly stopped: eliminating one is a 1.1 schema change that 1.3's scope
excluded (`SPEC_PROTOCOL §3`, *prefer elimination over reconciliation*).

`ReviewState.capital_remaining` is the one removed. The Review block already carries both
operands adjacent to it, so it is the textbook second home;
`budget.capital_remaining` is the figure the capital strip displays on every screen and the
one `seed.py` reports, so it survives as the single authored home.

Blast radius, checked before the change rather than after:

| Contract | Reads it? | Outcome |
|---|---|---|
| **Scorer / engine** (`backend/app/engine/*`) | **No** — `grep` returns zero | Untouched. No engine file changed on this branch |
| **1.4 seed** (`backend/seeds/riverside_r3.py`) | **No** | Untouched |
| **Loader** (`models.py` `StrictModel`, `extra="forbid"`) | Yes | A pack still authoring the key now **fails to load**. That is the intended migration signal, and it is documented in `CONTRACTS.md`. All 44 in-repo packs (43 fixtures + Riverside) were migrated in this same commit — one line deleted each, **no value changed** |
| **Validator `E14`** | Yes | One of two identical derivation rows removed; see §7.3 |
| **`app/casepack/seed.py`** | Yes | Now prints the derivation |
| **`scripts/harvest_readback.py`** | Yes | Row recomputes it; the CG-6 **declared conflict is still declared**, not quietly dropped |

Nothing was broken that could not be migrated inside this packet, so the instruction's
STOP condition was not met.

### 7.3 The invariant is preserved, not weakened

`E14` checked the same fact twice against the same expression. It now checks it once.
`broken_E14` — whose trigger is `budget.capital_remaining: 40000` — still fires `E14`, and
the fixture matrix confirms it. `harvest_readback.py`:

```
  Declared conflicts (reported, not silently reconciled):
    budget.capital_remaining     pack 46000 · derived 46000 · mockups 44000
    review remaining (derived)   pack 46000 · derived 46000 · mockups 46000

  47/47 matched, 0 mismatched, 2 declared conflicts
```

The `$44,000` mockup conflict is register item `B14`, ruled **ACCEPT — superseded** by §2 of
the scope file. It stays **declared**. It was not touched.

### 7.4 Documents

- `CONTRACTS.md` — new `capital_remaining` entry: one home, the derivation, the explicit
  `NOT a field on ReviewState`, producers, consumers, and the standing `B14` conflict.
  Header `Last updated` bumped.
- `docs/casepack-schema.md` — call-out under `initial_state`, with the migration instruction.
- `backend/packs/riverside_grocery/pack.yaml` — the two CG-6 comment blocks said *"the second
  home is NOT eliminated"* and *"the schema requires [it] and 1.3 could not remove"*. Both
  rewritten; leaving them would have made the pack lie about its own schema.

---

## 8. Register Reconciliation

> `findings/OPEN-REGISTER.md` §I, amendment 3. **Every register item naming this packet, with
> its closing check re-run.** This is the step `dad0989` skipped — it fixed five section-B
> items and updated none of their rows. `findings/OPEN-REGISTER.md` is updated **in the same
> commit as this file.**

| # | Closing check, as the register words it | Run | Result |
|---|---|---|---|
| **B5** | *grep the catalogue for the four section placeholders; expect non-zero* | `grep -c -E "\{(entity_name\|item_name\|rule_name\|question_name)\}" backend/app/casepack/validate_messages.yaml` | **9** (was 0) → **CLOSED**, with `E21` carried to `R1` (§4.5) |
| **B7** | *author an out-of-vocabulary `placement`; expect a targeted code, not `E00`* | §3.2 | `E29`, `events.yaml:2`, field named → **CLOSED** |
| **B10** | `grep -c "capital_remaining" backend/app/casepack/models.py` → `1` | §7.1 | **1** → **CLOSED** |
| **B11** | *each `config_tiers` multiplier carries a derivation or a `TODO: calibrate`* | §5.3 | **CLOSED** |
| **B13** | *one authored value, cited to its harvest source, with `components.html` agreeing* | §2.3 | **CLOSED.** Value `62`, cited in `PROVENANCE.md` §11, mockups already agreed. **Org pin did not move** |
| **B17** | *every table in the §5.1 transform map has a disposition line* | §6.1 | `34 disposed · missing: []` → **CLOSED** |
| **B14** | 16 mockups at `$44,000` vs a derivation of `46,000` | scope §2 | **ACCEPT — superseded.** NOT BUILT, and deliberately still printed as a declared conflict by `harvest_readback.py` (§7.3) |
| **B15** | 630 placeholder-seeded mapping rows | scope §2 | **ACCEPT.** NOT BUILT. Still recorded in `PROVENANCE.md` §5 |
| **B16** | 38 `TODO: calibrate` | scope §2 | **OPEN BY DESIGN → 1.7.** NOT BUILT. **Report:** the register's *38* was a `grep` over the whole pack **directory**, which counts four prose mentions inside `PROVENANCE.md` itself. Marked values in pack YAML were **33**, and are **34** after `B11` added one. Disposition unchanged |

### Also raised by this packet, and owned

| Item | What | Owner |
|---|---|---|
| **`R1`** (was already open, now blocking half of `B5`) | There is nowhere in `labels.yaml` to author an event's **name**, so `E21` still leads with a machine key. A schema change — a new label section — not authorable and not a validator fix | `labels.yaml` schema · **1.1 next** |
| **`1.3-004` is factually wrong** | The `erp_suite` derivation *does* reproduce, on the source's own `module_level` column (§5.1). Recorded in `PROVENANCE.md` §2a in place | *(closed by this packet — recorded, not silently dropped)* |
| **`preferences/training.yaml` provenance overstates** | Its string claims *"mis_lite change management tables reworked into training preferences"*; five archetype coverage entries are not a rework of 8 costed options + 20 fit cells. Recorded in `PROVENANCE.md` §5a | **1.7 calibration** (with the two change-management tables) |

---

## 9. What this packet deliberately did not do

- **No engine or scoring logic changed.** `backend/app/engine/` and `backend/seeds/` are
  untouched. The `B13` re-derivation is *reported* (pin unmoved); no pin was rewritten.
- **`B14` · `B15` · `B16` untouched**, per §2 of the scope file.
- **`E21` not forced through a label map that holds prose** — reported as `R1` instead.
- **`1.5-RC-002` not touched.** `B7`'s fix was routed through a raw-stage check precisely so
  it would not need to alter the `Literal` at `models.py:361` that `readiness-spec.md:14-15`
  froze and that the register marks **RULING REQUIRED**.
- **No self-audit.** `GOVERNANCE §6.1`.
