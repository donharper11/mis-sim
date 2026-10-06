"""Actual migrated start transactions and eligibility, never schema-created stand-ins."""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from app.models.base import Base
from app.models.platform import Course, Enrollment, Section, SimulationInstance, Team, User
from app.models.host_platform import HostPlatform, HostPlatformMember
from app.models.scheduling import RoundSchedule, RoundScheduleTeam
from app.models.grading import GradeConfig, GradeOverride
from app.round import models as legacy
from app.seed.demo import seed_cohort
from app.casepack.registry import resolve_runtime_pack
from app.services.instructor_start import RUNTIME_TABLES, inspect_start, start_instance, InvalidStart
from app.services.platform import reset_instance, PlatformConflict
from app.simulation.models import SimulationRunV1, SimulationSheetV1, SimulationCheckpointV1
from app.simulation.service import SimulationService, _state_payload, _state_digest
from app.simulation.estate import initialize_state
from app.simulation.types import SimulationError, SheetPatchV1
from test_host_scope_migration import migrate


@pytest.fixture(params=['sqlite','postgres'])
def database(request,tmp_path):
    if request.param=='postgres':
        raw=os.getenv('INSTRUCTOR_START_POSTGRES_URL')
        if not raw:pytest.skip('requires dedicated INSTRUCTOR_START_POSTGRES_URL')
        url=make_url(raw)
        assert url.host=='127.0.0.1' and url.port and not url.query
        assert (url.database or '').startswith('mis_sim_verify_instructor_start_')
        async_url=url.set(drivername='postgresql+asyncpg').render_as_string(hide_password=False)
        engine=create_engine(url.set(drivername='postgresql+psycopg2'))
        with engine.begin() as c:
            c.execute(text('DROP SCHEMA public CASCADE'));c.execute(text('CREATE SCHEMA public'))
    else:
        filename=tmp_path/'start.db'
        async_url=f'sqlite+aiosqlite:///{filename}'
        engine=create_engine(f'sqlite:///{filename}')
        @event.listens_for(engine,'connect')
        def fk(dbapi,_):dbapi.execute('PRAGMA foreign_keys=ON')
    migrate(async_url,'head')
    ae=create_async_engine(async_url,poolclass=NullPool)
    if engine.dialect.name=='sqlite':
        @event.listens_for(ae.sync_engine,'connect')
        def afk(dbapi,_):dbapi.execute('PRAGMA foreign_keys=ON')
    factory=async_sessionmaker(ae,expire_on_commit=False)
    async def seed():
        async with factory() as s:
            await seed_cohort(s)
            s.add_all([User(id=18,name='Other',email='other@start.test',role='instructor'),
                       User(id=19,name='Admin',email='admin@start.test',role='admin'),
                       User(id=20,name='TA',email='ta@start.test',role='ta')])
            await s.flush()
            s.add(Enrollment(user_id=20,section_id=1,role='ta'))
            await s.commit()
    asyncio.run(seed())
    with Session(engine) as s:
        packs={iid:resolve_runtime_pack(s,inst.pack_key,inst.pack_version) for iid in (1,2)
               for inst in [s.get(SimulationInstance,iid)]}
    db=SimpleNamespace(engine=engine,url=async_url,async_engine=ae,factory=factory,packs=packs,
                       choices={1:'cost_leadership',2:'customer_intimacy'})
    # Take actual authored alternatives, not a synthetic strategy vocabulary.
    db.choices[2]=packs[1].casepack.strategies[1].key
    yield db
    asyncio.run(ae.dispose());engine.dispose()


def snapshot(db):
    with db.engine.connect() as c:
        return {table.name:sorted([dict(row) for row in c.execute(select(table)).mappings()],key=repr)
                for table in Base.metadata.sorted_tables}


async def start(db, iid=1, choices=None):
    async with db.factory() as s:
        result=await start_instance(s,iid,db.packs[iid].pack_digest,choices or db.choices)
        await s.commit();return result


