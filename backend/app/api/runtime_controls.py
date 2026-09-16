"""Minimum Phase 4 decision controls over the versioned simulation sheet.

The first-playable gate needs the six decision families to be reachable from the
student shell.  This module is deliberately a projection and command adapter: all
prices, validation, state changes, and scoring remain owned by ``SimulationService``.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_instance, get_current_user, get_session
from app.api.runtime_platform import _label, _runtime_pack, _team_for_user
from app.models.platform import SimulationInstance, Team, User
from app.round.db import make_engine
from app.simulation.models import (
    SimulationCheckpointV1,
    SimulationRunV1,
    SimulationSheetV1,
)
from app.simulation.service import SimulationService
from app.simulation.types import SheetPatchV1, SimulationError

router = APIRouter(tags=["controls-runtime"])


class OptionOut(BaseModel):
    key: str
    label: str
    detail: str | None = None
    values: list[str] = Field(default_factory=list)


class GovernanceOut(BaseModel):
    capability: str
    label: str
    owner: str | None = None
    sponsor: str | None = None
    primary: str | None = None


class PolicyOut(BaseModel):
    key: str
    label: str
    selected: str
    options: list[str] = Field(default_factory=list)


class ChallengeOptionOut(BaseModel):
    key: str
    label: str
    cost: int = 0
    rationale_tags: list[str] = Field(default_factory=list)


class ChallengeOut(BaseModel):
    key: str
    label: str
    status: str
    options: list[ChallengeOptionOut] = Field(default_factory=list)


class ControlsTeamOut(BaseModel):
    id: int
    name: str
    current_round: int
    status: str
    revision: int | None = None
    locked_revision: int | None = None
    strategy: str | None = None
    governance: list[GovernanceOut] = Field(default_factory=list)
    policies: list[PolicyOut] = Field(default_factory=list)
    selected_commands: list[dict[str, Any]] = Field(default_factory=list)


class ControlsOut(BaseModel):
    instance_id: int
    current_round: int
    total_rounds: int
    strategies: list[OptionOut] = Field(default_factory=list)
    governance: list[GovernanceOut] = Field(default_factory=list)
    security_components: list[OptionOut] = Field(default_factory=list)
    policies: list[PolicyOut] = Field(default_factory=list)
    services: list[OptionOut] = Field(default_factory=list)
    people_units: list[OptionOut] = Field(default_factory=list)
    hiring_options: list[OptionOut] = Field(default_factory=list)
    communication_options: list[OptionOut] = Field(default_factory=list)
    challenges: list[ChallengeOut] = Field(default_factory=list)
    capital_balance: int | None = None
    capital_request_max_amount: int | None = None
    capital_request_min_reason_length: int | None = None
    capital_request_approval_rounds: list[int] = Field(default_factory=list)
    team: ControlsTeamOut | None = None


class ControlsPatchIn(BaseModel):
    version: int = 1
    expected_revision: int = Field(ge=0)
    commands: list[dict[str, Any]] = Field(default_factory=list)


_SECTIONS = {
    "strategy": {"governance"},
    "governance": {"governance"},
    "security": {"application", "policy"},
    "services": {"platform_service"},
    "people": {"staffing", "communication"},
    "challenges": {"event_response"},
    "budget": {"capital_request"},
}


def _option(key: str, label: str | None = None, detail: str | None = None, values: list[str] | None = None) -> OptionOut:
    return OptionOut(key=key, label=label or key.replace("_", " ").title(), detail=detail, values=values or [])


def _state_and_sheet(session, instance: SimulationInstance, team: Team):
    """Return the latest checkpoint and editable sheet for a modern runtime."""
    run = session.get(SimulationRunV1, (instance.instance_id, team.id))
    if run is None:
        return None, None, None
    checkpoint = session.get(SimulationCheckpointV1, (instance.instance_id, team.id, run.advanced_round))
    sheet = session.get(SimulationSheetV1, (instance.instance_id, team.id, run.current_round))
    state = checkpoint.state if checkpoint is not None and isinstance(checkpoint.state, Mapping) else {}
    return run, state, sheet


def _governance(pack: Any, state: Mapping[str, Any]) -> list[GovernanceOut]:
    current = state.get("governance", {}) if isinstance(state.get("governance"), Mapping) else {}
    primary = state.get("primary", {}) if isinstance(state.get("primary"), Mapping) else {}
    rows: list[GovernanceOut] = []
    for item in pack.casepack.capabilities:
        value = current.get(item.key, {})
        if not isinstance(value, Mapping):
            value = {}
        rows.append(GovernanceOut(
            capability=item.key, label=_label(pack, item.key), owner=value.get("owner"),
            sponsor=value.get("sponsor"), primary=primary.get(item.key),
        ))
    return rows


def _policies(pack: Any, state: Mapping[str, Any]) -> list[PolicyOut]:
    current = state.get("policies", {}) if isinstance(state.get("policies"), Mapping) else {}
    return [PolicyOut(
        key=item.key, label=_label(pack, item.key),
        selected=str((current.get(item.key) or {}).get("selected", item.default)),
        options=list(item.options),
    ) for item in pack.casepack.policies]


def _sheet_commands(sheet: SimulationSheetV1 | None) -> list[dict[str, Any]]:
    return list(sheet.commands) if sheet is not None and isinstance(sheet.commands, list) else []


async def _read_controls(session: AsyncSession, instance: SimulationInstance, team: Team | None, pack: Any | None) -> ControlsOut:
    if pack is None:
        raise HTTPException(status_code=409, detail="The registered runtime pack is unavailable")
    strategies = [_option(item.key, item.key.replace("_", " ").title(), values=list(item.capability_weights)) for item in pack.casepack.strategies]
    services = [_option(item.key, _label(pack, item.key, service=True), values=[str(key.value) for key in item.placement_options]) for item in pack.casepack.platform.services]
    security = []
    for item in pack.casepack.catalog:
        if "security" in item.key or "firewall" in item.key or "identity" in item.key or "threat" in item.key:
            security.append(_option(item.key, _label(pack, item.key), values=[str(key.value) for key in item.deployment_modes]))
    if not security:
        security = [_option(item.key, _label(pack, item.key), values=[str(key.value) for key in item.deployment_modes]) for item in pack.casepack.catalog]
    people_units = [_option(key, _label(pack, key)) for key in pack.runtime.people.units]
    hiring = [_option(key, key.replace("_", " ").title(), detail=f"{value.fte:g} FTE · ${value.wage_per_round:,}/round") for key, value in pack.runtime.people.hiring_options.items()]
    communication = [_option(key, key.replace("_", " ").title(), detail=f"${value.cost:,} · resistance −{value.resistance_reduction:g}") for key, value in pack.runtime.people.communication_options.items()]
    challenges = [ChallengeOut(
        key=item.key, label=_label(pack, item.key), status="available",
        options=[ChallengeOptionOut(key=option.key, label=option.key.replace("_", " ").title(), cost=int(option.cost), rationale_tags=list(option.tags)) for option in item.options],
    ) for item in pack.casepack.events]
    current_round = max(instance.current_round, 1)
    current_team = None
    if team is not None:
        run, state, sheet = await session.run_sync(_state_and_sheet, instance, team)
        state = state or {}
        current_round = run.current_round if run is not None else current_round
        current_team = ControlsTeamOut(
            id=team.id, name=team.name, current_round=current_round,
            status=run.status if run is not None else "uninitialized",
            revision=sheet.revision if sheet is not None else None,
            locked_revision=sheet.locked_revision if sheet is not None else None,
            strategy=state.get("strategy"), governance=_governance(pack, state),
            policies=_policies(pack, state), selected_commands=_sheet_commands(sheet),
        )
    return ControlsOut(
        instance_id=instance.instance_id, current_round=current_round, total_rounds=instance.total_rounds,
        strategies=strategies, governance=_governance(pack, state if team is not None else {}),
        security_components=security, policies=_policies(pack, state if team is not None else {}),
        services=services, people_units=people_units, hiring_options=hiring,
        communication_options=communication, challenges=challenges,
        capital_balance=(int(state.get("capital_balance")) if team is not None and state.get("capital_balance") is not None else None),
        capital_request_max_amount=int(pack.runtime.accounting.capital_request.max_amount),
        capital_request_min_reason_length=int(pack.runtime.accounting.capital_request.minimum_reason_length),
        capital_request_approval_rounds=list(pack.runtime.accounting.capital_request.approval_rounds),
        team=current_team,
    )


@router.get("/instances/{instance_id}/controls", response_model=ControlsOut)
async def read_controls(instance: SimulationInstance = Depends(get_current_instance), current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session), team_id: int | None = Query(default=None)):  # noqa: B008
    return await _read_controls(session, instance, await _team_for_user(session, instance, current_user, team_id), await _runtime_pack(session, instance))


@router.patch("/instances/{instance_id}/controls/{section}", response_model=ControlsOut)
async def patch_controls(section: str, payload: ControlsPatchIn, instance: SimulationInstance = Depends(get_current_instance), current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session), team_id: int | None = Query(default=None)):  # noqa: B008
    allowed = _SECTIONS.get(section)
    if allowed is None:
        raise HTTPException(status_code=404, detail="Unknown Phase 4 control section")
    team = await _team_for_user(session, instance, current_user, team_id)
    if team is None:
        raise HTTPException(status_code=409, detail="Select a team before editing decisions")
    pack = await _runtime_pack(session, instance)
    run = await session.get(SimulationRunV1, (instance.instance_id, team.id))
    if pack is None or run is None:
        raise HTTPException(status_code=409, detail="The team runtime is not initialized")
    instance_id = instance.instance_id
    team_id_value = team.id
    current_round = run.current_round
    categories = {category: payload.commands for category in allowed if category in {"governance", "policy", "application", "platform_service", "staffing", "communication", "event_response"}}
    if section == "strategy":
        categories = {"governance": [command for command in payload.commands if command.get("op") == "declare_strategy"]}
    elif section == "governance":
        categories = {"governance": [command for command in payload.commands if command.get("op") in {"assign", "set_primary"}]}
    elif section == "security":
        categories = {"policy": [command for command in payload.commands if command.get("op") == "set_policy"], "application": [command for command in payload.commands if command.get("op") in {"buy_application", "replace_application"}]}
    elif section == "services":
        categories = {"platform_service": [command for command in payload.commands if command.get("op") in {"buy_service", "replace_service"}]}
    elif section == "people":
        categories = {"staffing": [command for command in payload.commands if command.get("op") in {"hire", "set_support"}], "communication": [command for command in payload.commands if command.get("op") == "communicate"]}
    elif section == "challenges":
        categories = {"event_response": [command for command in payload.commands if command.get("op") == "respond"]}
    elif section == "budget":
        categories = {"capital_request": [command for command in payload.commands if command.get("op") == "request_capital"]}
    categories = {key: value for key, value in categories.items() if value}
    try:
        patch = SheetPatchV1.model_validate({"version": payload.version, "replace_categories": categories})
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Phase 4 commands are not valid for this round") from exc

    def apply_patch():
        engine = make_engine()
        try:
            return SimulationService(engine, pack).patch_sheet(instance_id, team_id_value, current_round, payload.expected_revision, patch)
        finally:
            engine.dispose()

    try:
        await session.rollback()
        await asyncio.to_thread(apply_patch)
    except SimulationError as exc:
        status = 409 if exc.code in {"revision_conflict", "locked", "round_state", "unaffordable", "not_found"} else 422
        raise HTTPException(status_code=status, detail={"code": exc.code, "field": exc.field}) from exc
    await session.rollback()
    instance = await session.get(SimulationInstance, instance_id)
    team = await session.get(Team, team_id_value)
    return await _read_controls(session, instance, team, pack)
