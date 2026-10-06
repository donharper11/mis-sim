import asyncio,tempfile
from pathlib import Path
from datetime import datetime,timedelta,timezone
from sqlalchemy import create_engine,select,delete
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
from test_host_scope_migration import migrate,seed_parents
from app.models.platform import Casepack,SimulationInstance,Section,User,Enrollment,Team
from app.models.host_platform import HostPlatform,HostPlatformMember
from app.simulation.models import SimulationRunV1,SimulationSheetV1
from app.simulation.content import load_runtime_pack
from app.services.instructor_start import start_instance
from app.services.platform import reset_instance
from app.scheduling.service import Scheduler
root=Path(tempfile.mkdtemp(prefix='mis_sim_instructor_start_audit_'))
url='postgresql+asyncpg://audit:audit@127.0.0.1:48183/mis_sim_verify_instructor_start_independent';engine=create_engine(url.replace('+asyncpg','+psycopg2'))
migrate(url,'20261004_0011');seed_parents(engine);migrate(url,'head')
pack=load_runtime_pack(Path('backend/packs/riverside_grocery').resolve());meta=pack.casepack.metadata
with Session(engine) as s:
 s.execute(delete(HostPlatformMember));s.execute(delete(HostPlatform))
 s.add(Casepack(pack_key=meta.pack_key,pack_version=meta.pack_version,pack_digest=pack.pack_digest,schema_version=meta.schema_version,display_name=meta.display_name,vertical=meta.vertical,rounds=meta.rounds,path=str(Path('backend/packs/riverside_grocery').resolve()),validation_json={'errors':[],'warnings':[],'exit_code':0}))
 inst=s.get(SimulationInstance,1);inst.pack_key=meta.pack_key;inst.pack_version=meta.pack_version;inst.pack_digest=pack.pack_digest;inst.total_rounds=meta.rounds
 sec=s.get(Section,1);sec.team_size_min=1
 u=User(name='Student',email='startprobe@example.test',role='student',is_active=True);s.add(u);s.flush()
 s.add(Enrollment(user_id=u.id,section_id=1,team_id=1,role='student',is_active=True));s.commit()
async def begin(restart=False):
 ae=create_async_engine(url)
 try:
  async with async_sessionmaker(ae,expire_on_commit=False)() as s:
   if restart:
    (await s.get(SimulationInstance,1)).status='setup';await s.flush()
    await reset_instance(s,1)
   result=await start_instance(s,1,pack.pack_digest,{1:'cost_leadership'});await s.commit();return result['started_at']
 finally:await ae.dispose()

import sqlite3
from app.simulation.service import SimulationService
from app.simulation.models import SimulationCheckpointV1
from app.services.instructor_start import RUNTIME_TABLES,inspect_start
with Session(engine) as s:
 s.add(Team(id=3,section_id=1,instance_id=1,name='Second team'));s.flush()
 u=User(name='Second student',email='startprobe2@example.test',role='student',is_active=True);s.add(u);s.flush()
 s.add(Enrollment(user_id=u.id,section_id=1,team_id=3,role='student',is_active=True));s.commit()

from concurrent.futures import ThreadPoolExecutor
from threading import Event,current_thread
import time
from sqlalchemy import text
ready=Event();release=Event();second_pid=[]
original=SimulationService.initialize_in_session
def held(self,session,iid,tid,strategy):
 result=original(self,session,iid,tid,strategy)
 if current_thread().name.startswith('starter') and tid==1:
  ready.set();assert release.wait(20)
 return result
SimulationService.initialize_in_session=held
choices={1:'cost_leadership',3:'differentiation'}
async def attempt(second=False):
 ae=create_async_engine(url)
 try:
  async with async_sessionmaker(ae,expire_on_commit=False)() as s:
   if second:second_pid.append(await s.scalar(text('SELECT pg_backend_pid()')))
   try:
    result=await start_instance(s,1,pack.pack_digest,choices);await s.commit();return ('success',result)
   except Exception as exc:
    await s.rollback();return (type(exc).__name__,str(exc))
 finally:await ae.dispose()
with ThreadPoolExecutor(1,thread_name_prefix='starter') as firstpool, ThreadPoolExecutor(1,thread_name_prefix='duplicate') as secondpool:
 first=firstpool.submit(lambda:asyncio.run(attempt()))
 assert ready.wait(20)
 second=secondpool.submit(lambda:asyncio.run(attempt(True)))
 deadline=time.monotonic()+10;blocked=None
 while time.monotonic()<deadline:
  if second_pid:
   with engine.connect() as c:blocked=c.execute(text('SELECT wait_event_type,query FROM pg_stat_activity WHERE pid=:pid'),{'pid':second_pid[0]}).first()
   if blocked and blocked[0]=='Lock':break
  time.sleep(.03)
 try:
  assert blocked and blocked[0]=='Lock' and 'section' in blocked[1],blocked
  print('PASS second start observed waiting on section lock')
 finally:release.set()
 firstresult=first.result(timeout=20);secondresult=second.result(timeout=20)
 assert firstresult[0]=='success',firstresult
 assert secondresult[0]=='PlatformConflict',secondresult
 print(firstresult);print(secondresult)
SimulationService.initialize_in_session=original
with Session(engine) as s:
 assert len(list(s.scalars(select(SimulationRunV1).where(SimulationRunV1.instance_id==1))))==2
 assert s.get(SimulationInstance,1).started_at==firstresult[1]['started_at']
print('PASS exactly one start; duplicate conflict; first timestamp and two initialized teams preserved')
