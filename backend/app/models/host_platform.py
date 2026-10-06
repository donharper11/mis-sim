"""Host platform container models.

Presentation-layer grouping of services and components into logical
host platforms (on-prem or cloud).  The simulation engine is not modified;
these tables exist solely for the UI container concept.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class HostPlatform(Base):
    __tablename__ = "host_platform"
    __table_args__ = (
        UniqueConstraint("instance_id", "team_id", "platform_code", name="uq_host_platform_code"),
        UniqueConstraint("id", "instance_id", name="uq_host_platform_instance_identity"),
        ForeignKeyConstraint(["team_id", "instance_id"], ["team.id", "team.instance_id"],
                             name="fk_host_platform_team_instance", ondelete="CASCADE"),
        CheckConstraint(
            "platform_type IN ('on_prem', 'cloud')",
            name="ck_host_platform_type",
        ),
        CheckConstraint(
            "cloud_subtype IS NULL OR cloud_subtype IN ('iaas', 'paas', 'saas', 'aiaas')",
            name="ck_host_platform_cloud_subtype",
        ),
        CheckConstraint(
            "status IN ('pending', 'active', 'retired')",
            name="ck_host_platform_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(
        ForeignKey("simulation_instance.instance_id", ondelete="CASCADE"),
        nullable=False,
    )
    team_id: Mapped[int] = mapped_column(Integer, nullable=False)
    platform_code: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    platform_type: Mapped[str] = mapped_column(String(16), nullable=False)
    cloud_subtype: Mapped[str | None] = mapped_column(String(16), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    created_round: Mapped[int] = mapped_column(Integer, nullable=False)
    activated_round: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )

    members: Mapped[list[HostPlatformMember]] = relationship(
        back_populates="platform", passive_deletes="all",
    )


class HostPlatformMember(Base):
    __tablename__ = "host_platform_member"
    __table_args__ = (
        UniqueConstraint("platform_id", "asset_key", name="uq_host_platform_member_asset"),
        ForeignKeyConstraint(["platform_id", "instance_id"], ["host_platform.id", "host_platform.instance_id"],
                             name="fk_host_platform_member_platform_instance", ondelete="CASCADE"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(
        ForeignKey("simulation_instance.instance_id", name="fk_host_platform_member_instance", ondelete="CASCADE"),
        nullable=False,
    )
    platform_id: Mapped[int] = mapped_column(Integer, nullable=False)
    asset_key: Mapped[str] = mapped_column(String(64), nullable=False)
    member_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    assigned_round: Mapped[int] = mapped_column(Integer, nullable=False)

    platform: Mapped[HostPlatform] = relationship(back_populates="members")


ALL_TABLES = (HostPlatform, HostPlatformMember)
