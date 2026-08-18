# 1.3 — mis_lite Harvest → Riverside Pack v1 · Definition of Done

**Builder:** Claude · **Date:** 2026-08-18 · **Branch:** `build/1.3-harvest`, cut from
`main` at `b1ae138` · **Spec:** `handoffs/1.3-harvest/spec.md` v1.1

**Exit condition met.** `backend/bin/validate_casepack backend/packs/riverside_grocery` →
**0 errors · 0 warnings · exit 0**, from a starting state of 20 errors and 7 warnings.
`GOVERNANCE §5`'s *"no casepack reaches a section until `validate_casepack` passes clean"*
is real for the first time.

**Two things this packet did NOT close, both reported rather than improvised:**
CG-6's *elimination* half (schema change, out of scope — §7), and open decision O3's
in-pack landing for `competitors` / `market_potential` (no schema section — §9).

---

## 1. Pre-Flight Verification Register

| # | Claim | Tag | Result | Evidence |
|---|---|---|---|---|
| 1 | 1.1 and 1.2 merged | `[V]` | **PASS** | `ls` returned all five: `models.py`, `loader.py`, `checks.py`, `validate.py`, `bin/validate_casepack` |
| 1a | The 1.1 gate is lifted | `[V]` | **PASS** | model introspection returned exactly the expected output — see below |
| 1b | The `1.2-020` ruling has been made | `[A]` | **PASS** | §5.1b's ruling box, RULED 2026-08-18. Porter's nine are a platform constant; `E13` resolves against it, never against capabilities. Authored accordingly — §6 |
| 1c | Two checks are DEFERRED, not waived | `[A]` | **PASS** | the dispatch names both by name: `I11` (no validator check, `1.2-037`) and `E13`'s `value_chain_coverage` arm (`1.2-020` ruled, not built). Both hand-verified — §6 |
| 2 | mis_lite reachable read-only | `[V]` | **PASS** | `psql -h 192.168.50.38 -U donwh -d mis_lite -tAc "select 1"` → `1` |
| 3 | Row counts match `design/01` §2 | `[V]` | **PASS** | all 28 counted tables match — §2 below |
| 4 | `component_strategy_fit` = 168 | `[V]` | **PASS** | `select count(*) from component_strategy_fit` → `168` |
| 5 | The nine `*_mapping` tables are uniform enough to transform mechanically | `[A]` | **FAIL, REPORTED — five of nine are placeholder-seeded, not one** | §3 below. This is the row the spec calls "the important one" and it found four tables `design/01` §4 did not |
| 6 | Skeleton pack exists from 1.1 | `[V]` | **PASS** | 12 YAML files + `preferences/` present |

**Row 1a, verbatim:**

```
$ cd backend && python3 -c "from app.casepack.models import Labels, WatchRule, PlatformService, Casepack as C; print('metric_kind' in WatchRule.model_fields, 'owns_entities' in PlatformService.model_fields, 'obligation_rules' in C.model_fields, sorted({'entities','catalog','watch_rules','questions'} & set(Labels.model_fields)))"
True True True ['catalog', 'entities', 'questions', 'watch_rules']
```

Exactly the expected output. No `False`, nothing missing. The gate is lifted and no `I6`
deferral was needed.

---

## 2. Pre-flight row 3 — source row counts

Every table in spec §5.1, counted live 2026-08-18. **No drift.**

```
strategy                                 4     component_strategy_fit          168
objectives                               5     component_types_master           45
impact_areas                             5     it_infrastructure_addons_master  11
stakeholders                            14     change_management_master          8
data_governance_policies                 3     change_management_strategy_fit   20
security_incidents                       3     mis_initiatives_master           12
regulatory_penalties                     3     erp_modules_master               21
competitors                              5     ecommerce_features_master         9
market_potential                        50     business_processes_master         8
deployment_types                         3     stakeholder_infrastructure_pref  14
hardware_types                           3     business_process_mapping        112
network_types                            3     component_mapping               630
database_types                           3     mis_initiative_mapping          168
maintenance_support_levels               3     integration_services              3
```

