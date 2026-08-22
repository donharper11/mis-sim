# 1.6 — Round Runner · Build Spec

**Authored under** `SPEC_PROTOCOL.md` v1.3 · **Author:** Claude · **Date:** 2026-07-26 · **Reconciled:** 2026-08-22 (v1.1)
**Phase:** 1 · **Depends on:** 1.1, 1.4, 1.5 · **Blocks:** 1.7, 2.3, 3.5, 3.6
**Gate tier:** **Heavy** (`GOVERNANCE §6.3`) — orchestrates a scoring path and produces
cross-module contract fields (`action_history`, `available_funds_by_round`,
`debt_ratio_by_capability`, `ArchNode.placement`) the merged 1.5 engine consumes. Full
four-gate cycle: independent spec review **and** independent audit.
**Independent spec review** *(SPEC_PROTOCOL §11, before dispatch)*: **pending** — this v1.1
reconciliation returns for an independent consistency pass before a builder is dispatched.

> The orchestrator. 1.4 and 1.5 are pure; this is where state, ordering, and persistence
> live — which makes it the first packet where `instance_id` is non-negotiable. **1.6 is also
> the assembler of the `TeamState` snapshot the pure engines read:** it persists round state in
> its own tables and, each round, constructs the immutable `TeamState`/`ArchNode`/`LedgerSignal`
> snapshot that 1.4 scores and 1.5 evaluates (§5.1a).

---

## 0. Spec Basis

**Read in full (original authoring, 2026-07-26):** `handoffs/1.4-scoring-engine/spec.md`,
`handoffs/1.5-event-signal-engine/spec.md` · `design/05-implementation-plan.md` §1.1 ·
`BECSR/async-round-deadlines.md` (the lock and advance semantics 2.3 will wrap) ·
`GOVERNANCE.md` §4.5 · `CONTRACTS.md` `instance_id`, `decision_line.category`.

**Read in full (2026-08-22 reconciliation) — the contracts that landed AFTER this spec was
authored:** `handoffs/1.5-event-signal-engine/contract-spec.md` v1.2 (§5 ledger, §7 events,
§8 blast radius/duration, §9 field-ownership table, §10 seed); `handoffs/1.4-scoring-engine/closeout-spec.md`
(the pin + `PolicyDecisionState`); `GOVERNANCE.md` v1.4 (§6.3 gate tiering), `SPEC_PROTOCOL.md`
v1.3, `QUALITY_PROTOCOL.md` v1.4; the merged engine —
`backend/app/engine/{state,ledger,events,metrics,preconditions,score}.py`;
`backend/seeds/{riverside_r3,riverside_signals}.py`; `backend/app/seed/demo.py`;
`backend/app/casepack/checks.py` (`ACTION_TYPES`); `backend/tests/test_engine_scoring.py`
(the frozen pin) and `test_signal_engine.py` (the orchestration sequence);
`CONTRACTS.md` (`WatchRule.metric`, `LedgerSignal`, `signal.cleared_by[]` price lookup,
`TeamState.action_history`/`available_funds_by_round`, outage-duration constants);
`findings/OPEN-REGISTER.md` §M (CC-D6/7/8/10, owned by 1.6) and §O (1.5 merged).

**Extraction sufficiency:** covered. BECSR's Django implementation was read for
*semantics* (lock reasons, grace, auto-advance), not for code — different stack. The
2026-08-22 reconciliation re-verified every field 1.6 owes 1.5 against the merged working
tree (`state.py`, `ledger.py`, `events.py`) — all five inputs already exist on the engine's
snapshot objects with explicit defaults, so this packet *populates* them, it does not define them.

---

## 1. Purpose and scope

**In scope:** the state model for a team's simulation · applying a locked decision sheet
to that state · the resolution order · producing an immutable `RoundResult` · the debt
ledger and opex ratchet · TCO forecast reconciliation · lock/advance state machine.

**Out of scope:** deadlines, auto-lock, auto-advance scheduling (2.3 — this exposes
`lock()` and `advance()`; 2.3 decides *when*) · UI · casepack loading (2.5) · auth.

---

## 2. Project-specific statements

**Scoring factors touched:** consumes 1.4 and 1.5; **owns** the debt ledger, opex run-rate,
and TCO forecast accuracy (`design/02` §D). **Produces the round-evolution inputs the 1.5
engine scores against** — `TeamState.action_history`, `available_funds_by_round`,
`debt_ratio_by_capability`, and `ArchNode.placement` (`state.py:118-134,209-222,45-49`;
`OPEN-REGISTER §M` CC-D10/CC-D7/CC-D6/CC-D8). These feed signal responsiveness
(`management.py:138-143`, via the `SignalState` projection) — a scoring path — so this packet
is **Heavy** (`GOVERNANCE §6.3`).

**Casepack keys read:** all, via the loaded pack — including `watch_rules`, `events`,
`obligation_rules`, `policies`, `catalog`, `platform` (the keys the 1.5 engine reads through
the snapshot 1.6 hands it, `1.5 contract-spec §2`).
**Casepack-identity branching:** none — I1.
**Instance scoping:** **every table this packet creates carries `instance_id`, non-null,
from creation** (`GOVERNANCE.md §4.5`). Every read filters on it. This is the first packet
where BECSR's retrofit pain is avoidable, and I4 enforces it. The pure engine snapshots
1.6 constructs (`TeamState`, `LedgerSignal`) carry no `instance_id` — the *persistence tables*
behind them do; the engine performs no I/O (1.5 I2, 1.4 I2).
**Business-language check:** emits keys and numbers; no prose. I3.

