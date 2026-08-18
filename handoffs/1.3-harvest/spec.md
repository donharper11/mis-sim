# 1.3 — mis_lite Harvest → Riverside Pack v1 · Build Spec

**Authored under** `SPEC_PROTOCOL.md` v1.1 · **Author:** Claude · **Date:** 2026-07-26
**Spec version:** v1.1 · **Revised:** 2026-08-16, against merged 1.2 and both its audits
**Phase:** 1 · **Depends on:** **1.1 + a 1.1 rework (§3a — this packet is gated)** ·
1.2 (validator, **merged `d5647d8`**) · **Blocks:** 1.4, 1.7

> ### ⛔ Read §3a before dispatching. This packet cannot complete today.
>
> Four schema additions must land in 1.1 first. Without them **CG-1 and CG-5 cannot be
> closed**, and the Definition of Done requires closing both. Dispatching against v1.0
> would produce a builder that gets most of the way and then stops — or worse, one that
> improvises a schema, which §1 forbids.

> Fill the skeleton with real content. Mechanical where possible, judged where not — and
> the spec says which is which, because a builder should never be guessing whether it is
> transforming or authoring.

---

## 0. Spec Basis

**Read in full:** `design/01-mis_lite-harvest.md` (the whole harvest analysis, including
§3 on the component-master problem and §4 on seed quality) · `handoffs/1.1-casepack-schema/spec.md` ·
`CONTRACTS.md` (the `trialNNN` note, the fit-multiplier conversion warning) ·
`mis_lite` live schema, 79 tables, masters sampled ·
**`findings/1.2-2026-08-14-audit.md`** and **`findings/1.2-rework-2026-08-15-audit.md`** —
between them they name every content defect this packet inherits ·
**`handoffs/1.5-event-signal-engine/spec.md`** v1.1 §10, which hands four requirements here.

**Extraction sufficiency:** covered for the tables named in `design/01` §2. The nine
`*_mapping` tables (~2,100 rows) were sampled, not read exhaustively — flagged as
**pre-flight row 5**, because the transform's correctness depends on their uniformity.

---

## 1. Purpose and scope

**In scope:** transform harvestable mis_lite content into `packs/riverside_grocery/`;
author what cannot be transformed; produce a provenance record.

**Out of scope:** changing the schema (that is 1.1 — if content will not fit, **stop and
report**) · authoring a second pack (6.1) · any engine code.

---

## 2. Project-specific statements

**Scoring factors touched:** authors inputs to all of them. **Casepack keys read/written:**
all of `riverside_grocery`. **Instance scoping:** N/A.
**Business-language check:** every harvested description becomes student-visible text and
must pass `GOVERNANCE.md §2.1`. mis_lite's descriptions are largely textbook prose —
invariant I3 greps the result.

---

## 3. Settled decisions

1. **Read-only against mis_lite.** No writes to `192.168.50.38`, ever.
2. **Drop `trialNNN`** on every table (`CONTRACTS.md`).
3. **Only ~19 of 45 `component_types_master` rows become catalog items.** The other ~26 are
   Chapter 5 *concepts* and go to `docs/curriculum-coverage.md`, not the catalog
   (`design/01` §3). The buildable list is enumerated there.
4. **Fit multipliers are converted, not copied.** mis_lite uses un-normalised multipliers
   around 1.0; the schema requires weights summing to 1.0 (`CONTRACTS.md`). Conversion is
   normalisation per strategy, and the raw values are retained in the provenance file.

   > **RATIFIED 2026-08-18 — the conversion runs; its output does NOT become
   > `capability_weights`.** *(`1.3-002`, author ruling)*
   >
   > This decision and §3 decision 6 conflicted, and the builder resolved it on its own
   > authority — which `GOVERNANCE §7` reserves to the author. **It resolved it correctly**,
   > and the ruling is recorded here rather than left as a builder's judgement:
   >
   > | | mean pairwise L1 distance between the four strategies |
   > |---|---|
   > | harvested, normalised | **0.042** — every weight in `[0.1323, 0.1520]` |
   > | authored | **0.700** — 16× more differentiated |
   >
   > The audit recomputed the conversion from all 168 raw cells and confirmed the range
   > exactly. Normalised weights make the four strategies **numerically indistinguishable**,
   > and `cost_leadership` comes out highest for all seven capabilities — a scale artefact of
   > an un-normalised source, not a signal.
   >
   > **Decision 6 wins**: `cost_leadership`'s weights are pinned by `mockups/strategy.html`,
   > and a pack whose strategies cannot be told apart fails 1.7's *no dominant strategy* gate
   > by being uniformly flat. The conversion still runs and its table still ships in
   > `PROVENANCE.md §4` — it is evidence about the source, not an input to the pack.
   >
   > **One risk this creates, and it is real:** `harvested_raw_fit` now ships *inside*
   > `strategies.yaml`, one field away from the weights it must never become, with no check
   > behind `CONTRACTS.md`'s "do not mix the two". **A validator check that
   > `capability_weights` never equals a normalisation of `harvested_raw_fit` belongs on
   > 1.2's list.**
