"""Add grading tables for M5.5 grade derivation and export."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261002_0009"
down_revision: Union[str, None] = "20260915_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "grade_config",
        sa.Column("instance_id", sa.Integer(), nullable=False),
        sa.Column("weight_financial", sa.Float(), nullable=False, server_default="0.25"),
        sa.Column("weight_customer", sa.Float(), nullable=False, server_default="0.25"),
        sa.Column("weight_internal_process", sa.Float(), nullable=False, server_default="0.25"),
        sa.Column("weight_learning_growth", sa.Float(), nullable=False, server_default="0.25"),
        sa.Column("rounds_mode", sa.String(length=16), nullable=False, server_default="final"),
        sa.Column("updated_by", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["instance_id"], ["simulation_instance.instance_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by"], ["user.id"]),
        sa.PrimaryKeyConstraint("instance_id"),
    )
    op.create_table(
        "grade_override",
        sa.Column("instance_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("override", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("reason", sa.String(length=256), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["instance_id"], ["simulation_instance.instance_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["team.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by"], ["user.id"]),
        sa.PrimaryKeyConstraint("instance_id", "team_id"),
    )


def downgrade() -> None:
    op.drop_table("grade_override")
    op.drop_table("grade_config")
