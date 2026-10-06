"""Authenticated host CRUD across real initialized team and instance boundaries."""
import asyncio
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.api import deps
from app.main import create_app
from app.models.platform import User, Enrollment, SimulationInstance
from app.models.host_platform import HostPlatformMember
from app.simulation.models import SimulationSheetV1
from app.services.auth import create_access_token


def test_host_member_crud_scope_and_editability():
    with tempfile.TemporaryDirectory(prefix='mis_sim_browser_host_api_', dir='/tmp') as directory:
        db = Path(directory) / 'fixture.db'
        result = subprocess.run([sys.executable, str(Path(__file__).parents[1] / 'scripts' / 'seed_readiness_demo.py'), '--database-url', f'sqlite+aiosqlite:///{db}'], env={**os.environ, 'SECRET_KEY': os.environ['SECRET_KEY']}, capture_output=True, text=True, timeout=90)
        assert result.returncode == 0, result.stdout + result.stderr

        async def run():
            engine = create_async_engine(f'sqlite+aiosqlite:///{db}')
            factory = async_sessionmaker(engine, expire_on_commit=False)
            async def get_session():
                async with factory() as session:
                    yield session
            app = create_app(); app.dependency_overrides[deps.get_session] = get_session
            headers = {}
            async with factory() as s:
                for student in ['M2-101', 'M2-102', 'M2-105', 'M2-108', 'M2-201']:
                    user = await s.scalar(select(User).where(User.student_id == student))
                    enrollment = await s.scalar(select(Enrollment).where(Enrollment.user_id == user.id))
                    instance = await s.scalar(select(SimulationInstance).where(SimulationInstance.section_id == enrollment.section_id))
                    headers[student] = {'Authorization': 'Bearer ' + create_access_token(user_id=user.id, role='student', section_id=enrollment.section_id, instance_id=instance.instance_id)}
                    if student == 'M2-108': enrollment.team_id = None
                await s.commit()
            async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
                a, mate, b, unassigned, c = (headers[k] for k in ['M2-101','M2-102','M2-105','M2-108','M2-201'])
                prefix = '/api/instances/1/host-platforms'
                async def request(method, path, h=a, data=None, status=200):
                    r = await client.request(method, path, headers=h, json=data)
                    assert r.status_code == status, r.text
                    return r.json()
                created = await request('POST', prefix, data={'platform_type':'on_prem','name':'Scope host'})
                host = created['platforms'][0]['id']
                path = f'{prefix}/{host}'
                renamed = await request('PATCH', path, data={'name':'Renamed'})
                assert renamed['platforms'][0]['name'] == 'Renamed'
                rollout = await request('GET','/api/instances/1/rollout')
                asset = rollout['team']['deployments'][0]['id']
                body = {'asset_key':asset,'member_kind':'component','instance_id':2}
                attached = await request('POST',path+'/members',data=body)
                member = attached['platforms'][0]['members'][0]['id']
                async with factory() as s:
                    assert (await s.get(HostPlatformMember, member)).instance_id == 1
                assert (await request('GET',prefix,h=mate))['platforms'][0]['members'][0]['id'] == member
                rollout = await request('GET','/api/instances/1/rollout')
                assert next(d for d in rollout['team']['deployments'] if d['id']==asset)['platform_id'] == host
                assert (await request('GET',prefix,h=b))['platforms'] == []
                assert (await request('GET','/api/instances/2/host-platforms',h=c))['platforms'] == []
                for foreign, code in [(b,404),(c,403)]:
                    await request('PATCH',path,h=foreign,data={'name':'Bad'},status=code)
                    await request('POST',path+'/members',h=foreign,data=body,status=code)
                    await request('DELETE',f'{path}/members/{member}',h=foreign,status=code)
                assert (await request('GET',prefix+'?team_id=1',h=unassigned))['platforms'] == []
                await request('POST',prefix,h=unassigned,data={'platform_type':'on_prem','name':'Bad'},status=409)
                for mode in ['locked','paused','completed']:
                    async with factory() as s:
                        inst=await s.get(SimulationInstance,1)
                        sheet=await s.get(SimulationSheetV1,(1,1,1))
                        inst.status='active' if mode=='locked' else mode
                        sheet.locked_revision=sheet.revision if mode=='locked' else None
                        await s.commit()
                    await request('PATCH',path,data={'name':'Bad'},status=409)
                    await request('POST',path+'/members',data=body,status=409)
                    await request('DELETE',f'{path}/members/{member}',status=409)
                    await request('POST',prefix,data={'platform_type':'on_prem','name':'Bad'},status=409)
                async with factory() as s:
                    (await s.get(SimulationInstance,1)).status='active'
                    await s.commit()
                removed=await request('DELETE',f'{path}/members/{member}')
                assert removed['platforms'][0]['members']==[]
                assert next(d for d in (await request('GET','/api/instances/1/rollout'))['team']['deployments'] if d['id']==asset)['platform_id'] is None
            app.dependency_overrides.clear()
            await engine.dispose()
        asyncio.run(run())
