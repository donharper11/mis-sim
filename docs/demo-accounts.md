# Development demo accounts

These credentials are deterministic development seed values only. Run
`python -m app.seed.demo --cohort --users` against SQLite, localhost, loopback, or
the Compose `db` host. The seed refuses non-local database URLs.

| Role | Login | Password |
|---|---|---|
| Student | `M2-101` through `M2-108` | `StudentPass!2026` |
| Student | `M2-201` through `M2-208` | `StudentPass!2026` |
| Instructor | `m2.instructor.a@example.edu` | `InstructorPass!2026` |
| Instructor | `m2.instructor.b@example.edu` | `InstructorPass!2026` |
| Admin | `m2.admin@example.edu` | `AdminPass!2026` |

The values are never logged or returned by the API. Change or remove them before
using a shared environment.
