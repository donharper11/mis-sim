# M2 packet 2.4 dispatch — auth, roles, route protection, login surface

Date: 2026-09-15  
Base: `0290e0c`  
Binding contract: [`m2-auth-amendment.md`](m2-auth-amendment.md) and the historical
[`../../2.4-auth/spec.md`](../../2.4-auth/spec.md), with the amendment taking precedence.

The builder may edit only these paths:

```text
backend/alembic/versions/<new-auth-revision>.py
backend/app/models/platform.py
backend/app/services/auth.py
backend/app/api/deps.py
backend/app/api/auth.py
backend/app/api/platform.py
backend/app/services/platform.py
backend/app/config.py
backend/app/seed/demo.py
backend/tests/conftest.py
backend/tests/test_auth.py
backend/tests/test_auth_guards.py
backend/tests/check_auth_invariants.py
frontend/src/App.jsx
frontend/src/api/client.js
frontend/src/i18n.js
frontend/src/pages/Login.jsx
frontend/src/styles/*
docker-compose.yml
Makefile
docs/demo-accounts.md
docs/auth-operations.md
CONTRACTS.md
SECURITY.md
handoffs/2.4-auth/dod.md
```

No scheduling, runtime-table, engine/scoring, casepack-registry, or unrelated migration
path may change. Do not add dependencies. Do not push, merge, deploy, or edit shared status
files. Do not subdelegate. Return any unresolved semantic choice to the supervisor.

`backend/app/config.py` must have no insecure fallback secret. `Makefile` and
`backend/tests/conftest.py` provide an explicit test-only `SECRET_KEY` so the full gate
remains runnable; Compose must require `${SECRET_KEY}` rather than silently defaulting.

Before editing, record the seven historical preflight results and the amendment decisions.
The builder must return an exact candidate SHA, a clean worktree, the focused evidence,
and any observation that is not implemented.

The candidate is not accepted by a builder report. A fresh auditor will inspect the exact
SHA, rerun the focused probes, run the browser canary, and run `make check` before the
supervisor updates the living register and merges.
