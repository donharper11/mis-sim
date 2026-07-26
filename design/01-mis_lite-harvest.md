# mis_lite Harvest Pass

**Source:** PostgreSQL `mis_lite` on 192.168.50.38 (owner `donwh`)
**Reviewed:** 2026-07-26 · 79 tables · content masters populated, runtime tables empty
**Purpose:** determine what transfers into the new MIS simulation casepack format

Note: every table carries a `trialNNN char(1)` column, uniformly `'T'`. Confirmed as a
software-migration carryover. Drop on harvest.

---

## 1. What engine mis_lite actually implements

Not a component catalogue with a scoring bolt-on. It is a **stakeholder-preference /
attractiveness-share model**, and the pattern is consistent across all nine decision
domains. Every `*_mapping` table has the same shape:

```
stakeholder_id
<item>_id
ideal_value        the level THIS stakeholder considers ideal for this item  (0–100)
selected_value     the level the team actually chose                         (0–100)
alignment_score    gap between ideal and selected
oar1..oar5_weight  how much this item matters to each of the 5 objectives
strat1..4_fit_multiplier   strategy fit
```

So the resolution chain is:

```
team picks a LEVEL per decision item
   → compare against each stakeholder's ideal level
   → alignment score
   → weight by objective attractiveness ratings (OAR)
   → apply strategy fit multiplier
   → attractiveness_units
   → market_share_of_attractiveness_units   (vs 5 scripted competitors)
   → adoption_units / cumulative_adoptions
   → kpi_scores · oas_scores · fit_index
```

`market_potential` is authored per objective per round (Objective 1: 8,000 → 15,500
across 10 rounds), so demand grows and teams compete for share of it.

**This is a demand-side model.** It answers *"did your IS investments please your
stakeholders and win you share?"*

The engine designed in the 2026-07-26 conversation is a **supply-side / operational
model** — capabilities, dependency topology, shared platform pools, complementary
assets (Tech × Org × Mgmt). It answers *"does your infrastructure actually work, and
did you manage the organisation well enough to realise value from it?"*

These are **complementary, not competing.** See §5.

---

## 2. Inventory and verdict

### TAKE AS-IS — pure content, no rework

| Table | Rows | Notes |
|---|---|---|
| `strategy` | 4 | Cost Leadership · Differentiation · Customer & Supplier Intimacy · Focus. Exactly the four in the new design |
| `objectives` | 5 | Laudon Ch 1 strategic business objectives (OEX, NPB, CSI, DMK, CMP) |
| `impact_areas` | 5 | Operational Efficiency · Customer Intimacy · Market Share · Profitability · Security Resilience. Range −100..+100 |
| `stakeholders` | 14 | 7 internal (C-suite, Finance, Employees, Operations, IT, HR, Marketing) + 7 external (Investor, Customer, Vendor, Security Auditor, Regulator, General Public, Media). Well-written descriptions |
| `data_governance_policies` | 3 | Direct hook for the information-policy layer |
| `security_incidents` | 3 | Seeds the event deck |
| `regulatory_penalties` | 3 | Seeds compliance consequences |
| `competitors` | 5 | Scripted rival archetypes |
| `market_potential` | 50 | 5 objectives × 10 rounds, growing demand curve |

### TAKE WITH REWORK — valuable, wrong shape

| Table | Rows | Rework needed |
|---|---|---|
| `component_strategy_fit` | 168 | `fit_multiplier` per component × strategy. **The single most valuable asset here.** Re-key from mis_lite component ids to new catalog ids — see §3 |
| `it_infrastructure_addons_master` | 11 | Backup, DR plan, encryption policy, cloud API, maintenance, IDS, **IAM**, threat detection, **failover clustering**, compliance audit, perf tuning. Nearly all map onto the new *shared platform services* layer |
| `change_management_master` + `_strategy_fit` | 8 + 20 | The Organisation-readiness decision set already exists. Re-cast as training / process redesign / communication options |
| `mis_initiatives_master` + mappings | 12 + 168 | Reusable as application-layer initiatives |
| `erp_modules_master` | 21 | Reusable as enterprise-application catalogue entries |
| `ecommerce_features_master` | 9 | Ch 10 coverage, reusable |
| `business_processes_master` | 8 | Maps onto value-chain activities — but check seeding quality (see §4) |
| `stakeholder_infrastructure_preference` | 14 | Cloud vs on-prem preference weight per stakeholder. Small but directly reusable for the hosting decision |
| `deployment_types`, `hardware_types`, `network_types`, `database_types`, `maintenance_support_levels`, `integration_services` | 3 each | Level-based option ladders with cost. Reusable as tiered choices (e.g. Basic / Standard / Premium support) |

### LEAVE — structure does not transfer

