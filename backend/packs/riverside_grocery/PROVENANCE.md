# Riverside Grocers — Harvest Provenance

**Module:** 1.3 — mis_lite harvest → Riverside pack v1 · **Date:** 2026-08-18
**Source:** PostgreSQL `mis_lite` on `192.168.50.38`, database `mis_lite`, user `donwh`
**Access mode:** READ-ONLY. `PGOPTIONS=-c default_transaction_read_only=on`; SELECT only.
Invariant I1: `grep -rniE "INSERT|UPDATE|DELETE|ALTER|DROP" backend/scripts/harvest*`
returns zero.
**Extraction:** `PGPASSWORD=… python3 backend/scripts/harvest_mis_lite.py --from mis_lite
--to riverside_grocery` → `backend/harvest/mis_lite/*.json` (34 tables, 2,456 rows) and
`_manifest.json`.
**Read-back:** `python3 backend/scripts/harvest_readback.py` → 43 pinned figures matched,
exit 0.

> In two years nobody will remember why 24 rows vanished. That is what this file is for.

---

## 1. Transform table — rows in, rows out, mode

| pack field | mis_lite source | rows in | rows out | mode | notes |
|---|---|---|---|---|---|
| `strategies[].key`, `headline_metric` | `strategy` | 4 | 4 | mechanical | the four are exactly the four this design uses |
| `strategies[].harvested_raw_fit` | `component_strategy_fit` | 168 | 28 | transform | 72 of 168 cells belong to buildable components; aggregated to 7 capabilities × 4 strategies. **Not used for `capability_weights`** — §4 |
| `strategies[].capability_weights` | — | — | 24 | authored / pinned | cost_leadership pinned by `mockups/strategy.html`; the other three authored. §4 |
| `catalog[]` | `component_types_master` | 45 | 21 buildable → 4 new rows | judged | 24 concepts → `docs/curriculum-coverage.md`; §2 below |
| `catalog[erp_suite].config_tiers` | `erp_modules_master` | 21 | 3 tiers | transform | family × Basic/Mid/Advanced ladder → capex multipliers 1.00 / 1.57 / 2.58 |
| `platform.services[]` | `it_infrastructure_addons_master` | 11 | 6 services + 2 policies | transform | §3 below |
| `platform.services[]` | `component_types_master` (buildable) | 21 | 5 services | judged | compute_pool, storage_pool, data_platform, end_user_email, integration_api |
| `platform.support_tiers[]` | `maintenance_support_levels` | 3 | 3 | mechanical | `cost_value` carried exactly: 20000 / 50000 / 100000 |
| `platform.integration_tiers[]` | `integration_services` | 3 | 3 | mechanical | `cost_value` carried exactly: 50000 / 120000 / 200000 |
| `policies[]` | `data_governance_policies` | 3 | 3 | transform | re-keyed from mechanism to policy dimension — see `policies.yaml` header |
| `policies[]` | `it_infrastructure_addons_master` rows 3, 10 | 2 | 0 | judged | Data Encryption Policy and Compliance Auditing Tool overlap the three above; costs not double-counted |
| `events[]` | `security_incidents` | 3 | 3 | judged | `impact_cost` → `outcomes.revenue_loss`, carried exactly (100000 / 50000 / 30000) |
| `events[]` | `regulatory_penalties` | 3 | 3 | judged | `fine_amount` → `revenue_loss`, `stakeholder_displeasure` → scorecard delta, both carried exactly |
| `events[]` | — | — | 4 | authored | CG-2 deck depth; two carry harvested cost bases from `mis_initiatives_master` |
| `stakeholders[]` | `stakeholders` | 14 | 14 | mechanical | 7 internal + 7 external; archetypes are the platform constant in `checks.py` |
| `labels.misc` objectives | `objectives` | 5 | 5 | mechanical | declaration vocabulary; rewritten to business language (O2) |
| `labels.misc` impact areas | `impact_areas` | 5 | 5 | mechanical | rewritten to business language (O2) |
| `preferences/platform.yaml` | `stakeholder_infrastructure_preference` + `it_infrastructure_types` | 14 | 7 internal archetypes (+7 external, authored) | mechanical | `preference_weight` carried exactly as `cloud_weight` / `on_prem_weight`; `ideal_placement` derived from the pair. **Corrected `finance` from `on_prem` to `cloud`** — the source says 1.1 vs 0.8 and the pack had asserted the opposite |
| `obligation_rules[]` | — | — | 6 | authored | CG-5. No mis_lite source: the prior build had no privacy layer |
| `preferences/policies.yaml` | — | — | 9 archetypes · 36 rows | authored | **NEW, 1.3 follow-up.** design/07 §3.5 — the PREFERENCE path for information policy. No mis_lite source: the source models stakeholder preference over infrastructure placement only and has no policy dimension. §10 below |
| `preferences/services.yaml` | — | — | 6 archetypes · 11 rows | authored | **NEW, 1.3 follow-up.** design/07 §3.6. The tier keys and every figure the views are about are harvested and already in `platform.yaml`; who holds a view and how strongly is authored |
| `policies[].options`, `.default` | — | — | 6 × 3 states + 6 defaults | authored | 1.3 follow-up. The permissive value of each switch was already named by `obligation_rules.yaml`, so half the vocabulary was authored before this packet; the middle and restrictive states and the six defaults are new. §10 |
| `lead_time_rounds` | `mis_initiatives_master.duration_in_rounds` | 12 | 37 rows re-authored | judged | 1.3 follow-up. 54 of 75 placement options completed in zero rounds. The band is anchored on the source's 12 durations (range 1–5, **no initiative shorter than one round**); the placement gradient is authored. §10 |
| `watch_rules[]` | — | — | 8 | authored / pinned | CG-1. 3 pinned from 0.4, 5 authored |
| `capabilities[]`, `entities[]`, `questions[]` | — | — | unchanged | — | authored by 1.1; 1.3 changed none of them |