---

## 3. Settled decisions

1. **`instance_id` on every table, day one.** No exceptions, no "add it later."
2. **`RoundResult` is immutable.** Re-running a round produces a new row; it never mutates
   an old one. Debriefs must remain reproducible after later rounds run.
3. **Resolution order is fixed and specified** (§5.2). Order changes outcomes, so it is a
   contract, not an implementation detail.
4. **The engine stays pure.** This packet is the only one that touches the session.
5. **Opex is a ratchet.** It carries forward and is recomputed from live deployments each
   round — never a stored running total that can drift.
6. **Deferral accrues debt**, which raises incident probability and is visible only in the
   ledger, not on the Tier-1 dashboard (`design/02` §D).
7. **Partial-update semantics for the decision sheet** — only categories present in the
   payload are written. (Learned from GSCM's `PeriodDecisionV2`; a full-replace payload
   silently wipes categories the UI did not send.)
8. **`people_affected` has one authoritative home: the catalog** *(finding CU-004,
   `SPEC_PROTOCOL §3` reconciliation rule).* `catalog.yaml`'s `<item>.people_affected.count`
   is the population a deployment of that item affects. A deployment's `people_affected` — the
   value the org scorer divides by (`organisation.py`: `training = trained_count /
   people_affected`) — **must equal the count of its `catalog_key`'s catalog item.** In the
   R3 seed it is hand-authored and duplicates the catalog; **this packet must derive it from
   the catalog** so the duplicate home disappears. Until then the two must not drift: the
   guard `backend/tests/test_people_affected_reconciliation.py` fails if any seeded
   deployment's `people_affected` disagrees with its catalog item, so the scorer can never
   silently divide by a number the authored pack does not carry.

### Reconciliation decisions (added 2026-08-22 — the merged 1.4/1.5 contracts)

9. **1.6 populates the four round-evolution inputs the 1.5 engine reads; it does not redefine
   them.** All four already exist on the engine's snapshot objects with explicit defaults, so
   populating them changes no engine code and cannot drift from the frozen shape:
   - **`TeamState.action_history: tuple[ActionRecord, ...]`** (`state.py:118-134,210-213`).
     `ActionRecord(action_type, locked_round, capability, target_key, cost)`. `action_type` is
     one of the **closed ten-key `checks.ACTION_TYPES`** set (`checks.py:13-24`); `locked_round`
     is the responsiveness clock; `cost` is the capex actually committed (`>= 0`). 1.6 derives
     one `ActionRecord` **per committed `decision_line`** whose category maps to an action type
     (§5.1a), append-only across rounds. Consumed by `ledger.matching_clear_actions`
     (`ledger.py:207-236`) to decide which action clears which signal. Register `CC-D10`.
   - **`TeamState.available_funds_by_round: tuple[int, ...]`** (`state.py:214-218`), index *r-1*
     = **remaining** capital for new commitments in round *r*, **committed spend already
     deducted** (`capital_remaining = capital_available − capital_committed`, `CONTRACTS.md
     capital_remaining`; `1.5 contract-spec §5.5.2`). This is the same ratchet as decision 5 —
     1.6 recomputes it from live deployments, never accumulates. Consumed by
     `ledger.was_actionable` (`ledger.py:192-204`). Register `CC-D7`.
   - **`TeamState.debt_ratio_by_capability: dict[str, float] | None`** (`state.py:219-222`),
     derived from the debt ledger (decision 6, the `debt_item` table). `None` means not supplied
     ⇒ the `debt_above` precondition **raises `MissingRoundInputError`** (never silently FALSE,
     `preconditions.py`). Unreachable in v1 (no Riverside event uses `debt_above`); 1.6 supplies
     it so future packs are not blocked. Register `CC-D6`.
   - **`ArchNode.placement: str | None`** (`state.py:45-49`), the runtime placement of the
     deployed item — one of `on_prem`/`cloud`/`saas`, **never the derived `hybrid`**
     (`CONTRACTS.md placement`). Read by the `placement_count` precondition. Register `CC-D8`.
10. **1.6 persists the 1.5 `LedgerSignal` ledger and reconstructs it as the immutable snapshot
    the engine reads.** The `signal` table (§5.1) stores every field of the frozen
    `LedgerSignal` (`ledger.py:29-46`; `CONTRACTS.md LedgerSignal`): `key · episode_id ·
    capability · metric · metric_kind · value · severity · status ∈ {open,cleared,fired} ·
    first_shown_round · cleared_round · fire_round · cleared_by · was_actionable ·
    cheapest_fix_when_raised` — plus `instance_id`, `team_id`, `round`. **Episode identity is
    `(key, episode_id)`; history is append-only and immutable** — a re-raise opens
    `episode_id + 1`, never overwrites a prior row (I9). The 1.4 scorer never reads this table;
    it reads the 4-field `SignalState` that `ledger.project_signal_state` derives (§5.2 step 10).
11. **1.6 calls the merged 1.5 engine at its frozen entry points; it re-implements none of it.**
    The resolution order (§5.2) binds to the pure functions the engine already ships:
    `ledger.advance_ledger()` (raise/escalate/clear), `events.resolve_events()` (fire + O2 cap +
    suppression), `events.failed_node()`/`failover_exists()`/`outage_duration()` (blast radius +
    duration), `ledger.project_signal_state()` (→ `SignalState`), and `score.score_team()`.
    The exact call sequence is the one the engine's own demo and tests use
    (`app/seed/demo.py:93-104`, `tests/test_signal_engine.py`) — §5.2.
