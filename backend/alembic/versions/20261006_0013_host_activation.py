"""Reconcile overdue presentation hosts against authoritative runs.

Revision ID: 20261006_0013
Revises: 20261006_0012
"""
from alembic import op
import sqlalchemy as sa

revision = "20261006_0013"
down_revision = "20261006_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("""
        UPDATE host_platform SET status = 'active'
        WHERE status = 'pending' AND created_round >= 1
          AND activated_round = CAST(created_round AS BIGINT) + 1
          AND EXISTS (
              SELECT 1 FROM simulation_run_v1 AS run
              WHERE run.instance_id = host_platform.instance_id
                AND run.team_id = host_platform.team_id
                AND host_platform.activated_round <= run.current_round
          )
    """))


def downgrade() -> None:
    # A status-only repair has no lossless inverse: original active rows and
    # repaired rows cannot be distinguished. Preserve all data on downgrade.
    pass
