"""Audit-only mutation: preserve locks but remove fresh instance refresh."""
import pytest
from sqlalchemy import select
from app.models.platform import SimulationInstance
from app.services import platform
original = platform.setup_instance
async def stale_instance(session, section_id):
    return await session.scalar(select(SimulationInstance).where(
        SimulationInstance.section_id == section_id,
    ).with_for_update(key_share=True))
platform.setup_instance = stale_instance
try:
    code = pytest.main(['-q', 'backend/tests/test_instructor_start_concurrency.py',
                       '-k', 'start_wins_setup_mutator_rechecks_cached_status and enrollment_assign'])
    assert code == pytest.ExitCode.TESTS_FAILED, f'Plant did not fail: {code}'
    print('PASS falsification: removing refresh caused the expected concurrency regression')
finally:
    platform.setup_instance = original
