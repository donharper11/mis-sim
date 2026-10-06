import sys, tempfile, importlib.util
from pathlib import Path
from sqlalchemy import create_engine,event
from alembic.migration import MigrationContext
from alembic.operations import Operations
sys.path.insert(0,'/home/ubuntu/projects/mis-sim/backend/tests')
from test_host_scope_migration import migrate,seed_parents
path=Path('/home/ubuntu/projects/mis-sim/backend/alembic/versions/20261006_0012_host_scope.py')
spec=importlib.util.spec_from_file_location('host_scope_migration',path); module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
for fail_at in [1,2]:
 with tempfile.TemporaryDirectory(prefix='host_scope_failure_') as temp:
  db=Path(temp)/'test.db';engine=create_engine(f'sqlite:///{db}')
  @event.listens_for(engine,'connect')
  def enable(conn, record):conn.execute('PRAGMA foreign_keys=ON')
  migrate(f'sqlite+aiosqlite:///{db}','20261004_0011');seed_parents(engine)
  with engine.connect() as conn:
   ctx=MigrationContext.configure(conn)
   with Operations.context(ctx):
    original=module.op.batch_alter_table; calls=[0]
    def fail(*args,**kwargs):
     calls[0]+=1
     if calls[0]==fail_at:raise RuntimeError('AUDITOR_PLANTED_DDL_FAILURE')
     return original(*args,**kwargs)
    module.op.batch_alter_table=fail
    try:
     with ctx.begin_transaction(_per_migration=True):module.upgrade()
    except RuntimeError as exc: assert str(exc)=='AUDITOR_PLANTED_DDL_FAILURE',repr(exc)
    else:raise AssertionError('failure plant not triggered')
    finally:module.op.batch_alter_table=original
   assert conn.exec_driver_sql('PRAGMA foreign_keys').scalar()==1
   assert conn.exec_driver_sql('PRAGMA foreign_key_check').all()==[]
   print(f'PASS SQLite injected batch failure{fail_at}: enforcement restored on same migration connection, no FK violation',flush=True)
