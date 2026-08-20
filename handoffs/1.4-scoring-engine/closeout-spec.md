# 1.4 — Scoring Engine Closeout · Build Spec

**Authored under** `SPEC_PROTOCOL.md` v1.2  
**Author:** Codex independent audit session · **Date:** 2026-08-21  
**Phase:** 1 · **Depends on:** 1.1 policy-order rework, 1.2 validator rework, 1.3 content follow-up, merged 1.4 core  
**Reference mockup:** N-A — pure headless engine; no user-facing surface

> Close the one deliberately paused scoring path without reopening the verified 1.4 core.
> Policy choices become mechanical Management inputs; data freshness receives an honest
> producer and owner instead of remaining silently folded into component currency.

---

## 0. Spec Basis

**Read in full:**

- `GOVERNANCE.md` — multiplicative MOT model, no LLM scoring, seed and evidence rules.
- `QUALITY_PROTOCOL.md` — headless verification ladder and independent audit gate.
- `SPEC_PROTOCOL.md` — evidence, decision, invariant and DoD requirements.
- `CONTRACTS.md` — `PolicyOption.options` is ordinal, index 0 least constrained.
- `design/02-traceability-matrix.md` — policy and data-freshness capture/storage claims.
- `design/04-decisions-g1-g6.md` — stakeholder alignment feeds Management Quality.
- `design/07-decision-consequence-map.md` §3.5–3.5b — policy preferences, asymmetric
  ordinal interpretation, and information-policy discipline.
- `handoffs/1.4-scoring-engine/spec.md` and `dod.md` — original frozen MOT arithmetic,
  implemented factor placement, seed pin and declared policy pause.
- `findings/1.4-2026-08-21-audit.md` — independent PASS WITH FINDINGS.
- `findings/OPEN-REGISTER.md` — F4 policy-distance owner and G2 data-freshness owner.
- `backend/app/engine/{state,management,score,technology}.py` — current runtime contracts
  and factor implementations.
- `backend/app/casepack/{models,loader,validate}.py` — current policy and preference shapes.
- `backend/packs/riverside_grocery/{policies.yaml,stakeholders.yaml,preferences/policies.yaml}`
  — six ordinal switches and nine archetype preference sets.
- `backend/tests/test_engine_scoring.py` and `backend/seeds/riverside_r3.py` — current
  properties and computed seed pin.

**Verified current facts:**

- `[V]` `PolicyOption.options` is a preserved `list[SnakeKey]`; its order is authoritative
  (`models.py`, `CONTRACTS.md`).
- `[V]` `policy_switch_alignment` currently raises `NotImplementedError` and has no call
  site (`management.py:165-200`).
- `[V]` `TeamState` carries no policy selection or active-decision state (`state.py`).
- `[V]` Riverside policy preferences use
  `defaults_by_archetype.<archetype>.by_decision.<policy>.{ideal_posture,weight}`.
- `[V]` the casepack validator now verifies obligation/policy references but does not
  compute scores.
- `[V]` the traceability row for data freshness names `platform_service.settings`, while
  neither `PlatformService` nor `TeamState` currently exposes such a setting.
- `[V]` the strategic-alignment spec already says cosine; audit finding `1.4-001` is closed.

**Cited from summaries:** none.

**Extraction sufficiency:** covered all load-bearing surfaces. No external platform or
database fact is required: this packet extends repository-native pure data contracts only.

---

## 1. Purpose and scope

The merged 1.4 core is correct for its declared scope, but its policy-preference path was
paused while `PolicyOption.options` ordering was reworked. That contract is now settled and
merged. This packet implements the deferred mechanical path, adds the missing active-policy
discipline factor, updates the seed and decomposition evidence, and assigns data freshness
to the packets that can actually produce it.

**In scope:**

- runtime policy-decision input on `TeamState`;
- ordinal, asymmetric policy-preference alignment;
- information-policy discipline as a Management sub-factor;
- Management decomposition evidence for both new factors;
- Riverside R3 seed policy state and recalibrated, computed pins;
- property and negative tests;
- in-place 1.4 spec/DoD and traceability corrections;
- closure of register F4, E2 and G2's 1.4 accounting obligation.

**Out of scope:**

- changing policy options, defaults, stakeholder preferences or weights in the casepack;
- policy-vs-practice contradiction scoring;
- obligation/event firing (1.5);
- persistence, `instance_id`, round evolution or lock semantics (1.6/2.x);
- creating the Platform data-freshness UI or storage (3.4);
- choosing or simulating a freshness value before those producers exist;
- changing Technology, Organisation, existing Management formulas, BSC formulas, graph
  behavior, cost behavior or any frontend artifact;
