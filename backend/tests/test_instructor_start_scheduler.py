"""Independent regression probes for scheduler generation and publication fences.

Uses the migrated SQLite / explicitly disposable PostgreSQL fixture shared by
the instructor-start packet. Every rejected obsolete operation must preserve the
entire replacement generation, including scheduling metadata.
"""
import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.models.platform import SimulationInstance
from app.scheduling.service import Scheduler, SchedulingError
from app.services.platform import reset_instance
from app.simulation.service import SimulationService
from app.simulation.types import SimulationError
from test_instructor_start import database, snapshot, start


def add_schedule(db, round_number=1):
    now = datetime.now(timezone.utc)
    with Session(db.engine) as session:
        row = Scheduler(session).set_schedule(
            1, round_number, now - timedelta(hours=2), now + timedelta(hours=2),
            auto_advance=False, grace_period_minutes=0,
        )
        session.commit()
        return row.id


def restart(db):
    async def run():
        async with db.factory() as session:
            (await session.get(SimulationInstance, 1)).status = "setup"
            await session.flush()
            await reset_instance(session, 1)
            await session.commit()
        return await start(db)
    return asyncio.run(run())


def invoke(scheduler, operation, now):
    if operation == "unlock":
        return scheduler.unlock(1, 1)
    return getattr(scheduler, operation)(1, 1, now)


@pytest.mark.parametrize("operation", ["lock_now", "advance_now", "unlock"])
def test_scheduler_captured_entry_rejects_replacement_metadata(database, monkeypatch, operation):
    db = database
    old = asyncio.run(start(db))["started_at"]
    add_schedule(db)
    now = datetime.now(timezone.utc)
    replacement = None
    original_scalar = Session.scalar
    with Session(db.engine) as session:
        def after_generation_read(current, statement, *args, **kwargs):
            nonlocal replacement
            result = original_scalar(current, statement, *args, **kwargs)
            if (current is session and replacement is None
                    and str(statement).startswith("SELECT simulation_instance.started_at")):
                assert restart(db)["started_at"] != old
                add_schedule(db)
                if operation == "unlock":
                    # A real new-generation lock, not an inconsistent sentinel.
                    with Session(db.engine) as other:
                        assert Scheduler(other).lock_now(1, 1, now)["state"] == "locked"
                replacement = snapshot(db)
            return result
        monkeypatch.setattr(Session, "scalar", after_generation_read)
        try:
            result = invoke(Scheduler(session), operation, now)
        except (SchedulingError, SimulationError):
            assert operation == "unlock"
        else:
            assert operation != "unlock"
            assert result["state"] == "failed" and result["failures"]
    assert replacement is not None
    assert snapshot(db) == replacement


def test_scheduler_tick_preserves_frozen_work_after_first_generation_failure(database, monkeypatch):
    db = database
    asyncio.run(start(db))
    add_schedule(db, 1)
    add_schedule(db, 2)
    replacement = None
    original_claim = Scheduler._claim
    def after_collection(self, schedule, at, **kwargs):
        nonlocal replacement
        if replacement is None:
            restart(db)
            add_schedule(db, 1)
            replacement = snapshot(db)
        return original_claim(self, schedule, at, **kwargs)
    monkeypatch.setattr(Scheduler, "_claim", after_collection)
    with Session(db.engine) as session:
        results = Scheduler(session).tick(datetime.now(timezone.utc))
    assert [(row["round_number"], row["state"]) for row in results] == [(1, "failed"), (2, "failed")]
    assert all(row["failures"] for row in results)
    assert replacement is not None
    assert snapshot(db) == replacement


@pytest.mark.parametrize("operation,service_method", [("lock_now", "lock"), ("advance_now", "advance"), ("unlock", "reopen")])
def test_scheduler_post_service_publication_cannot_touch_replacement(database, monkeypatch, operation, service_method):
    db = database
    asyncio.run(start(db))
    add_schedule(db)
    now = datetime.now(timezone.utc)
    if operation != "lock_now":
        with Session(db.engine) as session:
            assert Scheduler(session).lock_now(1, 1, now)["state"] == "locked"
    replacement = None
    original = getattr(SimulationService, service_method)
    def after_service(self, *args, **kwargs):
        nonlocal replacement
        result = original(self, *args, **kwargs)
        if replacement is None:
            restart(db)
            add_schedule(db)
            replacement = snapshot(db)
        return result
    monkeypatch.setattr(SimulationService, service_method, after_service)
    with Session(db.engine) as session:
        try:
            result = invoke(Scheduler(session), operation, now)
        except (SchedulingError, SimulationError):
            assert operation == "unlock"
        else:
            assert operation != "unlock"
            assert result["state"] == "failed" and result["failures"]
    assert replacement is not None
    assert snapshot(db) == replacement
