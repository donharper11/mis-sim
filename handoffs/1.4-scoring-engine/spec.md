# 1.4 — Scoring Engine · Build Spec

**Authored under** `SPEC_PROTOCOL.md` v1.1 · **Author:** Claude · **Date:** 2026-07-26
**Phase:** 1 · **Depends on:** 1.1, 1.3 · **Blocks:** 1.5, 1.6, 1.7, all of Phase 3

> `Realised Value = Technology × Organisation × Management`, per capability.
> Multiplication, not addition. Every term computed from a click or a timestamp —
> **nothing here is LLM-judged** (`GOVERNANCE.md §4.7`).

---

## 0. Spec Basis

**Read in full:** `design/02-traceability-matrix.md` (every factor, its source, its capture
point) · `design/04-decisions-g1-g6.md` (IT staffing load pool; stakeholder layer) ·
`design/03-scoring-frame-options.md` (BSC output frame) · `design/01-mis_lite-harvest.md`
§5 (why the two engines layer) · `handoffs/1.1-casepack-schema/spec.md` §5 · `CONTRACTS.md`.

**Extraction sufficiency:** covered. The mis_lite scoring service was **not** read — it is
a different engine family (preference-share, not capability composition) and reading it
risks importing its shape.

---

## 1. Purpose and scope

**In scope:** the three MOT terms and their sub-factors · the architecture graph analysis
(coverage, path capacity, path availability, single points of failure, blast radius) ·
platform pools including the IT staffing pool · stakeholder alignment · Balanced Scorecard
roll-up · a decomposition record explaining every number.

**Out of scope:** signals and events (1.5) · round orchestration (1.6) · persistence
(1.6/2.x) · any UI · the market/attractiveness layer (deferred, `design/04` G6).

---

## 2. Project-specific statements

**Scoring factors touched:** all of them — this is the packet `design/02` was written for.
Every factor in sections A, B, C, D of that matrix is implemented here or explicitly
deferred with a reason.

**Casepack keys read:** capabilities, catalog, strategies, platform, entities, preferences.
**Casepack-identity branching:** none — invariant I1.
**Instance scoping:** the engine is **pure** — it takes state in, returns results out, and
performs no I/O. Scoping is 1.6's concern. Invariant I2.
**Business-language check:** the engine emits factor **keys**, never prose. Rendering is
`labels.yaml` plus A3. Invariant I3.

---

## 3. Settled decisions

1. **Pure functions.** No DB, no clock, no randomness. Same inputs → same outputs, always.
   This is what makes 1.7 possible and debriefs reproducible.
2. **Weighted geometric mean *within* each term; plain product *across* the three.**
   Five multiplied sub-factors crush to unreadable values; the geometric mean keeps the
   "a zero kills you" property without it. Across MOT, plain multiplication — that is the
   Laudon lesson and it must bite (`design/02`).
3. **Per capability, never global.** A team may be excellent at one and negligent at
   another; the roll-up weights by declared strategy.
4. **Bottleneck, not sum.** Path capacity is `min()` along the serving path.
5. **SPOFs do not reduce reliability.** Their downtime is already in the path product.
   They *arm events* (1.5) and set blast radius. Double-counting would be wrong.
6. **Management cannot be bought.** No catalog item raises it. Tech is bought, Org is
   funded, Management is earned.
7. **Stakeholder alignment consumes realised value, not raw spend** (`design/04` G6) — the
   single point where the harvested layer joins this engine.

---

## 4. Open decisions

| # | Question | Criteria | Reporting |
|---|---|---|---|
| **O1** | Sub-factor weights inside each geometric mean — equal, or authored per casepack? | **Default: equal, hard-coded, v1.** Authored weights are a second calibration surface before we have evidence the first one works. Revisit after 1.7 | Record |
| **O2** | Does a hard-capped capability (missing required role) score 0, or a floor? | **Default: floor of 0.3 on coverage, not 0.** A true zero makes the whole capability 0 and hides the Org/Mgmt signal, which is the lesson. The student still sees "missing" prominently | Record |
| **O3** | Should Management Quality be capability-scoped or firm-wide? | **Default: hybrid.** Governance and stakeholder alignment are per capability; portfolio discipline, signal responsiveness, and follow-through are firm-wide and apply identically to each | Record |

---

## 5. Design

### 5.1 Technology Capability — from the graph, no judgement

```
tech(c) = geomean(coverage, capacity, reliability, data_adequacy, currency)
```