- LLM scoring or recommendation.

Named compliant route (`SPEC_PROTOCOL.md §4.1`): add one immutable policy-decision tuple to
the scorer input; resolve it only against casepack policy options and archetype preferences;
emit two pure numeric Management sub-factors plus evidence; update the seed explicitly; and
mark data freshness deferred to its real capture/evolution owners without inventing a value.

---

## 2. Project-specific statements

**Scoring factors touched:**

| Traceability factor | Change |
|---|---|
| Stakeholder alignment | adds the policy-preference dimension as `policy_alignment` |
| Information policy | current team selections become a real scorer input |
| Information-policy discipline | NEW named Management sub-factor: active decisions ÷ authored switches, with the settled floor below |
| Data currency / freshness | no score added; traceability corrected to deferred owners 3.4 + 1.6 |
| Component currency (EOL) | unchanged |

**Casepack keys read:** `policies[].{key,options,default}`;
`stakeholders[].{key,archetype}`;
`preferences/policies.yaml defaults_by_archetype.*.{weight,by_decision.*.{ideal_posture,weight}}`.

**Casepack-identity branching:** none. I1.

**Instance scoping:** N-A in this packet. The pure scorer receives an immutable state
snapshot and performs no query or persistence. The future runtime table that produces these
fields remains governed by 1.6/2.x and must carry `instance_id`.

**Business-language check:** no student-facing copy. Output remains factor keys and numeric
evidence. The UI later maps them through casepack/platform labels.

---

## 3. Settled decisions

1. **Policy alignment is a separate Management sub-factor.** Do not hide it inside the
   existing per-capability rollout `stakeholder_alignment` scalar. The current scalar stays
   byte-for-byte compatible; `policy_alignment` is firm-wide and applies identically to
   every capability. This follows G6: stakeholder preference is Management Quality.

2. **The asymmetric ordinal formula is frozen.** For a policy with `n >= 2` options, team
   index `t`, and stakeholder ideal index `i`:

   ```text
   span = n - 1

   if t == i: alignment = 1.0
   if t <  i: alignment = 1.0 - (i - t) / span
   if t >  i: alignment = 1.0 - 0.5 * (t - i) / span

   alignment = clamp(alignment, 0, 1)
   ```

   `t < i` means the team is more permissive than requested; it pays the full normalized
   distance. `t > i` means the team is stricter than requested; it pays half the normalized
   distance. Thus overshooting always costs less than ignoring by the same number of steps.

3. **Preference aggregation is a weighted arithmetic mean.** For every actual stakeholder
   in `pack.stakeholders`, resolve its archetype row. For every `by_decision` preference in
   that row, compute decision alignment and use:

   ```text
   effective_weight = archetype.weight * by_decision[policy].weight
   policy_alignment = sum(alignment * effective_weight) / sum(effective_weight)
   ```

   Stakeholders/archetypes with no policy row and policies with no stakeholder interest are
   absent from numerator and denominator, not neutral rows. If total weight is zero,
   `policy_alignment = 1.0` and evidence says `preferences: 0`.

4. **One archetype default is applied once per actual stakeholder.** Do not score the
   archetype table directly; the pack's stakeholder population is the roster. Overrides,
   if the loader exposes them for this domain, replace the corresponding archetype decision
   row rather than adding a duplicate. If current models cannot express that verified rule,
   STOP rather than inventing a second preference resolver.

5. **Policy choice is explicit immutable runtime state.** Add NEW frozen dataclass:

   ```python
   @dataclass(frozen=True)
   class PolicyDecisionState:
       policy: str
       selected: str
       actively_decided: bool
   ```

   Add NEW field to `TeamState`:

   ```python
   policy_decisions: tuple[PolicyDecisionState, ...] = ()
   ```

   Interfaces are **FROZEN by this packet**. `policy` and `selected` are machine keys;
   `actively_decided` records whether the team committed a choice, including deliberately
   retaining the default.

6. **Empty runtime policy state resolves to authored defaults.** For every pack policy
   absent from `state.policy_decisions`, use `policy.default` and set
   `actively_decided=False`. This makes the null path deterministic and backward-compatible
   with existing callers, while still charging the discipline factor.

