# M1 decision-driven simulation — master contract

Authored under `SPEC_PROTOCOL.md` v1.3, 2026-09-14. Author: `m1_contract_author`.
Base: `b7706fb2ff8cc63cee7e871bb9fbe82d24835074`. Tier: **Heavy**.
Status: **REVIEW CANDIDATE; supervisor rulings recorded below; independent review pending.**
This file and `verify.md` are authoring artifacts, not implementation or M1 exit evidence.
Every identifier/interface/parameter below marked NEW is a proposal unless its approval
is recorded in the authority table. No builder dispatch occurs before the final contract
and its bounded packet receive independent review.

## 0. Basis and authority

[V] Read in full: root `GOVERNANCE.md`, `QUALITY_PROTOCOL.md`, `SPEC_PROTOCOL.md`,
`CONTRACTS.md`; `design/04-decisions-g1-g6.md`, `design/07-decision-consequence-map.md`,
`design/08-implementation-north-star.md`; this folder's `inventory.md`, `review.md`;
`handoffs/1.4-scoring-engine/{spec,closeout-spec}.md`,
`handoffs/1.5-event-signal-engine/{spec,contract-spec}.md`,
`handoffs/1.6-round-runner/spec.md`, `handoffs/2.3-round-scheduling/spec.md`.
No `AGENTS.md` was found in the worktree or its filesystem ancestors.

[V] Primary executable readset: complete `backend/app/round/{runner,models,snapshot,actions,db}.py`;
complete `backend/app/engine/{state,graph,catalog,technology,organisation,management,score,rollup,metrics,preconditions,ledger,events}.py`;
complete `backend/app/casepack/{models,loader}.py`; complete
`backend/scripts/check_postgres_runtime.py`, `backend/alembic/env.py`,
`backend/alembic/versions/20260726_0001_baseline.py`, `backend/app/models/base.py`,
`backend/tests/{test_engine_scoring,test_round_pin}.py`, `Makefile`;
`validate.py`'s complete `validate_pack_dir`, `Report`, `exit_code_for` boundary.
Other validator implementation is not a basis for changing it; existing validator internals
remain untouched and are consumed through their public report boundary.

[V] Content read directly: Riverside `catalog.yaml`, `platform.yaml`, `capabilities.yaml`,
`strategies.yaml`, `policies.yaml`, all five `preferences/*.yaml`;
`backend/seeds/{riverside_r3,riverside_full,archetype_base,archetype_balanced,archetype_do_nothing,archetype_all_tech_no_org,archetype_overspender}.py`.
Independent content extraction by `m1_content_basis` is supporting evidence, not authority
for unverified prices or formulas. Runtime initial conditions and missing numeric parameters
are explicitly NEW authored values; old fixture outputs are not their target.

Extraction sufficiency: covered the transition, scoring and persistence seams; no external
service or shared database is needed. Package versions and live platform schemas are not
asserted. New-runtime source does not yet exist: its interfaces and checks are deliverables,
not claims of present behavior. `verify.md` separates author probes from builder checks.

Relevant existing contracts are quoted, not reinterpreted:

- `capital_remaining`: “One home, and it is `initial_state.budget.capital_remaining`.”
  This is the historical authored dashboard; the NEW runtime ledger is a different versioned
  context, never a second mutable copy of that R3 figure.
- `PolicyDecisionState`: “including deliberately retaining the authored default”; absent
  this-round action remains inactive even when last round's selection carries forward.
- `LedgerSignal`: episode identity `(key, episode_id)`; timely clear before a fire is credited.
- Scorecard v1: one point equals `0.01`, current Financial remains partial; no event point
  adjustment changes Tech/Org/Mgmt or firm score.

| Ruling | Supervisor disposition, 2026-09-14 |
|---|---|
| A1 | **APPROVED** separate versioned production service/checkpoints; historical runner retained; no production fallback into scripted seeding. |
| A2 | **APPROVED** service owns fresh transaction per operation; PostgreSQL run-row lock, SQLite `BEGIN IMMEDIATE`; advanced rounds immutable; reopen only locked/unadvanced current round. |
| A3 | **APPROVED** one physical node per asset; additive per-capability capacity and explicit-RTO input seam; existing scalar/default paths remain compatible. No facets. |
| A4 | **APPROVED** NEW organisation formulas in §6, hiring basis, placement staff factors, sunk-cost cancellation; no prepaid rollout for pending orders. |
| A5 | **APPROVED families** content, ringfenced capital/operating reserves, lifecycle and current-round funded prevention; subsequent M1-R11–R15 cover exact initial78200/3.7, action timing, horizon, debt/TCO and preference scope. |
| A6 | **APPROVED** M1-R16/R17 scoped entity access and bounded verified credit-eligible repair inputs, frozen in independently reviewed production-inputs/spec.md at2bab351. M1-R18 at supervisor commit c4a095b approves status-only held-response checks, signed hypothetical preparation with no persisted invalid balances, and exact initial-ID node_is_spof binding; master producer/DTO/game corrections remain subject to fresh review. |

Supervisor owns routine rulings under the user's explicit M1 authorization. Product-reserved
choices remain closed: no LLM scoring, auth UI, second substantive vertical, reflection
policy or claim of pedagogical balance. A contradiction returns here with source evidence;
the builder or auditor cannot bless an alternative.

## 1. Outcome, scope and decomposition

One content-authored estate is initialized once. Six typed decision sheets alone drive
persistent purchases, arrivals, resources, people, management, events, cost and scores.
Changing a decision changes its consequences; the caller cannot submit scores, prices,
throughput, trained counts, adoption, resistance, financial actuals or signal timestamps.
Invalid or unaffordable input leaves persisted state unchanged, including the draft.

[V] The existing runner cannot be used as the transition wrapper: `runner.advance`
materializes arbitrary `InFlightRow.node_payload`, reads per-round seeded rows, derives
funds and actions from caller-priced lines and refuses duplicate results after writes.
`snapshot.build_team_state` does not carry a prior estate. These are preserved historical
interfaces, not production authority. NEW `app.simulation` owns the decision-driven route.

Scoring input ownership touches all existing technology/organisation/management inputs,
financial ledgers and signal responsiveness in `design/02`. The MOT formulas, eight
management factors, event precedence/caps and M0 scorecard unit contract remain frozen.
M1 makes the inputs real; it does not implement full Financial scoring. Data freshness,
rich communication watch predicates, policy preference overrides and remaining policy
vectors, staffing's richer currency/skills model, capital-request approval/terms and
pedagogical retuning remain M4 follow-ups. M2 owns auth, enrollment, section timing and
registry lifecycle; M3 owns the browser loop. Browser/auth/UX ladder rungs are N-A for
this headless milestone, not waived for those later milestones.

One compliant route: validate a bound runtime-content bundle, persist its one-time initial
checkpoint, atomically edit typed drafts, lock a revision, derive next state through pure
estate and organisation reducers, project `TeamState`, call the existing pure ledger/events/
scorer, mechanically reuse M0 scorecard conversion, validate all outputs and commit the
checkpoint plus the existing immutable `RoundResult` in one service-owned transaction.

## 2. NEW versioned service, sheets and identities (D1, D2, D9)

Interfaces below are frozen as **version 1** on approval. Python is M1's production service
boundary; HTTP and actor authorization are M2. It accepts a SQLAlchemy Engine, never a
caller-owned Session. It reads no environment or shared DB URL implicitly.

```python
SimulationService(engine, runtime_pack: RuntimePackV1)
initialize(instance_id, team_id, strategy_key) -> RunViewV1
read(instance_id, team_id) -> RunViewV1
patch_sheet(instance_id, team_id, round, expected_revision, patch: SheetPatchV1) -> SheetViewV1
lock(instance_id, team_id, round, expected_revision) -> SheetViewV1
reopen(instance_id, team_id, round, expected_revision) -> SheetViewV1
advance(instance_id, team_id, round, locked_revision) -> dict  # persisted RoundResult payload
```

All IDs are strict positive integers; booleans are not integers. Machine keys use
`[a-z][a-z0-9_]*`, at most64 characters for physical/reference keys, at most48 for command keys; derived `r<round>_` asset IDs must fit64 or the content round bound rejects. Explicit empty/whitespace-only reason on request_capital is invalid_input before its
unsupported-operation refusal; amount must be positive integer and reason at most1000
characters. Exact bound pack digest is checked on every
operation; missing bundle/version or digest mismatch refuses before writes. There is no
strategy default: initialization requires a declared pack strategy. Allowed rounds are
`1..pack.metadata.rounds`; after the last advance the run is completed and no new sheet
can be opened. Reads of absent scopes return `not_found`; no scope is implicitly created.

NEW `SheetPatchV1 = {version:1, replace_categories: {category: [CommandV1,...]}}`.
Only present categories are replaced. A present `[]` clears that category. Empty map is
an exact no-op without a revision increment. Explicit null anywhere except fields marked
nullable is invalid. Unknown fields/command types/categories/enum values are invalid;
strings, floats or booleans are not coerced to integers, and NaN/Infinity are invalid.
The entire merged candidate is normalized, target-validated and affordability-previewed
before deleting/replacing any draft state. Every accepted nonempty patch increments a
monotone sheet revision even if its canonical commands equal the previous revision.
Expected-revision conflict changes nothing. Commands sort by category then line key;
list order never creates execution precedence.

Every command has `key` and discriminant `op`; category derives from `op` and must equal
its enclosing category. Command keys are unique across the merged sheet. NEW physical
asset/order/project IDs for acquisitions derive as `r<round>_<command.key>`; unchanged
through arrival, retirement or cancellation. Initial asset IDs use authored `initial_*`
keys. Named references resolve only in the selected instance/team checkpoint and candidate
sheet. NEW refs have disjoint typed fields: `asset`, `order`, `connection`, `capability`,
`policy`, `stakeholder`, `option`. Catalog keys are never interchangeable with asset IDs.
A replacement gets a NEW project/order ID from its command but keeps asset_id equal to
the replaced physical asset. Replacement_target equals that asset_id; a new purchase uses
its order ID as asset_id and replacement_target=null. No operation resurrects a terminal
asset or reuses an order identity. TCO is keyed by asset_id, so replacement costs join the
original acquisition forecast; replacement alone creates no second forecast. Initial assets
have actual cost evidence but no invented historical TCO forecast.

| Category | NEW command and complete user-authored fields beyond `key,op` |
|---|---|
| application | `buy_application(catalog,placement,config,primary_for: capability|null,tco_categories: list[str])` |
| platform_service | `buy_service(service,placement,units:int)`; `replace_service(asset,placement,units:int)` |
| application | `replace_application(asset,placement,config)` |
| integration | `connect(src,dst,kind,entity:str|null,tier:str|null)`; `disconnect(connection)` |
| lifecycle | `cancel_order(order)`; `retire_asset(asset)`; `project(order,choice:continue|pause|kill)` |
| training | `train(asset,option)` |
| process_redesign | `set_process(asset,choice:unchanged|partial|redesigned)` |
| communication | `communicate(org_unit,option)` |
| staffing | `hire(option)`; `set_support(tier:str|null,covered_assets:list[str])` |
| governance | `assign(capability,owner:stakeholder|null,sponsor:stakeholder|null)`; `set_primary(capability,asset:str|null)`; `declare_strategy(strategy)` |
| policy | `set_policy(policy,selected)` |
| event_response | `respond(event,option,rationale_tag)` |
| capital_request | `request_capital(amount:int,reason:str)` is recognized but any nonempty category refuses `unsupported_operation`; `[]` clears an empty category; no effect or credit |

