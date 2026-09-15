"""Instructor-only round advancement for the first-playable loop."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_instance, get_session, require_instructor_or_ta
from app.api.runtime_platform import _runtime_pack
from app.models.platform import SimulationInstance, Team, User
from app.round.db import make_engine
from app.simulation.models import SimulationRunV1, SimulationSheetV1
from app.simulation.service import SimulationService
from app.simulation.types import SimulationError

router = APIRouter(tags=["round-control"])


class AdvanceOut(BaseModel):
    instance_id: int
    round: int
    next_round: int | None = None
    advanced: list[int] = Field(default_factory=list)
    completed: list[int] = Field(default_factory=list)
    results: list[dict[str, Any]] = Field(default_factory=list)


@router.post("/instances/{instance_id}/round-control/advance", response_model=AdvanceOut)
async def advance_round(
    instance: SimulationInstance = Depends(get_current_instance),  # noqa: B008
    _staff: User = Depends(require_instructor_or_ta),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    pack = await _runtime_pack(session, instance)
    if pack is None:
        raise HTTPException(status_code=409, detail="The registered runtime pack is unavailable")
    team_ids = list((await session.scalars(select(Team.id).where(Team.instance_id == instance.instance_id).order_by(Team.id))).all())
    if not team_ids:
        raise HTTPException(status_code=409, detail="The instance has no teams to advance")
    instance_id_value = instance.instance_id
    total_rounds = instance.total_rounds
    target_round = max(instance.current_round, 1)
    advanced: list[int] = []
    completed: list[int] = []
    results: list[dict[str, Any]] = []
    for team_id in team_ids:
        run = await session.get(SimulationRunV1, (instance_id_value, team_id))
        if run is None:
            raise HTTPException(status_code=409, detail=f"Team {team_id} is not initialized")
        if run.status == "completed":
            completed.append(team_id)
            continue
        if run.current_round != target_round:
            raise HTTPException(status_code=409, detail=f"Team {team_id} is on round {run.current_round}; expected {target_round}")
        sheet = await session.get(SimulationSheetV1, (instance_id_value, team_id, target_round))
        if sheet is None:
            raise HTTPException(status_code=409, detail=f"Team {team_id} has no decision sheet")
        revision = sheet.revision
        existing_locked_revision = sheet.locked_revision
        instance_id = instance_id_value
        team_id_value = team_id
        round_number = run.current_round

        def advance_one(
            instance_id=instance_id,
            team_id_value=team_id_value,
            round_number=round_number,
            revision=revision,
            existing_locked_revision=existing_locked_revision,
        ):
            engine = make_engine()
            try:
                service = SimulationService(engine, pack)
                locked_revision = revision
                if existing_locked_revision is None:
                    locked = service.lock(instance_id, team_id_value, round_number, revision)
                    locked_revision = locked.locked_revision
                return service.advance(instance_id, team_id_value, round_number, locked_revision)
            finally:
                engine.dispose()

        try:
            await session.rollback()
            result = await asyncio.to_thread(advance_one)
        except SimulationError as exc:
            status = 409 if exc.code in {"revision_conflict", "locked", "round_state", "unaffordable", "not_found"} else 422
            raise HTTPException(status_code=status, detail={"code": exc.code, "field": exc.field}) from exc
        advanced.append(team_id)
        results.append({"team_id": team_id, "round": target_round, "score": result.get("score"), "scorecard": result.get("scorecard")})

    instance = await session.get(SimulationInstance, instance_id_value)
    if target_round >= total_rounds:
        instance.current_round = target_round
        instance.status = "completed"
        next_round = None
    else:
        instance.current_round = target_round + 1
        instance.status = "active"
        next_round = target_round + 1
    await session.commit()
    return AdvanceOut(instance_id=instance.instance_id, round=target_round, next_round=next_round, advanced=advanced, completed=completed, results=results)
