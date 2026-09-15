# Packet 2.2 builder evidence — instance scoping and isolation

Date: 2026-09-15. Builder: `m2_scoping_builder`.
Dispatch base: `35a7f3c`.
Implementation candidate: `da339c5fb8b2fdccc5060e64608c76d0c459d318`.
This record accompanies the independently audited candidate. Supervisor acceptance
is recorded in `findings/recovery-m2-scoping-2026-09-15.md`.

## Scope and implementation

The candidate stays within the amended dispatch allowlist. It adds:

- Alembic `20260915_0005_instance_scope`, with an imported-metadata assertion for
  exactly the 19 runtime tables, orphan preflight, direct non-null instance FKs,
  `ON DELETE RESTRICT`, SQLite batch operations, retained versioned composite FKs,
  and reversible upgrade/downgrade behavior.
- `ScopedRepo(session, instance_id, team_id=None)` with required instance scope,
  scoped `select`, identity-checked `get`, and scope-checked `add`.
- Guarded runtime reads in `round/snapshot.py`, `round/runner.py`, and
  `simulation/service.py`, preserving the existing runner and M1 service behavior.
- A migration-backed two-instance pytest canary covering all 19 tables, distinct
  opaque pack tuples, cross-scope select/get rejection, unscoped-constructor
  rejection, cross-scope add rejection, and populated-instance delete refusal.
- A `check_*.py` schema guard and the required `QUALITY_PROTOCOL.md` gate entry.

No hierarchy model declarations, engine, auth, scheduling, registry, UI, pack,
scoring, or transition files were changed.

## Verification evidence

| Requirement | Result | Evidence |
|---|---|---|
| Exact runtime inventory | PASS | Migration and guard compare imported model metadata to the amended 19-table set; guard prints `19 non-null direct restrictive FKs declared`. |
| Direct restrictive FKs | PASS | SQLite reflection after migration reports one direct `fk_<table>_instance` FK for each of the 19 tables, each with `ondelete: RESTRICT`. |
| Orphan preflight | PASS | Migration queries every runtime table before adding constraints and aborts with table/sample IDs when orphan rows exist. |
| SQLite reversibility | PASS | `alembic upgrade head`, `downgrade -1`, `upgrade head`: all return code 0 on `sqlite+aiosqlite`. |
| Scoped repository and runtime reads | PASS | Focused runner and service regressions pass; source reads in the three dispatched runtime modules route through `ScopedRepo`. |
| New two-instance canary | PASS | `PYTHONPATH=. python3 -m pytest -q tests/test_instance_isolation.py`: **1 passed**. |
| Existing same-pack isolation regression | PASS | `PYTHONPATH=. python3 tests/check_instance_isolation.py`: all checks PASS, zero cross-instance reads. |
| Focused M1 runner regression | PASS | `tests/test_round_runner.py`: **11 passed**. |
| Focused M1 simulation regression | PASS | `tests/test_simulation_service.py`: **5 passed in 60.82s**. |
| Diff/allowlist | PASS | `git diff --check` clean; implementation paths match the dispatch allowlist. |
| Full gate | PASS | Cumulative `make check`: **663 passed in 401.61s**, all guards green, including the round instance-scope guard. |

The working tree is clean at the accepted candidate and its audit evidence.