---

## 3. Pre-flight row 5 — the placeholder-seeding audit, all nine tables

**This row fails, and the failure is the finding.** `design/01` §4 found uniform
placeholder seeding in **one** table. Run across all nine, the pattern is in **five, plus
half of a sixth.**

```
table                        rows  distinct  top values                          verdict
------------------------------------------------------------------------------------------
addon_mapping                  84        64  85.00 x14, 75.00 x8, then singles   AUTHORED
business_process_mapping      112         2  85.00 x84, 75.00 x28                SEEDED  (known)
change_mgmt_mapping           112         3  85.00 x56, 75.00 x42, 80.00 x14     SEEDED  (NEW)
component_mapping             630       414  85.00 x22 (3.5% of rows)            AUTHORED
ecommerce_features_mapping    126         3  75.00 x56, 65.00 x56, 70.00 x14     SEEDED  (NEW)
ecommerce_security_mapping    112         3  85.00 x56, 75.00 x42, 80.00 x14     SEEDED  (NEW)
erp_feature_mapping           392       306  80.00 x14, 85.00 x10                AUTHORED
erp_master_mapping            294       141  85.00 x148 (50% of rows)            HALF-SEEDED (NEW)
mis_initiative_mapping        168         4  50.00 x84, 60.00 x42, 65.00 x28     SEEDED  (NEW)
```

Command, per table:
`select ideal_value, count(*) from <t> group by 1 order by 2 desc limit 5`

**Consequence, and why it did not stop the build.** None of the five seeded tables is in
the transform map's *take* list — `business_process_mapping` is the only one the spec
names, and O1 already discards it. The four newly-found tables would have been the source
for e-commerce and change-management preference content, which this packet does not
harvest. **The finding is recorded in `PROVENANCE.md` §5 with all nine dispositions**, and
the honest reading is: mis_lite's `*_mapping` volume is ~2,100 rows of which roughly 1,100
are real authored judgement and roughly 630 are placeholder seeding. Any later packet that
plans to "harvest the 2,100 mapping rows" should read this table first.

**W01 exists for exactly this** and it is clean on the shipped pack.

---

## 4. Invariants

| # | Invariant | Result | Evidence |
|---|---|---|---|
| I1 | No writes to mis_lite | **PASS** | `grep -rniE "INSERT\|UPDATE\|DELETE\|ALTER\|DROP" backend/scripts/harvest*` → zero hits, exit 1. Connection also opened with `PGOPTIONS=-c default_transaction_read_only=on` |
| I2 | No `trialNNN` anywhere in the pack | **PASS** | `grep -rn "trial" backend/packs/riverside_grocery/` → zero hits, exit 1. The extractor excludes `trial*` columns at the SELECT |
| I3 | No textbook prose in student-visible labels | **PASS** | `grep -rniE "traditional\|suitable for\|optimized for\|designed for" backend/packs/riverside_grocery/labels.yaml` → zero hits, exit 1 |
| I4 | Weights normalised, not copied | **PASS 4/4** | `cost_leadership 1.0 · differentiation 1.0 · customer_supplier_intimacy 1.0 · focus_strategy 1.0` |
| I5 | Every discarded table appears in PROVENANCE | **PASS** | `PROVENANCE.md` §5 lists nine discards plus the two market-layer deferrals, each with its reason |
| I6 | **Pack passes 1.2 with zero ERRORs** | **PASS — exit 0** | full output in §5 |
| I7 | §5.4 figures match the pack | **PASS 43/43** | `python3 backend/scripts/harvest_readback.py` → exit 0. Reads from the *loaded* pack, not the YAML text |
| I8 | Every capability can raise a signal; every rule declares its kind | **PASS** | no `E12`, no `E20` in the output; 8 of 8 rules declare `metric_kind` — table in §6 |
| I9 | Every strategy drawn by ≥6 events | **PASS 4/4** | `cost_leadership 9 · differentiation 10 · customer_supplier_intimacy 12 · focus_strategy 12`. No `W08` |
| I10 | Six policy switches, each with a stated cost | **PASS** | `grep -c "^- key:" policies.yaml` → `6`; costs 20000 / 15000 / 9000 / 30000 / 12000 / 7000, none bare |
| I11 | `obligation_rules.yaml` exists and references real entities and policies | **DEFERRED — hand-verified, 0 orphans** | §6, hand-verification 1. No validator check exists (`1.2-037`) |
| I12 | Every referenced label key resolves | **PASS** | no `E07` in the output. Was `E07 ×8`, the pack's largest error group |

