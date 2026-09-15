"""Scoped Rollout decision surface over the versioned simulation runtime."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, ValidationError
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
from app.simulation.types import CommandV1, SheetPatchV1, SimulationError

router = APIRouter(tags=["rollout-runtime"])


class RolloutOptionOut(BaseModel):
    key: str
    label: str
    cost: int = 0
    coverage: float | None = None


class RolloutDeploymentOut(BaseModel):
    id: str
    label: str
    org_unit: str | None = None
    people: int | None = None
    trained_count: int = 0
    training_pct: float = 0.0
    process: str = "unchanged"
    communication: str = "none"
    adoption: float = 0.0
    status: str
    training_options: list[RolloutOptionOut] = Field(default_factory=list)
    process_options: list[RolloutOptionOut] = Field(default_factory=list)
    communication_options: list[RolloutOptionOut] = Field(default_factory=list)


class RolloutTeamOut(BaseModel):
    id: int
    name: str
    current_round: int
    status: str
    revision: int | None = None
    locked_revision: int | None = None
    deployments: list[RolloutDeploymentOut] = Field(default_factory=list)


class RolloutOut(BaseModel):
    instance_id: int
    current_round: int
    total_rounds: int
    team: RolloutTeamOut | None = None


class RolloutPatchIn(BaseModel):
    version: int = 1
    expected_revision: int = Field(ge=0)
    replace_categories: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)


def _option_label(pack: Any | None, key: str) -> str:
    return _label(pack, key)


def _communication_options(pack: Any | None) -> list[RolloutOptionOut]:
    options = [RolloutOptionOut(key="none", label="No communication")]
    if pack is None:
        return options
    for key, option in pack.runtime.people.communication_options.items():
        options.append(RolloutOptionOut(key=key, label=key.replace("_", " ").title(), cost=int(option.cost)))
    return options


def _deployment(
    raw: Mapping[str, Any], pack: Any | None, rollout: Mapping[str, Any] | None,
    communications: Mapping[str, str], *, legacy: Any | None = None,
) -> RolloutDeploymentOut:
    source_key = str(raw.get("source_key", raw.get("catalog_key", raw.get("key", ""))))
    item = next((entry for entry in (pack.casepack.catalog if pack is not None else []) if entry.key == source_key), None)
    org_unit = item.people_affected.org_unit if item is not None else raw.get("org_unit")
    people = item.people_affected.count if item is not None else raw.get("people_affected", raw.get("people"))
    trained = int((rollout or {}).get("trained_count", raw.get("trained_count", 0)) or 0)
    adoption = float((rollout or {}).get("adoption", raw.get("adoption", 0.0)) or 0.0)
    process = str((rollout or {}).get("process", raw.get("process", "unchanged")))
    communication = communications.get(str(org_unit), str(raw.get("communication", "none")))
    training_options = [RolloutOptionOut(key=key, label=_option_label(pack, key), cost=int(option.cost), coverage=float(option.coverage)) for key, option in (item.training_options.items() if item is not None else [])]
    process_options = [RolloutOptionOut(key="unchanged", label="Keep current process", cost=0)]
    if item is not None and item.process_option is not None:
        process_options.extend([
            RolloutOptionOut(key="partial", label="Partly redesign process", cost=round(item.process_option.cost * pack.runtime.accounting.process_partial_fraction)),
            RolloutOptionOut(key="redesigned", label="Redesign process", cost=int(item.process_option.cost)),
        ])
    return RolloutDeploymentOut(
        id=str(raw.get("id", raw.get("key", ""))), label=_label(pack, source_key), org_unit=org_unit,
        people=people, trained_count=trained, training_pct=(trained / people if people else 0.0),
        process=process, communication=communication, adoption=adoption,
        status="needs-attention" if adoption < 0.5 else "partly-done" if adoption < 0.9 else "complete",
        training_options=training_options, process_options=process_options,
        communication_options=_communication_options(pack),
    )


def _communication_from_sheet(sheet: SimulationSheetV1 | None) -> dict[str, str]:
    if sheet is None or not isinstance(sheet.commands, list):
        return {}
    result: dict[str, str] = {}
    for raw in sheet.commands:
        try:
            command = CommandV1.model_validate(raw)
        except ValidationError:
            continue
        if command.op == "communicate" and command.org_unit and command.option:
            result[command.org_unit] = command.option
    return result


async def _read_team(session: AsyncSession, instance: SimulationInstance, team: Team, pack: Any | None) -> RolloutTeamOut:
    run = await session.get(SimulationRunV1, (instance.instance_id, team.id))
    if run is not None:
        checkpoint = await session.get(SimulationCheckpointV1, (instance.instance_id, team.id, run.advanced_round))
        state = checkpoint.state if checkpoint is not None and isinstance(checkpoint.state, Mapping) else {}
        sheet = await session.get(SimulationSheetV1, (instance.instance_id, team.id, run.current_round))
        rollouts = state.get("rollouts", {}) if isinstance(state.get("rollouts"), Mapping) else {}
        assets = state.get("assets", {}) if isinstance(state.get("assets"), Mapping) else {}
        communications = _communication_from_sheet(sheet)
        deployments = [_deployment(raw, pack, rollouts.get(asset_id), communications) for asset_id, raw in assets.items() if isinstance(raw, Mapping) and raw.get("source_kind") == "catalog" and asset_id in rollouts]
        return RolloutTeamOut(id=team.id, name=team.name, current_round=run.current_round, status=run.status, revision=sheet.revision if sheet is not None else None, locked_revision=sheet.locked_revision if sheet is not None else None, deployments=deployments)

    team_state = await session.get(TeamStateRow, (instance.instance_id, team.id))
    round_number = max((team_state.advanced_round if team_state and team_state.advanced_round else (team_state.current_round if team_state else instance.current_round)), 1)
    nodes = list((await session.scalars(select(ArchNodeRow).where(ArchNodeRow.instance_id == instance.instance_id, ArchNodeRow.team_id == team.id, ArchNodeRow.round == round_number))).all())
    legacy_rows = {row.key: row for row in (await session.scalars(select(DeploymentOrgStateRow).where(DeploymentOrgStateRow.instance_id == instance.instance_id, DeploymentOrgStateRow.team_id == team.id, DeploymentOrgStateRow.round == round_number))).all()}
    deployments = []
    for node in nodes:
        row = legacy_rows.get(node.key)
        raw = {"id": node.key, "source_key": row.catalog_key if row is not None else node.key, "key": node.key, "org_unit": row.org_unit if row is not None else None, "people_affected": row.people_affected if row is not None else None, "trained_count": row.trained_count if row is not None else 0, "process": row.process if row is not None else "unchanged", "adoption": row.adoption if row is not None else 0.0}
        if pack is None or any(item.key == raw["source_key"] for item in pack.casepack.catalog):
            deployments.append(_deployment(raw, pack, raw, {} , legacy=row))
    return RolloutTeamOut(id=team.id, name=team.name, current_round=round_number, status="active" if team_state is not None else "uninitialized", deployments=deployments)


@router.get("/instances/{instance_id}/rollout", response_model=RolloutOut)
async def read_rollout(instance: SimulationInstance = Depends(get_current_instance), current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session), team_id: int | None = Query(default=None)):
    team = await _team_for_user(session, instance, current_user, team_id)
    pack = await _runtime_pack(session, instance)
    return RolloutOut(instance_id=instance.instance_id, current_round=max(instance.current_round, 1), total_rounds=instance.total_rounds, team=await _read_team(session, instance, team, pack) if team is not None else None)


@router.patch("/instances/{instance_id}/rollout", response_model=RolloutOut)
async def patch_rollout(payload: RolloutPatchIn, instance: SimulationInstance = Depends(get_current_instance), current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session), team_id: int | None = Query(default=None)):
    team = await _team_for_user(session, instance, current_user, team_id)
    if team is None:
        raise HTTPException(status_code=409, detail="Select a team before editing rollout decisions")
    pack = await _runtime_pack(session, instance)
    if pack is None:
        raise HTTPException(status_code=409, detail="The registered runtime pack is unavailable")
    run = await session.get(SimulationRunV1, (instance.instance_id, team.id))
    if run is None:
        raise HTTPException(status_code=409, detail="The team runtime is not initialized")
    if set(payload.replace_categories) - {"training", "process_redesign", "communication"}:
        raise HTTPException(status_code=422, detail="Rollout accepts training, process, and communication commands only")
    try:
        patch = SheetPatchV1.model_validate({"version": payload.version, "replace_categories": payload.replace_categories})
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Rollout commands are not valid for this round") from exc

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
    return RolloutOut(instance_id=instance.instance_id, current_round=max(instance.current_round, 1), total_rounds=instance.total_rounds, team=await _read_team(session, instance, team, pack))
