import json,sys
from datetime import datetime,timedelta,timezone
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy.orm import Session
from app.round.db import make_engine
from app.scheduling.service import Scheduler
URL='postgresql://readiness:readiness@127.0.0.1:44535/mis_sim_browser_host_lifecycle_review'
mode=sys.argv[1]
if mode=='schedule':
 engine=make_engine()
 with Session(engine) as s:
  scheduler=Scheduler(s);now=datetime.now(timezone.utc)
  scheduler.set_schedule(2,1,now-timedelta(hours=2),now-timedelta(hours=1),auto_advance=True);s.commit()
  print(json.dumps(scheduler.tick(now)))
 engine.dispose()
else:
 with psycopg2.connect(URL) as db:
  with db.cursor(cursor_factory=RealDictCursor) as c:
   if mode=='setup':
    c.execute("UPDATE simulation_instance SET status='setup' WHERE instance_id=1")
    print('{}')
   elif mode=='snapshot':
    c.execute("SELECT table_name FROM information_schema.columns WHERE table_schema='public' AND column_name='instance_id' ORDER BY table_name")
    tables=[r['table_name'] for r in c.fetchall()];out={}
    for t in tables:
     c.execute('SELECT * FROM "'+t+'" ORDER BY row_to_json("'+t+'")::text');out[t]=[dict(r) for r in c.fetchall()]
    for t in ['user','enrollment','team','section','course']:
     c.execute("SELECT EXISTS(SELECT FROM information_schema.tables WHERE table_name=%s)",(t,))
     if c.fetchone()['exists']:
      c.execute('SELECT * FROM "'+t+'" ORDER BY row_to_json("'+t+'")::text');out[t]=[dict(r) for r in c.fetchall()]
    print(json.dumps(out,default=str,sort_keys=True))
