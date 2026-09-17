# M5 instructor operations — bounded setup and roster contract

Date: 2026-09-18  
Status: reconnaissance and handoff; no runtime implementation is included here.  
Scope: the smallest usable M5 slice toward the north-star `setup → grade export` path.

## Decision

The first M5 slice should be **M5.1 course/section/pack setup plus the M5.2 roster and
team-assignment workspace**, using the existing platform identity tables.  It should end
when an instructor can create or select a course, create/select a section, bind one
registered pack to its setup instance, see the complete roster and teams, and assign an
already-existing student identity to a team.

This is a deliberately bounded setup slice.  It does not include scheduling, round
advancement, monitoring, grading, participation, export, casepack registration, or clone /
archive / reset.  Those are separate packets with different state and acceptance risks.

## Verified starting point

The following claims were checked against the current checkout.

| Existing primitive | Evidence | Consequence |
|---|---|---|
| Course, Section, SimulationInstance, Team, Enrollment, User models exist | `[V]` `backend/app/models/platform.py:20-168` | The first slice needs no new table or migration. |
| Pack binding is registry-backed and digest-pinned | `[V]` `backend/app/services/platform.py:111-140`; `backend/app/casepack/registry.py:91-130` | Setup must choose a registered `(pack_key, pack_version)`; it must not accept arbitrary disk paths. |
| Auth has instructor/admin ownership and instance guards | `[V]` `backend/app/api/deps.py:55-145`; `backend/app/api/auth.py:42-103` | Every setup read/write must use `require_instructor` and ownership checks; no caller-supplied instance scope may override the authenticated context. |
| Single-record creation routes exist | `[V]` `backend/app/api/platform.py:158-258` | Existing `POST /courses`, `POST /courses/{id}/sections`, `POST /sections/{id}/instance`, `POST /instances/{id}/teams`, and `POST /sections/{id}/enrollments` can be reused or wrapped. |
| Existing services enforce identity and section/team invariants | `[V]` `backend/app/services/platform.py:33-245` | New list/assignment operations should call the services or add narrowly scoped methods, not write rows directly. |
| Casepack registry has no HTTP read/list surface | `[V]` `backend/app/casepack/registry.py:45-130`; `[V]` `backend/app/main.py:18-41` | Pack selection needs a read route; registration remains a later I6 operation. |
| No instructor frontend exists | `[V]` `frontend/src/App.jsx:18-43`; `[V]` `frontend/src/components/AppShell.jsx:15-58` | Add a role-gated instructor route and page; do not put instructor controls into student pages. |
| No roster list, team list, team assignment, or user provisioning route exists | `[V]` `backend/app/api/platform.py:158-258` | Current POST-only enrollment is insufficient for an instructor workspace. |
| No grading, participation, deliverable, or export model/API exists | `[V]` `rg -n "grading|participation|deliverable|export" backend/app frontend/src` | Do not couple the setup slice to an invented grading schema. |

The historical M2 contracts explicitly leave instructor UI to Phase 5 and instructor
roster management to 5.2: `[V]` `handoffs/2.1-hierarchy/spec.md:31-38` and
`[V]` `handoffs/2.4-auth/spec.md:41-52`.

## Exact missing contracts

### 1. Instructor setup read model

The frontend needs one stable, aggregate response rather than making a sequence of
single-record calls and guessing which records belong together.

Recommended route:

```http
GET /api/instructor/courses
GET /api/instructor/courses/{course_id}/setup
```

Both routes are instructor/admin-only.  The list route returns only owned courses for an
instructor and all courses for an admin.  The setup route returns:

```json
{
  "course": {
    "id": 1,
    "course_code": "MIS-PLATFORM",
    "course_name": "...",
    "academic_year": "2026",
    "semester": "A",
    "active_chapters": [1, 2],
    "is_active": true
  },
  "sections": [
    {
      "id": 2,
      "section_code": "A",
      "section_name": "Section A",
      "max_teams": 8,
      "team_size_min": 2,
      "team_size_max": 6,
      "is_active": true,
      "instance": {
        "instance_id": 3,
        "pack_key": "riverside_grocery",
        "pack_version": "0.1.0",
        "pack_digest": "<hex>",
        "current_round": 0,
        "total_rounds": 6,
        "status": "setup"
      },
      "teams": [
        {"id": 10, "name": "Team A", "member_count": 3}
      ],
      "enrollment_count": 3
    }
  ]
}
```

