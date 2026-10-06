"""Presentation host activation; callers hold the authoritative team run lock."""
from sqlalchemy import BigInteger, cast, update
from sqlalchemy.orm import Session

from app.models.host_platform import HostPlatform


def activate_due_hosts(session: Session, instance_id: int, team_id: int, current_round: int) -> None:
    session.execute(update(HostPlatform).where(
        HostPlatform.instance_id == instance_id,
        HostPlatform.team_id == team_id,
        HostPlatform.status == "pending",
        HostPlatform.created_round >= 1,
        HostPlatform.activated_round == cast(HostPlatform.created_round, BigInteger) + 1,
        HostPlatform.activated_round <= current_round,
    ).values(status="active"))
