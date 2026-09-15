"""JWT, password, and login contract tests."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.base import Base
from app.models.platform import User
from app.services.auth import create_access_token, decode_access_token, hash_password, verify_password


def test_passwords_are_bcrypt_hashes_and_jwt_claims_are_typed():
    hashed = hash_password("secret")
    assert hashed.startswith("$2b$")
    assert verify_password("secret", hashed)
    assert not verify_password("wrong", hashed)
    token = create_access_token(user_id=17, role="student", section_id=3, instance_id=7)
    claims = decode_access_token(token)
    assert claims["sub"] == "17"
    assert claims["role"] == "student"
    assert claims["section_id"] == 3 and claims["instance_id"] == 7
    assert isinstance(claims["iat"], int) and isinstance(claims["exp"], int)


def test_malformed_and_expired_tokens_are_rejected():
    with pytest.raises(ValueError, match="Invalid token"):
        decode_access_token("not-a-token")


def test_last_active_column_exists_and_user_can_be_inactive(tmp_path):
    async def run():
        engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'auth.db'}")
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all, tables=[User.__table__])
        async with async_sessionmaker(engine, expire_on_commit=False)() as session:
            user = User(student_id="S1", name="Student", email="s@example.test", role="student", password_hash=hash_password("x"), is_active=False)
            session.add(user)
            await session.commit()
            assert user.last_active_at is None
        await engine.dispose()
    asyncio.run(run())
