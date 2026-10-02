"""M5.5 grading and export API contract tests.

Covers all nine acceptance criteria:
  1. Default derivation (equal-weighted BSC average)
  2. Custom weights (financial=0.5 shifts grade)
  3. Average mode (grades average across all completed rounds)
  4. Override (override=0.85 becomes final_grade; derived_grade visible)
  5. CSV export (correct columns, values, UTF-8, header row)
  6. Incomplete team (null derived grade, included in export)
  7. Auth (student 403, wrong instructor 403)
  8. Weights validation (sum != 1.0 -> 422, negative -> 422)
  9. Browser proof is separate (frontend)
"""

from __future__ import annotations

import asyncio
import csv
import io

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api import deps, instructor, platform
from app.main import create_app
from app.models.base import Base
from app.models.grading import GradeConfig, GradeOverride
from app.models.platform import Casepack, Course, Enrollment, Section, SimulationInstance, Team, User
from app.round.models import RoundResult, TeamStateRow
from app.services.auth import create_access_token, hash_password


def _token(user: User) -> str:
    return create_access_token(user_id=user.id, role=user.role)


def _headers(user: User) -> dict:
    return {"Authorization": f"Bearer {_token(user)}"}


async def _fixture(tmp_path):
    """Create a test database with instance, teams, and round results."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'grading.db'}")
    tables = [
        User.__table__, Course.__table__, Section.__table__,
        SimulationInstance.__table__, Team.__table__, Enrollment.__table__,
        Casepack.__table__, RoundResult.__table__, TeamStateRow.__table__,
        GradeOverride.__table__, GradeConfig.__table__,
    ]
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=tables)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        owner = User(name="Owner", email="owner@grading.test", role="instructor", password_hash=hash_password("pw"))
        other = User(name="Other", email="other@grading.test", role="instructor", password_hash=hash_password("pw"))
        student = User(student_id="S1", name="Student", email="student@grading.test", role="student", password_hash=hash_password("pw"))
        session.add_all([owner, other, student])
        await session.flush()

        course = Course(course_code="MIS301", course_name="MIS", academic_year="2026", semester="A", instructor_id=owner.id)
        other_course = Course(course_code="OTHER", course_name="Other", academic_year="2026", semester="A", instructor_id=other.id)
        session.add_all([course, other_course])
        await session.flush()

        section = Section(course_id=course.id, section_code="SEC1", section_name="Section 1", max_teams=4, team_size_min=1, team_size_max=4)
        other_section = Section(course_id=other_course.id, section_code="B", section_name="Other B", max_teams=4, team_size_min=1, team_size_max=4)
        session.add_all([section, other_section])
        await session.flush()

        instance = SimulationInstance(
            section_id=section.id, pack_key="test_pack", pack_version="1.0",
            total_rounds=3, status="active", current_round=3,
        )
        session.add(instance)
        await session.flush()

        team_a = Team(section_id=section.id, instance_id=instance.instance_id, name="Team Alpha")
        team_b = Team(section_id=section.id, instance_id=instance.instance_id, name="Team Beta")
        team_c = Team(section_id=section.id, instance_id=instance.instance_id, name="Team Incomplete")
        session.add_all([team_a, team_b, team_c])
        await session.flush()

        # Team A: has results for rounds 1, 2, and 3
        for rnd, scores in [
            (1, {"financial": 0.60, "customer": 0.50, "internal_process": 0.40, "learning_growth": 0.70}),
            (2, {"financial": 0.70, "customer": 0.60, "internal_process": 0.50, "learning_growth": 0.80}),
            (3, {"financial": 0.80, "customer": 0.65, "internal_process": 0.50, "learning_growth": 0.70}),
        ]:
            session.add(RoundResult(
                instance_id=instance.instance_id, team_id=team_a.id, round=rnd,
                payload={"scorecard": scores, "firm_score": 1.23},
            ))

        # Team A strategy
        session.add(TeamStateRow(
            instance_id=instance.instance_id, team_id=team_a.id,
            current_round=3, declared_strategy="differentiation",
            declared_strategy_round=1, cash=50000, opex_runrate=5000,
        ))

        # Team B: has results for rounds 1 and 2 only
        for rnd, scores in [
            (1, {"financial": 0.55, "customer": 0.45, "internal_process": 0.35, "learning_growth": 0.65}),
            (2, {"financial": 0.65, "customer": 0.55, "internal_process": 0.45, "learning_growth": 0.75}),
        ]:
            session.add(RoundResult(
                instance_id=instance.instance_id, team_id=team_b.id, round=rnd,
                payload={"scorecard": scores, "firm_score": 1.10},
            ))

        session.add(TeamStateRow(
            instance_id=instance.instance_id, team_id=team_b.id,
            current_round=2, declared_strategy="cost_leadership",
            declared_strategy_round=1, cash=40000, opex_runrate=4000,
        ))

        # Team C: no results (incomplete)

        await session.commit()
        values = {
            "owner": owner, "other": other, "student": student,
            "course": course, "other_course": other_course,
            "section": section, "other_section": other_section,
            "instance": instance,
            "team_a": team_a, "team_b": team_b, "team_c": team_c,
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
# AC-1: Default derivation — equal-weighted average of 4 BSC dimensions
# ---------------------------------------------------------------------------

def test_default_derivation(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        headers = _headers(data["owner"])
        iid = data["instance"].instance_id
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/instructor/instances/{iid}/grades", headers=headers)
            assert resp.status_code == 200
            body = resp.json()
            assert body["instance_id"] == iid
            assert body["config"]["rounds_mode"] == "final"

            # Team Alpha: final round (3) scorecard = financial=0.80, customer=0.65, internal_process=0.50, learning_growth=0.70
            # Equal-weighted average = (0.80 + 0.65 + 0.50 + 0.70) / 4 = 0.6625
            team_a = next(t for t in body["teams"] if t["team_id"] == data["team_a"].id)
            assert abs(team_a["derived_grade"] - 0.6625) < 0.0001
            assert team_a["final_grade"] == team_a["derived_grade"]
            assert team_a["override"] is None
            assert team_a["strategy"] == "differentiation"
            assert team_a["scorecard"]["financial"] == 0.80

            # Team Beta: final round (2) scorecard = financial=0.65, customer=0.55, internal_process=0.45, learning_growth=0.75
            # Equal-weighted average = (0.65 + 0.55 + 0.45 + 0.75) / 4 = 0.60
            team_b = next(t for t in body["teams"] if t["team_id"] == data["team_b"].id)
            assert abs(team_b["derived_grade"] - 0.60) < 0.0001

        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# AC-2: Custom weights — financial=0.5, others=0.167 each
# ---------------------------------------------------------------------------

def test_custom_weights(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        headers = _headers(data["owner"])
        iid = data["instance"].instance_id
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Set custom weights: financial heavy
            config_resp = await client.put(
                f"/api/instructor/instances/{iid}/grades/config",
                json={
                    "weight_financial": 0.5,
                    "weight_customer": 0.167,
                    "weight_internal_process": 0.167,
                    "weight_learning_growth": 0.166,
                    "rounds_mode": "final",
                },
                headers=headers,
            )
            assert config_resp.status_code == 200

            # Re-read grades
            resp = await client.get(f"/api/instructor/instances/{iid}/grades", headers=headers)
            body = resp.json()

            # Team Alpha: final round (3): financial=0.80, customer=0.65, internal_process=0.50, learning_growth=0.70
            # Weighted: 0.80*0.5 + 0.65*0.167 + 0.50*0.167 + 0.70*0.166
            # = 0.40 + 0.10855 + 0.0835 + 0.1162 = 0.70825
            team_a = next(t for t in body["teams"] if t["team_id"] == data["team_a"].id)
            expected = 0.80 * 0.5 + 0.65 * 0.167 + 0.50 * 0.167 + 0.70 * 0.166
            assert abs(team_a["derived_grade"] - expected) < 0.001
            # With financial heavier, the grade should be higher than the equal-weighted 0.6625
            assert team_a["derived_grade"] > 0.6625

        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# AC-3: Average mode — grades average across all completed rounds
# ---------------------------------------------------------------------------

def test_average_mode(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        headers = _headers(data["owner"])
        iid = data["instance"].instance_id
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Set average mode
            config_resp = await client.put(
                f"/api/instructor/instances/{iid}/grades/config",
                json={
                    "weight_financial": 0.25,
                    "weight_customer": 0.25,
                    "weight_internal_process": 0.25,
                    "weight_learning_growth": 0.25,
                    "rounds_mode": "average",
                },
                headers=headers,
            )
            assert config_resp.status_code == 200

            resp = await client.get(f"/api/instructor/instances/{iid}/grades", headers=headers)
            body = resp.json()
            assert body["config"]["rounds_mode"] == "average"

            # Team Alpha has 3 rounds:
            # R1: financial=0.60, customer=0.50, internal_process=0.40, learning_growth=0.70
            # R2: financial=0.70, customer=0.60, internal_process=0.50, learning_growth=0.80
            # R3: financial=0.80, customer=0.65, internal_process=0.50, learning_growth=0.70
            # Average scorecard: financial=(0.60+0.70+0.80)/3, customer=(0.50+0.60+0.65)/3, etc.
            avg_financial = (0.60 + 0.70 + 0.80) / 3
            avg_customer = (0.50 + 0.60 + 0.65) / 3
            avg_internal = (0.40 + 0.50 + 0.50) / 3
            avg_learning = (0.70 + 0.80 + 0.70) / 3
            expected = (avg_financial + avg_customer + avg_internal + avg_learning) / 4

            team_a = next(t for t in body["teams"] if t["team_id"] == data["team_a"].id)
            assert abs(team_a["derived_grade"] - expected) < 0.001

            # The average-mode grade should differ from the final-only grade (0.6625)
            # Average: about 0.6148 vs final 0.6625
            assert abs(team_a["derived_grade"] - 0.6625) > 0.01

        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# AC-4: Override — override=0.85 becomes final_grade
# ---------------------------------------------------------------------------

def test_override(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        headers = _headers(data["owner"])
        iid = data["instance"].instance_id
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Set override for Team Alpha
            override_resp = await client.put(
                f"/api/instructor/instances/{iid}/grades/teams/{data['team_a'].id}",
                json={"override": 0.85, "reason": "Extra credit for presentation"},
                headers=headers,
            )
            assert override_resp.status_code == 200
            assert override_resp.json()["override"] == 0.85
            assert override_resp.json()["reason"] == "Extra credit for presentation"

            # Read grades and verify
            resp = await client.get(f"/api/instructor/instances/{iid}/grades", headers=headers)
            body = resp.json()

            team_a = next(t for t in body["teams"] if t["team_id"] == data["team_a"].id)
            assert team_a["override"] == 0.85
            assert team_a["final_grade"] == 0.85  # override wins
            assert abs(team_a["derived_grade"] - 0.6625) < 0.0001  # derived still visible
            assert team_a["override_reason"] == "Extra credit for presentation"

            # Clear override by setting to null
            clear_resp = await client.put(
                f"/api/instructor/instances/{iid}/grades/teams/{data['team_a'].id}",
                json={"override": None, "reason": None},
                headers=headers,
            )
            assert clear_resp.status_code == 200

            resp2 = await client.get(f"/api/instructor/instances/{iid}/grades", headers=headers)
            team_a2 = next(t for t in resp2.json()["teams"] if t["team_id"] == data["team_a"].id)
            assert team_a2["override"] is None
            assert team_a2["final_grade"] == team_a2["derived_grade"]

        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# AC-5: CSV export — correct columns, values, UTF-8, header row
# ---------------------------------------------------------------------------

def test_csv_export(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        headers = _headers(data["owner"])
        iid = data["instance"].instance_id
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Set an override first for richer CSV
            await client.put(
                f"/api/instructor/instances/{iid}/grades/teams/{data['team_a'].id}",
                json={"override": 0.90, "reason": "Adjusted"},
                headers=headers,
            )

            resp = await client.get(f"/api/instructor/instances/{iid}/grades/export", headers=headers)
            assert resp.status_code == 200
            assert resp.headers["content-type"].startswith("text/csv")
            assert "MIS301_SEC1_grades.csv" in resp.headers.get("content-disposition", "")

            # Parse CSV
            content = resp.content.decode("utf-8")
            reader = csv.reader(io.StringIO(content))
            rows = list(reader)

            # Header row
            assert rows[0] == [
                "team_name", "strategy", "final_realised_value",
                "financial", "customer", "internal_process", "learning_growth",
                "instructor_override", "final_grade", "override_reason",
            ]

            # Should have 3 team rows (Alpha, Beta, Incomplete)
            assert len(rows) == 4  # header + 3 teams

            # Find Team Alpha row
            alpha_row = next(r for r in rows[1:] if r[0] == "Team Alpha")
            assert alpha_row[1] == "differentiation"  # strategy
            assert alpha_row[7] == "0.9"  # override
            assert alpha_row[9] == "Adjusted"  # reason

            # Find Team Incomplete row — grade columns should be empty
            incomplete_row = next(r for r in rows[1:] if r[0] == "Team Incomplete")
            assert incomplete_row[3] == ""  # financial
            assert incomplete_row[8] == ""  # final_grade

        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# AC-6: Incomplete team — null derived grade, included in export
# ---------------------------------------------------------------------------

def test_incomplete_team(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        headers = _headers(data["owner"])
        iid = data["instance"].instance_id
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/instructor/instances/{iid}/grades", headers=headers)
            body = resp.json()

            team_c = next(t for t in body["teams"] if t["team_id"] == data["team_c"].id)
            assert team_c["derived_grade"] is None
            assert team_c["final_grade"] is None
            assert team_c["team_name"] == "Team Incomplete"

            # Also verify in export
            export_resp = await client.get(f"/api/instructor/instances/{iid}/grades/export", headers=headers)
            content = export_resp.content.decode("utf-8")
            reader = csv.reader(io.StringIO(content))
            rows = list(reader)
            incomplete_row = next(r for r in rows[1:] if r[0] == "Team Incomplete")
            assert incomplete_row is not None  # Team is included

        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# AC-7: Auth — student 403, wrong instructor 403
# ---------------------------------------------------------------------------

def test_auth_student_forbidden(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        iid = data["instance"].instance_id
        student_headers = _headers(data["student"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/instructor/instances/{iid}/grades", headers=student_headers)
            assert resp.status_code == 403

            resp2 = await client.put(
                f"/api/instructor/instances/{iid}/grades/config",
                json={
                    "weight_financial": 0.25, "weight_customer": 0.25,
                    "weight_internal_process": 0.25, "weight_learning_growth": 0.25,
                },
                headers=student_headers,
            )
            assert resp2.status_code == 403

            resp3 = await client.put(
                f"/api/instructor/instances/{iid}/grades/teams/{data['team_a'].id}",
                json={"override": 0.5},
                headers=student_headers,
            )
            assert resp3.status_code == 403

            resp4 = await client.get(f"/api/instructor/instances/{iid}/grades/export", headers=student_headers)
            assert resp4.status_code == 403

        await engine.dispose()
    asyncio.run(run())


def test_auth_wrong_instructor_forbidden(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        iid = data["instance"].instance_id
        wrong_headers = _headers(data["other"])
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/instructor/instances/{iid}/grades", headers=wrong_headers)
            assert resp.status_code == 403

            resp2 = await client.get(f"/api/instructor/instances/{iid}/grades/export", headers=wrong_headers)
            assert resp2.status_code == 403

        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# AC-8: Weights validation — sum != 1.0 -> 422, negative -> 422
# ---------------------------------------------------------------------------

def test_weights_validation(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        headers = _headers(data["owner"])
        iid = data["instance"].instance_id
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Sum not 1.0
            resp = await client.put(
                f"/api/instructor/instances/{iid}/grades/config",
                json={
                    "weight_financial": 0.5, "weight_customer": 0.5,
                    "weight_internal_process": 0.5, "weight_learning_growth": 0.5,
                },
                headers=headers,
            )
            assert resp.status_code == 422

            # Negative weight
            resp2 = await client.put(
                f"/api/instructor/instances/{iid}/grades/config",
                json={
                    "weight_financial": -0.1, "weight_customer": 0.4,
                    "weight_internal_process": 0.4, "weight_learning_growth": 0.3,
                },
                headers=headers,
            )
            assert resp2.status_code == 422

            # Invalid rounds_mode
            resp3 = await client.put(
                f"/api/instructor/instances/{iid}/grades/config",
                json={
                    "weight_financial": 0.25, "weight_customer": 0.25,
                    "weight_internal_process": 0.25, "weight_learning_growth": 0.25,
                    "rounds_mode": "invalid",
                },
                headers=headers,
            )
            assert resp3.status_code == 422

            # Valid weights near 1.0 (within tolerance)
            resp4 = await client.put(
                f"/api/instructor/instances/{iid}/grades/config",
                json={
                    "weight_financial": 0.25, "weight_customer": 0.25,
                    "weight_internal_process": 0.25, "weight_learning_growth": 0.25,
                },
                headers=headers,
            )
            assert resp4.status_code == 200

        await engine.dispose()
    asyncio.run(run())
