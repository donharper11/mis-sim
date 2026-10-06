import asyncio,tempfile,sqlite3
from pathlib import Path
from datetime import datetime,timedelta,timezone
from sqlalchemy import create_engine,select,delete
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
from test_host_scope_migration import migrate,seed_parents
from app.models.platform import Casepack,SimulationInstance,Section,User,Enrollment
from app.models.host_platform import HostPlatform,HostPlatformMember
from app.simulation.models import SimulationRunV1,SimulationSheetV1
from app.simulation.content import load_runtime_pack
from app.services.instructor_start import start_instance
from app.services.platform import reset_instance
from app.scheduling.service import Scheduler
from app.models.scheduling import RoundSchedule
root=Path(tempfile.mkdtemp(prefix='mis_sim_instructor_start_audit_'))
url=f'sqlite+aiosqlite:///{root}/probe.db';engine=create_engine(url.replace('+aiosqlite',''))
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
first=asyncio.run(begin())
now=datetime.now(timezone.utc)
def schedule():
 with Session(engine) as s:
  row=Scheduler(s).set_schedule(1,1,now-timedelta(hours=2),now+timedelta(hours=2),auto_advance=False,grace_period_minutes=0);s.commit();return row.id
old_id=schedule()
with Session(engine,expire_on_commit=False) as s:
 original=s.scalar;triggered=False;new_snapshot=None
 def intercepted(statement,*args,**kwargs):
  global triggered,new_snapshot
  if not triggered and str(statement).startswith('SELECT round_schedule.id'):
   triggered=True
   second=asyncio.run(begin(True));new_id=schedule()
   print('generations',first.isoformat(),second.isoformat(),'schedule ids',old_id,new_id)
   with sqlite3.connect(root/'probe.db') as snapshot_connection:new_snapshot='\n'.join(snapshot_connection.iterdump())
  return original(statement,*args,**kwargs)
 s.scalar=intercepted
 result=Scheduler(s).lock_now(1,1,now)
 print('old_operation_result',result)
with Session(engine) as s:
 print('new_schedule_reason',s.get(RoundSchedule,1).lock_reason)
 print('new_generation_run',s.get(SimulationRunV1,(1,1)).status,'locked_revision',s.get(SimulationSheetV1,(1,1,1)).locked_revision)

with sqlite3.connect(root/"probe.db") as c:assert "\n".join(c.iterdump())==new_snapshot
print("PASS exact new-generation SQL dump unchanged")
