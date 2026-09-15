from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base
import app.models.platform  # noqa: F401
import app.models.scheduling  # noqa: F401
import app.simulation.models  # noqa: F401
from app.models.platform import Course, Section, SimulationInstance, Team, User
from app.simulation.models import SimulationRunV1, SimulationSheetV1
from app.scheduling import Scheduler, SchedulingError


UTC = timezone.utc


class FakeService:
    def __init__(self):
        self.locked = []
        self.advanced = []

    def lock(self, instance_id, team_id, round, expected_revision, *, schedule_claim=None):
        self.locked.append((instance_id, team_id, round, expected_revision))
        return SimpleNamespace(locked_revision=expected_revision)

    def advance(self, instance_id, team_id, round, locked_revision, *, schedule_claim=None):
        self.advanced.append((instance_id, team_id, round, locked_revision))
        return {"round": round}

    def reopen(self, instance_id, team_id, round, expected_revision):
        return SimpleNamespace(locked_revision=None, revision=expected_revision + 1)


@pytest.fixture
def seeded():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine, expire_on_commit=False)
    user = User(name="Instructor", email="instructor@example.edu", role="instructor")
    session.add(user)
    session.flush()
    course = Course(course_code="TEST", course_name="Test", academic_year="2026", semester="autumn", instructor_id=user.id)
    session.add(course)
    session.flush()
    section = Section(course_id=course.id, section_code="A", section_name="A")
    session.add(section)
    session.flush()
    instance = SimulationInstance(section_id=section.id, pack_key="test", pack_version="1.0.0", pack_digest="d" * 64, total_rounds=2, settings={"grace_period_minutes": 5})
    session.add(instance)
    session.flush()
    for team_id in (1, 2):
        team = Team(id=team_id, section_id=section.id, instance_id=instance.instance_id, name=f"Team {team_id}")
        session.add(team)
        session.add(SimulationRunV1(instance_id=instance.instance_id, team_id=team_id, version=1, pack_key="test", pack_version="1.0.0", pack_digest="d" * 64, current_round=1, advanced_round=0, status="draft"))
        session.add(SimulationSheetV1(instance_id=instance.instance_id, team_id=team_id, round=1, revision=0, commands=[]))
    session.commit()
    fake = FakeService()
    scheduler = Scheduler(session, service_factory=lambda _engine, _pack: fake)
    scheduler._pack = lambda _instance: SimpleNamespace(pack_digest="d" * 64, casepack=SimpleNamespace(metadata=SimpleNamespace(rounds=2)))
    yield scheduler, fake, instance.instance_id, session
    session.close()
    engine.dispose()


def test_fixed_time_grace_and_idempotency(seeded):
    scheduler, fake, instance_id, session = seeded
    start = datetime(2026, 9, 15, 11, tzinfo=UTC)
    schedule = scheduler.set_schedule(instance_id, 1, start, start + timedelta(hours=1), grace_period_minutes=5, auto_advance=True)
    session.commit()
    assert scheduler.tick(start + timedelta(minutes=59))[0]["state"] == "pending"
    assert scheduler.tick(start + timedelta(hours=1))[0]["state"] == "locked"
    assert scheduler.status(instance_id, 1)["grace_period_minutes"] == 5
    assert scheduler.tick(start + timedelta(hours=1, minutes=5))[0]["state"] == "advanced"
    for _ in range(50):
        assert scheduler.tick(start + timedelta(hours=1, minutes=5))[0]["state"] == "advanced"
    assert len(fake.locked) == 2
    assert len(fake.advanced) == 2


def test_manual_unlock_before_advance_and_refusal_after(seeded):
    scheduler, _fake, instance_id, session = seeded
    start = datetime(2026, 9, 15, 11, tzinfo=UTC)
    scheduler.set_schedule(instance_id, 1, start, start + timedelta(hours=1), grace_period_minutes=0, auto_advance=False)
    session.commit()
    assert scheduler.lock_now(instance_id, 1, start)["state"] == "locked"
    assert scheduler.unlock(instance_id, 1)["decisions_locked"] is False
    assert scheduler.lock_now(instance_id, 1, start)["state"] == "locked"
    assert scheduler.advance_now(instance_id, 1, start)["state"] == "advanced"
    with pytest.raises(SchedulingError, match="after advancement"):
        scheduler.unlock(instance_id, 1)


def test_validation_rejects_naive_and_duplicate(seeded):
    scheduler, _fake, instance_id, session = seeded
    with pytest.raises(SchedulingError, match="timezone-aware"):
        scheduler.set_schedule(instance_id, 1, datetime(2026, 1, 1), datetime(2026, 1, 2))
    start = datetime(2026, 1, 1, tzinfo=UTC)
    scheduler.set_schedule(instance_id, 1, start, start + timedelta(hours=1))
    with pytest.raises(SchedulingError, match="duplicate"):
        scheduler.set_schedule(instance_id, 1, start, start + timedelta(hours=1))


@pytest.mark.parametrize("value", [-1, True, "5"])
def test_validation_rejects_invalid_lock_warning_minutes(seeded, value):
    scheduler, _fake, instance_id, session = seeded
    session.get(SimulationInstance, instance_id).settings = {"lock_warning_minutes": value}
    start = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(SchedulingError, match="lock_warning_minutes"):
        scheduler.set_schedule(instance_id, 1, start, start + timedelta(hours=1))


def test_reclaimed_claim_suppresses_service_calls(seeded):
    scheduler, fake, instance_id, session = seeded
    start = datetime(2026, 9, 15, 11, tzinfo=UTC)
    schedule = scheduler.set_schedule(instance_id, 1, start, start + timedelta(hours=1), auto_advance=False)
    session.commit()

    locked = scheduler._process(schedule, start + timedelta(hours=1), token="reclaimed-token")
    assert locked.state == "failed"
    assert locked.failures[0]["error"] == "schedule claim lost"
    assert fake.locked == []

    for row in scheduler._rows(schedule):
        row.locked_revision = 0
    session.commit()
    advanced = scheduler._advance(schedule, start + timedelta(hours=1), token="reclaimed-token")
    assert advanced[0]["error"] == "schedule claim lost"
    assert fake.advanced == []
