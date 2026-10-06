# Host scope migration and independent acceptance

2026-10-06. Local candidate on `build/readiness-2026-10-06`; not merged or deployed.
Preserves preexisting readiness work and the approved assignment/lifecycle semantics.

## Delivered

Migration `20261006_0012` backfills nonnull member.instance_id from the actual parent, adds
member/parent and host/team composite foreign keys, and preserves the prior CASCADE behavior.
Model and queries use this scope, including ORM relationship loads, removal and rollout.
No new API response fields, scoring fields, tables or assignment semantics were introduced.

Before writes, migration rejects orphaned hosts/members and host/team mismatches. Populated
upgrade/downgrade/re-upgrade preserves identities and fields. PostgreSQL remains transactional;
SQLite batch changes restore FK enforcement in success/failure paths. The accepted contract
explicitly does not promise SQLite DDL rollback after a mid-migration failure: retain a backup.

The existing nineteen-table guard stays unchanged. A separate host guard detects missing
scope/nullability/FKs, broken composite ORM joins and removed explicit query predicates.
Tests demonstrate failure on planted defects; an ordinary green run alone is insufficient.

## Evidence

- [Approved contract](../handoffs/readiness-2026-10-06/host-scope-contract.md) and
  [dispatch review](../handoffs/readiness-2026-10-06/contract-independent-review.md).
- [Backend independent audit — ACCEPT](../findings/readiness-2026-10-06/host-scope-independent-review.md):
  20 tests, no skips; additional PostgreSQL/SQLite probes with nonaligned parent IDs, all 32
  table contents, loaded-parent ORM cascades, actual constraints and injected DDL failure.
- [Browser independent audit — PASS](../findings/readiness-2026-10-06/host-scope-browser-review.md):
  fresh0012 database, real host CRUD/member reads, teammate access, other-team/cross-instance
  refusal, read-only rollout modal, lock and 720px layout; positive diagnostics empty.
- Builder focused gates: 19 migration/guard cases plus 1 authenticated API scenario passed.
  [Logs and reviewed hashes](../findings/host-scope-2026-10-06/).
- Fresh PostgreSQL verifier:32 application tables plus Alembic at 0012; six committed results.
- Full gate: **816 passed, no skips, 196 warnings, 730.06s; all guards green.**
  Both dedicated PostgreSQL targets were supplied. Frontend lint/build pass.
  Logs: `../findings/host-scope-2026-10-06/full-check.log`, `frontend-lint.log`,
  `frontend-build.log`. Reviewed candidate hashes all still match.

## Reproduction

Use the dependency setup in `readiness-runbook.md`. Create two distinct disposable PostgreSQL
verification databases. The host fixture DROPS public schema and validates a dedicated
`mis_sim_verify_host_scope_` name; the concurrency fixture is separately destructive.

```bash
HOST_SCOPE_POSTGRES_URL='<loopback URL / mis_sim_verify_host_scope_SUFFIX>' \
M5_POSTGRES_URL='<different disposable concurrency URL>' \
PATH=/tmp/mis-sim-readiness-venv/bin:$PATH make check
```

All required PostgreSQL cases must execute in the final gate; default developer runs skip the
five host-migration PostgreSQL parameter cases unless the dedicated URL is supplied.
The verifier and browser seed need their own new empty databases, never either test target.

## Remaining work

READY-001 scope integrity is **CLOSED for this local candidate**: implementation,
independent backend/browser audits and full gate all pass. READY-002 activation/reset, READY-003 instructor start, READY-004 performance,
and READY-AUD-BE-002 SQLite archive migration remain open. Scope constraints do not validate
asset identity or resolve multi-host assignment ambiguity. No class/production acceptance.

The inspected next boundary is recorded in
[host-lifecycle-preflight.md](../handoffs/readiness-2026-10-06/host-lifecycle-preflight.md),
including scheduler round provenance, historical pending metadata, reset inventory and
minimal harness schemas. Lifecycle still needs an independently reviewed dispatch contract.
