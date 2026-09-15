"""Password and bearer-token operations for the platform authentication boundary."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.platform import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    return bool(password_hash) and pwd_context.verify(password, password_hash)


def create_access_token(*, user_id: int, role: str, section_id: int | None = None, instance_id: int | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id), "role": role, "section_id": section_id,
        "instance_id": instance_id, "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
    if not isinstance(payload, dict):
        raise ValueError("Invalid token")
    if not isinstance(payload.get("sub"), str) or not payload["sub"].isdigit():
        raise ValueError("Invalid token")
    if not isinstance(payload.get("role"), str) or payload["role"] not in {"student", "ta", "instructor", "admin"}:
        raise ValueError("Invalid token")
    if not isinstance(payload.get("exp"), int) or isinstance(payload.get("exp"), bool):
        raise ValueError("Invalid token")
    for key in ("iat", "section_id", "instance_id"):
        if key in payload and payload[key] is not None and (not isinstance(payload[key], int) or isinstance(payload[key], bool)):
            raise ValueError("Invalid token")
    return payload


async def authenticate_user(session: AsyncSession, identifier: str, password: str, *, staff: bool = False) -> User | None:
    field = User.email if staff else User.student_id
    user = await session.scalar(select(User).where(field == identifier))
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        return None
    return user
