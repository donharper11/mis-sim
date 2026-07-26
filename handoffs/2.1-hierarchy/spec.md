# 2.1 — Course → Section → Instance → Team → Enrollment · Build Spec

**Authored under** `SPEC_PROTOCOL.md` v1.2 · **Author:** Claude · **Date:** 2026-07-26
**Phase:** 2 · **Depends on:** 0.2 (merged) · **Blocks:** 2.2, 2.3, 2.4, 2.5, all of Phase 5

> The multi-cohort backbone. Two sections must be able to run **different casepacks
> simultaneously** with zero data leakage. BECSR retrofitted this and left a standing note;
> we build it once, correctly.

---

## 0. Spec Basis

**Read in full:**
- `BECSR/course-section-management.md` (VM `.5`) — the Course/Section/SimulationInstance/
  Enrollment model, the instance-scoping rule, and the backfill migration they needed
- `mis-tutor/backend/app/models/course.py` — `Course`, `CourseSection`, `CourseEnrollment`
- `mis-tutor/backend/app/models/team.py` — `Team`, `TeamMember`
- `handoffs/1.6-round-runner/spec.md` §5.1 — the runtime tables that will carry `instance_id`
- `CONTRACTS.md` — `instance_id`, casepack identifiers

**Extraction sufficiency:** covered. mis-tutor's models are read in full and give the
Course/Section/Enrollment shape; BECSR supplies the `SimulationInstance` layer mis-tutor
lacks (it was built for a one-shot consulting project, so it has no round state to scope).

---

## 1. Purpose and scope

**In scope:** the five-level hierarchy as SQLAlchemy models + Alembic migration; CRUD
services; the `SimulationInstance` with `scenario_id`, `current_round`, `total_rounds`,
`status`, and a `settings` JSONB for per-cohort overrides.

**Out of scope:**
- Round scheduling — deadlines, auto-lock, auto-advance (2.3)
- Auth and route protection (2.4)
- Casepack loading (2.5); `scenario_id` is a plain string here
- Instructor UI (Phase 5)
- Backfilling or migrating any existing data — this repo has none

---

## 2. Project-specific statements

**Scoring factors touched:** none. Structural.
**Casepack keys read:** none. `scenario_id` stores a `pack_key` string; resolution is 2.5.
**Instance scoping:** this packet *creates* `simulation_instance`. Tables here
(`course`, `section`, `enrollment`) are **above** the instance and correctly carry no
`instance_id`; `team` carries both `section_id` and `instance_id`.
**Business-language check:** no student-facing strings. Errors are instructor-facing.

---

## 3. Settled decisions

1. **BECSR's hierarchy, adopted.** Course → Section → SimulationInstance → Team → Student
   via Enrollment.
2. **One simulation instance per section**, unique constraint on `section_id`.
3. **`settings` JSONB on the instance** for per-cohort overrides (round count, budget
   multipliers) without forking the casepack.
4. **Integer PKs**, matching mis-tutor and 0.2's models. *(mis-tutor uses a UUID string PK
   for `CourseSection` alone; we do not — a mixed PK scheme across one hierarchy is a
   defect waiting to happen.)*
5. **`status` enum:** `setup · active · paused · completed`.
6. **Team belongs to exactly one instance.** No cross-instance teams.

---

## 4. Named compliant route *(SPEC_PROTOCOL §4.1)*

One implementation satisfying every invariant simultaneously:

```
Alembic revision creates, in dependency order:
    course        (no instance_id — above the instance)
    section       FK course_id, unique(course_id, section_code)
    simulation_instance  FK section_id UNIQUE, scenario_id VARCHAR,
                         current_round INT default 0, total_rounds INT default 6,
                         status VARCHAR, settings JSONB
    team          FK section_id, FK instance_id, both NOT NULL
    enrollment    FK user_id, FK section_id, nullable team_id,
                  unique(user_id, section_id)

Services filter every read of team/enrollment by section_id or instance_id.
No service in this packet reads a runtime state table, so I3 holds trivially.
```

I1 (hierarchy above instance carries no `instance_id`) and I2 (team carries it, non-null)
are satisfied by the column list; I4 by the unique constraints.

---

## 5. Design

### 5.1 Models

```
Course              id · course_code · course_name · academic_year · semester
                    instructor_id FK user · active_chapters JSONB · is_active
Section             id · course_id FK · section_code · section_name
                    max_teams · team_size_min · team_size_max · is_active
                    UNIQUE(course_id, section_code)
SimulationInstance  id · section_id FK UNIQUE · scenario_id · scenario_version
                    current_round · total_rounds · status · settings JSONB
                    started_at · completed_at
Team                id · section_id FK · instance_id FK · name · created_by
Enrollment          id · user_id FK · section_id FK · team_id FK nullable
                    role · enrolled_at · is_active
                    UNIQUE(user_id, section_id)
```

