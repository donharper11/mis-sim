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

Optional files:

```text
backend/packs/<pack_key>/
  obligation_rules.yaml
```

A pack with no `obligation_rules.yaml` loads clean; the section reads as an empty list.

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
| `services` | list | yes | Each service has `key`, `roles_filled`, `placement_options`, `capacity_pct`, `staff_load`, optional `owns_entities`, `provenance` |
| `support_tiers` | list | yes | Each tier has `key`, `cost`, `fte_equivalent`, `provenance` |
| `integration_tiers` | list | yes | Each tier has `key`, `cost`, `provenance` |
| `starting_staff_fte` | number | yes | Initial IT staff capacity |

A shared service may also be the system of record for a data entity. `owns_entities` takes
the same shape as `catalog.yaml`'s field of the same name — a list of `{entity,
level_of_detail}` — and it exists because filling a *role* is not the same as holding the
*entity* that role's capability needs. `central_sign_on` fills the identity role, but until
it declares that it owns `user_account`, `firm_infrastructure`'s requirement is
unsatisfiable as authored.

`owns_entities` is optional and defaults to an empty list.

Worked example:

```yaml
services:
  - key: central_sign_on
    roles_filled: [identity_directory]
    placement_options:
      on_prem: {capex: 40000, opex: 2000, lead_time_rounds: 1}
    capacity_pct: 60
    staff_load: 0.3
    owns_entities:
      - {entity: user_account, level_of_detail: named_user}
    provenance: {source: AUTHORED, note: identity is the system of record for accounts}
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
| `metric_kind` | enum | no | `threshold` or `presence`; defaults to `threshold` |
| `warn_above` | number/null | yes | Threshold. Must be null when `metric_kind: presence` |
| `critical_above` | number/null | yes | Threshold. Must be null when `metric_kind: presence` |
| `cleared_by` | snake string list | yes | Action type keys matched exactly |
| `provenance` | object | yes | Source tag and rationale |

### Two kinds of rule

A watch rule answers one of two different questions, and `metric_kind` says which.

**`threshold`** — the metric is a number, and the rule fires when it climbs past a line you
draw. *"Order fulfilment is running at 95% of the capacity it has."* It must carry at least
one of `warn_above` / `critical_above`; a threshold rule with neither can never fire, and
the validator reports it as an error.

**`presence`** — the metric is a yes/no condition, and the rule fires when the condition is
true. *"Nothing is managing who can sign in."* It carries **neither** threshold, and it
raises at `critical`, never at `warning`: a condition is either true or it is not, so there
is no magnitude to be mildly concerned about.

> **Declare the kind on every rule you author.** `metric_kind` defaults to `threshold`
> because every rule written before the field existed was threshold-shaped, and defaulting
> is the only way those packs keep loading. The default is a migration affordance, not a
> licence to leave it unstated — a rule with no thresholds *and* no declared kind is a rule
> nobody can tell the difference between "presence" and "unfinished" on, and the validator
> reads it as unfinished.

Worked examples — one of each kind:

```yaml
- key: ord_cap_01
  capability: order_fulfilment
  metric: capacity_utilisation
  metric_kind: threshold
  warn_above: 0.80
  critical_above: 0.95
  cleared_by: [scale_node, add_node, move_to_cloud]

- key: sec_identity_01
  capability: firm_infrastructure
  metric: missing_identity_access
  metric_kind: presence
  warn_above: null
  critical_above: null
  cleared_by: [add_service_tier, add_policy]
```

## `events.yaml`

Feeds event deck, inbox, response decisions, rationale tags, and outcome trace.

| Field | Type | Required | Notes |
|---|---|---|---|
| `key` | snake string | yes | Event identifier |
| `preconditions` | list | yes | Each has `type` plus the fields that type reads; see below |
| `strategy_affinity` | list | yes | Strategy keys |
| `from_persona` | snake string | yes | Stakeholder/persona key |
| `body_key` | snake string | yes | Label key in `labels.events` |
| `outcomes` | object | yes | `revenue_loss`, `scorecard` delta map |
| `options` | list | yes | Each has `key`, `tags`, `cost` |
| `provenance` | object | yes | Source tag and rationale |

