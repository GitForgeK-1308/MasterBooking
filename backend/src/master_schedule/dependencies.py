from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_async_session
from src.master_schedule.repository import (
    MasterScheduleRepository,
)
from src.master_schedule.service import (
    MasterScheduleService,
)
from src.masters.repository import MasterRepository
from src.redis.dependencies import get_redis


def get_schedule_service(
    session: AsyncSession = Depends(
        get_async_session
        
    ),
    redis: Redis = Depends(
        get_redis
    )
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
        redis_client=redis,
    )