# M2 packet 2.2 dispatch — instance scoping and isolation

Date: 2026-09-15
Supervisor base: `06506e4` (`build/north-star-foundation`)
Amendment: [`m2-scoping-amendment.md`](m2-scoping-amendment.md)

## Boundary

Packet 2.2 closes the database and repository scope seam for the **exact 19
runtime tables** named in the amendment. It adds restricted direct foreign keys,
an instance/team-scoped repository, and a real two-section isolation canary.

It does not implement scheduling, auth, registry, UI, new hierarchy entities,
scoring, pack content, or changes to transition semantics. The existing M1
simulation results and the existing same-pack isolation check must remain
behaviorally unchanged.

## Allowed paths

The builder may change only these paths:

* `backend/alembic/versions/20260915_0005_instance_scope.py` (new migration)
* `backend/app/repo/__init__.py` (new package marker)
* `backend/app/repo/base.py` (new `ScopedRepo`)
* `backend/app/round/snapshot.py` (route runtime reads through the guard)
* `backend/app/round/runner.py` (route runtime reads through the guard)
* `backend/app/simulation/service.py` (route runtime reads through the guard)
* `backend/tests/test_instance_isolation.py` (new two-instance canary)
* `backend/tests/check_instance_scope_schema.py` (new 19-table schema guard)
* `QUALITY_PROTOCOL.md` (name the new canary/schema checks in the pre-merge gate)
* `handoffs/2.2-instance-scoping/dod.md` (builder evidence only)

No other implementation, migration, test, casepack, frontend, or contract path
may change. In particular, do not edit the 2.1 hierarchy models or the M1
round/simulation model declarations; their portable columns remain independent
of platform metadata and the migration is authoritative for these FKs.

## Required evidence

Before committing, the builder must:

1. run the pre-flight against the actual 19-table metadata and current query
   call sites;
2. prove the migration adds exactly 19 direct `instance_id` FKs, all
   restrictive, and preserves non-null columns on SQLite and PostgreSQL
   compatible paths;
3. prove the repository has no unscoped constructor and rejects cross-scope
   `select`, `get`, and `add` operations;
4. run the new canary with two 2.1 sections, distinct pack tuples, populated
   representative rows from all 19 tables, and a populated M1 run/sheet/
   checkpoint/result chain;
5. show deletion of a populated instance raises an integrity error and leaves
   rows intact;
6. run the unchanged M1 simulation focused tests and the complete `make check`.

The canary must be a pytest file discovered by the normal suite. The schema
guard must be a `check_*.py` file so `make check` executes it independently.

## Stop conditions

Stop with exact evidence if the metadata inventory differs from 19, if SQLite
cannot represent the required reversible migration without a documented
alternative, if any runtime read requires changing a pure engine function, or
if preserving the M1 payload/digest requires changing transition semantics.
Do not weaken the guard to a convention or silently omit a table.

## Gate

This is a schema and cross-module contract packet. It requires an independent
spec/implementation audit before integration. The supervisor integrates only a
candidate accepted against this allowlist and the cumulative M1 gate.

