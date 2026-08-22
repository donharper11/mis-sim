# 1.5 — Event & Signal Engine · Build Spec

**Authored under** `SPEC_PROTOCOL.md` v1.2 · **Author:** Claude/Codex · **Date:** 2026-07-26
**Spec version:** v1.2 · **Revised:** 2026-08-21, against `main` after the 1.4 closeout
**Phase:** 1 · **Depends on:** **1.1/1.2 readiness closeout (§10) · 1.3 (the deck) · 1.4**
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
   before pilot. The required 1.1/1.2/1.3 content is now live; §10 names the final narrow
   readiness closeout.
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

## 4. Build decisions — closed for dispatch

The five former open decisions are settled for the first implementation. Calibration may
change a threshold later through a new spec; the 1.5 builder has no decision authority here.

| # | Frozen decision |
|---|---|
| **O1** | A signal is actionable only if at least one clearing action was affordable at some point while it was open. Persist `cheapest_fix_when_raised`; exclude never-affordable signals from the responsiveness denominator. |
| **O2** | At most two events may fire for one capability in one round. Later satisfiable events are suppressed deterministically in authored deck order and recorded. |
| **O3** | Clearing after `fire_round` earns no responsiveness credit. Record the clearing for follow-through and the causal trace. |
| **O4** | `W08` uses the pack's authored round count: `N = pack.metadata.rounds`, not a global six. Riverside remains six; shorter and longer packs are judged against their own duration. |
| **O5** | A signal may be raised and cleared in the same round. Its `lead_time` is `0`, which is maximally responsive. |

Additional closeout rulings:

- Empty `strategy_affinity` is a legal explicitly-global card and counts as a draw for every
  strategy. `W03` remains a review warning, not a contradiction or prohibition; Riverside
  deliberately uses no empty affinities.
- `firm_infrastructure` having one presence-shaped rule is accepted content for Riverside.
  The engine remains general: a cleared signal may open a new ledger episode if its condition
  later becomes true again; signal history is not overwritten.
- The v1 metric vocabulary required by Riverside is closed to
  `capacity_utilisation`, `rollout_without_support`, `missing_identity_access`,
  `availability_shortfall`, and `data_coverage_gap`. All five functions must exist before
  the deck is considered executable. Unknown metric keys raise; they never evaluate false.
- The two missing precondition fields are frozen as `placement` and `other_policy`.
  `policy_contradiction` compares `policy` with `other_policy`; `placement_count` reads
  `placement` and `count`.

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

**Precondition types and the fields each needs.** The closed set stands. As of the v1.2
authoring baseline, `EventPrecondition` carries `type · signal · severity · capability ·
ratio · node · entity · policy · round · count`. The readiness closeout adds the last two
frozen fields, `placement` and `other_policy`, before the 1.5 implementation starts.

| Type | Needs | Expressible today? |
|---|---|---|
| `signal_open` | `signal`, `severity` | ✅ the only type Riverside uses |
| `demand_exceeds_capacity` | `capability`, `ratio` | ✅ |
| `adoption_below` | `capability`, `ratio` | ✅ |
| `staffing_over` | `ratio` | ✅ |
| `debt_above` | `ratio` | ✅ |
| `node_is_spof` | `node` | ✅ |
| `entity_unowned` | `entity` | ✅ |
| `placement_count` | `placement`, `count` | ⏳ readiness closeout |
| `policy_contradiction` | `policy`, `other_policy` | ⏳ readiness closeout |
| `sponsor_unassigned` | `capability` | ⚠️ works, but overloads `capability` |
| `round_equals` | `round` | ✅ |

The two readiness fields are a hard pre-flight gate. The validator also checks the closed
type vocabulary and each type's exact required/forbidden field set, so a typo or malformed
condition fails before the engine sees it. **A builder must not improvise missing values
into `ratio`.**

### 5.2a Deck coverage *(new v1.1 — §3 decision 9)*

