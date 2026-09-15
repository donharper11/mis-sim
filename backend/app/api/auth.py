"""Login and authenticated identity endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.models.platform import Course, Enrollment, Section, SimulationInstance, User
from app.services.auth import authenticate_user, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    student_id: str
    password: str
    section_id: int | None = None


class StaffLoginRequest(BaseModel):
    email: str
    password: str
    section_id: int | None = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: str
    section_id: int | None = None
    instance_id: int | None = None


class UserResponse(BaseModel):
    id: int
    student_id: str | None
    name: str
    email: str
    role: str
    section_id: int | None = None
    instance_id: int | None = None


def _invalid_credentials() -> HTTPException:
    return HTTPException(status_code=401, detail="Invalid credentials")


class MultipleEnrollment(Exception):
    def __init__(self, sections: list[dict]):
        self.sections = sections


async def _contexts(session: AsyncSession, user: User) -> list[dict]:
    rows = (await session.execute(
        select(Section, SimulationInstance).join(SimulationInstance, SimulationInstance.section_id == Section.id)
        .join(Enrollment, Enrollment.section_id == Section.id)
        .where(Enrollment.user_id == user.id, Enrollment.role == user.role, Enrollment.is_active.is_(True))
        .order_by(Section.id)
    )).all()
    return [{"section_id": section.id, "section_name": section.section_name, "instance_id": instance.instance_id} for section, instance in rows]


async def _context_for(session: AsyncSession, user: User, section_id: int | None) -> tuple[int | None, int | None]:
    contexts = await _contexts(session, user)
    if user.role == "student":
        if section_id is None:
            if len(contexts) > 1:
                raise MultipleEnrollment(contexts)
            selected = contexts[0] if contexts else None
        else:
            selected = next((item for item in contexts if item["section_id"] == section_id), None)
            if selected is None:
                raise HTTPException(status_code=403, detail="Section selection is not available")
    elif section_id is None:
        return None, None
    else:
        section = await session.get(Section, section_id)
        if section is None:
            raise HTTPException(status_code=403, detail="Section selection is not available")
        if user.role == "ta":
            selected = next((item for item in contexts if item["section_id"] == section_id), None)
        elif user.role == "instructor":
            owned = await session.scalar(select(Course.id).where(Course.id == section.course_id, Course.instructor_id == user.id))
            instance = await session.scalar(select(SimulationInstance).where(SimulationInstance.section_id == section_id))
            selected = {"section_id": section_id, "instance_id": instance.instance_id} if owned and instance else None
        else:
            instance = await session.scalar(select(SimulationInstance).where(SimulationInstance.section_id == section_id))
            selected = {"section_id": section_id, "instance_id": instance.instance_id} if section.is_active and instance else None
        if selected is None:
            raise HTTPException(status_code=403, detail="Section selection is not available")
    return (selected or {}).get("section_id"), (selected or {}).get("instance_id")


async def _issue(session: AsyncSession, user: User, section_id: int | None) -> AuthResponse:
    selected_section, instance_id = await _context_for(session, user, section_id)
    user.last_active_at = datetime.now(timezone.utc)
    token = create_access_token(user_id=user.id, role=user.role, section_id=selected_section, instance_id=instance_id)
    await session.commit()
    return AuthResponse(access_token=token, user_id=user.id, role=user.role, section_id=selected_section, instance_id=instance_id)


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_session)):
    user = await authenticate_user(session, payload.student_id, payload.password, staff=False)
    if user is None:
        raise _invalid_credentials()
    try:
        return await _issue(session, user, payload.section_id)
    except MultipleEnrollment as exc:
        return JSONResponse(status_code=409, content={"detail": "Select a section", "sections": exc.sections})


@router.post("/staff-login", response_model=AuthResponse)
async def staff_login(payload: StaffLoginRequest, session: AsyncSession = Depends(get_session)):
    user = await authenticate_user(session, payload.email, payload.password, staff=True)
    if user is None:
        raise _invalid_credentials()
    if user.role == "student":
        raise HTTPException(status_code=403, detail="This login is for instructors and TAs only")
    return await _issue(session, user, payload.section_id)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    claims = getattr(current_user, "_auth_claims", {})
    return UserResponse(
        id=current_user.id, student_id=current_user.student_id, name=current_user.name,
        email=current_user.email, role=current_user.role,
        section_id=claims.get("section_id"), instance_id=claims.get("instance_id"),
    )
