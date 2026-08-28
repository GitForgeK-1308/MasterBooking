import uuid
from datetime import time
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Time,
    UniqueConstraint,
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

from src.database.base import Base

if TYPE_CHECKING:
    from src.masters.models import Master


class WeekDay(str, Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class MasterSchedule(Base):
    __tablename__ = "master_schedules"

    __table_args__ = (
        UniqueConstraint(
            "master_id",
            "day_of_week",
            name="uq_master_schedule_day",
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
        index=True,
    )

    day_of_week: Mapped[WeekDay] = mapped_column(
        SQLAlchemyEnum(
            WeekDay,
            name="week_day_enum",
            values_callable=lambda enum: [day.value for day in enum],
        ),
        nullable=False,
    )

    start_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    end_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    is_working: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    master: Mapped["Master"] = relationship(
        back_populates="schedules",
    )
