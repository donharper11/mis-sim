# 1.5 — Event & Signal Engine · Build Spec

**Authored under** `SPEC_PROTOCOL.md` v1.1 · **Author:** Claude · **Date:** 2026-07-26
**Spec version:** v1.1 · **Revised:** 2026-08-15, against merged 1.1 and the 1.2 audit
**Phase:** 1 · **Depends on:** **1.1 (three schema additions, §10) · 1.3 (the deck) · 1.4**
**Blocks:** 1.6, 1.7, 3.2, 4.3

> **Signals are the game telling you what is coming. Events are the bill.**
> Every serious event is preceded by a signal. Nothing ambushes a student — that is what
> makes responsiveness fair to score.

---

## 0. Spec Basis

**Read in full:** `design/02-traceability-matrix.md` §C (signal responsiveness) ·
`design/04-decisions-g1-g6.md` (staffing affects recovery duration) ·
`handoffs/1.1-casepack-schema/spec.md` §5.6 (watch rules, event preconditions) ·
`handoffs/1.4-scoring-engine/spec.md` §5.1 (SPOFs arm events, do not reduce reliability) ·
`CONTRACTS.md` `signal.cleared_by[]` ·
**`findings/1.2-2026-08-14-audit.md`** — `1.2-001` and `1.2-013` are this packet's inputs ·
**`handoffs/1.2-validator/spec.md`** v1.2 §3 decision 7, §5.2.

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
3. **Every event has a precedent signal** — enforced by **I5 here** and by 1.2's `E20`
   *as widened in v1.2*. **Corrected v1.1:** the original text credited `E20` alone, which
   does not check this. `E20` guarantees each *capability* can raise a signal; it says
   nothing about whether a given *event* has a reachable precedent. `1.2-013` is the proof —
   two Riverside cards wait on a `critical` that could never arrive, and `E20` was silent.
   The guarantee is **I5's**, and I5 is tightened below to check reachability, not reference.
4. **SPOFs arm events; they do not reduce reliability** (1.4 decision 5).
5. **Blast radius is a traversal**, not an authored list. Remove the failed node, ask which
   capabilities lost their serving path.
6. **Deck draws against the declared strategy** via `strategy_affinity`.
7. **Privacy obligations reuse the signal machinery entirely** (`design/04`) — no parallel
   system. **Confirmed by the user 2026-08-15** against carving them into a separate packet:
   ethics is not a subsystem, and a deferred ethics layer is the one most likely to be cut
   before pilot. The cost is accepted — see §10, this packet is **gated on 1.1**.
8. **A watch rule declares its `metric_kind`: `threshold` or `presence`.** Ruled by the user
   2026-08-15, resolving the question 1.2's decision 7 deferred here. See §5.1a.
9. **Deck coverage is measured per strategy, not per round.** Ruled by the user 2026-08-15.
   `Event` gains **no round binding**; round timing stays emergent from preconditions,
   because two timing systems — one authored, one computed — is the design's central rule
   competing with itself. See §5.2a.
10. **Presence signals raise at `critical`, never at `warning`.** A presence condition is
    true or it is not; there is no magnitude to be mildly concerned about. Deriving a
    warning tier would require inventing one. See §5.1a.
11. **A signal's severity is a property of the signal, not of the rule that raised it.**
    Both kinds write the same ledger row and 1.4 consumes one shape. This is what keeps the
    two evaluation paths from becoming two subsystems.

---

## 4. Open decisions

