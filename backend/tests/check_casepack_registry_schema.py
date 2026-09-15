"""Static schema guard for the platform-level casepack registry."""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, inspect

from app.models.base import Base
from app.models.platform import Casepack, SimulationInstance, User


def main() -> int:
    engine = create_engine(os.environ.get("REGISTRY_SCHEMA_URL", "sqlite:///:memory:"))
    Base.metadata.create_all(engine, tables=[User.__table__, SimulationInstance.__table__, Casepack.__table__])
    info = inspect(engine)
    columns = {item["name"] for item in info.get_columns("casepack")}
    expected = {"id", "pack_key", "pack_version", "pack_digest", "schema_version", "display_name", "vertical", "rounds", "path", "validation_json", "registered_at", "registered_by"}
    assert columns == expected, (columns, expected)
    assert "instance_id" not in columns
    assert "pack_digest" in {item["name"] for item in info.get_columns("simulation_instance")}
    uniques = info.get_unique_constraints("casepack")
    assert any(set(item["column_names"]) == {"pack_key", "pack_version"} for item in uniques)
    print("casepack registry schema: PASS (metadata-only, unique tuple, no instance_id)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
