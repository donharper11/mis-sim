"""Instructor start readiness and atomic publication of every team's initial state."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.casepack.registry import RegistryError, aresolve_runtime_pack
from app.models import grading, host_platform, scheduling
from app.models.platform import Course, Enrollment, Section, SimulationInstance, Team, User
from app.round import models as round_models
from app.simulation import models as simulation_models
from app.simulation.service import SimulationService
from app.services.platform import PlatformConflict, PlatformNotFound, lock_setup_section, setup_instance

RUNTIME_TABLES = (*scheduling.ALL_TABLES, *host_platform.ALL_TABLES,
                 *simulation_models.ALL_TABLES, *round_models.ALL_TABLES, *grading.ALL_TABLES)


class InvalidStart(ValueError):
    """A structurally valid request with an invalid authored choice."""


async def inspect_start(session: AsyncSession, instance: SimulationInstance):
    """Read-only advisory inspection, reused after locks for start validation."""
    reasons = []
    section = await session.get(Section, instance.section_id, populate_existing=True)
    course = await session.get(Course, section.course_id, populate_existing=True)
    if not section.is_active or not course.is_active:
        reasons.append("Activate the course and section before starting.")
    if instance.status != "setup" or instance.current_round != 0:
        reasons.append("Only a section in setup at round 0 can be started.")
    pack = None
    try:
        pack = await aresolve_runtime_pack(session, instance.pack_key, instance.pack_version)
    except RegistryError:
        reasons.append("The registered case is unavailable or invalid. Review its registration before starting.")
    if not instance.pack_digest or (pack and instance.pack_digest != pack.pack_digest):
        reasons.append("The bound case no longer matches its registration. Review the case binding.")
    if pack and instance.total_rounds != pack.casepack.metadata.rounds:
        reasons.append(f"This case requires {pack.casepack.metadata.rounds} rounds; the section has {instance.total_rounds}.")
    teams = list((await session.scalars(select(Team).where(
        Team.instance_id == instance.instance_id,
    ).order_by(Team.id).execution_options(populate_existing=True))).all())
    if not teams:
        reasons.append("Create at least one team before starting.")
    if len(teams) > section.max_teams:
        reasons.append("The number of teams exceeds the section limit.")
    if section.max_teams < 1 or section.team_size_min < 1 or section.team_size_max < section.team_size_min:
        reasons.append("Correct the section's team-size limits before starting.")
    counts = {t.id: 0 for t in teams}
    rows = (await session.execute(select(Enrollment, User).outerjoin(User, User.id == Enrollment.user_id).where(
        Enrollment.section_id == section.id, Enrollment.is_active.is_(True), Enrollment.role == "student",
    ).execution_options(populate_existing=True))).all()
    for enrollment, user in rows:
        if user is None or not user.is_active or user.role != "student":
            reasons.append("An active student enrollment has no active student account. Correct the roster.")
        elif enrollment.team_id not in counts:
            reasons.append(f"Assign {user.name} to a team in this section before starting.")
        else:
            counts[enrollment.team_id] += 1
    for team in teams:
        if team.section_id != section.id:
            reasons.append("A team belongs to a different section. Correct the team setup.")
        if not section.team_size_min <= counts[team.id] <= section.team_size_max:
            reasons.append(f"{team.name} needs {section.team_size_min}–{section.team_size_max} active students; it has {counts[team.id]}.")
    for model in RUNTIME_TABLES:
        if (await session.execute(select(model.instance_id).where(model.instance_id == instance.instance_id).limit(1))).first():
            reasons.append("Existing simulation data must be cleared using Reset before starting this setup section.")
            break
    payload = {
        "instance_id": instance.instance_id, "status": instance.status,
        "pack_digest": instance.pack_digest, "total_rounds": instance.total_rounds,
        "ready": not reasons, "blocked_reasons": list(dict.fromkeys(reasons)),
        "strategies": [{"key": item.key, "label": pack.casepack.labels.strategies.get(item.key, item.key.replace("_", " ").title())}
                       for item in pack.casepack.strategies] if pack else [],
        "teams": [{"team_id": t.id, "name": t.name, "student_count": counts[t.id]} for t in teams],
    }
    return payload, pack


async def start_instance(session: AsyncSession, instance_id: int, expected_pack_digest: str, strategies: dict[int, str]):
    section_id = await session.scalar(select(SimulationInstance.section_id).where(SimulationInstance.instance_id == instance_id))
    if section_id is None:
        raise PlatformNotFound(f"Simulation instance {instance_id} was not found")
    await lock_setup_section(session, section_id)
    instance = await setup_instance(session, section_id)
    if instance is None or instance.instance_id != instance_id:
        raise PlatformNotFound(f"Simulation instance {instance_id} was not found")
    readiness, pack = await inspect_start(session, instance)
    if expected_pack_digest != instance.pack_digest:
        raise PlatformConflict("The case binding changed. Refresh the section before starting.")
    if set(strategies) != {t["team_id"] for t in readiness["teams"]}:
        raise PlatformConflict("The team list changed. Refresh and select a strategy for every team.")
    if not readiness["ready"]:
        raise PlatformConflict(" ".join(readiness["blocked_reasons"]))
    if pack and any(key not in {s.key for s in pack.casepack.strategies} for key in strategies.values()):
        raise InvalidStart("Choose a strategy from this section's registered case for every team.")
    service = SimulationService(session.get_bind(), pack)
    for team_id in sorted(strategies):
        await session.run_sync(lambda sync, tid=team_id: service.initialize_in_session(sync, instance_id, tid, strategies[tid]))
    instance.status = "active"
    instance.current_round = 1
    instance.started_at = datetime.now(timezone.utc)
    instance.completed_at = None
    await session.flush()
    return {"instance_id": instance_id, "status": instance.status, "current_round": 1,
            "started_at": instance.started_at, "team_ids": sorted(strategies)}
