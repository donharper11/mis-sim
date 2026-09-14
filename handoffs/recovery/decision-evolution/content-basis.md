# M1 content and producer basis

Date: 2026-09-14. Inspected base: `b7706fb2ff8cc63cee7e871bb9fbe82d24835074`.
Read-only research; this file is the sole repository change. **Not an approved schema,
transition formula, calibration ruling, or builder dispatch.** `[V]` marks direct source
inspection or the local reproduction below. **NEW** marks recommendations requiring the
M1 author's explicit contract. No values or formulas are inferred from historical scores.

## Basis and limits

Read `GOVERNANCE.md`, `QUALITY_PROTOCOL.md`, `SPEC_PROTOCOL.md`, `CONTRACTS.md` in full;
the north star, decision inventory and its review; designs 04/07; complete casepack
models/loader and Riverside catalog, platform, capabilities, metadata, strategies,
stakeholders, policies and five preference files. Inspected the engine state,
organisation, management, graph, technology, metrics, events, preconditions and rollup
consumers; round snapshot/models and runner mutation/accounting/event paths; R3/full
and four archetype seed construction; local `change_management_master.json` harvest.
The material below covers the content inputs needed to author M1, but cannot settle
missing numerical transition models. No external service or database was contacted.
Quality ladder: source/contract inspection and local pure-Python probes apply; build,
migration, browser/auth and UI checks are N/A to this documentation-only research.

The governing seams remain: “One source of truth per fact” (`SPEC_PROTOCOL.md §3`);
“The production path must never replace the estate with a hand-authored answer each
round” (`design/08-implementation-north-star.md:18`); policy absence resolves to default
with `actively_decided=False`, and policy overrides remain unsupported (`CONTRACTS.md`,
`TeamState.policy_decisions[]` entry). M0 event scorecard units and partial Financial
status are already frozen; M1 must preserve that contract.

## What content already authors

All rows in this section are **[V]**, with repository-relative citations at this base.

| Input | Actual source and consumer | Missing producer/meaning |
|---|---|---|
| Catalog identity, placement and configuration | `casepack/models.py:183–262` under `backend/app/`: 14 items/42 placement modes; capex, recurring opex, lead time, platform bypass, roles, serves, sizing, availability, service life, staff load, entities/dependencies, people, training/process, R/G/T, cost-category lists and config multipliers. | No throughput, installed-asset identity, placement-specific load, upgrade/refund or maintenance price. Config `compute_multiplier` does not define throughput. |
| Shared services | `backend/packs/riverside_grocery/platform.yaml:34–190`: 11 services/33 placement modes. Schema `models.py:285–315` has roles, prices, utilisation percentage, load, entities; starting staff is 2.0 FTE. | No absolute compute/storage supply, service availability/life, service `serves`, or catalogue training/primary-rollout equivalent. `PlatformServiceRow` exists but snapshot never reads it (`backend/app/round/models.py:110–120`; `snapshot.py:120–211`). |
| Demand | Seven capability curves plus units in `backend/packs/riverside_grocery/capabilities.yaml:1–66`; pure lookup `backend/app/engine/catalog.py:44–50`. | The catalog's ten sizing drivers are not all capability demand units; mappings/quantities need authoring. |
| Support | Basic 20,000 / 0.6 FTE; standard 50,000 / 1.4; premium 100,000 / 2.4 (`platform.yaml:192–234`). | Persistence, charged period, vendor scope and replacement timing. FTE values are explicitly authored calibration estimates, not harvested staffing measurements. |
| Integration tiers | Basic 50,000; advanced 120,000; vendor-managed 200,000 (`platform.yaml:236–239`). Model has only key/cost/provenance (`models.py:305–308`). | No per-edge tariff, capacity, availability, staff relief, lead time, or entity-transfer effects. These cannot be invented by treating a tier's name as its effect. |
| Training/process | Every item has none/basic/full cost+coverage; nine have a single costed process option. Order management: 0/12,000/34,000 for 0/.6/1 coverage; redesign 22,000 (`catalog.yaml:65–85`). | Integer rounding, overlap/repeat treatment, decay, timing; whether the single process option yields partial or redesigned. Existing scorer maps redesigned/partial/unchanged to 1/.5/.25 (`engine/organisation.py:24–25`), not a transition rule. |
| Strategy | `strategies.yaml:29–163`: four real keys, capability weights, concentration, R/G/T mix, maintenance floor, reopen cost 80,000 each. | Initial declaration and revision producer; resistance spike magnitude/timing; truthful maintenance-tag production. No strategy preference is required by design07 §3.0. |
| Policy | Six three-position ordinal switches with defaults, one cost and one generic effects map each (`policies.yaml:48–155`; `models.py:470–519`). | Per-position/repeated-change charge and effects semantics. Existing ordinal scoring/gating is live; generic effects are not applied by the runner. |
| Stakeholders/preferences | 14 actual stakeholder keys/archetypes (`stakeholders.yaml:1–14`); five preference domains loaded dynamically (`casepack/loader.py:72–82`). | No named owner/sponsor roster or capability eligibility. Non-policy alignment and caring sets are supplied scalars, not resolved from these preferences (`round/snapshot.py:181–185`). |
| Money/events | Budgets `[400000,260000,220000,220000,200000,200000]`, opening opex 47,000 (`pack.yaml:12–14`); 13 event options priced below. | Initial wages/cash, income per round, capital-request terms, debt settlement, real TCO actuals, funded-response effects. Company revenue 140 MUSD is company context, not a cash-flow formula (`pack.yaml:7–11`). |

