# 1.5 Contract-Completion — Build Spec

**Authored under** `SPEC_PROTOCOL.md` v1.3 · **Author:** integration agent (spec author) · **Date:** 2026-08-22
**Role:** contract-completion prerequisite to module 1.5 — makes 1.5 spec v1.2 executable. **Not the engine build.**
**Phase:** 1 · **Depends on:** 1.5 readiness closeout (merged `caece53`) · 1.4 (the pin) · **Blocks:** the 1.5 engine build
**Independent spec review** *(SPEC_PROTOCOL §11, before dispatch)*: **pending** — required before a 1.5 engine builder is dispatched.
**Base:** `main` @ `de1af03` (clean tree; readiness audit PASS, merged `caece53`).

> **Scope discipline.** This packet **defines interfaces**; it implements nothing. No metric
> body, ledger processing, event firing, blast-radius change, duration calculation, seed
> history, persistence, or UI is written here. It freezes the contracts the 1.5 engine
> builder found undefined at pre-flight row 11, and amends 1.5 v1.2 only by cross-reference.

---

## 0. Spec Basis

**Read in full:** the dispatch prompt (`handoffs/_prompts/1.5-contract-completion.txt`);
`GOVERNANCE.md` v1.3, `QUALITY_PROTOCOL.md` v1.4, `SPEC_PROTOCOL.md` v1.3, `CONTRACTS.md`;
`handoffs/1.5-event-signal-engine/{spec.md v1.2, readiness-spec.md, readiness-dod.md}`;
`handoffs/1.4-scoring-engine/{spec.md, closeout-spec.md}`; `handoffs/1.6-round-runner/spec.md`;
`backend/app/engine/{state,graph,technology,management,score,organisation}.py`;
`backend/app/casepack/models.py`; `backend/seeds/riverside_r3.py`; `backend/app/seed/demo.py`;
the full Riverside pack (events, watch_rules, obligation_rules, policies, catalog, platform,
capabilities, pack.yaml); `backend/tests/test_engine_scoring.py`.

**Extraction sufficiency:** covered. Every field, value, and threshold cited below carries a
`file:line`; every quantity with no source is marked **NEW** and decided in place, per the
`SPEC_PROTOCOL §4.3` / dispatch quality bar.

**Method note.** State/pack/design facts were mapped by three independent read-only passes and
every load-bearing number re-cited against the working tree before freezing.

---

## 0.5 STOP register — decisions surfaced, not silently reconciled *(GOVERNANCE §7)*

Six items where reality diverges from the dispatch prompt or the 1.5 spec, or where a change
is unowned by this packet. Each is resolved to a **compliant route** where the spec author has
authority, or escalated where it needs a ruling. **None was guessed.**

| # | Conflict | Resolution in this spec | Needs a ruling? |
|---|---|---|---|
| **S1** | **`capacity_utilisation` pins unreachable.** 1.5 §5.5/§8 pin `ord_cap_01` at `0.83` (R2) / `1.11` (R3), but the frozen 1.4 tech pin fixes `order_app` throughput at `7225.0` (`riverside_r3.py:48`); with R3 demand `12000` the formula (§4.1) yields `1.661`, not `1.11` — and I cannot change `7225` without breaking the 1.4 tech pin `0.750008` (`test_engine_scoring.py:34`, frozen to 1e-6, closeout invariant C1). | **Formula frozen (§4.1). The exact R2/R3 history numbers are calibration** (owned by **1.7**) and the seed author; 1.5 §5.5's `0.83`/`1.11` are re-marked illustrative-not-reproduced (amendment A2). The 1.4 arithmetic is untouched. | No — author authority; recorded for the auditor. |
| **S2** | **`saturday_queue_collapse` does not exist** in `events.yaml` or anywhere in the deck — only in spec prose (`1.5 spec.md:324,390`; `1.1 spec.md:230`). The two-path demonstration references a phantom event. | **Rebind the demonstration to a real event: `warehouse_rollout_gap`** (fires on `wh_rollout_01` critical presence; suppressible by clearing via `add_training`) — §10.3. Authoring `saturday_queue_collapse` as new content is **assigned to the pack-content owner (1.3), optional**, register item. | No — author authority; but see S2-note. |
| **S3** | **`Event` has no `capability` field and no `repeatable` field** (`models.py:386-394`), yet O2 (per-capability cap) and §5.2 ("unless repeatable") depend on both. | **`capability` is DERIVED, not authored** (§7.1): the event's capability set = the capabilities of the watch rules named by its `signal_open` preconditions. **`repeatable` defaults to fire-once with no schema field** (§7.2); authored repetition, if ever wanted, is a NEW `Event.repeatable: bool = False` **assigned to 1.1** — not needed by Riverside. | No — author authority. |
| **S4** | **`base_rto`, `no_failover_multiplier`, `staffing_modifier`, and the `availability_shortfall` "agreed availability" target do not exist** — zero fields, zero values (§4.4, §8). | Contracts defined (§8). Three are **NEW schema/constant items assigned to owners:** `catalog.base_rto_hours` → **1.1** (default provided); `agreed_availability` per capability → **1.1** (default `0.99`); `no_failover_multiplier` + `staffing_modifier` coefficients → **engine constants, NEW, decided here**, calibration owned by **1.7**. | Partly — the two **schema additions gate only the duration/availability paths**, not the metric/signal/precondition core. Register items. |
| **S5** | **`debt_above` needs a debt quantity `TeamState` does not carry** — the debt ledger is 1.6's (`1.6 spec.md:103`). 1.5 cannot compute it. | Formula frozen against a **NEW snapshot input `TeamState.debt_ratio_by_capability`** supplied by **1.6**; until then `debt_above` is **unreachable** (no Riverside event uses it — all 13 use `signal_open`). Register item, owner 1.6. | No — author authority; unreachable in v1. |
| **S6** | **The dispatch prompt cites stale 1.4 pins** (`mgmt 0.648` / `realised 0.246`). | **Corrected to the live pins:** `tech 0.750008 · org 0.507003 · mgmt 0.656778 · realised 0.249744 · throttle org` (`test_engine_scoring.py:34-41`). `0.648`/`0.246` are the superseded pre-closeout baselines (`1.4 spec.md:257`). | No — correction. |

