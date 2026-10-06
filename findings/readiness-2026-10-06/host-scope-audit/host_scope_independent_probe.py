import sys, tempfile
from pathlib import Path
from sqlalchemy import create_engine, text, inspect, select, event
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
sys.path.insert(0, '/home/ubuntu/projects/mis-sim/backend/tests')
from test_host_scope_migration import migrate, seed_parents
from app.models.host_platform import HostPlatform, HostPlatformMember

pg='postgresql+psycopg2://readiness@127.0.0.1:44535/mis_sim_verify_host_scope_audit'
for dialect in ['postgresql','sqlite']:
    if dialect=='postgresql':
        engine=create_engine(pg)
        url=pg.replace('+psycopg2','+asyncpg')
        with engine.begin() as c:
            c.execute(text('DROP SCHEMA public CASCADE')); c.execute(text('CREATE SCHEMA public'))
    else:
        temp=tempfile.TemporaryDirectory(prefix='host_scope_audit_')
        db=Path(temp.name)/'test.db'
        engine=create_engine(f'sqlite:///{db}'); url=f'sqlite+aiosqlite:///{db}'
        @event.listens_for(engine,'connect')
        def enable(conn, record): conn.execute('PRAGMA foreign_keys=ON')
    migrate(url,'20261004_0011'); seed_parents(engine)
    with engine.begin() as c:
        for hid,iid in [(101,2),(202,1)]:
            c.execute(text("INSERT INTO host_platform(id,instance_id,team_id,platform_code,name,platform_type,status,created_round) VALUES (:h,:i,:i,'AUDIT','Nonaligned','on_prem','pending',1)"),{'h':hid,'i':iid})
        c.execute(text('UPDATE host_platform_member SET platform_id=101 WHERE id=1'))
        c.execute(text('UPDATE host_platform_member SET platform_id=202 WHERE id=2'))
        c.execute(text('DELETE FROM host_platform WHERE id IN (1,2)'))
    def all_rows():
        with engine.connect() as c:
            return {n: sorted([dict(r) for r in c.execute(text(f'SELECT * FROM "{n}"')).mappings()], key=repr) for n in inspect(engine).get_table_names() if n!='alembic_version'}
    before=all_rows(); migrate(url,'head'); after=all_rows()
    for n in before:
        expected=before[n]
        if n=='host_platform_member': expected=[{**r,'instance_id':2 if r['platform_id']==101 else 1} for r in expected]
        assert after[n]==expected, n
    with Session(engine) as s:
        hosts=s.scalars(select(HostPlatform).options(selectinload(HostPlatform.members)).order_by(HostPlatform.id)).all()
        assert [(h.id,[(m.platform_id,m.instance_id) for m in h.members]) for h in hosts]==[(101,[(101,2)]),(202,[(202,1)])]
        assert s.get(HostPlatformMember,1).platform.instance_id==2
        s.delete(hosts[0]); s.flush()
        assert s.scalar(select(HostPlatformMember.id).where(HostPlatformMember.instance_id==2)) is None
        assert s.scalar(select(HostPlatformMember.id).where(HostPlatformMember.instance_id==1))==2
        s.rollback()
    for stmt in ['UPDATE host_platform_member SET platform_id=202 WHERE id=1','UPDATE host_platform SET instance_id=1 WHERE id=101']:
        try:
            with engine.begin() as c: c.execute(text(stmt))
        except IntegrityError: pass
        else: raise AssertionError(stmt)
    migrate(url,'20261004_0011','downgrade'); assert all_rows()==before
    migrate(url,'head'); assert all_rows()==after
    print(f'PASS {dialect}: all 32 tables preserved, nonaligned backfill, eager/lazy joins, loaded ORM cascade, update rejection and round-trip',flush=True)
    engine.dispose()