def test_atomic_start_state_parity_rollback_retry(database,monkeypatch):
    db=database;before=snapshot(db)
    original=SimulationService.initialize_in_session
    def fail_second(self,session,iid,tid,strategy):
        result=original(self,session,iid,tid,strategy)
        if tid==2:raise RuntimeError('second team injected failure')
        return result
    with monkeypatch.context() as patch:
        patch.setattr(SimulationService,'initialize_in_session',fail_second)
        with pytest.raises(RuntimeError,match='second team'):asyncio.run(start(db))
    assert snapshot(db)==before
    result=asyncio.run(start(db));assert result['team_ids']==[1,2]
    with Session(db.engine) as s:
        inst=s.get(SimulationInstance,1)
        assert (inst.status,inst.current_round,inst.completed_at)==('active',1,None)
        assert inst.started_at is not None
        for tid,strategy in db.choices.items():
            run=s.get(SimulationRunV1,(1,tid));cp=s.get(SimulationCheckpointV1,(1,tid,0));sheet=s.get(SimulationSheetV1,(1,tid,1))
            expected=initialize_state(db.packs[1],strategy)
            assert (run.status,run.current_round,run.advanced_round)==('draft',1,0)
            assert (cp.state,cp.state_digest)==(_state_payload(expected),_state_digest(expected))
            assert (sheet.commands,sheet.revision,sheet.locked_revision)==([],0,None)
        for model in RUNTIME_TABLES:
            if model not in (SimulationRunV1,SimulationCheckpointV1,SimulationSheetV1):
                assert s.execute(select(model).where(model.instance_id==1)).first() is None
    after=snapshot(db)
    for table,rows in before.items():
        if table not in {'simulation_instance','simulation_run_v1','simulation_sheet_v1','simulation_checkpoint_v1'}:
            assert after[table]==rows
        if rows and 'instance_id' in rows[0]:
            assert [r for r in after[table] if r['instance_id']==2]==[r for r in rows if r['instance_id']==2]
    with pytest.raises(PlatformConflict):asyncio.run(start(db))
    assert snapshot(db)==after


def test_readiness_eligibility_and_invalid_choices_are_read_only(database):
    db=database
    cases=[
        (Course,1,'is_active',False,'Activate'),(Section,1,'is_active',False,'Activate'),
        (SimulationInstance,1,'status','active','setup'),(SimulationInstance,1,'current_round',1,'round 0'),
        (SimulationInstance,1,'pack_digest',None,'binding'),(SimulationInstance,1,'pack_digest','wrong','binding'),
        (SimulationInstance,1,'pack_key','missing','unavailable'),(SimulationInstance,1,'total_rounds',3,'requires'),
        (Section,1,'max_teams',1,'number'),(Section,1,'team_size_min',5,'needs'),
        (Section,1,'team_size_max',3,'needs'),(Enrollment,1,'team_id',None,'Assign'),
        (User,2,'is_active',False,'account'),(User,2,'role','instructor','account'),
    ]
    async def run():
        async with db.factory() as s:
            for model,ident,field,value,reason in cases:
                row=await s.get(model,ident);setattr(row,field,value);await s.flush()
                inst=await s.get(SimulationInstance,1)
                report,_=await inspect_start(s,inst)
                assert not report['ready'] and any(reason in r for r in report['blocked_reasons']),report
                with pytest.raises(PlatformConflict):await start_instance(s,1,inst.pack_digest or 'missing',db.choices)
                await s.rollback()
            # Inactive enrollment is ignored; the remaining three students keep team eligible.
            (await s.get(Enrollment,1)).is_active=False
            await s.flush()
            report,_=await inspect_start(s,await s.get(SimulationInstance,1))
            assert report['ready'] and report['teams'][0]['student_count']==3
            await s.rollback()
            with pytest.raises(InvalidStart):await start_instance(s,1,db.packs[1].pack_digest,{1:'not_authored',2:db.choices[2]})
            await s.rollback()
            for choices,digest in [({1:'cost_leadership'},db.packs[1].pack_digest),(db.choices,'stale')]:
                with pytest.raises(PlatformConflict):await start_instance(s,1,digest,choices)
                await s.rollback()
    before=snapshot(db);asyncio.run(run());assert snapshot(db)==before


