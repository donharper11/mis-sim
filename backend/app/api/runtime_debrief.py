"""Read-only, persisted Debrief report for completed simulation rounds."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_instance, get_current_user, get_session
from app.api.runtime_platform import _runtime_pack, _team_for_user
from app.models.platform import SimulationInstance, Team, User
from app.round.models import RoundResult

router = APIRouter(tags=["debrief-runtime"])


class DebriefRoundOut(BaseModel):
    round: int
    scorecard: dict[str, Any] = Field(default_factory=dict)
    score: dict[str, Any] = Field(default_factory=dict)
    events: list[dict[str, Any]] = Field(default_factory=list)
    responses: list[dict[str, Any]] = Field(default_factory=list)
    prevented_events: list[dict[str, Any]] = Field(default_factory=list)
    state_changes: dict[str, Any] = Field(default_factory=dict)
    financials: dict[str, Any] = Field(default_factory=dict)
    technical_debt: dict[str, Any] = Field(default_factory=dict)
    tco: list[dict[str, Any]] = Field(default_factory=list)


class DebriefTeamOut(BaseModel):
    id: int
    name: str
    status: str
    latest_round: int | None = None
    rounds: list[DebriefRoundOut] = Field(default_factory=list)


class DebriefOut(BaseModel):
    instance_id: int
    current_round: int
    total_rounds: int
    team: DebriefTeamOut | None = None


def _round_payload(row: RoundResult, pack: Any | None) -> DebriefRoundOut:
    payload = row.payload if isinstance(row.payload, Mapping) else {}
    score = payload.get("score") if isinstance(payload.get("score"), Mapping) else {}
    scorecard = score.get("balanced_scorecard") if isinstance(score.get("balanced_scorecard"), Mapping) else payload.get("scorecard", {})
    state_changes = payload.get("state_changes") if isinstance(payload.get("state_changes"), Mapping) else {}
    events = payload.get("events") if isinstance(payload.get("events"), list) else []
    if pack is not None:
        for event in events:
            if isinstance(event, dict) and event.get("key"):
                event.setdefault("label", pack.casepack.labels.event_names.get(event["key"], event["key"].replace("_", " ").title()))
    return DebriefRoundOut(
        round=row.round, scorecard=dict(scorecard) if isinstance(scorecard, Mapping) else {}, score=dict(score),
        events=[dict(event) for event in events if isinstance(event, Mapping)],
        responses=[dict(response) for response in (payload.get("responses") or []) if isinstance(response, Mapping)],
        prevented_events=[dict(event) for event in (payload.get("prevented_events") or []) if isinstance(event, Mapping)],
        state_changes=dict(state_changes), financials=dict(payload.get("financials") or {}),
        technical_debt=dict(payload.get("technical_debt") or {}),
        tco=[dict(item) for item in (payload.get("tco") or []) if isinstance(item, Mapping)],
    )


async def _read_team(session: AsyncSession, instance: SimulationInstance, team: Team, pack: Any | None) -> DebriefTeamOut:
    rows = list((await session.scalars(select(RoundResult).where(RoundResult.instance_id == instance.instance_id, RoundResult.team_id == team.id).order_by(RoundResult.round))).all())
    return DebriefTeamOut(id=team.id, name=team.name, status="ready" if rows else "no-results", latest_round=rows[-1].round if rows else None, rounds=[_round_payload(row, pack) for row in rows])


@router.get("/instances/{instance_id}/debrief", response_model=DebriefOut)
async def read_debrief(instance: SimulationInstance = Depends(get_current_instance), current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session), team_id: int | None = Query(default=None)):
    team = await _team_for_user(session, instance, current_user, team_id)
    pack = await _runtime_pack(session, instance)
    return DebriefOut(instance_id=instance.instance_id, current_round=max(instance.current_round, 1), total_rounds=instance.total_rounds, team=await _read_team(session, instance, team, pack) if team is not None else None)


def _report_text(report: DebriefOut) -> str:
    lines = [f"MIS Simulation debrief · instance {report.instance_id}", f"Rounds completed: {len(report.team.rounds) if report.team else 0}", ""]
    if report.team is None:
        lines.append("No team selected.")
        return "\n".join(lines) + "\n"
    if not report.team.rounds:
        lines.append("No round results yet — advance a locked round before downloading the debrief.")
        return "\n".join(lines) + "\n"
    for item in report.team.rounds:
        lines.extend([f"ROUND {item.round}", "========", "Balanced Scorecard"])
        lines.extend(f"  {key.replace('_', ' ').title()}: {value}" for key, value in item.scorecard.items())
        lines.append(f"  Firm score: {item.score.get('firm_score', '—')}")
        lines.append("Events: " + (", ".join(str(event.get("label", event.get("key", ""))) for event in item.events) if item.events else "none"))
        if item.responses:
            lines.append("Challenge responses: " + ", ".join(f"{response.get('event', '')}/{response.get('option', '')}" for response in item.responses))
        changes = item.state_changes
        lines.append("Arrived: " + (", ".join(changes.get("arrived", [])) if changes.get("arrived") else "none"))
        lines.append("Rollout changes: " + str(len(changes.get("changed_rollouts", []))))
        lines.append(f"Capital spend: {item.financials.get('capital_spend', '—')}")
        lines.append(f"Run-rate: {item.financials.get('opex_runrate', '—')}")
        lines.append(f"Technical debt: {item.technical_debt.get('closing', '—')}")
        lines.append("")
    return "\n".join(lines)


@router.get("/instances/{instance_id}/debrief/download", response_class=PlainTextResponse)
async def download_debrief(instance: SimulationInstance = Depends(get_current_instance), current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session), team_id: int | None = Query(default=None)):
    team = await _team_for_user(session, instance, current_user, team_id)
    pack = await _runtime_pack(session, instance)
    report = DebriefOut(instance_id=instance.instance_id, current_round=max(instance.current_round, 1), total_rounds=instance.total_rounds, team=await _read_team(session, instance, team, pack) if team is not None else None)
    return PlainTextResponse(_report_text(report), headers={"Content-Disposition": f'attachment; filename="mis-sim-debrief-{instance.instance_id}.txt"'})
