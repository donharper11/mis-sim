"""Compare a captured server-side generation without taking an inverse instance lock."""
from datetime import datetime, timezone

from sqlalchemy import select

from app.models.platform import SimulationInstance
from .types import SimulationError

UNSPECIFIED_GENERATION = object()


def same_generation(first: datetime | None, second: datetime | None) -> bool:
    def utc(value):
        return value.replace(tzinfo=timezone.utc) if value is not None and value.tzinfo is None else value
    return utc(first) == utc(second)


def require_generation(session, instance_id: int, expected_started_at) -> None:
    if expected_started_at is UNSPECIFIED_GENERATION:
        return
    row = session.execute(select(SimulationInstance.started_at).where(
        SimulationInstance.instance_id == instance_id,
    )).first()
    if row is None or not same_generation(row[0], expected_started_at):
        raise SimulationError("round_state", "generation")
