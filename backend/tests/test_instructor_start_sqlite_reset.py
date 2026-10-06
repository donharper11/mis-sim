"""Actual SQLite reset/start transactions with observed writer contention."""
import asyncio
import sqlite3
import pytest
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.models.base import Base
from app.models.platform import SimulationInstance
from app.services.instructor_start import start_instance
from app.services.platform import PlatformConflict, reset_instance
from app.simulation.models import SimulationRunV1
from test_instructor_start import database, snapshot

pytestmark = pytest.mark.parametrize('database', ['sqlite'], indirect=True)

async def observe_writer_wait(db, task, entered):
    await asyncio.wait_for(entered.wait(), 5)
    # No pg_stat_activity on SQLite: actual entered contender SQL, independent
    # BEGIN IMMEDIATE failure, and pending task together demonstrate contention.
    connection = sqlite3.connect(db.engine.url.database, timeout=0)
    try:
        with pytest.raises(sqlite3.OperationalError, match='locked'):
            connection.execute('BEGIN IMMEDIATE')
    finally:
        connection.close()
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(asyncio.shield(task), .1)
    assert not task.done()


def test_sqlite_start_wins_reset_refreshes_and_refuses(database):
    db = database
    async def run():
        async with db.factory() as starting, db.factory() as resetting:
            cached = await resetting.get(SimulationInstance, 1)
            assert cached.status == 'setup'
            await start_instance(starting, 1, db.packs[1].pack_digest, db.choices)
            entered = asyncio.Event()
            def before(conn, cursor, statement, parameters, context, many):
                if statement.startswith('UPDATE simulation_instance'): entered.set()
            event.listen(db.async_engine.sync_engine, 'before_cursor_execute', before)
            task = asyncio.create_task(reset_instance(resetting, 1))
            try:
                await observe_writer_wait(db, task, entered)
                await starting.commit()
                expected = snapshot(db)
                with pytest.raises(PlatformConflict, match='setup'):
                    await asyncio.wait_for(task, 10)
                # Cache was refreshed before refusal; inspect before rollback expires it.
                assert cached.status == 'active'
                await resetting.rollback()
                assert snapshot(db) == expected
            finally:
                event.remove(db.async_engine.sync_engine, 'before_cursor_execute', before)
                await starting.rollback()
                if not task.done(): task.cancel()
                await asyncio.gather(task, return_exceptions=True)
    asyncio.run(run())


def test_sqlite_reset_eligibility_boundary_blocks_start_until_commit(database, monkeypatch):
    db = database
    baseline = snapshot(db)
    async def run():
        async with db.factory() as resetting, db.factory() as starting:
            eligible, release, entered = asyncio.Event(), asyncio.Event(), asyncio.Event()
            original = AsyncSession.execute
            async def pause_after_eligibility(current, statement, *args, **kwargs):
                if current is resetting and str(statement).startswith('SELECT round_schedule.') and not eligible.is_set():
                    eligible.set()
                    await release.wait()
                return await original(current, statement, *args, **kwargs)
            monkeypatch.setattr(AsyncSession, 'execute', pause_after_eligibility)
            reset_task = asyncio.create_task(reset_instance(resetting, 1))
            await asyncio.wait_for(eligible.wait(), 5)
            def before(conn, cursor, statement, parameters, context, many):
                if statement.startswith('UPDATE section'): entered.set()
            event.listen(db.async_engine.sync_engine, 'before_cursor_execute', before)
            start_task = asyncio.create_task(start_instance(starting, 1, db.packs[1].pack_digest, db.choices))
            try:
                await observe_writer_wait(db, start_task, entered)
                assert snapshot(db) == baseline
                release.set()
                await asyncio.wait_for(reset_task, 5)
                await resetting.commit()
                published = await asyncio.wait_for(start_task, 10)
                await starting.commit()
                after = snapshot(db)
                with Session(db.engine) as session:
                    instance = session.get(SimulationInstance, 1)
                    assert (instance.status, instance.current_round) == ('active', 1)
                    assert instance.started_at is not None and published['started_at'] is not None
                    assert len(list(session.scalars(select(SimulationRunV1).where(SimulationRunV1.instance_id == 1)))) == 2
                for table, rows in baseline.items():
                    if 'instance_id' in Base.metadata.tables[table].c:
                        assert [r for r in after[table] if r['instance_id'] != 1] == [r for r in rows if r['instance_id'] != 1]
                    elif table != 'simulation_instance':
                        assert after[table] == rows
                with pytest.raises(PlatformConflict): await reset_instance(resetting, 1)
                await resetting.rollback()
                assert snapshot(db) == after
            finally:
                release.set()
                event.remove(db.async_engine.sync_engine, 'before_cursor_execute', before)
                await resetting.rollback()
                await starting.rollback()
                for task in (reset_task, start_task):
                    if not task.done(): task.cancel()
                await asyncio.gather(reset_task, start_task, return_exceptions=True)
    asyncio.run(run())
