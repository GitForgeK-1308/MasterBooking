import uuid
from datetime import date, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bookings.models import (
    Booking,
    BookingStatus,
)


class BookingRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def get_by_id(
        self,
        booking_id: uuid.UUID,
    ) -> Booking | None:
        return await self.session.scalar(
            select(Booking).where(
                Booking.id == booking_id
            )
        )

    async def get_by_master_and_date(
        self,
        master_id: uuid.UUID,
        booking_date: date,
    ) -> list[Booking]:
        result = await self.session.scalars(
            select(Booking)
            .where(
                Booking.master_id == master_id,
                Booking.booking_date == booking_date,
            )
            .order_by(
                Booking.start_time.asc(),
                Booking.id.asc(),
            )
        )

        return list(result.all())

    async def get_active_by_master_and_date(
        self,
        master_id: uuid.UUID,
        booking_date: date,
    ) -> list[Booking]:
        result = await self.session.scalars(
            select(Booking)
            .where(
                Booking.master_id == master_id,
                Booking.booking_date == booking_date,
                Booking.status
                != BookingStatus.CANCELLED,
            )
            .order_by(
                Booking.start_time.asc(),
                Booking.id.asc(),
            )
        )

        return list(result.all())

    async def get_conflicting_booking(
        self,
        master_id: uuid.UUID,
        booking_date: date,
        start_time: time,
        end_time: time,
    ) -> Booking | None:
        return await self.session.scalar(
            select(Booking)
            .where(
                Booking.master_id == master_id,
                Booking.booking_date == booking_date,
                Booking.status
                != BookingStatus.CANCELLED,
                Booking.start_time < end_time,
                Booking.end_time > start_time,
            )
            .limit(1)
        )

    async def get_by_client_id(
        self,
        client_id: uuid.UUID,
    ) -> list[Booking]:
        result = await self.session.scalars(
            select(Booking)
            .where(
                Booking.client_id == client_id
            )
            .order_by(
                Booking.booking_date.asc(),
                Booking.start_time.asc(),
                Booking.id.asc(),
            )
        )

        return list(result.all())

    async def create(
        self,
        booking: Booking,
    ) -> Booking:
        self.session.add(
            booking
        )

        await self.session.commit()
        await self.session.refresh(
            booking
        )

        return booking

    async def update(
        self,
        booking: Booking,
    ) -> Booking:
        await self.session.commit()
        await self.session.refresh(
            booking
        )

        return booking