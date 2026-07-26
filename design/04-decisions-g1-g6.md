# Decisions — G1 (IT staffing) and G6 (stakeholder / market layer)

Settled 2026-07-26. Both were flagged as blocking for Spec A in
`02-traceability-matrix.md`.

---

# G1 — IT staffing binds to an operational load pool

## Decision

**IT staff is a capacity pool, modelled exactly like compute and storage.** Everything
the firm runs consumes staff capacity. Under-staff and existing scored factors degrade —
no new scoring axis is introduced.

## Mechanism

Every deployed platform service and application carries an **operational load** in staff
units, authored on the catalog row alongside its compute and storage draw.

```
  IT CAPACITY

    Staff                  2.0 FTE            capacity  2.0
    Operational load       3.4                    over  170%

      Platform services     1.9    hosting, network, backup, email
      Applications          1.5    POS, accounting, order mgmt

    ⚠ over-committed — see effects below
```

When load exceeds capacity, three factors already in the model take a penalty:

| Over-commitment degrades | Which term | Because |
|---|---|---|
| Incident recovery time | Technology (outage duration) | nobody available to fix it fast |
| Lifecycle / patching completion | Technology (currency) | you cannot patch what you have no time to patch |
| Adoption support during rollout | Organisation (adoption) | no floor support, no help desk |

It also amplifies the existing **change-volume resistance shock** — deploying three
systems in one round with no slack hurts more than deploying three with slack.

## Two ways to add capacity — the actual decision

```
  HIRE                    +1.0 FTE    $31,000/round    1-round lead
                          permanent · builds institutional knowledge ·
                          cheaper per unit over 4+ rounds

  MANAGED SUPPORT TIER    +0.6 FTE-equivalent
                          Basic $20,000 · Standard $50,000 · Premium $100,000
                          immediate · no institutional knowledge ·
                          vendor-scoped (covers only what it covers)
```

The support tiers come straight from mis_lite `maintenance_support_levels` (3 rows,
already costed) — a direct harvest fit. `integration_services` (Basic / Advanced /
Vendor-Managed) works the same way for integration work.

## Why this is the right binding

**It makes deployment mode a three-dimensional decision.** Until now, on-prem vs cloud
vs SaaS traded capex against opex. Now it also trades **people**:

```
  on our on-prem platform     high staff load    you run it
  on our cloud tenancy        medium load        you still run it
  vendor SaaS                 near-zero load     they run it
```

A cost leader who goes all-on-prem to avoid subscription opex discovers in round 4 that
they need three more staff — and headcount is opex too. That is a genuinely good MIS
lesson and it was completely absent before.

It also reuses machinery that already exists (pools, contention, utilisation signals,
watch rules) rather than adding a subsystem, and it gives the Organisation screen's
staffing block real weight.

## Optional refinement — skill coverage

Staff carry skill coverage for what they operate (on-prem / cloud / vendor-managed). A
split estate needs coverage on both sides. This recovers the accidental-hybrid penalty
that was cut with boundary crossings, in business language — *"you run two kinds of
estate with people who know one."*

**Recommend: defer to v2.** The load pool alone carries the lesson; skill coverage
doubles the authoring for a second-order effect.

## Casepack authoring cost

One field per catalog item (`staff_load`), plus a starting FTE count on the inherited
estate. Negligible.

---

# G6 — Adopt the stakeholder layer, defer the market layer

## The reframing

G6 was posed as "adopt mis_lite's attractiveness model or not." It isn't binary — the
mis_lite chain has **three separable layers**:

```
  1  STAKEHOLDER   decisions → alignment against each stakeholder's ideal
  2  OBJECTIVE     alignment → OAR weights → objective attractiveness
  3  MARKET        attractiveness → share of market_potential vs 5 rivals
```

They can be adopted independently, and they have very different cost-to-value.

## Decision

**Adopt layer 1 in v1. Carry layer 2's data without consuming it. Defer layer 3.**

## Why the stakeholder layer earns its place

