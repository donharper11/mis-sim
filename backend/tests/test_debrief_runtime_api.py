"""Debrief exposes persisted results and an honest empty state."""

from __future__ import annotations

import asyncio

from app.api import deps, runtime_debrief
from app.main import create_app
from app.models.base import Base
from app.models.platform import (
    Course,
    Enrollment,
    Section,
    SimulationInstance,
    Team,
    User,
)
from app.round.models import RoundResult
from app.services.auth import create_access_token, hash_password
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def test_debrief_reads_persisted_rounds_and_downloads_report(tmp_path):
    async def run():
        engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'debrief.db'}")
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            user = User(student_id="DEBR", name="Debrief Student", email="debrief@example.test", role="student", password_hash=hash_password("pw"), is_active=True)
            instructor = User(name="Instructor", email="debrief-instructor@example.test", role="instructor", password_hash=hash_password("pw"), is_active=True)
            session.add_all([user, instructor]); await session.flush()
            course = Course(course_code="DEBR", course_name="Debrief", academic_year="2026", semester="A", instructor_id=instructor.id)
            session.add(course); await session.flush()
            section = Section(course_id=course.id, section_code="A", section_name="Section A")
            session.add(section); await session.flush()
            instance = SimulationInstance(section_id=section.id, pack_key="pack", pack_version="1", current_round=2, total_rounds=6, status="active", settings={})
            session.add(instance); await session.flush()
            team = Team(section_id=section.id, instance_id=instance.instance_id, name="Team Debrief")
            session.add(team); await session.flush()
            session.add(Enrollment(user_id=user.id, section_id=section.id, team_id=team.id, role="student", is_active=True))
            session.add(RoundResult(instance_id=instance.instance_id, team_id=team.id, round=1, payload={"score": {"firm_score": .6, "balanced_scorecard": {"financial": 60}}, "events": [], "state_changes": {"arrived": ["order_mgmt_v42"], "changed_rollouts": []}, "financials": {"capital_spend": 1000, "opex_runrate": 5000}, "technical_debt": {"closing": 0}}))
            await session.commit()
            token = create_access_token(user_id=user.id, role="student", section_id=section.id, instance_id=instance.instance_id)
            async def get_session():
                yield session
            app = create_app()
            app.dependency_overrides[deps.get_session] = get_session
            app.dependency_overrides[runtime_debrief.get_session] = get_session
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                headers = {"Authorization": f"Bearer {token}"}
                response = await client.get(f"/api/instances/{instance.instance_id}/debrief", headers=headers)
                assert response.status_code == 200, response.text
                assert response.json()["team"]["latest_round"] == 1
                report = await client.get(f"/api/instances/{instance.instance_id}/debrief/download", headers=headers)
                assert report.status_code == 200
                assert "ROUND 1" in report.text
                assert "attachment" in report.headers["content-disposition"]
            app.dependency_overrides.clear()
        await engine.dispose()

    asyncio.run(run())
