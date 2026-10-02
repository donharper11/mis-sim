"""M5.7 clone, archive, and reset lifecycle API contract tests.

Covers all nine acceptance criteria:
  1. Clone: new section has same pack/teams/settings; instance at setup/round 0; no runtime rows; original unchanged
  2. Archive: completed instance -> archived; excluded from setup list; included in grade export
  3. Archive rejected: non-completed -> 409
  4. Reset: setup instance -> all runtime tables empty; round 0; pack binding preserved
  5. Reset rejected: active/completed -> 409
  6. Confirmation: missing/mismatched confirm_instance_id -> 422
  7. Cascade verification: after reset, runtime tables for that instance_id have zero rows; other instances unaffected
  8. Auth: wrong instructor -> 403; student -> 403
  9. Browser proof is separate (frontend)
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api import deps, instructor, platform
from app.main import create_app
from app.models.base import Base
from app.models.grading import GradeConfig, GradeOverride
from app.models.platform import Casepack, Course, Enrollment, Section, SimulationInstance, Team, User
from app.models.scheduling import RoundSchedule, RoundScheduleTeam
from app.round.models import RoundResult, TeamStateRow
from app.services.auth import create_access_token, hash_password
from app.simulation.models import SimulationCheckpointV1, SimulationRunV1, SimulationSheetV1


PACK = Path(__file__).resolve().parents[1] / "packs" / "riverside_grocery"


def _token(user: User) -> str:
    return create_access_token(user_id=user.id, role=user.role)


def _headers(user: User) -> dict:
    return {"Authorization": f"Bearer {_token(user)}"}


async def _fixture(tmp_path):
    """Create a test database with instances in various states for lifecycle testing."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'lifecycle.db'}")
    tables = [
        User.__table__, Course.__table__, Section.__table__,
        SimulationInstance.__table__, Team.__table__, Enrollment.__table__,
        Casepack.__table__, RoundSchedule.__table__, RoundScheduleTeam.__table__,
        SimulationRunV1.__table__, SimulationSheetV1.__table__,
        SimulationCheckpointV1.__table__,
        RoundResult.__table__, TeamStateRow.__table__,
        GradeOverride.__table__, GradeConfig.__table__,
    ]
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=tables)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        owner = User(name="Owner", email="owner@lifecycle.test", role="instructor", password_hash=hash_password("pw"))
        other = User(name="Other", email="other@lifecycle.test", role="instructor", password_hash=hash_password("pw"))
        student = User(student_id="S1", name="Student", email="student@lifecycle.test", role="student", password_hash=hash_password("pw"))
        session.add_all([owner, other, student])
        await session.flush()

        course = Course(course_code="LC", course_name="Lifecycle", academic_year="2026", semester="A", instructor_id=owner.id)
        other_course = Course(course_code="OT", course_name="Other", academic_year="2026", semester="A", instructor_id=other.id)
        session.add_all([course, other_course])
        await session.flush()

        # Section A: setup-status instance (for reset testing)
        section_a = Section(course_id=course.id, section_code="A", section_name="Section A", max_teams=4, team_size_min=1, team_size_max=4)
        # Section B: completed-status instance (for archive testing)
        section_b = Section(course_id=course.id, section_code="B", section_name="Section B", max_teams=4, team_size_min=1, team_size_max=4)
        # Section C: active-status instance (for rejection testing)
        section_c = Section(course_id=course.id, section_code="C", section_name="Section C", max_teams=4, team_size_min=1, team_size_max=4)
        session.add_all([section_a, section_b, section_c])
        await session.flush()

        # Create instances
        instance_a = SimulationInstance(
            section_id=section_a.id, pack_key="test_pack", pack_version="1.0",
            pack_digest="sha256_test", total_rounds=6, status="setup", current_round=0,
            settings={"default_round_duration_hours": 24, "auto_advance_on_deadline": False},
        )
        instance_b = SimulationInstance(
            section_id=section_b.id, pack_key="test_pack", pack_version="1.0",
            pack_digest="sha256_test", total_rounds=6, status="completed", current_round=6,
        )
        instance_c = SimulationInstance(
            section_id=section_c.id, pack_key="test_pack", pack_version="1.0",
            pack_digest="sha256_test", total_rounds=6, status="active", current_round=3,
        )
        session.add_all([instance_a, instance_b, instance_c])
        await session.flush()

        # Teams for section A
        team_a1 = Team(section_id=section_a.id, instance_id=instance_a.instance_id, name="Alpha")
        team_a2 = Team(section_id=section_a.id, instance_id=instance_a.instance_id, name="Beta")
        # Teams for section B
        team_b1 = Team(section_id=section_b.id, instance_id=instance_b.instance_id, name="Gamma")
        session.add_all([team_a1, team_a2, team_b1])
        await session.flush()

        # Add runtime data to instance A (setup) for reset testing
        session.add(RoundResult(
            instance_id=instance_a.instance_id, team_id=team_a1.id, round=1,
            payload={"scorecard": {"financial": 0.5}},
        ))
        session.add(GradeConfig(
            instance_id=instance_a.instance_id,
            weight_financial=0.25, weight_customer=0.25,
            weight_internal_process=0.25, weight_learning_growth=0.25,
            rounds_mode="final", updated_by=owner.id,
        ))
        session.add(GradeOverride(
            instance_id=instance_a.instance_id, team_id=team_a1.id,
            override=0.85, reason="Test", updated_by=owner.id,
        ))

        # Add runtime data to instance B (completed) for grade export testing
        session.add(RoundResult(
            instance_id=instance_b.instance_id, team_id=team_b1.id, round=1,
            payload={"scorecard": {"financial": 0.8, "customer": 0.7, "internal_process": 0.6, "learning_growth": 0.5}},
        ))

        # Enrollment for section A
        enrollment = Enrollment(section_id=section_a.id, user_id=student.id, team_id=team_a1.id, role="student")
        session.add(enrollment)

        await session.commit()
        values = {
            "owner": owner, "other": other, "student": student,
            "course": course, "other_course": other_course,
            "section_a": section_a, "section_b": section_b, "section_c": section_c,
            "instance_a": instance_a, "instance_b": instance_b, "instance_c": instance_c,
            "team_a1": team_a1, "team_a2": team_a2, "team_b1": team_b1,
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


# ---------------------------------------------------------------------------
# AC-1: Clone — new section has same pack/teams/settings; instance at setup/round 0;
#        no runtime rows; original unchanged
# ---------------------------------------------------------------------------

def test_clone_section(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        headers = _headers(data["owner"])
        sid = data["section_a"].id
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/api/instructor/sections/{sid}/clone",
                json={"section_code": "D", "section_name": "Section D"},
                headers=headers,
            )
            assert resp.status_code == 200, resp.text
            body = resp.json()
            new_section = body["section"]

            # Same pack binding
            assert new_section["instance"]["pack_key"] == "test_pack"
            assert new_section["instance"]["pack_version"] == "1.0"
            assert new_section["instance"]["pack_digest"] == "sha256_test"

            # Status and round
            assert new_section["instance"]["status"] == "setup"
            assert new_section["instance"]["current_round"] == 0

            # Same team count and names
            assert len(new_section["teams"]) == 2
            team_names = {t["name"] for t in new_section["teams"]}
            assert team_names == {"Alpha", "Beta"}

            # No enrollments
            assert new_section["enrollment_count"] == 0

            # New section properties
            assert new_section["section_code"] == "D"
            assert new_section["section_name"] == "Section D"
            assert new_section["max_teams"] == 4
            assert new_section["team_size_min"] == 1
            assert new_section["team_size_max"] == 4

            # Original unchanged
            setup = await client.get(
                f"/api/instructor/courses/{data['course'].id}/setup",
                headers=headers,
            )
            original = next(s for s in setup.json()["sections"] if s["id"] == sid)
            assert original["instance"]["current_round"] == 0
            assert original["instance"]["status"] == "setup"
            assert original["enrollment_count"] == 1  # student still enrolled

        await engine.dispose()
    asyncio.run(run())


def test_clone_section_default_suffix(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        headers = _headers(data["owner"])
        sid = data["section_a"].id
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/api/instructor/sections/{sid}/clone",
                json={},
                headers=headers,
            )
            assert resp.status_code == 200, resp.text
            body = resp.json()
            assert body["section"]["section_code"] == "A (clone)"
            assert body["section"]["section_name"] == "Section A (clone)"

        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# AC-2: Archive — completed instance -> archived; excluded from setup list;
#        included in grade export
# ---------------------------------------------------------------------------

def test_archive_completed_instance(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        headers = _headers(data["owner"])
        iid = data["instance_b"].instance_id
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/api/instructor/instances/{iid}/archive",
                json={"confirm_instance_id": iid},
                headers=headers,
            )
            assert resp.status_code == 200, resp.text
            body = resp.json()
            assert body["instance"]["status"] == "archived"
            assert body["instance"]["instance_id"] == iid

            # Excluded from setup list
            setup = await client.get(
                f"/api/instructor/courses/{data['course'].id}/setup",
                headers=headers,
            )
            section_ids = [s["id"] for s in setup.json()["sections"]]
            assert data["section_b"].id not in section_ids

            # Still accessible for grade export
            export = await client.get(
                f"/api/instructor/instances/{iid}/grades/export",
                headers=headers,
            )
            assert export.status_code == 200

        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# AC-3: Archive rejected — non-completed instance returns 409
# ---------------------------------------------------------------------------

def test_archive_rejected_non_completed(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        headers = _headers(data["owner"])

        # Try to archive a setup instance
        iid_a = data["instance_a"].instance_id
        resp = None
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/api/instructor/instances/{iid_a}/archive",
                json={"confirm_instance_id": iid_a},
                headers=headers,
            )
            assert resp.status_code == 409

            # Try to archive an active instance
            iid_c = data["instance_c"].instance_id
            resp2 = await client.post(
                f"/api/instructor/instances/{iid_c}/archive",
                json={"confirm_instance_id": iid_c},
                headers=headers,
            )
            assert resp2.status_code == 409

        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# AC-4: Reset — setup instance -> all runtime tables empty; round 0; pack binding preserved
# ---------------------------------------------------------------------------

def test_reset_setup_instance(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        headers = _headers(data["owner"])
        iid = data["instance_a"].instance_id
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/api/instructor/instances/{iid}/reset",
                json={"confirm_instance_id": iid},
                headers=headers,
            )
            assert resp.status_code == 200, resp.text
            body = resp.json()
            assert body["instance"]["status"] == "setup"
            assert body["instance"]["current_round"] == 0
            assert body["instance"]["pack_key"] == "test_pack"
            assert body["instance"]["pack_version"] == "1.0"
            assert body["instance"]["pack_digest"] == "sha256_test"

        # Verify runtime tables are empty for this instance
        async with factory() as session:
            assert await session.scalar(select(func.count()).select_from(RoundResult).where(RoundResult.instance_id == iid)) == 0
            assert await session.scalar(select(func.count()).select_from(GradeConfig).where(GradeConfig.instance_id == iid)) == 0
            assert await session.scalar(select(func.count()).select_from(GradeOverride).where(GradeOverride.instance_id == iid)) == 0

            # Teams are preserved
            teams = list((await session.scalars(select(Team).where(Team.instance_id == iid).order_by(Team.id))).all())
            assert len(teams) == 2
            assert {t.name for t in teams} == {"Alpha", "Beta"}

            # Settings preserved
            instance = await session.get(SimulationInstance, iid)
            assert instance.settings.get("default_round_duration_hours") == 24

        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# AC-5: Reset rejected — active or completed instance returns 409
# ---------------------------------------------------------------------------

def test_reset_rejected_non_setup(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        headers = _headers(data["owner"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Active instance
            iid_c = data["instance_c"].instance_id
            resp = await client.post(
                f"/api/instructor/instances/{iid_c}/reset",
                json={"confirm_instance_id": iid_c},
                headers=headers,
            )
            assert resp.status_code == 409

            # Completed instance
            iid_b = data["instance_b"].instance_id
            resp2 = await client.post(
                f"/api/instructor/instances/{iid_b}/reset",
                json={"confirm_instance_id": iid_b},
                headers=headers,
            )
            assert resp2.status_code == 409

        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# AC-6: Confirmation — missing/mismatched confirm_instance_id returns 422
# ---------------------------------------------------------------------------

def test_confirmation_mismatch(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        headers = _headers(data["owner"])
        iid = data["instance_a"].instance_id
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Mismatched confirm_instance_id for reset
            resp = await client.post(
                f"/api/instructor/instances/{iid}/reset",
                json={"confirm_instance_id": iid + 999},
                headers=headers,
            )
            assert resp.status_code == 422

            # Mismatched confirm_instance_id for archive
            iid_b = data["instance_b"].instance_id
            resp2 = await client.post(
                f"/api/instructor/instances/{iid_b}/archive",
                json={"confirm_instance_id": iid_b + 999},
                headers=headers,
            )
            assert resp2.status_code == 422

            # Missing confirm_instance_id
            resp3 = await client.post(
                f"/api/instructor/instances/{iid}/reset",
                json={},
                headers=headers,
            )
            assert resp3.status_code == 422

        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# AC-7: Cascade verification — after reset, runtime tables for that instance_id
#        have zero rows; other instances are unaffected
# ---------------------------------------------------------------------------

def test_cascade_isolation(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        headers = _headers(data["owner"])
        iid_a = data["instance_a"].instance_id
        iid_b = data["instance_b"].instance_id

        # Verify instance B has a RoundResult before the reset
        async with factory() as session:
            count_b_before = await session.scalar(
                select(func.count()).select_from(RoundResult).where(RoundResult.instance_id == iid_b)
            )
            assert count_b_before == 1

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/api/instructor/instances/{iid_a}/reset",
                json={"confirm_instance_id": iid_a},
                headers=headers,
            )
            assert resp.status_code == 200

        # Instance A runtime rows gone
        async with factory() as session:
            assert await session.scalar(
                select(func.count()).select_from(RoundResult).where(RoundResult.instance_id == iid_a)
            ) == 0
            assert await session.scalar(
                select(func.count()).select_from(GradeConfig).where(GradeConfig.instance_id == iid_a)
            ) == 0
            assert await session.scalar(
                select(func.count()).select_from(GradeOverride).where(GradeOverride.instance_id == iid_a)
            ) == 0

            # Instance B runtime rows still present
            count_b_after = await session.scalar(
                select(func.count()).select_from(RoundResult).where(RoundResult.instance_id == iid_b)
            )
            assert count_b_after == 1

        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# AC-8: Auth — wrong instructor -> 403; student -> 403
# ---------------------------------------------------------------------------

def test_auth_wrong_instructor_forbidden(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        wrong_headers = _headers(data["other"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Clone
            resp = await client.post(
                f"/api/instructor/sections/{data['section_a'].id}/clone",
                json={},
                headers=wrong_headers,
            )
            assert resp.status_code == 403

            # Archive
            iid_b = data["instance_b"].instance_id
            resp2 = await client.post(
                f"/api/instructor/instances/{iid_b}/archive",
                json={"confirm_instance_id": iid_b},
                headers=wrong_headers,
            )
            assert resp2.status_code == 403

            # Reset
            iid_a = data["instance_a"].instance_id
            resp3 = await client.post(
                f"/api/instructor/instances/{iid_a}/reset",
                json={"confirm_instance_id": iid_a},
                headers=wrong_headers,
            )
            assert resp3.status_code == 403

        await engine.dispose()
    asyncio.run(run())


def test_auth_student_forbidden(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        student_headers = _headers(data["student"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Clone
            resp = await client.post(
                f"/api/instructor/sections/{data['section_a'].id}/clone",
                json={},
                headers=student_headers,
            )
            assert resp.status_code == 403

            # Archive
            iid_b = data["instance_b"].instance_id
            resp2 = await client.post(
                f"/api/instructor/instances/{iid_b}/archive",
                json={"confirm_instance_id": iid_b},
                headers=student_headers,
            )
            assert resp2.status_code == 403

            # Reset
            iid_a = data["instance_a"].instance_id
            resp3 = await client.post(
                f"/api/instructor/instances/{iid_a}/reset",
                json={"confirm_instance_id": iid_a},
                headers=student_headers,
            )
            assert resp3.status_code == 403

        await engine.dispose()
    asyncio.run(run())
