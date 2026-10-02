"""Add archived to simulation_instance status CHECK constraint.

Revision ID: 20261002_0010
Revises: 20261002_0009
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261002_0010"
down_revision: Union[str, None] = "20261002_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite does not support ALTER TABLE ... DROP CONSTRAINT / ADD CONSTRAINT.
    # The CHECK constraint is enforced at the application/ORM level for SQLite.
    # For PostgreSQL, replace the CHECK constraint.
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.drop_constraint("ck_simulation_instance_status", "simulation_instance", type_="check")
        op.create_check_constraint(
            "ck_simulation_instance_status",
            "simulation_instance",
            "status IN ('setup', 'active', 'paused', 'completed', 'archived')",
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.drop_constraint("ck_simulation_instance_status", "simulation_instance", type_="check")
        op.create_check_constraint(
            "ck_simulation_instance_status",
            "simulation_instance",
            "status IN ('setup', 'active', 'paused', 'completed')",
        )