---

## 5. I6 — the validator run, in full

```
$ ./backend/bin/validate_casepack backend/packs/riverside_grocery

  riverside_grocery 0.1.0 (schema 1) — grocery_retail, 6 rounds

  ✓  7 capabilities · all required roles resolve
  ✓  4 strategies · weights sum to 1.000
  ✓  13 events · all preconditions resolve
  ✓  demand curves cover rounds 1–6

  0 errors · 0 warnings · exit 0

$ echo $?
0
```

**The path from 20 errors to 0**, each step re-run rather than assumed:

| After | Errors | Warnings | What closed |
|---|---|---|---|
| baseline (`b1ae138`) | 20 | 7 | — |
| `watch_rules.yaml` — `metric_kind` on all 8 rules, 5 new threshold rules | 10 | 7 | `E20 ×5`, `E12 ×2`, `E21 ×2` (CG-1, and `1.2-013` for free) |
| `platform.yaml` — `central_sign_on.owns_entities` + 7 new services | 14 | 7 | `E02 ×1` (`1.2-011`); new roles opened 5 new `E07` |
| `catalog.yaml` — 4 new items, `store_spreadsheets` role fix | 15 | 6 | `W04` |
| `labels.yaml` — 8 process keys, `inventory_app`, 5 new roles, 4 new sections | 4 | 6 | `E07 ×11` (`1.2-012`, `1.2-024`) |
| `policies.yaml` + `events.yaml` — six switches re-keyed; deck 3 → 13 *(validated together, one run)* | 1 | 1 | `E07 ×3`, `W05`, `W08 ×4` (CG-4, CG-2) |
| `strategies.yaml` — firm_infrastructure weighted, raw fit stored; `obligation_rules.yaml` added | 1 | 0 | `W02` (CG-5 adds no code — no check reads it, §6) |
| `pack.yaml` — capital_remaining derived | **0** | **0** | `E14 ×1` (CG-6, partly — §7) |
| `preferences/platform.yaml` — mechanical harvest | **0** | **0** | — |

All 29 validator fixtures still behave as named
(`python3 backend/tests/check_fixture_matrix.py` → exit 0, 29/29). No validator code was
touched: `validate.py` and `models.py` are byte-identical to `b1ae138`.

---

## 6. The two DEFERRED checks — hand-verification, pasted

> Spec §9: *"Deferred is not waived. Record both in `dod.md` with what you verified by hand
> and what remains unchecked by machine."*

### Deferred 1 — `I11`, obligation rules resolving against real entities and policies

**Why deferred:** finding `1.2-037`. `grep -n obligation backend/app/casepack/validate.py`
→ **zero**. A fully orphaned `obligation_rules.yaml` validates identically to a correct
one. Confirmed on this working tree.

**What the machine still cannot see:** whether `entity`, `policy`, `arms` and `cleared_by`
resolve; whether `permissive_value` is meaningful; whether the six switches are covered.

**Hand cross-check, every key, against the shipped pack:**

