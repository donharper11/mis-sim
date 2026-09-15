"""Dashboard read projection tests: scope, persisted results, and runtime response rows."""

from __future__ import annotations

import asyncio

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api import dashboard, deps
from app.main import create_app
from app.models.base import Base
from app.models.platform import Course, Enrollment, Section, SimulationInstance, Team, User
from app.round.models import ArchNodeRow, DeploymentOrgStateRow, OrgUnitRow, RoundResult, SignalRow, TeamStateRow
from app.services.auth import create_access_token, hash_password


def test_dashboard_reads_persisted_team_state_and_hides_other_teams(tmp_path):
    async def run():
        engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'dashboard.db'}")
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            user = User(student_id="DASH", name="Dashboard Student", email="dash@example.test", role="student", password_hash=hash_password("pw"), is_active=True)
            instructor = User(name="Instructor", email="dash-instructor@example.test", role="instructor", password_hash=hash_password("pw"), is_active=True)
            session.add_all([user, instructor]); await session.flush()
            course = Course(course_code="DASH", course_name="Dashboard", academic_year="2026", semester="A", instructor_id=instructor.id)
            session.add(course); await session.flush()
            section = Section(course_id=course.id, section_code="A", section_name="Section A")
            other_section = Section(course_id=course.id, section_code="B", section_name="Section B")
            session.add_all([section, other_section]); await session.flush()
            instance = SimulationInstance(section_id=section.id, pack_key="pack", pack_version="1", current_round=2, total_rounds=6, status="active", settings={})
            other_instance = SimulationInstance(section_id=other_section.id, pack_key="pack", pack_version="1", current_round=2, total_rounds=6, status="active", settings={})
            session.add_all([instance, other_instance]); await session.flush()
            team = Team(section_id=section.id, instance_id=instance.instance_id, name="Team A")
            other_team = Team(section_id=section.id, instance_id=instance.instance_id, name="Team B")
            session.add_all([team, other_team]); await session.flush()
            session.add(Enrollment(user_id=user.id, section_id=section.id, team_id=team.id, role="student", is_active=True))
            session.add(TeamStateRow(instance_id=instance.instance_id, team_id=team.id, current_round=2, declared_strategy="balanced", declared_strategy_round=1, cash=46000, opex_runrate=58300, locked_round=None, advanced_round=1))
            session.add(ArchNodeRow(instance_id=instance.instance_id, team_id=team.id, round=1, key="order_system", roles_filled=[], availability=.9, installed_round=1, service_life_rounds=6, serves=["order_fulfilment"], throughput=None, owns_entities=[], placement="on_prem", opex_contribution=1000))
            session.add(DeploymentOrgStateRow(instance_id=instance.instance_id, team_id=team.id, round=1, key="order_system", catalog_key="order_system", org_unit="warehouse", people_affected=34, trained_count=0, process="unchanged", adoption=.22, ever_trained=False, serves=["outbound_logistics"], is_primary_for=None, initiated=True, abandoned=False))
            session.add(OrgUnitRow(instance_id=instance.instance_id, team_id=team.id, round=1, key="warehouse", headcount=34, resistance=.5))
            session.add(SignalRow(instance_id=instance.instance_id, team_id=team.id, key="order_capacity", episode_id=1, round=1, capability="order_fulfilment", metric="capacity", metric_kind="threshold", value=.9, severity="critical", status="open", first_shown_round=1, cleared_round=None, fire_round=None, cleared_by=[], was_actionable=True, cheapest_fix_when_raised=1000))
            session.add(RoundResult(instance_id=instance.instance_id, team_id=team.id, round=1, payload={"scorecard": {"financial": .61, "customer": .48, "internal_process": .39, "learning_growth": .27}, "signals": {"open": [{"key": "order_capacity", "capability": "order_fulfilment", "severity": "critical", "status": "open", "first_shown_round": 1}]}, "financials": {"opex_runrate": 58300}}))
            await session.commit()

            token = create_access_token(user_id=user.id, role="student", section_id=section.id, instance_id=instance.instance_id)
            async def get_session():
                yield session
            app = create_app()
            app.dependency_overrides[deps.get_session] = get_session
            app.dependency_overrides[dashboard.get_session] = get_session
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(f"/api/instances/{instance.instance_id}/dashboard", headers={"Authorization": f"Bearer {token}"})
                assert response.status_code == 200, response.text
                body = response.json()
                assert body["selected_team_id"] == team.id
                assert [item["name"] for item in body["teams"]] == ["Team A"]
                assert body["teams"][0]["scorecard"]["financial"] == .61
                assert body["teams"][0]["units"][0]["name"] == "warehouse"
                assert body["teams"][0]["open_signals"][0]["key"] == "order_capacity"
                forbidden = await client.get(f"/api/instances/{other_instance.instance_id}/dashboard", headers={"Authorization": f"Bearer {token}"})
                assert forbidden.status_code == 403
            app.dependency_overrides.clear()
        await engine.dispose()

    asyncio.run(run())