| What | Why |
|---|---|
| Per-domain decision tables (`erp_decisions`, `ecommerce_platform_decisions`, `change_management_decisions`, …) | Not "hard-coded logic" — a consistent repeated pattern. But it requires a new table + migration per decision domain, so a new casepack in a different vertical cannot be added without DDL. Replace with one polymorphic `decision_line` table |
| `rounds`, `teams` (global scope) | No `instance_id`. Two sections running different casepacks would collide. Adopt BECSR's Course → Section → SimulationInstance → Team hierarchy instead |
| `fit_index`, `oas_scores`, `kpi_scores` | Output shapes are fine as a reference, but recompute under the new engine |
| `trialNNN` columns | Migration carryover — drop |

### EMPTY / INCOMPLETE — noted so nobody assumes coverage

- `objective_attractiveness_rating` — 0 rows. OAR weights live inline in the `*_mapping`
  tables instead, so the concept is present but this table was never populated
- `alignment_score` — null or 0.00 throughout. Never computed; the engine was never run
- `competitor_actions` — 0 rows. Competitors exist, their round-by-round moves do not
- `innovation_index`, `decisions`, `kpi_scores`, `oas_scores`, `fit_index` — all empty

---

## 3. The component master problem

`component_types_master` (45 rows) is the most-cited asset and needs the sharpest note.

It is a **Laudon Chapter 5 vocabulary list**, not an architecture parts list. Entries
include *Packet Switching*, *TCP/IP*, *Analog Signals*, *Web Software — HTML5*,
*Consumerization of IT*, *Green Computing*, *Mashups and Apps*.

Those work correctly in a preference model: a team sets an adoption level 1–100 and is
scored on alignment. They **cannot** work as nodes in a dependency graph — you cannot
draw an edge from *Green Computing* to *Data Mart*, and *Analog Signals* has no
capacity, availability, or service life.

Splitting the 45:

**Buildable (~19)** — carry forward as real catalog items with attributes:
High-Performance Server · Cloud-Based Storage · SQL Database · NoSQL Database ·
VPN Network · 5G Wireless Network · ERP Software Suite · Virtualization · PaaS · IaaS ·
SaaS · Data Warehouse · Data Mart · Hadoop · In-Memory Computing · OLAP · API Gateway ·
Next-Gen Firewall · Data Lake · LAN · WAN

**Concept/trend (~26)** — do not belong in the catalog. Retain as **curriculum
coverage** — reference material, quiz content, or debrief concept links. They are how
the sim proves it covers Chapter 5, but they are not things you buy.

**Consequence for `component_strategy_fit`:** only the ~19 buildable rows' multipliers
transfer directly (≈76 of 168 cells). The remainder are still useful as authored
judgement about which trends suit which strategy — worth keeping as reference even if
the engine no longer consumes them.

---

## 4. Seed-quality warnings

- `business_process_mapping` — rows 71–76 show identical `ideal_value` 85.00 and
  identical OAR weights across all six stakeholders for process 1. Looks like uniform
  placeholder seeding rather than authored judgement. **Verify before trusting.**
- `component_mapping` (630 rows) — sampled rows show plausible variation. Likely genuine
- `mis_initiative_mapping` (168 rows) — values vary at 2-decimal precision
  (0.76, 0.43, 0.57…), suggesting generated rather than hand-authored. Usable as a
  starting distribution; do not treat as pedagogically calibrated
- Total mapping volume ≈ **2,100 rows** across nine domains. Substantial, but audit
  a sample per domain before harvesting wholesale

---

## 5. The engine reconciliation — the real decision

Two coherent engines now exist on paper.

| | mis_lite | New design |
|---|---|---|
| Unit of decision | a **level** (0–100) per item | a **structural change** (place, wire, size, staff) |
| What's evaluated | alignment to stakeholder ideals | whether the architecture works |
| Failure mode taught | you displeased stakeholders | your system broke / value never realised |
| Output | market share, objective attainment | realised value per capability, service outcomes |
| Strengths | competition, stakeholder plurality, ~2,100 authored rows | topology, complementary assets, causal debriefs |
| Weaknesses | no topology, no org-readiness multiplier, no data model | no market, no stakeholder plurality, all authoring still to write |

**Recommendation: layer them, don't choose.**

```
  MOT engine  (new)         →  realised value per capability
        ↓
  attractiveness  (mis_lite) →  realised value replaces raw "selected_value"
        ↓                        as the input to stakeholder alignment
  market share / objectives  →  outcomes
```

The key move: in mis_lite the input to alignment is what the team *bought*. In the
combined model the input is what the team *actually realised* — Tech × Org × Mgmt. A
team that buys the ideal ERP and never trains anyone scores badly with stakeholders
**because the system isn't delivering**, not because they bought the wrong box. That is
a strictly better lesson and it makes the ~2,100 authored mapping rows keep their value.

Deferred to Spec A. Flagged here because it determines whether the harvest is
foundation or reference.

---

## 6. Open question carried forward

`impact_areas` / `objectives` (Laudon Ch 1) vs **Balanced Scorecard** (Ch 12).
Both are authored-content choices, not engine choices — the engine produces movements
and the scorecard is the presentation layer. See `03-scoring-frame-options.md`.
