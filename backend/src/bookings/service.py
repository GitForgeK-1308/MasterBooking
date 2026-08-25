import uuid
from datetime import date, datetime, time, timedelta

from src.bookings.exceptions import (
    BookingAccessDeniedError,
    BookingInPastError,
    BookingNotFoundError,
    BookingOutsideWorkingHoursError,
    BookingTimeConflictError,
    ClientPhoneRequiredError,
    InvalidBookingStartTimeError,
    InvalidBookingStatusTransitionError,
    MasterInactiveError,
    MasterNotFoundError,
    MasterScheduleUnavailableError,
    OfferingDoesNotBelongToMasterError,
    OfferingInactiveError,
    OfferingNotFoundError,
    SelfBookingNotAllowedError,
)
from src.bookings.models import (
    Booking,
    BookingStatus,
)
from src.bookings.repository import BookingRepository
from src.bookings.schemas import (
    AvailableSlotsResponse,
    BookingCreate,
    BookingStatusUpdate,
)
from src.master_offering.models import MasterOffering
from src.master_offering.repository import (
    MasterOfferingRepository,
)
from src.master_schedule.models import (
    MasterSchedule,
    WeekDay,
)
from src.master_schedule.repository import (
    MasterScheduleRepository,
)
from src.masters.repository import MasterRepository
from src.users.models import User

WEEKDAY_BY_NUMBER = {
    0: WeekDay.MONDAY,
    1: WeekDay.TUESDAY,
    2: WeekDay.WEDNESDAY,
    3: WeekDay.THURSDAY,
    4: WeekDay.FRIDAY,
    5: WeekDay.SATURDAY,
    6: WeekDay.SUNDAY,
}

SLOT_STEP_MINUTES = 30


