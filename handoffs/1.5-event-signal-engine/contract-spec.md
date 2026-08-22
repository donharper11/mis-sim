# 1.5 Contract-Completion — Build Spec

**Authored under** `SPEC_PROTOCOL.md` v1.3 · **Author (v1.1 revision):** fresh spec author (not the v1.0 author, `GOVERNANCE §6.2`) · **Date:** 2026-08-22
**Role:** contract-completion prerequisite to module 1.5 — makes 1.5 spec v1.2 executable. **Not the engine build.**
**Phase:** 1 · **Depends on:** 1.5 readiness closeout (merged `caece53`) · the 1.1/1.2 **outage-schema prerequisite** (§9.1, sequenced before dispatch) · 1.4 (the pin) · **Blocks:** the 1.5 engine build
**Independent spec review** *(SPEC_PROTOCOL §11, before dispatch)*: **pending re-audit** — the v1.0 candidate failed audit (`findings/1.5-contract-completion-2026-08-22.md`, six Blocking + one Report); this v1.1 revision closes CC-A-001..007 and returns for independent re-audit before a 1.5 engine builder is dispatched.
**Base:** `main` @ `de1af03` (clean tree; readiness audit PASS, merged `caece53`).

> **Scope discipline.** This packet **defines interfaces**; it implements nothing. No metric
> body, ledger processing, event firing, blast-radius change, duration calculation, seed
> history, persistence, or UI is written here. It freezes the contracts the 1.5 engine
> builder found undefined at pre-flight row 11, and amends 1.5 v1.2 only by cross-reference.

---

## 0. Spec Basis

**Read in full:** the dispatch prompt — **now carried in this candidate's own tree** at
`handoffs/_prompts/1.5-contract-completion.txt` (CC-A-007; the v1.0 candidate cited a path
absent from its tree — the file lived only on the unmerged `build/1.5-event-signal-engine`
commit `2f68317`; its full authoritative text is restored to the tree here so the exact
candidate is self-contained and independently auditable with no cross-branch lookup);
`GOVERNANCE.md` v1.3, `QUALITY_PROTOCOL.md` v1.4, `SPEC_PROTOCOL.md` v1.3, `CONTRACTS.md`;
`handoffs/1.5-event-signal-engine/{spec.md v1.2, readiness-spec.md, readiness-dod.md}`;
the v1.0 audit `findings/1.5-contract-completion-2026-08-22.md`;
`handoffs/1.4-scoring-engine/{spec.md, closeout-spec.md}`; `handoffs/1.6-round-runner/spec.md`;
`backend/app/engine/{state,graph,technology,management,score,organisation}.py`;
`backend/app/casepack/{models.py, checks.py}`; `backend/seeds/riverside_r3.py`; `backend/app/seed/demo.py`;
`backend/tests/{test_engine_scoring.py, check_policy_options.py}`;
the full Riverside pack (events, watch_rules, obligation_rules, policies, catalog, platform,
capabilities, pack.yaml).

**Extraction sufficiency:** covered. Every field, value, and threshold cited below carries a
`file:line`; every quantity with no source is marked **NEW** and decided in place, per the
`SPEC_PROTOCOL §4.3` / dispatch quality bar.

**Method note.** State/pack/design facts were mapped by three independent read-only passes and
every load-bearing number re-cited against the working tree before freezing. **Dispatch-scope
provenance (CC-A-007):** the restored `1.5-contract-completion.txt` is byte-faithful to the
authoritative copy at commit `2f68317:handoffs/_prompts/1.5-contract-completion.txt`; that
commit is the immutable source of record for the original scope.

---

## 0.5 STOP register — decisions surfaced, not silently reconciled *(GOVERNANCE §7)*

Seven items where reality diverges from the dispatch prompt or the 1.5 spec, or where a change
is unowned by this packet. Each is resolved to a **compliant route** where the spec author has
authority, or escalated where it needs a ruling. **None was guessed.** S1/S2/S6 were verified
honest by the v1.0 audit and are unchanged; S4 is tightened and S7 is new in this v1.1 revision.

