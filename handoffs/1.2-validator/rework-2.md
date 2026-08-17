# 1.2 — Second Rework Instruction

**Drafted by:** the AUTHOR · **Date:** 2026-08-17
**Branch to cut:** `build/1.2-rework-2`, from `main` @ `f5125f4`
**Scope:** the validator. Six items, all specified, none requiring design.

> **`rework.md` is the FIRST rework** — completed, audited and merged. Do not edit it and
> do not work from it. This document is yours.

---

## 1. Why this exists, and why it is the critical path

1.1's rework-2 landed six schema additions on 2026-08-17. **The gate it was meant to lift
did not lift**, because the validator does not know the new fields exist.

Proved by experiment, and independently verified: a scratch Riverside with
`metric_kind: presence` declared on both thresholdless rules validates **byte-identically to
the untouched pack**. `validate.py` never reads `metric_kind`; `E12`, `E20` and `_raisable`
all decide from thresholds alone. `E02` is the same story — `Lens.owned` is built from
`pack.catalog` only, while `filled_roles` two lines above it unions `pack.platform.services`.

```
1.1 rework-2   the schema fields exist                      ✅ merged f5125f4
1.2 rework-2   THIS PACKET — teach the validator the fields  ← nothing moves without it
1.3            declare kinds, author ownership, close CG-1..CG-6
```

**Eleven of Riverside's twenty errors, and 1.3's `I6`, `I8` and `I11`, are unreachable until
this packet lands.** It is the only thing standing between the schema and CG-1 closing.

---

## 2. The rule that governs every change

> **Every change here must move the Riverside error profile in a way you predicted before
> you made it.**

Today's profile, on merged `main`:

```
E07 ×8 · E20 ×6 · E12 ×2 · E21 ×2 · E02 ×1 · E14 ×1 · W02 · W04 · W05      exit 1
```

**This profile must not change**, because `backend/packs/` is not yours and Riverside still
declares no `metric_kind` and no ownership. Under the default (`threshold`), both rules stay
illegal, so `E12 ×2` and `E20 ×6` are still correct answers.

**What must change is what the validator says about a pack that DOES declare them.** That is
what §4's paired fixtures prove, and it is the whole packet.

The same prohibitions as last time apply, for the same reasons:

- **Do not touch `backend/packs/`.** Content is 1.3's. `git diff` must be empty.
- **Do not fix Riverside's content** to make anything pass.
- **Do not touch `models.py` or `loader.py`** — except item 3.6, which is one line and is
  explicitly scoped below.

---

## 3. The six items

### 3.1 `E12` exempts presence rules

```
ERROR when   metric_kind == "threshold"  AND  warn_above is None  AND  critical_above is None
silent when  metric_kind == "presence"   (carrying no threshold is that kind's correct shape)
```

A presence rule carrying a threshold is already rejected by the model, so you will not see
one — but if you can construct one, it must not reach `E12` as a false negative.

### 3.2 `E20` widens to include presence rules

The predicate becomes *"a capability with no watch rule **that can raise a signal**"*, where
a rule can raise one if it is `presence`, **or** `threshold` with at least one threshold set.

Today `E20` counts a rule as covering a capability only if it carries a threshold. A correctly
authored presence rule must count as coverage, or 1.3 closes CG-1 and `E20` still fires.

### 3.3 `_raisable` consults `metric_kind` — `1.1-r2-006`

`validate.py:727-736` decides whether an event's required severity is reachable, purely from
thresholds. It is the third place that must learn about presence rules, and **it was missing
from every handoff list until the rework audit found it.**

Per 1.5 §3 decision 10, **a presence rule raises at `critical`, never at `warning`.** So:

```
presence rule   →  "critical" reachable · "warning" NOT reachable
threshold rule  →  reachable iff the matching threshold field is set (unchanged)
```

**This is what resolves `E21 ×2` on Riverside** once 1.3 declares the kinds: the two dead
cards require `wh_rollout_01` at `critical`, which a presence rule can reach.

### 3.4 `Lens.owned` unions platform services — `1.1 rework-2 R2`

```python
self.owned  ←  pack.catalog  ∪  pack.platform.services      # entities, as filled_roles already does for roles
```

`E02` and `E23` consult `Lens.owned`. Until this lands, `PlatformService.owns_entities` is
inert and no pack can satisfy an entity requirement through a platform service. **`E02 ×1`
on Riverside will still fire when you finish** — 1.3 must then declare
`central_sign_on.owns_entities`. Adding the union does not clear it; it makes clearing it
*possible*.

### 3.5 `W08` — the per-strategy draw check

From 1.5 §5.2a, at `N = 6` (its O4):

```
for each strategy S:
    draws(S) = events whose strategy_affinity includes S, or is empty
    WARN if len(draws(S)) < 6
```