> **S2-note.** Rebinding the demonstration is author authority; but if the user wants
> `saturday_queue_collapse` as real content (its persona/body/outcomes), that is pack-content
> authoring (role 1.3), out of scope here, and is registered with owner 1.3.

---

## 1. Purpose and scope

**In scope — freeze the contracts 1.5 v1.2 references but never defines:** the five metric
function signatures + bodies (as *specification*, not code); the signal-ledger object, episode
identity, `lead_time`, actionability and clearing-price lookup; runtime semantics for all
eleven precondition shapes; event→capability attribution, repetition, suppression, and the
`arms`↔`preconditions` relationship; blast-radius node selection, `failover_exists`, and the
outage-duration formula with its NEW constants; the state-object field additions and where each
belongs; the seed-history contract; a preflight and DoD; CONTRACTS entries; register ownership;
and builder + auditor prompts.

**Out of scope:** implementing any of the above; persistence, round evolution, re-score
application (1.6); UI (4.3); authoring new pack content (1.3).

---

## 2. Project-specific statements *(SPEC_PROTOCOL §9)*

**Scoring factors touched:** defines the *inputs* to signal responsiveness (`design/02 §C`)
that 1.4 consumes; changes no scorer. **Casepack keys read** (by the engine this unblocks):
`watch_rules`, `events`, `obligation_rules`, `policies`, `capabilities`, `catalog`, `platform`.
**Casepack-identity branching:** none (engine I1). **Instance scoping:** N/A — pure contract,
no runtime table (engine is pure, I2). **Business-language check:** contracts name machine keys
only; no student-facing English (engine I3).

---

## 3. Settled decisions (author authority)

1. **Metric signature is frozen:** `metric(state: TeamState, pack: Casepack, rule: WatchRule) -> float | bool`. The rule supplies the capability and thresholds. Metrics are pure and read the **round-close snapshot before event outcomes are applied** (watch rules precede events — `1.6 spec.md:109` steps 10 then 11).
2. **A `METRICS` registry** maps the five frozen keys to functions. An **unknown key raises `UnknownMetricError(key)`** (a NEW named exception) — never evaluates false (`1.5 spec.md:110`).
3. **Threshold comparison is strict `>`** (`1.5 spec.md:167-171`): a value exactly at a threshold does **not** raise. Applies to every threshold metric and every `ratio`/`count` precondition.
4. **A metric measuring a property of an existing serving path returns `0.0` (no raise) when the capability has no serving path or non-positive capacity.** "No path" is a coverage failure scored by 1.4 / caught by the validator — it is not an operational watch signal. Applies uniformly to `capacity_utilisation`, `availability_shortfall`, `data_coverage_gap`.
5. **Stored metric `value` is rounded to 4 decimal places**; comparisons run on the unrounded float. (Enough precision for the 2-dp thresholds; deterministic.)
6. **Event capability is derived, never authored** (§7.1). **Events are fire-once by default** (§7.2).
7. **The rich ledger is 1.5's snapshot output; the 4-field `SignalState` the 1.4 scorer reads is a frozen projection of it** (§5.4), so the 1.4 pin is preserved by construction.