| # | Question | Criteria | Reporting |
|---|---|---|---|
| **O1** | "Actionable" for the responsiveness denominator: exclude signals whose only fix was never affordable? | **Default: exclude if no clearing action was affordable at any point while open.** Forgiving first; tighten after 1.7 shows the distribution. (Argument for counting them: unaffordability is often self-inflicted by earlier overspending) | Record |
| **O2** | Can two events fire on the same capability in one round? | **Default: yes, but cap at 2 per capability per round** and log suppressions. Uncapped cascades produce unteachable rounds | Record |
| **O3** | Does clearing a signal after an event has fired still earn partial responsiveness credit? | **Default: no credit, but record it** — it feeds follow-through instead | Record |
| **O4** | `N` for the per-strategy draw check (§5.2a) | **Default: 6, one per round.** Riverside fails on 3 of 4 strategies at this value, which is `CG-2` made visible. Lower it only if 1.7 shows the deck is unauthorable at 6 | Record |
| **O5** | Can a presence signal be cleared in the same round it is raised? | **Default: yes.** A presence condition removed within the round is genuinely resolved, and `lead_time = 0` is a legitimate, maximally responsive value. Threshold signals inherit the same rule | Record |

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
{ "key": "ord_cap_01", "capability": "order_fulfilment",
  "metric": "capacity_utilisation", "metric_kind": "threshold", "value": 1.11,
  "severity": "critical", "status": "open",
  "first_shown_round": 2, "cleared_round": None, "fire_round": 4,
  "cleared_by": ["scale_node", "add_node", "move_to_cloud"],
  "was_actionable": True, "cheapest_fix_when_raised": 60000 }
```

> **Key case corrected v1.1.** v1.0 wrote `ORD-CAP-01` here, in pre-flight row 3 and in build
> step 1. The pack authors `ord_cap_01`. Machine keys are snake_case and never displayed
> (`CONTRACTS.md`, 1.1's I3), and a builder grepping for the uppercase form finds nothing.

`cheapest_fix_when_raised` is what makes the debrief line possible:
*"cheapest fix available in round 2: $60,000 — cost of not fixing it: $142,000."*

### 5.1a Two evaluation paths, one ledger *(new v1.1 — §3 decision 8)*

`WatchRule` gains **`metric_kind`**, a 1.1 schema addition (§10):

```yaml
- key: ord_cap_01                      - key: sec_identity_01
  metric_kind: threshold                 metric_kind: presence
  metric: capacity_utilisation           metric: missing_identity_access
  warn_above: 0.80                       warn_above: null
  critical_above: 0.95                   critical_above: null
```

```
evaluate(rule, state):

    threshold │ value = metric(state)                    → float
              │ value > critical_above  → raise CRITICAL
              │ value > warn_above      → raise WARNING
              │ else                    → no signal
              │
    presence  │ value = metric(state)                    → bool
              │ value is True           → raise CRITICAL   (decision 10)
              │ else                    → no signal
```

**Why this and not a boolean metric with `critical_above: 0`.** The rejected alternative
needed no schema change and kept one evaluation path, but it encodes a boolean as a numeric
threshold — `critical_above: 0` is not readable as *"fires when identity access is missing"*
by the instructor who authors packs 2–5, and the schema is the artifact those authors work
from. The declared kind is self-documenting. **The cost is real and is accepted:** two paths
instead of one, and a schema change that ripples into 1.2 (§10).

**Both paths write the same ledger row.** `metric_kind` is recorded on the row for the
debrief's benefit, but `severity`, `first_shown_round`, `cleared_round` and `cleared_by`
behave identically, and **1.4 must never branch on it** (I8).

**Clearing a presence signal** is the same mechanism: an action in `cleared_by` is taken and
the metric goes false. There is no de-escalation path, because there is no tier below
critical to fall to.

### 5.2 Event resolution

```
for each event in deck:
    if all preconditions true
       and strategy_affinity matches or is empty
       and not already fired (unless repeatable)
       and per-capability cap not exceeded (O2):
           fire → outcomes → blast radius → scorecard deltas