12. **The 1.4 pin and 1.5 contracts are consumed, never redefined.** The frozen pin
    (`test_engine_scoring.py:34-40`: tech `0.750008` · org `0.507003` · mgmt `0.656778` ·
    realised `0.249744`, throttle `org`) and every 1.5 formula, constant, and lifecycle rule are
    inputs to this packet. A round-runner change that moves the pin is a defect (I10). Any
    genuine conflict is a STOP to the authority (O4), not a silent resolution (`GOVERNANCE §7`).

---

## 4. Open decisions

| # | Question | Criteria | Reporting |
|---|---|---|---|
| **O1** | Can a locked round be unlocked? | **Default: yes, instructor-only, and it invalidates the `RoundResult` rather than editing it.** Instructors need it in a live class; students must not | Record |
| **O2** | Where do lead-time purchases live between order and arrival? | **Default: an `in_flight` collection on team state, materialising into the graph at `arrival_round`.** Not in the graph early — that would inflate capacity | Record |
| **O3** | Does the engine run at lock, or at advance? | **Default: at advance.** Lock freezes input; advance produces results. Separating them lets an instructor lock a section and review before committing outcomes | Record |
| **O4** *(new, 2026-08-22 — STOP surfaced, needs a ruling)* | **Where does the FIRST scoring pass (step 9) sit relative to the ledger advance (step 10) that produces the `SignalState` the responsiveness term reads?** The 1.4 management scorer reads `state.signals` (`management.py:138-143`), and `state.signals` is `ledger.project_signal_state(ledger)`. The §5.2 order authored in 2026-07-26 places 1.4 scoring at step 9 **before** the watch-rule ledger advance at step 10 — but the projection seam that makes `signal_responsiveness` computable did not exist until the merged 1.5 engine. So step 9 as written would score responsiveness against a projection that lacks this round's clears/fires. This is an ordering tension between the 1.6 spec and the merged 1.4/1.5 projection contract on a **scoring path**. | **STOP to authority (`GOVERNANCE §7`) — do NOT resolve silently.** *Proposed compliant route for the ruling:* advance + project the ledger (step 10) **before** any responsiveness-bearing score, and treat the single re-score at step 12 (after events fire, §5.2) as the **authoritative** capability score for the round; the pre-event pass at step 9 supplies only the raw tech/org/mgmt terms events may perturb, and never a responsiveness number read from a stale projection. The frozen 1.4 pin is a single snapshot and does not constrain this ordering, so the choice affects the game's computed responsiveness but not the pin. | ✅ **RULED 2026-08-22 (user): adopt the compliant route.** Advance + project the ledger (step 10) **before** any responsiveness-bearing score; the pre-event pass at step 9 supplies only raw tech/org/mgmt terms; the single re-score at **step 12** is the **authoritative** per-capability score and is **where `signal_responsiveness` is read**, from the freshly-advanced ledger. Folded into §5.2 below. |

---

## 5. Design

### 5.1 State model — all `instance_id`-scoped

```
team_state            current round, strategy (versioned), cash, opex run-rate,
                      available_funds_by_round (remaining capital per round; decision 9)
arch_node             deployed items: catalog_key, placement (on_prem/cloud/saas — never
                      hybrid, decision 9/CC-D8), config_tier, installed_round, retired_round
arch_edge             integrations: source, target, entity, mode (kind ∈ network/integration/failover)
deployment_org_state  trained_pct, process_redesigned, sponsor, owner
platform_service      placement, capacity, utilisation
org_unit              headcount, resistance
it_staff              fte, load
in_flight             ordered, not yet arrived (O2)
decision_line         one row per decision, category per CONTRACTS.md; the source 1.6
                      derives each ActionRecord from (decision 9/CC-D10)
signal                the 1.5 LedgerSignal ledger, persisted (decision 10) — one row per
                      (instance, team, key, episode_id); every LedgerSignal field + round
debt_item             deferrals with accrual; the source of debt_ratio_by_capability (CC-D6)
tco_forecast          selected cost categories vs actuals
round_result          immutable, one per (instance, team, round)
```

**The `signal` table columns are the frozen `LedgerSignal` shape** (decision 10,
`ledger.py:29-46`, `CONTRACTS.md LedgerSignal`), non-negotiable so persistence round-trips the
engine output exactly:

```
signal(instance_id, team_id, round,
       key, episode_id, capability, metric, metric_kind,
       value, severity ∈ {warning,critical}, status ∈ {open,cleared,fired},
       first_shown_round, cleared_round?, fire_round?,
       cleared_by[], was_actionable, cheapest_fix_when_raised?)
       PK (instance_id, team_id, key, episode_id)   -- episode identity, append-only (I9)
```

### 5.1a Snapshot assembly — 1.6 builds what the pure engines read *(NEW, 2026-08-22)*

1.4 and 1.5 are pure functions of `(Casepack, TeamState)` and a prior `LedgerSignal` tuple; they
never touch the database (1.4 I2, 1.5 I2). **1.6 is the only packet that bridges the persistence
tables above to those in-memory snapshots.** Each round it constructs, from its own tables:

- the **`TeamState`** the engines score — `nodes` (with `placement`, decision 9) from `arch_node`,
  `edges` from `arch_edge`, `deployments` from `deployment_org_state`, `staff` from `it_staff`,
  `governance`/`org_units`/`decisions`/`policy_decisions` from their tables, plus the four
  round-evolution inputs of decision 9 (`action_history` from committed `decision_line` rows,
  `available_funds_by_round` from the capital ratchet, `debt_ratio_by_capability` from `debt_item`,
  and `signals` from the projected ledger — §5.2 step 10);
- the prior **`LedgerSignal` tuple** loaded from the `signal` table (append-order preserved), which
  `advance_ledger` takes as immutable history and returns a new tuple 1.6 persists back (I9).

**One source of truth per fact** (`SPEC_PROTOCOL §3`): the persistence tables are authoritative;
the snapshots are derived views rebuilt each round, never a second home that can drift. `ArchNode`,
`ActionRecord`, and `LedgerSignal` are **frozen dataclasses** — 1.6 assembles them, the engine
consumes them, and neither mutates them.

### 5.2 Resolution order — fixed contract

```
 1  validate the locked sheet (categories, affordability, legality)
 2  apply retirements and cancellations
 3  materialise in_flight arrivals for this round
 4  apply new purchases; deduct capex; recompute opex run-rate
 5  apply org decisions: training, process, communication, staffing
 6  apply governance: owners, sponsors, priorities, policy
 7  recompute platform pools (compute, storage, IT staff load)
 8  recompute the graph; derive serving paths and SPOFs
 9  1.4 scoring → raw tech/org/mgmt terms only; NO responsiveness here (O4 ruling)
10  1.5 watch rules → raise / escalate / clear signals    [ledger.advance_ledger]
11  1.5 events → fire, blast radius, outcome application   [events.resolve_events + duration]
12  re-score capabilities affected by event outcomes        ← single re-entry only
13  accrue debt for deferrals; reconcile TCO forecasts
14  roll up Balanced Scorecard; write immutable RoundResult
```

Step 12 runs **exactly once**. An event changes state, so scores must reflect it — but
iterating to a fixed point makes outcomes unexplainable, and explainability is the product.
Invariant I5.

**Steps 10–12 bind to the merged 1.5/1.4 entry points** (decision 11; the sequence the engine's
own demo and tests use — `app/seed/demo.py:93-104`, `tests/test_signal_engine.py`):

```
10  ledger = ledger.advance_ledger(prior_ledger, state, pack)      # raise/escalate/clear;
                                                                   #   no fires yet (fired={})
    state = state with signals = ledger.project_signal_state(ledger)  # → SignalState for 1.4
11  fired, suppressed = events.resolve_events(state, pack, ledger)  # O2 cap + suppression, in
                                                                   #   authored deck order
    for each fired event with a bound node:
        node = events.failed_node(event, state, pack)              # total: node or None
        evidence = events.outage_duration(state, node, cap, pack)  # blast radius + duration_hours
        apply the event's outcomes to state (I6 forbids authoring the radius/duration)
    ledger = ledger.advance_ledger(ledger, state, pack,
                                   fired_signals=frozenset(fired)) # stamp fire_round
    state = state with signals = ledger.project_signal_state(ledger)
12  re-score with score.score_team(pack, state)                    # single re-entry (I5)
```

`ledger.advance_ledger` reads the **round-close snapshot before event outcomes are applied**
(`1.5 contract-spec §3` decision 1) — which is exactly why watch rules (step 10) precede events
(step 11). The second `advance_ledger` pass at step 11 only stamps `fire_round` from the events
that fired; it opens no new episode for a signal already open (I9). Step 12 is the authoritative
per-capability score for the round, and is where `signal_responsiveness` is read from the
advanced ledger (O4 ruled 2026-08-22: advance the ledger before any responsiveness-bearing score;
step 9 supplies raw terms only).

> **How step 9 yields "raw terms only" (finding 1.6-SR-001).** `score_team` always computes a
> `signal_responsiveness` component of the mgmt term, so step 9 *does* produce a responsiveness
> number — but from the **pre-advance** ledger, so it is **provisional and discarded**: step 12's
> re-score, run after `advance_ledger` (step 10) has this round's clears/fires, **overwrites** the
> per-capability score and is the only responsiveness the `RoundResult` records. The builder does
> not need a second scoring entry point; it persists step 12's output, not step 9's.

### 5.3 `RoundResult`

Everything the debrief and 1.7 need, with no recomputation:

```python
{ "instance_id": …, "team_id": …, "round": 3,
  "capabilities": [ <decomposition record from 1.4 §5.6> ],
  "scorecard": {"financial": …, "customer": …,
                "internal_process": …, "learning_growth": …},
  "signals": {"raised": [...], "cleared": [...], "open": [...], "fired": [...]},
  "events": [ {"key": …, "blast_radius": [...], "duration_hours": …,
               "outcomes": {...}} ],
  "financials": {"capex_spent": …, "opex_runrate": …, "debt_total": …},
  "tco_variance": [ {"item": …, "forecast": …, "actual": …} ],
  "missed_signals": [ {"key": …, "first_shown_round": 2,
                       "cheapest_fix_when_raised": 60000} ] }
```

`missed_signals` is what prints *"you were told in round 2."*

**Reconciliation of the shapes above with the merged 1.5 engine (2026-08-22):**
- **`signals`** buckets the round's `LedgerSignal` rows by `status` — `fired`/`cleared`/`open`
  are the three status values (`ledger.py:24`); `raised` is the rows whose `first_shown_round`
  == this round. Each entry carries the frozen `LedgerSignal` fields (decision 10), not a
  reinvented shape.