---

## 4. Metric contracts

Each metric: **definition**, **compliant route** (formula against cited state), **rejected
alternative**, **edge cases**, **falsification check** (a planted input that must flip the
output — `SPEC_PROTOCOL §4.3`).

### 4.1 `capacity_utilisation` (threshold → float)
- **Definition:** load on the capability's scarcest resource. `utilisation = demand ÷ capacity`.
- **Compliant route:** `demand = capability.demand_curve[state.round - 1]` (`models.py:171`); `capacity = graph.bottleneck_capacity(state, serving_path(capability))` (`graph.py:113`, the min node `throughput` on the serving path). Rules: `ord_cap_01`, `store_cap_01`, `mkt_channel_01`, `svc_backlog_01`.
- **Rejected alternative:** reuse 1.4's `capacity` sub-factor `min(1, capacity÷demand)` (`1.5 spec.md:99`) — rejected: it is clipped to `[0,1]` and inverted, so it can never express the over-saturation (`1.11 > 0.95`) the ledger example requires. The watch metric is the **raw, unclipped** `demand÷capacity`; the two are deliberately different quantities.
- **Edge cases:** zero demand → `0.0`. No serving path / `bottleneck_capacity` is `None` / capacity `<= 0` → `0.0` (decision 4). Otherwise `round(demand/capacity, 4)`.
- **Pin (S1):** with the frozen `order_app` throughput `7225.0`, R3 demand `12000` → `1.6609`. The 1.5 spec's illustrative `1.11` is **not reproduced** and is deferred to 1.7 calibration; the formula is the contract.
- **Falsify:** hold capacity fixed, set demand above `capacity × critical_above` → must raise CRITICAL; set demand to `0` → must return `0.0` and not raise.

### 4.2 `rollout_without_support` (presence → bool)
- **Definition:** a live rollout of the capability that nobody was trained for and no process was changed for.
- **Compliant route:** `TRUE` iff **any** deployment serving the capability (`state.deployments_serving(capability)`, `state.py:196`) has `initiated and not abandoned and trained_count == 0 and process == "unchanged"` (`state.py:58-79`). Rule: `wh_rollout_01`; Riverside `dep_centraline` (`trained_count 0`, `process unchanged`, `riverside_r3.py:152`) → `TRUE`. ✓
- **Rejected alternative:** require training **and** process **and** communication all absent — rejected: **no communication field exists in engine state** (confirmed); a predicate cannot read a field the state does not carry. Communication is registered as a **1.6/schema gap** (§9) rather than silently dropped or invented.
- **Edge cases:** capability with **no deployment** → `FALSE` (nothing rolled out is a coverage issue, not "rollout without support"). Abandoned deployments are excluded.
- **Falsify:** flip `dep_centraline.trained_count` to non-zero **and** `process` to `redesigned` → must return `FALSE`.

### 4.3 `missing_identity_access` (presence → bool)
- **Definition:** no live node provides central sign-on for the firm.
- **Compliant route:** `TRUE` iff **no** node in `state.nodes` fills the `identity_access` role (`"identity_access" not in any node.roles_filled`; the role is authored — `labels.yaml:36` "Central sign-on"). Rule: `sec_identity_01`, capability `firm_infrastructure`.
- **Rejected alternative:** model per-account provisioning — rejected: **no account/identity state exists**, and the prompt warns against conflating a filled role with account ownership. The metric is scoped explicitly to **role presence** (the only grounded signal); per-account provisioning is out of scope and, if ever needed, is a schema addition (§9). Documenting the scope is how the conflation is avoided.
- **Edge cases:** empty node set → `TRUE` (no node ⇒ no identity node).
- **Falsify:** add a node with `roles_filled=("identity_access",)` → must return `FALSE`.

### 4.4 `availability_shortfall` (threshold → float)
- **Definition:** how far realised availability falls below the agreed target for the capability. `shortfall = max(0.0, agreed_availability − realised_availability)`.
- **Compliant route:** `realised = graph.path_reliability(state, serving_path(capability))` (`graph.py:101`, product of node availabilities). `agreed_availability` is a **NEW per-capability authored field (S4)** — `Capability.agreed_availability: float`, owner **1.1**, **default `0.99`** when absent so existing packs load; exact per-capability values marked `TODO: calibrate` (1.7). Rule: `fin_close_01` (`financial_reporting`, `warn 0.02 / crit 0.05`).
- **Rejected alternative:** an engine-wide constant SLA — rejected: `financial_reporting`'s close window and a marketing site have different agreed availabilities; the target is per-capability content, so it belongs in the pack, not a constant.
- **Edge cases:** no serving path → `0.0` (decision 4). `round(shortfall, 4)`.
- **Falsify:** set every node availability on the path to `1.0` → shortfall `0.0`, no raise; drop one node's availability so `agreed − realised > critical_above` → CRITICAL.