| # | Conflict | Resolution in this spec | Needs a ruling? |
|---|---|---|---|
| **S1** | **`capacity_utilisation` pins unreachable.** 1.5 §5.5/§8 pin `ord_cap_01` at `0.83` (R2) / `1.11` (R3), but the frozen 1.4 tech pin fixes `order_app` throughput at `7225.0` (`riverside_r3.py:48`); with R3 demand `12000` the formula (§4.1) yields `1.661`, not `1.11` — and I cannot change `7225` without breaking the 1.4 tech pin `0.750008` (`test_engine_scoring.py:34`, frozen to 1e-6, closeout invariant C1). | **Formula frozen (§4.1). The exact R2/R3 history numbers are calibration** (owned by **1.7**) and the seed author; 1.5 §5.5's `0.83`/`1.11` are re-marked illustrative-not-reproduced (amendment A2). The 1.4 arithmetic is untouched. | No — author authority; recorded for the auditor. |
| **S2** | **`saturday_queue_collapse` does not exist** in `events.yaml` or anywhere in the deck — only in spec prose (`1.5 spec.md:324,390`; `1.1 spec.md:230`). The two-path demonstration references a phantom event. | **Rebind the demonstration to a real event: `warehouse_rollout_gap`** (fires on `wh_rollout_01` critical presence; suppressible by clearing via `add_training`) — §10.3. Authoring `saturday_queue_collapse` as new content is **assigned to the pack-content owner (1.3), optional**, register item. | No — author authority; but see S2-note. |
| **S3** | **`Event` has no `capability` field and no `repeatable` field** (`models.py:386-394`), yet O2 (per-capability cap) and §5.2 ("unless repeatable") depend on both. | **`capability` is DERIVED, not authored** (§7.1): the event's capability set = the capabilities of the watch rules named by its `signal_open` preconditions. **`repeatable` defaults to fire-once with no schema field** (§7.2); authored repetition, if ever wanted, is a NEW `Event.repeatable: bool = False` **assigned to 1.1** — not needed by Riverside. | No — author authority. |
| **S4** | **`base_rto`, `no_failover_multiplier`, `staffing_modifier`, and the `availability_shortfall` "agreed availability" target do not exist** — zero fields, zero values (§4.4, §8). | Contracts defined (§8). `no_failover_multiplier` + `staffing_modifier` coefficients → **engine constants, NEW, decided here**, calibration owned by **1.7**. The two **schema fields** — `CatalogItem.base_rto_hours` and `Capability.agreed_availability` — are **NEW, owned by 1.1 (validation 1.2), and RECLASSIFIED in v1.1 from "deferred path" to a HARD prerequisite that lands and is independently audited BEFORE the 1.5 engine builder is dispatched** (§9.1). This closes the S7/CC-A-005 sequencing contradiction: with both fields present, all five metrics are buildable and there is no deferred-path escape. | No longer partial — the schema prerequisite is sequenced ahead of the build like the readiness closeout (§9.1). Register items `CC-D3`/`CC-D4` retagged **prerequisite, not optional**. |
| **S5** | **`debt_above` needs a debt quantity `TeamState` does not carry** — the debt ledger is 1.6's (`1.6 spec.md:103`). 1.5 cannot compute it. | Formula frozen against a **NEW snapshot input `TeamState.debt_ratio_by_capability`** supplied by **1.6**; until then `debt_above` is **unreachable** (no Riverside event uses it — all 13 use `signal_open`). Register item, owner 1.6. | No — author authority; unreachable in v1. |
| **S6** | **The dispatch prompt cites stale 1.4 pins** (`mgmt 0.648` / `realised 0.246`). | **Corrected to the live pins:** `tech 0.750008 · org 0.507003 · mgmt 0.656778 · realised 0.249744 · throttle org` (`test_engine_scoring.py:34-41`). `0.648`/`0.246` are the superseded pre-closeout baselines (`1.4 spec.md:257`). | No — correction. |
| **S7** *(new, v1.1)* | **The "all five metrics must exist before executable" rule (`1.5 spec.md:107-110`) contradicts deferring `availability_shortfall`'s schema.** The v1.0 candidate let pre-flight row 7 defer the availability path when `agreed_availability` was absent (`contract-spec §12 row 7`, `§9`), so a builder could not simultaneously implement all five required metrics and obey the sequencing STOP (audit **CC-A-005**). | **The all-five acceptance rule is KEPT unchanged; the sequencing is fixed instead.** The two schema fields (`base_rto_hours`, `agreed_availability`) become a **HARD 1.1/1.2 prerequisite sequenced before dispatch** (§9.1), exactly as the readiness closeout was. Pre-flight row 7 is rewritten from a deferral into a hard STOP: absent fields ⇒ the schema prerequisite has not merged ⇒ do not build. No deferred-path escape remains, and the "all five" rule is not touched (which would need the authority). | No — the preferred resolution the audit named is **author-authority sequencing**, not a change to the acceptance rule. Recorded for the auditor. |

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
- **`status` is a stored field the engine writes each round, computed as a total function of the episode's timestamps and whether its metric still raises at that round's close** (it is *not* re-derived from `(cleared_round, fire_round)` alone, because a lapse — metric false with no clearing action — clears the lifecycle without setting `cleared_round`, §5.5). The frozen decision procedure, evaluated in this order:

  ```
  status =
    "fired"   if fire_round is not None
               and not (cleared_round is not None and cleared_round <= fire_round)
    "cleared" elif (cleared_round is not None) or (the metric no longer raises at this close)
    "open"    else
  ```

  This is **total** (every episode falls in exactly one branch) and consistent with O3: a clear *after* fire (`cleared_round > fire_round`) leaves `status == "fired"` and earns no credit (§5.4), while a timely clear that lands on-or-before fire, or prevents fire entirely, yields `"cleared"`. A **lapse** (metric fell with no matching clearing action, §5.5) yields `"cleared"` with `cleared_round = None`, `cleared_by = ()` — a lifecycle clear that earns no responsiveness credit. The three-value vocabulary `{open, cleared, fired}` (`1.5 spec.md:139`) is preserved; no fourth status is invented.

### 5.3 `lead_time`, timestamps
- `lead_time = cleared_round − first_shown_round`. **`cleared_round` is the round the resolving action was locked** — this reconciles `design/02:62`'s responsiveness pair `(first_shown_round, decision.locked_round)` with the ledger's `cleared_round`: they are the same round. Clearing after `fire_round` records `cleared_round`/`lead_time` for the causal trace but earns **no responsiveness credit** (O3).

### 5.4 The `SignalState` projection (preserves the 1.4 pin) — **CORRECTED, CC-A-001**

The 1.5 engine outputs `tuple[LedgerSignal, ...]`. The 1.4 scorer reads the existing 4-field
`SignalState(key, capability, actionable, acted_before_fire)` (`state.py:104-109`) and counts
`acted_before_fire` in the responsiveness numerator over `actionable` signals
(`management.py:138-143`). Freeze the projection as **one total rule**:

```python
actionable        = was_actionable
acted_before_fire = (cleared_round is not None) and (fire_round is None or cleared_round <= fire_round)
```

**Why this rule and not the v1.0 rule (the defect CC-A-001 names).** The v1.0 projection required
*both* timestamps:
`acted_before_fire = (cleared_round is not None and fire_round is not None and cleared_round <= fire_round)`
(the v1.0 `§5.4` form; the `CONTRACTS.md` `LedgerSignal` entry is corrected to the rule above in the
same change). That gives **no credit to a timely clear that PREVENTS a fire** — the most responsive
outcome of all. `fire_round is None` is the *best* case (the student
acted so early the bill never arrived), yet the v1.0 rule scored it identical to never acting.
The corrected rule credits a clear whenever the episode was cleared **and** either it never fired
(`fire_round is None`) **or** the clear landed on-or-before the fire (`cleared_round <= fire_round`).
A clear *after* fire earns nothing (O3): `cleared_round is not None` but `fire_round is not None and
cleared_round > fire_round` ⇒ `False`. A never-cleared or lapsed signal (`cleared_round is None`)
earns nothing regardless of fire. The rule is **total** — it returns a boolean for every
`(cleared_round, fire_round)` pair in `{int, None} × {int, None}`.

**Compatibility gate — the explicit three-row projection (reproduces the pin byte-for-byte).**
The seed hand-builds three `SignalState` rows today (`riverside_r3.py:193-199`). The `--with-signals`
seed (§10) authors the R1–R3 `LedgerSignal` history whose timestamps project to exactly those rows:

| signal (episode) | `first_shown_round` | `cleared_round` | `fire_round` | `status` | projected `actionable` | projected `acted_before_fire` | seed row (`riverside_r3.py`) |
|---|---|---|---|---|---|---|---|
| `ord_cap_01` (ep 1) — a `scale_node` action clears it before any outage fires | 2 | **3** | **None** | `cleared` | `True` | `True` | `:196` `acted_before_fire=True` ✓ |
| `wh_rollout_01` (ep 1) — presence signal, un-acted, `warehouse_rollout_gap` fires | 3 | **None** | **3** | `fired` | `True` | `False` | `:197` `acted_before_fire=False` ✓ |
| `sec_identity_01` (ep 1) — presence signal, un-acted, still open at R3 | 3 | **None** | **None** | `open` | `True` | `False` | `:198` `acted_before_fire=False` ✓ |

