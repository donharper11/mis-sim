# Packet 2.1 builder evidence

Candidate: pending commit on the bounded M2 hierarchy branch.

Implemented within the dispatch allowlist:

- `User`, `Course`, `Section`, `SimulationInstance`, `Team`, and `Enrollment` models.
- Canonical `instance_id` primary key and opaque `(pack_key, pack_version)` identity.
- Unique section instances, section/team hierarchy checks, and per-user section enrollment uniqueness.
- Async service layer and unprotected nested CRUD seam.
- Reversible Alembic migration `20260915_0004` with no runtime foreign keys.
- Deterministic `python -m app.seed.demo --cohort` seed: one course, two sections,
  two opaque pack tuples, four teams, and sixteen student enrollments.

Validation commands and output are recorded in the builder handoff/commit report.
Runtime instance guards, auth, scheduling, and pack registry remain later packets.

Scope correction: `TeamService.read` and `EnrollmentService.read` require a
`section_id` or `instance_id` predicate. Focused negative tests prove that an
ID from another section or instance is not returned.