1. **It answers your own filter question.** *"What does it cost, who does it affect,
   what happens if it fails"* — we had no model of *who does it affect*. Now we do:
   14 stakeholders, 7 internal and 7 external, with authored preferences.

2. **It solves the persona orphan.** The traceability audit flagged persona interviews
   as feeding no scoring factor. A stakeholder whose preferences you've ignored is a
   persona with something specific to say — and it generates inbox items automatically
   rather than by authoring.

3. **It is the Management dimension made concrete.** Managing stakeholder expectations
   *is* management. It slots into Management Quality without a new axis.

4. **It preserves nearly all the harvest.** Of ~2,100 mapping rows, essentially all are
   stakeholder mappings — `component_mapping` 630, `erp_*` 686, `ecommerce_*` 238,
   `mis_initiative_mapping` 168, `business_process_mapping` 112, `change_mgmt_mapping`
   112, `addon_mapping` 84. Adopting layer 1 keeps them live. Rejecting it makes them
   reference material.

5. **It needs no market maths.** No demand curves, no share allocation, no rival
   performance model.

## How it computes

Stakeholder satisfaction per stakeholder, from two inputs both already available:

```
  satisfaction(s) =  alignment of your decisions to s's preferences
                  ×  realised value in the capabilities s cares about
```

The second term is the important one, and it is the change from mis_lite. There, the
input to alignment was `selected_value` — **what the team bought**. Here it is
**realised value (Tech × Org × Mgmt)** — what the team actually delivered.

Consequence: buy the ideal ERP, train nobody, and Operations is *still* unhappy —
because the system isn't delivering, not because you bought the wrong box. That is a
strictly better lesson and it stitches the two engines together at exactly one point.

Feeds **Management Quality** as a factor alongside governance, strategic alignment,
portfolio discipline, signal responsiveness, and follow-through. Note it does **not**
duplicate strategic alignment: a team can be perfectly strategy-aligned and have furious
operations staff.

## Why layer 3 is deferred, not rejected

Consistent with the very first scoping decision in this project — *independent now,
leaderboard later*. The market layer is the competitive layer, and it brings:

- demand/share allocation maths that isn't MIS learning in itself
- a second calibration surface on top of the MOT engine
- a causal-attribution problem — with two engines running, debriefs get harder to trace,
  which undermines the sim's main strength

When it arrives it plugs in **above** the stakeholder layer exactly as mis_lite designed
it: attractiveness units → share of `market_potential` → rival performance. The
`competitors` (5), `market_potential` (50 rows), and OAR weights are all preserved for
that day.

## What "carry layer 2 without consuming it" means

The `oar1..oar5_weight` columns ride along in the harvested mapping rows. They are not
read by the v1 engine. They cost nothing to keep and are required the moment layer 3
is switched on.

## Casepack authoring cost

Stakeholder preferences per decision item, per stakeholder. This is the **largest**
authoring surface in the whole design — ~2,100 rows for Riverside-equivalent coverage.

Mitigations:
- mis_lite's rows are harvested, so pack 1 is largely free
- packs 2–5 need a **default-by-stakeholder-archetype** mechanism: author preferences at
  the archetype level (Finance always prefers low cost; Operations always prefers
  reliability) and override only where the case demands it
- the casepack validator must check preference coverage and flag uniform placeholder
  seeding — the `business_process_mapping` problem found in the harvest

**That archetype-default mechanism is now a required element of Spec A.** Without it,
pack 2 is unauthorable.

---

# Status of blocking gaps

```
  G1  IT staffing has no consequence          SETTLED — load pool
  G3  Management question mechanic            SETTLED — gated reporting, no
                                                        Analysis screen
  G6  Stakeholder / market layer              SETTLED — layer 1 in, layer 3 deferred
  G2  LLM rationale modifier                  open, non-blocking
  G4  Competitor moves unauthored             deferred with layer 3
  G5  Reflection prompt scoring home          open, non-blocking
  G7  Casepack registry + validator           open — required build, not a design gap
```

Spec A is unblocked.