All three have `was_actionable = True` (§5.5), so `actionable = True` for each, matching the seed's
three `actionable=True` rows. The numerator is `acted = 1` (`ord_cap_01` only); the denominator is
`3`; `signal_responsiveness = 1/3 = 0.333333` — **identical to the value the current hand-built seed
feeds `_signal_responsiveness` (`management.py:138-143`)**, which is what produces the frozen pins
`mgmt 0.656778 / realised 0.249744` (`test_engine_scoring.py:39-40`).

> **Falsification watched to fail (SPEC_PROTOCOL §4.3), run 2026-08-22.** Applying the **v1.0** rule
> to this same history yields `ord_cap_01 → False` (`cleared_round=3`, `fire_round=None`), so
> `acted = 0` and `signal_responsiveness = 0/3 = 0.0` — the pin drifts and `make check` FAILS. The
> **corrected** rule yields `acted = 1`, `0.333333`, pin green. The two rules differ **exactly** on
> the clear-before-fire row, which is the row the seed depends on. (Arithmetic reproduced by the
> three-line projection above; verified by direct computation.)

### 5.5 Action history, funds history, clearing, and the price lookup (O1) — **EXPANDED, CC-A-002**

The v1.0 candidate added only `available_funds_by_round` and defined no action-history object, so
the engine could not decide **which committed action clears which signal**, could count a
zero-effect option as a fix, and left "is committed spend already deducted?" open (audit CC-A-002).
This section freezes all four.

#### 5.5.1 The immutable ACTION history (NEW input object, `ActionRecord`)
A frozen dataclass, an append-only immutable snapshot input the 1.5 engine **reads, never writes**
(produced by 1.6 round evolution, §9; seeded for the demo by `--with-signals`, §10):

```python
@dataclass(frozen=True)
class ActionRecord:
    action_type: str          # one of checks.py ACTION_TYPES (the closed 10-key set)
    locked_round: int         # the round the team committed it — the responsiveness clock
    capability: str | None    # the capability the action targets; None = firm-wide (e.g. add_policy)
    target_key: str | None    # the exact catalog item / platform tier / policy / node acted on
    cost: int                 # capex actually committed for this action (>= 0)
```

Carried on `TeamState` as `action_history: tuple[ActionRecord, ...] = ()` (explicit default preserves
every existing constructor — no caller changes; consistency with the empty-tuple defaults already on
`stakeholder_alignments`/`policy_decisions`, `state.py:178-184`). **Immutable:** the engine never
mutates a record; round *r*'s history is a superset of round *r-1*'s.

#### 5.5.2 The funds history and whether committed spend is deducted (FROZEN)
`TeamState.available_funds_by_round: tuple[int, ...] = ()` — index *r-1* is the capital available to
the team **for new commitments in round *r*, after that round's already-committed spend is
subtracted**. **Committed spend IS already deducted**: the figure is *remaining* capital, matching
the pack's own authored derivation `capital_remaining = capital_available − capital_committed`
(`pack.yaml:39-40,99-101`; R3 = `220000 − 174000 = 46000`). So the affordability
test never double-counts a spend already made. Owner **1.6 round** (§9); the demo seed derives R1–R3
from `pack.metadata.budget.capex_per_round` (`pack.yaml:14`) minus each round's committed actions.

#### 5.5.3 Exact target matching — which committed action clears which signal (FROZEN)
An open episode of signal `s` (rule `R`, capability `C`) is **CLEARED by action** at round `r` iff,
at `r`'s close, the metric no longer raises **and** there exists an **effectful** `ActionRecord` `a`
(§5.5.4) with **all** of:
1. `a.action_type ∈ R.cleared_by` (`watch_rules.yaml`; e.g. `ord_cap_01.cleared_by = [scale_node, add_node, move_to_cloud]`);
2. `a.capability == C`, **or** `a.capability is None` **and** `C ∈ serves(a.target_key)` (a firm-wide
   action — e.g. `add_policy` — that touches an item serving `C`); and
3. `R.first_shown_round <= a.locked_round <= r` (the action was locked while the episode was open).

Then `cleared_round = min a.locked_round` over the matching records, and `cleared_by` = the tuple of
matching action types in `R.cleared_by` order. If the metric goes false at `r` with **no** matching
effectful action (a *lapse* — e.g. a future pack's demand curve falling; Riverside's demand curves
are monotonically increasing, `capabilities.yaml:275,284,…`, so this does not arise for Riverside),
the episode is recorded `status = "cleared"` with `cleared_round = None`, `cleared_by = ()` — a
lifecycle clear with **no** responsiveness credit (§5.4 projects it to `acted_before_fire = False`).
This makes clearing **total** and keeps responsiveness honest: only a team's own resolving action
earns credit. **Rejected alternative:** treat any metric-false round as a credited clear regardless
of whether the team acted — rejected, it credits luck (an exogenous demand drop) as responsiveness.

#### 5.5.4 Effectful-option filtering and the clearing-price lookup (FROZEN)
`cheapest_fix_when_raised` = the **minimum cost, at the raise round, among the pack options that
perform any `cleared_by` action type for `C` AND are EFFECTFUL** — i.e. performing the option would
actually move the metric toward not-raising. `cleared_by` action keys carry no price themselves
(`checks.py:13-24 ACTION_TYPES`); the action-type → priced-candidate mapping (NEW):

  - `scale_node`/`add_node`/`move_to_cloud`/`upgrade_component` → cheapest `deployment_modes[*].capex`
    among catalog items whose `serves` includes `C` (`CatalogItem`, `models.py:229-248`). Every
    deployment mode is effectful (it adds/scales/re-places a real serving node); a `saas` mode with
    `capex: 0` is effectful (zero *capex*, real *effect*) and IS a candidate.
  - `add_training` → cheapest `training_options[*].cost` for `C` **where `coverage > 0`**. **This is
    the effectfulness filter the audit demands (CC-A-002):** Riverside authors a `none` training
    option with `cost: 0` **and `coverage: 0`** on every catalog item (`catalog.yaml:58,80,102,124,
    151,173,195,217,239,261,299,330,363,395`) — it trains no one, so it does **not** clear
    `rollout_without_support` (which needs `trained_count > 0`, §4.2) and MUST NOT count as a fix.
    Excluding `coverage == 0` drops it; the cheapest *effectful* training for `order_fulfilment` is
    then `basic` at `12000` (`order_mgmt_v42`/`centraline_im7`, `catalog.yaml:80,102`), not `0`.
  - `add_service_tier` → cheapest `platform.support_tiers[*].cost` / `integration_tiers[*].cost`
    (`platform.yaml:192,236`); all tiers are effectful.
  - `add_policy` → the `policies[*].cost` of the switch the signal's clearing needs
    (`policies.yaml`); a policy move is effectful (it changes the posture).
  - `redesign_process` → `process_option.cost` **when `process_option is not null`** (effectful);
    an item whose `process_option` is `null` (e.g. `store_spreadsheets`, `catalog.yaml:152`) offers
    no `redesign_process` candidate.
  - `retire_component` → `0` (no purchase); `fund_response` → the event's `fund` option `cost`
    (`events.yaml`, e.g. `warehouse_rollout_gap.fund = 6000`), effectful by construction.