Each category above stays in the existing twelve-category vocabulary. `declare_strategy`
is governance reporting, not a thirteenth category. Student-selected category/capex/action
aliases, RGT tags, maintenance flags, arrival dates, output state and raw payloads are forbidden.
`set_support` records a service decision but belongs to staffing because its live v1 effect
is staffing. Integration tiers are selected per `connect`, not a free standing unconsumed tier.

Conflicts reject the whole candidate: two operations setting the same policy/assignment/
primary/support/strategy/process/training/communication target; duplicate physical edge
`(unordered src,dst,kind,entity)`; acquisition and replacement of the same source;
retirement/cancellation/kill combined with any other command touching its target;
replacement with another mutation of its target; missing source/target; a same-sheet cycle
of dependencies. A new purchase may receive connection/rollout/primary commands only if
its preview arrival is this round. A due prior order may receive them unless cancelled or
paused. Unknown/foreign IDs get the same `invalid_reference` shape, without foreign data.

NEW error boundary: `SimulationError(code, field, details)` with closed codes
`not_found`, `invalid_input`, `invalid_reference`, `conflicting_commands`, `unaffordable`,
`revision_conflict`, `locked`, `round_state`, `pack_mismatch`, `scope_exists`,
`unsupported_operation`, `arrival_after_game_end`, `invalid_output`. No authentication claim follows from this
headless service. Unexpected DB/reducer failures propagate after rollback; M2 maps errors
to HTTP/business copy. Details contain local machine keys and required/available amounts,
never SQL, credentials, foreign rows or arbitrary exception strings.

Lock validates the complete draft again and freezes it without running the scorer. Calling
lock with the exact locked revision is idempotent; all other locked edits fail. Reopen is
permitted only for the current locked/unadvanced round, retains the draft, increments its
revision, and removes the lock. It neither deletes results nor rewinds history. Reopening an
advanced round is `round_state` and byte-identical no-op. M2 scheduling must replace its
contradictory old unlock descriptions with this v1 rule before dispatch.

Advance locks the run row, checks digest/round/revision and existing result **before** any
transition. Matching completed round/revision returns that immutable result unchanged;
wrong revision fails. A retry of an older completed round may return its existing result
without moving the current pointer. Concurrent matching advances produce one checkpoint/
result and return equal payloads. Different revisions cannot both resolve. Lock/edit/reopen/
advance serialize on the same run. No wall-clock or random input enters transition results.

## 3. NEW runtime content and one-time initialization (D3, D5)

NEW `RuntimePackV1` holds the original validated `Casepack`, NEW strict `RuntimeContentV1`
from `runtime.yaml`, and SHA-256 of canonical JSON `{casepack, runtime}`. Parsing calls
`validate_pack_dir`, requires zero errors and a non-null pack, then validates the supplement.
Warnings remain visible; Riverside's existing pack stays zero-warning. No optional-runtime
fallback: absent supplement is `unsupported_operation` for production initialization.
The original `Casepack`, schema_version 1, old YAML values and loaders remain unchanged.
Historic consumers ignore the additional file. Runtime validation is a separate versioned
boundary, not a new E00 diagnostic or a rewrite of the casepack validator.

`RuntimePackV1` takes a defensive deep copy of validated Casepack and runtime content,
retains canonical bytes, and exposes immutable views. Service operations recompute the
fingerprint from their private bound objects and compare it to stored digest; callers
cannot mutate the service's inputs through an original Casepack reference. The digest
binds canonical semantic content, not byte formatting or a filesystem watcher. Editing a
file does not alter an already constructed bundle; constructing a new bundle with different
semantic content refuses use against the old run. No file is reread during a transition.

Every numeric supplement leaf is covered by the explicit root provenance/unit pointer
registries defined below; raw source prices remain original Casepack-owned. All new estimates state `TODO: calibrate — owner M1/M4` in that note.
NEW supplement root fields are exactly:

| Field | Required shape and consumer |
|---|---|
| `version` | literal integer 1 |
| `catalog` | map over every original catalog key: `purchasable_placements`, `capacity_by_capability`, `capacity_multiplier_by_config`, `opex_multiplier_by_config`; source catalog still owns prices/roles/entities/people/life/sizing |
| `services` | map over every platform service: `serves`, `availability`, `service_life_rounds`, `capacity_by_capability`, `supply_by_placement:{compute,storage_gb}`, `max_units`; source platform owns prices/roles/entities/staff load |
| `drivers` | exact map of every catalog sizing.driver to six finite nonnegative numbers (or authored number of pack rounds) |
| `people` | organisational parameters in §6, `placement_staff_multiplier`, hiring/communication options, unit keys and initial resistance |
| `initial` | asset references, explicit installed rounds, initial rollout fractions/process/adoption, connections, primary map, governance assignments; no raw node payload or scores |
| `accounting` | opening balances, per-round operating allowances, connection charges/load, cancellation disposition, TCO category estimator rules and derived decision/action attribution enums; §7 |
| `preferences` | typed v1 non-policy preference rules, dispositions and stakeholder caring sets; §6 |
| `response_disposition` | explicit `prevent_current_round` funded disposition/rationale per event; §7 |

Maps reject duplicate/unknown keys; referenced catalog/config/placement/capability/entity/
stakeholder/options must exist. Every catalog serves key has an explicit finite positive
capacity or explicit null. Service maps similarly cover every authored service `serves`.
All config maps exactly cover source configs. `serves` entries are pack capabilities, units
have labels, and arrays reject duplicates. No silent fallback parameter or default formula.

Frozen `RuntimeContentV1` JSON/YAML layout: all fields required, no extras, keys/round
lengths as above. Tables below give complete nested schemas; provenance is deliberately a
separate registry to avoid wrapping values that the typed reducers consume.

```text
root = {version,catalog,services,drivers,people,initial,accounting,preferences,
        response_disposition,provenance,units}
catalog[source] = {purchasable_placements:list[placement],
 capacity_by_capability:map[cap,float|null], capacity_multiplier_by_config:map[config,float],
 opex_multiplier_by_config:map[config,float]}
services[source] = {serves:list[cap],availability:float,service_life_rounds:int,
 capacity_by_capability:map[cap,float|null],supply_by_placement:map[placement,
 {compute:float,storage_gb:float}],max_units:int}
drivers[driver] = list[float] # exactly N entries
people = {training_retention,resistance_retention,arrival_shock,strategy_shock,
 resistance_ceiling,adoption_adjustment,sponsor_present,sponsor_absent,staff_floor,
 starting_wage_per_fte,placement_staff_multiplier:map[placement,float],
 hiring_options:map[key,{fte:float,wage_per_round:int,lead_time_rounds:int}],
 communication_options:map[key,{cost:int,resistance_reduction:float}],
 units:map[key,{label:str,initial_resistance:float}]}
initial = {assets:list[{id,source_kind:catalog|service,source_key,placement,
 config:key|null,units:int,installed_round:int}],
 connections:list[{id,src,dst,kind,entity:key|null,tier:key|null}],
 training_fraction:float,adoption:float,process_with_option:partial,
 process_without_option:unchanged,primary:map[cap,asset|null],
 governance:map[cap,{owner:stakeholder|null,sponsor:stakeholder|null}]}
accounting = {opening_capital:int,opening_operating:int,operating_allowances:list[int],
 connection_terms:map[network|failover|basic|advanced|vendor_managed,
 {capex_source:none|integration_tier,opex:int,staff_load:float}],
 cancellation:sunk,platform_capability:key,decision_attribution_version:1,
 action_attribution_version:1,tco_estimators:map[category,estimator_enum],
 tco_capex_fraction:float,process_partial_fraction:float}
preferences = {rules:list[{stakeholder,cares_about:list[cap],
 views:list[{metric,ideal:number|string,weight:float,source_note:str}]}],
 dispositions:list[{source_path:str,disposition:live_v1|context_m4|no_preference,
 runtime_views:list[json_pointer],reason:str}]}
response_disposition[event] = {fund_effect:prevent_current_round,explanation:str}
provenance[pointer] = {source:AUTHORED|HARVESTED|PINNED,note:str}
units[pointer] = string # numeric dimension; nonempty
```

Pointers are slash-separated exact object paths; a pointer covering a subtree applies to
all its numeric descendant leaves unless a longer exact ancestor pointer overrides it.
No wildcard/index inference. Each numeric leaf excluding version constants must have one
most-specific provenance entry and one unit entry. Array entries inherit the array path;
config numbers inherit their config-map path; capability capacity leaves require individual
unit entries because units differ. Null capacity still has its declared capability unit.
Unknown/nonexistent registry paths reject. For example `/drivers/transactions` unit
`transactions/round`, `/catalog/erp_suite/capacity_by_capability/financial_reporting` unit
`reports/round`, `/people/starting_wage_per_fte` unit `dollars/FTE/round`. Fraction groups
use unit `fraction`, staff load `FTE`, storage `GB`, supply compute `compute_units`, prices
`dollars`, durations `rounds`. No labels appear as scorer IDs. People unit labels are the
literal catalog org_unit key with underscores replaced by spaces; not invented headcounts.

Exact remaining scalar values: staff_floor=.25; starting_wage_per_fte31000;
process_partial_fraction=.5; tco_capex_fraction=.1; opening balances0; allowances
[100000,100000,100000,100000,100000,100000]. Hiring/options and all other people constants
are exactly §6. `platform_capability=firm_infrastructure`. TCO estimator enum choices are
`full_training|basic_integration|full_process|compute_unit|backup_unit|one_round_opex|
capex_fraction|max_policy`; §7 maps every category to exactly one. Initial primary and
governance maps cover all7 capabilities, with nulls explicitly written. All11 service
serves arrays list all7 capabilities in source capability order. Initial connection IDs
are `initial_network_<target_source>`, plus `initial_pos_product` and
`initial_order_accounting`; no loop/self edge to client_network. Price references use
existing source objects, not strings interpreted as arbitrary code or eval paths.

NEW proposed Riverside numerical authoring is deliberately separate from old snapshot pins:

- Initial catalog: pos_system_2011, order_mgmt_v42, accounting_package, store_spreadsheets,
  order_db_cluster, store_back_office_pc, each on_prem at its `core` config, unit count one,
  installed_round 0. Initial services: client_network, compute_pool, storage_pool,
  backup_recovery on_prem, unit count one, installed_round 0. There is no initial Centraline,
  email, firewall, identity, analytics or SaaS order. No preexisting signals/debt/actions/costs.
- Catalog asset IDs are `initial_<catalog_key>`; service IDs `initial_<service_key>`.
  Initial network connections join client_network to every initial catalog asset and other
  initial service. Initial integration connects pos_system_2011→order_mgmt_v42 for product and
  order_mgmt_v42→accounting_package for order, `basic`. These inherited connections incur their
  recurring charge but no historical capex is invented.
- Primary deployments: order_mgmt for order_fulfilment; POS for store_operations;
  accounting for financial_reporting; all others absent. Initial catalog rollout training
  is `floor(0.6*catalog.people_affected.count)`, adoption .6, process partial where a process
  option exists and unchanged otherwise; ever_trained reflects the computed count. All
  owner/sponsor slots null, policy selections original defaults, all policy activity false.
- Unit keys are the distinct catalog people_affected.org_unit keys. Each starts resistance
  .2; no headcount total is invented or summed across the aggregate `firm` unit. Initial
  IT FTE is `platform.starting_staff_fte`, not the historical R3 people block.
