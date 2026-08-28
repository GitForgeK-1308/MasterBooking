import uuid
from datetime import date, datetime, time, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.bookings.exceptions import (
    BookingInPastError,
    MasterInactiveError,
    MasterNotFoundError,
    MasterScheduleUnavailableError,
    OfferingDoesNotBelongToMasterError,
    OfferingInactiveError,
    OfferingNotFoundError,
)
from src.bookings.repository import BookingRepository
from src.bookings.service import BookingService
from src.master_offering.repository import (
    MasterOfferingRepository,
)
from src.master_schedule.repository import (
    MasterScheduleRepository,
)
from src.masters.repository import MasterRepository


def future_date() -> date:
    return date.today() + timedelta(days=7)


def make_master(
    *,
    master_id: uuid.UUID | None = None,
    is_active: bool = True,
):
    return SimpleNamespace(
        id=master_id or uuid.uuid4(),
        is_active=is_active,
    )


def make_offering(
    *,
    master_id: uuid.UUID,
    offering_id: uuid.UUID | None = None,
    is_active: bool = True,
    duration_minutes: int = 60,
):
    return SimpleNamespace(
        id=offering_id or uuid.uuid4(),
        master_id=master_id,
        is_active=is_active,
        duration_minutes=duration_minutes,
    )


def make_schedule(
    *,
    start_time: time | None = time(9, 0),
    end_time: time | None = time(17, 0),
    is_working: bool = True,
):
    return SimpleNamespace(
        start_time=start_time,
        end_time=end_time,
        is_working=is_working,
    )


def make_existing_booking(
    *,
    booking_date: date,
    start_time: time,
    end_time: time,
):
    return SimpleNamespace(
        booking_date=booking_date,
        start_time=start_time,
        end_time=end_time,
    )


@pytest.fixture
def booking_repository() -> AsyncMock:
    return AsyncMock(spec=BookingRepository)


@pytest.fixture
def master_repository() -> AsyncMock:
    return AsyncMock(spec=MasterRepository)


@pytest.fixture
def offering_repository() -> AsyncMock:
    return AsyncMock(spec=MasterOfferingRepository)


@pytest.fixture
def schedule_repository() -> AsyncMock:
    return AsyncMock(spec=MasterScheduleRepository)


@pytest.fixture
def booking_service(
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
    offering_repository: AsyncMock,
    schedule_repository: AsyncMock,
) -> BookingService:
    return BookingService(
        booking_repository=booking_repository,
        master_repository=master_repository,
        offering_repository=offering_repository,
        schedule_repository=schedule_repository,
    )


def prepare_available_slots(
    *,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
    offering_repository: AsyncMock,
    schedule_repository: AsyncMock,
    master_id: uuid.UUID,
    duration_minutes: int = 60,
):
    master = make_master(master_id=master_id)

    offering = make_offering(
        master_id=master_id,
        duration_minutes=duration_minutes,
    )

    schedule = make_schedule()

    master_repository.get_by_id.return_value = master

    offering_repository.get_by_id.return_value = offering

    schedule_repository.get_by_master_and_day.return_value = schedule

    booking_repository.get_active_by_master_and_date.return_value = []

    return (
        master,
        offering,
        schedule,
    )


@pytest.mark.anyio
async def test_get_available_slots(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
    offering_repository: AsyncMock,
    schedule_repository: AsyncMock,
):
    master_id = uuid.uuid4()
    booking_date = future_date()

    _, offering, _ = prepare_available_slots(
        booking_repository=booking_repository,
        master_repository=master_repository,
        offering_repository=offering_repository,
        schedule_repository=schedule_repository,
        master_id=master_id,
    )

    result = await booking_service.get_available_slots(
        master_id=master_id,
        offering_id=offering.id,
        booking_date=booking_date,
    )

    assert result.master_id == master_id
    assert result.offering_id == offering.id
    assert result.booking_date == booking_date

    assert result.slots == [
        time(9, 0),
        time(9, 30),
        time(10, 0),
        time(10, 30),
        time(11, 0),
        time(11, 30),
        time(12, 0),
        time(12, 30),
        time(13, 0),
        time(13, 30),
        time(14, 0),
        time(14, 30),
        time(15, 0),
        time(15, 30),
        time(16, 0),
    ]

    booking_repository.get_active_by_master_and_date.assert_awaited_once_with(
        master_id=master_id,
        booking_date=booking_date,
    )