```

**Precondition types and the fields each needs.** The closed set stands; **what changes in
v1.1 is that six of the eleven types had no schema fields to carry their parameters**, and
would have been unbuildable. `EventPrecondition` today carries only
`type · signal · severity · capability · ratio`.

| Type | Needs | Expressible today? |
|---|---|---|
| `signal_open` | `signal`, `severity` | ✅ the only type Riverside uses |
| `demand_exceeds_capacity` | `capability`, `ratio` | ✅ |
| `adoption_below` | `capability`, `ratio` | ✅ |
| `staffing_over` | `ratio` | ✅ |
| `debt_above` | `ratio` | ✅ |
| `node_is_spof` | a **node** key | ❌ no `node` field |
| `entity_unowned` | an **entity** key | ❌ no `entity` field |
| `placement_count` | a placement + an integer | ❌ neither field |
| `policy_contradiction` | two **policy** keys | ❌ no `policy` field |
| `sponsor_unassigned` | `capability` | ⚠️ works, but overloads `capability` |
| `round_equals` | an **integer round** | ❌ `ratio` is a float and would be a lie |

**Five build cleanly, six do not.** `1.2-016` item 3 is the precedent: a spec that describes
a check the schema cannot express produces either a silent proxy or a stopped builder. The
fields in §10 are what make the remaining six real. **A builder must not improvise them into
`ratio`.**

### 5.2a Deck coverage *(new v1.1 — §3 decision 9)*

`CG-2` is *"3 event cards for 6 rounds × 4 strategies — strategies that draw nothing."*
1.2's `W05` was rewritten to deck **depth** (`len(events) < rounds`) because `Event` carries
no round field, and depth cannot see CG-2's real shape: a six-card deck all affine to one
strategy passes it.

**The check is per strategy, not per round:**

```
for each strategy S:
    draws(S) = events whose strategy_affinity includes S, or is empty
    assert len(draws(S)) >= N                                     # N = 6, O4
```

Riverside today, computed from `events.yaml`:

```
cost_leadership              3     ← every card
customer_supplier_intimacy   2
differentiation              1
focus_strategy               1
```

At `N = 6` all four fail, and three fail badly. That is `CG-2` made visible for the first
time, and it is 1.3's to close.

**This check belongs to 1.2, not to 1.5** — it is a pack-authoring check, and 1.2 is the
validator. 1.5 specifies it because 1.5 owns the question; **1.2 implements it as `W08`**
(§10). It is a `WARN`, not an `ERROR`: a thin deck is authorable content, not a broken pack,
and 1.7's calibration is where a deck that starves a strategy actually fails.

**Round timing stays emergent.** No `earliest_round` / `latest_round`, by decision 9. Two
timing systems — one authored, one computed from preconditions — would let a card satisfy
its preconditions in a round its binding forbids, and the resolution of that conflict is a
rule no student could see. *"Events fire on preconditions, never on dice"* also means never
on a calendar.

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

**`obligation_rules.yaml` does not exist.** It is `CG-5`, and it is not a section 1.1's
schema defines — which is why 1.2 cannot report its absence and the whole Ch 4 ethics layer
is currently inert. By decision 7 it stays here rather than being carved out, so **this
packet is gated on 1.1 adding the section** (§10). The shape 1.5 requires:

```yaml
obligation_rules:
  - key: customer_pii_retention
    entity: customer                    # an entity the pack defines
    condition: policy_permits           # policy key + the permissive value
    policy: data_retention
    permissive_value: indefinite
    severity: critical                  # obligations are presence-shaped (decision 10)
    cleared_by: [add_policy, retire_component]
    arms: [regulator_letter]            # event keys this obligation can arm
    provenance: {...}