- Catalog capacity rows are the exact literal table below, based on NEW25% initial
  headroom estimates plus the two grounded historical ceilings; order_mgmt uses
  `{order_fulfilment:8000,store_operations:6000}`, POS store_operations 6000, back-office PC
  all explicit null, spreadsheets all explicit null. Config capacity multipliers are NEW
  authored values initially equal to each config's existing compute multiplier; config opex
  multiplier is 1.0 for every tier. This is an explicit additional use, not an inference that
  compute_multiplier already meant throughput. `None` means no ceiling, not infinity.
- All platform services serve every capability, capacity map all null, availability .99,
  life 6; these are NEW values. Compute-pool unit supplies compute 12/24/24 for on_prem/
  cloud/saas and storage 0. Storage-pool unit supplies storage 5000/10000/10000 GB and compute
  0. Other services supply both zero. Maximum units is 8 for compute/storage and 1 otherwise.
- Catalog purchasable placements equal original modes except incumbent POS/accounting
  on_prem, whose zero capex means already-owned: initial-only, never a free replacement.
  One live/pending asset per source key; explicit replacements preserve identity. Platform
  units scale by replacing the service configuration, never by duplicating a free service.
- Driver literals: orders follows order_fulfilment demand; stores/sites equal company.sites;
  tickets follows service demand. NEW estimates: transactions `[80000,90000,100000,110000,120000,130000]`,
  sku_count `[12000]*6`, reporting_periods `[1]*6`, customer_records
  `[10000,12500,15000,18000,22000,26000]`, records `[100000,120000,140000,160000,180000,200000]`,
  visits `[10000,11000,13000,16000,19000,23000]`. These are explicit workload assumptions,
  never conversions from the incompatible store_day/campaigns/reports demand units.

Exact NEW catalog ceilings (each number's unit is the named capability's existing
`demand_unit`; initial25% headroom is a calibration rationale, not a runtime formula):

| Catalog key | capacity_by_capability |
|---|---|
| pos_system_2011 | store_operations6000 |
| order_mgmt_v42 | order_fulfilment8000; store_operations6000 |
| centraline_im7 | order_fulfilment7500 |
| accounting_package | financial_reporting100 |
| store_spreadsheets | store_operations:null; financial_reporting:null |
| next_gen_firewall | firm_infrastructure10 |
| customer_database | customer_insight1250; service375 |
| analytics_workspace | customer_insight1250; financial_reporting100 |
| ecommerce_site | marketing_sales1125 |
| service_desk | service375 |
| order_db_cluster | order_fulfilment7500; store_operations5250 |
| store_back_office_pc | store_operations:null |
| nosql_database | order_fulfilment7500; customer_insight1250 |
| erp_suite | financial_reporting100; order_fulfilment7500 |

Every source config maps capacity multiplier to the exact source compute_multiplier at
content authoring time, persisted as literals; opex multiplier1. Driver arrays not already
listed above are orders `[6000,6600,12000,15000,18000,22000]`, stores/sites
`[8,8,8,8,8,8]`, tickets `[300,360,430,520,620,740]`. Workload inputs and capability demands
remain separate dimensions. Prices/configs/lead times are referenced from original
content, never copied to a second price list. Runtime validation rejects NaN/Inf/bool,
missing or extra profile/config/driver keys, unsupported placement, zero authored capacity,
unknown unit or unresolved initial integration. Duplicate YAML keys are rejected before
Pydantic validation; the existing permissive generic preferences parser is not reused.

The content validator rejects an initial paid acquisition masquerading as a raw result:
no capex, opex, load, people count, role, entity, signal, forecast actual or score overrides
in `initial`. Initial inherited conditions are the sole exception for trained fraction,
process and adoption; later sheets cannot carry those fields. The checkpoint records their
content digest. Supplying a bundle with changed semantic content after initialization refuses; formatting-only
file changes do not change the bound semantic digest and no file watcher is implied.

## 4. NEW checkpoint and additive engine seam (D3, D9)

NEW tables use the existing `Base.metadata`, non-null integer instance_id/team_id in
all primary keys, and one new migration after `20260822_0002`:

| Table | Columns/keys |
|---|---|
| `simulation_run_v1` | PK `(instance_id,team_id)`; `version=1`, `pack_key`, `pack_version`, `pack_digest`, `current_round`, `advanced_round` (0 initially), `status:draft|locked|completed`; no duplicate cash/estate state |
| `simulation_sheet_v1` | PK `(instance_id,team_id,round)`; FK scope→run; `revision>=0`, `locked_revision:int|null`, `commands:JSON`, `sheet_digest:str|null` |
| `simulation_checkpoint_v1` | PK `(instance_id,team_id,round)`; FK scope→run; `version=1`, `pack_digest`, `sheet_revision:int|null`, `state:JSON`, `state_digest`; round0 initial checkpoint; round1..N immutable transition outputs |

Database column types: scope/round/revision/version integers; keys/versions/digests/status
Text with application validation (digest exactly64 lowercase hex); commands/state JSON;
lock/sheet_revision nullable only as specified. CHECK version=1, nonnegative revisions,
round bounds≥0 for checkpoints and≥1 for sheets, current/advanced pointers nonnegative;
composite FK sheet/checkpoint scopes reference run with no cascade deletion. No mutable
updated_at, random surrogate ID or wall-clock field enters canonical runtime state.

Existing `RoundResult` stores the scored report at `(instance_id,team_id,round)`. No new
production rows are written to historical estate/decision/signal/debt tables. Checkpoint
state is typed/validated on read and write; JSON is not an arbitrary extension point.
Every child lookup also filters instance/team; FK does not substitute for query scope.

NEW `CheckpointStateV1` has exactly: `strategy`, `strategy_declared_round`, `assets`,
`connections`, `projects`, `hiring_orders`, `staff_hires`, `support`, `rollouts`,
`unit_resistance`, `governance`, `primary`, `policies`, `capital_balance`,
`operating_reserve`, `cost_ledger`, `technical_debt`, `signal_ledger`, `action_history`,
`available_funds_by_round`, `event_history`, `response_history`, `tco_forecasts`,
`repair_assessment_history`, `unpriced_signal_exposures`.
All maps serialize by key; arrays use the collection-specific orders frozen below; canonical JSON uses
sorted object keys, compact separators, UTF-8, and `allow_nan=False`. Prices and units
are strict integer/finite numeric types; outputs round fractional transition state to
six decimals. Checkpoint digests include state only; payload digests include scope.
Game comparisons across fresh scopes normalize only instance_id/team_id, never numeric
results, actor choices, timestamps, ordering, or event evidence.

Asset records hold identity/source_kind/source_key/placement/config/units and
installed_round/retired_round, never duplicated prices/roles/people.
An order/project holds the same asset identity, immutable ordered_round/config/price,
remaining_lead, status `pending|paused|arrived|cancelled|abandoned`, and replacement target
if any. Rollout records hold trained_count, adoption, process, ever_trained and lifecycle;
people/serves/unit derive from catalog. Immutable cost entries are keyed by
`(round,kind,source)` with signed capital/operating deltas and optional asset/capability/
cost_category. Technical debt records are keyed by `(signal,episode_id)` with opened_round,
amount, settled_round|null. Signal rows use the complete existing `LedgerSignal` shape.
Only prior checkpoint plus current commands/content produce these fields.

Frozen nested checkpoint records (all keys required; null only where written; no extra
fields). `Key` means validated64-character machine key, `Money` integer dollars, `Round`
integer0..N. All maps are `dict[Key,record]`; key must equal record.id where present.

```text
Asset = {id,source_kind:catalog|service,source_key,placement,config:Key|null,units:int,
         installed_round:Round,retired_round:Round|null}
Project = {id,asset_id,source_kind,source_key,placement,config:Key|null,units:int,
           ordered_round:Round,paid_capex:Money,remaining_lead:int,status:
           pending|paused|arrived|cancelled|abandoned,replacement_target:Key|null,
           tco_categories:list[Key]}
HiringOrder = {id,option,ordered_round:Round,remaining_lead:int,status:
               pending|arrived|cancelled,arrival_round:Round|null}
StaffHire = {order_id,option,arrival_round:Round} # FTE/wage derives from option
Connection = {id,src,dst,kind:network|integration|failover,entity:Key|null,tier:Key|null,
              created_round:Round,retired_round:Round|null}
Support = {tier:Key|null,covered_assets:list[Key]}
Rollout = {trained_count:int,adoption:float,process:unchanged|partial|redesigned,
           ever_trained:bool,lifecycle:active|retired|abandoned}
Governance = {owner:Key|null,sponsor:Key|null}
Policy = {selected:Key,actively_decided:bool}
Debt = {signal,episode_id:int,capability,opened_round:Round,amount:Money,
        settled_round:Round|null}
ActionEnvelope = {id:sha256,source_round:Round,source_command:command_key,
                  effect_round:Round,record:existing ActionRecord complete fields}
Signal = existing LedgerSignal's complete fields
EventHistory = {round:Round,fired:list[event evidence],suppressed:list[suppression],
                prevented:list[prevention evidence]}
Response = {round:Round,key,event,option,rationale_tag,cost:Money,effect:
            prevent_current_round|none}
Tco = {asset_id,ordered_round:Round,selected_categories:list[Key],forecast:Money,
       forecast_horizon_round:Round,estimates:dict[Key,Money]}
```

`assets`, `connections`, `projects`, `hiring_orders`, `rollouts`, `governance`, `policies`
are maps of the corresponding records; `staff_hires`, `technical_debt`, `cost_ledger`,
`signal_ledger`, `action_history` (ActionEnvelope), `event_history`, `response_history`, `tco_forecasts`,
`repair_assessment_history`, `unpriced_signal_exposures` are arrays. `unit_resistance` is map[unit,float]; `primary` map[capability,asset|null];
`available_funds_by_round` is array[Money] of exactly checkpoint round length. Strategy
is Key, strategy_declared_round Round; both balances Money. No duplicate price-reference
field exists in Asset: its immutable source identity and pack digest reference price.
Initial project records are arrived/ordered0/paid0/remaining0 with empty TCO categories;
no initial hiring orders. Rollouts exist only for catalog assets/projects. Identity, range,
uniqueness, record joins, inventory totals and state digest validation runs before each
read/commit; malformed persisted state yields invalid_output without partial repair.

Initialization checks all existing historical `ALL_TABLES` plus all NEW tables for the
scope, before insertion. Any occupied scope refuses `scope_exists` without deleting or
adopting old data. Concurrent initializers: one inserts; the unique-key loser rolls back
and returns scope_exists. Production initialization is not a reset. `read` returns
`{version,pack_identity,current_round,status,checkpoint_round,checkpoint_digest,state,sheet}`;
`SheetViewV1` is `{version,round,revision,locked_revision,commands,preview}`. `state` is a defensive detached validated CheckpointStateV1 copy, never an ORM or mutable
service/content object. Actor visibility filtering belongs to M2/M3. Preview
contains derived costs/available capital, future operating-reserve schedule, due arrivals,
validation warnings and eligible challenges; it never persists or substitutes for results.

Initialization creates round1 draft revision0, locked_revision=null, sheet_digest=null,
commands=[]; run.current_round=1/advanced_round=0/status=draft. A sheet digest exists only
while locked and is SHA256 of canonical JSON `{version:1,round,revision,commands}`; no scope,
preview or clock is part of it. Reopen increments revision and sets both locked_revision
and sheet_digest null. After final advance, current_round=N, advanced_round=N,status=completed;
read/initialize RunView has sheet=null only when completed. Earlier states have the current
SheetView. Completed history retains sheetN's locked data for retries, but read does not
pretend a new editable sheet exists. checkpoint_round always equals advanced_round.

