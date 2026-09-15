"""Add the versioned production simulation run/checkpoint tables."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260914_0003"
down_revision: Union[str, None] = "20260822_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "simulation_run_v1",
        sa.Column("instance_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("pack_key", sa.String(length=64), nullable=False),
        sa.Column("pack_version", sa.String(length=48), nullable=False),
        sa.Column("pack_digest", sa.String(length=64), nullable=False),
        sa.Column("current_round", sa.Integer(), nullable=False),
        sa.Column("advanced_round", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.PrimaryKeyConstraint("instance_id", "team_id"),
        sa.CheckConstraint("version = 1", name="ck_simulation_run_v1_version"),
        sa.CheckConstraint("current_round >= 1", name="ck_simulation_run_v1_current_round"),
        sa.CheckConstraint("advanced_round >= 0", name="ck_simulation_run_v1_advanced_round"),
        sa.CheckConstraint("status IN ('draft', 'locked', 'completed')", name="ck_simulation_run_v1_status"),
    )
    op.create_table(
        "simulation_sheet_v1",
        sa.Column("instance_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("locked_revision", sa.Integer(), nullable=True),
        sa.Column("commands", sa.JSON(), nullable=False),
        sa.Column("sheet_digest", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(
            ["instance_id", "team_id"],
            ["simulation_run_v1.instance_id", "simulation_run_v1.team_id"],
            name="fk_simulation_sheet_v1_run",
        ),
        sa.PrimaryKeyConstraint("instance_id", "team_id", "round"),
        sa.CheckConstraint("round >= 1", name="ck_simulation_sheet_v1_round"),
        sa.CheckConstraint("revision >= 0", name="ck_simulation_sheet_v1_revision"),
        sa.CheckConstraint("locked_revision IS NULL OR locked_revision >= 0", name="ck_simulation_sheet_v1_locked_revision"),
    )
    op.create_table(
        "simulation_checkpoint_v1",
        sa.Column("instance_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("pack_digest", sa.String(length=64), nullable=False),
        sa.Column("sheet_revision", sa.Integer(), nullable=True),
        sa.Column("state", sa.JSON(), nullable=False),
        sa.Column("state_digest", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["instance_id", "team_id"],
            ["simulation_run_v1.instance_id", "simulation_run_v1.team_id"],
            name="fk_simulation_checkpoint_v1_run",
        ),
        sa.PrimaryKeyConstraint("instance_id", "team_id", "round"),
        sa.CheckConstraint("version = 1", name="ck_simulation_checkpoint_v1_version"),
        sa.CheckConstraint("round >= 0", name="ck_simulation_checkpoint_v1_round"),
        sa.CheckConstraint("sheet_revision IS NULL OR sheet_revision >= 0", name="ck_simulation_checkpoint_v1_sheet_revision"),
    )


def downgrade() -> None:
    op.drop_table("simulation_checkpoint_v1")
    op.drop_table("simulation_sheet_v1")
    op.drop_table("simulation_run_v1")

