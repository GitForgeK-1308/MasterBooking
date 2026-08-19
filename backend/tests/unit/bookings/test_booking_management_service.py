import uuid
from datetime import date, time, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.bookings.exceptions import (
    BookingAccessDeniedError,
    BookingNotFoundError,
    InvalidBookingStatusTransitionError,
    MasterNotFoundError,
)
from src.bookings.models import BookingStatus
from src.bookings.repository import BookingRepository
from src.bookings.schemas import BookingStatusUpdate
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
    user_id: uuid.UUID | None = None,
):
    return SimpleNamespace(
        id=user_id or uuid.uuid4()
    )


def make_master(
    *,
    master_id: uuid.UUID | None = None,
):
    return SimpleNamespace(
        id=master_id or uuid.uuid4()
    )


def make_booking(
    *,
    client_id: uuid.UUID | None = None,
    master_id: uuid.UUID | None = None,
    status: BookingStatus = BookingStatus.PENDING,
):
    booking_date = (
        date.today()
        + timedelta(
            days=7
        )
    )

    return SimpleNamespace(
        id=uuid.uuid4(),
        client_id=client_id or uuid.uuid4(),
        master_id=master_id or uuid.uuid4(),
        offering_id=uuid.uuid4(),
        booking_date=booking_date,
        start_time=time(
            10,
            0,
        ),
        end_time=time(
            11,
            0,
        ),
        status=status,
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


@pytest.mark.anyio
async def test_get_booking_for_client(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
):
    user = make_user()

    booking = make_booking(
        client_id=user.id
    )

    booking_repository.get_by_id.return_value = (
        booking
    )

    result = await booking_service.get_booking_for_user(
        booking_id=booking.id,
        current_user=user,
    )

    assert result is booking

    booking_repository.get_by_id.assert_awaited_once_with(
        booking.id
    )

    master_repository.get_by_user_id.assert_not_awaited()


@pytest.mark.anyio
async def test_get_booking_for_master(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
):
    user = make_user()
    master = make_master()

    booking = make_booking(
        master_id=master.id
    )

    booking_repository.get_by_id.return_value = (
        booking
    )

    master_repository.get_by_user_id.return_value = (
        master
    )

    result = await booking_service.get_booking_for_user(
        booking_id=booking.id,
        current_user=user,
    )

    assert result is booking

    master_repository.get_by_user_id.assert_awaited_once_with(
        user.id
    )


@pytest.mark.anyio
async def test_get_booking_not_found(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
):
    booking_repository.get_by_id.return_value = (
        None
    )

    with pytest.raises(
        BookingNotFoundError
    ):
        await booking_service.get_booking_for_user(
            booking_id=uuid.uuid4(),
            current_user=make_user(),
        )

    master_repository.get_by_user_id.assert_not_awaited()


@pytest.mark.anyio
async def test_get_booking_access_denied_for_other_client(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
):
    booking = make_booking()

    booking_repository.get_by_id.return_value = (
        booking
    )

    master_repository.get_by_user_id.return_value = (
        None
    )

    user = make_user()

    with pytest.raises(
        BookingAccessDeniedError
    ):
        await booking_service.get_booking_for_user(
            booking_id=booking.id,
            current_user=user,
        )

    master_repository.get_by_user_id.assert_awaited_once_with(
        user.id
    )


@pytest.mark.anyio
async def test_get_booking_access_denied_for_other_master(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
):
    booking = make_booking()

    other_master = make_master()

    booking_repository.get_by_id.return_value = (
        booking
    )

    master_repository.get_by_user_id.return_value = (
        other_master
    )

    with pytest.raises(
        BookingAccessDeniedError
    ):
        await booking_service.get_booking_for_user(
            booking_id=booking.id,
            current_user=make_user(),
        )

    assert (
        other_master.id
        != booking.master_id
    )


@pytest.mark.anyio
async def test_get_master_bookings(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
):
    master = make_master()

    booking_date = (
        date.today()
        + timedelta(
            days=7
        )
    )

    bookings = [
        make_booking(
            master_id=master.id
        ),
        make_booking(
            master_id=master.id
        ),
    ]

    master_repository.get_by_id.return_value = (
        master
    )

    booking_repository.get_by_master_and_date.return_value = (
        bookings
    )

    result = await booking_service.get_master_bookings(
        master_id=master.id,
        booking_date=booking_date,
    )

    assert result == bookings

    master_repository.get_by_id.assert_awaited_once_with(
        master.id
    )

    booking_repository.get_by_master_and_date.assert_awaited_once_with(
        master_id=master.id,
        booking_date=booking_date,
    )


@pytest.mark.anyio
async def test_get_master_bookings_master_not_found(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    master_repository: AsyncMock,
):
    master_repository.get_by_id.return_value = (
        None
    )

    with pytest.raises(
        MasterNotFoundError
    ):
        await booking_service.get_master_bookings(
            master_id=uuid.uuid4(),
            booking_date=date.today(),
        )

    booking_repository.get_by_master_and_date.assert_not_awaited()


@pytest.mark.anyio
async def test_get_client_bookings(
    booking_service: BookingService,
    booking_repository: AsyncMock,
):
    client_id = uuid.uuid4()

    bookings = [
        make_booking(
            client_id=client_id
        ),
        make_booking(
            client_id=client_id
        ),
    ]

    booking_repository.get_by_client_id.return_value = (
        bookings
    )

    result = await booking_service.get_client_bookings(
        client_id
    )

    assert result == bookings

    booking_repository.get_by_client_id.assert_awaited_once_with(
        client_id
    )


@pytest.mark.anyio
@pytest.mark.parametrize(
    (
        "initial_status",
        "new_status",
    ),
    [
        (
            BookingStatus.PENDING,
            BookingStatus.CONFIRMED,
        ),
        (
            BookingStatus.PENDING,
            BookingStatus.CANCELLED,
        ),
        (
            BookingStatus.CONFIRMED,
            BookingStatus.COMPLETED,
        ),
        (
            BookingStatus.CONFIRMED,
            BookingStatus.CANCELLED,
        ),
    ],
)
async def test_update_booking_status_allowed(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    initial_status: BookingStatus,
    new_status: BookingStatus,
):
    master_id = uuid.uuid4()

    booking = make_booking(
        master_id=master_id,
        status=initial_status,
    )

    booking_repository.get_by_id.return_value = (
        booking
    )

    booking_repository.update.side_effect = (
        lambda item: item
    )

    result = await booking_service.update_booking_status(
        booking_id=booking.id,
        master_id=master_id,
        data=BookingStatusUpdate(
            status=new_status
        ),
    )

    assert result is booking
    assert result.status == new_status

    booking_repository.update.assert_awaited_once_with(
        booking
    )


@pytest.mark.anyio
async def test_update_booking_status_not_found(
    booking_service: BookingService,
    booking_repository: AsyncMock,
):
    booking_repository.get_by_id.return_value = (
        None
    )

    with pytest.raises(
        BookingNotFoundError
    ):
        await booking_service.update_booking_status(
            booking_id=uuid.uuid4(),
            master_id=uuid.uuid4(),
            data=BookingStatusUpdate(
                status=BookingStatus.CONFIRMED
            ),
        )

    booking_repository.update.assert_not_awaited()


@pytest.mark.anyio
async def test_update_booking_status_access_denied(
    booking_service: BookingService,
    booking_repository: AsyncMock,
):
    booking = make_booking()

    booking_repository.get_by_id.return_value = (
        booking
    )

    with pytest.raises(
        BookingAccessDeniedError
    ):
        await booking_service.update_booking_status(
            booking_id=booking.id,
            master_id=uuid.uuid4(),
            data=BookingStatusUpdate(
                status=BookingStatus.CONFIRMED
            ),
        )

    booking_repository.update.assert_not_awaited()


@pytest.mark.anyio
@pytest.mark.parametrize(
    (
        "initial_status",
        "new_status",
    ),
    [
        (
            BookingStatus.PENDING,
            BookingStatus.COMPLETED,
        ),
        (
            BookingStatus.CONFIRMED,
            BookingStatus.PENDING,
        ),
        (
            BookingStatus.COMPLETED,
            BookingStatus.CANCELLED,
        ),
        (
            BookingStatus.CANCELLED,
            BookingStatus.CONFIRMED,
        ),
    ],
)
async def test_update_booking_status_invalid_transition(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    initial_status: BookingStatus,
    new_status: BookingStatus,
):
    master_id = uuid.uuid4()

    booking = make_booking(
        master_id=master_id,
        status=initial_status,
    )

    booking_repository.get_by_id.return_value = (
        booking
    )

    with pytest.raises(
        InvalidBookingStatusTransitionError
    ):
        await booking_service.update_booking_status(
            booking_id=booking.id,
            master_id=master_id,
            data=BookingStatusUpdate(
                status=new_status
            ),
        )

    booking_repository.update.assert_not_awaited()

    assert booking.status == initial_status


@pytest.mark.anyio
@pytest.mark.parametrize(
    "initial_status",
    [
        BookingStatus.PENDING,
        BookingStatus.CONFIRMED,
    ],
)
async def test_cancel_client_booking(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    initial_status: BookingStatus,
):
    client_id = uuid.uuid4()

    booking = make_booking(
        client_id=client_id,
        status=initial_status,
    )

    booking_repository.get_by_id.return_value = (
        booking
    )

    booking_repository.update.side_effect = (
        lambda item: item
    )

    result = await booking_service.cancel_client_booking(
        booking_id=booking.id,
        client_id=client_id,
    )

    assert result is booking

    assert (
        result.status
        == BookingStatus.CANCELLED
    )

    booking_repository.update.assert_awaited_once_with(
        booking
    )


@pytest.mark.anyio
async def test_cancel_client_booking_not_found(
    booking_service: BookingService,
    booking_repository: AsyncMock,
):
    booking_repository.get_by_id.return_value = (
        None
    )

    with pytest.raises(
        BookingNotFoundError
    ):
        await booking_service.cancel_client_booking(
            booking_id=uuid.uuid4(),
            client_id=uuid.uuid4(),
        )

    booking_repository.update.assert_not_awaited()


@pytest.mark.anyio
async def test_cancel_client_booking_access_denied(
    booking_service: BookingService,
    booking_repository: AsyncMock,
):
    booking = make_booking()

    booking_repository.get_by_id.return_value = (
        booking
    )

    with pytest.raises(
        BookingAccessDeniedError
    ):
        await booking_service.cancel_client_booking(
            booking_id=booking.id,
            client_id=uuid.uuid4(),
        )

    booking_repository.update.assert_not_awaited()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "initial_status",
    [
        BookingStatus.COMPLETED,
        BookingStatus.CANCELLED,
    ],
)
async def test_cancel_client_booking_invalid_status(
    booking_service: BookingService,
    booking_repository: AsyncMock,
    initial_status: BookingStatus,
):
    client_id = uuid.uuid4()

    booking = make_booking(
        client_id=client_id,
        status=initial_status,
    )

    booking_repository.get_by_id.return_value = (
        booking
    )

    with pytest.raises(
        InvalidBookingStatusTransitionError
    ):
        await booking_service.cancel_client_booking(
            booking_id=booking.id,
            client_id=client_id,
        )

    booking_repository.update.assert_not_awaited()

    assert booking.status == initial_status