# <MODULE-ID> — Playthrough Script

**Authored by:** <spec author> · **Date:** YYYY-MM-DD · **Before any code existed:** yes
**Spec:** `spec.md` in this folder
**Executed by:** AUDITOR, in a real browser, with a real session.

---

## Rules *(from `QUALITY_PROTOCOL.md §3`)*

1. Written in **student language** — what a person does, not what a test asserts
2. **Every step has an `EXPECT`.** A step without one is not a test
3. The **negligent path is included deliberately** — that is where the teaching lives
   and where the engine is most likely wrong
4. Zero console errors required to pass
5. Screenshot every `EXPECT` that concerns how a screen reads

---

## Setup

```
Casepack:    riverside_grocery v<n>
Section:     <section> · Instance: <id>
Team:        <team> · Round: <n>
Persona:     student · Strategy declared: <strategy>
Prior state: <what must already be true — prior rounds run, estate as inherited, etc.>
```

---

## Part A — the competent path

| # | Action | EXPECT | Shot |
|---|---|---|---|
| A1 | <what the student clicks or types> | <what they should see> | ☐ |
| A2 | | | ☐ |
| A3 | | | ☐ |

---

## Part B — the negligent path *(required)*

Deliberately do the wrong thing. The sim must **allow it**, warn appropriately, and
produce a correct causal trace later.

| # | Action | EXPECT | Shot |
|---|---|---|---|
| B1 | Leave the business sponsor as "none" | Form still submits — **no blocking validation** | ☐ |
| B2 | Set training to "none" | Accepted, cost stays $0 | ☐ |
| B3 | Open Review & Lock | Warning: "<verbatim copy from spec §5.x>" | ☐ |
| B4 | Lock the round anyway | Lock succeeds — the warning does not block | ☐ |
| B5 | Advance the round; open Debrief | Causal trace names **Organisation** as the throttling factor, with the trained-count stated | ☐ |

---

## Part C — null paths and negative cases

Drawn from spec §5.y. One row per case.

| # | Case | Action | EXPECT | Shot |
|---|---|---|---|---|
| C1 | No strategy declared | <action> | <expected> | ☐ |
| C2 | Round already locked | <action> | Inputs disabled; LockedBanner visible | ☐ |
| C3 | | | | ☐ |

---

## Part D — states and viewports

| # | Check | EXPECT | Shot |
|---|---|---|---|
| D1 | Loading state | Skeleton or spinner, no layout jump | ☐ |
| D2 | Empty state | Copy per spec §5.x, with a clear next action | ☐ |
| D3 | Blocked state | Reason stated in business language | ☐ |
| D4 | Viewport 1440 | No overlap, no clipping | ☐ |
| D5 | Viewport 1280 | No overlap, no clipping | ☐ |
| D6 | Viewport 1024 | No overlap, no clipping | ☐ |

---

## Part E — standing checks

| # | Check | EXPECT |
|---|---|---|
| E1 | Browser console across the whole run | **zero** errors |
| E2 | Network panel | zero failed requests |
| E3 | Any user-facing technical error text | none |
| E4 | Engine vocabulary on screen (`capability_key`, `instance_id`, "articulation point", raw enum values) | none |
| E5 | Auth canary — login + one authenticated call, same host pair | passes |
| E6 | Instance isolation — second section on a second casepack sees none of this data | passes |

---

## Result

```
Run date:      Auditor:
Steps passed:      /        Console errors:
Findings filed:  findings/<MODULE-ID>-YYYY-MM-DD.md
Verdict:  PASS / FAIL
```

A single blocking finding = FAIL. Return to a builder with the findings file.
