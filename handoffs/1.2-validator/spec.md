# 1.2 — Casepack Validator · Build Spec

**Authored under** `SPEC_PROTOCOL.md` v1.1 · **Author:** Claude · **Date:** 2026-07-26
**Phase:** 1 · **Depends on:** **1.1 as approved** · **Blocks:** 1.3, 6.1

> An unvalidated pack does not fail loudly — it runs and scores wrongly, and you find out
> in week 9. This is the guardrail that makes packs 2–5 authorable by someone who is not
> the schema's author.

---

## 0. Spec Basis

**Read in full:** `handoffs/1.1-casepack-schema/spec.md` (the schema being enforced) ·
`design/01-mis_lite-harvest.md` §4 (the seed-quality failures this must catch) ·
`GOVERNANCE.md` §5 (the validator gate) · `CONTRACTS.md`.

**Extraction sufficiency:** covered. 1.1's `checks.py` is the substrate; this wraps and
extends it.

---

## 1. Purpose and scope

A CLI that refuses to let a broken pack reach a section.

**In scope:** `validate_casepack <pack_dir>` · three severity levels · human-readable
output naming file and field · non-zero exit on error · a machine-readable `--json` mode
for 5.6's instructor view.

**Out of scope:** fixing anything · loading to DB (2.5) · UI (5.6) · validating *content
quality* beyond the heuristics in §5.3.

---

## 2. Project-specific statements

**Scoring factors touched:** none directly — it protects every one of them by ensuring
their authored inputs exist and resolve. **Casepack keys read:** all.
**Instance scoping:** N/A. **Business-language check:** validator output is for
instructors, not engineers — errors say *"capability 'Customer Service' needs customer
data at individual level, but no catalog item can hold it"*, not
`required_entities[1].min_level_of_detail unsatisfiable`.

---

## 3. Settled decisions

1. **Three severities.** `ERROR` blocks loading. `WARN` loads but is reported.
   `INFO` is advisory.
2. **Exit codes.** `0` clean · `1` errors present · `2` validator itself failed.
3. **Every check names its fix.** A message that states a problem without a next action
   is incomplete.
4. **Wraps 1.1's `checks.py`** rather than reimplementing it.

---

## 4. Open decisions

| # | Question | Criteria | Reporting |
|---|---|---|---|
| **O1** | Should `WARN` block a *production* section while allowing a draft? | **Default: no — WARN never blocks.** A blocking warning is an error under another name. 5.6 surfaces warnings to the instructor; the decision to run anyway is theirs | Record |
| **O2** | Validate cross-pack uniqueness of `pack_key`? | **Default: yes, when given a directory of packs**; skip for a single pack | Record |

---

## 5. Design

### 5.1 Structural checks — ERROR

Inherited from 1.1 §6 (I3–I8), plus:

```
E01  a required_role no catalog item can fill
E02  a required_entity at a level_of_detail no catalog item can own
E03  strategy capability_weights do not sum to 1.0 (±0.001)
E04  demand_curve length ≠ pack.rounds
E05  cleared_by references an unknown action type
E06  event precondition references an unknown signal, capability, or entity
E07  a label key referenced anywhere is absent from labels.yaml
E08  a persona bound to an archetype outside the platform's 14
E09  must_feed / must_be_fed_by names a capability that does not exist
E10  duplicate key within any collection
E11  schema_version newer than this validator understands
```

### 5.2 Coherence checks — ERROR

```
E20  a capability with no watch rule — it can never raise a signal, so it is
     invisible to responsiveness scoring and effectively unmanaged
E21  an event whose preconditions can never all be true simultaneously
E22  a strategy whose highest-weighted capability has no catalog path to full coverage
E23  a management question requiring an entity/level no catalog item can produce
```

E20 is the one most likely to be hit by a real author and least likely to be noticed
without it.

### 5.3 Seed-quality heuristics — WARN

Directly from the harvest's findings (`design/01` §4), where `business_process_mapping`
showed identical `ideal_value 85.00` and identical weights across all six stakeholders —
placeholder seeding indistinguishable from authored judgement.

```
W01  ≥N preference rows share an identical (ideal_value, weight) tuple
     → "looks like placeholder seeding, not authored judgement"
W02  a capability no strategy weights above 0.05 — content nobody will engage
W03  an event with no strategy_affinity — it will fire regardless of declaration
W04  a catalog item reachable from no capability — dead content
W05  the deck contains no event for a round
W06  every training option has coverage 1.0 — the tier choice is not a choice
W07  no accepted-risk / no decoy in true_cost_categories — TCO forecast is trivially winnable
```