```

An obligation is **presence-shaped by construction** — the condition holds or it does not —
so it uses the presence path of §5.1a with no further machinery. That is decision 7 paying
for itself: the ethics layer costs one schema section and zero new engine paths.

> ### ⛔ `permissive_value` has no referent. This shape does not work yet. *(added 2026-08-18, `1.3-012`)*
>
> The shape above reads `policy` + `permissive_value`. **`PolicyOption` has no value field
> at all** — verified: `key · category · cost · effects · provenance`, and nothing else. A
> policy switch has no notion of the states it can be in, so `permissive_value: indefinite`
> is a string pointing at nothing.
>
> **This is a defect in this spec, not in 1.3's authoring.** 1.3 authored exactly the shape
> §5.4 specified, its hand-check found the problem, and the audit confirmed it is worse than
> reported: **no keying of policies fixes it**, because the missing thing is the vocabulary
> itself. Same class as §5.2's six unexpressible precondition types — a shape specified
> against a schema that cannot hold it.
>
> **What the ethics layer actually needs**, stated so 1.1 can build it and 1.5 can consume it:
>
> ```
> a policy must declare the STATES it can be in        options: [minimal, standard, indefinite]
> a policy must declare which state is the DEFAULT     default: indefinite
>   — the position a team holds by not deciding, which is what makes ignoring the
>     ethics layer cost something rather than being an opt-in
> an obligation then names the state that OBLIGES      permissive_value: indefinite
>   — and it now resolves, because the policy enumerates it
> ```
>
> Without `options`, three things are impossible: the validator cannot check that
> `permissive_value` names a real state (`1.2-037`'s sibling), the Security screen (4.3)
> cannot render the switch's positions, and **the engine cannot tell whether a team has
> moved off the permissive default** — which is the entire mechanism by which an ignored
> obligation arms an event.
>
> **Filed to 1.1 as §10 item 5.** Until it lands, `obligation_rules.yaml` is authored
> correctly and inert — the same status `CG-5` had before, one layer further in.

---

## 5.5 Seed — a signal ledger with history *(GOVERNANCE §4.9)*

```
seed        extends riverside_r3 with rounds 1-3 of signal history
command     python -m app.seed.demo --scenario riverside_r3 --with-signals
demonstrate ord_cap_01 raised R2 at 0.83 · escalated R3 at 1.11
            a PRESENCE rule raised at critical with no threshold crossed
            saturday_queue_collapse FIRES at R4 on the do-nothing path
            and does NOT fire on a path where the signal was cleared at R3
            blast radius computed by traversal, printed
