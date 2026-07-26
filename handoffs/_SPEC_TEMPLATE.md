# <MODULE-ID> — <Module Name> · Build Spec

**Authored under** `SPEC_PROTOCOL.md` v1.1
**Author:** <agent/human id> · **Date:** YYYY-MM-DD
**Phase:** <n> · **Depends on:** <module ids, or "none">
**Reference mockup:** `mockups/<file>.html` *(required if acceptance is visual)*

---

## 0. Spec Basis

**Read in full:**
- `path/to/file` — <what it established>
- …

**Cited from summary or prose:** <target: none. List any, each downgraded to `[A]` with a
pre-flight row.>

**Extraction sufficiency:** <one of — "covered all load-bearing surfaces" /
"insufficient for X — targeted extraction requested" / "deferred to pre-flight rows N–M">

---

## 1. Purpose and scope

<Two or three sentences. What this module does and why it exists.>

**In scope:**
- …

**Out of scope** *(enumerate adjacent things a builder might helpfully extend)*:
- …

---

## 2. Project-specific statements *(SPEC_PROTOCOL §9)*

**Scoring factors touched** — keyed to `design/02-traceability-matrix.md`:

| Factor | This module | Direction |
|---|---|---|
| e.g. Training coverage | purchase form training tier | captures |
| e.g. Coverage | capability slot display | displays |

*Every input must feed a factor. Every displayed factor must read from a real source.
Anything that does neither is justified here or cut.*

**Casepack keys read:** `<list>`
**Casepack-identity branching:** none. Falsification check in §6.

**Instance scoping:** <every new table and every new query names its `instance_id`
handling. "N/A — no state" is an acceptable answer, stated explicitly.>

**Business-language check:** <confirm student-facing strings carry no engine vocabulary.
List any borderline terms and their resolution.>

---

## 3. Settled decisions

Numbered, so the builder can cite them.

1. …
2. …

## 4. Open decisions

Anything a builder might otherwise decide silently. Each with criteria and a reporting
obligation. **If this section is empty, say so and explain why nothing is open.**

| # | Question | Decision criteria | Reporting obligation |
|---|---|---|---|
| O1 | … | … | Report choice + rationale in `dod.md` |

---

## 5. Design

<Data model changes · API surface · component structure · state · screen layout.
Reference the mockup. Frozen interfaces declared explicitly as FROZEN or VERSIONED.>

### 5.x Student-facing copy

Written out verbatim, not described:

```
Empty state:   "No applications serve this activity yet."
Warning:       "You added capacity but funded no training."
Button:        "Add to plan"
```

### 5.z Seed — real demo data *(GOVERNANCE §4.9 — REQUIRED)*

```
seed        what real content this packet loads, and where it lives
command     the ONE command that produces it from a clean state
demonstrate what is COMPUTED from that seed — not asserted alongside it
```

A stub proves rendering. A seed proves the path from data to display runs.
`TODO` in shipped content is a defect; anything unauthorable is marked
`TODO: calibrate` **and listed in the report**.

### 5.y Null paths and negative cases

| Case | Expected behaviour | Verify step |
|---|---|---|
| No strategy declared yet | … | … |
| Capability with zero required roles | … | … |
| Round already locked | … | … |
| Casepack defines no events this round | … | … |

---

## 6. Invariants and their falsification checks

Every *must / never / only / zero / all* ships with the check that would break it.

| Invariant | Falsification check | Expected |
|---|---|---|
| No engine branch on casepack identity | `grep -rniE "riverside\|grocer" engine/` | zero hits |
| … | … | … |

---

## 7. Pre-Flight Verification Register

**Builder runs every row before writing code and reports each one.**
A FAIL means STOP and report — not adapt.

| # | Claim | Tag | Check (executable as written) | Expected result |
|---|---|---|---|---|
| 1 | … | `[V]` | `command` | … |
| 2 | … | `[A]` | `command` | … |

---

## 8. Build phases

Each with its own verify step. A step with no verify is not in scope.

### Phase 1 — <name>
- …
- **Verify:** <executable, or browser action with expected visible state>

### Phase 2 — <name>
- …
- **Verify:** …

---

## 9. Definition of Done

Derived mechanically from the body. Builder fills Status and Evidence.
**This filled table is the builder's session report.**

| Item | Status | Evidence |
|---|---|---|
| Pre-flight row 1 | | |
| Pre-flight row 2 | | |
| Phase 1 verify | | |
| Phase 2 verify | | |
| Invariant 1 falsification check | | |
| Open decision O1 resolved + reported | | |
| Ladder rung 1 — contract verification | | |
| Ladder rung 2 — build/tests/validator | | |
| Ladder rung 3 — runtime + auth canary | | |
| Ladder rung 4 — zero console errors | | |
| Ladder rung 5 — UX/navigation + viewports | | |
| Playthrough Script passes end to end | | |
| **Seed command reproduces the demo state from a clean database** | | |
| **Evidence shows results COMPUTED from the seed** | | |
| Screenshots attached, each with the command that produced its data | | |
| Instance-isolation canary *(if state-touching)* | | |
| Design-system canary — no hardcoded colours/fonts | | |
| `CONTRACTS.md` updated *(if cross-cutting field changed)* | | |
| Document deltas applied in-place with version bump | | |

Status values: **PASS · FAIL · DEVIATION · N-A** (N-A requires a stated reason).

---

## 10. Playthrough Script

See `playthrough.md` in this folder. Authored with this spec, before any code.
