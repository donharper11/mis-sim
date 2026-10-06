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

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
async def probe():
 ae=create_async_engine(url)
 factory=async_sessionmaker(ae,expire_on_commit=False)
 original=AsyncSession.execute
 async with factory() as resetting:
  fired=False
  async def intercept(self, statement, *args, **kwargs):
   nonlocal fired
   if self is resetting and not fired:
    fired=True
    print('BARRIER reset passed setup eligibility; before first schedule lock SELECT', flush=True)
    async with factory() as starting:
     result=await start_instance(starting,1,pack.pack_digest,{1:'cost_leadership'})
     await starting.commit()
     print('OTHER CONNECTION start committed',result,flush=True)
   return await original(self,statement,*args,**kwargs)
  AsyncSession.execute=intercept
  try:
   await reset_instance(resetting,1)
   await resetting.commit()
   print('OLD RESET COMMITTED',flush=True)
  finally:AsyncSession.execute=original
 async with factory() as check:
  instance=await check.get(SimulationInstance,1)
  count=await check.scalar(select(func.count()).select_from(SimulationRunV1).where(SimulationRunV1.instance_id==1))
  print('FINAL',instance.status,instance.current_round,instance.started_at,'runs',count,flush=True)
  assert instance.status=='active' and instance.current_round==1 and instance.started_at is not None and count==0
 await ae.dispose()
 print('REPRODUCED reset erased newly started generation',flush=True)
asyncio.run(probe())
