"""Synchronous session for the round runner -- the ONLY session-touching layer 1.6 adds.

The engine is pure (1.4 I2, 1.5 I2); this module lives outside ``app.engine`` so the engine
purity grep (``check_engine_purity.py``) never sees a session import. The runner is a
deterministic batch process (lock -> advance -> write RoundResult), so a synchronous session
is the honest fit; the app's async session (``app.database``) stays for the request path.

``session_for(url)`` builds a fresh engine + session for a given database URL, deriving a sync
driver from the configured async URL when none is passed (``+asyncpg`` -> plain psycopg2). The
invariant guards and the isolation canary pass an in-memory SQLite URL; ``--full`` and the
migration demo use the Postgres URL from settings.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models.base import Base
from app.round import models  # noqa: F401  -- register the tables on Base.metadata


def sync_url(url: str | None = None) -> str:
    """A synchronous SQLAlchemy URL. Strips an async driver from the configured URL."""
    raw = url or settings.DATABASE_URL
    return raw.replace("+asyncpg", "").replace("+aiosqlite", "")


def make_engine(url: str | None = None):
    return create_engine(sync_url(url), future=True)


def create_all(engine) -> None:
    """Create every round-runner table (used by the guards/canary on SQLite; the Postgres
    path uses the Alembic migration instead)."""
    Base.metadata.create_all(engine, tables=[t.__table__ for t in models.ALL_TABLES])


def drop_all(engine) -> None:
    Base.metadata.drop_all(engine, tables=[t.__table__ for t in models.ALL_TABLES])


@contextmanager
def session_for(url: str | None = None) -> Iterator[Session]:
    engine = make_engine(url)
    factory = sessionmaker(bind=engine, future=True, expire_on_commit=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