5. **The 14 stakeholders become archetypes**; Riverside persona instances are **authored
   new** — mis_lite has roles, not people.
6. **Riverside's fixed figures are authoritative.** Where harvested content conflicts with
   `handoffs/0.3-mockup-pilot/spec.md §5.4`, §5.4 wins — the mockups and the engine must
   agree.
7. **The validator is the gate, and it is now real.** *(added v1.1)* 1.2 merged at
   `d5647d8`. `GOVERNANCE §5` — *"no casepack reaches a section until `validate_casepack`
   passes clean"* — stops being aspirational here. **`backend/bin/validate_casepack
   backend/packs/riverside_grocery` exiting 0 is this packet's exit condition**, and it is
   the first packet for which that sentence has teeth.
8. **Every watch rule declares `metric_kind`.** *(added v1.1, from 1.5 §3 decision 8)*
   `threshold` rules carry at least one threshold; `presence` rules carry neither. A rule
   declaring neither kind is illegal under `E12`. See §3a.
9. **CG-2 is measured per strategy, never per round.** *(added v1.1, from 1.5 §3 decision 9)*
   `Event` carries no round field and, by that ruling, never will — round timing stays
   emergent from preconditions. **I9 is rewritten accordingly**; its v1.0 form was
   unmeasurable.
10. **Both `capital_remaining` figures are derived, and the mockup conflict is reported,
    not resolved unilaterally.** Unchanged in substance from §5.1a, but `E14` now enforces
    it — see the CG-6 block.

---

## 3a. The 1.1 gate — why this packet cannot start yet

Four schema additions are required before 1.3 can reach its own Definition of Done. They
were identified by 1.5's spec (§10) and by the two 1.2 audits, and **none of them is 1.3's
to build** — §1 puts schema changes out of scope and says *stop and report*.

| # | Missing from 1.1 | Without it, 1.3 cannot… | Source |
|---|---|---|---|
| 1 | `WatchRule.metric_kind` | close **CG-1**. Riverside's two presence-shaped rules (`sec_identity_01`, `wh_rollout_01`) have no legal form, so `E12 ×2` cannot be cleared without deleting rules that should exist | 1.5 §10 · `1.2-001` |
| 2 | `obligation_rules` as a schema section | close **CG-5** at all. There is nowhere to author the file, which is why 1.2 cannot even report its absence | 1.5 §10 · `CG-5` |
| 3 | `Labels` sections for `entities`, `catalog`, `watch_rules`, `questions` | give eight validator codes a business name to lead with — they currently print machine keys at instructors | `1.2-008` · `1.2-024` |
| 4 | `PlatformService.owns_entities` | satisfy `firm_infrastructure`'s `user_account` requirement. `central_sign_on` fills the *role* but no platform service can own an *entity* | `1.2-011` |
| 4b | **`Lens.owned` must union `pack.platform.services`** — a **1.2** change, not 1.1 | clear `E02` *at all*. See the box below | `1.1 rework-2` `R2` |

> **`E02` cannot be cleared by this packet, and that is new information.** *(added
> 2026-08-17)* Addition 4 lands the field, but `validate.py:437-443` builds `Lens.owned`
> from `pack.catalog` **only** — and `Lens.owned` is what `E02` and `E23` consult. The
> asymmetry is visible in adjacent lines: `filled_roles` unions `pack.platform.services`,
> `owned` does not.
>
> So after 1.3 declares `central_sign_on.owns_entities`, **`E02` still fires.** Verified
> 2026-08-17. Without the validator change, 1.3 authors correct content and gets blamed for
> a validator gap.
>
> **Consequence for this spec's `I6` (validator exit 0):** it is unreachable until 1.2's
> next rework lands, *regardless* of the 1.1 gate. Either sequence 1.2's rework before 1.3,
> or defer `I6` per §3a and accept `E02 ×1` as a known-outstanding error in `dod.md`.

**Current state, run 2026-08-16 against merged `main`:**

```
E07 ×8   missing label keys              → 1.3 content, buildable today
E20 ×6   capabilities that cannot signal → CG-1, needs addition 1
E12 ×2   thresholdless watch rules       → CG-1, needs addition 1
E21 ×2   events whose precondition can   → resolves for free once the two rules
         never be satisfied                 become legal presence rules
E02 ×1   nothing owns user_account       → needs addition 4
E14 ×1   capital authored twice, 44000   → CG-6, buildable today
         against a derived 46000
