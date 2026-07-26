# 2.3 — Round Scheduling, Auto-Lock, Auto-Advance · Build Spec

**Authored under** `SPEC_PROTOCOL.md` v1.2 · **Author:** Claude · **Date:** 2026-07-26
**Phase:** 2 · **Depends on:** 2.1, 1.6 · **Blocks:** 5.3, and running a real cohort

> 1.6 exposes `lock()` and `advance()`. This decides **when** they fire, so a section can
> run asynchronously across a semester without the instructor sitting on the clock.

---

## 0. Spec Basis

**Read in full:**
- `BECSR/async-round-deadlines.md` (VM `.5`) — the whole document: the four added columns,
  the `settings` keys, the instructor round-schedule table, the Set Schedule modal, and
  the bulk cascade
- `handoffs/1.6-round-runner/spec.md` §5, §8 phase 6 (the lock/advance state machine and
  its O3 decision that the engine runs at advance, not at lock)
- `handoffs/2.1-hierarchy/spec.md` §5.1 (`simulation_instance.settings`)

**Extraction sufficiency:** covered. BECSR's implementation is Django; read for semantics,
not code.

---

## 1. Purpose and scope

**In scope:** a `round_schedule` row per (instance, round) with start, deadline,
auto-advance flag, lock state and lock reason; the scheduler that locks at deadline and
optionally advances after a grace period; bulk cascade scheduling; the instructor-facing
service methods 5.3 will call.

**Out of scope:**
- `lock()` / `advance()` themselves — 1.6 owns the mechanics; this only decides timing
- Any scoring or resolution logic
- The instructor UI — 5.3
- Notifications or email
- Student-facing countdown rendering — 3.1 (this exposes the deadline; the shell renders it)

---

## 2. Project-specific statements

**Scoring factors touched:** none directly. It fixes `decision.locked_round`, which
`signal responsiveness` depends on (`design/02` §C) — a wrong lock time silently corrupts
that factor.
**Casepack keys read:** `pack.rounds` for the default `total_rounds`.
**Instance scoping:** `round_schedule` carries `instance_id`, non-null, FK per 2.2.
**Business-language check:** `lock_reason` values are stored as keys and rendered from
labels; a student sees *"This round closed at the deadline"*, never `deadline_expired`.

---

## 3. Settled decisions

1. **BECSR's column set, adopted:** `deadline`, `auto_advance`, `decisions_locked`,
   `lock_reason`.
2. **`lock_reason` enum:** `deadline_expired · instructor_locked · round_advanced`.
3. **`settings` keys on the instance,** as BECSR: `default_round_duration_hours`,
   `auto_advance_on_deadline`, `grace_period_minutes`, `lock_warning_minutes`.
4. **Lock and advance are separate**, per 1.6 O3. Deadline locks; advance is a second
   action, automatic only if `auto_advance` is set.
5. **Scheduling is per instance**, so two sections of one course run independently.
6. **The scheduler is idempotent.** Running it twice over the same deadline locks once.

---

## 4. Named compliant route *(SPEC_PROTOCOL §4.1)*

```
1  Migration: round_schedule(id, instance_id FK NOT NULL, round_number,
       start_at, deadline, auto_advance BOOL, decisions_locked BOOL,
       lock_reason VARCHAR NULL, UNIQUE(instance_id, round_number))

2  scheduler.tick(now: datetime) — a pure-ish service taking `now` as an ARGUMENT,
       never reading the clock itself. For each open schedule row where
       deadline <= now and not decisions_locked:
           call 1.6 lock(instance, round, reason="deadline_expired")
       For each locked row where auto_advance and
       deadline + grace <= now and round not yet advanced:
           call 1.6 advance(instance, round)

3  A thin entrypoint (management command or APScheduler job) passes datetime.now()
       into tick(). That entrypoint is the ONLY clock reader.
```

`now` as an argument is what makes I3 (determinism, testability) satisfiable at the same
time as the scheduler doing real time-based work — the two would otherwise conflict.

---

## 5. Design

### 5.1 Model

```
round_schedule   id · instance_id FK NOT NULL · round_number
                 start_at · deadline · auto_advance
                 decisions_locked · lock_reason · locked_at · advanced_at
                 UNIQUE(instance_id, round_number)
```

### 5.2 Service surface for 5.3

