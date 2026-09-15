"""M2 2.2 two-instance scope and delete-refusal canary."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Base
from app.models.platform import Course, Section, SimulationInstance, Team, User
from app.repo.base import ScopeError, ScopedRepo
from app.round import models as rm
from app.simulation import models as sm

BACKEND = Path(__file__).resolve().parents[1]
RUNTIME = (*rm.ALL_TABLES, *sm.ALL_TABLES)


def _migrate(path: Path) -> None:
    alembic = shutil.which("alembic")
    if alembic is None:
        candidate = Path(os.sys.executable).with_name("alembic")
        if candidate.exists():
            alembic = str(candidate)
    if alembic is None:
        pytest.fail("alembic executable is required for the migration-backed isolation canary")
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite+aiosqlite:///{path}"
    env["PYTHONPATH"] = str(BACKEND)
    result = subprocess.run(
        [alembic, "-c", "alembic.ini", "upgrade", "head"],
        cwd=BACKEND, env=env, text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.fixture()
def db(tmp_path):
    path = tmp_path / "instance-isolation.db"
    _migrate(path)
    engine = create_engine(f"sqlite:///{path}", future=True)
    event.listen(engine, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys=ON"))
    with Session(engine, expire_on_commit=False) as session:
        yield session
    engine.dispose()


def _platform(session: Session):
    instructor = User(name="M2 instructor", email="m2@example.test", role="instructor", is_active=True)
    session.add(instructor)
    session.flush()
    course = Course(
        course_code="M2", course_name="Platform", academic_year="2026", semester="fall",
        instructor_id=instructor.id, active_chapters=[1], is_active=True,
    )
    session.add(course)
    session.flush()
    sections = []
    instances = []
    teams = []
    for code, pack_key, pack_version in (("A", "pack-a", "1.0"), ("B", "pack-b", "2.0")):
        section = Section(section_code=code, section_name=f"Section {code}", course_id=course.id,
                          max_teams=4, team_size_min=1, team_size_max=4, is_active=True)
        session.add(section)
        session.flush()
        instance = SimulationInstance(section_id=section.id, pack_key=pack_key, pack_version=pack_version,
                                      current_round=1, total_rounds=6, status="active", settings={})
        session.add(instance)
        session.flush()
        team = Team(section_id=section.id, instance_id=instance.instance_id, name=f"Team {code}")
        session.add(team)
        session.flush()
        sections.append(section); instances.append(instance); teams.append(team)
    return instances, teams


def _runtime_rows(instance_id: int, team_id: int, marker: str):
    common = dict(instance_id=instance_id, team_id=team_id)
    return [
        rm.TeamStateRow(**common, current_round=1, declared_strategy=marker, declared_strategy_round=1, cash=0, opex_runrate=0),
        rm.ArchNodeRow(**common, round=1, key=marker, roles_filled=[], availability=1, installed_round=1, service_life_rounds=6, serves=[], throughput=None, owns_entities=[], placement=None, opex_contribution=0),
        rm.ArchEdgeRow(**common, round=1, src=marker, dst=marker, kind="network"),
        rm.DeploymentOrgStateRow(**common, round=1, key=marker, catalog_key=marker, org_unit=marker, people_affected=1, trained_count=0, process="unchanged", adoption=0, ever_trained=False, serves=[], is_primary_for=None, initiated=True, abandoned=False),
        rm.PlatformServiceRow(**common, round=1, key=marker, placement=None, capacity=1, utilisation=0),
        rm.OrgUnitRow(**common, round=1, key=marker, headcount=1, resistance=0),
        rm.ItStaffRow(**common, round=1, staff_fte=1, load_fte=0),
        rm.GovernanceStateRow(**common, round=1, capability=marker, owner_assigned=False, sponsor_assigned=False),
        rm.PolicyDecisionRow(**common, round=1, policy=marker, selected=marker, actively_decided=False),
        rm.StakeholderAlignmentRow(**common, round=1, stakeholder=marker, alignment=0, cares_about=[]),
        rm.InFlightRow(**common, key=marker, catalog_key=marker, ordered_round=1, arrival_round=2, capex=0, node_payload={}, materialised=False),
        rm.DecisionLineRow(**common, round=1, key=marker, category="communication", capability=None, capex=0, rgt_tag="run", is_maintenance=False, action_type=None, target_key=None),
        rm.SignalRow(**common, key=marker, episode_id=1, round=1, capability=marker, metric=marker, metric_kind="absolute", value=0, severity="low", status="open", first_shown_round=1, cleared_round=None, fire_round=None, cleared_by=[], was_actionable=False, cheapest_fix_when_raised=None),
        rm.DebtItemRow(**common, round=1, capability=None, amount=0, source_key=None, reason="deferral"),
        rm.TcoForecastRow(**common, round=1, item=marker, forecast=0, actual=0),
        rm.RoundResult(**common, round=1, payload={"marker": marker}),
        sm.SimulationRunV1(**common, version=1, pack_key=marker, pack_version="1.0", pack_digest=marker.ljust(64, "0")[:64], current_round=1, advanced_round=0, status="draft"),
        sm.SimulationSheetV1(**common, round=1, revision=0, locked_revision=None, commands=[], sheet_digest=None),
        sm.SimulationCheckpointV1(**common, round=0, version=1, pack_digest=marker.ljust(64, "0")[:64], sheet_revision=None, state={}, state_digest=marker.ljust(64, "0")[:64]),
    ]


def test_two_instances_are_scoped_and_populated_instance_cannot_be_deleted(db):
    instances, teams = _platform(db)
    a, b = instances
    ta, tb = teams
    rows_a = _runtime_rows(a.instance_id, ta.id, "A")
    rows_b = _runtime_rows(b.instance_id, tb.id, "B")
    deferred = (sm.SimulationSheetV1, sm.SimulationCheckpointV1)
    db.add_all([row for row in rows_a + rows_b if not isinstance(row, deferred)])
    db.commit()
    db.add_all([row for row in rows_a + rows_b if isinstance(row, deferred)])
    db.commit()

    for model in RUNTIME:
        ra = ScopedRepo(db, a.instance_id, ta.id)
        rb = ScopedRepo(db, b.instance_id, tb.id)
        assert len(db.scalars(ra.select(model)).all()) == 1
        assert len(db.scalars(rb.select(model)).all()) == 1
        identity_b = inspect(model).mapper.primary_key_from_instance(rows_b[RUNTIME.index(model)])
        result = None
        try:
            result = ra.get(model, tuple(identity_b))
        except ScopeError:
            pass
        assert result is None, model.__tablename__

    with pytest.raises(ScopeError):
        ScopedRepo(db, None)  # type: ignore[arg-type]
    with pytest.raises(ScopeError):
        ScopedRepo(db, a.instance_id, ta.id).add(rows_b[0])

    db.delete(a)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    assert db.get(SimulationInstance, a.instance_id) is not None
    assert db.scalar(select(rm.TeamStateRow).where(rm.TeamStateRow.instance_id == a.instance_id)) is not None