W02 W04 W05                              → CG-2, buildable today
```

**Eleven of the twenty errors need additions 1 and 4 before any authoring can clear them.**

> ### ✅ SUPERSEDED 2026-08-18 — both gates are now lifted. Read this first.
>
> 1.2's second rework (`build/1.2-rework-2`) taught the validator the fields, and the
> experiment below **now passes**: declaring `metric_kind: presence` clears `E12 ×2` and
> `E21 ×2` and drops `E20` from six to five. Reproduced independently twice.
>
> **`I6`, `I8`, `I9` and `I12` are reachable.** The box below is retained as the record of
> why they were not, and its two conclusions are now **false**: `I6` is *not* unreachable,
> and `E02` *is* closeable — by 1.3 declaring `central_sign_on.owns_entities`.
>
> **What is still outstanding for a 1.3 dispatch:**
>
> | Item | Status |
> |---|---|
> | `I6`, `I8`, `I9`, `I12` | **reachable** — no deferral clause needed |
> | `I11` (obligation rules resolve) | **still has no executable check** (`1.2-037`). A dispatch must defer it explicitly, or 1.2 must add the cross-reference check first |
> | `E02 ×1` | still fires as shipped — **1.3's to clear**, by declaring the ownership |
> | `1.2-024` | unclosed — the `Labels` sections exist but no message consults them |
> | `1.2-031` | `E02`/`E23` still say *"add a catalog item"* when a platform service is now a legal holder. **1.3's builder is the first person this misleads** |
> | `1.2-035` | emptying `strategy_affinity` to satisfy `W08` trades one `W08` for seven `W03`. A real authoring trap |
>
> **Measured forward:** with `metric_kind` declared *and* `central_sign_on.owns_entities`
> added, Riverside goes **20 errors → 14**, and all fourteen (`E07 ×8`, `E20 ×5`, `E14 ×1`)
> are pure authoring — which is exactly what this packet is for.

> ### The 1.1 gate is lifted. It was not enough. *(added 2026-08-17, superseded above)*
>
> `build/1.1-rework-2` delivered all four additions, and pre-flight row 1a now returns its
> exact expected output. **The eleven errors did not move.**
>
> The rework auditor built a scratch Riverside with `metric_kind: presence` declared on both
> rules — the exact move that closes CG-1 — and the validator output was **byte-identical to
> the untouched pack**. Verified independently: `validate.py` **never reads `metric_kind`**.
> `E12`, `E20` and `_raisable` all decide from thresholds alone.
>
> **Additions 1 and 4 are both validator-gated, not only addition 4.** The real sequence is:
>
> ```
> 1.1 rework-2   ✅ the fields exist
> 1.2 rework     ← REQUIRED AND NOT BUILT
>                  E12 exempts presence · E20 widens · _raisable consults kind ·
>                  Lens.owned unions platform services · W08
> 1.3            declares kinds, authors ownership, closes CG-1..CG-6
> ```
>
> **`I6`, `I8` and `I11` are unreachable until 1.2's rework lands.** Two further findings
> sharpen this: `1.2-024` is *not* closed by authoring the new `Labels` sections, because no
> validator message consults them yet (`1.1-r2-003`); and `I11` has no executable check at
> all — a fully orphaned `obligation_rules.yaml` validates identically to a correct one
> (`1.1-r2-005`).
>
> **Recommendation: sequence 1.2's rework before dispatching 1.3.** Running 1.3 first means
> authoring correct content against a validator that cannot confirm it, and deferring three
> invariants — which is how a gap becomes invisible.

### What 1.3 *can* do today, if the gate is not lifted first

`E07 ×8` (the eight missing label keys), `E14 ×1` (CG-6), `CG-2`, `CG-3`, `CG-4` and the
entire transform map in §5.1 are all buildable against today's schema. **That is most of the
packet.** If the sequencing decision is to run 1.3 before the 1.1 rework, this spec supports
it — but the DoD's `I6` (validator exit 0) must then be explicitly deferred, and the packet
returns for a second pass once 1.1 lands. **Say which, in the dispatch. Do not let a builder
discover the gate at step 6.**

---

## 4. Open decisions

| # | Question | Criteria | Reporting |
|---|---|---|---|
| **O1** | mis_lite's `business_process_mapping` shows uniform placeholder values (`design/01` §4). Harvest it or re-author? | **Default: do not harvest. Re-author from the archetype defaults in 1.1 §5.7.** Importing placeholder data that *looks* authored is worse than an honest default | Record, with the row count discarded |
| **O2** | mis_lite descriptions are textbook prose ("Traditional rack servers suitable for basic workloads"). Keep or rewrite? | **Default: rewrite to business language.** These become student-visible. Keep the originals in provenance | Record |
| **O3** | `market_potential` (50 rows) — harvest now or defer with the market layer? | **Default: harvest into the pack but mark `unused_until: market_layer`.** Free to carry, costly to re-derive (`design/04` G6) | Record |

---

## 5. Design

### 5.1 Transform map

| mis_lite source | Rows | → pack destination | Mode |
|---|---|---|---|
| `strategy` | 4 | `strategies.yaml` identity + labels | mechanical |
| `objectives` | 5 | `labels.yaml` declaration vocabulary | mechanical |
| `stakeholders` | 14 | platform archetypes (shared, not pack) | mechanical |
| `component_strategy_fit` | 168 | `strategies.yaml` weights — **normalised** | transform |
| `component_types_master` | 45 → ~19 | `catalog.yaml` | **judged** — see §5.2 |
| `it_infrastructure_addons_master` | 11 | `platform.yaml` shared services | transform |
| `maintenance_support_levels` | 3 | `platform.yaml` staff-capacity tiers (G1) | mechanical |
| `integration_services` | 3 | `platform.yaml` integration tiers | mechanical |
| `deployment_types`, `hardware/network/database_types` | 12 | `catalog.yaml` option ladders | transform |
| `change_management_master` + `_strategy_fit` | 8 + 20 | training / process / communication options | transform |
| `erp_modules_master` | 21 | `catalog.yaml` enterprise apps | transform |
| `ecommerce_features_master` | 9 | `catalog.yaml` | transform |
| `mis_initiatives_master` | 12 | `catalog.yaml` | transform |
| `data_governance_policies` | 3 | `policies.yaml` | transform |
| `security_incidents`, `regulatory_penalties` | 6 | `events.yaml` seeds | judged |
| `competitors` | 5 | `competitors.yaml`, `unused_until: market_layer` | mechanical |
| `market_potential` | 50 | same (O3) | mechanical |
| `stakeholder_infrastructure_preference` | 14 | `preferences/platform.yaml` | mechanical |
| `business_process_mapping` | 112 | **discarded** (O1) | — |
| per-domain `*_decisions` tables | 0 | **discarded** — runtime shape, superseded | — |

### 5.1a Content gaps 1.1 left — MUST be closed here *(added 2026-07-27)*

From `findings/content-coverage-2026-07-27.md`. None of these were in the original
transform map; all five are authoring, not transformation.

| Gap | Required output | Why it cannot wait |
|---|---|---|
| **CG-1** | A watch rule **carrying at least one threshold, or declared `metric_kind: presence`, for every capability** — restated 2026-08-14 | **Six** of 7 cannot raise a signal, not five. `firm_infrastructure` *has* a rule whose thresholds are both `null`, which is exactly as mute as having none. Validator **`E20` ×6 and `E12` ×2** fire on the current pack. **Gated on 1.1 addition 1** (§3a) |
| **CG-2** | **Every strategy drawn by ≥6 events** — `strategy_affinity` includes it, or is empty | Three cards across four strategies: `cost_leadership` 3, `customer_supplier_intimacy` 2, `differentiation` 1, `focus_strategy` 1. A strategy no card targets faces an empty deck, and 1.7 cannot distinguish a strategy that lost from one never tested |
| **CG-3** | Resolve project duration — authored catalog field or runtime state, **stated either way** | `grep duration_rounds` returns zero across `models.py`, 1.1 and 1.6. Follow-through needs to detect *abandoned mid-flight* and nothing says how long anything takes |
| **CG-4** | Six policy switches, each with its stated cost | Three exist. Design settled on collection · retention · access · logging · egress · staff monitoring. A switch with no stated cost is a morality quiz, not a trade-off |
| **CG-5** | `obligation_rules.yaml` | **Load-bearing for Chapter 4.** Without rules, sensitive data under permissive policy raises nothing, ignored obligations arm nothing, and the policy switches change no outcome. The ethics layer would be decorative |

**CG-5 is the one to get right.** The whole privacy design rides the signal machinery —
obligations raised like signals, cleared like signals, arming events like signals. The
rules are what connect a policy switch to a consequence.

> **CG-5 is gated on 1.1 addition 2** (§3a) and the shape is already specified — see
> `handoffs/1.5-event-signal-engine/spec.md` §5.4, which defines the section 1.1 must add
> and this packet must author into. An obligation is presence-shaped by construction, so it
> uses the same `metric_kind: presence` path as addition 1. **Do not design the section
> here; author into the one 1.5 specified.**

> **CG-4's six switches, named.** *(added v1.1)* `policies.yaml` today holds **three** —
> `encrypt_customer_data`, `compliance_audit`, `access_review` — against the six the design
> settled on: **collection · retention · access · logging · egress · staff monitoring**.
> Only *access* is arguably covered. This is buildable today and needs no schema change; each
> switch carries a stated cost, because a switch with no cost is a morality quiz rather than
> a trade-off. Note that the three that exist are keyed by *mechanism*
> (`encrypt_customer_data`) rather than by the *policy dimension* the design names — the
> builder must decide whether to re-key them and say so.

**CG-6 — derive the capital roll-ups; do not author them twice.** *(carried from
`findings/1.1-2026-07-27-audit.md` § 1.1-002, 2026-07-27)*

`pack.yaml` currently authors round-3 capital remaining in two places, and they disagree:

```
:22   initial_state.budget.capital_remaining:   44000     (round 3, available 220000)
:82   initial_state.review.capital_committed:  174000     (area lines sum to exactly this)
:84   initial_state.review.capital_remaining:   46000     (= 220000 − 174000)
```

No `$2,000` item exists anywhere in the round-3 blocks — the two figures were authored
independently and one is stale. **Not a blocker at 1.1:** nothing consumes them. `seed.py`
persists nothing, the 0.2 baseline migration is still `pass`, and no engine exists to compute
against. They are display fixtures pinned to the 0.4 mockups.

It becomes real here, because §5.4a reads the pinned figures back and matches them against
0.4 §5.4. Required output:

- `capex_per_round` and the review **area lines** are the authored facts;
- **both** `capital_remaining` values are **derived** — `available − committed` — not authored.
  `SPEC_PROTOCOL.md §3`: eliminate the second home rather than reconcile it. This makes the
  drift structurally impossible instead of corrected once;
- derived, round 3 resolves to **46000**. **16 mockups currently display `$44,000`** and two
  display both — so the read-back in §5.4a will fail against them until either the mockups
  take the derived figure or the authored lines change. **Report which, do not silently pick.**

Closing CG-6 also closes `0.4-002`, which is the same two figures on `review.html`.

> **Updated v1.1 — CG-6 is now enforced, not merely requested.** The validator's `E14`
> fires on this exact pair today (*"an authored figure contradicting one derived from the
> same pack, tolerance zero"*), so the drift can no longer reach a section unnoticed. Two
> consequences for this packet:
>
> 1. `E14` clearing is **necessary but not sufficient**. Deleting one figure clears the
>    error; §5.1a requires the second home to be *eliminated* and the value *derived*, per
>    `SPEC_PROTOCOL §3`. A builder that reconciles the numbers rather than removing the
>    duplicate has satisfied the validator and not the spec.
> 2. The mockup conflict is unchanged and still needs a decision — **16 against 2**,
>    re-counted 2026-08-16. Derivation says `46000`. Sixteen merged mockups say `$44,000`.
>    That is a 0.4 rework, not a 1.3 authoring choice, which is why this spec has always
>    said report rather than pick.

### 5.1b Content defects the validator found — 1.3 owns these *(added v1.1)*

The two 1.2 audits ran the validator against the shipped pack and found defects that are
neither content gaps nor schema problems: they are **content that is already wrong**. None
was reported before, because before 1.2 there was nothing to report them.

| Finding | Defect | Fix here |
|---|---|---|
| `1.2-012` | **Eight referenced label keys are absent from `labels.yaml`** — seven `process_option.label_key` values (`redesign_picking`, `redesign_checkout`, …) plus the role `inventory_app`. `E07 ×8`, the single largest error group in the pack | Author the eight labels. **A Rollout screen today would render `redesign_picking` at a student** |
| `1.2-024` | Eight codes lead their message with a machine key because `Labels` has no `catalog`, `watch_rules` or `questions` section, and `events` maps to a persona quote rather than a name | Author the sections **once 1.1 addition 3 lands**. Gated |
| `1.2-020` | `E13`'s `contributing` arm resolves `initial_state` keys against **the pack's own capabilities**, so Porter's canonical value-chain activities read as false errors | **Blocking at 1.3** — see the ruling required below |
| `1.2-013` | Two of three event cards wait on a `critical` their watch rule can never reach, leaving an effective deck of **one** | Resolves for free once CG-1 declares those rules `presence`. Verify it did |

> **Author ruling required before this packet is dispatched** (`1.2-020`). Riverside's
> `value_chain_coverage` holds Porter's nine activities — `inbound_logistics`,
> `procurement`, `technology`, `human_resources` and the rest — several of which are listed
> *precisely because nothing covers them* (`procurement: 0/3`, `technology: none`). They are
> **activities, not capabilities**, and the two vocabularies are different by design.
>
> The rework auditor proved that applying `E13` to them raises **eight false errors on
> correct content**, and upheld the builder's refusal to implement it. So the check is
> correctly absent — but that leaves `initial_state.value_chain_coverage` and
> `unit_responses[].contributing` **entirely unvalidated**, which is the hole `1.2-014`
> opened and `E13` was supposed to close.
>
> **1.3 is where this becomes urgent, because 1.3 regenerates `initial_state` wholesale.**
>
> ### RULED 2026-08-18 by the author
>
> **Porter's nine value-chain activities are a platform-level constant, not pack content,
> and `E13`'s `contributing` arm resolves against that constant — never against pack
> capabilities.**
>
> They sit beside `ACTION_TYPES` and `ARCHETYPES` in `checks.py`, for the same reason those
> do: they are vocabulary the *engine* knows, identical in every casepack, and a hospital
> pack will use the same nine. A capability is what a company chose to build; an activity is
> a slot in a model that predates the company. Resolving one against the other is a category
> error, which is exactly why it produced eight false errors on correct content.
>
> **What 1.3 does with this ruling:** author `value_chain_coverage` against the nine, using
> those exact keys, and treat a key outside them as an error in your own authoring.
>
> **What 1.3 does NOT do:** implement the check. `E13`'s new arm is a **1.2** change and it
> is not built — so `value_chain_coverage` and `unit_responses[].contributing` remain
> unvalidated during this packet. **Author as though the check existed.** It is on 1.2's
> list and it will arrive; content authored against the ruling will pass it, and content
> authored loosely will not.
>
> *Reversible if 1.2's implementation shows the nine are not in fact case-invariant. Nothing
> in this packet depends on the ruling being permanent — only on it being decided.*

### 5.2 The judged part — catalog items

The ~19 buildable rows carry only `cost_value` in mis_lite. Everything else in the
attribute vector (capacity, availability, service life, staff load, sizing driver,
entity ownership, integration requirements, training tiers) **does not exist and must be
authored.**

The builder does **not** invent these freely. Author them against:
- the fixed figures in `0.3/spec.md §5.4` where they overlap
- a stated rationale per item, recorded in provenance
- archetype defaults for anything not case-specific

**If a value cannot be justified, mark it `TODO: calibrate` and report it.** 1.7's harness
is where guesses get tested; a confident wrong number is worse than a flagged one.

### 5.3 Provenance record

`packs/riverside_grocery/PROVENANCE.md` — mandatory, one row per harvested collection:

```
| pack field | mis_lite source | rows in | rows out | mode | notes |
|---|---|---|---|---|---|
| strategies[].capability_weights | component_strategy_fit | 168 | 76 | normalised | only the ~19 buildable components transfer; raw multipliers below |
| catalog[] | component_types_master | 45 | 19 | judged | 26 concepts → docs/curriculum-coverage.md |
| … |
```

Also records: every discarded table with the reason, every `TODO: calibrate`, and the raw
fit multipliers before normalisation.

**A harvest with no provenance file is not done.** In two years nobody will remember why
26 rows vanished.

---

## 5.4a Seed — the harvest IS the seed *(GOVERNANCE §4.9)*

```
command     python -m app.casepack.harvest --from mis_lite --to riverside_grocery
demonstrate provenance table: rows in, rows out, mode, per source table
            the ~20 pinned figures read back and matched against 0.4 §5.4
            every TODO: calibrate listed in the report