Within `advance`, after row lock/revision checks: load checkpoint r-1, simulate fully in
memory, validate derived state/result, insert checkpoint and result, update pointer/create
empty sheet r+1 (unless completed), commit. A failure injected after either insert or
before commit rolls everything back. The connection is closed before return. Read views
use their own connection/transaction; no live ORM objects escape. SQLite file-backed
concurrency tests use distinct connections; in-memory single-connection tests do not prove
serialization. PostgreSQL `SELECT FOR UPDATE` guards all run mutations.

**Additive engine seam, independently reviewed P0.** `engine-inputs/spec.md` is the
exclusive freeze for optional immutable `ArchNode.capacity_by_capability` and optional
`base_rto_hours`, context-threading, RTO precedence and stable BFS. No catalog_key field.
Runtime projects positive-or-null authored capacities and may derive zero when resources
are unavailable; missing map keys mean no ceiling for incidental transit. Catalog RTO is
projected directly; platform RTO is null (legacy8-hour fallback). No scalar throughput is
populated alongside a map. One node remains one physical identity. All P0 legacy payload
and cross-process gates apply unchanged. Independently reviewed P0b in
production-inputs/spec.md adds optional immutable EntityAccess and RepairAssessment inputs;
production always supplies tuples (including empty where legal), never the None legacy
fallback. P0b preserves source roles/ownership and real repair opportunity semantics.

## 5. NEW estate/resource transition (D4, D5)

Frozen order for round r: grant capital/operating allowance → retire/cancel/pause/kill →
advance existing unpaused lead-time orders → apply new acquisitions/replacements and
materialize zero-delay acquisitions → connections → organisation/governance/policy →
resource/opex projection → signals → funded-response validation/prevention → events →
authoritative score → accounting/debt/TCO → immutable publication.

An order placed r with lead L arrives at r+L. A zero-delay order arrives during r after
purchase; L1 ordered R1 is absent R1 and arrives R2. Prior due order may be cancelled or
paused before arrival this round. Pausing freezes remaining lead before that round's
progress; continuing an already-pending order is an explicit no-op, continuing a paused
order allows progress this round. Kill/cancel are terminal and sunk; neither refunds capex.
With remaining_lead L>0 at start of round r, resuming now arrives at r+L-1;
resuming next round arrives at r+L. Carried paused expiry therefore occurs at
r=N-L+1 absent continue/cancel/kill. Example N6: L1 paused order can resume inR6, otherwise
expires at startR6; L2 can resume inR5 and arriveR6, otherwise expires at startR5. A new
pause in either last feasible round refuses. Lead0 is immediately arrived and cannot pause.
Expiry/cancel/pause resolve before due-arrival and rollout targeting, so no expired order
can receive training or arrive for free. No training/process/payment is accepted for a still-pending asset. A terminal order cannot
continue. Pending projects project no engine rollout; abandoned projects project an
initiated/abandoned record, so follow-through observes abandonment without early rollout
signals. Live assets cannot pause: retire is the explicit operating decision. Retired live
projects remain historical initiated records, keep ever_trained, have empty serves and
no primary, and do not become abandoned merely because retirement was deliberate.

Purchase capex = decimal ROUND_HALF_UP(mode.capex × config.capex_multiplier × units),
configuration omitted only for platform services (multiplier1). Application units fixed1.
All lifecycle/support/training/process/communication choices are priced by content, not
caller. Replacement pays the full new acquisition price, leaves the old asset running and
paying opex until arrival, then swaps its configuration atomically using the same asset ID;
no trade-in/refund. Same placement/config/units replacement is a no-op with zero charge,
no order, no timestamp reset and no ActionRecord. A real replacement resets installed_round
on arrival, preserves existing rollout counts/process/adoption and connections, and applies
a new arrival/change shock. Replacing while another order targets the asset is invalid.
Retirement removes live nodes, incident edges, support coverage and primary assignment
before opex; orders targeting that asset make retirement a conflict until cancelled.
A combined cancel-replacement-order plus retire-asset is permitted as the one exception
to terminal-touch conflict, because it resolves the pending liability before retirement.

One connection is undirected topology plus optional directed entity flow metadata. Network
and failover edges require entity/tier null; an integration requires both entity and tier.
Source must currently own the entity; receiver must declare a matching `must_be_fed_by`
entity and, where present, its from_capability must be in source's original serves. Only
catalog receivers are permitted for entity integrations in v1. P2 produces exact P0b
EntityAccess(connection,source,receiver,capability,entity) records for receiver's original
served capabilities. Node.serves/roles/owns_entities remain unchanged. Mandatory receiver
paths, exact entity/level scope, owner de-duplication, failure exclusions and per-entity
access_via evidence follow production-inputs/spec.md exclusively; no serves-union fallback.
Disconnect reverses only that access derivation. Source/destination must be live after
arrival; self-edges and duplicate topology/entity identities reject. Failover connection
requires at least one endpoint to fill the authored `failover` role. Every edge has one
source ID and a derived stable connection key from its creating command.

NEW connection parameters: network/failover capex0/opex0/staff_load0; they express physical
wiring over already-purchased infrastructure. An integration costs its source
platform.integration_tiers[tier].cost once, plus NEW operating charge/load per round:
basic1000/.2FTE, advanced2000/.1FTE, vendor_managed3000/.05FTE. All three create the same
validated data access; their ongoing load/price trade differs. These operating estimates
are explicit calibrated content, not meanings already present in IntegrationTier.

For each active application, driver = content.drivers[item.sizing.driver][r-1].
Resource draw = `(base + per_unit × driver/per)` per compute/storage; multiply compute
only by config.compute_multiplier. Multiply by units1; bypasses_platform => both draws0.
Sum draws per placement. Active pool services supply their content compute/storage per
unit × units. For each placement, factor = min(1, compute_supply/compute_draw when draw>0
else1, storage_supply/storage_draw when draw>0 else1). Missing supply with positive draw
means factor0; no division by zero. Catalog capacity per capability = authored capacity ×
authored config capacity multiplier × that placement factor, rounded6; bypassed apps use
factor1. Pool supply is never `capacity_pct`, which is historical utilization context.
Every asset contributes its source staff_load × placement staff factor; integrations and
selected policy staff load are added once. No per-capability duplicated costs or FTE.

## 6. NEW organisation, governance and preference producers (D6, D7)

For existing active catalog rollouts, decay training first:
`T0=floor(previous_trained_count*.90)`; new arrivals start0. A training command sets
`T=max(T0,ceil(people_affected*option.coverage))`, capped at catalog population. It charges
the option cost even when it restores a previously purchased coverage; none/coverage0
costs0, has no effect, no ActionRecord. No cumulative overlap assumption: repeated basic
restores basic's target, it does not eventually become full. `ever_trained` becomes true
only after a positive trained count, and never resets. Catalog is the sole people/unit
source; new IT hires do not magically increase end-user populations or count as trained.

Process has existing values unchanged/partial/redesigned. Price for a change to partial is
ROUND_HALF_UP(process_option.cost*.5), redesigned full cost, unchanged0. Repeating the
same process state costs0; a catalog item with null process_option accepts unchanged only.
No partial process formula is invented in the scorer: reuse its `PROCESS_FIT` mapping.

NEW communicate options: feedback_loops2500/reduction.05, knowledge_portal3500/.08,
change_champions4000/.10, none0/0. Monetary values are NEW authored simulation estimates
based on the locally harvested option concepts; exact provenance distinguishes them from
transition coefficients, which are entirely NEW. One choice per unit per round; absent
means none, no automatic renewal. It changes resistance this round, not trained_count or
the frozen `rollout_without_support` predicate. Richer communication predicates stay M4.

Staff load and capacity are computed before resistance/adoption. Hire option `it_generalist`
is +1FTE, recurring31000, lead1, capex0; no firing or skill ladder in v1. Starting FTE costs
31000 per FTE per round as a NEW wage assumption, rounded HALF_UP. Pending hires may be
cancelled through their typed hiring-order identity before arrival, with no refund. Support
is immediate, recurring source-tier cost, not capital; null removes it and requires an
empty covered_assets list. Eligible support assets are active catalog/service assets;
capacity credit `min(tier.fte_equivalent,sum(load of covered_assets))` limits vendor scope.
An absent command retains tier and surviving coverage; no automatic expansion to new assets.
IT capacity = startingFTE + arrived hires + that capped support credit. Reuse existing
`staffing_factor` on the derived StaffPool; zero load gives1, no staff with load gives0.

For each unit, count newly arrived or replaced **catalog** rollouts affecting it this round
(service installations do not invent end-user changes). Resistance:
`R=round(clamp(previousR*.90 + .10*arrival_count/max(staffing_factor,.25)
 + (.10 if strategy changed else0) - communication_reduction,0,.90),6)`.
For each active rollout use the NEW target
`target=(trained_count/people)*PROCESS_FIT[process]*(1 if sponsor assigned else.75)
 *staffing_factor*(1-R)` and
`adoption=round(clamp(previous_adoption+.35*(target-previous_adoption),0,1),6)`.
New rollouts previous_adoption0; replacement preserves prior adoption before adjustment.
Sponsor is the governing sponsor of the rollout's primary capability, or absent if it is
not primary. An assignment affects the same round. A rollout can be primary for at most
one capability; at most one primary per capability; selecting a non-serving/retired asset
rejects. Missing primary retains a real zero Org term; the service never invents one.

Assignments use real pack stakeholders. Owners must be internal; sponsors must be internal
c_suite or finance. Null explicitly removes; omitted category retains assignments. The same
stakeholder group may own and sponsor, and may cover several capabilities. Governance projects only
booleans from these identified stakeholder-group records, never accepts booleans as identity. Strategy changes
charge the selected Strategy.reopen_cost once and shock every unit. First declaration is
initialization; identical selection is free/no shock; one change per round.

Policy selected value persists. `actively_decided=True` exactly when that round has a
set_policy command, including repeated/default selection; absence always false. A changed
selection charges PolicyOption.cost once, identical selection0. Source ordinal semantics
and asymmetric policy alignment remain unchanged. NEW active policy intensity is its
selected ordinal index/(n-1), or0 for one-option policies. Only `effects.staff_load` is
consumed in M1, as FTE × intensity. Other effects remain recorded, not silently applied to
scores or capacity; policy obligations already consume the selected values. Non-empty
policy overrides retain the existing explicit refusal; their richer typed targeting and
precedence remain M4. The runtime loader validates this refusal before initialization.

NEW non-policy preference shape is `preferences.rules:[{stakeholder,cares_about,
views:[{metric,ideal,weight,source_note}]}]`; at most one row per eligible actual stakeholder, no duplicates; unsupported-only
stakeholders have no row and never become neutral votes.
Metrics are closed to `training_coverage`, `asset_reliability`, `staff_load_ratio`,
`platform_placement`, `support_tier`, `integration_tier`, `cost_posture`,
`process_fit`, `communication`. Caring capabilities are explicit pack keys. `ideal` is a
finite0..1 number for numeric metrics or an exact declared choice key for categorical
metrics. Weights finite nonnegative, all0 produces alignment1 with zero-interest evidence.
No policy switches are counted here: their separate scorer dimension is frozen.

