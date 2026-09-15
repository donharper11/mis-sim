"""Thin hierarchy CRUD services for M2 packet 2.1.

These services only read and write the six platform identity tables.  Runtime
state ownership and instance guards are deliberately deferred to packet 2.2.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import Course, Enrollment, Section, SimulationInstance, Team, User


class PlatformNotFound(LookupError):
    pass


class PlatformConflict(ValueError):
    pass


class DeletionBlocked(RuntimeError):
    pass


async def _one(session: AsyncSession, model, ident: int, label: str):
    row = await session.get(model, ident)
    if row is None:
        raise PlatformNotFound(f"{label} {ident} was not found")
    return row


class CourseService:
    @staticmethod
    async def create(session: AsyncSession, **values) -> Course:
        course = Course(**values)
        session.add(course)
        await session.flush()
        return course

    @staticmethod
    async def read(session: AsyncSession, course_id: int) -> Course:
        return await _one(session, Course, course_id, "Course")

    @staticmethod
    async def delete(session: AsyncSession, course_id: int) -> None:
        course = await CourseService.read(session, course_id)
        sections = (await session.scalars(select(Section).where(Section.course_id == course.id))).all()
        instances = []
        for section in sections:
            instance = await session.scalar(select(SimulationInstance).where(SimulationInstance.section_id == section.id))
            if instance is not None:
                instances.append(instance)
        blocked = next((item for item in instances if item.status != "setup"), None)
        if blocked is not None:
            raise DeletionBlocked(
                f"Cannot delete course {course.id}: simulation instance {blocked.instance_id} "
                f"is {blocked.status} and may contain live state"
            )
        for section in sections:
            await SectionService._delete_setup_section(session, section)
        await session.delete(course)
        await session.flush()


class SectionService:
    @staticmethod
    async def create(session: AsyncSession, course_id: int, **values) -> Section:
        await CourseService.read(session, course_id)
        section = Section(course_id=course_id, **values)
        session.add(section)
        await session.flush()
        return section

    @staticmethod
    async def read(session: AsyncSession, section_id: int) -> Section:
        return await _one(session, Section, section_id, "Section")

    @staticmethod
    async def _delete_setup_section(session: AsyncSession, section: Section) -> None:
        instance = await session.scalar(select(SimulationInstance).where(SimulationInstance.section_id == section.id))
        if instance is not None:
            if instance.status != "setup":
                raise DeletionBlocked(
                    f"Cannot delete section {section.id}: simulation instance {instance.instance_id} "
                    f"is {instance.status} and may contain live state"
                )
            teams = (await session.scalars(select(Team).where(Team.section_id == section.id))).all()
            for team in teams:
                await session.execute(Enrollment.__table__.delete().where(Enrollment.team_id == team.id))
                await session.delete(team)
            await session.delete(instance)
        await session.execute(Enrollment.__table__.delete().where(Enrollment.section_id == section.id))
        await session.delete(section)
        await session.flush()

    @staticmethod
    async def delete(session: AsyncSession, section_id: int) -> None:
        section = await SectionService.read(session, section_id)
        await SectionService._delete_setup_section(session, section)


class InstanceService:
    @staticmethod
    async def create(session: AsyncSession, section_id: int, **values) -> SimulationInstance:
        await SectionService.read(session, section_id)
        existing = await session.scalar(select(SimulationInstance).where(SimulationInstance.section_id == section_id))
        if existing is not None:
            raise PlatformConflict(f"Section {section_id} already has simulation instance {existing.instance_id}")
        instance = SimulationInstance(section_id=section_id, **values)
        session.add(instance)
        await session.flush()
        return instance

    @staticmethod
    async def read(session: AsyncSession, instance_id: int) -> SimulationInstance:
        return await _one(session, SimulationInstance, instance_id, "Simulation instance")

    @staticmethod
    async def delete(session: AsyncSession, instance_id: int) -> None:
        instance = await InstanceService.read(session, instance_id)
        if instance.status != "setup":
            raise DeletionBlocked(
                f"Cannot delete simulation instance {instance.instance_id}: it is {instance.status} "
                "and may contain live state"
            )
        raise DeletionBlocked(
            f"Cannot delete simulation instance {instance.instance_id} directly; delete its section "
            "so the hierarchy cascade is explicit"
        )


class TeamService:
    @staticmethod
    async def create(session: AsyncSession, instance_id: int, section_id: int, **values) -> Team:
        instance = await InstanceService.read(session, instance_id)
        await SectionService.read(session, section_id)
        if instance.section_id != section_id:
            raise PlatformConflict("Team section_id must match the simulation instance's section")
        team = Team(instance_id=instance_id, section_id=section_id, **values)
        session.add(team)
        await session.flush()
        return team

    @staticmethod
    async def read(
        session: AsyncSession,
        team_id: int,
        *,
        section_id: int | None = None,
        instance_id: int | None = None,
    ) -> Team:
        if section_id is None and instance_id is None:
            raise PlatformConflict("Team reads require section_id or instance_id scope")
        predicates = [Team.id == team_id]
        if section_id is not None:
            predicates.append(Team.section_id == section_id)
        if instance_id is not None:
            predicates.append(Team.instance_id == instance_id)
        row = await session.scalar(select(Team).where(*predicates))
        if row is None:
            raise PlatformNotFound(f"Team {team_id} was not found in the requested scope")
        return row


class EnrollmentService:
    @staticmethod
    async def create(session: AsyncSession, section_id: int, user_id: int, team_id: int | None = None, **values) -> Enrollment:
        await SectionService.read(session, section_id)
        await _one(session, User, user_id, "User")
        if team_id is not None:
            try:
                team = await TeamService.read(session, team_id, section_id=section_id)
            except PlatformNotFound as exc:
                raise PlatformConflict("Enrollment team_id must belong to the enrollment section") from exc
            if team.section_id != section_id:
                raise PlatformConflict("Enrollment team_id must belong to the enrollment section")
        existing = await session.scalar(
            select(Enrollment).where(Enrollment.user_id == user_id, Enrollment.section_id == section_id)
        )
        if existing is not None:
            raise PlatformConflict(f"User {user_id} is already enrolled in section {section_id}")
        enrollment = Enrollment(section_id=section_id, user_id=user_id, team_id=team_id, **values)
        session.add(enrollment)
        await session.flush()
        return enrollment

    @staticmethod
    async def read(
        session: AsyncSession,
        enrollment_id: int,
        *,
        section_id: int | None = None,
        instance_id: int | None = None,
    ) -> Enrollment:
        if section_id is None and instance_id is None:
            raise PlatformConflict("Enrollment reads require section_id or instance_id scope")
        predicates = [Enrollment.id == enrollment_id]
        if section_id is not None:
            predicates.append(Enrollment.section_id == section_id)
        query = select(Enrollment)
        if instance_id is not None:
            query = query.join(SimulationInstance, SimulationInstance.section_id == Enrollment.section_id)
            predicates.append(SimulationInstance.instance_id == instance_id)
        row = await session.scalar(query.where(*predicates))
        if row is None:
            raise PlatformNotFound(f"Enrollment {enrollment_id} was not found in the requested scope")
        return row