| Sub-factor | Computation |
|---|---|
| `coverage` | filled ÷ required roles; missing role → capped per O2 |
| `capacity` | `min(capacity along serving path) ÷ demand_curve[round]`, clipped to 1.0 |
| `reliability` | product of node availabilities along the serving path |
| `data_adequacy` | required entities owned at ≥ required level of detail; **penalty for an entity owned by ≥2 nodes with no integration edge** |
| `currency` | `1 − (age ÷ service_life)`, floored at 0 |

**Serving path** = graph walk from any `client_access` node to the node owning the
capability's primary entity. If no path exists, coverage is capped and capacity is 0.

**SPOF detection** = remove each node on the path; if no path survives, it is a single
point of failure. Standard articulation-point logic. Reported, not scored (decision 5).

### 5.2 Organisational Readiness — from what was funded

```
org(c) = geomean(training, process_fit, adoption, resistance_inv, staffing)
```

| Sub-factor | Computation |
|---|---|
| `training` | trained ÷ affected, **decayed each round**; new hires arrive untrained |
| `process_fit` | 1.0 redesigned · 0.5 partial · 0.25 unchanged |
| `adoption` | `f(training × sponsorship × usability − resistance)`, formula in §5.6 |
| `resistance_inv` | `1 − resistance`; resistance **rises with deployments-per-round** |
| `staffing` | IT capacity pool: `min(1, capacity ÷ load)` — G1 |

**IT staffing pool (G1).** Every deployed service and application contributes `staff_load`.
Over-commitment degrades three things already scored: incident recovery duration (1.5),
lifecycle completion (`currency`), and adoption support (`adoption`). It is a modifier,
not a fourth term.

### 5.3 Management Quality — from the pattern of decisions

```
mgmt(c) = geomean(governance, strategic_alignment, portfolio_discipline,
                  signal_responsiveness, follow_through, stakeholder_alignment)
```

| Sub-factor | Computation |
|---|---|
| `governance` | owner and sponsor slots filled for this capability ÷ 2 |
| `strategic_alignment` | cosine similarity of spend-by-capability with declared `capability_weights` — a bounded [0,1] value fit for the geometric mean. *(Corrected 2026-08-21 from "dot product" per audit finding `1.4-001`: the build chose cosine similarity, which is the right input for a geomean and reproduces the pin; the spec wording was wrong, the artifact is right. R5: spec amendment, no artifact repair.)* |
| `portfolio_discipline` | geomean(concentration vs `expected_concentration`, RGT mix vs target, maintenance ratio vs floor) |
| `signal_responsiveness` | signals acted on before firing ÷ **actionable** signals (1.5 supplies the ledger; affordability filter per `findings/0.2` lineage) |
| `follow_through` | 1 − (abandoned + deployed-but-never-trained) ÷ initiated |
| `stakeholder_alignment` | per §5.5 |

**Nothing in the catalog raises any of these.** Invariant I4.

### 5.4 Realised value and roll-up

```
realised(c) = tech(c) × org(c) × mgmt(c)
firm_score  = Σ realised(c) × strategy.capability_weights[c]
```

Balanced Scorecard roll-up (`design/03`):

```
Financial          capex, opex run-rate, TCO variance, cost per transaction, debt
Customer           service outcomes, availability, unmet demand, outage blast radius
Internal Process   realised value per capability, coverage, integration, data adequacy
Learning & Growth  training coverage, adoption, resistance, staff skills, governance
```

### 5.5 Stakeholder alignment (G6, layer 1 only)

```
satisfaction(s) = alignment(s's preferences vs decisions)
                × realised value in the capabilities s cares about
```

Preferences resolve **archetype default → per-item override** (1.1 §5.7). Layers 2 and 3
(OAR weighting, market share) are **not implemented**; the data rides along unconsumed.

### 5.6 The decomposition record — the actual product

Every capability, every round, emits a structure naming **which factor throttled it**:

```python
{ "capability": "order_fulfilment",
  "realised": 0.249,
  "terms": {"tech": 0.750, "org": 0.507, "mgmt": 0.648},
  "throttle": "org",
  "sub_factors": {"org": {"training": 0.35, "process_fit": 0.50, ...}},
  "evidence": {"training": {"trained": 49, "affected": 140}},
  "spofs": ["wan_link", "hq_firewall", "core_switch", "order_app"] }
```

