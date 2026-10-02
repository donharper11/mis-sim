"""M5.6 registry admin API contract tests."""

from __future__ import annotations

import asyncio
from pathlib import Path

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api import admin, deps, instructor, platform
from app.main import create_app
from app.models.base import Base
from app.models.platform import Casepack, Course, Enrollment, Section, SimulationInstance, Team, User
from app.services.auth import create_access_token, hash_password
from app.simulation.content import load_runtime_pack


PACK = Path(__file__).resolve().parents[1] / "packs" / "riverside_grocery"


def _token(user: User) -> str:
    return create_access_token(user_id=user.id, role=user.role)


async def _fixture(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'registry_admin.db'}")
    tables = [
        User.__table__, Course.__table__, Section.__table__,
        SimulationInstance.__table__, Team.__table__, Enrollment.__table__,
        Casepack.__table__,
    ]
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=tables)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        admin_user = User(name="Admin", email="admin@example.test", role="admin", password_hash=hash_password("pw"))
        instructor_user = User(name="Instructor", email="instructor@example.test", role="instructor", password_hash=hash_password("pw"))
        student_user = User(student_id="S1", name="Student", email="student@example.test", role="student", password_hash=hash_password("pw"))
        session.add_all([admin_user, instructor_user, student_user])
        await session.flush()
        course = Course(course_code="MIS", course_name="MIS", academic_year="2026", semester="A", instructor_id=instructor_user.id)
        session.add(course)
        await session.flush()
        section = Section(course_id=course.id, section_code="A", section_name="Section A", max_teams=4, team_size_min=1, team_size_max=4)
        session.add(section)
        await session.flush()
        await session.commit()
        values = {
            "admin": admin_user,
            "instructor": instructor_user,
            "student": student_user,
            "course": course,
            "section": section,
        }
    return engine, factory, values


def _app(factory):
    async def get_session():
        async with factory() as session:
            yield session
    app = create_app()
    for module in (deps, admin, instructor, platform):
        app.dependency_overrides[module.get_session] = get_session
    return app


def test_admin_registers_on_disk_pack(tmp_path):
    """AC1: admin registers an on-disk pack; response contains pack_key, pack_version, pack_digest, and validation summary."""
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        headers = {"Authorization": f"Bearer {_token(data['admin'])}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/admin/casepacks/register",
                json={"pack_key": "riverside_grocery", "pack_path": str(PACK)},
                headers=headers,
            )
            assert response.status_code == 201, response.text
            body = response.json()
            assert body["pack_key"] == "riverside_grocery"
            assert body["pack_version"] is not None
            assert body["pack_digest"] is not None and len(body["pack_digest"]) > 0
            assert "errors" in body and "warnings" in body and "exit_code" in body
            assert body["errors"] == 0
        await engine.dispose()
    asyncio.run(run())


def test_duplicate_registration_returns_409(tmp_path):
    """AC2: registering the same (pack_key, pack_version) twice returns 409."""
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        headers = {"Authorization": f"Bearer {_token(data['admin'])}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            first = await client.post(
                "/api/admin/casepacks/register",
                json={"pack_key": "riverside_grocery", "pack_path": str(PACK)},
                headers=headers,
            )
            assert first.status_code == 201
            second = await client.post(
                "/api/admin/casepacks/register",
                json={"pack_key": "riverside_grocery", "pack_path": str(PACK)},
                headers=headers,
            )
            assert second.status_code == 409
        await engine.dispose()
    asyncio.run(run())


def test_validation_report_returns_findings(tmp_path):
    """AC4: GET returns the full finding list with codes, messages, and file locations."""
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        headers = {"Authorization": f"Bearer {_token(data['admin'])}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            reg = await client.post(
                "/api/admin/casepacks/register",
                json={"pack_key": "riverside_grocery", "pack_path": str(PACK)},
                headers=headers,
            )
            assert reg.status_code == 201
            version = reg.json()["pack_version"]
            response = await client.get(
                f"/api/admin/casepacks/riverside_grocery/{version}/validation",
                headers=headers,
            )
            assert response.status_code == 200
            body = response.json()
            assert "findings" in body
            assert "errors" in body
            assert "warnings" in body
            assert "exit_code" in body
        await engine.dispose()
    asyncio.run(run())


def test_validation_report_404_for_unregistered(tmp_path):
    """Validation report returns 404 for unregistered pack."""
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        headers = {"Authorization": f"Bearer {_token(data['admin'])}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/admin/casepacks/nonexistent/0.0.0/validation",
                headers=headers,
            )
            assert response.status_code == 404
        await engine.dispose()
    asyncio.run(run())


def test_bound_instances_lists_instances(tmp_path):
    """AC5: detail response lists all instances currently bound to this pack version."""
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        # Pre-register the pack and bind an instance
        runtime = load_runtime_pack(PACK)
        meta = runtime.casepack.metadata
        async with factory() as session:
            session.add(Casepack(
                pack_key=meta.pack_key, pack_version=meta.pack_version,
                pack_digest=runtime.pack_digest, schema_version=meta.schema_version,
                display_name=meta.display_name, vertical=meta.vertical,
                rounds=meta.rounds, path=str(PACK),
                validation_json={"findings": [], "errors": [], "warnings": [], "exit_code": 0},
            ))
            await session.flush()
            instance = SimulationInstance(
                section_id=data["section"].id,
                pack_key=meta.pack_key, pack_version=meta.pack_version,
                pack_digest=runtime.pack_digest, total_rounds=6, status="setup",
            )
            session.add(instance)
            await session.commit()
        app = _app(factory)
        headers = {"Authorization": f"Bearer {_token(data['admin'])}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                f"/api/admin/casepacks/{meta.pack_key}/{meta.pack_version}/instances",
                headers=headers,
            )
            assert response.status_code == 200
            body = response.json()
            assert len(body) == 1
            assert body[0]["pack_key"] == meta.pack_key
            assert body[0]["status"] == "setup"
            assert "instance_id" in body[0]
        await engine.dispose()
    asyncio.run(run())


