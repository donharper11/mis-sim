# Content Coverage Scan — the casepack vs the scoring factors

**Date:** 2026-07-27 · **Run by:** Claude (spec author)
**Method:** every factor in `design/02-traceability-matrix.md` checked against what
`backend/packs/riverside_grocery/` actually declares, after 1.1 built it.
**Verdict:** the schema holds up. **Five content gaps**, all belonging to a packet that
has not run yet.

> This is a different question from `findings/field-coverage-2026-07-27.md`. That asked
> *can a student enter it?* This asks *does the authored content exist for it to be scored
> at all?* Content gaps are deeper: if the pack cannot say it, no screen can capture it and
> no engine can compute it.

---

## What holds up

The catalog is complete on every field the Organisation term needs — `training_options`,
`process_option`, `people_affected`, `rgt_tag`, `true_cost_categories`, `must_be_fed_by`,
`must_feed`, `config_tiers` — **10 of 10 items, no partials.** Strategies carry weights,
concentration targets, RGT mix and maintenance floors. Fourteen stakeholders with
archetypes. Entities carry sensitivity. Every file has `provenance`.

1.1 did its job. These gaps are content depth, not structure.

---

## The five gaps

### CG-1 — ~~five~~ **six** of seven capabilities cannot raise a signal

> **Corrected 2026-08-14** by `findings/1.2-2026-08-14-audit.md` finding `1.2-001`, verified
> against the pack. The count was five; the real condition is **six of seven**.
> `firm_infrastructure` *has* a watch rule — `sec_identity_01` — whose `warn_above` and
> `critical_above` are **both `null`**, so it can never fire. A capability watched only by a
> rule that cannot fire is exactly as mute as one watched by nothing.

```
order_fulfilment      watch   catalog    ord_cap_01 warn 0.80 / crit 0.95 — the only
                                         rule in the pack that can actually fire
store_operations        —     catalog    <-- gap, no rule
financial_reporting     —     catalog    <-- gap, no rule
customer_insight        —     catalog    <-- gap, no rule
marketing_sales         —     catalog    <-- gap, no rule
service                 —     catalog    <-- gap, no rule
firm_infrastructure   watch   catalog    <-- gap, sec_identity_01 has neither
                                         threshold — added 2026-08-14
```

**Also mute, and separately illegal as of 2026-08-14:** `wh_rollout_01` watches
`order_fulfilment` with neither threshold set. It does not add a seventh mute capability,
because `ord_cap_01` covers that capability — but it is an illegal rule in its own right and
1.3 must not reproduce its shape. Both it and `sec_identity_01` use *presence-style* metrics
(`adoption`, `missing_identity_access`) that `WatchRule` cannot currently express; **1.5 owns
the schema answer**, and until it lands there is no legal way to author this kind of rule.

A capability with no watch rule **can never raise a signal**, so it is invisible to signal
responsiveness — a Management Quality sub-factor — and can never arm an event.

Five of seven capabilities are currently unmanageable in the one sense the sim measures.

1.2's check **E20** exists for precisely this and will fire on the pack as it stands. That
is the validator working, not a defect in it.

### CG-2 — the event deck is three cards

Three events, for **six rounds across four declared strategies**. Events draw by
`strategy_affinity`, so a team declaring a strategy no card targets faces an empty deck —
and 1.7's calibration cannot distinguish strategies that are never tested.

Rough floor: enough that every strategy draws in most rounds. Three does not reach it.

### CG-3 — nothing defines project duration

`grep duration_rounds` returns **zero hits** across `models.py`, 1.1's spec and 1.6's spec.

Follow-through is defined in 1.4 §5.3 as `1 − (abandoned + deployed-but-never-trained) ÷
initiated`. Detecting *abandoned* requires knowing a project was still in flight when it
stopped. Nothing in the pack says how long anything takes.

1.6 has an `in_flight` table, so this may resolve as runtime state rather than authored
content — **but it is unspecified in both places**, which is how it went missing.

### CG-4 — three policies, six designed

`policies.yaml` holds three. The information-policy design settled on **six switches**:
collection · retention · access · access logging · data egress · staff monitoring.

### CG-5 — no obligation rules, so the privacy layer is inert

`obligation_rules.yaml` does not exist.

This is the load-bearing one for Chapter 4. The design has privacy obligations riding the
signal machinery — sensitive data held under permissive policy raises an obligation;
ignored obligations arm events. **With no rules, the policy switches generate nothing.**

So even once `security.html` gains its six switches, flipping them would change no
outcome. The ethics layer would be decorative.

*(`competitors.yaml` is also absent, correctly — deferred with the market layer per
`design/04` G6.)*

---

## Disposition — all five belong to 1.3

1.3 is the harvest-and-author packet and it has not run. Its transform map covers
strategies, stakeholders, fit multipliers, add-ons, change-management options, ERP
modules, e-commerce features and governance policies.

`grep -ci "watch_rule|obligation"` over 1.3's spec returns **0**. Neither is in its map.

So these are not new work — they are **work 1.3 was never told to do.** 1.3 is amended
rather than a new packet created.

| Gap | 1.3 must additionally produce |
|---|---|
| CG-1 | a watch rule **carrying at least one threshold** for every capability — validator `E20` **and `E12`** clean *(restated 2026-08-14)* |
| CG-2 | an event deck sized so every strategy draws in most rounds |
| CG-3 | resolve project duration: authored field or runtime state, **stated either way** |
| CG-4 | six policy switches, each with its stated cost |
| CG-5 | `obligation_rules.yaml` — the privacy layer's rules |

---

## Sequencing

**Does not block 1.2.** The validator should run against the pack as it stands and **fire
`E20` on six capabilities and `E12` on two rules** *(corrected 2026-08-14; was "E20 on five")*
— that is the demonstration that both checks work, and a validator whose checks have never
fired on real content is untested.

> **Why the restatement matters more than the count.** As originally written, CG-1's closure
> condition — *"a watch rule for every capability, E20 clean"* — could be satisfied by
> authoring five rules shaped like `sec_identity_01`, with both thresholds null. `E20` would
> have gone green with **seven of seven capabilities still unable to raise a signal**, and the
> gate would have certified the exact condition it exists to prevent. Signal responsiveness
> is one of Management Quality's six sub-factors and is scored from two timestamps; with no
> rule able to fire, it would have scored nothing, silently, for every team.

**Blocks 1.7.** Calibration against a three-card deck and two watched capabilities would
produce curves that say more about the content's thinness than about the model.