```
entities.yaml declares : customer, inventory, ledger, order, product, sale,
                         service_ticket, user_account
policies.yaml declares : access_logging, data_access, data_collection, data_egress,
                         data_retention, staff_monitoring
events.yaml declares   : 13 keys
ACTION_TYPES (checks.py:12) : 10 keys

customer_pii_retention
   entity      customer                   OK
   policy      data_retention             OK
   permissive  indefinite                 free string; no pack object to resolve against
   severity    critical                   OK
   cleared_by  add_policy OK , retire_component OK
   arms        privacy_regulator_letter OK
customer_pii_collection
   entity      customer                   OK
   policy      data_collection            OK
   permissive  everything_by_default      free string
   severity    critical                   OK
   cleared_by  add_policy OK , retire_component OK
   arms        privacy_regulator_letter OK , crm_data_exposed OK
sale_detail_open_to_all_staff
   entity      sale                       OK
   policy      data_access                OK
   permissive  open_to_all_staff          free string
   severity    critical                   OK
   cleared_by  add_policy OK , add_service_tier OK
   arms        crm_data_exposed OK
user_account_changes_unlogged
   entity      user_account               OK
   policy      access_logging             OK
   permissive  unlogged                   free string
   severity    critical                   OK
   cleared_by  add_policy OK , add_service_tier OK
   arms        unlogged_system_change OK
ledger_egress_unrestricted
   entity      ledger                     OK
   policy      data_egress                OK
   permissive  unrestricted               free string
   severity    critical                   OK
   cleared_by  add_policy OK , upgrade_component OK
   arms        financial_audit_deadline_missed OK
staff_activity_untracked
   entity      user_account               OK
   policy      staff_monitoring           OK
   permissive  untracked                  free string
   severity    critical                   OK
   cleared_by  add_policy OK , add_training OK
   arms        phishing_on_staff_accounts OK

RESULT: 6 obligation rules, 0 orphans
Policy coverage: every one of the six switches is read by at least one rule -> True
```

**Still unchecked by machine, and named so it does not go invisible:**
1. that these keys resolve at all — the whole cross-check above;
2. that `permissive_value` names a state the policy can actually be in — the schema gives
   a policy no value vocabulary, so **nothing in the pack or the validator could check
   this even after 1.2 builds the cross-reference check.** Worth 1.2 or 1.1 knowing;
3. that every sensitive entity is covered by *some* obligation. It is not: `inventory`
   (medium) and `service_ticket` (medium) have none, deliberately — the three `high`
   sensitivity entities (`customer`, `ledger`, `user_account`) all do.

### Deferred 2 — `E13`'s `value_chain_coverage` arm

**Why deferred:** the `1.2-020` ruling is made (2026-08-18) and not implemented. Porter's
nine are a platform constant and `E13` must resolve against that constant, never against
pack capabilities.

**Authored against the nine, as ruled. Hand cross-check:**

```
the nine (from the §5.1b ruling):
  inbound_logistics, operations, outbound_logistics, marketing_sales, service,
  firm_infrastructure, human_resources, technology, procurement

pack.yaml initial_state.value_chain_coverage keys:
  inbound_logistics, operations, outbound_logistics, marketing_sales, service,
  firm_infrastructure, human_resources, technology, procurement

keys outside the nine : none
of the nine, absent   : none          -> 9/9, exact, no extras

unit_responses[].contributing:
  warehouse          outbound_logistics    OK   (also a chain_position: True)
  store_operations   operations            OK   (also a chain_position: True)
  finance            firm_infrastructure   OK   (also a chain_position: True)
```

**The counter-check — the category error the ruling forbids, reproduced on this pack:**

```
resolving the same keys against pack CAPABILITIES instead of the constant would report:
  value_chain_coverage : inbound_logistics, operations, outbound_logistics,
                         human_resources, technology, procurement       -> 6 false errors
  unit_responses[].contributing : outbound_logistics, operations,
                                  firm_infrastructure                   -> 2 false errors
                                                                    total 8 false errors
```

**Exactly the eight false errors on correct content the rework auditor measured** — the
ruling is confirmed against the post-1.3 pack, not merely inherited. `procurement: 0/3`
and `technology: none` are in the file *because nothing covers them*; they are activities,
not capabilities, and they are also pinned by `mockups/dashboard.html`.