### 5.4 Output

```
$ validate_casepack packs/riverside_grocery

  riverside_grocery 0.1.0 (schema 1) — grocery_retail, 6 rounds

  ✓  7 capabilities · all required roles resolve
  ✓  4 strategies · weights sum to 1.000
  ✓  31 events · all preconditions resolve
  ✓  demand curves cover rounds 1–6

  ERROR  capabilities.yaml:41  customer_service
         Needs customer data at individual level. No catalog item can hold it.
         Fix: add a catalog item with owns_entities CUSTOMER at individual_record,
              or lower min_level_of_detail.

  WARN   watch_rules.yaml       financial_reporting has no watch rule
         It can never raise a signal, so it is invisible to responsiveness scoring.

  WARN   preferences/catalog.yaml  18 rows share (ideal_value 85.00, weight 0.80)
         Looks like placeholder seeding rather than authored judgement.

  1 error · 2 warnings · exit 1
```

---

## 5.5 Seed — real fixture packs *(GOVERNANCE §4.9)*

```
seed        backend/tests/fixtures/packs/
              minimal_valid/     a small COHERENT pack that passes clean
              broken_<CODE>/     one per error code, minimally broken
command     validate_casepack backend/tests/fixtures/packs/<name>
demonstrate exit 0 on minimal_valid · exit 1 with the named error on each broken pack
            exit 0 on the real riverside_grocery from 1.1
```

`minimal_valid` is real content, not empty scaffolding — a two-capability company that
would actually run.

---

## 6. Invariants

| # | Invariant | Check | Expected |
|---|---|---|---|
| I1 | Every ERROR message names a file and a fix | `grep -c "Fix:" $(grep -rl "ERROR" backend/app/casepack/validate*)` vs error-code count | equal |
| I2 | Exit 1 whenever ≥1 ERROR | run against a deliberately broken pack | exit 1 |
| I3 | Exit 0 with warnings only | run against a warn-only pack | exit 0 |
| I4 | No pack-identity branching | `grep -rniE "riverside\|grocer" backend/app/casepack/validate*` | zero |
| I5 | `--json` is parseable | `validate_casepack --json … \| python -m json.tool` | valid JSON |

---

## 7. Pre-Flight Verification Register

| # | Claim | Tag | Check | Expected |
|---|---|---|---|---|
| 1 | 1.1 merged; `casepack/models.py` and `checks.py` exist | `[V]` | `ls backend/app/casepack/` | both present |
| 2 | Skeleton pack loads clean under 1.1 | `[V]` | `python -m app.casepack.loader packs/riverside_grocery` | no exception |
| 3 | 1.1's `checks.py` exposes the eight invariant functions | `[A]` | `grep -n "^def " backend/app/casepack/checks.py` | ≥ 8 |
| 4 | Action-type enum exists for E05 | `[A]` | `grep -rn "action_type\|ActionType" backend/app/` | found, or **NEW — declare it here** |

---

## 8. Build steps

1. **Structural checks** E01–E11 wrapping 1.1's `checks.py`. *Verify:* each fires against a
   purpose-broken fixture; paste output.
2. **Coherence checks** E20–E23. *Verify:* same, one fixture per code.
3. **Heuristics** W01–W07. *Verify:* W01 fires against the real
   `business_process_mapping` shape from `design/01` §4.
4. **CLI + output formatting + `--json`.** *Verify:* I1–I5.
5. **Fixture suite** — one minimal broken pack per error code, under
   `backend/tests/fixtures/packs/`. *Verify:* every code has a fixture; a code with no
   fixture is untested and is a finding.

---

## 9. Definition of Done

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–4 | | |
| E01–E11 implemented, each with a fixture | | |
| E20–E23 implemented, each with a fixture | | |
| W01–W07 implemented | | |
| CLI output matches §5.4 shape | | |
| `--json` mode | | |
| I1–I5 | | |
| O1, O2 recorded | | |
| Riverside skeleton validates (errors only where 1.3 will fill stubs) | | |
| **Seed** — fixture packs, one per error code, all exercised | | |
| Real Riverside pack validates clean | | |
| Browser / auth / instance canaries | | **N-A** — headless CLI |
