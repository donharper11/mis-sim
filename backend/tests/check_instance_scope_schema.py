#!/usr/bin/env python3
"""Static metadata guard for the amended 19-table instance-scope boundary."""

from __future__ import annotations

import importlib.util
from pathlib import Path


from app.round import models as round_models
from app.simulation import models as simulation_models

EXPECTED = {
    "team_state", "arch_node", "arch_edge", "deployment_org_state", "platform_service",
    "org_unit", "it_staff", "governance_state", "policy_decision", "stakeholder_alignment",
    "in_flight", "decision_line", "signal", "debt_item", "tco_forecast", "round_result",
    "simulation_run_v1", "simulation_sheet_v1", "simulation_checkpoint_v1",
}

models = (*round_models.ALL_TABLES, *simulation_models.ALL_TABLES)
actual = {model.__tablename__ for model in models}
assert actual == EXPECTED, f"runtime inventory mismatch: {sorted(actual ^ EXPECTED)}"
for model in models:
    column = model.__table__.c.get("instance_id")
    assert column is not None, f"{model.__tablename__} missing instance_id"
    assert not column.nullable, f"{model.__tablename__}.instance_id is nullable"

# The migration declares one direct restrictive FK per imported runtime model.
_path = Path(__file__).parents[1] / "alembic" / "versions" / "20260915_0005_instance_scope.py"
_spec = importlib.util.spec_from_file_location("m2_scope_migration", _path)
migration = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(migration)

assert len(migration.EXPECTED_RUNTIME_TABLES) == 19
assert len(migration.RUNTIME_TABLES) == 19
assert {f"fk_{table}_instance" for table in migration.RUNTIME_TABLES} == {
    f"fk_{table}_instance" for table in EXPECTED
}
print("instance-scope schema guard green: 19 non-null direct restrictive FKs declared")
