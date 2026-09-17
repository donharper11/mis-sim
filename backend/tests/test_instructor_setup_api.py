"""M5 bounded instructor setup and roster API contract tests."""

from __future__ import annotations

import asyncio
from pathlib import Path

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api import deps, instructor, platform
from app.main import create_app
from app.models.base import Base
from app.models.platform import Casepack, Course, Enrollment, Section, SimulationInstance, Team, User
from app.services.auth import create_access_token, hash_password
from app.simulation.content import load_runtime_pack


PACK = Path(__file__).resolve().parents[1] / "packs" / "riverside_grocery"


def _token(user: User) -> str:
    return create_access_token(user_id=user.id, role=user.role)


async def _fixture(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'instructor.db'}")
    tables = [User.__table__, Course.__table__, Section.__table__, SimulationInstance.__table__, Team.__table__, Enrollment.__table__, Casepack.__table__]
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=tables)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        owner = User(name="Owner", email="owner@example.test", role="instructor", password_hash=hash_password("pw"))
        other = User(name="Other", email="other@example.test", role="instructor", password_hash=hash_password("pw"))
        admin = User(name="Admin", email="admin@example.test", role="admin", password_hash=hash_password("pw"))
        student = User(student_id="S1", name="Student", email="student@example.test", role="student", password_hash=hash_password("pw"))
        session.add_all([owner, other, admin, student])
        await session.flush()
        course = Course(course_code="MIS", course_name="MIS", academic_year="2026", semester="A", instructor_id=owner.id)
        other_course = Course(course_code="OTHER", course_name="Other", academic_year="2026", semester="A", instructor_id=other.id)
        session.add_all([course, other_course])
        await session.flush()
        section = Section(course_id=course.id, section_code="A", section_name="Section A", max_teams=2, team_size_min=1, team_size_max=2)
        other_section = Section(course_id=other_course.id, section_code="A", section_name="Other A", max_teams=2, team_size_min=1, team_size_max=2)
        session.add_all([section, other_section])
        await session.flush()
        runtime = load_runtime_pack(PACK)
        metadata = runtime.casepack.metadata
        session.add(Casepack(
            pack_key=metadata.pack_key, pack_version=metadata.pack_version, pack_digest=runtime.pack_digest,
            schema_version=metadata.schema_version, display_name=metadata.display_name, vertical=metadata.vertical,
            rounds=metadata.rounds, path=str(PACK), validation_json={"errors": [], "warnings": [], "exit_code": 0},
        ))
        await session.commit()
        values = {"owner": owner, "other": other, "admin": admin, "student": student, "course": course, "other_course": other_course, "section": section, "other_section": other_section, "runtime": runtime}
    return engine, factory, values


def _app(factory):
    async def get_session():
        async with factory() as session:
            yield session
    app = create_app()
    for module in (deps, instructor, platform):
        app.dependency_overrides[module.get_session] = get_session
    return app


