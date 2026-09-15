"""Platform screen reads the scoped runtime estate and leaves uninitialized teams honest."""

from __future__ import annotations

import asyncio

from app.api import deps, runtime_platform
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
from app.round.models import ArchNodeRow, PlatformServiceRow, TeamStateRow
from app.services.auth import create_access_token, hash_password
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def test_platform_read_is_scoped_and_uninitialized_runtime_is_empty(tmp_path):
    async def run():
        engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'platform.db'}")
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            user = User(student_id="PLAT", name="Platform Student", email="platform@example.test", role="student", password_hash=hash_password("pw"), is_active=True)
            instructor = User(name="Instructor", email="platform-instructor@example.test", role="instructor", password_hash=hash_password("pw"), is_active=True)
            session.add_all([user, instructor]); await session.flush()
            course = Course(course_code="PLAT", course_name="Platform", academic_year="2026", semester="A", instructor_id=instructor.id)
            session.add(course); await session.flush()
            section = Section(course_id=course.id, section_code="A", section_name="Section A")
            session.add(section); await session.flush()
            instance = SimulationInstance(section_id=section.id, pack_key="pack", pack_version="1", current_round=2, total_rounds=6, status="active", settings={})
            session.add(instance); await session.flush()
            team = Team(section_id=section.id, instance_id=instance.instance_id, name="Team Platform")
            session.add(team); await session.flush()
            session.add(Enrollment(user_id=user.id, section_id=section.id, team_id=team.id, role="student", is_active=True))
            session.add(TeamStateRow(instance_id=instance.instance_id, team_id=team.id, current_round=2, declared_strategy="balanced", declared_strategy_round=1, cash=46000, opex_runrate=58300))
            session.add(ArchNodeRow(instance_id=instance.instance_id, team_id=team.id, round=2, key="compute_pool", roles_filled=["compute_capacity"], availability=.99, installed_round=1, service_life_rounds=6, serves=[], throughput=None, owns_entities=[], placement="on_prem", opex_contribution=1800))
            session.add(PlatformServiceRow(instance_id=instance.instance_id, team_id=team.id, round=2, key="compute_pool", placement="on_prem", capacity=100, utilisation=1.0))
            await session.commit()

            token = create_access_token(user_id=user.id, role="student", section_id=section.id, instance_id=instance.instance_id)
            async def get_session():
                yield session
            app = create_app()
            app.dependency_overrides[deps.get_session] = get_session
            app.dependency_overrides[runtime_platform.get_session] = get_session
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(f"/api/instances/{instance.instance_id}/platform", headers={"Authorization": f"Bearer {token}"})
                assert response.status_code == 200, response.text
                body = response.json()
                assert body["team"]["name"] == "Team Platform"
                assert body["team"]["assets"][0]["source_key"] == "compute_pool"
                assert body["team"]["assets"][0]["utilisation_pct"] == 100.0
                assert body["team"]["missing_services"] == []
                patch = await client.patch(
                    f"/api/instances/{instance.instance_id}/platform",
                    json={"version": 1, "expected_revision": 0, "commands": []},
                    headers={"Authorization": f"Bearer {token}"},
                )
                assert patch.status_code == 409
            app.dependency_overrides.clear()
        await engine.dispose()

    asyncio.run(run())
