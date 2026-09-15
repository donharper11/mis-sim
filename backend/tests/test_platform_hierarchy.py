"""Focused M2 packet 2.1 hierarchy tests."""

from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.base import Base
from app.models.platform import Course, Enrollment, Section, SimulationInstance, Team, User
from app.services.platform import (
    CourseService,
    EnrollmentService,
    InstanceService,
    PlatformConflict,
    PlatformNotFound,
    SectionService,
    TeamService,
)


@pytest.fixture()
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'platform.db'}")
    Base.metadata.create_all(engine, tables=[x.__table__ for x in (User, Course, Section, SimulationInstance, Team, Enrollment)])
    yield engine
    engine.dispose()


def test_platform_tables_have_canonical_identity_columns(db):
    assert inspect(db).get_pk_constraint("simulation_instance")["constrained_columns"] == ["instance_id"]
    assert {c["name"] for c in inspect(db).get_columns("team")} >= {"section_id", "instance_id"}
    assert "scenario_id" not in {c["name"] for c in inspect(db).get_columns("simulation_instance")}
    assert "scenario_version" not in {c["name"] for c in inspect(db).get_columns("simulation_instance")}


def test_hierarchy_constraints_and_duplicate_instance(db):
    from sqlalchemy.orm import Session

    with Session(db) as session:
        user = User(name="Instructor", email="i@example.edu", role="instructor")
        session.add(user)
        session.flush()
        course = Course(course_code="M", course_name="M", academic_year="2026", semester="A", instructor_id=user.id)
        session.add(course)
        session.flush()
        section = Section(course_id=course.id, section_code="A", section_name="A")
        session.add(section)
        session.flush()
        first = SimulationInstance(section_id=section.id, pack_key="pack_alpha", pack_version="1.0.0")
        session.add(first)
        session.commit()
        session.add(SimulationInstance(section_id=section.id, pack_key="pack_beta", pack_version="1.0.0"))
        with pytest.raises(IntegrityError):
            session.commit()


def test_services_reject_cross_section_team_and_duplicate_enrollment():
    async def run():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, tables=[x.__table__ for x in (User, Course, Section, SimulationInstance, Team, Enrollment)])
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            instructor = User(name="Instructor", email="i@example.edu", role="instructor")
            student = User(student_id="S1", name="Student", email="s@example.edu", role="student")
            session.add_all([instructor, student])
            await session.flush()
            course = await CourseService.create(
                session, course_code="M", course_name="M", academic_year="2026", semester="A", instructor_id=instructor.id
            )
            one = await SectionService.create(session, course.id, section_code="A", section_name="A")
            two = await SectionService.create(session, course.id, section_code="B", section_name="B")
            instance = await InstanceService.create(session, one.id, pack_key="pack_alpha", pack_version="1.0.0")
            with pytest.raises(PlatformConflict):
                await InstanceService.create(session, one.id, pack_key="pack_beta", pack_version="1.0.0")
            with pytest.raises(PlatformConflict):
                await TeamService.create(session, instance.instance_id, two.id, name="wrong")
            team = await TeamService.create(session, instance.instance_id, one.id, name="right")
            await EnrollmentService.create(session, one.id, student.id, team_id=team.id)
            with pytest.raises(PlatformConflict):
                await EnrollmentService.create(session, one.id, student.id)
            with pytest.raises(PlatformConflict):
                await EnrollmentService.create(session, two.id, student.id, team_id=team.id)
            instance_two = await InstanceService.create(session, two.id, pack_key="pack_beta", pack_version="1.0.0")
            team_two = await TeamService.create(session, instance_two.instance_id, two.id, name="other")
            enrollment_two = await EnrollmentService.create(session, two.id, student.id, team_id=team_two.id)
            assert await TeamService.read(session, team.id, section_id=one.id) == team
            assert await TeamService.read(session, team.id, instance_id=instance.instance_id) == team
            with pytest.raises(PlatformNotFound):
                await TeamService.read(session, team.id, section_id=two.id)
            with pytest.raises(PlatformNotFound):
                await TeamService.read(session, team.id, instance_id=instance_two.instance_id)
            assert await EnrollmentService.read(session, enrollment_two.id, section_id=two.id) == enrollment_two
            assert await EnrollmentService.read(session, enrollment_two.id, instance_id=instance_two.instance_id) == enrollment_two
            with pytest.raises(PlatformNotFound):
                await EnrollmentService.read(session, enrollment_two.id, section_id=one.id)
            with pytest.raises(PlatformNotFound):
                await EnrollmentService.read(session, enrollment_two.id, instance_id=instance.instance_id)
            with pytest.raises(PlatformConflict):
                await TeamService.read(session, team.id)
            with pytest.raises(PlatformConflict):
                await EnrollmentService.read(session, enrollment_two.id)
        await engine.dispose()

    asyncio.run(run())


def test_platform_services_do_not_reference_runtime_tables():
    from pathlib import Path

    source = Path(__file__).parents[1] / "app" / "services" / "platform.py"
    text = source.read_text()
    assert not any(name in text for name in ("arch_node", "round_result", "decision_line", "signal", "simulation_run_v1"))