7. **Information-policy discipline is firm-wide and floored.** Let `P` be pack policies
   declaring non-empty options and `D` the subset actively decided:

   ```text
   if P is empty: policy_discipline = 1.0
   else:          policy_discipline = 0.25 + 0.75 * (|D| / |P|)
   ```

   The `0.25` floor makes ignoring the screen costly without zeroing the entire Management
   term and hiding every other lesson. It is a hard-coded v1 calibration constant, named
   `POLICY_DISCIPLINE_FLOOR`, revisited only by 1.7.

8. **Management gains exactly two sub-factors.** The formula becomes:

   ```text
   mgmt(c) = geomean(governance, strategic_alignment, portfolio_discipline,
                     signal_responsiveness, follow_through, stakeholder_alignment,
                     policy_alignment, policy_discipline)
   ```

   Existing six inputs and their formulas do not change.

9. **Invalid score input fails loudly.** Duplicate runtime decisions for one policy,
   unknown policy keys, selected values outside declared options, missing defaults needed
   by the null path, unknown stakeholder archetypes, or preference ideals outside policy
   options raise `ValueError` before a score is returned. Never clamp, skip or guess around a
   broken scoring contract.

10. **Riverside R3 seed represents an attentive team, not an ignored screen.** Add exactly
    one `PolicyDecisionState` for each of Riverside's six policies, with
    `actively_decided=True`. The selected value is the existing authored `default` for each
    policy. This preserves content; it does not invent a new team choice. The new exact Mgmt
    and realised pins are whatever the frozen formulas compute from that seed. Record them
    to six decimals in the closeout DoD and update the original spec §5.7 only after the
    independent computation passes.

11. **Do not tune inputs to recover 0.648.** Tech and Org pins must remain unchanged within
    `0.000001`. The old Mgmt/realised pins become historical baseline values because two
    real Management inputs were previously absent. The builder reports the new computed
    values; it does not change weights, preferences, policy selections or calibration knobs
    to chase the old number.

12. **Data freshness is not a 1.4 input yet.** Amend `design/02` so its row is no longer
    falsely complete: capture/storage belongs to 3.4 Platform; round-to-round freshness
    production belongs to 1.6; scoring consumption returns to a future 1.4 follow-up only
    after both exist. Component EOL currency remains the current `currency` sub-factor and
    must not be relabeled as data freshness. This closes G2 as an explicit, named deferral.

13. **Strategic alignment remains cosine.** `1.4-001`/G1 is already corrected in the living
    spec. No change is authorized.

---

## 4. Open decisions

None. Formula, aggregation, state contract, null paths, calibration handling and ownership
are frozen above. A builder encountering a missing loader surface or contradictory current
model stops; it does not choose an alternative representation.

---

## 5. Design

### 5.1 Pure helpers

Add pure functions in `management.py` (names NEW, signatures FROZEN):

```python
def policy_switch_alignment(pack: Casepack, state: TeamState) -> tuple[float, dict[str, Any]]
def policy_discipline(pack: Casepack, state: TeamState) -> tuple[float, dict[str, Any]]
```

Remove the deferred `*args/**kwargs` hook. Both functions return rounded-at-boundary values
using the existing engine convention; internal arithmetic uses full precision.

`policy_switch_alignment` evidence includes, at minimum:

```python
{
  "preferences": <count>,
  "total_weight": <float>,
  "alignment": <float>,
  "rows": [
    {"stakeholder": <key>, "archetype": <key>, "policy": <key>,
     "selected": <key>, "ideal": <key>, "team_index": <int>,
     "ideal_index": <int>, "direction": "match|too_permissive|stricter",
     "alignment": <float>, "weight": <float>}
  ]
}
```

`policy_discipline` evidence includes `eligible`, `actively_decided`, `floor`, `ratio`, and
the undecided policy keys.

### 5.2 Integration into Management

Compute both firm-wide policy values once in `firm_management`; extend `FirmManagement` with
NEW frozen fields `policy_alignment` and `policy_discipline`. `management()` inserts them
into the sub-factor map for every capability. Do not recompute them per capability.

The decomposition record therefore exposes both under
`sub_factors.management` and their evidence under Management evidence. No prose is emitted.

### 5.3 Null and negative paths