### Preconditions

An event fires when every one of its preconditions is true. Each precondition names a
`type`, and each type reads only the fields it needs — every field below is optional, and
you author the ones your `type` calls for.

| Field | Type | Read by |
|---|---|---|
| `type` | snake string | required on every precondition |
| `signal` | string | `signal_open` — the watch rule key |
| `severity` | enum | `signal_open` — `warning` or `critical` |
| `capability` | snake string | `demand_exceeds_capacity`, `adoption_below`, `sponsor_unassigned` |
| `ratio` | number | `demand_exceeds_capacity`, `adoption_below`, `staffing_over`, `debt_above` |
| `node` | snake string | `node_is_spof` |
| `entity` | snake string | `entity_unowned` |
| `policy` | snake string | `policy_contradiction` |
| `round` | integer | `round_equals` — a whole round number, never a ratio |
| `count` | integer | `placement_count` |

`round` is an integer because a round is a whole number. Do not express it as `ratio`, and
do not press any other parameter into `ratio` either: a precondition that says
`ratio: 4` when it means "round 4" reads as a threshold to everyone downstream.

Worked example:

```yaml
- key: warehouse_rollout_gap
  preconditions:
    - {type: signal_open, signal: wh_rollout_01, severity: critical}
    - {type: node_is_spof, node: kelso_road_link}
    - {type: entity_unowned, entity: user_account}
    - {type: round_equals, round: 4}
  from_persona: dana_ruiz
  body_key: event_tablets_arrived
  options:
    - {key: fund, tags: [strategic_priority], cost: 6000}
```

## `obligation_rules.yaml` — optional

Feeds the privacy and ethics layer. An obligation rule connects a policy switch to a
consequence: when a sensitive entity is held under a permissive policy, the obligation
raises, and while it stays open it arms the events named in `arms` — a regulator letter, a
subject access request, staff snooping.

Obligations reuse the signal machinery exactly. They raise like a signal, they clear like a
signal, and they arm events like a signal. There is no separate ethics subsystem.

**This file is optional.** A pack without it loads clean and simply has no obligations; the
policy switches then change no outcome, which is a content gap rather than a broken pack.

| Field | Type | Required | Notes |
|---|---|---|---|
| `key` | snake string | yes | Obligation identifier |
| `entity` | snake string | yes | An entity the pack defines in `entities.yaml` |
| `condition` | snake string | yes | What makes the obligation true, e.g. `policy_permits` |
| `policy` | snake string | yes | The policy switch the condition reads |
| `permissive_value` | string | yes | The value of that policy which leaves the obligation open. Should name one of that policy's `options` — see [`default` is not `permissive_value`](#default-is-not-permissive_value) |
| `severity` | enum | no | `critical` only, and the default. See below |
| `cleared_by` | snake string list | yes | Action type keys matched exactly, as in `watch_rules.yaml` |
| `arms` | snake string list | no | Event keys this obligation can arm; defaults to empty |
| `provenance` | object | yes | Source tag and rationale |

An obligation is presence-shaped by construction — the condition holds or it does not — so
it raises at `critical` and there is no warning tier to author.

Worked example:

```yaml
- key: customer_pii_retention
  entity: customer
  condition: policy_permits
  policy: data_retention
  permissive_value: indefinite
  severity: critical
  cleared_by: [add_policy, retire_component]
  arms: [regulator_letter]
  provenance:
    source: AUTHORED
    note: Ch 4 privacy layer; retention left open is the classic exposure
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
| `options` | snake string list | no | The states this switch can be in. Defaults to empty |
| `default` | snake string | no | The state a team holds by not deciding. Defaults to unset |
| `provenance` | object | yes | Source tag and rationale |

Worked example:

```yaml
- key: encrypt_customer_data
  category: data_governance
  cost: 1500
  effects: {privacy_risk: -0.2, staff_load: 0.05}
