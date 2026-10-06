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
from app.api import runtime_review
from app.models.scheduling import RoundSchedule,RoundScheduleTeam
original_to_thread=asyncio.to_thread
new_snapshot=None
async def request():
 global new_snapshot
 ae=create_async_engine(url);factory=async_sessionmaker(ae,expire_on_commit=False)
 async def intercepted(func,*args,**kwargs):
  global new_snapshot
  result=await original_to_thread(func,*args,**kwargs)
  if func.__name__=='lock_run':
   await begin(True);schedule()
   with sqlite3.connect(root/'probe.db') as c:new_snapshot='\n'.join(c.iterdump())
  return result
 runtime_review.make_engine=lambda:create_engine(url.replace('+aiosqlite',''))
 asyncio.to_thread=intercepted
 try:
  async with factory() as session:
   instance=await session.get(SimulationInstance,1);user=await session.get(User,1)
   result=await runtime_review.lock_review(runtime_review.ReviewLockIn(expected_revision=0),instance,user,session,team_id=1)
   print('response_status',result.team.status)
 finally:
  asyncio.to_thread=original_to_thread
  await ae.dispose()
asyncio.run(request())
with Session(engine) as s:
 print('new sheet',s.get(SimulationSheetV1,(1,1,1)).locked_revision)
 print('new schedule',s.get(RoundSchedule,1).decisions_locked,'new participant',s.get(RoundScheduleTeam,(1,1)).locked_revision)
with sqlite3.connect(root/'probe.db') as c:print('exact_new_generation_unchanged','\n'.join(c.iterdump())==new_snapshot)
