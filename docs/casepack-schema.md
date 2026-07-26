# Casepack Schema

This document is the instructor-facing authoring reference for MIS Simulation casepacks.
A casepack is a directory of YAML files loaded into a typed `Casepack` object. Machine
keys are stable, lower snake case, and never displayed to students. Display text lives in
`labels.yaml`.

## Layout

Required files:

```text
backend/packs/<pack_key>/
  pack.yaml
  strategies.yaml
  capabilities.yaml
  catalog.yaml
  platform.yaml
  entities.yaml
  watch_rules.yaml
  events.yaml
  stakeholders.yaml
  preferences/*.yaml
  policies.yaml
  questions.yaml
  labels.yaml
```

## Shared Rules

`key` fields are required unless stated otherwise and use `^[a-z][a-z0-9_]*$`.
`provenance` is required on authored content records and has:

| Field | Type | Required | Notes |
|---|---|---|---|
| `source` | enum | yes | `HARVESTED`, `PINNED`, or `AUTHORED` |
| `note` | string | yes | States source and rationale |

Worked example:

```yaml
provenance:
  source: PINNED
  note: handoffs/0.4-mockups-remaining/spec.md section 5.4
```

## `pack.yaml`

Feeds budget, company profile, round count, and the seeded baseline used to prove the
loader reads real content.

| Field | Type | Required | Notes |
|---|---|---|---|
| `pack_key` | snake string | yes | Stable forever |
| `pack_version` | semver string | yes | Example `0.1.0` |
| `schema_version` | integer | yes | Positive integer |
| `display_name` | string | yes | Authored display label |
| `vertical` | snake string | yes | Industry family |
| `rounds` | integer | yes | Positive; default design is 6 |
| `company` | object | yes | `employees`, `sites`, `revenue_musd`, `founded`, `narrative` |
| `budget` | object | yes | `capex_per_round[]`, `opening_opex`; capex length equals rounds |
| `initial_state` | object | yes | Seeded baseline; see below |

`initial_state` records pinned mockup figures for seed evidence. It includes `round`,
declared strategy, round budget, Balanced Scorecard, attention items, unit response
chain, value-chain coverage, open signal counts, IT staff/load, and Review totals.

Worked example:

```yaml
pack_key: riverside_grocery
pack_version: 0.1.0
schema_version: 1
display_name: Riverside Grocers
vertical: grocery_retail
rounds: 6
budget:
  capex_per_round: [400000, 260000, 220000, 220000, 200000, 200000]
  opening_opex: 47000
```

## `capabilities.yaml`

Feeds coverage, capacity, reliability, data adequacy, strategic alignment, governance,
and reporting detail.

| Field | Type | Required | Notes |
|---|---|---|---|
| `key` | snake string | yes | Capability identifier |
| `chain_position` | string | yes | `primary/...` or `support/...` |
| `required_roles` | snake string list | yes | Bare role keys; must be filled by catalog/platform |
| `required_entities` | list | yes | Each has `entity`, `min_level_of_detail` |
| `demand_curve` | integer list | yes | Exactly `rounds` entries |
| `demand_unit` | snake string | yes | Unit for the curve |
| `provenance` | object | yes | Source tag and rationale |

Worked example:

```yaml
- key: order_fulfilment
  chain_position: primary/outbound_logistics
  required_roles: [transaction_store, order_app, client_access, network_path]
  required_entities:
    - {entity: order, min_level_of_detail: order_line}
  demand_curve: [6000, 6600, 12000, 15000, 18000, 22000]
  demand_unit: orders
```

## `catalog.yaml`

Feeds application choices, placement, capacity draw, reliability, lifecycle, staff load,
training/process decisions, TCO forecast, and Run/Grow/Transform mix.

