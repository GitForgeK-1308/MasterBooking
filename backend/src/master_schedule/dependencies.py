from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_async_session
from src.master_schedule.repository import (
    MasterScheduleRepository,
)
from src.master_schedule.service import (
    MasterScheduleService,
)
from src.masters.repository import MasterRepository


def get_schedule_service(
    session: AsyncSession = Depends(
        get_async_session
    ),
) -> MasterScheduleService:
    schedule_repository = MasterScheduleRepository(
        session
    )

    master_repository = MasterRepository(
        session
    )

    return MasterScheduleService(
        schedule_repository=schedule_repository,
        master_repository=master_repository,
    )