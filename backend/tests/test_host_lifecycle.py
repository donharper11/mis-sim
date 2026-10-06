"""Host timing, reset inventory and real transaction boundaries on both engines.

The PostgreSQL fixture destroys only an explicit dedicated loopback database.
"""
import asyncio
from datetime import datetime, timedelta, timezone
import importlib.util
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Event
import time

import pytest
from sqlalchemy import create_engine, event, select, text, Integer, Float, Boolean, JSON
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

from app.models.base import Base
from app.models import grading, host_platform, platform, scheduling
from app.models.host_platform import HostPlatform, HostPlatformMember
from app.round import models as legacy
from app.simulation import models as simulation
from app.simulation.content import load_runtime_pack
from app.simulation.service import SimulationService
from app.services.platform import reset_instance, PlatformConflict
from test_host_scope_migration import migrate, seed_parents

PACK = Path(__file__).parents[1] / 'packs' / 'riverside_grocery'
RUNTIME = (*scheduling.ALL_TABLES, *host_platform.ALL_TABLES, *simulation.ALL_TABLES,
           *legacy.ALL_TABLES, grading.GradeConfig, grading.GradeOverride)


@pytest.fixture(params=['sqlite', 'postgres'])
def database(request, tmp_path):
    if request.param == 'postgres':
        raw = os.getenv('HOST_LIFECYCLE_POSTGRES_URL')
        if not raw:
            pytest.skip('requires dedicated HOST_LIFECYCLE_POSTGRES_URL')
        url = make_url(raw)
        assert url.host == '127.0.0.1' and url.port and not url.query
        assert url.database.startswith('mis_sim_verify_host_lifecycle_')
        async_url = url.set(drivername='postgresql+asyncpg').render_as_string(hide_password=False)
        engine = create_engine(url.set(drivername='postgresql+psycopg2'))
        with engine.begin() as c:
            c.execute(text('DROP SCHEMA public CASCADE'))
            c.execute(text('CREATE SCHEMA public'))
    else:
        filename = tmp_path / 'lifecycle.db'
        async_url = f'sqlite+aiosqlite:///{filename}'
        engine = create_engine(f'sqlite:///{filename}')
        @event.listens_for(engine, 'connect')
        def foreign_keys(dbapi, _):
            dbapi.execute('PRAGMA foreign_keys=ON')
    migrate(async_url, '20261004_0011')
    seed_parents(engine)
    migrate(async_url, '20261006_0012')
    if engine.dialect.name == 'postgresql':
        # Historical seed uses explicit IDs; align generated IDs for CRUD tests.
        with engine.begin() as c:
            for table in ('host_platform', 'host_platform_member'):
                c.execute(text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), (SELECT max(id) FROM {table}))"))
    yield engine, async_url
    engine.dispose()


def snapshot(engine, models=RUNTIME, instance_id=None):
    with engine.connect() as c:
        return {m.__tablename__: sorted(
            [dict(r) for r in c.execute(select(m.__table__).where(m.instance_id == instance_id) if instance_id else select(m.__table__)).mappings()],
            key=repr,
        ) for m in models}


def service_for(engine):
    pack = load_runtime_pack(PACK)
    with Session(engine) as s:
        meta = pack.casepack.metadata
        s.add(platform.Casepack(pack_key=meta.pack_key, pack_version=meta.pack_version,
            pack_digest=pack.pack_digest, schema_version=meta.schema_version,
            display_name=meta.display_name, vertical=meta.vertical, rounds=meta.rounds,
            path=str(PACK), validation_json={'errors': [], 'warnings': [], 'exit_code': 0}))
        for iid in (1, 2):
            inst = s.get(platform.SimulationInstance, iid)
            inst.pack_key, inst.pack_version, inst.pack_digest = meta.pack_key, meta.pack_version, pack.pack_digest
            inst.total_rounds = meta.rounds
        s.commit()
    service = SimulationService(engine, pack)
    for iid in (1, 2):
        service.initialize(iid, iid, 'cost_leadership')
    return service


