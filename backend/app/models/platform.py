"""M2 platform hierarchy models.

This module owns the identity layer above the simulation runtime.  Runtime tables
deliberately remain independent until packet 2.2 adds their complete instance
foreign-key treatment.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Integer, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


def _chapters() -> list[int]:
    return list(range(1, 13))


class User(Base):
    __tablename__ = "user"
    __table_args__ = (
        CheckConstraint("role IN ('student', 'ta', 'instructor', 'admin')", name="ck_user_role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="student")
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class Course(Base):
    __tablename__ = "course"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_code: Mapped[str] = mapped_column(String(64), nullable=False)
    course_name: Mapped[str] = mapped_column(String(200), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(32), nullable=False)
    semester: Mapped[str] = mapped_column(String(32), nullable=False)
    instructor_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="RESTRICT"), nullable=False)
    active_chapters: Mapped[list] = mapped_column(JSON, nullable=False, default=_chapters)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    instructor: Mapped[User] = relationship(foreign_keys=[instructor_id])
    sections: Mapped[list[Section]] = relationship(back_populates="course", passive_deletes=True)


class Section(Base):
    __tablename__ = "section"
    __table_args__ = (UniqueConstraint("course_id", "section_code", name="uq_section_course_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("course.id", ondelete="CASCADE"), nullable=False)
    section_code: Mapped[str] = mapped_column(String(64), nullable=False)
    section_name: Mapped[str] = mapped_column(String(200), nullable=False)
    max_teams: Mapped[int] = mapped_column(Integer, nullable=False, default=8)
    team_size_min: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    team_size_max: Mapped[int] = mapped_column(Integer, nullable=False, default=6)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    course: Mapped[Course] = relationship(back_populates="sections")
    instance: Mapped[SimulationInstance | None] = relationship(back_populates="section", uselist=False, passive_deletes=True)
    teams: Mapped[list[Team]] = relationship(back_populates="section", passive_deletes=True)
    enrollments: Mapped[list[Enrollment]] = relationship(back_populates="section", passive_deletes=True)


class SimulationInstance(Base):
    __tablename__ = "simulation_instance"
    __table_args__ = (
        UniqueConstraint("section_id", name="uq_simulation_instance_section"),
        UniqueConstraint("instance_id", "section_id", name="uq_simulation_instance_identity"),
        CheckConstraint("status IN ('setup', 'active', 'paused', 'completed')", name="ck_simulation_instance_status"),
        CheckConstraint("current_round >= 0", name="ck_simulation_instance_current_round"),
        CheckConstraint("total_rounds > 0", name="ck_simulation_instance_total_rounds"),
    )

    instance_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("section.id", ondelete="CASCADE"), nullable=False)
    pack_key: Mapped[str] = mapped_column(String(128), nullable=False)
    pack_version: Mapped[str] = mapped_column(String(64), nullable=False)
    current_round: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_rounds: Mapped[int] = mapped_column(Integer, nullable=False, default=6)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="setup")
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    section: Mapped[Section] = relationship(back_populates="instance")
    teams: Mapped[list[Team]] = relationship(back_populates="instance", passive_deletes=True, overlaps="section,teams")


class Team(Base):
    __tablename__ = "team"
    __table_args__ = (
        ForeignKeyConstraint(
            ["instance_id", "section_id"],
            ["simulation_instance.instance_id", "simulation_instance.section_id"],
            name="fk_team_instance_section",
            ondelete="CASCADE",
        ),
        UniqueConstraint("id", "section_id", name="uq_team_section_identity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("section.id", ondelete="CASCADE"), nullable=False)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"), nullable=True)

    section: Mapped[Section] = relationship(back_populates="teams", foreign_keys=[section_id], overlaps="teams,instance")
    instance: Mapped[SimulationInstance] = relationship(back_populates="teams", foreign_keys=[instance_id, section_id], overlaps="section,teams")
    creator: Mapped[User | None] = relationship(foreign_keys=[created_by])
    enrollments: Mapped[list[Enrollment]] = relationship(back_populates="team", passive_deletes=True, overlaps="section,enrollments")


class Enrollment(Base):
    __tablename__ = "enrollment"
    __table_args__ = (
        UniqueConstraint("user_id", "section_id", name="uq_enrollment_user_section"),
        CheckConstraint("role IN ('student', 'ta')", name="ck_enrollment_role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="RESTRICT"), nullable=False)
    section_id: Mapped[int] = mapped_column(ForeignKey("section.id", ondelete="CASCADE"), nullable=False)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("team.id", ondelete="SET NULL"), nullable=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="student")
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped[User] = relationship(foreign_keys=[user_id])
    section: Mapped[Section] = relationship(back_populates="enrollments", foreign_keys=[section_id], overlaps="enrollments,team")
    team: Mapped[Team | None] = relationship(back_populates="enrollments", foreign_keys=[team_id], overlaps="enrollments,section")


ALL_TABLES = (User, Course, Section, SimulationInstance, Team, Enrollment)