**Still unchecked by machine:** that a `value_chain_coverage` key is one of the nine, and
that a `contributing` value is one of the nine. Until 1.2 builds the arm, a typo here
reaches a student screen silently.

---

## 7. CG-6 — what closed, and what 1.3 could not close

### Closed: `E14`, and the derivation

```
authored facts     budget.capex_per_round[3]  = 220000
                   review.lines[].capital     = 0 + 98000 + 34000 + 30000 + 0 + 0 + 12000
derived            review.capital_committed   = 174000
                   review.capital_available   = 220000
                   review.capital_remaining   = 220000 - 174000 = 46000
                   budget.capital_available   = 220000
                   budget.capital_remaining   = 220000 - 174000 = 46000   (was 44000)
                   review.run_rate_after      = 58300 + 3900 = 62200
                   budget.run_rate            = 58300
```

All six of `E14`'s derivations now agree with tolerance zero.

### **NOT closed: the second home. Reported, not improvised.**

Spec §5.1a: *"a builder that reconciles the numbers rather than removing the duplicate has
satisfied the validator and not the spec."* That is precisely the state this packet is in,
and here is why it could not be otherwise.

**Both fields are REQUIRED by the schema.** Proven by experiment on scratch copies of the
pack:

```
$ # remove initial_state.budget.capital_remaining, then validate
  This pack could not be read: pack.yaml:
  metadata.initial_state.budget.capital_remaining: Field required
  1 error · 0 warnings · exit 1

$ # remove initial_state.review.capital_remaining, then validate
  This pack could not be read: pack.yaml:
  metadata.initial_state.review.capital_remaining: Field required
  1 error · 0 warnings · exit 1
```

`models.py:58` `RoundBudgetState.capital_remaining: int = Field(ge=0)` and `models.py:99`
`ReviewState.capital_remaining: int` both have no default, and `StrictModel` forbids
extras, so **there is no authoring move that leaves one home.** Eliminating it is a schema
change; spec §1 puts schema changes out of 1.3's scope and says *stop and report*.

**What 1.1 needs to do, stated so it can be picked up:** make `capital_remaining` optional
on both models and have the loader compute it from `capital_available − capital_committed`,
or collapse the two blocks so the figure has one home. Either removes the drift
structurally, which is what `SPEC_PROTOCOL §3` asks for, instead of correcting it once.

**What 1.3 did instead:** set both to the derived value and annotate both fields in
`pack.yaml` with the derivation, the authored facts they come from, and this finding. The
drift cannot recur silently — `E14` catches it with tolerance zero — but the second home
survives.

### The mockup conflict — **recommendation, not a decision**

| | value | where |
|---|---|---|
| derived | **46,000** | `220000 − 174000`, enforced by `E14` |
| mockups | **44,000** | 16 files: `challenges`, `challenges-item`, `components`, `components-detail`, `components-wizard`, `dashboard`, `people`, `platform`, `review`, `review-locked`, `rollout`, `rollout-detail`, `rollout-locked`, `security`, `services`, `strategy` |
| mockups | **46,000** | 2 files: `review.html`, `review-locked.html` — which also carry 44,000, in the header strip |

**Recommendation: change the sixteen mockups to `$46,000`. Do not change the authored
review lines.** Four reasons:

1. **The 174,000 is corroborated seven times over.** It is the sum of seven independent
   area lines. The 44,000 is corroborated by nothing except its own repetition across a
   header strip that was copied file to file.
2. **Making 44,000 true requires inventing a decision that never happened.** It needs the
   committed total to be 176,000, and **no $2,000 item exists anywhere in the round-3
   blocks.** Authoring one to make the arithmetic land on a display figure is fitting the
   facts to the fixture.