The digest may be displayed as a pack identity check but should not be editable.  Do not
return runtime rows, student decision data, or grades from this read model.

### 2. Registered pack selection

Recommended route:

```http
GET /api/casepacks
```

Response fields are the existing `Casepack` metadata only:
`pack_key`, `pack_version`, `display_name`, `vertical`, `schema_version`, `rounds`,
`pack_digest`, registration time, and validation summary (`errors`, `warnings`, `exit_code`).
No filesystem path or pack content should reach the browser.

The setup action may continue using the existing
`POST /api/sections/{section_id}/instance`.  Its contract must make the following
conditions explicit:

* the authenticated instructor owns the section's course;
* the selected `(pack_key, pack_version)` is registered and validator-clean;
* one instance exists per section;
* the instance starts in `setup`, `current_round = 0`, and `total_rounds` does not exceed
  the registered pack's authored rounds;
* the instance records the registry digest;
* an existing non-setup instance cannot have its pack changed.

The existing service already enforces registry resolution and digest capture; the missing
piece is the instructor-facing list and explicit response/error contract.

### 3. Roster and team assignment

For the bounded first slice, operate on **existing `User` identities**.  This keeps the
packet migration-free and avoids silently inventing password provisioning semantics.

Recommended routes:

```http
GET  /api/sections/{section_id}/roster
POST /api/sections/{section_id}/enrollments
PATCH /api/sections/{section_id}/enrollments/{enrollment_id}
GET  /api/instances/{instance_id}/teams
POST /api/instances/{instance_id}/teams
PATCH /api/instances/{instance_id}/teams/{team_id}
```

Roster response rows should include `enrollment_id`, `user_id`, `student_id`, `name`,
`email`, enrollment role, active state, and assigned team `{id, name}` or `null`.
Student email and ID are instructor data; they must remain behind the instructor scope.

The assignment patch accepts only a `team_id` in the same instance/section or `null` to
unassign.  It must reject a team from another section or instance with 409, preserve the
existing `UNIQUE(user_id, section_id)` rule, and enforce `section.team_size_min`,
`section.team_size_max`, and `section.max_teams` before mutation.  The current
`EnrollmentService.create` checks section identity and duplicate enrollment but does not
enforce team size or expose assignment mutation.

### 4. Account provisioning is a dependency, not a hidden part of this packet

The current `User.password_hash` is nullable and there is no instructor route for creating
students or issuing invitations: `[V]` `backend/app/models/platform.py:20-38`,
`[V]` `handoffs/2.4-auth/spec.md:41-52`.  Therefore this packet must either:

1. use seeded / pre-provisioned users and state that limitation in the UI; or
2. receive a separately approved account-provisioning contract before CSV import is
   claimed.

The first option is recommended for this bounded slice.  Full M5.2 CSV support should be a
follow-up packet that defines required columns, duplicate handling, password/invite
lifecycle, preview versus apply, and row-level error reporting.  A CSV upload that merely
creates users with null passwords would make the production gate appear complete while
students cannot log in.

## Narrow packet boundary

### In scope

* Instructor/admin setup workspace and role-gated route.
* Course and section list/read aggregation.
* Registered casepack metadata list and setup-instance pack selection.
* Setup-state validation and clear 404/403/409 responses.
* Roster read for one section.
* Team list/create/rename and existing-user enrollment / team assignment.
* Team-size and max-team constraints at the mutation boundary.
* Backend API tests, frontend lint/build, and one browser proof using a disposable seeded
  cohort.

### Out of scope

