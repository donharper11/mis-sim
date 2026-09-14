# Backend development and PostgreSQL verification

Run these commands from the repository root in Bash. Python 3.12, `venv`, `make`,
and network access to the Python package index are required. No ambient Python
packages are needed. Runtime requirements include the psycopg2 driver used by
`app.round.db`; development requirements include runtime requirements and pytest.
Application settings accept the shared `.env.example` shape: unrelated `POSTGRES_*`
keys are ignored, declared settings remain validated, and an explicit environment
`DATABASE_URL` takes precedence over the dotenv value.

```bash
set -euo pipefail
runtime_venv=$(mktemp -d /tmp/mis-sim-venv.XXXXXX)
python3.12 -m venv "$runtime_venv"
source "$runtime_venv/bin/activate"
python -m pip install -r backend/requirements-dev.txt
python -m pip check
make check
```

`make check` runs the fast SQLite suite, the PostgreSQL driver construction
regression (without connecting), every `check_*.py` guard, and validator fixtures.
It does not start PostgreSQL. The command below adds actual PostgreSQL migration
and persistence verification; missing prerequisites cause a nonzero exit.

## Create an isolated local PostgreSQL cluster

Install PostgreSQL server/client tools before this step. The example uses the
PostgreSQL 16 binary directory on Ubuntu and runs as an ordinary user. Adjust
`runtime_pg_bin` for your installed tools. It creates a new cluster below `/tmp`,
binds only to loopback on an unused port, and uses a dedicated role/password.
It does not require Docker or an existing PostgreSQL service.

Keep this shell open so the variables also identify the exact cleanup target.
The port is chosen by the OS; if another process takes it before startup,
`pg_ctl` fails rather than connecting to that process.

```bash
runtime_pg_bin=/usr/lib/postgresql/16/bin
"$runtime_pg_bin/initdb" --version
runtime_pg_root=$(mktemp -d /tmp/mis-sim-pg.XXXXXX)
mkdir "$runtime_pg_root/socket"
runtime_pg_user=runtime_verify
runtime_pg_password=$(python -c 'import secrets; print(secrets.token_hex(16))')
runtime_pg_port=$(python -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()')
runtime_pg_database="mis_sim_verify_$(python -c 'import secrets; print(secrets.token_hex(8))')"
printf '%s\n' "$runtime_pg_password" > "$runtime_pg_root/password"
chmod 600 "$runtime_pg_root/password"
# Clear inherited libpq connection overrides in this verification shell.
for runtime_pg_key in ${!PG@}; do unset "$runtime_pg_key"; done
"$runtime_pg_bin/initdb" -D "$runtime_pg_root/data" -U "$runtime_pg_user" \
  --auth-local=scram-sha-256 --auth-host=scram-sha-256 \
  --pwfile="$runtime_pg_root/password"
"$runtime_pg_bin/pg_ctl" -D "$runtime_pg_root/data" \
  -l "$runtime_pg_root/postgres.log" \
  -o "-h 127.0.0.1 -p $runtime_pg_port -k $runtime_pg_root/socket" -w start
PGPASSWORD="$runtime_pg_password" "$runtime_pg_bin/createdb" \
  -h 127.0.0.1 -p "$runtime_pg_port" -U "$runtime_pg_user" \
  -T template0 "$runtime_pg_database"
runtime_database_url="postgresql+asyncpg://$runtime_pg_user:$runtime_pg_password@127.0.0.1:$runtime_pg_port/$runtime_pg_database"
python backend/scripts/check_postgres_runtime.py --database-url "$runtime_database_url"
```

The verifier requires an explicit URL. It ignores configured database defaults
and removes inherited `PG*` overrides before connecting. Only `postgresql`,
`postgresql+asyncpg`, and `postgresql+psycopg2` schemes are accepted. Hosts must be
literal `127.0.0.1` or `::1`, with an explicit port. Query parameters are forbidden.
The database must be named `mis_sim_verify_` followed by lowercase letters,
digits, or underscores (63 characters total maximum). Explicit username/password
characters are limited to letters, digits, underscores, and hyphens; use the
generated hexadecimal password above. This also avoids percent-escape handling
in the existing Alembic configuration.

The verifier first checks the connected database/address and refuses any existing
user tables, views, materialized views, sequences, or foreign tables in any user
schema. It runs `alembic upgrade head`, checks the actual Alembic revision and
all 16 runtime tables with non-null integer `instance_id` columns **before
seeding**, then calls the existing `run_full_game` seed directly. It never invokes
`create_all` as a fallback. A separate session reads six committed RoundResult
rows for instance 1/team 1, checks rounds 1–6 and payload identity, and reports
scoped row counts. The final `PASS` appears only after those reads succeed.

The seed uses the historical authored estate snapshots each round. This proves
driver, migration, and persistence operation; it does not prove decision-driven
estate evolution, scorecard unit correctness, browser/auth workflows, or the
Phase 2 cross-casepack isolation canary. Those are separate recovery milestones.

## Refusal checks and cleanup

Reusing the populated verification database must fail before any migrations or
seeding. Ordinary database names, remote hosts, query overrides, and missing URLs
must also fail:

```bash
if python backend/scripts/check_postgres_runtime.py --database-url "$runtime_database_url"; then exit 1; fi
if python backend/scripts/check_postgres_runtime.py --database-url 'postgresql://probe:unused@127.0.0.1:1/mis_sim'; then exit 1; fi
if python backend/scripts/check_postgres_runtime.py --database-url 'postgresql://probe:unused@192.0.2.1:1/mis_sim_verify_refuse'; then exit 1; fi
if python backend/scripts/check_postgres_runtime.py --database-url 'postgresql://probe:unused@127.0.0.1:1/mis_sim_verify_refuse?host=192.0.2.1'; then exit 1; fi
if python backend/scripts/check_postgres_runtime.py; then exit 1; fi
```

The verifier leaves its database intact on success or failure for inspection. It
does not wipe schemas, drop databases, or stop services. After recording evidence
and coordinating with the auditor, the person who created this cluster owns its
cleanup. These commands target only that exact database and cluster:

```bash
PGPASSWORD="$runtime_pg_password" "$runtime_pg_bin/dropdb" \
  -h 127.0.0.1 -p "$runtime_pg_port" -U "$runtime_pg_user" "$runtime_pg_database"
"$runtime_pg_bin/pg_ctl" -D "$runtime_pg_root/data" -m fast -w stop
rm -r -- "$runtime_pg_root"
deactivate
rm -r -- "$runtime_venv"
```

For another run, create another fresh `mis_sim_verify_*` database or repeat the
isolated-cluster recipe. Do not point this verifier at a normal application DB,
including an application database that happens to be empty.
