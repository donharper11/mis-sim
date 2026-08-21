# 1.4 — Scoring Engine · Definition of Done

**Builder:** Claude (opus-4-8) · **Date:** 2026-08-21 · **Branch:** `build/1.4-scoring`
**Spec:** `handoffs/1.4-scoring-engine/spec.md`

Evidence commands are run from `backend/`. The engine is pure and headless, so the
browser / auth / instance canaries are **N-A** (spec §9); the property tests and the
seed demonstration stand in their place (QUALITY_PROTOCOL §2, adapted per dispatch).

---

## Constraint update during this build cycle (handoffs/README.md R1)

**2026-08-21 — POLICY-DISTANCE WORK PAUSED (coordinator).** The `design/07 §3.5b`
"`PolicyOption.options` is ordinal / distance" ruling is being reworked and
independently re-audited, so the interpretation is **UNSETTLED**. No engine code may
encode whether policy-`ideal_posture` alignment is an exact match or a distance along
the options ordering, nor whether `options` is ordinal or unordered.

- **What it defers:** the information-policy-switch portion of spec **§5.5** stakeholder
  alignment (the `by_decision` / `ideal_posture` path over `PolicyOption.options`).
- **How it is handled here:** that path is a clearly-marked deferred hook,
  `management.policy_switch_alignment`, which **raises `NotImplementedError`** and is
  **not called** by the scoring path — it can never silently contribute a number. The
  `_stakeholder_alignment` computation scores only the capability-rollout dimension of
  §5.5, consuming an opaque `StakeholderDecisionAlignment.alignment` scalar; it does not
  read `PolicyOption.options`.
- **Effect on the pins:** none. **Tech 0.750 and Org 0.507 have no policy dependency
  and hold.** The **Mgmt 0.648 / realised 0.249** pin is reproduced **without any
  policy-options interpretation** — the seed's stakeholder scalars are rollout-alignment
  inputs, so the Mgmt pin is *not* blocked by the pause. If the reworked policy
  interpretation later becomes a *component* of stakeholder alignment, the Mgmt seed
  scalar `OPERATIONS_ALIGNMENT` will need recalibrating; that is expected and flagged.
- **Already-committed code encoding an options interpretation:** **none.** Verified
  `grep -rniE "policyoption|ideal_posture|by_decision|\.options|policies" app/engine seeds app/seed`
  → no references; and nothing was committed before the update arrived.

See finding **F-5**.

---

## 0. Pre-Flight Verification Register (spec §7) — run BEFORE any code

| # | Claim | Result | Evidence |
|---|---|---|---|
| 1 | 1.1/1.3 merged; Riverside pack loads | **PASS** | `python -m app.casepack.loader packs/riverside_grocery` → import exit 0; `load_casepack` returns 7 capabilities · 14 catalog · 4 strategies |
| 2 | Pack validates clean | **PASS** | `./bin/validate_casepack packs/riverside_grocery` → `0 errors · 0 warnings · exit 0` |
| 3 | `design/02` lists the factors | **PASS** | `grep -c "^\|" design/02-traceability-matrix.md` → 75 (matrix present) |
| 4 | 0.3 fixed-figures string present | **DEVIATION** | `grep -n "0.75 · Org 0.51 · Mgmt 0.65" handoffs/0.3-mockup-pilot/spec.md` → **not found**. The string does not live in the 0.3 spec. It lives in the delivered mockup `situation.html` (a 0.4-lineage screen that the 0.3 **v3** respec deleted), and is quoted in `findings/0.3-2026-07-27-mockup-audit.md:260` (`Tech 0.75 · Org 0.51 · Mgmt 0.65`, `Held back by: Organisation`). The **arithmetic target itself is intact and approved** — it is restated precisely in this spec §5.6/§5.7 (0.750 / 0.507 / 0.648 / 0.249, throttle org) and I compute against that. Per the dispatch, this is a deviation to **report, not work around**; it is not a FAIL (the target exists and is approved) and not a STOP (nothing is missing). See §8 finding F-1. |
| 5 | Graph library available or needed | **DEVIATION → resolved** | `grep -n networkx backend/requirements.txt` → absent. The spec's own row authorises the fallback: **implemented articulation points directly** (Tarjan, ~35 lines, `app/engine/graph.py:articulation_points`). No dependency added — this keeps the engine pure (I2). |

