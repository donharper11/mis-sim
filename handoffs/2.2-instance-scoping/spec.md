# 2.2 — Instance Scoping & Isolation Canary · Build Spec

**Authored under** `SPEC_PROTOCOL.md` v1.2 · **Author:** Claude · **Date:** 2026-07-26
**Phase:** 2 · **Depends on:** 2.1, 1.6 · **Blocks:** every later packet that reads state

> 1.6 created runtime tables with `instance_id` as an unconstrained integer because
> `simulation_instance` did not yet exist. This packet closes the loop: adds the foreign
> keys, and builds the standing canary that proves two cohorts cannot see each other.

---

## 0. Spec Basis

**Read in full:**
- `handoffs/1.6-round-runner/spec.md` §5.1 (the runtime table list) and pre-flight row 4
  (which explicitly deferred the FK to this packet)
- `handoffs/2.1-hierarchy/spec.md` §5.1 (`simulation_instance`)
- `BECSR/course-section-management.md` — the retrofit and the standing note
  *"No data should ever leak between sections"*
- `GOVERNANCE.md` §4.5, §5 · `CONTRACTS.md` `instance_id`

**Extraction sufficiency:** covered.

---

## 1. Purpose and scope

**In scope:** FK constraints from every runtime table's `instance_id` to
`simulation_instance`; a repository-layer guard making an unscoped read impossible rather
than merely discouraged; the isolation canary as a runnable test.

**Out of scope:**
- Creating any runtime table — 1.6 owns those
- Changing any scoring or round logic
- The hierarchy itself — 2.1
- Any UI

---

## 2. Project-specific statements

**Scoring factors touched:** none. This packet protects all of them.
**Casepack keys read:** none.
**Instance scoping:** this *is* the packet. Every runtime table gains an FK; every read
path gains a guard.
**Business-language check:** the canary's failure message is for developers.

---

## 3. Settled decisions

1. **Guard at the repository layer, not by convention.** A rule that says "always filter
   by `instance_id`" is a rule that will be broken. A base repository that *requires* the
   scope makes the omission a type error rather than a leak.
2. **FKs are `ON DELETE RESTRICT`.** Deleting an instance with live state must fail loudly,
   never cascade a cohort's game away.
3. **The canary is a test, not a script.** It runs in the suite and in the pre-merge gate
   for every state-touching packet thereafter.
4. **`instance_id` stays non-nullable.** It was created non-null in 1.6; this adds the FK,
   it does not relax anything.

---

## 4. Named compliant route *(SPEC_PROTOCOL §4.1)*

```
1  Alembic revision: for each runtime table in 1.6 §5.1,
   ALTER TABLE … ADD CONSTRAINT fk_<t>_instance
   FOREIGN KEY (instance_id) REFERENCES simulation_instance(id) ON DELETE RESTRICT

2  backend/app/repo/base.py:
       class ScopedRepo:
           def __init__(self, session, instance_id: int):   # required, no default
               ...
           def select(self, model):
               return sa.select(model).where(model.instance_id == self.instance_id)

3  Every runtime read goes through ScopedRepo.select().
   I2's grep proves no bare select() on a runtime model survives.
```

I1 is satisfied by step 1, I2 by steps 2–3, I3 by the canary in §5.3. No step conflicts
with another.

---

## 5. Design

### 5.1 Foreign keys

One migration, one `ADD CONSTRAINT` per runtime table named in 1.6 §5.1:
`team_state · arch_node · arch_edge · deployment_org_state · platform_service · org_unit ·
it_staff · in_flight · decision_line · signal · debt_item · tco_forecast · round_result`.

If 1.6 shipped a table not on that list, **STOP and report** — an unscoped runtime table is
the exact defect this packet exists to prevent, and silently adding it to the list hides
that 1.6's spec was incomplete.

### 5.2 The repository guard

`ScopedRepo` takes `instance_id` as a **required constructor argument** and exposes
`select()`, `get()`, `add()`. Every runtime read and write goes through it. A caller that
wants an unscoped query must reach past the repo layer, which the grep in I2 catches.

