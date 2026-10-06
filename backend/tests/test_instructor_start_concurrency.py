"""Real PostgreSQL setup/start serialization, including stale identity maps.

Uses the guarded, migrated fixture in test_instructor_start. The configured database
is destructive and must be a dedicated mis_sim_verify_instructor_start_* target.
Every race observes a PostgreSQL lock wait; sleeps alone are not synchronization.
"""
import asyncio
from datetime import datetime, timezone

import pytest
from sqlalchemy import select, text

from app.models.platform import Course, Enrollment, Section, SimulationInstance, Team
from app.models.grading import GradeConfig
from app.services.instructor_start import start_instance
from app.services.platform import (
    CourseService, DeletionBlocked, EnrollmentService, InstanceService,
    PlatformConflict, PlatformNotFound, SectionService, TeamService, reset_instance,
)
from test_instructor_start import database, snapshot, start  # noqa: F401

# Override the imported fixture's SQLite/PG parametrization: row-lock races require PG.
pytestmark = pytest.mark.parametrize("database", ["postgres"], indirect=True)


async def _pid(session):
    return await session.scalar(text("SELECT pg_backend_pid()"))


async def _observe_wait(db, waiter_pid, blocker_pid, task):
    deadline = asyncio.get_running_loop().time() + 10
    async with db.factory() as observer:
        while asyncio.get_running_loop().time() < deadline:
            assert not task.done(), "Contender completed without the required lock wait"
            row = (await observer.execute(text(
                "SELECT wait_event_type, pg_blocking_pids(pid) AS blockers "
                "FROM pg_stat_activity WHERE pid=:pid"
            ), {"pid": waiter_pid})).one()
            if row.wait_event_type == "Lock" and blocker_pid in row.blockers:
                return
            await asyncio.sleep(0.01)
    pytest.fail(f"No observed lock wait: waiter={waiter_pid}, blocker={blocker_pid}")


async def _cache_setup(session):
    # Retain strong references: SQLAlchemy's identity map uses weak references.
    rows = [await session.get(model, ident) for model, ident in (
        (Course, 1), (Section, 1), (SimulationInstance, 1), (Team, 1), (Enrollment, 1),
    )]
    assert rows[2].status == "setup"
    return rows


async def _mutate(session, db, operation):
    if operation == "team_create":
        return await TeamService.create(session, 1, 1, name="Concurrent extra team")
    if operation == "team_rename":
        return await TeamService.rename(session, 1, instance_id=1, section_id=1, name="Concurrent rename")
    if operation == "enrollment_create":
        # User10 is an existing active student from the other section, not yet in section1.
        return await EnrollmentService.create(session, 1, 10, team_id=None)
    if operation == "enrollment_assign":
        return await EnrollmentService.assign_team(session, 1, section_id=1, team_id=None)
    if operation == "bind_pack":
        pack = db.packs[2].casepack.metadata
        return await InstanceService.bind_pack(session, 1, pack.pack_key, pack.pack_version)
    if operation == "section_delete":
        return await SectionService.delete(session, 1)
    if operation == "course_delete":
        return await CourseService.delete(session, 1)
    raise AssertionError(operation)


OPERATIONS = ["team_create", "team_rename", "enrollment_create", "enrollment_assign",
              "bind_pack", "section_delete", "course_delete"]


def test_duplicate_start_waits_then_conflicts_without_republication(database):
    db = database

    async def run():
        async with db.factory() as winner, db.factory() as loser:
            cached = await _cache_setup(loser)
            winner_pid, loser_pid = await _pid(winner), await _pid(loser)
            published = await start_instance(winner, 1, db.packs[1].pack_digest, db.choices)
            task = asyncio.create_task(start_instance(loser, 1, db.packs[1].pack_digest, db.choices))
            try:
                await _observe_wait(db, loser_pid, winner_pid, task)
                await winner.commit()
                expected = snapshot(db)
                with pytest.raises(PlatformConflict, match="setup"):
                    await asyncio.wait_for(task, 10)
                await loser.rollback()
                assert snapshot(db) == expected
                assert published["started_at"] is not None
                assert cached  # Keep cached setup objects alive across the wait.
            finally:
                await winner.rollback()
                if not task.done():
                    task.cancel()
                await asyncio.gather(task, return_exceptions=True)
    asyncio.run(run())