- **`was_actionable` = TRUE iff `cheapest_fix_when_raised <= available_funds_by_round[r-1]` for ANY
  round `r` in which the episode was open** ("affordability changes while open", O1). Committed spend
  already deducted (§5.5.2), so the comparison uses *remaining* capital.
- **Ties:** `min` collapses equal costs. **No effectful candidates:** `cheapest_fix_when_raised =
  None`, `was_actionable = False`, and the signal is **excluded from the responsiveness denominator**
  (O1) — never counted as an un-acted miss for a fix that never existed.
- **Worked example — the seed's three signals (all `was_actionable = True`, matching
  `riverside_r3.py:196-198`):** `ord_cap_01` cheapest fix = a deployment serving `order_fulfilment`
  (a `saas` mode at `capex 0`, `catalog.yaml:71`) → `0`; `wh_rollout_01` cheapest effectful fix =
  `add_training basic 12000` (the `none:0` option excluded) → `12000`; `sec_identity_01` cheapest fix
  = `central_sign_on saas capex 0` (`platform.yaml:103`) or `add_policy` → affordable. All ≤ the R2/R3
  remaining capital (`≥ 46000`, `pack.yaml:39`), so all three project `actionable = True`. *(The 1.5
  spec's illustrative `cheapest_fix_when_raised: 60000` at `1.5 spec.md:141` is **not reproduced** —
  exact fix prices are 1.7 calibration, consistent with S1; the contract is the lookup, not the
  figure.)*
- **Falsify:** set `available_funds_by_round` below the cheapest fix in every open round →
  `was_actionable = False`; raise it in one open round → `True`. Plant a `training.none`-only
  candidate set (delete every `coverage > 0` option) → `cheapest_fix_when_raised = None` (not `0`),
  `was_actionable = False` — proving the effectfulness filter fires.

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
| `policy_contradiction` | the resolved ordinal index of `policy` and `other_policy` (via `PolicyDecisionState`, default-resolved) are **on opposite sides of their midpoints** — one permissive, one restrictive (exact test §6.1) | `i/n == 0.5` counts as restrictive-half (strict `<`) | **either policy has `< 2` options → FALSE** (guard runs before division, no `0/0`, §6.1); either policy unresolvable with no default → raises (per `PolicyDecisionState` null path, `management.py:224-228`) |
| `sponsor_unassigned` | `not state.governance_for(capability).sponsor_assigned` (`state.py:92,211`) | — | no governance row → TRUE (unsponsored) |
| `round_equals` | `state.round == round` | `==` | — |

### 6.1 `policy_contradiction` exact test — **CORRECTED, no div-by-zero (CC-A-003)**

Let `i(p)` = the ordinal index of policy `p`'s resolved selection in its `options` list
(permissive = index 0; `CONTRACTS.md PolicyOption.options`), resolved through `PolicyDecisionState`
(default when not actively decided, per `_resolve_policy_decisions`, `management.py:192-231`). Let
`n(p) = len(p.options) − 1`.

**The `< 2`-option guard, evaluated BEFORE any division (the v1.0 div-by-zero fix).** The midpoint
classification `i/n` requires `n ≥ 1`, i.e. `len(options) ≥ 2`. The existing schema permits two valid
shapes the v1.0 formula divided by zero on (audit CC-A-003): a **one-option** policy (`len == 1` ⇒
`n == 0` ⇒ `0/0`) and a **zero-option / legacy** policy (`options == []`, which the permanent contract
check proves loads — `check_policy_options.py:152-172`, "legacy PolicyOption … options==[]", and the
`ok_obligations_empty` fixture, both green in `make check`). Freeze:

> **If EITHER referenced policy has `len(options) < 2`, `policy_contradiction` is `FALSE`** — a switch
> with no expressible spread of positions cannot be "permissive vs restrictive," so no contradiction
> can be asserted. The guard is checked first; division never runs on `n == 0`.