**Totals:** 2,456 rows extracted · 26 tables in the transform map · 9 discarded (§5) ·
30 `TODO: calibrate` markers (§7).

---

## 2. `component_types_master` — the 45-row split

`design/01` §3 writes *"Buildable (~19)"* and then enumerates **21** names. The
enumeration governs, so the split is **21 buildable / 24 concept**, not 19 / 26. The two
prose estimates drifted; the data did not. Full disposition table, per row, in
`docs/curriculum-coverage.md`.

Four buildable rows became new catalog items:

| Catalog key | mis_lite row | `cost_value` | Why this one |
|---|---|---|---|
| `order_db_cluster` | 3, SQL Database | 10000 | 0.3 §5.6 lists it in the COMPONENTS table; the pack did not have it |
| `store_back_office_pc` | — | — | 0.3 §5.6 lists it; mis_lite's nearest row (1, High-Performance Server, 20000) is a data-centre server, so the figure was **not** carried across |
| `nosql_database` | 4, NoSQL Database | 12000 | before 1.3, every role in the pack had exactly one filler, so no decision had an alternative |
| `erp_suite` | 9 + `erp_modules_master` | 30000 + 44571 | the one place the 21 module rows become pack content |

**Why the ERP modules, e-commerce features and MIS initiatives are not 42 catalog rows.**
In mis_lite they are *levels within one decision* — a team sets an adoption level per
module, and `erp_modules_master` is literally a family × Basic/Mid/Advanced ladder. The
new schema expresses a level as `config_tiers` on a catalog item. Forty-two extra
shopping-list rows would also be the first thing `GOVERNANCE §2` says this must not feel
like.

---

## 3. `it_infrastructure_addons_master` — all 11 rows accounted for

