"""Read-only dashboard projection for the student core loop.

The dashboard deliberately reads persisted runtime state.  It does not re-score a team,
invent casepack copy, or mutate a decision sheet.  The legacy round tables and the versioned
simulation checkpoint are both supported while the platform migrates between runtime paths.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_instance, get_current_user, get_session
from app.models.platform import Enrollment, SimulationInstance, Team, User
from app.round.models import (
    ArchNodeRow,
    DeploymentOrgStateRow,
    OrgUnitRow,
    RoundResult,
    SignalRow,
    TeamStateRow,
)
from app.simulation.models import SimulationCheckpointV1, SimulationRunV1

router = APIRouter(tags=["dashboard"])

_SCORECARD_DIMENSIONS = ("financial", "customer", "internal_process", "learning_growth")


class DashboardScorecard(BaseModel):
    financial: float | None = None
    customer: float | None = None
    internal_process: float | None = None
    learning_growth: float | None = None


class DashboardSignal(BaseModel):
    model_config = ConfigDict(extra="ignore")

    key: str
    capability: str | None = None
    severity: str | None = None
    status: str | None = None
    round: int | None = None
    value: float | None = None
    first_shown_round: int | None = None
    cleared_round: int | None = None
    fire_round: int | None = None


class DashboardUnit(BaseModel):
    key: str
    name: str
    people: int | None = None
    running: list[str] = Field(default_factory=list)
    implemented: list[str] = Field(default_factory=list)
    adoption: float | None = None
    process: str | None = None
    contributing: list[str] = Field(default_factory=list)


class DashboardTeam(BaseModel):
    id: int
    name: str
    current_round: int
    status: str
    strategy: str | None = None
    capital_remaining: int | None = None
    run_rate: int | None = None
    latest_result_round: int | None = None
    scorecard: DashboardScorecard = Field(default_factory=DashboardScorecard)
    open_signals: list[DashboardSignal] = Field(default_factory=list)
    attention: list[str] = Field(default_factory=list)
    units: list[DashboardUnit] = Field(default_factory=list)


class DashboardOut(BaseModel):
    instance_id: int
    current_round: int
    total_rounds: int
    status: str
    selected_team_id: int | None = None
    teams: list[DashboardTeam] = Field(default_factory=list)


def _number(value: Any) -> int | float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value


def _scorecard(payload: Mapping[str, Any] | None) -> DashboardScorecard:
    values = payload.get("scorecard") if isinstance(payload, Mapping) else None
    if not isinstance(values, Mapping):
        return DashboardScorecard()
    return DashboardScorecard(**{dimension: _number(values.get(dimension)) for dimension in _SCORECARD_DIMENSIONS})


def _signal(raw: Any, *, default_round: int | None = None) -> DashboardSignal | None:
    if isinstance(raw, Mapping):
        source = raw
    else:
        source = {name: getattr(raw, name, None) for name in (
            "key", "capability", "severity", "status", "round", "value",
            "first_shown_round", "cleared_round", "fire_round",
        )}
    if not isinstance(source.get("key"), str):
        return None
    return DashboardSignal(
        key=source["key"], capability=source.get("capability"), severity=source.get("severity"),
        status=source.get("status"), round=source.get("round", default_round),
        value=_number(source.get("value")), first_shown_round=source.get("first_shown_round"),
        cleared_round=source.get("cleared_round"), fire_round=source.get("fire_round"),
    )


def _signals(payload: Mapping[str, Any] | None, fallback: list[Any]) -> list[DashboardSignal]:
    raw_values: list[Any] = []
    if isinstance(payload, Mapping) and isinstance(payload.get("signals"), Mapping):
        raw_values.extend(payload["signals"].get("open") or [])
    if not raw_values:
        raw_values.extend(fallback)
    return [item for raw in raw_values if (item := _signal(raw)) is not None]


def _unit_rows(
    deployments: list[DeploymentOrgStateRow],
    nodes: list[ArchNodeRow],
    org_units: list[OrgUnitRow],
) -> list[DashboardUnit]:
    by_unit: dict[str, DashboardUnit] = {}
    for deployment in deployments:
        key = deployment.org_unit or deployment.key
        unit = by_unit.setdefault(key, DashboardUnit(key=key, name=key, people=deployment.people_affected))
        if deployment.people_affected is not None:
            unit.people = deployment.people_affected
        for node in nodes:
            if node.key == deployment.key or deployment.catalog_key == node.key:
                for label in (node.key, deployment.catalog_key):
                    if label and label not in unit.running:
                        unit.running.append(label)
        trained = f"trained {deployment.trained_count}"
        if trained not in unit.implemented:
            unit.implemented.append(trained)
        if deployment.process:
            unit.process = deployment.process
            if deployment.process not in unit.implemented:
                unit.implemented.append(f"process {deployment.process}")
        unit.adoption = deployment.adoption
        for capability in deployment.serves or []:
            if capability not in unit.contributing:
                unit.contributing.append(capability)
    for row in org_units:
        unit = by_unit.setdefault(row.key, DashboardUnit(key=row.key, name=row.key))
        # Resistance is a real persisted input; retain it as an implementation hint only when
        # there is no rollout row to supply adoption.  It remains a nullable response field.
        if unit.adoption is None:
            unit.adoption = max(0.0, min(1.0, 1.0 - row.resistance))
    return list(by_unit.values())


def _modern_units(state: Mapping[str, Any]) -> list[DashboardUnit]:
    rollouts = state.get("rollouts") if isinstance(state.get("rollouts"), Mapping) else {}
    units = state.get("unit_resistance") if isinstance(state.get("unit_resistance"), Mapping) else {}
    implemented = []
    adoption_values = []
    for rollout in rollouts.values():
        if isinstance(rollout, Mapping):
            trained = rollout.get("trained_count")
            process = rollout.get("process")
            if trained is not None:
                implemented.append(f"trained {trained}")
            if process:
                implemented.append(f"process {process}")
            adoption = _number(rollout.get("adoption"))
            if isinstance(adoption, (int, float)):
                adoption_values.append(float(adoption))
    return [DashboardUnit(
        key=str(key), name=str(key), implemented=implemented,
        adoption=(sum(adoption_values) / len(adoption_values)) if adoption_values else None,
    ) for key in units]


async def _team_dashboard(session: AsyncSession, instance: SimulationInstance, team: Team) -> DashboardTeam:
    team_state = await session.get(TeamStateRow, (instance.instance_id, team.id))
    result = await session.scalar(
        select(RoundResult)
        .where(RoundResult.instance_id == instance.instance_id, RoundResult.team_id == team.id)
        .order_by(desc(RoundResult.round))
        .limit(1)
    )
    payload = result.payload if result is not None and isinstance(result.payload, Mapping) else None
    current_round = instance.current_round or 1
    status = "uninitialized"
    strategy = None
    capital_remaining = None
    run_rate = None
    units: list[DashboardUnit] = []
    fallback_signals: list[Any] = []

    if team_state is not None:
        current_round = max(int(team_state.current_round), 1)
        status = "locked" if team_state.locked_round and team_state.locked_round >= current_round else "active"
        strategy = team_state.declared_strategy
        capital_remaining = int(team_state.cash)
        run_rate = int(team_state.opex_runrate)
        snapshot_round = result.round if result is not None else max(current_round - 1, 1)
        deployments = (await session.scalars(select(DeploymentOrgStateRow).where(
            DeploymentOrgStateRow.instance_id == instance.instance_id,
            DeploymentOrgStateRow.team_id == team.id,
            DeploymentOrgStateRow.round == snapshot_round,
        ))).all()
        nodes = (await session.scalars(select(ArchNodeRow).where(
            ArchNodeRow.instance_id == instance.instance_id,
            ArchNodeRow.team_id == team.id,
            ArchNodeRow.round == snapshot_round,
        ))).all()
        org_units = (await session.scalars(select(OrgUnitRow).where(
            OrgUnitRow.instance_id == instance.instance_id,
            OrgUnitRow.team_id == team.id,
            OrgUnitRow.round == snapshot_round,
        ))).all()
        units = _unit_rows(list(deployments), list(nodes), list(org_units))
        fallback_signals = list((await session.scalars(select(SignalRow).where(
            SignalRow.instance_id == instance.instance_id,
            SignalRow.team_id == team.id,
            SignalRow.status == "open",
        ))).all())
    else:
        run = await session.get(SimulationRunV1, (instance.instance_id, team.id))
        if run is not None:
            current_round = max(int(run.current_round), 1)
            status = run.status
            checkpoint = await session.get(SimulationCheckpointV1, (instance.instance_id, team.id, run.advanced_round))
            state = checkpoint.state if checkpoint is not None and isinstance(checkpoint.state, Mapping) else {}
            strategy = state.get("strategy")
            capital_remaining = _number(state.get("capital_balance"))
            run_rate = _number(payload.get("financials", {}).get("opex_runrate")) if isinstance(payload, Mapping) else None
            units = _modern_units(state)
            fallback_signals = state.get("signal_ledger", []) if isinstance(state.get("signal_ledger"), list) else []

    open_signals = _signals(payload, fallback_signals)
    attention = [signal.key for signal in open_signals]
    for unit in units:
        if unit.adoption is not None and unit.adoption <= 0:
            attention.append(unit.name)
    return DashboardTeam(
        id=team.id, name=team.name, current_round=current_round, status=status,
        strategy=strategy, capital_remaining=capital_remaining, run_rate=run_rate,
        latest_result_round=result.round if result is not None else None,
        scorecard=_scorecard(payload), open_signals=open_signals, attention=attention, units=units,
    )


@router.get("/instances/{instance_id}/dashboard", response_model=DashboardOut)
async def read_dashboard(
    instance: SimulationInstance = Depends(get_current_instance),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    teams = list((await session.scalars(select(Team).where(
        Team.instance_id == instance.instance_id,
    ).order_by(Team.id))).all())
    selected_team_id: int | None = None
    if current_user.role == "student":
        selected_team_id = await session.scalar(select(Enrollment.team_id).where(
            Enrollment.user_id == current_user.id,
            Enrollment.section_id == instance.section_id,
            Enrollment.role == "student",
            Enrollment.is_active.is_(True),
        ))
        teams = [team for team in teams if team.id == selected_team_id]
    projected = [await _team_dashboard(session, instance, team) for team in teams]
    return DashboardOut(
        instance_id=instance.instance_id,
        current_round=max(instance.current_round, 1),
        total_rounds=instance.total_rounds,
        status=instance.status,
        selected_team_id=selected_team_id if selected_team_id is not None else (projected[0].id if len(projected) == 1 else None),
        teams=projected,
    )
