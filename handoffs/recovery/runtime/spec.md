# Recovery: reproducible backend runtime

Date: 2026-09-14. Tier: Light (dependency/runtime plumbing; no scoring contract change).
Owner: assigned runtime builder. Auditor: supervising agent, independently.
Base: the planning commit supplied in the dispatch. Prerequisite: read
`design/08-implementation-north-star.md`, governance/quality/spec protocols and CONTRACTS.

## Spec basis and verified problem

Read: `backend/requirements.txt`, `backend/Dockerfile`, `Makefile`, `backend/app/round/db.py`,
`backend/alembic/env.py`, `backend/app/config.py`, `backend/app/seed/demo.py`.
The round adapter strips `+asyncpg` and uses SQLAlchemy's synchronous PostgreSQL driver.
`psycopg2` is absent from the requirements; constructing that engine at baseline raises
`ModuleNotFoundError`. `make check` uses pytest, also undeclared in an installable dev file.
No scoring factors or casepack keys change. SQLite remains the fast suite's database.

## Allowed files

- `backend/requirements.txt`
- `backend/requirements-dev.txt` (new)
- `backend/tests/test_runtime_dependencies.py` (new, only if needed to guard the actual driver path)
- `backend/scripts/check_postgres_runtime.py` (new)
- `docs/backend-development.md` (new)
- `handoffs/recovery/runtime/dod.md` (new)

Request a scope amendment for any other file. Do not edit `.env`, Docker Compose, engine,
round logic, pack values, Makefile, shared registers, or frontend. Do not push or deploy.

## Decisions

Preserve the existing psycopg2 synchronous adapter; supply its missing driver dependency.
Choose an available Python-3.12-compatible exact version verified from the package index;
record the command/version in the DoD. Declare pytest in a development requirements file
including the runtime requirements. Do not upgrade the existing runtime pins as cleanup.
If those pins cannot install, report the exact incompatibility before changing their scope.

Create the verification command against an explicitly supplied **disposable local database**.
It must not use configured/environment database defaults, accept a remote target, reuse a
normal application database, or wipe an existing schema. Prefer a freshly created database
whose name has a documented verification-only prefix; check that it has no user tables
before migrations. The script may fail clearly when prerequisites are absent; it must never
skip PostgreSQL and report success. Document clean-environment install and verification commands.

Exercise the existing Alembic migrations and six-round seed through PostgreSQL, then inspect
persisted results for the expected six rounds and all 16 runtime tables' instance columns.
Migration up/down/up is permissible only inside that disposable database. Cleanup must target
only resources created for this verification; leave shared services and databases untouched.

## Preflight and acceptance

1. Prove the current configured-driver construction fails for the missing import without
   connecting to a database. Confirm requirements currently omit the driver and pytest.
2. Inspect availability of local PostgreSQL tools/service or Docker. Use isolated local
   resources, a unique port/name, and task-specific credentials. Report what was used.
3. Install the declared runtime+dev requirements into a fresh venv outside the worktree.
4. In that venv, constructing the synchronous engine with a nonconnecting dummy PostgreSQL
   URL succeeds; meaningful driver regression fails if the declared driver is omitted.
5. Run `make check` in the fresh venv. No ambient site packages may supply missing dependencies.
6. Run the disposable PostgreSQL path: migrations, seeded six-round results, actual database
   reads, and cleanup. Record exact command, result counts, versions and exit code.
7. Prove the verification refuses a non-disposable/nonempty/remote target before mutation.

DoD reports preflight, changed files, validation, refusal checks, limitations, commit SHA and
any owned residue. Browser/auth: N-A, headless infrastructure. Instance canary: existing suite
plus isolated verification state; no claim of the Phase 2 cross-casepack canary. Full `make
check` remains required. Auditor independently reruns installation/runtime checks before integration.