`CG-2` was *"3 event cards for 6 rounds × 4 strategies — strategies that draw nothing."*
1.2's `W05` was rewritten to deck **depth** (`len(events) < rounds`) because `Event` carries
no round field, and depth cannot see CG-2's real shape: a six-card deck all affine to one
strategy passes it.

**The check is per strategy, not per round:**

```
for each strategy S:
    draws(S) = events whose strategy_affinity includes S, or is empty
    assert len(draws(S)) >= pack.metadata.rounds                  # O4
```

Riverside at the v1.2 baseline has 13 cards and at least six draws for every strategy;
`W08` passes. Empty affinities remain legal but Riverside uses none, so `W03` also passes.

```
cost_leadership              >= 6
customer_supplier_intimacy   >= 6
differentiation              >= 6
focus_strategy               >= 6
```

That closes CG-2 for Riverside. The threshold is derived from each pack's own authored
duration rather than fixed globally.

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

**This path is live content and validated at the v1.2 baseline.** Riverside authors six
rules in `obligation_rules.yaml`; the loader exposes the section, `PolicyOption.options`
provides the ordinal policy vocabulary, and validator `E24`–`E28` check every referenced
policy, entity, value, action and event. The engine consumes this shape:

```yaml
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

> ### Closed prerequisite history — `permissive_value` now resolves
>
> The earlier v1.1 baseline had no policy-state vocabulary. That gate is now closed:
> `PolicyOption.options` is ordinal and permissive-first, `default` is the untouched state,
> and `ObligationRule.permissive_value` must resolve into the named policy's options.
>
> The canonical semantics live in `CONTRACTS.md`; 1.5 consumes them and does not redefine
> policy ordering.

---

## 5.5 Seed — a signal ledger with history *(GOVERNANCE §4.9)*

```
seed        extends riverside_r3 with rounds 1-3 of signal history
command     python -m app.seed.demo --scenario riverside_r3 --with-signals   (NEW flag)
demonstrate ord_cap_01 raised then escalated across R2->R3 (utilisation from
              capacity_utilisation, contract-spec §4.1; exact figures are 1.7
              calibration — the old "0.83/1.11" were illustrative and are NOT
              reproduced under the frozen 1.4 throughput, contract-spec §0.5 S1)
            a PRESENCE rule raised at critical with no threshold crossed
            warehouse_rollout_gap FIRES on the do-nothing path and does NOT fire
              on a path where wh_rollout_01 was cleared (rebind from the phantom
              saturday_queue_collapse, contract-spec §0.5 S2 / §10.3)
            blast radius computed by traversal, printed