### 4.5 `data_coverage_gap` (threshold → float)
- **Definition:** the share of the capability's required entity-levels it cannot see. `gap = unmet_required ÷ total_required`.
- **Compliant route:** for each `RequiredEntity(entity, min_level_of_detail)` on the capability (`models.py`), it is **met** iff some node owns that entity at a level `>=` the required level (`graph.owner_nodes` + `graph._level_ok`, `graph.py:60,68`; ordinal per `CONTRACTS.md` `entity.level_of_detail`). `gap = (count unmet) / (count required)`. Rule: `cust_data_01` (`customer_insight`, `warn 0.30 / crit 0.60`).
- **Rejected alternative:** define `gap = 1 − data_adequacy` (1.4's sub-factor) — rejected: `data_adequacy` folds in a multi-owner-no-integration **penalty** (`1.5 spec.md:101`) that is a scoring nuance, not a coverage count; the gap metric is a clean coverage ratio and must not inherit the penalty.
- **Edge cases:** zero required entities → `0.0`. No path → `0.0` (decision 4). `round(gap, 4)`.
- **Falsify:** remove the node owning `customer` at household level → gap rises above `critical_above` → CRITICAL; restore it → `0.0`.

### 4.6 Registry and unknown keys
`METRICS = {"capacity_utilisation": …, "rollout_without_support": …, "missing_identity_access": …, "availability_shortfall": …, "data_coverage_gap": …}`. `evaluate(rule, state, pack)` looks up `METRICS[rule.metric]`; a missing key raises `UnknownMetricError(rule.metric)` (**never** returns `False`). **Falsify:** a rule with `metric: not_a_metric` must raise, not silently pass.

---

## 5. Signal ledger contract

### 5.1 The ledger object (NEW: `LedgerSignal`, frozen dataclass)
Fields (the shape 1.4 consumes, `1.5 spec.md:135-141`, plus `episode_id` for recurrence):
`key · episode_id: int · capability · metric · metric_kind · value: float · severity: Literal["warning","critical"] · status: Literal["open","cleared","fired"] · first_shown_round: int · cleared_round: int | None · fire_round: int | None · cleared_by: tuple[str, ...] · was_actionable: bool · cheapest_fix_when_raised: int | None`.

### 5.2 Lifecycle, immutability, episodes
- **Immutable history in, pure result out.** The engine takes the prior ledger (immutable) + the current snapshot and returns a new ledger; it never mutates a prior row.
- **Episode identity:** `(key, episode_id)`. A re-raise of a previously-cleared condition opens `episode_id + 1`; a cleared or fired episode is **never overwritten** (`1.5 spec.md:105-106`). 1.4 counts each episode independently.
- **Raise/escalate/clear/fire** per `1.5 spec.md:121-131`. **No de-escalation** (`spec.md:188`). **Same-round raise+clear** → `lead_time = 0` (O5).
- **`status`:** `fired` iff `fire_round` set and no clear landed on-or-before it; `cleared` iff `cleared_round <= fire_round` (or fire never occurred); else `open`.

### 5.3 `lead_time`, timestamps
- `lead_time = cleared_round − first_shown_round`. **`cleared_round` is the round the resolving action was locked** — this reconciles `design/02:62`'s responsiveness pair `(first_shown_round, decision.locked_round)` with the ledger's `cleared_round`: they are the same round. Clearing after `fire_round` records `cleared_round`/`lead_time` for the causal trace but earns **no responsiveness credit** (O3).

### 5.4 The `SignalState` projection (preserves the 1.4 pin)
The 1.5 engine outputs `tuple[LedgerSignal, ...]`. The 1.4 scorer reads the existing 4-field
`SignalState(key, capability, actionable, acted_before_fire)` (`state.py:104-109`). Freeze the
projection: `actionable = was_actionable`; `acted_before_fire = (cleared_round is not None and fire_round is not None and cleared_round <= fire_round)`. **Compatibility gate:** projecting the seeded R1–R3 history must reproduce the three `SignalState` values the seed hand-builds today (`ord_cap_01` actionable+acted; `wh_rollout_01`, `sec_identity_01` actionable, not-acted — `riverside_r3.py:193-199`), so the 1.4 pin is byte-identical.

### 5.5 Actionability and clearing-price lookup (O1)
- `cheapest_fix_when_raised` = the **minimum cost, at the raise round, among pack options that perform any `cleared_by` action type for the signal's capability.** Action-type → priced-candidate mapping (NEW, `cleared_by` action keys carry no price themselves — `checks.py ACTION_TYPES`):
  - `scale_node`/`add_node`/`move_to_cloud`/`upgrade_component` → cheapest `catalog` `deployment_modes[*].capex` among items serving the capability (`models.py` `CatalogItem`).
  - `add_training` → cheapest `catalog.training_options[*].cost` for the capability.
  - `add_service_tier` → cheapest `platform.support_tiers[*].cost` / integration tier.
  - `add_policy` → the `policies[*].cost` of the relevant switch.
  - `redesign_process` → `catalog.process_option.cost`; `retire_component`/`fund_response` → `0` (no purchase) or the event option `cost`.
- **`was_actionable` = TRUE iff `cheapest_fix_when_raised <= available_funds` in ANY round the signal was open** ("affordability changes while open"). `available_funds` per round is a **NEW snapshot input** (from `pack.budget.capex_per_round` / 1.6 round state, §9).
- **Ties:** `min` is well-defined (equal costs collapse). **No candidates:** `cheapest_fix_when_raised = None`, `was_actionable = False`, and the signal is **excluded from the responsiveness denominator** (O1).
- **Falsify:** set `available_funds` below the cheapest fix in every open round → `was_actionable = False`; raise it in one open round → `True`.

---

## 6. Precondition runtime semantics (all eleven)

Boundary direction, empty/missing, and invalid-input behaviour, frozen per type. **Riverside
uses only `signal_open`**; the other ten ship with a positive + negative + boundary test each.

| Type | Runtime truth (frozen) | Boundary | Empty/missing |
|---|---|---|---|
| `signal_open` | an open (not cleared, not fired) `LedgerSignal` for `signal` whose `severity >= required` — **severity is a floor, not exact** (`warning` matches an escalated `critical`) | ≥ on the `warning < critical` order | no such signal → FALSE |
| `demand_exceeds_capacity` | `capacity_utilisation(capability) > ratio` | strict `>` | no path → `0.0` (decision 4) → FALSE |
| `adoption_below` | `primary_deployment(capability).adoption < ratio` (`state.py:74,199`) | strict `<` | no deployment → FALSE |
| `staffing_over` | `state.staff.load_fte / state.staff.staff_fte > ratio` (`state.py:96`) | strict `>` | `staff_fte == 0` → TRUE (any load over zero capacity is over) |
| `debt_above` | `TeamState.debt_ratio_by_capability[capability] > ratio` — **NEW input, owner 1.6 (S5); unreachable in v1** | strict `>` | input absent → raises `MissingRoundInputError` (never silently FALSE) |
| `node_is_spof` | `node in graph.articulation_points(state)` over the **whole graph** (`graph.py:127`) — a SPOF is a SPOF firm-wide; per-path SPOF is `spofs_on_path`, not this | — | unknown node key → FALSE |
| `entity_unowned` | no node in `state.nodes` has `entity` in its `owns_entities` at **any** level (`state.py:44`) | — | entity owned by ≥1 node → FALSE |
| `placement_count` | count of `ArchNode`s whose placement == `placement` `>= count` — **requires NEW `ArchNode.placement` snapshot field (S4/§9)**; never store derived `hybrid` (`CONTRACTS.md placement`) | `>=` on `count` | field absent → raises `MissingRoundInputError` |
| `policy_contradiction` | the resolved ordinal index of `policy` and `other_policy` (via `PolicyDecisionState`, default-resolved) are **on opposite sides of their midpoints** — one permissive, one restrictive (exact test §6.1) | — | either policy unresolved → raises (per `PolicyDecisionState` null path) |
| `sponsor_unassigned` | `not state.governance_for(capability).sponsor_assigned` (`state.py:92,211`) | — | no governance row → TRUE (unsponsored) |
| `round_equals` | `state.round == round` | `==` | — |

### 6.1 `policy_contradiction` exact test
Let `i(p)` = the ordinal index of policy `p`'s resolved selection in its `options` list
(permissive = index 0; `CONTRACTS.md PolicyOption.options`), resolved through `PolicyDecisionState`
(default when not actively decided). Let `n(p) = len(options) − 1`. The precondition is TRUE iff
the two switches sit on **opposite halves**: `(i(policy) / n(policy) < 0.5) != (i(other_policy) / n(other_policy) < 0.5)` — one permissive, one restrictive. **Rejected alternative:** "indices unequal" — rejected: two adjacent restrictive positions are not a contradiction; opposite-halves is the defensible reading of "contradiction." **Falsify:** set both switches permissive → FALSE; move one to its most-restrictive option → TRUE.

### 6.2 Conjunction
`Event.preconditions` is a flat **AND** list (`1.5 spec.md:195`). No OR/grouping in v1; an event
needing disjunction authors two events. A multi-precondition event's capability set is the union
of its `signal_open` capabilities (§7.1).

---

## 7. Event ownership, repetition, suppression, arms

### 7.1 Event → capability attribution (O2) — derived
An event's **capability set** = `{ watch_rule(pc.signal).capability for pc in preconditions if pc.type == "signal_open" }` (resolve each `signal` to its `WatchRule.capability`, `models.py:311`). O2's "at most two events per capability per round" applies to **each** capability in the set. An event with no `signal_open` precondition (none in Riverside) has an **empty** capability set and is O2-exempt (recorded). **Rejected alternative:** add `Event.capability` to the schema — rejected: it duplicates a fact the preconditions already determine and could contradict them; derivation is single-source. **Falsify:** three satisfiable events all resolving to `order_fulfilment` → exactly two fire, the third is suppressed and logged (I7).

### 7.2 Repetition
Events are **fire-once**: an event with an episode already `fired` in history does not re-fire.
Dedupe key: `event.key`. No `repeatable` field is added in v1 (Riverside needs none). **If** authored repetition is later required, it is a NEW `Event.repeatable: bool = False`, **owner 1.1** (§9) — and a repeatable event re-fires only on a **new signal episode** (§5.2), never on the same open episode.

### 7.3 Suppression record
When O2 or fire-once suppresses a satisfiable event, record `(event.key, round, reason ∈ {"cap","already_fired"}, capability)` in **authored deck order** (`1.5 spec.md:94`), deterministically.

### 7.4 `arms` vs `preconditions`
An obligation's `arms` list is an **additional gate, not a replacement**: an armed event fires
only when **both** its own `preconditions` are true **and** at least one obligation naming it in
`arms` is **open** (`ObligationRule` on the presence path, `models.py:397`). Multiple obligations
arming one event combine by **OR** (any one open arms it). **Rejected alternative:** `arms`
replaces preconditions — rejected: it would let an event with unmet preconditions fire, breaking
I5 reachability and the "every event has a precedent signal" rule. **Falsify:** open the arming
obligation but leave the event's precondition false → event does **not** fire; make both true →
fires.

---

## 8. Blast radius and outage duration

### 8.1 Blast radius (derivation exists; input binding is the gap)
`graph.blast_radius(state, node_key, capabilities, primary)` is built (`graph.py:180`); I6 forbids
authoring the result. **The gap is which node an event removes.** Freeze: the failed node is the
event's **bound node** — for a `node_is_spof` precondition, that `node`; otherwise the **bottleneck
node** of the primary capability's serving path (`graph.bottleneck_capacity`'s min-throughput node).
The seed's "WAN link" example (`wan_link`, `riverside_r3.py`) is one such bound node. **Never author
the radius** (I6). **Failed-object model:** the helper removes a **node**; `ArchEdge` objects also
exist, but v1 blast radius removes nodes only — edge failure is registered as a future extension
(§9), not implemented.