def test_instructor_courses_are_owned_and_casepack_list_is_safe(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            owner_headers = {"Authorization": f"Bearer {_token(data['owner'])}"}
            other_headers = {"Authorization": f"Bearer {_token(data['other'])}"}
            admin_headers = {"Authorization": f"Bearer {_token(data['admin'])}"}
            owner = await client.get("/api/instructor/courses", headers=owner_headers)
            assert owner.status_code == 200 and [item["id"] for item in owner.json()] == [data["course"].id]
            denied = await client.get(f"/api/instructor/courses/{data['course'].id}/setup", headers=other_headers)
            assert denied.status_code == 403
            allowed = await client.get(f"/api/instructor/courses/{data['course'].id}/setup", headers=owner_headers)
            assert allowed.status_code == 200 and allowed.json()["sections"][0]["instance"] is None
            all_courses = await client.get("/api/instructor/courses", headers=admin_headers)
            assert all_courses.status_code == 200 and len(all_courses.json()) == 2
            packs = await client.get("/api/casepacks", headers=owner_headers)
            assert packs.status_code == 200 and packs.json()[0]["pack_key"] == "riverside_grocery"
            assert "path" not in packs.json()[0] and "content" not in packs.json()[0]
            student_denied = await client.get("/api/instructor/courses", headers={"Authorization": f"Bearer {_token(data['student'])}"})
            assert student_denied.status_code == 403
        await engine.dispose()
    asyncio.run(run())


def test_setup_instance_is_digest_pinned_and_round_bounded(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        headers = {"Authorization": f"Bearer {_token(data['owner'])}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            base = {"pack_key": "riverside_grocery", "pack_version": "0.1.0", "total_rounds": 6}
            created = await client.post(f"/api/sections/{data['section'].id}/instance", json=base, headers=headers)
            assert created.status_code == 201
            assert created.json()["pack_digest"] == data["runtime"].pack_digest
            assert created.json()["current_round"] == 0 and created.json()["status"] == "setup"
            setup = await client.get(f"/api/instructor/courses/{data['course'].id}/setup", headers=headers)
            assert setup.json()["sections"][0]["instance"]["pack_digest"] == data["runtime"].pack_digest
            duplicate = await client.post(f"/api/sections/{data['section'].id}/instance", json=base, headers=headers)
            assert duplicate.status_code == 409
            too_many = await client.post(f"/api/sections/{data['other_section'].id}/instance", json={**base, "total_rounds": 7}, headers={"Authorization": f"Bearer {_token(data['other'])}"})
            assert too_many.status_code == 409
            unknown = await client.post(f"/api/sections/{data['other_section'].id}/instance", json={**base, "pack_key": "missing"}, headers={"Authorization": f"Bearer {_token(data['other'])}"})
            assert unknown.status_code == 409
        await engine.dispose()
    asyncio.run(run())


def test_roster_assignment_is_scoped_and_team_limits_apply(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        async with factory() as session:
            instance = SimulationInstance(section_id=data["section"].id, pack_key="riverside_grocery", pack_version="0.1.0", pack_digest=data["runtime"].pack_digest, total_rounds=6, status="setup")
            other_instance = SimulationInstance(section_id=data["other_section"].id, pack_key="riverside_grocery", pack_version="0.1.0", pack_digest=data["runtime"].pack_digest, total_rounds=6, status="setup")
            session.add_all([instance, other_instance])
            await session.flush()
            cross_team = Team(section_id=data["other_section"].id, instance_id=other_instance.instance_id, name="Other team")
            session.add(cross_team)
            await session.commit()
        app = _app(factory)
        headers = {"Authorization": f"Bearer {_token(data['owner'])}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            enrolled = await client.post(f"/api/sections/{data['section'].id}/enrollments", json={"user_id": data["student"].id}, headers=headers)
            assert enrolled.status_code == 201
            team = await client.post(f"/api/instances/{instance.instance_id}/teams", json={"name": "Team A"}, headers=headers)
            assert team.status_code == 201
            roster = await client.get(f"/api/sections/{data['section'].id}/roster", headers=headers)
            assert roster.status_code == 200 and roster.json()[0]["team"] is None
            assigned = await client.patch(f"/api/sections/{data['section'].id}/enrollments/{enrolled.json()['id']}", json={"team_id": team.json()["id"]}, headers=headers)
            assert assigned.status_code == 200 and assigned.json()["team_id"] == team.json()["id"]
            unassigned = await client.patch(f"/api/sections/{data['section'].id}/enrollments/{enrolled.json()['id']}", json={"team_id": None}, headers=headers)
            assert unassigned.status_code == 200 and unassigned.json()["team_id"] is None
            cross = await client.patch(f"/api/sections/{data['section'].id}/enrollments/{enrolled.json()['id']}", json={"team_id": cross_team.id}, headers=headers)
            assert cross.status_code == 409
            duplicate = await client.post(f"/api/sections/{data['section'].id}/enrollments", json={"user_id": data["student"].id}, headers=headers)
            assert duplicate.status_code == 409
            second_team = await client.post(f"/api/instances/{instance.instance_id}/teams", json={"name": "Team B"}, headers=headers)
            assert second_team.status_code == 201
            third_team = await client.post(f"/api/instances/{instance.instance_id}/teams", json={"name": "Team C"}, headers=headers)
            assert third_team.status_code == 409
        await engine.dispose()
    asyncio.run(run())

