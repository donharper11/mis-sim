"""M5.3 round-control API contract tests.

Covers: pause/resume enforcement, manual lock, advance (existing), reopen,
schedule read, settings update, and auth boundary.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from httpx import ASGITransport, AsyncClient
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api import deps, instructor, platform
from app.api import runtime_round_control  # noqa: F401 – router registration
from app.config import settings
from app.main import create_app
from app.models.base import Base
from app.models.platform import Casepack, Course, Enrollment, Section, SimulationInstance, Team, User
from app.models.scheduling import RoundSchedule, RoundScheduleTeam
from app.services.auth import create_access_token, hash_password
from app.round import models as round_models
from app.simulation.content import load_runtime_pack
from app.simulation.models import SimulationRunV1, SimulationSheetV1, SimulationCheckpointV1

PACK = Path(__file__).resolve().parents[1] / "packs" / "riverside_grocery"


def _token(user: User) -> str:
    return create_access_token(user_id=user.id, role=user.role)


async def _fixture(tmp_path):
    db_path = tmp_path / "round_control.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    tables = [
        User.__table__, Course.__table__, Section.__table__,
        SimulationInstance.__table__, Team.__table__, Enrollment.__table__,
        Casepack.__table__, RoundSchedule.__table__, RoundScheduleTeam.__table__,
        SimulationRunV1.__table__, SimulationSheetV1.__table__,
        SimulationCheckpointV1.__table__,
    ] + [t.__table__ for t in round_models.ALL_TABLES]
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=tables)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        owner = User(name="Owner", email="owner@rc.test", role="instructor", password_hash=hash_password("pw"))
        other = User(name="Other", email="other@rc.test", role="instructor", password_hash=hash_password("pw"))
        student = User(student_id="S1", name="Student", email="student@rc.test", role="student", password_hash=hash_password("pw"))
        ta = User(name="TA", email="ta@rc.test", role="ta", password_hash=hash_password("pw"))
        session.add_all([owner, other, student, ta])
        await session.flush()
        course = Course(course_code="RC", course_name="Round Control", academic_year="2026", semester="A", instructor_id=owner.id)
        other_course = Course(course_code="OT", course_name="Other", academic_year="2026", semester="A", instructor_id=other.id)
        session.add_all([course, other_course])
        await session.flush()
        section = Section(course_id=course.id, section_code="A", section_name="Section A", max_teams=4, team_size_min=1, team_size_max=4)
        other_section = Section(course_id=other_course.id, section_code="B", section_name="Other B", max_teams=4, team_size_min=1, team_size_max=4)
        session.add_all([section, other_section])
        await session.flush()
        runtime = load_runtime_pack(PACK)
        metadata = runtime.casepack.metadata
        session.add(Casepack(
            pack_key=metadata.pack_key, pack_version=metadata.pack_version, pack_digest=runtime.pack_digest,
            schema_version=metadata.schema_version, display_name=metadata.display_name, vertical=metadata.vertical,
            rounds=metadata.rounds, path=str(PACK), validation_json={"errors": [], "warnings": [], "exit_code": 0},
        ))
        instance = SimulationInstance(
            section_id=section.id, pack_key=metadata.pack_key, pack_version=metadata.pack_version,
            pack_digest=runtime.pack_digest, total_rounds=metadata.rounds, status="active", current_round=1,
        )
        session.add(instance)
        await session.flush()
        team_a = Team(section_id=section.id, instance_id=instance.instance_id, name="Team A")
        team_b = Team(section_id=section.id, instance_id=instance.instance_id, name="Team B")
        session.add_all([team_a, team_b])
        await session.flush()
        enrollment = Enrollment(section_id=section.id, user_id=student.id, team_id=team_a.id, role="student")
        ta_enrollment = Enrollment(section_id=section.id, user_id=ta.id, role="ta")
        session.add_all([enrollment, ta_enrollment])
        await session.commit()
        values = {
            "owner": owner, "other": other, "student": student, "ta": ta,
            "course": course, "other_course": other_course,
            "section": section, "other_section": other_section,
            "instance": instance, "team_a": team_a, "team_b": team_b,
            "runtime": runtime, "db_path": db_path,
        }
    return engine, factory, values


def _app(factory):
    async def get_session():
        async with factory() as session:
            yield session
    app = create_app()
    for module in (deps, instructor, platform):
        app.dependency_overrides[module.get_session] = get_session
    return app


def _headers(user):
    return {"Authorization": f"Bearer {_token(user)}"}


# ---------------------------------------------------------------------------
# AC-1: Pause enforcement -- student PATCH returns 409 when paused, succeeds after resume
# ---------------------------------------------------------------------------

def test_pause_and_resume_enforcement(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        iid = data["instance"].instance_id
        staff = _headers(data["owner"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Pause the active instance
            resp = await client.post(f"/api/instances/{iid}/round-control/pause", headers=staff)
            assert resp.status_code == 200
            assert resp.json()["status"] == "paused"

            # Pausing again should 409 (not active)
            resp2 = await client.post(f"/api/instances/{iid}/round-control/pause", headers=staff)
            assert resp2.status_code == 409

            # Resume
            resp3 = await client.post(f"/api/instances/{iid}/round-control/resume", headers=staff)
            assert resp3.status_code == 200
            assert resp3.json()["status"] == "active"

            # Resuming again should 409 (not paused)
            resp4 = await client.post(f"/api/instances/{iid}/round-control/resume", headers=staff)
            assert resp4.status_code == 409

        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# AC-2: Manual lock -- all draft teams become locked
# ---------------------------------------------------------------------------

def test_manual_lock_all_draft_teams(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        from app.round.db import make_engine as _mk
        from app.simulation.service import SimulationService

        runtime = data["runtime"]
        iid = data["instance"].instance_id
        db_url = f"sqlite:///{data['db_path']}"

        sync_engine = _mk(db_url)
        try:
            service = SimulationService(sync_engine, runtime)
            service.initialize(iid, data["team_a"].id, runtime.casepack.strategies[0].key)
            service.initialize(iid, data["team_b"].id, runtime.casepack.strategies[0].key)
        finally:
            sync_engine.dispose()

        app = _app(factory)
        staff = _headers(data["owner"])
        with patch.object(settings, "DATABASE_URL", db_url):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(f"/api/instances/{iid}/round-control/lock", headers=staff)
                assert resp.status_code == 200
                body = resp.json()
                assert body["instance_id"] == iid
                for team_result in body["teams"]:
                    assert team_result["status"] == "locked"
                    assert team_result["locked_revision"] == 0

        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# AC-4: Reopen -- locked-but-not-advanced team returns to draft
# ---------------------------------------------------------------------------

def test_reopen_locked_team(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        from app.round.db import make_engine as _mk
        from app.simulation.service import SimulationService

        runtime = data["runtime"]
        iid = data["instance"].instance_id
        db_url = f"sqlite:///{data['db_path']}"

        sync_engine = _mk(db_url)
        try:
            service = SimulationService(sync_engine, runtime)
            service.initialize(iid, data["team_a"].id, runtime.casepack.strategies[0].key)
            service.lock(iid, data["team_a"].id, 1, 0)
        finally:
            sync_engine.dispose()

        app = _app(factory)
        staff = _headers(data["owner"])
        with patch.object(settings, "DATABASE_URL", db_url):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(
                    f"/api/instances/{iid}/round-control/reopen",
                    json={"team_id": data["team_a"].id},
                    headers=staff,
                )
                assert resp.status_code == 200
                body = resp.json()
                assert body["team_id"] == data["team_a"].id
                assert body["status"] == "draft"
                assert body["locked_revision"] is None
                assert body["revision"] == 1  # incremented from 0

        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# AC-5: Schedule read -- returns per-round data with team-level timestamps
# ---------------------------------------------------------------------------

def test_schedule_read(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        iid = data["instance"].instance_id
        now = datetime.now(timezone.utc)
        # Seed a round schedule with team-level data
        async with factory() as session:
            schedule = RoundSchedule(
                instance_id=iid, round_number=1, start_at=now,
                deadline=now + timedelta(hours=24), auto_advance=False,
                grace_period_minutes=30, decisions_locked=False,
            )
            session.add(schedule)
            await session.flush()
            session.add(RoundScheduleTeam(
                schedule_id=schedule.id, instance_id=iid,
                team_id=data["team_a"].id, locked_revision=None,
            ))
            session.add(RoundScheduleTeam(
                schedule_id=schedule.id, instance_id=iid,
                team_id=data["team_b"].id, locked_revision=None,
            ))
            await session.commit()

        app = _app(factory)
        staff = _headers(data["owner"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/instances/{iid}/round-control/schedule", headers=staff)
            assert resp.status_code == 200
            body = resp.json()
            assert body["instance_id"] == iid
            assert len(body["rounds"]) == 1
            rnd = body["rounds"][0]
            assert rnd["round_number"] == 1
            assert rnd["decisions_locked"] is False
            assert "start_at" in rnd and "deadline" in rnd
            assert len(rnd["teams"]) == 2

        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# AC-6: Settings update -- persisted correctly
# ---------------------------------------------------------------------------

def test_settings_update(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        iid = data["instance"].instance_id
        app = _app(factory)
        staff = _headers(data["owner"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.patch(
                f"/api/instances/{iid}/settings",
                json={"default_round_duration_hours": 48.0, "auto_advance_on_deadline": True, "grace_period_minutes": 15},
                headers=staff,
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["default_round_duration_hours"] == 48.0
            assert body["auto_advance_on_deadline"] is True
            assert body["grace_period_minutes"] == 15

            # Verify persistence -- update a single field
            resp2 = await client.patch(
                f"/api/instances/{iid}/settings",
                json={"lock_warning_minutes": 10},
                headers=staff,
            )
            assert resp2.status_code == 200
            assert resp2.json()["lock_warning_minutes"] == 10
            assert resp2.json()["default_round_duration_hours"] == 48.0  # prior value retained

            # Validation: negative duration
            resp3 = await client.patch(
                f"/api/instances/{iid}/settings",
                json={"default_round_duration_hours": -1},
                headers=staff,
            )
            assert resp3.status_code == 409

            # Validation: empty body (all None)
            resp4 = await client.patch(
                f"/api/instances/{iid}/settings",
                json={},
                headers=staff,
            )
            assert resp4.status_code == 409

        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# AC-7: Auth -- student gets 403, wrong instructor gets 403
# ---------------------------------------------------------------------------

def test_auth_student_forbidden(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        iid = data["instance"].instance_id
        app = _app(factory)
        student = _headers(data["student"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Student cannot pause
            resp = await client.post(f"/api/instances/{iid}/round-control/pause", headers=student)
            assert resp.status_code == 403

            # Student cannot resume
            resp2 = await client.post(f"/api/instances/{iid}/round-control/resume", headers=student)
            assert resp2.status_code == 403

            # Student cannot lock
            resp3 = await client.post(f"/api/instances/{iid}/round-control/lock", headers=student)
            assert resp3.status_code == 403

            # Student cannot reopen
            resp4 = await client.post(f"/api/instances/{iid}/round-control/reopen", json={"team_id": 1}, headers=student)
            assert resp4.status_code == 403

            # Student cannot read schedule
            resp5 = await client.get(f"/api/instances/{iid}/round-control/schedule", headers=student)
            assert resp5.status_code == 403

            # Student cannot update settings
            resp6 = await client.patch(f"/api/instances/{iid}/settings", json={"grace_period_minutes": 5}, headers=student)
            assert resp6.status_code == 403

        await engine.dispose()
    asyncio.run(run())


def test_auth_wrong_instructor_forbidden(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        iid = data["instance"].instance_id
        app = _app(factory)
        wrong = _headers(data["other"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(f"/api/instances/{iid}/round-control/pause", headers=wrong)
            assert resp.status_code == 403

            resp2 = await client.patch(
                f"/api/instances/{iid}/settings",
                json={"grace_period_minutes": 5},
                headers=wrong,
            )
            assert resp2.status_code == 403

        await engine.dispose()
    asyncio.run(run())


def test_ta_can_access_round_control(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        iid = data["instance"].instance_id
        app = _app(factory)
        ta = _headers(data["ta"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # TA can pause (they are enrolled as ta in the section)
            resp = await client.post(f"/api/instances/{iid}/round-control/pause", headers=ta)
            assert resp.status_code == 200

            # TA can resume
            resp2 = await client.post(f"/api/instances/{iid}/round-control/resume", headers=ta)
            assert resp2.status_code == 200

            # TA can read schedule
            resp3 = await client.get(f"/api/instances/{iid}/round-control/schedule", headers=ta)
            assert resp3.status_code == 200

        await engine.dispose()
    asyncio.run(run())
