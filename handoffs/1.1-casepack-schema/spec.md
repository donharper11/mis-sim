# 1.1 — Casepack Schema · Build Spec

**Authored under** `SPEC_PROTOCOL.md` v1.1
**Author:** Claude (design session) · **Date:** 2026-07-26
**Phase:** 1 · **Depends on:** 0.2 (merged) · **Blocks:** 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 6.1
**Reference mockup:** N/A — headless

> **The foundation packet.** Every other engine module reads this schema, and Phase 6
> fails if it is not genuinely case-agnostic. Errors here are the most expensive in the
> project.

---

## 0. Spec Basis

**Read in full:**
- `design/01-mis_lite-harvest.md` — what content exists and in what shape
- `design/02-traceability-matrix.md` — every scoring factor and what authors it
- `design/03-scoring-frame-options.md` — Balanced Scorecard as headline
- `design/04-decisions-g1-g6.md` — IT staffing load pool; stakeholder layer adopted
- `design/05-implementation-plan.md` §1.1, §1.4 — module inventory, AI layer
- `CONTRACTS.md` — all nine entries, several of which this schema must honour
- `mis_lite` live schema on `192.168.50.38` — 79 tables inspected, masters sampled
- `BECSR/course-section-management.md` — the `SimulationInstance.settings` override pattern

**Cited from summary or prose:** none.

**Extraction sufficiency:** covered all load-bearing surfaces. Not extracted: BECSR's
scoring service implementation (different engine family — preference alignment, not
capability composition) and globalstrat's scenario schema (`globalstrat-scenario-schema.md`,
noted as a future comparison but not a dependency).

---

## 1. Purpose and scope

Define the **casepack** — the complete authored content bundle that turns a generic engine
into a specific company's simulation. Deliver it as versioned YAML with a Pydantic model
layer, plus one worked reference pack skeleton.

**In scope:**
- The YAML schema for a casepack, all sections
- Pydantic models mirroring it, with validation types
- Loader that parses YAML → typed objects (no DB writes — that is 2.5)
- A skeleton `riverside_grocery` pack with **structure complete and content stubbed**
- The schema reference document authors will work from

**Out of scope:**
- The validator (1.2) — this packet defines *what is valid*, 1.2 *enforces* it
- The mis_lite harvest (1.3) — this defines the shape, 1.3 fills it
- Any scoring computation (1.4)
- Any DB table or migration (2.5 loads packs; this parses them)
- Instructor authoring UI — packs are files (settled 2026-07-26)

---

## 2. Project-specific statements

**Scoring factors touched:** none computed. This packet **authors the inputs** to every
factor in `design/02-traceability-matrix.md`. Each schema section below names the factors
it feeds; a section feeding no factor must be justified or cut.

**Casepack keys read:** this defines them. **Casepack-identity branching:** none —
invariant I1.

**Instance scoping:** N/A — casepacks are authored content, not runtime state. They are
referenced by `simulation_instance.scenario_id` (2.1) but carry no `instance_id`
themselves.

**Business-language check:** the schema carries **two label layers** — machine keys
(snake_case, never displayed) and display labels (authored per pack, always displayed).
Invariant I3.

---

## 3. Settled decisions

1. **YAML, not JSON.** Authors are instructors. YAML has comments; JSON does not.
2. **One directory per pack**, not one file. A pack is ~2,000+ rows of stakeholder
   preferences; a single file is unreviewable.
3. **Semver `pack_version`.** `pack_key` is stable forever (`CONTRACTS.md`).
4. **Every displayed string is authored in the pack.** No English in engine code.
5. **Two-layer stakeholders** — 14 platform archetypes, per-pack persona instances
   (`design/05-implementation-plan.md §1.4.1`).
6. **Archetype defaults with per-item override** for stakeholder preferences. Without
   this, pack 2 is unauthorable (`design/04-decisions-g1-g6.md`).
7. **Balanced Scorecard is the headline frame**; Ch 1 objectives are declaration
   vocabulary (`design/03`).
8. **Six rounds default**, overridable per instance via `settings`.

---

## 4. Open decisions

