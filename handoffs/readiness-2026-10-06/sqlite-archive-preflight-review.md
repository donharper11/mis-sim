# SQLite archive CHECK repair — independent preflight

Date:2026-10-07 · Reviewer `/root/contract_review` · Queue:READY-AUD-BE-002.
Read-only source/database inspection; no application/test edit or migration execution.
This note is evidence and a proposed boundary for the next author, not dispatch approval.

## Verified defect and why the old tests missed it

`20260915_0004_platform_hierarchy.py:75` created `ck_simulation_instance_status` with four
values:setup,active,paused,completed. `20261002_0010_add_archived_status.py:20–31` replaces it
with the five-value vocabulary **only on PostgreSQL**. Its comment claiming SQLite's CHECK
is enforced by the ORM is incorrect:declaring the new ORM constraint does not replace a
CHECK already stored in the migrated database. No successor through0013 repairs it.

I inspected existing databases without mutation:

- SQLite `/tmp/pytest-of-ubuntu/pytest-57/test_public_start_routes_autho0/start.db`, opened with
  `sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)`:revision `20261006_0013`,33 tables
  including Alembic,empty `PRAGMA foreign_key_check`,and actual stored SQL:
  `CONSTRAINT ck_simulation_instance_status CHECK (status IN ('setup','active','paused','completed'))`
  (whitespace normalized here). Full output: `archive-preflight/sqlite-head-schema.txt`.
- PostgreSQL auditor-owned `mis_sim_verify_instructor_start_review` on port44535:revision0013;
  `pg_constraint` already reports the five-value CHECK including archived. Full read-only
  psql query/output: `archive-preflight/postgres-head-schema.txt`.

The current model declares all five values (`models/platform.py:80`), and
`test_lifecycle_api.py:44–59` creates tables from current metadata instead of Alembic. Its
archive test therefore exercises a schema that migrated SQLite installations do not have.

The production service (`services/platform.py:426–435`) accepts only completed instances,
sets status=archived and flushes. The instructor API (`api/instructor.py:893–916`) verifies
confirmation and ownership,commits on success and rolls back errors. Course setup excludes
archived instances (`:184–186`); grade export must remain available (existing test at
`test_lifecycle_api.py:240–274`). The intended behavior is already settled; no new archive
status,scoring rule or client/API payload is needed.

## Smallest proposed repair

Add a NEW successor of current head0013 (prospective0014; author chooses filename/revision),
without rewriting0010 or historical audit evidence. On SQLite,reflect and batch-recreate
`simulation_instance`,replacing only the named status CHECK with the already canonical
five-value condition. PostgreSQL already has that condition; preserve it and every row.
Do not rebuild from the current ORM declaration:historical column widths/names/defaults,
pack_digest,unique keys and FK metadata must remain those of the actual table.

Require exact table/constraint preflight and reject an unexpected schema before destructive
DDL. Author should explicitly choose whether an already-repaired five-value SQLite CHECK is
recognized as a no-op; do not silently accept arbitrary wider/missing constraints. An online
migration is the natural supported route because SQLite reflection and data checks require
an actual connection; do not advertise offline SQL output without separately specifying it.

This repair should not change lifecycle service semantics. API/browser regressions must use
an Alembic-migrated fixture so the original failure cannot be hidden by create_all again.
A small archive-specific schema guard or migrated test must fail if a SQLite migration claims
success while retaining the old CHECK; existing metadata-only model checks are insufficient.

## Preservation risks

`simulation_instance` is a heavily referenced parent. SQLite batch recreation drops its old
table:with FK enforcement enabled this can reject the operation or trigger destructive
cascades through teams,hosts,schedules and their children. Disable FK enforcement on the
actual migration connection **outside a transaction**,assert that it changed,then restore
it on success and every failure path; require an empty foreign_key_check. Existing0012's
SQLite context pattern is an inspectable precedent,not permission to blindly reuse code.
Document the normal backup/recovery requirement rather than promise transactional SQLite DDL
rollback. PostgreSQL should remain transactionally unchanged by this correction.

