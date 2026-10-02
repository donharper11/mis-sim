"""Admin-only casepack registry management routes (M5.6)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.casepack.registry import RegistryError, register_casepack, pack_root
from app.database import async_session
from app.models.platform import Casepack, SimulationInstance, User
from app.services.platform import PlatformConflict, PlatformNotFound


router = APIRouter(tags=["admin"])


async def get_session():
    async with async_session() as session:
        yield session


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


class RegisterRequest(BaseModel):
    pack_key: str
    pack_path: str | None = None


class RegisterResponse(BaseModel):
    pack_key: str
    pack_version: str
    pack_digest: str
    display_name: str
    vertical: str
    schema_version: int
    rounds: int
    errors: int
    warnings: int
    exit_code: int


class BoundInstanceOut(BaseModel):
    instance_id: int
    section_id: int
    pack_key: str
    pack_version: str
    status: str
    current_round: int
    total_rounds: int


@router.post("/admin/casepacks/register", response_model=RegisterResponse, status_code=201)
async def admin_register_casepack(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    path = payload.pack_path or str(pack_root() / payload.pack_key)
    try:

        def _register(sync_session):
            return register_casepack(sync_session, path, registered_by=current_user.id)

        row = await session.run_sync(_register)
        await session.commit()
    except RegistryError as exc:
        msg = str(exc)
        if "already registered" in msg:
            raise HTTPException(status_code=409, detail=msg) from exc
        raise HTTPException(status_code=400, detail=msg) from exc
    vj = row.validation_json or {}
    return RegisterResponse(
        pack_key=row.pack_key,
        pack_version=row.pack_version,
        pack_digest=row.pack_digest,
        display_name=row.display_name,
        vertical=row.vertical,
        schema_version=row.schema_version,
        rounds=row.rounds,
        errors=len(vj.get("errors", [])),
        warnings=len(vj.get("warnings", [])),
        exit_code=vj.get("exit_code", 1),
    )


@router.get("/admin/casepacks/{pack_key}/{pack_version}/validation")
async def admin_validation_report(
    pack_key: str,
    pack_version: str,
    session: AsyncSession = Depends(get_session),
    _current_user: User = Depends(require_admin),
):
    row = await session.scalar(
        select(Casepack).where(Casepack.pack_key == pack_key, Casepack.pack_version == pack_version)
    )
    if row is None:
        raise HTTPException(status_code=404, detail=f"Casepack {pack_key} {pack_version} is not registered")
    return row.validation_json or {}


@router.get("/admin/casepacks/{pack_key}/{pack_version}/instances", response_model=list[BoundInstanceOut])
async def admin_bound_instances(
    pack_key: str,
    pack_version: str,
    session: AsyncSession = Depends(get_session),
    _current_user: User = Depends(require_admin),
):
    # Verify pack exists
    row = await session.scalar(
        select(Casepack).where(Casepack.pack_key == pack_key, Casepack.pack_version == pack_version)
    )
    if row is None:
        raise HTTPException(status_code=404, detail=f"Casepack {pack_key} {pack_version} is not registered")
    instances = list(
        (await session.scalars(
            select(SimulationInstance).where(
                SimulationInstance.pack_key == pack_key,
                SimulationInstance.pack_version == pack_version,
            ).order_by(SimulationInstance.instance_id)
        )).all()
    )
    return [
        BoundInstanceOut(
            instance_id=inst.instance_id,
            section_id=inst.section_id,
            pack_key=inst.pack_key,
            pack_version=inst.pack_version,
            status=inst.status,
            current_round=inst.current_round,
            total_rounds=inst.total_rounds,
        )
        for inst in instances
    ]


@router.delete("/admin/casepacks/{pack_key}/{pack_version}")
async def admin_deregister_casepack(
    pack_key: str,
    pack_version: str,
    session: AsyncSession = Depends(get_session),
    _current_user: User = Depends(require_admin),
):
    row = await session.scalar(
        select(Casepack).where(Casepack.pack_key == pack_key, Casepack.pack_version == pack_version)
    )
    if row is None:
        raise HTTPException(status_code=404, detail=f"Casepack {pack_key} {pack_version} is not registered")
    # Check for active bound instances (status != 'archived')
    active_instances = list(
        (await session.scalars(
            select(SimulationInstance).where(
                SimulationInstance.pack_key == pack_key,
                SimulationInstance.pack_version == pack_version,
                SimulationInstance.status != "archived",
            )
        )).all()
    )
    if active_instances:
        ids = [inst.instance_id for inst in active_instances]
        raise HTTPException(
            status_code=409,
            detail=f"Cannot deregister: active instances bound to this pack: {ids}",
        )
    await session.delete(row)
    await session.commit()
    return {"status": "ok", "pack_key": pack_key, "pack_version": pack_version}
