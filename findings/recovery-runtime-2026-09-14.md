# Recovery runtime audit

Date: 2026-09-14. Initial candidate: `d68d8925607c63a75b092568637c7b017dd990e6`
(implementation `9ed2b94516c26f1b815680dcfd65f0927dc417f1`).
Corrected candidate: `ae634456665fe116f7d4f47ba08301aa29b99f03`
(implementation including correction `e1efd50742e65397b44afcb4d76a0282fd37cccb`).
Author/auditor: supervisor. Builder: `runtime_builder`, separate agent and worktree.
**Infrastructure author-audit exception declared:** no student surface and no scoring
factor is captured or displayed by this change. Browser/auth checks are N-A for this
headless dependency/migration verifier. The supervisor independently installed and ran
the checks; this acceptance does not rely on the builder's logs.

**Final verdict: ACCEPT corrected candidate.** NS-001 and NS-006 close on the integration
branch in the commit containing this record. No main merge or remote publication claimed.

## Finding and correction

**NS-006 — blocking at initial audit, now closed.** `backend/app/config.py:10` read the
shared `.env` but rejected the `POSTGRES_*` keys shipped in `.env.example`. Launching the
new verifier from a temporary directory with those keys failed at configuration import
before any connection, and the uncaught validation traceback echoed the fixture values.
An isolated worktree without `.env` had concealed the problem.

The supervisor reproduced this using dummy values only and issued scope amendment
`6a6c707`. The builder changed only `Settings.model_config`'s extra-key handling, keeping
the declared fields/defaults and known-field validation. No real dotenv file changed.
Independent regression on a fresh archive of `9ed2b94`, with the corrected tests copied
in: **two dotenv cases fail, two driver cases pass**. Corrected candidate: **four pass**.
The tests use fresh subprocess imports and prove explicit DATABASE_URL precedence,
retained dotenv settings, and rejection of an invalid declared integer setting.

## Supervisor evidence

1. Reproduced the baseline driver failure before connecting: from `backend/`, set a
   dummy PostgreSQL DATABASE_URL and invoke `app.round.db.make_engine()` with the
   pre-existing interpreter: `ModuleNotFoundError: psycopg2`.
2. Created `/tmp/mis-sim-supervisor-venv-r2cjbjvg` and installed only
   `backend/requirements-dev.txt`. Python **3.12.3**, pytest **8.3.5**, psycopg2-binary
   **2.9.11**; user site disabled, no ambient/user packages in sys.path. `pip check` passes.
3. Read the complete verifier and candidate diff. Exact amended eight-file cumulative
   allowlist, including its authorized spec amendments; no scoring/runner/pack changes.
4. Independently created new databases in the builder's isolated PostgreSQL **16.15**
   cluster. The verifier ran actual Alembic upgrade to **20260822_0002**, inspected
   all **16 runtime tables** and their non-null integer instance columns before seed,
   and wrote six rounds. Separate SQL reads confirmed scope and rounds 1–6.
5. Launched the corrected verifier from a temporary shared-dotenv directory with a
   different dummy remote DATABASE_URL. The explicit local URL won; six results were
   verified with no traceback, validation exception or fixture-secret echo.
6. Independently repeated missing-URL, ordinary-name, remote-host, query-override and
   nonempty-target refusals. No success claim; all six existing payloads stayed identical.
7. Wrapped actual Alembic execution to drop `round_result` immediately after migration,
   with a spy on seed. Verification failed on the migrated table set **before any seed
   call**, so a seed/create_all fallback cannot mask the defect. Seed calls: **0**.
8. Repeated the PostgreSQL proof on the combined integration checkout. Supervisor-created
   databases were dropped in `finally`; only task-specific databases were touched.
9. Combined-tree `make check`: **132 pytest tests**, every check script and **44 fixture
   cases** pass. Existing isolation and scoring pins remain green; `pip check` passes.

Supervisor logs: `/tmp/mis-sim-supervisor-runtime-check.log`,
`/tmp/mis-sim-supervisor-runtime-reaudit.log`,
`/tmp/mis-sim-supervisor-integrated-pg.log`,
`/tmp/mis-sim-supervisor-combined-check.log`.
Independent harness: `/tmp/mis-sim-supervisor-runtime-audit.py`.
Durable setup, verifier and scoped cleanup recipe: `docs/backend-development.md`.
Builder DoD includes complete source for its additional schema/readback mutations.

## Closing checks and limits

From `backend/`: `PYTHONPATH=. python -m pytest tests/test_runtime_dependencies.py -q`.
From the repository root, follow `docs/backend-development.md` using a newly created
disposable database and explicit URL, then run `make check`. A driver-only import test
does not substitute for the actual PostgreSQL run above.

No decision-to-estate mutation or score semantics changed. PostgreSQL verification uses
the historical per-round seed; it does not establish M1, browser/auth workflows, full
financial scoring, the Phase 2 cross-casepack canary, Docker deployment or pilot readiness.
Exact direct pins are now installable; this is not a transitive lockfile. Remaining
score-unit work keeps M0 open. Builder owns retained-cluster cleanup after acceptance;
the recovery execution record records its final cleanup confirmation.
