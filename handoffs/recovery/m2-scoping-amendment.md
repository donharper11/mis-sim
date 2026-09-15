# M2 packet 2.2 amendment — complete runtime inventory and scope guard

Date: 2026-09-15  
Authority: supervisor, following the M2 reconciliation and the accepted 2.1
hierarchy (`5d6b573`)

This amendment supersedes the historical 13-table list and its stale path
assumptions. The builder follows this document where the original
`handoffs/2.2-instance-scoping/spec.md` differs.

## Complete runtime inventory

The packet covers exactly **19** tables. The first 16 are the 1.6 round-runtime
tables:

```text
team_state
arch_node
arch_edge
deployment_org_state
platform_service
org_unit
it_staff
governance_state
policy_decision
stakeholder_alignment
in_flight
decision_line
signal
debt_item
tco_forecast
round_result
```

M1 added the three versioned production tables:

```text
simulation_run_v1
simulation_sheet_v1
simulation_checkpoint_v1
```

The 2.2 migration must assert that this set matches the imported model metadata
before applying constraints. Any addition or omission is a STOP to the
supervisor; the builder does not silently widen the packet.

## Foreign-key treatment

Every one of the 19 tables receives a non-null `instance_id` foreign key to
`simulation_instance.instance_id` with `ON DELETE RESTRICT`.

`simulation_sheet_v1` and `simulation_checkpoint_v1` retain their existing
composite foreign keys to `(simulation_run_v1.instance_id,
simulation_run_v1.team_id)` and additionally receive the direct instance FK.
The composite key protects run ownership; the direct key makes the complete
runtime inventory visible to the platform-scope query and deletion checks.

The migration must be reversible on PostgreSQL and SQLite. Because the runtime
tables already exist, SQLite uses Alembic batch operations rather than a raw
`ALTER TABLE ADD CONSTRAINT`. No runtime table is recreated by 2.2's model
code, and no nullable relaxation or cascade is permitted.

Before adding constraints, the migration checks every runtime table for
`instance_id` values absent from `simulation_instance.instance_id`. A non-empty
orphan result aborts with the table name and sample IDs; 2.2 performs no
backfill, deletion, or guessed mapping. Clean migrated databases and explicitly
mapped deployments are the supported upgrade inputs. SQLite canary engines must
enable `PRAGMA foreign_keys=ON`; otherwise a delete-refusal check is invalid.

The ORM runtime models keep their portable integer columns; their database FKs
are introduced by this migration. This preserves the existing isolated SQLite
round/simulation test fixtures, which intentionally create runtime tables
without the platform hierarchy. The migration/schema checks, not a partial
`Base.metadata.create_all`, are authoritative for the FK invariant.

## Enforceable repository guard

Add `backend/app/repo/base.py` with:

```text
ScopedRepo(session, instance_id, team_id=None)
```

`instance_id` is required and validated. `select(model, ...)` always adds the
instance predicate and, when the model has `team_id`, the bound team predicate;
`get(model, identity)` rejects an identity whose first scope component differs;
`add(row)` rejects a row with a different `instance_id`. A caller may create a
second repository for another explicitly authorized scope, but there is no
unscoped constructor or fallback.

Refactor all runtime reads in `app/round/snapshot.py`, `app/round/runner.py`,
and `app/simulation/service.py` through this guard. This includes existing
`session.get(...)` calls and the M1 `select(SimulationRunV1)` path. The pure
engine remains untouched. Existing state-transition order and payloads must be
byte-identical; this packet changes access control and schema constraints only.

## Canary contract

Add a pytest canary at `backend/tests/test_instance_isolation.py` and retain the
existing same-pack `check_instance_isolation.py` regression. The new canary:

1. creates two 2.1 sections/instances with different opaque pack tuples and one
   team in each;
2. writes real runtime rows for both scopes, including one versioned M1 run,
   sheet, checkpoint, and round result;
3. proves `ScopedRepo` for A cannot select or get B's rows, and vice versa, for
   representative rows from all 19 tables;
4. proves an unscoped repository read raises the guard error;
5. proves deleting either populated `simulation_instance` raises an integrity
   error and leaves all state intact.

The migration/schema test must count all 19 direct instance FKs, verify every
`instance_id` remains non-null, and verify every delete rule is restrictive.
The canary is named in `QUALITY_PROTOCOL.md` and runs under `make check`.

## Explicit exclusions

No scheduling, auth, registry, browser work, score/scoring changes, pack content,
or hierarchy cardinality changes are allowed. Do not change the M1 transaction
semantics or add a second runtime table. If a runtime read cannot be moved
behind the guard without changing its result, stop with the exact call site and
do not improvise.
