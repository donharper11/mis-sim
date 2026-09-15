"""Add the complete M2 runtime instance-scope foreign-key boundary."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.round import models as round_models
from app.simulation import models as simulation_models

revision: str = "20260915_0005"
down_revision: Union[str, None] = "20260915_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EXPECTED_RUNTIME_TABLES = frozenset({
    "team_state", "arch_node", "arch_edge", "deployment_org_state", "platform_service",
    "org_unit", "it_staff", "governance_state", "policy_decision", "stakeholder_alignment",
    "in_flight", "decision_line", "signal", "debt_item", "tco_forecast", "round_result",
    "simulation_run_v1", "simulation_sheet_v1", "simulation_checkpoint_v1",
})

# Children are handled first on SQLite so the run table remains available while its
# existing composite references are copied by batch operations.
RUNTIME_TABLES = tuple(model.__tablename__ for model in (
    *round_models.ALL_TABLES,
    simulation_models.SimulationSheetV1,
    simulation_models.SimulationCheckpointV1,
    simulation_models.SimulationRunV1,
))


def _assert_inventory() -> None:
    imported = frozenset(model.__tablename__ for model in (
        *round_models.ALL_TABLES,
        *simulation_models.ALL_TABLES,
    ))
    if imported != EXPECTED_RUNTIME_TABLES:
        raise RuntimeError(
            "M2 2.2 runtime inventory mismatch: "
            f"expected={sorted(EXPECTED_RUNTIME_TABLES)} imported={sorted(imported)}"
        )
    for model in (*round_models.ALL_TABLES, *simulation_models.ALL_TABLES):
        column = model.__table__.c.get("instance_id")
        if column is None or column.nullable:
            raise RuntimeError(f"M2 2.2 requires non-null instance_id: {model.__tablename__}")


def _assert_no_orphans(bind) -> None:
    for table in sorted(EXPECTED_RUNTIME_TABLES):
        rows = bind.execute(sa.text(
            f"SELECT r.instance_id FROM {table} AS r "
            "LEFT JOIN simulation_instance AS i ON i.instance_id = r.instance_id "
            "WHERE i.instance_id IS NULL LIMIT 5"
        )).fetchall()
        if rows:
            sample = [row[0] for row in rows]
            raise RuntimeError(f"M2 2.2 orphan instance_id values in {table}: {sample}")


def _sqlite_fk_mode(bind, enabled: bool) -> None:
    if bind.dialect.name == "sqlite":
        bind.exec_driver_sql(f"PRAGMA foreign_keys={'ON' if enabled else 'OFF'}")


def _add_fk(bind, table: str) -> None:
    name = f"fk_{table}_instance"
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table(table, recreate="always") as batch:
            batch.create_foreign_key(
                name, "simulation_instance", ["instance_id"], ["instance_id"], ondelete="RESTRICT"
            )
    else:
        op.create_foreign_key(
            name, table, "simulation_instance", ["instance_id"], ["instance_id"], ondelete="RESTRICT"
        )


def _drop_fk(bind, table: str) -> None:
    name = f"fk_{table}_instance"
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table(table, recreate="always") as batch:
            batch.drop_constraint(name, type_="foreignkey")
    else:
        op.drop_constraint(name, table, type_="foreignkey")


def upgrade() -> None:
    _assert_inventory()
    bind = op.get_bind()
    _assert_no_orphans(bind)
    # SQLite batch recreation needs temporary enforcement off while a referenced
    # runtime table is copied. The preflight and the newly-created restrictive FKs
    # restore the invariant before this migration returns.
    _sqlite_fk_mode(bind, False)
    try:
        for table in RUNTIME_TABLES:
            _add_fk(bind, table)
    finally:
        _sqlite_fk_mode(bind, True)


def downgrade() -> None:
    _assert_inventory()
    bind = op.get_bind()
    _sqlite_fk_mode(bind, False)
    try:
        for table in reversed(RUNTIME_TABLES):
            _drop_fk(bind, table)
    finally:
        _sqlite_fk_mode(bind, True)
