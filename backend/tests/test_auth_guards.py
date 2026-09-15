"""Authenticated platform route matrix probes."""

from __future__ import annotations

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api import deps, platform
from app.main import create_app
from app.models.base import Base
from app.models.platform import Course, Enrollment, Section, SimulationInstance, Team, User
from app.services.auth import create_access_token, hash_password


@pytest.fixture()
def setup_db(tmp_path):
    async def run():
        engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'guards.db'}")
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all, tables=[User.__table__, Course.__table__, Section.__table__, SimulationInstance.__table__, Team.__table__, Enrollment.__table__])
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            instructor = User(name="Instructor", email="i@example.test", role="instructor", password_hash=hash_password("pw"), is_active=True)
            student_a = User(student_id="A", name="A", email="a@example.test", role="student", password_hash=hash_password("pw"), is_active=True)
            student_b = User(student_id="B", name="B", email="b@example.test", role="student", password_hash=hash_password("pw"), is_active=True)
            session.add_all([instructor, student_a, student_b]); await session.flush()
            course = Course(course_code="M", course_name="M", academic_year="2026", semester="A", instructor_id=instructor.id)
            session.add(course); await session.flush()
            sections = [Section(course_id=course.id, section_code=x, section_name=f"Section {x}") for x in ("A", "B")]
            session.add_all(sections); await session.flush()
            instances = [SimulationInstance(section_id=s.id, pack_key="p", pack_version="1.0.0", current_round=0, total_rounds=6, status="setup", settings={}) for s in sections]
            session.add_all(instances); await session.flush()
            session.add_all([Enrollment(user_id=student_a.id, section_id=sections[0].id, role="student", is_active=True), Enrollment(user_id=student_b.id, section_id=sections[1].id, role="student", is_active=True)])
            await session.commit()
            return engine, factory, student_a.id, instances[0].instance_id, instances[1].instance_id
    return asyncio.run(run())


def test_cross_instance_student_access_is_403(setup_db):
    async def run():
        engine, factory, user_id, own, other = setup_db
        async with factory() as session:
            token = create_access_token(user_id=user_id, role="student", section_id=1, instance_id=own)
            async def get_session():
                yield session
            app = create_app()
            app.dependency_overrides[deps.get_session] = get_session
            app.dependency_overrides[platform.get_session] = get_session
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(f"/api/instances/{other}", headers={"Authorization": f"Bearer {token}"})
                assert response.status_code == 403
                assert (await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})).status_code == 200
            app.dependency_overrides.clear()
        await engine.dispose()
    asyncio.run(run())


def test_unauthenticated_course_create_is_401(setup_db):
    async def run():
        engine, factory, *_ = setup_db
        async with factory() as session:
            async def get_session():
                yield session
            app = create_app()
            app.dependency_overrides[deps.get_session] = get_session
            app.dependency_overrides[platform.get_session] = get_session
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/courses", json={"course_code": "X", "course_name": "X", "academic_year": "2026", "semester": "A"})
                assert response.status_code == 401
                assert response.headers["www-authenticate"] == "Bearer"
            app.dependency_overrides.clear()
        await engine.dispose()
    asyncio.run(run())


def test_student_login_and_staff_rejection_have_canonical_bodies(setup_db):
    async def run():
        engine, factory, *_ = setup_db
        async with factory() as session:
            async def get_session():
                yield session
            app = create_app()
            app.dependency_overrides[deps.get_session] = get_session
            app.dependency_overrides[platform.get_session] = get_session
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                student = await client.post("/api/auth/login", json={"student_id": "A", "password": "pw"})
                assert student.status_code == 200
                assert student.json()["instance_id"] == 1
                unknown = await client.post("/api/auth/login", json={"student_id": "missing", "password": "pw"})
                wrong = await client.post("/api/auth/login", json={"student_id": "A", "password": "wrong"})
                assert unknown.status_code == wrong.status_code == 401
                assert unknown.json() == wrong.json() == {"detail": "Invalid credentials"}
                staff = await client.post("/api/auth/staff-login", json={"email": "a@example.test", "password": "pw"})
                assert staff.status_code == 403
                assert staff.json() == {"detail": "This login is for instructors and TAs only"}
            app.dependency_overrides.clear()
        await engine.dispose()
    asyncio.run(run())
