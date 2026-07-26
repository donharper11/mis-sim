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

### CG-1 — five of seven capabilities have no watch rule

```
order_fulfilment      watch   catalog
store_operations        —     catalog    <-- gap
financial_reporting     —     catalog    <-- gap
customer_insight        —     catalog    <-- gap
marketing_sales         —     catalog    <-- gap
service                 —     catalog    <-- gap
firm_infrastructure   watch   catalog
```

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
| CG-1 | a watch rule for **every** capability — validator E20 clean |
| CG-2 | an event deck sized so every strategy draws in most rounds |
| CG-3 | resolve project duration: authored field or runtime state, **stated either way** |
| CG-4 | six policy switches, each with its stated cost |
| CG-5 | `obligation_rules.yaml` — the privacy layer's rules |

---

## Sequencing

**Does not block 1.2.** The validator should run against the pack as it stands and **fire
E20 on five capabilities** — that is the demonstration that E20 works, and a validator
whose checks have never fired on real content is untested.

**Blocks 1.7.** Calibration against a three-card deck and two watched capabilities would
produce curves that say more about the content's thinness than about the model.
