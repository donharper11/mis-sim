"""Real populated migrations and FK falsification on SQLite and opt-in disposable PG.

HOST_SCOPE_POSTGRES_URL must name a dedicated mis_sim_verify_host_scope_* database;
this fixture drops its public schema. Never point it at browser/concurrency databases.
"""
import os
from pathlib import Path
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.platform import User, Course, Section, SimulationInstance, Team

BACKEND = Path(__file__).parents[1]


def migrate(url, revision, direction='upgrade', success=True):
    result = subprocess.run([sys.executable, '-m', 'alembic', direction, revision], cwd=BACKEND,
        env={**os.environ, 'DATABASE_URL': str(url), 'SECRET_KEY': 'host-scope-test-only'}, capture_output=True, text=True, timeout=90)
    if success:
        assert result.returncode == 0, result.stdout + result.stderr
    else:
        assert result.returncode != 0
        assert 'Host scope preflight failed' in result.stderr
    return result


def seed_parents(engine):
    with Session(engine) as s:
        u = User(name='Instructor', email='scope@example.test', role='instructor')
        s.add(u); s.flush()
        c = Course(course_code='scope', course_name='Scope', academic_year='2026', semester='A', instructor_id=u.id)
        s.add(c); s.flush()
        for n in (1, 2):
            sec = Section(id=n, course_id=c.id, section_code=str(n), section_name=f'Section {n}')
            s.add(sec); s.flush()
            inst = SimulationInstance(instance_id=n, section_id=n, pack_key='test', pack_version='1', settings={})
            s.add(inst); s.flush()
            s.add(Team(id=n, section_id=n, instance_id=n, name=f'Team {n}')); s.flush()
        s.commit()
    with engine.begin() as c:
        for n in (1, 2):
            c.execute(text("INSERT INTO host_platform(id,instance_id,team_id,platform_code,name,notes,platform_type,status,created_round,activated_round) VALUES (:n,:n,:n,'OP01','Preserved','notes','on_prem','pending',1,2)"), {'n': n})
            c.execute(text("INSERT INTO host_platform_member(id,platform_id,asset_key,member_kind,assigned_round) VALUES (:n,:n,'same_asset','component',1)"), {'n': n})


@pytest.fixture(params=['sqlite', 'postgres'])
def database(request, tmp_path):
    if request.param == 'postgres':
        raw = os.environ.get('HOST_SCOPE_POSTGRES_URL')
        if not raw:
            pytest.skip('set HOST_SCOPE_POSTGRES_URL to a dedicated disposable DB')
        url = make_url(raw)
        assert url.host == '127.0.0.1' and url.port and not url.query
        assert url.database.startswith('mis_sim_verify_host_scope_')
        async_url = url.set(drivername='postgresql+asyncpg').render_as_string(hide_password=False)
        engine = create_engine(url.set(drivername='postgresql+psycopg2'))
        with engine.begin() as c:
            c.execute(text('DROP SCHEMA public CASCADE')); c.execute(text('CREATE SCHEMA public'))
    else:
        filename = tmp_path / 'migration.db'
        async_url = f'sqlite+aiosqlite:///{filename}'
        engine = create_engine(f'sqlite:///{filename}')
        @event.listens_for(engine, 'connect')
        def enforce(dbapi, _):
            dbapi.execute('PRAGMA foreign_keys=ON')
    migrate(async_url, '20261004_0011')
    seed_parents(engine)
    yield engine, async_url
    engine.dispose()


def snapshot(engine):
    with engine.connect() as c:
        return {name: list(c.execute(text(f'SELECT * FROM {name} ORDER BY 1')).mappings()) for name in ('host_platform', 'host_platform_member')}


