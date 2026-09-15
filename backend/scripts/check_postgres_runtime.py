"""Verify migrations and the existing six-round seed on an empty local throwaway DB.

No database is created, cleared, or dropped here. See docs/backend-development.md
for creating a dedicated cluster, supplying the required URL, and scoped cleanup.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from sqlalchemy import Integer, func, inspect, select, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError, SQLAlchemyError


BACKEND = Path(__file__).resolve().parents[1]
DATABASE_PREFIX = "mis_sim_verify_"
EXPECTED_ROUNDS = list(range(1, 7))
EXPECTED_TABLE_COUNT = 19


def expected_models(round_models, simulation_models):
    """Return the historical 16 plus the three versioned simulation tables."""
    return (*round_models.ALL_TABLES, *simulation_models.ALL_TABLES)


class VerificationError(RuntimeError):
    pass


def disposable_url(raw: str) -> URL:
    """Validate every connection field before importing app settings or connecting.

    Literal loopback addresses avoid DNS ambiguity. Query parameters are forbidden:
    libpq host/hostaddr/service overrides could otherwise redirect a local URL.
    Verification credentials use URL-safe characters, including through Alembic's
    ConfigParser URL setting, which does not accept literal percent escapes.
    """
    try:
        url = make_url(raw)
    except (ArgumentError, ValueError) as exc:
        raise VerificationError("invalid database URL") from exc
    if url.drivername not in {"postgresql", "postgresql+asyncpg", "postgresql+psycopg2"}:
        raise VerificationError("a PostgreSQL URL is required")
    if url.host not in {"127.0.0.1", "::1"}:
        raise VerificationError("only literal loopback hosts 127.0.0.1 or ::1 are permitted")
    if url.port is None or not 1 <= url.port <= 65535:
        raise VerificationError("an explicit local PostgreSQL port is required")
    if url.query:
        raise VerificationError("URL query parameters are forbidden (connection overrides)")
    if not re.fullmatch(r"mis_sim_verify_[a-z0-9_]+", url.database or "") or len(url.database) > 63:
        raise VerificationError(f"database name must start with {DATABASE_PREFIX} and use a-z, 0-9, _ (max 63 characters)")
    for field in (url.username, url.password):
        if not field or not re.fullmatch(r"[A-Za-z0-9_-]+", field):
            raise VerificationError("explicit verification username and password must use A-Z, a-z, 0-9, _ or -")
    return url.set(drivername="postgresql+asyncpg")


def require_empty_database(engine, database: str) -> str:
    """Read-only preflight covers relations in every user schema, including views."""
    with engine.connect() as connection:
        actual, address, version = connection.execute(text(
            "SELECT current_database(), host(inet_server_addr()), version()"
        )).one()
        if actual != database or address not in {"127.0.0.1", "::1"}:
            raise VerificationError("connected database or server address differs from the disposable target")
        relations = connection.execute(text("""
            SELECT n.nspname, c.relname
            FROM pg_catalog.pg_class AS c
            JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
            WHERE n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'
              AND c.relkind IN ('r', 'p', 'v', 'm', 'S', 'f')
            ORDER BY n.nspname, c.relname
        """)).all()
        if relations:
            names = ", ".join(f"{schema}.{name}" for schema, name in relations)
            raise VerificationError(f"database is not empty; refusing before migrations: {names}")
        return version


def verify_schema(engine, models) -> list[str]:
    from app.simulation import models as simulation_models

    models_for_schema = expected_models(models, simulation_models)
    expected = {model.__tablename__ for model in models_for_schema}
    if len(expected) != EXPECTED_TABLE_COUNT:
        raise VerificationError(f"expected {EXPECTED_TABLE_COUNT} runtime table models; found {len(expected)}")
    inspector = inspect(engine)
    actual = set(inspector.get_table_names(schema="public"))
    if actual != expected | {"alembic_version"}:
        raise VerificationError(f"migrated tables differ: {sorted(actual)}")
    for name in sorted(expected):
        columns = {column["name"]: column for column in inspector.get_columns(name, schema="public")}
        column = columns.get("instance_id")
        if column is None or column["nullable"] or not isinstance(column["type"], Integer):
            raise VerificationError(f"{name}.instance_id must be a non-null integer")
    return sorted(expected)


def verify_results(session, models, instance_id: int, team_id: int) -> dict:
    from app.simulation import models as simulation_models

    models_for_schema = expected_models(models, simulation_models)
    result = models.RoundResult
    rows = session.scalars(select(result).where(
        result.instance_id == instance_id, result.team_id == team_id,
    ).order_by(result.round)).all()
    if [row.round for row in rows] != EXPECTED_ROUNDS:
        raise VerificationError(f"expected persisted rounds {EXPECTED_ROUNDS}; found {[row.round for row in rows]}")
    for row in rows:
        payload = row.payload
        if (payload.get("instance_id"), payload.get("team_id"), payload.get("round")) != (
            instance_id, team_id, row.round,
        ) or not payload.get("capabilities") or not payload.get("financials"):
            raise VerificationError(f"round {row.round}: incomplete or incorrectly scoped persisted payload")
    counts = {}
    for model in models_for_schema:
        counts[model.__tablename__] = session.scalar(select(func.count()).select_from(model).where(
            model.instance_id == instance_id, model.team_id == team_id,
        ))
    return {
        "instance_id": instance_id, "team_id": team_id,
        "persisted_rounds": [row.round for row in rows], "scoped_row_counts": counts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", required=True, help="explicit empty mis_sim_verify_* database on a literal loopback address")
    args = parser.parse_args()
    try:
        url = disposable_url(args.database_url)
        # Never let PGHOSTADDR/PGSERVICE/PGOPTIONS (etc.) redirect this process or
        # its Alembic child. App settings receive only the validated explicit URL.
        for key in list(os.environ):
            if key.startswith("PG"):
                del os.environ[key]
        database_url = url.render_as_string(hide_password=False)
        os.environ["DATABASE_URL"] = database_url
        sys.path.insert(0, str(BACKEND))

        from alembic.config import Config
        from alembic.script import ScriptDirectory
        from app.round import models
        from app.round.db import make_engine, session_for
        from seeds.riverside_full import INSTANCE_ID, TEAM_ID, run_full_game

        engine = make_engine(database_url)
        try:
            version = require_empty_database(engine, url.database)
            print(f"Empty disposable database confirmed: {url.host}:{url.port}/{url.database}", flush=True)
            env = dict(os.environ, PYTHONPATH=str(BACKEND))
            subprocess.run(
                [sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"],
                cwd=BACKEND, env=env, check=True, timeout=120,
            )
            tables = verify_schema(engine, models)
            config = Config(str(BACKEND / "alembic.ini"))
            config.set_main_option("script_location", str(BACKEND / "alembic"))
            heads = set(ScriptDirectory.from_config(config).get_heads())
            with engine.connect() as connection:
                revisions = set(connection.scalars(text("SELECT version_num FROM public.alembic_version")))
            if revisions != heads:
                raise VerificationError(f"migration revision mismatch: {sorted(revisions)} != {sorted(heads)}")
            with session_for(database_url) as session:
                run_full_game(session)
            # A separate session proves committed database state, not returned seed values.
            with session_for(database_url) as session:
                summary = verify_results(session, models, INSTANCE_ID, TEAM_ID)
            summary.update({
                "postgresql": version, "database": url.database,
                "alembic_heads": sorted(revisions), "runtime_tables_with_instance_id": tables,
            })
            print(json.dumps(summary, indent=2, sort_keys=True))
            print("PASS: PostgreSQL migrations and six committed rounds verified; retain this database for audit, then use the documented scoped cleanup.")
            return 0
        finally:
            engine.dispose()
    except VerificationError as exc:
        print(f"REFUSED/FAILED: {exc}", file=sys.stderr)
    except (SQLAlchemyError, ImportError, subprocess.SubprocessError) as exc:
        # Connection errors can embed credentials; report the class without echoing a URL.
        print(f"FAILED: {type(exc).__name__}; check declared dependencies and disposable PostgreSQL prerequisites. No verification success is claimed.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
