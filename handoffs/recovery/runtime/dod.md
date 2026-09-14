# Recovery runtime — builder Definition of Done

Date: 2026-09-14. Builder: `/root/runtime_builder`. Status: **candidate ready for independent audit; not integrated**.
Worktree: `/tmp/mis-sim-recovery-runtime`; branch: `build/recovery-runtime`.
Base: `d4652c1e34e712303d101177ba1c5949941bae0a`.
Implementation SHA including shared-dotenv audit fix: `e1efd50742e65397b44afcb4d76a0282fd37cccb`.
First implementation SHA (superseded by audit fix): `9ed2b94516c26f1b815680dcfd65f0927dc417f1`.
Initial author-amendment SHA: `edc65fc92b55ada342046620a85caa2abc8ffe6b`.
Shared-dotenv author-amendment SHA: `6652317` (exact spec from supervisor `6a6c707`).
This evidence-only commit follows the implementation SHA; obtain the delivered candidate
including this report with `git rev-parse HEAD` on the handed-off branch.

The supervisor initially authorized the additional spec file: the exact runtime spec amendment
from integration commit `0a3f967`. Applied and committed with:

```bash
git show 0a3f967:handoffs/recovery/runtime/spec.md > handoffs/recovery/runtime/spec.md
git add handoffs/recovery/runtime/spec.md
git commit -m 'docs(runtime): apply supervisor migration verification amendment'
```

The amendment strengthens acceptance row 6: assert migrated schema and Alembic revision
before seed/create_all could conceal missing migrations. It also declares the infrastructure
author-audit exception. The builder remains separate from the auditor.

## Shared-dotenv audit correction and current acceptance

The independent supervisor audit found the first candidate failed when the current
working directory contained the shared `.env.example` shape. Its `POSTGRES_*` keys
were rejected at settings import, and the exception echoed the fixture values. The
clean worktree without `.env` had concealed this. The first-candidate readiness claim
is superseded by the correction below; independent **re-audit is pending**.

The supervisor authorized the narrow `backend/app/config.py` addition to scope. The
exact spec amendment was applied and committed separately:

```bash
git show 6a6c707:handoffs/recovery/runtime/spec.md > handoffs/recovery/runtime/spec.md
git add handoffs/recovery/runtime/spec.md
git commit -m 'docs(runtime): apply supervisor shared dotenv audit amendment'
```

| Acceptance | Status | Evidence |
|---|---|---|
| Narrow settings change | PASS | `model_config = {"env_file": ".env", "extra": "ignore"}`; the only changed line in config. Every declared field/default and the dotenv source remain identical. |
| Fresh-import regression before fix | PASS, defect reproduced | New subprocess cases in `test_runtime_dependencies.py` failed twice before the fix; config bytes were asserted identical to `git show 9ed2b94:backend/app/config.py`. All other implementation source also remained at the audited implementation. Log: `/tmp/mis-sim-runtime-dotenv-before-20260914.log`. |
| Shared extras and explicit URL | PASS | Fresh subprocess imports from a temporary shared-shape `.env` directory; ignores `POSTGRES_*`, retains declared dotenv `SECRET_KEY`, and constructs the nonconnecting explicit PostgreSQL engine at port 1 rather than the dotenv target. |
| Declared-field validation retained | PASS | The second fresh subprocess supplies `ACCESS_TOKEN_EXPIRE_MINUTES=not_an_integer` and requires the sole validation error to name that declared field. It still fails validation after extras are ignored. |
| Runtime tests after fix | PASS | `PYTHONPATH=backend /tmp/mis-sim-runtime-clean-20260914-builder/bin/python -m pytest -q backend/tests/test_runtime_dependencies.py` → **4 passed in 0.68s**, exit 0. Both subprocess outputs contain no fixture-secret echo or traceback. |
| Full checks after fix | PASS | `PATH=/tmp/mis-sim-runtime-clean-20260914-builder/bin:$PATH make check` → **86 passed in 11.11s**, all guards and **44 fixtures** pass, exit 0. Log: `/tmp/mis-sim-runtime-dotenv-make-check-20260914.log`. Same fresh declared-dependency venv, no dependency changes. |
| Actual PG with shared dotenv | PASS | Verifier launched by absolute path with cwd `/tmp/mis-sim-runtime-dotenv-builder-20260914-_dlh0up8`, containing only dummy `.env` values. Exit 0; 16 tables checked before seed, six rounds committed and independently reread. No `Traceback`, `ValidationError`, or fixture marker in stdout/stderr. |
| Scoped evidence retained | PASS | New DB `mis_sim_verify_dotenv_builder_20260914`, same builder cluster `127.0.0.1:53883`; metadata `/tmp/mis-sim-runtime-dotenv-builder-20260914.json`. Original six-round DB remains too. No real `.env` was changed. Builder retains both for re-audit/owned cleanup. |
| Supervisor first audit | Complete, correction requested | Supervisor independently installed dependencies, passed the original 84-test suite, checked 16 migrated tables/six rows, five refusals, and missing-table-before-seed regression. Supervisor dropped its own two audit DBs. This does not substitute for re-audit of the corrected candidate. |