No FAIL rows. Both deviations are the register pointing at stale/absent artefacts, not the underlying claims failing; both are resolved above and reported in §8.

---

## 1. The pin (spec §5.7, §8 step 2) — Riverside R3 order_fulfilment

**Computed from the seed `backend/seeds/riverside_r3.py`, not asserted.**

```
$ python -m app.engine.score riverside_r3
scenario riverside_r3: order_fulfilment tech 0.750 org 0.507 mgmt 0.648 realised 0.246 throttle org
```

| Figure | Pinned | Computed (6 dp) | Δ | Within 0.01? |
|---|---|---|---|---|
| tech | 0.750 | 0.750008 | 0.000008 | ✅ |
| org | 0.507 | 0.507003 | 0.000003 | ✅ |
| mgmt | 0.648 | 0.648006 | 0.000006 | ✅ |
| realised | 0.249 | 0.246408 | 0.002592 | ✅ |
| throttle | org | **org** | — | ✅ |
| spofs | `[wan_link, hq_firewall, core_switch, order_app]` | **exact match** | — | ✅ |

**On realised 0.246 vs 0.249:** the three terms hit their pins to 5 dp; realised is
their *plain product* (invariant I6), so realised is whatever the terms multiply to:
`0.750 × 0.507 × 0.648 = 0.246`. The spec's own example writes `0.249`, which is the
product of the **2-decimal display** terms (`0.75 × 0.51 × 0.65 = 0.2486 → 0.249`).
The 0.003 gap is that display-rounding artefact inside the spec's example, not an
engine error — and it is inside tolerance either way. The seed's `firm_score`
(0.2493) lands on 0.249 by the same arithmetic. **No STOP condition.**

---

## 2. Spec §9 Definition-of-Done table

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–5 | ✅ | §0 above (rows 4, 5 are reported deviations, not FAILs) |
| Steps 1–6 verified | ✅ | Step 1 graph: `test_articulation_points_linear_chain`, `test_i8_*`. Step 2 tech≈0.75, Step 3 org≈0.51, Step 4 mgmt≈0.65 + I4, Step 5 realised≈0.249 + throttle=org: `test_pin_riverside_r3_order_fulfilment`. Step 6 property tests: I5–I8 below |
| Riverside R3 reproduces 0.75/0.51/0.65/0.249 | ✅ | §1 |
| I1–I8 | ✅ | §3 |
| O1, O2, O3 recorded | ✅ | §4 |
| Every `design/02` §A–D factor implemented or deferred with a reason | ✅ | §5 |
| Decomposition record emitted for every capability | ✅ | `score_team` emits one `decomposition_record` per capability (7/7); keys `{capability, realised, terms, throttle, sub_factors, evidence, spofs}` verified well-formed |
| Seed — `riverside_r3` seeded; scorer COMPUTES 0.750/0.507/0.648/0.249 from it | ✅ | `python -m app.seed.demo --scenario riverside_r3` builds the state; `python -m app.engine.score riverside_r3` computes the figures from it |
| Browser / auth / instance canaries | **N-A** | Pure, headless functions — no browser, no state, no I/O |

---

## 3. Invariants I1–I8 (spec §6)

| # | Invariant | Check | Result |
|---|---|---|---|
| I1 | No pack-identity branching | `grep -rniE "riverside\|grocer\|pack_key *==" app/engine/` | ✅ zero hits |
| I2 | Engine pure — no I/O, clock, randomness | `grep -rnE "session\|execute\|datetime\.now\|random\.\|requests\.\|open\(" app/engine/` | ✅ zero hits |
| I3 | No displayed English | `grep -rnE '"[A-Z][a-z]+ [a-z]+ [a-z]+' app/engine/*.py \| grep -v '#\|"""\|raise'` | ✅ zero hits |
| I4 | No catalog item raises Management | `grep -rn "mgmt\|management" app/engine/catalog*.py` | ✅ zero references |
| I5 | Determinism | `test_i5_determinism_one_hash_over_100_runs` — 100 runs, SHA-256 of the record | ✅ one distinct hash |
| I6 | Across-MOT is plain product | `grep -n "tech \* org \* mgmt" app/engine/score.py` → line 52; `test_i6_realised_is_plain_product_of_three_terms` (all 7 caps) | ✅ present, no geomean across terms |
| I7 | A zero in any term zeroes realised | `test_i7_zero_in_any_term_zeroes_realised` (tech=0 via no nodes; org=0 via no deployment) + `test_i7_direct_arithmetic` | ✅ holds for all three |
| I8 | Capacity is `min` not `sum` | `test_i8_adding_a_slow_node_never_raises_capacity` + `test_i8_bottleneck_is_min` | ✅ holds |