- **`events`** entries are the `events.outage_duration` evidence dict
  (`events.py:230-238`): `{node, base_rto_hours, failover_exists, failover_factor,
  staffing_modifier, duration_hours, blast_radius}` plus the applied `outcomes`. An event with
  **no bound node** (`failed_node` → `None`, e.g. every Riverside persona/scorecard card,
  `1.5 contract-spec §8.1`) has an **empty `blast_radius` and no `duration_hours`** — a valid,
  honest result, not an error. The blast radius and duration are **derived, never authored** (I6).
- **`missed_signals`** reads `cheapest_fix_when_raised` from the `LedgerSignal` rows that were
  `actionable` (`was_actionable=True`) and never credited (`acted_before_fire=False` after the
  §5.2 projection). The illustrative `60000` is **not reproduced** — exact fix prices are 1.7
  calibration (`1.5 contract-spec §5.5.4`, S1/CC-D1).

---

## 5.5 Seed — a full six-round game *(GOVERNANCE §4.9)*

```
seed        a course, section, instance, team, and six rounds of real decisions
command     python -m app.seed.demo --full
demonstrate six immutable RoundResults in the database
            opex run-rate ratcheting 47,000 → 53,000 → 58,300 → …
            missed_signals populated with first_shown_round
            \d on every runtime table showing instance_id NOT NULL
```

**This is the command every later packet uses.** One step, clean database to complete
demo state (`GOVERNANCE §4.9` rule 4).

**Reconciliation with the merged engine seed (2026-08-22):** the merged 1.5 engine already ships
`python -m app.seed.demo --scenario riverside_r3 --with-signals` — a *single-round* demonstration
that hand-authors the R1–R3 `LedgerSignal` history (`seeds/riverside_signals.py`) and runs the two-
path `warehouse_rollout_gap` demo. **1.6's `--full` supersedes the hand-authored history:** it
populates the `signal` table by **running the real `ledger.advance_ledger` transition** across six
rounds (§5.2 step 10), so the persisted ledger is computed, not stubbed (`GOVERNANCE §4.9` — seed
data, never stubs).

**How the pin is preserved — the honest reading (corrected, finding 1.6-A-007).** The frozen 1.4
pin is preserved **two ways, neither of which is the `--full` seed's own R3 number**:
1. **Hermetically** — `test_engine_scoring.py` scores the `riverside_r3` snapshot directly and 1.6
   touches no engine, scoring, or calibration code, so the pin (tech `0.750008` / org `0.507003` /
   mgmt `0.656778` / realised `0.249744`) is **byte-identical** by construction (I10).
2. **Through the projection seam** — the R1–R3 `LedgerSignal` history projects
   (`ledger.project_signal_state`) to exactly the three `SignalState` rows the pin depends on, and
   scoring the snapshot with those *projected* signals still yields the pin (`test_round_pin.py`,
   the CC-A-001 mechanism). The round-evolution inputs 1.6 produces drive that projection
   (`action_history` → `cleared_round`; `available_funds_by_round` → `was_actionable`), so planting
   either drifts the pin.

The `--full` seed is a **distinct, coherent playthrough**: its R3 ledger, run through the real
`advance_ledger`, reproduces the same credited/un-credited **pattern** the pin depends on
(`ord_cap_01` cleared-before-fire = credited; `wh_rollout_01`/`sec_identity_01` un-credited; all
actionable), but **not the pinned number** — the seed scales order capacity so `ord_cap_01` can clear
before the deck fires it, which changes the order-fulfilment technology term (R3 realised `≈0.2038`
≠ the pinned `0.249744`). This is expected: the pinned snapshot's near-capacity order system cannot
reproduce a cleared-before-fire `ord_cap_01` under the real deck (`pos_support_ending` fires it on
warning), which is exactly why the pin is anchored to `test_engine_scoring` and the projection seam
rather than to the seed's computed R3 score. `--with-signals` remains valid as the isolated engine
demo; `--full` is the round-runner's clean-DB seed.

---

## 6. Invariants

| # | Invariant | Check | Expected |
|---|---|---|---|
| I1 | No pack-identity branching | `grep -rniE "riverside\|grocer" backend/app/round/` | zero |
| I2 | Engine purity preserved — no session imports under `engine/` | `grep -rn "session\|execute" backend/app/engine/` | zero |
| I3 | No displayed English | `grep -rnE '"[A-Z][a-z]+ [a-z]+ [a-z]+' backend/app/round/*.py \| grep -v '#\|"""\|raise'` | zero |
| I4 | **Every new table has non-null `instance_id`; every query filters on it** | inspect each migration; then `grep -rn "select(" backend/app/round/ \| grep -v instance_id` | all tables have it; zero unfiltered selects |
| I5 | Re-scoring re-entry happens exactly once | `grep -c "rescore" backend/app/round/runner.py` | 1 |
| I6 | `RoundResult` is never updated | `grep -rn "update(RoundResult\|round_result.*=.*" backend/app/round/` | zero mutations |
| I7 | Opex recomputed, never accumulated | `grep -rn "opex_runrate +=" backend/` | zero |
| I8 | Partial update — absent categories are untouched | property test | holds |
| I9 | **Signal ledger is append-only and immutable — a re-raise opens `episode_id+1`, a prior episode row is never UPDATEd** (decision 10, `1.5 contract-spec §5.2`) | `grep -rniE "update\(.*signal\|signal.*\.status *=" backend/app/round/` → zero UPDATEs on a prior episode; **plant a re-raise of a cleared `(key, ep1)` → a `(key, ep2)` row exists and the `(key, ep1)` row is byte-unchanged** (mirrors engine `test_cc5`) | zero mutating UPDATEs; the plant makes the "new episode, prior row unchanged" test FAIL if the runner overwrites |
| I10 | **The frozen 1.4 pin survives the six-round seed** (decision 12; `test_engine_scoring.py:34-40`) | `cd backend && PYTHONPATH=. python3 -m pytest tests/test_engine_scoring.py -q` after `--full`; **plant an `available_funds_by_round` or `action_history` value that changes the R3 projection** → pin drifts | pass (tech `0.750008`, org `0.507003`, mgmt `0.656778`, realised `0.249744`); the plant makes it FAIL |