Metric producers (NEW): numeric metrics use arithmetic means over active catalog rollouts/
assets whose original serves intersects cares_about; no assets => value0. Training reads
real trained/population, reliability original asset availability, process existing mapping,
communication this-round reduction/.10 capped1, staff_load_ratio=min(1,load/max(capacity,.001)).
Cost posture is selected mode capex divided by the maximum available mode capex for that
source item, denominator0=>0; lower is cheaper. Platform placement categorical match uses
active platform service placements; support uses held tier (null is none); integration uses
active connection tiers (none when empty). Numeric alignment = clamp(1-abs(actual-ideal),0,1);
categorical = fraction exactly matching ideal, `no_preference` view excluded. Weighted mean
across views yields the one StakeholderDecisionAlignment scalar; cares_about is content.
No feedback from realised value: existing scorer alone computes satisfaction afterward.

The authored v1 rules are a distinct explicit interpretation of existing preference
interests; ambiguous historical `ideal_value:85/95` and generic risk vocabulary are not
silently parsed as scores. Runtime content must enumerate a disposition for every original
non-policy preference leaf: supported v1 rule with source pointer, or retained context/M4
with reason. Minimum live rows cover all actual stakeholders with supported interests;
people without a supported view are omitted/excluded, never fabricated neutral votes.
Exact Riverside rows are frozen below. Tuple notation is `(metric,ideal,weight)`; each
weight is a NEW interpretation using existing source weights (services multiply its two
levels). Duplicate interests across domains deliberately remain separate views because
these sources authored separate interests. `ALL` expands to the seven capability keys;
no groups or caring sets are inferred at runtime.

| Stakeholder key | cares_about | Exact v1 views |
|---|---|---|
| senior_management | ALL | (cost_posture,0,.8), (asset_reliability,.98,.8), (platform_placement,cloud,.8), (support_tier,basic,.48), (integration_tier,advanced,.32) |
| finance | financial_reporting | (cost_posture,0,.9), (platform_placement,cloud,.9), (support_tier,basic,.81), (integration_tier,basic,.72) |
| employees | ALL | (training_coverage,1,.7), (training_coverage,1,.9), (support_tier,premium,.49) |
| operations | order_fulfilment,store_operations | (asset_reliability,.99,.8), (platform_placement,on_prem,.8), (training_coverage,1,.9), (support_tier,premium,.72), (integration_tier,advanced,.4) |
| it_department | ALL | (staff_load_ratio,0,.7), (staff_load_ratio,0,.8), (platform_placement,on_prem,.8), (support_tier,premium,.8), (integration_tier,vendor_managed,.64) |
| hr | ALL | (training_coverage,1,.7), (training_coverage,1,.8) |
| marketing | customer_insight,marketing_sales | (platform_placement,cloud,.6) |
| investor | ALL | (cost_posture,0,.8), (cost_posture,0,.7) |
| customer | customer_insight,service | (asset_reliability,1,.8), (asset_reliability,1,.8) |
| vendor | ALL | (integration_tier,vendor_managed,.7), (integration_tier,vendor_managed,.7), (integration_tier,vendor_managed,.7), (support_tier,premium,.56) |

NEW explicit dispositions exhaust original preference leaves: catalog cost/training/
reliability/staff-load/availability/integration become the table's numeric0/1/exact tiers;
platform placement uses source ideal (no_preference excluded), investor cost/customer
availability/vendor integration use the table. Operations platform availability maps to
its existing catalog reliability view only (no duplicate view); IT platform load has its
separate .8 view. Training high maps1; finance medium-training-cost and IT medium-change-
volume have no unit-consistent metric and remain context/M4. Marketing customer-data,
security/compliance/privacy/incident-visibility/identity/recovery ideals remain context/M4
until typed metrics exist. Those unsupported-only stakeholders (security_auditor,
regulator,general_public,media) are excluded from this non-policy scalar, while their
existing policy preferences remain live. The14 original platform cloud_weight/on_prem_weight leaves (seven internal archetypes
×two weights) remain source/context because v1 uses exact ideal-placement match, not the
alternative raw weighted placement metric. All five original item overrides are context/M4:
raw ideal_value has no declared unit or precedence. No override is silently applied or
reported implemented. `preferences.dispositions` lists those source paths/reasons as
content, validated to cover every original scalar leaf exactly once. The universe is
all scalar leaves under defaults_by_archetype and overrides in catalog/platform/training/
services preference files (131 at this base), excluding provenance and policy preferences.
Each source_path has one disposition; runtime_views may list several view pointers when
one source weight contributes to multiple views, and is empty for context/no_preference.
Operations platform ideal_availability aliases its catalog reliability view by explicit
exception to retaining duplicate interests; both source paths point to that one view. Policy overrides still
refuse entirely, as frozen above. Process/communication metrics are reserved enum members
with no Riverside preference views; their Org producers are live.

## 7. NEW accounting, actions, signals and consequences (D8)

Money uses integer dollars and Decimal ROUND_HALF_UP for multiplication, never binary
float summation. Opening capital and operating reserve are0. At round r, capital receives
`pack.metadata.budget.capex_per_round[r-1]`; operating receives100000. Capital pays all
one-off application/service/configuration, integration, training, process, communication,
changed-policy, changed-strategy and funded-response charges. Operating pays live source
mode opex × config opex multiplier × units, integration recurring, wages and support, plus
fired-event revenue_loss. This last debit is a NEW IT operating-reserve consequence proxy,
not company revenue accounting or a Financial score. Initial inherited costs are14200
source recurring +62000 wages +2000 inherited integrations =78200; derived staff load3.7.
No synthetic47000 target, depreciation, refund, debt interest or cross-reserve transfer.

Affordability preview first quotes the entire candidate, including response charges. Capital
must cover all new one-off charges. For operating, simulate the baseline's unavoidable
liabilities and the candidate's liabilities with no future discretionary choices through
H=final_game_round. No appropriation, grant or solvency assertion exists beyond H.
New orders/hires/replacements arriving after H refuse arrival_after_game_end. Pausing an
order is accepted only if resuming next round could still arrive by H; otherwise cancel/kill
is required. At the start of its last feasible resume round, a carried paused order with no
continue/cancel/kill command automatically becomes abandoned with expiry evidence. Explicit
continue takes precedence over that expiry, then normal progress may arrive in-game. A new
pause that would cross this boundary refuses arrival_after_game_end. Pending replacements keep old recurring until arrival; paused orders
forecast resumed next round (no perpetual pause affordability loophole).
An increased recurring commitment is accepted only if the candidate projected reserve is
nonnegative at every forecast close. Compare the candidate versus baseline recurring liability amount separately in every
remaining round. If any candidate round is higher, the full candidate closing-reserve
schedule must stay nonnegative. A candidate with no such per-round increase may resolve
even with a negative operating reserve, provided capital covers all one-off charges: empty, retirement, cancellation,
free same-value policy acknowledgement and capital-funded training/process/response
choices cannot strand a run. Retirement offsets only the rounds where its reduction
actually takes effect, never an aggregate future saving against an earlier liability. A candidate may combine retirement with new affordable commitment; test aggregate
candidate schedules. Unavoidable events may make final reserve negative after validation.
Affordability never alters a requested choice, silently downgrades it or omits a line.

NEW `CostEntryV1` keys are `(round,kind,source)`, amounts integer signed deltas; kind is
`capital_grant|operating_allowance|acquisition|integration|training|process|communication|
policy|strategy|response|asset_opex|integration_opex|wages|support|event_loss`. Each includes
`asset:null|id`, `capability:null|key`, `category:null|cost_category`, `capital_delta`,
`operating_delta`. Both deltas are0 only for an explicitly recorded free decision, never
for a fabricated expenditure. Live opex is recomputed each round, not accumulated into its
run rate. Sum entries from round0 gives both closing balances exactly; event cost is charged
once per fired event and once per validated response, never both for a prevented event.

NEW management `DecisionState` comes only from current real capital charge entries, plus
zero-cost explicit policy acknowledgements; no arbitrary capex or tags. For an application,
capability is buy.primary_for if supplied else the first source serves key; RGT is the
source item's rgt_tag. Replacement/training/process inherit that source capability/RGT;
maintenance=True for replacement and lifecycle-related charges, false for new application.
Platform charges use runtime.accounting.platform_capability (Riverside firm_infrastructure),
run, maintenance=True. Integration uses receiver's
first original serves, grow, maintenance=False. Communication uses first alphabetic
capability served by active rollouts in that unit (null if none), run, maintenance=True.
Policy uses null capability, run, maintenance=True. Strategy uses null, transform, false.
Response uses event primary capability, run, maintenance=True. Recurring wages/support/opex
never masquerade as capital in the frozen management factor. Every attribution includes
traceable source command/cost key in result evidence. Empty decisions retain scorer's exact
null behavior; this proposal does not normalize an empty portfolio into a desired score.

NEW action producer is distinct from spend. Emit a real ActionRecord only after an effect
becomes live; retain `locked_round` of its original commitment, never arrival-as-commitment.
All target_key values use original catalog key for catalog actions, not physical ID. Emit
one record per original served capability where needed; this does not duplicate cash charges.

| Effect | Action type / cost | Explicit no-action cases |
|---|---|---|
| new arrived catalog/service | add_node / paid original capex | pending, paused, cancelled or abandoned acquisition |
| arrived replacement changes placement to cloud | move_to_cloud / paid capex | same placement/config/units |
| other arrived replacement | scale_node if units/config capacity multiplier increases, else upgrade_component / capex | identical selection |
| training increases retained trained count | add_training / actual positive source price | none, coverage0, no increase; zero-price effectful training is unsupported runtime content because frozen ledger uses cost0 proxy |
| process improves PROCESS_FIT | redesign_process / actual price | same state or reverting |
| live integration/support changes to a different nonnull tier | add_service_tier / integration capex or support recurring quote | same held support, disconnect, null tier |
| retired live catalog | retire_component /0 | cancellation of never-live order |
| changed policy selection | add_policy / actual source price | retained/default acknowledgement changes discipline only |
| communications, hires, assignments, strategy, fund/defer/reject, project pause/continue | none | no invented clearing-action alias |

For services/support/policies with no catalog serves lookup, emit explicit capability from
actual affected scope; policy scope is all pack capabilities and service scope its authored
serves. No training/action is emitted merely because a response's rationale mentions training.
An effective action alone is insufficient for credit: existing ledger still requires the
watch metric to stop raising. Arrival after a signal fire cannot rewrite the old terminal
episode. A commitment predating a signal episode does not earn responsiveness for that episode
under the frozen original-commitment clock; no timestamp is moved to manufacture credit.

### 7.1 Verified repair producer and quote scope (MSR-003)

P4 NEW repairs.py produces the complete P0b RepairAssessment tuple for all watch rules.
It is a bounded verified CREDIT-ELIGIBLE repair catalogue, not an exhaustive search or an
advisor recommendation. `unassessed` means no candidate verified in this catalogue, never
no fix exists. Physical repairs that cannot earn credit under original cleared_by are
reported as repaired_but_uncredited and excluded from the actionability candidates. For
example a valid POS→customer_database sale integration can fix data_coverage_gap but its
add_service_tier action does not occur in cust_data_01.cleared_by; its signal naturally
lapses without responsiveness credit. Never relabel it upgrade_component or edit the watch.

The preparation boundary is `prepare_effects(pack,prior_checkpoint,merged_sheet,round)`:
it derives estate/organisation/resources/costs and proposed actions once from immutable
round r-1 state. It does NOT call repair assessment, advance_ledger, events or score_team,
and writes nothing. It performs structural/effect/cost validation but reports affordability
separately: its candidate state carries prior balances/funds/history until final settlement;
signed provisional capital_remaining and future operating rows live in PreparedEffectsV1.
Only hypothetical TeamState funds may be negative during an unaffordable witness check;
no such state is a valid committed checkpoint. Public quote/resolve enforce the complete
affordability rule before publication. Every candidate reruns this shared preparation from that SAME prior
checkpoint with current sheet plus candidate commands. It never applies a repair onto an
already-decayed/granted/debited current state, so grants/decay/shocks/charges occur once.
Candidates append choices; they cannot replace a same-target current command, remove a
held response command or bypass duplicate/conflict/affordability validation. A candidate
conflicting with any current choice is excluded, with a rejection reason in witness audit.