@pytest.mark.parametrize("operation", OPERATIONS)
def test_start_wins_setup_mutator_rechecks_cached_status(database, operation):
    db = database

    async def run():
        async with db.factory() as winner, db.factory() as loser:
            cached = await _cache_setup(loser)
            winner_pid, loser_pid = await _pid(winner), await _pid(loser)
            await start_instance(winner, 1, db.packs[1].pack_digest, db.choices)
            task = asyncio.create_task(_mutate(loser, db, operation))
            try:
                await _observe_wait(db, loser_pid, winner_pid, task)
                await winner.commit()
                expected = snapshot(db)
                rejection = DeletionBlocked if operation.endswith("delete") else PlatformConflict
                with pytest.raises(rejection):
                    await asyncio.wait_for(task, 10)
                await loser.rollback()
                assert snapshot(db) == expected, operation
                assert cached
            finally:
                await winner.rollback()
                if not task.done():
                    task.cancel()
                await asyncio.gather(task, return_exceptions=True)
    asyncio.run(run())


@pytest.mark.parametrize("operation", OPERATIONS)
def test_setup_mutator_wins_start_revalidates_committed_changes(database, operation):
    db = database

    async def run():
        async with db.factory() as winner, db.factory() as loser:
            cached = await _cache_setup(loser)
            winner_pid, loser_pid = await _pid(winner), await _pid(loser)
            await _mutate(winner, db, operation)
            task = asyncio.create_task(start_instance(loser, 1, db.packs[1].pack_digest, db.choices))
            try:
                await _observe_wait(db, loser_pid, winner_pid, task)
                await winner.commit()
                expected = snapshot(db)
                if operation == "team_rename":
                    result = await asyncio.wait_for(task, 10)
                    await loser.commit()
                    assert result["team_ids"] == [1, 2]
                    current = snapshot(db)
                    for name, rows in expected.items():
                        if name not in {"simulation_instance", "simulation_run_v1",
                                        "simulation_sheet_v1", "simulation_checkpoint_v1"}:
                            assert current[name] == rows
                    assert next(row for row in current["team"] if row["id"] == 1)["name"] == "Concurrent rename"
                else:
                    rejection = PlatformNotFound if operation.endswith("delete") else PlatformConflict
                    with pytest.raises(rejection):
                        await asyncio.wait_for(task, 10)
                    await loser.rollback()
                    assert snapshot(db) == expected, operation
                assert cached
            finally:
                await winner.rollback()
                if not task.done():
                    task.cancel()
                await asyncio.gather(task, return_exceptions=True)
    asyncio.run(run())


@pytest.mark.parametrize("winner_name", ["start", "reset"])
def test_start_reset_lock_order_and_cached_pointer(database, winner_name):
    db = database

    async def run():
        # A setup instance can contain historical residue. Reset must publish a
        # clean round0 before the waiting start checks eligibility.
        if winner_name == "reset":
            async with db.factory() as seed:
                inst = await seed.get(SimulationInstance, 1)
                inst.current_round = 3
                inst.started_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
                seed.add(GradeConfig(instance_id=1, updated_by=1))
                await seed.commit()
        async with db.factory() as winner, db.factory() as loser:
            cached = await _cache_setup(loser)
            winner_pid, loser_pid = await _pid(winner), await _pid(loser)
            if winner_name == "start":
                await start_instance(winner, 1, db.packs[1].pack_digest, db.choices)
                task = asyncio.create_task(reset_instance(loser, 1))
            else:
                await reset_instance(winner, 1)
                task = asyncio.create_task(start_instance(loser, 1, db.packs[1].pack_digest, db.choices))
            try:
                await _observe_wait(db, loser_pid, winner_pid, task)
                await winner.commit()
                expected = snapshot(db)
                if winner_name == "start":
                    with pytest.raises(PlatformConflict, match="setup"):
                        await asyncio.wait_for(task, 10)
                    await loser.rollback()
                    assert snapshot(db) == expected
                else:
                    result = await asyncio.wait_for(task, 10)
                    await loser.commit()
                    assert result["current_round"] == 1
                    current = snapshot(db)
                    assert not current["grade_config"]
                    assert next(row for row in current["simulation_instance"] if row["instance_id"] == 1)["status"] == "active"
                    for name, rows in expected.items():
                        if name not in {"simulation_instance", "simulation_run_v1",
                                        "simulation_sheet_v1", "simulation_checkpoint_v1"}:
                            assert current[name] == rows
                    # Reuse the public test helper: the committed start is not replayed.
                    with pytest.raises(PlatformConflict):
                        await start(db)
                    assert snapshot(db) == current
                assert cached
            finally:
                await winner.rollback()
                if not task.done():
                    task.cancel()
                await asyncio.gather(task, return_exceptions=True)
    asyncio.run(run())
