# 1.6 — Round Runner · Build Spec

**Authored under** `SPEC_PROTOCOL.md` v1.1 · **Author:** Claude · **Date:** 2026-07-26
**Phase:** 1 · **Depends on:** 1.1, 1.4, 1.5 · **Blocks:** 1.7, 2.3, 3.5, 3.6

> The orchestrator. 1.4 and 1.5 are pure; this is where state, ordering, and persistence
> live — which makes it the first packet where `instance_id` is non-negotiable.

---

## 0. Spec Basis

**Read in full:** `handoffs/1.4-scoring-engine/spec.md`, `handoffs/1.5-event-signal-engine/spec.md` ·
`design/05-implementation-plan.md` §1.1 · `BECSR/async-round-deadlines.md` (the lock and
advance semantics 2.3 will wrap) · `GOVERNANCE.md` §4.5 · `CONTRACTS.md` `instance_id`,
`decision_line.category`.

**Extraction sufficiency:** covered. BECSR's Django implementation was read for
*semantics* (lock reasons, grace, auto-advance), not for code — different stack.

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
and TCO forecast accuracy (`design/02` §D).

**Casepack keys read:** all, via the loaded pack.
**Casepack-identity branching:** none — I1.
**Instance scoping:** **every table this packet creates carries `instance_id`, non-null,
from creation** (`GOVERNANCE.md §4.5`). Every read filters on it. This is the first packet
where BECSR's retrofit pain is avoidable, and I4 enforces it.
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

---

## 4. Open decisions

| # | Question | Criteria | Reporting |
|---|---|---|---|
| **O1** | Can a locked round be unlocked? | **Default: yes, instructor-only, and it invalidates the `RoundResult` rather than editing it.** Instructors need it in a live class; students must not | Record |
| **O2** | Where do lead-time purchases live between order and arrival? | **Default: an `in_flight` collection on team state, materialising into the graph at `arrival_round`.** Not in the graph early — that would inflate capacity | Record |
| **O3** | Does the engine run at lock, or at advance? | **Default: at advance.** Lock freezes input; advance produces results. Separating them lets an instructor lock a section and review before committing outcomes | Record |

---

## 5. Design

### 5.1 State model — all `instance_id`-scoped

```
team_state            current round, strategy (versioned), cash, opex run-rate
arch_node             deployed items: catalog_key, placement, config_tier,
                      installed_round, retired_round
arch_edge             integrations: source, target, entity, mode
deployment_org_state  trained_pct, process_redesigned, sponsor, owner
platform_service      placement, capacity, utilisation
org_unit              headcount, resistance
it_staff              fte, load
in_flight             ordered, not yet arrived (O2)
decision_line         one row per decision, category per CONTRACTS.md
signal                the 1.5 ledger, persisted
debt_item             deferrals with accrual
tco_forecast          selected cost categories vs actuals
round_result          immutable, one per (instance, team, round)
```

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
 9  1.4 scoring → per-capability decomposition
10  1.5 watch rules → raise / escalate / clear signals
11  1.5 events → fire, blast radius, outcome application
12  re-score capabilities affected by event outcomes        ← single re-entry only
13  accrue debt for deferrals; reconcile TCO forecasts
14  roll up Balanced Scorecard; write immutable RoundResult
```

Step 12 runs **exactly once**. An event changes state, so scores must reflect it — but
iterating to a fixed point makes outcomes unexplainable, and explainability is the product.
Invariant I5.

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

---

## 7. Pre-Flight Verification Register

| # | Claim | Tag | Check | Expected |
|---|---|---|---|---|
| 1 | 1.4 and 1.5 merged and pure | `[V]` | `grep -rn "session\|random\." backend/app/engine/` | zero |
| 2 | Alembic chain exists from 0.2 | `[V]` | `ls backend/alembic/versions/` | baseline present |
| 3 | `decision_line.category` enum matches CONTRACTS | `[V]` | `grep -A14 "decision_line.category" CONTRACTS.md` | 12 values |
| 4 | No `simulation_instance` table yet (2.1 creates it) | `[V]` | `grep -rn "simulation_instance" backend/` | absent → **`instance_id` is an unconstrained integer here; 2.1 adds the FK.** Column is still non-null |
| 5 | Riverside pack loads and scores | `[V]` | `python -m app.engine.score packs/riverside_grocery <fixture>` | decomposition emitted |

Row 4 matters: this packet must not wait for 2.1, but it must not omit the column either.

---

## 8. Build steps

1. **State model + migrations.** *Verify:* I4 on every table; `alembic upgrade head` then
   `downgrade` then `upgrade` cleanly.
2. **Decision sheet application, steps 1–6.** *Verify:* I8 partial-update property test.
3. **Pool recomputation + graph rebuild, steps 7–8.** *Verify:* in-flight items absent
   until `arrival_round` (O2).
4. **Resolution steps 9–12.** *Verify:* I5; a fired event changes the score exactly once.
5. **Debt, TCO reconciliation, scorecard, `RoundResult`, steps 13–14.** *Verify:* I6, I7.
6. **Lock / advance state machine.** *Verify:* O1 and O3 behaviours; locked state rejects
   decision writes.
7. **Six-round integration run** on Riverside with a scripted decision sequence.
   *Verify:* six immutable results; opex ratchets upward; `missed_signals` populated.

---

## 9. Definition of Done

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–5 | | |
| Steps 1–7 verified | | |
| I1–I8 | | |
| O1, O2, O3 recorded | | |
| Resolution order matches §5.2 exactly | | |
| Six-round run produces six immutable results | | |
| Migration up/down/up clean | | |
| `CONTRACTS.md` updated if any field shape changed | | |
| Instance-isolation canary | | **partial** — column enforced; full canary at 2.2 |
| **Seed** — `--full` produces six rounds from a clean DB in one command | | |
| Every later packet can reproduce the demo state with it | | |
| Auth / browser canaries | | **N-A** — headless |