### 8.2 `failover_exists`
TRUE iff, after removing the failed node, the affected capability still has a serving path that
traverses a `"failover"`-kind edge (`EdgeKind`, `state.py:24`) — i.e. a surviving path exists
**because of** a failover edge. **Rejected alternative:** "any surviving path" — rejected: that is
just an empty blast radius; `failover_exists` specifically asks whether **redundancy** saved it, which
is what the duration multiplier rewards. **Falsify:** add a `failover` edge giving an alternate path
→ TRUE and duration multiplier `1.0`; remove it → FALSE and multiplier `no_failover_multiplier`.

### 8.3 Duration formula and NEW constants
`duration_hours = round(base_rto_hours(node) × failover_factor × staffing_modifier, 1)` where:
- **`base_rto_hours(node)`** = the failed node's catalog item's `base_rto_hours` — **NEW `CatalogItem.base_rto_hours: float`, owner 1.1**, `TODO: calibrate` (1.7); engine default `8.0` hours if absent.
- **`failover_factor`** = `1.0` if `failover_exists` else **`no_failover_multiplier`** — **NEW engine constant = `3.0`** (decided; `TODO: calibrate` 1.7).
- **`staffing_modifier`** (G1: "over-commitment degrades incident recovery time", `design/04:33-39`, effect direction only, no formula) — **NEW formula:** `1.0 + max(0.0, load_fte/staff_fte − 1.0)`, i.e. every 100% over-commitment adds one whole recovery-time again. Riverside `load 3.4 / staff 2.0 = 1.70` → modifier `1.70`. `staff_fte == 0` → a NEW `UNDERSTAFFED_MULTIPLIER = 4.0` (no one to fix it). **Rejected alternative:** a step function (penalty only past a threshold) — rejected: G1 says degradation is continuous with over-commitment; linear is the minimal faithful form. **Falsify:** set `load == staff` → modifier `1.0`; double the load → modifier `2.0`.
- **Rounding:** duration to 1 decimal (hours). Result/evidence shape: `{node, base_rto_hours, failover_exists, failover_factor, staffing_modifier, duration_hours, blast_radius: [...]}`.

