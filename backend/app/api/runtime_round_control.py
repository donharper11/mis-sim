"""Instructor-only round advancement for the first-playable loop."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_instance, get_session, require_instructor_or_ta
from app.api.runtime_platform import _runtime_pack
from app.models.platform import SimulationInstance, Team, User
from app.models.scheduling import RoundSchedule, RoundScheduleTeam
from app.round.db import make_engine
from app.simulation.models import SimulationRunV1, SimulationSheetV1
from app.simulation.service import SimulationService
from app.simulation.generation import same_generation
from app.simulation.types import SimulationError

router = APIRouter(tags=["round-control"])


class InstanceStatusOut(BaseModel):
    instance_id: int
    status: str
    current_round: int
    total_rounds: int


class LockTeamResult(BaseModel):
    team_id: int
    status: str
    locked_revision: int | None = None


class LockOut(BaseModel):
    instance_id: int
    round: int
    teams: list[LockTeamResult] = Field(default_factory=list)


class ReopenIn(BaseModel):
    team_id: int


class ReopenOut(BaseModel):
    team_id: int
    round: int
    revision: int
    locked_revision: int | None = None
    status: str


class ScheduleTeamOut(BaseModel):
    team_id: int
    locked_revision: int | None = None
    locked_at: datetime | None = None
    advanced_at: datetime | None = None


class ScheduleRoundOut(BaseModel):
    round_number: int
    start_at: datetime
    deadline: datetime
    auto_advance: bool
    grace_period_minutes: int
    decisions_locked: bool
    lock_reason: str | None = None
    locked_at: datetime | None = None
    advanced_at: datetime | None = None
    teams: list[ScheduleTeamOut] = Field(default_factory=list)


class ScheduleOut(BaseModel):
    instance_id: int
    rounds: list[ScheduleRoundOut] = Field(default_factory=list)


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
    expected_started_at = instance.started_at
    pack = await _runtime_pack(session, instance)
    if pack is None:
        raise HTTPException(status_code=409, detail="The registered runtime pack is unavailable")
    team_ids = list((await session.scalars(select(Team.id).where(Team.instance_id == instance.instance_id).order_by(Team.id))).all())
    if not team_ids:
        raise HTTPException(status_code=409, detail="The instance has no teams to advance")
    instance_id_value = instance.instance_id
    run_rounds: dict[int, int] = {}
    for team_id in team_ids:
        run = await session.get(SimulationRunV1, (instance_id_value, team_id))
        if run is None:
            raise HTTPException(status_code=409, detail=f"Team {team_id} is not initialized")
        if run.status != "completed":
            run_rounds[team_id] = run.current_round
    active_rounds = set(run_rounds.values())
    if len(active_rounds) > 1:
        raise HTTPException(status_code=409, detail=f"Teams are on different rounds: {sorted(active_rounds)}")
    # The versioned run is authoritative.  The scheduler may have advanced a run
    # without updating the presentation-level instance pointer, so reconcile the
    # pointer after a successful batch instead of rejecting a valid scheduled round.
    target_round = next(iter(active_rounds), max(instance.current_round, 1))
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
                    locked = service.lock(instance_id, team_id_value, round_number, revision, expected_started_at=expected_started_at)
                    locked_revision = locked.locked_revision
                return service.advance(instance_id, team_id_value, round_number, locked_revision, expected_started_at=expected_started_at)
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

    # Reset can complete after the last per-team commit. Fence the final display
    # update with its instance lock and fresh scalar run rows, not cached ORM data.
    await session.rollback()
    if session.bind.dialect.name == "sqlite":
        await session.execute(update(SimulationInstance).where(
            SimulationInstance.instance_id == instance_id_value,
        ).values(current_round=SimulationInstance.current_round).execution_options(synchronize_session=False))
    instance = await session.scalar(select(SimulationInstance).where(
        SimulationInstance.instance_id == instance_id_value,
    ).with_for_update(key_share=True).execution_options(populate_existing=True))
    runs = (await session.execute(select(
        SimulationRunV1.team_id, SimulationRunV1.current_round,
        SimulationRunV1.advanced_round, SimulationRunV1.status,
    ).where(SimulationRunV1.instance_id == instance_id_value))).all()
    if instance is None or not same_generation(instance.started_at, expected_started_at) or {r.team_id for r in runs} != set(team_ids) or any(r.advanced_round < target_round for r in runs):
        raise HTTPException(status_code=409, detail="The instance changed while advancing; refresh its current status")
    active_rounds = {r.current_round for r in runs if r.status != "completed"}
    if len(active_rounds) > 1:
        raise HTTPException(status_code=409, detail="Teams are on different rounds; refresh their current status")
    next_round = next(iter(active_rounds), None)
    instance.current_round = next_round if next_round is not None else max(r.current_round for r in runs)
    if instance.status not in {"paused", "archived"}:
        instance.status = "active" if next_round is not None else "completed"
    await session.commit()
    return AdvanceOut(instance_id=instance.instance_id, round=target_round, next_round=next_round, advanced=advanced, completed=completed, results=results)


@router.post("/instances/{instance_id}/round-control/pause", response_model=InstanceStatusOut)
async def pause_instance(
    instance: SimulationInstance = Depends(get_current_instance),  # noqa: B008
    _staff: User = Depends(require_instructor_or_ta),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    if instance.status != "active":
        raise HTTPException(status_code=409, detail="Only an active instance can be paused")
    instance.status = "paused"
    await session.commit()
    return InstanceStatusOut(instance_id=instance.instance_id, status=instance.status, current_round=instance.current_round, total_rounds=instance.total_rounds)


@router.post("/instances/{instance_id}/round-control/resume", response_model=InstanceStatusOut)
async def resume_instance(
    instance: SimulationInstance = Depends(get_current_instance),  # noqa: B008
    _staff: User = Depends(require_instructor_or_ta),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    if instance.status != "paused":
        raise HTTPException(status_code=409, detail="Only a paused instance can be resumed")
    instance.status = "active"
    await session.commit()
    return InstanceStatusOut(instance_id=instance.instance_id, status=instance.status, current_round=instance.current_round, total_rounds=instance.total_rounds)


@router.post("/instances/{instance_id}/round-control/lock", response_model=LockOut)
async def lock_round(
    instance: SimulationInstance = Depends(get_current_instance),  # noqa: B008
    _staff: User = Depends(require_instructor_or_ta),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    expected_started_at = instance.started_at
    pack = await _runtime_pack(session, instance)
    if pack is None:
        raise HTTPException(status_code=409, detail="The registered runtime pack is unavailable")
    team_ids = list((await session.scalars(
        select(Team.id).where(Team.instance_id == instance.instance_id).order_by(Team.id)
    )).all())
    if not team_ids:
        raise HTTPException(status_code=409, detail="The instance has no teams to lock")
    instance_id_value = instance.instance_id
    current_round = max(instance.current_round, 1)
    results: list[LockTeamResult] = []
    for tid in team_ids:
        run = await session.get(SimulationRunV1, (instance_id_value, tid))
        if run is None:
            results.append(LockTeamResult(team_id=tid, status="not_initialized"))
            continue
        if run.status == "completed":
            results.append(LockTeamResult(team_id=tid, status="completed"))
            continue
        if run.status == "locked":
            sheet = await session.get(SimulationSheetV1, (instance_id_value, tid, run.current_round))
            results.append(LockTeamResult(team_id=tid, status="already_locked", locked_revision=sheet.locked_revision if sheet else None))
            continue
        sheet = await session.get(SimulationSheetV1, (instance_id_value, tid, run.current_round))
        if sheet is None:
            results.append(LockTeamResult(team_id=tid, status="no_sheet"))
            continue
        revision = sheet.revision
        team_id_for_lock = tid
        round_for_lock = run.current_round

        def lock_one(iid=instance_id_value, t=team_id_for_lock, r=round_for_lock, rev=revision):
            engine = make_engine()
            try:
                service = SimulationService(engine, pack)
                return service.lock(iid, t, r, rev, expected_started_at=expected_started_at)
            finally:
                engine.dispose()

        try:
            await session.rollback()
            locked = await asyncio.to_thread(lock_one)
            results.append(LockTeamResult(team_id=tid, status="locked", locked_revision=locked.locked_revision))
        except SimulationError as exc:
            if exc.field == "generation":
                raise HTTPException(status_code=409, detail="The simulation was restarted; refresh before changing the round") from exc
            results.append(LockTeamResult(team_id=tid, status=f"error:{exc.code}"))

    return LockOut(instance_id=instance_id_value, round=current_round, teams=results)


@router.post("/instances/{instance_id}/round-control/reopen", response_model=ReopenOut)
async def reopen_team(
    payload: ReopenIn,
    instance: SimulationInstance = Depends(get_current_instance),  # noqa: B008
    _staff: User = Depends(require_instructor_or_ta),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    expected_started_at = instance.started_at
    pack = await _runtime_pack(session, instance)
    if pack is None:
        raise HTTPException(status_code=409, detail="The registered runtime pack is unavailable")
    instance_id_value = instance.instance_id
    team_id = payload.team_id
    run = await session.get(SimulationRunV1, (instance_id_value, team_id))
    if run is None:
        raise HTTPException(status_code=404, detail=f"Team {team_id} is not initialized")
    if run.status != "locked":
        raise HTTPException(status_code=409, detail=f"Team {team_id} is not locked (status: {run.status})")
    sheet = await session.get(SimulationSheetV1, (instance_id_value, team_id, run.current_round))
    if sheet is None or sheet.locked_revision is None:
        raise HTTPException(status_code=409, detail=f"Team {team_id} has no locked sheet for round {run.current_round}")
    locked_revision = sheet.locked_revision
    round_number = run.current_round

    def reopen_one(iid=instance_id_value, t=team_id, r=round_number, rev=locked_revision):
        engine = make_engine()
        try:
            service = SimulationService(engine, pack)
            return service.reopen(iid, t, r, rev, expected_started_at=expected_started_at)
        finally:
            engine.dispose()

    try:
        await session.rollback()
        result = await asyncio.to_thread(reopen_one)
    except SimulationError as exc:
        status = 409 if exc.code in {"revision_conflict", "locked", "round_state"} else 422
        raise HTTPException(status_code=status, detail={"code": exc.code, "field": exc.field}) from exc
    return ReopenOut(team_id=team_id, round=round_number, revision=result.revision, locked_revision=result.locked_revision, status="draft")


@router.get("/instances/{instance_id}/round-control/schedule", response_model=ScheduleOut)
async def read_schedule(
    instance: SimulationInstance = Depends(get_current_instance),  # noqa: B008
    _staff: User = Depends(require_instructor_or_ta),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
):
    schedules = list((await session.scalars(
        select(RoundSchedule)
        .where(RoundSchedule.instance_id == instance.instance_id)
        .order_by(RoundSchedule.round_number)
    )).all())
    rounds: list[ScheduleRoundOut] = []
    for schedule in schedules:
        team_rows = list((await session.scalars(
            select(RoundScheduleTeam)
            .where(RoundScheduleTeam.schedule_id == schedule.id, RoundScheduleTeam.instance_id == instance.instance_id)
        )).all())
        teams = [ScheduleTeamOut(
            team_id=row.team_id, locked_revision=row.locked_revision,
            locked_at=row.locked_at, advanced_at=row.advanced_at,
        ) for row in team_rows]
        rounds.append(ScheduleRoundOut(
            round_number=schedule.round_number, start_at=schedule.start_at, deadline=schedule.deadline,
            auto_advance=schedule.auto_advance, grace_period_minutes=schedule.grace_period_minutes,
            decisions_locked=schedule.decisions_locked, lock_reason=schedule.lock_reason,
            locked_at=schedule.locked_at, advanced_at=schedule.advanced_at, teams=teams,
        ))
    return ScheduleOut(instance_id=instance.instance_id, rounds=rounds)
