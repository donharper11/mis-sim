"""The configured PostgreSQL round adapter must construct without connecting.

SQLite tests cannot detect a missing synchronous PostgreSQL driver. This exercises
the actual settings -> sync_url -> make_engine path using a nonconnecting URL.
"""

import os
from pathlib import Path
import subprocess
import sys

import pytest

from app.round.db import make_engine, settings


@pytest.mark.parametrize("scheme", ["postgresql+asyncpg", "postgresql"])
def test_configured_postgres_engine_loads_sync_driver(monkeypatch, scheme):
    monkeypatch.setattr(
        settings,
        "DATABASE_URL",
        f"{scheme}://runtime_probe:unused@127.0.0.1:1/mis_sim_verify_driver",
    )
    engine = make_engine()
    try:
        assert engine.dialect.name == "postgresql"
        assert engine.dialect.driver == "psycopg2"
        assert engine.dialect.dbapi.__name__ == "psycopg2"
    finally:
        engine.dispose()


@pytest.mark.parametrize("invalid_declared_setting", [False, True])
def test_shared_dotenv_fresh_import(tmp_path, invalid_declared_setting):
    """Shared Compose keys must not block imports or weaken declared-field validation."""
    backend = Path(__file__).resolve().parents[1]
    fixture_secret = "fixture_secret_do_not_echo"
    (tmp_path / ".env").write_text(
        "DATABASE_URL=postgresql+asyncpg://dotenv:unused@db:5432/mis_sim\n"
        "POSTGRES_DB=fixture_db\n"
        "POSTGRES_USER=fixture_user\n"
        f"POSTGRES_PASSWORD={fixture_secret}\n"
        "SECRET_KEY=fixture_application_key\n"
    )
    declared = {"database_url", "secret_key", "access_token_expire_minutes", "algorithm"}
    env = {key: value for key, value in os.environ.items() if key.lower() not in declared}
    env.update(
        PYTHONPATH=str(backend),
        DATABASE_URL="postgresql+asyncpg://runtime_probe:unused@127.0.0.1:1/mis_sim_verify_dotenv",
    )
    if invalid_declared_setting:
        env["ACCESS_TOKEN_EXPIRE_MINUTES"] = "not_an_integer"
    result = subprocess.run(
        [sys.executable, "-c", """
import os
from pydantic import ValidationError

try:
    from app.round.db import make_engine, settings
except ValidationError as exc:
    assert os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES') == 'not_an_integer'
    assert [error['loc'] for error in exc.errors()] == [('ACCESS_TOKEN_EXPIRE_MINUTES',)]
    print('declared-setting validation preserved')
else:
    assert 'ACCESS_TOKEN_EXPIRE_MINUTES' not in os.environ
    assert settings.DATABASE_URL == os.environ['DATABASE_URL']
    assert settings.SECRET_KEY == 'fixture_application_key'
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 480
    assert settings.ALGORITHM == 'HS256'
    engine = make_engine()
    try:
        assert engine.dialect.driver == 'psycopg2'
        assert engine.url.host == '127.0.0.1'
        assert engine.url.port == 1
        assert engine.url.database == 'mis_sim_verify_dotenv'
    finally:
        engine.dispose()
    print('shared dotenv accepted; explicit database selected')
"""],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert fixture_secret not in result.stdout + result.stderr
    assert "Traceback" not in result.stderr
    assert ("declared-setting validation preserved" if invalid_declared_setting else
            "shared dotenv accepted; explicit database selected") in result.stdout