| Case | Required result | Verification |
|---|---|---|
| No pack policies | alignment 1.0; discipline 1.0; empty evidence | unit test |
| Policies, empty runtime tuple | use every authored default; all inactive; discipline 0.25 | unit test |
| Team actively selects the default | alignment same as default; discipline counts it | paired test |
| Stakeholder has no policy preferences | excluded from denominator | unit test |
| No stakeholder has a policy preference | alignment 1.0 with `preferences: 0` | unit test |
| Team is one step too permissive | full normalized penalty | table-driven test |
| Team is one step stricter | half normalized penalty | table-driven test; value greater than prior row |
| Two-option switch at opposite ends | permissive miss 0.0; strict overshoot 0.5 | exact test |
| Duplicate runtime decision | `ValueError` | negative test |
| Unknown policy or selected option | `ValueError` | negative test |
| Missing default needed for absent runtime decision | `ValueError` | negative test |
| Ideal posture not in options | `ValueError` | negative test |

### 5.4 Seed and calibration

Seed remains `backend/seeds/riverside_r3.py`; command remains:

```text
PYTHONPATH=backend python3 -m app.engine.score riverside_r3
```

Required demonstration:

- all six Riverside policy decisions visible in seed input;
- `policy_discipline == 1.0`;
- policy-alignment evidence resolves real stakeholder/archetype rows from the loaded pack;
- Tech and Org remain `0.750008` and `0.507003` within `0.000001`;
- new Mgmt, realised and firm-score values are computed and recorded, never preselected;
- decomposition remains present for all seven capabilities.

### 5.5 Document deltas

Apply in the same commit:

1. `handoffs/1.4-scoring-engine/spec.md`: version/date header; Management formula and table;
   policy formulas/state; revised seed pin; changelog.
2. `handoffs/1.4-scoring-engine/dod.md`: append closeout, do not rewrite historical audit
   evidence.
3. `design/02-traceability-matrix.md`: data freshness status/owners and policy discipline
   row; correct strategic-alignment parenthetical `dot product` → `cosine similarity`.
4. `findings/OPEN-REGISTER.md`: mark F4 and E2 closed by this packet; mark G2 explicitly
   deferred to 3.4 + 1.6, not implemented.
5. `CONTRACTS.md`: add the now-cross-cutting `PolicyDecisionState` runtime snapshot contract,
   including producer ownership (1.6/2.x) and scorer consumer. Version/date update required.

---

## 6. Invariants and falsification checks

| # | Invariant | Falsification check | Expected |
|---|---|---|---|
| C1 | Existing Tech and Org behavior does not change | run old 1.4 tests plus seed; compare six-decimal terms | exact old values |
| C2 | Equal miss distance penalizes permissive more than strict | table test over every `n=2..6`, every valid ideal and symmetric reachable pair | strict-side alignment greater |
| C3 | Exact match is always 1 | property test over all option indices | 1.0 |
| C4 | Alignment always in `[0,1]` | exhaustive table test for `n=2..10` | no breach |
| C5 | Policy order is consumed, not string equality | reverse a test vocabulary without changing strings | score changes as predicted |
| C6 | Active default counts as managed | paired identical selections with active false/true | alignment equal; discipline higher |
| C7 | No silent invalid input | all §5.3 negative cases | every case raises |
| C8 | Existing six Management inputs unchanged | compare pre/post seed evidence excluding two NEW keys | byte-identical |
| C9 | No casepack identity branch | `git ls-files backend/app/engine backend/tests | xargs grep -niE "riverside|grocer|pack_key *=="` excluding seed/test fixture names | zero engine hits |
| C10 | Engine remains pure | original I2 grep plus `grep -rnE "yaml|Path\(|read_text|open\(" backend/app/engine/` | zero product-code hits |
| C11 | Policy scores come from the pack and state | mutate one selected value, then one preference ideal, independently | each changes evidence/score |
| C12 | Ignoring policy is not neutral | Riverside copy with empty policy decisions | discipline 0.25 and Mgmt lower than attentive seed |
| C13 | No raw-fit scoring regression | retain/pass the 1.3 rework guard proving `harvested_raw_fit` is unconsumed | pass |

---

## 7. Pre-Flight Verification Register

Builder runs every row before writing code. Any mismatch is FAIL → STOP.

