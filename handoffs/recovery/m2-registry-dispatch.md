# M2 packet 2.5 dispatch

Date: 2026-09-15  
Exact base: `6a83b9a`  
Builder: one bounded registry builder; no subdelegation  
Independent audit: fresh M2 build auditor after candidate commit

## Allowlist

The builder may add or modify only:

- `backend/alembic/versions/20260915_0006_casepack_registry.py`
- `backend/app/models/platform.py`
- `backend/app/casepack/registry.py`
- `backend/app/services/platform.py`
- `backend/app/simulation/registry.py`
- `backend/app/seed/demo.py`
- `backend/packs/m2_isolation_fixture/**`
- `backend/app/casepack/validate.py`
- `backend/app/casepack/validate_messages.yaml`
- `backend/tests/fixtures/packs/broken_E19/**`
- `backend/tests/test_casepack_registry.py`
- `backend/tests/check_casepack_registry_schema.py`
- `backend/tests/check_fixture_matrix.py`
- `docs/casepack-operations.md`
- `QUALITY_PROTOCOL.md`
- `handoffs/2.5-casepack-registry/dod.md`

The builder must not modify auth, scheduling, frontend, engine/scoring, transition logic,
the 19-table runtime scope migration, existing casepack content, or unrelated tests/docs.
The validator follow-up is limited to the E19 numeric-range diagnostic and its named fixture
matrix updates.

## Acceptance commands

From repository root:

```text
PATH=/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin:$PATH PYTHONPATH=backend \
  pytest -q backend/tests/test_casepack_registry.py
PATH=/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin:$PATH PYTHONPATH=backend \
  python backend/tests/check_casepack_registry_schema.py
PATH=/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin:$PATH PYTHONPATH=backend \
  python backend/tests/check_fixture_matrix.py
PATH=/tmp/mis-sim-supervisor-venv-r2cjbjvg/bin:$PATH PYTHONPATH=backend \
  make check
```

The builder must also show fresh SQLite migration reversibility, registry cache/digest
negatives, both registered runtime-capable pack tuples bound to the two 2.1 instances, and
the existing 2.2 isolation canary. A passing builder report is not acceptance; the supervisor
will inspect the exact allowlist and obtain the independent audit before integration.