Test suite: `PYTHONPATH=. python -m pytest tests/test_engine_scoring.py -q` → **9 passed**.

---

## 4. Open decisions — recorded (spec §4)

| # | Decision | Default | Implemented as |
|---|---|---|---|
| **O1** | Sub-factor weights inside each geometric mean | equal, hard-coded, v1 | `mathx.geomean` weights every sub-factor equally; no per-casepack weight surface. Recorded; revisit after 1.7 |
| **O2** | Hard-capped capability (missing required role): 0 or floor | floor 0.3 on coverage | `technology.COVERAGE_FLOOR = 0.3`; a missing required role floors coverage at 0.3, and the missing role is surfaced in `evidence["missing_roles"]` so the student still sees it |
| **O3** | Management scope: capability or firm-wide | hybrid | `management.py`: `governance` and `stakeholder_alignment` are per-capability; `strategic_alignment`, `portfolio_discipline`, `signal_responsiveness`, `follow_through` are firm-wide (`FirmManagement`, computed once, applied identically to each capability) |

---

## 5. Every `design/02` §A–D factor — implemented or deferred with reason

### §A Technology — all implemented
| Factor | Status | Where |
|---|---|---|
| Coverage — required roles | ✅ | `graph.coverage_fraction`, `technology._coverage` (O2 floor) |
| Coverage — required entities | ✅ | `graph.owner_nodes` (ordinal level check), `technology._data_adequacy` |
| Capacity — platform pool + application draw | ✅ | `graph.bottleneck_capacity` (node throughput = pool/app draw), `technology.technology` (÷ demand). Note: pool utilisation *evolution* (draw → throughput each round) is 1.6's; 1.4 reads the round's throughput |
| Reliability — path availability | ✅ | `graph.path_reliability` |
| Reliability — redundancy | ✅ | graph-derived: a failover/sibling edge removes an articulation point, lowering the SPOF set |
| Single points of failure | ✅ | `graph.articulation_points` (Tarjan), `graph.spofs_on_path`, `graph.blast_radius` |
| Data adequacy — integration | ✅ | integration-edge check in `technology._data_adequacy` / `_has_integration_edge` |
| Data adequacy — inconsistency | ✅ | dual-owner-without-integration penalty (`INCONSISTENCY_PENALTY`) |
| Data currency / component EOL | ✅ | `technology._currency` = mean over serving nodes of `1 − age/service_life` |

### §B Organisation
| Factor | Status | Where / reason |
|---|---|---|
| Training coverage | ✅ | `organisation.organisation` (`trained_count/people_affected`) |
| Training decay | ⏸ deferred → 1.6 | Decay is round-to-round state evolution needing `casepack.decay_rate` + prior state; 1.4 scores one snapshot. Matrix marks it 🔵 *recomputed each round* |
| Process fit | ✅ | `PROCESS_FIT` map (redesigned 1.0 · partial 0.5 · unchanged 0.25) |
| Adoption rate | ✅ (consumed) | Read from `DeploymentState.adoption`. Matrix lists adoption as `round_result.adoption` (persisted, 🔵 derived); the simulation formula `f(training×sponsorship×usability−resistance)` is 1.6 state evolution — the spec's "formula in §5.6" is a forward reference (§5.6 is the decomposition record; no formula is stated there and no casepack adoption-params exist in the 1.1 schema). See finding F-2 |
| Resistance | ✅ | `resistance_inv = 1 − org_unit.resistance` |
| Change-volume shock | ⏸ deferred → 1.6 | Resistance *evolution* with deployments-per-round; 1.4 reads current `org_unit.resistance` (matrix 🔵) |
| IT staffing (G1) | ✅ | `organisation.staffing_factor = min(1, staff_fte/load_fte)` — the operational load pool |
| Stakeholder alignment (G6 layer 1) | ✅ | consumed as `StakeholderDecisionAlignment.alignment` in `management._stakeholder_alignment`; realised-value-weighted satisfaction emitted separately (§5.5, `rollup.stakeholder_satisfaction`) |

