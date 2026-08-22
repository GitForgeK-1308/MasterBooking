import uuid
from datetime import time
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.master_schedule.exceptions import (
    MasterNotFoundError,
    ScheduleAccessDeniedError,
    ScheduleAlreadyExistsError,
)
from src.master_schedule.models import (
    MasterSchedule,
    WeekDay,
)
from src.master_schedule.repository import (
    MasterScheduleRepository,
)
from src.master_schedule.schemas import (
    MasterScheduleCreate,
    MasterScheduleUpdate,
)
from src.master_schedule.service import (
    MasterScheduleService,
)
from src.masters.repository import MasterRepository


def make_master():
    return SimpleNamespace(
        id=uuid.uuid4()
    )


def make_schedule(
    *,
    master_id: uuid.UUID | None = None,
    day_of_week: WeekDay = WeekDay.MONDAY,
    start_time: time | None = time(9, 0),
    end_time: time | None = time(17, 0),
    is_working: bool = True,
) -> MasterSchedule:
    return MasterSchedule(
        id=uuid.uuid4(),
        master_id=master_id or uuid.uuid4(),
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        is_working=is_working,
    )


@pytest.fixture
def schedule_repository() -> AsyncMock:
    return AsyncMock(
        spec=MasterScheduleRepository
    )


@pytest.fixture
def master_repository() -> AsyncMock:
    return AsyncMock(
        spec=MasterRepository
    )


@pytest.fixture
def redis_client() -> AsyncMock:
    redis = AsyncMock()

    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.delete = AsyncMock()

    return redis


@pytest.fixture
def schedule_service(
    schedule_repository: AsyncMock,
    master_repository: AsyncMock,
    redis_client: AsyncMock,
) -> MasterScheduleService:
    return MasterScheduleService(
        schedule_repository=schedule_repository,
        master_repository=master_repository,
        redis_client=redis_client,
        
    )


@pytest.mark.anyio
async def test_get_schedule_by_id(
    schedule_service: MasterScheduleService,
    schedule_repository: AsyncMock,
):
    schedule = make_schedule()

    schedule_repository.get_by_id.return_value = (
        schedule
    )

    result = await schedule_service.get_schedule_by_id(
        schedule.id
    )

    assert result is schedule

    schedule_repository.get_by_id.assert_awaited_once_with(
        schedule.id
    )