---

## 9. State/field ownership — snapshot vs round vs persistence vs schema

Every new field the contracts above require, and where it belongs (the dispatch prompt's central
classification). **Snapshot (1.5)** items are produced by the 1.5 engine as pure outputs. Others
gate specific engine paths and are **registered with named owners** (`GOVERNANCE §9`).

| Item | Belongs to | Gates |
|---|---|---|
| `LedgerSignal` object; the five metric bodies; raise/escalate/clear/fire; `lead_time`; `was_actionable`/`cheapest_fix_when_raised`; event firing + O2 + suppression; blast-radius node binding; `failover_exists`; `duration_hours`; the `SignalState` projection | **1.5 snapshot (this unblocks)** | the engine build |
| `TeamState.available_funds_by_round` (O1 affordability input) | **1.6 round** → 1.5 takes it as input | actionability |
| `TeamState.debt_ratio_by_capability` (S5) | **1.6 round** | `debt_above` only (unreachable in v1) |
| `ArchNode.placement` (S4) | **1.6/1.1** — runtime placement from the deployed item; never store `hybrid` | `placement_count` only (unused by Riverside) |
| Ledger/RoundResult **persistence**, `instance_id`, re-score application | **1.6 / 2.x** | round runner |
| `CatalogItem.base_rto_hours` (S4) | **1.1 schema** (+ 1.2 validation) | duration only |
| `Capability.agreed_availability` (S4, default 0.99) | **1.1 schema** | `availability_shortfall` only |
| `Event.repeatable` (S3, only if repetition wanted) | **1.1 schema** | repetition only; not needed by Riverside |
| a "communication" rollout field (§4.2) | **1.1/1.6 gap, registered** | a richer `rollout_without_support` (v1 uses training+process) |

