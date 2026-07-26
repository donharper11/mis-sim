# 1.5 — Event & Signal Engine · Build Spec

**Authored under** `SPEC_PROTOCOL.md` v1.1 · **Author:** Claude · **Date:** 2026-07-26
**Phase:** 1 · **Depends on:** 1.1, 1.4 · **Blocks:** 1.6, 1.7, 3.2, 4.3

> **Signals are the game telling you what is coming. Events are the bill.**
> Every serious event is preceded by a signal. Nothing ambushes a student — that is what
> makes responsiveness fair to score.

---

## 0. Spec Basis

**Read in full:** `design/02-traceability-matrix.md` §C (signal responsiveness) ·
`design/04-decisions-g1-g6.md` (staffing affects recovery duration) ·
`handoffs/1.1-casepack-schema/spec.md` §5.6 (watch rules, event preconditions) ·
`handoffs/1.4-scoring-engine/spec.md` §5.1 (SPOFs arm events, do not reduce reliability) ·
`CONTRACTS.md` `signal.cleared_by[]`.

**Extraction sufficiency:** covered.

---

## 1. Purpose and scope

**In scope:** evaluate watch rules at round close and raise/escalate/clear signals ·
maintain the signal ledger with the two timestamps responsiveness depends on ·
evaluate event preconditions and fire the deck · compute blast radius by graph traversal ·
compute outage duration including the staffing modifier · raise privacy obligations as
signals.

**Out of scope:** scoring the responsiveness ratio (1.4 consumes this ledger) ·
persistence (1.6) · inbox UI (4.3) · authoring the deck (1.3).

---

## 2. Project-specific statements

**Scoring factors touched:** *supplies* signal responsiveness (`design/02` §C) and open
privacy obligations (§D); *consumes* Tech capacity/reliability from 1.4.
**Casepack keys read:** `watch_rules`, `events`, `obligation_rules`, `capabilities`.
**Casepack-identity branching:** none — I1. **Instance scoping:** pure, like 1.4 — I2.
**Business-language check:** emits event **keys**; prose comes from `labels.yaml`. I3.

---

## 3. Settled decisions

1. **Pure, like 1.4.** State in, results out. Determinism is what makes 1.7 work.
2. **No randomness anywhere.** Events fire on preconditions, never on dice. A student who
   loses must be able to see exactly why.
3. **Every event has a precedent signal** — enforced by 1.2's check E20 and by I5 here.
4. **SPOFs arm events; they do not reduce reliability** (1.4 decision 5).
5. **Blast radius is a traversal**, not an authored list. Remove the failed node, ask which
   capabilities lost their serving path.
6. **Deck draws against the declared strategy** via `strategy_affinity`.
7. **Privacy obligations reuse the signal machinery entirely** (`design/04`) — no parallel
   system.

---

## 4. Open decisions

| # | Question | Criteria | Reporting |
|---|---|---|---|
| **O1** | "Actionable" for the responsiveness denominator: exclude signals whose only fix was never affordable? | **Default: exclude if no clearing action was affordable at any point while open.** Forgiving first; tighten after 1.7 shows the distribution. (Argument for counting them: unaffordability is often self-inflicted by earlier overspending) | Record |
| **O2** | Can two events fire on the same capability in one round? | **Default: yes, but cap at 2 per capability per round** and log suppressions. Uncapped cascades produce unteachable rounds | Record |
| **O3** | Does clearing a signal after an event has fired still earn partial responsiveness credit? | **Default: no credit, but record it** — it feeds follow-through instead | Record |

---

## 5. Design

### 5.1 Signal lifecycle

```
       evaluate watch rules at round close
                    │
      metric crosses warn_above ──▶ RAISE   (first_shown_round = R)
                    │
      crosses critical_above ────▶ ESCALATE (severity = critical)
                    │
      resolving action taken ────▶ CLEARED  (cleared_round, lead_time)
                    │
      event precondition met ────▶ FIRED    (fire_round)
```

Ledger row — these fields exist *because* 1.4's responsiveness factor needs them:

```python
{ "key": "ORD-CAP-01", "capability": "order_fulfilment",
  "metric": "capacity_utilisation", "value": 1.11,
  "severity": "critical", "status": "open",
  "first_shown_round": 2, "cleared_round": None, "fire_round": 4,
  "cleared_by": ["scale_node", "add_node", "move_to_cloud"],
  "was_actionable": True, "cheapest_fix_when_raised": 60000 }
```

`cheapest_fix_when_raised` is what makes the debrief line possible:
*"cheapest fix available in round 2: $60,000 — cost of not fixing it: $142,000."*

### 5.2 Event resolution

```
for each event in deck:
    if all preconditions true
       and strategy_affinity matches or is empty
       and not already fired (unless repeatable)
       and per-capability cap not exceeded (O2):
           fire → outcomes → blast radius → scorecard deltas
```