### §C Management
| Factor | Status | Where / reason |
|---|---|---|
| Governance coverage | ✅ | `management._governance` ((owner+sponsor)/2) |
| Strategic alignment | ✅ | `management._strategic_alignment` (cosine of spend-by-capability vs `capability_weights`) |
| Portfolio concentration | ✅ | Herfindahl vs `expected_concentration` |
| Run/Grow/Transform mix | ✅ | total-variation distance vs `target_rgt_mix` |
| Maintenance floor | ✅ | maintenance ratio vs `maintenance_floor_pct` |
| Signal responsiveness | ✅ | `acted_before_fire / actionable` (ledger supplied by state; 1.5 populates it in production) |
| Follow-through | ✅ | `1 − (abandoned + deployed-never-trained)/initiated` |
| Deployed-but-never-trained | ✅ | the `never_trained` term inside follow-through |
| Decision rationale consistency | ⏸ deferred → 1.5 | Reads `inbox_response.rationale_tag` from event responses; events/inbox are 1.5, out of 1.4 scope (spec §1) |
| Rationale quality (±10% LLM modifier) | ⏸ deferred | G2 (open, non-blocking). An LLM surface — excluded from the engine by GOVERNANCE §4.7 (the engine judges; the LLM never scores) |

### §D Strategy / Policy / Cost
| Factor | Status | Where / reason |
|---|---|---|
| Strategic intent declaration | ✅ (consumed) | `TeamState.declared_strategy` drives weights, alignment, portfolio |
| Integration count | ✅ | `ArchEdge(kind="integration")` consumed by data adequacy and connectivity |
| Hosting placement / hybrid / split-rule | ⏸ deferred → cost layer / 1.6 | Placement drives capex/opex and staff load, not a scored term of its own; its people effect (G1) *is* scored via `staff_load`→`load_fte`. The cost ledger is out of 1.4 scope (spec §1) |
| Strategy reopen cost · Capex · Opex · Debt · Capital request · TCO | ⏸ deferred → cost layer / 1.6 | Financial ledger; spec §1 puts persistence and cost out of scope. The BSC **financial** perspective is therefore marked `financial_partial=True` and computed as the cost-discipline proxy the engine can see (alignment × portfolio), never fabricated |
| Information policy · policy-vs-practice · obligations | ⏸ deferred → 1.5 | Signals, events and obligations are 1.5 (spec §1 out of scope) |

### §E Outcomes (the ones 1.4 owns)
| Element | Status |
|---|---|
| Realised value per capability | ✅ `score_capability` |
| Causal trace ("throttled by …") | ✅ `throttle` + full decomposition record (spec §5.6) |
| Balanced Scorecard (4 perspectives) | ✅ `rollup.balanced_scorecard` (financial partial, marked) |
| Signals missed · event resolution · competitor · debrief · instructor override | ⏸ out of 1.4 scope (1.5 / 1.6 / UI) |

---

## 6. Files delivered

```
backend/app/engine/__init__.py        purity contract note
backend/app/engine/mathx.py           clamp, geomean (O1 equal weights), round6
backend/app/engine/state.py           TeamState + component dataclasses (the 2nd input)
backend/app/engine/graph.py           serving path, min-capacity, path availability,
                                       Tarjan articulation points, SPOFs, blast radius
backend/app/engine/catalog.py         read-only casepack lookups (I4: no earned-term refs)
backend/app/engine/technology.py      tech term + sub-factors + evidence + spofs
backend/app/engine/organisation.py    org term incl. the IT staffing pool (G1)
backend/app/engine/management.py      mgmt term incl. stakeholder alignment (O3 hybrid)
backend/app/engine/rollup.py          firm score, Balanced Scorecard, stakeholder satisfaction
backend/app/engine/score.py           orchestrator, decomposition record, CLI (I6 lives here)
backend/app/seed/__init__.py          demo-seed package
backend/app/seed/demo.py              load_scenario + `--scenario` CLI (wires loader↔seed)
backend/seeds/__init__.py             scenario data package
backend/seeds/riverside_r3.py         the architecture that PRODUCES the pinned figures
backend/tests/test_engine_scoring.py  I5–I8 + the pin + graph fixtures (9 tests)
```