### 5.3 The isolation canary

```
Given  section A running pack P1, section B running pack P2 (2.1's fixture)
       each with a team, each having locked and advanced one round
Then   for every runtime table:
         count(rows visible to A's instance) == count(rows A created)
         count(rows visible to B's instance) == count(rows B created)
         A's ScopedRepo returns zero rows created by B, and vice versa
And    deleting A's instance while state exists raises IntegrityError, not a cascade
```

Lives at `backend/tests/test_instance_isolation.py` and is referenced by
`QUALITY_PROTOCOL.md §5`'s pre-merge gate.

---

## 6. Invariants

| # | Invariant | Check | Expected |
|---|---|---|---|
| I1 | Every runtime table has an FK on `instance_id` | `psql -c "select conrelid::regclass, conname from pg_constraint where confrelid = 'simulation_instance'::regclass"` | one row per table in 1.6 §5.1 |
| I2 | No bare select on a runtime model | `grep -rnE "select\((TeamState\|ArchNode\|ArchEdge\|DecisionLine\|Signal\|RoundResult\|DebtItem\|TcoForecast\|PlatformService\|OrgUnit\|ItStaff\|InFlight\|DeploymentOrgState)\)" backend/app \| grep -v "repo/base.py"` | zero |
| I3 | Canary passes | `pytest backend/tests/test_instance_isolation.py -q` | passed |
| I4 | FKs are RESTRICT, not CASCADE | `psql -c "select conname, confdeltype from pg_constraint where confrelid='simulation_instance'::regclass"` | all `r` |
| I5 | `instance_id` still non-nullable everywhere | `psql -c "select table_name from information_schema.columns where column_name='instance_id' and is_nullable='YES'"` | zero rows |
| I6 | Migration reversible | `alembic upgrade head && alembic downgrade -1 && alembic upgrade head` | exits 0 |

---

## 7. Pre-Flight Verification Register

| # | Claim | Tag | Check | Expected |
|---|---|---|---|---|
| 1 | 2.1 merged; `simulation_instance` exists | `[V]` | `psql -c "\d simulation_instance"` | table present |
| 2 | 1.6 merged; runtime tables exist with non-null `instance_id` | `[V]` | `psql -c "select table_name, is_nullable from information_schema.columns where column_name='instance_id'"` | all `NO` |
| 3 | The runtime table set matches 1.6 §5.1 exactly | `[V]` | compare the query in row 2 against 1.6 §5.1's list | identical. **A difference is a STOP** |
| 4 | **Nothing out of scope reads runtime tables directly** *(§4.2)* | `[V]` | `grep -rn "arch_node\|round_result\|decision_line" backend/app --include=*.py \| grep -v "app/round/\|app/repo/\|app/engine/"` | zero — proves the "no changes outside repo/round" claim |
| 5 | 2.1's two-section fixture exists | `[V]` | `grep -rn "two_section" backend/tests/` | fixture present |
| 6 | No FK on `instance_id` yet | `[V]` | the query in I1 | zero rows |

---

## 8. Build steps

1. **FK migration.** *Verify:* I1, I4, I5, I6.
2. **`ScopedRepo` + refactor every runtime read through it.** *Verify:* I2; the existing
   1.6 six-round integration run still passes unchanged.
3. **Isolation canary.** *Verify:* I3, including the delete-refusal assertion.
4. **Wire the canary into the pre-merge gate.** *Verify:* `QUALITY_PROTOCOL.md §5`'s
   instance-isolation line now names the test path.

---

## 9. Definition of Done

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–6, esp. row 3 | | |
| Steps 1–4 verified | | |
| I1–I6 | | |
| 1.6's six-round run still passes after the refactor | | |
| Canary path referenced in `QUALITY_PROTOCOL.md §5` | | |
| **Instance-isolation canary** | | **PASS required — this packet is where it becomes real** |
| Auth / browser canaries | | **N-A** |
