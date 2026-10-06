"""Rollout workbench projects the persisted deployment state."""

from __future__ import annotations

import asyncio

from app.api import deps, runtime_rollout, runtime_host_platform, runtime_platform, runtime_persona
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
from app.round.models import ArchNodeRow, DeploymentOrgStateRow, TeamStateRow
from app.simulation.models import SimulationRunV1, SimulationSheetV1
from app.services.auth import create_access_token, hash_password
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def test_rollout_read_is_scoped_and_uninitialized_write_is_blocked(tmp_path):
    async def run():
        engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'rollout.db'}")
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            user = User(student_id="ROLL", name="Rollout Student", email="rollout@example.test", role="student", password_hash=hash_password("pw"), is_active=True)
            instructor = User(name="Instructor", email="rollout-instructor@example.test", role="instructor", password_hash=hash_password("pw"), is_active=True)
            session.add_all([user, instructor]); await session.flush()
            course = Course(course_code="ROLL", course_name="Rollout", academic_year="2026", semester="A", instructor_id=instructor.id)
            session.add(course); await session.flush()
            section = Section(course_id=course.id, section_code="A", section_name="Section A")
            session.add(section); await session.flush()
            instance = SimulationInstance(section_id=section.id, pack_key="pack", pack_version="1", current_round=2, total_rounds=6, status="active", settings={})
            session.add(instance); await session.flush()
            team = Team(section_id=section.id, instance_id=instance.instance_id, name="Team Rollout")
            session.add(team); await session.flush()
            session.add(Enrollment(user_id=user.id, section_id=section.id, team_id=team.id, role="student", is_active=True))
            session.add(TeamStateRow(instance_id=instance.instance_id, team_id=team.id, current_round=2, declared_strategy="balanced", declared_strategy_round=1, cash=46000, opex_runrate=58300))
            session.add(ArchNodeRow(instance_id=instance.instance_id, team_id=team.id, round=2, key="order_mgmt_v42", roles_filled=["order_app"], availability=.99, installed_round=1, service_life_rounds=6, serves=["order_fulfilment"], throughput=None, owns_entities=[], placement="on_prem", opex_contribution=2400))
            session.add(DeploymentOrgStateRow(instance_id=instance.instance_id, team_id=team.id, round=2, key="order_mgmt_v42", catalog_key="order_mgmt_v42", org_unit="store_operations", people_affected=140, trained_count=50, process="partial", adoption=.35, ever_trained=True, serves=["order_fulfilment"], is_primary_for="order_fulfilment", initiated=True, abandoned=False))
            await session.commit()

            token = create_access_token(user_id=user.id, role="student", section_id=section.id, instance_id=instance.instance_id)
            async def get_session():
                yield session
            app = create_app()
            app.dependency_overrides[deps.get_session] = get_session
            app.dependency_overrides[runtime_rollout.get_session] = get_session
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(f"/api/instances/{instance.instance_id}/rollout", headers={"Authorization": f"Bearer {token}"})
                assert response.status_code == 200, response.text
                body = response.json()
                assert body["team"]["name"] == "Team Rollout"
                assert body["team"]["deployments"][0]["trained_count"] == 50
                assert body["team"]["deployments"][0]["process"] == "partial"
                patch = await client.patch(f"/api/instances/{instance.instance_id}/rollout", json={"version": 1, "expected_revision": 0, "replace_categories": {"training": []}}, headers={"Authorization": f"Bearer {token}"})
                assert patch.status_code == 409
                headers = {"Authorization": f"Bearer {token}"}
                platforms_url = f"/api/instances/{instance.instance_id}/host-platforms"
                platform_input = {"platform_type": "on_prem", "name": "Test platform"}
                assert (await client.post(platforms_url, json=platform_input, headers=headers)).status_code == 409
                session.add(SimulationRunV1(instance_id=instance.instance_id, team_id=team.id, pack_key="pack", pack_version="1", pack_digest="test", current_round=2, advanced_round=1, status="draft"))
                await session.flush()
                sheet = SimulationSheetV1(instance_id=instance.instance_id, team_id=team.id, round=2, revision=0, commands=[])
                session.add(sheet)
                await session.commit()
                created = await client.post(platforms_url, json=platform_input, headers=headers)
                assert created.status_code == 200, created.text
                platform_id = created.json()["platforms"][0]["id"]
                member = await client.post(f"{platforms_url}/{platform_id}/members", json={"asset_key": "order_mgmt_v42", "member_kind": "component"}, headers=headers)
                assert member.status_code == 200, member.text
                member_id = member.json()["platforms"][0]["members"][0]["id"]
                sheet.locked_revision = 0
                await session.commit()
                assert (await client.post(platforms_url, json=platform_input, headers=headers)).status_code == 409
                assert (await client.patch(f"{platforms_url}/{platform_id}", json={"name": "Changed"}, headers=headers)).status_code == 409
                assert (await client.post(f"{platforms_url}/{platform_id}/members", json={"asset_key": "another", "member_kind": "component"}, headers=headers)).status_code == 409
                assert (await client.delete(f"{platforms_url}/{platform_id}/members/{member_id}", headers=headers)).status_code == 409
                # A student without a team cannot inherit the section's only team.
                enrollment = await session.scalar(select(Enrollment).where(Enrollment.user_id == user.id))
                enrollment.team_id = None
                await session.commit()
                assert await runtime_platform._team_for_user(session, instance, user, team.id) is None
                assert await runtime_host_platform._team_for_user(session, instance, user, team.id) is None
                assert await runtime_persona._team_for_user(session, instance, user, team.id) is None
                response = await client.get(f"/api/instances/{instance.instance_id}/rollout", headers={"Authorization": f"Bearer {token}"})
                assert response.status_code == 200
                assert response.json()["team"] is None
            app.dependency_overrides.clear()
        await engine.dispose()

    asyncio.run(run())


def test_rollout_metadata_uses_authored_costs_and_specific_asset_assignment():
    from pathlib import Path
    from app.simulation import load_runtime_pack

    pack = load_runtime_pack(Path(__file__).parents[1] / "packs" / "riverside_grocery")
    item = next(item for item in pack.casepack.catalog if any(mode.capex > 0 for mode in item.deployment_modes.values()))
    placement, mode = next((key, mode) for key, mode in item.deployment_modes.items() if mode.capex > 0)
    row = runtime_rollout._deployment(
        {"id": "specific_asset", "source_key": item.key, "placement": placement},
        pack, {}, {}, platform_map={
            item.key: {"platform_id": 1, "platform_code": "OP01", "platform_name": "Catalog default"},
            "specific_asset": {"platform_id": 2, "platform_code": "CL01", "platform_name": "Actual deployment"},
        },
    )
    assert row.capex == mode.capex > 0
    assert row.opex == mode.opex
    assert row.platform_id == 2
    assert row.platform_name == "Actual deployment"


def test_rollout_metadata_without_pack_remains_unassigned():
    row = runtime_rollout._deployment({"id": "legacy", "placement": "on_prem"}, None, {}, {})
    assert row.platform_id is None
    assert row.capex == row.opex == 0
