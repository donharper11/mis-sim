"""Host platform container CRUD — presentation-layer grouping of assets."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_instance, get_current_user, get_session
from app.models.host_platform import HostPlatform, HostPlatformMember
from app.models.platform import Enrollment, SimulationInstance, Team, User

router = APIRouter(tags=["host-platform"])


# ── Pydantic response / request models ──────────────────────────────

class MemberOut(BaseModel):
    id: int
    asset_key: str
    member_kind: str
    assigned_round: int


class HostPlatformOut(BaseModel):
    id: int
    instance_id: int
    team_id: int
    platform_code: str
    name: str
    notes: str | None = None
    platform_type: str
    cloud_subtype: str | None = None
    status: str
    created_round: int
    activated_round: int | None = None
    members: list[MemberOut] = Field(default_factory=list)


class HostPlatformListOut(BaseModel):
    platforms: list[HostPlatformOut] = Field(default_factory=list)


class CreatePlatformIn(BaseModel):
    platform_type: str
    cloud_subtype: str | None = None
    name: str = Field(min_length=1, max_length=200)
    notes: str | None = Field(default=None, max_length=1000)


class UpdatePlatformIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    notes: str | None = Field(default=None, max_length=1000)


class AddMemberIn(BaseModel):
    asset_key: str = Field(min_length=1, max_length=64)
    member_kind: str  # service | component


# ── Helpers ──────────────────────────────────────────────────────────

async def _team_for_user(
    session: AsyncSession, instance: SimulationInstance, user: User, team_id: int | None,
) -> Team | None:
    if user.role == "student":
        selected = await session.scalar(select(Enrollment.team_id).where(
            Enrollment.user_id == user.id,
            Enrollment.section_id == instance.section_id,
            Enrollment.role == "student",
            Enrollment.is_active.is_(True),
        ))
        team_id = selected
    if team_id is None:
        candidates = list((await session.scalars(select(Team).where(
            Team.instance_id == instance.instance_id,
        ).order_by(Team.id))).all())
        if len(candidates) != 1:
            return None
        return candidates[0]
    return await session.scalar(select(Team).where(
        Team.instance_id == instance.instance_id, Team.id == team_id,
    ))


def _serialize(platform: HostPlatform) -> HostPlatformOut:
    return HostPlatformOut(
        id=platform.id,
        instance_id=platform.instance_id,
        team_id=platform.team_id,
        platform_code=platform.platform_code,
        name=platform.name,
        notes=platform.notes,
        platform_type=platform.platform_type,
        cloud_subtype=platform.cloud_subtype,
        status=platform.status,
        created_round=platform.created_round,
        activated_round=platform.activated_round,
        members=[
            MemberOut(id=m.id, asset_key=m.asset_key, member_kind=m.member_kind, assigned_round=m.assigned_round)
            for m in platform.members
        ],
    )


async def _list_platforms(session: AsyncSession, instance_id: int, team_id: int) -> list[HostPlatformOut]:
    result = await session.scalars(
        select(HostPlatform)
        .where(HostPlatform.instance_id == instance_id, HostPlatform.team_id == team_id)
        .options(selectinload(HostPlatform.members))
        .order_by(HostPlatform.id),
    )
    return [_serialize(p) for p in result.all()]


async def _next_code(session: AsyncSession, instance_id: int, team_id: int, prefix: str) -> str:
    count = await session.scalar(
        select(func.count(HostPlatform.id)).where(
            HostPlatform.instance_id == instance_id,
            HostPlatform.team_id == team_id,
            HostPlatform.platform_code.like(f"{prefix}%"),
        ),
    )
    return f"{prefix}{(count or 0) + 1:02d}"


# ── Endpoints ────────────────────────────────────────────────────────

@router.get("/instances/{instance_id}/host-platforms", response_model=HostPlatformListOut)
async def list_host_platforms(
    instance: SimulationInstance = Depends(get_current_instance),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    team_id: int | None = Query(default=None),
):
    team = await _team_for_user(session, instance, current_user, team_id)
    if team is None:
        return HostPlatformListOut(platforms=[])
    return HostPlatformListOut(platforms=await _list_platforms(session, instance.instance_id, team.id))


@router.post("/instances/{instance_id}/host-platforms", response_model=HostPlatformListOut)
async def create_host_platform(
    payload: CreatePlatformIn,
    instance: SimulationInstance = Depends(get_current_instance),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    team_id: int | None = Query(default=None),
):
    team = await _team_for_user(session, instance, current_user, team_id)
    if team is None:
        raise HTTPException(status_code=409, detail="Select a team before creating a platform")
    if payload.platform_type not in ("on_prem", "cloud"):
        raise HTTPException(status_code=422, detail="platform_type must be on_prem or cloud")
    if payload.platform_type == "cloud" and payload.cloud_subtype not in ("iaas", "paas", "saas", "aiaas"):
        raise HTTPException(status_code=422, detail="cloud_subtype is required for cloud platforms")
    if payload.platform_type == "on_prem":
        payload.cloud_subtype = None

    prefix = "OP" if payload.platform_type == "on_prem" else "CL"
    code = await _next_code(session, instance.instance_id, team.id, prefix)
    current_round = max(instance.current_round, 1)

    platform = HostPlatform(
        instance_id=instance.instance_id,
        team_id=team.id,
        platform_code=code,
        name=payload.name,
        notes=payload.notes,
        platform_type=payload.platform_type,
        cloud_subtype=payload.cloud_subtype,
        status="pending",
        created_round=current_round,
        activated_round=current_round + 1,
    )
    session.add(platform)
    await session.commit()
    return HostPlatformListOut(platforms=await _list_platforms(session, instance.instance_id, team.id))


@router.patch("/instances/{instance_id}/host-platforms/{platform_id}", response_model=HostPlatformListOut)
async def update_host_platform(
    platform_id: int,
    payload: UpdatePlatformIn,
    instance: SimulationInstance = Depends(get_current_instance),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    team_id: int | None = Query(default=None),
):
    team = await _team_for_user(session, instance, current_user, team_id)
    if team is None:
        raise HTTPException(status_code=409, detail="Select a team")
    platform = await session.get(HostPlatform, platform_id)
    if platform is None or platform.instance_id != instance.instance_id or platform.team_id != team.id:
        raise HTTPException(status_code=404, detail="Platform not found")
    if payload.name is not None:
        platform.name = payload.name
    if payload.notes is not None:
        platform.notes = payload.notes
    await session.commit()
    return HostPlatformListOut(platforms=await _list_platforms(session, instance.instance_id, team.id))


@router.post("/instances/{instance_id}/host-platforms/{platform_id}/members", response_model=HostPlatformListOut)
async def add_member(
    platform_id: int,
    payload: AddMemberIn,
    instance: SimulationInstance = Depends(get_current_instance),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    team_id: int | None = Query(default=None),
):
    team = await _team_for_user(session, instance, current_user, team_id)
    if team is None:
        raise HTTPException(status_code=409, detail="Select a team")
    platform = await session.scalar(
        select(HostPlatform)
        .where(HostPlatform.id == platform_id, HostPlatform.instance_id == instance.instance_id, HostPlatform.team_id == team.id)
        .options(selectinload(HostPlatform.members)),
    )
    if platform is None:
        raise HTTPException(status_code=404, detail="Platform not found")
    if payload.member_kind not in ("service", "component"):
        raise HTTPException(status_code=422, detail="member_kind must be service or component")
    kind_count = sum(1 for m in platform.members if m.member_kind == payload.member_kind)
    if kind_count >= 5:
        raise HTTPException(status_code=409, detail=f"A platform can have at most 5 {payload.member_kind} members")
    existing = next((m for m in platform.members if m.asset_key == payload.asset_key), None)
    if existing is not None:
        raise HTTPException(status_code=409, detail="This asset is already assigned to this platform")
    member = HostPlatformMember(
        platform_id=platform.id,
        asset_key=payload.asset_key,
        member_kind=payload.member_kind,
        assigned_round=max(instance.current_round, 1),
    )
    session.add(member)
    await session.commit()
    return HostPlatformListOut(platforms=await _list_platforms(session, instance.instance_id, team.id))


@router.delete("/instances/{instance_id}/host-platforms/{platform_id}/members/{member_id}", response_model=HostPlatformListOut)
async def remove_member(
    platform_id: int,
    member_id: int,
    instance: SimulationInstance = Depends(get_current_instance),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    team_id: int | None = Query(default=None),
):
    team = await _team_for_user(session, instance, current_user, team_id)
    if team is None:
        raise HTTPException(status_code=409, detail="Select a team")
    platform = await session.get(HostPlatform, platform_id)
    if platform is None or platform.instance_id != instance.instance_id or platform.team_id != team.id:
        raise HTTPException(status_code=404, detail="Platform not found")
    member = await session.get(HostPlatformMember, member_id)
    if member is None or member.platform_id != platform.id:
        raise HTTPException(status_code=404, detail="Member not found")
    await session.delete(member)
    await session.commit()
    return HostPlatformListOut(platforms=await _list_platforms(session, instance.instance_id, team.id))
