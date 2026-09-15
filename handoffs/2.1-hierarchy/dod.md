# Packet 2.1 builder evidence

Candidate: `5d6b573` (successor after scoped-read and cohort-seed corrections).

Implemented within the dispatch allowlist:

- `User`, `Course`, `Section`, `SimulationInstance`, `Team`, and `Enrollment` models.
- Canonical `instance_id` primary key and opaque `(pack_key, pack_version)` identity.
- Unique section instances, section/team hierarchy checks, and per-user section enrollment uniqueness.
- Async service layer and unprotected nested CRUD seam.
- Reversible Alembic migration `20260915_0004` with no runtime foreign keys.
- Deterministic `python -m app.seed.demo --cohort` seed: one course, two sections,
  two opaque pack tuples, four teams, and sixteen student enrollments.

Validation: the focused hierarchy suite passes **5 tests** in the declared
supervisor environment; SQLite Alembic `upgrade head -> downgrade -1 -> upgrade
head` passes; a clean migrated database runs `python -m app.seed.demo --cohort`
and persists 2 sections, 2 instances, 4 teams, and 16 enrollments. The combined
root gate passes **662 tests** and all guards. Independent audit:
`findings/recovery-m2-hierarchy-2026-09-15.md`.
Runtime instance guards, auth, scheduling, and pack registry remain later packets.

Scope correction: `TeamService.read` and `EnrollmentService.read` require a
`section_id` or `instance_id` predicate. Focused negative tests prove that an
ID from another section or instance is not returned.
