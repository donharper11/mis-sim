"""Scoped Platform decision surface over the versioned simulation runtime."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_instance, get_current_user, get_session
from app.casepack.registry import RegistryError, aresolve_runtime_pack
from app.models.platform import Enrollment, SimulationInstance, Team, User
from app.round.db import make_engine
from app.round.models import ArchEdgeRow, ArchNodeRow, PlatformServiceRow, TeamStateRow
from app.simulation.models import (
    SimulationCheckpointV1,
    SimulationRunV1,
    SimulationSheetV1,
)
from app.simulation.service import SimulationService
from app.simulation.types import SheetPatchV1, SimulationError

router = APIRouter(tags=["platform-runtime"])


class PlatformAssetOut(BaseModel):
    id: str
    label: str
    source_kind: str
    source_key: str
    placement: str
    config: str | None = None
    units: int = 1
    installed_round: int
    status: str
    capacity_pct: int | None = None
    utilisation_pct: float | None = None


class PlatformProjectOut(BaseModel):
    id: str
    label: str
    source_kind: str
    source_key: str
    placement: str
    status: str
    remaining_lead: int
    paid_capex: int


class PlatformConnectionOut(BaseModel):
    id: str
    src: str
    dst: str
    kind: str
    tier: str | None = None


class PlatformChoiceOut(BaseModel):
    key: str
    label: str
    placements: list[str] = Field(default_factory=list)


class PlatformTeamOut(BaseModel):
    id: int
    name: str
    current_round: int
    status: str
    strategy: str | None = None
    revision: int | None = None
    locked_revision: int | None = None
    assets: list[PlatformAssetOut] = Field(default_factory=list)
    projects: list[PlatformProjectOut] = Field(default_factory=list)
    connections: list[PlatformConnectionOut] = Field(default_factory=list)
    available_services: list[PlatformChoiceOut] = Field(default_factory=list)
    missing_services: list[PlatformChoiceOut] = Field(default_factory=list)
    split_rule: list[str] = Field(default_factory=list)


class PlatformOut(BaseModel):
    instance_id: int
    current_round: int
    total_rounds: int
    team: PlatformTeamOut | None = None


class PlatformPatchIn(BaseModel):
    version: int = 1
    expected_revision: int = Field(ge=0)
    commands: list[dict[str, Any]] = Field(default_factory=list)


def _label(pack: Any | None, key: str, *, service: bool = False) -> str:
    if pack is not None:
        labels = pack.casepack.labels
        if service:
            definition = next((item for item in pack.casepack.platform.services if item.key == key), None)
            if definition is not None:
                for role in definition.roles_filled:
                    if role in labels.roles:
                        return labels.roles[role]
        for family in ("catalog", "roles", "capabilities", "misc"):
            value = getattr(labels, family, {}).get(key)
            if value:
                return value
    return key.replace("_", " ").title()


def _placements(pack: Any | None, key: str, *, service: bool) -> list[str]:
    if pack is None:
        return []
    if service:
        definition = next((item for item in pack.casepack.platform.services if item.key == key), None)
    else:
        definition = next((item for item in pack.casepack.catalog if item.key == key), None)
    if definition is None:
        return []
    modes = definition.placement_options if service else definition.deployment_modes
    return [str(item.value) for item in modes]


async def _team_for_user(session: AsyncSession, instance: SimulationInstance, user: User, team_id: int | None) -> Team | None:
    if user.role == "student":
        selected = await session.scalar(select(Enrollment.team_id).where(
            Enrollment.user_id == user.id,
            Enrollment.section_id == instance.section_id,
            Enrollment.role == "student",
            Enrollment.is_active.is_(True),
        ))
        team_id = selected
    if team_id is None:
        candidates = list((await session.scalars(select(Team).where(
            Team.instance_id == instance.instance_id,
        ).order_by(Team.id))).all())
        if len(candidates) != 1:
            return None
        return candidates[0]
    return await session.scalar(select(Team).where(
        Team.instance_id == instance.instance_id, Team.id == team_id,
    ))


async def _runtime_pack(session: AsyncSession, instance: SimulationInstance):
    try:
        return await aresolve_runtime_pack(session, instance.pack_key, instance.pack_version)
    except RegistryError:
        return None


def _state_rows(team: Team, instance: SimulationInstance, state: Mapping[str, Any], pack: Any | None, service_rows: list[PlatformServiceRow] | None = None):
    service_index = {row.key: row for row in service_rows or []}
    assets: list[PlatformAssetOut] = []
    for raw in (state.get("assets", {}) if isinstance(state.get("assets"), Mapping) else {}).values():
        if not isinstance(raw, Mapping):
            continue
        source_key = str(raw.get("source_key", ""))
        row = service_index.get(source_key)
        definition = next((item for item in (pack.casepack.platform.services if pack is not None else []) if item.key == source_key), None)
        assets.append(PlatformAssetOut(
            id=str(raw.get("id", "")), label=_label(pack, source_key, service=raw.get("source_kind") == "service"),
            source_kind=str(raw.get("source_kind", "catalog")), source_key=source_key,
            placement=str(raw.get("placement", "")), config=raw.get("config"), units=int(raw.get("units", 1)),
            installed_round=int(raw.get("installed_round", 0)), status="retired" if raw.get("retired_round") is not None else "active",
            capacity_pct=int(row.capacity) if row is not None else (int(definition.capacity_pct) if definition is not None else None),
            utilisation_pct=float(row.utilisation * 100) if row is not None else None,
        ))
    projects: list[PlatformProjectOut] = []
    for raw in (state.get("projects", {}) if isinstance(state.get("projects"), Mapping) else {}).values():
        if isinstance(raw, Mapping):
            source_key = str(raw.get("source_key", ""))
            projects.append(PlatformProjectOut(
                id=str(raw.get("id", "")), label=_label(pack, source_key, service=raw.get("source_kind") == "service"),
                source_kind=str(raw.get("source_kind", "catalog")), source_key=source_key,
                placement=str(raw.get("placement", "")), status=str(raw.get("status", "pending")),
                remaining_lead=int(raw.get("remaining_lead", 0)), paid_capex=int(raw.get("paid_capex", 0)),
            ))
    connections: list[PlatformConnectionOut] = []
    for raw in (state.get("connections", {}) if isinstance(state.get("connections"), Mapping) else {}).values():
        if isinstance(raw, Mapping):
            connections.append(PlatformConnectionOut(
                id=str(raw.get("id", "")), src=str(raw.get("src", "")), dst=str(raw.get("dst", "")),
                kind=str(raw.get("kind", "network")), tier=raw.get("tier"),
            ))
    services = [PlatformChoiceOut(key=item.key, label=_label(pack, item.key, service=True), placements=_placements(pack, item.key, service=True)) for item in pack.casepack.platform.services] if pack is not None else []
    active_services = {item.source_key for item in assets if item.source_kind == "service" and item.status == "active"}
    return assets, projects, connections, services, [item for item in services if item.key not in active_services]


async def _read_team(session: AsyncSession, instance: SimulationInstance, team: Team, pack: Any | None) -> PlatformTeamOut:
    run = await session.get(SimulationRunV1, (instance.instance_id, team.id))
    if run is not None:
        checkpoint = await session.get(SimulationCheckpointV1, (instance.instance_id, team.id, run.advanced_round))
        state = checkpoint.state if checkpoint is not None and isinstance(checkpoint.state, Mapping) else {}
        sheet = await session.get(SimulationSheetV1, (instance.instance_id, team.id, run.current_round))
        service_rows = list((await session.scalars(select(PlatformServiceRow).where(
            PlatformServiceRow.instance_id == instance.instance_id,
            PlatformServiceRow.team_id == team.id,
            PlatformServiceRow.round == max(run.advanced_round, 1),
        ))).all())
        assets, projects, connections, services, missing = _state_rows(team, instance, state, pack, service_rows)
        return PlatformTeamOut(
            id=team.id, name=team.name, current_round=run.current_round, status=run.status,
            strategy=state.get("strategy"), revision=sheet.revision if sheet is not None else None,
            locked_revision=sheet.locked_revision if sheet is not None else None,
            assets=assets, projects=projects, connections=connections,
            available_services=services, missing_services=missing,
        )
    team_state = await session.get(TeamStateRow, (instance.instance_id, team.id))
    round_number = max((team_state.advanced_round if team_state and team_state.advanced_round else (team_state.current_round if team_state else instance.current_round)), 1)
    service_rows = list((await session.scalars(select(PlatformServiceRow).where(
        PlatformServiceRow.instance_id == instance.instance_id,
        PlatformServiceRow.team_id == team.id,
        PlatformServiceRow.round == round_number,
    ))).all())
    nodes = list((await session.scalars(select(ArchNodeRow).where(
        ArchNodeRow.instance_id == instance.instance_id,
        ArchNodeRow.team_id == team.id,
        ArchNodeRow.round == round_number,
    ))).all())
    edges = list((await session.scalars(select(ArchEdgeRow).where(
        ArchEdgeRow.instance_id == instance.instance_id,
        ArchEdgeRow.team_id == team.id,
        ArchEdgeRow.round == round_number,
    ))).all())
    state = {"assets": {
        row.key: {"id": row.key, "source_kind": "service" if row.key in {item.key for item in service_rows} else "catalog", "source_key": row.key, "placement": row.placement or "", "config": None, "units": 1, "installed_round": row.installed_round, "retired_round": None}
        for row in nodes
    }, "connections": {str(row.id): {"id": str(row.id), "src": row.src, "dst": row.dst, "kind": row.kind, "tier": None} for row in edges}}
    assets, projects, connections, services, missing = _state_rows(team, instance, state, pack, service_rows)
    return PlatformTeamOut(
        id=team.id, name=team.name, current_round=round_number,
        status="active" if team_state is not None else "uninitialized",
        strategy=team_state.declared_strategy if team_state is not None else None,
        assets=assets, projects=projects, connections=connections,
        available_services=services, missing_services=missing,
    )


@router.get("/instances/{instance_id}/platform", response_model=PlatformOut)
async def read_platform(
    instance: SimulationInstance = Depends(get_current_instance),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    team_id: int | None = Query(default=None),
):
    team = await _team_for_user(session, instance, current_user, team_id)
    pack = await _runtime_pack(session, instance)
    return PlatformOut(
        instance_id=instance.instance_id, current_round=max(instance.current_round, 1),
        total_rounds=instance.total_rounds,
        team=await _read_team(session, instance, team, pack) if team is not None else None,
    )


@router.patch("/instances/{instance_id}/platform", response_model=PlatformOut)
async def patch_platform(
    payload: PlatformPatchIn,
    instance: SimulationInstance = Depends(get_current_instance),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    team_id: int | None = Query(default=None),
):
    team = await _team_for_user(session, instance, current_user, team_id)
    if team is None:
        raise HTTPException(status_code=409, detail="Select a team before editing platform decisions")
    pack = await _runtime_pack(session, instance)
    if pack is None:
        raise HTTPException(status_code=409, detail="The registered runtime pack is unavailable")
    run = await session.get(SimulationRunV1, (instance.instance_id, team.id))
    if run is None:
        raise HTTPException(status_code=409, detail="The team runtime is not initialized")
    try:
        patch = SheetPatchV1.model_validate({"version": payload.version, "replace_categories": {"platform_service": payload.commands}})
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Platform commands are not valid for this round") from exc

    def apply_patch():
        engine = make_engine()
        try:
            return SimulationService(engine, pack).patch_sheet(instance.instance_id, team.id, run.current_round, payload.expected_revision, patch)
        finally:
            engine.dispose()

    try:
        await asyncio.to_thread(apply_patch)
    except SimulationError as exc:
        status = 409 if exc.code in {"revision_conflict", "locked", "round_state", "unaffordable", "not_found"} else 422
        raise HTTPException(status_code=status, detail={"code": exc.code, "field": exc.field}) from exc
    refreshed = await _read_team(session, instance, team, pack)
    return PlatformOut(instance_id=instance.instance_id, current_round=max(instance.current_round, 1), total_rounds=instance.total_rounds, team=refreshed)
