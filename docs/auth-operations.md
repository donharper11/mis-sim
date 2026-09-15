# Authentication operations

The API exposes `POST /api/auth/login` for students, `POST /api/auth/staff-login`
for instructors, TAs, and admins, and `GET /api/auth/me`. The client keeps the
bearer token in `sessionStorage` under `mis_sim.access_token`; requests add the
`Authorization: Bearer` header.

Tokens carry string `sub`, global `role`, nullable selected `section_id` and
`instance_id`, and integer `iat`/`exp`. Every request re-looks up an active user.
Students with multiple active enrollments select a section before receiving a
token. Staff may select an owned or assigned section or use a global token.

`SECRET_KEY` is required in every environment. Compose refuses to start without
it. The development seed is local-only and documented in `docs/demo-accounts.md`.
Passwords are bcrypt hashes and are never returned.
