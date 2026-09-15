"""Versioned persistence rows for the production simulation service.

The checkpoint is the only mutable simulation state.  Historical round-runner
tables remain registered separately and are deliberately not replaced by these
three rows.
"""

from __future__ import annotations

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SimulationRunV1(Base):
    __tablename__ = "simulation_run_v1"
    __table_args__ = (
        CheckConstraint("version = 1", name="ck_simulation_run_v1_version"),
        CheckConstraint("current_round >= 1", name="ck_simulation_run_v1_current_round"),
        CheckConstraint("advanced_round >= 0", name="ck_simulation_run_v1_advanced_round"),
        CheckConstraint("status IN ('draft', 'locked', 'completed')", name="ck_simulation_run_v1_status"),
    )

    instance_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    pack_key: Mapped[str] = mapped_column(String(64), nullable=False)
    pack_version: Mapped[str] = mapped_column(String(48), nullable=False)
    pack_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    current_round: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    advanced_round: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")


class SimulationSheetV1(Base):
    __tablename__ = "simulation_sheet_v1"
    __table_args__ = (
        ForeignKeyConstraint(
            ["instance_id", "team_id"],
            ["simulation_run_v1.instance_id", "simulation_run_v1.team_id"],
            name="fk_simulation_sheet_v1_run",
        ),
        CheckConstraint("round >= 1", name="ck_simulation_sheet_v1_round"),
        CheckConstraint("revision >= 0", name="ck_simulation_sheet_v1_revision"),
        CheckConstraint("locked_revision IS NULL OR locked_revision >= 0", name="ck_simulation_sheet_v1_locked_revision"),
    )

    instance_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    round: Mapped[int] = mapped_column(Integer, primary_key=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_revision: Mapped[int | None] = mapped_column(Integer, nullable=True)
    commands: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    sheet_digest: Mapped[str | None] = mapped_column(String(64), nullable=True)


class SimulationCheckpointV1(Base):
    __tablename__ = "simulation_checkpoint_v1"
    __table_args__ = (
        ForeignKeyConstraint(
            ["instance_id", "team_id"],
            ["simulation_run_v1.instance_id", "simulation_run_v1.team_id"],
            name="fk_simulation_checkpoint_v1_run",
        ),
        CheckConstraint("version = 1", name="ck_simulation_checkpoint_v1_version"),
        CheckConstraint("round >= 0", name="ck_simulation_checkpoint_v1_round"),
        CheckConstraint("sheet_revision IS NULL OR sheet_revision >= 0", name="ck_simulation_checkpoint_v1_sheet_revision"),
    )

    instance_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    round: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    pack_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    sheet_revision: Mapped[int | None] = mapped_column(Integer, nullable=True)
    state: Mapped[dict] = mapped_column(JSON, nullable=False)
    state_digest: Mapped[str] = mapped_column(String(64), nullable=False)


ALL_TABLES = (SimulationRunV1, SimulationSheetV1, SimulationCheckpointV1)

