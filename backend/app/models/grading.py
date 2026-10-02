"""Grading models for M5.5 grade derivation and export."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class GradeOverride(Base):
    __tablename__ = "grade_override"

    instance_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("simulation_instance.instance_id", ondelete="CASCADE"),
        primary_key=True,
    )
    team_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("team.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    override: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(256), nullable=True)
    updated_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class GradeConfig(Base):
    __tablename__ = "grade_config"

    instance_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("simulation_instance.instance_id", ondelete="CASCADE"),
        primary_key=True,
    )
    weight_financial: Mapped[float] = mapped_column(Float, default=0.25, nullable=False)
    weight_customer: Mapped[float] = mapped_column(Float, default=0.25, nullable=False)
    weight_internal_process: Mapped[float] = mapped_column(Float, default=0.25, nullable=False)
    weight_learning_growth: Mapped[float] = mapped_column(Float, default=0.25, nullable=False)
    rounds_mode: Mapped[str] = mapped_column(String(16), default="final", nullable=False)
    updated_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


ALL_TABLES = (GradeOverride, GradeConfig)
