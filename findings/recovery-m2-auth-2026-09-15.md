# M2.4 Authentication Audit — 2026-09-15

**Candidate:** `e0d0d10`  
**Dispatch/amendment basis:** `handoffs/recovery/m2-auth-dispatch.md`, `handoffs/recovery/m2-auth-amendment.md`  
**Verdict:** **RETURN**

## Blocking finding

### AUTH-001 — `--cohort --users` creates the wrong instructor population and unusable seeded staff access

The amendment requires the cohort seed to be idempotent and to create **16 students, two instructors, and one admin**, with active enrollments and usable documented credentials. On a fresh migrated SQLite database, running:

```text
python -m app.seed.demo --cohort --users
python -m app.seed.demo --cohort --users
```

succeeded twice and was idempotent for row counts, but the resulting counts were:

```text
users=20, courses=1, sections=2, instances=2, enrollments=16
roles: admin=1, instructor=3, student=16
```

The three instructors were `m2.instructor@example.edu`, `m2.instructor.a@example.edu`, and `m2.instructor.b@example.edu`. The seeded course is owned by the initial `m2.instructor@example.edu`, while the documented A/B instructor accounts are the newly-created users. A direct staff-login/API probe showed:

```text
POST /api/auth/staff-login  (m2.instructor.a@example.edu) -> 200
GET  /api/courses/1         (same bearer token)             -> 403
{"detail":"Access to this course is forbidden"}
```

This violates the exact two-instructor seed contract and leaves the documented seeded staff accounts without access to the seeded course. Repair the seed so the final population has exactly two instructors and the documented instructor account(s) own or are otherwise authorized for the seeded course, then rerun the idempotency and route probes.

## Evidence run

- Focused auth tests: `8 passed` for `backend/tests/test_auth.py backend/tests/test_auth_guards.py`.
- Static auth invariant guard: `auth invariants: PASS (no stub, no client instance context, required secret)`.
- Alembic SQLite migration: upgrade to `20260915_0007`, downgrade to `20260915_0006`, and upgrade back to head all passed.
- Seed idempotency: two consecutive `--cohort --users` runs completed; row counts remained stable, but the role count exposed AUTH-001.
- Frontend: `npm run lint` passed; `npm run build` passed with only the Vite large-chunk warning.
- Browser canary: student login, bearer storage, `/api/auth/me`, and cross-instance denial passed in a fresh same-host Vite/API run.
- Full `make check` was attempted under the system interpreter: `657 passed`, with three dependency/environment failures and one Alembic error (`psycopg2` and `alembic` unavailable in that interpreter); no auth test failure was observed. This is not product proof for the full gate.
- Candidate implementation diff passed `git diff --check` against the auth dispatch implementation base. No implementation files were modified during this audit.

## Scope/status

The reviewed auth implementation paths were limited to the dispatch allowlist (backend auth/API/dependency/config/model/seed/migration, auth tests/checks, Compose/Makefile, and the frontend login/session client). The candidate was clean before audit artifacts; the browser harness left an untracked temporary Vite config. This report is the only audit report artifact added.

## Successor re-audit — `d89d5b6c187cedef33dd0d2621faf00f12539069`

**Final verdict: PASS.** The successor changes only the cohort’s initial instructor identity and adds a deterministic role/ownership regression. On a fresh migrated SQLite database, two consecutive `--cohort --users` runs produced:

```text
roles: admin=1, instructor=2, student=16
course owner: m2.instructor.a@example.edu
```

Both documented instructor accounts authenticated successfully with `InstructorPass!2026`; instructor A received `GET /api/courses/1 -> 200`, and instructor B received the expected `403 Access to this course is forbidden`. The prior AUTH-001 is closed.

Successor evidence:

- Focused auth/guard tests: `9 passed` (including the new role/ownership regression; the parent audit independently observed `14 passed` across its focused auth set).
- Auth invariant guard: PASS.
- Exact successor migration cycle: `0007 -> 0006 -> 0007` passed; `user.last_active_at` was restored nullable at head.
- Seed idempotency: two real CLI runs passed with stable counts and exactly 2 instructors, 16 students, and 1 admin.
- Frontend `npm run lint`: passed. `npm run build`: passed; only the existing large-chunk warning was emitted.
- The previous same-host browser canary passed on the unchanged frontend/auth surface. A fresh successor browser rerun was attempted with a temporary external Vite harness but could not start because that harness could not resolve `react-refresh`; this is a harness dependency issue, and the successor contains no frontend changes. Direct API login, `/me`, ownership, and cross-instance guard probes passed.
- Full `make check` remains environment-limited under the system interpreter by missing `psycopg2`/Alembic dependencies; this did not produce an auth failure.

No implementation files were modified by the auditor. The only repository artifact is this report.