def test_generation_mutations_refuse_recreated_run(database):
    db=database;old=asyncio.run(start(db))['started_at']
    async def restart():
        async with db.factory() as s:
            (await s.get(SimulationInstance,1)).status='setup';await s.flush()
            await reset_instance(s,1);await s.commit()
        return await start(db)
    new=asyncio.run(restart())['started_at'];assert new!=old
    service=SimulationService(db.engine,db.packs[1]);before=snapshot(db)
    actions=[lambda:service.patch_sheet(1,1,1,0,SheetPatchV1(version=1,replace_categories={}),expected_started_at=old),
             lambda:service.lock(1,1,1,0,expected_started_at=old),
             lambda:service.reopen(1,1,1,0,expected_started_at=old),
             lambda:service.advance(1,1,1,0,expected_started_at=old),
             lambda:service.lock(1,1,1,0,expected_started_at=None)]
    for action in actions:
        with pytest.raises(SimulationError,match='generation'):action()
        assert snapshot(db)==before
    # Naive SQLite UTC and aware PostgreSQL UTC mean the same generation.
    service.lock(1,1,1,0,expected_started_at=new.replace(tzinfo=None))
    service.reopen(1,1,1,0,expected_started_at=new)


def test_every_runtime_inventory_blocks_start_and_reset_recovers(database):
    """Real constrained residue, with parents when required, must never be adopted."""
    from datetime import timedelta
    from sqlalchemy import Boolean, Float, Integer, JSON
    db = database
    # An explicit independent inventory catches a forgotten registration as well.
    expected = {m.__tablename__ for m in legacy.ALL_TABLES} | {
        'round_schedule', 'round_schedule_team', 'host_platform', 'host_platform_member',
        'simulation_run_v1', 'simulation_sheet_v1', 'simulation_checkpoint_v1', 'grade_config', 'grade_override',
    }
    assert len(expected) == 25 and {m.__tablename__ for m in RUNTIME_TABLES} == expected
    before = snapshot(db)
    async def run():
        async with db.factory() as session:
            for model in RUNTIME_TABLES:
                now = datetime.now(timezone.utc)
                if model in (SimulationRunV1, SimulationSheetV1, SimulationCheckpointV1):
                    service = SimulationService(session.get_bind(), db.packs[1])
                    await session.run_sync(lambda sync: service.initialize_in_session(sync, 1, 1, db.choices[1]))
                elif model in (RoundSchedule, RoundScheduleTeam):
                    schedule = RoundSchedule(instance_id=1, round_number=1, start_at=now, deadline=now+timedelta(days=1), auto_advance=False, grace_period_minutes=0)
                    session.add(schedule); await session.flush()
                    if model is RoundScheduleTeam:
                        session.add(RoundScheduleTeam(schedule_id=schedule.id, instance_id=1, team_id=1))
                elif model in (HostPlatform, HostPlatformMember):
                    host = HostPlatform(instance_id=1, team_id=1, platform_code='RESIDUE', name='Residue', platform_type='on_prem', created_round=1)
                    session.add(host); await session.flush()
                    if model is HostPlatformMember:
                        session.add(HostPlatformMember(platform_id=host.id, instance_id=1, asset_key='residue', member_kind='service', assigned_round=1))
                elif model in (GradeConfig, GradeOverride):
                    values = {'instance_id': 1, 'updated_by': 1}
                    if model is GradeOverride: values['team_id'] = 1
                    session.add(model(**values))
                else:
                    values = {'instance_id': 1, 'team_id': 1}
                    for col in model.__table__.columns:
                        if col.name in values or col.name == 'id' or col.nullable or col.default is not None: continue
                        if isinstance(col.type, JSON): value = {}
                        elif isinstance(col.type, Boolean): value = False
                        elif isinstance(col.type, (Integer, Float)): value = 1
                        else: value = 'residue'
                        values[col.name] = value
                    session.add(model(**values))
                await session.flush()
                report, _ = await inspect_start(session, await session.get(SimulationInstance, 1))
                assert not report['ready'] and any('Reset' in reason for reason in report['blocked_reasons']), model.__tablename__
                with pytest.raises(PlatformConflict, match='Reset'):
                    await start_instance(session, 1, db.packs[1].pack_digest, db.choices)
                # Reset removes every seeded family without changing teams/roster.
                await reset_instance(session, 1)
                report, _ = await inspect_start(session, await session.get(SimulationInstance, 1))
                assert report['ready'], (model.__tablename__, report)
                await session.rollback()
    asyncio.run(run())
    assert snapshot(db) == before