**Note (I5, reconciled):** the "single re-score re-entry" is the single `score.score_team()` call
at §5.2 step 12. The `grep -c "rescore" runner.py == 1` check compares the build to itself and
cannot fail on the dimension it names (`SPEC_PROTOCOL §4.3`); the builder must additionally prove
re-entry-once with a **planted second re-score** that makes an "event outcome scored exactly once"
property test FAIL — not by counting a string.

---

## 7. Pre-Flight Verification Register

| # | Claim | Tag | Check | Expected |
|---|---|---|---|---|
| 1 | 1.4 and 1.5 merged and pure | `[V]` | `grep -rn "session\|random\." backend/app/engine/` | zero |
| 2 | Alembic chain exists from 0.2 | `[V]` | `ls backend/alembic/versions/` | baseline present |
| 3 | `decision_line.category` enum matches CONTRACTS | `[V]` | `grep -A14 "decision_line.category" CONTRACTS.md` | 12 values |
| 4 | No `simulation_instance` table yet (2.1 creates it) | `[V]` | `grep -rn "simulation_instance" backend/` | absent → **`instance_id` is an unconstrained integer here; 2.1 adds the FK.** Column is still non-null |
| 5 | Riverside pack loads and scores | `[V]` | `cd backend && PYTHONPATH=. python3 -m app.engine.score riverside_r3` | decomposition emitted; the pinned `order_fulfilment` line (tech `0.750`/org `0.507`/mgmt `0.657`) |
| 6 | **The four round-evolution inputs 1.6 produces already exist on the engine snapshot with defaults** (decision 9) | `[V]` | `grep -n "action_history\|available_funds_by_round\|debt_ratio_by_capability" backend/app/engine/state.py; grep -n "placement" backend/app/engine/state.py` | `action_history: tuple[ActionRecord, ...] = ()`, `available_funds_by_round: tuple[int, ...] = ()`, `debt_ratio_by_capability: dict[str,float] \| None = None`, `ArchNode.placement: str \| None = None` all present → 1.6 populates, never redefines |
| 7 | **`ActionRecord` shape and the closed `ACTION_TYPES` set are frozen** (decision 9/CC-D10) | `[V]` | `grep -n "class ActionRecord\|action_type\|locked_round\|target_key" backend/app/engine/state.py; grep -c '"' backend/app/casepack/checks.py` — inspect `ACTION_TYPES` | `ActionRecord(action_type, locked_round, capability, target_key, cost)`; `ACTION_TYPES` = the ten keys (`checks.py:13-24`) |
| 8 | **The 1.5 entry points 1.6 orchestrates exist and are pure** (decision 11) | `[V]` | `grep -n "def advance_ledger\|def resolve_events\|def project_signal_state\|def outage_duration\|def failed_node" backend/app/engine/ledger.py backend/app/engine/events.py; grep -rnE "session\|open\(\|random\.\|datetime\.now" backend/app/engine/` | all five functions present; zero I/O hits (engine purity, 1.5 CC8) |
| 9 | **The `signal` table must store every `LedgerSignal` field** (decision 10) | `[V]` | `grep -n "class LedgerSignal" -A18 backend/app/engine/ledger.py` | 14 fields incl. `episode_id`, `cleared_by`, `was_actionable`, `cheapest_fix_when_raised` — the frozen persistence shape |
| 10 | **The frozen 1.4 pin is present and green at base** (decision 12/I10) | `[V]` | `cd backend && PYTHONPATH=. python3 -m pytest tests/test_engine_scoring.py -q` | pass |

Row 4 matters: this packet must not wait for 2.1, but it must not omit the column either.
Rows 6–9 confirm the central reconciliation finding: **the merged 1.5 engine already declares
every input 1.6 owes it, with defaults** — a builder who finds any row FAIL has hit a spec/code
conflict and **STOPs** (`GOVERNANCE §7`), it does not adapt the engine.

---

## 8. Build steps

0. **O4 ruling is recorded (§4): responsiveness is read at step 12 from the advanced ledger,
   not at step 9.** Build steps 9–12 to this order.
1. **State model + migrations**, including the `signal` table at the frozen `LedgerSignal` shape
   (decision 10). *Verify:* I4 on every table; `alembic upgrade head` then `downgrade` then
   `upgrade` cleanly.
2. **Decision sheet application, steps 1–6**, including deriving `ActionRecord` rows from
   committed `decision_line`s (decision 9). *Verify:* I8 partial-update property test.
