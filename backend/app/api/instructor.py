"""Bounded M5 instructor setup and roster workspace routes.

This module exposes read models and assignment mutations for course setup.  It
does not provision accounts or touch simulation runtime state.  M5.4 adds
read-only cross-team monitoring and round progression routes.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import authorize_course, authorize_section, get_current_user, require_instructor
from app.database import async_session
from app.models.platform import Casepack, Course, Enrollment, Section, SimulationInstance, Team, User
from app.round.models import RoundResult, SignalRow, TeamStateRow
from app.services.platform import (
    CourseService,
    EnrollmentService,
    InstanceService,
    PlatformConflict,
    PlatformNotFound,
    TeamService,
    archive_instance,
    clone_section,
    reset_instance,
)
from app.simulation.models import SimulationCheckpointV1, SimulationRunV1


router = APIRouter(tags=["instructor"])


async def get_session():
    async with async_session() as session:
        yield session


class CourseSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_code: str
    course_name: str
    academic_year: str
    semester: str
    instructor_id: int
    active_chapters: list[int]
    is_active: bool


class InstanceSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    instance_id: int
    pack_key: str
    pack_version: str
    pack_digest: str | None
    current_round: int
    total_rounds: int
    status: str


class TeamSummary(BaseModel):
    id: int
    name: str
    member_count: int


class SectionSetup(BaseModel):
    id: int
    section_code: str
    section_name: str
    max_teams: int
    team_size_min: int
    team_size_max: int
    is_active: bool
    instance: InstanceSummary | None
    teams: list[TeamSummary]
    enrollment_count: int


class CourseSetup(BaseModel):
    course: CourseSummary
    sections: list[SectionSetup]


class CasepackSummary(BaseModel):
    pack_key: str
    pack_version: str
    display_name: str
    vertical: str
    schema_version: int
    rounds: int
    pack_digest: str
    registered_at: datetime
    errors: list[dict] = Field(default_factory=list)
    warnings: list[dict] = Field(default_factory=list)
    exit_code: int


class EnrollmentRosterRow(BaseModel):
    enrollment_id: int
    user_id: int
    student_id: str | None
    name: str
    email: str
    role: str
    is_active: bool
    team: TeamSummary | None


class TeamOut(BaseModel):
    id: int
    section_id: int
    instance_id: int
    name: str
    member_count: int


class TeamRename(BaseModel):
    name: str = Field(min_length=1, max_length=160)


class EnrollmentPatch(BaseModel):
    team_id: int | None


class SettingsPatchIn(BaseModel):
    default_round_duration_hours: float | None = None
    auto_advance_on_deadline: bool | None = None
    grace_period_minutes: int | None = None
    lock_warning_minutes: int | None = None


def _error(exc: Exception) -> HTTPException:
    if isinstance(exc, HTTPException):
        return exc
    if isinstance(exc, PlatformNotFound):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, PlatformConflict):
        return HTTPException(status_code=409, detail=str(exc))
    return HTTPException(status_code=400, detail=str(exc))


async def _team_out(session: AsyncSession, team: Team) -> TeamOut:
    count = await session.scalar(select(func.count(Enrollment.id)).where(Enrollment.team_id == team.id, Enrollment.is_active.is_(True)))
    return TeamOut(id=team.id, section_id=team.section_id, instance_id=team.instance_id, name=team.name, member_count=count or 0)


async def _team_summary(session: AsyncSession, team: Team) -> TeamSummary:
    count = await session.scalar(select(func.count(Enrollment.id)).where(Enrollment.team_id == team.id, Enrollment.is_active.is_(True)))
    return TeamSummary(id=team.id, name=team.name, member_count=count or 0)


@router.get("/instructor/courses", response_model=list[CourseSummary])
async def list_instructor_courses(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_instructor),
):
    rows = await CourseService.list_for(session, instructor_id=None if current_user.role == "admin" else current_user.id)
    return rows


@router.get("/instructor/courses/{course_id}/setup", response_model=CourseSetup)
async def read_course_setup(
    course_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_instructor),
):
    try:
        course = await authorize_course(session, current_user, course_id)
        sections = list((await session.scalars(select(Section).where(Section.course_id == course.id).order_by(Section.id))).all())
        result: list[SectionSetup] = []
        for section in sections:
            instance = await session.scalar(select(SimulationInstance).where(SimulationInstance.section_id == section.id))
            # M5.7: archived instances are excluded from the setup list.
            if instance is not None and instance.status == "archived":
                continue
            teams = []
            if instance is not None:
                teams = list((await session.scalars(select(Team).where(Team.instance_id == instance.instance_id, Team.section_id == section.id).order_by(Team.id))).all())
            team_summaries = [await _team_summary(session, team) for team in teams]
            enrollment_count = await session.scalar(select(func.count(Enrollment.id)).where(Enrollment.section_id == section.id, Enrollment.is_active.is_(True)))
            instance_summary = None if instance is None else InstanceSummary.model_validate(instance)
            result.append(SectionSetup(
                id=section.id, section_code=section.section_code, section_name=section.section_name,
                max_teams=section.max_teams, team_size_min=section.team_size_min,
                team_size_max=section.team_size_max, is_active=section.is_active,
                instance=instance_summary, teams=team_summaries, enrollment_count=enrollment_count or 0,
            ))
        return CourseSetup(course=CourseSummary.model_validate(course), sections=result)
    except Exception as exc:
        raise _error(exc) from exc

@router.get("/casepacks", response_model=list[CasepackSummary])
async def list_casepacks(
    session: AsyncSession = Depends(get_session),
    _current_user: User = Depends(require_instructor),
):
    rows = list((await session.scalars(select(Casepack).order_by(Casepack.pack_key, Casepack.pack_version))).all())
    return [CasepackSummary(
        pack_key=row.pack_key, pack_version=row.pack_version, display_name=row.display_name,
        vertical=row.vertical, schema_version=row.schema_version, rounds=row.rounds,
        pack_digest=row.pack_digest, registered_at=row.registered_at,
        errors=(row.validation_json or {}).get("errors", []),
        warnings=(row.validation_json or {}).get("warnings", []),
        exit_code=(row.validation_json or {}).get("exit_code", 1),
    ) for row in rows]


async def _section_instance_for_instructor(session: AsyncSession, section_id: int, current_user: User) -> tuple[Section, SimulationInstance]:
    section = await authorize_section(session, current_user, section_id)
    instance = await session.scalar(select(SimulationInstance).where(SimulationInstance.section_id == section.id))
    if instance is None:
        raise PlatformNotFound(f"Section {section_id} has no simulation instance")
    return section, instance


async def _instance_for_instructor(session: AsyncSession, instance_id: int, current_user: User) -> tuple[Section, SimulationInstance]:
    instance = await session.get(SimulationInstance, instance_id)
    if instance is None:
        raise PlatformNotFound(f"Simulation instance {instance_id} was not found")
    return await _section_instance_for_instructor(session, instance.section_id, current_user)


@router.get("/sections/{section_id}/roster", response_model=list[EnrollmentRosterRow])
async def read_roster(
    section_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_instructor),
):
    try:
        await authorize_section(session, current_user, section_id)
        rows = await EnrollmentService.list_for_section(session, section_id)
        teams = {team.id: team for team in (await session.scalars(
            select(Team).where(Team.section_id == section_id).order_by(Team.id)
        )).all()}
        counts = dict((await session.execute(
            select(Enrollment.team_id, func.count(Enrollment.id)).where(
                Enrollment.section_id == section_id, Enrollment.is_active.is_(True), Enrollment.team_id.is_not(None)
            ).group_by(Enrollment.team_id)
        )).all())
        users = {user.id: user for user in (await session.scalars(select(User).where(User.id.in_([row.user_id for row in rows])))).all()} if rows else {}
        return [EnrollmentRosterRow(
            enrollment_id=row.id, user_id=row.user_id, student_id=users[row.user_id].student_id,
            name=users[row.user_id].name, email=users[row.user_id].email, role=row.role,
            is_active=row.is_active,
            team=None if row.team_id is None or row.team_id not in teams else TeamSummary(
                id=teams[row.team_id].id, name=teams[row.team_id].name, member_count=counts.get(row.team_id, 0)
            ),
        ) for row in rows]
    except Exception as exc:
        raise _error(exc) from exc


@router.get("/instances/{instance_id}/teams", response_model=list[TeamOut])
async def read_teams(
    instance_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_instructor),
):
    try:
        section, instance = await _instance_for_instructor(session, instance_id, current_user)
        teams = await TeamService.list_for_instance(session, instance.instance_id, section.id)
        return [await _team_out(session, team) for team in teams]
    except Exception as exc:
        raise _error(exc) from exc


@router.patch("/instances/{instance_id}/teams/{team_id}", response_model=TeamOut)
async def rename_team(
    instance_id: int,
    team_id: int,
    payload: TeamRename,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_instructor),
):
    try:
        section, _instance = await _instance_for_instructor(session, instance_id, current_user)
        row = await TeamService.rename(session, team_id, instance_id=instance_id, section_id=section.id, name=payload.name)
        await session.commit()
        return await _team_out(session, row)
    except Exception as exc:
        await session.rollback()
        raise _error(exc) from exc


@router.patch("/sections/{section_id}/enrollments/{enrollment_id}", response_model=dict)
async def assign_enrollment_team(
    section_id: int,
    enrollment_id: int,
    payload: EnrollmentPatch,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_instructor),
):
    try:
        await authorize_section(session, current_user, section_id)
        row = await EnrollmentService.assign_team(session, enrollment_id, section_id=section_id, team_id=payload.team_id)
        await session.commit()
        return {"enrollment_id": row.id, "section_id": row.section_id, "team_id": row.team_id}
    except Exception as exc:
        await session.rollback()
        raise _error(exc) from exc


@router.patch("/instances/{instance_id}/settings", response_model=dict)
async def update_instance_settings(
    instance_id: int,
    payload: SettingsPatchIn,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_instructor),
):
    try:
        _section, instance = await _instance_for_instructor(session, instance_id, current_user)
        updates = payload.model_dump(exclude_none=True)
        if not updates:
            raise PlatformConflict("No settings fields provided")
        if "default_round_duration_hours" in updates:
            if updates["default_round_duration_hours"] <= 0:
                raise PlatformConflict("default_round_duration_hours must be positive")
        if "grace_period_minutes" in updates:
            if updates["grace_period_minutes"] < 0:
                raise PlatformConflict("grace_period_minutes must be non-negative")
        if "lock_warning_minutes" in updates:
            if updates["lock_warning_minutes"] < 0:
                raise PlatformConflict("lock_warning_minutes must be non-negative")
        settings = dict(instance.settings) if instance.settings else {}
        settings.update(updates)
        instance.settings = settings
        await session.commit()
        return settings
    except Exception as exc:
        await session.rollback()
        raise _error(exc) from exc


# ---------------------------------------------------------------------------
# M5.4 — Monitoring dashboard response models
# ---------------------------------------------------------------------------

_SCORECARD_DIMENSIONS = ("financial", "customer", "internal_process", "learning_growth")


class MonitoringScorecard(BaseModel):
    financial: float | None = None
    customer: float | None = None
    internal_process: float | None = None
    learning_growth: float | None = None


class CapitalDistribution(BaseModel):
    min: int | None = None
    max: int | None = None
    mean: int | None = None


class MonitoringSummary(BaseModel):
    teams_by_status: dict[str, int] = Field(default_factory=dict)
    average_scorecard: MonitoringScorecard = Field(default_factory=MonitoringScorecard)
    total_open_signals: int = 0
    capital_distribution: CapitalDistribution = Field(default_factory=CapitalDistribution)


class MonitoringTeam(BaseModel):
    team_id: int
    team_name: str
    current_round: int
    status: str
    scorecard: MonitoringScorecard | None = None
    open_signals_count: int = 0
    capital_remaining: int | None = None
    last_activity_at: datetime | None = None


class AttentionAlert(BaseModel):
    team_id: int
    team_name: str
    reason: str


class MonitoringOut(BaseModel):
    instance_id: int
    instance_status: str
    current_round: int
    total_rounds: int
    summary: MonitoringSummary = Field(default_factory=MonitoringSummary)
    teams: list[MonitoringTeam] = Field(default_factory=list)
    attention: list[AttentionAlert] = Field(default_factory=list)


class ProgressionRoundScorecard(BaseModel):
    round: int
    scorecard: MonitoringScorecard


class ProgressionTeam(BaseModel):
    team_id: int
    team_name: str
    rounds: list[ProgressionRoundScorecard] = Field(default_factory=list)


class ProgressionOut(BaseModel):
    teams: list[ProgressionTeam] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# M5.4 — Monitoring helpers
# ---------------------------------------------------------------------------

def _number(value: Any) -> int | float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value


def _scorecard_from_payload(payload: Mapping[str, Any] | None) -> MonitoringScorecard | None:
    values = payload.get("scorecard") if isinstance(payload, Mapping) else None
    if not isinstance(values, Mapping):
        return None
    result = {dim: _number(values.get(dim)) for dim in _SCORECARD_DIMENSIONS}
    if all(v is None for v in result.values()):
        return None
    return MonitoringScorecard(**result)


async def _team_monitoring_data(
    session: AsyncSession, instance: SimulationInstance, team: Team,
) -> tuple[MonitoringTeam, list[str]]:
    """Build per-team monitoring row and collect attention reasons."""
    current_round = max(instance.current_round, 1)
    status = "uninitialized"
    scorecard: MonitoringScorecard | None = None
    capital_remaining: int | None = None
    open_signals_count = 0
    last_activity_at: datetime | None = None
    has_critical_signal = False

    # Latest round result for scorecard
    result = await session.scalar(
        select(RoundResult)
        .where(RoundResult.instance_id == instance.instance_id, RoundResult.team_id == team.id)
        .order_by(desc(RoundResult.round))
        .limit(1)
    )
    payload = result.payload if result is not None and isinstance(result.payload, Mapping) else None
    scorecard = _scorecard_from_payload(payload)

    # Try modern SimulationRunV1 first
    run = await session.get(SimulationRunV1, (instance.instance_id, team.id))
    if run is not None:
        current_round = max(int(run.current_round), 1)
        status = run.status
        checkpoint = await session.get(SimulationCheckpointV1, (instance.instance_id, team.id, run.advanced_round))
        state = checkpoint.state if checkpoint is not None and isinstance(checkpoint.state, Mapping) else {}
        capital_remaining = _number(state.get("capital_balance"))
        if isinstance(capital_remaining, float):
            capital_remaining = int(capital_remaining)
        # Count open signals from checkpoint state ledger
        signal_ledger = state.get("signal_ledger", []) if isinstance(state.get("signal_ledger"), list) else []
        for sig in signal_ledger:
            if isinstance(sig, Mapping) and sig.get("status") == "open":
                open_signals_count += 1
                if sig.get("severity") == "critical":
                    has_critical_signal = True
    else:
        # Fall back to legacy TeamStateRow
        team_state = await session.get(TeamStateRow, (instance.instance_id, team.id))
        if team_state is not None:
            current_round = max(int(team_state.current_round), 1)
            status = "locked" if team_state.locked_round and team_state.locked_round >= team_state.current_round else "active"
            capital_remaining = int(team_state.cash)

    # Count open signals from signal table as well / fallback
    if open_signals_count == 0:
        signal_rows = list((await session.scalars(select(SignalRow).where(
            SignalRow.instance_id == instance.instance_id,
            SignalRow.team_id == team.id,
            SignalRow.status == "open",
        ))).all())
        open_signals_count = len(signal_rows)
        has_critical_signal = has_critical_signal or any(s.severity == "critical" for s in signal_rows)

    # Count open signals from payload as another fallback
    if open_signals_count == 0 and isinstance(payload, Mapping):
        signals_data = payload.get("signals")
        if isinstance(signals_data, Mapping):
            open_list = signals_data.get("open") or []
            if isinstance(open_list, list):
                open_signals_count = len(open_list)
                has_critical_signal = has_critical_signal or any(
                    isinstance(s, Mapping) and s.get("severity") == "critical" for s in open_list
                )

    team_row = MonitoringTeam(
        team_id=team.id,
        team_name=team.name,
        current_round=current_round,
        status=status,
        scorecard=scorecard,
        open_signals_count=open_signals_count,
        capital_remaining=capital_remaining,
        last_activity_at=last_activity_at,
    )

    # Build attention reasons
    reasons: list[str] = []
    if capital_remaining is not None and capital_remaining <= 0:
        reasons.append("zero_capital")
    if current_round < max(instance.current_round, 1):
        reasons.append("behind_round")
    if has_critical_signal:
        reasons.append("critical_signals")

    return team_row, reasons


# ---------------------------------------------------------------------------
# M5.4 — Monitoring routes
# ---------------------------------------------------------------------------

@router.get("/instructor/instances/{instance_id}/monitoring", response_model=MonitoringOut)
async def read_monitoring(
    instance_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_instructor),
):
    try:
        _section, instance = await _instance_for_instructor(session, instance_id, current_user)
        teams = list((await session.scalars(
            select(Team).where(Team.instance_id == instance.instance_id).order_by(Team.id)
        )).all())

        team_rows: list[MonitoringTeam] = []
        attention_alerts: list[AttentionAlert] = []
        status_counts: dict[str, int] = {}
        scorecard_accumulators: dict[str, list[float]] = {dim: [] for dim in _SCORECARD_DIMENSIONS}
        capital_values: list[int] = []
        total_open_signals = 0

        for team in teams:
            team_row, reasons = await _team_monitoring_data(session, instance, team)
            team_rows.append(team_row)

            # Accumulate status counts
            status_counts[team_row.status] = status_counts.get(team_row.status, 0) + 1

            # Accumulate scorecard values for averaging
            if team_row.scorecard is not None:
                for dim in _SCORECARD_DIMENSIONS:
                    val = getattr(team_row.scorecard, dim)
                    if val is not None:
                        scorecard_accumulators[dim].append(val)

            # Accumulate capital
            if team_row.capital_remaining is not None:
                capital_values.append(team_row.capital_remaining)

            total_open_signals += team_row.open_signals_count

            # Build attention alerts
            for reason in reasons:
                attention_alerts.append(AttentionAlert(
                    team_id=team.id, team_name=team.name, reason=reason,
                ))

        # Average scorecard
        avg_scorecard = MonitoringScorecard(**{
            dim: (round(sum(vals) / len(vals), 4) if vals else None)
            for dim, vals in scorecard_accumulators.items()
        })

        # Capital distribution
        capital_dist = CapitalDistribution()
        if capital_values:
            capital_dist = CapitalDistribution(
                min=min(capital_values),
                max=max(capital_values),
                mean=int(sum(capital_values) / len(capital_values)),
            )

        return MonitoringOut(
            instance_id=instance.instance_id,
            instance_status=instance.status,
            current_round=max(instance.current_round, 1),
            total_rounds=instance.total_rounds,
            summary=MonitoringSummary(
                teams_by_status=status_counts,
                average_scorecard=avg_scorecard,
                total_open_signals=total_open_signals,
                capital_distribution=capital_dist,
            ),
            teams=team_rows,
            attention=attention_alerts,
        )
    except Exception as exc:
        raise _error(exc) from exc


@router.get("/instructor/instances/{instance_id}/monitoring/progression", response_model=ProgressionOut)
async def read_monitoring_progression(
    instance_id: int,
    team_ids: str = Query(default=""),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_instructor),
):
    try:
        _section, instance = await _instance_for_instructor(session, instance_id, current_user)

        # Parse team_ids from comma-separated string
        requested_ids: list[int] = []
        if team_ids.strip():
            for part in team_ids.split(","):
                part = part.strip()
                if part:
                    requested_ids.append(int(part))

        # If no team_ids given, return all teams
        if not requested_ids:
            teams = list((await session.scalars(
                select(Team).where(Team.instance_id == instance.instance_id).order_by(Team.id)
            )).all())
        else:
            teams = list((await session.scalars(
                select(Team).where(
                    Team.instance_id == instance.instance_id,
                    Team.id.in_(requested_ids),
                ).order_by(Team.id)
            )).all())

        progression_teams: list[ProgressionTeam] = []
        for team in teams:
            results = list((await session.scalars(
                select(RoundResult)
                .where(RoundResult.instance_id == instance.instance_id, RoundResult.team_id == team.id)
                .order_by(RoundResult.round)
            )).all())

            rounds: list[ProgressionRoundScorecard] = []
            for result in results:
                payload = result.payload if isinstance(result.payload, Mapping) else None
                sc = _scorecard_from_payload(payload)
                if sc is not None:
                    rounds.append(ProgressionRoundScorecard(round=result.round, scorecard=sc))

            progression_teams.append(ProgressionTeam(
                team_id=team.id, team_name=team.name, rounds=rounds,
            ))

        return ProgressionOut(teams=progression_teams)
    except Exception as exc:
        raise _error(exc) from exc


# ---------------------------------------------------------------------------
# M5.5 — Grading and CSV export
# ---------------------------------------------------------------------------

class GradeConfigIn(BaseModel):
    weight_financial: float
    weight_customer: float
    weight_internal_process: float
    weight_learning_growth: float
    rounds_mode: str = "final"


class GradeOverrideIn(BaseModel):
    override: float | None = None
    reason: str | None = Field(default=None, max_length=256)


@router.get("/instructor/instances/{instance_id}/grades")
async def read_grades(
    instance_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_instructor),
):
    try:
        await _instance_for_instructor(session, instance_id, current_user)
        from app.services.grading import get_team_grades
        return await get_team_grades(session, instance_id)
    except Exception as exc:
        raise _error(exc) from exc


@router.put("/instructor/instances/{instance_id}/grades/config")
async def update_grade_config(
    instance_id: int,
    payload: GradeConfigIn,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_instructor),
):
    try:
        await _instance_for_instructor(session, instance_id, current_user)
        from app.services.grading import validate_weights
        from app.models.grading import GradeConfig

        # Validate rounds_mode
        if payload.rounds_mode not in ("final", "average"):
            raise HTTPException(status_code=422, detail="rounds_mode must be 'final' or 'average'")

        # Validate weights
        error = validate_weights(
            payload.weight_financial, payload.weight_customer,
            payload.weight_internal_process, payload.weight_learning_growth,
        )
        if error:
            raise HTTPException(status_code=422, detail=error)

        row = await session.get(GradeConfig, instance_id)
        if row is None:
            row = GradeConfig(
                instance_id=instance_id,
                weight_financial=payload.weight_financial,
                weight_customer=payload.weight_customer,
                weight_internal_process=payload.weight_internal_process,
                weight_learning_growth=payload.weight_learning_growth,
                rounds_mode=payload.rounds_mode,
                updated_by=current_user.id,
            )
            session.add(row)
        else:
            row.weight_financial = payload.weight_financial
            row.weight_customer = payload.weight_customer
            row.weight_internal_process = payload.weight_internal_process
            row.weight_learning_growth = payload.weight_learning_growth
            row.rounds_mode = payload.rounds_mode
            row.updated_by = current_user.id
        await session.commit()
        return {
            "weight_financial": row.weight_financial,
            "weight_customer": row.weight_customer,
            "weight_internal_process": row.weight_internal_process,
            "weight_learning_growth": row.weight_learning_growth,
            "rounds_mode": row.rounds_mode,
        }
    except HTTPException:
        raise
    except Exception as exc:
        await session.rollback()
        raise _error(exc) from exc


@router.put("/instructor/instances/{instance_id}/grades/teams/{team_id}")
async def update_grade_override(
    instance_id: int,
    team_id: int,
    payload: GradeOverrideIn,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_instructor),
):
    try:
        await _instance_for_instructor(session, instance_id, current_user)
        from app.models.grading import GradeOverride

        # Verify team belongs to this instance
        team = await session.scalar(
            select(Team).where(Team.id == team_id, Team.instance_id == instance_id)
        )
        if team is None:
            raise PlatformNotFound(f"Team {team_id} was not found in instance {instance_id}")

        row = await session.get(GradeOverride, (instance_id, team_id))
        if row is None:
            row = GradeOverride(
                instance_id=instance_id,
                team_id=team_id,
                override=payload.override,
                reason=payload.reason,
                updated_by=current_user.id,
            )
            session.add(row)
        else:
            row.override = payload.override
            row.reason = payload.reason
            row.updated_by = current_user.id
        await session.commit()
        return {
            "instance_id": instance_id,
            "team_id": team_id,
            "override": float(row.override) if row.override is not None else None,
            "reason": row.reason,
        }
    except HTTPException:
        raise
    except Exception as exc:
        await session.rollback()
        raise _error(exc) from exc


@router.get("/instructor/instances/{instance_id}/grades/export")
async def export_grades(
    instance_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_instructor),
):
    try:
        await _instance_for_instructor(session, instance_id, current_user)
        from app.services.grading import export_csv
        from fastapi.responses import Response

        csv_content, filename = await export_csv(session, instance_id)
        return Response(
            content=csv_content.encode("utf-8"),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        raise _error(exc) from exc


# ---------------------------------------------------------------------------
# M5.7 — Clone, archive, and reset lifecycle operations
# ---------------------------------------------------------------------------

class CloneIn(BaseModel):
    section_code: str | None = None
    section_name: str | None = None


class CloneOut(BaseModel):
    section: SectionSetup
    message: str


class ConfirmIn(BaseModel):
    confirm_instance_id: int


class LifecycleOut(BaseModel):
    instance: InstanceSummary
    message: str


@router.post("/instructor/sections/{section_id}/clone", response_model=CloneOut)
async def clone_section_route(
    section_id: int,
    payload: CloneIn | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_instructor),
):
    try:
        await _section_instance_for_instructor(session, section_id, current_user)
        new_section = await clone_section(
            session,
            section_id,
            new_section_code=payload.section_code if payload else None,
            new_section_name=payload.section_name if payload else None,
        )
        await session.commit()
        # Build the SectionSetup response for the new section
        new_instance = await session.scalar(
            select(SimulationInstance).where(SimulationInstance.section_id == new_section.id)
        )
        new_teams = list((await session.scalars(
            select(Team).where(
                Team.instance_id == new_instance.instance_id,
                Team.section_id == new_section.id,
            ).order_by(Team.id)
        )).all())
        team_summaries = [await _team_summary(session, t) for t in new_teams]
        enrollment_count = await session.scalar(
            select(func.count(Enrollment.id)).where(
                Enrollment.section_id == new_section.id,
                Enrollment.is_active.is_(True),
            )
        )
        section_setup = SectionSetup(
            id=new_section.id,
            section_code=new_section.section_code,
            section_name=new_section.section_name,
            max_teams=new_section.max_teams,
            team_size_min=new_section.team_size_min,
            team_size_max=new_section.team_size_max,
            is_active=new_section.is_active,
            instance=InstanceSummary.model_validate(new_instance),
            teams=team_summaries,
            enrollment_count=enrollment_count or 0,
        )
        return CloneOut(section=section_setup, message="Section cloned successfully.")
    except Exception as exc:
        await session.rollback()
        raise _error(exc) from exc


@router.post("/instructor/instances/{instance_id}/archive", response_model=LifecycleOut)
async def archive_instance_route(
    instance_id: int,
    payload: ConfirmIn,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_instructor),
):
    if payload.confirm_instance_id != instance_id:
        raise HTTPException(
            status_code=422,
            detail=f"Confirmation mismatch: expected {instance_id}, got {payload.confirm_instance_id}",
        )
    try:
        await _instance_for_instructor(session, instance_id, current_user)
        instance = await archive_instance(session, instance_id)
        await session.commit()
        return LifecycleOut(
            instance=InstanceSummary.model_validate(instance),
            message="Instance archived successfully.",
        )
    except Exception as exc:
        await session.rollback()
        raise _error(exc) from exc


@router.post("/instructor/instances/{instance_id}/reset", response_model=LifecycleOut)
async def reset_instance_route(
    instance_id: int,
    payload: ConfirmIn,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_instructor),
):
    if payload.confirm_instance_id != instance_id:
        raise HTTPException(
            status_code=422,
            detail=f"Confirmation mismatch: expected {instance_id}, got {payload.confirm_instance_id}",
        )
    try:
        await _instance_for_instructor(session, instance_id, current_user)
        instance = await reset_instance(session, instance_id)
        await session.commit()
        return LifecycleOut(
            instance=InstanceSummary.model_validate(instance),
            message="Instance reset successfully. All runtime state has been cleared.",
        )
    except Exception as exc:
        await session.rollback()
        raise _error(exc) from exc