```

**No packet downstream may run against a pack containing unreported `TODO`s.**

---

## 6. Invariants

| # | Invariant | Check | Expected |
|---|---|---|---|
| I1 | No writes to mis_lite | `git ls-files 'backend/scripts/harvest*' \| xargs grep -niE "\b(insert\|update\|delete\|alter\|drop\|truncate\|create)\s+(into\|table\|from\|set\|index)"` — SQL write verbs in statement position, not bare substrings | zero |
| I2 | No `trialNNN` anywhere in the pack | `grep -rn "trial" packs/riverside_grocery/` | zero |
| I3 | No textbook prose in student-visible labels | `grep -rniE "traditional\|suitable for\|optimized for\|designed for" packs/riverside_grocery/labels.yaml` | zero |
| I4 | Weights normalised, not copied | every strategy's `capability_weights` sums to 1.0 ±0.001 | 4/4 |
| I5 | Every discarded table appears in PROVENANCE | cross-check §5.1 discards vs the file | all present |
| I6 | Pack passes 1.2 with zero ERRORs | `backend/bin/validate_casepack backend/packs/riverside_grocery` | **exit 0** |
| I7 | §5.4 figures match the pack | script comparing the 0.3 fixed data to loaded pack values | exact |
| I8 | **Every capability can raise a signal** (CG-1) — *rewritten v1.1* | `validate_casepack … \| grep -E "E12\|E20"` **and** assert every rule declares a `metric_kind` | no `E12`, no `E20`, no rule undeclared |
| I9 | **Every strategy is drawn by ≥6 events** (CG-2) — *rewritten v1.1* | for each strategy, count events whose `strategy_affinity` includes it or is empty | all 4 strategies ≥ 6 |
| I10 | **Six policy switches, each with a stated cost** (CG-4) | `grep -c "^- key:" policies.yaml` and read each | 6, none bare |
| I11 | **`obligation_rules.yaml` exists and references real entities and policies** (CG-5) | cross-reference against `entities.yaml`, `policies.yaml` | zero orphans |
| I12 | **Every referenced label key resolves** — *added v1.1* | `validate_casepack … \| grep E07` | zero |

> **I9 was unmeasurable as written and is rewritten.** v1.0 required *"≥1 event in ≥4 of 6
> rounds"*. `Event` carries **no round field**, and 1.5 §3 decision 9 settles that it never
> will — round timing stays emergent from preconditions, because two timing systems would
> let a card satisfy its preconditions in a round its binding forbids. The check as written
> could not be run at all. It is now the per-strategy draw count, which is the same check
> 1.2 will enforce as `W08` at `N = 6` (1.5 §10).
>
> **I8 was also too weak.** `grep E20` alone passes a pack whose rules all carry `null`
> thresholds — the precise loophole that made CG-1's original closure condition gameable
> (`1.2-001`). It now requires `E12` clean and every rule's kind declared.
>
> **Numbering note (`R2`).** I6 and I7 kept their numbers and their guards and are simply
> moved above I8–I11, where they were previously listed out of order. I8 and I9 keep their
> numbers with **changed checks**, stated above. I12 is new. No guard was dropped.

---

## 7. Pre-Flight Verification Register

| # | Claim | Tag | Check | Expected |
|---|---|---|---|---|
| 1 | 1.1 and 1.2 merged | `[V]` | `ls backend/app/casepack/{models,loader,checks,validate}.py backend/bin/validate_casepack` | all present — 1.2 merged at `d5647d8` |
| 1a | **The 1.1 gate is lifted** (§3a additions 1–4) | `[V]` | from `backend/`: `python3 -c "from app.casepack.models import Labels, WatchRule, PlatformService, Casepack as C; print('metric_kind' in WatchRule.model_fields, 'owns_entities' in PlatformService.model_fields, 'obligation_rules' in C.model_fields, sorted({'entities','catalog','watch_rules','questions'} & set(Labels.model_fields)))"` | `True True True ['catalog', 'entities', 'questions', 'watch_rules']`. **Any False or missing → STOP and report which**, unless the dispatch explicitly deferred `I6` per §3a |

> **Row 1a was corrected 2026-08-17, before any builder saw it.** As first written it grepped
> `^  (entities|catalog|…)` — **two** spaces, against a four-space Python class body. It
> matched nothing, and the row's instruction is *"any absent → STOP"*, so **1.3's builder
> would have stopped on a gate that was in fact lifted.** Found by the 1.1 rework builder
> (`R5`) and verified here.
>
> This is the fourth pre-flight row on this project whose check could not return the right
> answer — 1.2's rows 3 and 4, 1.5's row 5, now this one — and all four were *greps whose
> pattern did not match the artifact*. The replacement introspects the model instead: it
> cannot silently no-match, and every element of the expected output is named.
| 1b | **The `1.2-020` ruling has been made** | `[A]` | read §5.1b's ruling box | **SATISFIED 2026-08-18** — Porter's nine are a platform constant; `E13` resolves against it, not against capabilities. Author `value_chain_coverage` against the nine |
| 1c | **Two checks are DEFERRED, not waived** | `[A]` | read the deferral box in §9 | the dispatch names both. **Absent → STOP** — a deferred check that nobody recorded is an invisible gap |
| 2 | mis_lite reachable read-only | `[V]` | `PGPASSWORD=… psql -h 192.168.50.38 -U donwh -d mis_lite -c "select 1"` | 1 |
| 3 | Row counts match `design/01` §2 | `[V]` | count each table in §5.1 | match, or report drift |
| 4 | `component_strategy_fit` = 168 | `[V]` | `select count(*) from component_strategy_fit` | 168 |
| 5 | The nine `*_mapping` tables are uniform enough to transform mechanically | `[A]` | for each: `select ideal_value, count(*) from <t> group by 1 order by 2 desc limit 5` | **if one value dominates, that table is placeholder-seeded — report before transforming** |
| 6 | Skeleton pack exists from 1.1 | `[V]` | `ls packs/riverside_grocery/` | files present |

Row 5 is the important one. `design/01` §4 found this pattern in one table; the check
looks for it in all nine.

---

## 8. Build steps

1. **Read-only extraction script** → intermediate JSON, one file per source table.
   *Verify:* I1; row counts match pre-flight.
2. **Mechanical transforms** (the `mechanical` rows in §5.1). *Verify:* counts in = counts
   out, or a documented reason.
3. **Normalisation transforms** — fit multipliers, option ladders. *Verify:* I4; raw values
   preserved in provenance.
4. **Judged authoring** — catalog attribute vectors, event seeds, persona instances.
   *Verify:* every value justified or marked `TODO: calibrate`; I7.
5. **Provenance + curriculum-coverage doc.** *Verify:* I5; the 26 concepts are documented.
6. **Validate.** *Verify:* I6 — exit 0.

---

## 9. Definition of Done

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1, 1a, 1b, 2–6, esp. row 5 per table | | |
| Steps 1–6 verified | | |
| I1 read-only | | |
| I2 no `trialNNN` | | |
| I3 no textbook prose in labels | | |
| I4 weights normalised | | |
| I5 discards documented | | |
| **I6 validator exit 0** — the packet's exit condition (§3 decision 7) | | |
| I7 0.3 figures match | | |
| I8 every capability can signal, every rule declares its kind — CG-1 | | |
| I9 every strategy drawn by ≥6 events — CG-2 | | |
| I10 six policies with costs — CG-4 | | |
| I11 obligation rules present and resolving — CG-5 | | |
| I12 every label key resolves — `1.2-012` | | |
| CG-3 project duration resolved and stated | | |
| CG-6 — **second home eliminated**, not reconciled; mockup conflict reported | | |
| `1.2-024` label sections authored (gated on 1.1 addition 3) | | |
| `1.2-013` verified resolved — the deck is three cards, not one | | |
| O1, O2, O3 recorded | | |
| `PROVENANCE.md` complete | | |
| `docs/curriculum-coverage.md` — the 26 concepts | | |
| Every `TODO: calibrate` listed in the report | | |
| **Seed** — harvest command reproducible from a clean pack directory | | |
| Browser / auth / instance canaries | | **N-A** — headless |

> ### Deferrals — updated 2026-08-18, and these are the only two
>
> The 1.1 and 1.2 gates are both **lifted**. `I6`, `I8`, `I9` and `I12` are reachable and
> are **not** deferred; the §3a paragraph they came from is superseded.
>
> **Exactly two checks are deferred, both because 1.2 has not built them yet:**
>
> | Deferred | Why | What 1.3 does instead |
> |---|---|---|
> | **`I11`** — obligation rules resolve against real entities and policies | `1.2-037`: no validator check exists. `grep -n obligation validate.py` → zero | Author `obligation_rules.yaml` correctly anyway, and **hand-verify** every `entity`, `policy` and `arms` key against the pack. Paste that cross-check in `dod.md` — it is the evidence standing in for the missing check |
> | **`E13`'s `value_chain_coverage` arm** | The `1.2-020` ruling is made but not implemented | Author against Porter's nine as ruled, and hand-verify the keys the same way |
>
> **Deferred is not waived.** Record both in `dod.md` with what you verified by hand and what
> remains unchecked by machine. A DoD row marked N/A without a reason is how a gap becomes
> invisible — and both of these guard content this packet is authoring for the first time.

---

## 10. Changelog

**v1.1 — 2026-08-16.** Revised by the author against merged 1.2 (`d5647d8`), both its
audits, and 1.5's spec v1.1. No build cycle is open and no builder has been dispatched, so
`handoffs/README.md` **R1** does not apply. **R2:** I6 and I7 keep their numbers and guards
and are only reordered; **I8 and I9 keep their numbers with changed checks**, both stated in
§6; **I12 is new**. No guard was dropped.

| Change | Why |
|---|---|
| **§3a — the 1.1 gate** | Four schema additions must land before CG-1 and CG-5 can close. Eleven of the pack's twenty errors depend on two of them. Without this section a builder reaches step 6 and stops |
| §3 decisions 7–10 | The validator is real and is now the exit condition; `metric_kind` on every rule; CG-2 measured per strategy; CG-6 enforced by `E14` |
| §5.1a — CG-1 restated | **Six** mute capabilities, not five. `firm_infrastructure` has a rule whose thresholds are both `null` — as mute as none, and the loophole that made the original closure condition gameable |
| §5.1a — CG-2 restated | Per-strategy draws at `N = 6`. The old *"most rounds"* wording was unmeasurable against a schema with no round field |
| §5.1a — CG-4 named | Three switches exist against six; the six are now named, and the existing three are keyed by mechanism rather than by policy dimension |
| §5.1a — CG-5 pointed at 1.5 §5.4 | The section's shape is already specified. Authoring a second design here is how two shapes reach `main` |
| §5.1a — CG-6 updated | `E14` now enforces it. Clearing the error is necessary but **not sufficient** — the second home must be eliminated, not reconciled |
| **§5.1b — content defects, new** | `1.2-012` (eight missing label keys, the pack's largest error group), `1.2-024`, `1.2-013`, and the `1.2-020` ruling this packet must not start without |
| §6 — I8, I9 rewritten; I12 added | I9 could not be run at all; I8 passed a pack whose rules all carry `null` thresholds |
| §7 — rows 1a, 1b added | The gate and the ruling, both checked before a builder writes anything |
| §9 — DoD | New rows; the duplicated *"every TODO listed"* row removed; deferral rule stated |

**Not changed, deliberately.** The §5.1 transform map, the §5.2 judged-authoring rules, the
§5.3 provenance requirement and O1–O3 all still hold. The harvest itself was well specified
in v1.0; what had gone stale was everything downstream of it.