3. **The screen that shows the arithmetic already agrees with the derivation.**
   `review.html` prints *"Capital committed $174,000 of $220,000 · Remaining $46,000"* in
   its own table while its header strip says *"$44,000 remaining"* — the two figures
   contradict each other **inside one file**, and the one attached to the working is the
   46,000. There is also no consistent reading that rescues both: a pre-commitment figure
   would have to be *larger* than the post-commitment one, and 44,000 < 46,000.
4. **Blast radius.** Changing the mockups changes a display string in static HTML that
   computes nothing. Changing the authored lines changes the pack's economics and would
   ripple into 1.4's scoring and 1.7's calibration.

This is a **0.4 rework**, not a 1.3 authoring choice, which is why the spec has always said
report rather than pick. `mockups/` was not touched by this packet. Closing it also closes
`0.4-002` and `1.1-002`.

---

## 8. Content gaps — one by one

| Gap | Status | Evidence |
|---|---|---|
| **CG-1** — every capability can raise a signal | **CLOSED** | 8 rules, all declaring `metric_kind`. Table below. No `E12`, no `E20`, no `E21` |
| **CG-2** — every strategy drawn by ≥6 events | **CLOSED** | deck 3 → 13; draws 9 / 10 / 12 / 12. No `W08`, no `W05`. **The 1.2-035 trap was not taken**: zero cards have an empty `strategy_affinity`, so no `W03` was traded for the `W08` |
| **CG-3** — project duration resolved and stated | **CLOSED, stated** | `PROVENANCE.md` §9. Authored half = `deployment_modes[].lead_time_rounds`, pinned by 0.3 §5.6's wizard; runtime half = 1.6 O2's `in_flight` with `arrival_round`. No new field, no schema change. Corroborated by mis_lite's own `mis_initiatives_master.duration_in_rounds` (1–5) |
| **CG-4** — six policy switches with stated costs | **CLOSED, re-keyed** | six dimensions; the three mechanism keys retired. Decision and its three reasons in the `policies.yaml` header. Nothing outside `policies.yaml` and `labels.yaml` referenced the old keys |
| **CG-5** — `obligation_rules.yaml` | **CLOSED** | six rules in 1.5 §5.4's shape, hand-verified in §6. Every one of the six policy switches is read by at least one rule, so no switch is decorative |
| **CG-6** — second home eliminated | **PARTLY CLOSED — §7** | `E14` cleared and the value derived; the second home survives because the schema requires it. Mockup conflict reported with a recommendation |
| `1.2-012` — eight missing label keys | **CLOSED** | eight `misc` entries; `E07 ×8` → 0. A Rollout screen no longer renders `redesign_picking` at a student |
| `1.2-011` — nothing owns `user_account` | **CLOSED** | `central_sign_on.owns_entities: [{entity: user_account, level_of_detail: named_user}]`; `E02` → 0 |
| `1.2-024` — messages lead with machine keys | **CLOSED for this pack** | `labels.yaml` now carries `catalog`, `watch_rules`, `questions` and `entities` sections, 33 keys. Note the finding's *other* half is 1.2's: `events` still maps a `body_key` to a persona quote, so an event has nowhere to hold a NAME |
| `1.2-013` — two of three cards wait on an unreachable severity | **VERIFIED RESOLVED** | all 13 cards' `signal_open` preconditions checked for reachability: 13/13 reachable. `E21` → 0 |

**CG-1 — the eight rules:**

```
rule              capability            kind        warn   crit    source
ord_cap_01        order_fulfilment      threshold   0.80   0.95    PINNED 0.3 §5.6
wh_rollout_01     order_fulfilment      presence    null   null    PINNED 0.4
sec_identity_01   firm_infrastructure   presence    null   null    PINNED 0.4
store_cap_01      store_operations      threshold   0.80   0.95    AUTHORED  TODO: calibrate
fin_close_01      financial_reporting   threshold   0.02   0.05    AUTHORED  TODO: calibrate
cust_data_01      customer_insight      threshold   0.30   0.60    AUTHORED  TODO: calibrate
mkt_channel_01    marketing_sales       threshold   0.80   0.95    AUTHORED  TODO: calibrate
svc_backlog_01    service               threshold   0.75   0.90    AUTHORED  TODO: calibrate
```