| Field | Type | Required | Notes |
|---|---|---|---|
| `key` | snake string | yes | Catalog item identifier |
| `roles_filled` | snake string list | yes | Roles this item can satisfy |
| `serves` | snake string list | yes | Capability keys |
| `deployment_modes` | map | yes | Keys: `on_prem`, `cloud`, `saas`; each has `capex`, `opex`, `lead_time_rounds`, optional `bypasses_platform` |
| `sizing` | object | yes | `driver`, `base{compute, storage_gb}`, `per_unit{compute, storage_gb, per}` |
| `availability` | number | yes | `0 < availability <= 1` |
| `service_life_rounds` | integer | yes | Positive |
| `staff_load` | number | yes | IT FTE load |
| `owns_entities` | list | yes | May be empty; each has `entity`, `level_of_detail` |
| `must_be_fed_by` | list | yes | May be empty; each has `entity`, `from_capability` |
| `must_feed` | list | yes | May be empty; each has `entity`, `to_capability` |
| `people_affected` | object | yes | `org_unit`, `count` |
| `training_options` | map | yes | Each has `cost`, `coverage` |
| `process_option` | object/null | yes | `cost`, `label_key` |
| `rgt_tag` | enum | yes | `run`, `grow`, `transform` |
| `true_cost_categories` | list | yes | TCO checklist truth |
| `decoy_cost_categories` | list | yes | TCO distractors |
| `config_tiers` | map | yes | Each has `capex_multiplier`, `compute_multiplier` |
| `provenance` | object | yes | Source tag and rationale |

Worked example:

```yaml
- key: centraline_im7
  roles_filled: [inventory_app, wms_integration]
  serves: [order_fulfilment]
  deployment_modes:
    on_prem: {capex: 86000, opex: 1900, lead_time_rounds: 2}
    cloud: {capex: 12000, opex: 7400, lead_time_rounds: 0}
    saas: {capex: 0, opex: 9100, lead_time_rounds: 0, bypasses_platform: true}
```

## `strategies.yaml`

Feeds strategy declaration, strategic alignment, portfolio concentration, RGT mix,
maintenance floor, and reopen cost.

| Field | Type | Required | Notes |
|---|---|---|---|
| `key` | snake string | yes | Strategy identifier |
| `headline_metric` | snake string | yes | What this strategy measures |
| `capability_weights` | map | yes | Capability key to number; sums to 1.000 |
| `expected_concentration` | number | yes | 0 to 1 |
| `target_rgt_mix` | map | yes | `run`, `grow`, `transform`; values sum conceptually to 1 |
| `maintenance_floor_pct` | number | yes | 0 to 1 |
| `punishes` | snake string | yes | Penalty label key |
| `reopen_cost` | integer | yes | Capex cost |
| `harvested_raw_fit` | map | no | Raw source multipliers retained as provenance |
| `provenance` | object | yes | Source tag and rationale |

Worked example:

```yaml
- key: cost_leadership
  headline_metric: cost_per_transaction
  capability_weights:
    order_fulfilment: 0.35
    store_operations: 0.30
    financial_reporting: 0.15
    customer_insight: 0.10
    marketing_sales: 0.10
```

## `platform.yaml`

Feeds shared platform services, support tiers, integration tiers, and IT staffing load.

| Field | Type | Required | Notes |
|---|---|---|---|
| `services` | list | yes | Each service has `key`, `roles_filled`, `placement_options`, `capacity_pct`, `staff_load`, `provenance` |
| `support_tiers` | list | yes | Each tier has `key`, `cost`, `fte_equivalent`, `provenance` |
| `integration_tiers` | list | yes | Each tier has `key`, `cost`, `provenance` |
| `starting_staff_fte` | number | yes | Initial IT staff capacity |

Worked example:

```yaml
support_tiers:
  - key: basic
    cost: 20000
    fte_equivalent: 0.6
    provenance: {source: HARVESTED, note: mis_lite Basic Support}
```

## `entities.yaml`

Feeds data adequacy, policy contradiction checks, management question answerability, and
reporting detail.

| Field | Type | Required | Notes |
|---|---|---|---|
| `key` | snake string | yes | Entity identifier |
| `levels_of_detail` | snake string list | yes | Ordered coarse to fine |
| `sensitivity` | enum | yes | `low`, `medium`, `high` |
| `provenance` | object | yes | Source tag and rationale |

Worked example:

```yaml
- key: order
  levels_of_detail: [daily_store_total, order_header, order_line]
  sensitivity: medium
```

## `watch_rules.yaml`

Feeds signal responsiveness and event preconditions.

| Field | Type | Required | Notes |
|---|---|---|---|
| `key` | snake string | yes | Signal/watch identifier |
| `capability` | snake string | yes | Capability key |
| `metric` | snake string | yes | Metric key |
| `warn_above` | number/null | yes | Threshold |
| `critical_above` | number/null | yes | Threshold |
| `cleared_by` | snake string list | yes | Action type keys matched exactly |
| `provenance` | object | yes | Source tag and rationale |

Worked example:

```yaml
- key: ord_cap_01
  capability: order_fulfilment
  metric: capacity_utilisation
  warn_above: 0.80
  critical_above: 0.95
  cleared_by: [scale_node, add_node, move_to_cloud]
```

