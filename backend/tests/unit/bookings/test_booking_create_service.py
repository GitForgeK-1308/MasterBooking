import uuid
from datetime import date, time, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.bookings.exceptions import (
    BookingInPastError,
    BookingOutsideWorkingHoursError,
    BookingTimeConflictError,
    ClientPhoneRequiredError,
    InvalidBookingStartTimeError,
    MasterInactiveError,
    MasterNotFoundError,
    MasterScheduleUnavailableError,
    OfferingDoesNotBelongToMasterError,
    OfferingInactiveError,
    OfferingNotFoundError,
)
from src.bookings.models import Booking
from src.bookings.repository import BookingRepository
from src.bookings.schemas import BookingCreate
from src.bookings.service import BookingService
from src.master_offering.repository import (
    MasterOfferingRepository,
)
from src.master_schedule.repository import (
    MasterScheduleRepository,
)
from src.masters.repository import MasterRepository


def make_user(
    *,
    phone: str | None = "+79991234567",
):
    return SimpleNamespace(
        id=uuid.uuid4(),
        first_name="Ivan",
        last_name="Ivanov",
        phone=phone,
        email="user@example.com",
    )


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


def future_date() -> date:
    return date.today() + timedelta(
        days=7
    )


@pytest.fixture
def booking_repository() -> AsyncMock:
    return AsyncMock(
        spec=BookingRepository
    )


@pytest.fixture
def master_repository() -> AsyncMock:
    return AsyncMock(
        spec=MasterRepository
    )


@pytest.fixture
def offering_repository() -> AsyncMock:
    return AsyncMock(
        spec=MasterOfferingRepository
    )


@pytest.fixture
def schedule_repository() -> AsyncMock:
    return AsyncMock(
        spec=MasterScheduleRepository
    )


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


def prepare_bookable_data(
    *,
    master_repository: AsyncMock,
    offering_repository: AsyncMock,
    schedule_repository: AsyncMock,
    master_id: uuid.UUID,
    duration_minutes: int = 60,
):
    master = make_master(
        master_id=master_id
    )

    offering = make_offering(
        master_id=master_id,
        duration_minutes=duration_minutes,
    )

    schedule = make_schedule()

    master_repository.get_by_id.return_value = (
        master
    )

    offering_repository.get_by_id.return_value = (
        offering
    )

    schedule_repository.get_by_master_and_day.return_value = (
        schedule
    )

    return (
        master,
        offering,
        schedule,
    )


