"""Migrate and initialize a fresh, explicitly local readiness database.

Usage: python backend/scripts/seed_readiness_demo.py --database-url <URL>
Refuses non-local URLs, non-readiness database names and existing user rows.
Never drops data. Creates the demo cohort/users and four round-one runtime teams.
"""
from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path
import subprocess
import sys

from sqlalchemy import func, select
from sqlalchemy.engine import make_url


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", required=True)
    args = parser.parse_args()
    url = make_url(args.database_url)
    if url.drivername not in {"postgresql+asyncpg", "sqlite+aiosqlite"} or url.query:
        parser.error("Use PostgreSQL+asyncpg or SQLite+aiosqlite without URL query overrides")
    if url.drivername == "postgresql+asyncpg":
        if url.host != "127.0.0.1" or not url.port or not (url.database or "").startswith("mis_sim_browser_"):
            parser.error("Use 127.0.0.1, an explicit port, and a mis_sim_browser_ database")
    elif not str(Path(url.database or "").resolve()).startswith("/tmp/mis_sim_browser_"):
        parser.error("SQLite path must start with /tmp/mis_sim_browser_")
    backend = Path(__file__).resolve().parents[1]
    os.environ["DATABASE_URL"] = args.database_url
    os.environ.setdefault("SECRET_KEY", "mis-sim-readiness-local-only")
    # Prevent ambient libpq variables from redirecting a local rehearsal.
    for key in list(os.environ):
        if key.startswith("PG"):
            del os.environ[key]
    sys.path.insert(0, str(backend))
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=backend, check=True)
    from app.database import async_session, engine as async_engine
    from app.models.platform import User, Team, SimulationInstance
    from app.seed.demo import seed_cohort, seed_users
    from app.casepack.registry import resolve_runtime_pack
    from app.round.db import make_engine
    from app.simulation.service import SimulationService
    from sqlalchemy.orm import Session

    async def seed():
        try:
            async with async_session() as session:
                if await session.scalar(select(func.count(User.id))):
                    raise SystemExit("REFUSED: database already has users; use a fresh disposable database")
                cohort = await seed_cohort(session)
                await seed_users(session, cohort)
                await session.commit()
        finally:
            await async_engine.dispose()
    asyncio.run(seed())
    engine = make_engine()
    try:
        # initialize owns its transaction. Close the read session before invoking it,
        # and defer instance writes until every team is initialized (SQLite has one writer).
        with Session(engine) as session:
            work = []
            for instance in session.scalars(select(SimulationInstance)):
                pack = resolve_runtime_pack(session, instance.pack_key, instance.pack_version)
                team_ids = list(session.scalars(select(Team.id).where(Team.instance_id == instance.instance_id)))
                work.append((instance.instance_id, pack, team_ids))
        for instance_id, pack, team_ids in work:
            for team_id in team_ids:
                SimulationService(engine, pack).initialize(instance_id, team_id, "cost_leadership")
        with Session(engine) as session:
            for instance_id, _, _ in work:
                instance = session.get(SimulationInstance, instance_id)
                instance.current_round = 1
                instance.status = "active"
            session.commit()
    finally:
        engine.dispose()
    print("Ready: two sections, four round-one teams; accounts in docs/demo-accounts.md")


if __name__ == "__main__":
    main()