For both policies with `len(options) ≥ 2`, the precondition is TRUE iff the two switches sit on
**opposite halves**: `(i(policy) / n(policy) < 0.5) != (i(other_policy) / n(other_policy) < 0.5)` —
one permissive-half, one restrictive-half. **Boundary:** `i/n == 0.5` is **not** `< 0.5`, so an
exactly-central option (e.g. a 3-option switch's middle index 1: `1/2 = 0.5`) counts as the
**restrictive half** ("not permissive"); this is a deliberate, stated boundary decision, not an
accident of floating point. Riverside's six switches each carry exactly three options
(`policies.yaml:164,182,199,213,233,253`), so `n == 2` for every switch and the `< 2` guard is
unreachable in Riverside — but the runtime is total for every pack.

**Rejected alternative:** "indices unequal" — rejected: two adjacent restrictive positions are not a
contradiction; opposite-halves is the defensible reading of "contradiction." **Rejected alternative
for the boundary:** raise on a `< 2`-option policy (as `debt_above` raises on an absent input) —
rejected: the input is *present and well-formed*, it simply cannot express a posture, so `FALSE` (no
contradiction) is the total, non-throwing reading; the **validator (1.2, registered)** SHOULD reject
a `policy_contradiction` precondition that names a `< 2`-option policy at load, so it never reaches
the engine, but the engine must not divide by zero if one slips through.

**Falsify (required tests — positive, negative, and both boundaries):**
- both switches permissive (index 0) → `FALSE`; move one to its most-restrictive option → `TRUE`.
- **one-option policy** (`options=["only"]`, `n=0`) named on either side → `FALSE`, **no
  ZeroDivisionError** (the guard returns before dividing).
- **zero-option / legacy policy** (`options=[]`) named on either side → `FALSE`, no exception (the
  guard returns before any index lookup).

### 6.2 Conjunction
`Event.preconditions` is a flat **AND** list (`1.5 spec.md:195`). No OR/grouping in v1; an event
needing disjunction authors two events. A multi-precondition event's capability **sequence** is the
ordered, de-duplicated list of its `signal_open` capabilities in authored order (§7.1 — an ordered
tuple, never a set).

---

## 7. Event ownership, repetition, suppression, arms

### 7.1 Event → capability attribution (O2) — derived, **ordered & total (CC-A-004)**

The v1.0 candidate derived a Python **set** and left the multi-cap suppression `capability`, the
empty-set path, and the "primary capability" undefined — none deterministic (audit CC-A-004). Freeze
an **ordered** derivation instead of a set:

**Capability sequence** (a `tuple`, never a `set`): walk `event.preconditions` **in authored order**
(`Event.preconditions` is an ordered `list`, `models.py:388`); for each `pc` with
`pc.type == "signal_open"`, resolve `watch_rule(pc.signal).capability` (`WatchRule.capability`,
`models.py:335`); append it **de-duplicated, preserving first occurrence**. Set iteration is
prohibited because it is not deterministic across runs (breaks I4 determinism).

- **Primary capability** = the **first** element of the sequence (the capability of the first
  `signal_open` precondition in authored order). This is the single capability recorded on the
  suppression/fire record for a multi-cap event, and the capability whose serving path binds the
  blast-radius node (§8.1). Every Riverside event has exactly one `signal_open` precondition
  (`events.yaml`), so its sequence is length 1 and its primary capability is unambiguous.
- **Empty sequence** (an event with **no** `signal_open` precondition — none in Riverside; e.g. a
  future `round_equals`-only card): the sequence is the empty tuple `()`, the **primary capability is
  `None`**, the event is **O2-exempt** (consumes no per-capability slot, never suppressed by O2), and
  its recorded `capability` is `None`. Total and deterministic.

**O2 slot accounting (deterministic, authored deck order).** Maintain a per-capability fired-count
for the round. Iterate events in **authored deck order** (`events.yaml` top-to-bottom, the order the
loader preserves). An otherwise-satisfiable event **fires** iff, for **every** capability in its
sequence, the count is `< 2`; firing then increments the count for **each** capability in its
sequence. If **any** capability in its sequence is already at `2`, the event is **suppressed** and
recorded (§7.3). "At most two events per capability per round" (O2, `1.5 spec.md:94`) thus holds for
every capability, including one shared by a multi-cap event.

**Rejected alternative:** add `Event.capability` to the schema — rejected: it duplicates a fact the
preconditions already determine and could contradict them; derivation is single-source. **Rejected
alternative:** derive a `set` and pick "the" capability by `min()`/iteration order — rejected: not
authored-deterministic; the ordered tuple + first-element rule is.

**Falsify:** three satisfiable events all resolving to `order_fulfilment` → in authored order exactly
the first two fire, the third is suppressed and logged with `capability = "order_fulfilment"` (I7).
Plant a multi-cap event whose sequence is `("order_fulfilment", "store_operations")` after
`order_fulfilment` is already at 2 → it is suppressed and recorded with `capability =
"order_fulfilment"` (the primary/first). Plant a `round_equals`-only event → empty sequence, O2-exempt,
recorded `capability = None`, fires regardless of any capability's count.

### 7.2 Repetition
Events are **fire-once**: an event with an episode already `fired` in history does not re-fire.
Dedupe key: `event.key`. No `repeatable` field is added in v1 (Riverside needs none). **If** authored repetition is later required, it is a NEW `Event.repeatable: bool = False`, **owner 1.1** (§9) — and a repeatable event re-fires only on a **new signal episode** (§5.2), never on the same open episode.

### 7.3 Suppression record
When O2 or fire-once suppresses a satisfiable event, append
`(event.key, round, reason ∈ {"cap","already_fired"}, capability)` to the suppression log in
**authored deck order** (`events.yaml` order, `1.5 spec.md:94`), deterministically. The recorded
`capability` is the event's **primary capability** (§7.1: first element of its capability sequence,
or `None` for an empty sequence) — a single value even when the event resolves to several
capabilities, and always the same value across runs. For `reason == "cap"`, the primary capability is
the one whose count blocked it when the primary itself is full; when a *non-primary* capability in the
sequence is the one at 2, the record still names the **primary** (the stable identifier for the event)
and the blocking capability is recoverable from the sequence — one recorded field, no ambiguity.

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

### 8.1 Blast radius — the failed-node binding is **total & deterministic (CC-A-004)**
`graph.blast_radius(state, node_key, capabilities, primary)` is built (`graph.py:180`); I6 forbids
authoring the result. **The gap the v1.0 candidate left is which node an event removes when there is
no single "primary capability."** Freeze a **total** binding that returns a node **or `None`** for
every event:

```
failed_node(event, state):
  spof_pcs = [pc for pc in event.preconditions if pc.type == "node_is_spof"]   # authored order
  if spof_pcs:
      return spof_pcs[0].node                       # 1. explicit SPOF binding — first in authored order
  caps = capability_sequence(event)                 # §7.1 ordered tuple
  if caps:
      path = serving_path(state, caps[0], ...)      # 2. bottleneck of the PRIMARY capability (caps[0])
      if path is None:
          return None                               #    no serving path → no node to fail
      return bottleneck_node(state, path)
  return None                                        # 3. empty sequence, no SPOF → no node bound
```

- **`bottleneck_node(state, path)`** = the **first** node in `graph.serving_path` order (deterministic
  BFS, `graph.py:33-57,85-98`) whose `throughput` equals the path minimum
  (`graph.bottleneck_capacity`, `graph.py:113-124`), skipping `throughput is None` nodes. `serving_path`
  gives a stable node order, so the tie-break ("first at the minimum") is deterministic — this supplies
  the specific node the helper's `min()` alone does not name.
- **Rule 3 (no node bound):** an event with an **empty capability sequence and no `node_is_spof`
  precondition** models no infrastructural failure — `failed_node` returns `None`, the blast radius is
  **empty**, and **no `duration_hours` is computed** (§8.3 runs only when a node is bound). This covers
  **all thirteen Riverside events** (each is a persona/scorecard challenge with a single `signal_open`
  precondition and no `node_is_spof`, `events.yaml`), so none of them binds a node via rule 1; rule 2
  binds the bottleneck of its primary capability only when a serving path exists. An empty radius is a
  valid, honest result, not an error.
- **The seed's "WAN link" demonstration** (`wan_link`, `riverside_r3.py:64-68`) is a **direct**
  `graph.blast_radius(state, "wan_link", …)` call in the `--with-signals` demo (§10, `1.5 spec.md:403`
  step 4 "removing the WAN link darkens the expected capability set"), not an event-bound failure —
  `wan_link` is an articulation point with `throughput = UNCONSTRAINED`, so it is bound by demonstration,
  not by rule 2's bottleneck. The event-binding rules above and the seed's direct call are independent
  entry points into the same derived helper.
