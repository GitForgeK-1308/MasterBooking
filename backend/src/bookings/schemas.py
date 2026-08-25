import uuid
from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict

from src.bookings.models import BookingStatus


class BookingCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    offering_id: uuid.UUID
    booking_date: date
    start_time: time


class BookingStatusUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    status: BookingStatus


class BookingResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: uuid.UUID
    client_id: uuid.UUID | None

    master_id: uuid.UUID
    offering_id: uuid.UUID

    booking_date: date
    start_time: time
    end_time: time

    client_name: str
    client_phone: str
    client_email: str | None
    has_review: bool

    status: BookingStatus
    created_at: datetime


class AvailableSlotsResponse(BaseModel):
    master_id: uuid.UUID
    offering_id: uuid.UUID
    booking_date: date
    slots: list[time]