7 of 7 capabilities signal-covered. Was 1 of 7.

---

## 9. Declared substitutions

Four. Each is a place the spec's default could not be executed as written.

| # | Spec says | What was done | Why |
|---|---|---|---|
| **S1** | §5.4a: seed command is `python -m app.casepack.harvest --from mis_lite --to riverside_grocery` | `python3 backend/scripts/harvest_mis_lite.py --from mis_lite --to riverside_grocery`, same flags | I1's own check greps `backend/scripts/harvest*`, so the script must live there. Putting a DB-connecting harvester inside `app/casepack/` would also add engine-package code, which §1 puts out of scope |
| **S2** | O3: harvest `market_potential` (and `competitors`) into the pack, marked `unused_until: market_layer` | Extracted and preserved in `backend/harvest/mis_lite/`; **not** authored into the pack | `docs/casepack-schema.md` describes no `competitors` or `market_potential` section and the loader reads neither. Authoring one is a schema change (§1: stop and report). `findings/content-coverage-2026-07-27.md` already records `competitors.yaml` as *"correctly absent, deferred with the market layer"*, and `design/04` G6 asks only that the rows be *preserved* |
| **S3** | §5.1: `component_strategy_fit` → `strategies[].capability_weights`, mode *transform* | The conversion **was run**, its full normalised output is in `PROVENANCE.md` §4 and the raw means are in `harvested_raw_fit` on all four strategies — but `capability_weights` stays authored | Every normalised weight lands in [0.1323, 0.1520]. All four strategies become numerically indistinguishable, and `cost_leadership` is the highest multiplier for all seven capabilities, which is a scale artefact of an un-normalised source rather than a strategic statement. `design/01` §4 already flags mis_lite's mapping values as generated, not calibrated. **Reversible** — the table is in provenance |
| **S4** | dispatch: *"wh_rollout_01 (metric: adoption) … is presence-shaped"* | Declared `metric_kind: presence`, **and renamed the metric** `adoption` → `rollout_without_support` | `docs/casepack-schema.md`: a presence metric *"is a yes/no condition"*. A boolean named `adoption` reads as a ratio to 1.5's evaluator and to anyone reading the ledger. The rename changes no validator output; the presence declaration is what the dispatch measured |

**Also changed beyond the letter of the dispatch, and declared:**

- **Three catalog `opex` figures corrected to the pinned components table** —
  `order_mgmt_v42` 3900 → 2400, `pos_system_2011` 1800 → 3100, `accounting_package`
  1200 → 900. `components.html` and 0.3 §5.6 both give a "Cost per round" column and the
  pack contradicted it on three of six rows. Spec §3 decision 6 rules that the fixed
  figures win, and I7 is a 1.3 DoD row. The `98000` capex was left alone: `review.html`'s
  components line reads *"2 changes · $98,000 capex · +$3,900/round"*, which is an
  aggregate of two changes and cannot be attributed to one item without guessing.
- **`store_spreadsheets` gained `transaction_export`** and now also serves
  `financial_reporting`. It filled only `spreadsheet_workaround`, which no capability asks
  for, so `W04` said buying it could never help anyone — while the case has it running and
  the review warns that spreadsheets are still in daily use. Declaring the role it actually
  fills is both truer and clears the warning.
- **`preferences/platform.yaml` `finance.ideal_placement` corrected `on_prem` → `cloud`.**
  The source says finance weights cloud 1.1 against on-premises 0.8. The old value had been
  authored, not harvested, and nothing had checked it.
- **`firm_infrastructure` given weight 0.06 in all four strategies.** For
  `cost_leadership` this is a re-split of the 0.15 `mockups/strategy.html` displays against
  *Firm infrastructure* — two capabilities share that chain position, so the displayed line
  is unchanged at 0.15 and `W02` clears. A strategy that weights the platform at zero says
  the platform can fail without cost.