**The metric/signal/precondition/event/blast-radius core needs no schema change** — it runs on
existing state plus `agreed_availability` (defaulted) and the two duration constants. The four
schema additions gate only the availability and duration paths and are sequenced behind 1.1/1.2.

---

## 10. Seed and compatibility

### 10.1 `--with-signals` (NEW flag)
`python -m app.seed.demo --scenario riverside_r3 --with-signals` does **not exist** today
(`demo.py` defines only `--scenario`). It is **NEW**, added by the 1.5 build: it seeds R1–R3
`LedgerSignal` history and demonstrates the two paths. The bare `--scenario riverside_r3` command
and its 1.4 pin are unchanged.

### 10.2 1.4 pin preservation
Adding `signals`-derived history and any defaulted field must leave `test_engine_scoring.py`
byte-identical: `tech 0.750008 · org 0.507003 · mgmt 0.656778 · realised 0.249744 · throttle org`
(1e-6), the SPOF list, and the determinism hash. The `SignalState` projection (§5.4) is the seam
that keeps `signal_responsiveness` — and thus the pin — stable.

### 10.3 The two-path demonstration (S2 rebind)
Demonstrate on **`warehouse_rollout_gap`** (fires on `wh_rollout_01` critical presence): on the
do-nothing path it fires at its round; on a path where `wh_rollout_01` was cleared (an
`add_training` action makes `rollout_without_support` false) it does **not** fire — the same card,
opposite outcomes, no authored branching. `saturday_queue_collapse` remains optional future
content (owner 1.3, register).

---

## 11. Invariants and their falsification checks *(each shown to fail — SPEC_PROTOCOL §4.3)*

| # | Invariant | Falsification check | Shown to fail on |
|---|---|---|---|
| CC1 | Unknown metric key raises `UnknownMetricError`, never returns false | evaluate a rule with `metric: nope` | a planted unknown key → must raise |
| CC2 | Threshold comparison is strict `>` | metric value == `critical_above` exactly | a value set equal to the threshold → must NOT raise |
| CC3 | No-serving-path metrics return 0.0, never divide-by-zero | capability with `nodes=(), edges=()` | planted empty graph → `0.0`, no exception |
| CC4 | `SignalState` projection reproduces the seed's hand-built values | project seeded R1–R3 history | compare to the three current `SignalState` rows → identical |
| CC5 | Event capability is derived, O2 caps per capability | 3 events resolving to one capability | third fires → must be suppressed+logged |
| CC6 | `arms` is an additional gate, not a replacement | armed obligation open, precondition false | event fires → must NOT fire |
| CC7 | 1.4 pin unchanged by any addition | run `make check` | `test_engine_scoring.py` drifts → must stay green |
| CC8 | No engine identity-branching / I/O / clock / randomness in the contracts | `git ls-files backend/app/engine \| xargs grep -niE "riverside\|grocer\|random\.\|datetime\.now"` | zero (a planted `if pack=="riverside"` → caught) |

