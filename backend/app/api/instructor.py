"""Bounded M5 instructor setup and roster workspace routes.

This module exposes read models and assignment mutations for course setup.  It
does not provision accounts or touch simulation runtime state.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import authorize_course, authorize_section, get_current_user, require_instructor
from app.database import async_session
from app.models.platform import Casepack, Course, Enrollment, Section, SimulationInstance, Team, User
from app.services.platform import (
    CourseService,
    EnrollmentService,
    InstanceService,
    PlatformConflict,
    PlatformNotFound,
    TeamService,
)


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