No changes to any 1.1/1.3 file; no new runtime dependency; `CONTRACTS.md` unchanged
(no new cross-cutting field — the engine consumes existing contract fields).

---

## 7. Verification ladder (QUALITY_PROTOCOL §2)

- **Rung 1 (contract):** read models, loader, pack, `CONTRACTS.md` before coding.
  Confirmed `capability_weights`, `placement`, `required_roles[]`, `level_of_detail`
  (ordinal), `cleared_by[]` shapes against the parsed pack. ✅
- **Rung 2 (implementation):** `py_compile` clean on all engine/seed files; validator
  clean; 9/9 property + pin tests pass. mypy not installed in this env — `py_compile`
  is the standing type/compile gate, stated per protocol. ✅
- **Rung 3 (runtime / seed):** `python -m app.seed.demo --scenario riverside_r3` builds
  the demo state from a clean checkout; `python -m app.engine.score riverside_r3`
  computes the figures **from** that seed. ✅
- **Rungs 3 (auth/instance) · 4 (browser) · 5 (UX):** **N-A** — pure headless
  functions, no browser, no session, no screen. Stated, not silently skipped.
- **Rung 6 (audit):** for the independent fresh-context auditor (mandatory, E*-class).

---

## 8. Findings for the auditor

- **F-1 (pre-flight row 4, stale pointer — report only).** The register greps the 0.3
  spec for `0.75 · Org 0.51 · Mgmt 0.65`; that string was in the delivered mockup
  `situation.html`, which the 0.3 v3 respec deleted (see `findings/0.3-2026-07-27-mockup-audit.md:260`).
  The arithmetic target is intact and approved in this spec §5.6/§5.7. Suggest the
  author repoint row 4 at the audit finding or at §5.6. No engine impact.
- **F-2 (spec §5.2 adoption formula — under-specified, resolved by scope boundary).**
  §5.2 lists adoption as `f(training×sponsorship×usability−resistance)`, "formula in
  §5.6", but §5.6 states no formula and the 1.1 schema carries no adoption-formula
  params. Resolved by treating adoption as a consumed persisted input
  (`round_result.adoption`, matrix §B, 🔵 derived); the simulation that produces it is
  1.6 state evolution. Recorded, not improvised. If the author intends 1.4 to own the
  adoption formula, that needs casepack params (a schema change) and a calibration pass.
- **F-3 (BSC financial is partial by construction).** The cost ledger (capex, opex,
  TCO, debt) is out of 1.4 scope (spec §1); the financial perspective is computed as a
  cost-discipline proxy and flagged `financial_partial=True`. Not a defect — a declared
  boundary — but the debrief UI must not present it as a settled financial number until
  the cost layer lands.
- **F-5 (policy-distance pause — coordinator, 2026-08-21).** The §5.5 information-policy-
  switch path is deferred (see the constraint-update section above). It is a hook that
  raises `NotImplementedError` and is not wired into scoring; stakeholder alignment here
  is the capability-rollout dimension only. The auditor should (a) confirm no engine code
  reads `PolicyOption.options`, and (b) treat the policy interpretation as UNSETTLED —
  the pack comments asserting "options is ordinal" are exactly what is under rework and
  must not be read as decided. When policy-distance is settled and re-audited, revisit
  whether it becomes a component of stakeholder alignment and recalibrate the Mgmt seed.