`platform.capacity_pct` is **used percentage**: compute 100%, storage 70%; the pack states
this explicitly (`platform.yaml:45–73`). It cannot become capacity supply. Catalog sizing
drivers are `transactions`, `orders`, `sku_count`, `reporting_periods`, `stores`, `sites`,
`customer_records`, `records`, `visits`, `tickets`. Company sites supplies 8 for sites/stores;
orders can explicitly reference the order curve. Mapping store-day to transactions,
campaigns to visits, reports to reporting periods, or orders to SKU count is **NEW**, not
an identity conversion. Resource-draw units are compute and storage GB (`models.py:190–202`).

## One inherited estate, and why copying the fixture fails

[V] `InitialState` is dashboard context at round **3**, with scorecard/people/review prose,
not an architecture (`models.py:114–139`; `pack.yaml:15–114`). Runtime round snapshots
read only that round's node/edge/deployment rows (`round/snapshot.py:134–155`). Full-game
and archetype seeds therefore author estates every round; this is their declared fixture
role (`backend/seeds/riverside_full.py:15–18`; `archetype_base.py:3–18`).

**NEW recommended initial references**, to be authored once in a versioned runtime content
section such as the contract author's proposed `runtime.yaml` / `Casepack.runtime_v1`:

- Catalog, on-premises: `pos_system_2011`, `order_mgmt_v42`, `accounting_package`,
  `store_spreadsheets`, `order_db_cluster`, `store_back_office_pc`; each uses its actual
  baseline configuration key (`core`). These reflect the incumbent component rows in
  `catalog.yaml:43–157,288–354`.
- Platform, on-premises: `client_network`, `compute_pool`, `storage_pool`,
  `backup_recovery`, from `platform.yaml:34–83`. Email is described as placed R2
  (`platform.yaml:159–173`), so it is not automatically a round-1 incumbent.
- Place Centraline through a later purchase. The full seed omits its deployment in R1
  (`riverside_full.py:92–109`) but retains its node via `_nodes_for_round` and
  `riverside_r3._nodes`; that fixture inconsistency must not become the initialization rule.
- `next_gen_firewall` is an optional additional explicit incumbent, if the author wants
  the inherited security perimeter. Its own catalog facts apply; do not import a seed
  node's extra `network_path` role (`catalog.yaml:158–183`; `riverside_r3.py:69–73`).

[V] The proposed six catalog/four platform references total **14,200 recurring cost and
3.3 staff load**, before salaries/support. Adding the catalog firewall adds 2,500/.2.
The reproduction below derives these totals. The historical 47,000 is instead
back-distributed over nodes (`riverside_full.py:41–44,80–89`); no documented breakdown
justifies using its difference as a hidden recurring expense. Applying the design's
31,000 hire price to both starting FTE would itself exceed that historic opening total;
there is no authored starting-wage rule.