---

## 10. Definition of Done table

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1, 1a, 1b, 1c, 2–6, esp. row 5 per table | **DONE** | §1, §2, §3. Row 5 FAILS and the failure is reported, not worked around |
| Steps 1–6 verified | **DONE** | 1 extraction (34 tables / 2,456 rows, read-only) · 2 mechanical · 3 normalisation · 4 judged authoring · 5 provenance + curriculum · 6 validate |
| I1 read-only | **DONE** | §4 |
| I2 no `trialNNN` | **DONE** | §4 |
| I3 no textbook prose in labels | **DONE** | §4 |
| I4 weights normalised | **DONE** | §4, 4/4 |
| I5 discards documented | **DONE** | `PROVENANCE.md` §5, nine discards + two deferrals |
| **I6 validator exit 0** | **DONE** | §5, pasted in full |
| I7 0.3 figures match | **DONE** | 43/43, `backend/scripts/harvest_readback.py` exit 0 |
| I8 every capability can signal, every rule declares its kind — CG-1 | **DONE** | §8 |
| I9 every strategy drawn by ≥6 events — CG-2 | **DONE** | §8 |
| I10 six policies with costs — CG-4 | **DONE** | §4, §8 |
| I11 obligation rules present and resolving — CG-5 | **DEFERRED, hand-verified** | §6, 0 orphans |
| I12 every label key resolves — `1.2-012` | **DONE** | §4 |
| CG-3 project duration resolved and stated | **DONE** | `PROVENANCE.md` §9 |
| CG-6 — second home eliminated; mockup conflict reported | **PARTLY — reported** | §7. `E14` cleared, value derived, conflict reported with a recommendation; **elimination blocked on a 1.1 schema change** |
| `1.2-024` label sections authored | **DONE for this pack** | §8, and the residual half named |
| `1.2-013` verified resolved — the deck is three cards, not one | **DONE** | §8, 13/13 preconditions reachable |
| O1, O2, O3 recorded | **DONE** | `PROVENANCE.md` §6. O3 substituted, declared — §9 S2 |
| `PROVENANCE.md` complete | **DONE** | rows in / rows out / mode per table, nine discards with reasons, raw fit multipliers, 27 TODOs, O1–O3, CG-3 |
| `docs/curriculum-coverage.md` — the concepts | **DONE** | 24 concepts, not 26 — the count drift is reported there and in `PROVENANCE.md` §2 |
| Every `TODO: calibrate` listed in the report | **DONE** | 27, tabulated in `PROVENANCE.md` §7 |
| **Seed** — harvest command reproducible from a clean pack directory | **PARTLY** | the extraction is one command and reproducible (run twice, identical output). **The YAML authoring is not machine-generated** — most of the transform is judged (§5.2), so `harvest_mis_lite.py` produces the intermediate JSON and the provenance trail, not the pack. `harvest_readback.py` is the seed-in-the-loop evidence: 43 pinned figures read back out of the *loaded* pack. Declared rather than claimed |
| Browser / auth / instance canaries | **N-A** | headless — this packet ships no screen and no runtime state |

---

## 11. For the auditor — where to look first

1. **§7.** CG-6 is the one row not fully closed. The experiment output is pasted; re-run it.
2. **§3.** Pre-flight row 5 fails and the finding is bigger than the spec expected.
3. **§9 S3.** The fit-multiplier conversion ran and its output was deliberately not used.
   That is the largest judgement in the packet. `PROVENANCE.md` §4 has the full table so
   the arithmetic can be checked without touching mis_lite.
4. **§6.** Two hand-verifications standing in for two absent machine checks. Both name what
   is *still* unchecked.
5. **27 `TODO: calibrate`.** None of them is on a figure pinned by 0.3 or 0.4 — all 43
   pinned figures match exactly. Every TODO is on a number 1.7's harness is expected to
   move.
