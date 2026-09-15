# M2 packet 2.1 hierarchy independent audit

- Candidate: `35f9ab56e48fdc03229b16ad170a6d3dd041965d`
- Dispatch base: `376d54c` (the candidate's immediate parent is the reconciled M2 foundation)
- Worktree: `/home/ubuntu/projects/mis-sim`
- Verdict: **RETURN**

## Scope and tree

The candidate worktree was clean. The commit changed exactly the nine dispatch-allowlisted paths:

- `backend/app/models/platform.py`
- `backend/app/services/platform.py`
- `backend/app/api/platform.py`
- `backend/alembic/versions/20260915_0004_platform_hierarchy.py`
- `backend/alembic/env.py`
- `backend/app/main.py`
- `backend/app/seed/demo.py`
- `backend/tests/test_platform_hierarchy.py`
- `handoffs/2.1-hierarchy/dod.md`

`git diff --check` passed. No simulation, casepack, auth, frontend, or existing migration paths changed. The migration has `revision=20260915_0004` and `down_revision=20260914_0003`, creates the six amended tables, and adds no runtime-table foreign keys. Alembic metadata imports both M1 simulation and M2 platform models.

## Evidence

- Focused hierarchy tests under system Python: **4 passed**.
- The supervisor venv focused run produced **3 passed, 1 environment failure** because that venv lacks `aiosqlite`; system Python has the dependency and passes the same test file. This is an environment limitation, not treated as a product failure.
- Source inspection confirmed canonical `simulation_instance.instance_id`, opaque `(pack_key, pack_version)`, one instance per section, non-null team section/instance references, enrollment uniqueness, nullable team assignment, and narrow unprotected API routes.
- The deterministic cohort seed creates one course, two sections with distinct opaque pack tuples, four teams, and sixteen student enrollments.
- Alembic upgrade/down/up was not independently executed: the available supervisor venv has Alembic but lacks `aiosqlite`, while the system environment has `aiosqlite` but no Alembic module. The migration source and revision chain were inspected directly.

## Blocking finding

### M2-001 — Team and enrollment reads are not scope-filtered

The dispatch/spec requires every service read of team/enrollment to carry `section_id` or `instance_id` scope. `TeamService.read(session, team_id)` and `EnrollmentService.read(session, enrollment_id)` call the generic ID-only `_one` helper and accept no parent scope. A caller with an ID can therefore retrieve a team or enrollment without proving its section/instance context. This violates the hierarchy isolation contract even though the minimum route set does not expose GET routes for these rows yet; later packet consumers will inherit the unscoped service seam.

The create paths do validate section/team relationships, but that does not repair the read API's missing scope predicate.

## Conclusion

**RETURN.** Add scoped read signatures/queries for teams and enrollments (and preserve those scopes in later route consumers), then rerun focused tests and the disposable PostgreSQL upgrade → downgrade → upgrade evidence. No implementation or shared contract files were modified by this audit.

## Successor audit — `5d6b5733b923f044b6dbb8dcadbe01e98748c803`

**Verdict: PASS.** This successor includes the scoped-read correction from
`ad199f5` and the cohort seed team-ID correction.

### Scope and tree

The cumulative builder changes from `35f9ab5` through `5d6b573` are confined
to the dispatch allowlist: the six hierarchy implementation paths, the
Alembic metadata adapter, `main.py`, `seed/demo.py`, `requirements.txt`, the
focused test, and the hierarchy DoD. The only additional tracked artifact in
the audit chain is this findings report. `git diff --check` passed and the
candidate was clean before this report append.

### Independent evidence

- Declared supervisor environment (`/tmp/mis-sim-supervisor-venv-r2cjbjvg`),
  with the newly declared `aiosqlite`, focused hierarchy tests: **5 passed**.
- SQLite Alembic: `upgrade head`, `downgrade 20260914_0003`, and `upgrade
  head` all passed. The final database had 26 expected tables and
  `alembic_version=20260915_0004`.
- Fresh migrated SQLite database plus `python -m app.seed.demo --cohort`:
  output was `sections=2 instances=2 teams=4 enrollments=16`; persisted counts
  were user=17, course=1, section=2, instance=2, team=4, enrollment=16.
  Pack tuples were `pack_alpha@1.0.0` and `pack_beta@1.0.0`; each section had
  eight enrollments and eight non-null team assignments.
- The focused scope probes now prove section and instance reads succeed only
  in the matching scope, mismatched scopes return `PlatformNotFound`, and an
  unscoped team/enrollment read raises `PlatformConflict`.
- The route table contains the exact minimum hierarchy routes under `/api` and
  no hierarchy service reads runtime state tables.
- Direct deletion probe blocked course deletion with an active instance and
  allowed setup-section cleanup; a fresh session confirmed section, instance,
  team, and enrollment rows were all removed.
- The supervisor reported the full root gate green at **662 passed**, with all
  guards green.

M2-001 is closed: both `TeamService.read` and `EnrollmentService.read` now
require `section_id` or `instance_id` and apply that predicate to the query.
No implementation or shared contract files were modified by this audit.
