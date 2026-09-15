"""Database-backed deterministic round scheduling.

The scheduler is deliberately synchronous: it is a short-lived command/service
boundary around the synchronous ``SimulationService``.  ``tick`` receives its
time from the caller; only the CLI entrypoint reads a clock.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import uuid
from typing import Any, Callable

from sqlalchemy import and_, exists, select, update
from sqlalchemy.orm import Session

from app.casepack.registry import RegistryError, resolve_runtime_pack
from app.models.platform import SimulationInstance, Team
from app.models.scheduling import RoundSchedule, RoundScheduleTeam
from app.simulation.models import SimulationCheckpointV1, SimulationRunV1, SimulationSheetV1
from app.simulation.service import SimulationService


LEASE_SECONDS = 60


class SchedulingError(ValueError):
    """A schedule request cannot be completed."""


def utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise SchedulingError("timestamps must be timezone-aware UTC values")
    return value.astimezone(timezone.utc)


def _db_utc(value: datetime | None) -> datetime | None:
    """SQLite returns timezone columns as naive values; interpret them as UTC."""
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _settings(instance: SimulationInstance) -> tuple[float, bool, int]:
    raw = instance.settings or {}
    duration = raw.get("default_round_duration_hours", 1)
    auto = raw.get("auto_advance_on_deadline", True)
    grace = raw.get("grace_period_minutes", 0)
    lock_warning = raw.get("lock_warning_minutes", 0)
    if isinstance(duration, bool) or not isinstance(duration, (int, float)) or duration <= 0:
        raise SchedulingError("default_round_duration_hours must be positive")
    if not isinstance(auto, bool):
        raise SchedulingError("auto_advance_on_deadline must be boolean")
    if isinstance(grace, bool) or not isinstance(grace, int) or grace < 0:
        raise SchedulingError("grace_period_minutes must be nonnegative")
    if isinstance(lock_warning, bool) or not isinstance(lock_warning, int) or lock_warning < 0:
        raise SchedulingError("lock_warning_minutes must be nonnegative")
    return float(duration), auto, grace


@dataclass(frozen=True)
class TickResult:
    instance_id: int
    round_number: int
    state: str
    failures: tuple[dict[str, Any], ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "round_number": self.round_number,
            "state": self.state,
            "failures": [dict(item) for item in self.failures],
        }


class Scheduler:
    """Persist and execute instance-scoped schedule rows.

    ``service_factory`` is an explicit seam for tests; production resolves the
    registered pack and constructs the M1 service after digest verification.
    """

    def __init__(self, session: Session, service_factory: Callable[[Any, Any], SimulationService] | None = None):
        self.session = session
        self.service_factory = service_factory or SimulationService

    def _instance(self, instance_id: int) -> SimulationInstance:
        instance = self.session.get(SimulationInstance, instance_id)
        if instance is None:
            raise SchedulingError(f"instance {instance_id} does not exist")
        return instance

    def _pack(self, instance: SimulationInstance):
        if not instance.pack_digest:
            raise SchedulingError("simulation instance has no bound pack digest")
        try:
            pack = resolve_runtime_pack(self.session, instance.pack_key, instance.pack_version)
        except RegistryError as exc:
            raise SchedulingError(str(exc)) from exc
        if pack.pack_digest != instance.pack_digest:
            raise SchedulingError("simulation instance pack digest does not match registry")
        return pack

    def _service(self, instance: SimulationInstance):
        pack = self._pack(instance)
        bind = self.session.get_bind()
        return self.service_factory(bind, pack)

    def _participants(self, instance_id: int) -> list[int]:
        team_ids = set(self.session.scalars(select(Team.id).where(Team.instance_id == instance_id)).all())
        run_ids = set(self.session.scalars(select(SimulationRunV1.team_id).where(SimulationRunV1.instance_id == instance_id)).all())
        if team_ids != run_ids:
            raise SchedulingError("initialized simulation runs and platform teams do not match")
        if not run_ids:
            raise SchedulingError("cannot schedule an instance with no initialized teams")
        return sorted(run_ids)

    def _validate_round(self, instance: SimulationInstance, round_number: int) -> None:
        if type(round_number) is not int or round_number < 1 or round_number > instance.total_rounds:
            raise SchedulingError("round is outside the instance total_rounds")
        pack = self._pack(instance)
        if round_number > pack.casepack.metadata.rounds:
            raise SchedulingError("round is outside the registered pack authored rounds")

    def set_schedule(
        self,
        instance_id: int,
        round_number: int,
        start_at: datetime,
        deadline: datetime,
        *,
        auto_advance: bool | None = None,
        grace_period_minutes: int | None = None,
    ) -> RoundSchedule:
        start = utc(start_at)
        end = utc(deadline)
        if end <= start:
            raise SchedulingError("deadline must be after start_at")
        instance = self._instance(instance_id)
        self._validate_round(instance, round_number)
        _, default_auto, default_grace = _settings(instance)
        auto = default_auto if auto_advance is None else auto_advance
        grace = default_grace if grace_period_minutes is None else grace_period_minutes
        if not isinstance(auto, bool):
            raise SchedulingError("auto_advance must be boolean")
        if type(grace) is not int or grace < 0:
            raise SchedulingError("grace_period_minutes must be nonnegative")
        if self.session.scalar(select(RoundSchedule).where(RoundSchedule.instance_id == instance_id, RoundSchedule.round_number == round_number)):
            raise SchedulingError("duplicate schedule")
        participants = self._participants(instance_id)
        row = RoundSchedule(
            instance_id=instance_id, round_number=round_number, start_at=start, deadline=end,
            auto_advance=auto, grace_period_minutes=grace,
        )
        self.session.add(row)
        self.session.flush()
        self.session.add_all([
            RoundScheduleTeam(schedule_id=row.id, instance_id=instance_id, team_id=team_id)
            for team_id in participants
        ])
        self.session.flush()
        return row

    def bulk_schedule(
        self,
        instance_id: int,
        first_start_at: datetime,
        *,
        duration_hours: float | None = None,
        auto_advance: bool | None = None,
        grace_period_minutes: int | None = None,
    ) -> dict[str, Any]:
        start = utc(first_start_at)
        instance = self._instance(instance_id)
        default_duration, default_auto, default_grace = _settings(instance)
        duration = default_duration if duration_hours is None else duration_hours
        if isinstance(duration, bool) or not isinstance(duration, (int, float)) or duration <= 0:
            raise SchedulingError("duration_hours must be positive")
        auto = default_auto if auto_advance is None else auto_advance
        grace = default_grace if grace_period_minutes is None else grace_period_minutes
        if not isinstance(auto, bool) or type(grace) is not int or grace < 0:
            raise SchedulingError("invalid schedule defaults")
        self._validate_round(instance, 1)
        skipped: list[int] = []
        created: list[RoundSchedule] = []
        for round_number in range(1, instance.total_rounds + 1):
            existing = self.session.scalar(select(RoundSchedule).where(RoundSchedule.instance_id == instance_id, RoundSchedule.round_number == round_number))
            if existing is not None:
                if existing.advanced_at is not None:
                    skipped.append(round_number)
                    start = _db_utc(existing.deadline) + timedelta(minutes=existing.grace_period_minutes)
                    continue
                raise SchedulingError(f"duplicate schedule for round {round_number}")
            end = start + timedelta(hours=float(duration))
            created.append(self.set_schedule(instance_id, round_number, start, end, auto_advance=auto, grace_period_minutes=grace))
            start = end + timedelta(minutes=grace)
        return {"created": created, "skipped": skipped}

    def _rows(self, schedule: RoundSchedule) -> list[RoundScheduleTeam]:
        return list(self.session.scalars(select(RoundScheduleTeam).where(
            RoundScheduleTeam.schedule_id == schedule.id,
            RoundScheduleTeam.instance_id == schedule.instance_id,
        ).order_by(RoundScheduleTeam.team_id)).all())

    def _conditional_participant_update(self, row: RoundScheduleTeam, token: str | None, **values: Any) -> bool:
        statement = update(RoundScheduleTeam).where(
            RoundScheduleTeam.schedule_id == row.schedule_id,
            RoundScheduleTeam.instance_id == row.instance_id,
            RoundScheduleTeam.team_id == row.team_id,
        )
        if token is not None:
            statement = statement.where(exists(select(RoundSchedule.id).where(
                RoundSchedule.id == row.schedule_id,
                RoundSchedule.instance_id == row.instance_id,
                RoundSchedule.claim_token == token,
            )))
        result = self.session.execute(statement.values(**values))
        return result.rowcount == 1

    def _claim_owned(self, schedule: RoundSchedule, token: str | None) -> bool:
        """Fence service side effects against a worker lease being reclaimed."""
        if token is None:
            return True
        owned = self.session.scalar(select(RoundSchedule.id).where(
            RoundSchedule.id == schedule.id,
            RoundSchedule.instance_id == schedule.instance_id,
            RoundSchedule.claim_token == token,
        ))
        # Close this verification read before invoking SimulationService,
        # whose transaction is deliberately owned by that service.
        self.session.commit()
        return owned is not None

    def _failure(self, failures: list[dict[str, Any]], team_id: int, exc: Exception) -> None:
        failures.append({"team_id": team_id, "error": str(exc)})

    def _lock(self, schedule: RoundSchedule, at: datetime, *, token: str | None, reason: str) -> list[dict[str, Any]]:
        failures: list[dict[str, Any]] = []
        service = self._service(self._instance(schedule.instance_id))
        for row in self._rows(schedule):
            if row.locked_revision is not None:
                continue
            try:
                run = self.session.get(SimulationRunV1, (schedule.instance_id, row.team_id))
                if run is None or run.current_round != schedule.round_number:
                    raise SchedulingError("missing run or current round mismatch")
                sheet = self.session.get(SimulationSheetV1, (schedule.instance_id, row.team_id, schedule.round_number))
                if sheet is None:
                    raise SchedulingError("missing production sheet")
                revision = sheet.locked_revision if sheet.locked_revision is not None else sheet.revision
                # SimulationService owns its own transaction. Close the
                # scheduler session's read transaction before invoking it;
                # SQLite's BEGIN IMMEDIATE otherwise sees the read lock.
                self.session.commit()
                if not self._claim_owned(schedule, token):
                    raise SchedulingError("schedule claim lost")
                service.lock(
                    schedule.instance_id, row.team_id, schedule.round_number, revision,
                    schedule_claim=(schedule.id, token) if token is not None else None,
                )
                if not self._conditional_participant_update(row, token, locked_revision=revision, locked_at=at):
                    raise SchedulingError("schedule claim lost")
                self.session.commit()
            except Exception as exc:
                self._failure(failures, row.team_id, exc)
                break
        self.session.flush()
        rows = self._rows(schedule)
        if not failures and all(row.locked_revision is not None for row in rows):
            schedule.decisions_locked = True
            schedule.lock_reason = schedule.lock_reason or reason
            schedule.locked_at = schedule.locked_at or at
        return failures

    def _advance(self, schedule: RoundSchedule, at: datetime, *, token: str | None) -> list[dict[str, Any]]:
        failures: list[dict[str, Any]] = []
        service = self._service(self._instance(schedule.instance_id))
        for row in self._rows(schedule):
            if row.advanced_at is not None:
                continue
            if row.locked_revision is None:
                continue
            try:
                self.session.commit()
                if not self._claim_owned(schedule, token):
                    raise SchedulingError("schedule claim lost")
                service.advance(
                    schedule.instance_id, row.team_id, schedule.round_number, row.locked_revision,
                    schedule_claim=(schedule.id, token) if token is not None else None,
                )
                if not self._conditional_participant_update(row, token, advanced_at=at):
                    raise SchedulingError("schedule claim lost")
                self.session.commit()
            except Exception as exc:
                self._failure(failures, row.team_id, exc)
                break
        self.session.flush()
        rows = self._rows(schedule)
        if not failures and all(row.advanced_at is not None for row in rows):
            schedule.advanced_at = schedule.advanced_at or at
        return failures

    def _process(self, schedule: RoundSchedule, at: datetime, *, token: str | None, force_lock: bool = False, force_advance: bool = False) -> TickResult:
        failures: list[dict[str, Any]] = []
        if force_lock or at >= _db_utc(schedule.deadline):
            reason = schedule.lock_reason or ("instructor_locked" if force_lock else "deadline_expired")
            # Preserve the first cause even when one participant operation fails.
            # A later deadline tick must not rewrite an instructor's explicit lock.
            schedule.lock_reason = schedule.lock_reason or reason
            failures.extend(self._lock(schedule, at, token=token, reason=reason))
        if not failures and (force_advance or (schedule.auto_advance and at >= _db_utc(schedule.deadline) + timedelta(minutes=schedule.grace_period_minutes))):
            failures.extend(self._advance(schedule, at, token=token))
        state = "advanced" if schedule.advanced_at else "locked" if schedule.decisions_locked else "failed" if failures else "pending"
        return TickResult(schedule.instance_id, schedule.round_number, state, tuple(failures))

    def _claim(self, schedule: RoundSchedule, at: datetime) -> str | None:
        token = uuid.uuid4().hex
        result = self.session.execute(update(RoundSchedule).where(
            RoundSchedule.id == schedule.id,
            and_(RoundSchedule.claim_token.is_(None), (RoundSchedule.claim_until.is_(None) | (RoundSchedule.claim_until <= at))),
        ).values(claim_token=token, claim_until=at + timedelta(seconds=LEASE_SECONDS)))
        self.session.commit()
        return token if result.rowcount == 1 else None

    def _clear_claim(self, schedule_id: int, token: str) -> None:
        self.session.execute(update(RoundSchedule).where(RoundSchedule.id == schedule_id, RoundSchedule.claim_token == token).values(claim_token=None, claim_until=None))
        self.session.commit()

    def tick(self, now: datetime) -> list[dict[str, Any]]:
        at = utc(now)
        schedules = list(self.session.scalars(select(RoundSchedule).where(RoundSchedule.start_at <= at).order_by(RoundSchedule.instance_id, RoundSchedule.round_number)).all())
        result: list[dict[str, Any]] = []
        for schedule in schedules:
            if schedule.advanced_at is not None:
                result.append(TickResult(schedule.instance_id, schedule.round_number, "advanced").as_dict())
                continue
            token = self._claim(schedule, at)
            if token is None:
                result.append(TickResult(schedule.instance_id, schedule.round_number, "busy").as_dict())
                continue
            try:
                result.append(self._process(schedule, at, token=token).as_dict())
                self.session.commit()
            except Exception as exc:
                self.session.rollback()
                result.append(TickResult(schedule.instance_id, schedule.round_number, "failed", ({"error": str(exc),},)).as_dict())
            finally:
                self._clear_claim(schedule.id, token)
        return result

    def lock_now(self, instance_id: int, round_number: int, at: datetime) -> dict[str, Any]:
        when = utc(at)
        schedule = self.session.scalar(select(RoundSchedule).where(RoundSchedule.instance_id == instance_id, RoundSchedule.round_number == round_number))
        if schedule is None:
            raise SchedulingError("schedule does not exist")
        result = self._process(schedule, when, token=None, force_lock=True)
        self.session.commit()
        return result.as_dict()

    def advance_now(self, instance_id: int, round_number: int, at: datetime) -> dict[str, Any]:
        when = utc(at)
        schedule = self.session.scalar(select(RoundSchedule).where(RoundSchedule.instance_id == instance_id, RoundSchedule.round_number == round_number))
        if schedule is None:
            raise SchedulingError("schedule does not exist")
        result = self._process(schedule, when, token=None, force_lock=False, force_advance=True)
        self.session.commit()
        return result.as_dict()

    def unlock(self, instance_id: int, round_number: int) -> dict[str, Any]:
        schedule = self.session.scalar(select(RoundSchedule).where(RoundSchedule.instance_id == instance_id, RoundSchedule.round_number == round_number))
        if schedule is None:
            raise SchedulingError("schedule does not exist")
        if schedule.advanced_at is not None or self.session.scalar(select(RoundScheduleTeam).where(RoundScheduleTeam.schedule_id == schedule.id, RoundScheduleTeam.advanced_at.is_not(None))):
            raise SchedulingError("cannot unlock after advancement")
        service = self._service(self._instance(instance_id))
        for row in self._rows(schedule):
            if row.locked_revision is not None:
                reopen = getattr(service, "reopen", None)
                if reopen is None:
                    raise SchedulingError("production service cannot reopen a locked round")
                try:
                    reopen(instance_id, row.team_id, round_number, row.locked_revision)
                except Exception as exc:
                    raise SchedulingError(f"cannot reopen team {row.team_id}: {exc}") from exc
            row.locked_revision = None
            row.locked_at = None
            row.advanced_at = None
        schedule.decisions_locked = False
        schedule.lock_reason = None
        schedule.locked_at = None
        schedule.advanced_at = None
        schedule.claim_token = None
        schedule.claim_until = None
        self.session.commit()
        return self.status(instance_id, round_number)

    def status(self, instance_id: int, round_number: int | None = None) -> Any:
        statement = select(RoundSchedule).where(RoundSchedule.instance_id == instance_id).order_by(RoundSchedule.round_number)
        if round_number is not None:
            statement = statement.where(RoundSchedule.round_number == round_number)
        rows = list(self.session.scalars(statement).all())
        payload = []
        for schedule in rows:
            participants = self._rows(schedule)
            payload.append({
                "instance_id": schedule.instance_id, "round_number": schedule.round_number,
                "start_at": _db_utc(schedule.start_at).isoformat(), "deadline": _db_utc(schedule.deadline).isoformat(),
                "grace_period_minutes": schedule.grace_period_minutes, "auto_advance": schedule.auto_advance,
                "decisions_locked": schedule.decisions_locked, "lock_reason": schedule.lock_reason,
                "advanced": sum(row.advanced_at is not None for row in participants), "participants": len(participants),
                "advanced_at": _db_utc(schedule.advanced_at).isoformat() if schedule.advanced_at else None,
            })
        return payload[0] if round_number is not None and payload else (payload if round_number is None else None)