Exact before/after commands:

```bash
# Before the one-line fix; new regression on the otherwise unchanged 9ed2b94 source:
PYTHONPATH=backend /tmp/mis-sim-runtime-clean-20260914-builder/bin/python -m pytest -q backend/tests/test_runtime_dependencies.py -k shared_dotenv
# 2 failed, 2 deselected in 0.68s; exit 1.
# After adding extra="ignore":
PYTHONPATH=backend /tmp/mis-sim-runtime-clean-20260914-builder/bin/python -m pytest -q backend/tests/test_runtime_dependencies.py
PATH=/tmp/mis-sim-runtime-clean-20260914-builder/bin:$PATH make check
/tmp/mis-sim-runtime-clean-20260914-builder/bin/python /tmp/mis-sim-runtime-dotenv-postgres-20260914.py
# Each exits 0. The last command creates its own named DB and leaves it for audit;
# choose a new mis_sim_verify_* name in the helper before repeating it.
```

The real-PG helper is reproduced below for an independent rerun. It writes only a
new verification database and a new temporary directory. It never prints the cluster
password. Its log is `/tmp/mis-sim-runtime-dotenv-postgres-20260914.log`.

```python
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import psycopg2

cfg=json.loads(Path('/tmp/mis-sim-runtime-pg-builder-20260914.json').read_text())
pw=(Path(cfg['root'])/'password').read_text().strip()
env={k:v for k,v in os.environ.items() if not k.startswith('PG') and k.lower() not in {'database_url','secret_key','access_token_expire_minutes','algorithm'}}
env['PGPASSWORD']=pw
name='mis_sim_verify_dotenv_builder_20260914'
subprocess.run([cfg['bin']+'/createdb','-h','127.0.0.1','-p',str(cfg['port']),'-U',cfg['user'],'-T','template0',name],env=env,check=True)
fixture=Path(tempfile.mkdtemp(prefix='mis-sim-runtime-dotenv-builder-20260914-'))
marker='fixture_secret_do_not_echo'
(fixture/'.env').write_text(
    'DATABASE_URL=postgresql+asyncpg://dotenv_user:unused@db:5432/mis_sim\n'
    f'POSTGRES_DB={marker}\nPOSTGRES_USER={marker}\nPOSTGRES_PASSWORD={marker}\n'
    'SECRET_KEY=fixture_application_key\n'
)
(fixture/'.env').chmod(0o600)
url=f"postgresql+asyncpg://{cfg['user']}:{pw}@127.0.0.1:{cfg['port']}/{name}"
result=subprocess.run([sys.executable,'/tmp/mis-sim-recovery-runtime/backend/scripts/check_postgres_runtime.py','--database-url',url],cwd=fixture,env=env,capture_output=True,text=True,timeout=60)
output=result.stdout+result.stderr
Path('/tmp/mis-sim-runtime-dotenv-postgres-20260914.log').write_text(output)
assert result.returncode==0,result.stderr
assert marker not in output and 'Traceback' not in output and 'ValidationError' not in output
summary=json.JSONDecoder().raw_decode(result.stdout[result.stdout.index('{'):])[0]
assert summary['persisted_rounds']==list(range(1,7))
assert summary['database']==name
assert len(summary['runtime_tables_with_instance_id'])==16
con=psycopg2.connect(host='127.0.0.1',port=cfg['port'],user=cfg['user'],password=pw,dbname=name)
try:
    with con.cursor() as cur:
        cur.execute('SELECT round, payload FROM round_result WHERE instance_id=1 AND team_id=1 ORDER BY round')
        rows=cur.fetchall()
        assert [row[0] for row in rows]==list(range(1,7))
        assert all(row[1]['round']==row[0] and row[1]['instance_id']==1 and row[1]['team_id']==1 for row in rows)
finally:
    con.close()
Path('/tmp/mis-sim-runtime-dotenv-builder-20260914.json').write_text(json.dumps({'fixture_directory':str(fixture),'database':name,'port':cfg['port'],'result_count':len(rows)},indent=2)+'\n')
print('Verifier exit 0; 16 migrated scoped tables and 6 committed rounds; no traceback, ValidationError, or fixture-value echo.')
print('Retained dotenv fixture directory:',fixture)
print('Retained audit database:',name)
```