Each watch receives one assessment. A watch not currently raising has an empty assessment;
otherwise use its latest open episode window, or the prospective new episode beginning r.
Do not create a present opportunity solely for a watch that might first raise in the future.
Enumerate the following finite catalogue in op/source/target/option lexical order:
- All legal buy_application and replace_application source modes/configs and buy_service/
  replace_service source placements/units1..max_units, respecting one-live/pending and
  initial-only restrictions. Buy_application candidates use primary_for=null and
  tco_categories=[]; all other fields use the enumerated source choices. A zero-delay NEW acquisition may additionally bundle one free
  network connection from each existing live client_access node (one variant per client).
  Delayed acquisitions have no assumed future connection command: they arrive unconnected
  under empty future decisions and can verify only effects they actually produce, such as
  the global identity role. Replacements retain only actual existing connections.
- Each existing/due-live catalog target with each training option or each process choice;
  each source policy and selected option; each support tier with its existing surviving
  coverage or all currently live assets (two unique variants; null/no-op cannot verify).
- Each currently legal directed entity integration with each authored tier. No network-only
  or retirement candidate is advertised as a repair in this bounded v1 catalogue; no
  arbitrary multi-repair combinations, hire search, pending-order cancellation or future
  instructor grant. Pool unit/config replacements above cover their actual resource effects.

For each variant, canonical commands use reserved internal keys `repair_` plus first32hex
of its canonical op/target/options digest and free-edge suffix `_link`; collision with a
student key excludes the variant rather than silently overwriting it. Candidate_key is
SHA256 of the complete canonical candidate command array. Validate targets/content/round
first and calculate source price even if affordability fails. Starting from that current
preparation, advance only passive transitions with EMPTY future decision sheets until the
candidate's first effect round, respecting horizon and paused expiry. The projection never
adds future training, wiring, funds, policy change or repair commands. It does not assume
future event losses: opportunity affordability uses the same current pre-event capital and
remaining known recurring schedule as normal command validation; unexpected future losses
are explicitly outside this forecast. The first-effect round must be≤N.

Evaluate the original watched metric at that effect round on both the candidate trajectory
and the otherwise identical current-sheet-only trajectory (same empty future decisions).
Candidate verifies only if baseline still raises, candidate no longer raises, and the
candidate emits a real matching original-cleared_by action with original locked_round=r
within the current open episode's response window. Path-property metrics additionally
require a candidate serving path with strictly positive/no-ceiling capacity; making the
capability disappear or zero-capacity is not a repair. For a newly raised episode the
prospective window begins r. Fund/defer/reject are never candidates; option label or a
similar price is no proof of repair. No score is called to certify a repair.

A current sheet with response commands (fund, defer or reject) uses a disposable STATUS-ONLY
ledger for each hypothetical candidate: same real prior LedgerSignal tuple and candidate-prepared current
state/actions, with one P0b RepairAssessment(signal,r,candidates=()) for EVERY watch rule.
Call existing advance_ledger and original event preconditions/strategy-affinity/arms against
that disposable ledger to check every held response is still eligible. A candidate that
invalidates any held response is excluded as held_response_ineligible; it cannot remove
that response command.
These status-only rows are never published, used for debt/actionability, cached as an
assessment, or allowed to invoke repair search. All11 original preconditions depend on
state/status, not repair cost or was_actionable; no broad capability exclusion or generic
non-signal-precondition refusal is needed. After assessment, build the OFFICIAL ledger
from the original prior ledger and real prepared state with real assessments exactly once,
then the existing fire-stamping pass. This is a bounded pure ledger call inside hypothetical
validation, not recursive quote→assessment→quote. Prove that replacing quote/actionability
fields with unassessed values leaves all event eligibility results unchanged, while actually
repairing the watched condition can correctly invalidate its held response.

Current minimum = cheapest verified credit-eligible capital cost; affordable witness =
cheapest (cost,candidate_key) among those passing FULL candidate current capital and
per-round operating-liability rules. A cheaper SaaS repair may be unaffordable while a
higher-capex on-prem repair is affordable; preserve both distinctions. P0b consumes only
these verified candidates, freezes first-episode quote, and can mark a later open episode
was_actionable when a later real affordable witness exists without repricing its origin.

NEW immutable RepairAssessmentHistory row:
`{round,signal,status:verified|unassessed,reason:null|bounded_catalogue_no_verified_repair,
initial_state_digest,merged_sheet_digest,candidates:[RepairWitness],
repaired_but_uncredited:[RepairWitness],excluded:[{candidate_key,reason}]}`.
Excluded reason is one of the SimulationError codes or
held_response_ineligible|command_key_collision|baseline_not_raised|metric_not_repaired|
no_positive_path|no_in_game_effect. A physically repaired but nonqualifying action goes to
repaired_but_uncredited, never a fabricated credit-eligible candidate.
RepairWitness exact fields are `{candidate_key,commands,capital_cost,effective_round,
affordable,operating_forecast,baseline_metric:float|bool,candidate_metric:float|bool,
emitted_action_ids:list[sha256],credit_eligible:bool,assumptions:empty_future_decisions}`;
capital_cost is incremental one-off candidate-command spend, excluding the held sheet
spend, grants and recurring costs; full candidate affordability includes those held choices
and every recurring period. Emitted_action_ids are counterfactual envelope IDs recomputed
from witness commands, not assertions that those actions appear in actual action_history.
operating_forecast uses PreviewV1's exact rows and commands use CommandV1. Unaffordable
witnesses still retain correctly quoted schedule and amount; affordability is not inferred
from capital_cost alone. History is append-only, keyed(round,signal), persisted once at
actual advance and never during preview/candidate search. Compact P0b inputs are derived
from its candidates array, never from repaired_but_uncredited. The state digest references
checkpoint r-1; merged_sheet_digest is canonical prospective command-array digest, not a
second lock revision or mutable input source.

Build canonical pre-event TeamState after all real decisions, capital costs (including every
requested fund option), current recurring quotes and prior outstanding debt. Record current
available_funds as capital after commitments; no operating cash or speculative grant enters
`available_funds_by_round`. Call existing `advance_ledger(prior,state,original_pack)` once
without fired signals, supplying the P0b assessments above (no legacy-price fallback). Project `project_signal_state(...,current_round=r)`, preserving the
same-round and fired-on-sight response-window exclusions. No raw score pass is required.

Fund eligibility is evaluated against that one final-cost pre-event state and resulting
ledger: exact original event, option fund, valid rationale tag, not already fired, every
original precondition true, original strategy affinity and arms gate satisfied. Eligibility
ignores O2 capacity because prevention is a separate paid choice; it removes that event
before the remaining original deck consumes its unchanged cap slots. All selected funds
are checked together, never successively against partially deducted costs. Ineligible fund
rejects the entire candidate without charge. Defer/reject require the same current challenge
eligibility and an original allowed rationale tag, cost0, and preserve the original event
consequence; absence also leaves it unchanged. Current-round freshly raised challenges may
appear in preview; this does not change frozen responsiveness timing or score credit.

NEW runtime response content covers all13 events with effect `prevent_current_round`:

| Event key | Existing fund price | NEW effect explanation |
|---|---:|---|
| inventory_audit_question | 6000 | Temporary review support prevents this round's audit disruption. |
| warehouse_rollout_gap | 6000 | Temporary floor support prevents this round's rollout disruption. |
| pos_support_ending | 6000 | Temporary support cover prevents this round's outage consequence. |
| ransomware_on_finance | 40000 | Contingency response prevents this round's financial-system disruption. |
| crm_data_exposed | 20000 | Incident containment prevents this round's exposure consequence. |
| phishing_on_staff_accounts | 12000 | An urgent briefing prevents this round's phishing consequence. |
| privacy_regulator_letter | 15000 | A compliance response prevents this round's enforcement consequence. |
| financial_audit_deadline_missed | 18000 | Deadline assistance prevents this round's reporting consequence. |
| unlogged_system_change | 9000 | A change review prevents this round's uncontrolled-change consequence. |
| checkout_queues_lengthen | 14000 | Temporary queue cover prevents this round's checkout consequence. |
| service_backlog_builds | 11000 | Temporary surge support prevents this round's backlog consequence. |
| supplier_portal_request | 15000 | Assisted stock responses prevent this round's supplier consequence. |
| analytics_request_from_board | 10000 | A commissioned report prevents this round's board-request consequence. |

These NEW game effects expire at round end; they buy neither lasting repair nor an estate
asset. Each sentence carries TODO:calibrate M1/M4. Original EventOption.tags are the exact
allowed rationale_tag vocabulary, not the sentences above. Persist `prevented_events` with
key/round/option/rationale_tag/cost/effect and associated open signal episode IDs. A prevented
event is neither fired nor suppressed and does not enter already_fired. Its underlying
watch remains open unless a separate real action removed the condition. A later unfunded
eligible round may fire original outcomes. No response modifies the bound Casepack object:
construct a transient validated copy whose events omit funded keys; use original pack for
all attribution/outcome/price lookup. Run original `resolve_events` once on that deck;
remaining authored order, affinity, arms, fire-once and per-capability cap are unchanged.

Fired events preserve existing failed-node/outage/blast-radius evidence and raw outcomes.
They debit original revenue_loss once and contribute their original scorecard points through
the shared M0 helper. Do not permanently delete failed nodes or secretly alter Tech/Org/Mgmt:
original event outcomes declare no estate mutation. Outage duration describes temporary
consequence, while next-round underlying estate persists. Map fired event signal_open
preconditions to signal keys and call the existing second ledger pass to stamp fire_round.
Project final signals and call existing score_team once authoritatively. No LLM/clock/random
choice enters scoring, transition or resolution. Validate every output finite/ranged, all
scorecard v1 metadata exact, before any publish write.

Technical debt is a separate estimate of deferred fixes, not cash owed. Open one debt record
for an actionable newly raised uncleared episode with positive cheapest_fix_when_raised;
amount is that frozen bounded CREDIT-ELIGIBLE repair quote. Zero/None makes no monetary
debt. An episode whose initial assessment is unassessed gets one separate
UnpricedSignalExposure `{signal,episode_id,opened_round,settled_round:null|round,
reason:unassessed_initial_repair}`. It is not a zero-dollar debt or proof of no repair;
settles when that episode's watched condition no longer raises, without cash effects.
Later opportunities never fill in/reprice the initial unknown amount. Financial/debt
evidence reports priced_total plus unpriced_episode_count; debt_ratio is explicitly the
priced-estimate ratio only. Runtime content with debt_above gates is unsupported in v1
while unpriced exposure can exist (explicit M4 ownership), so unknown costs cannot silently
become a false debt gate. The original pure precondition and legacy path remain unchanged. Runtime node_is_spof
requires pc.node to reference an authored initial physical asset ID; source catalog keys or
guessed future decision-generated IDs are invalid_reference. This closes the exact literal
identity lookup without translating or disabling that precondition. Other original PCs
retain their existing producers and meanings. Settle (settled_round=r)
only when that episode's metric no longer raises and status is cleared; a natural lapse may
settle liability without responsiveness credit. No direct cash debit/refund; real repairs
already charge their actual decision. Fired immutable episodes retain debt until the current
metric ceases raising (then settle liability only, never rewrite ledger history). Outstanding
per-capability ratio = debt/(debt + cumulative attributed real capital spend), with0/0=0;
prior debt feeds pre-event gates; newly accrued/settled debt is for next-round pre-event gates.
Expose opening, additions, settlements, closing; never charge the same episode again.