- **Never author the radius** (I6). **Failed-object model:** the helper removes a **node**; `ArchEdge`
  objects also exist (`state.py:51-56`), but v1 blast radius removes nodes only — edge failure is
  registered as a future extension (§9), not implemented.

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
| `TeamState.action_history` (`ActionRecord[]`, §5.5.1 — action-target matching + clearing) | **1.6 round** → 1.5 takes it as input (explicit `()` default preserves constructors) | clearing / responsiveness |
| `TeamState.available_funds_by_round` (O1 affordability input, §5.5.2 — committed spend already deducted) | **1.6 round** → 1.5 takes it as input (explicit `()` default) | actionability |
| `TeamState.debt_ratio_by_capability` (S5) | **1.6 round** | `debt_above` only (unreachable in v1) |
| `ArchNode.placement` (S4) | **1.6/1.1** — runtime placement from the deployed item; never store `hybrid` | `placement_count` only (unused by Riverside) |
| Ledger/RoundResult **persistence**, `instance_id`, re-score application | **1.6 / 2.x** | round runner |
| `CatalogItem.base_rto_hours` (S4) | **1.1 schema** (+ 1.2 validation) — **HARD prerequisite, §9.1** | duration path (in scope once §9.1 lands) |
| `Capability.agreed_availability` (S4, default 0.99) | **1.1 schema** (+ 1.2 validation) — **HARD prerequisite, §9.1** | `availability_shortfall` (in scope once §9.1 lands) |
| `Event.repeatable` (S3, only if repetition wanted) | **1.1 schema** | repetition only; not needed by Riverside |
| a "communication" rollout field (§4.2) | **1.1/1.6 gap, registered** | a richer `rollout_without_support` (v1 uses training+process) |

**Two classes of new field, deliberately different (this closes CC-A-005).** The `TeamState`
*round-evolution inputs* (`action_history`, `available_funds_by_round`, `debt_ratio_by_capability`)
are 1.6 outputs the pure 1.5 engine **reads** — they carry explicit empty-tuple defaults so every
existing `TeamState` constructor and the 1.4 pin are untouched, and the demo seeds them via
`--with-signals`. The two *casepack-schema fields* (`base_rto_hours`, `agreed_availability`) are the
**only** items the metric/signal/event core cannot run without, and they are now a **hard 1.1/1.2
prerequisite sequenced before the engine build** (§9.1) rather than a deferred path — so the
"all five metrics must exist before executable" rule (`1.5 spec.md:107-110`) and this packet's build
boundary no longer contradict.

### 9.1 Outage-schema prerequisite — sequenced before dispatch (**NEW, closes CC-A-005**)

The v1.0 candidate let `availability_shortfall` (and duration) be *deferred* when
`Capability.agreed_availability` / `CatalogItem.base_rto_hours` were absent (v1.0 `§9`, pre-flight
row 7), while `1.5 spec.md:107-110` requires **all five** metric functions to exist before the deck is
executable. A builder could not satisfy both (audit **CC-A-005**). Resolution — the author-authority
route the audit named as preferred: **make the two schema fields a hard prerequisite that lands and is
independently audited before the 1.5 engine builder is dispatched, exactly as the readiness closeout
was** (`1.5 spec.md:429-446`). The acceptance rule is **not** changed (that would need the user's
authority; not taken).

**The prerequisite packet (small, owned by 1.1 schema + 1.2 validation):**
1. `CatalogItem.base_rto_hours: float = 8.0` (`models.py CatalogItem`, §8.3) — hours to restore the
   item; default `8.0` so all 30 existing packs load unchanged; exact per-item values `TODO: calibrate`
   (1.7).
2. `Capability.agreed_availability: float = 0.99` (`models.py Capability`, §4.4) — the per-capability
   SLA target; default `0.99` so existing packs load unchanged; exact per-capability values
   `TODO: calibrate` (1.7).
3. 1.2 validation: both fields in `[0,1]` (availability) / `> 0` (hours), consistent with the existing
   `Field(gt=0, le=1)` pattern (`models.py:235`).

Both fields carry defaults, so **once the fields exist on the model, all five metrics are buildable
for every pack** (a pack that authors nothing still resolves the default). Pre-flight row 7 (§12) is
rewritten from a deferral into a **hard STOP**: if the fields are absent, the prerequisite has not
merged — do **not** build. This removes the deferred-path escape entirely. Register: `CC-D3`/`CC-D4`
retagged from optional deferrals to **prerequisites** (`OPEN-REGISTER §M`).

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

## 11. Invariants and their falsification checks *(each shown to fail on a PLANTED DEFECT — SPEC_PROTOCOL §4.3/§11)*

The v1.0 register was a ritual: it covered eight invariants but omitted recurrence/immutability,
lifecycle-status ordering, action-target matching + price selection, the eleven precondition
boundaries, multi-cap suppression ordering, failed-node binding, and duration evidence, and its CC8
grep (`riverside|grocer|random.|datetime.now`) could **not** detect `open(` or a `session` access —
planting either passed it (audit CC-A-006). This register derives a **falsifiable** row from **every
load-bearing contract** above. Each names the **planted defect** and the **observable failure**.

**Column key.** *Kind* = `grep` (a command runnable against this tree now — output shown) · `arith`
(an arithmetic check computable now) · `test` (a required builder test: the builder MUST plant the
defect, watch the check fail, then fix and watch it pass; a row with no such demonstration does not
close the DoD).