| # | Question | Criteria | Reporting |
|---|---|---|---|
| **O1** | Should `capability` and `value_chain_activity` be one concept or two? | **Default: one.** A capability *is* a value chain activity; the Applications screen groups them under Porter's primary/support split via a `chain_position` field. Two concepts would need a mapping table nobody would maintain | Record in `dod.md` |
| **O2** | Demand curves: absolute per round, or a base plus growth rate? | **Default: explicit absolute values per round.** Six numbers an instructor can read and tune beat a formula they must simulate. Verbose but legible | Record |
| **O3** | Stakeholder preference storage: one file per decision domain (mis_lite's nine) or one flat file? | **Default: one file per domain**, mirroring the harvest source, so 1.3 is a near-mechanical transform | Record |

---

## 5. Design — the schema

### 5.1 Pack layout

```
packs/riverside_grocery/
  pack.yaml                 identity, version, rounds, company profile
  strategies.yaml           4 strategies: weights, headline metric, expected mix
  capabilities.yaml         required roles, entities, demand curves, chain position
  catalog.yaml              buildable items with full attribute vectors
  platform.yaml             shared services, pools, placement options
  entities.yaml             data entities, levels of detail, sensitivity
  watch_rules.yaml          thresholds that raise signals
  events.yaml               event deck with preconditions
  stakeholders.yaml         persona instances bound to the 14 archetypes
  preferences/              one file per decision domain (O3)
    catalog.yaml  platform.yaml  training.yaml  …
  policies.yaml             information policy options and their costs
  questions.yaml            management questions + data requirements
  labels.yaml               every displayed string, including sidebar labels
```

### 5.2 `pack.yaml`

```yaml
pack_key: riverside_grocery          # stable forever, snake_case
pack_version: 0.1.0                  # semver
schema_version: 1                    # bumps when THIS spec changes
display_name: "Riverside Grocers"
vertical: grocery_retail
rounds: 6
company:
  employees: 620
  sites: 8
  revenue_musd: 140
  founded: 1987
  narrative: |                       # authored prose, shown at round 1
    ...
budget:
  capex_per_round: [400000, 260000, 220000, 220000, 200000, 200000]
  opening_opex: 47000
```

### 5.3 `capabilities.yaml` — feeds Coverage · Capacity · Reliability · Data adequacy

```yaml
- key: order_fulfilment              # machine key, never displayed
  chain_position: primary/outbound_logistics
  required_roles: [transaction_store, order_app, client_access,
                   network_path, wms_integration]
  required_entities:
    - entity: ORDER
      min_level_of_detail: order_line
    - entity: INVENTORY
      min_level_of_detail: sku_location
  demand_curve: [6000, 6600, 12000, 15000, 18000, 22000]   # per round (O2)
  demand_unit: orders
```

`required_roles` is bare role keys per `CONTRACTS.md`. Display labels live in
`labels.yaml`.

### 5.4 `catalog.yaml` — the attribute vectors that replace `cost_tier`

```yaml
- key: centraline_im7
  roles_filled: [inventory_app]
  serves: [inventory_management]
  deployment_modes:                  # CONTRACTS.md: on_prem | cloud | saas
    on_prem: {capex: 86000, opex: 1900, lead_time_rounds: 2}
    cloud:   {capex: 12000, opex: 7400, lead_time_rounds: 0}
    saas:    {capex: 0,     opex: 9100, lead_time_rounds: 0, bypasses_platform: true}
  sizing:
    driver: sku_count                # ONE driver per item (design/01 §5)
    base: {compute: 2, storage_gb: 1000}
    per_unit: {compute: 0.8, storage_gb: 500, per: 10000}
  availability: 0.99
  service_life_rounds: 6
  staff_load: 0.4                    # feeds the IT capacity pool (G1)
  owns_entities: [{entity: INVENTORY, level_of_detail: sku_location}]
  must_be_fed_by: [{entity: PRODUCT, from_capability: point_of_sale}]
  must_feed: [{entity: INVENTORY, to_capability: order_fulfilment}]
  people_affected: {org_unit: warehouse, count: 34}
  training_options:
    none:  {cost: 0,     coverage: 0.0}
    basic: {cost: 12000, coverage: 0.6}
    full:  {cost: 34000, coverage: 1.0}
  process_option: {cost: 22000, label_key: redesign_picking}
  rgt_tag: grow                      # run | grow | transform
  true_cost_categories: [integration, data_migration, training, capacity]
  decoy_cost_categories: [backup, process_redesign]     # TCO forecast (spec 0.2 lineage)
  config_tiers:
    core:        {capex_multiplier: 1.0,  compute_multiplier: 1.0}
    forecasting: {capex_multiplier: 1.44, compute_multiplier: 1.5}
    full_suite:  {capex_multiplier: 1.87, compute_multiplier: 2.17}
```

### 5.5 `strategies.yaml` — feeds Strategic alignment · Portfolio discipline

```yaml
- key: cost_leadership
  headline_metric: cost_per_transaction
  capability_weights:                # MUST sum to 1.0 (CONTRACTS.md)
    order_fulfilment: 0.35
    store_operations: 0.30
    financial_reporting: 0.15
    customer_insight: 0.10
    point_of_sale: 0.10
  expected_concentration: 0.28       # Herfindahl target
  target_rgt_mix: {run: 0.45, grow: 0.40, transform: 0.15}
  maintenance_floor_pct: 0.15
  punishes: overprovisioning
  reopen_cost: 80000
```

### 5.6 `watch_rules.yaml` + `events.yaml` — feed Signal responsiveness

```yaml
# watch_rules.yaml
- key: ORD-CAP-01
  capability: order_fulfilment
  metric: capacity_utilisation
  warn_above: 0.80
  critical_above: 0.95
  cleared_by: [scale_node, add_node, move_to_cloud]   # CONTRACTS.md: exact keys

# events.yaml
- key: saturday_queue_collapse
  preconditions:
    - {type: signal_open, signal: ORD-CAP-01, severity: critical}
    - {type: demand_exceeds_capacity, capability: order_fulfilment, ratio: 1.3}
  strategy_affinity: [cost_leadership]     # deck draws against declaration
  from_persona: tom_beckett
  body_key: event_saturday_queue
  outcomes:
    revenue_loss: 142000
    scorecard: {customer: -8, financial: -5}
```

### 5.7 `preferences/` — the archetype-default mechanism (decision 6)

```yaml
# preferences/catalog.yaml
defaults_by_archetype:               # applies to every catalog item unless overridden
  finance:     {ideal_cost_posture: low,  weight: 0.9}
  operations:  {ideal_reliability: 0.99,  weight: 0.8}
  it:          {ideal_staff_load: low,    weight: 0.7}
overrides:
  - item: centraline_im7
    archetype: operations
    ideal_value: 85
    weight: 1.0
```

Without `defaults_by_archetype`, pack 2 requires ~2,100 hand-authored rows and is
therefore unauthorable. This section is **mandatory**, not optional.

### 5.8 `labels.yaml` — every displayed string

```yaml
capabilities:
  order_fulfilment: "Order Fulfilment"
roles:
  wms_integration: "Warehouse system connection"
sidebar:                             # globalstrat's server-supplied sidebarLabels
  applications: "Applications"
  platform: "Platform"
events:                              # keyed by body_key: the persona's message (prose)
  event_saturday_queue: |
    Online orders queued for six hours Saturday...
event_names:                         # keyed by the event's own key: its short title
  saturday_overflow: "Saturday Overflow"
```

**`event_names` added by finding J1.** Every label family maps a key to a short name;
`events` was the exception — it maps `body_key` to a paragraph of in-world prose, so a
finding about an event (E21) had nowhere to read a title and led with the machine key.
`event_names` is the title map, keyed by the event's own key. Optional: an event with no
title falls back to its key, so existing packs load unchanged.

**No English literal may appear in engine code.** Invariant I2.

---

## 5.9 Seed — the Riverside pack is REAL, not a skeleton *(GOVERNANCE §4.9)*

**Reverses this spec's earlier "content stubbed with TODO markers."** A pack of `TODO`
markers cannot demonstrate that the loader works, and 1.2 would validate nothing.

```
seed        backend/packs/riverside_grocery/   fully populated
command     python -m app.casepack.seed riverside_grocery
demonstrate loader parses it and prints:
              7 capabilities · N catalog items · 4 strategies
              every strategy's weights summing to 1.000
              the ~20 pinned figures from 0.4 spec §5.4, read back from the pack
```

Content sources, in order of preference: **harvested** from mis_lite (`design/01` §2),
**pinned** to the mockup figures, or **authored with a stated rationale**. Anything that
cannot be justified is `TODO: calibrate` **and listed in the report** — never silent.

---

## 6. Invariants and their falsification checks

| # | Invariant | Check | Expected |
|---|---|---|---|
| I1 | No engine code branches on pack identity | `grep -rniE "riverside\|grocer\|pack_key *==" backend/app/casepack/` | zero hits |
| I2 | No displayed English in engine code | `grep -rnE '"[A-Z][a-z]+ [a-z]+' backend/app/casepack/*.py \| grep -v '#\|"""\|log\|raise'` | zero hits |
| I3 | Machine keys are snake_case, never displayed | every `key:` matches `^[a-z][a-z0-9_]*$` | all pass |
| I4 | Every `required_role` is fillable by ≥1 catalog item | cross-reference script | zero unfillable |
| I5 | Every strategy's `capability_weights` sums to 1.0 ±0.001 | load and assert | all 4 pass |
| I6 | Every `cleared_by` key is a real action type | cross-reference against the action enum | zero orphans |
| I7 | Every `demand_curve` has exactly `rounds` entries | load and assert | all pass |
| I8 | Pydantic models round-trip YAML without loss | load → dump → diff | byte-identical modulo key order |

---

## 7. Pre-Flight Verification Register

| # | Claim | Tag | Check | Expected |
|---|---|---|---|---|
| 1 | 0.2 merged; `backend/app/` exists | `[V]` | `git ls-tree --name-only origin/main -- backend/app/` | present |
| 2 | `CONTRACTS.md` has 9 entries this schema must honour | `[V]` | `grep -c "^## " CONTRACTS.md` | ≥ 9 |
| 3 | mis_lite has 14 stakeholders, 4 strategies | `[V]` | `PGPASSWORD=… psql -h 192.168.50.38 -U donwh -d mis_lite -c "select count(*) from stakeholders; select count(*) from strategy;"` | 14, 4 |
| 4 | mis_lite `component_types_master` = 45, ~19 buildable | `[V]` | `psql … -c "select count(*) from component_types_master;"` + `design/01 §3` | 45 |
| 5 | `pydantic` and a YAML lib are available | `[A]` | `grep -n "pydantic" backend/requirements.txt; python3 -c "import yaml"` | pydantic pinned; PyYAML **NEW — add to requirements** |
| 6 | No `packs/` directory exists yet | `[V]` | `ls backend/packs 2>&1` | not found |

---

## 8. Build steps

**Step 1 — Schema document.** Write `docs/casepack-schema.md`: every section, every
field, type, required/optional, and one worked example per section. **This is the artefact
an instructor authors from.** *Verify:* every section in §5 documented; a reader can
author a section without reading Python.

**Step 2 — Pydantic models.** `backend/app/casepack/models.py`. Types, enums, constraints.
No I/O. *Verify:* `python -c "from app.casepack.models import Casepack"` succeeds;
mypy/pyright clean.

**Step 3 — Loader.** `backend/app/casepack/loader.py` — directory → typed `Casepack`.
Clear errors naming file and line. *Verify:* loads the skeleton pack; a deliberately
malformed file produces an error naming the file and field.

**Step 4 — Skeleton pack.** `backend/packs/riverside_grocery/` — every file present,
structure complete, content **stubbed with `TODO` markers** where 1.3 will harvest.
Real content only for the fixed figures in `handoffs/0.3-mockup-pilot/spec.md §5.4`, so
the mockups and the engine agree. *Verify:* loader parses it; I3–I8 pass.

**Step 5 — Invariant checks as a script.** `backend/app/casepack/checks.py` — the
functions 1.2 will wrap in a CLI. *Verify:* all eight run against the skeleton.

---

## 9. Definition of Done

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–6 reported | | |
| Step 1 — schema document | | |
| Step 2 — Pydantic models | | |
| Step 3 — loader with named errors | | |
| Step 4 — skeleton pack loads | | |
| Step 5 — checks script | | |
| I1 no pack-identity branching | | |
| I2 no displayed English in code | | |
| I3 keys snake_case | | |
| I4 every role fillable | | |
| I5 strategy weights sum 1.0 | | |
| I6 `cleared_by` keys resolve | | |
| I7 demand curves length = rounds | | |
| I8 YAML round-trips | | |
| O1 capability/activity — recorded | | |
| O2 demand curve form — recorded | | |
| O3 preference file split — recorded | | |
| `CONTRACTS.md` updated for any new cross-cutting field | | |
| Every §5 section traced to a factor in `design/02` | | |
| PyYAML added to `requirements.txt` | | |
| Auth / instance-isolation / browser canaries | | **N-A** — headless, no state, no UI |

---

## 10. Verification script

No browser playthrough — this module is headless (`QUALITY_PROTOCOL.md §3`: playthroughs
are for user-facing workflows). `verify.md` in this folder holds the CLI sequence the
auditor re-runs.
| **Seed** — Riverside pack populated, loader prints real counts, weights sum to 1.000 | | |
| No unlisted `TODO` in shipped pack content | | |
