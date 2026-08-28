import uuid
from datetime import time

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.master_schedule.models import (
    MasterSchedule,
    WeekDay,
)
from src.master_schedule.repository import (
    MasterScheduleRepository,
)
from src.masters.models import Master


def make_schedule(
    *,
    master_id: uuid.UUID,
    day_of_week: WeekDay,
    start_time: time | None = time(9, 0),
    end_time: time | None = time(17, 0),
    is_working: bool = True,
) -> MasterSchedule:
    return MasterSchedule(
        master_id=master_id,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        is_working=is_working,
    )


@pytest.mark.anyio
async def test_create_schedule(
    db_session: AsyncSession,
    master: Master,
):
    repository = MasterScheduleRepository(db_session)

    schedule = make_schedule(
        master_id=master.id,
        day_of_week=WeekDay.WEDNESDAY,
    )

    result = await repository.create(schedule)

    assert result.id is not None
    assert isinstance(
        result.id,
        uuid.UUID,
    )

    assert result.master_id == master.id
    assert result.day_of_week == WeekDay.WEDNESDAY
    assert result.start_time == time(
        9,
        0,
    )
    assert result.end_time == time(
        17,
        0,
    )
    assert result.is_working is True


@pytest.mark.anyio
async def test_get_schedule_by_id(
    db_session: AsyncSession,
    monday_schedule: MasterSchedule,
):
    repository = MasterScheduleRepository(db_session)

    schedule_id = monday_schedule.id

    db_session.expunge(monday_schedule)

    result = await repository.get_by_id(schedule_id)

    assert result is not None
    assert result.id == schedule_id
    assert result.day_of_week == WeekDay.MONDAY
    assert result.start_time == time(
        9,
        0,
    )
    assert result.end_time == time(
        17,
        0,
    )


@pytest.mark.anyio
async def test_get_schedule_by_id_not_found(
    db_session: AsyncSession,
):
    repository = MasterScheduleRepository(db_session)

    result = await repository.get_by_id(uuid.uuid4())

    assert result is None


@pytest.mark.anyio
async def test_get_schedules_by_master_id_sorted_and_scoped(
    db_session: AsyncSession,
    master: Master,
    monday_schedule: MasterSchedule,
    tuesday_schedule: MasterSchedule,
    day_off_schedule: MasterSchedule,
    foreign_schedule: MasterSchedule,
):
    repository = MasterScheduleRepository(db_session)

    result = await repository.get_by_master_id(master.id)

    assert [schedule.id for schedule in result] == [
        monday_schedule.id,
        tuesday_schedule.id,
        day_off_schedule.id,
    ]

    assert all(schedule.master_id == master.id for schedule in result)

    assert foreign_schedule.id not in {schedule.id for schedule in result}


@pytest.mark.anyio
async def test_get_schedules_by_master_id_empty(
    db_session: AsyncSession,
    second_master: Master,
):
    repository = MasterScheduleRepository(db_session)

    result = await repository.get_by_master_id(second_master.id)

    assert result == []


@pytest.mark.anyio
async def test_get_schedule_by_master_and_day(
    db_session: AsyncSession,
    master: Master,
    monday_schedule: MasterSchedule,
):
    repository = MasterScheduleRepository(db_session)

    result = await repository.get_by_master_and_day(
        master_id=master.id,
        day_of_week=WeekDay.MONDAY,
    )

    assert result is not None
    assert result.id == monday_schedule.id
    assert result.master_id == master.id
    assert result.day_of_week == WeekDay.MONDAY


@pytest.mark.anyio
async def test_get_schedule_by_master_and_day_not_found(
    db_session: AsyncSession,
    master: Master,
):
    repository = MasterScheduleRepository(db_session)

    result = await repository.get_by_master_and_day(
        master_id=master.id,
        day_of_week=WeekDay.FRIDAY,
    )

    assert result is None


@pytest.mark.anyio
async def test_update_schedule(
    db_session: AsyncSession,
    monday_schedule: MasterSchedule,
):
    repository = MasterScheduleRepository(db_session)

    monday_schedule.start_time = time(
        10,
        30,
    )

    monday_schedule.end_time = time(
        19,
        0,
    )

    result = await repository.update(monday_schedule)

    assert result.start_time == time(
        10,
        30,
    )
    assert result.end_time == time(
        19,
        0,
    )

    schedule_id = result.id

    db_session.expunge(result)

    schedule_from_database = await repository.get_by_id(schedule_id)

    assert schedule_from_database is not None

    assert schedule_from_database.start_time == time(
        10,
        30,
    )

    assert schedule_from_database.end_time == time(
        19,
        0,
    )


@pytest.mark.anyio
async def test_delete_schedule(
    db_session: AsyncSession,
    monday_schedule: MasterSchedule,
):
    repository = MasterScheduleRepository(db_session)

    schedule_id = monday_schedule.id

    await repository.delete(monday_schedule)

    result = await repository.get_by_id(schedule_id)

    assert result is None
