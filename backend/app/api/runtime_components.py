"""Scoped Components workbench over the versioned simulation runtime."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_instance, get_current_user, get_session
from app.api.runtime_platform import _label, _runtime_pack, _team_for_user
from app.models.platform import SimulationInstance, Team, User
from app.round.db import make_engine
from app.round.models import ArchNodeRow, DeploymentOrgStateRow, TeamStateRow
from app.simulation.models import (
    SimulationCheckpointV1,
    SimulationRunV1,
    SimulationSheetV1,
)
from app.simulation.service import SimulationService
from app.simulation.types import SheetPatchV1, SimulationError

router = APIRouter(tags=["components-runtime"])


class ComponentPlacementOut(BaseModel):
    key: str
    label: str
    capex: int
    opex: int
    lead_time: int
    bypasses_platform: bool = False


class ComponentConfigOut(BaseModel):
    key: str
    label: str


class ComponentChoiceOut(BaseModel):
    key: str
    label: str
    category: str = "application"
    serves: list[str] = Field(default_factory=list)
    org_unit: str | None = None
    people: int | None = None
    placements: list[ComponentPlacementOut] = Field(default_factory=list)
    configs: list[ComponentConfigOut] = Field(default_factory=list)
    true_cost_categories: list[str] = Field(default_factory=list)
    decoy_cost_categories: list[str] = Field(default_factory=list)


class ComponentAssetOut(BaseModel):
    id: str
    label: str
    source_key: str
    placement: str
    config: str | None = None
    units: int = 1
    installed_round: int
    status: str
    serves: list[str] = Field(default_factory=list)
    org_unit: str | None = None
    people: int | None = None
    trained_count: int | None = None
    adoption: float | None = None
    process: str | None = None
    lifecycle: str | None = None


class ComponentProjectOut(BaseModel):
    id: str
    label: str
    source_key: str
    placement: str
    config: str | None = None
    status: str
    remaining_lead: int
    paid_capex: int


class ComponentsTeamOut(BaseModel):
    id: int
    name: str
    current_round: int
    status: str
    strategy: str | None = None
    revision: int | None = None
    locked_revision: int | None = None
    assets: list[ComponentAssetOut] = Field(default_factory=list)
    projects: list[ComponentProjectOut] = Field(default_factory=list)
    choices: list[ComponentChoiceOut] = Field(default_factory=list)


class ComponentsOut(BaseModel):
    instance_id: int
    current_round: int
    total_rounds: int
    team: ComponentsTeamOut | None = None


class ComponentsPatchIn(BaseModel):
    version: int = 1
    expected_revision: int = Field(ge=0)
    replace_categories: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)


def _catalog_choice(pack: Any, item: Any) -> ComponentChoiceOut:
    labels = pack.casepack.labels
    return ComponentChoiceOut(
        key=item.key,
        label=_label(pack, item.key),
        serves=[labels.capabilities.get(key, key.replace("_", " ").title()) for key in item.serves],
        org_unit=labels.misc.get(item.people_affected.org_unit, item.people_affected.org_unit.replace("_", " ").title()),
        people=item.people_affected.count,
        placements=[ComponentPlacementOut(
            key=str(key.value), label=str(key.value).replace("_", " ").title(),
            capex=mode.capex, opex=mode.opex, lead_time=mode.lead_time_rounds,
            bypasses_platform=mode.bypasses_platform,
        ) for key, mode in item.deployment_modes.items()],
        configs=[ComponentConfigOut(key=key, label=key.replace("_", " ").title()) for key in item.config_tiers],
        true_cost_categories=list(item.true_cost_categories),
        decoy_cost_categories=list(item.decoy_cost_categories),
    )


def _asset_from(raw: Mapping[str, Any], pack: Any | None, rollout: Mapping[str, Any] | None, *, legacy: Any | None = None) -> ComponentAssetOut:
    source_key = str(raw.get("source_key", raw.get("key", "")))
    item = next((entry for entry in (pack.casepack.catalog if pack is not None else []) if entry.key == source_key), None)
    serves = [str(value) for value in (item.serves if item is not None else raw.get("serves", []) or [])]
    labels = pack.casepack.labels if pack is not None else None
    serves = [labels.capabilities.get(value, value.replace("_", " ").title()) if labels is not None else value.replace("_", " ").title() for value in serves]
    org_unit = item.people_affected.org_unit if item is not None else raw.get("org_unit")
    people = item.people_affected.count if item is not None else raw.get("people")
    return ComponentAssetOut(
        id=str(raw.get("id", raw.get("key", ""))), label=_label(pack, source_key), source_key=source_key,
        placement=str(raw.get("placement", "")), config=raw.get("config"), units=int(raw.get("units", 1)),
        installed_round=int(raw.get("installed_round", 0)),
        status="retired" if raw.get("retired_round") is not None or (legacy is not None and getattr(legacy, "abandoned", False)) else "active",
        serves=serves, org_unit=org_unit, people=people,
        trained_count=(rollout or {}).get("trained_count", raw.get("trained_count")),
        adoption=(rollout or {}).get("adoption", raw.get("adoption")),
        process=(rollout or {}).get("process", raw.get("process")),
        lifecycle=(rollout or {}).get("lifecycle"),
    )


async def _read_team(session: AsyncSession, instance: SimulationInstance, team: Team, pack: Any | None) -> ComponentsTeamOut:
    choices = [_catalog_choice(pack, item) for item in pack.casepack.catalog] if pack is not None else []
    run = await session.get(SimulationRunV1, (instance.instance_id, team.id))
    if run is not None:
        checkpoint = await session.get(SimulationCheckpointV1, (instance.instance_id, team.id, run.advanced_round))
        state = checkpoint.state if checkpoint is not None and isinstance(checkpoint.state, Mapping) else {}
        sheet = await session.get(SimulationSheetV1, (instance.instance_id, team.id, run.current_round))
        rollouts = state.get("rollouts", {}) if isinstance(state.get("rollouts"), Mapping) else {}
        assets = [_asset_from(raw, pack, rollouts.get(key)) for key, raw in (state.get("assets", {}) if isinstance(state.get("assets"), Mapping) else {}).items() if isinstance(raw, Mapping) and raw.get("source_kind") == "catalog"]
        projects = [ComponentProjectOut(id=str(raw.get("id", "")), label=_label(pack, str(raw.get("source_key", ""))), source_key=str(raw.get("source_key", "")), placement=str(raw.get("placement", "")), config=raw.get("config"), status=str(raw.get("status", "pending")), remaining_lead=int(raw.get("remaining_lead", 0)), paid_capex=int(raw.get("paid_capex", 0))) for raw in (state.get("projects", {}) if isinstance(state.get("projects"), Mapping) else {}).values() if isinstance(raw, Mapping) and raw.get("source_kind") == "catalog"]
        return ComponentsTeamOut(id=team.id, name=team.name, current_round=run.current_round, status=run.status, strategy=state.get("strategy"), revision=sheet.revision if sheet is not None else None, locked_revision=sheet.locked_revision if sheet is not None else None, assets=assets, projects=projects, choices=choices)

    team_state = await session.get(TeamStateRow, (instance.instance_id, team.id))
    round_number = max((team_state.advanced_round if team_state and team_state.advanced_round else (team_state.current_round if team_state else instance.current_round)), 1)
    nodes = list((await session.scalars(select(ArchNodeRow).where(ArchNodeRow.instance_id == instance.instance_id, ArchNodeRow.team_id == team.id, ArchNodeRow.round == round_number))).all())
    deployments = {row.key: row for row in (await session.scalars(select(DeploymentOrgStateRow).where(DeploymentOrgStateRow.instance_id == instance.instance_id, DeploymentOrgStateRow.team_id == team.id, DeploymentOrgStateRow.round == round_number))).all()}
    catalog_keys = {item.key for item in (pack.casepack.catalog if pack is not None else [])}
    assets = [_asset_from({"id": node.key, "source_key": deployments.get(node.key, node).catalog_key if node.key in deployments else node.key, "placement": node.placement or "", "units": 1, "installed_round": node.installed_round, "serves": node.serves}, pack, deployments.get(node.key).__dict__ if node.key in deployments else None, legacy=deployments.get(node.key)) for node in nodes if pack is None or (deployments.get(node.key).catalog_key if node.key in deployments else node.key) in catalog_keys]
    return ComponentsTeamOut(id=team.id, name=team.name, current_round=round_number, status="active" if team_state is not None else "uninitialized", strategy=team_state.declared_strategy if team_state is not None else None, assets=assets, choices=choices)


@router.get("/instances/{instance_id}/components", response_model=ComponentsOut)
async def read_components(instance: SimulationInstance = Depends(get_current_instance), current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session), team_id: int | None = Query(default=None)):  # noqa: B008
    team = await _team_for_user(session, instance, current_user, team_id)
    pack = await _runtime_pack(session, instance)
    return ComponentsOut(instance_id=instance.instance_id, current_round=max(instance.current_round, 1), total_rounds=instance.total_rounds, team=await _read_team(session, instance, team, pack) if team is not None else None)


@router.patch("/instances/{instance_id}/components", response_model=ComponentsOut)
async def patch_components(payload: ComponentsPatchIn, instance: SimulationInstance = Depends(get_current_instance), current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session), team_id: int | None = Query(default=None)):  # noqa: B008
    team = await _team_for_user(session, instance, current_user, team_id)
    if team is None:
        raise HTTPException(status_code=409, detail="Select a team before editing component decisions")
    pack = await _runtime_pack(session, instance)
    if pack is None:
        raise HTTPException(status_code=409, detail="The registered runtime pack is unavailable")
    run = await session.get(SimulationRunV1, (instance.instance_id, team.id))
    if run is None:
        raise HTTPException(status_code=409, detail="The team runtime is not initialized")
    if set(payload.replace_categories) - {"application", "lifecycle"}:
        raise HTTPException(status_code=422, detail="Components accepts application and lifecycle commands only")
    try:
        patch = SheetPatchV1.model_validate({"version": payload.version, "replace_categories": payload.replace_categories})
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Component commands are not valid for this round") from exc

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
    return ComponentsOut(instance_id=instance.instance_id, current_round=max(instance.current_round, 1), total_rounds=instance.total_rounds, team=await _read_team(session, instance, team, pack))
