# Independent host-scope implementation review

2026-10-06 · Auditor `/root/contract_review` · Builder: parent readiness agent.
Contract: `handoffs/readiness-2026-10-06/host-scope-contract.md`, SHA-256
`c6da305e6a7ddb1a41ffd0d8d8e7cf308ee8257f8b01adfd4fda384d83e7c401`.
I reviewed that contract independently before implementation; I did not author the contract
or implement this change. No application code or shared database was modified by this audit.

## Verdict

**ACCEPT the bounded backend host-scope implementation. No Blocking or Functional finding.**
This accepts the migration, model, scoped CRUD/rollout changes and closing tests at the exact
candidate hashes in `findings/host-scope-2026-10-06/source-sha256.txt`; I independently ran
`sha256sum -c` and all nine entries, including CONTRACTS, returned OK.

This is not standalone merge/release approval. The separately assigned browser audit and
builder's full gate remain necessary for combined packet acceptance. Lifecycle activation,
reset, initialization, asset-key ambiguity, deployment uniqueness and member-kind semantics
remain explicitly excluded; their existing limitations are not closed here.

## Independently executed evidence

I created only `mis_sim_verify_host_scope_audit` on local PostgreSQL port44535. The destructive
migration fixtures and extra probes targeted that database or unique temporary SQLite files;
I did not use the builder's concurrency or browser database.

```bash
SECRET_KEY=host-scope-audit-only \
HOST_SCOPE_POSTGRES_URL=postgresql://readiness@127.0.0.1:44535/mis_sim_verify_host_scope_audit \
PYTHONPATH=backend /tmp/mis-sim-readiness-venv/bin/python -m pytest -q \
  backend/tests/test_host_scope_migration.py \
  backend/tests/test_host_scope_guard.py \
  backend/tests/test_host_scope_api.py
```

Result: **20 passed, zero skipped, 39.39s**. Warnings are existing passlib `crypt` and jose
`utcnow` deprecations, not failures. Full log:
`host-scope-audit/mis-sim-host-scope-independent-tests.log`.

The executed cases cover populated SQLite/PostgreSQL upgrade/downgrade/re-upgrade; invalid
insert/update/null/orphan inputs; separately planted malformed history with unchanged
pre-upgrade rows/schema/revision; same-scope host/team/instance cascades and preservation of
the other instance; same asset key across hosts; four structural guard mutations; removed
rollout/removal scope predicates; either missing ORM join equality; authenticated real-seed
create/rename/member add/read/remove/rollout; same-team access, other-team and other-instance
refusal, unassigned student and locked/paused/completed refusal.

I additionally authored and ran two audit-only scripts, retained with their logs under
`host-scope-audit/` (not application/test implementation):

- `host_scope_independent_probe.py`: **PASS PostgreSQL and SQLite**. Used host IDs101/202
  mapping to instances2/1, deliberately avoiding the builder fixture's aligned IDs. Compared
  contents of all32 application tables before/after upgrade, allowing only correctly
  parent-derived member scope; independently exercised eager and lazy ORM joins, deletion
  of a parent whose members were already loaded, additional cross-instance parent-ID
  updates, and exact populated downgrade/re-upgrade restoration.
- `host_scope_failure_probe.py`: **PASS both injected SQLite failures**. Raised before the
  first and second batch operations on the actual migration connection; verified FK
  enforcement restored to1 and `foreign_key_check` empty after each exception. The harness
  uses Alembic's per-migration transaction context, as real `run_migrations` does. This does
  not promise SQLite DDL rollback; the accepted contract explicitly requires backup and
  does not promise transactional recovery after DDL failure.

Both scripts were run with `SECRET_KEY=host-scope-audit-only PYTHONPATH=backend` and the same
venv Python. Their PostgreSQL fixture explicitly destroys only the auditor-owned database.
Replays require recreating/retaining that isolated database; never substitute a shared DB.

I independently reran both static guard entrypoints:

```text
instance-scope schema guard green: 19 non-null direct restrictive FKs declared
host scope guard green: two host tables, scoped member queries and composite ORM join
```

## Database and source inspection

A final read of the auditor database returned revision `20261006_0012`. PostgreSQL's actual
`pg_constraint` definitions included:

```text
fk_host_platform_member_instance          FOREIGN KEY (instance_id) REFERENCES simulation_instance(instance_id) ON DELETE CASCADE
fk_host_platform_member_platform_instance FOREIGN KEY (platform_id, instance_id) REFERENCES host_platform(id, instance_id) ON DELETE CASCADE
fk_host_platform_team_instance            FOREIGN KEY (team_id, instance_id) REFERENCES team(id, instance_id) ON DELETE CASCADE
host_platform_instance_id_fkey            FOREIGN KEY (instance_id) REFERENCES simulation_instance(instance_id) ON DELETE CASCADE
uq_host_platform_instance_identity        UNIQUE (id, instance_id)
uq_host_platform_member_asset             UNIQUE (platform_id, asset_key)
```

Source inspection confirms migration preflight precedes DDL/backfill, bounded offending IDs,
reflection of existing FK names, no permanent scope default, old single-column FKs replaced,
and named child-before-parent downgrade. Host member ORM relationships derive the composite
join; `passive_deletes="all"` preserves database cascades even for loaded collections.
Creation derives instance from authorized context; removal includes member ID, instance and
parent predicates; rollout includes member instance plus authorized parent/team predicates.
The existing response DTO is unchanged. The accepted scope text is now merged into CONTRACTS
immediately after the instance entry. No score, casepack or host-status transition was added.

The original nineteen-table guard is unchanged and still passes. New host-only guard is
picked up by Makefile's existing `tests/check_*.py` loop. Its source query check deliberately
has a narrow predicate-presence purpose; the authenticated API tests provide complementary
behavioral scope checks. I observed the requested copied-metadata/source mutation failures
and restored green checks through the independently rerun guard suite.

## Reconciliation

NCR-001 through NCR-004 in the preimplementation review were specification findings already
closed by the accepted bounded contract. The implementation evidence above now satisfies
those bounded database/query concerns. There is no new open implementation finding from
this audit. Parent must attach the separate browser verdict/full gate and preserve the
excluded QA-06 residue before claiming packet closure.
