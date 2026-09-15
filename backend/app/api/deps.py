"""Bearer authentication and platform context authorization dependencies."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.platform import Course, Enrollment, Section, SimulationInstance, User
from app.services.auth import decode_access_token

bearer = HTTPBearer(auto_error=False)


async def get_session():
    async with async_session() as session:
        yield session


def _unauthenticated(detail: str = "Invalid token") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, headers={"WWW-Authenticate": "Bearer"})


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: AsyncSession = Depends(get_session),
) -> User:
    if credentials is None:
        raise _unauthenticated()
    try:
        claims = decode_access_token(credentials.credentials)
        user_id = int(claims["sub"])
    except (ValueError, TypeError, KeyError):
        raise _unauthenticated() from None
    user = await session.get(User, user_id)
    if user is None or not user.is_active or user.role != claims.get("role"):
        raise _unauthenticated()
    # Dependencies expose claims to route helpers without trusting claims for identity.
    user._auth_claims = claims  # type: ignore[attr-defined]
    return user


def _claims(user: User) -> dict:
    return getattr(user, "_auth_claims", {})


async def _instance(session: AsyncSession, instance_id: int) -> SimulationInstance:
    instance = await session.get(SimulationInstance, instance_id)
    if instance is None:
        raise HTTPException(status_code=404, detail=f"Simulation instance {instance_id} was not found")
    return instance


async def get_current_instance(
    instance_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SimulationInstance:
    instance = await _instance(session, instance_id)
    claims = _claims(current_user)
    selected_section = claims.get("section_id")
    selected_instance = claims.get("instance_id")
    if selected_section is not None and selected_section != instance.section_id:
        raise HTTPException(status_code=403, detail="Access to this instance is forbidden")
    if selected_instance is not None and selected_instance != instance.instance_id:
        raise HTTPException(status_code=403, detail="Access to this instance is forbidden")
    if current_user.role == "admin":
        return instance
    if current_user.role == "student":
        allowed = await session.scalar(select(Enrollment.id).where(
            Enrollment.user_id == current_user.id, Enrollment.section_id == instance.section_id,
            Enrollment.role == "student", Enrollment.is_active.is_(True),
        ))
    elif current_user.role == "ta":
        allowed = await session.scalar(select(Enrollment.id).where(
            Enrollment.user_id == current_user.id, Enrollment.section_id == instance.section_id,
            Enrollment.role == "ta", Enrollment.is_active.is_(True),
        ))
    else:
        allowed = await session.scalar(select(Section.id).join(Course, Course.id == Section.course_id).where(
            Section.id == instance.section_id, Course.instructor_id == current_user.id,
        ))
    if allowed is None:
        raise HTTPException(status_code=403, detail="Access to this instance is forbidden")
    return instance


async def require_instructor(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in {"instructor", "admin"}:
        raise HTTPException(status_code=403, detail="Instructor access required")
    return current_user


async def require_instructor_or_ta(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in {"instructor", "ta", "admin"}:
        raise HTTPException(status_code=403, detail="Instructor or TA access required")
    return current_user


async def authorize_section(session: AsyncSession, user: User, section_id: int) -> Section:
    section = await session.get(Section, section_id)
    if section is None:
        raise HTTPException(status_code=404, detail=f"Section {section_id} was not found")
    claims = _claims(user)
    if claims.get("section_id") is not None and claims["section_id"] != section_id:
        raise HTTPException(status_code=403, detail="Access to this section is forbidden")
    if user.role == "admin":
        return section
    if user.role == "instructor":
        allowed = await session.scalar(select(Course.id).where(Course.id == section.course_id, Course.instructor_id == user.id))
    else:
        allowed = await session.scalar(select(Enrollment.id).where(
            Enrollment.user_id == user.id, Enrollment.section_id == section_id,
            Enrollment.role == user.role, Enrollment.is_active.is_(True),
        ))
    if allowed is None:
        raise HTTPException(status_code=403, detail="Access to this section is forbidden")
    return section


async def authorize_course(session: AsyncSession, user: User, course_id: int) -> Course:
    course = await session.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail=f"Course {course_id} was not found")
    if user.role == "admin":
        return course
    selected_section = _claims(user).get("section_id")
    if selected_section is not None:
        selected_course = await session.scalar(select(Section.course_id).where(Section.id == selected_section))
        if selected_course != course_id:
            raise HTTPException(status_code=403, detail="Access to this course is forbidden")
    if user.role == "instructor":
        allowed = course.instructor_id == user.id
    else:
        allowed = (await session.scalar(select(Enrollment.id).join(Section, Section.id == Enrollment.section_id).where(
            Enrollment.user_id == user.id, Enrollment.role == user.role,
            Enrollment.is_active.is_(True), Section.course_id == course_id,
        ))) is not None
    if not allowed:
        raise HTTPException(status_code=403, detail="Access to this course is forbidden")
    return course
