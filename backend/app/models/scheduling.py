"""Persisted, instance-scoped round schedules."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RoundSchedule(Base):
    __tablename__ = "round_schedule"
    __table_args__ = (
        ForeignKeyConstraint(["instance_id"], ["simulation_instance.instance_id"], ondelete="CASCADE"),
        UniqueConstraint("instance_id", "round_number", name="uq_round_schedule_instance_round"),
        UniqueConstraint("id", "instance_id", name="uq_round_schedule_identity"),
        CheckConstraint("round_number >= 1", name="ck_round_schedule_round"),
        CheckConstraint("deadline > start_at", name="ck_round_schedule_deadline"),
        CheckConstraint("grace_period_minutes >= 0", name="ck_round_schedule_grace"),
        CheckConstraint("lock_reason IS NULL OR lock_reason IN ('deadline_expired', 'instructor_locked')", name="ck_round_schedule_lock_reason"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    auto_advance: Mapped[bool] = mapped_column(Boolean, nullable=False)
    grace_period_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    decisions_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    lock_reason: Mapped[str | None] = mapped_column(String(32), nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    advanced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    claim_token: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    claim_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RoundScheduleTeam(Base):
    __tablename__ = "round_schedule_team"
    __table_args__ = (
        ForeignKeyConstraint(
            ["schedule_id", "instance_id"],
            ["round_schedule.id", "round_schedule.instance_id"],
            name="fk_round_schedule_team_schedule",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["team_id", "instance_id"],
            ["team.id", "team.instance_id"],
            name="fk_round_schedule_team_team",
            ondelete="RESTRICT",
        ),
        CheckConstraint("locked_revision IS NULL OR locked_revision >= 0", name="ck_round_schedule_team_locked_revision"),
    )

    schedule_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False)
    team_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    locked_revision: Mapped[int | None] = mapped_column(Integer, nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    advanced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


ALL_TABLES = (RoundSchedule, RoundScheduleTeam)