| # | Addon | `cost_value` | Landed in |
|---|---|---|---|
| 1 | Continuous Backups | 2000 | `platform.backup_recovery` (with row 2) |
| 2 | Disaster Recovery Plan | 5000 | `platform.backup_recovery` on-premises capex |
| 3 | Data Encryption Policy | 1500 | **not carried.** 1500 buys encryption in transit, not a position on what may leave the firm; using it as the `data_egress` cost would state a figure the source does not support |
| 4 | Cloud Integration API | 3000 | `platform.integration_api` |
| 5 | Routine Maintenance Support | 2500 | superseded by `maintenance_support_levels` → `support_tiers` |
| 6 | Intrusion Detection System | 4000 | `platform.intrusion_detection` |
| 7 | Identity and Access Management | 25000 | `platform.central_sign_on` |
| 8 | Advanced Threat Detection | 40000 | `platform.threat_detection` |
| 9 | Failover Clustering | 30000 | `platform.failover_cluster` — load-bearing for 1.5 §5.3's `no_failover_multiplier` |
| 10 | Compliance Auditing Tool | 20000 | overlaps `data_governance_policies` row 3 (30000), which is used instead |
| 11 | Performance Tuning Engine | 35000 | **not instantiated** — duplicates the support-tier ladder |

---

## 4. Fit multipliers — converted, and the conversion's result reported

