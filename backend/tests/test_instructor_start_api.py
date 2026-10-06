"""Public start contract and requests spanning a reset/restart, on migrated databases."""
import asyncio
from copy import deepcopy

from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine

from app.api import deps, instructor, runtime_components, runtime_controls, runtime_platform, runtime_rollout, runtime_review, runtime_round_control
from app.main import create_app
from app.models.platform import SimulationInstance
from app.services.auth import create_access_token
from app.services.platform import reset_instance
from app.simulation.service import SimulationService
from test_instructor_start import database, snapshot, start  # noqa: F401


def app_for(db):
    app = create_app()
    async def sessions():
        async with db.factory() as session:
            yield session
    for module in (deps, instructor):
        app.dependency_overrides[module.get_session] = sessions
    return app


def headers(uid=1, role='instructor'):
    return {'Authorization': f'Bearer {create_access_token(user_id=uid, role=role)}'}


async def restart(db):
    async with db.factory() as session:
        (await session.get(SimulationInstance, 1)).status = 'setup'
        await session.flush()
        await reset_instance(session, 1)
        await session.commit()
    return await start(db)


def test_public_start_routes_authorization_validation_and_retry(database):
    db = database
    before = snapshot(db)
    payload = {'confirm_instance_id': 1, 'expected_pack_digest': db.packs[1].pack_digest,
               'team_strategies': [{'team_id': tid, 'strategy_key': key} for tid, key in db.choices.items()]}
    async def run():
        async with AsyncClient(transport=ASGITransport(app=app_for(db)), base_url='http://test') as client:
            base = '/api/instructor/instances/1'
            for auth, status in [({}, 401), (headers(2, 'student'), 403), (headers(20, 'ta'), 403), (headers(18), 403)]:
                assert (await client.get(base+'/start-readiness', headers=auth)).status_code == status
                assert (await client.post(base+'/start', headers=auth, json=payload)).status_code == status
            for auth in (headers(), headers(19, 'admin')):
                response = await client.get(base+'/start-readiness', headers=auth)
                assert response.status_code == 200, response.text
                body = response.json()
                assert body['ready'] and body['blocked_reasons'] == []
                assert [t['student_count'] for t in body['teams']] == [4, 4]
                assert {s['key'] for s in body['strategies']} == {s.key for s in db.packs[1].casepack.strategies}
            variants = []
            for key, value in [('confirm_instance_id', 2), ('confirm_instance_id', '1'), ('extra', True), ('team_strategies', payload['team_strategies']*2)]:
                item = deepcopy(payload); item[key] = value; variants.append((item, 422))
            item = deepcopy(payload); item['team_strategies'][0]['strategy_key'] = 'invalid'; variants.append((item, 422))
            item = deepcopy(payload); item['team_strategies'][0]['team_id'] = 3; variants.append((item, 409))
            item = deepcopy(payload); item['expected_pack_digest'] = 'stale'; variants.append((item, 409))
            for item, status in variants:
                response = await client.post(base+'/start', headers=headers(), json=item)
                assert response.status_code == status, response.text
                assert snapshot(db) == before
            response = await client.post(base+'/start', headers=headers(19, 'admin'), json=payload)
            assert response.status_code == 200, response.text
            assert response.json()['team_ids'] == [1, 2]
            after = snapshot(db)
            assert (await client.post(base+'/start', headers=headers(), json=payload)).status_code == 409
            changed = deepcopy(payload)
            changed['team_strategies'][0]['strategy_key'] = 'invalid'
            assert (await client.post(base+'/start', headers=headers(), json=changed)).status_code == 409
            assert snapshot(db) == after
    asyncio.run(run())


def test_http_mutation_producers_reject_old_generation_before_service(database, monkeypatch):
    db = database
    modules = [runtime_components, runtime_controls, runtime_platform, runtime_rollout, runtime_review, runtime_round_control]
    for module in modules:
        monkeypatch.setattr(module, 'make_engine', lambda: create_engine(db.engine.url))
    original = asyncio.to_thread
    cases = [
        ('PATCH', 'platform', {'expected_revision': 0, 'commands': []}, 'apply_patch'),
        ('PATCH', 'components', {'expected_revision': 0, 'replace_categories': {}}, 'apply_patch'),
        ('PATCH', 'rollout', {'expected_revision': 0, 'replace_categories': {}}, 'apply_patch'),
        ('PATCH', 'controls/strategy', {'expected_revision': 0, 'commands': []}, 'apply_patch'),
        ('POST', 'review/lock', {'expected_revision': 0}, 'lock_run'),
        ('POST', 'round-control/lock', None, 'lock_one'),
        ('POST', 'round-control/advance', None, 'advance_one'),
        ('POST', 'round-control/reopen', {'team_id': 1}, 'reopen_one'),
    ]
    async def run():
        await start(db)
        async with AsyncClient(transport=ASGITransport(app=app_for(db)), base_url='http://test') as client:
            for method, route, payload, name in cases:
                await restart(db)
                if route.endswith('/reopen'):
                    SimulationService(db.engine, db.packs[1]).lock(1, 1, 1, 0)
                captured = []
                async def interleave(func, *args, **kwargs):
                    if func.__name__ == name and not captured:
                        await restart(db)
                        captured.append(snapshot(db))
                    return await original(func, *args, **kwargs)
                with monkeypatch.context() as patch:
                    patch.setattr(asyncio, 'to_thread', interleave)
                    response = await client.request(method, '/api/instances/1/'+route+'?team_id=1', headers=headers(), json=payload)
                assert captured, (route, response.text)
                assert response.status_code == 409, (route, response.text)
                assert snapshot(db) == captured[0], route
    asyncio.run(run())


