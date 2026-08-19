import uuid
from datetime import time

from src.master_schedule.exceptions import (
    MasterNotFoundError,
    ScheduleAccessDeniedError,
    ScheduleAlreadyExistsError,
)
from src.master_schedule.models import (
    MasterSchedule,
)
from src.master_schedule.repository import (
    MasterScheduleRepository,
)
from src.master_schedule.schemas import (
    MasterScheduleCreate,
    MasterScheduleUpdate,
)
from src.masters.repository import MasterRepository


class MasterScheduleService:
    def __init__(
        self,
        schedule_repository: MasterScheduleRepository,
        master_repository: MasterRepository,
    ) -> None:
        self.schedule_repository = schedule_repository
        self.master_repository = master_repository

    async def get_schedule_by_id(
        self,
        schedule_id: uuid.UUID,
    ) -> MasterSchedule | None:
        return await self.schedule_repository.get_by_id(
            schedule_id
        )

    async def get_master_schedules(
        self,
        master_id: uuid.UUID,
    ) -> list[MasterSchedule]:
        return await self.schedule_repository.get_by_master_id(
            master_id
        )

    async def create_schedule(
        self,
        master_id: uuid.UUID,
        data: MasterScheduleCreate,
    ) -> MasterSchedule:
        master = await self.master_repository.get_by_id(
            master_id
        )

        if master is None:
            raise MasterNotFoundError

        existing_schedule = (
            await self.schedule_repository.get_by_master_and_day(
                master_id=master_id,
                day_of_week=data.day_of_week,
            )
        )

        if existing_schedule is not None:
            raise ScheduleAlreadyExistsError

        new_schedule = MasterSchedule(
            master_id=master_id,
            day_of_week=data.day_of_week,
            start_time=data.start_time,
            end_time=data.end_time,
            is_working=data.is_working,
        )

        return await self.schedule_repository.create(
            new_schedule
        )

    async def update_schedule(
        self,
        schedule_id: uuid.UUID,
        master_id: uuid.UUID,
        data: MasterScheduleUpdate,
    ) -> MasterSchedule | None:
        schedule = await self.schedule_repository.get_by_id(
            schedule_id
        )

        if schedule is None:
            return None

        if schedule.master_id != master_id:
            raise ScheduleAccessDeniedError

        update_data = data.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        new_day_of_week = update_data.get(
            "day_of_week",
            schedule.day_of_week,
        )

        if new_day_of_week != schedule.day_of_week:
            existing_schedule = (
                await self.schedule_repository.get_by_master_and_day(
                    master_id=master_id,
                    day_of_week=new_day_of_week,
                )
            )

            if existing_schedule is not None:
                raise ScheduleAlreadyExistsError

        new_start_time = update_data.get(
            "start_time",
            schedule.start_time,
        )
        new_end_time = update_data.get(
            "end_time",
            schedule.end_time,
        )
        new_is_working = update_data.get(
            "is_working",
            schedule.is_working,
        )

        self._validate_schedule(
            is_working=new_is_working,
            start_time=new_start_time,
            end_time=new_end_time,
        )

        if not new_is_working:
            update_data["start_time"] = None
            update_data["end_time"] = None

        for field, value in update_data.items():
            setattr(
                schedule,
                field,
                value,
            )

        return await self.schedule_repository.update(
            schedule
        )

    async def delete_schedule(
        self,
        schedule_id: uuid.UUID,
        master_id: uuid.UUID,
    ) -> bool | None:
        schedule = await self.schedule_repository.get_by_id(
            schedule_id
        )

        if schedule is None:
            return None

        if schedule.master_id != master_id:
            raise ScheduleAccessDeniedError

        await self.schedule_repository.delete(
            schedule
        )

        return True

    @staticmethod
    def _validate_schedule(
        is_working: bool,
        start_time: time | None,
        end_time: time | None,
    ) -> None:
        if not is_working:
            return

        if (
            start_time is None
            or end_time is None
        ):
            raise ValueError(
                "Для рабочего дня необходимо "
                "указать время начала и окончания"
            )

        if start_time >= end_time:
            raise ValueError(
                "Время начала должно быть раньше "
                "времени окончания"
            )