**Contract:** `CONTRACTS.md` — *"mis_lite's equivalent (`component_strategy_fit.
fit_multiplier`) was un-normalised multipliers around 1.0 — a different scheme. Do not mix
the two. Harvested multipliers are converted on ingest, not stored raw."*

### The conversion, as run

1. `component_strategy_fit` holds 168 cells = 42 components × 4 strategies. Rows 43, 44
   and 45 (API Gateway, Next-Gen Firewall, Data Lake) carry **no fit rows at all**, so of
   the 21 buildable components only 18 have multipliers → **72 cells, not the 76 the
   spec's §5.3 example estimates.** Reported drift; the data governs.
2. Each of the 18 was mapped to the capability it serves (mapping table below).
3. `raw(strategy, capability)` = mean multiplier over the components mapped to it. These
   are the values stored in `strategies[].harvested_raw_fit`, which is the field
   `docs/casepack-schema.md` describes as *"Raw source multipliers retained as
   provenance"*.
4. `normalised(strategy, capability)` = `raw ÷ Σ raw` per strategy. Table below.

**Component → capability mapping (judged, recorded so it can be checked):**

```
order_fulfilment      3 SQL Database · 40 In-Memory Computing · 34 WAN
store_operations      1 High-Performance Server · 6 5G Wireless · 33 LAN
financial_reporting   9 ERP Software Suite · 37 Data Warehouse · 41 OLAP
customer_insight      4 NoSQL Database · 38 Data Mart · 39 Hadoop
marketing_sales      13 PaaS
service              25 SaaS
firm_infrastructure   2 Cloud-Based Storage · 5 VPN · 12 Virtualization · 14 IaaS
```

### Raw means, and the normalised weights they produce

| capability | cost_leadership | differentiation | cust_supplier_intimacy | focus_strategy |
|---|---|---|---|---|
| order_fulfilment | 1.330 → 0.1444 | 1.073 → 0.1403 | 1.117 → 0.1463 | 1.180 → 0.1368 |
| store_operations | 1.320 → 0.1433 | 1.113 → 0.1455 | 1.073 → 0.1406 | 1.283 → 0.1487 |
| financial_reporting | 1.330 → 0.1444 | 1.047 → 0.1368 | 1.077 → 0.1410 | 1.220 → 0.1414 |
| customer_insight | 1.287 → 0.1397 | 1.087 → 0.1420 | 1.107 → 0.1450 | 1.270 → 0.1472 |
| marketing_sales | 1.270 → 0.1379 | 1.150 → 0.1503 | 1.160 → 0.1520 | 1.310 → 0.1518 |
| service | 1.320 → 0.1433 | 1.150 → 0.1503 | 1.010 → 0.1323 | 1.160 → 0.1344 |
| firm_infrastructure | 1.355 → 0.1471 | 1.033 → 0.1349 | 1.090 → 0.1428 | 1.205 → 0.1397 |
| **sum** | **1.0000** | **1.0000** | **1.0000** | **1.0000** |

### The result is recorded and NOT used for `capability_weights`. Declared.

Every normalised weight lands in **[0.1323, 0.1520]** — a spread of 1.97 percentage points
across seven capabilities and four strategies. Two consequences:

1. **All four strategies become numerically indistinguishable.** A team's declaration —
   the decision the whole strategy layer exists to create — would change a capability's
   weight by at most two points. 1.7 could not calibrate against it and 1.4's strategic
   alignment factor would score every team the same.
2. **`cost_leadership`'s multiplier is the highest of the four for all seven
   capabilities** (1.27–1.36 against differentiation's 1.03–1.15). That is not a claim
   that cost leadership benefits more from everything; it is a scale artefact of an
   un-normalised source. `design/01` §4 already flags mis_lite's mapping values as
   generated rather than pedagogically calibrated, and this is the same signature.

So the conversion ran, its full output is above, and `capability_weights` stays authored.
`harvested_raw_fit` carries the raw means on every strategy, so the table can be
re-derived without re-querying mis_lite. **Reversible:** if 1.7's harness shows the
authored weights are wrong, the harvested table is one table away.

**Invariant I4 holds on what shipped:** all four `capability_weights` sum to 1.000.

---

## 5. Discarded tables, each with its reason

Spec §5.1 names two discards; pre-flight row 5 produced seven more. All nine below.

| Table | Rows | Reason |
|---|---|---|
| `business_process_mapping` | 112 | **Open decision O1, default taken.** Placeholder-seeded: 2 distinct `ideal_value`s across 112 rows (85.00 × 84, 75.00 × 28). Importing data that *looks* authored is worse than an honest default |
| `change_mgmt_mapping` | 112 | Placeholder-seeded: 3 distinct values (85.00 × 56, 75.00 × 42, 80.00 × 14). **Not previously reported** — `design/01` §4 found the pattern in one table; row 5 found it in five |
| `ecommerce_features_mapping` | 126 | Placeholder-seeded: 3 distinct values (75.00 × 56, 65.00 × 56, 70.00 × 14) |
| `ecommerce_security_mapping` | 112 | Placeholder-seeded: 3 distinct values, identical shape to `change_mgmt_mapping` |
| `mis_initiative_mapping` | 168 | Placeholder-seeded on `ideal_value`: 4 distinct values (50/60/65/55) across 168 rows |
| `erp_master_mapping` | 294 | **Half seeded.** 141 distinct values, but 85.00 alone accounts for 148 of 294 rows. Not harvested wholesale; usable later with the uniform half excluded |
| per-domain `*_decisions` tables | 0 | Runtime shape, superseded by the polymorphic `decision_line` (`design/01` §2). All empty in any case |
| `rounds`, `teams` | — | No `instance_id`. Two sections running different casepacks would collide (`GOVERNANCE §4.5`) |
| `fit_index`, `oas_scores`, `kpi_scores`, `alignment_score`, `objective_attractiveness_rating`, `competitor_actions`, `innovation_index`, `decisions` | 0 | Empty, or output shapes the new engine recomputes |

**Not discarded — deferred with the market layer** (`design/04` G6, open decision O3):

| Table | Rows | Disposition |
|---|---|---|
| `competitors` | 5 | Extracted to `backend/harvest/mis_lite/competitors.json` and **preserved there**, not authored into the pack |
| `market_potential` | 50 | Same |

> **Declared substitution against O3.** O3's default is *"harvest into the pack but mark
> `unused_until: market_layer`"*. **The schema has no home for either.**
> `docs/casepack-schema.md` describes no `competitors` or `market_potential` section, the
> loader reads neither file, and adding one is a schema change that spec §1 puts out of
> 1.3's scope. `findings/content-coverage-2026-07-27.md` already records `competitors.yaml`
> as *"correctly absent, deferred with the market layer"*, so the pack side is settled.
> The rows are therefore preserved in the extraction directory, which satisfies `design/04`
> G6's *"the competitors (5), market_potential (50 rows) and OAR weights are all preserved
> for that day"* without inventing a section. **Reported, not improvised.**

Nine mapping tables were also extracted whole (2,030 rows) purely so pre-flight row 5's
uniformity audit is reproducible. Only `addon_mapping` (84 rows, 64 distinct),
`component_mapping` (630 rows, 414 distinct) and `erp_feature_mapping` (392 rows, 306
distinct) show authored variation.

---

## 6. Open decisions — recorded

| # | Question | Default | Taken? |
|---|---|---|---|
| **O1** | `business_process_mapping` shows uniform placeholder values. Harvest or re-author? | do not harvest; re-author from archetype defaults | **Taken.** 112 rows discarded. Pre-flight row 5 found the same pattern in four more tables and half of a fifth — 630 rows discarded on this ground in total |
| **O2** | mis_lite descriptions are textbook prose. Keep or rewrite? | rewrite to business language | **Taken.** No mis_lite description string appears anywhere in the pack. Originals in §8 below. Invariant I3 greps `labels.yaml` and returns zero |
| **O3** | `market_potential` (50 rows) — harvest now or defer? | harvest into the pack, mark `unused_until: market_layer` | **Substituted, declared** — §5. No schema section exists; preserved in the extraction directory instead |

---

## 7. Every `TODO: calibrate` — 30 markers

`GOVERNANCE §4.9` rule 5: estimates are allowed; unmarked estimates are not. Every value
below is authored judgement that 1.7's harness is expected to move.

| File | Count | What is unjustified |
|---|---|---|
| `watch_rules.yaml` | 5 | thresholds on `store_cap_01`, `fin_close_01`, `cust_data_01`, `mkt_channel_01`, `svc_backlog_01`. Only `ord_cap_01`'s 0.80/0.95 is pinned |
| `events.yaml` | 7 | scorecard deltas and option costs on all seven non-pinned cards. `revenue_loss` on the six harvested cards is **not** a TODO — those are `impact_cost` / `fine_amount` carried exactly |
| `policies.yaml` | 6 | every effect vector; `data_egress` cost 12000; `data_access` cost 9000 inherited from 1.1; `staff_monitoring` cost and effects entirely |
| `catalog.yaml` | 5 | `store_back_office_pc` capex; the cloud/saas ladders on the three new items; `erp_suite` compute multipliers, opex, lead times; **and the whole lead-time band (§10)** |
| `platform.yaml` | 4 | cloud and saas figures on `failover_cluster`, `threat_detection`, `end_user_email`, `data_platform` |
| `preferences/platform.yaml` | 1 | the `weight` column throughout — how much each archetype's view counts. mis_lite weighted every stakeholder the same |
| `preferences/policies.yaml` | 1 | both `weight` columns throughout — the archetype-level weight and the per-switch weight. Which switch matters most to whom is authored judgement. The `ideal_posture` values are **not** marked: each is either stated in design/07 §3.5 or read off an effect vector or an obligation rule already in the pack, and every one is cited in the file |
| `preferences/services.yaml` | 1 | both `weight` columns, on the same footing. The `ideal_tier` values are not marked — each is stated in design/07 §3.6 or read off a figure in `platform.yaml` |

**Nothing pinned by 0.3 §5.6 or the 0.4 mockups carries a TODO.** All 43 pinned figures
match — `backend/scripts/harvest_readback.py`.

---

## 8. mis_lite descriptions, kept for the record (open decision O2)

None of these strings is in the pack. They are here because O2 says keep the originals,
and because invariant I3 greps `labels.yaml` for exactly this register.

```
strategy
  1 Cost Leadership            "Focus on low-cost production and operations"
  2 Differentiation            "Emphasize unique products and customer experience"
  3 Customer & Supplier        "Use information systems to tighten linkages with suppliers
    Intimacy                    and develop intimacy with customers"
  4 Focus Strategy             "Target a specific market segment with tailored services"

