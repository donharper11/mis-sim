# 1.3 — mis_lite Harvest → Riverside Pack v1 · Build Spec

**Authored under** `SPEC_PROTOCOL.md` v1.1 · **Author:** Claude · **Date:** 2026-07-26
**Phase:** 1 · **Depends on:** 1.1 (schema), 1.2 (validator) · **Blocks:** 1.4, 1.7

> Fill the skeleton with real content. Mechanical where possible, judged where not — and
> the spec says which is which, because a builder should never be guessing whether it is
> transforming or authoring.

---

## 0. Spec Basis

**Read in full:** `design/01-mis_lite-harvest.md` (the whole harvest analysis, including
§3 on the component-master problem and §4 on seed quality) · `handoffs/1.1-casepack-schema/spec.md` ·
`CONTRACTS.md` (the `trialNNN` note, the fit-multiplier conversion warning) ·
`mis_lite` live schema, 79 tables, masters sampled.

**Extraction sufficiency:** covered for the tables named in `design/01` §2. The nine
`*_mapping` tables (~2,100 rows) were sampled, not read exhaustively — flagged as
**pre-flight row 5**, because the transform's correctness depends on their uniformity.

---

## 1. Purpose and scope

**In scope:** transform harvestable mis_lite content into `packs/riverside_grocery/`;
author what cannot be transformed; produce a provenance record.

**Out of scope:** changing the schema (that is 1.1 — if content will not fit, **stop and
report**) · authoring a second pack (6.1) · any engine code.

---

## 2. Project-specific statements

**Scoring factors touched:** authors inputs to all of them. **Casepack keys read/written:**
all of `riverside_grocery`. **Instance scoping:** N/A.
**Business-language check:** every harvested description becomes student-visible text and
must pass `GOVERNANCE.md §2.1`. mis_lite's descriptions are largely textbook prose —
invariant I3 greps the result.

---

## 3. Settled decisions

1. **Read-only against mis_lite.** No writes to `192.168.50.38`, ever.
2. **Drop `trialNNN`** on every table (`CONTRACTS.md`).
3. **Only ~19 of 45 `component_types_master` rows become catalog items.** The other ~26 are
   Chapter 5 *concepts* and go to `docs/curriculum-coverage.md`, not the catalog
   (`design/01` §3). The buildable list is enumerated there.
4. **Fit multipliers are converted, not copied.** mis_lite uses un-normalised multipliers
   around 1.0; the schema requires weights summing to 1.0 (`CONTRACTS.md`). Conversion is
   normalisation per strategy, and the raw values are retained in the provenance file.
5. **The 14 stakeholders become archetypes**; Riverside persona instances are **authored
   new** — mis_lite has roles, not people.
6. **Riverside's fixed figures are authoritative.** Where harvested content conflicts with
   `handoffs/0.4a-mockup-pilot/spec.md §5.4`, §5.4 wins — the mockups and the engine must
   agree.

---

## 4. Open decisions

| # | Question | Criteria | Reporting |
|---|---|---|---|
| **O1** | mis_lite's `business_process_mapping` shows uniform placeholder values (`design/01` §4). Harvest it or re-author? | **Default: do not harvest. Re-author from the archetype defaults in 1.1 §5.7.** Importing placeholder data that *looks* authored is worse than an honest default | Record, with the row count discarded |
| **O2** | mis_lite descriptions are textbook prose ("Traditional rack servers suitable for basic workloads"). Keep or rewrite? | **Default: rewrite to business language.** These become student-visible. Keep the originals in provenance | Record |
| **O3** | `market_potential` (50 rows) — harvest now or defer with the market layer? | **Default: harvest into the pack but mark `unused_until: market_layer`.** Free to carry, costly to re-derive (`design/04` G6) | Record |

---

## 5. Design

### 5.1 Transform map

| mis_lite source | Rows | → pack destination | Mode |
|---|---|---|---|
| `strategy` | 4 | `strategies.yaml` identity + labels | mechanical |
| `objectives` | 5 | `labels.yaml` declaration vocabulary | mechanical |
| `stakeholders` | 14 | platform archetypes (shared, not pack) | mechanical |
| `component_strategy_fit` | 168 | `strategies.yaml` weights — **normalised** | transform |
| `component_types_master` | 45 → ~19 | `catalog.yaml` | **judged** — see §5.2 |
| `it_infrastructure_addons_master` | 11 | `platform.yaml` shared services | transform |
| `maintenance_support_levels` | 3 | `platform.yaml` staff-capacity tiers (G1) | mechanical |
| `integration_services` | 3 | `platform.yaml` integration tiers | mechanical |
| `deployment_types`, `hardware/network/database_types` | 12 | `catalog.yaml` option ladders | transform |
| `change_management_master` + `_strategy_fit` | 8 + 20 | training / process / communication options | transform |
| `erp_modules_master` | 21 | `catalog.yaml` enterprise apps | transform |
| `ecommerce_features_master` | 9 | `catalog.yaml` | transform |
| `mis_initiatives_master` | 12 | `catalog.yaml` | transform |
| `data_governance_policies` | 3 | `policies.yaml` | transform |
| `security_incidents`, `regulatory_penalties` | 6 | `events.yaml` seeds | judged |
| `competitors` | 5 | `competitors.yaml`, `unused_until: market_layer` | mechanical |
| `market_potential` | 50 | same (O3) | mechanical |
| `stakeholder_infrastructure_preference` | 14 | `preferences/platform.yaml` | mechanical |
| `business_process_mapping` | 112 | **discarded** (O1) | — |
| per-domain `*_decisions` tables | 0 | **discarded** — runtime shape, superseded | — |

