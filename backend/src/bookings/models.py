import uuid
from datetime import date, datetime, time
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Time,
)
from sqlalchemy import (
    Enum as SQLAlchemyEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.sql import func

from src.database.base import Base

if TYPE_CHECKING:
    from src.master_offering.models import MasterOffering
    from src.masters.models import Master
    from src.users.models import User


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Booking(Base):
    __tablename__ = "bookings"

    __table_args__ = (
        Index(
            "ix_bookings_master_date",
            "master_id",
            "booking_date",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    master_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "masters.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    offering_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "master_services.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    client_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    booking_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    client_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    client_phone: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    client_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    status: Mapped[BookingStatus] = mapped_column(
        SQLAlchemyEnum(
            BookingStatus,
            name="booking_status_enum",
            values_callable=lambda enum: [
                status.value for status in enum
            ],
        ),
        default=BookingStatus.PENDING,
        nullable=False,
    )

    reminder_sent: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    master: Mapped["Master"] = relationship(
        back_populates="bookings",
    )

    offering: Mapped["MasterOffering"] = relationship(
        back_populates="bookings",
    )

    client: Mapped["User | None"] = relationship(
        back_populates="bookings",
    )