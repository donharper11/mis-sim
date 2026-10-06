# Independent backend readiness review — 2026-10-06

Auditor: `/root/backend_review`, fresh reviewer; not the author or builder. Reviewed the uncommitted tree against baseline `0a535ba`. Read GOVERNANCE, QUALITY_PROTOCOL, SPEC_PROTOCOL, CONTRACTS, the dated readiness report, changed backend implementation/tests and relevant service, migration and auth consumers. No implementation edits were made by this reviewer. The parent fixed the seed defect after receiving this reviewer's reproducer.

**Verdict: ACCEPT the bounded backend readiness corrections after the seed re-review; REJECT a claim of complete backend/cohort readiness.** The original new seed defect is closed. Existing host scope/lifecycle gates remain open, and a preexisting SQLite archive defect is newly recorded. This is neither merge approval nor production acceptance. Browser and full-gate evidence are owned by the parent review and are not inferred from these API checks.

## Independently executed evidence

- `/tmp/mis-sim-readiness-venv/bin/python -m pytest tests/test_rollout_runtime_api.py tests/test_simulation_service.py tests/test_health_readiness.py -q`, from `backend`: **11 passed, 11 warnings, 105.52s**. Covers authored rollout metadata, concrete host assignment precedence, no-team fallback rejection, uninitialized/locked host mutations, budget parity/no expensive quote, service revision/locking and HTTP 503 outage response.
- `/tmp/mis-sim-readiness-venv/bin/python -m pytest tests/test_dashboard_api.py tests/test_postgres_runtime_check.py tests/test_platform_runtime_api.py -q`, from `backend`: **4 passed, 5 warnings, 1.94s**. Dashboard fixture is legacy state; the independent modern dashboard probe below supplements it.
- Additional probes against this reviewer's migrated disposable SQLite database: budget read preserved an identical complete SQL dump; wrong instance and wrong team both produced `not_found`; poisoned run pack digest, checkpoint state digest and malformed persisted command were rejected; modern dashboard returned the same capital value `400000`; paused/completed host edits returned 409; cross-instance host read returned 403. Evidence: `backend-independent-probe.log`. The probe deliberately changed/restored persisted fields on the disposable fixture; it did not change implementation.
- The same independent probe demonstrated reset residue and inspected actual member columns, detailed below. Its initial archive attempt and traceback are retained in `backend-independent-probe-initial.log`.
- Fixed fresh seed independently executed against **both SQLite and PostgreSQL**, then independently read back. Both contain two active round-one instances and all four draft runs at `current_round=1, advanced_round=0`. Both refuse a repeat invocation with existing users. Evidence: `backend-independent-seed-fixed.log`, `backend-independent-pg-seed.log`, `backend-independent-db-readback.log`.
- PostgreSQL verifier independently executed on a separate empty database in this reviewer's own loopback-only cluster. It passed migrations, all 32 model tables plus Alembic, and six committed historical rounds. Independent SQL readback returned **33 tables**, **6 results / rounds 1–6**, and head **20261004_0011**. Evidence: `backend-independent-pg-verifier.log`, `backend-independent-db-readback.log`. This proves historical persistence, not decision-driven pedagogical acceptance. Invocation required `SECRET_KEY=local-independent-audit-only`; an initial omitted-settings attempt failed before migrations and was corrected.

PostgreSQL reproduction commands (the dedicated audit cluster was created for this review):

```bash
SECRET_KEY=local-independent-audit-only /tmp/mis-sim-readiness-venv/bin/python backend/scripts/check_postgres_runtime.py --database-url postgresql+asyncpg://audit:audit@127.0.0.1:48183/mis_sim_verify_backend_audit
/tmp/mis-sim-readiness-venv/bin/python backend/scripts/seed_readiness_demo.py --database-url postgresql+asyncpg://audit:audit@127.0.0.1:48183/mis_sim_browser_backend_audit
```

These are disposable local audit-only identities, not production credentials. Populated targets intentionally refuse reseeding/reverification; use newly created database names to reproduce the fresh path.

## Findings and re-review

### READY-AUD-BE-001 — Functional, CLOSED after independent re-review

**Original defect:** the new readiness seed advertised SQLite support but failed against a completely fresh allowed SQLite URL. Original `backend/scripts/seed_readiness_demo.py:62–69` kept a Session open while invoking `SimulationService.initialize`, which owns a separate transaction. After the first instance, the outer Session autoflushed its status/round updates while processing the second instance and retained SQLite's writer lock. The nested initialize failed with `sqlite3.OperationalError: database is locked` at `BEGIN IMMEDIATE` (`backend/app/simulation/service.py:149`). It left only `(instance=1, team=1)` and `(instance=1, team=2)` runs, with both instances still setup/round zero. Because user creation had already committed, a retry refused the population.

**Original executable reproducer:**

```bash
/tmp/mis-sim-readiness-venv/bin/python backend/scripts/seed_readiness_demo.py --database-url sqlite+aiosqlite:////tmp/mis_sim_browser_backend_seed_repro_20261006.db
```

Original failing output is preserved in `backend-independent-seed.log`. This closing check was therefore demonstrated to fail on the original implementation.