def hosts(engine, iid=1, team=1):
    # Includes legal INTEGER extremes: evaluating malformed input cannot overflow.
    rows = [(11,1,2,'pending'), (12,2,3,'pending'), (13,1,None,'pending'),
            (14,1,1,'pending'), (15,0,1,'pending'), (16,1,2,'retired'),
            (17,1,2,'active'), (18,2147483647,2147483647,'pending'),
            (19,-2147483648,-2147483647,'pending')]
    with Session(engine) as s:
        for hid, created, activated, status in rows:
            s.add(HostPlatform(id=hid, instance_id=iid, team_id=team,
                platform_code=f'H{hid}', name=f'Host {hid}', platform_type='on_prem',
                created_round=created, activated_round=activated, status=status))
        s.commit()


def test_activation_atomic_retry_parity_and_final_horizon(database, monkeypatch):
    engine, _ = database
    service = service_for(engine)
    hosts(engine)
    before_other = snapshot(engine, instance_id=2)
    service.lock(1,1,1,0)
    before = snapshot(engine)
    import app.simulation.service as module
    original = module.activate_due_hosts
    def failed(*args):
        original(*args)
        raise RuntimeError('after promotion')
    with monkeypatch.context() as patch:
        patch.setattr(module, 'activate_due_hosts', failed)
        with pytest.raises(RuntimeError, match='after promotion'):
            service.advance(1,1,1,0)
    assert snapshot(engine) == before
    result = service.advance(1,1,1,0)
    assert snapshot(engine, instance_id=2) == before_other
    with Session(engine) as s:
        statuses = dict(s.execute(select(HostPlatform.id,HostPlatform.status)).all())
    assert {hid for hid,status in statuses.items() if status=='active'} == {1,11,17}
    committed = snapshot(engine)
    assert service.advance(1,1,1,0) == result
    assert snapshot(engine) == committed
    # Identical engine result and checkpoint with a no-host control scope.
    with engine.begin() as c:
        c.execute(HostPlatformMember.__table__.delete().where(HostPlatformMember.instance_id==2))
        c.execute(HostPlatform.__table__.delete().where(HostPlatform.instance_id==2))
    service.lock(2,2,1,0)
    assert service.advance(2,2,1,0) == result
    with Session(engine) as s:
        a=s.get(simulation.SimulationCheckpointV1,(1,1,1))
        b=s.get(simulation.SimulationCheckpointV1,(2,2,1))
        assert (a.state,a.state_digest)==(b.state,b.state_digest)
    final=service.runtime_pack.casepack.metadata.rounds
    for round_no in range(2, final+1):
        if round_no==final:
            with Session(engine) as s:
                s.add(HostPlatform(id=30,instance_id=1,team_id=1,platform_code='FINAL',name='Final',
                    platform_type='cloud',created_round=final,activated_round=final+1,status='pending'))
                s.commit()
        service.lock(1,1,round_no,0)
        service.advance(1,1,round_no,0)
    with Session(engine) as s:
        assert s.get(HostPlatform,30).status=='pending'
        assert s.get(HostPlatform,12).status=='active'
        assert s.get(simulation.SimulationRunV1,(1,1)).current_round==final


