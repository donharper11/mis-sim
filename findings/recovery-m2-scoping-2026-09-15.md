# M2 packet 2.2 instance-scoping independent audit

- Candidate: `da339c5fb8b2fdccc5060e64608c76d0c459d318`
- Implementation: `03e1233ff2383b694aec851dcd10e3554152f73f` plus allowlisted runner guard correction `da339c5`
- Dispatch base: `35a7f3c`
- Verdict: **PASS**

## Scope

The cumulative implementation and evidence changes from the amended dispatch
base are exactly the ten allowlisted paths: the scope migration, repository
package and guard, the three dispatched runtime modules, the two canary/schema
tests, `QUALITY_PROTOCOL.md`, and `handoffs/2.2-instance-scoping/dod.md`.
`git diff --check` passed and the candidate worktree was clean before this
report was created. No hierarchy models, engine, auth, scheduling, registry,
UI, pack, or transition files changed.

## Independent evidence

- `backend/tests/check_instance_scope_schema.py` passed and reported the exact
  19-table inventory with 19 non-null direct restrictive FK declarations.
- `backend/tests/test_instance_isolation.py`: **1 passed**. The canary
  migration-created two instances with distinct pack tuples, populated one
  representative row in every runtime table, rejected cross-scope select/get
  and add operations, rejected an unscoped repository, and refused deletion
  of a populated instance while preserving its state.
- On a fresh SQLite database, Alembic `upgrade head`, `downgrade
  20260915_0004`, and `upgrade head` all succeeded. Final head was
  `20260915_0005`; reflection showed direct `ON DELETE RESTRICT` FKs on the
  runtime tables, including the additional direct FKs on the versioned run,
  sheet, and checkpoint tables while their existing composite run FKs remained.
- A planted orphan (`team_state.instance_id=999`) caused the 0005 migration
  to abort with `RuntimeError: M2 2.2 orphan instance_id values in team_state:
  [999]`; no backfill or deletion was attempted.
- `backend/tests/test_round_runner.py`: **11 passed**.
- `backend/tests/test_simulation_service.py`: **5 passed in 61.83s**.
- Existing `backend/tests/check_instance_isolation.py` passed all checks,
  including zero cross-instance reads and per-instance immutable results.
- Source inspection found all runtime read statements in `round/runner.py`,
  `round/snapshot.py`, and `simulation/service.py` constructed through
  `ScopedRepo`; no direct runtime `session.get` or bare unscoped `select`
  remains. The repository requires a positive `instance_id`, applies optional
  team scope, validates scoped identities, and rejects cross-scope rows on
  `add`.

The DoD-only successor `3471e4d` adds the required builder evidence without
changing implementation behavior. The cumulative candidate satisfies the
amended 19-table FK, orphan-policy, repository-guard, canary, and regression
contracts. No implementation or shared contract files were modified by this
audit.


## Final successor validation — `da339c5fb8b2fdccc5060e64608c76d0c459d318`

**Verdict remains PASS.** The successor changes only the allowlisted
`backend/app/round/runner.py`, making the existing repository instance
predicate explicit at the seven static-guard call sites. No other path changed.

`backend/tests/check_round_invariants.py` passed all guards: I1, I3, I4, I5,
I6, I7, and I9. `git diff --check` passed and the candidate was clean before
this report update.