TCO v1 is an explicit forecast/actual ledger, not full Financial. At application commitment,
validate tco_categories as unique subset of source true+decoy categories; missing field is
invalid, empty list legal. Freeze base capex plus quoted recurring from expected arrival
throughR6, plus estimates for the selected categories: training full option; integration
basic tier; process_redesign full process option or0; capacity one compute_pool unit at
chosen placement; backup one backup_recovery at chosen placement; maintenance one round
source opex; lifecycle and data_migration each ROUND_HALF_UP(.10×base capex); policy maximum
source policy cost (empty policy set=>0). These NEW category estimates live in runtime
content, have source/formula and calibration labels, and do not themselves create expenses.
Decoy selections may overestimate without inventing actual charges. Forecast stays fixed;
actual-to-date sums unique real asset-attributed acquisition, recurring, training, process
and integration(receiver) entries, including replacements. Unallocated wages/firm policy/
response costs remain firm overhead and are displayed separately. TCO output includes
item, selected_categories, true_selected, omitted_true, selected_decoys, forecast,
actual_to_date, forecast_horizon_round6, observation_round and variance=actual_to_date-forecast.
Never call a partial-horizon observation a final forecast error. No caller authors forecast
or actual money; cancellation retains sunk acquisition actual, retirement stops future opex.

## 8. Frozen staged builder packets and acceptance interfaces (D10)

Every packet is Heavy, starts from the supervisor's exact audited integration SHA, and ends
with a fresh independent audit before dependent dispatch. At most two implementation tracks:
P1 waits for independently reviewed/audited P0b; P2 runs after P1; P3 runs after audited P2 because it consumes resource projection;
P4 follows audited P3. This is deliberately sequential except independently bounded P0. P0 is separately dispatchable under its own approved spec. No packet may
amend another's public type/formula; contradictions stop at the supervisor. Shared living
contracts/register/status are supervisor-owned integration edits, not extra builder scope.
All filenames below are NEW unless marked existing. A packet may add its own
`handoffs/recovery/decision-evolution/<packet>/dod.md`, and no other report file.

| Packet | Exact allowed implementation/test files | Deliverable and gate |
|---|---|---|
| P0 engine-inputs | exactly engine-inputs/spec.md allowlist | unit-correct optional inputs and deterministic paths; exact legacy24 gate |
| P0b production-inputs | exactly production-inputs/spec.md allowlist | scoped one-hop data paths and verified-repair input seam; after audited P0 and before P1 |
| P1 content-types | NEW backend/app/simulation/__init__.py; NEW backend/app/simulation/types.py; NEW backend/app/simulation/content.py; backend/packs/riverside_grocery/runtime.yaml; backend/tests/test_simulation_content.py | strict command/runtime/checkpoint DTOs and immutable pack binding; complete frozen NEW content, missing/extra/duplicate/invalid/null/override refusals; no reducer or DB |
| P2 estate | backend/app/simulation/estate.py, resources.py, projection.py; backend/tests/test_simulation_estate.py | one initial estate, lifecycle, edges, source prices/resources, physical graph projection and action-effect candidates; no organisation formulas or persistence |
| P3 organisation | backend/app/simulation/organisation.py; backend/tests/test_simulation_organisation.py | real training/process/communication/resistance/adoption, staff/governance/policy/preferences; only pure DTO input/output |
| P4 consequences | NEW backend/app/simulation/accounting.py, consequences.py, repairs.py; existing backend/app/round/runner.py (only mechanical scorer delegation); NEW backend/tests/test_simulation_consequences.py; NEW handoffs/recovery/decision-evolution/consequences/dod.md | complete pure quote/resolution, costs/actions/ledger/events/debt/TCO, shared M0 helper, authoritative scorer call; no DB |
| P5 persistence | backend/app/simulation/models.py, service.py; NEW backend/alembic/versions/20260914_0003_simulation_v1.py; existing backend/alembic/env.py, backend/scripts/check_postgres_runtime.py; NEW backend/tests/test_postgres_runtime_check.py; backend/tests/test_simulation_service.py | three canonical tables, fresh owned transactions, revisions/reopen/retry/isolation, full migrated schema verification |
| P6 games | backend/app/simulation/games.py; backend/tests/test_simulation_games.py; backend/tests/fixtures/simulation_v1_decisions.json; backend/docs/simulation-v1.md | actual headless decision-only route, four archetypes×four strategies×six rounds, documented direct Python use and evidence limits |

P1 explicitly creates the three NEW source files `backend/app/simulation/__init__.py`,
`backend/app/simulation/types.py` and `backend/app/simulation/content.py`. Their absence at
integrated base `2859e851dd9e429afc2ff9d3e3840f98b017a9cd` is expected, not a
missing-existing-file failure. No other simulation source module belongs to P1; its runtime
content, test and DoD paths remain exactly as already listed. Verify PF1a records absence
before edits and checks the actual candidate creates exactly these three source paths.

If an existing filename above is absent on the assigned base, preflight fails and supervisor corrects the exact allowlist before editing. It is
not permission to create a guessed replacement. P5 keeps historical16 ALL_TABLES unchanged,
adds SIMULATION_TABLES with the3 NEW models, and imports both model modules into Alembic
metadata. Expected public schema is the exact migrated19 model tables plus alembic_version;
verify_schema must not weaken its equality assertion. No Base.create_all substitute for
migration evidence, no table rename, and no database selected from ambient environment.

P4's shared scorer is the existing private `RoundRunner._rolled_scorecard` helper in
`backend/app/round/runner.py`, which is authoritative for the frozen M0 scorecard shape and
legacy behavior. P4 may expose `rolled_scorecard(pack, final_score, event_records)` through
that existing runner module only as a mechanical adapter to the helper. It must not create a
new `scorecard.py` module or change runner semantics beyond that delegation; this path
correction does not expand P4's behavior or persistence scope.

NEW internal interfaces (all pure except service; dataclasses/strict models may implement):

```python
load_runtime_pack(path) -> RuntimePackV1
normalize_patch(existing: tuple[CommandV1,...], patch: SheetPatchV1) -> tuple[CommandV1,...]
initialize_state(pack, strategy_key) -> CheckpointStateV1                 # P2
reduce_estate(pack, prior, commands, round) -> EstateDeltaV1              # P2
resource_projection(pack, assets, connections, policies, round) -> ResourceViewV1
reduce_organisation(pack, prior, estate, commands, round) -> OrgDeltaV1    # P3
project_team_state(pack, state, round, resources:ResourceViewV1, staff:StaffPool,
                   stakeholder_alignments, decisions, actions, funds, debt_ratios,
                   signals=(), entity_access=(), repair_assessments=()) -> TeamState                            # P2
prepare_effects(pack, prior, commands, round) -> PreparedEffectsV1         # P4
assess_repairs(pack, prior, commands, round, prepared) -> list[RepairAssessmentHistory]
quote_transition(pack, prior, commands, round) -> PreviewV1               # P4
resolve_transition(pack, prior, commands, round) -> TransitionV1          # P4
rolled_scorecard(pack, final_score, event_records) -> (dict, dict)         # shared M0
run_game(engine, pack, archetype, strategy, instance_id, team_id) -> list[dict] # P6
```

`EstateDeltaV1` contains updated assets/connections/projects/hiring_orders/staff_hires/
rollouts(primary lifecycle/count carry only)/primary, actual estate charge entries,
arrived_ids, retired_ids, expired_ids, and effect_candidates. It never contains Org scores.
`ResourceViewV1` contains per-placement supply/draw/factor, per-asset capability ceilings/
load/recurring and total load/recurring. P3 receives that state and uses same resource function
for staffing after policy changes, rather than recoding resource formulas. `OrgDeltaV1`
contains updated rollouts/unit_resistance/governance/primary/policies/support/strategy/
strategy_declared_round, staff capacity/load, this-round communication selections,
organisation charge entries, stakeholder alignments and effect_candidates. P4 passes OrgDelta stakeholder_alignments and staff totals explicitly into P2 projection;
P2 never imports P3 or reads a duplicate alignment checkpoint. No financial
balances are independently mutable in these deltas; P4 alone combines/settles them.

PreparedEffectsV1 is `{estate:EstateDeltaV1,organisation:OrgDeltaV1,resources:ResourceViewV1,
state:CheckpointStateV1,cost_entries:list[CostEntryV1],decisions:list[DecisionState],
actions:list[ActionEnvelope],operating_forecast,capital_available,capital_spend,capital_remaining}`.
Its state is a private uncommitted candidate, with prior signal/event/assessment histories
carried unchanged; no grant/decay operation is repeated after this boundary.

Frozen inter-packet DTO details (all fields required, no extras):

```text
EffectCandidateV1 = {effect_kind:arrival|replacement|training|process|integration|support|
 retirement|policy,source_round:int,source_command:command_key,effect_round:int,
 asset_id:key|null,target_key:key|null,capabilities:list[key],cost:int,action_type:
 add_node|scale_node|move_to_cloud|upgrade_component|add_training|redesign_process|
 add_service_tier|retire_component|add_policy}
ResourceViewV1 = {by_placement:map[placement,{compute_supply,storage_supply_gb,
 compute_draw,storage_draw_gb,factor}],by_asset:map[asset,{capacity_by_capability:
 map[cap,float|null],compute_draw,storage_draw_gb,staff_load,opex:int}],
 integration_load:float,policy_load:float,total_load:float,total_opex:int}
EstateDeltaV1 = {assets,connections,projects,hiring_orders,staff_hires,rollouts,primary,
 charge_entries:list[CostEntryV1],arrived_ids:list[key],retired_ids:list[key],
 expired_ids:list[key],effect_candidates:list[EffectCandidateV1]}
OrgDeltaV1 = {rollouts,unit_resistance,governance,primary,policies,support,strategy,
 strategy_declared_round,staff:StaffPool,communication:map[unit,option],
 charge_entries:list[CostEntryV1],stakeholder_alignments:list[StakeholderDecisionAlignment],
 effect_candidates:list[EffectCandidateV1]}
```

Unannotated ResourceView numbers are finite nonnegative floats rounded6; factor0..1.
Total_opex covers assets/integrations only, not wages/support/event losses; P4's accounting
adds those exactly once. Source values/units derive from runtime content. Asset maps include
live assets only; by_placement includes every declared placement even if all values0 and
factor1. Policy load is included in total_load once, and support alters StaffPool capacity,
not source resource draw. Other unannotated DTO members use the exact checkpoint record
shapes in§4. EffectCandidate.cost exact nonnegative integer is original real charge; keys
and caps validate against original source/live effect. effect_round is currentr, source_round
is originalcommitment≤r; new purchases cannot emit an effect candidate while pending.

P4 expands each EffectCandidate's sorted unique capabilities into ActionEnvelopes. Envelope
id=SHA256 canonical JSON `[source_round,source_command,effect_round,action_type,capability,
target_key]`. Its record is the existing ActionRecord with locked_round=source_round and
source price. No envelope for empty effect/no-op. Unique envelope IDs reject duplicate
emission. Source join is `(source_round,source_command)` to the immutable locked historical
or current candidate sheet; service validates that join before publishing/reading history,
while pure preparation obtains it from current commands or original Project IDs. Price,
action and target must match that producer's effect; a valid-looking unattached envelope
is invalid_output. The engine receives only tuple(envelope.record), not the provenance
wrapper. This adds no field to the existing pure ActionRecord.

