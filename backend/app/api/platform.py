"""Unprotected M2 hierarchy CRUD routes; authentication arrives in packet 2.4."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.platform import Course, Enrollment, Section, SimulationInstance, Team
from app.services.platform import (
    CourseService,
    DeletionBlocked,
    EnrollmentService,
    InstanceService,
    PlatformConflict,
    PlatformNotFound,
    SectionService,
    TeamService,
)

router = APIRouter(tags=["platform"])


async def get_session():
    async with async_session() as session:
        yield session


class CourseIn(BaseModel):
    course_code: str
    course_name: str
    academic_year: str
    semester: str
    instructor_id: int
    active_chapters: list[int] = Field(default_factory=lambda: list(range(1, 13)))
    is_active: bool = True


class SectionIn(BaseModel):
    section_code: str
    section_name: str
    max_teams: int = 8
    team_size_min: int = 2
    team_size_max: int = 6
    is_active: bool = True


class InstanceIn(BaseModel):
    pack_key: str
    pack_version: str
    current_round: int = 0
    total_rounds: int = 6
    status: str = "setup"
    settings: dict = Field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None


class TeamIn(BaseModel):
    section_id: int
    name: str
    created_by: int | None = None


class EnrollmentIn(BaseModel):
    user_id: int
    team_id: int | None = None
    role: str = "student"
    is_active: bool = True


class RowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CourseOut(RowOut):
    id: int
    course_code: str
    course_name: str
    academic_year: str
    semester: str
    instructor_id: int
    active_chapters: list[int]
    is_active: bool


class SectionOut(RowOut):
    id: int
    course_id: int
    section_code: str
    section_name: str
    max_teams: int
    team_size_min: int
    team_size_max: int
    is_active: bool


class InstanceOut(RowOut):
    instance_id: int
    section_id: int
    pack_key: str
    pack_version: str
    current_round: int
    total_rounds: int
    status: str
    settings: dict
    started_at: datetime | None
    completed_at: datetime | None


class TeamOut(RowOut):
    id: int
    section_id: int
    instance_id: int
    name: str
    created_by: int | None


class EnrollmentOut(RowOut):
    id: int
    user_id: int
    section_id: int
    team_id: int | None
    role: str
    enrolled_at: datetime
    is_active: bool


def _error(exc: Exception) -> HTTPException:
    if isinstance(exc, PlatformNotFound):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, (PlatformConflict, DeletionBlocked)):
        return HTTPException(status_code=409, detail=str(exc))
    return HTTPException(status_code=400, detail=str(exc))


@router.post("/courses", response_model=CourseOut, status_code=201)
async def create_course(payload: CourseIn, session: AsyncSession = Depends(get_session)):
    try:
        row = await CourseService.create(session, **payload.model_dump())
        await session.commit()
        return row
    except Exception as exc:
        await session.rollback()
        raise _error(exc) from exc


@router.get("/courses/{course_id}", response_model=CourseOut)
async def read_course(course_id: int, session: AsyncSession = Depends(get_session)):
    try:
        return await CourseService.read(session, course_id)
    except Exception as exc:
        raise _error(exc) from exc


@router.post("/courses/{course_id}/sections", response_model=SectionOut, status_code=201)
async def create_section(course_id: int, payload: SectionIn, session: AsyncSession = Depends(get_session)):
    try:
        row = await SectionService.create(session, course_id, **payload.model_dump())
        await session.commit()
        return row
    except Exception as exc:
        await session.rollback()
        raise _error(exc) from exc


@router.get("/sections/{section_id}", response_model=SectionOut)
async def read_section(section_id: int, session: AsyncSession = Depends(get_session)):
    try:
        return await SectionService.read(session, section_id)
    except Exception as exc:
        raise _error(exc) from exc


@router.post("/sections/{section_id}/instance", response_model=InstanceOut, status_code=201)
async def create_instance(section_id: int, payload: InstanceIn, session: AsyncSession = Depends(get_session)):
    try:
        row = await InstanceService.create(session, section_id, **payload.model_dump())
        await session.commit()
        return row
    except Exception as exc:
        await session.rollback()
        raise _error(exc) from exc


@router.get("/instances/{instance_id}", response_model=InstanceOut)
async def read_instance(instance_id: int, session: AsyncSession = Depends(get_session)):
    try:
        return await InstanceService.read(session, instance_id)
    except Exception as exc:
        raise _error(exc) from exc


@router.post("/instances/{instance_id}/teams", response_model=TeamOut, status_code=201)
async def create_team(instance_id: int, payload: TeamIn, session: AsyncSession = Depends(get_session)):
    try:
        row = await TeamService.create(session, instance_id, **payload.model_dump())
        await session.commit()
        return row
    except Exception as exc:
        await session.rollback()
        raise _error(exc) from exc


@router.post("/sections/{section_id}/enrollments", response_model=EnrollmentOut, status_code=201)
async def create_enrollment(section_id: int, payload: EnrollmentIn, session: AsyncSession = Depends(get_session)):
    try:
        row = await EnrollmentService.create(session, section_id, **payload.model_dump())
        await session.commit()
        return row
    except Exception as exc:
        await session.rollback()
        raise _error(exc) from exc