This is what the debrief renders and what makes the score defensible. A number without its
decomposition is not a deliverable.

---

## 5.7 Seed — a scoreable team state *(GOVERNANCE §4.9)*

```
seed        backend/seeds/riverside_r3.py — the architecture that PRODUCES Tech 0.75
              nodes, edges, deployments, org state, platform pools, governance
command     python -m app.seed.demo --scenario riverside_r3
demonstrate python -m app.engine.score riverside_r3
              → Tech 0.750 · Org 0.507 · Mgmt 0.648 · realised 0.249
              → throttle: org
```

**Computed from the seed, not asserted alongside it.** If the seeded architecture does not
produce those figures, either the seed or the engine is wrong — **STOP and report**. That
is the check that pins nineteen mockups to the engine.

---

## 6. Invariants

| # | Invariant | Check | Expected |
|---|---|---|---|
| I1 | No pack-identity branching | `grep -rniE "riverside\|grocer\|pack_key *==" backend/app/engine/` | zero |
| I2 | Engine is pure — no I/O, no clock, no randomness | `grep -rnE "session\|execute\|datetime\.now\|random\.\|requests\.\|open\(" backend/app/engine/` | zero |
| I3 | No displayed English | `grep -rnE '"[A-Z][a-z]+ [a-z]+ [a-z]+' backend/app/engine/*.py \| grep -v '#\|"""\|raise'` | zero |
| I4 | No catalog item raises Management | `grep -rn "mgmt\|management" backend/app/engine/catalog*.py` | zero references |
| I5 | Determinism | run the same state 100×, hash results | one distinct hash |
| I6 | Across-MOT is plain product | `grep -n "tech \* org \* mgmt" backend/app/engine/score.py` | present; no geomean across terms |
| I7 | A zero in any term zeroes realised value | property test | holds for all three |
| I8 | Capacity is `min` not `sum` | property test: adding a slow node never raises capacity | holds |

---

## 7. Pre-Flight Verification Register

| # | Claim | Tag | Check | Expected |
|---|---|---|---|---|
| 1 | 1.1 and 1.3 merged; Riverside pack loads | `[V]` | `python -m app.casepack.loader packs/riverside_grocery` | no exception |
| 2 | Pack validates clean | `[V]` | `validate_casepack packs/riverside_grocery` | exit 0 |
| 3 | `design/02` lists the factors implemented here | `[V]` | `grep -c "^|" design/02-traceability-matrix.md` | matrix present |
| 4 | 0.3 fixed figures for the arithmetic target | `[V]` | `grep -n "0.75 · Org 0.51 · Mgmt 0.65" handoffs/0.3-mockup-pilot/spec.md` | present |
| 5 | A graph library is available or needed | `[A]` | `grep -n "networkx" backend/requirements.txt` | absent → **NEW, add it**, or implement articulation points directly (~30 lines) |

---

## 8. Build steps

1. **Graph model + analysis** — serving path, coverage, min-capacity, path availability,
   articulation points, blast radius. *Verify:* I8; a hand-built 7-node fixture reproduces
   the `design/02` worked example.
2. **Technology term.** *Verify:* Riverside round 3 order fulfilment → `tech ≈ 0.75`
   (0.3 §5.4). A deviation >0.01 is a **STOP and report** — either the engine or the
   mockup figures are wrong, and that must be resolved, not absorbed.
3. **Organisation term** incl. the IT staffing pool. *Verify:* `org ≈ 0.51`.
4. **Management term** incl. stakeholder alignment. *Verify:* `mgmt ≈ 0.65`; I4.
5. **Roll-up + BSC + decomposition record.** *Verify:* `realised ≈ 0.249`; the record names
   `org` as throttle.
6. **Property tests.** *Verify:* I5, I6, I7, I8.

Step 2's verify step is the most important in this packet: it is where the engine and the
already-approved mockups either agree or expose a contradiction.

---

## 9. Definition of Done

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–5 | | |
| Steps 1–6 verified | | |
| Riverside R3 reproduces 0.75 / 0.51 / 0.65 / 0.249 | | |
| I1–I8 | | |
| O1, O2, O3 recorded | | |
| Every factor in `design/02` §A–D implemented or deferred with a reason | | |
| Decomposition record emitted for every capability | | |
| **Seed** — `riverside_r3` seeded; scorer COMPUTES 0.750/0.507/0.648/0.249 from it | | |
| Browser / auth / instance canaries | | **N-A** — pure functions, headless |
