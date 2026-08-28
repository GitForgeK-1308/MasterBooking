from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.bookings.repository import BookingRepository
from src.bookings.service import BookingService
from src.database.session import get_async_session
from src.master_offering.repository import (
    MasterOfferingRepository,
)
from src.master_schedule.repository import (
    MasterScheduleRepository,
)
from src.masters.repository import MasterRepository


def get_booking_service(
    session: AsyncSession = Depends(get_async_session),
) -> BookingService:
    booking_repository = BookingRepository(session)

    master_repository = MasterRepository(session)

    offering_repository = MasterOfferingRepository(session)

    schedule_repository = MasterScheduleRepository(session)

    return BookingService(
        booking_repository=booking_repository,
        master_repository=master_repository,
        offering_repository=offering_repository,
        schedule_repository=schedule_repository,
    )
