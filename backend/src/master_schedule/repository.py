import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.master_schedule.models import (
    MasterSchedule,
    WeekDay,
)


class MasterScheduleRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def get_by_id(
        self,
        schedule_id: uuid.UUID,
    ) -> MasterSchedule | None:
        return await self.session.scalar(
            select(MasterSchedule).where(MasterSchedule.id == schedule_id)
        )

    async def get_by_master_id(
        self,
        master_id: uuid.UUID,
    ) -> list[MasterSchedule]:
        result = await self.session.scalars(
            select(MasterSchedule)
            .where(MasterSchedule.master_id == master_id)
            .order_by(MasterSchedule.day_of_week.asc())
        )

        return list(result.all())

    async def get_by_master_and_day(
        self,
        master_id: uuid.UUID,
        day_of_week: WeekDay,
    ) -> MasterSchedule | None:
        return await self.session.scalar(
            select(MasterSchedule).where(
                MasterSchedule.master_id == master_id,
                MasterSchedule.day_of_week == day_of_week,
            )
        )

    async def create(
        self,
        schedule: MasterSchedule,
    ) -> MasterSchedule:
        self.session.add(schedule)

        await self.session.commit()
        await self.session.refresh(schedule)

        return schedule

    async def update(
        self,
        schedule: MasterSchedule,
    ) -> MasterSchedule:
        await self.session.commit()
        await self.session.refresh(schedule)

        return schedule

    async def delete(
        self,
        schedule: MasterSchedule,
    ) -> None:
        await self.session.delete(schedule)

        await self.session.commit()