**NEW initialization semantics needed:** stable asset IDs and source references; installed
age/round; physical connections; active configuration/placement; explicit primary rollout;
only inherited trained count/process/adoption/resistance as one-time authored conditions;
policy defaults; starting assignments and prior commitments only when actually authored.
Carry these forward from the previous committed estate; snapshot rows may be materialized
outputs, but cannot be an additional authoring input each round. Initial inheritance need
not pay the new-purchase capex; that accounting treatment must be explicit.

### Topology and mixed demand units

[V] A node has **one** throughput scalar, defined in the demand unit of its capabilities
(`engine/state.py:29–44`). Serving-path source/target selection checks `serves`, but the
walk uses **global** adjacency (`engine/graph.py:85–98`); the bottleneck includes every
finite-throughput node along that path (`graph.py:113–124`). Examples of incompatible
units on one catalog item include ERP (orders/reports), order management (orders/store-day),
customer database (customer records/tickets), and analytics (records/reports).

**NEW recommendation:** an explicit capability-specific throughput profile, together with
a reviewed projection that never compares different units on one path. Capability facets
alone are insufficient if cross-capability paths can transit other finite-capacity facets.
Retirement, accounting and staff load must apply once per physical asset, and failure must
have explicit physical-asset versus facet semantics. Two existing consumers also need a
seam: `placement_count` counts nodes (`engine/preconditions.py:106–110`), and RTO lookup
matches catalog key directly to failed **node key** (`engine/events.py:214–218`). Generated
facet IDs would otherwise inflate placement counts and miss catalog RTO values.

[V] Existing finite seed candidates are **8,000 orders** at R1/R2
(`riverside_full.py:37–39`) and **6,000 store-day** for POS (`riverside_r3.py:104–108`).
The separate R3 score pin uses order throughput 7,225, fitted to the pin, not a baseline
capacity specification (`riverside_r3.py:15–24,45–49`). Shared seed nodes use 10,000,000
to mean unconstrained; the real schema already supports `None` for no ceiling. No grounded
finite ceilings were found for customer database, analytics, ecommerce, service desk,
ERP, spreadsheets, or the database alternatives. Those values and configuration/placement
capacity effects require **NEW authored calibration data**, not an invented derivation
from `compute_multiplier` or the current round's demand.

[V] Copying the old topology also invents content: seed `accounting_node` owns sale and
fills transaction export (`riverside_r3.py:111–115`), whereas the accounting catalog owns
only ledger and fills accounting_app (`catalog.yaml:109–129`). Seed `store_pc` serves
order/store/finance, while its catalog equivalent serves only store operations
(`riverside_r3.py:58–62`; `catalog.yaml:323–335`).

**NEW topology recommendation:** connect the shared client-network service to the actual
application/data assets and author its capability reach. Keep catalog roles and ownership
as the source. Define what an integration exposes and where, including direction/entity
and duplicate ownership semantics; today's edge stores only src/dst/kind
(`round/models.py:77–86`). The source's `must_be_fed_by` is a dependency, not an implemented
data-transfer producer. Current data adequacy only sees owners whose `serves` includes
the capability (`engine/graph.py:68–82`; `technology.py:53–75`).

The complete declared-catalog union still lacks **sale for customer_insight** and
**product and customer for marketing_sales**. No marketing_sales product owner means no
serving path even if ecommerce is purchased. POS owns product/sale; ecommerce explicitly
expects product from store operations (`catalog.yaml:54,235–241`). This gives a grounded
integration need, not permission to synthesize ownership for free. Firm infrastructure's
user-account owner is the platform's central sign-on (`platform.yaml:103–120`). All four
strategies must be exercised against these actual content constraints.

## People, rollout and governance inputs

[V] Affected population belongs to the catalog, **not the unit total**. The real values are:
POS 62; order/spreadsheets 140; Centraline 34; accounting/ERP 8; customer database/analytics/
ecommerce 28; service desk 18; order DB/NoSQL 2; back-office PC 8; firewall 620
(`catalog.yaml:57,79,101,123,150,176,198,220,242,264,306,337,370,402`). POS's 62 are till
operators within the 140-person unit, explicitly documented. Do not sum deployments as
unique people. Unit headcount is stored but not consumed by the snapshot, and archetypes
seed it as zero (`round/models.py:123–132`; `snapshot.py:157–160`;
`archetype_base.py:85–86`).