Precondition types (closed set; a new type needs this spec to change):

```
signal_open · demand_exceeds_capacity · node_is_spof · placement_count
policy_contradiction · adoption_below · staffing_over · entity_unowned
sponsor_unassigned · round_equals · debt_above
```

### 5.3 Blast radius and duration

```
blast_radius(node) = remove node from graph
                     → capabilities with no surviving serving path

duration_hours = base_rto(node)
               × (1.0 if failover_exists else no_failover_multiplier)
               × staffing_modifier          # G1: over-committed IT recovers slower
```

Same event card, two teams, opposite outcomes — determined entirely by whether a failover
edge exists. No authored branching.

### 5.4 Privacy obligations

`obligation_rules` in the pack produce signals on the same ledger when sensitive entities
are held under permissive policy. Ignored obligations arm events (regulator letter, subject
access request, employee snooping) exactly as capacity signals arm outages.

---

## 5.5 Seed — a signal ledger with history *(GOVERNANCE §4.9)*

```
seed        extends riverside_r3 with rounds 1-3 of signal history
command     python -m app.seed.demo --scenario riverside_r3 --with-signals
demonstrate ORD-CAP-01 raised R2 at 0.83 · escalated R3 at 1.11
            saturday_queue_collapse FIRES at R4 on the do-nothing path
            and does NOT fire on a path where the signal was cleared at R3
            blast radius computed by traversal, printed
```

Two paths from one seed is the demonstration — the same event card, opposite outcomes.

---

## 6. Invariants

| # | Invariant | Check | Expected |
|---|---|---|---|
| I1 | No pack-identity branching | `grep -rniE "riverside\|grocer" backend/app/engine/events*` | zero |
| I2 | Pure — no I/O, clock, randomness | `grep -rnE "random\.\|datetime\.now\|session\|open\(" backend/app/engine/events*` | zero |
| I3 | No displayed English | `grep -rnE '"[A-Z][a-z]+ [a-z]+ [a-z]+' backend/app/engine/events*.py \| grep -v '#\|"""\|raise'` | zero |
| I4 | Determinism | same state 100× → one result hash | 1 |
| I5 | Every event has a precedent signal path | for each event, assert ≥1 precondition references a signal or a signal-raising metric | all pass |
| I6 | Blast radius is derived, never authored | `grep -rn "blast_radius" packs/` | zero hits in pack files |
| I7 | Cap enforced | property test: 5 satisfiable events on one capability → 2 fire, 3 logged | holds |

---

## 7. Pre-Flight Verification Register

| # | Claim | Tag | Check | Expected |
|---|---|---|---|---|
| 1 | 1.4 merged; graph analysis available | `[V]` | `grep -n "def serving_path\|def articulation" backend/app/engine/graph.py` | both present |
| 2 | Riverside pack has watch rules and events | `[V]` | `grep -c "^- key:" packs/riverside_grocery/{watch_rules,events}.yaml` | ≥1 and ≥20 |
| 3 | `ORD-CAP-01` exists with the 0.3 semantics | `[V]` | `grep -A4 "ORD-CAP-01" packs/riverside_grocery/watch_rules.yaml` | warn 0.80, critical 0.95 |
| 4 | The action-type enum from 1.2 E05 exists | `[V]` | `grep -rn "class ActionType\|ACTION_TYPES" backend/app/` | present |
| 5 | 1.2 check E20 passes on Riverside | `[A]` | `validate_casepack packs/riverside_grocery \| grep E20` | no E20 error |

---

## 8. Build steps

1. **Watch-rule evaluation + ledger.** *Verify:* Riverside R2 raises `ORD-CAP-01` at
   utilisation 0.83 with `first_shown_round = 2`.
2. **Escalation and clearing.** *Verify:* R3 escalates to critical; a `scale_node` action
   clears it and records `lead_time`.
3. **Event preconditions + firing + cap.** *Verify:* `saturday_queue_collapse` fires at R4
   for the do-nothing path and **does not fire** when the signal was cleared at R3. I7.
4. **Blast radius + duration + staffing modifier.** *Verify:* removing the WAN link darkens
   the expected capability set; adding a failover edge yields an empty radius from the
   identical event.
5. **Privacy obligations on the same ledger.** *Verify:* a permissive policy over a
   sensitive entity raises an obligation; clearing it behaves like any signal.

---

## 9. Definition of Done

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–5 | | |
| Steps 1–5 verified | | |
| I1–I7 | | |
| O1, O2, O3 recorded | | |
| Ledger carries both timestamps 1.4 needs | | |
| `cheapest_fix_when_raised` populated | | |
| Two-team divergence demonstrated from one event card | | |
| **Seed** — signal history seeded; both paths demonstrated from one seed | | |
| Browser / auth / instance canaries | | **N-A** — pure, headless |