`WARN`, not `ERROR` — a thin deck is authorable content, not a broken pack, and 1.7's
calibration is where a deck that starves a strategy actually fails. Riverside will raise it
**four times** (`cost_leadership` 3, `customer_supplier_intimacy` 2, `differentiation` 1,
`focus_strategy` 1), which is `CG-2` visible for the first time.

**Note:** this changes the *warning* count, not the error count. §2's error profile still
holds; state the new warning total in your report.

### 3.6 `1.1-r2-001` — one line in `loader.py`, explicitly in scope

An empty or comment-only `obligation_rules.yaml` makes the **whole pack** `E00`, which is the
opposite of what the loader's own comment says the optional section does.

**This is 1.1's file, and I am scoping it here deliberately.** The reasons, so the auditor can
rule on whether that was right: it is one line; it is fully specified by the finding; it will
bite 1.3 the moment it creates the file before filling it; and spinning a third 1.1 packet for
a single line is waste. **Touch nothing else in `loader.py`.** If the fix turns out to be more
than a line, **stop and report** rather than growing the scope.

---

## 4. Fixtures — paired, and this is how the packet is proved

Every item above changes behaviour on packs that do not exist yet. A fixture suite that only
covers today's content proves nothing about the change.

**For each of 3.1, 3.2, 3.3, 3.4, add a PAIR:**

```
the illegal / uncovered / unreachable shape   →  the code still fires
the newly legal shape                         →  the code is now SILENT
```

Concretely, at minimum:

| Fixture | Shape | Expected |
|---|---|---|
| `broken_E12` | threshold rule, no thresholds | `E12` fires (unchanged) |
| `ok_presence_rule` | presence rule, no thresholds | **`E12` silent, `E20` silent** |
| `broken_E20_mute` | capability watched only by a thresholdless threshold-rule | `E20` fires (unchanged) |
| `broken_E21` | event needing `critical` from a rule that cannot reach it | `E21` fires (unchanged) |
| `ok_presence_arms_event` | event needing `critical` from a **presence** rule | **`E21` silent** |
| `broken_E02` | entity required, nothing owns it | `E02` fires (unchanged) |
| `ok_service_owns_entity` | entity owned by a **platform service** | **`E02` silent** |
| `broken_W08` | a strategy drawn by < 6 events | `W08` fires |
| `ok_obligations_empty` | empty `obligation_rules.yaml` | **loads clean, no `E00`** (3.6) |

`GOVERNANCE §4.9` applies: these are real, coherent, minimally-different packs, not stubs.
Derive them from `minimal_valid` — it is a working two-capability company and the cheapest
honest starting point.

**`check_fixture_matrix.py` must assert both halves of every pair.** A suite that only proves
errors still fire has not tested this packet at all.

---

## 5. Definition of Done

| Item | Evidence required |
|---|---|
| 3.1–3.5 implemented | code excerpt each, plus the paired fixtures firing and falling silent |
| 3.6, one line, nothing else in `loader.py` | the diff |
| **Riverside's ERROR profile unchanged** — §2 | before/after, pasted |
| **Riverside's warning total, with `W08` ×4** | pasted, and the four counts named |
| `check_fixture_matrix.py` green, asserting both halves of each pair | pasted, exit 0 |
| `backend/packs/` byte-identical | `git diff f5125f4..HEAD -- backend/packs/` → empty |
| `models.py` untouched | same → empty |
| I1 set-equality still holds with `W08` added | I1 compares implemented codes against **spec-named** codes, so `W08` must be named in 1.2's spec too — see below |
| I2–I5 re-run | pasted |
| **The proof this packet exists for** | a scratch Riverside (NOT in `backend/packs/`) with `metric_kind: presence` on both rules: **`E12 ×2` and `E21 ×2` must vanish and `E20` must fall from 6 to 5.** Paste it. This is the experiment that failed after 1.1's rework, and passing it is what lifts 1.3's gate |

> **`W08` and the spec.** `I1` is set equality between implemented codes and codes the spec
> names. Adding `W08` to the build without adding it to `handoffs/1.2-validator/spec.md` §5.3
> **breaks `I1`**. You are authorised to add exactly that one line to §5.3, and nothing else
> in the spec — it is the code list `SPEC_PROTOCOL §3` requires to be versioned, and the
> author has already ruled `W08` in (1.5 §10 item 3). Note the edit in your report.

---

## 6. When you are done

Fill `handoffs/1.2-validator/dod-rework-2.md` — a new file; do not overwrite `dod.md`.
Push `build/1.2-rework-2` and verify with `git ls-remote` against your local HEAD.
**Do not merge.** A fresh auditor takes it from there.

**Declare every substitution.** `1.2-004` exists on this project because a correct
substitution was made silently and a vacuous check survived to audit.

Stop and report on anything this document does not settle.