def test_review_metadata_publication_rejects_generation_replacement(database, monkeypatch):
    db = database
    monkeypatch.setattr(runtime_review, 'make_engine', lambda: create_engine(db.engine.url))
    original = asyncio.to_thread
    captured = []
    async def interleave(func, *args, **kwargs):
        result = await original(func, *args, **kwargs)
        if func.__name__ == 'lock_run':
            await restart(db)
            captured.append(snapshot(db))
        return result
    async def run():
        await start(db)
        with monkeypatch.context() as patch:
            patch.setattr(asyncio, 'to_thread', interleave)
            async with AsyncClient(transport=ASGITransport(app=app_for(db)), base_url='http://test') as client:
                response = await client.post('/api/instances/1/review/lock?team_id=1', headers=headers(), json={'expected_revision': 0})
        assert response.status_code == 409, response.text
        assert captured and snapshot(db) == captured[0]
    asyncio.run(run())


def test_manual_advance_generation_barriers(database, monkeypatch):
    """Matching run IDs/revisions after reset must never admit an old batch."""
    db = database
    monkeypatch.setattr(runtime_round_control, 'make_engine', lambda: create_engine(db.engine.url))
    original_lock, original_advance = SimulationService.lock, SimulationService.advance
    async def run():
        await start(db)
        async with AsyncClient(transport=ASGITransport(app=app_for(db)), base_url='http://test') as client:
            for phase in ('before_lock', 'between_lock_advance', 'later_team', 'after_final_commit'):
                await restart(db)
                captured = []
                def replace_generation():
                    asyncio.run(restart(db))
                    # Bring replacement to the same final-round pointer, defeating
                    # a fence that checks only round/advanced_round but not generation.
                    if phase == 'after_final_commit':
                        service = SimulationService(db.engine, db.packs[1])
                        for tid in (1, 2):
                            original_lock(service, 1, tid, 1, 0)
                            original_advance(service, 1, tid, 1, 0)
                    captured.append(snapshot(db))
                def lock(service, iid, tid, *args, **kwargs):
                    if not captured and (phase == 'before_lock' or (phase == 'later_team' and tid == 2)):
                        replace_generation()
                    result = original_lock(service, iid, tid, *args, **kwargs)
                    if not captured and phase == 'between_lock_advance':
                        replace_generation()
                    return result
                def advance(service, iid, tid, *args, **kwargs):
                    result = original_advance(service, iid, tid, *args, **kwargs)
                    if phase == 'after_final_commit' and tid == 2 and not captured:
                        replace_generation()
                    return result
                with monkeypatch.context() as patch:
                    patch.setattr(SimulationService, 'lock', lock)
                    patch.setattr(SimulationService, 'advance', advance)
                    response = await client.post('/api/instances/1/round-control/advance', headers=headers())
                assert captured and response.status_code == 409, (phase, response.text)
                assert snapshot(db) == captured[0], phase
    asyncio.run(run())


def test_host_metadata_request_rejects_old_generation(database, monkeypatch):
    from app.api import runtime_host_platform
    db = database
    original = runtime_host_platform._require_editable
    captured = []
    async def interleave(session, instance, team):
        await restart(db)
        captured.append(snapshot(db))
        return await original(session, instance, team)
    async def run():
        await start(db)
        with monkeypatch.context() as patch:
            patch.setattr(runtime_host_platform, '_require_editable', interleave)
            async with AsyncClient(transport=ASGITransport(app=app_for(db)), base_url='http://test') as client:
                response = await client.post('/api/instances/1/host-platforms?team_id=1', headers=headers(),
                                            json={'platform_type': 'on_prem', 'name': 'Old request'})
        assert response.status_code == 409, response.text
        assert captured and snapshot(db) == captured[0]
    asyncio.run(run())