The application settings fix, subprocess tests and documentation were committed with:

```bash
git add backend/app/config.py backend/tests/test_runtime_dependencies.py docs/backend-development.md
git commit -m 'fix(runtime): accept shared dotenv keys without weakening settings validation'
```

The remaining sections preserve the initial runtime evidence. Counts of 84 below are
the first-candidate run; the corrected candidate has the 86-test result above.

## Preflight, before initial implementation

Read in full: GOVERNANCE, QUALITY_PROTOCOL, SPEC_PROTOCOL, CONTRACTS,
`design/08-implementation-north-star.md`, and the runtime handoff. Inspected requirements,
Dockerfile, Makefile, settings, synchronous adapter, Alembic environment/migrations,
runtime models, demo CLI, and six-round seed before implementation.

Relevant unchanged contract: `CONTRACTS.md` says `instance_id` is an `integer`, present on
every runtime table and never nullable; game-state queries filter on it. Verification
reads use instance 1/team 1. The existing deferred Phase 2 FK is not created or claimed.

| Row | Status | Exact check and observed result |
|---|---|---|
| Worktree/base | PASS | `git status --short` empty; `git branch --show-current` → `build/recovery-runtime`; `git rev-parse HEAD` → dispatched base before edits. |
| 1: missing dependencies | PASS, defect reproduced | `rg -n 'psycopg\|pytest' backend/requirements.txt` had no matches (the actual search used regex `psycopg|pytest`). `make_engine` on a nonconnecting dummy URL raised `ModuleNotFoundError: No module named 'psycopg2'`; baseline fresh venv also had no pytest. |
| 2: local infrastructure | PASS | `python3 --version` → 3.12.3; `/usr/lib/postgresql/16/bin/initdb --version` and `pg_ctl --version` → PostgreSQL 16.15. Docker 29.1.3 was available but unused. Created an independent cluster as user ubuntu; no existing service/database was used. |
| Existing pins install | PASS | Fresh baseline venv installed `backend/requirements.txt` unchanged, exit 0. No incompatibility or scope amendment for existing pins was needed. |
| Availability of new pins | PASS | `python3 -m pip index versions psycopg2-binary` and `pytest` both listed selected versions. Direct PyPI JSON confirmed psycopg2-binary 2.9.11, Python >=3.9, cp312 manylinux x86_64 wheel; pytest 8.3.5, Python >=3.8, universal wheel. |
| Acceptance rows 3–7 | Scheduled after preflight, now PASS | Installation, driver regression, full suite, real PostgreSQL and refusal evidence below. Preflight was reported to supervisor before implementation edits. |

