from datetime import time

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.master_schedule.models import (
    MasterSchedule,
    WeekDay,
)
from src.masters.models import Master


@pytest.fixture
async def monday_schedule(
    db_session: AsyncSession,
    master: Master,
) -> MasterSchedule:
    schedule = MasterSchedule(
        master_id=master.id,
        day_of_week=WeekDay.MONDAY,
        start_time=time(
            9,
            0,
        ),
        end_time=time(
            17,
            0,
        ),
        is_working=True,
    )

    db_session.add(schedule)
    await db_session.commit()
    await db_session.refresh(
        schedule
    )

    return schedule


@pytest.fixture
async def tuesday_schedule(
    db_session: AsyncSession,
    master: Master,
) -> MasterSchedule:
    schedule = MasterSchedule(
        master_id=master.id,
        day_of_week=WeekDay.TUESDAY,
        start_time=time(
            10,
            0,
        ),
        end_time=time(
            18,
            0,
        ),
        is_working=True,
    )

    db_session.add(schedule)
    await db_session.commit()
    await db_session.refresh(
        schedule
    )

    return schedule


@pytest.fixture
async def day_off_schedule(
    db_session: AsyncSession,
    master: Master,
) -> MasterSchedule:
    schedule = MasterSchedule(
        master_id=master.id,
        day_of_week=WeekDay.SUNDAY,
        start_time=None,
        end_time=None,
        is_working=False,
    )

    db_session.add(schedule)
    await db_session.commit()
    await db_session.refresh(
        schedule
    )

    return schedule


@pytest.fixture
async def foreign_schedule(
    db_session: AsyncSession,
    second_master: Master,
) -> MasterSchedule:
    schedule = MasterSchedule(
        master_id=second_master.id,
        day_of_week=WeekDay.WEDNESDAY,
        start_time=time(
            9,
            0,
        ),
        end_time=time(
            15,
            0,
        ),
        is_working=True,
    )

    db_session.add(schedule)
    await db_session.commit()
    await db_session.refresh(
        schedule
    )

    return schedule