```
set_schedule(instance, round, start_at, deadline, auto_advance)
bulk_schedule(instance, first_start, duration_hours, auto_advance)
      cascades: round N+1 starts at round N's deadline + grace
lock_now(instance, round, reason="instructor_locked")
unlock(instance, round)          instructor only; invalidates the RoundResult per 1.6 O1
advance_now(instance, round)
status(instance) -> per-round state for the schedule table
```

### 5.3 Student-visible effects

The shell (3.1) reads `deadline` and `decisions_locked` to render the countdown and the
locked banner. This packet exposes them; it renders nothing.

### 5.4 Null paths and negative cases

| Case | Expected | Verify |
|---|---|---|
| No schedule set for a round | Round is open indefinitely. No auto-lock. Not an error | tick() over an unscheduled instance is a no-op |
| Deadline in the past when set | Locks on the next tick. Allowed — instructors backfill | set a past deadline, tick, assert locked |
| `auto_advance` on, but the round is already advanced | No-op, not a second advance | tick twice, assert one `advanced_at` |
| Instructor locks before the deadline | `lock_reason = instructor_locked`; deadline no longer fires | assert reason not overwritten |
| Unlock after advance | Refused — the result exists. 1.6 O1 governs | assert 409 |
| Bulk schedule over already-completed rounds | Skips them, reports which | assert skipped list |
| Two ticks in the same second | Idempotent | I4 |

---

## 6. Invariants

| # | Invariant | Check | Expected |
|---|---|---|---|
| I1 | `round_schedule.instance_id` non-null with FK | `psql -c "\d round_schedule"` | not null, FK present |
| I2 | The scheduler never reads the clock | `grep -rnE "datetime\.now\|utcnow\|time\.time" backend/app/scheduling/ \| grep -v entrypoint` | zero |
| I3 | Deterministic given `now` | run `tick(fixed_now)` 50× on one fixture, hash state | one hash |
| I4 | Idempotent | `tick(now); tick(now)` → one lock, one advance | assert counts |
| I5 | No engine or scoring logic here | `grep -rnE "realised\|geomean\|tech\|org_readiness" backend/app/scheduling/` | zero |
| I6 | `lock_reason` never surfaces raw | `grep -rn "deadline_expired" backend/app --include=*.py \| grep -v "scheduling/\|constants"` | zero |
| I7 | Migration reversible | `alembic upgrade head && downgrade -1 && upgrade head` | exits 0 |

---

## 7. Pre-Flight Verification Register

| # | Claim | Tag | Check | Expected |
|---|---|---|---|---|
| 1 | 1.6 merged; `lock()` and `advance()` exist with the expected signatures | `[V]` | `grep -n "def lock\|def advance" backend/app/round/runner.py` | both present |
| 2 | 1.6 settled that the engine runs at advance, not lock | `[V]` | `grep -n "O3" handoffs/1.6-round-runner/spec.md` | default recorded |
| 3 | 2.1 merged; `simulation_instance.settings` is JSONB | `[V]` | `psql -c "\d simulation_instance"` | `settings jsonb` |
| 4 | **Nothing out of scope reads round timing today** *(§4.2)* | `[V]` | `grep -rn "deadline\|decisions_locked" backend/app --include=*.py` | zero — nothing exists to break |
| 5 | 2.2 merged; the scoped repo pattern is in place | `[V]` | `grep -n "class ScopedRepo" backend/app/repo/base.py` | present |
| 6 | A scheduler entrypoint mechanism is available | `[A]` | `grep -n "apscheduler\|celery" backend/requirements.txt` | **absent → default to a management command run by cron; report the choice** |

---

## 8. Build phases

1. **Model + migration.** *Verify:* I1, I7.
2. **`tick(now)` with lock and advance paths.** *Verify:* I2, I3, I4, I5.
3. **Service surface for 5.3, incl. bulk cascade.** *Verify:* every §5.4 row, output pasted.
4. **Entrypoint** (per pre-flight row 6). *Verify:* it is the only clock reader; a manual
   run over the 2.1 fixture locks the expected round.

---

## 9. Definition of Done

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–6, esp. row 6 resolved | | |
| Phases 1–4 verified | | |
| I1–I7 | | |
| All seven §5.4 null/negative cases | | |
| Instance-isolation canary still passes | | |
| Auth / browser canaries | | **N-A** — 2.4 adds auth; no UI |