| # | Claim | Tag | Check | Expected |
|---|---|---|---|---|
| 1 | Required contract and validator reworks are merged | `[V]` | `git log --oneline --all -- CONTRACTS.md backend/app/casepack/validate.py | head -20` | policy ordinal contract and E15–E28 present on branch base |
| 2 | Riverside validates clean | `[V]` | `cd backend && PYTHONPATH=. bin/validate_casepack packs/riverside_grocery` | 0 errors, 0 warnings |
| 3 | Deferred hook still raises and has no call site | `[V]` | `git grep -n "policy_switch_alignment" -- backend/app backend/tests backend/seeds` | definition/comments only; no scoring call |
| 4 | TeamState has no policy state yet | `[V]` | `git grep -n "policy_decisions\|PolicyDecisionState" -- backend/app/engine backend/seeds backend/tests` | zero |
| 5 | Six Riverside policies declare ordered options/defaults | `[V]` | `cd backend && PYTHONPATH=. python3 tests/check_policy_options.py` | all checks pass; six switches |
| 6 | Policy preferences use verified by-decision shape | `[V]` | `grep -n "ideal_posture\|by_decision" backend/packs/riverside_grocery/preferences/policies.yaml | head` | both keys present |
| 7 | Current seed pins and properties are green | `[V]` | `cd backend && python3 -m pytest -q tests/test_engine_scoring.py` | 9 passed before changes |
| 8 | Data-freshness producer is absent | `[V]` | `git grep -n "freshness\|platform_service.settings" -- backend/app backend/packs backend/seeds` | zero functional producer hits |
| 9 | 1.3 raw-fit guard is available | `[A]` | `git grep -n "harvested_raw_fit" -- backend/tests` | a regression test exists; if 1.3 rework has not merged, STOP and rebase after it |
| 10 | Current main/branch base is stable | `[V]` | `git rev-parse main; git merge-base main HEAD` | builder reports exact SHAs; same commit before code |

---

## 8. Build steps

### Step 1 — Runtime contract and resolver

Add `PolicyDecisionState`, the `TeamState` field, strict resolution/null handling and pure
policy helper tests.

**Verify:** §5.3 table and C2–C7 pass; existing 1.4 tests remain green.

### Step 2 — Management integration and evidence

Add firm-wide policy alignment/discipline fields, integrate exactly two new Management
sub-factors, and emit the required evidence.

**Verify:** C1, C8, C11, C12; every capability record includes both keys.

### Step 3 — Seed and computed pins

Add six explicit attentive default selections to Riverside R3. Run the real loader + scorer,
record new pins and do not tune them.

**Verify:** §5.4 demonstration; Tech/Org unchanged; discipline 1.0; seven decompositions.

### Step 4 — Living documents and full regression

Apply §5.5 deltas, run validator, all tests, invariants and the 1.3 raw-fit guard.

**Verify:** fixture matrix, full pytest, Riverside 0/0, `git diff --check`, document greps,
and a clean merge simulation against then-current main.

---

## 9. Definition of Done

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–10 reported before code | | |
| Step 1 verify — state contract, null/negative paths, C2–C7 | | |
| Step 2 verify — two Management factors and evidence, C1/C8/C11/C12 | | |
| Step 3 verify — six policy decisions and computed new pins | | |
| Step 4 verify — documents and full regression | | |
| C1–C13 | | |
| Existing Technology and Organisation pins unchanged | | |
| Existing six Management inputs unchanged | | |
| Every capability decomposition carries both policy factors | | |
| Riverside validator clean in text and JSON modes | | |
| Complete 1.2 fixture matrix green | | |
| Complete pytest suite green | | |
| 1.3 raw-fit isolation guard green | | |
| `CONTRACTS.md`, original 1.4 spec, `design/02`, register updated in place | | |
| No casepack identity branching | | |
| Engine purity maintained | | |
| Seed result computed from real pack/state and recorded | | |
| Ladder rung 1 — contracts inspected | | |
| Ladder rung 2 — compile/tests/validator | | |
| Ladder rung 3 — seed/scorer runtime | | |
| Ladder rungs 3 auth/instance, 4 browser, 5 UX | | **N-A — pure headless scorer; no DB/session/UI** |
| Independent audit | | required before merge |
| Worktree clean; nothing pushed/merged/deployed/migrated | | |

Status values: **PASS · FAIL · DEVIATION · N-A**. N-A requires the reason above.

---

## 10. Verification script

No browser playthrough: this packet has no user surface. The independent auditor runs:

```text
cd backend
python3 -m pytest -q
PYTHONPATH=. python3 tests/check_fixture_matrix.py
PYTHONPATH=. bin/validate_casepack packs/riverside_grocery
PYTHONPATH=. python3 -m app.seed.demo --scenario riverside_r3
PYTHONPATH=. python3 -m app.engine.score riverside_r3
```

The auditor independently reconstructs at least one permissive miss and one strict
overshoot from option indexes, verifies the asymmetric arithmetic by hand, mutates one pack
ideal and one team selection separately, checks the new seed pins, and re-runs C1–C13.