**NEW minimum organisation content:** a real unit registry and membership/aggregate rule;
starting headcounts; initial resistance; option applicability/target; count rounding and
repeat-training overlap rule; decay rate; adoption inputs including new-deployment baseline,
sponsorship and usability; change-volume sensitivity and staffing amplification;
communication effect and duration; strategy-reopen shock. These are required *inputs to
the author's transition formula*, not new formulas supplied by this research. Starting
warehouse 34/store 140/finance 8 are supported by `pack.yaml:49–69`; marketing 28/service
18/IT 2 are catalog affected counts and should not silently become exhaustive headcounts.
`firm=620` is an aggregate population, not an extra department to add to all others.

[V] Usable inherited rollout candidates, only if deliberately rebased into a new initial
estate: POS trained 62/process redesigned/adoption .97; accounting 8/redesigned/.94;
order 49/partial/.61; spreadsheets 70/unchanged/.48 (`riverside_r3.py:138–173`). These are
historical R3 state, not evidence for transition coefficients. Likewise .4665 store
resistance was fitted, warehouse .62 and finance .18 were authored (`riverside_r3.py:45–49,
176–181`). The existing engine only reads these outputs (`engine/organisation.py:44–84`).

[V] Grounded new option candidates: **hire** +1.0 FTE, 31,000/round, one-round lead from
`design/04-decisions-g1-g6.md:47–54`; communication **Change Champions 4,000**, **Knowledge
Sharing Portal 3,500**, **Feedback Loops 2,500** from local harvest
`backend/harvest/mis_lite/change_management_master.json:29–36,56–72`. **NEW** stable option
keys, price-period/scope, effects, lifetime and applicability are still required. These
harvest rows provide no decay/adoption/resistance coefficients. Reuse catalog training
prices instead of the harvest's unrelated “Comprehensive Training” 5,000.

[V] Design04 distinguishes on-prem/cloud/SaaS staff burden, while catalog/platform have
one load scalar each (`design/04:63–74`; `models.py:251,290`). **NEW** per-placement load
or modifier and support scope are necessary if that decision is to work as designed.
Scorer staffing is existing capacity/load capped at one; outage staffing already has a
frozen modifier (`engine/organisation.py:35–41`; `events.py:223–226`). Do not silently
replace those formulas. Staffing's effect on currency is also absent from the current
age-only currency function (`technology.py:79–90`), despite design04 §G1.

[V] Governance currently consumes booleans; primary rollout is at most one capability
per deployment (`engine/state.py:64–97`). Existing stakeholder rows include departments
and external groups, not assignable persons; event `from_persona` keys are different
identifiers (`stakeholders.yaml`; `events.yaml:24,39,54`). **NEW** assignment eligibility,
person/role identity, owner/sponsor removals and primary selection need a contract. A
minimal role roster may reference existing internal stakeholder roles, but must not
pretend those groups are already a person directory. Governance is free in design07 §3.4.

## Preferences: supported facts versus undefined interpretation

[V] `PreferenceDefaults` allows arbitrary dictionaries (`models.py:464–467`), so a loaded
file is not proof of a numeric resolver. Actual non-policy shapes are:

- Catalog: `ideal_cost_posture`, numeric `ideal_reliability`, high/low training/data/
  availability/integration/security/compliance/privacy/visibility/load ideals; overrides
  use `item`, `archetype`, `ideal_value`, `weight` (`preferences/catalog.yaml:1–19`).
- Platform: exact cloud/on-prem weights for seven internal archetypes; `no_preference`
  is real; no SaaS weight exists. Other ideals are high/low; overrides include 95/90 with
  no specified unit (`preferences/platform.yaml:29–49`).
- Training: high coverage, medium cost/change volume; Centraline override ideal_value 100
  (`preferences/training.yaml:1–9`). Services: per-decision `ideal_tier` plus weights and
  no overrides (`preferences/services.yaml:62–141`).