```

### `options` and `default` — a policy's value vocabulary

A policy is a **switch**, and a switch has positions. `options` enumerates them, and
`default` names the position a team occupies before it has decided anything.

```yaml
- key: data_retention
  category: data_governance
  cost: 9000
  effects: {privacy_risk: -0.25, staff_load: 0.05}
  options: [minimal, standard, indefinite]
  default: indefinite
  provenance:
    source: AUTHORED
    note: how long customer contact and purchase history is kept
```

**Ordering is an authoring convention, not semantics.** Listing `minimal` first does not
make it the strict end. Nothing reads position, and nothing should be authored on the
assumption that it does.

**`default` is what makes the ethics layer cost something to ignore.** A team that never
opens the Security screen still holds a policy position — the one you authored here. If the
default you choose is the permissive one, ignoring the obligation has a price. If you author
no default at all, a team starts nowhere and the ethics layer becomes something to opt into
rather than something to manage. A pack may legitimately start a team somewhere already
compliant; that is a deliberate authoring choice about where this company begins, not an
oversight.

**One rule is enforced:** if `options` is non-empty, `default` must be one of them. A pack
that names a `default` outside its own `options` will not load.

```yaml
options: [minimal, standard, indefinite]
default: forever          # rejected -- 'forever' is not one of the declared options
```

Everything else is left open on purpose. `options` may be omitted — a policy without it is
the legacy shape and loads exactly as it always has. `default` may be omitted too, with or
without `options`.

### `default` is not `permissive_value`

These two look alike and are frequently the same string. They are different concepts and
they live in different files.

| | Lives in | Means |
|---|---|---|
| `default` | `policies.yaml` | **where a team starts** — the position held by not deciding |
| `permissive_value` | `obligation_rules.yaml` | **what obliges** — the position that leaves an obligation open |

Read together, the pair is what tells the engine whether a team has moved:

```yaml
# policies.yaml
- key: data_retention
  options: [minimal, standard, indefinite]
  default: indefinite            # this company keeps everything, until someone changes it

# obligation_rules.yaml
- key: customer_pii_retention
  entity: customer
  condition: policy_permits
  policy: data_retention
  permissive_value: indefinite   # and keeping everything is what the regulator objects to
```

Here they coincide, so the pack starts permissive: the obligation is open from round 1 and
stays open until a team moves the switch. Author them apart and the pack starts compliant —
`default: standard` against `permissive_value: indefinite` means a team has to actively
choose the exposure. Both are valid packs. Which one you author is a statement about the
company, and it should be one you made on purpose.

`permissive_value` should name a member of the policy's `options`; otherwise it points at a
state the switch cannot be in. The validator does not yet check this — author it correctly.

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
| `events` | map | no | Event body strings — see the note below |
| `policies` | map | no | Policy labels |
| `entities` | map | no | Entity key to display label |
| `catalog` | map | no | Catalog item key to display label |
| `watch_rules` | map | no | Watch rule key to display label |
| `questions` | map | no | Question key to display label |
| `misc` | map | no | Other authored display strings |

Author a label for every key an instructor or a student will see named. Without one, the
message leads with the machine key — an instructor reading a validator finding gets
`wh_rollout_01` where they should get "Warehouse rollout adoption".

> **`events` is not a name map.** Every other section here maps a key to a short display
> name. `events` maps an event's `body_key` to the persona's message — a sentence or a
> paragraph of in-world prose. There is currently nowhere to author an event's *name*,
> which is why messages about events still print machine keys.

Worked example:

```yaml
capabilities:
  order_fulfilment: Order Fulfilment
roles:
  wms_integration: Warehouse system connection
watch_rules:
  ord_cap_01: Order fulfilment capacity
entities:
  user_account: User accounts
questions:
  inventory_accuracy: Do we know our inventory is right?
```

## Open Decision Defaults Recorded

O1: capability and value-chain activity are one concept, represented by `Capability`
with `chain_position`.

O2: demand curves are explicit absolute per-round arrays.

O3: stakeholder preferences are one file per decision domain under `preferences/`.