@pytest.mark.anyio
async def test_available_slots_exclude_conflicts(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
    offering_repository: AsyncMock,
    schedule_repository: AsyncMock,
):
    master_id = uuid.uuid4()
    booking_date = future_date()

    _, offering, _ = prepare_available_slots(
        booking_repository=booking_repository,
        master_repository=master_repository,
        offering_repository=offering_repository,
        schedule_repository=schedule_repository,
        master_id=master_id,
    )

    booking_repository.get_active_by_master_and_date.return_value = [
        make_existing_booking(
            booking_date=booking_date,
            start_time=time(
                10,
                0,
            ),
            end_time=time(
                11,
                0,
            ),
        )
    ]

    result = await booking_service.get_available_slots(
        master_id=master_id,
        offering_id=offering.id,
        booking_date=booking_date,
    )

    assert (
        time(
            9,
            0,
        )
        in result.slots
    )

    assert (
        time(
            9,
            30,
        )
        not in result.slots
    )

    assert (
        time(
            10,
            0,
        )
        not in result.slots
    )

    assert (
        time(
            10,
            30,
        )
        not in result.slots
    )

    assert (
        time(
            11,
            0,
        )
        in result.slots
    )

    assert len(result.slots) == 12


@pytest.mark.anyio
async def test_available_slots_multiple_conflicts(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
    offering_repository: AsyncMock,
    schedule_repository: AsyncMock,
):
    master_id = uuid.uuid4()
    booking_date = future_date()

    _, offering, _ = prepare_available_slots(
        booking_repository=booking_repository,
        master_repository=master_repository,
        offering_repository=offering_repository,
        schedule_repository=schedule_repository,
        master_id=master_id,
    )

    booking_repository.get_active_by_master_and_date.return_value = [
        make_existing_booking(
            booking_date=booking_date,
            start_time=time(
                10,
                0,
            ),
            end_time=time(
                11,
                0,
            ),
        ),
        make_existing_booking(
            booking_date=booking_date,
            start_time=time(
                14,
                0,
            ),
            end_time=time(
                15,
                0,
            ),
        ),
    ]

    result = await booking_service.get_available_slots(
        master_id=master_id,
        offering_id=offering.id,
        booking_date=booking_date,
    )

    assert (
        time(
            10,
            0,
        )
        not in result.slots
    )

    assert (
        time(
            14,
            0,
        )
        not in result.slots
    )

    assert (
        time(
            11,
            0,
        )
        in result.slots
    )

    assert (
        time(
            15,
            0,
        )
        in result.slots
    )


@pytest.mark.anyio
async def test_available_slots_respect_offering_duration(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
    offering_repository: AsyncMock,
    schedule_repository: AsyncMock,
):
    master_id = uuid.uuid4()
    booking_date = future_date()

    _, offering, _ = prepare_available_slots(
        booking_repository=booking_repository,
        master_repository=master_repository,
        offering_repository=offering_repository,
        schedule_repository=schedule_repository,
        master_id=master_id,
        duration_minutes=90,
    )

    result = await booking_service.get_available_slots(
        master_id=master_id,
        offering_id=offering.id,
        booking_date=booking_date,
    )

    assert result.slots[0] == time(
        9,
        0,
    )

    assert result.slots[-1] == time(
        15,
        30,
    )

    assert len(result.slots) == 14

    assert (
        time(
            16,
            0,
        )
        not in result.slots
    )


@pytest.mark.anyio
async def test_available_slots_in_past(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
):
    booking_date = date.today() - timedelta(days=1)

    with pytest.raises(BookingInPastError):
        await booking_service.get_available_slots(
            master_id=uuid.uuid4(),
            offering_id=uuid.uuid4(),
            booking_date=booking_date,
        )

    master_repository.get_by_id.assert_not_awaited()

    booking_repository.get_active_by_master_and_date.assert_not_awaited()


@pytest.mark.anyio
async def test_available_slots_master_not_found(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
    offering_repository: AsyncMock,
):
    master_repository.get_by_id.return_value = None

    with pytest.raises(MasterNotFoundError):
        await booking_service.get_available_slots(
            master_id=uuid.uuid4(),
            offering_id=uuid.uuid4(),
            booking_date=future_date(),
        )

    offering_repository.get_by_id.assert_not_awaited()

    booking_repository.get_active_by_master_and_date.assert_not_awaited()


