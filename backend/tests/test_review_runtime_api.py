"""Review reads the current sheet boundary and refuses absent runtimes."""

from __future__ import annotations

import asyncio

from app.api import deps, runtime_review
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
from app.round.models import TeamStateRow
from app.services.auth import create_access_token, hash_password
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def test_review_read_is_scoped_and_uninitialized_lock_is_blocked(tmp_path):
    async def run():
        engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'review.db'}")
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            user = User(student_id="REV", name="Review Student", email="review@example.test", role="student", password_hash=hash_password("pw"), is_active=True)
            instructor = User(name="Instructor", email="review-instructor@example.test", role="instructor", password_hash=hash_password("pw"), is_active=True)
            session.add_all([user, instructor]); await session.flush()
            course = Course(course_code="REV", course_name="Review", academic_year="2026", semester="A", instructor_id=instructor.id)
            session.add(course); await session.flush()
            section = Section(course_id=course.id, section_code="A", section_name="Section A")
            session.add(section); await session.flush()
            instance = SimulationInstance(section_id=section.id, pack_key="pack", pack_version="1", current_round=2, total_rounds=6, status="active", settings={})
            session.add(instance); await session.flush()
            team = Team(section_id=section.id, instance_id=instance.instance_id, name="Team Review")
            session.add(team); await session.flush()
            session.add(Enrollment(user_id=user.id, section_id=section.id, team_id=team.id, role="student", is_active=True))
            session.add(TeamStateRow(instance_id=instance.instance_id, team_id=team.id, current_round=2, declared_strategy="balanced", declared_strategy_round=1, cash=46000, opex_runrate=58300))
            await session.commit()

            token = create_access_token(user_id=user.id, role="student", section_id=section.id, instance_id=instance.instance_id)
            async def get_session():
                yield session
            app = create_app()
            app.dependency_overrides[deps.get_session] = get_session
            app.dependency_overrides[runtime_review.get_session] = get_session
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                headers = {"Authorization": f"Bearer {token}"}
                response = await client.get(f"/api/instances/{instance.instance_id}/review", headers=headers)
                assert response.status_code == 200, response.text
                assert response.json()["team"]["status"] == "active"
                locked = await client.post(f"/api/instances/{instance.instance_id}/review/lock", json={"expected_revision": 0}, headers=headers)
                assert locked.status_code == 409
            app.dependency_overrides.clear()
        await engine.dispose()

    asyncio.run(run())
