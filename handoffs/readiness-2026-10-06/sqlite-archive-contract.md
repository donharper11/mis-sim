# SQLite archive correction — proposed implementation contract

2026-10-07 · Author root · READY-AUD-BE-002 · PROPOSED, awaiting independent review.
Implementation follows completion of the instructor-start gate. User authorized continuing
prioritized work; this is a correction to an existing lifecycle feature, not a new policy.

## Verified basis and bounded change

[V] Independent [preflight](sqlite-archive-preflight-review.md) inspected real head0013
SQLite and PostgreSQL schemas. SQLite still has the four-status CHECK from0004;0010 changes
only PostgreSQL. Current ORM and archive API already support `archived`. Existing API tests
use create_all and therefore miss the live migrated-schema defect.

Add revision `20261007_0014`, successor `20261006_0013`. Do not edit historical migrations.
SQLite online upgrade reflects the existing `simulation_instance` table and replaces only
named `ck_simulation_instance_status` with the canonical five-status constraint:
`status IN ('setup','active','paused','completed','archived')`. Do not recreate from current
ORM metadata. Preserve every column/default/PK/unique/FK/index and all application rows.
PostgreSQL already has the five-status constraint: verify it and do not rewrite the table.
No other dialect is claimed supported by this repair. Offline SQL generation is refused
with a clear message because real schema/data inspection is necessary.

Accept exactly the known four-value SQLite constraint or the already-correct five-value
constraint (the latter is a no-op). Reject missing/unexpected status constraints and unknown
stored statuses before destructive DDL. Do not silently accept a widened arbitrary domain.
Preserve original instance statuses, settings, bindings, timestamps and identifiers; no
unarchive, deletion, score recalculation, seeded migration data or API contract change.

## SQLite lifecycle and downgrade

The parent table has dependent foreign keys. Reserve a dedicated migration connection;
turn SQLite FK enforcement off outside any transaction, assert it is off, and restore its
original state on both success and failure. Do not drop/recreate a referenced parent with
FK enforcement active. After successful rebuilding, require empty foreign_key_check before
claiming success. Follow the inspectable0012 handling pattern only where it satisfies these
requirements. Do not promise atomic rollback for arbitrary SQLite DDL failure; tests inspect
actual resulting state, and an incomplete migration must fail rather than claim head0014.

**Author decision:**0014→0013 downgrade is a documented no-op on both engines. This is a
retained correction matching current ORM and the PostgreSQL predecessor, not restoration of
the broken SQLite CHECK. Archived rows and every other row survive downgrade and re-upgrade.
Do not claim arbitrary older downgrade safety; historical0010 PostgreSQL downgrade has its
own narrower domain and is outside this packet.

## Acceptance and falsification

1. Real populated0013→0014 on SQLite and PostgreSQL, never create_all. Populate two differently
   bound instances, identities/teams/roster, host/member, schedules/participants, modern
   run/sheet/checkpoint, legacy runtime/results and grading. Compare all32 application-table
   contents and reflected schema before/after; SQLite status CHECK is the sole intended
   schema difference and Alembic version becomes0014. Verify new identity allocation works.
2. All five status values succeed on migrated DBs; unknown/null statuses fail. Existing
   round checks, unique keys and direct/composite FK scope constraints still reject defects.
   Fresh install and already-repaired five-value predecessor are also covered.
3. Authenticated migrated API completed→archived succeeds; only status changes. Preserve
   timestamps/results/foreign scope, hide archived instance in setup and retain grade export.
   Wrong confirm422, student/TA/wrong owner403, noncompleted409. Browser exercises actual
   Archive confirmation against persisted completed demo results with no unexpected errors.
4. No-op downgrade and re-upgrade preserve schema correction and all data with/without
   archived rows. Inject batch failure; inspect same-connection FK restoration and revision.
   Unexpected schema preflight refuses without row/schema/revision mutation.
5. Run the SQLite archive assertion on predecessor0013 and observe the actual CHECK refusal;
   remove the replacement in an isolated0014 copy and demonstrate closing test failure.
6. Full make check with all PostgreSQL targets, frontend lint/build, fresh PG verifier at0014,
   independent backend/browser reviews, source hashes and register reconciliation. Keep
   seeded technical acceptance separate from later live-human pilot.

## Files and handoff

Implementation: new Alembic0014 file; only necessary migration helpers/env changes if tests
prove required. No production lifecycle behavior changes are intended. Tests:
`backend/tests/test_archive_migration.py` and migrated lifecycle/API coverage; reusable browser
proof for completed demo archive. Update verifier expected head, README/BATTLECARD/TODO,
CONTRACTS only if required, findings register and dated archive report. Keep32 model-table
inventory unchanged. Dedicated destructive PostgreSQL test target must have a guarded local
verification prefix, never browser/application/production data. Root owns builder work;
fresh independent agents own review and findings.