```

Two paths from one seed is the demonstration — the same event card, opposite outcomes.

---

## 6. Invariants

| # | Invariant | Check | Expected |
|---|---|---|---|
| I1 | No pack-identity branching | `git ls-files backend/app/engine \| xargs grep -niE "riverside\|grocer"` | zero |
| I2 | Pure — no I/O, clock, randomness | `git ls-files backend/app/engine \| xargs grep -nE "random\.\|datetime\.now\|session\|open\("` | zero |
| I3 | No displayed English | `git ls-files 'backend/app/engine/*.py' \| xargs grep -nE '"[A-Z][a-z]+ [a-z]+ [a-z]+' \| grep -v '#\|"""\|raise'` | zero |
| I4 | Determinism | same state 100× → one result hash | 1 |
| I5 | **Every event's precedent signal is *reachable*, not merely referenced** | for each event precondition of type `signal_open`, resolve the named rule and assert it **can attain the required severity**: a `threshold` rule needs `critical_above` set to require `critical`; a `presence` rule can only ever attain `critical` | all pass |
| I6 | Blast radius is derived, never authored | `git ls-files backend/packs \| xargs grep -n "blast_radius"` | zero |
| I7 | Cap enforced | property test: 5 satisfiable events on one capability → 2 fire, 3 logged | holds |
| I8 | **Nothing downstream branches on `metric_kind`** | `git ls-files backend/app/engine backend/app/scoring \| xargs grep -n "metric_kind"` | hits **only** in the watch-rule evaluator and the ledger writer |

> **I5 rewritten in v1.1.** v1.0 asserted *"≥1 precondition references a signal or a
> signal-raising metric"* — reference, not reachability. Riverside satisfies the old I5 and
> is broken anyway: `inventory_audit_question` and `warehouse_rollout_gap` both require
> `wh_rollout_01` at `critical`, and that rule carries no thresholds, so the severity can
> never arrive. **Two of three cards are dead and the old I5 passes them** (`1.2-013`).
> Reachability is the property the invariant was always reaching for.
>
> **I8 is new**, and it is what stops decision 8's two evaluation paths becoming two
> subsystems. The moment 1.4 branches on `metric_kind`, presence signals have a second
> scoring path and `design/04`'s *"no parallel system"* is lost.

---

## 7. Pre-Flight Verification Register

| # | Claim | Tag | Check | Expected |
|---|---|---|---|---|
| 1 | 1.4 merged; graph analysis available | `[V]` | `grep -n "def serving_path\|def articulation" backend/app/engine/graph.py` | both present |
| 2 | Riverside has watch rules and a deck **sized for six rounds** | `[V]` | `grep -c "^- key:" backend/packs/riverside_grocery/watch_rules.yaml backend/packs/riverside_grocery/events.yaml` | `≥7` and `≥6`. **If events < 6, STOP — 1.3 has not closed CG-2** |
| 3 | `ord_cap_01` exists with the 0.3 semantics | `[V]` | `grep -A5 "key: ord_cap_01" backend/packs/riverside_grocery/watch_rules.yaml` | `warn_above: 0.80`, `critical_above: 0.95` |
| 4 | The action-type set from 1.2's E05 exists | `[V]` | `grep -n "^ACTION_TYPES" backend/app/casepack/checks.py` | present, line 12 |
| 5 | **`WatchRule.metric_kind` exists** (§10 item 1) | `[V]` | `grep -n "metric_kind" backend/app/casepack/models.py` | present. **Absent → STOP, 1.1 has not run** |
| 6 | **`obligation_rules` is a schema section** (§10 item 2) | `[V]` | `grep -n "obligation_rules\|class ObligationRule" backend/app/casepack/models.py` | present. **Absent → STOP** |
| 7 | **The six precondition fields exist** (§10 item 3) | `[V]` | `grep -nE "node:\|entity:\|policy:\|round:" backend/app/casepack/models.py` | all four present on `EventPrecondition` |
| 8 | Riverside validates with **no `E12`, no `E20`, no `E21`** | `[A]` | `validate_casepack backend/packs/riverside_grocery \| grep -E "E12\|E20\|E21"` | no matches. **Any match → STOP, 1.3 has not closed CG-1** |

> **Rows 2, 3, 5, 6, 7, 8 are new or corrected in v1.1**, and every one of them would have
> failed a builder dispatched against v1.0.
>
> - **Row 2** demanded `≥20` events. Riverside has **three**. A guaranteed FAIL.
> - **Row 3** grepped `ORD-CAP-01`; the pack authors `ord_cap_01`. A guaranteed FAIL on case.
> - **Row 5 (old row 4)** grepped `class ActionType|ACTION_TYPES` — the same near-miss that
>   cost 1.2 a spurious pre-flight FAIL. It is now pinned to the real name and line.
> - **Old row 5** expected `no E20 error` on Riverside. Riverside emits **six**, plus two
>   `E12`. The row is now row 8 and says plainly what it means: **1.5 cannot start until 1.3
>   has closed CG-1.** That is a real gate, not a formality — an engine built against a pack
>   whose signals cannot fire is an engine whose central mechanism is never exercised.

---

## 8. Build steps

1. **Watch-rule evaluation + ledger, both kinds.** *Verify:* Riverside R2 raises `ord_cap_01`
   at utilisation 0.83 with `first_shown_round = 2`; a `presence` rule raises at `critical`
   with both thresholds null. I8.
2. **Escalation and clearing.** *Verify:* R3 escalates `ord_cap_01` to critical; a
   `scale_node` action clears it and records `lead_time`. A presence signal clears when its
   metric goes false, with no de-escalation step.
3. **Event preconditions + firing + cap.** *Verify:* all eleven precondition types evaluate
   against the §10 fields; `saturday_queue_collapse` fires at R4 for the do-nothing path and
   **does not fire** when the signal was cleared at R3. I5, I7.
4. **Blast radius + duration + staffing modifier.** *Verify:* removing the WAN link darkens
   the expected capability set; adding a failover edge yields an empty radius from the
   identical event.
5. **Privacy obligations on the same ledger.** *Verify:* a permissive policy over a sensitive
   entity raises an obligation at `critical` via the presence path; clearing it behaves like
   any signal; an ignored obligation arms the event named in `arms`.

---

## 9. Definition of Done

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–8 | | |
| Steps 1–5 verified | | |
| I1–I8 | | |
| O1–O5 recorded | | |
| Ledger carries both timestamps 1.4 needs | | |
| `cheapest_fix_when_raised` populated | | |
| **Both `metric_kind` paths write an identical ledger shape** | | |
| Two-team divergence demonstrated from one event card | | |
| **Seed** — signal history seeded; both paths demonstrated from one seed | | |
| Browser / auth / instance canaries | | **N-A** — pure, headless |

---

## 10. What this packet hands to others

**None of these are 1.5's to build.** Each is named here because 1.5's decisions created it,
and a decision whose consequences land in another packet is not settled until that packet
knows. *(`SPEC_PROTOCOL §4.2` — a claim about blast radius is verified, not asserted.)*

### To 1.1 — three schema additions, all gating this packet

| # | Addition | Driven by |
|---|---|---|
| 1 | **`WatchRule.metric_kind`**: `Literal["threshold","presence"]`, required. Plus the constraint decision 7 asked for: a `threshold` rule must carry at least one of `warn_above` / `critical_above`; a `presence` rule must carry **neither** | §3 decision 8 |
| 2 | **`obligation_rules`** as a schema section, in the §5.4 shape | §3 decision 7, `CG-5` |
| 3 | **`EventPrecondition` gains `node`, `entity`, `policy`, `round`** (and an integer count for `placement_count`), so the six unexpressible precondition types of §5.2 become real | §5.2 |
| 3a | **Still outstanding after 1.1 rework-2** *(added 2026-08-17)*: `placement_count` needs a **`placement` key as well as `count`** — only `count` was added, and `extra="forbid"` rejects the other half, so the type remains unexpressible (`1.1-r2-002`). `policy_contradiction` needs a **second policy key** — §5.2 says two, §10 item 3 specified one, one was added (`1.1 rework-2 R3`). **Three of six types are still not expressible**, so §8 build step 3 would hit a wall | `1.1-r2-002` |
| 4 | `WatchRule.key` is `str`, not `SnakeKey`, where every sibling key is constrained. Cosmetic, but it is the one key in the schema that could be authored in any case | observed 2026-08-15 |
| 5 | **`PolicyOption` gains `options: list[SnakeKey]` and `default: SnakeKey`** — the states a switch can be in, and the one a team holds by not deciding. **Highest priority of the five.** Without it `permissive_value` has no referent, the validator cannot check it, 4.3 cannot render the switch, and the engine cannot tell whether a team has moved off the permissive default — which is the whole mechanism of the ethics layer. See the box in §5.4 | `1.3-012` |

### To 1.2 — the validator, after 1.1 lands

| # | Change | Why |
|---|---|---|
| 1 | **`E12` must exempt `metric_kind: presence`** | A presence rule legitimately carries no thresholds. As built, `E12` fires on exactly the rules decision 8 makes legal |
| 2 | **`E20`'s predicate becomes** *"no watch rule that can raise a signal"* — a `threshold` rule with a threshold, **or** any `presence` rule | Otherwise a correctly-authored presence rule still reads as mute |
| 3 | **`W08` — the per-strategy draw check** of §5.2a, at `N = 6` (O4) | `CG-2` is invisible to `W05`'s deck-depth proxy |
| 4 | A `presence` rule carrying a threshold, or a `threshold` rule carrying none, is an ERROR — the schema constraint of item 1 above, mirrored in the validator | Defence in depth. **Note the split made in 1.1's rework-2:** the model rejects only the presence-plus-threshold shape, because rejecting a thresholdless threshold-rule at load makes Riverside unloadable and collapses twenty findings into one `E00`. The other half stays `E12`'s |
| 5 | **`Lens.owned` must union `pack.platform.services`**, as `filled_roles` already does | *(added 2026-08-17, from 1.1 rework-2 `R2`)* `validate.py:437-443` builds `owned` from `pack.catalog` alone, so `PlatformService.owns_entities` is **inert** — `E02` and `E23` cannot see it. Until this lands, no pack can satisfy an entity requirement through a platform service, and `E02 ×1` on Riverside is uncloseable by authoring. This blocks 1.3's `I6` |

| 6 | **`_raisable` (`validate.py:727-736`) must consult `metric_kind`** | *(added 2026-08-17, from `1.1-r2-006`)* It decides whether a severity is reachable purely from thresholds, so it is the third place that must learn about presence rules — and it was missing from this list, which made the note below false as originally written |

> **Consequence for Riverside — corrected 2026-08-17.** The original note here said `E12 ×2`,
> `E20 6→5` and `E21 ×2` resolve *"once 1.1 ships `metric_kind` and 1.3 declares the kind"*,
> and named 1.1 as the only gate. **That was wrong, and the rework audit proved it by
> experiment:** a scratch Riverside with `presence` declared on both rules validates
> **byte-identically** to the untouched pack. Verified independently — `validate.py` **never
> reads `metric_kind`**; `E12`, `E20` and `_raisable` all decide from thresholds alone.
>
> The correct sequence is **three packets, not two**:
>
> ```
> 1.1 rework-2   the field exists                 ✅ built
> 1.2 rework     E12 exempts · E20 widens · _raisable consults it   ← REQUIRED, not built
> 1.3            declares the kind on every rule
> ```
>
> Until the middle step lands, declaring `presence` is **inert** — it changes no validator
> output at all. Three of the 1.2 audit's findings still close on this ruling, but they close
> at **1.2's rework**, not at 1.1's.

### To 1.3 — the harvest

| Item | Note |
|---|---|
| `CG-1` closure now also means **declaring `metric_kind` on every rule** | A rule with neither a threshold nor a presence declaration is illegal under both packets |
| `CG-2` closure is measured by `W08` at `N = 6`, **per strategy** | Riverside is at 3 / 2 / 1 / 1. Depth alone will not close it |
| `CG-5` — author `obligation_rules.yaml` once 1.1 has the section | The Ch 4 ethics layer is inert until this exists |
| The deck must give **every** strategy a reason to draw | `differentiation` and `focus_strategy` have one card each |

---

## 11. Changelog

**v1.1 — 2026-08-15.** Revised by the author against merged 1.1, the 1.2 audit, and three
user rulings. No build cycle is open and no builder has been dispatched, so `R1` does not
apply. **`R2`:** I1–I7 keep their numbers; **I5's guard changed meaning** — from *reference*
to *reachability* — and **I8 is new**. No guard was dropped.

| Change | Why |
|---|---|
| §3 decisions 8–11; §5.1a | User ruling: `metric_kind` on `WatchRule`, presence raises at critical, one ledger shape |
| §3 decision 9; §5.2a; O4 | User ruling: per-strategy draw check, no round binding on `Event` |
| §3 decision 7 confirmed; §5.4 expanded | User ruling: privacy stays in 1.5; the packet is gated on 1.1 rather than split |
| §3 decision 3 corrected | Credited `E20` with a guarantee it does not provide; `1.2-013` is the counter-example |
| §5.2 precondition table | **Six of eleven types had no schema fields.** Unbuildable as written — the `1.2-016` item 3 failure, caught before dispatch this time |
| §5.1, §7 row 3, §8 step 1 — key case | Spec said `ORD-CAP-01`; the pack authors `ord_cap_01` |
| §6 I5 rewritten, I8 added | I5 passed a deck two-thirds of which cannot fire |
| §7 rows 2, 5, 6, 7, 8 | Row 2 demanded ≥20 events against a deck of 3; old row 5 demanded a clean `E20` that Riverside cannot give until 1.3 runs. Both were guaranteed FAILs, and a FAIL stops a builder |
| §10 added | Four schema changes and four validator changes fall out of these rulings, in three other packets |
