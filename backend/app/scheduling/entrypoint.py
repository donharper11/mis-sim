"""Fixed-time scheduling command boundary.

Examples:
    python -m app.scheduling.entrypoint --instance 12 --at 2026-09-15T12:00:00Z
    python -m app.scheduling.entrypoint --instance 12
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import settings
from app.round.db import sync_url
from .service import Scheduler


def _at(raw: str | None) -> datetime:
    if raw is not None:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    else:
        value = datetime.now(timezone.utc)
    if value.tzinfo is None or value.utcoffset() is None:
        raise SystemExit("--at must include a timezone offset")
    return value.astimezone(timezone.utc)


def main() -> int:
    parser = argparse.ArgumentParser(prog="app.scheduling.entrypoint")
    parser.add_argument("--instance", type=int, required=True)
    parser.add_argument("--round", type=int)
    parser.add_argument("--at", help="explicit timezone-aware ISO timestamp")
    parser.add_argument("--database-url", default=None)
    args = parser.parse_args()
    engine = create_engine(sync_url(args.database_url or settings.DATABASE_URL), future=True)
    try:
        with Session(engine, expire_on_commit=False) as session:
            results = Scheduler(session).tick(_at(args.at))
            if args.round is not None:
                results = [item for item in results if item["instance_id"] == args.instance and item["round_number"] == args.round]
            else:
                results = [item for item in results if item["instance_id"] == args.instance]
            for item in results:
                print(item)
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