component_types_master (buildable rows only)
  1 High-Performance Server    "Dedicated high-performance server"
  2 Cloud-Based Storage        "Cloud storage solution"
  3 SQL Database               "Relational SQL database"
  4 NoSQL Database             "Flexible NoSQL database"
  9 ERP Software Suite         "Comprehensive ERP software"
 12 Virtualization             "Abstracting physical hardware resources for efficient use"
 13 PaaS                       "Cloud-based platform providing tools for app development"
 14 IaaS                       "Cloud-based infrastructure resources"
 25 SaaS                       "Cloud-based software applications"
 37 Data Warehouse             "Centralized repository for structured data analytics"
 43 API Gateway                "Manages API requests and connections"
 44 Next-Gen Firewall          "Advanced firewall with zero-trust features"
 45 Data Lake                  "Centralized repository for structured and unstructured data"

it_infrastructure_addons_master
  1 Continuous Backups         "Enables continuous backup of data"
  4 Cloud Integration API      "Provides an API for cloud integrations"
  6 Intrusion Detection        "Monitors and detects unauthorized access"
  7 Identity and Access Mgmt   "Manages user identities and roles with MFA and audit trails."
  8 Advanced Threat Detection  "Uses AI/ML to detect abnormal behaviors and potential intrusions."
  9 Failover Clustering        "Ensures high availability with automated failover in case of failure."

