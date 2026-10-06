# Host scope integrity — bounded implementation contract

2026-10-06. Author: readiness implementation agent. Status: PROPOSED, awaiting fresh
contract reviewer. This supersedes only the scope portion of `next-contract.md`.
Tier: Heavy (cross-module persistence contract). No implementation before review acceptance.

## Purpose and verified preflight

[V] Host membership lacks instance scope. Host.instance_id and host.team_id independently
reference valid rows but do not require the team to belong to that instance.
[V] Team already declares `uq_team_instance_identity(id, instance_id)`.
[V] Migration head is `20261004_0011`; both existing host FKs and member->host use CASCADE.
[V] CONTRACTS requires a nonnull instance FK and scoped queries. RESTRICT is the historical
19-table guard's rule, not a global deletion rule. This packet preserves host CASCADE behavior.

## Frozen schema and migration

New migration `20261006_0012`, predecessor `20261004_0011`:

- Host: add `uq_host_platform_instance_identity(id, instance_id)`; replace the existing
  single-column team FK with `fk_host_platform_team_instance(team_id, instance_id)` ->
  `team(id, instance_id)`, ON DELETE CASCADE. Keep its direct instance FK and existing
  uniqueness/checks unchanged.
- Member: add `instance_id INTEGER NOT NULL`, no permanent default; backfill it from
  its parent host. Add `fk_host_platform_member_instance(instance_id)` ->
  `simulation_instance(instance_id)`, ON DELETE CASCADE. Replace old platform-only FK with
  `fk_host_platform_member_platform_instance(platform_id, instance_id)` ->
  `host_platform(id, instance_id)`, ON DELETE CASCADE.
- Preserve member primary IDs, parent IDs, asset keys, kinds, assignment rounds, host rows,
  existing unique(platform_id,asset_key), and all unrelated data. No key normalization,
  deduplication, kind restriction, assignment reassignment or lifecycle transition.
- Preflight BEFORE DDL/backfill: abort on host referencing missing instance/team, host/team
  instance mismatch, member without host. Report table and bounded offending IDs; never
  delete or repair malformed history automatically. Refusal must leave revision0011 and
  rows/schema unchanged. Supported online migration only; no offline data-backfill promise.
- Upgrade/downgrade work on PostgreSQL16 and SQLite with FK enforcement restored and checked.
  Use named reflected constraints/batch operations for SQLite, not speculative auto-generated
  PostgreSQL names. PostgreSQL DDL is transactional. SQLite preflight runs before any DDL;
  failure during DDL is not promised transactional rollback, so require a backup as usual.
- Downgrade removes new member FKs/column, restores platform-only CASCADE FK, restores
  host team-only CASCADE FK, then removes host identity unique. Retain original rows and
  primary keys. Exercise downgrade and re-upgrade with populated tables on both databases.
  If SQLite batch recreation requires temporarily disabled FKs, do so outside a transaction
  with enforcement restored on success/failure; assert foreign_key_check empty afterward.

## ORM/API contract

Model definitions match migration. Relationships use the composite member->host relationship
so eager/lazy loads join instance as well as platform_id; do not leave redundant platform-only
FK ambiguity. Explicit member queries carry instance_id, and removal also carries platform_id.
Creation derives instance_id from authorized parent/context (not client input). Rollout member
projection filters member.instance_id plus scoped parent/team. API response shape unchanged.
Current scoped parent selection and editable-run/locked-sheet checks remain mandatory.

Any expected integrity rejection returns a controlled domain response if reachable through
existing API inputs; never expose raw SQL. No new client-supplied instance fields.

## Guard inventory and explicit exclusions

Keep the original19 inventory/migration assertion intact. Add a separate metadata guard for
host_platform and host_platform_member: nonnull direct instance FK, exact composite FK column
pairs/CASCADE and host identity unique. Do not silently expand original19 and historical0005.
The complete migration verifier still expects32 application tables (no table added).
Grade2 and schedule2 retain their current contracts; schedule_team's composite indirect
instance FK is not changed. The guard must name this limited host extension, not claim a
complete repair of every later runtime table.

Explicitly excluded and owned in TODO QA-06: host activation/reset; instructor initialization;
asset-key validity, ambiguous multi-host assignment, member-kind semantics; grading/schedule
constraint changes. No scoring/engine changes. No claim that scope closure makes the entire
host feature or release acceptable.

## Implementation boundary

Allow: backend/app/models/host_platform.py; new Alembic migration; runtime_host_platform.py;
runtime_rollout.py; new focused tests under backend/tests; check_instance_scope_schema.py
(or a separately auto-discovered check_host_scope_schema.py); verifier migration-head
expectations if necessary; CONTRACTS/TODO/BATTLECARD/readiness documents and findings.
Existing host callers/tests may be adjusted only to supply explicit instance_id. No unrelated
UI, lifecycle, scoring, authoring or seed behavior changes in this packet.

## Acceptance and falsification

1. Populated0011 upgrade: two instances/teams/hosts/members, retained row identities and
   payloads, parent-derived scope, latest Alembic head,32-table inventory. Both database types.