| # | Load-bearing contract | Kind | Falsification check | Planted defect → observable failure |
|---|---|---|---|---|
| CC1 | Unknown metric key raises `UnknownMetricError`, never returns false (§4.6) | test | evaluate a rule with `metric: not_a_metric` | returns `False` instead of raising → test asserting `raises(UnknownMetricError)` FAILS on the defect |
| CC2 | Threshold comparison is strict `>` (§3, `1.5 spec.md:167`) | test | metric value set **==** `critical_above` | a `>=` defect raises at the boundary → the "exactly-at-threshold does NOT raise" assertion FAILS |
| CC3 | No-serving-path metrics return `0.0`, never divide-by-zero (§4, decision 4) | test | capability with `nodes=(), edges=()` | a defect that divides by `capacity` raises `ZeroDivisionError` → "returns 0.0, no exception" FAILS |
| CC4 | **`SignalState` projection reproduces the seed rows AND credits clear-before-fire (§5.4, CC-A-001)** | arith | project the seeded R1–R3 history (the three-row table §5.4) | the **v1.0 rule** (`fire_round is not None` required) → `ord_cap_01 acted=False`, `responsiveness 0/3=0.0`, pin drifts, `make check` FAILS. **Verified 2026-08-22.** The corrected rule → `1/3=0.333333`, pin green |
| CC5 | **Recurrence opens a new episode; history is never overwritten (§5.2)** | test | re-raise a cleared `(key, ep 1)` condition | a defect reusing `episode_id 1` (or mutating the prior row) → the assertion that a `(key, 2)` row exists and the `(key, 1)` row is byte-unchanged FAILS |
| CC6 | **Lifecycle status ordering — no de-escalation; clear-after-fire stays `fired` (§5.2)** | test | escalate `critical`→ then attempt `warning`; and set `cleared_round > fire_round` | a de-escalation defect writes `warning` → "severity never falls" FAILS; a defect flipping status to `cleared` after fire → "O3: clear-after-fire earns no credit, status stays `fired`" FAILS |
| CC7 | **Action-target matching + effectful price selection excludes zero-effect options (§5.5.3-4, CC-A-002)** | test | build a candidate set of only `training.none` (`cost 0, coverage 0`) | a defect that omits the `coverage > 0` filter → `cheapest_fix_when_raised = 0`, `was_actionable = True` → the assertion `cheapest_fix_when_raised is None and was_actionable is False` FAILS. Also: an `ActionRecord` for the wrong `capability` must NOT clear the signal |
| CC8 | **No engine identity-branching / I/O / clock / randomness / session (I1+I2)** | grep | `git ls-files backend/app/engine \| xargs grep -nE "riverside\|grocer\|random\.\|datetime\.now\|session\|open\("` | **run 2026-08-22 → zero hits** (matches `1.5 spec.md:349` I2). Planting `open("x")` **or** a `session` access **or** `if pack=="riverside"` → non-zero, check FAILS (the v1.0 grep missed `open(`/`session`; this one catches them) |
| CC9 | 1.4 pin unchanged by any addition (§10.2) | grep | `cd backend && PYTHONPATH=. python3 -m pytest tests/test_engine_scoring.py -q` | any addition that moves `tech/org/mgmt/realised` → pytest FAILS (tech `0.750008`, org `0.507003`, mgmt `0.656778`, realised `0.249744`) |
| CC10 | **Eleven precondition boundaries — each fires and each fails to fire (§6)** | test | one positive + one negative + one boundary input per type (Riverside uses `signal_open`; the other ten ship synthetic fixtures) | e.g. `demand_exceeds_capacity` at `ratio` exactly (strict `>` → FALSE); `staffing_over` at `staff_fte==0` → TRUE; `policy_contradiction` with a `<2`-option policy → FALSE, **no `ZeroDivisionError`** (§6.1, CC-A-003); `debt_above` with absent input → raises `MissingRoundInputError`. A defect flipping any boundary → that type's boundary test FAILS |
| CC11 | **Multi-cap suppression is deterministic in authored deck order (§7.1, §7.3, CC-A-004)** | test | 3 satisfiable events on one capability, then a multi-cap event whose sequence includes an already-full capability | a defect iterating a `set` instead of the authored tuple → non-deterministic which two fire; a defect that suppresses without recording, or records a non-primary `capability`, → the "exactly first two fire; third suppressed, `capability == primary`" assertion FAILS (I7) |
| CC12 | **Failed-node binding is total (node or `None`) and deterministic (§8.1, CC-A-004)** | test | an event with a `node_is_spof` pc; an event with only `signal_open`; an event with an empty capability sequence | a defect returning a `set`/arbitrary node → the "SPOF pc → that node; primary-cap event → first path node at min throughput; empty sequence → `None`, empty radius, no duration" assertions FAIL |
| CC13 | **`arms` is an additional gate, not a replacement; multiple obligations OR (§7.4)** | test | armed obligation open, event precondition FALSE; then both true | a defect where `arms` alone fires the event → "does not fire with precondition false" FAILS; then both true → must fire (I5 reachability preserved) |
| CC14 | **Duration evidence shape & staffing modifier (§8.2-8.3)** | test | remove the failed node with / without a `failover`-kind edge; set `load==staff`, then double load; set `staff_fte==0` | a defect where `failover_exists` returns true on "any surviving path" → multiplier `1.0` when it should be `no_failover_multiplier=3.0`; `load==staff` → modifier must be `1.0`, double → `2.0`, `staff_fte==0` → `UNDERSTAFFED_MULTIPLIER=4.0`; evidence dict missing a key → shape assertion FAILS |

**Checks run against this tree, 2026-08-22 (Kind = grep/arith):**
- **CC8** — `git ls-files backend/app/engine | xargs grep -nE "riverside|grocer|random\.|datetime\.now|session|open\("` → **zero hits** (I1+I2 hold on the current engine; the greenfield metric-key and `LedgerSignal` greps §12 rows 3-4 also return zero).
- **CC4** — the §5.4 three-row projection computed by hand: corrected rule → `acted=1`, `0.333333`; v1.0 rule → `acted=0`, `0.0`. The two rules differ exactly on the clear-before-fire row.
- **CC9** — `make check` is green at the base (pytest 40 + every `check_*.py` + the fixture matrix).

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
| 7 | **The outage-schema prerequisite (§9.1) has landed** — `CatalogItem.base_rto_hours` and `Capability.agreed_availability` exist on the model | `[V]` | `grep -n "base_rto_hours\|agreed_availability" backend/app/casepack/models.py` | **both present. Absent → STOP: the 1.1/1.2 outage-schema prerequisite has not merged; the engine build cannot start (CC-A-005 — no deferred path)** |
| 8 | `ActionRecord` / action-and-funds inputs are the shape §5.5.1-2 freezes (or absent, to be added with explicit defaults) | `[V]` | `grep -n "action_history\|available_funds_by_round" backend/app/engine/state.py` | absent at greenfield (added by the build with `()` defaults); present → matches §5.5.1-2 |

Row 7 is now a **hard sequencing STOP, not a deferral (CC-A-005).** With both schema fields present,
**all five** metric functions are buildable (both fields carry defaults, §9.1) and there is no
availability/duration escape path — the "all five metrics must exist before executable" rule
(`1.5 spec.md:107-110`) and this packet's build boundary are consistent. If either field is absent,
the prerequisite (§9.1) has not merged and the builder STOPs.

---

## 13. Definition of Done (this contract packet)

| Item | Status | Evidence |
|---|---|---|
| All five metric contracts frozen with formula, edge cases, rejected alternative, falsification | ✅ DONE | §4 |
| Signal ledger object, episode identity, lead_time, projection, actionability+price lookup | ✅ DONE | §5 |
| **CC-A-001 — one total responsiveness rule; clear-before-fire credited; explicit three-row projection reproduces the pin** | ✅ DONE | §5.4 (arith verified 2026-08-22) |
| **CC-A-002 — immutable `ActionRecord` + funds history; exact target matching; effectful-option filtering (`training.none` excluded); committed-spend-deducted affordability** | ✅ DONE | §5.5.1-4, §9 |
| Eleven precondition runtime semantics incl. boundaries and `policy_contradiction` test | ✅ DONE | §6 |
| **CC-A-003 — `policy_contradiction` zero/one-option guard (no div-by-zero); boundary tests required** | ✅ DONE | §6.1, §6-table, §11 CC10 |
| Event attribution, repetition, suppression, `arms` relationship | ✅ DONE | §7 |
| **CC-A-004 — ordered (not set) attribution; primary capability; empty-set path; multi-cap suppression record; total failed-node binding** | ✅ DONE | §7.1, §7.3, §8.1 |
| Blast-radius node binding, `failover_exists`, duration formula + NEW constants | ✅ DONE | §8 |
| Field-ownership table (snapshot/round/persistence/schema) | ✅ DONE | §9 |
| **CC-A-005 — schema-gate contradiction resolved: outage-schema prerequisite sequenced before dispatch; row 7 is a hard STOP; all-five rule unchanged** | ✅ DONE | §0.5 S7, §9.1, §12 row 7 |
| **CC-A-006 — §11 register derives a falsifiable row from every load-bearing contract; CC8 detects I/O (`open(`,`session`)** | ✅ DONE | §11 (greps run 2026-08-22) |
| **CC-A-007 — dispatch scope carried into the tree; immutable source cited** | ✅ DONE | `handoffs/_prompts/1.5-contract-completion.txt`, §0 |
| Seed `--with-signals` contract; 1.4-pin preservation; two-path rebind | ✅ DONE | §10 |
| STOP register — every conflict surfaced, resolved or escalated with owner | ✅ DONE | §0.5 (S1-S7) |
| CONTRACTS.md entries for every frozen cross-module interface | ✅ DONE | §14; `CONTRACTS.md` |
| OPEN-REGISTER ownership for every deferral (S2 content, S4 schema, S5 debt, comms gap, action/funds inputs) | ✅ DONE | `findings/OPEN-REGISTER.md §M` |
| Builder + independent-auditor prompts | ✅ DONE | `handoffs/_prompts/1.5-{engine-builder,contract-completion-auditor}.txt` |
| Independent spec review (SPEC_PROTOCOL §11) before dispatch | **pending — re-audit gate** | this v1.1 candidate returns for independent audit |
| Browser / auth / instance canaries | **N-A** — pure contract packet | — |