def test_historical_repair_status_only_idempotent_and_noop_downgrade(database):
    engine,url=database
    service_for(engine)
    hosts(engine)
    with Session(engine) as s:
        s.get(simulation.SimulationRunV1,(1,1)).current_round=2
        run=s.get(simulation.SimulationRunV1,(2,2));run.current_round=6;run.status='completed'
        # Missing run remains untouched.
        s.add(platform.Team(id=3,section_id=1,instance_id=1,name='No run'));s.flush()
        s.add(HostPlatform(id=31,instance_id=1,team_id=3,platform_code='NORUN',name='No run',
            platform_type='cloud',status='pending',created_round=1,activated_round=2))
        s.commit()
    before=snapshot(engine)
    migrate(url,'20261006_0013')
    after=snapshot(engine)
    expected=before.copy()
    expected['host_platform']=[{**r,'status':'active'} if r['id'] in (1,2,11) else r for r in before['host_platform']]
    assert after==expected
    module_path=Path(__file__).parents[1]/'alembic/versions/20261006_0013_host_activation.py'
    spec=importlib.util.spec_from_file_location('repair',module_path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    with engine.begin() as c:
        with Operations.context(MigrationContext.configure(c)):
            module.upgrade()
    assert snapshot(engine)==after
    migrate(url,'20261006_0012','downgrade')
    assert snapshot(engine)==after


def fill_legacy(engine):
    # Deliberately populate every declared historical table, including tables that
    # production initialize no longer writes. Type-generated payloads are cleanup
    # sentinels, never evidence of game calculations.
    with engine.begin() as c:
        for iid in (1,2):
            for model in legacy.ALL_TABLES:
                values={'instance_id':iid,'team_id':iid}
                for col in model.__table__.columns:
                    if col.name in values or col.name=='id' or col.nullable or col.default is not None:
                        continue
                    if isinstance(col.type,JSON): value={}
                    elif isinstance(col.type,Boolean): value=False
                    elif isinstance(col.type,(Integer,Float)): value=1
                    else: value='sentinel'
                    values[col.name]=value
                c.execute(model.__table__.insert().values(**values))


def test_reset_all_runtime_preservation_rejection_and_rollback(database):
    engine,url=database
    service_for(engine);fill_legacy(engine)
    now=datetime.now(timezone.utc)
    with Session(engine) as s:
        for iid in (1,2):
            inst=s.get(platform.SimulationInstance,iid)
            inst.current_round=3;inst.started_at=now;inst.completed_at=now
            sch=scheduling.RoundSchedule(instance_id=iid,round_number=1,start_at=now,deadline=now+timedelta(days=1),auto_advance=True,grace_period_minutes=0)
            s.add(sch);s.flush()
            s.add(scheduling.RoundScheduleTeam(schedule_id=sch.id,instance_id=iid,team_id=iid))
            s.add(grading.GradeConfig(instance_id=iid,updated_by=1))
            s.add(grading.GradeOverride(instance_id=iid,team_id=iid,updated_by=1,override=0.5,reason='Preserve scope'))
        s.commit()
    original=snapshot(engine)
    identities=snapshot(engine,platform.ALL_TABLES)
    async def run():
        ae=create_async_engine(url);factory=async_sessionmaker(ae,expire_on_commit=False)
        try:
            async with factory() as s:
                def fail_after_delete(conn,cursor,statement,params,context,many):
                    if statement.startswith('DELETE FROM grade_config'):
                        raise RuntimeError('late reset failure')
                event.listen(ae.sync_engine,'before_cursor_execute',fail_after_delete)
                try:
                    with pytest.raises(RuntimeError,match='late reset failure'):
                        await reset_instance(s,1)
                    await s.rollback()
                finally:
                    event.remove(ae.sync_engine,'before_cursor_execute',fail_after_delete)
            assert snapshot(engine)==original
            assert snapshot(engine,platform.ALL_TABLES)==identities
            for status in ('active','paused','completed','archived'):
                # SQLite archive CHECK repair is a separately owned open task.
                if status=='archived' and engine.dialect.name=='sqlite': continue
                async with factory() as s:
                    inst=await s.get(platform.SimulationInstance,1);inst.status=status
                    await s.commit()
                    with pytest.raises(PlatformConflict):await reset_instance(s,1)
                    await s.rollback()
                assert snapshot(engine)==original
            async with factory() as s:
                inst=await s.get(platform.SimulationInstance,1);inst.status='setup';await s.commit()
                await reset_instance(s,1);await s.commit()
                await reset_instance(s,1);await s.commit()
        finally:await ae.dispose()
    asyncio.run(run())
    assert all(not rows for rows in snapshot(engine,instance_id=1).values())
    assert snapshot(engine,instance_id=2)=={k:[r for r in v if r['instance_id']==2] for k,v in original.items()}
    after=snapshot(engine,platform.ALL_TABLES)
    expected=identities.copy()
    expected['simulation_instance']=[{**r,'current_round':0,'started_at':None,'completed_at':None} if r['instance_id']==1 else r for r in identities['simulation_instance']]
    assert after==expected


@pytest.mark.parametrize('actor',['host_edit','advance'])
def test_postgres_host_edit_reset_serialization(database,monkeypatch,actor):
    engine,url=database
    if engine.dialect.name!='postgresql':return
    service=service_for(engine)
    if actor=='advance':
        service.lock(1,1,1,0)
        import app.simulation.service as module
        original=module.activate_due_hosts
        def paused(*args):
            locked.set();assert release.wait(10)
            return original(*args)
        monkeypatch.setattr(module,'activate_due_hosts',paused)
    locked=Event();release=Event();reset_started=Event()
    def edit():
        if actor=='advance':
            service.advance(1,1,1,0)
            return
        with Session(engine) as s:
            s.execute(select(simulation.SimulationRunV1).where(simulation.SimulationRunV1.instance_id==1).with_for_update())
            locked.set();assert release.wait(10)
            s.add(HostPlatform(id=42,instance_id=1,team_id=1,platform_code='RACE',name='Race',
                platform_type='cloud',created_round=1,activated_round=2,status='pending'))
            s.commit()
    def reset():
        async def run():
            ae=create_async_engine(url)
            try:
                async with async_sessionmaker(ae)() as s:
                    await s.execute(text("SET LOCAL statement_timeout='8s'"))
                    await s.execute(text("SET LOCAL application_name='host_lifecycle_reset_probe'"))
                    reset_started.set();await reset_instance(s,1);await s.commit()
            finally:await ae.dispose()
        asyncio.run(run())
    with ThreadPoolExecutor(2) as pool:
        first=pool.submit(edit);assert locked.wait(5)
        second=pool.submit(reset);assert reset_started.wait(5)
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            with engine.connect() as c:
                blocked=c.execute(text("SELECT count(*) FROM pg_stat_activity WHERE application_name='host_lifecycle_reset_probe' AND wait_event_type='Lock'")).scalar()
            if blocked:break
            time.sleep(0.02)
        assert blocked, 'reset never waited on the held run lock'
        release.set();first.result(timeout=12);second.result(timeout=12)
    assert all(not rows for rows in snapshot(engine,instance_id=1).values())
    assert snapshot(engine,instance_id=2)['simulation_run_v1']


def test_real_manual_and_scheduler_activation_parity(database, monkeypatch):
    from httpx import ASGITransport, AsyncClient
    from app.api import deps, runtime_round_control
    from app.main import create_app
    from app.services.auth import create_access_token
    from app.scheduling.service import Scheduler
    engine,url=database
    service_for(engine)
    # Endpoint disposes its engine; use a separate pool per call, as production does.
    monkeypatch.setattr(runtime_round_control,'make_engine',lambda:create_engine(engine.url))
    async def run():
        ae=create_async_engine(url);factory=async_sessionmaker(ae,expire_on_commit=False)
        async def session_dep():
            async with factory() as s:yield s
        app=create_app();app.dependency_overrides[deps.get_session]=session_dep
        try:
            token=create_access_token(user_id=1,role='instructor')
            async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as client:
                r=await client.post('/api/instances/1/round-control/advance',headers={'Authorization':'Bearer '+token})
                assert r.status_code==200,r.text
                assert r.json()['next_round']==2
            async with factory() as s:
                with pytest.raises(PlatformConflict):await reset_instance(s,1)
        finally:await ae.dispose()
    asyncio.run(run())
    now=datetime.now(timezone.utc)
    with Session(engine) as s:
        scheduler=Scheduler(s)
        scheduler.set_schedule(2,1,now-timedelta(days=2),now-timedelta(days=1),auto_advance=True,grace_period_minutes=0)
        result=scheduler.tick(now)
        assert result[0]['state']=='advanced',result
    with Session(engine) as s:
        assert s.get(HostPlatform,1).status==s.get(HostPlatform,2).status=='active'
        assert s.get(legacy.RoundResult,(1,1,1)).payload==s.get(legacy.RoundResult,(2,2,1)).payload
        assert s.get(simulation.SimulationCheckpointV1,(1,1,1)).state_digest==s.get(simulation.SimulationCheckpointV1,(2,2,1)).state_digest
        # Scheduled advancement deliberately leaves presentation pointer stale.
        assert s.get(platform.SimulationInstance,2).current_round==0


@pytest.mark.parametrize('interleave',['reset','newer_advance'])
def test_manual_final_reconciliation_fence(database, monkeypatch, interleave):
    from httpx import ASGITransport, AsyncClient
    from app.api import deps, runtime_round_control
    from app.main import create_app
    from app.services.auth import create_access_token
    engine,url=database
    service=service_for(engine)
    monkeypatch.setattr(runtime_round_control,'make_engine',lambda:create_engine(engine.url))
    original_to_thread=asyncio.to_thread
    async def run():
        ae=create_async_engine(url);factory=async_sessionmaker(ae,expire_on_commit=False)
        async def session_dep():
            async with factory() as s:yield s
        app=create_app();app.dependency_overrides[deps.get_session]=session_dep
        async def after_service(func,*args,**kwargs):
            value=await original_to_thread(func,*args,**kwargs)
            if func.__name__=='advance_one':
                if interleave=='reset':
                    async with factory() as s:
                        await reset_instance(s,1);await s.commit()
                else:
                    service.lock(1,1,2,0);service.advance(1,1,2,0)
            return value
        monkeypatch.setattr(asyncio,'to_thread',after_service)
        try:
            token=create_access_token(user_id=1,role='instructor')
            async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as client:
                r=await client.post('/api/instances/1/round-control/advance',headers={'Authorization':'Bearer '+token})
                assert r.status_code==(409 if interleave=='reset' else 200),r.text
                if interleave=='newer_advance':assert r.json()['next_round']==3
        finally:await ae.dispose()
    asyncio.run(run())
    with Session(engine) as s:
        inst=s.get(platform.SimulationInstance,1)
        if interleave=='reset':
            assert (inst.status,inst.current_round)==('setup',0)
            assert all(not rows for rows in snapshot(engine,instance_id=1).values())
        else:assert (inst.status,inst.current_round)==('active',3)


def test_pending_only_writes_and_authoritative_round(database, monkeypatch):
    from httpx import ASGITransport, AsyncClient
    from app.api import deps
    from app.main import create_app
    from app.services.auth import create_access_token
    engine,url=database
    service=service_for(engine)
    service.lock(1,1,1,0);service.advance(1,1,1,0)
    async def run():
        ae=create_async_engine(url);factory=async_sessionmaker(ae,expire_on_commit=False)
        async def session_dep():
            async with factory() as s:yield s
        app=create_app();app.dependency_overrides[deps.get_session]=session_dep
        token=create_access_token(user_id=1,role='instructor')
        try:
            async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test',headers={'Authorization':'Bearer '+token}) as client:
                base='/api/instances/1/host-platforms'
                created=await client.post(base,json={'name':'New round','platform_type':'on_prem'})
                assert created.status_code==200,created.text
                new=next(p for p in created.json()['platforms'] if p['name']=='New round')
                assert (new['created_round'],new['activated_round'])==(2,3)
                path=f"{base}/{new['id']}"
                attached=await client.post(path+'/members',json={'asset_key':'asset','member_kind':'component'})
                assert attached.status_code==200,attached.text
                row=next(p for p in attached.json()['platforms'] if p['id']==new['id'])
                assert row['members'][0]['assigned_round']==2
                mid=row['members'][0]['id']
                assert (await client.patch(path,json={'name':'Renamed'})).status_code==200
                for status in ('active','retired'):
                    async with factory() as s:
                        (await s.get(HostPlatform,new['id'])).status=status;await s.commit()
                    before=snapshot(engine)
                    assert (await client.patch(path,json={'name':'Bad'})).status_code==409
                    assert (await client.post(path+'/members',json={'asset_key':'other','member_kind':'component'})).status_code==409
                    assert (await client.delete(path+f'/members/{mid}')).status_code==409
                    assert snapshot(engine)==before
                for method,suffix,body in [('PATCH','',{'name':'Bad'}),('POST','/members',{'asset_key':'other','member_kind':'component'}),('DELETE','/members/2',None)]:
                    r=await client.request(method,base+'/2'+suffix,json=body)
                    assert r.status_code==404,r.text
        finally:await ae.dispose()
    asyncio.run(run())