2. Plants on each DB with FK enforcement ON: member valid-parent/wrong-instance, host
   valid-team/wrong-instance, missing/null member instance and missing parent all rejected.
   A valid same-instance row succeeds. Same asset key in different hosts remains allowed.
3. Each malformed-history preflight class is planted separately with enforcement temporarily
   disabled; migration fails before modification, revision/rows/schema unchanged. Restore
   enforcement afterward. Include member orphan, host instance orphan and team mismatch.
4. Scoped API: authenticated student can list/add/remove their member and see correct rollout
   projection. Same-instance other-team and cross-instance parent/member IDs cannot be read
   or mutated; unassigned student gets no team. Verify real populated members, not empty lists.
   Locked/paused/completed writes remain refused. Browser host proof rerun with fresh seed.
5. Delete a host/team/instance in a minimal allowed fixture: same-scope cascade remains as
   before; other-instance rows survive. A populated downgrade/re-upgrade retains all original
   rows, IDs and fields and restores intended constraints at each revision.
6. Run guards, focused regressions, `make check` with isolated PostgreSQL concurrency DB,
   fresh PostgreSQL migration verifier, lint/build and relevant browser proof. Record candidate
   source hashes. Independent audit reruns high-risk probes and must accept before merge.

## Dispatch verification map and feasible implementation route

Author freezes these test/guard homes (implementation may add cases within these files):

| Obligation | Command/evidence |
|---|---|
| Live preflight | SQLAlchemy inspector on isolated PostgreSQL: record0011 revision, host/member/team FK/unique inventory and row counts in `findings/readiness-2026-10-06/host-scope-preflight.md` |
| Populated upgrade/downgrade/re-upgrade, malformed-history refusal, CASCADE preservation | `PYTHONPATH=backend pytest -q backend/tests/test_host_scope_migration.py`; database parametrization SQLite and explicit disposable `HOST_SCOPE_POSTGRES_URL` |
| Invalid inserts AND updates, no-null, both host/team and member/parent mismatch | Same migration tests on both database types; transaction rollback after each plant |
| Authenticated CRUD/rollout and cross-team/instance/lock behavior | `PYTHONPATH=backend pytest -q backend/tests/test_host_scope_api.py` |
| Static schema/query boundary and planted-defect sensitivity | `PYTHONPATH=backend python backend/tests/check_host_scope_schema.py`; `PYTHONPATH=backend pytest -q backend/tests/test_host_scope_guard.py` |
| Browser | Fresh readiness seed then `MIS_SIM_DISPOSABLE=1 node frontend/tests/host-platform-proof.mjs`; UI create/detail/readonly/lock and authenticated API member addition, existing 720px screenshot |
| Full gate | `PATH=<venv>/bin:$PATH M5_POSTGRES_URL=<separate disposable DB> make check`; PostgreSQL verifier on its own empty verification DB; frontend lint/build |
| Independent acceptance | Auditor's dated findings with test logs, candidate hashes and original19 guard still passing |

API test playthrough: enroll studentA/teamA, teammate, studentB/teamB same instance, studentC
other instance and unassigned student. A creates host, renames it, adds a real initialized
asset, reads member and rollout assignment, removes it, reads empty membership. B/C cannot
rename/add/remove using A's IDs or expose A's member in scoped reads. Unassigned student sees
no team. Repeat writes after locked/paused/completed to require409. This is the explicit
rename/remove acceptance; the existing browser UI has no rename/remove controls.

Guard sensitivity is distinct from malformed data: tests mutate a copied metadata definition
to remove instance column/non-null/direct FK/composite FK and require guard failure; a source
query checker or behavioral instrument must fail when explicit member instance predicate is
removed from rollout/removal. Do not mutate live app source permanently. ORM member load
join must contain platform AND instance equality; removing either must fail its probe.

Feasible route: named-constraint reflected Alembic batch copies with parent unique created
before composite member FK, child constraints removed before parent unique on downgrade;
preflight raw SQL on existing tables, then backfill; derive ORM join from sole composite
member-parent FK; caller supplies authorized instance. Inspect emitted SQLite PRAGMA and
PostgreSQL constraints in tests instead of assuming metadata proves migration execution.

Insert into CONTRACTS after the existing instance_id entry (only after accepted build):

> HostPlatformMember has nonnull instance_id. Host (team_id,instance_id) references Team
> (id,instance_id); member (platform_id,instance_id) references host (id,instance_id).
> Both host and member directly reference SimulationInstance by instance_id. These host
> relationships use ON DELETE CASCADE, preserving the original host deletion behavior;
> the historical nineteen-table RESTRICT contract remains separate. API member writes derive
> instance_id from authorized context; all member queries and ORM parent loads constrain it.
> Asset-key assignment and lifecycle semantics are unchanged by this scope migration.

DoD: all map rows pass with no silently skipped required PostgreSQL case; invalid-history
refusals preserve pre-upgrade schema/data, valid upgrades/downgrades preserve identities,
zero cross-team/instance exposure, matching API shape, independent acceptance recorded. Any
failed row stays open with an owner; no claim of readiness closure based only on schema PASS.