---

## 14. CONTRACTS.md entries (added in the same change)

New/updated entries: **`WatchRule.metric` / the `METRICS` registry** (closed five-key vocabulary,
signature, unknown-raises); **`LedgerSignal`** (the ledger row + episode identity + the **corrected
`SignalState` projection**, CC-A-001); **`signal.cleared_by[]` price lookup** (extends the existing
PROSPECTIVE entry with the action-type→cost mapping and the **effectful-option filter**, CC-A-002);
**`TeamState.action_history` / `available_funds_by_round`** (the immutable action & funds inputs,
committed-spend-deducted, CC-A-002); **outage duration constants** (`base_rto_hours`,
`no_failover_multiplier`, `staffing_modifier`). Each carries producers/consumers and the "cite, never
restate" rule. **This revision edits the `LedgerSignal` projection line and the `cleared_by` price
line in `CONTRACTS.md` in the same change (§8 behaviour-change ripple).**

---

## 15. Changelog

**v1.2 — 2026-08-22.** Re-audit returned **PASS WITH FINDINGS**
(`findings/1.5-contract-completion-reaudit-2026-08-22.md`): all seven v1.0 findings independently
confirmed CLOSED, two new Report-level miscitations raised (RA-001, RA-002 — correct values, wrong
line pointers). Both fixed here: `pack.yaml` citations corrected to `:14` (capex_per_round) and
`:39-40,99-101` (the capital derivation), `platform.yaml` to `:103` (central_sign_on) and `:192,236`
(tiers) — all grep-verified against the real files (114 and 241 lines). No contract, formula, or
value changed; pointers only. `make check` green.

> **Recorded honestly (re-audit observation, not a finding):** the v1.0 and v1.1 commits carry the
> same git identity, so "fresh author" is a contextual claim (an isolated subagent, not a fork), not
> one confirmable from commit metadata. The freshness was in the authoring context; git attribution
> for all agents is the repository identity. Noted for the process, `OPEN-REGISTER §N`.

**v1.1 — 2026-08-22.** Revised by a **fresh author** (not the v1.0 author, `GOVERNANCE §6.2`) to
close every finding of the v1.0 audit (`findings/1.5-contract-completion-2026-08-22.md`, six Blocking
+ one Report). One logical revision over `main @ de1af03`. Per-finding closure:

| Finding | Change |
|---|---|
| **CC-A-001** | §5.4 — one **total** responsiveness rule: `acted_before_fire = cleared_round is not None and (fire_round is None or cleared_round <= fire_round)`; `fire_round is None` (clear prevents fire) is now the **most** responsive case. Explicit three-row projection table reproduces the seed's `(ord_cap_01 True, wh_rollout_01 False, sec_identity_01 False)` → `1/3 = 0.333333`, keeping the pin byte-identical; the v1.0 rule is shown to yield `0.0` (pin drift), the watched failure. |
| **CC-A-002** | §5.5.1-4 — immutable `ActionRecord` (type, locked round, capability/target scope, cost) + `available_funds_by_round`; exact target matching; effectful-option filter excludes `training.none` (`coverage 0`, `catalog.yaml:58,80`); committed spend is **already deducted** (funds = remaining, `pack.yaml:39`). |
| **CC-A-003** | §6.1 — `< 2`-option guard evaluated **before** any division (no `0/0` for one-option or legacy zero-option policies, which `check_policy_options.py` proves load); zero/one-option boundary tests required (§11 CC10). |
| **CC-A-004** | §7.1/§7.3/§8.1 — **ordered** (tuple, not set) attribution; primary capability = first in sequence; empty-sequence path (`None`, O2-exempt); single recorded suppression `capability`; **total** failed-node binding (SPOF pc → node; primary-cap bottleneck; else `None`/empty radius). |
| **CC-A-005** | §0.5 S7, §9.1, §12 row 7 — the two outage-schema fields become a **hard 1.1/1.2 prerequisite sequenced before dispatch** (like the readiness closeout); row 7 is a hard STOP, not a deferral; the "all five metrics" acceptance rule is untouched. |
| **CC-A-006** | §11 — register rebuilt to derive a falsifiable, planted-defect row from every load-bearing contract (recurrence/immutability, lifecycle ordering, action-target/price, eleven precondition boundaries, multi-cap suppression, failed-node binding, duration evidence); **CC8 grep now detects `open(`/`session`** (matches `1.5 spec.md:349` I2), run to zero hits. |
| **CC-A-007** | §0 — the dispatch prompt is **carried into the candidate's tree** (`handoffs/_prompts/1.5-contract-completion.txt`) and its immutable source (`2f68317`) is cited; no cross-branch lookup needed. |

Preserved honest (audit-verified, unchanged): **S1** (`12000/7225 = 1.660899…`, not `1.11`; formula
frozen, numbers 1.7 calibration), **S2** (`saturday_queue_collapse` absent; demo rebound to
`warehouse_rollout_gap`), **S6** (live pins `0.656778/0.249744`). No engine code changed; the 1.4 pin
and `make check` are untouched by construction.

**v1.0 — 2026-08-22.** Contract-completion candidate authored under SPEC_PROTOCOL v1.3 against
`main @ de1af03`. Freezes the five metric bodies, the signal-ledger object and projection, all
eleven precondition semantics, event attribution/repetition/arms, and the blast-radius/duration
formula with NEW constants. Six conflicts recorded in the STOP register (§0.5). **Failed independent
audit** — six Blocking findings (CC-A-001..006) + one Report (CC-A-007); superseded by v1.1.
