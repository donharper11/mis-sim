"""Scoped Review & Lock surface over the versioned simulation runtime."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_instance, get_current_user, get_session
from app.api.runtime_platform import _runtime_pack, _team_for_user
from app.models.platform import SimulationInstance, Team, User
from app.models.scheduling import RoundSchedule, RoundScheduleTeam
from app.round.db import make_engine
from app.round.models import TeamStateRow
from app.simulation.models import (
    SimulationRunV1,
    SimulationSheetV1,
)
from app.simulation.service import SimulationService
from app.simulation.types import SimulationError

router = APIRouter(tags=["review-runtime"])


class ReviewLineOut(BaseModel):
    category: str
    changes: int
    capital: int
    operating: int


class ReviewTeamOut(BaseModel):
    id: int
    name: str
    current_round: int
    status: str
    revision: int | None = None
    locked_revision: int | None = None
    lines: list[ReviewLineOut] = Field(default_factory=list)
    capital_available: int | None = None
    capital_spend: int = 0
    capital_remaining: int | None = None
    run_rate_before: int | None = None
    run_rate_after: int | None = None
    warnings: list[str] = Field(default_factory=list)


class ReviewOut(BaseModel):
    instance_id: int
    current_round: int
    total_rounds: int
    team: ReviewTeamOut | None = None


class ReviewLockIn(BaseModel):
    expected_revision: int = Field(ge=0)


_CATEGORY_LABELS = {
    "platform_service": "Platform",
    "application": "Components",
    "lifecycle": "Lifecycle",
    "training": "Training",
    "process_redesign": "Process redesign",
    "communication": "Communication",
    "integration": "Connections",
    "staffing": "People",
    "governance": "Governance",
    "policy": "Policy",
    "event_response": "Challenges",
    "capital_request": "Capital",
}


def _warning_text(raw: Any) -> str:
    if isinstance(raw, Mapping):
        code = str(raw.get("code", "warning")).replace("_", " ")
        keys = raw.get("keys") or []
        return f"{code.title()}: {', '.join(str(key) for key in keys)}" if keys else code.title()
    return str(raw)


def _review_from_view(view: Any, team: Team) -> ReviewTeamOut:
    sheet = view.sheet
    if sheet is None:
        return ReviewTeamOut(id=team.id, name=team.name, current_round=view.current_round, status=view.status)
    commands = list(sheet.commands)
    preview = sheet.preview
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: {"changes": 0, "capital": 0, "operating": 0})
    for command in commands:
        category = {"buy_application": "application", "replace_application": "application", "buy_service": "platform_service", "replace_service": "platform_service", "connect": "integration", "disconnect": "integration", "cancel_order": "lifecycle", "retire_asset": "lifecycle", "project": "lifecycle", "train": "training", "set_process": "process_redesign", "communicate": "communication", "hire": "staffing", "set_support": "staffing", "assign": "governance", "set_primary": "governance", "declare_strategy": "governance", "set_policy": "policy", "respond": "event_response", "request_capital": "capital_request"}.get(command.op, command.op)
        grouped[category]["changes"] += 1
    for entry in preview.cost_entries:
        category = str(entry.get("category") or entry.get("kind") or "other")
        grouped[category]["capital"] += max(0, -int(entry.get("capital_delta", 0)))
        grouped[category]["operating"] += max(0, -int(entry.get("operating_delta", 0)))
    lines = [ReviewLineOut(category=_CATEGORY_LABELS.get(category, category.replace("_", " ").title()), changes=values["changes"], capital=values["capital"], operating=values["operating"]) for category, values in sorted(grouped.items()) if values["changes"] or values["capital"] or values["operating"]]
    forecasts = list(preview.operating_forecast)
    before = forecasts[0].opening if forecasts else None
    return ReviewTeamOut(
        id=team.id, name=team.name, current_round=view.current_round, status=view.status,
        revision=sheet.revision, locked_revision=sheet.locked_revision, lines=lines,
        capital_available=preview.capital_available, capital_spend=preview.capital_spend,
        capital_remaining=preview.capital_remaining, run_rate_before=before,
        run_rate_after=preview.operating_runrate, warnings=[_warning_text(item.model_dump(mode="json")) for item in preview.warnings],
    )


async def _read_team(session: AsyncSession, instance: SimulationInstance, team: Team, pack: Any | None) -> ReviewTeamOut:
    run = await session.get(SimulationRunV1, (instance.instance_id, team.id))
    if run is not None and pack is not None:
        def read_run():
            engine = make_engine()
            try:
                return SimulationService(engine, pack).read(instance.instance_id, team.id)
            finally:
                engine.dispose()
        try:
            view = await asyncio.to_thread(read_run)
            return _review_from_view(view, team)
        except SimulationError as exc:
            raise HTTPException(status_code=409, detail={"code": exc.code, "field": exc.field}) from exc
    if run is not None:
        sheet = await session.get(SimulationSheetV1, (instance.instance_id, team.id, run.current_round))
        return ReviewTeamOut(id=team.id, name=team.name, current_round=run.current_round, status="unavailable", revision=sheet.revision if sheet else None, locked_revision=sheet.locked_revision if sheet else None)
    state = await session.get(TeamStateRow, (instance.instance_id, team.id))
    round_number = max((state.current_round if state else instance.current_round), 1)
    return ReviewTeamOut(id=team.id, name=team.name, current_round=round_number, status="active" if state else "uninitialized", capital_available=state.cash if state else None, capital_remaining=state.cash if state else None, run_rate_before=state.opex_runrate if state else None, run_rate_after=state.opex_runrate if state else None)


@router.get("/instances/{instance_id}/review", response_model=ReviewOut)
async def read_review(instance: SimulationInstance = Depends(get_current_instance), current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session), team_id: int | None = Query(default=None)):
    team = await _team_for_user(session, instance, current_user, team_id)
    pack = await _runtime_pack(session, instance)
    return ReviewOut(instance_id=instance.instance_id, current_round=max(instance.current_round, 1), total_rounds=instance.total_rounds, team=await _read_team(session, instance, team, pack) if team is not None else None)


@router.post("/instances/{instance_id}/review/lock", response_model=ReviewOut)
async def lock_review(payload: ReviewLockIn, instance: SimulationInstance = Depends(get_current_instance), current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session), team_id: int | None = Query(default=None)):
    team = await _team_for_user(session, instance, current_user, team_id)
    if team is None:
        raise HTTPException(status_code=409, detail="Select a team before locking the round")
    pack = await _runtime_pack(session, instance)
    if pack is None:
        raise HTTPException(status_code=409, detail="The registered runtime pack is unavailable")
    run = await session.get(SimulationRunV1, (instance.instance_id, team.id))
    if run is None:
        raise HTTPException(status_code=409, detail="The team runtime is not initialized")
    round_number = run.current_round
    def lock_run():
        engine = make_engine()
        try:
            return SimulationService(engine, pack).lock(instance.instance_id, team.id, round_number, payload.expected_revision)
        finally:
            engine.dispose()
    try:
        locked = await asyncio.to_thread(lock_run)
    except SimulationError as exc:
        status = 409 if exc.code in {"revision_conflict", "locked", "round_state", "not_found"} else 422
        raise HTTPException(status_code=status, detail={"code": exc.code, "field": exc.field}) from exc
    schedule = await session.scalar(select(RoundSchedule).where(RoundSchedule.instance_id == instance.instance_id, RoundSchedule.round_number == round_number))
    if schedule is not None:
        participant = await session.get(RoundScheduleTeam, (schedule.id, team.id))
        if participant is not None:
            participant.locked_revision = locked.locked_revision
            participant.locked_at = datetime.now(timezone.utc)
            rows = list((await session.scalars(select(RoundScheduleTeam).where(RoundScheduleTeam.schedule_id == schedule.id))).all())
            if rows and all(row.locked_revision is not None for row in rows):
                schedule.decisions_locked = True
                schedule.locked_at = schedule.locked_at or datetime.now(timezone.utc)
            await session.commit()
    await session.refresh(run)
    return ReviewOut(instance_id=instance.instance_id, current_round=max(instance.current_round, 1), total_rounds=instance.total_rounds, team=await _read_team(session, instance, team, pack))