@pytest.mark.anyio
async def test_get_master_schedules(
    schedule_service: MasterScheduleService,
    schedule_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    schedules = [
        make_schedule(
            master_id=master_id,
            day_of_week=WeekDay.MONDAY,
        ),
        make_schedule(
            master_id=master_id,
            day_of_week=WeekDay.TUESDAY,
        ),
    ]

    schedule_repository.get_by_master_id.return_value = (
        schedules
    )

    result = await schedule_service.get_master_schedules(
        master_id
    )

    assert result == schedules

    schedule_repository.get_by_master_id.assert_awaited_once_with(
        master_id
    )


@pytest.mark.anyio
async def test_create_schedule(
    schedule_service: MasterScheduleService,
    schedule_repository: AsyncMock,
    master_repository: AsyncMock,
):
    master = make_master()

    master_repository.get_by_id.return_value = (
        master
    )

    schedule_repository.get_by_master_and_day.return_value = (
        None
    )

    schedule_repository.create.side_effect = (
        lambda schedule: schedule
    )

    data = MasterScheduleCreate(
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

    result = await schedule_service.create_schedule(
        master_id=master.id,
        data=data,
    )

    assert result.master_id == master.id
    assert result.day_of_week == WeekDay.MONDAY
    assert result.start_time == time(
        9,
        0,
    )
    assert result.end_time == time(
        17,
        0,
    )
    assert result.is_working is True

    master_repository.get_by_id.assert_awaited_once_with(
        master.id
    )

    schedule_repository.get_by_master_and_day.assert_awaited_once_with(
        master_id=master.id,
        day_of_week=WeekDay.MONDAY,
    )

    schedule_repository.create.assert_awaited_once_with(
        result
    )


@pytest.mark.anyio
async def test_create_day_off_schedule(
    schedule_service: MasterScheduleService,
    schedule_repository: AsyncMock,
    master_repository: AsyncMock,
):
    master = make_master()

    master_repository.get_by_id.return_value = (
        master
    )

    schedule_repository.get_by_master_and_day.return_value = (
        None
    )

    schedule_repository.create.side_effect = (
        lambda schedule: schedule
    )

    data = MasterScheduleCreate(
        day_of_week=WeekDay.SUNDAY,
        is_working=False,
    )

    result = await schedule_service.create_schedule(
        master_id=master.id,
        data=data,
    )

    assert result.day_of_week == WeekDay.SUNDAY
    assert result.start_time is None
    assert result.end_time is None
    assert result.is_working is False


@pytest.mark.anyio
async def test_create_schedule_master_not_found(
    schedule_service: MasterScheduleService,
    schedule_repository: AsyncMock,
    master_repository: AsyncMock,
):
    master_repository.get_by_id.return_value = None

    data = MasterScheduleCreate(
        day_of_week=WeekDay.MONDAY,
        start_time=time(
            9,
            0,
        ),
        end_time=time(
            17,
            0,
        ),
    )

    with pytest.raises(
        MasterNotFoundError
    ):
        await schedule_service.create_schedule(
            master_id=uuid.uuid4(),
            data=data,
        )

    schedule_repository.get_by_master_and_day.assert_not_awaited()
    schedule_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_create_schedule_already_exists(
    schedule_service: MasterScheduleService,
    schedule_repository: AsyncMock,
    master_repository: AsyncMock,
):
    master = make_master()

    existing_schedule = make_schedule(
        master_id=master.id
    )

    master_repository.get_by_id.return_value = (
        master
    )

    schedule_repository.get_by_master_and_day.return_value = (
        existing_schedule
    )

    data = MasterScheduleCreate(
        day_of_week=WeekDay.MONDAY,
        start_time=time(
            10,
            0,
        ),
        end_time=time(
            18,
            0,
        ),
    )

    with pytest.raises(
        ScheduleAlreadyExistsError
    ):
        await schedule_service.create_schedule(
            master_id=master.id,
            data=data,
        )

    schedule_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_update_schedule_not_found(
    schedule_service: MasterScheduleService,
    schedule_repository: AsyncMock,
):
    schedule_repository.get_by_id.return_value = None

    result = await schedule_service.update_schedule(
        schedule_id=uuid.uuid4(),
        master_id=uuid.uuid4(),
        data=MasterScheduleUpdate(
            start_time=time(
                10,
                0,
            )
        ),
    )

    assert result is None

    schedule_repository.update.assert_not_awaited()


@pytest.mark.anyio
async def test_update_schedule_access_denied(
    schedule_service: MasterScheduleService,
    schedule_repository: AsyncMock,
):
    schedule = make_schedule()

    schedule_repository.get_by_id.return_value = (
        schedule
    )

    with pytest.raises(
        ScheduleAccessDeniedError
    ):
        await schedule_service.update_schedule(
            schedule_id=schedule.id,
            master_id=uuid.uuid4(),
            data=MasterScheduleUpdate(
                start_time=time(
                    10,
                    0,
                )
            ),
        )

    schedule_repository.update.assert_not_awaited()


@pytest.mark.anyio
async def test_update_schedule_times(
    schedule_service: MasterScheduleService,
    schedule_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    schedule = make_schedule(
        master_id=master_id
    )

    schedule_repository.get_by_id.return_value = (
        schedule
    )

    schedule_repository.update.side_effect = (
        lambda item: item
    )

    result = await schedule_service.update_schedule(
        schedule_id=schedule.id,
        master_id=master_id,
        data=MasterScheduleUpdate(
            start_time=time(
                10,
                0,
            ),
            end_time=time(
                19,
                0,
            ),
        ),
    )

    assert result is schedule
    assert result.start_time == time(
        10,
        0,
    )
    assert result.end_time == time(
        19,
        0,
    )
    assert result.is_working is True

    schedule_repository.update.assert_awaited_once_with(
        schedule
    )


@pytest.mark.anyio
async def test_update_schedule_day(
    schedule_service: MasterScheduleService,
    schedule_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    schedule = make_schedule(
        master_id=master_id,
        day_of_week=WeekDay.MONDAY,
    )

    schedule_repository.get_by_id.return_value = (
        schedule
    )

    schedule_repository.get_by_master_and_day.return_value = (
        None
    )

    schedule_repository.update.side_effect = (
        lambda item: item
    )

    result = await schedule_service.update_schedule(
        schedule_id=schedule.id,
        master_id=master_id,
        data=MasterScheduleUpdate(
            day_of_week=WeekDay.WEDNESDAY,
        ),
    )

    assert result is schedule
    assert (
        result.day_of_week
        == WeekDay.WEDNESDAY
    )

    schedule_repository.get_by_master_and_day.assert_awaited_once_with(
        master_id=master_id,
        day_of_week=WeekDay.WEDNESDAY,
    )


@pytest.mark.anyio
async def test_update_schedule_same_day_does_not_check_duplicate(
    schedule_service: MasterScheduleService,
    schedule_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    schedule = make_schedule(
        master_id=master_id,
        day_of_week=WeekDay.MONDAY,
    )

    schedule_repository.get_by_id.return_value = (
        schedule
    )

    schedule_repository.update.side_effect = (
        lambda item: item
    )

    result = await schedule_service.update_schedule(
        schedule_id=schedule.id,
        master_id=master_id,
        data=MasterScheduleUpdate(
            day_of_week=WeekDay.MONDAY,
        ),
    )

    assert result is schedule

    schedule_repository.get_by_master_and_day.assert_not_awaited()
    schedule_repository.update.assert_awaited_once_with(
        schedule
    )


@pytest.mark.anyio
async def test_update_schedule_duplicate_day(
    schedule_service: MasterScheduleService,
    schedule_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    schedule = make_schedule(
        master_id=master_id,
        day_of_week=WeekDay.MONDAY,
    )

    existing_schedule = make_schedule(
        master_id=master_id,
        day_of_week=WeekDay.TUESDAY,
    )

    schedule_repository.get_by_id.return_value = (
        schedule
    )

    schedule_repository.get_by_master_and_day.return_value = (
        existing_schedule
    )

    with pytest.raises(
        ScheduleAlreadyExistsError
    ):
        await schedule_service.update_schedule(
            schedule_id=schedule.id,
            master_id=master_id,
            data=MasterScheduleUpdate(
                day_of_week=WeekDay.TUESDAY,
            ),
        )

    schedule_repository.update.assert_not_awaited()


@pytest.mark.anyio
async def test_update_schedule_to_day_off_clears_times(
    schedule_service: MasterScheduleService,
    schedule_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    schedule = make_schedule(
        master_id=master_id
    )

    schedule_repository.get_by_id.return_value = (
        schedule
    )

    schedule_repository.update.side_effect = (
        lambda item: item
    )

    result = await schedule_service.update_schedule(
        schedule_id=schedule.id,
        master_id=master_id,
        data=MasterScheduleUpdate(
            is_working=False
        ),
    )

    assert result is schedule
    assert result.is_working is False
    assert result.start_time is None
    assert result.end_time is None


@pytest.mark.anyio
async def test_update_day_off_to_working_requires_time(
    schedule_service: MasterScheduleService,
    schedule_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    schedule = make_schedule(
        master_id=master_id,
        day_of_week=WeekDay.SUNDAY,
        start_time=None,
        end_time=None,
        is_working=False,
    )

    schedule_repository.get_by_id.return_value = (
        schedule
    )

    with pytest.raises(
        ValueError,
        match=(
            "Для рабочего дня необходимо "
            "указать время начала и окончания"
        ),
    ):
        await schedule_service.update_schedule(
            schedule_id=schedule.id,
            master_id=master_id,
            data=MasterScheduleUpdate(
                is_working=True
            ),
        )

    schedule_repository.update.assert_not_awaited()


@pytest.mark.anyio
async def test_update_schedule_invalid_time_range(
    schedule_service: MasterScheduleService,
    schedule_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    schedule = make_schedule(
        master_id=master_id
    )

    schedule_repository.get_by_id.return_value = (
        schedule
    )

    with pytest.raises(
        ValueError,
        match=(
            "Время начала должно быть раньше "
            "времени окончания"
        ),
    ):
        await schedule_service.update_schedule(
            schedule_id=schedule.id,
            master_id=master_id,
            data=MasterScheduleUpdate(
                start_time=time(
                    18,
                    0,
                ),
                end_time=time(
                    9,
                    0,
                ),
            ),
        )

    schedule_repository.update.assert_not_awaited()


@pytest.mark.anyio
async def test_delete_schedule(
    schedule_service: MasterScheduleService,
    schedule_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    schedule = make_schedule(
        master_id=master_id
    )

    schedule_repository.get_by_id.return_value = (
        schedule
    )

    result = await schedule_service.delete_schedule(
        schedule_id=schedule.id,
        master_id=master_id,
    )

    assert result is True

    schedule_repository.delete.assert_awaited_once_with(
        schedule
    )


@pytest.mark.anyio
async def test_delete_schedule_not_found(
    schedule_service: MasterScheduleService,
    schedule_repository: AsyncMock,
):
    schedule_repository.get_by_id.return_value = None

    result = await schedule_service.delete_schedule(
        schedule_id=uuid.uuid4(),
        master_id=uuid.uuid4(),
    )

    assert result is None

    schedule_repository.delete.assert_not_awaited()


@pytest.mark.anyio
async def test_delete_schedule_access_denied(
    schedule_service: MasterScheduleService,
    schedule_repository: AsyncMock,
):
    schedule = make_schedule()

    schedule_repository.get_by_id.return_value = (
        schedule
    )

    with pytest.raises(
        ScheduleAccessDeniedError
    ):
        await schedule_service.delete_schedule(
            schedule_id=schedule.id,
            master_id=uuid.uuid4(),
        )

    schedule_repository.delete.assert_not_awaited()



@pytest.mark.anyio
async def test_get_master_schedules_from_cache(
    schedule_service: MasterScheduleService,
    schedule_repository: AsyncMock,
    redis_client: AsyncMock,
):
    master_id = uuid.uuid4()

    schedules = [
        make_schedule(
            master_id=master_id,
            day_of_week=WeekDay.MONDAY,
        ),
        make_schedule(
            master_id=master_id,
            day_of_week=WeekDay.TUESDAY,
        ),
    ]

    cached_data = schedule_service._serialize_schedules(
        schedules
    )

    redis_client.get.return_value = cached_data

    result = await schedule_service.get_master_schedules(
        master_id
    )

    assert len(result) == 2
    assert result[0].day_of_week == WeekDay.MONDAY
    assert result[1].day_of_week == WeekDay.TUESDAY

    redis_client.get.assert_awaited_once_with(
        f"master:{master_id}:schedule"
    )

    schedule_repository.get_by_master_id.assert_not_awaited()

    redis_client.set.assert_not_awaited()


@pytest.mark.anyio
async def test_get_master_schedules_cache_miss(
    schedule_service: MasterScheduleService,
    schedule_repository: AsyncMock,
    redis_client: AsyncMock,
):
    master_id = uuid.uuid4()

    schedules = [
        make_schedule(
            master_id=master_id,
            day_of_week=WeekDay.MONDAY,
        ),
        make_schedule(
            master_id=master_id,
            day_of_week=WeekDay.TUESDAY,
        ),
    ]

    redis_client.get.return_value = None

    schedule_repository.get_by_master_id.return_value = (
        schedules
    )

    result = await schedule_service.get_master_schedules(
        master_id
    )

    assert result == schedules

    redis_client.get.assert_awaited_once_with(
        f"master:{master_id}:schedule"
    )

    schedule_repository.get_by_master_id.assert_awaited_once_with(
        master_id
    )

    redis_client.set.assert_awaited_once()

    args, kwargs = redis_client.set.await_args

    assert args[0] == f"master:{master_id}:schedule"
    assert kwargs["ex"] == 300


@pytest.mark.anyio
async def test_create_schedule_invalidates_cache(
    schedule_service: MasterScheduleService,
    schedule_repository: AsyncMock,
    master_repository: AsyncMock,
    redis_client: AsyncMock,
):
    master = make_master()

    master_repository.get_by_id.return_value = master
    schedule_repository.get_by_master_and_day.return_value = None
    schedule_repository.create.side_effect = (
        lambda schedule: schedule
    )

    data = MasterScheduleCreate(
        day_of_week=WeekDay.MONDAY,
        start_time=time(9, 0),
        end_time=time(17, 0),
        is_working=True,
    )

    await schedule_service.create_schedule(
        master_id=master.id,
        data=data,
    )

    redis_client.delete.assert_awaited_once_with(
        f"master:{master.id}:schedule"
    )


@pytest.mark.anyio
async def test_update_schedule_invalidates_cache(
    schedule_service: MasterScheduleService,
    schedule_repository: AsyncMock,
    redis_client: AsyncMock,
):
    master_id = uuid.uuid4()

    schedule = make_schedule(
        master_id=master_id,
    )

    schedule_repository.get_by_id.return_value = schedule
    schedule_repository.update.side_effect = (
        lambda item: item
    )

    await schedule_service.update_schedule(
        schedule_id=schedule.id,
        master_id=master_id,
        data=MasterScheduleUpdate(
            start_time=time(10, 0),
            end_time=time(18, 0),
        ),
    )

    redis_client.delete.assert_awaited_once_with(
        f"master:{master_id}:schedule"
    )


@pytest.mark.anyio
async def test_delete_schedule_invalidates_cache(
    schedule_service: MasterScheduleService,
    schedule_repository: AsyncMock,
    redis_client: AsyncMock,
):
    master_id = uuid.uuid4()

    schedule = make_schedule(
        master_id=master_id,
    )

    schedule_repository.get_by_id.return_value = schedule

    await schedule_service.delete_schedule(
        schedule_id=schedule.id,
        master_id=master_id,
    )

    redis_client.delete.assert_awaited_once_with(
        f"master:{master_id}:schedule"
    )