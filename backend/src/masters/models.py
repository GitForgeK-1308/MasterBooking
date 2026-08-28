import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from src.database.base import Base

if TYPE_CHECKING:
    from src.bookings.models import Booking
    from src.locations.models import City, District
    from src.master_offering.models import MasterOffering
    from src.master_schedule.models import MasterSchedule
    from src.users.models import User


class Master(Base):
    __tablename__ = "masters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        unique=True,
        nullable=True,
    )

    first_name: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(25),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    experience: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    education: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    district: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    address: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    city_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "cities.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    district_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "districts.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    master_services: Mapped[list["MasterOffering"]] = relationship(
        back_populates="master",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    schedules: Mapped[list["MasterSchedule"]] = relationship(
        back_populates="master",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="master",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    user: Mapped["User | None"] = relationship(
        back_populates="master_profile",
    )

    city_ref: Mapped["City | None"] = relationship(
        foreign_keys=[city_id],
    )

    district_ref: Mapped["District | None"] = relationship(
        foreign_keys=[district_id],
    )

    @property
    def phone(self) -> str | None:
        if self.user is None:
            return None

        return self.user.phone

    @property
    def avatar_url(self) -> str | None:
        if self.user is None:
            return None

        if self.user.avatar_storage_key is None:
            return None

        return f"/uploads/{self.user.avatar_storage_key}"
