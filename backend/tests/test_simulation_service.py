"""P5 service transaction, revision and detached-state checks."""

from pathlib import Path
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models.base import Base
from app.models import platform as platform_models
from app.round import models as round_models
from app.simulation import models as simulation_models
from app.simulation.content import load_runtime_pack
from app.simulation.service import SimulationService
from app.simulation.types import CommandV1, SheetPatchV1, SimulationError
from app.models import scheduling as scheduling_models
from app.models.scheduling import RoundSchedule


PACK = Path(__file__).parents[1] / "packs" / "riverside_grocery"


@pytest.fixture()
def service(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'simulation.db'}", future=True)
    # Tests create the already-migrated schema; production service never does so.
    Base.metadata.create_all(engine, tables=[x.__table__ for x in (*platform_models.ALL_TABLES, *round_models.ALL_TABLES, *simulation_models.ALL_TABLES, *scheduling_models.ALL_TABLES)])
    yield SimulationService(engine, load_runtime_pack(PACK))
    engine.dispose()


def test_initialize_read_and_detached_state(service):
    view = service.initialize(1, 1, "cost_leadership")
    assert view.current_round == 1
    assert view.checkpoint_round == 0
    assert view.sheet.revision == 0
    view.state.assets.clear()
    assert service.read(1, 1).state.assets


def test_edit_lock_reopen_preserves_commands_and_increments_revision(service):
    service.initialize(1, 1, "cost_leadership")
    command = CommandV1(key="buy_compute", op="buy_service", service="compute_pool", placement="cloud", units=1)
    patch = SheetPatchV1(version=1, replace_categories={"platform_service": [command]})
    edited = service.patch_sheet(1, 1, 1, 0, patch)
    assert edited.revision == 1
    locked = service.lock(1, 1, 1, 1)
    assert locked.locked_revision == 1
    assert service.lock(1, 1, 1, 1).locked_revision == 1
    with pytest.raises(SimulationError, match="locked"):
        service.patch_sheet(1, 1, 1, 1, SheetPatchV1(version=1, replace_categories={}))
    reopened = service.reopen(1, 1, 1, 1)
    assert reopened.revision == 2
    assert [item.key for item in reopened.commands] == ["buy_compute"]


def test_persisted_commands_retain_required_nullable_fields(service):
    service.initialize(1, 1, "cost_leadership")
    command = CommandV1(
        key="warehouse", op="buy_application", catalog="centraline_im7",
        placement="saas", config="core", primary_for=None,
        tco_categories=["integration", "training"],
    )
    patch = SheetPatchV1(version=1, replace_categories={"application": [command]})
    edited = service.patch_sheet(1, 1, 1, 0, patch)
    assert service.read(1, 1).sheet.commands[0].primary_for is None
    locked = service.lock(1, 1, 1, edited.revision)
    assert locked.commands[0].primary_for is None


def test_invalid_patch_and_scope_are_atomic(service):
    service.initialize(1, 1, "cost_leadership")
    with pytest.raises(SimulationError):
        service.patch_sheet(1, 1, 1, 0, {"version": 1, "replace_categories": {"bad": []}})
    assert service.read(1, 1).sheet.revision == 0
    with pytest.raises(SimulationError, match="scope_exists"):
        service.initialize(1, 1, "cost_leadership")
    with pytest.raises(SimulationError, match="not_found"):
        service.read(2, 1)


def test_stale_revision_does_not_change_sheet(service):
    service.initialize(1, 1, "cost_leadership")
    command = CommandV1(key="buy_compute", op="buy_service", service="compute_pool", placement="cloud", units=1)
    patch = SheetPatchV1(version=1, replace_categories={"platform_service": [command]})
    service.patch_sheet(1, 1, 1, 0, patch)
    with pytest.raises(SimulationError, match="revision_conflict"):
        service.patch_sheet(1, 1, 1, 0, patch)
    assert service.read(1, 1).sheet.revision == 1


def test_schedule_claim_is_verified_inside_mutation_transaction(service):
    service.initialize(1, 1, "cost_leadership")
    with Session(service.engine) as session:
        schedule = RoundSchedule(
            instance_id=1,
            round_number=1,
            start_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            deadline=datetime(2026, 1, 2, tzinfo=timezone.utc),
            auto_advance=True,
            grace_period_minutes=0,
            claim_token="live-token",
        )
        session.add(schedule)
        session.commit()
        schedule_id = schedule.id

    with pytest.raises(SimulationError, match="schedule_claim_lost"):
        service.lock(1, 1, 1, 0, schedule_claim=(schedule_id, "reclaimed-token"))
    assert service.read(1, 1).status == "draft"
    locked = service.lock(1, 1, 1, 0, schedule_claim=(schedule_id, "live-token"))
    assert locked.locked_revision == 0
    with pytest.raises(SimulationError, match="schedule_claim_lost"):
        service.advance(1, 1, 1, 0, schedule_claim=(schedule_id, "reclaimed-token"))
    assert service.read(1, 1).status == "locked"