**Correction independently reviewed:** current `backend/scripts/seed_readiness_demo.py:62–78` materializes instance/pack/team work, closes the reader Session, initializes every team without an outer writer, then updates instance statuses in a separate final transaction. Fresh SQLite `/tmp/mis_sim_browser_backend_fix_audit_20261006.db` and fresh PostgreSQL `mis_sim_browser_backend_audit` both succeeded and persisted all four runs/two active instances; second invocations refused. Closure applies to this transaction-lock defect, not every possible interrupted-seed recovery scenario.

### READY-AUD-BE-002 — Functional, OPEN; owner: platform/migrations

**Preexisting, not introduced by the readiness diff.** A fresh migrated SQLite database rejects `SimulationInstance.status = 'archived'`, despite the model/application supporting archive. `backend/alembic/versions/20261002_0010_add_archived_status.py:22–34` modifies the CHECK constraint only for PostgreSQL; its SQLite branch is a no-op. The comment that the constraint is enforced at the ORM level does not remove the old physical CHECK. An independent update at head `20261004_0011` failed with `IntegrityError: CHECK constraint failed: ck_simulation_instance_status`; traceback and SQL are in `backend-independent-probe-initial.log`.

Executable closing check, against a **fresh migrated disposable SQLite seed** (the transaction rolls back):

```bash
python3 - <<'PY'
import sqlite3
c = sqlite3.connect('/tmp/mis_sim_browser_backend_fix_audit_20261006.db')
try:
    c.execute("update simulation_instance set status='archived' where instance_id=1")
    assert c.execute('select status from simulation_instance where instance_id=1').fetchone() == ('archived',)
finally:
    c.rollback()
    c.close()
PY
```

A model-created test schema does not exercise this migration gap. Remains separately owned; not folded into the proposed host-scope migration.

### READY-001 — Existing Blocking governance gate, OPEN; owner: next Heavy scope packet

Confirmed `HostPlatformMember` has no `instance_id` in both metadata (`backend/app/models/host_platform.py:70–83`) and the actual freshly migrated SQLite schema. Column readback: `['id', 'platform_id', 'asset_key', 'member_kind', 'assigned_round']`. `backend/tests/check_instance_scope_schema.py:14–29` checks only the original 19 core runtime tables. The expanded verifier's `backend/scripts/check_postgres_runtime.py:121–125` checks scope type/nullability only **when** the column exists; its 32-table inventory pass therefore does not establish the host scope contract. No cross-instance API leak was reproduced: the changed queries scope through the authorized host parent and the API negative returned 403. The direct scope/relational contract remains unfulfilled.

Executable closing check after the separately reviewed scope work:

```bash
cd backend
PYTHONPATH=. /tmp/mis-sim-readiness-venv/bin/python - <<'PY'
from app.models.host_platform import HostPlatformMember
column = HostPlatformMember.__table__.c.get('instance_id')
assert column is not None and not column.nullable
PY
```

This is only the minimal formerly failing invariant; relational migration/backfill/cross-instance checks remain required by that Heavy packet.

### READY-002 — Existing Functional lifecycle gate, OPEN; owner: host lifecycle packet

Independently reproduced reset residue. `backend/app/services/platform.py:414–462` deletes simulation, scheduling and grading state but not host tables. After creating two host platforms, changing the disposable instance to setup, calling `reset_instance`, and committing, authenticated `GET /api/instances/1/host-platforms` still returned **two platforms** (`backend-independent-probe.log`). The existing activation gap is also visible in `backend/app/api/runtime_host_platform.py:184–197`: creation sets pending/next-round activation, but these changed endpoints do not reconcile advancement. No claim is made that presentation metadata affects the scorer.

Closing check: a disposable seeded fixture creates a platform/member, resets its setup-status instance, commits, and asserts the scoped host/member counts are zero and authenticated host GET returns `platforms=[]`. The current independent probe demonstrated the inverse (two residual platforms). The lifecycle packet must additionally exercise actual advancement into activation.

## Remaining gates and limits

- Full final-tree `make check`, browser auth/navigation/controls/rollout playthrough and browser diagnostics belong to the parent audit. This reviewer did not accept builder logs as substitutes, and did not duplicate the full gate.
- New seed fix received real migration/seed/readback/refusal checks on both database backends. Follow-up independent review inspected and ran the newly added `backend/tests/test_readiness_seed.py`: **1 passed in 23.37s** using `/tmp/mis-sim-readiness-venv/bin/python -m pytest tests/test_readiness_seed.py -q` from `backend`. It invokes the actual seed subprocess against a unique disposable SQLite database, asserts four round-one runs/two active instances, and verifies a refused second invocation leaves the exact SQL dump unchanged. Persistent regression coverage is now present; the earlier 15 focused tests had passed while the original seed was broken.
- PostgreSQL host mutation concurrency was inspected through the shared run-row `FOR UPDATE` boundary (`backend/app/api/runtime_host_platform.py:91–103`), but not independently stress-tested here. Sequential lock denial is covered by executed tests. SQLite does not implement PostgreSQL row locks.
- READY-003 instructor runtime initialization, READY-004 performance, observed competent/negligent six-round acceptance, and production/restore/host-specific operations remain outside this bounded backend acceptance. The PostgreSQL verifier does not close them.
- The backend working tree remains uncommitted; no pushed, merged, deployed or shipped-commit claim is made.