## `events.yaml`

Feeds event deck, inbox, response decisions, rationale tags, and outcome trace.

| Field | Type | Required | Notes |
|---|---|---|---|
| `key` | snake string | yes | Event identifier |
| `preconditions` | list | yes | Each has `type` and optional signal/severity/capability/ratio |
| `strategy_affinity` | list | yes | Strategy keys |
| `from_persona` | snake string | yes | Stakeholder/persona key |
| `body_key` | snake string | yes | Label key in `labels.events` |
| `outcomes` | object | yes | `revenue_loss`, `scorecard` delta map |
| `options` | list | yes | Each has `key`, `tags`, `cost` |
| `provenance` | object | yes | Source tag and rationale |

Worked example:

```yaml
- key: warehouse_rollout_gap
  from_persona: dana_ruiz
  body_key: event_tablets_arrived
  options:
    - {key: fund, tags: [strategic_priority], cost: 6000}
```

## `stakeholders.yaml`

Feeds stakeholder alignment and persona grounding. It stores persona instances bound to
platform archetypes.

| Field | Type | Required | Notes |
|---|---|---|---|
| `key` | snake string | yes | Stakeholder identifier |
| `archetype` | snake string | yes | One of the platform archetypes |
| `display_name_key` | snake string | yes | Resolves in `labels.stakeholders` |
| `role_key` | snake string | yes | Resolves in `labels.misc` |
| `stakeholder_type` | enum | yes | `internal` or `external` |
| `provenance` | object | yes | Source tag and rationale |

Worked example:

```yaml
- key: operations
  archetype: operations
  display_name_key: stakeholder_operations
  role_key: role_operations_department
  stakeholder_type: internal
```

## `preferences/*.yaml`

Feeds the stakeholder-alignment layer and makes later packs authorable through defaults.
One file per decision domain is the default from O3.

| Field | Type | Required | Notes |
|---|---|---|---|
| `defaults_by_archetype` | map | yes | Archetype key to preference values |
| `overrides` | list | yes | May be empty; item-specific exceptions |
| `provenance` | object | yes | Source tag and rationale |

Worked example:

```yaml
defaults_by_archetype:
  finance: {ideal_cost_posture: low, weight: 0.9}
  operations: {ideal_reliability: 0.99, weight: 0.8}
overrides:
  - {item: order_mgmt_v42, archetype: operations, ideal_value: 85, weight: 1.0}
```

## `policies.yaml`

Feeds information policy, policy cost, privacy/security effects, and policy-vs-practice
contradictions.

| Field | Type | Required | Notes |
|---|---|---|---|
| `key` | snake string | yes | Policy option identifier |
| `category` | snake string | yes | Policy group |
| `cost` | integer | yes | Non-negative |
| `effects` | map | yes | Authored effect vector |
| `provenance` | object | yes | Source tag and rationale |

Worked example:

```yaml
- key: encrypt_customer_data
  category: data_governance
  cost: 1500
  effects: {privacy_risk: -0.2, staff_load: 0.05}
```

## `questions.yaml`

Feeds management question answerability and data adequacy.

| Field | Type | Required | Notes |
|---|---|---|---|
| `key` | snake string | yes | Question identifier |
| `requires_entities` | list | yes | Entity and minimum level required |
| `provenance` | object | yes | Source tag and rationale |

Worked example:

```yaml
- key: inventory_accuracy
  requires_entities:
    - {entity: inventory, min_level_of_detail: sku_location}
```

## `labels.yaml`

Feeds every displayed string. Python code never supplies student-facing labels.

| Field | Type | Required | Notes |
|---|---|---|---|
| `capabilities` | map | no | Capability key to display label |
| `roles` | map | no | Role key to display label |
| `sidebar` | map | no | Navigation labels |
| `strategies` | map | no | Strategy labels |
| `stakeholders` | map | no | Stakeholder labels |
| `events` | map | no | Event body strings |
| `policies` | map | no | Policy labels |
| `misc` | map | no | Other authored display strings |

Worked example:

```yaml
capabilities:
  order_fulfilment: Order Fulfilment
roles:
  wms_integration: Warehouse system connection
```

## Open Decision Defaults Recorded

O1: capability and value-chain activity are one concept, represented by `Capability`
with `chain_position`.

O2: demand curves are explicit absolute per-round arrays.

O3: stakeholder preferences are one file per decision domain under `preferences/`.