* Creating users, passwords, invites, or CSV import.
* Round schedules, pause/lock/advance, or monitoring dashboards.
* Grading configuration, participation, deliverable overrides, or export.
* Casepack registration/validation UI.
* Clone, archive, reset, or deletion workflows.
* Runtime state, scoring, engine, migrations, and changes to the student decision screens.

## Allowed implementation surface for the builder

The implementation agent should be constrained to:

```text
backend/app/api/instructor.py                 # new setup/roster routes and schemas
backend/app/api/platform.py                   # only if existing setup routes need contract fixes
backend/app/services/platform.py              # only bounded list/assignment methods
backend/app/casepack/registry.py              # read-only metadata query helper, if needed
backend/app/main.py                           # router registration
backend/tests/test_instructor_setup_api.py    # new API contract tests
backend/tests/test_platform_hierarchy.py      # only focused invariant additions, if needed
frontend/src/App.jsx                          # instructor route
frontend/src/components/AppShell.jsx          # instructor navigation/role boundary
frontend/src/pages/InstructorSetup.jsx        # new setup page
frontend/src/api/client.js                    # only typed request helpers, if added
frontend/src/styles/theme.css                 # only styles required by the new page
frontend/package.json                         # no dependency additions without review
```

No Alembic revision is expected for this slice.  No edits are permitted to engine,
simulation runtime models/services, scoring, casepack content, student pages, or shared
design/north-star documents.

## Acceptance tests

The builder should add focused tests with these observable assertions.

1. **Ownership:** an instructor sees only their courses; another instructor receives 403
   for the setup aggregate; admin can read both.
2. **Pack list safety:** `GET /api/casepacks` returns registered metadata and validation
   summary but no filesystem path or casepack content.
3. **Setup creation:** instructor creates a section instance with a registered pack; the
   response contains the registry digest and `setup/current_round=0`; an unregistered pack
   returns 409 and creates no row.
4. **Setup immutability:** a second instance for the section is 409; rebinding an active
   or round-started instance is 409; a different section remains isolated.
5. **Roster scope:** roster rows show only the requested owned section; cross-section access
   is 403; student tokens cannot call the instructor route.
6. **Enrollment:** an existing student enrolls once; duplicate enrollment is 409; a
   cross-section team ID is 409; unassigning sets `team_id = null`.
7. **Team constraints:** a team cannot exceed `team_size_max`, and a section cannot exceed
   `max_teams`; both failures are 409 with instructor-readable details.
8. **Assignment concurrency:** two simultaneous assignment attempts cannot leave a team
   above its maximum; the losing transaction receives 409 and the persisted roster remains
   valid.  If the existing SQLite tests cannot prove this, run the check on disposable
   PostgreSQL.
9. **Browser proof:** a staff login reaches the instructor setup route, selects a registered
   pack, displays section/instance status, creates or selects a team, and assigns a seeded
   student; the browser console and network log are clean at the supported desktop width.
10. **Student regression:** the seeded student login still reaches the existing student
    dashboard and cannot see the instructor route or roster data.

The packet is complete only when the browser proof is observed.  API-only success does not
close the M5 setup gate.

## Dependencies and next handoffs

* **Available now:** M2 hierarchy, auth/ownership, registry, and the seeded cohort are
  present and covered by focused tests.
* **Must remain stable:** pack identity `(pack_key, pack_version)` and digest pinning;
  instance setup status; section-scoped enrollment uniqueness.
* **Follow-up M5 packet:** account provisioning plus CSV preview/apply and row-level error
  report.  It should consume this roster contract rather than bypass it.
* **Parallel M5 packet:** grading configuration, deliverable override, participation, and
  export requires a separate data contract.  It can proceed against a stable enrollment
  and team read model but must not add grade fields to this packet.
* **Later M5 packet:** round-control and monitoring can consume the existing scheduler and
  round-control services after instructor setup produces initialized teams.

The north-star M5 exit gate remains broader than this packet: the complete observed path is
setup, pack load, enrollment, scheduling, advancement, and grade export.  This handoff closes
only the first setup/roster segment and makes the missing seams explicit so later agents do
not wire unrelated features into it.
