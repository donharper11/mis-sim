# Reproducing the October readiness checks

Updated 2026-10-06. Use a disposable local database. Commands below assume the repository
root, Python 3.12, Node 22 and PostgreSQL 16 binaries. Production host details and acceptance
are still pending; this runbook does not claim a deployed release.

## Dependencies and baseline checks

```bash
python3.12 -m venv /tmp/mis-sim-readiness-venv
/tmp/mis-sim-readiness-venv/bin/pip install -r backend/requirements-dev.txt
/tmp/mis-sim-readiness-venv/bin/pip check
PATH=/tmp/mis-sim-readiness-venv/bin:$PATH make check
npm --prefix frontend ci
npm --prefix frontend run lint
npm --prefix frontend run build
```

`make check` includes pytest, all `check_*.py` guards and validator fixtures. The explicit
PostgreSQL concurrency test is skipped unless `M5_POSTGRES_URL` is supplied. That test drops
its target's public schema: give it a **separate disposable database**, never the browser,
restore, application or production database.

## PostgreSQL and browser seed

Use the isolated cluster recipe in `backend-development.md`. Keep its generated connection
values in your local shell; do not copy real credentials into reports. Create three separate
empty databases: `mis_sim_verify_<suffix>` for the migration/persistence verifier,
`mis_sim_browser_<suffix>` for browser actions, and another `mis_sim_verify_<suffix>` for
concurrency. Create a fourth empty database if rehearsing restore.

```bash
# Supply the local URLs you just created. Never use the repository .env default.
export READINESS_DATABASE_URL='postgresql+asyncpg://USER:PASSWORD@127.0.0.1:PORT/mis_sim_browser_SUFFIX'
export SECRET_KEY='choose-a-local-rehearsal-secret'
/tmp/mis-sim-readiness-venv/bin/python backend/scripts/seed_readiness_demo.py --database-url "$READINESS_DATABASE_URL"
```

The seed migrates to head, refuses an existing user population, creates the two-section
cohort and demo identities, and initializes four teams at round 1. It does not drop or
reset data. `--schedule` on the historical demo seed advances some rounds and is not a
substitute for this round-one browser fixture.

In one terminal:

```bash
cd backend
DATABASE_URL="$READINESS_DATABASE_URL" /tmp/mis-sim-readiness-venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8211
```

In another terminal, run `npm --prefix frontend run dev -- --host 127.0.0.1`. The current
Vite config proxies `/api` to port 8211. Use the same `127.0.0.1:3000` origin for login and
browser actions.

```bash
MIS_SIM_DISPOSABLE=1 node frontend/tests/readiness-proof.mjs
MIS_SIM_DISPOSABLE=1 node frontend/tests/host-platform-proof.mjs
MIS_SIM_DISPOSABLE=1 node frontend/tests/controls-proof.mjs
```

The script signs in through the browser, checks student routes at four widths, saves two
rollout choices, verifies reload and capital, locks, visits instructor workspaces, advances
six rounds and downloads the debrief. It writes `/tmp/mis-sim-readiness-browser/` screenshots
and `results.json`. A nonzero exit is a failed gate. It is a technical smoke rehearsal,
not the observed competent/negligent teaching acceptance in `pilot-rehearsal.md`. The host
proof uses Section B and verifies create, assignment, read-only detail, cross-instance
refusal and lock enforcement; its artifacts go to `/tmp/mis-sim-readiness-host/`. The controls
proof uses Section B team 2 and checks five cross-panel save/reload behaviors; its artifacts
go to `/tmp/mis-sim-readiness-controls/`. These scripts mutate the seeded teams: use a fresh
seeded database for an independent replay.

## Database and recovery evidence

Run `backend/scripts/check_postgres_runtime.py --database-url <verification URL>` against
the empty `mis_sim_verify_` database. The verifier checks the complete 32-model migration
inventory at head `20261006_0013` plus six historical committed results; it separately
retains the 19-table core runtime inventory. This does not substitute for the decision-driven
browser loop. Future migrations must update the explicit inventory.

Use `pg_dump -Fc` on that disposable database and `pg_restore` into a different empty local
database. Verify Alembic revision, schema inventory, six `round_result` rows spanning 1–6,
and payload identity with the source. Retain the dump and evidence until the review ends.
Stop only the cluster you created using its exact data directory; never stop a shared service.

## Production handoff checklist

Before publishing, the operator must supply a host/domain and choose a deployment window.
Prepare the built frontend, API environment, database backup and tested migration command,
reverse proxy/TLS, health monitoring, scheduler worker, staff accounts and rollback artifact.
The existing Compose file supplies API and database only; it is not a complete production
frontend/TLS deployment. Demo seeds must not be used as production account provisioning.

Verify `/api/health`, real browser login on the deployed origin, scoped API reads, scheduled
and manual advancement, error visibility, backup restoration and the running revision. Record
host-specific commands and results in the readiness evidence before claiming production
acceptance. No unknown destination is assumed by this runbook.

## Independent review evidence

The October6 independent reviews live under `findings/readiness-2026-10-06/` (backend and
frontend reports), with contract dispatch review under `handoffs/readiness-2026-10-06/`.
The frontend reviewer authored separate browser probes in the `frontend-review/` evidence
subdirectory. They use an isolated reviewer API/Vite and disposable cohort; read the report
for ports, fixture state and expected deliberate409 diagnostics before replaying.
Original failures are retained in `*-before.json`; the closure checker must fail with
`--before` and pass with corrected results. These bounded acceptance probes do not replace
the independently observed competent/negligent teaching pilot.

The SQLite seed transaction regression is retained as
`backend/tests/test_readiness_seed.py`: fresh migration/seed, all4 teams, reuse refusal and
unchanged database dump. Existing SQLite archive CHECK migration failure remains a separate
open platform/migrations issue; a successful seed does not certify archive.