- Policy: `by_decision[policy].ideal_posture` plus weights; this is already consumed by
  the frozen asymmetric ordinal scorer (`engine/management.py:254–359`).

**NEW minimal supported resolver recommendation:** typed measures tied to actual choices
or produced attributes, beginning with training coverage, numeric reliability, placement
and support/integration tier. Author exact normalisation, scope, absence, weighting,
override targeting and duplicate rules. “High/low/medium” needs a declared ordinal or
numeric scale; 85/95 cannot be treated as percentages without a new unit contract. A
versioned runtime mapping may make that interpretation explicit while preserving the
legacy files. It must name every supported/unsupported source field; silently ignoring
the catalog/platform/training overrides is not a valid resolver.

[V] Only three historical caring sets are supplied: operations → order/store, finance →
reporting, customer → insight/service (`riverside_r3.py:236–255`). **NEW** authored caring
sets are needed for additional stakeholder output. The existing per-capability scorer
averages the supplied scalars; satisfaction multiplies alignment by realised value as
an output only (`management.py:393–408`; `rollup.py:103–119`). Do not feed satisfaction
back into alignment or count policy again in this non-policy scalar.

[V] The six policies' generic effect keys are `privacy_risk`, `customer_trust`,
`analytics_reach`, `storage_cost`, `recovery_confidence`, `staff_load`, `compliance_risk`,
`integration_friction`, `partner_reach`, `insider_risk`, `employee_trust`
(`policies.yaml:51,69,86,103,120,140`). **NEW** a v1 disposition for each is required:
which state field or report it changes, or an explicit M4 deferral. In particular a
`staff_load: .05` vector does not say whether it applies to both non-default positions,
scales by ordinal index, or repeats on every decision. Preserve existing policy preference
and obligation behavior without inventing those extra effects.

## Accounting and event dispositions

[V] Current event fund prices are below; every defer/reject is zero. All 13 options have
only key/tags/cost, with **no response-specific outcome or mutation payload**
(`models.py:410–424`; `backend/packs/riverside_grocery/events.yaml`, cited starts below).

| Event | Fund cost | Source start |
|---|---:|---:|
| inventory_audit_question | 6,000 | 20 |
| warehouse_rollout_gap | 6,000 | 35 |
| pos_support_ending | 6,000 | 50 |
| ransomware_on_finance | 40,000 | 66 |
| crm_data_exposed | 20,000 | 89 |
| phishing_on_staff_accounts | 12,000 | 110 |
| privacy_regulator_letter | 15,000 | 132 |
| financial_audit_deadline_missed | 18,000 | 153 |
| unlogged_system_change | 9,000 | 172 |
| checkout_queues_lengthen | 14,000 | 193 |
| service_backlog_builds | 11,000 | 214 |
| supplier_portal_request | 15,000 | 235 |
| analytics_request_from_board | 10,000 | 257 |

No reliable 13-row response-to-mutation map can be recovered from this schema. Warehouse
fund 6,000 differs from its actual training 12,000/34,000; POS support fund 6,000 differs
from basic support 20,000. Making these options secretly buy those actions introduces
**NEW** scope/subsidy/quantity semantics. The author must either supply explicit response
effects and their pricing rule or clearly limit v1 to recorded response/cost/rationale
with a named later effect owner. Neither choice is already settled by the source.

[V] Event outcomes contain separate monetary `revenue_loss` and BSC point deltas. Runner
records outage evidence and re-reads unchanged estate; it neither deletes the failed node
nor deducts revenue loss from a cash balance (`runner.py:326–355`). The failed-node docstring
describes removal, but the code computes hypothetical outage evidence only. **NEW** timing
and persistence disposition must distinguish temporary outage, permanent estate mutation,
reported loss and actual cash effect. Preserve M0 scorecard conversion; monetary loss is
not another automatic Financial-score delta (`CONTRACTS.md`, scorecard v1 entry).