def test_deregister_unbound_pack_returns_200(tmp_path):
    """AC6: admin removes a pack version with zero bound instances; response 200; subsequent GET /api/casepacks omits it."""
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        headers = {"Authorization": f"Bearer {_token(data['admin'])}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            reg = await client.post(
                "/api/admin/casepacks/register",
                json={"pack_key": "riverside_grocery", "pack_path": str(PACK)},
                headers=headers,
            )
            assert reg.status_code == 201
            version = reg.json()["pack_version"]
            # Verify it appears in the list
            packs = await client.get("/api/casepacks", headers=headers)
            assert any(p["pack_key"] == "riverside_grocery" for p in packs.json())
            # Deregister
            delete = await client.delete(
                f"/api/admin/casepacks/riverside_grocery/{version}",
                headers=headers,
            )
            assert delete.status_code == 200
            # Verify it is gone from the list
            packs_after = await client.get("/api/casepacks", headers=headers)
            assert not any(p["pack_key"] == "riverside_grocery" and p["pack_version"] == version for p in packs_after.json())
        await engine.dispose()
    asyncio.run(run())


def test_deregister_bound_pack_returns_409(tmp_path):
    """AC7: removing a pack bound to an active instance returns 409 with the bound instance IDs."""
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        runtime = load_runtime_pack(PACK)
        meta = runtime.casepack.metadata
        async with factory() as session:
            session.add(Casepack(
                pack_key=meta.pack_key, pack_version=meta.pack_version,
                pack_digest=runtime.pack_digest, schema_version=meta.schema_version,
                display_name=meta.display_name, vertical=meta.vertical,
                rounds=meta.rounds, path=str(PACK),
                validation_json={"findings": [], "errors": [], "warnings": [], "exit_code": 0},
            ))
            await session.flush()
            instance = SimulationInstance(
                section_id=data["section"].id,
                pack_key=meta.pack_key, pack_version=meta.pack_version,
                pack_digest=runtime.pack_digest, total_rounds=6, status="active",
            )
            session.add(instance)
            await session.commit()
            instance_id = instance.instance_id
        app = _app(factory)
        headers = {"Authorization": f"Bearer {_token(data['admin'])}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete(
                f"/api/admin/casepacks/{meta.pack_key}/{meta.pack_version}",
                headers=headers,
            )
            assert response.status_code == 409
            assert str(instance_id) in response.json()["detail"]
        await engine.dispose()
    asyncio.run(run())


def test_non_admin_auth_returns_403(tmp_path):
    """AC8: instructor (non-admin) cannot register, deregister, or view the admin registry page."""
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        instructor_headers = {"Authorization": f"Bearer {_token(data['instructor'])}"}
        student_headers = {"Authorization": f"Bearer {_token(data['student'])}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            for headers in [instructor_headers, student_headers]:
                reg = await client.post(
                    "/api/admin/casepacks/register",
                    json={"pack_key": "riverside_grocery", "pack_path": str(PACK)},
                    headers=headers,
                )
                assert reg.status_code == 403, f"Expected 403 for register, got {reg.status_code}"
                val = await client.get(
                    "/api/admin/casepacks/riverside_grocery/0.1.0/validation",
                    headers=headers,
                )
                assert val.status_code == 403, f"Expected 403 for validation, got {val.status_code}"
                inst = await client.get(
                    "/api/admin/casepacks/riverside_grocery/0.1.0/instances",
                    headers=headers,
                )
                assert inst.status_code == 403, f"Expected 403 for instances, got {inst.status_code}"
                dereg = await client.delete(
                    "/api/admin/casepacks/riverside_grocery/0.1.0",
                    headers=headers,
                )
                assert dereg.status_code == 403, f"Expected 403 for deregister, got {dereg.status_code}"
        await engine.dispose()
    asyncio.run(run())


def test_register_without_pack_path_uses_pack_key(tmp_path):
    """Registration with only pack_key uses default pack root to resolve the path."""
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        headers = {"Authorization": f"Bearer {_token(data['admin'])}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/admin/casepacks/register",
                json={"pack_key": "riverside_grocery"},
                headers=headers,
            )
            assert response.status_code == 201, response.text
            body = response.json()
            assert body["pack_key"] == "riverside_grocery"
        await engine.dispose()
    asyncio.run(run())


def test_casepacks_list_includes_validation_status(tmp_path):
    """AC5 augmented: GET /api/casepacks includes validation status indicators."""
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        headers = {"Authorization": f"Bearer {_token(data['admin'])}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            reg = await client.post(
                "/api/admin/casepacks/register",
                json={"pack_key": "riverside_grocery", "pack_path": str(PACK)},
                headers=headers,
            )
            assert reg.status_code == 201
            packs = await client.get("/api/casepacks", headers=headers)
            assert packs.status_code == 200
            pack = packs.json()[0]
            assert "errors" in pack
            assert "warnings" in pack
            assert "exit_code" in pack
        await engine.dispose()
    asyncio.run(run())
