# M2 packet 2.4 — auth and login DoD

Implementation is bounded by `handoffs/recovery/m2-auth-amendment.md` and
`handoffs/recovery/m2-auth-dispatch.md`.

| Requirement | Evidence | Status |
|---|---|---|
| Reversible User/auth migration including `last_active_at` | fresh Alembic upgrade → downgrade → upgrade | pending |
| JWT claims, type validation, bearer 401s, inactive/deleted-user refusal | `test_auth.py`, `test_auth_guards.py` | pending |
| Equal unknown-user/wrong-password response and multiple-enrollment selection | focused auth tests | pending |
| Student/TA/instructor/admin route matrix and cross-instance 403 | guarded API tests | pending |
| No plaintext passwords or unvalidated query/body instance context | `check_auth_invariants.py` | pending |
| Secret configuration and non-local seed refusal | invariant check and seed probe | pending |
| Seeded `/login` → authenticated `/api/auth/me` same-host browser canary | Playwright/browser evidence | pending |
| Existing isolation canary and full repository gate | `check_instance_isolation.py`; `make check` | pending |

The packet does not implement scheduling, runtime-table changes, engine/scoring behavior,
casepack registry behavior, or UI beyond the minimal login surface.