def test_populated_upgrade_downgrade_constraints_and_cascades(database):
    engine, url = database
    original = snapshot(engine)
    migrate(url, '20261006_0012')
    current = snapshot(engine)
    assert current['host_platform'] == original['host_platform']
    for old, new in zip(original['host_platform_member'], current['host_platform_member']):
        assert dict(new) == {**old, 'instance_id': old['platform_id']}
    inspector = inspect(engine)
    assert len(inspector.get_table_names()) == 33
    assert not next(c for c in inspector.get_columns('host_platform_member') if c['name'] == 'instance_id')['nullable']
    assert any(f['constrained_columns'] == ['platform_id', 'instance_id'] for f in inspector.get_foreign_keys('host_platform_member'))
    invalid = [
        "INSERT INTO host_platform_member(id,instance_id,platform_id,asset_key,member_kind,assigned_round) VALUES (9,2,1,'x','component',1)",
        "UPDATE host_platform_member SET instance_id=2 WHERE id=1",
        "INSERT INTO host_platform(id,instance_id,team_id,platform_code,name,platform_type,status,created_round) VALUES (9,1,2,'BAD','bad','on_prem','pending',1)",
        "UPDATE host_platform SET team_id=2 WHERE id=1",
        "INSERT INTO host_platform_member(id,platform_id,asset_key,member_kind,assigned_round) VALUES (9,1,'x','component',1)",
        "UPDATE host_platform_member SET instance_id=NULL WHERE id=1",
        "INSERT INTO host_platform_member(id,instance_id,platform_id,asset_key,member_kind,assigned_round) VALUES (9,999,1,'x','component',1)",
        "INSERT INTO host_platform_member(id,instance_id,platform_id,asset_key,member_kind,assigned_round) VALUES (9,1,999,'x','component',1)",
    ]
    for sql in invalid:
        with pytest.raises(IntegrityError), engine.begin() as c:
            c.execute(text(sql))
    with engine.connect() as c:
        tx = c.begin()
        c.execute(text("INSERT INTO host_platform_member(id,instance_id,platform_id,asset_key,member_kind,assigned_round) VALUES (9,1,1,'valid','component',1)"))
        tx.rollback()
    # Preserve original semantics: same key across different hosts is allowed.
    assert len([r for r in current['host_platform_member'] if r['asset_key'] == 'same_asset']) == 2
    for parent, key in [('host_platform','id'), ('team','id'), ('simulation_instance','instance_id')]:
        with engine.connect() as c:
            tx = c.begin()
            c.execute(text(f'DELETE FROM {parent} WHERE {key}=1'))
            assert c.execute(text('SELECT count(*) FROM host_platform_member WHERE instance_id=1')).scalar() == 0
            assert c.execute(text('SELECT count(*) FROM host_platform_member WHERE instance_id=2')).scalar() == 1
            tx.rollback()
    migrate(url, '20261004_0011', 'downgrade')
    assert snapshot(engine) == original
    assert 'instance_id' not in {c['name'] for c in inspect(engine).get_columns('host_platform_member')}
    migrate(url, '20261006_0012')
    assert snapshot(engine) == current
    with engine.connect() as c:
        assert c.execute(text('SELECT version_num FROM alembic_version')).scalar() == '20261006_0012'
        if engine.dialect.name == 'sqlite':
            assert c.exec_driver_sql('PRAGMA foreign_keys').scalar() == 1
            assert not c.exec_driver_sql('PRAGMA foreign_key_check').all()


@pytest.mark.parametrize('plant', [
    'UPDATE host_platform SET team_id=2 WHERE id=1',
    'UPDATE host_platform SET team_id=999 WHERE id=1',
    'UPDATE host_platform SET instance_id=999 WHERE id=1',
    'UPDATE host_platform_member SET platform_id=999 WHERE id=1',
])
def test_invalid_history_refused_without_changes(database, plant):
    engine, url = database
    with engine.connect() as c:
        if engine.dialect.name == 'sqlite':
            c.exec_driver_sql('PRAGMA foreign_keys=OFF'); c.commit()
        else:
            c.execute(text("SET session_replication_role='replica'")); c.commit()
        try:
            c.execute(text(plant)); c.commit()
        finally:
            c.exec_driver_sql('PRAGMA foreign_keys=ON' if engine.dialect.name == 'sqlite' else "SET session_replication_role='origin'"); c.commit()
    before = snapshot(engine)
    schema_before = {t: (inspect(engine).get_columns(t), inspect(engine).get_foreign_keys(t), inspect(engine).get_unique_constraints(t)) for t in before}
    migrate(url, '20261006_0012', success=False)
    assert snapshot(engine) == before
    for table in before:
        columns, fks, uniques = schema_before[table]
        assert [c['name'] for c in inspect(engine).get_columns(table)] == [c['name'] for c in columns]
        assert inspect(engine).get_foreign_keys(table) == fks
        assert inspect(engine).get_unique_constraints(table) == uniques
    with engine.connect() as c:
        assert c.execute(text('SELECT version_num FROM alembic_version')).scalar() == '20261004_0011'