Availability was queried during this session from
[psycopg2-binary 2.9.11](https://pypi.org/project/psycopg2-binary/2.9.11/)
and [pytest 8.3.5](https://pypi.org/project/pytest/8.3.5/), including:

```bash
python3 - <<'CHECK'
import json, urllib.request
for package, version in [('psycopg2-binary', '2.9.11'), ('pytest', '8.3.5')]:
    with urllib.request.urlopen(f'https://pypi.org/pypi/{package}/{version}/json', timeout=20) as response:
        data = json.load(response)
    print(data['info']['version'], data['info']['requires_python'])
    print(next(row['filename'] for row in data['urls'] if
               'cp312-cp312-manylinux2014_x86_64' in row['filename'] or
               'py3-none-any.whl' in row['filename']))
CHECK
```

## Changes and acceptance

| Item | Status | Evidence |
|---|---|---|
| Runtime driver declared | PASS | Only added `psycopg2-binary==2.9.11` to runtime requirements; all 13 prior requirement lines unchanged. |
| Development install declared | PASS | New `requirements-dev.txt` includes `-r requirements.txt` and `pytest==8.3.5`. |
| Actual configured-driver path guarded | PASS | Two parametrized cases call the unchanged `make_engine()` through overridden settings for plain PostgreSQL and `+asyncpg`. No connection is opened. Reached by pytest/`make check`. |
| 3: fresh declared-only install | PASS | `/tmp/mis-sim-runtime-clean-20260914-builder`, Python 3.12.3; `include-system-site-packages = false`, `site.ENABLE_USER_SITE = False`, no `dist-packages` or user-site path. `pip install -r backend/requirements-dev.txt` and `pip check` exit 0. |
| 4: missing-driver regression | PASS | Same new tests with baseline runtime requirements plus pytest but without driver: **2 failed**, both `ModuleNotFoundError: psycopg2`, exit 1. Declared clean environment: both pass. |
| 5: full suite | PASS | Fresh-venv `make check`: **84 passed in 10.57s**, all `check_*.py` guards green; **44 fixtures** behave as named, 38/39 codes covered, existing I8 unfixturable residue unchanged. Exit 0. |
| Validator | PASS | `backend/bin/validate_casepack backend/packs/riverside_grocery`: **0 errors, 0 warnings**, exit 0. |
| 6: actual migrations before seed | PASS | PostgreSQL 16.15; Alembic `20260822_0002`; all **16** runtime tables inspected as actual tables, non-null integer instance columns. No `create_all` fallback in verifier. |
| 6: committed six-round reads | PASS | New session reads RoundResult rounds **[1,2,3,4,5,6]**, instance 1/team 1, payload identity and nonempty computed content. Detailed counts below. Exit 0. |
| 6: missing migration cannot be masked | PASS | Dropping `platform_service` immediately after actual migrations yields verifier exit 1 before a planted seed/create_all fallback runs (`seed_called=False`). Nullable instance and incorrect revision also fail before seed. |
| Persisted readback falsification | PASS | Delete round 6 → exit 1; change persisted payload instance 1→2 → exit 1. Both checks inspect a separate committed session. |
| 7: target refusal | PASS | Missing URL exits 2 even when DATABASE_URL is populated; ordinary name, remote/DNS host, query host/hostaddr override, missing port/database, SQLite and nonempty targets exit 1. No migration success banner for these. |
| 7: no mutation on nonempty target | PASS | All six retained payloads unchanged after refusal. A sentinel table in a non-public schema retained its value and had no Alembic version table after refusal. A view-only database was refused too. |
| Configured/environment defaults unused | PASS | Fresh explicit local target succeeded despite different remote `DATABASE_URL`, `PGHOSTADDR`, nonexistent `PGSERVICE`, and `PGOPTIONS` search-path overrides. Result readback confirmed local target. Exit 0; test database dropped. |
| Docs install-to-cleanup recipe | PASS | Executed all four Bash blocks from `docs/backend-development.md` unchanged. Another fresh venv: **84 passed in 10.38s**, all guards, PG run, refusals, database drop, cluster stop, directory/venv removal; script exit 0. |
| Scoped cleanup | PASS / retained audit resource | Refusal, mutation and environment-test databases dropped. Documentation-run cluster `/tmp/mis-sim-pg.84Kqa7`, port 37071, DB `mis_sim_verify_c7ed3328ea7294bc` removed. Main evidence cluster remains for auditor, owned by builder. |
| Scope and syntax | PASS | `git diff --check` and `python -m compileall -q` on new Python files exit 0. Only allowlisted files plus exact authorized spec amendment changed. |
| Browser/auth/design-system | N-A | Headless infrastructure; no UI, auth, CSS, route or browser-host changes. Quality ladder browser/UX rungs do not apply. |
| Instance canary | PASS within existing scope | Existing SQLite canary reports zero cross-instance reads. PostgreSQL verification is only the isolated seeded instance; **no claim of Phase 2 cross-casepack isolation**. |
| Register reconciliation / integration | Supervisor-owned, pending audit | North-star recovery instructions reserve shared register updates for supervisor at integration. Builder changed no shared register. The driver finding is a tested candidate, not marked integrated. |
| Independent audit | PENDING | Supervisor reruns checks on delivered commit. This builder report is not an audit acceptance. |

No scorer, runner, migration, casepack, existing version pin, Docker Compose, `.env`,
Makefile or frontend code changed. No push, deployment, main merge, or shared DB write.

## Reproduction commands and actual evidence

All commands below were run from `/tmp/mis-sim-recovery-runtime` unless noted.
Baseline failure used the unmodified runtime requirements installed in a separate venv:

```bash
python3 -m venv /tmp/mis-sim-runtime-venv-20260914-builder
/tmp/mis-sim-runtime-venv-20260914-builder/bin/python -m pip install --index-url https://pypi.org/simple -r backend/requirements.txt
PYTHONPATH=backend /tmp/mis-sim-runtime-venv-20260914-builder/bin/python - <<'CHECK'
from app.round.db import make_engine
make_engine('postgresql+asyncpg://runtime_probe:unused@127.0.0.1:1/mis_sim_verify_missing_driver')
CHECK
# Observed before requirements changed: ModuleNotFoundError: psycopg2, exit 1.
/tmp/mis-sim-runtime-venv-20260914-builder/bin/python -m pytest --version
# Observed: No module named pytest, exit 1.
/tmp/mis-sim-runtime-venv-20260914-builder/bin/python -m pip install --index-url https://pypi.org/simple pytest==8.3.5
PYTHONPATH=backend /tmp/mis-sim-runtime-venv-20260914-builder/bin/python -m pytest -q backend/tests/test_runtime_dependencies.py
# Observed after test added, before driver installed: 2 failed in 0.21s, exit 1.
```

To recreate this omitted-driver environment from the candidate later, install the
requirements obtained with `git show d4652c1:backend/requirements.txt` (not the candidate's
requirements); the preserved baseline venv still has the driver omitted.

```bash
python3 -m venv /tmp/mis-sim-runtime-clean-20260914-builder
/tmp/mis-sim-runtime-clean-20260914-builder/bin/python -m pip install --index-url https://pypi.org/simple -r backend/requirements-dev.txt
/tmp/mis-sim-runtime-clean-20260914-builder/bin/python -m pip check
PATH=/tmp/mis-sim-runtime-clean-20260914-builder/bin:$PATH make check
PATH=/tmp/mis-sim-runtime-clean-20260914-builder/bin:$PATH backend/bin/validate_casepack backend/packs/riverside_grocery
/tmp/mis-sim-runtime-clean-20260914-builder/bin/python -m pip freeze
```

Versions read from the installed environment: psycopg2-binary **2.9.11**, pytest **8.3.5**,
SQLAlchemy **2.0.36**, asyncpg **0.30.0**, Alembic **1.14.1**. The 43-package resolved
freeze is `/tmp/mis-sim-runtime-clean-freeze-20260914.txt`; transitive dependencies are
resolved by pip and are not newly locked by this bounded handoff.

Actual PG invocation used an explicit generated credential URL, passed as one argument
without printing the password. The retained cluster identifiers are:

| Identifier | Value |
|---|---|
| Cluster data directory | `/tmp/mis-sim-runtime-pg-builder-20260914-pbrswfo2/data` |
| Unix-socket directory | `/tmp/mis-sim-runtime-pg-builder-20260914-pbrswfo2/socket` |
| Network binding | `127.0.0.1:53883` only |
| PostgreSQL | 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1), x86_64 |
| Role | `runtime_builder` |
| Password file | `/tmp/mis-sim-runtime-pg-builder-20260914-pbrswfo2/password` (mode 0600; generated only for this cluster) |
| Database retained | `mis_sim_verify_builder_20260914` |
| Machine-readable identifiers | `/tmp/mis-sim-runtime-pg-builder-20260914.json` |
| Logs | Cluster root `initdb.log`, `postgres.log`; verification `/tmp/mis-sim-runtime-postgres-20260914.log` |

Use the documented cluster recipe for a completely independent environment. To rerun
on this cluster, create a **new** database; the retained one deliberately refuses reuse:

```bash
source /tmp/mis-sim-runtime-clean-20260914-builder/bin/activate
runtime_pg_root=/tmp/mis-sim-runtime-pg-builder-20260914-pbrswfo2
runtime_pg_bin=/usr/lib/postgresql/16/bin
runtime_pg_password=$(cat "$runtime_pg_root/password")
runtime_audit_db="mis_sim_verify_audit_$(python -c 'import secrets; print(secrets.token_hex(8))')"
for runtime_pg_key in ${!PG@}; do unset "$runtime_pg_key"; done
PGPASSWORD="$runtime_pg_password" "$runtime_pg_bin/createdb" -h 127.0.0.1 -p 53883 -U runtime_builder -T template0 "$runtime_audit_db"
python backend/scripts/check_postgres_runtime.py --database-url "postgresql+asyncpg://runtime_builder:$runtime_pg_password@127.0.0.1:53883/$runtime_audit_db"
# Expect exit 0, Alembic head 20260822_0002 and rounds 1–6.
# After audit, drop only this newly created audit database:
PGPASSWORD="$runtime_pg_password" "$runtime_pg_bin/dropdb" -h 127.0.0.1 -p 53883 -U runtime_builder "$runtime_audit_db"
```

Actual persisted counts for instance 1/team 1:

| Table | Rows | Table | Rows |
|---|---:|---|---:|
| arch_edge | 48 | arch_node | 57 |
| debt_item | 2 | decision_line | 23 |
| deployment_org_state | 29 | governance_state | 18 |
| in_flight | 0 | it_staff | 6 |
| org_unit | 18 | platform_service | 0 |
| policy_decision | 36 | round_result | 6 |
| signal | 10 | stakeholder_alignment | 18 |
| tco_forecast | 6 | team_state | 1 |

Additional actual commands and retained full logs:

```bash
/tmp/mis-sim-runtime-clean-20260914-builder/bin/python /tmp/mis-sim-runtime-refusals-20260914.py
# exit 0; each bad verifier invocation exits 1 (missing flag exits 2).
/tmp/mis-sim-runtime-clean-20260914-builder/bin/python /tmp/mis-sim-runtime-mutations-20260914.py
# exit 0; all five mutated verifier runs exit 1 (details/source below).
bash /tmp/mis-sim-runtime-doc-recipe-20260914.sh
# exit 0; exact concatenation of all four documented Bash blocks.
```

Logs: `/tmp/mis-sim-runtime-driver-before-20260914.log`,
`/tmp/mis-sim-runtime-baseline-install-20260914.log`,
`/tmp/mis-sim-runtime-clean-install-20260914.log`,
`/tmp/mis-sim-runtime-make-check-20260914.log`,
`/tmp/mis-sim-runtime-refusals-20260914.log`,
`/tmp/mis-sim-runtime-mutations-20260914.log`,
`/tmp/mis-sim-runtime-environment-20260914.log`, and
`/tmp/mis-sim-runtime-doc-recipe-20260914.log`.

The refusal harness initially kept its own psycopg connection open, so dropdb refused
cleanup. The harness was corrected to close its connections; the refusal run and scoped
cleanup then passed. No verifier code or database safety rule was relaxed.

## Durable migration/readback falsification script

The following is the exact source of the executed mutation harness. It creates its own
`mis_sim_verify_mutation_*` databases inside the builder cluster and drops only those.
The planted seed wrapper contains `create_all`: migration checks must fail before that
wrapper can repair the missing table. No repository migration or round code is edited.

```python
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import importlib.util
import json
import os
import subprocess
import sys
import psycopg2

backend = Path('/tmp/mis-sim-recovery-runtime/backend')
sys.path.insert(0, str(backend))
spec = importlib.util.spec_from_file_location('runtime_verifier', backend/'scripts/check_postgres_runtime.py')
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)
import seeds.riverside_full as seed
cfg = json.loads(Path('/tmp/mis-sim-runtime-pg-builder-20260914.json').read_text())
pw = (Path(cfg['root'])/'password').read_text().strip()
base = f"postgresql+asyncpg://{cfg['user']}:{pw}@127.0.0.1:{cfg['port']}/"
env = {k: v for k, v in os.environ.items() if not k.startswith('PG')}
env['PGPASSWORD'] = pw
original_run = subprocess.run
original_seed = seed.run_full_game

for label, ddl, expected, phase in [
    ('missing_table', 'DROP TABLE platform_service', 'migrated tables differ', 'migration'),
    ('nullable_instance', 'ALTER TABLE arch_node ALTER COLUMN instance_id DROP NOT NULL', 'arch_node.instance_id must be a non-null integer', 'migration'),
    ('wrong_revision', "UPDATE alembic_version SET version_num='deliberately_wrong'", 'migration revision mismatch', 'migration'),
    ('missing_round', 'DELETE FROM round_result WHERE instance_id=1 AND team_id=1 AND round=6', 'expected persisted rounds', 'seed'),
    ('wrong_payload_scope', "UPDATE round_result SET payload=jsonb_set(payload::jsonb, '{instance_id}', '2')::json WHERE instance_id=1 AND team_id=1 AND round=1", 'incorrectly scoped persisted payload', 'seed'),
]:
    name = 'mis_sim_verify_mutation_' + label
    def db_command(command):
        original_run([cfg['bin']+'/'+command, '-h', '127.0.0.1', '-p', str(cfg['port']), '-U', cfg['user'], name], env=env, check=True)
    db_command('createdb')
    def mutate():
        with psycopg2.connect(host='127.0.0.1', port=cfg['port'], user=cfg['user'], password=pw, dbname=name) as con:
            with con.cursor() as cur:
                cur.execute(ddl)
    seed_called = []
    def migration_run(*args, **kwargs):
        result = original_run(*args, **kwargs)
        if phase == 'migration':
            mutate()
        return result
    def tracked_seed(session):
        seed_called.append(True)
        # Deliberate create_all fallback: a missing migration must be caught
        # before this can reconstruct the missing table and mask the defect.
        from app.round.db import create_all
        create_all(session.get_bind())
        result = original_seed(session)
        if phase == 'seed':
            mutate()
        return result
    subprocess.run = migration_run
    seed.run_full_game = tracked_seed
    sys.argv = [str(backend/'scripts/check_postgres_runtime.py'), '--database-url', base+name]
    stdout, stderr = StringIO(), StringIO()
    try:
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = verifier.main()
        assert code == 1, (label, stdout.getvalue(), stderr.getvalue())
        assert expected in stderr.getvalue(), (label, stderr.getvalue())
        assert bool(seed_called) == (phase == 'seed'), (label, seed_called)
        print(f'{label}: verifier exit {code}, seed_called={bool(seed_called)}; {stderr.getvalue().strip()}')
    finally:
        subprocess.run = original_run
        seed.run_full_game = original_seed
        db_command('dropdb')
print('all five deliberately damaged states rejected; mutation databases dropped')
```

Observed:

- Missing `platform_service`: verifier exit 1, `seed_called=False`, `migrated tables differ`.
- Nullable `arch_node.instance_id`: verifier exit 1, `seed_called=False`, non-null integer requirement failed.
- Wrong Alembic revision: verifier exit 1, `seed_called=False`, revision mismatch.
- Deleted round 6: verifier exit 1, `seed_called=True`, found only rounds 1–5.
- Wrong payload instance: verifier exit 1, `seed_called=True`, incorrectly scoped payload.

## Ownership, limitations and delivery

Builder owns cleanup of the retained cluster, both named builder venvs, the dummy
dotenv fixture directory, and `/tmp` verification scripts/logs **after coordinating with the supervisor/auditor**. At first-candidate
readback the only `mis_sim_verify_*` database remaining in the retained cluster was
`mis_sim_verify_builder_20260914`, with rounds 1–6. The separate documentation cluster
was stopped and its directory removed. No shared resources need cleanup.

After audit coordination, exact retained-cluster cleanup (credentials read from its
own password file) is:

```bash
runtime_pg_root=/tmp/mis-sim-runtime-pg-builder-20260914-pbrswfo2
runtime_pg_password=$(cat "$runtime_pg_root/password")
for runtime_pg_key in ${!PG@}; do unset "$runtime_pg_key"; done
PGPASSWORD="$runtime_pg_password" /usr/lib/postgresql/16/bin/dropdb -h 127.0.0.1 -p 53883 -U runtime_builder mis_sim_verify_dotenv_builder_20260914
PGPASSWORD="$runtime_pg_password" /usr/lib/postgresql/16/bin/dropdb -h 127.0.0.1 -p 53883 -U runtime_builder mis_sim_verify_builder_20260914
/usr/lib/postgresql/16/bin/pg_ctl -D "$runtime_pg_root/data" -m fast -w stop
rm -r -- "$runtime_pg_root"
rm -r -- /tmp/mis-sim-runtime-dotenv-builder-20260914-_dlh0up8
```

Limitations: historical per-round estate seed only; no decision-evolution or scorecard
semantics changed or validated; no browser/auth or Phase 2 canary claim; no Docker image
build or deployment; migration upgrade tested, downgrade cycle not required/exercised.
Direct pins are exact, existing transitive dependencies remain pip-resolved. This is
runtime M0 evidence, not completion of M0 or any subsequent milestone.

No open implementation ruling remains. Independent audit and supervisor register/status
integration remain outstanding. Changes committed with an exact add list:

```bash
git add backend/requirements.txt backend/requirements-dev.txt backend/tests/test_runtime_dependencies.py backend/scripts/check_postgres_runtime.py docs/backend-development.md
git commit -m 'fix(runtime): declare PostgreSQL driver and verify disposable persistence'
git add handoffs/recovery/runtime/dod.md
git commit -m 'docs(runtime): record dependency and PostgreSQL verification evidence'
```
