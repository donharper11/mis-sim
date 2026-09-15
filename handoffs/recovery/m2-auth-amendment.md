# M2 packet 2.4 amendment — authenticated platform and login surface

Date: 2026-09-15  
Authority: supervisor, following the M2 reconciliation and independent contract review  
Base: `0290e0c` (M2.5 registry accepted and pushed)

This amendment is binding on the historical `handoffs/2.4-auth/spec.md`. It resolves
the old UI ownership, context selection, staff authorization, and secret-configuration
ambiguities before implementation. The packet is Heavy: it changes the User schema,
route authorization, token claims, and the first student-facing authentication workflow.

## Canonical authenticated context

The token payload is:

```json
{"sub":"17","role":"student","section_id":3,"instance_id":7,"iat":1780000000,"exp":1780028800}
```

`sub` is the string form of `user.id`; `role` is the global `User.role`; `section_id`
and `instance_id` are nullable authenticated context; `iat` and `exp` are integer JWT
timestamps. Decoding validates claim types and rejects missing or malformed `sub`, `role`,
or `exp`. Students receive context from active enrollments. Staff may receive a selected
section context; global staff tokens remain valid only where route-level ownership or
enrollment checks succeed. No token is trusted without a live user lookup and `is_active`.

The User schema gains nullable `last_active_at` through a reversible migration. Existing
2.1 identity fields remain unchanged. Passwords are stored only as bcrypt hashes and are
never logged or returned.

Unknown users, wrong passwords, and inactive accounts all return exactly
`{"detail":"Invalid credentials"}`. A student with multiple active enrollments receives
409 with this fixed body shape, which supplies the choices needed by the login UI:

```json
{"detail":"Select a section","sections":[
  {"section_id":3,"section_name":"Section A","instance_id":7},
  {"section_id":4,"section_name":"Section B","instance_id":8}
]}
```

## Login and context selection

The API surface is exactly:

```text
POST /api/auth/login       {student_id, password, section_id?}
POST /api/auth/staff-login {email, password, section_id?}
GET  /api/auth/me
```

Unknown users and wrong passwords return the same 401 response body. Inactive accounts
return that same 401. `/staff-login` rejects students with 403. Missing, malformed,
expired, or deleted-user bearer tokens return 401 with `WWW-Authenticate: Bearer`.

For a student, an optional `section_id` must identify an active enrollment. Without it,
one active enrollment is inferred; multiple active enrollments return 409 naming the
selection requirement; no active enrollment returns a valid token with null context.
Clients may never submit `instance_id` to login. For TA users, the selected section must
have an active TA enrollment. For instructors, a selected section must belong to a course
whose `instructor_id` is that user. Admins may select any active section. Staff may also
obtain a global token with no section selection; route-level checks then determine access.

`get_current_instance` accepts a route path `instance_id`, resolves its section, and checks:

- student: token context and active enrollment match the path instance;
- TA: active TA enrollment matches the instance's section;
- instructor: the instance's section belongs to an owned course;
- admin: unrestricted platform access.

A mismatch is 403. Query and request-body `instance_id` values are never read. Path
`instance_id` is permitted because it is validated against the authenticated context.

## Platform route guards

The existing 2.1 response shapes remain unchanged. Request input may remove fields whose
values are derived from the authenticated user. Add authorization without changing the
identity model. The reproducible route matrix is:

| Route | Allowed context |
|---|---|
| `POST /courses` | instructor (derive `instructor_id` from token) or admin (may choose it) |
| `GET /courses/{course_id}` | course instructor, admin, or a user with an active enrollment in one of its sections |
| `POST /courses/{course_id}/sections` | owning instructor or admin |
| `GET /sections/{section_id}` | active enrollment in section, owning instructor, or admin |
| `POST /sections/{section_id}/instance` | owning instructor or admin |
| `GET /instances/{instance_id}` | active enrollment in its section, owning instructor, assigned TA, or admin |
| `POST /instances/{instance_id}/teams` | owning instructor, assigned TA, or admin; TA may create any team in the assigned section |
| `POST /sections/{section_id}/enrollments` | owning instructor or admin |

Global instructor tokens reach any section they own; global TA tokens reach any section with
an active TA enrollment; global admin tokens reach any section. A selected token context
must additionally match the route's section or instance. `TeamIn` removes `created_by` from
the request body; `TeamOut` may expose it, and the service derives it from the authenticated
user.

`/staff-login` rejects a student with exactly `{"detail":"This login is for instructors and TAs only"}`.
The route guards must preserve 404/409 domain semantics after authentication failures are
handled at the dependency boundary. No runtime table, engine, scoring, registry, or
scheduling route is added here.

## Login surface and browser canary

M2 owns a minimal `/login` React route using the existing semantic design tokens. It has
student/staff mode, credential fields, optional section selection when the API reports
multiple contexts, visible invalid-credential/forbidden/inactive states, bearer-token
storage, and a successful `/api/auth/me` request using the same session. 3.1 inherits this
API/client/session contract and builds post-login application screens; it does not recreate
login.

The canary runs the Vite frontend and API with the existing relative `/api` proxy on one
browser-visible host pair, logs in a seeded student, then reads `/api/auth/me` in that same
browser session. It also proves a section-A student receives 403 when requesting section-B
data using `GET /api/instances/{section_B_instance_id}`. No cookie transport is introduced
in this packet; the bearer token is stored in `sessionStorage` under the exact key
`mis_sim.access_token`, and the Axios client adds `Authorization: Bearer <token>`. This is
the stable session contract inherited by 3.1.

## Seed and secret configuration

`python -m app.seed.demo --cohort --users` extends the accepted registry cohort with 16
students, two instructors, one admin, active enrollments, bcrypt hashes, and documented
development credentials in `docs/demo-accounts.md`. It refuses non-local databases;
local means SQLite, loopback hostnames, or the Compose `db` hostname. No password appears
in logs, API responses, or committed fixtures beyond the explicitly documented dev-only
credentials file. `--cohort` without `--users` remains supported for the pre-auth hierarchy
canary. `--users` is deterministic and idempotent on the seeded email/student-id keys, or
refuses with a clear conflict rather than inserting duplicates.

`SECRET_KEY` must be supplied by environment everywhere the application starts. Remove the
known default from `backend/app/config.py`; Compose passes `${SECRET_KEY:?SECRET_KEY must be
set}` to the API service. Tests and `make check` set an explicit non-production key through
the allowlisted `Makefile`/test configuration; no committed runtime configuration contains
the old default. Startup fails when no usable key is present. The canonical auth error body
for unknown, wrong-password, or inactive accounts is exactly `{"detail":"Invalid credentials"}`.
Multiple active enrollments return 409 with the fixed body shape shown above, including the
available section choices.
Do not add rate limiting in this packet; record that accepted risk and the trigger “before
any internet-facing deployment” in `SECURITY.md`.

## Required evidence

- migration upgrade → downgrade → upgrade;
- JWT round-trip, claim validation, missing/malformed/expired/deleted-user rejection;
- identical unknown-user and wrong-password bodies, inactive-account rejection;
- student multiple-enrollment selection, TA/instructor/admin context matrix;
- guarded platform route matrix and cross-instance 403;
- no plaintext password persistence/logging and no unvalidated query/body instance context;
- secret configuration check and non-local seed refusal;
- seeded browser login followed by authenticated `/me` on the same app/API host pair;
- existing instance-isolation canary and the full repository gate.

Scheduling, runtime tables, engine/scoring, casepack registry behavior, and 2.5 migrations
remain out of scope.