```

Two paths from one seed is the demonstration — the same event card, opposite outcomes.

> **Amended 2026-08-22 (contract-completion).** The metric bodies, ledger object, precondition
> runtime semantics, event attribution, and duration formula this section assumes are frozen in
> `handoffs/1.5-event-signal-engine/contract-spec.md`. Two corrections landed here: the
> `capacity_utilisation` figures are calibration outputs, not fixed pins (S1); and the two-path
> demonstration uses `warehouse_rollout_gap` because `saturday_queue_collapse` is not authored
> content (S2). No build cycle was open, so R1 does not apply.

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
| 2 | Riverside has watch rules and a deck sized for its six rounds | `[V]` | `grep -c "^- key:" backend/packs/riverside_grocery/watch_rules.yaml backend/packs/riverside_grocery/events.yaml` | `8` and `13` |
| 3 | `ord_cap_01` exists with the 0.3 semantics | `[V]` | `grep -A5 "key: ord_cap_01" backend/packs/riverside_grocery/watch_rules.yaml` | `warn_above: 0.80`, `critical_above: 0.95` |
| 4 | The action-type set from 1.2's E05 exists | `[V]` | `grep -n "^ACTION_TYPES" backend/app/casepack/checks.py` | present, line 12 |
| 5 | **`WatchRule.metric_kind` exists** (§10 item 1) | `[V]` | `grep -n "metric_kind" backend/app/casepack/models.py` | present. **Absent → STOP, 1.1 has not run** |
| 6 | **`obligation_rules` is a schema section** (§10 item 2) | `[V]` | `grep -n "obligation_rules\|class ObligationRule" backend/app/casepack/models.py` | present. **Absent → STOP** |
| 7 | All twelve precondition fields exist, including the two closeout fields | `[V]` | `sed -n '/class EventPrecondition/,/class EventOutcome/p' backend/app/casepack/models.py` | includes `placement` and `other_policy` as well as the ten existing fields; either absent → STOP |
| 8 | Riverside validates clean | `[V]` | `cd backend && PYTHONPATH=. bin/validate_casepack packs/riverside_grocery` | `0 errors · 0 warnings · exit 0` |
| 9 | W08 derives its threshold from pack duration | `[V]` | `grep -n "metadata.rounds" backend/app/casepack/validate.py` | W08 comparison uses the loaded pack's round count; no `W08_MIN_DRAWS` constant |
| 10 | Closed precondition vocabulary and shapes are validated | `[V]` | `rg -n "PRECONDITION_TYPES|check_precondition" backend/app/casepack backend/tests` | canonical 11-type set, per-type field checks, positive and negative tests |
| 11 | The five Riverside metric functions are an explicit engine contract | `[V]` | `rg -n "capacity_utilisation|rollout_without_support|missing_identity_access|availability_shortfall|data_coverage_gap" backend/app/engine backend/tests` | each implemented and tested; unknown metric raises |

Rows 7–10 are hard prerequisite gates. Row 11 is intentionally a builder-owned gate: the
five metric functions are the first engine deliverable, and the remaining deck/event steps
must not proceed until their focused tests pass.

---

## 8. Build steps

1. **Watch-rule evaluation + ledger, both kinds.** *Verify:* Riverside R2 raises `ord_cap_01`
   at utilisation 0.83 with `first_shown_round = 2`; a `presence` rule raises at `critical`
   with both thresholds null. I8.
2. **Escalation and clearing.** *Verify:* R3 escalates `ord_cap_01` to critical; a
   `scale_node` action clears it and records `lead_time`. A presence signal clears when its
   metric goes false, with no de-escalation step.
3. **Event preconditions + firing + cap.** *Verify:* all eleven precondition types evaluate
   with the runtime semantics frozen in `contract-spec.md §6`; `warehouse_rollout_gap` fires on
   the do-nothing path and **does not fire** when `wh_rollout_01` was cleared (S2 rebind). I5, I7.
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
| Pre-flight rows 1–11 | ✅ | contract-spec §12 rows 1–8 all PASS (row 7 fields land as STEP 0 per GOVERNANCE §6.3, commit `44c60b1`); 1.5 §7 rows re-verified (graph, 8 rules / 13 events, `metric_kind`, `obligation_rules`, `placement`+`other_policy`, validate `0/0`, W08). |
| Steps 1–5 verified | ✅ | `python -m app.seed.demo --scenario riverside_r3 --with-signals` prints the ledger, the projection-reproduces-seed gate (`True`), the two-path outcome, and the WAN blast radius; `tests/test_signal_engine.py` (CC1–CC14). |
| I1–I8 | ✅ | I1/I2/I3/I8 → `tests/check_engine_purity.py` (green, in `make check`); I4 determinism → existing `test_engine_scoring.py`; I5 reachability + I6 derived + I7 cap → `test_signal_engine.py` (CC11/CC12) and the pin tests. |
| O1–O5 implemented exactly as frozen | ✅ | O1 `was_actionable`/`cheapest_effectful_fix` (CC7); O2 cap + suppression (CC11); O3 clear-after-fire no credit (CC6); O4 pack-duration W08 (existing); O5 `lead_time == 0` (`LedgerSignal.lead_time`). |
| Ledger carries both timestamps 1.4 needs | ✅ | `LedgerSignal.{first_shown_round, cleared_round, fire_round}` + `lead_time`; projection §5.4 (CC4). |
| `cheapest_fix_when_raised` populated | ✅ | `ledger.cheapest_effectful_fix` (CC7); populated on every raised row by `advance_ledger` and in the seed history. |
| **Both `metric_kind` paths write an identical ledger shape** | ✅ | `ledger.evaluate` handles threshold + presence into one `LedgerSignal`; I8 confines `metric_kind` to `ledger.py` (`check_engine_purity.py`). |
| Two-team divergence demonstrated from one event card | ✅ | `warehouse_rollout_gap` fires on the do-nothing path, does not fire on the `add_training`-cleared path (demo + CC11 scaffold); no authored branching. |
| **Seed** — signal history seeded; both paths demonstrated from one seed | ✅ | `--with-signals` flag; `seeds/riverside_signals.py`; projection reproduces the three seed `SignalState` rows byte-for-byte (CC4). |
| Register Reconciliation | ✅ | `CC-D3`/`CC-D4` (the two outage-schema fields) CLOSED — landed as STEP 0 of this build (`OPEN-REGISTER §M`). |
| Browser / auth / instance canaries | ✅ | **N-A** — pure, headless engine. |

---

## 10. Readiness gate and closed handoffs

Historical 1.1, 1.2 and 1.3 handoffs are closed on the v1.2 baseline: `metric_kind` is
live, presence reachability is validated, Riverside has 8 rules and 13 events,
`obligation_rules` has six validated rows, policy options are ordinal and live, and the
pack validates at 0 errors / 0 warnings.

One prerequisite packet remains, specified exhaustively in `readiness-spec.md`:

| Owner | Required before 1.5 implementation | Gate |
|---|---|---|
| 1.1 schema | Add `EventPrecondition.placement` and `.other_policy` | pre-flight row 7 |
| 1.2 validator | Closed 11-type vocabulary with exact per-type field validation | pre-flight row 10 |
| 1.2 validator | Derive W08 from `pack.metadata.rounds`; preserve empty-affinity semantics and W03 | pre-flight row 9 |

This prerequisite is deliberately separate from the engine build and requires its own
independent audit. After it merges, all 1.5 pre-flight rows must pass before engine code is
written.

**Second prerequisite — contract completion.** The engine builder ran pre-flight rows 1–10
(pass) and row 11 in its builder-owned state, then found the metric bodies, ledger object,
precondition runtime semantics, event attribution, and duration formula **undefined**. Those
contracts are frozen in `handoffs/1.5-event-signal-engine/contract-spec.md` (**v1.1**, revised by a
fresh author 2026-08-22 to close the v1.0 audit's six Blocking + one Report findings, **pending
independent re-audit**). It also amends this spec by cross-reference (§5.5, §8 step 3) and records ten
owned deferrals (`OPEN-REGISTER §M`). **The engine build restarts pre-flight only after the
contract-spec is independently re-audited and merged.**

**Third prerequisite — outage schema (contract-spec §9.1, resolves the CC-A-005 sequencing).** The
`availability_shortfall` and outage-duration paths need two NEW casepack-schema fields that do not
exist today. Because `§4` above requires **all five** metric functions to exist before the deck is
executable, these fields are **not** a deferred path — they are a small 1.1/1.2 prerequisite packet
(`CatalogItem.base_rto_hours: float = 8.0`; `Capability.agreed_availability: float = 0.99`; validation)
that lands and is independently audited **before** the 1.5 engine builder is dispatched, exactly as
the readiness closeout was. Both carry defaults, so once the fields exist every pack's five metrics are
buildable. See the pre-flight gate below.

| Owner | Required before 1.5 implementation | Gate |
|---|---|---|
| 1.1 schema (+ 1.2 validation) | Add `CatalogItem.base_rto_hours` and `Capability.agreed_availability` (both defaulted) | contract-spec §12 row 7 (hard STOP) |

---

## 11. Changelog

**v1.2 — 2026-08-21.** Reconciled against merged 1.1–1.4 and the Phase-1 open
register. No 1.5 build cycle was open. O1–O5 are frozen; W08 is pack-duration-relative;
empty affinity, signal recurrence, the five metric functions, and the last two
precondition field names are settled. Historical gates are replaced by executable
pre-flight rows 7–11 and the bounded `readiness-spec.md`. I1–I8 retain their numbers and
meanings; no invariant was dropped.

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