---

## 12. Pre-Flight Verification Register (builder runs before writing engine code)

| # | Claim | Tag | Check | Expected |
|---|---|---|---|---|
| 1 | On `main` after this contract-spec merges; clean tree | `[V]` | `git rev-parse --verify main`; `git status --porcelain` | at the merge SHA; empty |
| 2 | 1.5 v1.2 pre-flight rows 1–10 pass at the current SHA | `[V]` | re-run 1.5 spec §7 rows 1–10 | all PASS |
| 3 | The five metric keys still absent from engine (greenfield) | `[V]` | `rg -n "capacity_utilisation\|rollout_without_support\|missing_identity_access\|availability_shortfall\|data_coverage_gap" backend/app/engine` | zero — row 11 still builder-owned |
| 4 | `LedgerSignal` / rich ledger absent | `[V]` | `grep -rn "LedgerSignal\|episode_id" backend/app/engine` | zero |
| 5 | 1.4 pin present and green | `[V]` | `cd backend && PYTHONPATH=. python3 -m pytest tests/test_engine_scoring.py -q` | pass; tech `0.750008`, org `0.507003`, mgmt `0.656778` |
| 6 | `make check` green at the base | `[V]` | `make check` | all guards green |
| 7 | Schema additions this contract assigns (S4) are landed **or** their paths are deferred | `[V]` | `grep -n "base_rto_hours\|agreed_availability" backend/app/casepack/models.py` | present → duration/availability in scope; absent → those paths STOP to 1.1 first |

Row 7 is the sequencing gate: the metric/signal/precondition/event/blast-radius core proceeds
regardless; the duration and availability-shortfall paths wait on 1.1.

---

## 13. Definition of Done (this contract packet)

| Item | Status | Evidence |
|---|---|---|
| All five metric contracts frozen with formula, edge cases, rejected alternative, falsification | | §4 |
| Signal ledger object, episode identity, lead_time, projection, actionability+price lookup | | §5 |
| Eleven precondition runtime semantics incl. boundaries and `policy_contradiction` test | | §6 |
| Event attribution, repetition, suppression, `arms` relationship | | §7 |
| Blast-radius node binding, `failover_exists`, duration formula + NEW constants | | §8 |
| Field-ownership table (snapshot/round/persistence/schema) | | §9 |
| Seed `--with-signals` contract; 1.4-pin preservation; two-path rebind | | §10 |
| STOP register — every conflict surfaced, resolved or escalated with owner | | §0.5 |
| CONTRACTS.md entries for every frozen cross-module interface | | separate commit, §14 |
| OPEN-REGISTER ownership for every deferral (S2 content, S4 schema, S5 debt, comms gap) | | separate commit |
| Builder + independent-auditor prompts | | `handoffs/_prompts/` |
| Independent spec review (SPEC_PROTOCOL §11) before dispatch | | **pending — gate** |
| Browser / auth / instance canaries | | **N-A** — pure contract packet |

---

## 14. CONTRACTS.md entries (added in the same change)

New/updated entries: **`WatchRule.metric` / the `METRICS` registry** (closed five-key vocabulary,
signature, unknown-raises); **`LedgerSignal`** (the ledger row + episode identity + `SignalState`
projection); **`signal.cleared_by[]` price lookup** (extends the existing PROSPECTIVE entry with
the action-type→cost mapping); **outage duration constants** (`base_rto_hours`, `no_failover_multiplier`,
`staffing_modifier`). Each carries producers/consumers and the "cite, never restate" rule.

---

## 15. Changelog

**v1.0 — 2026-08-22.** Contract-completion candidate authored under SPEC_PROTOCOL v1.3 against
`main @ de1af03`. Freezes the five metric bodies, the signal-ledger object and projection, all
eleven precondition semantics, event attribution/repetition/arms, and the blast-radius/duration
formula with NEW constants. Six conflicts recorded in the STOP register (§0.5), including the
`capacity_utilisation` pin vs the frozen 1.4 tech pin, the phantom `saturday_queue_collapse`, and
the stale pin numbers in the dispatch prompt. Requires independent audit before the 1.5 engine
builder is dispatched.