3. **Pool recomputation + graph rebuild, steps 7–8.** *Verify:* in-flight items absent
   until `arrival_round` (O2).
4. **Snapshot assembly + resolution steps 9–12** — build the `TeamState`/prior-`LedgerSignal`
   snapshot (§5.1a) and call `advance_ledger` → `resolve_events` → `outage_duration` →
   re-`advance_ledger` (fire stamp) → `project_signal_state` → `score_team` (§5.2, decision 11).
   *Verify:* I5 (single re-score); I9 (re-raise opens a new episode, prior row unchanged); a fired
   event changes the score exactly once.
5. **Debt, TCO reconciliation, scorecard, `RoundResult`, steps 13–14** — populate
   `debt_ratio_by_capability` from the debt ledger (decision 9). *Verify:* I6, I7.
6. **Lock / advance state machine.** *Verify:* O1 and O3 behaviours; locked state rejects
   decision writes.
7. **Six-round integration run** on Riverside with a scripted decision sequence.
   *Verify:* six immutable results; opex/`available_funds_by_round` ratchets; `missed_signals`
   populated; **I10 — the R3 projection keeps the 1.4 pin byte-identical**.

---

## 9. Definition of Done

*Filled by the builder on `build/1.6-round-runner` (finding 1.6-A-006); the independent audit
returned **PASS WITH FINDINGS** (`findings/1.6-round-runner-2026-08-22.md`, no Blocking).*

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–10 | ✅ | All 10 PASS, reported before code (builder report §Pre-Flight). E.g. row 5 `python -m app.engine.score riverside_r3` → order_fulfilment tech 0.750/org 0.507/mgmt 0.657; row 10 pin green. |
| **O4 ordering ruling recorded before build (STOP)** | ✅ | Build step 0: responsiveness read at step 12 from the advanced ledger, not step 9. `runner.advance()` step 9 is a provisional pass (discarded); step 12 `score_team` is authoritative (finding 1.6-SR-001). |
| Steps 0–7 verified | ✅ | `runner.py` implements steps 1–14; `test_round_runner.py` + `--full` cover them; A-002 (estate-mutation of steps 2/4–6) registered as a ruled deferral (§ below). |
| I1–I10 | ✅ | `check_round_invariants.py` (I1/I3/I4/I5/I6/I7/I9 green); `test_round_runner.py` (I5/I8/I9 property + plants); `test_round_pin.py` (I10 seam + plants); I2 by `check_engine_purity.py` (engine unchanged). |
| O1, O2, O3 recorded; O4 ruled | ✅ | `test_round_runner.py::test_o1_*`, `test_o2_in_flight_*`, `test_o3_*`; O4 folded into §5.2. |
| Resolution order matches §5.2 exactly; steps 10–12 bind to the merged entry points (decision 11) | ✅ | `runner.advance()` calls `advance_ledger → resolve_events → outage_duration/failed_node → advance_ledger(fired_signals) → project_signal_state → score_team`. |
| **The four round-evolution inputs populated at the frozen shape (decision 9/CC-D6/7/8/10)** | ✅ | `--full` R6 snapshot: `action_history=[(scale_node,3)…(scale_node,6)]`; `available_funds_by_round=(282000,142000,18000,88000,82000,82000)`; `debt_ratio_by_capability` a dict over all 7 caps (never None); `ArchNode.placement ∈ {on_prem,saas}`, `hybrid` count = 0. |
| **`signal` table round-trips every `LedgerSignal` field; ledger append-only (I9)** | ✅ | `\d signal` = 14 LedgerSignal fields, PK `(instance_id,team_id,key,episode_id)`; `test_i9_*` (re-raise opens ep2, prior row byte-unchanged; plant overwrite FAILS). |
| **1.4 pin byte-identical after the six-round seed (I10)** | ✅ | `pytest tests/test_engine_scoring.py` green after `--full` (tech 0.750008/org 0.507003/mgmt 0.656778/realised 0.249744); `test_round_pin.py` seam + plants. **Note:** the pin is preserved hermetically + via the seam; the `--full` seed reproduces the credited/un-credited *pattern*, not the number (R3 realised ≈0.2038) — corrected §5.5 (1.6-A-007). |
| Six-round run produces six immutable results | ✅ | `SELECT count(*) FROM round_result WHERE instance_id=1` = 6, opex 47000→53000→58300→62200→66000→70000. |
| Migration up/down/up clean | ✅ | `alembic upgrade head` → `downgrade base` → `upgrade head` clean on Postgres (`20260822_0002_round_runner`). |
| `CONTRACTS.md` updated if any field shape changed | ✅ | No change — 1.6 populates existing frozen shapes; the `LedgerSignal`/`action_history`/`available_funds` entries already name 1.6 as producer/persister. |
| **OPEN-REGISTER §M reconciliation — CC-D6/7/8/10 re-tested on the shipped commit, rows updated in the same commit (GOVERNANCE §9)** | ✅ | `findings/OPEN-REGISTER.md §M` — CLOSED with evidence table, in the build commit. |
| Instance-isolation canary | ✅ **partial** | `check_instance_isolation.py` green (two instances, zero cross-reads). Single-casepack limitation registered as 1.6-A-008 (full cross-casepack canary at 2.2). |
| **Seed** — `--full` produces six rounds from a clean DB in one command | ✅ | `python -m app.seed.demo --full` from a clean migrated DB → six RoundResults computed. |
| Every later packet can reproduce the demo state with it | ✅ | `--full` is idempotent (wipes instance 1 first); one command, any session. |
| Auth / browser canaries | **N-A** | Headless; no UI/auth in 1.6. |
| Independent spec review (SPEC_PROTOCOL §11) before dispatch — Heavy tier | ✅ | Completed before dispatch (`bb3ee26`, folded `1.6-SR-001` at `23eb6c7`). |
| Independent audit (Heavy tier) | ✅ | PASS WITH FINDINGS, no Blocking (`findings/1.6-round-runner-2026-08-22.md`); A-001 fixed, A-007/A-006 addressed, A-002/3/4/5/8/9 registered with owners. |