@pytest.mark.anyio
async def test_create_booking(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
    offering_repository: AsyncMock,
    schedule_repository: AsyncMock,
):
    user = make_user()
    master_id = uuid.uuid4()

    _, offering, _ = prepare_bookable_data(
        master_repository=master_repository,
        offering_repository=offering_repository,
        schedule_repository=schedule_repository,
        master_id=master_id,
    )

    booking_repository.get_conflicting_booking.return_value = (
        None
    )

    booking_repository.create.side_effect = (
        lambda booking: booking
    )

    booking_date = future_date()

    data = BookingCreate(
        offering_id=offering.id,
        booking_date=booking_date,
        start_time=time(
            10,
            0,
        ),
    )

    result = await booking_service.create_booking(
        master_id=master_id,
        current_user=user,
        data=data,
    )

    assert isinstance(
        result,
        Booking,
    )

    assert result.client_id == user.id
    assert result.master_id == master_id
    assert result.offering_id == offering.id

    assert result.booking_date == booking_date
    assert result.start_time == time(
        10,
        0,
    )
    assert result.end_time == time(
        11,
        0,
    )

    assert (
        result.client_name
        == "Ivan Ivanov"
    )
    assert result.client_phone == user.phone
    assert result.client_email == user.email

    booking_repository.get_conflicting_booking.assert_awaited_once_with(
        master_id=master_id,
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

    booking_repository.create.assert_awaited_once_with(
        result
    )


@pytest.mark.anyio
async def test_create_booking_phone_required(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
):
    user = make_user(
        phone=None
    )

    with pytest.raises(
        ClientPhoneRequiredError
    ):
        await booking_service.create_booking(
            master_id=uuid.uuid4(),
            current_user=user,
            data=BookingCreate(
                offering_id=uuid.uuid4(),
                booking_date=future_date(),
                start_time=time(
                    10,
                    0,
                ),
            ),
        )

    master_repository.get_by_id.assert_not_awaited()
    booking_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_create_booking_master_not_found(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
    offering_repository: AsyncMock,
):
    master_repository.get_by_id.return_value = None

    with pytest.raises(
        MasterNotFoundError
    ):
        await booking_service.create_booking(
            master_id=uuid.uuid4(),
            current_user=make_user(),
            data=BookingCreate(
                offering_id=uuid.uuid4(),
                booking_date=future_date(),
                start_time=time(
                    10,
                    0,
                ),
            ),
        )

    offering_repository.get_by_id.assert_not_awaited()
    booking_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_create_booking_master_inactive(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
    offering_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    master_repository.get_by_id.return_value = (
        make_master(
            master_id=master_id,
            is_active=False,
        )
    )

    with pytest.raises(
        MasterInactiveError
    ):
        await booking_service.create_booking(
            master_id=master_id,
            current_user=make_user(),
            data=BookingCreate(
                offering_id=uuid.uuid4(),
                booking_date=future_date(),
                start_time=time(
                    10,
                    0,
                ),
            ),
        )

    offering_repository.get_by_id.assert_not_awaited()
    booking_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_create_booking_offering_not_found(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
    offering_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    master_repository.get_by_id.return_value = (
        make_master(
            master_id=master_id
        )
    )

    offering_repository.get_by_id.return_value = None

    with pytest.raises(
        OfferingNotFoundError
    ):
        await booking_service.create_booking(
            master_id=master_id,
            current_user=make_user(),
            data=BookingCreate(
                offering_id=uuid.uuid4(),
                booking_date=future_date(),
                start_time=time(
                    10,
                    0,
                ),
            ),
        )

    booking_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_create_booking_offering_inactive(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
    offering_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    master_repository.get_by_id.return_value = (
        make_master(
            master_id=master_id
        )
    )

    offering_repository.get_by_id.return_value = (
        make_offering(
            master_id=master_id,
            is_active=False,
        )
    )

    with pytest.raises(
        OfferingInactiveError
    ):
        await booking_service.create_booking(
            master_id=master_id,
            current_user=make_user(),
            data=BookingCreate(
                offering_id=uuid.uuid4(),
                booking_date=future_date(),
                start_time=time(
                    10,
                    0,
                ),
            ),
        )

    booking_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_create_booking_offering_from_other_master(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
    offering_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    master_repository.get_by_id.return_value = (
        make_master(
            master_id=master_id
        )
    )

    offering_repository.get_by_id.return_value = (
        make_offering(
            master_id=uuid.uuid4()
        )
    )

    with pytest.raises(
        OfferingDoesNotBelongToMasterError
    ):
        await booking_service.create_booking(
            master_id=master_id,
            current_user=make_user(),
            data=BookingCreate(
                offering_id=uuid.uuid4(),
                booking_date=future_date(),
                start_time=time(
                    10,
                    0,
                ),
            ),
        )

    booking_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_create_booking_in_past(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
    offering_repository: AsyncMock,
    schedule_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    _, offering, _ = prepare_bookable_data(
        master_repository=master_repository,
        offering_repository=offering_repository,
        schedule_repository=schedule_repository,
        master_id=master_id,
    )

    data = BookingCreate(
        offering_id=offering.id,
        booking_date=(
            date.today()
            - timedelta(
                days=1
            )
        ),
        start_time=time(
            10,
            0,
        ),
    )

    with pytest.raises(
        BookingInPastError
    ):
        await booking_service.create_booking(
            master_id=master_id,
            current_user=make_user(),
            data=data,
        )

    schedule_repository.get_by_master_and_day.assert_not_awaited()
    booking_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_create_booking_schedule_unavailable(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
    offering_repository: AsyncMock,
    schedule_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    master = make_master(
        master_id=master_id
    )

    offering = make_offering(
        master_id=master_id
    )

    master_repository.get_by_id.return_value = (
        master
    )

    offering_repository.get_by_id.return_value = (
        offering
    )

    schedule_repository.get_by_master_and_day.return_value = (
        None
    )

    with pytest.raises(
        MasterScheduleUnavailableError
    ):
        await booking_service.create_booking(
            master_id=master_id,
            current_user=make_user(),
            data=BookingCreate(
                offering_id=offering.id,
                booking_date=future_date(),
                start_time=time(
                    10,
                    0,
                ),
            ),
        )

    booking_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_create_booking_before_working_hours(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
    offering_repository: AsyncMock,
    schedule_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    _, offering, _ = prepare_bookable_data(
        master_repository=master_repository,
        offering_repository=offering_repository,
        schedule_repository=schedule_repository,
        master_id=master_id,
    )

    with pytest.raises(
        BookingOutsideWorkingHoursError
    ):
        await booking_service.create_booking(
            master_id=master_id,
            current_user=make_user(),
            data=BookingCreate(
                offering_id=offering.id,
                booking_date=future_date(),
                start_time=time(
                    8,
                    30,
                ),
            ),
        )

    booking_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_create_booking_ends_after_working_hours(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
    offering_repository: AsyncMock,
    schedule_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    _, offering, _ = prepare_bookable_data(
        master_repository=master_repository,
        offering_repository=offering_repository,
        schedule_repository=schedule_repository,
        master_id=master_id,
    )

    with pytest.raises(
        BookingOutsideWorkingHoursError
    ):
        await booking_service.create_booking(
            master_id=master_id,
            current_user=make_user(),
            data=BookingCreate(
                offering_id=offering.id,
                booking_date=future_date(),
                start_time=time(
                    16,
                    30,
                ),
            ),
        )

    booking_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_create_booking_cannot_cross_midnight(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
    offering_repository: AsyncMock,
    schedule_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    _, offering, _ = prepare_bookable_data(
        master_repository=master_repository,
        offering_repository=offering_repository,
        schedule_repository=schedule_repository,
        master_id=master_id,
        duration_minutes=600,
    )

    with pytest.raises(
        BookingOutsideWorkingHoursError
    ):
        await booking_service.create_booking(
            master_id=master_id,
            current_user=make_user(),
            data=BookingCreate(
                offering_id=offering.id,
                booking_date=future_date(),
                start_time=time(
                    20,
                    0,
                ),
            ),
        )

    booking_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_create_booking_invalid_slot_start(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
    offering_repository: AsyncMock,
    schedule_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    _, offering, _ = prepare_bookable_data(
        master_repository=master_repository,
        offering_repository=offering_repository,
        schedule_repository=schedule_repository,
        master_id=master_id,
    )

    with pytest.raises(
        InvalidBookingStartTimeError
    ):
        await booking_service.create_booking(
            master_id=master_id,
            current_user=make_user(),
            data=BookingCreate(
                offering_id=offering.id,
                booking_date=future_date(),
                start_time=time(
                    9,
                    15,
                ),
            ),
        )

    booking_repository.get_conflicting_booking.assert_not_awaited()
    booking_repository.create.assert_not_awaited()


@pytest.mark.anyio
async def test_create_booking_time_conflict(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
    offering_repository: AsyncMock,
    schedule_repository: AsyncMock,
):
    master_id = uuid.uuid4()

    _, offering, _ = prepare_bookable_data(
        master_repository=master_repository,
        offering_repository=offering_repository,
        schedule_repository=schedule_repository,
        master_id=master_id,
    )

    booking_repository.get_conflicting_booking.return_value = (
        SimpleNamespace(
            id=uuid.uuid4()
        )
    )

    with pytest.raises(
        BookingTimeConflictError
    ):
        await booking_service.create_booking(
            master_id=master_id,
            current_user=make_user(),
            data=BookingCreate(
                offering_id=offering.id,
                booking_date=future_date(),
                start_time=time(
                    10,
                    0,
                ),
            ),
        )

    booking_repository.create.assert_not_awaited()