data_governance_policies
  1 Data Retention Policy      "Defines how long data should be stored and retained."
  2 Data Classification Stds   "Categorizes data to ensure sensitive information is protected."
  3 Audit and Reporting Stds   "Establishes auditing procedures for regulatory compliance."
```

Every one of them explains how the technology works. `GOVERNANCE §2.1` asks instead: what
does it cost, who does it affect, what happens if it fails. `labels.yaml` answers that
question and nothing else — *"Standby copy for outages"*, not *"Ensures high availability
with automated failover"*.

---

## 9. CG-3 — project duration, resolved and stated

`findings/content-coverage-2026-07-27.md`: *"`grep duration_rounds` returns zero across
`models.py`, 1.1's spec and 1.6's spec. Follow-through cannot detect abandonment."*

**Resolved as: authored per placement, plus runtime state. Both already exist.**

| Half | Where it lives | Evidence |
|---|---|---|
| How long a project takes | `catalog[].deployment_modes[].lead_time_rounds` and `platform.services[].placement_options[].lead_time_rounds`, present on every row — **but 54 of the 75 were `0` when this was written, which is corrected and explained in §10** | 0.3 §5.6 wizard pins it: *"On our on-premises platform … available in 2 rounds"* = `centraline_im7.on_prem.lead_time_rounds: 2` |
| Whether it is still in flight | 1.6 spec open decision **O2**: *"an `in_flight` collection on team state, materialising into the graph at `arrival_round`"* | runtime, not authored |

**Abandoned** is therefore computable: a decision line that entered `in_flight` and left it
before `arrival_round`. **Deployed-but-never-trained** is `training_options` coverage 0 on
a component past its arrival. Both are the inputs 1.4 §5.3's follow-through formula needs.

No new field is required and none was added — spec §1 puts schema changes out of scope.

**Corroboration from the source:** mis_lite carried this concept explicitly, as
`mis_initiatives_master.duration_in_rounds` (values 1–5 across its 12 rows). The new
schema's `lead_time_rounds` is the same fact expressed per placement rather than per
initiative, which is strictly more useful — the cloud option is genuinely faster than the
on-premises one, and mis_lite could not say so.


---

## 10. The 1.3 follow-up — policy vocabularies, policy and service preferences, lead times

`design/07-decision-consequence-map.md` applies one test — *a decision is real only if a
stakeholder holds a view on it, a sub-factor consumes it, and it can move a signal or an
event* — and two of this pack's decision classes failed it. All four items below are
content. None needed a schema change.

### 10.1 `policies[].options` and `.default` — the vocabularies

`PolicyOption.options` and `.default` landed in 1.1 rework-3 and no pack used them, so
every `permissive_value` in `obligation_rules.yaml` was a string pointing at nothing and
the privacy layer was inert. Each switch now declares three states and a default.

| Policy | `options` | `default` | Why that default |
|---|---|---|---|
| `data_collection` | `everything_by_default` · `purpose_limited` · `minimal` | `everything_by_default` | a firm that has never asked what it may collect is collecting what the tills and the loyalty scheme produce |
| `data_retention` | `indefinite` · `standard_period` · `minimal` | `indefinite` | the case's actual state — nobody has deleted anything since 2011 |
| `data_access` | `open_to_all_staff` · `role_based` · `need_to_know` | `open_to_all_staff` | 0.4's security screen: four separate logins and no position behind them |
| `access_logging` | `unlogged` · `sampled` · `full_audit_trail` | `unlogged` | 0.4 states it in plain words — *"no record of who views customer data"* |
| `data_egress` | `unrestricted` · `approved_destinations` · `no_export` | `unrestricted` | extracts already move to suppliers, to marketing and into the store spreadsheets |
| `staff_monitoring` | `untracked` · `aggregate_only` · `individual_activity` | `untracked` | nothing is recorded about staff today, and leaving it there arms `phishing_on_staff_accounts` |

**The permissive half was authored before this packet.** `obligation_rules.yaml` already
named all six permissive values; what is new is the middle and restrictive states and the
six `default` declarations.

**Order is meaningful and ordinal** — least constrained at index 0, most constrained last
(`models.py`, `CONTRACTS.md` `PolicyOption.options`, design/07 §3.5b). All six lists above
are authored that way, so alignment against a stakeholder's ideal is a distance, not an
exact match. On `staff_monitoring` the ordinal "more constrained" end means the firm
watches its own people more, so its permissive index-0 end is the low-surveillance end
(`untracked`) — design/07 §3.5a.

**Hand-verified**, because no validator check exists (it is 1.2's next packet): all six
`permissive_value`s in `obligation_rules.yaml` name a member of their policy's `options`,
and all six are also that policy's `default`. All 36 `ideal_posture` values in
`preferences/policies.yaml` likewise name a declared option. Both cross-checks are pasted
in `handoffs/1.3-harvest/dod-followup.md`.

### 10.2 `preferences/policies.yaml` — 9 archetypes, 36 rows, authored per switch

The nine archetypes are exactly the nine `design/07` §3.5 names. `hr`, `investor`, `it`,
`media` and `vendor` have no rows, deliberately — the design does not give them a view on
this class and inventing one would be authoring past it.

Ideals are authored **per switch, not per archetype**, and the file carries no
archetype-wide posture at all. `finance` holds a view on all six and is permissive on four
of them; `employees` hold exactly one view. No archetype expresses one posture at one
weight across all six.

Two rows deserve naming because they run against the obvious reading, and both are read off
this pack rather than off an opinion:

- **`finance` wants `standard_period` on retention.** A retention position is the only one
  of the six whose effect vector *reduces* a running cost (`storage_cost: -0.05`).
- **`regulator` wants `standard_period` where `security_auditor` wants `minimal`.** Two
  archetypes both asking the firm to constrain itself, and they still disagree — the
  regulator's interest is that a defined period exists, the auditor's is that less is held.

**`staff_monitoring` runs on the opposite axis to the other five**, and the file says so.
Its permissive value is `untracked`, so the undecided end is the *low*-surveillance end.
`design/07`'s table reads *"employees want strict on staff_monitoring"*, but its own reason
column says *"being watched is not free"* — the interest governs, so `employees` want
`untracked` and are the one archetype already aligned with doing nothing.
`security_auditor` wants `individual_activity` on the same switch, because
`insider_risk: -0.25` is the risk they are employed to look at. Neither side is endorsed.

### 10.3 `preferences/services.yaml` — 6 archetypes, 11 rows

Exactly the six `design/07` §3.6 names. `it`'s view is the strongest in the file and is a
capacity argument rather than a comfort one: `premium` support carries 2.4 FTE against a
`starting_staff_fte` of 2.0, so the load the tier does not absorb is load the two existing
IT staff carry. That is G1's staffing pool made visible. `vendor` prefers the higher tier
because it is their revenue, and that is recorded plainly.

### 10.4 `lead_time_rounds` — the band, and why 54 zeroes was a defect

54 of 75 placement options completed in zero rounds, so *follow-through* — a named
Management sub-factor with a UI, a casepack field and a formula — had almost nothing to act
on, and *"started five things, finished none"* was an impossible failure rather than a
teachable one.

**The band:**

| Rounds | What it is |
|---|---|
| **0** | already running, or nothing to install and nobody to retrain |
| **1** | a departmental application or a shared platform service: procure, configure, integrate, cut one department over |
| **2** | touches every store, the warehouse or the general ledger: migration plus a period of parallel running |

**Anchored on the source.** `mis_initiatives_master.duration_in_rounds`, 12 rows, range
1–5: BI dashboard 1 · CRM enhancements 1 · data governance 1 · data quality audit 1 · ERP
finance module 2 · endpoint security 2 · training programme 2 · unit-based ERP 2 · system
tuning 2 · data migration 3 · predictive analytics 4 · supplier portal 5. **The source has
no initiative shorter than one round**, which is the strongest single argument that 54
zeroes was a content defect and not a modelling choice.

**Placement gradient — authored, and it corrects §9.** §9 says the cloud option *"is
genuinely faster than the on-premises one"*. mis_lite's own data does not support that as a
general rule: its four cloud initiatives average 2.75 rounds against 2.0 for its two
on-premises ones. What is defensible is narrower, and it is what was applied here:
placement changes the answer only where the delay was *infrastructure*. `saas` rows carry
`bypasses_platform: true` — the firm does not build the platform underneath them — so SaaS
is one round faster where that build was the wait, and no faster where the wait is
migration, training or process change.

**Only the zeroes were re-authored.** The 21 rows already carrying 1 or 2, including every
row 0.3 §5.6 pins, are untouched.

| | before | after |
|---|---|---|
| 0 rounds | 54 | 17 |
| 1 round | 17 | 51 |
| 2 rounds | 4 | 7 |

**The 17 rows still at 0 are deliberate.** Two incumbent on-premises systems the firm
already runs (`pos_system_2011`, `accounting_package`, both at capex 0); the store
spreadsheets and the back-office PC; three subscribed services that start working when the
invoice is signed (`next_gen_firewall` saas, `service_desk` saas — there is no incumbent
service desk to migrate from — and `intrusion_detection` saas); `end_user_email` cloud and
saas, the one service 0.3 §5.6 pins as already placed in the cloud; and `compute_pool` and
`storage_pool` cloud and saas, where capacity on demand *is* the difference between the
placements and 0.3 §5.6 pins the compute pool at 100% used.

**TODO: calibrate — the whole band**, and two rows specifically:

- `erp_suite.on_prem` is 2, below the 3 the band would give a firm-wide replacement
  carrying both a data migration and the finance close. It is left as authored because it
  is not one of the 54 zeroes.
- `central_sign_on` is 1 on all three placements. Issuing credentials to 620 staff is
  plausibly 2; the existing on-premises 1 is what holds the other two down.

One round now dominates the distribution (51 of 75). That is a fair reflection of a pack
whose catalogue is mostly departmental systems and shared services, but it means the
sharpest follow-through failures rest on the 7 two-round options. 1.7's harness is expected
to spread it.
