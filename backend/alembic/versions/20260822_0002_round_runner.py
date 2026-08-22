"""round runner runtime tables (module 1.6)

Every table carries ``instance_id`` NON-NULL from creation (GOVERNANCE section 4.5, 1.6
decision 1). No ``simulation_instance`` table exists yet -- 2.1 creates it and adds the FK
(pre-flight row 4); here ``instance_id`` is an unconstrained non-null integer.

Reversible: ``downgrade`` drops every table, so ``upgrade`` -> ``downgrade`` -> ``upgrade``
is clean (spec build step 1).

Revision ID: 20260822_0002
Revises: 20260726_0001
Create Date: 2026-08-22
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260822_0002"
down_revision: Union[str, None] = "20260726_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _iid() -> sa.Column:
    return sa.Column("instance_id", sa.Integer(), nullable=False)


def _team() -> sa.Column:
    return sa.Column("team_id", sa.Integer(), nullable=False)


def upgrade() -> None:
    op.create_table(
        "team_state",
        _iid(), _team(),
        sa.Column("current_round", sa.Integer(), nullable=False),
        sa.Column("declared_strategy", sa.String(), nullable=False),
        sa.Column("declared_strategy_round", sa.Integer(), nullable=False),
        sa.Column("cash", sa.Integer(), nullable=False),
        sa.Column("opex_runrate", sa.Integer(), nullable=False),
        sa.Column("locked_round", sa.Integer(), nullable=True),
        sa.Column("advanced_round", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("instance_id", "team_id"),
    )

    op.create_table(
        "arch_node",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        _iid(), _team(),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("roles_filled", sa.JSON(), nullable=False),
        sa.Column("availability", sa.Float(), nullable=False),
        sa.Column("installed_round", sa.Integer(), nullable=False),
        sa.Column("service_life_rounds", sa.Integer(), nullable=False),
        sa.Column("serves", sa.JSON(), nullable=False),
        sa.Column("throughput", sa.Float(), nullable=True),
        sa.Column("owns_entities", sa.JSON(), nullable=False),
        sa.Column("placement", sa.String(), nullable=True),
        sa.Column("opex_contribution", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_arch_node_instance_id", "arch_node", ["instance_id"])

    op.create_table(
        "arch_edge",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        _iid(), _team(),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("src", sa.String(), nullable=False),
        sa.Column("dst", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_arch_edge_instance_id", "arch_edge", ["instance_id"])

    op.create_table(
        "deployment_org_state",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        _iid(), _team(),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("catalog_key", sa.String(), nullable=False),
        sa.Column("org_unit", sa.String(), nullable=False),
        sa.Column("people_affected", sa.Integer(), nullable=False),
        sa.Column("trained_count", sa.Integer(), nullable=False),
        sa.Column("process", sa.String(), nullable=False),
        sa.Column("adoption", sa.Float(), nullable=False),
        sa.Column("ever_trained", sa.Boolean(), nullable=False),
        sa.Column("serves", sa.JSON(), nullable=False),
        sa.Column("is_primary_for", sa.String(), nullable=True),
        sa.Column("initiated", sa.Boolean(), nullable=False),
        sa.Column("abandoned", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_deployment_org_state_instance_id", "deployment_org_state", ["instance_id"])

    op.create_table(
        "platform_service",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        _iid(), _team(),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("placement", sa.String(), nullable=True),
        sa.Column("capacity", sa.Float(), nullable=False),
        sa.Column("utilisation", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_platform_service_instance_id", "platform_service", ["instance_id"])

    op.create_table(
        "org_unit",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        _iid(), _team(),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("headcount", sa.Integer(), nullable=False),
        sa.Column("resistance", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_org_unit_instance_id", "org_unit", ["instance_id"])

    op.create_table(
        "it_staff",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        _iid(), _team(),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("staff_fte", sa.Float(), nullable=False),
        sa.Column("load_fte", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_it_staff_instance_id", "it_staff", ["instance_id"])

    op.create_table(
        "governance_state",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        _iid(), _team(),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("capability", sa.String(), nullable=False),
        sa.Column("owner_assigned", sa.Boolean(), nullable=False),
        sa.Column("sponsor_assigned", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_governance_state_instance_id", "governance_state", ["instance_id"])

    op.create_table(
        "policy_decision",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        _iid(), _team(),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("policy", sa.String(), nullable=False),
        sa.Column("selected", sa.String(), nullable=False),
        sa.Column("actively_decided", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_policy_decision_instance_id", "policy_decision", ["instance_id"])

    op.create_table(
        "stakeholder_alignment",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        _iid(), _team(),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("stakeholder", sa.String(), nullable=False),
        sa.Column("alignment", sa.Float(), nullable=False),
        sa.Column("cares_about", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stakeholder_alignment_instance_id", "stakeholder_alignment", ["instance_id"])

    op.create_table(
        "in_flight",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        _iid(), _team(),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("catalog_key", sa.String(), nullable=False),
        sa.Column("ordered_round", sa.Integer(), nullable=False),
        sa.Column("arrival_round", sa.Integer(), nullable=False),
        sa.Column("capex", sa.Integer(), nullable=False),
        sa.Column("node_payload", sa.JSON(), nullable=False),
        sa.Column("materialised", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_in_flight_instance_id", "in_flight", ["instance_id"])

    op.create_table(
        "decision_line",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        _iid(), _team(),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("capability", sa.String(), nullable=True),
        sa.Column("capex", sa.Integer(), nullable=False),
        sa.Column("rgt_tag", sa.String(), nullable=False),
        sa.Column("is_maintenance", sa.Boolean(), nullable=False),
        sa.Column("action_type", sa.String(), nullable=True),
        sa.Column("target_key", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_decision_line_instance_id", "decision_line", ["instance_id"])

    op.create_table(
        "signal",
        _iid(), _team(),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("episode_id", sa.Integer(), nullable=False),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("capability", sa.String(), nullable=False),
        sa.Column("metric", sa.String(), nullable=False),
        sa.Column("metric_kind", sa.String(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("first_shown_round", sa.Integer(), nullable=False),
        sa.Column("cleared_round", sa.Integer(), nullable=True),
        sa.Column("fire_round", sa.Integer(), nullable=True),
        sa.Column("cleared_by", sa.JSON(), nullable=False),
        sa.Column("was_actionable", sa.Boolean(), nullable=False),
        sa.Column("cheapest_fix_when_raised", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("instance_id", "team_id", "key", "episode_id"),
    )

    op.create_table(
        "debt_item",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        _iid(), _team(),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("capability", sa.String(), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("source_key", sa.String(), nullable=True),
        sa.Column("reason", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_debt_item_instance_id", "debt_item", ["instance_id"])

    op.create_table(
        "tco_forecast",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        _iid(), _team(),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("item", sa.String(), nullable=False),
        sa.Column("forecast", sa.Integer(), nullable=False),
        sa.Column("actual", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tco_forecast_instance_id", "tco_forecast", ["instance_id"])

    op.create_table(
        "round_result",
        _iid(), _team(),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("instance_id", "team_id", "round"),
    )


def downgrade() -> None:
    for name in (
        "round_result", "tco_forecast", "debt_item", "signal", "decision_line", "in_flight",
        "stakeholder_alignment", "policy_decision", "governance_state", "it_staff", "org_unit",
        "platform_service", "deployment_org_state", "arch_edge", "arch_node", "team_state",
    ):
        op.drop_table(name)