Compare all32 application-table contents,not just parent row counts. Preserve IDs,roster,
pack binding/digest,settings,timestamps,statuses and every result/checkpoint payload byte or
canonical JSON value. Preserve parent PK,the two instance unique keys,section FK,round
checks,all indexes and child composite/direct constraints. Check a subsequent insert still
gets a valid new identity; do not assume AUTOINCREMENT/sqlite_sequence exists (the inspected
SQLite table uses INTEGER PRIMARY KEY without an explicit AUTOINCREMENT clause).

## Downgrade is an author decision

Two defensible contracts exist; do not leave the builder to choose:

1. **Correction retained:**0014→0013 downgrade is a documented no-op on the repaired CHECK,
   preserving archive support and all rows. This does not claim to restore the defective
   historical SQLite schema; it matches the current model and PostgreSQL predecessor.
2. **Exact SQLite predecessor shape:**restore the four-value SQLite CHECK only if no archived
   rows exist. Preflight archived IDs and refuse **before DDL/revision changes** when present;
   never delete,relabel or unarchive data automatically. PostgreSQL0014→0013 is a no-op,
   because its predecessor already supports archived. Test clean downgrade/re-upgrade and
   refused downgrade separately.

An additional historical limitation exists:0010→0009 on PostgreSQL narrows to four values
without an archived-row preflight. A0014 repair must not claim arbitrary deep downgrade is
safe. Keep that limitation explicit or dispatch a separately authorized historical-policy
change; the narrow SQLite repair need not rewrite old migration0010.

## Required acceptance

- Start from actual populated0013,not create_all,on both SQLite and PostgreSQL. Two differently
  bound instances with teams/roster,host/member,schedule participants,modern checkpoints/
  sheets/results,legacy runtime and grading sentinels. Snapshot all32 tables and reflected
  constraints. Upgrade preserves every row; the only intended schema delta is SQLite's
  widened status CHECK; version advances and inventory stays32 application tables.
- On migrated SQLite and PostgreSQL,each canonical status is DB-valid and unknown/null status
  remains rejected. Existing positive-round and identity/FK constraints still reject planted
  defects. This must distinguish a live SQLite database from merely current model metadata.
- Real authenticated API:completed→archived succeeds,identity/timestamps/results unchanged;
  disappears from setup listing,grade export remains available. Wrong confirmation422,
  wrong instructor/TA/student403,noncompleted409; no cross-instance changes. Independently
  replay the visible Archive confirmation in a real browser with persisted completed results.
- Observe the migrated archive assertion fail at0013 SQLite and pass at successor head;
  intentionally omit CHECK replacement in an isolated migration copy and require the new
  closing check to fail. No permanent source mutation.
- Verify selected downgrade behavior with archived rows and without them; re-upgrade preserves
  all data. For exact-shape downgrade,refusal leaves revision,rows and schema unchanged.
- Inject a SQLite batch-operation failure and verify FK enforcement restoration on the SAME
  migration connection; inspect resulting state instead of relying on an exit status. Fresh
  PG verifier,full checks and independent backend/browser audit still apply.

The task is a bounded correction to an existing published status vocabulary. Do not broaden
it into archive/unarchive policy,reset,start,grades,or new scored behavior. Root should record
the chosen downgrade/support boundary in the contract before implementation.

Read-only PostgreSQL inspection command used:

```bash
psql -h127.0.0.1 -p44535 -Ureadiness -dmis_sim_verify_instructor_start_review \
  -c 'SELECT version_num FROM alembic_version' \
  -c "SELECT conname,pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid='simulation_instance'::regclass ORDER BY conname"
```

SQLite inspection used its read-only connection to execute `SELECT version_num FROM
alembic_version`, `SELECT sql FROM sqlite_master WHERE type='table' AND
name='simulation_instance'`, table count excluding SQLite internal names,and
`PRAGMA foreign_key_check`. Neither database was altered.
