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
strategies=[item.key for item in pack.casepack.strategies]
choices={1:strategies[0],3:strategies[1]}
def dump():
 with sqlite3.connect(root/'probe.db') as c:return '\n'.join(c.iterdump())
async def start():
 ae=create_async_engine(url)
 try:
  async with async_sessionmaker(ae,expire_on_commit=False)() as s:
   try:
    result=await start_instance(s,1,pack.pack_digest,choices);await s.commit();return result
   except Exception:
    await s.rollback();raise
 finally:await ae.dispose()
original=SimulationService.initialize_in_session
def fail_second(self,session,iid,tid,strategy):
 if tid==3:raise RuntimeError('independent late-team failure')
 return original(self,session,iid,tid,strategy)
before=dump();SimulationService.initialize_in_session=fail_second
try:
 try:asyncio.run(start())
 except RuntimeError as exc:assert 'late-team' in str(exc)
 else:raise AssertionError('expected failure')
finally:SimulationService.initialize_in_session=original
assert dump()==before
print('PASS late second-team failure: entire SQL dump identical')
result=asyncio.run(start());print('started',result)
with Session(engine) as s:
 for tid,strategy in choices.items():
  from app.simulation.estate import initialize_state
  from app.simulation.service import _state_payload,_state_digest
  state=initialize_state(pack,strategy);row=s.get(SimulationCheckpointV1,(1,tid,0))
  assert row.state==_state_payload(state) and row.state_digest==_state_digest(state)
  assert s.get(SimulationSheetV1,(1,tid,1)).commands==[]
 for model in RUNTIME_TABLES:
  rows=list(s.scalars(select(model).where(model.instance_id==1)))
  assert len(rows)==(2 if model in (SimulationRunV1,SimulationSheetV1,SimulationCheckpointV1) else 0),(model,len(rows))
print('PASS explicit different strategies yield exact initial state/digests; only six intended runtime rows')
before=dump()
try:asyncio.run(start())
except Exception as exc:print('duplicate',type(exc).__name__,str(exc))
else:raise AssertionError('duplicate accepted')
assert dump()==before
print('PASS duplicate start unchanged full SQL dump')
