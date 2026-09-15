"""Seed a complete demo environment and describe it.

`load_scenario(name)` returns the parsed casepack and the seeded `TeamState` a
scenario is built from -- the one place the loader (which reads files) and the seed
builder (pure Python data) are wired together, so the engine package itself stays
free of I/O (invariant I2).

CLI: `python -m app.seed.demo --scenario riverside_r3` loads the pack, builds the
state, and prints what the demo contains -- the counts the scorer will read, so the
next session can confirm the seed is in the loop before trusting any figure.
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from sqlalchemy import inspect, select
from sqlalchemy.engine import make_url

from app.casepack.loader import load_casepack
from app.casepack.models import Casepack
from app.engine.state import TeamState
from app.database import async_session
from app.models.platform import Casepack, Course, Enrollment, Section, SimulationInstance, Team, User
from app.services.auth import hash_password
from app.services.platform import CourseService, EnrollmentService, InstanceService, PlatformConflict, SectionService, TeamService
from app.casepack.registry import register_casepack

#: scenario name -> (pack directory relative to backend/, seed builder module path)
_SCENARIOS: dict[str, tuple[str, str]] = {
    "riverside_r3": ("packs/riverside_grocery", "seeds.riverside_r3"),
}

_BACKEND_ROOT = Path(__file__).resolve().parents[2]


def load_scenario(name: str) -> tuple[Casepack, TeamState]:
    if name not in _SCENARIOS:
        raise KeyError(f"unknown scenario {name!r}; known: {sorted(_SCENARIOS)}")
    pack_rel, builder_mod = _SCENARIOS[name]
    pack = load_casepack(_BACKEND_ROOT / pack_rel)

    import importlib

    module = importlib.import_module(builder_mod)
    state: TeamState = module.build_team_state()
    return pack, state


def _describe(name: str, pack: Casepack, state: TeamState) -> str:
    lines = [
        f"scenario {name}",
        f"pack {pack.metadata.pack_key} v{pack.metadata.pack_version} "
        f"round {state.round} of {pack.metadata.rounds}",
        f"strategy {state.declared_strategy}",
        f"capabilities {len(pack.capabilities)} · catalog {len(pack.catalog)} "
        f"· strategies {len(pack.strategies)}",
        f"nodes {len(state.nodes)} · edges {len(state.edges)} "
        f"· deployments {len(state.deployments)}",
        f"governance rows {len(state.governance)} · signals {len(state.signals)} "
        f"· decisions {len(state.decisions)}",
        f"staff pool {state.staff.staff_fte} fte carrying {state.staff.load_fte} load",
        f"stakeholder alignments {len(state.stakeholder_alignments)}",
        f"policy decisions {len(state.policy_decisions)} "
        f"({sum(1 for p in state.policy_decisions if p.actively_decided)} actively decided)",
    ]
    return "\n".join(lines)


def _describe_signals(pack: Casepack, state: TeamState) -> str:
    """The `--with-signals` demonstration: the R1-R3 ledger, its projection compatibility, the
    two-path event outcome, and a blast-radius traversal (1.5 spec section 5.5, contract-spec
    section 10). Pure orchestration -- the engine reads no file and no clock (invariant I2)."""
    from app.engine import events as events_mod
    from app.engine import graph as graph_mod
    from app.engine import ledger as ledger_mod
    from app.engine import catalog as catalog_mod
    import seeds.riverside_signals as sig

    lines: list[str] = ["", "-- signal ledger (R1-R3 history) --"]

    ledger = sig.signal_history()
    for s in ledger:
        lines.append(
            f"  {s.key} ep{s.episode_id} {s.metric_kind}/{s.metric} sev={s.severity} "
            f"status={s.status} shown={s.first_shown_round} cleared={s.cleared_round} "
            f"fired={s.fire_round} actionable={s.was_actionable} fix={s.cheapest_fix_when_raised}"
        )

    # Compatibility gate: the projection must reproduce the seed's three SignalState rows.
    projected = ledger_mod.project_signal_state(ledger)
    seed_rows = state.signals
    match = projected == seed_rows
    lines.append(f"  projection reproduces the seed SignalState rows: {match}")

    # Two paths from one event card (warehouse_rollout_gap), opposite outcomes, no branching.
    lines.append("")
    lines.append("-- two-path demonstration: warehouse_rollout_gap --")
    do_nothing = sig.do_nothing_state()
    open_ledger = ledger_mod.advance_ledger((), do_nothing, pack)
    fired_dn, _ = events_mod.resolve_events(do_nothing, pack, open_ledger)
    lines.append(f"  do-nothing path: warehouse_rollout_gap fires = {'warehouse_rollout_gap' in fired_dn}")

    cleared = sig.cleared_state()
    cleared_ledger = ledger_mod.advance_ledger(open_ledger, cleared, pack)
    wh = next(s for s in cleared_ledger if s.key == "wh_rollout_01")
    fired_cl, _ = events_mod.resolve_events(cleared, pack, cleared_ledger)
    lines.append(
        f"  cleared path: wh_rollout_01 status={wh.status} cleared_round={wh.cleared_round}; "
        f"warehouse_rollout_gap fires = {'warehouse_rollout_gap' in fired_cl}"
    )

    # Blast radius by traversal: removing the WAN link darkens the capabilities behind it.
    lines.append("")
    lines.append("-- blast radius (traversal) --")
    caps = [c.key for c in pack.capabilities]
    primary = {c: catalog_mod.primary_entity(pack, c) for c in caps}
    darkened = graph_mod.blast_radius(state, "wan_link", caps, primary)
    lines.append(f"  removing wan_link darkens: {darkened}")

    return "\n".join(lines)


def _describe_full(results: list[dict]) -> str:
    """The `--full` demonstration summary: six immutable RoundResults COMPUTED from the seed,
    the opex ratchet, and the R3 signal projection (spec section 5.5). Numbers come from the
    persisted RoundResult payloads, not from any hardcoded value beside them (GOVERNANCE 4.9)."""
    lines: list[str] = ["", "-- six-round game (--full): immutable RoundResults --"]
    for r in results:
        fin = r["financials"]
        sig = r["signals"]
        of = next((c for c in r["capabilities"] if c["capability"] == "order_fulfilment"), None)
        of_realised = f"{of['realised']:.4f}" if of else "n/a"
        lines.append(
            f"  round {r['round']}: opex_runrate={fin['opex_runrate']} capex_spent={fin['capex_spent']} "
            f"debt_total={fin['debt_total']} | order_fulfilment realised={of_realised} | "
            f"raised={len(sig['raised'])} cleared={len(sig['cleared'])} "
            f"fired={len(sig['fired'])} open={len(sig['open'])} | "
            f"missed_signals={len(r['missed_signals'])}"
        )
    opex = [r["financials"]["opex_runrate"] for r in results]
    lines.append(f"  opex ratchet: {' -> '.join(str(o) for o in opex)}")
    r3 = next((r for r in results if r["round"] == 3), None)
    if r3 is not None:
        lines.append("  R3 missed signals (what prints 'you were told in round N'):")
        for ms in r3["missed_signals"]:
            lines.append(
                f"    {ms['key']} first_shown_round={ms['first_shown_round']} "
                f"cheapest_fix_when_raised={ms['cheapest_fix_when_raised']}"
            )
    return "\n".join(lines)


def _run_full() -> int:
    """Seed and run the six-round game from a clean database (spec section 5.5). Creates the
    round-runner tables if absent (the Postgres path normally uses `alembic upgrade head` first;
    create_all is the idempotent fallback for a fresh DB)."""
    from app.round.db import create_all, make_engine, session_for
    from seeds.riverside_full import run_full_game

    create_all(make_engine())
    with session_for() as session:
        results = run_full_game(session)
    print(_describe_full(results))
    return 0


async def seed_cohort(session) -> dict:
    """Create the deterministic two-section platform cohort used by M2 canaries."""
    existing_course = await session.scalar(select(Course).where(Course.course_code == "MIS-PLATFORM"))
    if existing_course is not None:
        sections = (await session.scalars(select(Section).where(Section.course_id == existing_course.id).order_by(Section.id))).all()
        if len(sections) != 2:
            raise PlatformConflict("M2 cohort exists with an incomplete section set; refusing duplicate seed")
        instances = []
        teams = []
        enrollments = []
        for section in sections:
            instance = await session.scalar(select(SimulationInstance).where(SimulationInstance.section_id == section.id))
            if instance is None:
                raise PlatformConflict("M2 cohort exists with an incomplete instance set; refusing duplicate seed")
            instances.append(instance)
            teams.extend((await session.scalars(select(Team).where(Team.instance_id == instance.instance_id).order_by(Team.id))).all())
            enrollments.extend((await session.scalars(select(Enrollment).where(Enrollment.section_id == section.id).order_by(Enrollment.id))).all())
        return {"course": existing_course, "sections": sections, "instances": instances, "teams": teams, "enrollments": enrollments}
    has_registry = await session.run_sync(lambda sync: "casepack" in inspect(sync.get_bind()).get_table_names())
    if has_registry:
        def ensure_packs(sync):
            for name, key, version in (
                ("riverside_grocery", "riverside_grocery", "0.1.0"),
                ("m2_isolation_fixture", "m2_isolation_fixture", "0.1.1"),
            ):
                if sync.scalar(select(Casepack).where(Casepack.pack_key == key, Casepack.pack_version == version)) is None:
                    register_casepack(sync, _BACKEND_ROOT / "packs" / name)
        await session.run_sync(ensure_packs)
        pack_tuples = (("riverside_grocery", "0.1.0"), ("m2_isolation_fixture", "0.1.1"))
    else:
        # Isolated pre-registry unit fixtures retain their historical synthetic IDs.
        pack_tuples = (("pack_alpha", "1.0.0"), ("pack_beta", "1.0.0"))
    instructor = User(student_id=None, name="M2 Instructor", email="m2.instructor@example.edu", role="instructor")
    session.add(instructor)
    await session.flush()
    course = await CourseService.create(
        session,
        course_code="MIS-PLATFORM",
        course_name="Management Information Systems",
        academic_year="2026",
        semester="autumn",
        instructor_id=instructor.id,
    )
    sections = []
    instances = []
    teams = []
    enrollments = []
    for index, (code, (pack_key, pack_version)) in enumerate(zip(("A", "B"), pack_tuples), start=1):
        section = await SectionService.create(session, course.id, section_code=code, section_name=f"Section {code}")
        instance = await InstanceService.create(
            session, section.id, pack_key=pack_key, pack_version=pack_version, total_rounds=6, settings={}
        )
        sections.append(section)
        instances.append(instance)
        for team_number in (1, 2):
            team = await TeamService.create(session, instance.instance_id, section.id, name=f"Section {code} Team {team_number}")
            teams.append(team)
        for student_number in range(1, 9):
            student = User(
                student_id=f"M2-{index}{student_number:02d}",
                name=f"M2 Student {index}-{student_number}",
                email=f"m2.student.{index}.{student_number}@example.edu",
                role="student",
            )
            session.add(student)
            await session.flush()
            enrollment = await EnrollmentService.create(
                session,
                section.id,
                student.id,
                team_id=teams[-2 + (student_number > 4)].id,
            )
            enrollments.append(enrollment)
    await session.commit()
    return {"course": course, "sections": sections, "instances": instances, "teams": teams, "enrollments": enrollments}


def _local_database(url: str) -> bool:
    parsed = make_url(url)
    if parsed.get_backend_name() == "sqlite":
        return True
    return (parsed.host or "").lower() in {"localhost", "127.0.0.1", "::1", "db"}


async def seed_users(session, cohort: dict | None = None) -> dict:
    """Create or update deterministic development accounts without emitting secrets."""
    from app.config import settings
    if not _local_database(settings.DATABASE_URL):
        raise RuntimeError("--users refuses non-local DATABASE_URL")
    if cohort is None:
        cohort = await seed_cohort(session)
    accounts = []
    for index in range(1, 17):
        student_id = f"M2-{1 if index <= 8 else 2}{index if index <= 8 else index - 8:02d}"
        email = f"m2.student.{1 if index <= 8 else 2}.{index if index <= 8 else index - 8}@example.edu"
        user = await session.scalar(select(User).where(User.student_id == student_id))
        if user is None:
            user = User(student_id=student_id, name=f"M2 Student {index}", email=email, role="student")
            session.add(user)
        user.password_hash = hash_password("StudentPass!2026")
        user.is_active = True
        accounts.append(user)
    for email, name, role, password in (
        ("m2.instructor.a@example.edu", "M2 Instructor A", "instructor", "InstructorPass!2026"),
        ("m2.instructor.b@example.edu", "M2 Instructor B", "instructor", "InstructorPass!2026"),
        ("m2.admin@example.edu", "M2 Administrator", "admin", "AdminPass!2026"),
    ):
        user = await session.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(name=name, email=email, role=role)
            session.add(user)
        user.password_hash = hash_password(password)
        user.is_active = True
        accounts.append(user)
    await session.flush()
    return {"cohort": cohort, "users": accounts}


def _run_cohort(with_users: bool = False) -> int:
    async def run() -> None:
        async with async_session() as session:
            cohort = await seed_cohort(session)
            if with_users:
                await seed_users(session, cohort)
                await session.commit()
            print(
                f"cohort course={cohort['course'].course_code} sections={len(cohort['sections'])} "
                f"instances={len(cohort['instances'])} teams={len(cohort['teams'])} "
                f"enrollments={len(cohort['enrollments'])}"
            )
            for section, instance in zip(cohort["sections"], cohort["instances"]):
                print(f"  section={section.section_code} pack={instance.pack_key}@{instance.pack_version}")

    asyncio.run(run())
    return 0


def _run_packs() -> int:
    async def run() -> None:
        async with async_session() as session:
            await session.run_sync(
                lambda sync: [
                    register_casepack(sync, _BACKEND_ROOT / "packs" / name)
                    for name in ("riverside_grocery", "m2_isolation_fixture")
                ]
            )
            await session.commit()
            rows = (await session.scalars(select(Casepack))).all()
            for row in rows:
                print(f"pack {row.pack_key}@{row.pack_version} digest={row.pack_digest}")

    from sqlalchemy import select
    from app.models.platform import Casepack

    asyncio.run(run())
    return 0


def _main() -> int:
    parser = argparse.ArgumentParser(prog="app.seed.demo")
    parser.add_argument("--scenario", default="riverside_r3", help="scenario name, e.g. riverside_r3")
    parser.add_argument(
        "--with-signals", action="store_true",
        help="also seed the R1-R3 signal ledger and demonstrate the two paths",
    )
    parser.add_argument(
        "--full", action="store_true",
        help="seed and run the full six-round game into the database (spec section 5.5)",
    )
    parser.add_argument("--cohort", action="store_true", help="seed the deterministic two-section platform cohort")
    parser.add_argument("--packs", action="store_true", help="register the two runtime-capable demo packs")
    parser.add_argument("--users", action="store_true", help="seed deterministic development auth accounts (requires --cohort)")
    args = parser.parse_args()

    if args.full:
        return _run_full()
    if args.cohort or args.users:
        return _run_cohort(with_users=args.users)
    if args.packs:
        return _run_packs()

    pack, state = load_scenario(args.scenario)
    print(_describe(args.scenario, pack, state))
    if args.with_signals:
        print(_describe_signals(pack, state))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