[V] Costs currently mean caller-supplied decision capex, node-contribution opex and accrued
unsettled fix debt (`round/snapshot.py:39–56,70–97`; `runner.py:185–237`). TCO actual is
pre-supplied, not derived. **NEW** authoring/producer decisions needed: inherited costs,
salary and support expense timing, capital carry/refunds, cash authority, debt meaning and
settlement, forecast horizon/categories, actual-cost attribution, and request terms. Full
Financial scoring stays M4: the live Financial rollup remains a discipline proxy with
`financial_partial=True` (`engine/rollup.py:77–90`).

[V] Signal actionability uses catalog mode capex, effectful training prices, tier/policy/
process prices and event fund prices (`engine/ledger.py:157–214`); a zero-capex SaaS option
can be a real candidate, while training coverage zero is excluded. Clear-action matching
also rejects zero-cost training (`ledger.py:253–255`). **NEW** supported command effects,
generated asset IDs, actual charges and this price lookup must agree; a new free/subsidized
training response cannot simply masquerade as the existing training action. Remaining
funds are already net of committed spend (`ledger.py:217–229`), so do not deduct twice.

## Minimal additions and dispatch constraints

The smallest coherent **NEW** runtime content package contains: (1) one-time catalog/
platform-reference estate; (2) missing capability throughput and platform supply/life/
availability data; (3) explicit driver mapping and integration visibility; (4) real units,
rollout parameters, communication/hiring options and placement load; (5) eligible governance
identities and primary mappings; (6) typed non-policy preference interpretation/caring sets;
(7) accounting inputs and event-response/state-effect dispositions. Existing prices, roles,
entities, populations, strategy weights and policy ideals should be referenced, not duplicated.

Schema additions also need loader registration/optional legacy behavior, cross-reference
validation, finite/range checks, label homes and provenance; arbitrary YAML under a new
filename will not be loaded by today's fixed section loader (`casepack/loader.py:26–41,
85–111`). A runtime section may be optional for historical fixtures, but a decision-driven
game must fail clearly when its required runtime inputs are absent. Missing coefficients
block the dependent transition implementation; no builder should tune until a pin matches.

[V] All four historic archetypes use cost leadership and inject per-round estates
(`archetype_base.py:155–169`; the four archetype classes). M1 scenario authoring must select
actual priced/configured options across `cost_leadership`, `differentiation`,
`customer_supplier_intimacy`, `focus_strategy`; preserve the old fixtures as independent
scorer evidence. In particular the old overspender's arbitrary 20,000 response lines and
the all-tech archetype's endlessly fresh nodes are not legal purchase plans. No ranking
or balance conclusion follows from this content research.

## Local reproduction

Run at the inspected base from `backend/`; no state or external services are used:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 - <<'PY'
from pathlib import Path
from app.casepack.loader import load_casepack
p = load_casepack(Path('packs/riverside_grocery'))
cat = {i.key: i for i in p.catalog}
plat = {s.key: s for s in p.platform.services}
ci = ['pos_system_2011', 'order_mgmt_v42', 'accounting_package',
      'store_spreadsheets', 'order_db_cluster', 'store_back_office_pc']
si = ['client_network', 'compute_pool', 'storage_pool', 'backup_recovery']
print('candidate recurring', sum(cat[k].deployment_modes['on_prem'].opex for k in ci)
      + sum(plat[k].placement_options['on_prem'].opex for k in si))
print('candidate load', round(sum(cat[k].staff_load for k in ci)
      + sum(plat[k].staff_load for k in si), 6))
print('catalog', len(p.catalog), sum(len(i.deployment_modes) for i in p.catalog))
print('platform', len(p.platform.services),
      sum(len(i.placement_options) for i in p.platform.services))
print('process options', sum(i.process_option is not None for i in p.catalog))
for c in p.capabilities:
    owned = {e.entity for i in p.catalog if c.key in i.serves for e in i.owns_entities}
    print(c.key, [r.entity for r in c.required_entities if r.entity not in owned])
PY
```

Observed: recurring `14200`; load `3.3`; catalog `14 42`; platform `11 33`; process options
`9`. Missing catalog entities: customer_insight `['sale']`; marketing_sales
`['product', 'customer']`; firm_infrastructure `['user_account']`; other capabilities `[]`.
The last gap has an existing platform owner as noted above; this probe does not claim
catalog union is the complete intended integration model.
