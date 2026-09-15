"""Add the platform-level immutable casepack registry."""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260915_0006"
down_revision: Union[str, None] = "20260915_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("simulation_instance", sa.Column("pack_digest", sa.String(length=64), nullable=True))
    op.create_table(
        "casepack",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("pack_key", sa.String(length=128), nullable=False),
        sa.Column("pack_version", sa.String(length=64), nullable=False),
        sa.Column("pack_digest", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("vertical", sa.String(length=128), nullable=False),
        sa.Column("rounds", sa.Integer(), nullable=False),
        sa.Column("path", sa.String(length=1024), nullable=False),
        sa.Column("validation_json", sa.JSON(), nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("registered_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["registered_by"], ["user.id"], name="fk_casepack_registered_by", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pack_key", "pack_version", name="uq_casepack_key_version"),
    )


def downgrade() -> None:
    op.drop_column("simulation_instance", "pack_digest")
    op.drop_table("casepack")
