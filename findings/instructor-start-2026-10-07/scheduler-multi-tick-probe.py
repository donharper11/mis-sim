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
with Session(engine) as s:
 Scheduler(s).set_schedule(1,2,now-timedelta(hours=1),now+timedelta(hours=3),auto_advance=False,grace_period_minutes=0);s.commit()
from app.scheduling.service import Scheduler
original_claim=Scheduler._claim
triggered=False
def intercepted_claim(self,schedule_row,at,**kwargs):
 global triggered,new_snapshot
 if not triggered:
  triggered=True
  asyncio.run(begin(True));new_id=schedule()
  with sqlite3.connect(root/'probe.db') as c:new_snapshot='\n'.join(c.iterdump())
 return original_claim(self,schedule_row,at,**kwargs)
Scheduler._claim=intercepted_claim
try:
 with Session(engine) as s:
  try:print('tick_result',Scheduler(s).tick(now))
  except Exception as exc:print('tick_exception',type(exc).__name__,str(exc))
finally:Scheduler._claim=original_claim
with sqlite3.connect(root/'probe.db') as c:assert '\n'.join(c.iterdump())==new_snapshot
print('new generation unchanged')
