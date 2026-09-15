"""Add deterministic instance-scoped round schedules."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260915_0008"
down_revision: Union[str, None] = "20260915_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("team", schema=None) as batch:
        batch.create_unique_constraint("uq_team_instance_identity", ["id", "instance_id"])

    op.create_table(
        "round_schedule",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("instance_id", sa.Integer(), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("auto_advance", sa.Boolean(), nullable=False),
        sa.Column("grace_period_minutes", sa.Integer(), nullable=False),
        sa.Column("decisions_locked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("lock_reason", sa.String(length=32), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("advanced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("claim_token", sa.String(length=64), nullable=True),
        sa.Column("claim_until", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["instance_id"], ["simulation_instance.instance_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("instance_id", "round_number", name="uq_round_schedule_instance_round"),
        sa.UniqueConstraint("id", "instance_id", name="uq_round_schedule_identity"),
        sa.UniqueConstraint("claim_token", name="uq_round_schedule_claim_token"),
        sa.CheckConstraint("round_number >= 1", name="ck_round_schedule_round"),
        sa.CheckConstraint("deadline > start_at", name="ck_round_schedule_deadline"),
        sa.CheckConstraint("grace_period_minutes >= 0", name="ck_round_schedule_grace"),
        sa.CheckConstraint("lock_reason IS NULL OR lock_reason IN ('deadline_expired', 'instructor_locked')", name="ck_round_schedule_lock_reason"),
    )
    op.create_table(
        "round_schedule_team",
        sa.Column("schedule_id", sa.Integer(), nullable=False),
        sa.Column("instance_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("locked_revision", sa.Integer(), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("advanced_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["schedule_id", "instance_id"], ["round_schedule.id", "round_schedule.instance_id"], name="fk_round_schedule_team_schedule", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id", "instance_id"], ["team.id", "team.instance_id"], name="fk_round_schedule_team_team", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("schedule_id", "team_id"),
        sa.CheckConstraint("locked_revision IS NULL OR locked_revision >= 0", name="ck_round_schedule_team_locked_revision"),
    )


def downgrade() -> None:
    op.drop_table("round_schedule_team")
    op.drop_table("round_schedule")
    with op.batch_alter_table("team", schema=None) as batch:
        batch.drop_constraint("uq_team_instance_identity", type_="unique")
