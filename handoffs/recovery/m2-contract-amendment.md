# M2 contract amendment — platform identity and dispatch boundary

Date: 2026-09-15  
Authority: supervisor, following the independent reconciliation in
[`m2-spec-reconciliation.md`](m2-spec-reconciliation.md)

This amendment is the living decision record for the M2 dispatch. It resolves
historical wording that predates the audited M1 runtime. The original 2.x specs
remain useful source material, but a builder follows this amendment where the
old text differs.

## Canonical identity

`simulation_instance.instance_id` is the integer primary key and the target of
the canonical `instance_id` foreign key in [`CONTRACTS.md`](../../CONTRACTS.md).
Every runtime table keeps a non-null integer `instance_id`. A model may expose
an ORM convenience alias, but migrations, foreign-key declarations, route
parameters, token claims, and evidence use `instance_id` consistently.

The instance's pack identity is the tuple `(pack_key, pack_version)`, matching
M1's `simulation_run_v1` and [`CONTRACTS.md`](../../CONTRACTS.md). The historical
`scenario_id` and `scenario_version` names are retired; they must not be added
as a second source of truth. The registry later supplies the validated pack and
its immutable digest; M1 continues to pin `pack_digest` on each run.

## 2.1 hierarchy ruling

Packet 2.1 creates these new tables: `user`, `course`, `section`,
`simulation_instance`, `team`, and `enrollment`. `user.id`, `course.id`,
`section.id`, `team.id`, and `enrollment.id` are integer primary keys.
`simulation_instance.instance_id` is its primary key, unique per `section_id`.

`User` is only the identity/FK foundation in 2.1. It has `student_id` (unique and
nullable for staff), `name`, `email` (unique), `role` (`student|ta|instructor|admin`),
nullable `password_hash`, `is_active`, and timestamps. Password hashing, token
issuance, login, and route guards belong exclusively to 2.4; 2.1 never logs or
interprets passwords.

`Course.instructor_id` references `user.id`. `Section.course_id` references
`course.id` and is unique with `section_code`. `Team.section_id` and
`Team.instance_id` are both non-null and reference their hierarchy parents.
`Enrollment.user_id` and `Enrollment.section_id` are required; `team_id` is
nullable until assignment. `(user_id, section_id)` is unique. Enrollment roles
are `student|ta`; course ownership remains on `Course.instructor_id`.

`SimulationInstance` stores `pack_key`, `pack_version`, `current_round`,
`total_rounds`, `status` (`setup|active|paused|completed`), `settings` JSON,
and lifecycle timestamps. 2.1 treats pack values as opaque strings. 2.5 is
responsible for validated registration, digest resolution, and immutable binding.

The 2.1 API is an unprotected CRUD seam because auth is 2.4. It uses the service
layer and nested resource paths; it never reads or writes a runtime state table.
The exact minimum routes are:

```
POST /api/courses
GET  /api/courses/{course_id}
POST /api/courses/{course_id}/sections
GET  /api/sections/{section_id}
POST /api/sections/{section_id}/instance
GET  /api/instances/{instance_id}
POST /api/instances/{instance_id}/teams
POST /api/sections/{section_id}/enrollments
```

Responses are JSON projections of the created/read model rows. 2.4 adds
authentication and authorization without changing these identity fields.

The deterministic `--cohort` seed creates one course, two sections, one
instance per section, two teams per instance, and users/enrollments with
distinct opaque pack tuples. It does not claim registry validation; that claim
belongs to the M2 integration seed after 2.5.

## 2.2 inventory ruling (pre-dispatch only)

The complete current runtime inventory is the 16 tables in
`handoffs/1.6-round-runner/spec.md` **plus** the three M1 tables
`simulation_run_v1`, `simulation_sheet_v1`, and `simulation_checkpoint_v1`.
The omitted 1.6 tables are `governance_state`, `policy_decision`, and
`stakeholder_alignment`; they are included. 2.2 must decide and document the
direct-FK treatment for all 19 tables: the three M1 child tables already have a
composite FK to `simulation_run_v1`, while the run and every legacy table need
an explicit restricted path to `simulation_instance`. No 2.1 builder adds those
runtime FKs.

## Later packet blockers

2.2 remains blocked until its 19-table FK list, repository guard, and actual
canary path are amended. 2.4 remains blocked until staff section context,
token claims, and the M2-owned login surface are amended. 2.3 remains blocked
until per-team lock/advance semantics are defined against the real runner.
2.5 remains blocked until registry-to-`RuntimePackV1` construction, digest
pinning, and the production second-pack policy are defined. None of those
decisions are delegated to the 2.1 builder.