- **F-4 (calibration knobs).** Four seed inputs (`ORDER_THROUGHPUT`,
  `ORDER_STORE_INSTALLED`, `STORE_OPS_RESISTANCE`, `OPERATIONS_ALIGNMENT`) are fitted so
  the terms reproduce the approved figures. None is a mockup-pinned number — the mockups
  pin the *terms*, not the raw throughput/resistance behind them — so this is authoring
  the architecture to the target, which is exactly what spec §5.7 asks ("the
  architecture that PRODUCES Tech 0.75"). 1.7's calibration harness is where these move.
```

---

# Closeout — information-policy dimension (2026-08-21)

Appended, not rewritten. The audit evidence above is the original 1.4 core; this section
records the follow-up built under `closeout-spec.md` on branch `build/1.4-closeout` (cut
from `main` at `34238f4`; the original `build/1.4-scoring` is stale, behind `main`). Full
narrative in `handoffs/1.4-scoring-engine/closeout.md`.

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–10 | PASS | All 10 reported before code; base `34238f4`; validator 0/0; deferred hook had no call site; no prior policy state; 9 seed tests green |
| Step 1 — state contract + resolver + null/negative + C2–C7 | PASS | `PolicyDecisionState` + `TeamState.policy_decisions`; `_resolve_policy_decisions`, `_asymmetric_alignment`; `tests/test_policy_dimension.py` (24 tests) |
| Step 2 — two Management factors + evidence (C1/C8/C11/C12) | PASS | `FirmManagement.policy_alignment/policy_discipline`; folded into geomean; per-capability evidence gains exactly two keys; C8 hand-verified (six inputs byte-identical) |
| Step 3 — six seed decisions + computed pins | PASS | attentive seed, all six `actively_decided=True` at authored defaults; `policy_discipline=1.0`, `policy_alignment=0.4676` computed |
| Step 4 — documents + full regression | PASS | spec/dod/design-02/register/CONTRACTS updated; full pytest 32 passed; validator text+JSON clean; fixture matrix; raw-fit guard |
| C1 — Tech/Org unchanged | PASS | Tech `0.750008`, Org `0.507003` to 1e-6 (`test_engine_scoring.py`) |
| C2 — permissive penalised more than strict | PASS | `test_c2_equal_distance_penalizes_permissive_more`, n=2..6 |
| C3 — exact match = 1 | PASS | `test_c3_exact_match_is_one` |
| C4 — alignment in [0,1] | PASS | `test_c4_alignment_in_unit_interval`, n=2..10 exhaustive |
| C5 — order consumed, not string equality | PASS | `test_c5_reversing_option_order_changes_the_score` |
| C6 — active default counts as managed | PASS | `test_c6_active_default_counts_as_managed` |
| C7 — no silent invalid input | PASS | six negative tests, all raise `ValueError` |
| C8 — existing six Mgmt inputs unchanged | PASS | seed mgmt sub-factors: the six pre-existing values byte-identical; only two keys added |
| C9 — no casepack identity branch | PASS | `git ls-files backend/app/engine | xargs grep -niE "riverside|grocer|pack_key *=="` → zero |
| C10 / I2 — engine pure | PASS | no `open(`/`Path(`/`read_text`/clock/random in `backend/app/engine/` (one docstring mentions "yaml") |
| C11 — scores come from pack + state | PASS | `test_c11_*` mutate one selection and one preference ideal independently |
| C12 — ignoring policy not neutral | PASS | `test_empty_runtime_tuple_*`: discipline 0.25, Mgmt lower |
| C13 — raw-fit guard green | PASS | `tests/test_raw_fit_isolation.py` 2 passed |
| New Mgmt/realised pins recorded | PASS | Mgmt `0.656778`, realised `0.249744`, firm_score `0.254585` (spec §5.7) |
| Decomposition carries both policy factors | PASS | all 7 capabilities: `sub_factors.mgmt.{policy_alignment,policy_discipline}` + Mgmt evidence |
| Register F4, E2 closed; G2 deferred | PASS | `findings/OPEN-REGISTER.md` |
| main + unrelated worktrees/files untouched | PASS | see closeout.md §confirmations |
| Nothing pushed/merged/deployed/migrated | PASS | branch committed locally only; auditor gate pending |
| Ladder rungs 3(auth/instance)/4/5 | N-A | pure headless scorer; no DB/session/UI |
| Independent audit | PENDING | required before merge; builder does not declare approval |

**Computed pins:** Tech `0.750008` · Org `0.507003` · Mgmt `0.656778` · realised `0.249744`
· throttle `org` · firm_score `0.254585`. Not tuned (decision 11).