### 5.2 The judged part — catalog items

The ~19 buildable rows carry only `cost_value` in mis_lite. Everything else in the
attribute vector (capacity, availability, service life, staff load, sizing driver,
entity ownership, integration requirements, training tiers) **does not exist and must be
authored.**

The builder does **not** invent these freely. Author them against:
- the fixed figures in `0.4a/spec.md §5.4` where they overlap
- a stated rationale per item, recorded in provenance
- archetype defaults for anything not case-specific

**If a value cannot be justified, mark it `TODO: calibrate` and report it.** 1.7's harness
is where guesses get tested; a confident wrong number is worse than a flagged one.

### 5.3 Provenance record

`packs/riverside_grocery/PROVENANCE.md` — mandatory, one row per harvested collection:

```
| pack field | mis_lite source | rows in | rows out | mode | notes |
|---|---|---|---|---|---|
| strategies[].capability_weights | component_strategy_fit | 168 | 76 | normalised | only the ~19 buildable components transfer; raw multipliers below |
| catalog[] | component_types_master | 45 | 19 | judged | 26 concepts → docs/curriculum-coverage.md |
| … |
```

Also records: every discarded table with the reason, every `TODO: calibrate`, and the raw
fit multipliers before normalisation.

**A harvest with no provenance file is not done.** In two years nobody will remember why
26 rows vanished.

---

## 6. Invariants

| # | Invariant | Check | Expected |
|---|---|---|---|
| I1 | No writes to mis_lite | `grep -rniE "INSERT\|UPDATE\|DELETE\|ALTER\|DROP" backend/scripts/harvest*` | zero |
| I2 | No `trialNNN` anywhere in the pack | `grep -rn "trial" packs/riverside_grocery/` | zero |
| I3 | No textbook prose in student-visible labels | `grep -rniE "traditional\|suitable for\|optimized for\|designed for" packs/riverside_grocery/labels.yaml` | zero |
| I4 | Weights normalised, not copied | every strategy's `capability_weights` sums to 1.0 ±0.001 | 4/4 |
| I5 | Every discarded table appears in PROVENANCE | cross-check §5.1 discards vs the file | all present |
| I6 | Pack passes 1.2 with zero ERRORs | `validate_casepack packs/riverside_grocery` | exit 0 |
| I7 | §5.4 figures match the pack | script comparing the 0.4a fixed data to loaded pack values | exact |

---

## 7. Pre-Flight Verification Register

| # | Claim | Tag | Check | Expected |
|---|---|---|---|---|
| 1 | 1.1 and 1.2 merged | `[V]` | `ls backend/app/casepack/{models,loader,checks}.py backend/app/casepack/validate*` | all present |
| 2 | mis_lite reachable read-only | `[V]` | `PGPASSWORD=… psql -h 192.168.50.38 -U donwh -d mis_lite -c "select 1"` | 1 |
| 3 | Row counts match `design/01` §2 | `[V]` | count each table in §5.1 | match, or report drift |
| 4 | `component_strategy_fit` = 168 | `[V]` | `select count(*) from component_strategy_fit` | 168 |
| 5 | The nine `*_mapping` tables are uniform enough to transform mechanically | `[A]` | for each: `select ideal_value, count(*) from <t> group by 1 order by 2 desc limit 5` | **if one value dominates, that table is placeholder-seeded — report before transforming** |
| 6 | Skeleton pack exists from 1.1 | `[V]` | `ls packs/riverside_grocery/` | files present |

Row 5 is the important one. `design/01` §4 found this pattern in one table; the check
looks for it in all nine.

---

## 8. Build phases

1. **Read-only extraction script** → intermediate JSON, one file per source table.
   *Verify:* I1; row counts match pre-flight.
2. **Mechanical transforms** (the `mechanical` rows in §5.1). *Verify:* counts in = counts
   out, or a documented reason.
3. **Normalisation transforms** — fit multipliers, option ladders. *Verify:* I4; raw values
   preserved in provenance.
4. **Judged authoring** — catalog attribute vectors, event seeds, persona instances.
   *Verify:* every value justified or marked `TODO: calibrate`; I7.
5. **Provenance + curriculum-coverage doc.** *Verify:* I5; the 26 concepts are documented.
6. **Validate.** *Verify:* I6 — exit 0.

---

## 9. Definition of Done

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–6, esp. row 5 per table | | |
| Phases 1–6 verified | | |
| I1 read-only | | |
| I2 no `trialNNN` | | |
| I3 no textbook prose in labels | | |
| I4 weights normalised | | |
| I5 discards documented | | |
| I6 validator exit 0 | | |
| I7 0.4a figures match | | |
| O1, O2, O3 recorded | | |
| `PROVENANCE.md` complete | | |
| `docs/curriculum-coverage.md` — the 26 concepts | | |
| Every `TODO: calibrate` listed in the report | | |
| Browser / auth / instance canaries | | **N-A** — headless |