`Course.active_chapters` carries forward from mis-tutor — it already exists there as a
JSONB list defaulting to `[1..12]`, and the trimmed syllabus is a config change on it.

### 5.2 Services

`course_service` · `section_service` · `instance_service` · `team_service` ·
`enrollment_service`. Thin, no game logic (`GOVERNANCE` — service-first, but this packet
has no game logic to hold).

`instance_service.create(section_id, scenario_id, total_rounds)` — creating an instance for
a section that already has one raises a 409 through 0.2's `IntegrityError` handler.

### 5.3 Deletion behaviour

Deleting a course with active instances is refused with a message naming what blocks it.
Cascades are **explicit and narrow**: deleting a section cascades to its instance and teams;
deleting an instance does **not** delete its runtime state, it refuses while state exists.
*(An accidental cascade across a whole cohort's game state is unrecoverable.)*

---

## 5.4 Seed — a populated cohort *(GOVERNANCE §4.9)*

```
command     python -m app.seed.demo --cohort
seeds       1 course · 2 sections · 2 instances on DIFFERENT casepacks
            4 teams · 16 enrolled students with real names and IDs
demonstrate a query printing the full hierarchy, both sections side by side
```

The two-section fixture is not a test artifact — it is the seed 2.2's canary runs against
and 2.5 binds packs to.

---

## 6. Invariants

| # | Invariant | Check | Expected |
|---|---|---|---|
| I1 | Hierarchy above the instance carries no `instance_id` | `grep -n "instance_id" backend/app/models/{course,section,enrollment}.py` | zero |
| I2 | `team.instance_id` and `team.section_id` are both NOT NULL | `psql -c "\d team"` | both `not null` |
| I3 | This packet's services never read a runtime state table | `grep -rnE "arch_node\|round_result\|decision_line\|signal" backend/app/services/{course,section,instance,team,enrollment}_service.py` | zero |
| I4 | One instance per section | `psql -c "\d simulation_instance"` | unique index on `section_id` |
| I5 | Migration is reversible | `alembic upgrade head && alembic downgrade -1 && alembic upgrade head` | exits 0 each time |
| I6 | No pack-identity branching | `grep -rniE "riverside\|grocer" backend/app/models/ backend/app/services/` | zero |

---

## 7. Pre-Flight Verification Register

| # | Claim | Tag | Check | Expected |
|---|---|---|---|---|
| 1 | 0.2 merged; alembic baseline present | `[V]` | `ls backend/alembic/versions/` | one baseline revision |
| 2 | No hierarchy tables exist yet | `[V]` | `grep -rn "class Course\|class Section\|class Team" backend/app/models/` | zero |
| 3 | **Nothing out of scope depends on these models** *(§4.2)* | `[V]` | `grep -rn "Course\|Section\|Team\|Enrollment" backend/app --include=*.py \| grep -v "app/models/base"` | zero — greenfield, so the out-of-scope claim is trivially true and now proven |
| 4 | A `user` model exists to FK against | `[A]` | `grep -rn "class User" backend/app/models/` | **absent → this packet creates a minimal `User` (id, student_id, name, email, role, password_hash, is_active). 2.4 extends it.** Report which |
| 5 | 1.6's spec names the runtime tables that will carry `instance_id` | `[V]` | `grep -c "instance_id" handoffs/1.6-round-runner/spec.md` | ≥ 3 |

Row 4 is a real fork: 0.2 shipped no models beyond `Base`. Resolve it in the report, not
silently.

---

## 8. Build steps

1. **Models + migration.** *Verify:* I1, I2, I4, I5.
2. **Services with narrow cascades.** *Verify:* I3; deleting a course with an active
   instance is refused with a naming message.
3. **API routes**, unprotected for now (2.4 adds guards). *Verify:* create course → section
   → instance → team → enrol a user, end to end via `curl`, output pasted.
4. **Two-section fixture** — two sections under one course, different `scenario_id` values.
   *Verify:* both exist independently; this is the fixture 2.2's canary will use.

---

## 9. Definition of Done

| Item | Status | Evidence |
|---|---|---|
| Pre-flight rows 1–5, esp. row 4 resolved | | |
| Steps 1–4 verified | | |
| I1–I6 | | |
| Two-section two-casepack fixture exists | | |
| Migration up/down/up clean | | |
| `CONTRACTS.md` updated if any field shape changed | | |
| **Seed** — `--cohort` produces two sections on two casepacks | | |
| Auth canary | | **N-A** — 2.4 adds auth |
| Instance-isolation canary | | **partial** — fixture built here, canary asserted at 2.2 |
| Browser canaries | | **N-A** — no UI |