---

## 10. Compliant route + rejected alternative — the reconciliation interfaces *(SPEC_PROTOCOL §4.1)*

**Producing `action_history` (CC-D10).**
*Compliant route:* 1.6 emits one `ActionRecord` per committed `decision_line` whose
`category` maps to an action type, at commit (lock) time — `action_type` from the category
mapping, `locked_round` = the lock round, `capability`/`target_key` from the decision, `cost` =
the committed capex; the history is append-only across rounds and handed to the engine on the
snapshot (§5.1a). *Rejected alternative:* have the 1.5 engine re-derive which action cleared a
signal from the raw `decision_line` table — rejected: the engine is pure (I2) and reads a frozen
snapshot, never the database; deriving inside the engine would put persistence in the pure core.

**The snapshot-assembly seam (§5.1a).**
*Compliant route:* 1.6 rebuilds the immutable `TeamState` + prior `LedgerSignal` tuple from its
own tables each round and calls the pure engine functions in the §5.2 order; persistence tables
are the single source of truth, snapshots are derived views. *Rejected alternative:* keep a
long-lived mutable `TeamState` object and mutate it in place across rounds — rejected: it breaks
`RoundResult` reproducibility (decision 2) and the frozen-dataclass immutability the engine
relies on; a later round could silently alter an earlier round's inputs.

**Persisting the ledger (decision 10).**
*Compliant route:* one `signal` row per `(instance, team, key, episode_id)` carrying every
`LedgerSignal` field; a re-raise INSERTs a new `episode_id`, never UPDATEs a prior row (I9).
*Rejected alternative:* a single mutable row per `(key)` updated in place — rejected: it destroys
episode history the responsiveness projection and the debrief depend on (`1.5 contract-spec §5.2`).

---

## 11. Reconciliation changelog

- **v1.1** (2026-08-22) — **bounded reconciliation** of the 2026-07-26 spec against the merged
  1.4-closeout and 1.5 contracts (`GOVERNANCE §6.3`: 1.6 confirmed **Heavy**). No scope expansion.
  - **Header/§0/§2:** re-based on `SPEC_PROTOCOL v1.3`; added the 2026-08-22 read set (1.5
    contract-spec, merged engine files, CONTRACTS entries, OPEN-REGISTER §M/§O); declared the
    scoring-input production and Heavy tiering.
  - **§3 decisions 9–12 (new):** 1.6 *populates* the four round-evolution inputs
    (`action_history`/`available_funds_by_round`/`debt_ratio_by_capability`/`ArchNode.placement`) —
    already frozen on `state.py` with defaults; persists the `LedgerSignal` ledger; calls the merged
    1.5 entry points; consumes the 1.4 pin + 1.5 contracts, never redefining them.
  - **§4 O4 (new STOP):** surfaced an ordering tension between the authored step-9 score and the
    step-10 ledger-advance that produces the `SignalState` the responsiveness term reads — routed to
    the authority (`GOVERNANCE §7`), not resolved silently; a compliant route is proposed for the ruling.
  - **§5.1/§5.1a/§5.2/§5.3/§5.5:** froze the `signal` table to the `LedgerSignal` shape; added the
    snapshot-assembly seam; bound resolution steps 10–12 to `advance_ledger`/`resolve_events`/
    `outage_duration`/`project_signal_state`/`score_team` (the demo+test sequence); reconciled the
    `RoundResult` signal/event/missed-signal shapes with the engine's evidence dicts; tied the
    `--full` seed to the real ledger transition (supersedes hand-authored `--with-signals`).
  - **§6 I9/I10 (new):** ledger append-only/immutable; 1.4 pin survives the six-round seed — each
    with a planted-defect falsification check (`SPEC_PROTOCOL §4.3`); noted I5's self-referential
    grep is not a real check.
  - **§7 rows 6–10 (new); row 5 corrected:** verify the frozen inputs, `ActionRecord`, the entry
    points, the `LedgerSignal` shape, and the base pin all exist — a FAIL is a STOP, not an adaptation.
  - **§8/§9:** build step 0 (confirm O4 ruling); steps bound to the entry points and input
    production; DoD adds the reconciliation rows and the §M register reconciliation.
  - **§10 (new):** compliant route + rejected alternative for each reconciliation interface.
  - **CONTRACTS.md:** no change required — the `LedgerSignal`, `action_history`/
    `available_funds_by_round`, and outage-duration entries already name 1.6 as producer/persister
    and match `state.py`/`ledger.py`. Ownership unchanged; nothing to re-home.
- **v1.0** (2026-07-26) — initial authoring under `SPEC_PROTOCOL v1.1`, before 1.4-closeout and 1.5
  landed. State model, resolution order, `RoundResult` immutability, opex ratchet, debt ledger,
  partial-update semantics, lock/advance.