Canonical collection order is exhaustive:

| Collection | Identity and order |
|---|---|
| assets/connections/projects/hiring_orders/rollouts/governance/primary/policies/unit_resistance maps | unique object key; JSON object keys sorted |
| sheet commands / repair witness commands | unique command.key; sort(category,key) |
| staff_hires | unique order_id; sort(arrival_round,order_id) |
| technical_debt / unpriced_signal_exposures | unique(signal,episode_id); sort(opened_round,signal,episode_id) |
| cost_ledger / charge_entries | unique(round,kind,source); sort same tuple |
| signal_ledger | unique(key,episode_id); sort(first_shown_round,original_watch_rule_index,episode_id), preserving original append chronology |
| action_history envelopes | unique id; sort(effect_round,source_round,source_command,record.action_type,record.capability or empty,record.target_key or empty) |
| effect_candidates | unique(source_round,source_command,effect_kind,target_key); sort(effect_round,source_round,source_command,effect_kind,target_key or empty) |
| event_history | unique round; ascendinground; nested fired/suppressed retain original deck order; prevented original deck order |
| response_history | unique(round,key); sort(round,key) |
| tco_forecasts | unique asset_id; sort(ordered_round,asset_id) |
| repair_assessment_history | unique(round,signal); sort(round,original_watch_rule_index); candidates/uncredited/excluded by candidate_key |
| available_funds_by_round / operating_forecast / driverarrays | ordinal round index; never lexical/value sort |
| IDs/capabilities/coverage lists, preference caring sets | de-duplicate where producer-derived, reject duplicate caller/content entries; sortlexically |
| stakeholder_alignments / preferences.rules | unique stakeholder; source stakeholder order; views retain authored table order and source pointers address stable list indices |
| access_via | exact P0b five-field sort/filter/empty rules |

No generic `(round,key)` fallback exists. Digest canonicalization calls these orders before
sorted-key compact JSON, so reversed input maps/sets cannot change state, and arrays with
meaningful source order are not arbitrarily reordered. No unsupported null replaces an
empty required list/map. Initial empty histories are explicit[]; scalar nulls remain only
where their shapes allow them.

NEW vocabulary ownership: M1 headless guide uses machine keys for hiring/communications,
command enums, assessment reasons and errors; no rendered student label is claimed. M3
must author and validate display labels in the casepack labels.yaml/UI vocabulary boundary
for it_generalist, feedback_loops, knowledge_portal, change_champions and their decision/
error/status copy before browser release. Runtime schema does not invent label keys now.
Unit labels already have people.units.label; original catalog/service/policy labels remain
original content-owned. The headless guide documents this exact deferred display home;
P1/P5 cannot silently create alternate human label text in DTOs or HTTP responses.

`PreviewV1` has version1, round, normalized_commands, arrivals/retirements/expiries (IDs),
capital_available, capital_spend, capital_remaining, operating_runrate,
operating_forecast:[{round,opening,allowance,recurring,closing}],
challenges:[{event,eligible,allowed_options:[{key,cost,tags}],ineligible_reason}],
repair_assessments:[RepairAssessmentHistory], prevented_events, would_fire:[event_key],
cost_entries and warnings:[{code,keys}]. All fields are required. Challenge
ineligible_reason is null when eligible, otherwise precondition|strategy_affinity|arms|
already_fired, using that precedence; all source events appear in original deck order.
Warning code is operating_deficit|unpriced_repair, keys sorted machine references (empty
for a whole-run operating deficit); no arbitrary prose or undeclared warning code.
Repair assessments are detached current-round witness rows, never appended by preview. It exposes
all remaining event costs in would_fire evidence via original outcome references. Invalid
fund/affordability raises typed errors containing the candidate preview's relevant facts;
no invalid candidate preview is saved as a draft. `TransitionV1` is `{state:CheckpointStateV1,
result:dict,preview:PreviewV1}`. Shared private transition preparation produces both quote and
resolve; quote never calls score_team or writes history. Resolve's result uses existing
RoundResult core fields plus `simulation_version:1`, pack_digest, sheet_revision,
checkpoint_digest, prevented_events, accounting, state_changes and TCO v1 detail. Existing
scorecard and scorecard_meta shape/units/status remain byte-compatible. Pure transition
result's scope/revision/digest publication fields are supplied solely by service after
validated resolution, then validated again; sheets cannot supply them.

Exact NEW result evidence homes: `accounting={opening_capital,opening_operating,
capital_grant,operating_allowance,capital_spend,opex_runrate,event_loss,closing_capital,
closing_operating,cost_entries,unallocated_operating,technical_debt:{opening,added,settled,
closing,unpriced_episode_count}}`, all money integers, count a nonnegative integer,
closing the priced_total estimate only, and cost_entries this round only. `state_changes={arrived,
retired,expired,changed_rollouts,changed_policies,changed_assignments,resource_view,
entity_access}`, ID lists sorted; changed lists hold their exact new checkpoint record
plus its key, resource_view uses ResourceViewV1, entity_access rows have the exact5
EntityAccess fields; no added_capabilities/expanded-serves state exists. No evidence changes state.
The existing `financials` compatibility fields are actual capital_spend/opex_runrate/debt
closing, not a duplicate financial authority. `pack_identity={key,version,digest}`.
Prevention evidence `{key,round,option,rationale_tag,cost,effect,signal_episodes:
list[{key,episode_id}]}`; suppression `{key,reason:cap|already_fired,capability:key|null}`;
fired evidence is exactly original runner's event/outage shape. TCO item values use §7's
exact named shape; these are version1 extensions, never inserted into historical payloads.

P1–P6 required readsets: root four protocols/contracts, this master+verify+authority,
inventory/review/content-basis, design04/07/08 and original1.4/1.5/1.6 specs; complete files
read or called by each packet, including preceding packet public DTOs. P1 additionally
reads original loader/models/validate boundary and every referenced YAML. P2 reads complete
state/graph/catalog/technology/metrics/preconditions/events. P3 reads complete organisation/
management/state and all preference/policy sources. P4 reads complete ledger/events/score/
rollup/runner/actions/snapshot and event/watch/obligation YAML. P5 reads complete old models/
db, migrations/env/schema verifier and any runtime verifier tests then present (the named P5 test file is NEW). P6 reads complete
service/DTOs/consequences, historical calibration harness and game seed sources; no seed
call is permitted in its route. Readset completion is a preflight fact, not a title-only read.

Each packet reports PF0 clean/exact-base; PF1 actual predecessor imports/signatures;
PF2 all source prices/keys/consumers it relies on; PF3 focused preexisting tests; PF4 the
out-of-scope dependency scan and explicit inspected hits; PF5 its computed falsification
probes in verify.md. Any mismatch stops dependent edits. `make check`, own focused suite,
`git diff --check`, allowed-file audit and independent candidate audit complete each packet;
P5 additionally migrates a disposable PostgreSQL DB and proves schema/concurrency. P6
reruns historical24 full payload and the production96 rounds. Neither is a balance claim.

## 9. Living contracts, limitations and closeout

Supervisor applies the following literal NEW entry to CONTRACTS.md on audited integration
and bumps its changelog/version in the same session:

> **Simulation v1 — decision and state authority.** The production SimulationService owns
> fresh scoped transactions, typed revisioned sheets and immutable transition checkpoints.
> Initialization binds one validated runtime-content fingerprint and refuses occupied scope.
> Only the checkpoint is authoritative; pure TeamState is an in-memory projection. All
> acquisitions, arrivals, resource use, training, process, communications, staff, governance,
> policy activity, costs, actions, signals, responses and debt/TCO derive from content plus
> decisions. Callers cannot author price, score or resulting state. Invalid edits and failed
> advances roll back; matching advance retries return the same result. Only current locked
> unadvanced sheets reopen; advanced history is immutable. Historical RoundRunner/seeds and
> their16 tables remain fixture compatibility interfaces. M2 scheduling/auth binds to
> SimulationService, never uses that historical path as a production fallback.
>
> **Simulation v1 money/consequences.** Capital carries authored grants; operating reserve
> receives the explicitly provisional runtime allowance and pays derived recurring costs
> and event losses. They never silently transfer. New liabilities must fit the remaining
> six-round horizon; no purchase arrives after the game. Funded challenge prevention lasts
> only its current round and is separately recorded, with no false fire or repair credit.
> Signal actions publish only upon actual effect with their original commitment round;
> zero-effect/zero-cost training and cancelled/no-op purchases publish no action. Technical
> debt is a frozen estimate from the bounded verified credit-eligible repair catalogue;
> unassessed exposure is reported separately, never as a zero-price or no-fix assertion.
> Uncredited physical repairs may lapse a signal without changing authored clearing rules.
> TCO is forecast versus actual cost evidence. Financial
> score remains partial under unchanged scorecard-v1 units/status; full finance is M4.

Append to design/07-decision-consequence-map.md:

> ### M1 production consequence route
> Simulation v1 resolves one initial estate through six typed decision sheets. Runtime
> supplement v1 makes missing resource, organisation and preference parameters explicit
> provisional authored estimates. Training/process/communication, named stakeholder-group
> governance, staffing/support, lifecycle, connections, policy activity and cost consequences
> now have decision producers after the audited M1 packets land. Existing pure MOT, policy
> alignment, event/ledger and scorecard-v1 rules remain the consumers. Scoped one-hop entity
> access preserves physical source ownership and roles and requires its receiving asset
> in serving paths. Verified repair inputs preserve historical legacy quote behavior only
> for the historical route. Do not use historical
> scripted RoundRunner examples as evidence of this production route. Full finance and the
> explicitly recorded unsupported preference/policy vectors remain M4; browser interaction
> remains M3 and authentication/scheduling M2.

Append to the production-v1 applicability note in handoffs/2.3-round-scheduling/spec.md:

> M1 authority supersedes legacy rewind descriptions for production v1: reopening is legal
> only on the current locked/unadvanced sheet and increments its revision. An advanced
> sheet/result/checkpoint is immutable. Scheduling must call SimulationService; future
> instructor resets require a separate authorized run lifecycle contract.

Supervisor integration (README.md, exact existing path) updates the schema verifier's runtime documentation to19 model tables plus the
migration version table, preserving the historical16 explanation where fixture-specific.
P6 calibration-marker report uses actual YAML inventory including NEW runtime.yaml;
no parameter/file is excluded to preserve an obsolete count. Existing pack YAML bytes stay
unchanged; the directory gains new versioned runtime content. Supervisor records current
marker count after authoring rather than asserting the old38 count remains.

Explicit M1 limitation: ecommerce_site's original `must_be_fed_by` declares only product;
customer_database originally serves customer_insight/service. Therefore validated product
integration can expose POS product to marketing_sales, but no declared customer integration
exposes household customer or its role there. This source gap remains M4 authored-content
work. All four strategies must execute with honest partial scores/evidence; M1 promises
neither perfect attainable coverage nor pedagogical balance. No undeclared dependency,
role/entity overwrite or second vertical is added to conceal it.

Settled/open status: architecture/content families and numerical proposals approved by
supervisor rulings recorded in authority and dated messages; exact master schemas/order/
packet interfaces require fresh review before P1. Any defect found in review is OPEN until
author correction and supervisor/reviewer acceptance, never builder discretion. Product
reserved decisions remain unopened. Definition of Done and headless student playthrough
are in verify.md, whose rows map D1–D10 and every packet above. Browser screenshots and
visual acceptance are N-A because this artifact changes no student screen or HTTP route.
