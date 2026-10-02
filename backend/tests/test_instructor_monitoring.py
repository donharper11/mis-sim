"""M5.4 instructor monitoring dashboard API contract tests.

Covers: auth boundary, aggregate accuracy, round progression, attention alerts,
cross-section isolation, and empty-state projection.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api import deps, instructor, platform
from app.main import create_app
from app.models.base import Base
from app.models.platform import Casepack, Course, Enrollment, Section, SimulationInstance, Team, User
from app.round.models import RoundResult, SignalRow, TeamStateRow
from app.services.auth import create_access_token, hash_password
from app.simulation.content import load_runtime_pack
from app.simulation.models import SimulationRunV1, SimulationCheckpointV1

PACK = Path(__file__).resolve().parents[1] / "packs" / "riverside_grocery"


def _token(user: User) -> str:
    return create_access_token(user_id=user.id, role=user.role)


def _headers(user: User) -> dict:
    return {"Authorization": f"Bearer {_token(user)}"}


async def _fixture(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'monitoring.db'}")
    tables = [
        User.__table__, Course.__table__, Section.__table__,
        SimulationInstance.__table__, Team.__table__, Enrollment.__table__,
        Casepack.__table__, RoundResult.__table__, SignalRow.__table__,
        TeamStateRow.__table__, SimulationRunV1.__table__,
        SimulationCheckpointV1.__table__,
    ]
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=tables)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        owner = User(name="Owner", email="owner@mon.test", role="instructor", password_hash=hash_password("pw"))
        other = User(name="Other", email="other@mon.test", role="instructor", password_hash=hash_password("pw"))
        admin = User(name="Admin", email="admin@mon.test", role="admin", password_hash=hash_password("pw"))
        student = User(student_id="S1", name="Student", email="student@mon.test", role="student", password_hash=hash_password("pw"))
        session.add_all([owner, other, admin, student])
        await session.flush()

        course = Course(course_code="MON", course_name="Monitoring", academic_year="2026", semester="A", instructor_id=owner.id)
        other_course = Course(course_code="OTH", course_name="Other", academic_year="2026", semester="A", instructor_id=other.id)
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
            pack_digest=runtime.pack_digest, total_rounds=6, status="active", current_round=3,
        )
        session.add(instance)
        await session.flush()

        team_a = Team(section_id=section.id, instance_id=instance.instance_id, name="Team A")
        team_b = Team(section_id=section.id, instance_id=instance.instance_id, name="Team B")
        team_c = Team(section_id=section.id, instance_id=instance.instance_id, name="Team C")
        session.add_all([team_a, team_b, team_c])
        await session.flush()

        enrollment = Enrollment(section_id=section.id, user_id=student.id, team_id=team_a.id, role="student")
        session.add(enrollment)

        # Other course instance for cross-section isolation
        other_instance = SimulationInstance(
            section_id=other_section.id, pack_key=metadata.pack_key, pack_version=metadata.pack_version,
            pack_digest=runtime.pack_digest, total_rounds=6, status="active", current_round=2,
        )
        session.add(other_instance)
        await session.flush()

        other_team = Team(section_id=other_section.id, instance_id=other_instance.instance_id, name="Other Team")
        session.add(other_team)
        await session.commit()

        values = {
            "owner": owner, "other": other, "admin": admin, "student": student,
            "course": course, "other_course": other_course,
            "section": section, "other_section": other_section,
            "instance": instance, "other_instance": other_instance,
            "team_a": team_a, "team_b": team_b, "team_c": team_c,
            "other_team": other_team, "runtime": runtime,
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
# AC-1: Auth — instructor sees all teams; student gets 403
# ---------------------------------------------------------------------------

def test_auth_instructor_sees_teams_student_gets_403(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        iid = data["instance"].instance_id
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Instructor can read monitoring
            resp = await client.get(f"/api/instructor/instances/{iid}/monitoring", headers=_headers(data["owner"]))
            assert resp.status_code == 200
            body = resp.json()
            assert body["instance_id"] == iid
            assert len(body["teams"]) == 3  # Team A, B, C

            # Student gets 403
            resp2 = await client.get(f"/api/instructor/instances/{iid}/monitoring", headers=_headers(data["student"]))
            assert resp2.status_code == 403

            # Admin can also read
            resp3 = await client.get(f"/api/instructor/instances/{iid}/monitoring", headers=_headers(data["admin"]))
            assert resp3.status_code == 200
        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# AC-2: Aggregate accuracy — average scorecard matches manual calculation
# ---------------------------------------------------------------------------

def test_aggregate_scorecard_accuracy(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        iid = data["instance"].instance_id

        # Seed round results with known scorecards for teams A and B
        async with factory() as session:
            session.add(RoundResult(
                instance_id=iid, team_id=data["team_a"].id, round=2,
                payload={
                    "scorecard": {"financial": 0.80, "customer": 0.60, "internal_process": 0.50, "learning_growth": 0.70},
                    "signals": {"open": []},
                },
            ))
            session.add(RoundResult(
                instance_id=iid, team_id=data["team_b"].id, round=2,
                payload={
                    "scorecard": {"financial": 0.60, "customer": 0.80, "internal_process": 0.40, "learning_growth": 0.50},
                    "signals": {"open": []},
                },
            ))
            # Team C has no results
            await session.commit()

        app = _app(factory)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/instructor/instances/{iid}/monitoring", headers=_headers(data["owner"]))
            assert resp.status_code == 200
            body = resp.json()
            avg = body["summary"]["average_scorecard"]

            # Manual calculation: (0.80+0.60)/2=0.70, (0.60+0.80)/2=0.70, (0.50+0.40)/2=0.45, (0.70+0.50)/2=0.60
            assert abs(avg["financial"] - 0.70) < 0.01
            assert abs(avg["customer"] - 0.70) < 0.01
            assert abs(avg["internal_process"] - 0.45) < 0.01
            assert abs(avg["learning_growth"] - 0.60) < 0.01

            # Verify individual team scorecards are present
            team_a_data = next(t for t in body["teams"] if t["team_id"] == data["team_a"].id)
            assert team_a_data["scorecard"]["financial"] == 0.80
            assert team_a_data["scorecard"]["customer"] == 0.60
        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# AC-3: Round progression — team with 3 completed rounds returns scorecard for 1-3
# ---------------------------------------------------------------------------

def test_round_progression(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        iid = data["instance"].instance_id

        # Seed 3 rounds of results for team A
        async with factory() as session:
            for r in range(1, 4):
                session.add(RoundResult(
                    instance_id=iid, team_id=data["team_a"].id, round=r,
                    payload={
                        "scorecard": {
                            "financial": 0.50 + r * 0.10,
                            "customer": 0.40 + r * 0.10,
                            "internal_process": 0.30 + r * 0.10,
                            "learning_growth": 0.35 + r * 0.10,
                        },
                    },
                ))
            await session.commit()

        app = _app(factory)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                f"/api/instructor/instances/{iid}/monitoring/progression",
                params={"team_ids": str(data["team_a"].id)},
                headers=_headers(data["owner"]),
            )
            assert resp.status_code == 200
            body = resp.json()
            assert len(body["teams"]) == 1
            team_data = body["teams"][0]
            assert team_data["team_id"] == data["team_a"].id
            assert len(team_data["rounds"]) == 3

            # Verify round ordering and values
            assert team_data["rounds"][0]["round"] == 1
            assert abs(team_data["rounds"][0]["scorecard"]["financial"] - 0.60) < 0.01
            assert team_data["rounds"][1]["round"] == 2
            assert abs(team_data["rounds"][1]["scorecard"]["financial"] - 0.70) < 0.01
            assert team_data["rounds"][2]["round"] == 3
            assert abs(team_data["rounds"][2]["scorecard"]["financial"] - 0.80) < 0.01
        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# AC-4: Attention alerts — zero capital and behind-round teams appear
# ---------------------------------------------------------------------------

def test_attention_alerts(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        iid = data["instance"].instance_id

        # Team A: zero capital via SimulationRunV1 + checkpoint
        # Team B: behind round (current_round < instance.current_round=3)
        # Team C: critical signal
        async with factory() as session:
            # Team A: zero capital
            session.add(SimulationRunV1(
                instance_id=iid, team_id=data["team_a"].id,
                pack_key="riverside_grocery", pack_version="0.1.0",
                pack_digest=data["runtime"].pack_digest,
                current_round=3, advanced_round=2, status="draft",
            ))
            session.add(SimulationCheckpointV1(
                instance_id=iid, team_id=data["team_a"].id, round=2,
                version=1, pack_digest=data["runtime"].pack_digest,
                state={"capital_balance": 0, "signal_ledger": []},
                state_digest="abc123",
            ))

            # Team B: behind round (current_round=2 < instance=3)
            session.add(SimulationRunV1(
                instance_id=iid, team_id=data["team_b"].id,
                pack_key="riverside_grocery", pack_version="0.1.0",
                pack_digest=data["runtime"].pack_digest,
                current_round=2, advanced_round=1, status="draft",
            ))
            session.add(SimulationCheckpointV1(
                instance_id=iid, team_id=data["team_b"].id, round=1,
                version=1, pack_digest=data["runtime"].pack_digest,
                state={"capital_balance": 500000, "signal_ledger": []},
                state_digest="def456",
            ))

            # Team C: critical signal
            session.add(SimulationRunV1(
                instance_id=iid, team_id=data["team_c"].id,
                pack_key="riverside_grocery", pack_version="0.1.0",
                pack_digest=data["runtime"].pack_digest,
                current_round=3, advanced_round=2, status="draft",
            ))
            session.add(SimulationCheckpointV1(
                instance_id=iid, team_id=data["team_c"].id, round=2,
                version=1, pack_digest=data["runtime"].pack_digest,
                state={
                    "capital_balance": 300000,
                    "signal_ledger": [
                        {"key": "crit_sig", "status": "open", "severity": "critical", "capability": "security"},
                    ],
                },
                state_digest="ghi789",
            ))
            await session.commit()

        app = _app(factory)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/instructor/instances/{iid}/monitoring", headers=_headers(data["owner"]))
            assert resp.status_code == 200
            body = resp.json()

            attention = body["attention"]
            attention_map = {(a["team_id"], a["reason"]) for a in attention}

            # Team A should have zero_capital
            assert (data["team_a"].id, "zero_capital") in attention_map
            # Team B should have behind_round
            assert (data["team_b"].id, "behind_round") in attention_map
            # Team C should have critical_signals
            assert (data["team_c"].id, "critical_signals") in attention_map
        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# AC-5: Cross-section isolation — instructor for course A can't read course B
# ---------------------------------------------------------------------------

def test_cross_section_isolation(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        other_iid = data["other_instance"].instance_id
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Owner of course A cannot read course B's instance monitoring
            resp = await client.get(
                f"/api/instructor/instances/{other_iid}/monitoring",
                headers=_headers(data["owner"]),
            )
            assert resp.status_code == 403

            # Other instructor (course B) can read their own
            resp2 = await client.get(
                f"/api/instructor/instances/{other_iid}/monitoring",
                headers=_headers(data["other"]),
            )
            assert resp2.status_code == 200

            # Progression is also isolated
            resp3 = await client.get(
                f"/api/instructor/instances/{other_iid}/monitoring/progression",
                headers=_headers(data["owner"]),
            )
            assert resp3.status_code == 403
        await engine.dispose()
    asyncio.run(run())


# ---------------------------------------------------------------------------
# AC-6: Empty state — fresh instance returns null scorecards and empty progression
# ---------------------------------------------------------------------------

def test_empty_state(tmp_path):
    async def run():
        engine, factory, data = await _fixture(tmp_path)
        app = _app(factory)
        iid = data["instance"].instance_id
        # No round results or simulation runs seeded — pure empty state
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/api/instructor/instances/{iid}/monitoring", headers=_headers(data["owner"]))
            assert resp.status_code == 200
            body = resp.json()

            # All teams should have null scorecards
            for team in body["teams"]:
                assert team["scorecard"] is None

            # Average scorecard should be all null
            avg = body["summary"]["average_scorecard"]
            assert avg["financial"] is None
            assert avg["customer"] is None

            # Progression should be empty
            resp2 = await client.get(
                f"/api/instructor/instances/{iid}/monitoring/progression",
                params={"team_ids": str(data["team_a"].id)},
                headers=_headers(data["owner"]),
            )
            assert resp2.status_code == 200
            body2 = resp2.json()
            assert len(body2["teams"]) == 1
            assert len(body2["teams"][0]["rounds"]) == 0
        await engine.dispose()
    asyncio.run(run())