class BookingService:
    def __init__(
        self,
        booking_repository: BookingRepository,
        master_repository: MasterRepository,
        offering_repository: MasterOfferingRepository,
        schedule_repository: MasterScheduleRepository,
    ) -> None:
        self.booking_repository = booking_repository
        self.master_repository = master_repository
        self.offering_repository = offering_repository
        self.schedule_repository = schedule_repository

    async def get_booking_for_user(
        self,
        booking_id: uuid.UUID,
        current_user: User,
    ) -> Booking:
        booking = await self.booking_repository.get_by_id(
            booking_id
        )

        if booking is None:
            raise BookingNotFoundError

        if booking.client_id == current_user.id:
            return booking

        master = await self.master_repository.get_by_user_id(
            current_user.id
        )

        if (
            master is not None
            and booking.master_id == master.id
        ):
            return booking

        raise BookingAccessDeniedError

    async def get_master_bookings(
        self,
        master_id: uuid.UUID,
        booking_date: date,
    ) -> list[Booking]:
        master = await self.master_repository.get_by_id(
            master_id
        )

        if master is None:
            raise MasterNotFoundError

        return await self.booking_repository.get_by_master_and_date(
            master_id=master_id,
            booking_date=booking_date,
        )

    async def create_booking(
        self,
        master_id: uuid.UUID,
        current_user: User,
        data: BookingCreate,
    ) -> Booking:

        current_master = await self.master_repository.get_by_user_id(
            current_user.id
        )

        if (
            current_master is not None
            and current_master.id == master_id
        ):
            raise SelfBookingNotAllowedError

        if not current_user.phone:
            raise ClientPhoneRequiredError

        offering = await self._get_bookable_offering(
            master_id=master_id,
            offering_id=data.offering_id,
        )

        booking_start = datetime.combine(
            data.booking_date,
            data.start_time,
        )

        now = datetime.now()

        if booking_start <= now:
            raise BookingInPastError

        schedule = await self._get_working_schedule(
            master_id=master_id,
            booking_date=data.booking_date,
        )

        booking_end = booking_start + timedelta(
            minutes=offering.duration_minutes
        )

        if booking_end.date() != data.booking_date:
            raise BookingOutsideWorkingHoursError

        end_time = booking_end.time()

        if (
            schedule.start_time is None
            or schedule.end_time is None
        ):
            raise MasterScheduleUnavailableError

        if (
            data.start_time < schedule.start_time
            or end_time > schedule.end_time
        ):
            raise BookingOutsideWorkingHoursError

        if not self._is_valid_slot_start(
            booking_date=data.booking_date,
            schedule_start=schedule.start_time,
            requested_start=data.start_time,
        ):
            raise InvalidBookingStartTimeError

        conflicting_booking = (
            await self.booking_repository.get_conflicting_booking(
                master_id=master_id,
                booking_date=data.booking_date,
                start_time=data.start_time,
                end_time=end_time,
            )
        )

        if conflicting_booking is not None:
            raise BookingTimeConflictError

        new_booking = Booking(
            client_id=current_user.id,
            master_id=master_id,
            offering_id=data.offering_id,
            booking_date=data.booking_date,
            start_time=data.start_time,
            end_time=end_time,
            client_name=(
                f"{current_user.first_name} "
                f"{current_user.last_name}"
            ),
            client_phone=current_user.phone,
            client_email=current_user.email,
        )

        return await self.booking_repository.create(
            new_booking
        )

    async def update_booking_status(
        self,
        booking_id: uuid.UUID,
        master_id: uuid.UUID,
        data: BookingStatusUpdate,
    ) -> Booking:
        booking = await self.booking_repository.get_by_id(
            booking_id
        )

        if booking is None:
            raise BookingNotFoundError

        if booking.master_id != master_id:
            raise BookingAccessDeniedError

        allowed_transitions = {
            BookingStatus.PENDING: {
                BookingStatus.CONFIRMED,
                BookingStatus.CANCELLED,
            },
            BookingStatus.CONFIRMED: {
                BookingStatus.COMPLETED,
                BookingStatus.CANCELLED,
            },
        }

        allowed_statuses = allowed_transitions.get(
            booking.status,
            set(),
        )

        if data.status not in allowed_statuses:
            raise InvalidBookingStatusTransitionError

        booking.status = data.status

        return await self.booking_repository.update(
            booking
        )

    async def get_available_slots(
        self,
        master_id: uuid.UUID,
        offering_id: uuid.UUID,
        booking_date: date,
    ) -> AvailableSlotsResponse:
        now = datetime.now()

        if booking_date < now.date():
            raise BookingInPastError

        offering = await self._get_bookable_offering(
            master_id=master_id,
            offering_id=offering_id,
        )

        schedule = await self._get_working_schedule(
            master_id=master_id,
            booking_date=booking_date,
        )

        if (
            schedule.start_time is None
            or schedule.end_time is None
        ):
            raise MasterScheduleUnavailableError

        existing_bookings = (
            await self.booking_repository.get_active_by_master_and_date(
                master_id=master_id,
                booking_date=booking_date,
            )
        )

        work_start = datetime.combine(
            booking_date,
            schedule.start_time,
        )

        work_end = datetime.combine(
            booking_date,
            schedule.end_time,
        )

        offering_duration = timedelta(
            minutes=offering.duration_minutes
        )

        slot_step = timedelta(
            minutes=SLOT_STEP_MINUTES
        )

        available_slots: list[time] = []

        current_start = work_start

        while (
            current_start + offering_duration
            <= work_end
        ):
            current_end = (
                current_start + offering_duration
            )

            if current_start > now:
                has_conflict = any(
                    self._bookings_overlap(
                        existing_booking=booking,
                        requested_start=current_start,
                        requested_end=current_end,
                    )
                    for booking in existing_bookings
                )

                if not has_conflict:
                    available_slots.append(
                        current_start.time()
                    )

            current_start += slot_step

        return AvailableSlotsResponse(
            master_id=master_id,
            offering_id=offering_id,
            booking_date=booking_date,
            slots=available_slots,
        )

    async def get_client_bookings(
        self,
        client_id: uuid.UUID,
    ) -> list[Booking]:
        return await self.booking_repository.get_by_client_id(
            client_id
        )

    async def cancel_client_booking(
        self,
        booking_id: uuid.UUID,
        client_id: uuid.UUID,
    ) -> Booking:
        booking = await self.booking_repository.get_by_id(
            booking_id
        )

        if booking is None:
            raise BookingNotFoundError

        if booking.client_id != client_id:
            raise BookingAccessDeniedError

        if booking.status not in {
            BookingStatus.PENDING,
            BookingStatus.CONFIRMED,
        }:
            raise InvalidBookingStatusTransitionError

        booking.status = BookingStatus.CANCELLED

        return await self.booking_repository.update(
            booking
        )

    async def _get_bookable_offering(
        self,
        master_id: uuid.UUID,
        offering_id: uuid.UUID,
    ) -> MasterOffering:
        master = await self.master_repository.get_by_id(
            master_id
        )

        if master is None:
            raise MasterNotFoundError

        if not master.is_active:
            raise MasterInactiveError

        offering = await self.offering_repository.get_by_id(
            offering_id
        )

        if offering is None:
            raise OfferingNotFoundError

        if not offering.is_active:
            raise OfferingInactiveError

        if offering.master_id != master_id:
            raise OfferingDoesNotBelongToMasterError

        return offering

    async def _get_working_schedule(
        self,
        master_id: uuid.UUID,
        booking_date: date,
    ) -> MasterSchedule:
        day_of_week = WEEKDAY_BY_NUMBER[
            booking_date.weekday()
        ]

        schedule = (
            await self.schedule_repository.get_by_master_and_day(
                master_id=master_id,
                day_of_week=day_of_week,
            )
        )

        if (
            schedule is None
            or not schedule.is_working
            or schedule.start_time is None
            or schedule.end_time is None
        ):
            raise MasterScheduleUnavailableError

        return schedule

    @staticmethod
    def _is_valid_slot_start(
        booking_date: date,
        schedule_start: time,
        requested_start: time,
    ) -> bool:
        work_start = datetime.combine(
            booking_date,
            schedule_start,
        )

        requested_start_datetime = datetime.combine(
            booking_date,
            requested_start,
        )

        difference_seconds = (
            requested_start_datetime - work_start
        ).total_seconds()

        slot_step_seconds = (
            SLOT_STEP_MINUTES * 60
        )

        return (
            difference_seconds >= 0
            and difference_seconds
            % slot_step_seconds
            == 0
        )

    @staticmethod
    def _bookings_overlap(
        existing_booking: Booking,
        requested_start: datetime,
        requested_end: datetime,
    ) -> bool:
        existing_start = datetime.combine(
            existing_booking.booking_date,
            existing_booking.start_time,
        )

        existing_end = datetime.combine(
            existing_booking.booking_date,
            existing_booking.end_time,
        )

        return (
            existing_start < requested_end
            and existing_end > requested_start
        )