@pytest.mark.anyio
async def test_available_slots_master_inactive(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
    offering_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    master_repository.get_by_id.return_value = make_master(
        master_id=master_id,
        is_active=False,
    )

    with pytest.raises(MasterInactiveError):
        await booking_service.get_available_slots(
            master_id=master_id,
            offering_id=uuid.uuid4(),
            booking_date=future_date(),
        )

    offering_repository.get_by_id.assert_not_awaited()

    booking_repository.get_active_by_master_and_date.assert_not_awaited()


@pytest.mark.anyio
async def test_available_slots_offering_not_found(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
    offering_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    master_repository.get_by_id.return_value = make_master(master_id=master_id)

    offering_repository.get_by_id.return_value = None

    with pytest.raises(OfferingNotFoundError):
        await booking_service.get_available_slots(
            master_id=master_id,
            offering_id=uuid.uuid4(),
            booking_date=future_date(),
        )

    booking_repository.get_active_by_master_and_date.assert_not_awaited()


@pytest.mark.anyio
async def test_available_slots_offering_inactive(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
    offering_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    master_repository.get_by_id.return_value = make_master(master_id=master_id)

    offering_repository.get_by_id.return_value = make_offering(
        master_id=master_id,
        is_active=False,
    )

    with pytest.raises(OfferingInactiveError):
        await booking_service.get_available_slots(
            master_id=master_id,
            offering_id=uuid.uuid4(),
            booking_date=future_date(),
        )

    booking_repository.get_active_by_master_and_date.assert_not_awaited()


@pytest.mark.anyio
async def test_available_slots_offering_from_other_master(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
    offering_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    master_repository.get_by_id.return_value = make_master(master_id=master_id)

    offering_repository.get_by_id.return_value = make_offering(master_id=uuid.uuid4())

    with pytest.raises(OfferingDoesNotBelongToMasterError):
        await booking_service.get_available_slots(
            master_id=master_id,
            offering_id=uuid.uuid4(),
            booking_date=future_date(),
        )

    booking_repository.get_active_by_master_and_date.assert_not_awaited()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "schedule",
    [
        None,
        make_schedule(is_working=False),
        make_schedule(start_time=None),
        make_schedule(end_time=None),
    ],
)
async def test_available_slots_schedule_unavailable(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
    offering_repository: AsyncMock,
    schedule_repository: AsyncMock,
    schedule,
):
    master_id = uuid.uuid4()

    master_repository.get_by_id.return_value = make_master(master_id=master_id)

    offering = make_offering(master_id=master_id)

    offering_repository.get_by_id.return_value = offering

    schedule_repository.get_by_master_and_day.return_value = schedule

    with pytest.raises(MasterScheduleUnavailableError):
        await booking_service.get_available_slots(
            master_id=master_id,
            offering_id=offering.id,
            booking_date=future_date(),
        )

    booking_repository.get_active_by_master_and_date.assert_not_awaited()


@pytest.mark.parametrize(
    (
        "requested_start",
        "expected",
    ),
    [
        (
            time(9, 0),
            True,
        ),
        (
            time(9, 30),
            True,
        ),
        (
            time(10, 0),
            True,
        ),
        (
            time(9, 15),
            False,
        ),
        (
            time(8, 30),
            False,
        ),
    ],
)
def test_is_valid_slot_start(
    requested_start: time,
    expected: bool,
):
    result = BookingService._is_valid_slot_start(
        booking_date=future_date(),
        schedule_start=time(
            9,
            0,
        ),
        requested_start=requested_start,
    )

    assert result is expected


@pytest.mark.parametrize(
    (
        "existing_start",
        "existing_end",
        "requested_start",
        "requested_end",
        "expected",
    ),
    [
        (
            time(10, 0),
            time(11, 0),
            time(10, 30),
            time(11, 30),
            True,
        ),
        (
            time(10, 0),
            time(11, 0),
            time(9, 0),
            time(10, 0),
            False,
        ),
        (
            time(10, 0),
            time(11, 0),
            time(11, 0),
            time(12, 0),
            False,
        ),
        (
            time(10, 0),
            time(11, 0),
            time(9, 30),
            time(11, 30),
            True,
        ),
    ],
)
def test_bookings_overlap(
    existing_start: time,
    existing_end: time,
    requested_start: time,
    requested_end: time,
    expected: bool,
):
    booking_date = future_date()

    existing_booking = make_existing_booking(
        booking_date=booking_date,
        start_time=existing_start,
        end_time=existing_end,
    )

    result = BookingService._bookings_overlap(
        existing_booking=existing_booking,
        requested_start=datetime.combine(
            booking_date,
            requested_start,
        ),
        requested_end=datetime.combine(
            booking_date,
            requested_end,
        ),
    )

    assert result is expected
