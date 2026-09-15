"""Create the M2 platform hierarchy and identity foundation."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260915_0004"
down_revision: Union[str, None] = "20260914_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.String(length=64), nullable=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", name="uq_user_student_id"),
        sa.UniqueConstraint("email", name="uq_user_email"),
        sa.CheckConstraint("role IN ('student', 'ta', 'instructor', 'admin')", name="ck_user_role"),
    )
    op.create_table(
        "course",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("course_code", sa.String(length=64), nullable=False),
        sa.Column("course_name", sa.String(length=200), nullable=False),
        sa.Column("academic_year", sa.String(length=32), nullable=False),
        sa.Column("semester", sa.String(length=32), nullable=False),
        sa.Column("instructor_id", sa.Integer(), nullable=False),
        sa.Column("active_chapters", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["instructor_id"], ["user.id"], name="fk_course_instructor", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "section",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("section_code", sa.String(length=64), nullable=False),
        sa.Column("section_name", sa.String(length=200), nullable=False),
        sa.Column("max_teams", sa.Integer(), nullable=False),
        sa.Column("team_size_min", sa.Integer(), nullable=False),
        sa.Column("team_size_max", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["course.id"], name="fk_section_course", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "section_code", name="uq_section_course_code"),
    )
    op.create_table(
        "simulation_instance",
        sa.Column("instance_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("section_id", sa.Integer(), nullable=False),
        sa.Column("pack_key", sa.String(length=128), nullable=False),
        sa.Column("pack_version", sa.String(length=64), nullable=False),
        sa.Column("current_round", sa.Integer(), nullable=False),
        sa.Column("total_rounds", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("settings", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["section_id"], ["section.id"], name="fk_instance_section", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("instance_id"),
        sa.UniqueConstraint("section_id", name="uq_simulation_instance_section"),
        sa.UniqueConstraint("instance_id", "section_id", name="uq_simulation_instance_identity"),
        sa.CheckConstraint("status IN ('setup', 'active', 'paused', 'completed')", name="ck_simulation_instance_status"),
        sa.CheckConstraint("current_round >= 0", name="ck_simulation_instance_current_round"),
        sa.CheckConstraint("total_rounds > 0", name="ck_simulation_instance_total_rounds"),
    )
    op.create_table(
        "team",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("section_id", sa.Integer(), nullable=False),
        sa.Column("instance_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["section_id"], ["section.id"], name="fk_team_section", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["instance_id", "section_id"], ["simulation_instance.instance_id", "simulation_instance.section_id"], name="fk_team_instance_section", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"], name="fk_team_created_by", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "section_id", name="uq_team_section_identity"),
    )
    op.create_table(
        "enrollment",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("section_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=True),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name="fk_enrollment_user", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["section_id"], ["section.id"], name="fk_enrollment_section", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["team.id"], name="fk_enrollment_team", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "section_id", name="uq_enrollment_user_section"),
        sa.CheckConstraint("role IN ('student', 'ta')", name="ck_enrollment_role"),
    )


def downgrade() -> None:
    op.drop_table("enrollment")
    op.drop_table("team")
    op.drop_table("simulation_instance")
    op.drop_table("section")
    op.drop_table("course")
    op.drop_table("user")
