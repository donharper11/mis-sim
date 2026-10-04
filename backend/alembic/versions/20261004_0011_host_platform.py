"""Add host_platform and host_platform_member tables.

Revision ID: 20261004_0011
Revises: 20261002_0010
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261004_0011"
down_revision: Union[str, None] = "20261002_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "host_platform",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("instance_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("platform_code", sa.String(16), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("notes", sa.String(1000), nullable=True),
        sa.Column("platform_type", sa.String(16), nullable=False),
        sa.Column("cloud_subtype", sa.String(16), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("created_round", sa.Integer(), nullable=False),
        sa.Column("activated_round", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["instance_id"], ["simulation_instance.instance_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["team.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("instance_id", "team_id", "platform_code", name="uq_host_platform_code"),
        sa.CheckConstraint("platform_type IN ('on_prem', 'cloud')", name="ck_host_platform_type"),
        sa.CheckConstraint("cloud_subtype IS NULL OR cloud_subtype IN ('iaas', 'paas', 'saas', 'aiaas')", name="ck_host_platform_cloud_subtype"),
        sa.CheckConstraint("status IN ('pending', 'active', 'retired')", name="ck_host_platform_status"),
    )

    op.create_table(
        "host_platform_member",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("platform_id", sa.Integer(), nullable=False),
        sa.Column("asset_key", sa.String(64), nullable=False),
        sa.Column("member_kind", sa.String(16), nullable=False),
        sa.Column("assigned_round", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["platform_id"], ["host_platform.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("platform_id", "asset_key", name="uq_host_platform_member_asset"),
    )


def downgrade() -> None:
    op.drop_table("host_platform_member")
    op.drop_table("host_platform")
